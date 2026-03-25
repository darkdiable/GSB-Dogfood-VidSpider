BOT_NAME = 'douyin_spider'
SPIDER_MODULES = ['douyin_spider.spiders']
NEWSPIDER_MODULE = 'douyin_spider.spiders'
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 2
DOWNLOAD_DELAY = 1
COOKIES_ENABLED = False
DOWNLOADER_MIDDLEWARES = {
    'douyin_spider.middlewares.RandomUserAgentMiddleware': 400,
}
ITEM_PIPELINES = {
    'douyin_spider.pipelines.DouyinVideoPipeline': 1,
}
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'
LOG_LEVEL = 'INFO'
OUTPUT_DIR = 'douyinOutput'
