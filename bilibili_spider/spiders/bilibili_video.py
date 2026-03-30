import re
import json
import scrapy
from urllib.parse import urlencode
from bilibili_spider.items import BilibiliVideoItem


class BilibiliVideoSpider(scrapy.Spider):
    name = 'bilibili_video'
    allowed_domains = ['bilibili.com', 'api.bilibili.com']
    
    custom_settings = {
        'ITEM_PIPELINES': {
            'bilibili_spider.pipelines.BilibiliVideoPipeline': 1,
        }
    }
    
    def __init__(self, url=None, *args, **kwargs):
        super(BilibiliVideoSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
    
    def start_requests(self):
        for url in self.start_urls:
            bvid_match = re.search(r'BV[\w]+', url)
            if bvid_match:
                bvid = bvid_match.group()
                api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
                yield scrapy.Request(
                    url=api_url,
                    callback=self.parse_video_info,
                    meta={'bvid': bvid, 'original_url': url},
                    headers={
                        'Referer': url,
                    }
                )
            else:
                self.logger.error(f'Invalid Bilibili URL: {url}')
    
    def parse_video_info(self, response):
        data = json.loads(response.text)
        if data.get('code') != 0:
            self.logger.error(f"API error: {data.get('message')}")
            return
        
        video_data = data.get('data', {})
        bvid = video_data.get('bvid', response.meta.get('bvid'))
        cid = video_data.get('cid')
        title = video_data.get('title', '')
        duration = video_data.get('duration', 0)
        description = video_data.get('desc', '')
        
        self.logger.info(f"Video info - Title: {title}, BV: {bvid}, CID: {cid}")
        
        params = {
            'bvid': bvid,
            'cid': cid,
            'qn': 80,
            'fnval': 16,
            'fnver': 0,
            'fourk': 1,
        }
        
        play_url = f'https://api.bilibili.com/x/player/playurl?{urlencode(params)}'
        
        yield scrapy.Request(
            url=play_url,
            callback=self.parse_play_url,
            meta={
                'bvid': bvid,
                'cid': cid,
                'title': title,
                'duration': duration,
                'description': description,
                'original_url': response.meta.get('original_url'),
            },
            headers={
                'Referer': response.meta.get('original_url'),
            }
        )
    
    def parse_play_url(self, response):
        data = json.loads(response.text)
        if data.get('code') != 0:
            self.logger.error(f"Play URL API error: {data.get('message')}")
            return
        
        play_data = data.get('data', {})
        
        video_url = None
        audio_url = None
        
        dash = play_data.get('dash')
        if dash:
            video_list = dash.get('video', [])
            audio_list = dash.get('audio', [])
            
            if video_list:
                best_video = max(video_list, key=lambda x: x.get('id', 0))
                video_url = best_video.get('baseUrl') or best_video.get('base_url')
            
            if audio_list:
                best_audio = max(audio_list, key=lambda x: x.get('id', 0))
                audio_url = best_audio.get('baseUrl') or best_audio.get('base_url')
        
        if not video_url:
            durl = play_data.get('durl', [])
            if durl:
                video_url = durl[0].get('url')
        
        if video_url:
            item = BilibiliVideoItem()
            item['bvid'] = response.meta.get('bvid')
            item['title'] = response.meta.get('title')
            item['cid'] = response.meta.get('cid')
            item['video_url'] = video_url
            item['audio_url'] = audio_url
            item['duration'] = response.meta.get('duration')
            item['description'] = response.meta.get('description')
            
            self.logger.info(f"Found video URL for: {item['title']}")
            yield item
        else:
            self.logger.error("No video URL found")
