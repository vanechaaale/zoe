import random
import re
import discord
from discord.ext import commands
import Data
from Data import Quotes, gifs
from riotwatcher import LolWatcher
from lolesports_api import Lolesports_API
from fuzzywuzzy import fuzz
import BaseMessageResponse
import threading
from threading import Thread
from tinydb import TinyDB, Query, where
import asyncio
import time
import constants

bot = constants.BOT


class Tracker:

    def __init__(self):
        pass

    @bot.command(brief="Track a champion in professional play",
                 description="Get notified by Zoe Bot whenever a certain champion is being played in a professional "
                             "match, or use the command again to stop receiving notifications from Zoe Bot.")
    async def track(self, message, *champion_name):
        # person calls 'track <champion_name>'
        # format champion_name
        champion_name = format_champion_name(' '.join(champion_name))
        if not champion_name:
            await message.channel.send(
                "use '~track <champion>' to be notified when a champion is being played in a professional match!")
            return
        # Query champion user id list
        champion = Query()
        user_id = message.author.id
        champ_name_user_ids_dict = db.get(champion['champion_name'] == champion_name)
        # I tried using a set but it broke whenever i called db.insert()
        user_ids_list = [] if champ_name_user_ids_dict is None else champ_name_user_ids_dict['user_ids']
        if champ_name_user_ids_dict is None:
            user_ids_list.append(user_id)
            db.insert({'champion_name': champion_name, 'user_ids': user_ids_list})
            await message.channel.send(f"Now tracking live pro games for {champion_name}.")
        elif user_id not in user_ids_list:
            user_ids_list.append(user_id)
            db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
            await message.channel.send(f"Now tracking live pro games for {champion_name}.")
        else:
            user_ids_list.remove(user_id)
            db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
            await message.channel.send(f"No longer tracking live pro games for {champion_name}.")

    @bot.command(brief="Show list of all champions being tracked for professional play",
                 description="Show a list of all champions that Zoe Bot will notify a Discord User for when one or "
                             "more champs are being played in a professional game. Remove a champion from this list "
                             "with the command '~track <champion_name>'.")
    async def subscribed(self, message):
        tracked_list = []
        user_id = message.author.id
        for champ_name in CHAMP_DICT.values():
            champion = Query()
            query_results = db.get(champion['champion_name'] == champ_name)
            if query_results is not None:
                user_ids_list = query_results['user_ids']
                if user_id in user_ids_list:
                    tracked_list.append(champ_name)
        if len(tracked_list) != 0:
            await message.channel.send(f"Currently tracking professional matches for: {', '.join(tracked_list)}")
        else:
            await message.channel.send(f"You are currently not tracking live games for any champion.")

    # threaded function
    async def check_tracked_champions(self):
        while True:
            all_live_champs = get_all_live_champs()
            champion = Query()
            if len(all_live_champs) == 0:
                user = bot.get_user(226105055051382788)
                await user.send("NO MATCHES LOL")
            for champ in all_live_champs:
                champ_name_user_ids_dict = db.get(champion['champion_name'] == champ)
                if champ_name_user_ids_dict is not None:
                    for user_id in champ_name_user_ids_dict['user_ids']:
                        matches_found = find_pro_play_champion(champ)
                        if matches_found:
                            for match in matches_found:
                                user = bot.get_user(user_id)
                                if user is not None:
                                    await user.send(embed=get_embed_for_player(match))


    async def tracker(self):
        task1 = asyncio.create_task(
            check_tracked_champions())
        await task1


    def between_callback(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(tracker())
        loop.close()
