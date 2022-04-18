import scrapy
from scrapy.crawler import CrawlerProcess


class SkinSalesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = [
        'https://www.riftfeed.gg/lol-skins/lol-skins-sale/',
    ]

    # parse data from 'https://www.riftfeed.gg/lol-skins/lol-skins-sale/' to get all skins on sale and their
    # current RP cost
    def parse(self, response):
        # skin images go from 4-18 to account for other images on the page
        for index in range(4, 18):
            # skin name and rp cost starts at index 1, whereas skin image starts at index 4, hence the index - 3 offset
            skin_name_rp_cost = self.get_skin_name_rp_cost_by_index(response, index - 3)
            yield {
                'skin_image': self.get_image_by_index(response, index),
                'skin_name': skin_name_rp_cost[0],
                'rp_cost': skin_name_rp_cost[1]
            }

    # # get skin name and rp cost by index of riftfeed webpage
    # '<b>15. Frostfire Annie (390 RP):</b>' -> ("Frostfire Annie", "390 RP"
    def get_skin_name_rp_cost_by_index(self, response, index):
        text = response.xpath(f'//div/div/section[2]/div/div[1]/div[1]/div[1]/div[{index}]/div[2]/div/p/b').get()
        skin_data = text.split(' ')
        rp_cost_index = len(skin_data) - 1
        rp_cost = f"{str(skin_data[rp_cost_index].replace('(', ''))} RP"
        skin_name_data = skin_data[1:rp_cost_index - 1]
        skin_name = ' '.join(skin_name_data)
        return skin_name, rp_cost

    # given all images on the webpage, return the image by index
    def get_image_by_index(self, response, index):
        images = response.css('img')
        return images[index].xpath('@src').get()


# process = CrawlerProcess({
#     'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
# })
#
# process.crawl(SkinSalesSpider)
# process.start()
