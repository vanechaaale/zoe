import cv2
import json
import numpy as np
import os
import requests
import scrapy
import shutil
from imageio import imread, imwrite
from scrapy.crawler import CrawlerProcess
from urllib.request import Request, urlopen


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


def main():
    # clear current json data file and then scrape again
    if os.path.exists("Data/skin_sales_data.json"):
        os.remove("Data/skin_sales_data.json")
    crawler = CustomCrawler()
    crawler.crawl(SkinSalesSpider)

    # reset images for sales command
    images = []
    with open("Data/skin_sales_data.json", 'r') as file:
        dictionary = json.load(file)
    # iterate through dictionary
    for entry in dictionary:
        image_url = entry['skin_image']
        image_url_list = image_url.split(' ')
        image_url = image_url_list[1].replace('src=', '').replace('"', '')
        r = requests.get(image_url,
                         stream=True, headers={'User-agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            with open("Data/single_skin_image.jpg", 'wb') as file:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, file)
                image = imread(file.name)[..., :3]
                x = int(image.shape[1] * .8)
                y = int(image.shape[0] * .8)
                # resizing image
                image = cv2.resize(image, dsize=(x, y), interpolation=cv2.INTER_CUBIC)
                # cropping image
                x_crop_amount = int(x * .12)
                y_crop_amount = int(y * .05)
                image = image[y_crop_amount: y - y_crop_amount, x_crop_amount:x - x_crop_amount]
                images.append(image)
    # 5 x 3 display
    rows = np.hstack(images[0:5]), np.hstack(images[5:10]), np.hstack(images[10:15])
    # 3 x 5 display
    # rows = np.hstack(images[0:3]), np.hstack(images[3:6]), np.hstack(images[6:9]), np.hstack(images[9:12]), \
    #        np.hstack(images[12:15])
    full_image = np.vstack(rows)
    imwrite('Data/full_skin_sales_image.jpg', full_image)


if __name__ == "__main__":
    main()
