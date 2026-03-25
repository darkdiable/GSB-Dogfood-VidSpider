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


class BilibiliVideoDownloadPipeline:
    def __init__(self):
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/bilibiliOutput'
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        if spider.name != 'bilibili':
            return item
            
        adapter = ItemAdapter(item)
        video_url = adapter.get('video_url')
        video_urls = adapter.get('video_urls', [])
        audio_url = adapter.get('audio_url')
        title = adapter.get('title', 'bilibili_video')
        
        if not video_url and not video_urls:
            raise DropItem("Missing video URL in item")
        
        title = self.sanitize_filename(title)
        raw_file_path = os.path.join(self.output_dir, f'{title}_raw.mp4')
        final_file_path = os.path.join(self.output_dir, f'{title}.mp4')
        
        counter = 1
        while os.path.exists(raw_file_path) or os.path.exists(final_file_path):
            raw_file_path = os.path.join(self.output_dir, f'{title}_{counter}_raw.mp4')
            final_file_path = os.path.join(self.output_dir, f'{title}_{counter}.mp4')
            counter += 1
        
        response = None
        working_video_url = None
        
        all_urls_to_try = [video_url] + video_urls if video_url else video_urls
        
        for url in all_urls_to_try:
            if not url:
                continue
            try:
                spider.logger.info(f'Trying to download from (showing first 100 chars): {url[:100]}...')
                spider.logger.info(f'Full URL length: {len(url)}')
                response = requests.get(
                    url,
                    stream=True,
                    timeout=60,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.bilibili.com/video/BV1AZQoBaEeM/',
                    }
                )
                response.raise_for_status()
                working_video_url = url
                break
            except Exception as e:
                spider.logger.warning(f'Failed to download from this URL: {str(e)}')
                continue
        
        if not response or not working_video_url:
            raise DropItem("Failed to download video from all available URLs")
        
        try:
            with open(raw_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            spider.logger.info(f'Raw video saved to: {raw_file_path}')
            
            if audio_url:
                spider.logger.info(f'Downloading audio from: {audio_url[:100]}...')
                audio_file_path = os.path.join(self.output_dir, f'{title}_audio.mp4')
                response = requests.get(
                    audio_url,
                    stream=True,
                    timeout=60,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.bilibili.com/',
                        'Origin': 'https://www.bilibili.com',
                    }
                )
                response.raise_for_status()
                
                with open(audio_file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                merged_file_path = os.path.join(self.output_dir, f'{title}_merged.mp4')
                self.merge_audio_video(raw_file_path, audio_file_path, merged_file_path, spider)
                
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                if os.path.exists(raw_file_path):
                    os.remove(raw_file_path)
                raw_file_path = merged_file_path
            
            self.remove_watermark(raw_file_path, final_file_path, spider)
            
            if os.path.exists(raw_file_path):
                os.remove(raw_file_path)
            
            spider.logger.info(f'Final video saved to: {final_file_path}')
            adapter['file_path'] = final_file_path
            
        except Exception as e:
            spider.logger.error(f'Failed to process video: {str(e)}')
            raise DropItem(f"Failed to process video: {str(e)}")
        
        return item

    def merge_audio_video(self, video_path, audio_path, output_path, spider):
        try:
            import subprocess
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            spider.logger.info(f'Merging audio and video: {" ".join(cmd)}')
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                spider.logger.error(f'FFmpeg merge error: {result.stderr}')
                raise Exception(f'FFmpeg merge failed: {result.stderr}')
            spider.logger.info('Audio and video merged successfully')
        except Exception as e:
            spider.logger.error(f'Failed to merge audio and video: {str(e)}')
            raise

    def remove_watermark(self, input_path, output_path, spider):
        try:
            import subprocess
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', 'delogo=x=10:y=10:w=180:h=60:show=0',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            spider.logger.info(f'Removing watermark: {" ".join(cmd)}')
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                spider.logger.error(f'FFmpeg delogo error: {result.stderr}')
                raise Exception(f'FFmpeg delogo failed: {result.stderr}')
            spider.logger.info('Watermark removed successfully')
        except Exception as e:
            spider.logger.error(f'Failed to remove watermark: {str(e)}')
            raise

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'bilibili_video'
