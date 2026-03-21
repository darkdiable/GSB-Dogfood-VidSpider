#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_spider.py <bilibili_video_url>")
        print("Example: python run_spider.py https://www.bilibili.com/video/BV1KjYTzaEcx")
        sys.exit(1)
    
    video_url = sys.argv[1]
    
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    
    process.crawl('bilibili_video', url=video_url)
    process.start()

if __name__ == '__main__':
    main()
