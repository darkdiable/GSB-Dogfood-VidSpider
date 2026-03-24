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
            if (('.mp4' in url or '.m3u8' in url or '/mv/' in url or '/play/' in url) 
                and 'blob:' not in url 
                and url not in self.video_urls
                and len(url) > 50):
                spider.logger.debug(f'Captured video URL: {url[:100]}...')
                self.video_urls.append(url)

        page.on("response", handle_response)

        try:
            await page.goto(request.url, timeout=60000, wait_until='domcontentloaded')
            await asyncio.sleep(5)

            try:
                play_button = await page.query_selector('button[class*="play"]') or \
                             await page.query_selector('div[class*="play-btn"]') or \
                             await page.query_selector('div[class*="video"]')
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

class InstagramPlaywrightMiddleware:
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
        if spider.name == 'instagram':
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                viewport={'width': 390, 'height': 844}
            )

    async def spider_closed(self, spider):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def process_request(self, request, spider):
        if spider.name != 'instagram':
            return None

        self.video_urls = []
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            content_type = response.headers.get('content-type', '')
            if ('video' in content_type.lower() or 
                '.mp4' in url or 
                'cdninstagram' in url and ('.mp4' in url or 'video' in url.lower()) or
                'fbcdn' in url and '.mp4' in url):
                if 'blob:' not in url and url not in self.video_urls:
                    spider.logger.info(f'Captured video URL: {url[:150]}...')
                    self.video_urls.append(url)

        page.on("response", handle_response)

        try:
            await page.goto(request.url, timeout=90000, wait_until='networkidle')
            await asyncio.sleep(10)

            try:
                video_element = await page.query_selector('video')
                if video_element:
                    src = await video_element.get_attribute('src')
                    if src and src not in self.video_urls:
                        spider.logger.info(f'Found video src: {src[:150]}...')
                        self.video_urls.append(src)
            except Exception as e:
                spider.logger.debug(f'Error getting video src: {e}')

            try:
                play_selectors = [
                    'div[role="button"]',
                    'button[type="button"]',
                    'article div',
                    'video',
                ]
                for selector in play_selectors:
                    elements = await page.query_selector_all(selector)
                    for elem in elements[:3]:
                        try:
                            await elem.click(force=True)
                            await asyncio.sleep(1)
                        except:
                            pass
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

class PlaywrightMiddleware:
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
        if spider.name in ['douyin_playwright', 'douyin']:
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
        if spider.name not in ['douyin_playwright', 'douyin']:
            return None

        self.video_urls = []
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            if ('.mp4' in url or 'video' in url.lower()) and 'blob:' not in url and 'byted-static' not in url:
                if url not in self.video_urls:
                    spider.logger.debug(f'Captured video URL: {url[:100]}...')
                    self.video_urls.append(url)

        page.on("response", handle_response)

        try:
            await page.goto(request.url, timeout=60000, wait_until='domcontentloaded')
            await asyncio.sleep(5)

            try:
                play_button = await page.query_selector('button[data-e2e="feed-play"]') or \
                             await page.query_selector('div[class*="play"]') or \
                             await page.query_selector('xg-icon[class*="play"]')
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
