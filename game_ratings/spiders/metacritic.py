import os
import time

import pandas as pd
import scrapy
from game_ratings.items import GameRatingsItem
from scrapy.http import request
from tqdm import tqdm


class MetacriticSpider(scrapy.Spider):
    name = 'metacritic'
    allowed_domains = ['metacritic.com']
    custom_settings = {
        'LOG_LEVEL': 'ERROR'
    }

    url_format = 'https://www.metacritic.com/browse/games/score/metascore/all/all/filtered?view=detailed&page=%d'
    delay = 3
    last_page = 0

    def start_requests(self):
        yield scrapy.Request(url=self.url_format % 0, callback=self.parse)

    def parse(self, response):
        def retry_request(response):
            time.sleep(self.delay)
            return scrapy.Request(response.url, callback=self.parse, dont_filter=True)

        current_page = response.url.split('&page=')[-1]
        if current_page is None:
            yield retry_request(response)
            return
        current_page = int(current_page)

        if self.last_page == 0:
            last_page = response.css(
                '.last_page > .page_num::text').get()
            if last_page is None:
                yield retry_request(response)
                return
            self.last_page = int(last_page)
            self.pbar = tqdm(total=self.last_page,
                             desc="Listing games", unit='page')
            for page in range(current_page + 1, self.last_page):
                time.sleep(self.delay)
                yield scrapy.Request(url=self.url_format % page, callback=self.parse)

        lines = response.css('.clamp-list tr')[::2]
        if len(lines) == 0:
            yield retry_request(response)
            return

        results = []
        for line in lines:
            date_str = line.css('.clamp-details > span::text').get()
            date = pd.to_datetime(date_str).date()
            title = line.css('.title > h3::text').get()
            platform = line.css('.data::text').get().strip()
            score = line.css(
                '.clamp-score-wrap > .metascore_anchor > .metascore_w::text').get()
            must_play = False
            must_play_icon = line.css('.mcmust').get()
            if must_play_icon is not None:
                must_play = True

            result = f'{date},"{title}",{platform},{score},{must_play}'
            results.append(result)
        if len(results) == 0:
            yield retry_request(response)
            return

        yield GameRatingsItem(page=current_page, results=results)
