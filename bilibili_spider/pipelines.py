import os
import json
import requests
import subprocess
from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.project import get_project_settings


class BilibiliVideoPipeline:
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        bv_id = item.get('bv_id', 'unknown')
        title = item.get('title', 'unknown')
        
        spider.logger.info(f'Processing video: {title} ({bv_id})')
        
        # Save video info to JSON
        info_file = os.path.join(self.output_dir, f'{bv_id}_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump({
                'bv_id': bv_id,
                'title': title,
                'video_url': item.get('video_url', ''),
                'audio_url': item.get('audio_url', ''),
            }, f, ensure_ascii=False, indent=2)
        
        spider.logger.info(f'Video info saved to: {info_file}')
        
        video_file = None
        audio_file = None
        
        # Download video if URL is available
        video_url = item.get('video_url', '')
        if video_url:
            video_file = os.path.join(self.output_dir, f'{bv_id}_video.m4s')
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com',
                }
                response = requests.get(video_url, headers=headers, stream=True, timeout=30)
                if response.status_code == 200:
                    with open(video_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    spider.logger.info(f'Video downloaded to: {video_file}')
                else:
                    spider.logger.error(f'Failed to download video: HTTP {response.status_code}')
                    video_file = None
            except Exception as e:
                spider.logger.error(f'Error downloading video: {e}')
                video_file = None
        
        # Download audio if URL is available
        audio_url = item.get('audio_url', '')
        if audio_url:
            audio_file = os.path.join(self.output_dir, f'{bv_id}_audio.m4s')
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com',
                }
                response = requests.get(audio_url, headers=headers, stream=True, timeout=30)
                if response.status_code == 200:
                    with open(audio_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    spider.logger.info(f'Audio downloaded to: {audio_file}')
                else:
                    spider.logger.error(f'Failed to download audio: HTTP {response.status_code}')
                    audio_file = None
            except Exception as e:
                spider.logger.error(f'Error downloading audio: {e}')
                audio_file = None
        
        # Merge video and audio using FFmpeg
        if video_file and audio_file and os.path.exists(video_file) and os.path.exists(audio_file):
            output_file = os.path.join(self.output_dir, f'{bv_id}.mp4')
            try:
                spider.logger.info(f'Merging video and audio into: {output_file}')
                cmd = [
                    'ffmpeg',
                    '-i', video_file,
                    '-i', audio_file,
                    '-c', 'copy',
                    '-y',
                    output_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    spider.logger.info(f'Successfully merged to: {output_file}')
                    # Remove temporary files after successful merge
                    os.remove(video_file)
                    os.remove(audio_file)
                    spider.logger.info('Removed temporary video and audio files')
                else:
                    spider.logger.error(f'FFmpeg merge failed: {result.stderr}')
            except subprocess.TimeoutExpired:
                spider.logger.error('FFmpeg merge timed out')
            except FileNotFoundError:
                spider.logger.error('FFmpeg not found. Please install FFmpeg to merge video and audio.')
            except Exception as e:
                spider.logger.error(f'Error merging video and audio: {e}')
        elif video_file and os.path.exists(video_file) and not audio_file:
            # If only video is available, rename it to mp4
            output_file = os.path.join(self.output_dir, f'{bv_id}.mp4')
            try:
                cmd = [
                    'ffmpeg',
                    '-i', video_file,
                    '-c', 'copy',
                    '-y',
                    output_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    spider.logger.info(f'Video converted to: {output_file}')
                    os.remove(video_file)
                else:
                    spider.logger.error(f'FFmpeg conversion failed: {result.stderr}')
            except Exception as e:
                spider.logger.error(f'Error converting video: {e}')
        
        return item
