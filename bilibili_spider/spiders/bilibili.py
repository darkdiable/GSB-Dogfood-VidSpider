import re
import json
import scrapy
from urllib.parse import urlencode
from bilibili_spider.items import BilibiliVideoItem


class BilibiliSpider(scrapy.Spider):
    name = 'bilibili'
    allowed_domains = ['bilibili.com']

    def __init__(self, bv_id=None, **kwargs):
        super().__init__(**kwargs)
        if bv_id:
            self.bv_id = bv_id
        else:
            self.bv_id = 'BV1KjYTzaEcx'
        self.start_urls = [f'https://www.bilibili.com/video/{self.bv_id}']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com',
                }
            )

    def parse(self, response):
        self.logger.info(f'Parsing page: {response.url}')

        # Extract video title
        title = response.css('h1.video-title::text').get('')
        if not title:
            title = response.xpath('//h1[@class="video-title"]//text()').get('')
        if not title:
            title = response.css('title::text').get('')
        title = title.strip() if title else self.bv_id

        self.logger.info(f'Video title: {title}')

        # Extract __playinfo__ from page script
        playinfo_match = re.search(r'<script>window\.__playinfo__=({.*?})</script>', response.text)

        if playinfo_match:
            try:
                playinfo = json.loads(playinfo_match.group(1))
                self.logger.info('Found __playinfo__ data')

                # Extract video and audio URLs from playinfo
                video_url = None
                audio_url = None

                # Check for dash data (DASH format)
                dash_data = playinfo.get('data', {}).get('dash', {})
                if dash_data:
                    video_list = dash_data.get('video', [])
                    audio_list = dash_data.get('audio', [])

                    if video_list:
                        # Get the first video stream (usually highest quality)
                        video_url = video_list[0].get('baseUrl') or video_list[0].get('base_url')
                        self.logger.info(f'Found video URL: {video_url[:100]}...' if video_url else 'No video URL')

                    if audio_list:
                        # Get the first audio stream
                        audio_url = audio_list[0].get('baseUrl') or audio_list[0].get('base_url')
                        self.logger.info(f'Found audio URL: {audio_url[:100]}...' if audio_url else 'No audio URL')

                # Check for durl data (FLV format)
                durl_data = playinfo.get('data', {}).get('durl', [])
                if durl_data and not video_url:
                    video_url = durl_data[0].get('url')
                    self.logger.info(f'Found FLV video URL: {video_url[:100]}...' if video_url else 'No FLV URL')

                item = BilibiliVideoItem()
                item['bv_id'] = self.bv_id
                item['title'] = title
                item['video_url'] = video_url or ''
                item['audio_url'] = audio_url or ''

                yield item

            except json.JSONDecodeError as e:
                self.logger.error(f'Failed to parse __playinfo__: {e}')
        else:
            self.logger.warning('No __playinfo__ found in page')

        # Also try to extract from __INITIAL_STATE__
        initial_state_match = re.search(r'<script>window\.__INITIAL_STATE__=({.*?});\(function\(\)', response.text)
        if initial_state_match:
            try:
                initial_state = json.loads(initial_state_match.group(1))
                self.logger.info('Found __INITIAL_STATE__ data')
                # Could extract additional metadata here if needed
            except json.JSONDecodeError as e:
                self.logger.error(f'Failed to parse __INITIAL_STATE__: {e}')
