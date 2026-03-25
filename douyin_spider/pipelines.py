import os
import re
import requests
from urllib.parse import urljoin
from scrapy.utils.project import get_project_settings


class DouyinVideoPipeline:
    def __init__(self):
        settings = get_project_settings()
        self.output_dir = settings.get('OUTPUT_DIR', 'douyinOutput')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def process_item(self, item, spider):
        video_url = item.get('video_url')
        if not video_url:
            spider.logger.error('No video URL in item')
            return item
        
        if video_url.startswith('/'):
            video_url = urljoin('https://www.iesdouyin.com', video_url)
            spider.logger.info(f'Converted relative URL to: {video_url}')
        
        video_id = item.get('video_id', 'unknown')
        title = item.get('video_title', 'douyin_video')
        author = item.get('author', 'unknown')
        
        safe_title = self.sanitize_filename(title)[:50]
        safe_author = self.sanitize_filename(author)[:20]
        
        filename = f"{safe_author}_{video_id}_{safe_title}.mp4"
        filepath = os.path.join(self.output_dir, filename)
        
        if os.path.exists(filepath):
            spider.logger.info(f'Video already exists: {filepath}')
            item['file_path'] = filepath
            return item
        
        spider.logger.info(f'Downloading video from: {video_url[:100]}...')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Referer': 'https://www.douyin.com/',
        }
        
        try:
            response = requests.get(video_url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            spider.logger.info(f'Video saved to: {filepath}')
            item['file_path'] = filepath
            
        except requests.RequestException as e:
            spider.logger.error(f'Failed to download video: {e}')
        
        return item
    
    def sanitize_filename(self, filename):
        filename = re.sub(r'[<>:"/\\|?*\n\r\t]', '', filename)
        filename = filename.strip()
        filename = re.sub(r'\s+', '_', filename)
        return filename if filename else 'unnamed'
