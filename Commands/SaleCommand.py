import json
import random

import discord

from Data import Quotes


async def sale(channel, bot):
    skin_sales_data = []
    with open("Data/skin_sales_data.json", 'r') as file:
        dictionary = json.load(file)
    # iterate through dictionary and get list of skins on sale
    for entry in dictionary:
        skin_name_rp_cost = " ".join(entry['skin_name_rp_cost'].split())
        skin_data = skin_name_rp_cost.split(' ')
        skin_name = ' '.join(skin_data[0: len(skin_data) - 3])
        skin_rp_cost = ' '.join(skin_data[len(skin_data) - 2: len(skin_data)])
        skin_sales_data.append((skin_name, skin_rp_cost))

    # List of image URLs
    image_urls_file = open("Data/image_urls_list.txt", "r")
    image_urls_list = []
    for image_url in image_urls_file:
        image_urls_list.append(image_url)

    # Init embed
    count = 0
    embed = discord.Embed(color=0xe8bffb, title="Champion Skin Sales")
    embed.add_field(
        name=skin_sales_data[count][0],
        value=skin_sales_data[count][1],
        inline=False
    )
    embed.set_image(url=image_urls_list[count])
    embed.set_footer(text=f"{count + 1}/{len(image_urls_list)}\nShop refreshes every Monday at 3 pm EST")
    # Add reactions to embed message
    msg = await channel.send(embed=embed)
    msg_id = msg.id
    left_arrow = "⬅"
    right_arrow = "➡"
    await msg.add_reaction(left_arrow)
    await msg.add_reaction(right_arrow)

    # Method to verify that either arrow reaction was made on the embedded message by a non-bot user
    def check(r, u):
        return str(r.emoji) in [left_arrow, right_arrow] and r.message.id == msg_id and not u.bot

    # Reacting to the message will change the current skin displayed
    while True:
        try:
            # User adds a reaction to the message, which is immediately removed
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            await msg.remove_reaction(reaction, user)
            # Edit the embed message to reflect new skin image and name
            if str(reaction.emoji) == left_arrow:
                count = count - 1 if count > 0 else 14
            if str(reaction.emoji) == right_arrow:
                count = count + 1 if count < 14 else 0
            embed_dict = embed.to_dict()
            embed_dict['fields'][0]['name'] = skin_sales_data[count][0]
            embed_dict['fields'][0]['value'] = skin_sales_data[count][1]
            embed_dict['image']['url'] = image_urls_list[count]
            # embed_dict['footer']['text'] = \
            # f"{count + 1}/{len(image_urls_list)}\nShop refreshes every Monday at 3 pm EST "
            embed = discord.Embed.from_dict(embed_dict)
            await msg.edit(embed=embed)
        except (Exception,):
            return


async def sale_all(c):
    """The original sale command for Zoe Bot, which showed the list of all champion skins on sale and an image collage
    of all splash arts for skins that were on sale"""
    sale_skins_name_rp_costs = []
    embed = discord.Embed(title="Champion skins sale:",
                          description="The shop resets every Monday at 3pm EST", color=0xe8bffb)
    try:
        with open("Data/skin_sales_data.json", 'r') as file:
            dictionary = json.load(file)
        # iterate through dictionary
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
        await c.send(embed=embed, file=image_file)
    except (Exception,):
        await c.channel.send(random.choice(Quotes.Zoe_error_message))
    return
