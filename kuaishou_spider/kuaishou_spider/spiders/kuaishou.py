import scrapy
import re
import requests
import json
import urllib.parse


class KuaishouSpider(scrapy.Spider):
    name = "kuaishou"
    allowed_domains = ["kuaishou.com", "kuaishouapp.com", "v.kuaishou.com", "chenzhongtech.com"]
    start_urls = []

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.kuaishou.com/',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'kuaishou_spider.middlewares.KuaishouPlaywrightMiddleware': 543,
        },
        'DOWNLOAD_TIMEOUT': 120,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(KuaishouSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def parse(self, response):
        video_urls = response.meta.get('video_urls', [])
        self.logger.info(f'Captured video URLs from network: {len(video_urls)}')
        for url in video_urls[:5]:
            self.logger.info(f'  - {url[:100]}...')

        title = 'kuaishou_video'
        author = ''

        og_title = response.xpath('//meta[@property="og:title"]/@content').get()
        if og_title:
            title = og_title
            self.logger.info(f'Found title from og:title: {title}')

        json_pattern = r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.*?})</script>'
        json_match = re.search(json_pattern, response.text, re.DOTALL)

        if json_match:
            try:
                json_str = json_match.group(1)
                initial_state = json.loads(json_str)
                self.logger.info('Successfully parsed __INITIAL_STATE__')

                if 'video' in initial_state:
                    video_data = initial_state['video']
                    title = video_data.get('caption', '') or video_data.get('title', '') or title
                    author = video_data.get('author', {}).get('name', '')
                    self.logger.info(f'Video info - title: {title}, author: {author}')

                    for key in ['photoUrl', 'videoUrl', 'srcUrl', 'url', 'playUrl', 'mainUrl']:
                        if key in video_data and video_data[key]:
                            url = video_data[key]
                            if isinstance(url, str) and url not in video_urls:
                                video_urls.append(url)
                                self.logger.info(f'Found video URL from {key}: {url[:80]}...')

                if 'photo' in initial_state:
                    photo_data = initial_state['photo']
                    for key in ['photoUrl', 'videoUrl', 'srcUrl', 'url', 'playUrl', 'mainUrl']:
                        if key in photo_data and photo_data[key]:
                            url = photo_data[key]
                            if isinstance(url, str) and url not in video_urls:
                                video_urls.append(url)
                                self.logger.info(f'Found video URL from photo.{key}: {url[:80]}...')

            except Exception as e:
                self.logger.debug(f'Failed to parse JSON: {str(e)}')

        if not video_urls:
            self.logger.warning('No video URLs captured, trying regex patterns...')
            patterns = [
                r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)',
                r'(https?://[^\s"\'<>]*kuaishou[^\s"\'<>]*video[^\s"\'<>]*)',
                r'(https?://[^\s"\'<>]*kuaishou[^\s"\'<>]*\.mp4[^\s"\'<>]*)',
                r'(https?://[^\s"\'<>]*chenzhongtech[^\s"\'<>]*\.mp4[^\s"\'<>]*)',
                r'(https?://[^\s"\'<>]*kwaicdn[^\s"\'<>]*\.mp4[^\s"\'<>]*)',
                r'(https?://[^\s"\'<>]*kwai[^\s"\'<>]*\.mp4[^\s"\'<>]*)',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if 'blob:' not in match and match not in video_urls:
                        video_urls.append(match)
                        self.logger.info(f'Found video URL from regex: {match[:80]}...')

        self.logger.info(f'Total video URLs to check: {len(video_urls)}')

        valid_videos = []
        for video_url in video_urls:
            try:
                video_url = video_url.replace('\\u002F', '/').replace('\\/', '/')
                video_url = urllib.parse.unquote(video_url)

                self.logger.debug(f'Checking URL: {video_url[:80]}...')

                head = requests.head(
                    video_url,
                    timeout=15,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.kuaishou.com/',
                        'Accept': '*/*',
                    },
                    allow_redirects=True
                )

                content_type = head.headers.get('content-type', '').lower()
                content_length = head.headers.get('content-length', '0')

                try:
                    content_length = int(content_length)
                except:
                    content_length = 0

                self.logger.debug(f'URL check - type: {content_type}, size: {content_length}')

                is_video = 'video' in content_type or 'mp4' in content_type or 'octet-stream' in content_type

                if is_video and content_length > 50000:
                    valid_videos.append((video_url, content_length))
                    self.logger.info(f'Valid video: {content_length/1024/1024:.2f} MB - {video_url[:80]}...')

            except Exception as e:
                self.logger.debug(f'Error checking {video_url[:50]}: {str(e)}')

        if not valid_videos:
            self.logger.info('Trying GET requests for video URLs...')
            for video_url in video_urls[:10]:
                try:
                    video_url = video_url.replace('\\u002F', '/').replace('\\/', '/')
                    video_url = urllib.parse.unquote(video_url)

                    resp = requests.get(
                        video_url,
                        timeout=15,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Referer': 'https://www.kuaishou.com/',
                        },
                        stream=True
                    )

                    content_type = resp.headers.get('content-type', '').lower()
                    content_length = resp.headers.get('content-length', '0')

                    try:
                        content_length = int(content_length)
                    except:
                        content_length = len(resp.content) if resp.content else 0

                    is_video = 'video' in content_type or 'mp4' in content_type or 'octet-stream' in content_type

                    if is_video and content_length > 50000:
                        valid_videos.append((video_url, content_length))
                        self.logger.info(f'Valid video (GET): {content_length/1024/1024:.2f} MB')
                        break

                except Exception as e:
                    self.logger.debug(f'GET error: {str(e)}')

        if valid_videos:
            valid_videos.sort(key=lambda x: x[1], reverse=True)
            best_url, best_size = valid_videos[0]

            self.logger.info(f'Selected best video: {best_size/1024/1024:.2f} MB')

            yield {
                'video_url': best_url,
                'title': title,
                'author': author,
                'size_mb': round(best_size / 1024 / 1024, 2),
                'video_urls': [url for url, _ in valid_videos]
            }
        else:
            self.logger.error('No valid video files found')
