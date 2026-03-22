import re
import os
import json
import requests
from urllib.parse import unquote
from playwright.sync_api import sync_playwright


class DouyinVideoDownloader:
    def __init__(self, output_dir='douyinOutput'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def get_rendered_html(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            final_url = url
            video_urls = []
            
            def handle_response(response):
                nonlocal video_urls
                resp_url = response.url.lower()
                if '.mp4' in resp_url:
                    if 'douyinstatic.com' in resp_url or 'byteeffecttos.com' in resp_url:
                        return
                    if 'douyinvod.com' in resp_url or 'bytedance.com' in resp_url or 'tiktokcdn' in resp_url:
                        if resp_url not in video_urls:
                            video_urls.append(response.url)
                            print(f'Found video URL: {response.url[:100]}...')
            
            page.on('response', handle_response)
            
            try:
                page.goto(url, timeout=60000)
                page.wait_for_load_state('networkidle', timeout=30000)
                final_url = page.url
                page.wait_for_timeout(5000)
                
                html = page.content()
                
                video_elements = page.query_selector_all('video')
                for video in video_elements:
                    src = video.get_attribute('src')
                    if src and src not in video_urls:
                        src_lower = src.lower()
                        if 'douyinstatic.com' not in src_lower and 'byteeffecttos.com' not in src_lower:
                            video_urls.append(src)
                            print(f'Found video element src: {src[:100]}...')
                
            except Exception as e:
                print(f'Error loading page: {e}')
                try:
                    final_url = page.url
                    html = page.content()
                except:
                    html = ''
            finally:
                browser.close()
            
            return final_url, html, video_urls
    
    def extract_video_id(self, url):
        patterns = [
            r'/video/(\d+)',
            r'modal_id=(\d+)',
            r'aweme_id=(\d+)',
            r'/(\d{19})/',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info_from_html(self, html, video_urls):
        if video_urls:
            return {'video_url': video_urls[0], 'title': 'douyin_video', 'author': 'unknown'}
        
        patterns = [
            r'window\._ROUTER_DATA\s*=\s*({.+?})\s*</script>',
            r'<script\s+id="RENDER_DATA"\s+type="application/json">([^<]+)</script>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                data_str = match.group(1)
                try:
                    data_str = unquote(data_str)
                except:
                    pass
                try:
                    data = json.loads(data_str)
                    video_info = self.find_video_info(data)
                    if video_info:
                        return video_info
                except json.JSONDecodeError as e:
                    print(f'JSON decode error: {e}')
                    continue
        
        video_url_patterns = [
            (r'"playAddr"\s*:\s*\[\s*\{\s*"src"\s*:\s*"([^"]+)"', False),
            (r'"play_addr"\s*:\s*\{\s*"url_list"\s*:\s*\[\s*"([^"]+)"', False),
            (r'"playApi"\s*:\s*"([^"]+)"', False),
            (r'"src"\s*:\s*"(https?://[^"]*v[^"]*\.douyinvod\.com[^"]*)"', False),
            (r'"src"\s*:\s*"(//[^"]*v[^"]*\.douyinvod\.com[^"]*)"', True),
            (r'(https?://[^"\s]*\.douyinvod\.com/[^"\s]+\.mp4[^"\s]*)', False),
            (r'<video[^>]+src="([^"]+)"', False),
            (r'<source[^>]+src="([^"]+)"', False),
        ]
        
        for pattern, add_https in video_url_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                video_url = match.group(1)
                if add_https and video_url.startswith('//'):
                    video_url = 'https:' + video_url
                print(f'Found video URL via pattern: {video_url[:80]}...')
                return {'video_url': video_url, 'title': 'douyin_video', 'author': 'unknown'}
        
        print('No video URL found in HTML')
        print(f'HTML length: {len(html)}')
        
        return None
    
    def find_video_info(self, data, depth=0):
        if depth > 15:
            return None
        
        if isinstance(data, dict):
            if 'video' in data and isinstance(data['video'], dict):
                video = data['video']
                play_addr = video.get('play_addr', {})
                if isinstance(play_addr, dict):
                    url_list = play_addr.get('url_list', [])
                    if url_list:
                        video_url = url_list[0]
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        title = data.get('desc', 'douyin_video')
                        author = data.get('author', {}).get('nickname', 'unknown')
                        return {'video_url': video_url, 'title': title, 'author': author}
            
            if 'aweme' in data and isinstance(data['aweme'], dict):
                return self.find_video_info(data['aweme'], depth + 1)
            
            if 'aweme_detail' in data and isinstance(data['aweme_detail'], dict):
                return self.find_video_info(data['aweme_detail'], depth + 1)
            
            for key in ['detail', 'videoInfo', 'video_data', 'itemInfo']:
                if key in data and isinstance(data[key], dict):
                    result = self.find_video_info(data[key], depth + 1)
                    if result:
                        return result
            
            for value in data.values():
                if isinstance(value, dict):
                    result = self.find_video_info(value, depth + 1)
                    if result:
                        return result
        
        return None
    
    def download_video(self, video_url, filename):
        filepath = os.path.join(self.output_dir, filename)
        
        if os.path.exists(filepath):
            print(f'Video already exists: {filepath}')
            return filepath
        
        print(f'Downloading video from: {video_url[:100]}...')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
        }
        
        try:
            resp = requests.get(video_url, headers=headers, stream=True, timeout=60)
            resp.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f'Video saved to: {filepath}')
            return filepath
        except Exception as e:
            print(f'Error downloading video: {e}')
            return None
    
    def sanitize_filename(self, filename):
        filename = re.sub(r'[<>:"/\\|?*\n\r\t]', '', filename)
        filename = filename.strip()
        filename = re.sub(r'\s+', '_', filename)
        return filename[:100] if filename else 'unnamed'
    
    def download(self, url):
        print(f'Processing URL: {url}')
        
        final_url, html, video_urls = self.get_rendered_html(url)
        print(f'Final URL: {final_url}')
        
        video_id = self.extract_video_id(final_url)
        print(f'Video ID: {video_id}')
        
        video_info = self.get_video_info_from_html(html, video_urls)
        if not video_info:
            print('Failed to get video info')
            return None
        
        video_url = video_info.get('video_url')
        title = video_info.get('title', 'douyin_video')
        author = video_info.get('author', 'unknown')
        
        print(f'Title: {title}')
        print(f'Author: {author}')
        print(f'Video URL: {video_url[:100]}...')
        
        safe_title = self.sanitize_filename(title)
        safe_author = self.sanitize_filename(author)
        filename = f'{safe_author}_{video_id}_{safe_title}.mp4'
        
        return self.download_video(video_url, filename)


if __name__ == '__main__':
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://v.douyin.com/06CE2EJQVPU/'
    
    downloader = DouyinVideoDownloader()
    result = downloader.download(url)
    
    if result:
        print(f'\nSuccess! Video saved to: {result}')
    else:
        print('\nFailed to download video')
