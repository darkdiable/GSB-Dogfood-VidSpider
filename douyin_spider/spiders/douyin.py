import re
import json
import scrapy
from urllib.parse import unquote
from douyin_spider.items import DouyinVideoItem


class DouyinSpider(scrapy.Spider):
    name = 'douyin'
    allowed_domains = ['douyin.com', 'v.douyin.com', 'iesdouyin.com']
    
    custom_settings = {
        'REDIRECT_ENABLED': True,
        'REDIRECT_MAX_TIMES': 10,
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
    }
    
    def __init__(self, url=None, *args, **kwargs):
        super(DouyinSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_with_playwright,
                dont_filter=True,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_goto_kwargs': {
                        'wait_until': 'domcontentloaded',
                        'timeout': 60000,
                    },
                }
            )
    
    async def parse_with_playwright(self, response):
        page = response.meta.get('playwright_page')
        if page:
            final_url = page.url
            html = response.text
            video_urls = []
            
            try:
                video_elements = await page.query_selector_all('video')
                for video in video_elements:
                    src = await video.get_attribute('src')
                    if src and src not in video_urls:
                        src_lower = src.lower()
                        if 'douyinstatic.com' not in src_lower and 'byteeffecttos.com' not in src_lower:
                            video_urls.append(src)
                            self.logger.info(f'Found video element src: {src[:80]}...')
            except Exception as e:
                self.logger.error(f'Error getting video elements: {e}')
            
            video_id = self.extract_video_id(final_url)
            self.logger.info(f'Final URL: {final_url}')
            self.logger.info(f'Video ID: {video_id}')
            
            video_info = self.get_video_info_from_html(html, video_urls)
            
            if video_info:
                item = DouyinVideoItem()
                item['video_id'] = video_id or ''
                item['video_title'] = video_info.get('title', 'douyin_video')
                item['author'] = video_info.get('author', 'unknown')
                item['video_url'] = video_info.get('video_url')
                yield item
            else:
                self.logger.error('Failed to get video info')
            
            await page.close()
    
    def extract_video_id(self, url):
        patterns = [
            r'/video/(\d+)',
            r'modal_id=(\d+)',
            r'aweme_id=(\d+)',
            r'/(\d{19})/',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info_from_html(self, html, video_urls):
        if video_urls:
            return {'video_url': video_urls[0], 'title': 'douyin_video', 'author': 'unknown'}
        
        patterns = [
            r'window\._ROUTER_DATA\s*=\s*({.+?})\s*</script>',
            r'<script\s+id="RENDER_DATA"\s+type="application/json">([^<]+)</script>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                data_str = match.group(1)
                try:
                    data_str = unquote(data_str)
                except:
                    pass
                try:
                    data = json.loads(data_str)
                    video_info = self.find_video_info(data)
                    if video_info:
                        return video_info
                except json.JSONDecodeError as e:
                    self.logger.error(f'JSON decode error: {e}')
                    continue
        
        video_url_patterns = [
            (r'"playAddr"\s*:\s*\[\s*\{\s*"src"\s*:\s*"([^"]+)"', False),
            (r'"play_addr"\s*:\s*\{\s*"url_list"\s*:\s*\[\s*"([^"]+)"', False),
            (r'"playApi"\s*:\s*"([^"]+)"', False),
            (r'"src"\s*:\s*"(https?://[^"]*v[^"]*\.douyinvod\.com[^"]*)"', False),
            (r'"src"\s*:\s*"(//[^"]*v[^"]*\.douyinvod\.com[^"]*)"', True),
            (r'(https?://[^"\s]*\.douyinvod\.com/[^"\s]+\.mp4[^"\s]*)', False),
            (r'(https?://[^"\s]*zjcdn\.com/[^"\s]+/video/[^"\s]+)', False),
        ]
        
        for pattern, add_https in video_url_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                video_url = match.group(1)
                if add_https and video_url.startswith('//'):
                    video_url = 'https:' + video_url
                self.logger.info(f'Found video URL via pattern: {video_url[:80]}...')
                return {'video_url': video_url, 'title': 'douyin_video', 'author': 'unknown'}
        
        self.logger.error('No video URL found in HTML')
        return None
    
    def find_video_info(self, data, depth=0):
        if depth > 15:
            return None
        
        if isinstance(data, dict):
            if 'video' in data and isinstance(data['video'], dict):
                video = data['video']
                play_addr = video.get('play_addr', {})
                if isinstance(play_addr, dict):
                    url_list = play_addr.get('url_list', [])
                    if url_list:
                        video_url = url_list[0]
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        title = data.get('desc', 'douyin_video')
                        author = data.get('author', {}).get('nickname', 'unknown')
                        return {'video_url': video_url, 'title': title, 'author': author}
            
            if 'aweme' in data and isinstance(data['aweme'], dict):
                return self.find_video_info(data['aweme'], depth + 1)
            
            if 'aweme_detail' in data and isinstance(data['aweme_detail'], dict):
                return self.find_video_info(data['aweme_detail'], depth + 1)
            
            for key in ['detail', 'videoInfo', 'video_data', 'itemInfo']:
                if key in data and isinstance(data[key], dict):
                    result = self.find_video_info(data[key], depth + 1)
                    if result:
                        return result
            
            for value in data.values():
                if isinstance(value, dict):
                    result = self.find_video_info(value, depth + 1)
                    if result:
                        return result
        
        return None
