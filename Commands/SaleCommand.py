import Data
import asyncio
import discord
import json
import random
from Data import Quotes


async def sale(channel):
    sale_skins_name_rp_costs = []
    embed = discord.Embed(title="Champion skins sale:",
                          description="\n", color=0x87cefa)
    try:
        with open("Data/skin_sales_data.json", 'r') as file:
            dictionary = json.load(file)
        # iterate through dictionary and get list of skins on sale
        for entry in dictionary:
            skin_name_rp_cost = " ".join(entry['skin_name_rp_cost'].split())
            skin_data = skin_name_rp_cost.split(' ')
            skin_name = skin_data[0: len(skin_data) - 3]
            skin_rp_cost = skin_data[len(skin_data) - 2: len(skin_data)]
            embed.add_field(
                name=f"{' '.join(skin_name)}",
                value=' '.join(skin_rp_cost),
                inline=True)
            sale_skins_name_rp_costs.append(skin_name_rp_cost)
        # skins_sale = '\n'.join(sale_skins_name_rp_costs)
        # await c.channel.send("List of champion skins on sale this week: \n" + skins_sale)
        image_file = discord.File('Data/full_skin_sales_image.jpg', filename='full_skin_sales_image.jpg')
        embed.set_image(url='attachment://full_skin_sales_image.jpg')
        await channel.send(embed=embed, file=image_file)
    except (Exception,):
        await channel.channel.send(random.choice(Quotes.Zoe_error_message))
