from scrapy import signals
from scrapy.http import HtmlResponse
import asyncio
from playwright.async_api import async_playwright

class KuaishouPlaywrightMiddleware:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.video_urls = []

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    async def spider_opened(self, spider):
        if spider.name == 'kuaishou':
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )

    async def spider_closed(self, spider):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def process_request(self, request, spider):
        if spider.name != 'kuaishou':
            return None

        self.video_urls = []
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            if ('.mp4' in url or 'video' in url.lower() or 'playUrl' in url or 'photoUrl' in url) and 'blob:' not in url:
                if url not in self.video_urls:
                    spider.logger.debug(f'Captured video URL: {url[:100]}...')
                    self.video_urls.append(url)
            
            if 'api' in url and ('photo' in url or 'video' in url):
                try:
                    json_data = response.json()
                    if isinstance(json_data, dict):
                        self._extract_video_urls(json_data, spider)
                except:
                    pass

        page.on("response", handle_response)

        try:
            await page.goto(request.url, timeout=60000, wait_until='domcontentloaded')
            await asyncio.sleep(5)

            try:
                play_button = await page.query_selector('button[class*="play"]') or \
                             await page.query_selector('div[class*="play"]') or \
                             await page.query_selector('video')
                if play_button:
                    await play_button.click(force=True)
                    await asyncio.sleep(3)
            except:
                pass

            content = await page.content()

            response = HtmlResponse(
                page.url,
                status=200,
                body=content.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            response.meta['video_urls'] = self.video_urls.copy()
            return response

        except Exception as e:
            import traceback
            error_msg = f'{str(e)}\n{traceback.format_exc()}'
            spider.logger.error(f'Playwright error: {error_msg}')
            response = HtmlResponse(
                request.url,
                status=200,
                body=b'',
                encoding='utf-8',
                request=request
            )
            response.meta['video_urls'] = self.video_urls.copy()
            return response
        finally:
            await page.close()

    def _extract_video_urls(self, data, spider):
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['playUrl', 'photoUrl', 'videoUrl', 'url'] and isinstance(value, str):
                    if value not in self.video_urls:
                        spider.logger.debug(f'Extracted video URL from JSON: {value[:100]}...')
                        self.video_urls.append(value)
                elif isinstance(value, (dict, list)):
                    self._extract_video_urls(value, spider)
        elif isinstance(data, list):
            for item in data:
                self._extract_video_urls(item, spider)
