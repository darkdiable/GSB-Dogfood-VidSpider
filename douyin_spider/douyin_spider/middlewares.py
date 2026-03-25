from scrapy import signals
from scrapy.http import HtmlResponse
import asyncio
from playwright.async_api import async_playwright
import re
import json

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

class BilibiliPlaywrightMiddleware:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.video_urls = []
        self.audio_urls = []

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    async def spider_opened(self, spider):
        if spider.name == 'bilibili':
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
        if spider.name != 'bilibili':
            return None

        self.video_urls = []
        self.audio_urls = []
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            try:
                if '.m4s' in url or '.mp4' in url:
                    if '30280' in url or '30232' in url or '30216' in url:
                        if '30280' in url or '30232' in url:
                            if url not in self.audio_urls:
                                spider.logger.debug(f'Captured audio URL: {url[:100]}...')
                                self.audio_urls.append(url)
                        elif '30216' in url:
                            if url not in self.video_urls and 'blob:' not in url:
                                spider.logger.debug(f'Captured video URL: {url[:100]}...')
                                self.video_urls.append(url)
                    elif url not in self.video_urls and 'blob:' not in url:
                        spider.logger.debug(f'Captured other video URL: {url[:100]}...')
                        self.video_urls.append(url)
            except:
                pass

        page.on("response", handle_response)

        try:
            await page.goto(request.url, timeout=60000, wait_until='domcontentloaded')
            await asyncio.sleep(8)

            try:
                play_button = await page.query_selector('button[class*="play"]') or \
                             await page.query_selector('div[class*="bpx-player-ctrl-play"]') or \
                             await page.query_selector('.bpx-player-ctrl-btn')
                if play_button:
                    await play_button.click(force=True)
                    await asyncio.sleep(5)
            except:
                pass

            content = await page.content()

            playinfo_match = re.search(r'window\.__playinfo__\s*=\s*(\{.+?\})\s*</script>', content, re.DOTALL)
            if playinfo_match:
                try:
                    playinfo_json = playinfo_match.group(1)
                    playinfo_data = json.loads(playinfo_json)
                    
                    if 'data' in playinfo_data and 'dash' in playinfo_data['data']:
                        dash = playinfo_data['data']['dash']
                        
                        if 'video' in dash:
                            for video in dash['video']:
                                if 'baseUrl' in video:
                                    video_url = video['baseUrl']
                                    if video_url not in self.video_urls:
                                        self.video_urls.append(video_url)
                                        spider.logger.info(f'Extracted video URL from playinfo: {video_url[:80]}...')
                        
                        if 'audio' in dash:
                            for audio in dash['audio']:
                                if 'baseUrl' in audio:
                                    audio_url = audio['baseUrl']
                                    if audio_url not in self.audio_urls:
                                        self.audio_urls.append(audio_url)
                                        spider.logger.info(f'Extracted audio URL from playinfo: {audio_url[:80]}...')
                except Exception as e:
                    spider.logger.warning(f'Failed to parse playinfo: {str(e)}')

            if not self.video_urls:
                scripts = await page.query_selector_all('script')
                for script in scripts:
                    try:
                        script_content = await script.inner_text()
                        if 'playurl' in script_content.lower() or 'video_url' in script_content.lower() or 'baseUrl' in script_content:
                            video_matches = re.findall(r'"baseUrl"\s*:\s*"(https?://[^"]+\.m4s[^"]*)"', script_content)
                            for match in video_matches:
                                if match not in self.video_urls and match not in self.audio_urls:
                                    if '30280' in match or '30232' in match:
                                        self.audio_urls.append(match)
                                    else:
                                        self.video_urls.append(match)
                    except:
                        pass

            response = HtmlResponse(
                page.url,
                status=200,
                body=content.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            response.meta['video_urls'] = self.video_urls.copy()
            response.meta['audio_urls'] = self.audio_urls.copy()
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
            response.meta['audio_urls'] = self.audio_urls.copy()
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
