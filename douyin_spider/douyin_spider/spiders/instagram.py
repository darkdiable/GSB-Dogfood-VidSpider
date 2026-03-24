import scrapy
import re
import requests
import json

class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["instagram.com", "cdninstagram.com", "fbcdn.net"]
    start_urls = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
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

    def start_requests(self):
        for url in self.start_urls:
            shortcode = self._extract_shortcode(url)
            if shortcode:
                embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
                yield scrapy.Request(
                    embed_url,
                    callback=self.parse_embed,
                    meta={'original_url': url, 'shortcode': shortcode}
                )
            else:
                yield scrapy.Request(url, callback=self.parse, meta={'original_url': url})

    def _extract_shortcode(self, url):
        patterns = [
            r'instagram\.com/(?:reel|p|tv)/([^/?]+)',
            r'instagram\.com/(?:reel|p|tv)/([^/]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def parse_embed(self, response):
        shortcode = response.meta.get('shortcode', '')
        original_url = response.meta.get('original_url', '')
        
        video_urls = []
        
        video_elements = response.css('video::attr(src)').getall()
        video_urls.extend(video_elements)
        
        source_elements = response.css('source::attr(src)').getall()
        video_urls.extend(source_elements)
        
        page_content = response.text
        
        mp4_pattern = r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*'
        matches = re.findall(mp4_pattern, page_content)
        video_urls.extend(matches)
        
        json_patterns = [
            r'"video_url":"([^"]+)"',
            r'"url":"(https?://[^"]*\.mp4[^"]*)"',
            r'"playable_url":"([^"]+)"',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                clean_url = match.replace('\\u002F', '/').replace('\\/', '/')
                if clean_url and clean_url not in video_urls:
                    video_urls.append(clean_url)
        
        if not video_urls:
            api_url = f"https://i.instagram.com/api/v1/media/{shortcode}/info/"
            yield scrapy.Request(
                api_url,
                callback=self.parse_api,
                meta={'original_url': original_url, 'shortcode': shortcode},
                headers={
                    'User-Agent': 'Instagram 219.0.0.12.117 (iPhone; iOS 16.0; en_US; iPhone14,2; scale/3.00; 1080x1920; 447317382)',
                    'X-IG-App-ID': '936619743392459',
                }
            )
            return
        
        self.logger.info(f'Found {len(video_urls)} video URLs from embed page')
        
        valid_videos = self._validate_videos(video_urls, response)
        
        if valid_videos:
            best_url, best_size = valid_videos[0]
            title = f'instagram_{shortcode}'
            self.logger.info(f'Selected best video: {best_size/1024/1024:.2f} MB')
            
            yield {
                'video_url': best_url,
                'title': title,
                'size_mb': round(best_size / 1024 / 1024, 2),
                'video_urls': [url for url, _ in valid_videos]
            }
        else:
            yield scrapy.Request(
                original_url,
                callback=self.parse,
                meta={'original_url': original_url}
            )

    def parse_api(self, response):
        original_url = response.meta.get('original_url', '')
        
        try:
            data = json.loads(response.text)
            video_urls = self._extract_video_urls_from_json(data)
            
            self.logger.info(f'Found {len(video_urls)} video URLs from API')
            
            valid_videos = self._validate_videos(video_urls, response)
            
            if valid_videos:
                best_url, best_size = valid_videos[0]
                title = 'instagram_video'
                self.logger.info(f'Selected best video: {best_size/1024/1024:.2f} MB')
                
                yield {
                    'video_url': best_url,
                    'title': title,
                    'size_mb': round(best_size / 1024 / 1024, 2),
                    'video_urls': [url for url, _ in valid_videos]
                }
            else:
                self.logger.error('No valid video files found from API')
        except Exception as e:
            self.logger.error(f'API parse error: {e}')
            yield scrapy.Request(
                original_url,
                callback=self.parse,
                meta={'original_url': original_url}
            )

    def parse(self, response):
        video_urls = response.meta.get('video_urls', [])
        
        page_content = response.text
        
        json_patterns = [
            r'"video_url":"([^"]+)"',
            r'"url":"(https?://[^"]*\.mp4[^"]*)"',
            r'"playable_url":"([^"]+)"',
            r'"download_url":"([^"]+)"',
            r'"src":"(https?://[^"]*cdninstagram[^"]*\.mp4[^"]*)"',
            r'"src":"(https?://[^"]*fbcdn[^"]*\.mp4[^"]*)"',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                clean_url = match.replace('\\u002F', '/').replace('\\/', '/')
                if clean_url and 'blob:' not in clean_url and clean_url not in video_urls:
                    self.logger.info(f'Found video URL from pattern: {clean_url[:100]}...')
                    video_urls.append(clean_url)
        
        script_data_pattern = r'<script type="application/ld\+json">([^<]+)</script>'
        script_matches = re.findall(script_data_pattern, page_content)
        for script in script_matches:
            try:
                data = json.loads(script)
                if isinstance(data, dict):
                    for key in ['video', 'contentUrl', 'embedUrl']:
                        if key in data:
                            url = data[key]
                            if isinstance(url, str) and url not in video_urls:
                                video_urls.append(url)
                                self.logger.info(f'Found video URL from JSON-LD: {url[:100]}...')
            except:
                pass
        
        shared_data_pattern = r'window\._sharedData\s*=\s*({.+?});</script>'
        shared_matches = re.findall(shared_data_pattern, page_content)
        for shared in shared_matches:
            try:
                data = json.loads(shared)
                video_urls.extend(self._extract_video_urls_from_json(data))
            except:
                pass
        
        additional_data_pattern = r'window\.__additionalDataLoaded\s*\([^,]+,\s*({.+?})\);</script>'
        additional_matches = re.findall(additional_data_pattern, page_content)
        for additional in additional_matches:
            try:
                data = json.loads(additional)
                video_urls.extend(self._extract_video_urls_from_json(data))
            except:
                pass
        
        if not video_urls:
            self.logger.warning('No video URLs captured from network, trying regex...')
            patterns = [
                r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, page_content)
                for match in matches:
                    if 'blob:' not in match and match not in video_urls:
                        video_urls.append(match.replace('\\u002F', '/'))
        
        self.logger.info(f'Total video URLs found: {len(video_urls)}')
        
        valid_videos = self._validate_videos(video_urls, response)
        
        if valid_videos:
            best_url, best_size = valid_videos[0]
            
            title = 'instagram_video'
            og_title = response.xpath('//meta[@property="og:title"]/@content').get()
            if og_title:
                title = og_title
            else:
                meta_title = response.xpath('//title/text()').get()
                if meta_title:
                    title = meta_title.strip()
            
            self.logger.info(f'Selected best video: {best_size/1024/1024:.2f} MB')
            
            yield {
                'video_url': best_url,
                'title': title,
                'size_mb': round(best_size / 1024 / 1024, 2),
                'video_urls': [url for url, _ in valid_videos]
            }
        else:
            self.logger.error('No valid video files found')
    
    def _validate_videos(self, video_urls, response):
        valid_videos = []
        for video_url in video_urls:
            try:
                clean_url = video_url.split('?')[0] if '?' in video_url else video_url
                head = requests.head(
                    video_url,
                    timeout=10,
                    allow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.instagram.com/',
                    }
                )
                
                content_type = head.headers.get('content-type', '')
                content_length = int(head.headers.get('content-length', 0))
                
                if 'video' in content_type and content_length > 100000:
                    valid_videos.append((video_url, content_length))
                    self.logger.info(f'Valid video: {content_length/1024/1024:.2f} MB - {video_url[:100]}...')
                    
            except Exception as e:
                self.logger.debug(f'Error checking {video_url[:50]}: {str(e)}')
        
        valid_videos.sort(key=lambda x: x[1], reverse=True)
        return valid_videos
    
    def _extract_video_urls_from_json(self, data, depth=0):
        if depth > 10:
            return []
        
        urls = []
        if isinstance(data, dict):
            video_keys = ['video_url', 'url', 'playable_url', 'download_url', 'src', 'contentUrl']
            for key in video_keys:
                if key in data:
                    url = data[key]
                    if isinstance(url, str) and ('.mp4' in url or 'cdninstagram' in url or 'fbcdn' in url):
                        clean_url = url.replace('\\u002F', '/').replace('\\/', '/')
                        if clean_url not in urls:
                            urls.append(clean_url)
            
            for value in data.values():
                urls.extend(self._extract_video_urls_from_json(value, depth + 1))
        
        elif isinstance(data, list):
            for item in data:
                urls.extend(self._extract_video_urls_from_json(item, depth + 1))
        
        return urls
