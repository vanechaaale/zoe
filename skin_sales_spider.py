import scrapy
from scrapy.crawler import CrawlerProcess
import json
import os


# Python script to scrape earlygame.com for skin sales
class SkinSalesSpider(scrapy.Spider):
    name = "skin sales"
    start_urls = [
        'https://earlygame.com/lol/lol-skins-sale/',
    ]
    data = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_callback = kwargs.get('args').get('callback')

    # parse data from earlygame.com to get all skins on sale and their current RP cost
    def parse(self, response):
        skin_name_rp_costs = response.xpath(
            '//div/div/div[3]/div[1]/div[1]/div[1]/figure/figcaption/h2/text()').getall()
        images = response.xpath('//div/div/div[3]/div[1]/div[1]/div[1]/figure/picture/img').getall()
        for index, value in enumerate(skin_name_rp_costs):
            self.data.append({
                'skin_image': images[index],
                'skin_name_rp_cost': value
            })
        json_data = json.dumps(self.data)
        with open('Data/skin_sales_data.json', 'w') as outfile:
            outfile.write(json_data)

    def close(self):
        self.output_callback(self.data)

    # def run_spider(self):
    #     process = CrawlerProcess(
    #         # {'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'},
    #         settings={"FEEDS": {"Data/items.json": {"format": "json"}, }},
    #     )
    #     process.crawl(SkinSalesSpider)
    #     process.start()


class CustomCrawler:

    def __init__(self):
        self.output = None
        self.process = CrawlerProcess(settings={'LOG_ENABLED': False})

    def yield_output(self, data):
        self.output = data

    def crawl(self, cls):
        self.process.crawl(cls, args={'callback': self.yield_output})
        self.process.start()


# clear current json data file and then scrape again
if os.path.exists("Data/skin_sales_data.json"):
    os.remove("Data/skin_sales_data.json")
crawler = CustomCrawler()
crawler.crawl(SkinSalesSpider)
