from scrapy import signals
from scrapy.http import HtmlResponse
import asyncio
from playwright.async_api import async_playwright
import subprocess
import os

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
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/bilibiliOutput'
        os.makedirs(self.output_dir, exist_ok=True)

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

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'bilibili_video'

    def download_stream_sync(self, url, file_path, spider):
        """同步下载视频或音频流"""
        cmd = [
            'ffmpeg',
            '-headers', 'Referer: https://www.bilibili.com/\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n',
            '-i', url,
            '-c', 'copy',
            '-y',
            file_path
        ]

        spider.logger.info(f'Downloading stream to {file_path}...')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            spider.logger.error(f'FFmpeg download error: {result.stderr}')
            raise Exception(f'FFmpeg download failed: {result.stderr}')

        spider.logger.info(f'Stream downloaded successfully')

    def merge_streams_sync(self, video_path, audio_path, output_path, spider):
        """使用ffmpeg合并视频和音频流"""
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-c', 'copy',
            '-y',
            output_path
        ]

        spider.logger.info(f'Merging streams...')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            spider.logger.error(f'FFmpeg merge error: {result.stderr}')
            raise Exception(f'FFmpeg merge failed: {result.stderr}')

        spider.logger.info(f'Streams merged successfully')

    def remove_watermark_sync(self, input_path, output_path, spider):
        """使用ffmpeg去除左上角水印"""
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', 'delogo=x=10:y=10:w=150:h=80',
            '-c:a', 'copy',
            '-y',
            output_path
        ]

        spider.logger.info(f'Removing watermark...')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            spider.logger.error(f'FFmpeg watermark removal error: {result.stderr}')
            raise Exception(f'FFmpeg watermark removal failed: {result.stderr}')

        spider.logger.info(f'Watermark removed successfully')

    async def process_request(self, request, spider):
        if spider.name != 'bilibili':
            return None

        self.video_urls = []
        video_data = {}
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            if (('.m4s' in url or '.mp4' in url or 'mcdn.bilivideo.cn' in url or 'upos-sz-mirrorcos.bilivideo.cn' in url)
                and 'blob:' not in url
                and url not in self.video_urls
                and len(url) > 50):
                spider.logger.debug(f'Captured video URL: {url[:100]}...')
                self.video_urls.append(url)

            # 捕获playurl API响应
            if 'playurl' in url or 'x/player/wbi/playurl' in url:
                try:
                    spider.logger.info(f'Captured playurl API: {url[:100]}...')
                except:
                    pass

        page.on("response", handle_response)

        try:
            await page.goto(request.url, timeout=60000, wait_until='domcontentloaded')
            await asyncio.sleep(5)

            title = 'bilibili_video'
            try:
                title_elem = await page.query_selector('h1.video-title')
                if title_elem:
                    title = await title_elem.inner_text()
                else:
                    title_elem = await page.query_selector('h1.title')
                    if title_elem:
                        title = await title_elem.inner_text()
            except:
                pass

            # 尝试从页面获取视频信息
            try:
                video_info = await page.evaluate('''() => {
                    if (window.__playinfo__) {
                        return window.__playinfo__;
                    }
                    return null;
                }''')
                if video_info:
                    spider.logger.info('Found __playinfo__ in window object')
                    video_data = video_info.get('data', {})
            except Exception as e:
                spider.logger.debug(f'Error getting __playinfo__: {e}')

            # 如果上面没获取到，尝试其他方式
            if not video_data:
                try:
                    video_info = await page.evaluate('''() => {
                        const scripts = document.querySelectorAll('script');
                        for (const script of scripts) {
                            const text = script.textContent;
                            if (text.includes('__playinfo__')) {
                                const match = text.match(/window\.__playinfo__\s*=\s*({.+?});/);
                                if (match) {
                                    return JSON.parse(match[1]);
                                }
                            }
                        }
                        return null;
                    }''')
                    if video_info:
                        spider.logger.info('Found __playinfo__ in script tag')
                        video_data = video_info.get('data', {})
                except Exception as e:
                    spider.logger.debug(f'Error parsing __playinfo__: {e}')

            try:
                play_button = await page.query_selector('button.bpx-player-ctrl-play') or \
                             await page.query_selector('.bilibili-player-video-btn-start') or \
                             await page.query_selector('video')
                if play_button:
                    await play_button.click(force=True)
                    await asyncio.sleep(5)
            except:
                pass

            content = await page.content()

            # 立即下载视频（因为URL会过期）
            file_path = None
            if video_data and 'dash' in video_data:
                dash_data = video_data['dash']
                video_list = dash_data.get('video', [])
                audio_list = dash_data.get('audio', [])

                video_url = None
                audio_url = None

                if video_list:
                    best_video = max(video_list, key=lambda x: x.get('id', 0))
                    video_url = best_video.get('baseUrl') or best_video.get('base_url')
                    spider.logger.info(f'Selected video quality: {best_video.get("id")}')

                if audio_list:
                    best_audio = max(audio_list, key=lambda x: x.get('id', 0))
                    audio_url = best_audio.get('baseUrl') or best_audio.get('base_url')
                    spider.logger.info(f'Selected audio quality: {best_audio.get("id")}')

                if video_url:
                    title = self.sanitize_filename(title)
                    file_path = os.path.join(self.output_dir, f'{title}.mp4')

                    counter = 1
                    while os.path.exists(file_path):
                        file_path = os.path.join(self.output_dir, f'{title}_{counter}.mp4')
                        counter += 1

                    try:
                        if audio_url:
                            video_temp = os.path.join(self.output_dir, f'{title}_video_temp.mp4')
                            audio_temp = os.path.join(self.output_dir, f'{title}_audio_temp.mp4')

                            await asyncio.get_event_loop().run_in_executor(
                                None, self.download_stream_sync, video_url, video_temp, spider
                            )
                            await asyncio.get_event_loop().run_in_executor(
                                None, self.download_stream_sync, audio_url, audio_temp, spider
                            )
                            await asyncio.get_event_loop().run_in_executor(
                                None, self.merge_streams_sync, video_temp, audio_temp, file_path, spider
                            )

                            os.remove(video_temp)
                            os.remove(audio_temp)
                        else:
                            await asyncio.get_event_loop().run_in_executor(
                                None, self.download_stream_sync, video_url, file_path, spider
                            )

                        # 去除水印
                        watermark_removed_path = os.path.join(self.output_dir, f'{title}_no_watermark.mp4')
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.remove_watermark_sync, file_path, watermark_removed_path, spider
                        )

                        # 替换原文件
                        os.remove(file_path)
                        os.rename(watermark_removed_path, file_path)

                        final_size = os.path.getsize(file_path)
                        spider.logger.info(f'Video saved to: {file_path} ({final_size/1024/1024:.2f} MB)')

                    except Exception as e:
                        spider.logger.error(f'Failed to download video: {str(e)}')
                        file_path = None

            response = HtmlResponse(
                page.url,
                status=200,
                body=content.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            response.meta['video_urls'] = self.video_urls.copy()
            response.meta['title'] = title
            response.meta['video_data'] = video_data
            response.meta['file_path'] = file_path
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
            response.meta['title'] = title
            response.meta['video_data'] = video_data
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
        self.video_urls = []
        page = await self.context.new_page()

        def handle_response(response):
            url = response.url
            if (('.mp4' in url or '.m3u8' in url or 'video' in url.lower()) 
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
                             await page.query_selector('div[class*="video"]') or \
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
