import os
import requests
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class KuaishouVideoDownloadPipeline:
    def __init__(self):
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/ksOutput'
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        if spider.name != 'kuaishou':
            return item
            
        adapter = ItemAdapter(item)
        video_url = adapter.get('video_url')
        title = adapter.get('title', 'kuaishou_video')
        
        if not video_url:
            raise DropItem("Missing video URL in item")
        
        title = self.sanitize_filename(title)
        file_path = os.path.join(self.output_dir, f'{title}.mp4')
        
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(self.output_dir, f'{title}_{counter}.mp4')
            counter += 1
        
        try:
            spider.logger.info(f'Downloading video from: {video_url}')
            response = requests.get(
                video_url,
                stream=True,
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.kuaishou.com/',
                }
            )
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            spider.logger.info(f'Video saved to: {file_path}')
            adapter['file_path'] = file_path
            
        except Exception as e:
            spider.logger.error(f'Failed to download video: {str(e)}')
            raise DropItem(f"Failed to download video: {str(e)}")
        
        return item

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'kuaishou_video'

class DouyinVideoDownloadPipeline:
    def __init__(self):
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/douyinOutput'
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        video_url = adapter.get('video_url')
        title = adapter.get('title', 'douyin_video')
        
        if not video_url:
            raise DropItem("Missing video URL in item")
        
        title = self.sanitize_filename(title)
        file_path = os.path.join(self.output_dir, f'{title}.mp4')
        
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(self.output_dir, f'{title}_{counter}.mp4')
            counter += 1
        
        try:
            spider.logger.info(f'Downloading video from: {video_url}')
            response = requests.get(
                video_url,
                stream=True,
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.douyin.com/',
                }
            )
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            spider.logger.info(f'Video saved to: {file_path}')
            adapter['file_path'] = file_path
            
        except Exception as e:
            spider.logger.error(f'Failed to download video: {str(e)}')
            raise DropItem(f"Failed to download video: {str(e)}")
        
        return item

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'douyin_video'

class InstagramVideoDownloadPipeline:
    def __init__(self):
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/insOutput'
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        if spider.name != 'instagram':
            return item
            
        adapter = ItemAdapter(item)
        video_url = adapter.get('video_url')
        title = adapter.get('title', 'instagram_video')
        
        if not video_url:
            raise DropItem("Missing video URL in item")
        
        title = self.sanitize_filename(title)
        file_path = os.path.join(self.output_dir, f'{title}.mp4')
        
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(self.output_dir, f'{title}_{counter}.mp4')
            counter += 1
        
        try:
            spider.logger.info(f'Downloading video from: {video_url}')
            response = requests.get(
                video_url,
                stream=True,
                timeout=60,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.instagram.com/',
                }
            )
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            spider.logger.info(f'Video saved to: {file_path}')
            adapter['file_path'] = file_path
            
        except Exception as e:
            spider.logger.error(f'Failed to download video: {str(e)}')
            raise DropItem(f"Failed to download video: {str(e)}")
        
        return item

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'instagram_video'
