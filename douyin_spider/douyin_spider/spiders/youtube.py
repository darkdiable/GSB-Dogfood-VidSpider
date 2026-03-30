import scrapy
import yt_dlp

class YoutubeSpider(scrapy.Spider):
    name = "youtube"
    allowed_domains = ["youtube.com", "youtu.be", "googlevideo.com"]
    start_urls = []
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.youtube.com/',
        },
        'DOWNLOAD_TIMEOUT': 120,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(YoutubeSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def parse(self, response):
        self.logger.info('Extracting YouTube video info with yt-dlp...')
        try:
            ydl_opts = {
                'quiet': False,
                'no_warnings': False,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'noplaylist': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(response.url, download=False)
                
                if info:
                    video_id = info.get('id', '')
                    title = info.get('title', 'youtube_video')
                    duration = info.get('duration', 0)
                    
                    formats = info.get('formats', [])
                    video_url = ''
                    
                    for fmt in formats:
                        if fmt.get('ext') == 'mp4' and fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                            video_url = fmt.get('url', '')
                            break
                    
                    if not video_url:
                        for fmt in formats:
                            if fmt.get('ext') == 'mp4' and fmt.get('vcodec') != 'none':
                                video_url = fmt.get('url', '')
                                break
                    
                    self.logger.info(f'Successfully extracted video info: {title}')
                    self.logger.info(f'Video ID: {video_id}, Duration: {duration}s')
                    
                    yield {
                        'video_url': video_url or response.url,
                        'title': title,
                        'duration': duration,
                        'extractor': 'yt-dlp',
                        'video_id': video_id,
                        'original_url': response.url,
                    }
                else:
                    self.logger.error('yt-dlp failed to extract video info')
                    
        except Exception as e:
            self.logger.error(f'yt-dlp error: {str(e)}', exc_info=True)
            
            og_title = response.xpath('//meta[@property="og:title"]/@content').get()
            og_url = response.xpath('//meta[@property="og:url"]/@content').get()
            
            yield {
                'video_url': response.url,
                'title': og_title or 'youtube_video',
                'extractor': 'fallback',
                'video_id': '',
                'original_url': response.url,
            }
