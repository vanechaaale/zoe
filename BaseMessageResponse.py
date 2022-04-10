from fuzzywuzzy import fuzz
import discord
import random
import re
import discord
from discord.ext import commands
import Data
from Data import Quotes, gifs
from riotwatcher import LolWatcher
from lolesports_api import Lolesports_API
from fuzzywuzzy import fuzz
import threading
from tinydb import TinyDB, Query, where


class BaseMessageResponse:
    def __init__(self):
        pass

    def invoke(self, message: discord.Message) -> bool:
        raise NotImplementedError

    def execute(self, message: discord.Message):
        raise NotImplementedError


class Zoe(BaseMessageResponse):
    TEXT_MAP = {
        'hate': "No, that's not nice!",
        'love': "Yes! This'll be fun, right?",
        'bye': 'https://1.bp.blogspot.com/-Oaewrz-7M0E/Wo9PZE-jDaI/AAAAAAAA5yY'
               '/BOSEiViGD5k7jwcLYur4SvSypBN8p0VuQCLcBGAs/s1600/d59ac85417e4a84d.png '
    }

    def invoke(self, message: discord.Message) -> bool:
        return bool(re.search('[Zz][Oo][Ee]', message.content))

    async def execute(self, message: discord.Message):
        for keyword, quote in Zoe.TEXT_MAP.items():
            if keyword in message.content.lower():
                await message.channel.send(f'"*{quote}*"')
                return
        quote = random.choice(Quotes.Zoe)
        await message.channel.send(f'"*{quote}*"')


class Ezreal(BaseMessageResponse):
    def invoke(self, message: discord.Message) -> bool:
        return bool(re.search('[Ee][Zz][Rr][Ee][Aa][Ll]', message.content))

    async def execute(self, message: discord.Message):
        quote = random.choice(Quotes.Ezreal)
        await message.channel.send(f'"*{quote}*"')


class Lux(BaseMessageResponse):
    def invoke(self, message: discord.Message) -> bool:
        return bool(re.search('[^a-z]?lux(?:[^a-z]|$|^)', message.content, flags=re.IGNORECASE | re.MULTILINE))

    async def execute(self, message: discord.Message):
        rand = random.randint(1, 2)
        if rand == 1:
            quote = random.choice(Quotes.Lux)
            await message.channel.send(f'"*{quote}*"')


class Mooncake(BaseMessageResponse):
    def invoke(self, message: discord.Message) -> bool:
        return bool(re.search('[Mm][Oo][Oo][Nn][Cc][Aa][Kk][Ee]', message.content)
                    or "moon cake" in message.content.lower())

    async def execute(self, message: discord.Message):
        quote = random.choice(Quotes.Mooncake)
        await message.channel.send(f'"*{quote}*"')


class Xingqui(BaseMessageResponse):
    def invoke(self, message: discord.Message) -> bool:
        ratio = fuzz.ratio("Xingqiu", message.content.title())
        if ratio == 100:
            return False
        else:
            return bool(ratio > 75)

    async def execute(self, message: discord.Message):
        await message.channel.send("it's spelled xingqiu btw")


RESPONSES = [Zoe(), Ezreal(), Lux(), Mooncake(), Xingqui()]
