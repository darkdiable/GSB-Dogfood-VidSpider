import scrapy
import re
import requests
import json

class BilibiliSpider(scrapy.Spider):
    name = "bilibili"
    allowed_domains = ["bilibili.com", "bilivideo.com", "biliapi.com", "hdslb.com"]
    start_urls = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.bilibili.com/',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'douyin_spider.middlewares.BilibiliPlaywrightMiddleware': 543,
        },
        'DOWNLOAD_TIMEOUT': 120,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(BilibiliSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def parse(self, response):
        video_urls = response.meta.get('video_urls', [])
        audio_urls = response.meta.get('audio_urls', [])
        
        self.logger.info(f'Total video URLs found: {len(video_urls)}')
        self.logger.info(f'Total audio URLs found: {len(audio_urls)}')
        
        title = 'bilibili_video'
        og_title = response.xpath('//meta[@property="og:title"]/@content').get()
        if og_title:
            title = og_title
        else:
            h1_title = response.xpath('//h1[@class="video-title"]/text()').get()
            if h1_title:
                title = h1_title
        
        bvid = ''
        bvid_match = re.search(r'BV[\w]+', response.url)
        if bvid_match:
            bvid = bvid_match.group()
        
        if video_urls:
            best_video_url = self.select_best_url(video_urls, prefer_cdn=True)
            best_audio_url = self.select_best_url(audio_urls, prefer_cdn=True) if audio_urls else None
            
            self.logger.info(f'Selected video URL: {best_video_url[:100]}...')
            if best_audio_url:
                self.logger.info(f'Selected audio URL: {best_audio_url[:100]}...')
            
            yield {
                'video_url': best_video_url,
                'audio_url': best_audio_url,
                'title': title,
                'bvid': bvid,
                'video_urls': video_urls,
                'audio_urls': audio_urls
            }
        else:
            self.logger.error('No video URLs found')
            yield {
                'video_url': None,
                'audio_url': None,
                'title': title,
                'bvid': bvid,
                'video_urls': [],
                'audio_urls': []
            }
    
    def select_best_url(self, urls, prefer_cdn=True):
        if not urls:
            return None
        
        if prefer_cdn:
            cdn_urls = [url for url in urls if 'mcdn.bilivideo.cn' in url or 'bilivideo.cn' in url]
            if cdn_urls:
                return cdn_urls[0]
        
        return urls[0]
