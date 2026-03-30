import os
import re
import requests
from itemadapter import ItemAdapter


class BilibiliVideoPipeline:
    def __init__(self):
        self.output_dir = 'output'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        bvid = adapter.get('bvid', 'unknown')
        title = adapter.get('title', 'untitled')
        video_url = adapter.get('video_url')
        audio_url = adapter.get('audio_url')
        
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        safe_title = safe_title[:100]
        
        spider.logger.info(f"Processing video: {title}")
        
        if video_url:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com',
                'Accept': '*/*',
                'Accept-Encoding': 'identity',
                'Connection': 'keep-alive',
            }
            
            video_filename = f"{safe_title}_{bvid}.mp4"
            video_path = os.path.join(self.output_dir, video_filename)
            
            spider.logger.info(f"Downloading video to: {video_path}")
            
            try:
                response = requests.get(video_url, headers=headers, stream=True, timeout=60)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                spider.logger.info(f"Download progress: {progress:.1f}%")
                
                spider.logger.info(f"Video saved successfully: {video_path}")
                
                if audio_url:
                    audio_filename = f"{safe_title}_{bvid}_audio.m4s"
                    audio_path = os.path.join(self.output_dir, audio_filename)
                    
                    spider.logger.info(f"Downloading audio to: {audio_path}")
                    
                    audio_response = requests.get(audio_url, headers=headers, stream=True, timeout=60)
                    audio_response.raise_for_status()
                    
                    with open(audio_path, 'wb') as f:
                        for chunk in audio_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    spider.logger.info(f"Audio saved successfully: {audio_path}")
                    
            except Exception as e:
                spider.logger.error(f"Error downloading video: {e}")
        
        return item
