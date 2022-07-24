import Data
import asyncio
import discord
import json
import random
from Data import Quotes


async def sale(channel, base_command):
    """THIS COMMAND IS CURRENTLY NOT IN USE"""
    sale_skins_name_rp_costs = []
    bot = base_command.bot
    with open("Data/skin_sales_data.json", 'r') as file:
        dictionary = json.load(file)
    # iterate through dictionary and get list of skins on sale
    for entry in dictionary:
        skin_name_rp_cost = " ".join(entry['skin_name_rp_cost'].split())
        # skin_data = skin_name_rp_cost.split(' ')
        # skin_name = skin_data[0: len(skin_data) - 3]
        # skin_rp_cost = skin_data[len(skin_data) - 2: len(skin_data)]
        sale_skins_name_rp_costs.append(skin_name_rp_cost)

    image_urls_file = open("Data/image_urls_list.txt", "r")
    image_urls_list = []
    for image_url in image_urls_file:
        image_urls_list.append(image_url)

    left_arrow = "⬅"
    right_arrow = "➡"
    image_urls_file = open("Data/image_urls_list.txt", "r")
    image_urls_list = []
    for image_url in image_urls_file:
        image_urls_list.append(image_url)
    count = 0
    embed = discord.Embed(color=0xffb6c1)
    embed.add_field(name="Champion Skins Sale", value="your mom", inline=False)
    embed.set_image(url=image_urls_list[count])

    msg = await channel.send(embed=embed)
    await msg.add_reaction(left_arrow)
    await msg.add_reaction(right_arrow)

    def check(r, u):
        return u == channel.author and str(r.emoji) in [left_arrow, right_arrow]

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == left_arrow:
                count = count - 1 if count > 0 else 15
            if str(reaction.emoji) == right_arrow:
                count = count + 1 if count < 15 else 0
            embed = discord.Embed(
                color=0xffb6c1)
            embed.add_field(name="Champion Skins Sale", value=sale_skins_name_rp_costs[count], inline=False)
            embed.set_image(url=image_urls_list[count])
            await msg.edit(embed=embed)
        except (Exception,):
            pass