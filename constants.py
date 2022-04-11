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

# read API key
with open('Data/api_key') as f:
    API_KEY = f.readline()
LOL_ESPORTS_LIVE_LINK = 'https://lolesports.com/live/'
API = Lolesports_API()
WATCHER = LolWatcher(API_KEY)
my_region = 'na1'
free_champion_ids = WATCHER.champion.rotations(my_region)
db = TinyDB('Data/database.json')

# check league's latest version
latest = WATCHER.data_dragon.versions_for_region(my_region)['n']['champion']
# Lets get some champions static information
static_champ_list = WATCHER.data_dragon.champions(latest, False, 'en_US')


# champ static list data to dict for looking up
# Champ_id : Champ_name
# init data
def init_data():
    CHAMP_DICT = {}
    for key in static_champ_list['data']:
        row = static_champ_list['data'][key]
        name = row['name']
        CHAMP_DICT[row['key']] = name
    return CHAMP_DICT


SPECIAL_CHAMPION_NAME_MATCHES_DICT = {
    "Renata": "Renata Glasc",
    "Glasc": "Renata Glasc",
    "Jarvan": "Jarvan IV",
    "Aurelion": "Aurelion Sol",
    "Lee": "Lee Sin",
    "Yi": "Master Yi",
    "Nunu": "Nunu & Willump",
    "Tahm": "Tahm Kench",
    "TF": "Twisted Fate",
    "MonkeyKing": "Wukong",
    "Monkey King": "Wukong",
    "Asol": "Aurelion Sol",
    "Powder": "Jinx",
    "Violet": "Vi",
    "The Aspect of Twilight": "Zoe",
    "TK": "Tahm Kench",
    "Ali": "Alistar",
    "Mundo": "Dr. Mundo",
    "Kaisa": "Kai'Sa",
    "Khazix": "Kha'Zix",
    "MF": "Miss Fortune",
    "Reksai": "Rek'Sai",
    "Velkoz": "Vel'koz",
    "Xin": "Xin Zhao",
}

help_command = commands.DefaultHelpCommand(no_category='List of Zoe Bot Commands')
intents = discord.Intents.default()
intents.members = True

BOT = commands.Bot(
    command_prefix='~', help_command=help_command,
    description="I'm Zoe, what's your name?", intents=intents)
