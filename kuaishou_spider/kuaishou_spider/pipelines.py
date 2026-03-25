import os
import requests
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class KuaishouVideoDownloadPipeline:
    def __init__(self):
        self.output_dir = '/Users/bilei/work/LargeModelAnnotation/GBS/260319/GSB-Dogfood-VidSpider/ksOutput'
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        video_url = adapter.get('video_url')
        title = adapter.get('title', 'kuaishou_video')
        author = adapter.get('author', '')

        if not video_url:
            raise DropItem("Missing video URL in item")

        title = self.sanitize_filename(title)
        if author:
            author = self.sanitize_filename(author)
            file_name = f'{author}_{title}.mp4'
        else:
            file_name = f'{title}.mp4'

        file_path = os.path.join(self.output_dir, file_name)

        counter = 1
        while os.path.exists(file_path):
            if author:
                file_path = os.path.join(self.output_dir, f'{author}_{title}_{counter}.mp4')
            else:
                file_path = os.path.join(self.output_dir, f'{title}_{counter}.mp4')
            counter += 1

        try:
            spider.logger.info(f'Downloading video from: {video_url[:80]}...')
            spider.logger.info(f'Expected size: {adapter.get("size_mb", "unknown")} MB')

            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.kuaishou.com/',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            })

            response = session.get(
                video_url,
                stream=True,
                timeout=(30, 300),
                allow_redirects=True
            )
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            spider.logger.info(f'Actual content length: {total_size / 1024 / 1024:.2f} MB')

            downloaded = 0
            chunk_size = 64 * 1024
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded % (1024 * 1024) == 0:
                            spider.logger.info(f'Downloaded: {downloaded / 1024 / 1024:.2f} MB')

            spider.logger.info(f'Video successfully saved to: {file_path}')
            spider.logger.info(f'Total downloaded: {downloaded / 1024 / 1024:.2f} MB')
            adapter['file_path'] = file_path

        except Exception as e:
            spider.logger.error(f'Failed to download video: {str(e)}')
            if os.path.exists(file_path):
                os.remove(file_path)
            raise DropItem(f"Failed to download video: {str(e)}")

        return item

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip()
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else 'kuaishou_video'
