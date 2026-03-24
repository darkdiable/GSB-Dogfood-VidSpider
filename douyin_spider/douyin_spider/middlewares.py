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

class YoutubePlaywrightMiddleware:
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
        if spider.name == 'youtube':
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
            )
            await self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    async def spider_closed(self, spider):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def process_request(self, request, spider):
        if spider.name != 'youtube':
            return None

        self.video_urls = []
        video_info = {}
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            if ('googlevideo.com' in url or 'videoplayback' in url) and 'blob:' not in url:
                if url not in self.video_urls and len(url) > 50:
                    spider.logger.debug(f'Captured video URL: {url[:100]}...')
                    self.video_urls.append(url)

        page.on("response", handle_response)

        try:
            await page.goto(request.url, timeout=90000, wait_until='domcontentloaded')
            await asyncio.sleep(8)

            try:
                title_elem = await page.query_selector('h1.ytd-video-primary-info-renderer yt-formatted-string') or \
                            await page.query_selector('h1.title') or \
                            await page.query_selector('#title h1') or \
                            await page.query_selector('yt-formatted-string.ytd-watch-metadata')
                if title_elem:
                    video_info['title'] = await title_elem.inner_text()
            except:
                pass

            try:
                player_data = await page.evaluate('''() => {
                    try {
                        const scripts = document.querySelectorAll('script');
                        for (let script of scripts) {
                            const text = script.textContent;
                            if (text && text.includes('ytInitialPlayerResponse')) {
                                const match = text.match(/ytInitialPlayerResponse\\s*=\\s*(\\{.+?\\});/s);
                                if (match) {
                                    return JSON.parse(match[1]);
                                }
                            }
                        }
                    } catch (e) {}
                    return null;
                }''')
                
                if player_data:
                    spider.logger.info('Found ytInitialPlayerResponse')
                    streaming_data = player_data.get('streamingData', {})
                    formats = streaming_data.get('formats', [])
                    adaptive_formats = streaming_data.get('adaptiveFormats', [])
                    
                    all_formats = formats + adaptive_formats
                    video_formats = [f for f in all_formats if f.get('mimeType', '').startswith('video/') and f.get('url')]
                    
                    if video_formats:
                        video_formats.sort(key=lambda x: int(x.get('contentLength', 0)) if x.get('contentLength') else 0, reverse=True)
                        best_format = video_formats[0]
                        video_url = best_format.get('url')
                        if video_url:
                            spider.logger.info(f'Found video URL from player response: {best_format.get("qualityLabel", "unknown")}')
                            video_info['url'] = video_url
                            video_info['title'] = player_data.get('videoDetails', {}).get('title', video_info.get('title', 'youtube_video'))
                            if video_url not in self.video_urls:
                                self.video_urls.insert(0, video_url)
            except Exception as e:
                spider.logger.debug(f'Error extracting player response: {str(e)}')

            try:
                await page.evaluate('''() => {
                    const video = document.querySelector('video');
                    if (video) {
                        video.muted = true;
                        video.currentTime = 0;
                        video.play().catch(() => {});
                    }
                }''')
                await asyncio.sleep(10)
            except:
                pass

            try:
                video_url = await page.evaluate('''() => {
                    const video = document.querySelector('video');
                    if (video && video.src && !video.src.startsWith('blob:')) {
                        return video.src;
                    }
                    return null;
                }''')
                if video_url and video_url not in self.video_urls:
                    spider.logger.info(f'Found video element src: {video_url[:100]}...')
                    self.video_urls.insert(0, video_url)
                    if 'url' not in video_info:
                        video_info['url'] = video_url
            except Exception as e:
                spider.logger.debug(f'Error getting video element: {str(e)}')

            content = await page.content()

            response = HtmlResponse(
                page.url,
                status=200,
                body=content.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            response.meta['video_urls'] = self.video_urls.copy()
            response.meta['video_info'] = video_info
            response.meta['original_url'] = request.url
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
            response.meta['original_url'] = request.url
            response.meta['video_info'] = video_info
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
        if spider.name != 'instagram':
            return None

        self.video_urls = []
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            if (('.mp4' in url or '.m3u8' in url or '.mpd' in url or '/dash/' in url or '/hls/' in url or 'cdninstagram' in url or 'fbcdn' in url or 'fna.fbcdn.net' in url) 
                and 'blob:' not in url 
                and url not in self.video_urls
                and len(url) > 50
                and '.jpg' not in url
                and '.jpeg' not in url
                and '.png' not in url
                and '.gif' not in url):
                spider.logger.debug(f'Captured potential video URL: {url[:100]}...')
                self.video_urls.append(url)

        page.on("response", handle_response)

        try:
            await page.goto(request.url, timeout=60000, wait_until='domcontentloaded')
            await asyncio.sleep(8)

            try:
                play_button = await page.query_selector('button[aria-label*="Play"]') or \
                             await page.query_selector('div[role*="button"]') or \
                             await page.query_selector('video')
                if play_button:
                    await play_button.click(force=True)
                    await asyncio.sleep(5)
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
