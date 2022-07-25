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
import os
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
# runs the skin sales webscraper and automatically updates all the skins on sale in the league shop
# import skin_sales_spider

help_command = commands.DefaultHelpCommand(no_category='List of Zoe Bot Commands')
intents = discord.Intents.default()
intents.members = True


class BaseCommand(commands.Bot):
    """The parent of all Zoe Bot Commands.
    If I make the files in Commands/ extensions of this BaseCommand class, will it make multiple instances of the bot
    to run the same command a bunch of times? Will it break everything? I have no idea
    """
    def __init__(self):
        super().__init__(
            command_prefix='~',
            help_command=help_command,
            description="I'm Zoe, what's your name?",
            intents=intents
        )
        self.champ_dict = constants.CHAMP_DICT
        self.champ_skins_set = constants.CHAMP_SKINS_DICT
        self.cache = dict()
        self.bot = commands.Bot(
            command_prefix='~',
            help_command=help_command,
            description="I'm Zoe, what's your name?",
            intents=intents)
        self.db = constants.DB
        self.favorite_skin_db = constants.SKIN_DB
        self.free_champ_ids = constants.FREE_CHAMPION_IDS

        @self.event
        async def on_ready():
            cache_clear_hours = 2
            check_tracked_mins = 3 * 60
            activity = discord.Game(name="Do something fun! The world might be ending... Or not!")
            await bot.change_presence(status=discord.Status.online, activity=activity)
            await check_tracked_skins(self)
            while True:
                # Champions being followed in pro play are tracked in this loop
                await check_tracked_champions(self)
                await clear_cache(self.cache, cache_clear_hours)
                await asyncio.sleep(check_tracked_mins)

        @self.command(hidden=True)
        @commands.is_owner()
        async def shutdown(c):
            await c.channel.send("Logging out...")
            await bot.close()

        @self.command(hidden=True)
        @commands.is_owner()
        async def update_skin_sales(channel, *args):
            """
            Command to manually run the skin sales webscraper AND notify users about their liked champs
            """
            args = ' '.join(args)
            if args.lower() == 'spider':
                os.system('python skin_sales_spider.py')
                await channel.send("Successfully updated this week's champion skin sales.")
            await check_tracked_skins(self)
            await channel.send("Successfully notified users about their favorite champions' skin sales.")

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

        @self.command(brief="Show live professional games of a champion",
                      description="Given a champion's name, shows a list of all live professional games where the "
                                  "champion is being played, or use '~live all' to see a list of all champions in "
                                  "live games")
        async def live(channel, *champion_name):
            await LiveCommand.live(channel, *champion_name)

        @self.command(hidden=True,
                      brief="Show Zoe matchup tips! (WIP)",
                      description="View Zoe's matchup statistics against a champion")
        async def matchup(channel, champion):
            """WORK IN PROGRESS"""
            champion.lower()
            await channel.send(get_zoe_error_message())

        @matchup.error
        async def matchup_error(ctx, error):
            if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
                await ctx.send(
                    "use '~matchup <champion>' to search for Zoe's matchup statistics against a champion!")

        @self.command(hidden=True,
                      brief="Paddle Star Damage Calculator (WIP)",
                      description="Zoe Q damage calculator based on items, runes, and masteries")
        async def psdc(channel):
            """WORK IN PROGRESS"""
            await channel.send(get_zoe_error_message())

        @self.command(brief="Show the weekly free champion rotation",
                      description="Weekly free to play champion rotation for summoner level 11+ accounts")
        async def rotation(c):
            await WeeklyRotationCommand.rotation(c, self)

        # I'm leaving this method without its own Command file because when i move it to its own file, image flipping
        # breaks lol
        @self.command(brief="Show champion skins on sale this week",
                      description="Show list of all champion skins on sale (which refreshes every Monday at 3 pm EST),"
                                  "or use '~sale all' to see a list of all skins on sale "
                                  "(not recommended by yours truly, because I think it's quite ugly, but it's more "
                                  "convenient I guess")
        async def sale(channel, *kwargs):
            command_args = ' '.join(kwargs)
            if command_args.lower() == 'all':
                await SaleCommand.sale(channel)
                return
            skin_sales_data = []
            # bot = base_command.bot
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
                    embed_dict['footer']['text'] = \
                        f"{count + 1}/{len(image_urls_list)}\nShop refreshes every Monday at 3 pm EST "
                    embed = discord.Embed.from_dict(embed_dict)
                    await msg.edit(embed=embed)
                except (Exception,):
                    return

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

        @self.command(hidden=True)
        async def test(channel):
            await SaleCommand.sale(channel, self)


bot = BaseCommand()


def main():
    # Start up the bot
    with open('Data/alpha_token') as f:
        token = f.readline()
    bot.run(token)


if __name__ == "__main__":
    main()
