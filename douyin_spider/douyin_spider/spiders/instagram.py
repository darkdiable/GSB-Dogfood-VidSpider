import scrapy
import re
import requests
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["instagram.com", "fbcdn.net", "cdninstagram.com"]
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

    def clean_video_url(self, url):
        """Remove bytestart/byteend parameters to get full video URL"""
        parsed = urlsplit(url)
        query_params = parse_qs(parsed.query)
        
        params_to_remove = ['bytestart', 'byteend']
        for param in params_to_remove:
            if param in query_params:
                del query_params[param]
        
        new_query = urlencode(query_params, doseq=True)
        cleaned_url = urlunsplit((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            new_query,
            parsed.fragment
        ))
        return cleaned_url

    def parse(self, response):
        video_urls = response.meta.get('video_urls', [])

        if not video_urls:
            self.logger.warning('No video URLs captured from network, trying regex...')
            patterns = [
                r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*',
                r'https?://[^\s"\'<>]*cdninstagram[^\s"\'<>]*\.mp4[^\s"\'<>]*',
                r'https?://[^\s"\'<>]*fbcdn[^\s"\'<>]*\.mp4[^\s"\'<>]*',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if 'blob:' not in match and match not in video_urls:
                        video_urls.append(match)

        self.logger.info(f'Total video URLs found: {len(video_urls)}')

        cleaned_urls = {}
        for url in video_urls:
            cleaned = self.clean_video_url(url)
            if cleaned not in cleaned_urls:
                cleaned_urls[cleaned] = url

        valid_videos = []
        for cleaned_url, original_url in cleaned_urls.items():
            try:
                head = requests.head(
                    cleaned_url,
                    timeout=10,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.instagram.com/',
                    }
                )

                content_type = head.headers.get('content-type', '')
                content_length = int(head.headers.get('content-length', 0))

                if 'video' in content_type and content_length > 100000:
                    valid_videos.append((cleaned_url, content_length))
                    self.logger.info(f'Valid video: {content_length/1024/1024:.2f} MB - {cleaned_url[:100]}...')

            except Exception as e:
                self.logger.debug(f'Error checking {cleaned_url[:50]}: {str(e)}')

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
