
import json
import os
# from datetime import datetime

import scrapy
from scrapy.crawler import CrawlerProcess

# TODO: re import these when jpg file reading is fixed

# import shutil
# from imageio.v2 import imread, imwrite
# import numpy as np
# import cv2
# import requests


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
    def parse(self, response, **kwargs):
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

    def close(self, **kwargs):
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

    """
    Create JPG images of each individual splashart (not to be used in an embed which require url and not a jpg), then
    put them all together in a large jpg image of all skin sales
    """
    # reset images for sales command
    # images = []
    with open("Data/skin_sales_data.json", 'r') as file:
        skins_sale_dictionary = json.load(file)
    # iterate through dictionary
    # count = 0
    with open("Data/image_urls_list.txt", 'w') as image_urls_file:
        # Write each splash art img url to a list of urls
        for entry in skins_sale_dictionary:
            image_url = entry['skin_image']
            image_url_list = image_url.split(' ')
            image_url = image_url_list[1].replace('src=', '').replace('"', '')
            image_urls_file.write(image_url + '\n')
    # TODO: Fix writing to jpg img files for weekly skin sale splash arts

    #         r = requests.get(image_url,
    #                          stream=True, headers={'User-agent': 'Mozilla/5.0'})
    #         if r.status_code == 200:
    #             # Write a single skin splashart to the Data/skin_sale_jpgs dir
    #             with open(f"Data/skin_sale_jpgs/single_skin_image{count}.jpg", 'wb') as file:
    #                 r.raw.decode_content = True
    #                 shutil.copyfileobj(r.raw, file)
    #                 image = imread(file.name)[..., :3]
    #                 x = int(image.shape[1] * 1)
    #                 y = int(image.shape[0] * 1)
    #                 # resizing image
    #                 image = cv2.resize(image, dsize=(x, y), interpolation=cv2.INTER_CUBIC)
    #                 # cropping image
    #                 x_crop_amount = int(x * 0)
    #                 y_crop_amount = int(y * 0)
    #                 image = image[y_crop_amount: y - y_crop_amount, x_crop_amount:x - x_crop_amount]
    #                 images.append(image)
    #         count += 1
    # # 5 x 3 display
    # rows = np.hstack(images[0:5]), np.hstack(images[5:10]), np.hstack(images[10:15])
    # # 3 x 5 display
    # # rows = np.hstack(images[0:3]), np.hstack(images[3:6]), np.hstack(images[6:9]), np.hstack(images[9:12]), \
    # #        np.hstack(images[12:15])
    # full_image = np.vstack(rows)
    # # Full image of all 15 sale skins
    # imwrite('Data/full_skin_sales_image.jpg', full_image)
    print(f'Skin sales spider finished scraping!')


main()
