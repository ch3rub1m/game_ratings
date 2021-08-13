import datetime as dt
import os
import time
from sys import platform
from urllib.parse import urlparse

import pandas as pd
import scrapy
from game_ratings.items import GameRatingsItem
from html2text import HTML2Text, html2text
from scrapy.http import request
from tqdm import tqdm


class SoftDBSpider(scrapy.Spider):
    name = 'soft_db'

    platform_dict = {
        'ds-collection.net': 'DS',
        'ps3-collection.net': 'PS3',
        '3ds.soft-db.net': '3DS',
        'psvita.soft-db.net': 'Vita',
        'wiiu.soft-db.net': 'Wii U',
        'ps4.soft-db.net': 'PS4',
        'switch.soft-db.net': 'Switch'
    }
    allowed_domains = list(platform_dict.keys())

    ds_page = 0

    custom_settings = {
        'LOG_LEVEL': 'ERROR'
    }

    delay = 3

    def start_requests(self):
        self.pbar = tqdm(total=11 * len(self.allowed_domains),
                         desc="Listing games", unit='page')
        for domain in self.allowed_domains:
            if self.platform_dict[domain] == 'DS':
                self.pbar.total -= 10
                yield scrapy.Request(url=f'http://{domain}/best/best_01.html', callback=self.parse_ds, errback=self.errback)
            else:
                for score in range(30, 41):
                    yield scrapy.Request(url=f'http://{domain}/dendo/dendo_{score}', callback=self.parse, errback=self.errback)

    def parse_ds(self, response):
        domain = urlparse(response.url).netloc
        if self.ds_page == 0:
            links = response.css('.page')[0].css('a::attr(href)').getall()[:-1]
            self.ds_page += len(links)
            self.pbar.total += self.ds_page
            for link in links:
                yield scrapy.Request(url=f'http://{domain}/best/{link}', callback=self.parse_ds, errback=self.errback)

        year = response.url.removesuffix('.html').split('/best_')[-1]
        year = int(year)

        results = []
        lines = response.css('#myTable > tbody > tr')
        for line in lines:
            attributes = line.css('.ttl > a::text, td::text').getall()
            if attributes[4] == '-':
                continue
            date = dt.datetime.strptime(attributes[5], '%y.%m.%d').date()
            score = int(attributes[4])
            result = f'{date},"{attributes[1]}",DS,{score}'
            results.append(result)

        if year == 1:
            year = 9999
            results = reversed(results)

        yield GameRatingsItem(page=year, results=results)

    def parse(self, response):
        def retry_request(response):
            time.sleep(self.delay)
            return scrapy.Request(response.url, callback=self.parse, dont_filter=True)

        domain = urlparse(response.url).netloc
        platform = self.platform_dict[domain]

        score = response.url.removesuffix('.html').split('/dendo_')[-1]
        if score is None:
            yield retry_request(response)
            return
        score = int(score)

        results = []
        lines = response.css('.dendo table > tbody > tr')
        for line in lines:
            title = line.css('td > a::text').get()
            date_str = line.css('.ctr::text').get()
            date = dt.datetime.strptime(date_str, '%y.%m.%d').date()
            result = f'{date},"{title}",{platform},{score}'
            results.append(result)

        yield GameRatingsItem(page=score, results=results)

    def errback(self, failure):
        if failure.value.response.status == 404:
            self.pbar.total -= 1
