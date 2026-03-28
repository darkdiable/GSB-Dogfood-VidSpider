import scrapy
import re
import requests
import json

class YoutubeSpider(scrapy.Spider):
    name = "youtube"
    allowed_domains = ["youtube.com", "youtu.be", "googlevideo.com", "ytimg.com"]
    start_urls = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'douyin_spider.middlewares.YoutubePlaywrightMiddleware': 543,
        },
        'DOWNLOAD_TIMEOUT': 180,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(YoutubeSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def parse(self, response):
        video_urls = response.meta.get('video_urls', [])
        video_info = response.meta.get('video_info', {})
        original_url = response.meta.get('original_url', response.url)
        
        self.logger.info(f'Total video URLs found: {len(video_urls)}')
        
        if video_info and video_info.get('url'):
            title = video_info.get('title', 'youtube_video')
            best_url = video_info.get('url')
            self.logger.info(f'Found video from page info: {title}')
            yield {
                'video_url': best_url,
                'title': title,
                'size_mb': 0,
                'video_urls': video_urls,
                'original_url': original_url
            }
            return
        
        title = 'youtube_video'
        og_title = response.xpath('//meta[@property="og:title"]/@content').get()
        if og_title:
            title = og_title
        
        youtube_video_urls = []
        for video_url in video_urls:
            if 'googlevideo.com' in video_url and 'videoplayback' in video_url:
                youtube_video_urls.append(video_url)
        
        if youtube_video_urls:
            self.logger.info(f'Found {len(youtube_video_urls)} YouTube video URLs')
            
            valid_videos = []
            for video_url in youtube_video_urls:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.youtube.com/',
                        'Range': 'bytes=0-1',
                    }
                    
                    resp = requests.get(
                        video_url,
                        headers=headers,
                        timeout=15,
                        stream=True,
                        allow_redirects=True
                    )
                    
                    if resp.status_code in [200, 206]:
                        content_range = resp.headers.get('content-range', '')
                        if content_range:
                            total_size = int(content_range.split('/')[-1])
                            valid_videos.append((video_url, total_size))
                            self.logger.info(f'Valid video: {total_size/1024/1024:.2f} MB')
                        else:
                            valid_videos.append((video_url, 0))
                            self.logger.info(f'Valid video URL found (size unknown)')
                            
                except Exception as e:
                    self.logger.debug(f'Error checking URL: {str(e)[:100]}')
            
            if valid_videos:
                valid_videos.sort(key=lambda x: x[1], reverse=True)
                best_url, best_size = valid_videos[0]
                if best_size > 0:
                    self.logger.info(f'Selected best video: {best_size/1024/1024:.2f} MB')
                else:
                    self.logger.info(f'Selected video URL (size unknown)')
                
                yield {
                    'video_url': best_url,
                    'title': title,
                    'size_mb': round(best_size / 1024 / 1024, 2) if best_size > 0 else 0,
                    'video_urls': [url for url, _ in valid_videos],
                    'original_url': original_url
                }
                return
        
        self.logger.error('No valid video files found')
