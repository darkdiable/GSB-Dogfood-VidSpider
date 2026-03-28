import os
import requests
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import asyncio
from playwright.async_api import async_playwright
import nest_asyncio
import yt_dlp
import subprocess
import re

nest_asyncio.apply()

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
        if spider.name != 'douyin':
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
        video_url = adapter.get('video_url')
        title = adapter.get('title', 'youtube_video')
        original_url = adapter.get('original_url', '')
        
        if not video_url and not original_url:
            raise DropItem("Missing video URL in item")
        
        title = self.sanitize_filename(title)
        file_path = os.path.join(self.output_dir, f'{title}.mp4')
        
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(self.output_dir, f'{title}_{counter}.mp4')
            counter += 1
        
        try:
            spider.logger.info(f'Downloading video using yt-dlp...')
            
            download_url = original_url if original_url else video_url
            
            cmd = [
                'python3', '-m', 'yt_dlp',
                '--extractor-args', 'youtube:player_client=android',
                '-f', 'best[ext=mp4]/best',
                '-o', file_path,
                '--no-playlist',
                download_url
            ]
            
            spider.logger.info(f'Running command: {" ".join(cmd)}')
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                spider.logger.error(f'yt-dlp stderr: {result.stderr}')
                raise Exception(f'yt-dlp failed with return code {result.returncode}')
            
            spider.logger.info(f'yt-dlp stdout: {result.stdout}')
            
            if os.path.exists(file_path):
                final_size = os.path.getsize(file_path)
                spider.logger.info(f'Video saved to: {file_path} ({final_size/1024/1024:.2f} MB)')
                adapter['file_path'] = file_path
            else:
                possible_files = [f for f in os.listdir(self.output_dir) if f.startswith(title)]
                if possible_files:
                    actual_file = os.path.join(self.output_dir, possible_files[-1])
                    final_size = os.path.getsize(actual_file)
                    spider.logger.info(f'Video saved to: {actual_file} ({final_size/1024/1024:.2f} MB)')
                    adapter['file_path'] = actual_file
                else:
                    raise Exception('Video file not found after download')
            
        except Exception as e:
            spider.logger.error(f'Failed to download video: {str(e)}')
            if os.path.exists(file_path):
                os.remove(file_path)
            raise DropItem(f"Failed to download video: {str(e)}")
        
        return item

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'youtube_video'
