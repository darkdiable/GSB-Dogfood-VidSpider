import scrapy
import os
import yt_dlp
from urllib.parse import urlparse, parse_qs

class YoutubeSpider(scrapy.Spider):
    name = "youtube"
    allowed_domains = ["youtube.com", "youtu.be", "googlevideo.com"]
    start_urls = []

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'DOWNLOAD_TIMEOUT': 300,
        'ROBOTSTXT_OBEY': False,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(YoutubeSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/ytOutput'
        os.makedirs(self.output_dir, exist_ok=True)

    def parse(self, response):
        video_url = response.url
        self.logger.info(f'Processing YouTube URL: {video_url}')

        try:
            video_info = self.extract_video_info(video_url)
            if video_info:
                file_path = self.download_video(video_url, video_info)
                if file_path:
                    yield {
                        'video_url': video_url,
                        'title': video_info.get('title', 'youtube_video'),
                        'file_path': file_path,
                        'duration': video_info.get('duration'),
                        'uploader': video_info.get('uploader'),
                    }
                else:
                    self.logger.error('Failed to download video')
            else:
                self.logger.error('Failed to extract video info')
        except Exception as e:
            self.logger.error(f'Error processing video: {str(e)}')

    def extract_video_info(self, url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'referer': 'https://www.youtube.com/',
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                    'player_skip': [],
                }
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'youtube_video'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'id': info.get('id'),
                }
        except Exception as e:
            self.logger.error(f'Error extracting video info: {str(e)}')
            return None

    def download_video(self, url, video_info):
        video_id = video_info.get('id', 'unknown')
        title = video_info.get('title', 'youtube_video')
        safe_title = self.sanitize_filename(title)
        output_file = os.path.join(self.output_dir, f'{safe_title}.mp4')

        counter = 1
        while os.path.exists(output_file):
            output_file = os.path.join(self.output_dir, f'{safe_title}_{counter}.mp4')
            counter += 1

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_file,
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'referer': 'https://www.youtube.com/',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.youtube.com/',
                'Connection': 'keep-alive',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                    'player_skip': [],
                }
            },
            'throttledratelimit': 100000,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'keep_fragments': False,
        }

        try:
            self.logger.info(f'Starting download: {title}')
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                self.logger.info(f'Video downloaded successfully: {output_file} ({file_size / 1024 / 1024:.2f} MB)')
                return output_file
            else:
                # Try to find the downloaded file with different extension
                base_path = os.path.splitext(output_file)[0]
                for ext in ['.mp4', '.webm', '.mkv']:
                    potential_file = base_path + ext
                    if os.path.exists(potential_file):
                        file_size = os.path.getsize(potential_file)
                        self.logger.info(f'Video downloaded successfully: {potential_file} ({file_size / 1024 / 1024:.2f} MB)')
                        return potential_file
                self.logger.error('Download completed but file not found')
                return None
        except Exception as e:
            self.logger.error(f'Error downloading video: {str(e)}')
            return None

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'youtube_video'
