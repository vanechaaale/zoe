import BaseMessageResponse
import Commands
import Data
import PIL
import asyncio
import constants
import cv2
import discord
import json
import numpy as np
import random
import re
import requests
import shutil
import threading
import time
from Commands import GuideCommand, LiveCommand, SaleCommand, FollowProCommand, FollowSkinCommand, WeeklyRotationCommand
from Data import Quotes, gifs
from PIL import Image
from constants import *
from discord import Webhook, RequestsWebhookAdapter, File
from discord.ext import commands
from discord.ext.commands import Context
from fuzzywuzzy import fuzz
from imageio import imread, imwrite
from lolesports_api import Lolesports_API
from riotwatcher import LolWatcher
from threading import Thread
from tinydb import TinyDB, Query, where
from urllib.request import Request, urlopen

help_command = commands.DefaultHelpCommand(no_category='List of Zoe Bot Commands')
intents = discord.Intents.default()
intents.members = True


class BaseCommand(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='~',
            help_command=help_command,
            description="I'm Zoe, what's your name?",
            intents=intents
        )

        # read API key for lolesports api
        with open('Data/api_key') as f:
            API_KEY = f.readline()
        LOL_ESPORTS_LIVE_LINK = 'https://lolesports.com/live/'
        API = Lolesports_API()
        WATCHER = LolWatcher(API_KEY)
        my_region = 'na1'

        # check league's latest patch version
        latest = WATCHER.data_dragon.versions_for_region(my_region)['n']['champion']
        # get some champions static information
        static_champ_list = WATCHER.data_dragon.champions(latest, False, 'en_US')
        CHAMP_DICT = {}
        for key in static_champ_list['data']:
            row = static_champ_list['data'][key]
            name = row['name']
            CHAMP_DICT[row['key']] = name
        self.champ_dict = CHAMP_DICT
        self.cache = dict()
        self.bot = commands.Bot(
            command_prefix='~', help_command=help_command,
            description="I'm Zoe, what's your name?", intents=intents)
        # USING ALPHA DATABASES
        self.db = TinyDB('Data/test_database.json')
        self.skin_db = TinyDB('Data/test_skin_database.json')
        self.free_champ_ids = WATCHER.champion.rotations(my_region)

        @self.event
        async def on_ready():
            cache_clear_hours = 2
            check_tracked_mins = 3 * 60
            activity = discord.Game(name="Do something fun! The world might be ending... Or not!")
            await bot.change_presence(status=discord.Status.online, activity=activity)
            while True:
                await check_tracked_champions(self)
                await clear_cache(self.cache, cache_clear_hours)
                await asyncio.sleep(check_tracked_mins)

        @self.command(hidden=True)
        @commands.is_owner()
        async def shutdown(c):
            await c.channel.send("Logging out...")
            await bot.close()

        @self.event
        async def on_guild_join(guild):
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    quote = random.choice(Quotes.Zoe_join_server_message)
                    await channel.send(f'"*{quote}*"')
                break

        @self.event
        async def on_command_error(channel, error):
            if isinstance(error, commands.CommandNotFound):
                return
            else:
                await channel.send(error)

        @self.listen()
        async def on_message(message):
            if message.author == bot.user:
                return
            for cmd in BaseMessageResponse.RESPONSES:
                if cmd.invoke(message) and not is_command(message):
                    await cmd.execute(message)
            if message.is_system() and message.type == discord.MessageType.new_member:
                quote = random.choice(Quotes.Greet)
                await message.channel.send(f'"*{quote}*"')

        @self.command(brief="Show Zoe guides", description="List of Zoe guides and Zoe players!")
        async def guide(channel):
            await GuideCommand.guide(channel)

        @self.command(brief="Zoe gifs.", description="Beautiful Zoe gifs.")
        async def gif(channel):
            await channel.send(random.choice(gifs.gifs))

        @self.command(brief="Show Zoe matchup tips! (WIP)",
                      description="View Zoe's matchup statistics against a champion")
        async def matchup(channel, champion):
            champion.lower()
            await channel.send(get_zoe_error_message())

        @matchup.error
        async def matchup_error(ctx, error):
            if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
                await ctx.send(
                    "use '~matchup <champion>' to search for Zoe's matchup statistics against a champion!")

        @self.command(brief="Paddle Star Damage Calculator (WIP)",
                      description="Zoe Q damage calculator based on items, runes, and masteries")
        async def psdc(channel):
            await channel.send(get_zoe_error_message())

        @self.command(brief="Show the weekly free champion rotation",
                      description="Weekly free to play champion rotation for summoner level 11+ accounts")
        async def rotation(c):
            await WeeklyRotationCommand.rotation(c, self)

        # I'm leaving this method without its own Command class because when i move it to its own file, image flipping
        # breaks lol
        @self.command(brief="Show champion skins on sale this week",
                      description="Show list of all champion skins on sale, which refreshes every Monday at 3 pm EST")
        async def sale(channel):
            sale_skins_name_rp_costs = []
            # bot = base_command.bot
            with open("Data/skin_sales_data.json", 'r') as file:
                dictionary = json.load(file)
            # iterate through dictionary and get list of skins on sale
            for entry in dictionary:
                skin_name_rp_cost = " ".join(entry['skin_name_rp_cost'].split())
                # skin_data = skin_name_rp_cost.split(' ')
                # skin_name = skin_data[0: len(skin_data) - 3]
                # skin_rp_cost = skin_data[len(skin_data) - 2: len(skin_data)]
                sale_skins_name_rp_costs.append(skin_name_rp_cost)

            # List of image URLs
            image_urls_file = open("Data/image_urls_list.txt", "r")
            image_urls_list = []
            for image_url in image_urls_file:
                image_urls_list.append(image_url)

            # Init embed
            count = 0
            embed = discord.Embed(color=0xffb6c1, title="Weekly Champion Skins Sale")
            embed.add_field(
                value="Shop refreshes every Monday at 3 pm EST",
                name=sale_skins_name_rp_costs[count],
                inline=False
            )
            embed.set_image(url=image_urls_list[count])
            embed.set_footer(text=f"{count + 1}/{len(image_urls_list)}                 "
                                  f"Shop refreshes every Monday at 3 pm EST")
            # Add reactions to embed message
            msg = await channel.send(embed=embed)
            msg_id = msg.id
            left_arrow = "⬅"
            right_arrow = "➡"
            await msg.add_reaction(left_arrow)
            await msg.add_reaction(right_arrow)

            # Method to verify that the correct reactions were made
            def check(r, u):
                return u == channel.author and str(r.emoji) in [left_arrow, right_arrow] \
                       and r.message.id == msg_id

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
                    embed_dict['fields'][0]['name'] = sale_skins_name_rp_costs[count]
                    embed_dict['image']['url'] = image_urls_list[count]
                    embed_dict['footer']['text'] = f"{count + 1}/{len(image_urls_list)}                 " \
                                                   f"Shop refreshes every Monday at 3 pm EST"
                    embed = discord.Embed.from_dict(embed_dict)
                    await msg.edit(embed=embed)
                except (Exception,):
                    pass

        @self.command(brief="Show live professional games of a champion",
                      description="Given a champion's name, shows a list of all live professional games where the "
                                  "champion is being played, or use '~live all' to see a list of all champions in "
                                  "live games")
        async def live(channel, *champion_name):
            await LiveCommand.live(channel, self, *champion_name)

        @self.command(brief="Get notified when a champion has a skin on sale",
                      description="Receive messages from Zoe Bot whenever the given champion has a skin on sale")
        async def favorite(message, *champion_name):
            await FollowSkinCommand.favorite(message, self, *champion_name)

        @self.command(brief="Show list of favorite champions",
                      description="Show a list of all champions that Zoe Bot will notify a Discord User for when one "
                                  "or more champs have skins on sale. Remove a champion from "
                                  "this list with the command '~favorite <champion_name>'.")
        async def favlist(message):
            await FollowSkinCommand.favlist(message, self)

        @self.command(brief="Follow a champion in professional play",
                      description="Receive messages from Zoe Bot whenever the given champion is being played in a "
                                  "professional game, or use the command again to stop receiving notifications from "
                                  "Zoe Bot.")
        async def follow(message, *champion_name):
            await FollowProCommand.follow(message, self, *champion_name)

        @self.command(brief="Show all followed champions",
                      description="Show a list of all champions that Zoe Bot will notify a Discord User for when one "
                                  "or more champs are being played in a professional game. Remove a champion from "
                                  "this list with the command '~track <champion_name>'.")
        async def following(message):
            await FollowProCommand.following(message, self)

        @self.command()
        async def test(channel):
            await SaleCommand.sale(channel, self)
            # sale_skins_name_rp_costs = []
            # # bot = base_command.bot
            # with open("Data/skin_sales_data.json", 'r') as file:
            #     dictionary = json.load(file)
            # # iterate through dictionary and get list of skins on sale
            # for entry in dictionary:
            #     skin_name_rp_cost = " ".join(entry['skin_name_rp_cost'].split())
            #     # skin_data = skin_name_rp_cost.split(' ')
            #     # skin_name = skin_data[0: len(skin_data) - 3]
            #     # skin_rp_cost = skin_data[len(skin_data) - 2: len(skin_data)]
            #     sale_skins_name_rp_costs.append(skin_name_rp_cost)
            #
            # image_urls_file = open("Data/image_urls_list.txt", "r")
            # image_urls_list = []
            # for image_url in image_urls_file:
            #     image_urls_list.append(image_url)
            #
            # left_arrow = "⬅"
            # right_arrow = "➡"
            # image_urls_file = open("Data/image_urls_list.txt", "r")
            # image_urls_list = []
            # for image_url in image_urls_file:
            #     image_urls_list.append(image_url)
            # count = 0
            # embed = discord.Embed(color=0xffb6c1)
            # embed.add_field(name="Champion Skins Sale", value="your mom", inline=False)
            # embed.set_image(url=image_urls_list[count])
            #
            # msg = await channel.send(embed=embed)
            # await msg.add_reaction(left_arrow)
            # await msg.add_reaction(right_arrow)
            #
            # def check(r, u):
            #     return u == channel.author and str(r.emoji) in [left_arrow, right_arrow]
            #
            # while True:
            #     try:
            #         reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            #         if str(reaction.emoji) == left_arrow:
            #             count = count - 1 if count > 0 else 15
            #         if str(reaction.emoji) == right_arrow:
            #             count = count + 1 if count < 15 else 0
            #         embed = discord.Embed(
            #             color=0xffb6c1)
            #         embed.add_field(name="Champion Skins Sale", value=sale_skins_name_rp_costs[count], inline=False)
            #         embed.set_image(url=image_urls_list[count])
            #         await msg.edit(embed=embed)
            #     except (Exception,):
            #         pass


async def update_cache(self, user_id, game_info):
    # update cache with new game ids upon seeing them for the first time, else it does nothing and won't msg users
    game_id = game_info['player'][7]
    champion = game_info['player'][1]
    champ_game_tuple = champion, game_id
    if champ_game_tuple not in self.cache:
        self.cache[champ_game_tuple] = datetime.datetime.now()
        user = bot.get_user(user_id)
        await user.send(embed=get_embed_for_player(game_info))

bot = BaseCommand()


def main():
    # Start up the bot
    with open('Data/alpha_token') as f:
        token = f.readline()
    bot.run(token)


if __name__ == "__main__":
    main()
