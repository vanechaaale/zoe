import random
import re

from discord.ext import commands

bot = commands.Bot(command_prefix='!', description="This is Zoe Bot")

@bot.listen()
async def on_message(message):
    match = re.search('.*?[Zz][Oo][Ee].*?', message.content)
    hate = re.search('.*?[Hh][Aa][Tt][Ee].*?', message.content)
    love = re.search('.*?[Ll][Oo][Vv][Ee].*?', message.content)

    if match is not None and hate is not None:
        await message.channel.send("No, that's not nice!")
        return
    if match is not None and love is not None:
        await message.channel.send("Yes! This'll be fun, right?")
        return
    if match is not None:
        await message.channel.send("I'm Zoe, what's your name?")
        return
    if "ezreal" in message.content:
        rand = random.randint(1, 11)
        await message.channel.send(switcher.get(rand, None))


@bot.command()
async def guide(c):
    await c.send("Here are some guides to the Aspect of Twilight and some streamers who play her!\n\n"
                 "Detention: NA Challenger Mid \n"
                 "https://www.youtube.com/watch?v=v0e9P1nu8dk\n\n"
                 "Vicksy: EUW Master Mid\n"
                 "https://www.mobafire.com/league-of-legends/build/11-18-vicksys-updated-master-zoe"
                 "-guide-for-season-11-524904\n\n"
                 "PekinWoof: Ex-Pro Player, NA Challenger Mid\n"
                 "https://www.youtube.com/user/PekinGaming\n\n"
                 )
    return


switcher = {
    1: "HEY, I'M ZOE! YOU'RE EZREAL! I KNOW THAT! I mean- uh, "
       "I found it out! I mean... ugh... kill me now.",
    2: "HI EZREAL! I mean- That is you over there, "
       "right? I'm over here. I'm Zoe... Never mind.",
    3: "Are you from here? I walk between worlds. "
       "Well, hop, actually. You're cuuuute...",
    4: "I'm just saying, if you wanted to hold hands, that would be okay.",

    5: "You just haven't realized how cool I am yet!",

    6: "Do I like you or chocolate mooncake more?! So hard to decide!",

    7: "I'm not saying Lux isn't a good girlfriend buuuttt... you could do better!",

    8: "Ezreal is really dreamy!",

    9: "He was so cute. I mean, uh, not that I noticed. Hehe.",

    10: "Hello! Hi! Hey! Or... whatever...",

    11: "I did not say I wanna kiss you... yet.."
}

bot.run('ODg3ODE5ODU5NjA4NjEyODY0.YUJsrQ.s50gQRs6_pMgjNJC6BnJlFq9UiA')
