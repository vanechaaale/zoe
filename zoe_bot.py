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
from Commands import GuideCommand, LiveCommand, SaleCommand, FollowProCommand
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
            try:
                free_rotation = []
                for champion_id in self.free_champ_ids['freeChampionIds']:
                    free_rotation.append(CHAMP_DICT[str(champion_id)])
                free_rotation.sort()
                free_rotation = ', '.join(free_rotation)
                await c.channel.send("The champions in this week's free to play rotation are: " + free_rotation)
            except (Exception,):
                await c.channel.send(get_zoe_error_message())

        @self.command(brief="Show champion skins on sale this week",
                      description="Show list of all champion skins on sale, which refreshes every Monday at 3 pm EST")
        async def sale(channel):
            await SaleCommand.sale(channel)

        @self.command(brief="Show live professional games of a champion",
                      description="Given a champion's name, shows a list of all live professional games where the "
                                  "champion is being played, or use '~live all' to see a list of all champions in "
                                  "live games")
        async def live(channel, *champion_name):
            await LiveCommand.live(channel, self, *champion_name)

        @self.command()
        async def test(message, *champion_name):
            # format champion_name
            champion_name = self.format_champion_name(' '.join(champion_name))
            if not champion_name:
                await message.channel.send(
                    f"use '~test <champion>' to be notified when a champion's skins go on sale!")
                return
            # Query champion user id list
            champion = Query()
            user_id = message.author.id
            skin_db = SKIN_DB
            champ_name_user_ids_dict = skin_db.get(champion['champion_name'] == champion_name)
            # I tried using a set but it broke whenever i called db.insert()
            user_ids_list = [] if champ_name_user_ids_dict is None else champ_name_user_ids_dict['user_ids']
            if champ_name_user_ids_dict is None:
                user_ids_list.append(user_id)
                skin_db.insert({'champion_name': champion_name, 'user_ids': user_ids_list})
                await message.channel.send(f"Now tracking skin sales for {champion_name}.")
            elif user_id not in user_ids_list:
                user_ids_list.append(user_id)
                skin_db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
                await message.channel.send(f"Now tracking skin sales for {champion_name}.")
            else:
                user_ids_list.remove(user_id)
                skin_db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
                await message.channel.send(f"No longer tracking skin sales for {champion_name}.")

        @self.command(brief="Track a champion in professional play",
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

        @self.command
        def test():
            check_tracked_skins()

    async def update_cache(self, user_id, game_info):
        # update cache with new game ids upon seeing them for the first time, else it does nothing and won't msg users
        game_id = game_info['player'][7]
        champion = game_info['player'][1]
        champ_game_tuple = champion, game_id
        if champ_game_tuple not in self.cache:
            self.cache[champ_game_tuple] = datetime.datetime.now()
            user = bot.get_user(user_id)
            await user.send(embed=get_embed_for_player(game_info))

    def get_fuzzy_match(self, champion_name):
        for champ in self.champ_dict.values():
            if fuzz.token_sort_ratio(champ, champion_name) >= 80:
                return champ
        return ''

        # Given a janky version of a champion, format it to be pretty
        #     str given_name: name input as a string
        #     Return properly formatted champion name as a string

    def format_champion_name(self, champion_name):
        champion_name = self.get_fuzzy_match(check_for_special_name_match(champion_name))
        if champion_name == '':
            return None
        else:
            return champion_name


bot = BaseCommand()


def main():
    # Start up the bot
    with open('Data/alpha_token') as f:
        token = f.readline()
    bot.run(token)


if __name__ == "__main__":
    main()
