import scrapy
import re
import requests

class KuaishouSpider(scrapy.Spider):
    name = "kuaishou"
    allowed_domains = ["kuaishou.com", "v.kuaishou.com", "gifshow.com", "ksapisrv.com", "kuaishoucdn.com"]
    start_urls = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.kuaishou.com/',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'ks_spider.middlewares.KuaishouPlaywrightMiddleware': 543,
        },
        'DOWNLOAD_TIMEOUT': 120,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(KuaishouSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def parse(self, response):
        video_urls = response.meta.get('video_urls', [])
        
        if not video_urls:
            self.logger.warning('No video URLs captured from network, trying regex...')
            patterns = [
                r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*',
                r'"playUrl"\s*:\s*"(https?://[^"]+)"',
                r'"photoUrl"\s*:\s*"(https?://[^"]+)"',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1] if len(match) > 1 else match
                    if 'blob:' not in match and match not in video_urls:
                        video_urls.append(match)
        
        self.logger.info(f'Total video URLs found: {len(video_urls)}')
        
        valid_videos = []
        for video_url in video_urls:
            try:
                clean_url = video_url.replace('\\u002F', '/').replace('\\/', '/')
                
                head = requests.head(
                    clean_url,
                    timeout=10,
                    allow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.kuaishou.com/',
                    }
                )
                
                content_type = head.headers.get('content-type', '')
                content_length = int(head.headers.get('content-length', 0))
                
                if 'video' in content_type or 'mp4' in clean_url.lower():
                    if content_length > 100000 or content_length == 0:
                        valid_videos.append((clean_url, content_length if content_length > 0 else 1))
                        self.logger.info(f'Valid video: {content_length/1024/1024:.2f} MB - {clean_url[:100]}...')
                    
            except Exception as e:
                self.logger.debug(f'Error checking {video_url[:50]}: {str(e)}')
        
        if valid_videos:
            valid_videos.sort(key=lambda x: x[1], reverse=True)
            best_url, best_size = valid_videos[0]
            
            title = 'kuaishou_video'
            og_title = response.xpath('//meta[@property="og:title"]/@content').get()
            if og_title:
                title = og_title
            
            title_match = re.search(r'"caption"\s*:\s*"([^"]+)"', response.text)
            if title_match:
                title = title_match.group(1)
            
            self.logger.info(f'Selected best video: {best_size/1024/1024:.2f} MB')
            
            yield {
                'video_url': best_url,
                'title': title,
                'size_mb': round(best_size / 1024 / 1024, 2),
                'video_urls': [url for url, _ in valid_videos]
            }
        else:
            self.logger.error('No valid video files found')
