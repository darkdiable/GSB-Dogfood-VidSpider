import scrapy


class BilibiliVideoItem(scrapy.Item):
    bv_id = scrapy.Field()
    title = scrapy.Field()
    video_url = scrapy.Field()
    audio_url = scrapy.Field()
    file_path = scrapy.Field()
