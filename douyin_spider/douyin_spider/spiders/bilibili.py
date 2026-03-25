import scrapy
import re
import requests

class BilibiliSpider(scrapy.Spider):
    name = "bilibili"
    allowed_domains = ["bilibili.com", "bilivideo.com", "biliapi.net"]
    start_urls = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.bilibili.com/',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'douyin_spider.middlewares.BilibiliPlaywrightMiddleware': 543,
        },
        'DOWNLOAD_TIMEOUT': 120,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(BilibiliSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def parse(self, response):
        video_urls = response.meta.get('video_urls', [])
        audio_urls = response.meta.get('audio_urls', [])
        
        if not video_urls:
            self.logger.warning('No video URLs captured from network, trying regex...')
            patterns = [
                r'https?://[^\s"\'<>]+\.m4s[^\s"\'<>]*',
                r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if 'blob:' not in match and match not in video_urls:
                        if 'video' in match.lower():
                            video_urls.append(match)
                        elif 'audio' in match.lower():
                            audio_urls.append(match)
                        else:
                            video_urls.append(match)
        
        self.logger.info(f'Total video URLs found: {len(video_urls)}')
        self.logger.info(f'Total audio URLs found: {len(audio_urls)}')
        
        valid_videos = []
        for video_url in video_urls:
            try:
                head = requests.head(
                    video_url,
                    timeout=10,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.bilibili.com/',
                    }
                )
                
                content_type = head.headers.get('content-type', '')
                content_length = int(head.headers.get('content-length', 0))
                
                if ('video' in content_type or 'mp4' in content_type) and content_length > 100000:
                    valid_videos.append((video_url, content_length))
                    self.logger.info(f'Valid video: {content_length/1024/1024:.2f} MB - {video_url[:100]}...')
                    
            except Exception as e:
                self.logger.debug(f'Error checking {video_url[:50]}: {str(e)}')
        
        valid_audios = []
        for audio_url in audio_urls:
            try:
                head = requests.head(
                    audio_url,
                    timeout=10,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.bilibili.com/',
                    }
                )
                
                content_type = head.headers.get('content-type', '')
                content_length = int(head.headers.get('content-length', 0))
                
                if ('audio' in content_type or 'mp4' in content_type) and content_length > 10000:
                    valid_audios.append((audio_url, content_length))
                    self.logger.info(f'Valid audio: {content_length/1024/1024:.2f} MB - {audio_url[:100]}...')
                    
            except Exception as e:
                self.logger.debug(f'Error checking {audio_url[:50]}: {str(e)}')
        
        if valid_videos:
            valid_videos.sort(key=lambda x: x[1], reverse=True)
            best_url, best_size = valid_videos[0]
            
            best_audio_url = None
            if valid_audios:
                valid_audios.sort(key=lambda x: x[1], reverse=True)
                best_audio_url, _ = valid_audios[0]
            
            title = 'bilibili_video'
            og_title = response.xpath('//meta[@property="og:title"]/@content').get()
            if og_title:
                title = og_title
            
            self.logger.info(f'Selected best video: {best_size/1024/1024:.2f} MB')
            
            yield {
                'video_url': best_url,
                'audio_url': best_audio_url,
                'title': title,
                'size_mb': round(best_size / 1024 / 1024, 2),
                'video_urls': [url for url, _ in valid_videos]
            }
        else:
            self.logger.error('No valid video files found')
