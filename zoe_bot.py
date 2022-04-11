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
from constants import Constants

# CONSTANTS
const = Constants()
bot = constants.BOT
api = constants.API
CHAMP_DICT = const.champ_dict
db = constants.DB
free_champion_ids = constants.FREE_CHAMPION_IDS


@bot.event
async def on_ready():
    activity = discord.Game(name="Do something fun! The world might be ending... Or not!")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    while True:
        await const.check_tracked_champions()
        await asyncio.sleep(180)


@bot.command(hidden=True)
@commands.is_owner()
async def shutdown(c):
    await c.channel.send("Logging out...")
    await bot.close()


@bot.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            quote = random.choice(Quotes.Zoe_join_server_message)
            await channel.send(f'"*{quote}*"')
        break


@bot.event
async def on_command_error(channel, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        await channel.send(error)


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    for cmd in BaseMessageResponse.RESPONSES:
        if cmd.invoke(message) and not const.is_command(message):
            await cmd.execute(message)
    if message.is_system() and message.type == discord.MessageType.new_member:
        quote = random.choice(Quotes.Greet)
        await message.channel.send(f'"*{quote}*"')


@bot.command(brief="Show Zoe guides", description="List of Zoe guides and Zoe players!")
async def guide(channel):
    await channel.send("Here are some guides to the Aspect of Twilight and some streamers who play her!\n\n")
    detention = discord.Embed(
        color=0xffb6c1,
    )
    detention.add_field(name="Detention", value="NA Challenger Mid Laner", inline=False)
    detention.set_thumbnail(url='https://pbs.twimg.com/profile_images/1465745862940897281/Q_QU3wNS_400x400.png')
    detention.add_field(name="Youtube Guide", value='https://www.youtube.com/watch?v=YW37o9TVTho')
    await channel.send(embed=detention)
    # vicksy
    vicksy = discord.Embed(
        color=0xffb6c1)
    vicksy.add_field(name="Vicksy", value="EUW Master Mid Laner", inline=False)
    vicksy.add_field(
        name="Mobafire Guide",
        value="https://www.mobafire.com/league-of-legends/build/vicksys-updated-master-zoe-guide-for-season-12"
              "-524904",
        inline=False)
    vicksy.set_thumbnail(
        url="https://static-cdn.jtvnw.net/jtv_user_pictures/37e7e61e-369f-4ba6-8fd6-106f860eca82-profile_image"
            "-70x70.png")
    await channel.send(embed=vicksy)
    # pekin woof
    pekin = discord.Embed(color=0xffb6c1, url="https://www.youtube.com/user/PekinGaming")
    pekin.add_field(
        name="Pekin Woof",
        value="Ex-Pro Player, NA Challenger Mid Laner",
        inline=False)
    pekin.add_field(
        name="Youtube Channel", value="https://www.youtube.com/user/PekinGaming")
    pekin.set_thumbnail(
        url="https://yt3.ggpht.com/ytc/AKedOLTPLJMSw3i8BAqEGeZjEbYlMPlcYwF8Ted417Omew=s88-c-k-c0x00ffffff-no-rj")
    await channel.send(embed=pekin)


@bot.command(brief="Zoe gifs.", description="Beautiful Zoe gifs.")
async def gif(channel):
    await channel.send(random.choice(gifs.gifs))


@bot.command(brief="Show Zoe matchup tips! (WIP)", description="View Zoe's matchup statistics against a champion")
async def matchup(channel, champion):
    champion.lower()
    await channel.send(const.get_zoe_error_message())


@bot.command(brief="Paddle Star Damage Calculator (WIP)",
             description="Zoe Q damage calculator based on items, runes, and masteries")
async def damage_calc(channel):
    await channel.send(const.get_zoe_error_message())


@bot.command(brief="Show the weekly free champion rotation",
             description="Weekly free to play champion rotation for summoner level 11+ accounts")
async def rotation(c):
    try:
        free_rotation = []
        for champion_id in free_champion_ids['freeChampionIds']:
            free_rotation.append(CHAMP_DICT[str(champion_id)])
        free_rotation.sort()
        free_rotation = ', '.join(free_rotation)
        await c.channel.send("The champions in this week's free to play rotation are: " + free_rotation)
    except (Exception,):
        await c.channel.send(const.get_zoe_error_message())


@bot.command(brief="Show list of live games with a champion in professional play",
             description="Given a champion's name, shows a list of all live professional games where the champion "
                         "is being played, or use '~pro all' to see a list of all champions in live games")
async def pro(channel, *champion_name):
    if not isinstance(channel, discord.User) and channel is not None:
        channel = channel.channel
    try:
        original_message = ' '.join(champion_name)
        if not champion_name:
            await channel.send("use '~pro <champion>' to search for a champion currently in pro play!")
            return
        if original_message.lower() == "all":
            await const.pro_all(channel)
            return
        champion_name = const.get_fuzzy_match(const.check_for_special_name_match(original_message))
        if champion_name == '':
            await channel.send(f"No champion with name '{original_message}' was found.")
            return
        matches_found = const.find_pro_play_champion(champion_name)
        if matches_found:
            for match in matches_found:
                await channel.send(embed=const.get_embed_for_player(match))
        else:
            await channel.send(f"{champion_name} isn't on Summoner's Rift right now :(")
    except (Exception,):
        await channel.send(const.get_zoe_error_message())


# Given champion name -> returns a name if it matches the weird names dictionary
# "Renata" -> "Renata Glasc"

@matchup.error
async def matchup_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("use '~matchup <champion>' to search for Zoe's matchup statistics against a champion!")


# Given a janky version of a champion, format it to be pretty
#     str given_name: name input as a string
#     Return properly formatted champion name as a string

""" @bot.command(brief="champs and skins on sale", description="champs and skins on sale")
async def sale(c):
    try:
        
    except:
        await c.channel.send(random.choice(Quotes.Zoe_error_message))"""


@bot.command(brief="Track a champion in professional play",
             description="Get notified by Zoe Bot whenever a certain champion is being played in a professional "
                         "match, or use the command again to stop receiving notifications from Zoe Bot.")
async def track(message, *champion_name):
    # person calls 'track <champion_name>'
    # format champion_name
    champion_name = const.format_champion_name(' '.join(champion_name))
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
async def subscribed(message):
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


# Start up the bot
with open('Data/token') as f:
    token = f.readline()
bot.run(token)
