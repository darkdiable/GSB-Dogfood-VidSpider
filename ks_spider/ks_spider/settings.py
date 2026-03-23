BOT_NAME = "ks_spider"

SPIDER_MODULES = ["ks_spider.spiders"]
NEWSPIDER_MODULE = "ks_spider.spiders"

ADDONS = {}

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

ITEM_PIPELINES = {
    "ks_spider.pipelines.KuaishouVideoDownloadPipeline": 300,
}

FEED_EXPORT_ENCODING = "utf-8"
