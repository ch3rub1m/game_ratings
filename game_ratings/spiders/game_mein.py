import datetime as dt
import os
import time

import pandas as pd
import scrapy
from game_ratings.items import GameRatingsItem
from html2text import HTML2Text, html2text
from scrapy.http import request
from tqdm import tqdm


class GameMeinSpider(scrapy.Spider):
    name = 'game_mein'
    allowed_domains = ['ne.jp']
    custom_settings = {
        'LOG_LEVEL': 'ERROR'
    }

    delay = 3

    def start_requests(self):
        self.pbar = tqdm(total=30, desc="Listing games", unit='page')
        for year in range(1986, 2016):
            yield scrapy.Request(url=f'http://www.ne.jp/asahi/dq/dq/meisaku/{year}', callback=self.parse)

    def parse(self, response):
        def retry_request(response):
            time.sleep(self.delay)
            return scrapy.Request(response.url, callback=self.parse, dont_filter=True)

        year = response.url.split('/')[-1]
        if year is None:
            yield retry_request(response)
            return
        year = int(year)

        results = []
        lines = response.css('table table')[-1].css('tr~tr')

        if len(lines[1].css('td')) == 5:
            current_score = 0
            for line in lines:
                columns = line.css('td')
                if len(columns) == 1:
                    score = int(columns.css(
                        'div font::text').get().split('点')[0])
                    current_score = score
                else:
                    handler = HTML2Text()
                    handler.ignore_links = True
                    attributes = []
                    for column in columns:
                        textHTML = column.css('font > a, a > font').get()
                        if textHTML is None:
                            textHTML = column.css('font, a').get()
                        text = handler.handle(textHTML)
                        attribute = " ".join(text.split())
                        attributes.append(attribute)
                    strs = attributes[3].split('/')
                    if len(strs) >= 2:
                        date = dt.date(year=year, month=int(
                            strs[-2]), day=int(strs[-1]))
                    else:
                        date = f'{year}-{attributes[3]}'

                    platform = attributes[0]
                    if platform == 'XB':
                        platform = 'Xbox'
                    if platform == 'XB-360' or platform == 'XB360' or platform == 'XB 360':
                        platform = 'Xbox 360'
                    if platform == 'XB One' or platform == 'XB ONE' or platform == 'XB one':
                        platform = 'Xbox One'
                    if platform == 'vita':
                        platform = 'Vita'

                    result = f'{date},"{attributes[1]}",{platform},{current_score}'
                    results.append(result)

        if len(lines[1].css('td')) == 2:
            current_score = 0
            for line in lines:
                columns = line.css('td')
                if html2text(columns[1].get()).strip() == '':
                    score = int(columns.css(
                        'font::text').get().split('点')[0])
                    current_score = score
                else:
                    attributes = [" ".join(html2text(column.css('font').getall()[
                        0]).split()) for column in columns]
                    strs = attributes[0].split('/', 1)

                    platform = strs[0]
                    if platform == 'XB':
                        platform = 'Xbox'
                    if platform == 'XB-360' or platform == 'XB360' or platform == 'XB 360':
                        platform = 'Xbox 360'
                    if platform == 'XB One' or platform == 'XB ONE' or platform == 'XB one':
                        platform = 'Xbox One'
                    if platform == 'vita':
                        platform = 'Vita'

                    result = f'{year},"{strs[1]}",{platform},{current_score}'
                    results.append(result)

        yield GameRatingsItem(page=year, results=results)
