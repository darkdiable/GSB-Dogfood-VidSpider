import scrapy


class BilibiliVideoItem(scrapy.Item):
    bvid = scrapy.Field()
    title = scrapy.Field()
    cid = scrapy.Field()
    video_url = scrapy.Field()
    audio_url = scrapy.Field()
    duration = scrapy.Field()
    description = scrapy.Field()
