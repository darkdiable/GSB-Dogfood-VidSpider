# Scrapy settings for kuaishou_spider project

BOT_NAME = "kuaishou_spider"

SPIDER_MODULES = ["kuaishou_spider.spiders"]
NEWSPIDER_MODULE = "kuaishou_spider.spiders"

ADDONS = {}

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

ITEM_PIPELINES = {
    "kuaishou_spider.pipelines.KuaishouVideoDownloadPipeline": 300,
}

FEED_EXPORT_ENCODING = "utf-8"
