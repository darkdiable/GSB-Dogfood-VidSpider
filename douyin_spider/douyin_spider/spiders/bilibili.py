import scrapy

class BilibiliSpider(scrapy.Spider):
    name = "bilibili"
    allowed_domains = ["bilibili.com", "bilibili.tv", "hdslb.com"]
    start_urls = []

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.bilibili.com/',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'douyin_spider.middlewares.BilibiliPlaywrightMiddleware': 543,
        },
        'DOWNLOAD_TIMEOUT': 600,
    }

    def __init__(self, url=None, *args, **kwargs):
        super(BilibiliSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def parse(self, response):
        file_path = response.meta.get('file_path')
        title = response.meta.get('title', 'bilibili_video')

        if file_path:
            self.logger.info(f'Video successfully downloaded to: {file_path}')
            yield {
                'file_path': file_path,
                'title': title,
                'status': 'success'
            }
        else:
            self.logger.error('Video download failed')
            yield {
                'title': title,
                'status': 'failed'
            }
