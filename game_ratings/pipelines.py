# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import os
import sys
from collections import defaultdict

from itemadapter import ItemAdapter

# useful for handling different item types with a single interface


class GameRatingsPipeline:
    dict = defaultdict(list)

    def process_item(self, item, spider):
        page = item['page']
        results = item['results']
        self.dict[page] += results

        spider.pbar.update(1)

    def close_spider(self, spider):
        filename = f'{spider.name}.csv'
        home = os.path.expanduser('~')
        path = getattr(self, 'path', f'{home}/Documents')
        filepath = f'{path}/{filename}'
        with open(filepath, 'w') as f:
            f.write('date,title,platform,score,mustplay\n')
            for page, results in sorted(self.dict.items()):
                for result in results:
                    f.write(f'{result}\n')
