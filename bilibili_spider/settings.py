BOT_NAME = 'bilibili_spider'

SPIDER_MODULES = ['bilibili_spider.spiders']
NEWSPIDER_MODULE = 'bilibili_spider.spiders'

ROBOTSTXT_OBEY = False

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.bilibili.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

ITEM_PIPELINES = {
    'bilibili_spider.pipelines.BilibiliVideoPipeline': 1,
}

DOWNLOAD_TIMEOUT = 30
CONCURRENT_REQUESTS = 2
DOWNLOAD_DELAY = 1

LOG_LEVEL = 'INFO'
