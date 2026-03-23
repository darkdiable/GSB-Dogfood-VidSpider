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
        if spider.name in ['kuaishou']:
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
        if spider.name not in ['kuaishou']:
            return None

        self.video_urls = []
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            content_type = response.headers.get('content-type', '').lower()

            is_video = (
                '.mp4' in url.lower() or
                'video' in content_type or
                'mp4' in content_type or
                'octet-stream' in content_type or
                'kwaicdn' in url.lower() or
                'oskwai' in url.lower() or
                'chenzhongtech' in url.lower()
            )

            if is_video and 'blob:' not in url and 'css' not in url and 'js' not in url and '.html' not in url:
                if url not in self.video_urls:
                    spider.logger.info(f'Captured video URL: {url[:100]}...')
                    self.video_urls.append(url)

        page.on("response", handle_response)

        try:
            spider.logger.info(f'Navigating to: {request.url}')
            await page.goto(request.url, timeout=60000, wait_until='networkidle')
            await asyncio.sleep(2)

            for _ in range(3):
                try:
                    video_src = await page.evaluate('''() => {
                        const videos = document.querySelectorAll('video');
                        for (const v of videos) {
                            if (v.src && v.src.startsWith('http') && v.src.includes('.mp4')) {
                                return v.src;
                            }
                            const sources = v.querySelectorAll('source');
                            for (const s of sources) {
                                if (s.src && s.src.startsWith('http')) {
                                    return s.src;
                                }
                            }
                        }
                        const scripts = document.querySelectorAll('script');
                        for (const script of scripts) {
                            const text = script.textContent || '';
                            const match = text.match(/(https?:\\/\\/[^\s"'<>]+\.mp4[^\s"'<>]*)/);
                            if (match) return match[1].replace(/\\/g, '/');
                        }
                        return null;
                    }''')

                    if video_src and video_src not in self.video_urls:
                        spider.logger.info(f'Captured video from page: {video_src[:100]}...')
                        self.video_urls.append(video_src)
                        break
                except Exception as e:
                    spider.logger.debug(f'Error extracting video: {e}')

                try:
                    play_selectors = [
                        'button[class*="play"]',
                        'div[class*="play-icon"]',
                        '[class*="play-button"]',
                        'video',
                        '[class*="video-container"]',
                        '.video-player',
                        '[data-e2e*="video"]',
                        '.video',
                        '[class*="player"]'
                    ]
                    
                    for selector in play_selectors:
                        play_button = await page.query_selector(selector)
                        if play_button:
                            spider.logger.info(f'Clicking element: {selector}')
                            await play_button.click(force=True)
                            await asyncio.sleep(3)
                            break
                except Exception as e:
                    spider.logger.debug(f'Click error: {e}')

                await asyncio.sleep(2)

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
