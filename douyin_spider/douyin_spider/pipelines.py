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
        if spider.name not in ['douyin', 'douyin_playwright']:
            return item
            
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
        
        video_url = self.clean_instagram_url(video_url)
        
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
            
            total_size = int(response.headers.get('content-length', 0))
            spider.logger.info(f'Total video size: {total_size/1024/1024:.2f} MB')
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            final_size = os.path.getsize(file_path)
            spider.logger.info(f'Video saved to: {file_path} ({final_size/1024/1024:.2f} MB)')
            adapter['file_path'] = file_path
            
        except Exception as e:
            spider.logger.error(f'Failed to download video: {str(e)}')
            raise DropItem(f"Failed to download video: {str(e)}")
        
        return item

    def clean_instagram_url(self, url):
        if 'bytestart' in url or 'byteend' in url:
            url = url.split('bytestart=')[0].rstrip('&?')
            url = url.split('byteend=')[0].rstrip('&?')
        return url

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'instagram_video'

class YoutubeVideoDownloadPipeline:
    def __init__(self):
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/ytOutput'
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        if spider.name != 'youtube':
            return item
            
        adapter = ItemAdapter(item)
        original_url = adapter.get('original_url', '')
        video_id = adapter.get('video_id', '')
        title = adapter.get('title', 'youtube_video')
        
        if not original_url and not video_id:
            raise DropItem("Missing both original URL and video ID")
        
        return self.download_with_yt_dlp(original_url or video_id, title, adapter, spider)
    
    def download_with_yt_dlp(self, video_url, title, adapter, spider):
        import yt_dlp
        
        title = self.sanitize_filename(title)
        file_path = os.path.join(self.output_dir, f'{title}.mp4')
        
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(self.output_dir, f'{title}_{counter}.mp4')
            counter += 1
        
        spider.logger.info(f'Downloading YouTube video: {title}')
        spider.logger.info(f'Output file: {file_path}')
        
        ydl_opts = {
            'outtmpl': file_path,
            'format': 'best[ext=mp4]/best',
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'retries': 5,
            'fragment_retries': 5,
            'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if not video_url.startswith('http'):
                    video_url = f'https://www.youtube.com/watch?v={video_url}'
                
                info = ydl.extract_info(video_url, download=True)
                
                if info and os.path.exists(file_path):
                    final_size = os.path.getsize(file_path)
                    spider.logger.info(f'Success! Video saved to: {file_path} ({final_size/1024/1024:.2f} MB)')
                    adapter['file_path'] = file_path
                    adapter['video_url'] = info.get('url', '')
                    return dict(adapter)
                else:
                    raise DropItem("yt-dlp download failed: file not created")
                    
        except Exception as e:
            spider.logger.error(f'Failed to download video: {str(e)}')
            raise DropItem(f"Failed to download video: {str(e)}")

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'youtube_video'
