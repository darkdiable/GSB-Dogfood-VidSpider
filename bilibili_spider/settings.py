BOT_NAME = 'bilibili_spider'

SPIDER_MODULES = ['bilibili_spider.spiders']
NEWSPIDER_MODULE = 'bilibili_spider.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure download delay
DOWNLOAD_DELAY = 1

# Disable cookies
COOKIES_ENABLED = True

# Default request headers
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.bilibili.com',
}

# Configure pipelines
ITEM_PIPELINES = {
    'bilibili_spider.pipelines.BilibiliVideoPipeline': 300,
}

# Configure middlewares
DOWNLOADER_MIDDLEWARES = {
    'bilibili_spider.middlewares.BilibiliDownloaderMiddleware': 543,
}

SPIDER_MIDDLEWARES = {
    'bilibili_spider.middlewares.BilibiliSpiderMiddleware': 543,
}

# Log level
LOG_LEVEL = 'INFO'

# Output directory
OUTPUT_DIR = 'output'
