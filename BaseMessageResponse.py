import random
import re
import string

import discord
from Data import Quotes
from fuzzywuzzy import fuzz


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
        return bool(re.search('[^a-z]?zoe(?:[^a-z]|$|^)', message.content, flags=re.IGNORECASE | re.MULTILINE))

    async def execute(self, message: discord.Message):
        for keyword, quote in Zoe.TEXT_MAP.items():
            if keyword in message.content.lower():
                await message.channel.send(f'"*{quote}*"')
                return
        quote = random.choice(Quotes.Zoe)
        await message.channel.send(f'"*{quote}*"')


class Ezreal(BaseMessageResponse):
    def invoke(self, message: discord.Message) -> bool:
        return bool(re.search('[^a-z]?ezreal(?:[^a-z]|$|^)', message.content, flags=re.IGNORECASE | re.MULTILINE))

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
        return bool(re.search('[^a-z]?mooncake(?:[^a-z]|$|^)', message.content, flags=re.IGNORECASE | re.MULTILINE)
                    or "moon cake" in message.content.lower())

    async def execute(self, message: discord.Message):
        quote = random.choice(Quotes.Mooncake)
        await message.channel.send(f'"*{quote}*"')


class Xingqui(BaseMessageResponse):
    def invoke(self, message: discord.Message) -> bool:
        # TODO: buggy with messages like 'xingqiu.' or doesnt work with multiple words in msg
        ratio = 0
        for word in message.content.split(' '):
            word = word.translate(str.maketrans('', '', string.punctuation))
            ratio = fuzz.ratio("Xingqiu", word.title())
        return 100 > ratio >= 75

    async def execute(self, message: discord.Message):
        await message.channel.send("it's spelled xingqiu btw")


RESPONSES = [Zoe(), Ezreal(), Lux(), Mooncake(), Xingqui()]
