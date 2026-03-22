import scrapy
import re
import json
import os
import urllib.parse
from scrapy.http import Request


class DouyinSpider(scrapy.Spider):
    name = 'douyin'
    allowed_domains = ['douyin.com', 'iesdouyin.com']

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        },
        'MEDIA_ALLOW_REDIRECTS': True,
        'ROBOTSTXT_OBEY': False,
    }

    def __init__(self, url=None, **kwargs):
        super().__init__(**kwargs)
        self.start_url = url or 'https://v.douyin.com/06CE2EJQVPU/'
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/douyinOutput'
        os.makedirs(self.output_dir, exist_ok=True)

    def start_requests(self):
        yield Request(
            url=self.start_url,
            callback=self.parse_redirect,
            meta={'handle_httpstatus_list': [302, 301]},
            dont_filter=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1'
            }
        )

    def parse_redirect(self, response):
        if response.status in [301, 302]:
            real_url = response.headers.get('Location', b'').decode('utf-8')
            if real_url:
                self.logger.info(f"重定向到: {real_url}")
                yield Request(
                    url=real_url,
                    callback=self.parse_video_page,
                    dont_filter=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1',
                        'Referer': 'https://www.douyin.com/'
                    }
                )
        else:
            yield Request(
                url=response.url,
                callback=self.parse_video_page,
                dont_filter=True
            )

    def parse_video_page(self, response):
        video_id = self.extract_video_id(response.url)
        if not video_id:
            self.logger.error(f"无法从URL提取视频ID: {response.url}")
            return

        self.logger.info(f"提取到视频ID: {video_id}")

        router_data = self.extract_router_data(response.text)
        if router_data:
            self.logger.info("成功提取到 ROUTER_DATA")
            video_url, item_info = self.get_video_url_from_router(router_data)
            if video_url:
                self.logger.info(f"从ROUTER_DATA提取到视频URL: {video_url}")
                yield self.download_video(video_url, video_id, item_info)
                return

        video_url = self.extract_video_from_html(response.text)
        if video_url:
            yield self.download_video(video_url, video_id)
            return

        self.logger.error("无法从页面提取视频URL")

    def extract_router_data(self, html):
        pattern = r'<script[^>]*>window\._ROUTER_DATA\s*=\s*(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                data_str = match.group(1)
                data_str = data_str.replace('\\u002F', '/').replace('\\u0026', '&')
                return json.loads(data_str)
            except Exception as e:
                self.logger.warning(f"解析ROUTER_DATA失败: {e}")
        return None

    def get_video_url_from_router(self, router_data):
        try:
            if not isinstance(router_data, dict):
                return None, None

            loader_data = router_data.get('loaderData', {})
            video_page = loader_data.get('video_(id)/page', {})

            # 从 videoInfoRes -> item_list -> video -> play_addr 获取
            video_info_res = video_page.get('videoInfoRes', {})
            item_list = video_info_res.get('item_list', [])

            if item_list and len(item_list) > 0:
                item = item_list[0]
                video = item.get('video', {})

                # 获取play_addr
                play_addr = video.get('play_addr', {})
                url_list = play_addr.get('url_list', [])

                if url_list:
                    # 替换playwm为play获取无水印版本
                    video_url = url_list[0].replace('playwm', 'play')
                    return video_url, item

                # 尝试download_addr
                download_addr = video.get('download_addr', {})
                download_urls = download_addr.get('url_list', [])
                if download_urls:
                    return download_urls[0], item

        except Exception as e:
            self.logger.warning(f"从ROUTER_DATA提取视频URL失败: {e}")
        return None, None

    def extract_video_from_html(self, html):
        patterns = [
            r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*(.*?)</script>',
            r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*(.*?)</script>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data_str = match.group(1)
                    data_str = data_str.replace('undefined', 'null')
                    data = json.loads(data_str)

                    if isinstance(data, dict):
                        if 'app' in data and 'videoDetail' in data['app']:
                            video = data['app']['videoDetail'].get('video', {})
                            play_addr = video.get('playAddr', [])
                            if play_addr:
                                return play_addr[0] if isinstance(play_addr, list) else play_addr
                except:
                    continue

        video_patterns = [
            r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)',
            r'"playAddr":\s*"(https?://[^"]+)"',
            r'"play_addr":\s*\{[^}]*"url_list":\s*\["(https?://[^"]+)"',
        ]

        for pattern in video_patterns:
            match = re.search(pattern, html)
            if match:
                url = match.group(1)
                url = url.replace('\\u002F', '/').replace('\\/', '/')
                return url

        return None

    def download_video(self, video_url, video_id, item_info=None):
        if item_info:
            desc = item_info.get('desc', '')[:50]
            desc = re.sub(r'[^\w\s-]', '', desc).strip()
            filename = f"{video_id}_{desc}.mp4" if desc else f"{video_id}.mp4"
        else:
            filename = f"{video_id}.mp4"

        filepath = os.path.join(self.output_dir, filename)

        self.logger.info(f"开始下载视频: {video_url}")
        self.logger.info(f"保存路径: {filepath}")

        return Request(
            url=video_url,
            callback=self.save_video,
            meta={'filepath': filepath, 'video_id': video_id},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.douyin.com/',
            },
            dont_filter=True
        )

    def save_video(self, response):
        filepath = response.meta.get('filepath')
        video_id = response.meta.get('video_id')

        if response.status == 200:
            with open(filepath, 'wb') as f:
                f.write(response.body)
            self.logger.info(f"视频下载成功: {filepath}")
            self.logger.info(f"文件大小: {len(response.body)} bytes")
            yield {
                'video_id': video_id,
                'filepath': filepath,
                'size': len(response.body),
                'status': 'success'
            }
        else:
            self.logger.error(f"下载失败，状态码: {response.status}")

    def extract_video_id(self, url):
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)

        match = re.search(r'share/video/(\d+)', url)
        if match:
            return match.group(1)

        match = re.search(r'item/(\d+)', url)
        if match:
            return match.group(1)

        match = re.search(r'/video/(\d+)[/?]', url)
        if match:
            return match.group(1)

        return None
