import scrapy


class DouyinVideoItem(scrapy.Item):
    video_url = scrapy.Field()
    video_title = scrapy.Field()
    video_id = scrapy.Field()
    author = scrapy.Field()
    file_path = scrapy.Field()
