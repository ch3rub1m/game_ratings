# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GameRatingsItem(scrapy.Item):
    page = scrapy.Field()
    results = scrapy.Field()
