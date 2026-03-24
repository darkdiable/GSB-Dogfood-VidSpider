import scrapy
import re
import requests
import json

class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["instagram.com", "cdninstagram.com", "fbcdn.net", "instagram.fcgq1-1.fna.fbcdn.net"]
    start_urls = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.instagram.com/',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'douyin_spider.middlewares.InstagramPlaywrightMiddleware': 543,
        },
        'DOWNLOAD_TIMEOUT': 120,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(InstagramSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def parse(self, response):
        video_urls = response.meta.get('video_urls', [])
        
        self.logger.info(f'Captured from network: {len(video_urls)} URLs')
        for i, url in enumerate(video_urls):
            self.logger.debug(f'URL {i}: {url[:150]}...')
        
        if not video_urls:
            self.logger.warning('No video URLs captured from network, trying regex and script parsing...')
            
            patterns = [
                r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*',
                r'https?://scontent\.[^\s"\'<>]+cdninstagram\.com/[^\s"\'<>]+\.mp4[^\s"\'<>]*',
                r'https?://video\.[^\s"\'<>]+cdninstagram\.com/[^\s"\'<>]+\.mp4[^\s"\'<>]*',
                r'https?://instagram[^.]*\.fna\.fbcdn\.net/[^\s"\'<>]+\.mp4[^\s"\'<>]*',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if 'blob:' not in match and match not in video_urls:
                        video_urls.append(match)
                        self.logger.debug(f'Regex found: {match[:100]}...')
            
            script_data = self.extract_script_data(response.text)
            if script_data:
                extracted_urls = self.extract_video_from_json(script_data)
                for url in extracted_urls:
                    if url not in video_urls:
                        video_urls.append(url)
                        self.logger.debug(f'JSON found: {url[:100]}...')
        
        self.logger.info(f'Total video URLs found: {len(video_urls)}')
        
        valid_videos = []
        for video_url in video_urls:
            try:
                head = requests.head(
                    video_url,
                    timeout=10,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.instagram.com/',
                    },
                    allow_redirects=True
                )
                
                content_type = head.headers.get('content-type', '')
                content_length = int(head.headers.get('content-length', 0))
                
                self.logger.debug(f'Checking {video_url[:80]}: type={content_type}, size={content_length}')
                
                if ('video' in content_type or 'octet-stream' in content_type) and content_length > 100000:
                    valid_videos.append((video_url, content_length))
                    self.logger.info(f'Valid video: {content_length/1024/1024:.2f} MB - {video_url[:100]}...')
                    
            except Exception as e:
                self.logger.debug(f'Error checking {video_url[:50]}: {str(e)}')
        
        if valid_videos:
            valid_videos.sort(key=lambda x: x[1], reverse=True)
            best_url, best_size = valid_videos[0]
            
            title = 'instagram_video'
            og_title = response.xpath('//meta[@property="og:title"]/@content').get()
            if og_title:
                title = og_title
            
            self.logger.info(f'Selected best video: {best_size/1024/1024:.2f} MB')
            
            yield {
                'video_url': best_url,
                'title': title,
                'size_mb': round(best_size / 1024 / 1024, 2),
                'video_urls': [url for url, _ in valid_videos]
            }
        else:
            self.logger.error('No valid video files found')

    def extract_script_data(self, html):
        patterns = [
            r'window\._sharedData\s*=\s*({.*?});',
            r'window\.__additionalDataLoaded\s*\(\s*\'[^\']*\'\s*,\s*({.*?})\s*\);',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                try:
                    return json.loads(matches[0])
                except:
                    pass
        return None

    def extract_video_from_json(self, data):
        urls = []
        try:
            def find_videos(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['video_url', 'original_width', 'src', 'url']:
                            if isinstance(value, str) and ('.mp4' in value or 'video' in value.lower()):
                                urls.append(value)
                        find_videos(value)
                elif isinstance(obj, list):
                    for item in obj:
                        find_videos(item)
            find_videos(data)
        except:
            pass
        return urls
