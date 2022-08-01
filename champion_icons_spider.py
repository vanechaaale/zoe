import json

import scrapy


class SkinSalesSpider(scrapy.Spider):
    name = "Champion icons"
    start_urls = [
        'https://na.op.gg/champions',
    ]
    data = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_callback = kwargs.get('args').get('callback')

    # parse data from op.gg to get all champion icons and champ name
    def parse(self, response, **kwargs):
        champ_icon_data = response.xpath(
            '//div[5]/div[2]/aside/nav/ul/li/a/img').getall()
        champion_name = response.xpath('//div[5]/div[2]/aside/nav/ul/li/a/span').getall()
        for index, value in enumerate(champ_icon_data):
            self.data.append({
                'skin_image': champion_name[index],
                'skin_name_rp_cost': value
            })
        json_data = json.dumps(self.data)
        with open('Data/skin_sales_data.json', 'w') as outfile:
            outfile.write(json_data)

    def close(self, **kwargs):
        self.output_callback(self.data)
