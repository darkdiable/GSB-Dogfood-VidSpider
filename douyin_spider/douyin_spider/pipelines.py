import os
import requests
import subprocess
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
        audio_url = adapter.get('audio_url')
        title = adapter.get('title', 'bilibili_video')
        bvid = adapter.get('bvid', '')
        
        if not video_url:
            spider.logger.error('No video URL found')
            raise DropItem("Missing video URL in item")
        
        title = self.sanitize_filename(title)
        if bvid:
            base_filename = f'{bvid}_{title}'
        else:
            base_filename = title
        
        temp_video_path = os.path.join(self.output_dir, f'{base_filename}_video.m4s')
        temp_audio_path = os.path.join(self.output_dir, f'{base_filename}_audio.m4s')
        merged_video_path = os.path.join(self.output_dir, f'{base_filename}_merged.mp4')
        final_video_path = os.path.join(self.output_dir, f'{base_filename}.mp4')
        
        counter = 1
        while os.path.exists(final_video_path):
            final_video_path = os.path.join(self.output_dir, f'{base_filename}_{counter}.mp4')
            counter += 1
        
        temp_files = [temp_video_path]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'video',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
        }
        
        try:
            spider.logger.info(f'Downloading video stream from: {video_url[:100]}...')
            response = requests.get(
                video_url,
                stream=True,
                timeout=120,
                headers=headers
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            spider.logger.info(f'Video stream size: {total_size/1024/1024:.2f} MB')
            
            with open(temp_video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            spider.logger.info(f'Video stream downloaded to: {temp_video_path}')
            
            if audio_url:
                temp_files.append(temp_audio_path)
                spider.logger.info(f'Downloading audio stream from: {audio_url[:100]}...')
                response = requests.get(
                    audio_url,
                    stream=True,
                    timeout=120,
                    headers=headers
                )
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                spider.logger.info(f'Audio stream size: {total_size/1024/1024:.2f} MB')
                
                with open(temp_audio_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                spider.logger.info(f'Audio stream downloaded to: {temp_audio_path}')
            
            spider.logger.info('Merging video and audio with ffmpeg...')
            merge_success = self.merge_video_audio(
                temp_video_path, 
                temp_audio_path if audio_url else None, 
                merged_video_path, 
                spider
            )
            
            if merge_success:
                temp_files.append(merged_video_path)
                spider.logger.info('Removing watermark with ffmpeg...')
                success = self.remove_watermark(merged_video_path, final_video_path, spider)
                
                if success:
                    spider.logger.info(f'Final video saved to: {final_video_path}')
                    adapter['file_path'] = final_video_path
                else:
                    if os.path.exists(merged_video_path):
                        os.rename(merged_video_path, final_video_path)
                        spider.logger.info(f'Video saved without watermark removal: {final_video_path}')
                        adapter['file_path'] = final_video_path
            else:
                spider.logger.warning('Failed to merge, trying to convert video directly...')
                success = self.remove_watermark(temp_video_path, final_video_path, spider)
                if success:
                    adapter['file_path'] = final_video_path
                else:
                    raise DropItem("Failed to process video")
            
        except Exception as e:
            spider.logger.error(f'Failed to download video: {str(e)}')
            raise DropItem(f"Failed to download video: {str(e)}")
        finally:
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
        
        return item

    def merge_video_audio(self, video_path, audio_path, output_path, spider):
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                spider.logger.warning('ffmpeg not found')
                return False
        except FileNotFoundError:
            spider.logger.warning('ffmpeg not installed')
            return False
        
        try:
            if audio_path and os.path.exists(audio_path):
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-i', audio_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-y',
                    output_path
                ]
            else:
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-y',
                    output_path
                ]
            
            spider.logger.info(f'Running ffmpeg merge command')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                spider.logger.info('Video and audio merged successfully')
                return True
            else:
                spider.logger.error(f'ffmpeg merge error: {result.stderr}')
                return False
                
        except subprocess.TimeoutExpired:
            spider.logger.error('ffmpeg merge timeout')
            return False
        except Exception as e:
            spider.logger.error(f'ffmpeg merge failed: {str(e)}')
            return False

    def remove_watermark(self, input_path, output_path, spider):
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                spider.logger.warning('ffmpeg not found, skipping watermark removal')
                return False
        except FileNotFoundError:
            spider.logger.warning('ffmpeg not installed, skipping watermark removal')
            return False
        
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', 'delogo=x=10:y=10:w=120:h=50:show=0',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            spider.logger.info(f'Running ffmpeg delogo command')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                spider.logger.info('Watermark removed successfully')
                return True
            else:
                spider.logger.error(f'ffmpeg delogo error: {result.stderr}')
                return False
                
        except subprocess.TimeoutExpired:
            spider.logger.error('ffmpeg delogo timeout')
            return False
        except Exception as e:
            spider.logger.error(f'ffmpeg delogo failed: {str(e)}')
            return False

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'bilibili_video'
