import scrapy
import re
import json
import os
from urllib.parse import urljoin

class BilibiliSpider(scrapy.Spider):
    name = 'bilibili'
    allowed_domains = ['bilibili.com']
    
    def __init__(self, url=None, *args, **kwargs):
        super(BilibiliSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
        self.output_dir = 'output'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def parse(self, response):
        # 提取视频标题
        title = response.xpath('//h1[contains(@class, "video-title")]/text()').get()
        if not title:
            title = response.xpath('//meta[@name="title"]/@content').get()
        title = title.strip() if title else 'unknown_video'
        
        # 清理标题中的特殊字符
        title = re.sub(r'[\\/*?:"<>|]', '_', title)
        
        # 查找视频播放信息
        playinfo_pattern = r'window.__playinfo__=({.*?})</script>'
        playinfo_match = re.search(playinfo_pattern, response.text, re.DOTALL)
        
        if playinfo_match:
            playinfo_json = playinfo_match.group(1)
            try:
                playinfo = json.loads(playinfo_json)
                video_url = None
                
                # 从playinfo中提取视频URL
                if 'data' in playinfo:
                    data = playinfo['data']
                    if 'dash' in data and data['dash']:
                        dash = data['dash']
                        if 'video' in dash and len(dash['video']) > 0:
                            video_url = dash['video'][0]['baseUrl']
                    elif 'durl' in data and len(data['durl']) > 0:
                        video_url = data['durl'][0]['url']
                
                if video_url:
                    self.logger.info(f'Found video URL: {video_url[:100]}...')
                    yield scrapy.Request(
                        url=video_url,
                        callback=self.save_video,
                        meta={'title': title},
                        headers={
                            'Referer': response.url,
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        },
                        dont_filter=True
                    )
                else:
                    self.logger.error('Could not find video URL in playinfo')
                    
            except json.JSONDecodeError as e:
                self.logger.error(f'Failed to parse playinfo: {e}')
        else:
            self.logger.error('Could not find playinfo on the page')

    def save_video(self, response):
        title = response.meta['title']
        file_path = os.path.join(self.output_dir, f'{title}.mp4')
        
        with open(file_path, 'wb') as f:
            f.write(response.body)
        
        self.logger.info(f'Video saved to: {file_path}')
        yield {
            'title': title,
            'file_path': file_path,
            'status': 'success'
        }
