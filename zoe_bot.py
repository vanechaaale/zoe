import random
import re
import token

import discord
from discord.ext import commands
from Data import Quotes, gifs
from riotwatcher import LolWatcher
from lolesports_api import Lolesports_API
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import Levenshtein


API_KEY = "RGAPI-d59a41c8-3c95-4f3e-83f1-630d9122ba62"

# CONSTANTS
LOL_ESPORTS_LIVE_LINK = 'https://lolesports.com/live/'
api = Lolesports_API()
watcher = LolWatcher(API_KEY)
my_region = 'na1'
free_champion_ids = watcher.champion.rotations(my_region)

# check league's latest version
latest = watcher.data_dragon.versions_for_region(my_region)['n']['champion']
# Lets get some champions static information
static_champ_list = watcher.data_dragon.champions(latest, False, 'en_US')

# champ static list data to dict for looking up
# Champ_id : Champ_name
champ_dict = {}
# init data
for key in static_champ_list['data']:
    row = static_champ_list['data'][key]
    name = row['name']
    champ_dict[row['key']] = name

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
    "Monkey King": "Wukong"
}

intents = discord.Intents.default()
intents.members = True

help_command = commands.DefaultHelpCommand(
    no_category='List of Zoe Bot Commands')

bot = commands.Bot(command_prefix='~', help_command=help_command,
                   description="I'm Zoe, what's your name?", intents=intents)


@bot.event
async def on_ready():
    activity = discord.Game(name="Do something fun! The world might be ending... Or not!")
    await bot.change_presence(status=discord.Status.online, activity=activity)


@bot.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            quote = random.choice(Quotes.Zoe_join_server_message)
            await channel.send(f'"*{quote}*"')
        break


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    for cmd in RESPONSES:
        if cmd.invoke(message) and not is_command(message):
            await cmd.execute(message)
    # if bot.user.mentioned_in(message) and not is_command(message):
    #     quote = random.choice(Quotes.Zoe)
    #     await message.channel.send(f'"*{quote}*"')
    if message.is_system() and message.type == discord.MessageType.new_member:
        quote = random.choice(Quotes.Greet)
        await message.channel.send(f'"*{quote}*"')


class BaseMessageResponse:
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


@bot.command(brief="Show Zoe guides", description="List of Zoe guides and Zoe players!")
async def guide(c):
    await c.send("Here are some guides to the Aspect of Twilight and some streamers who play her!\n\n")
    await c.send("https://www.youtube.com/watch?v=YW37o9TVTho")
    # vicksy
    vicksy = discord.Embed(
        color=0xff0000,
        url="https://www.mobafire.com/league-of-legends/build/11-18-vicksys-updated-master-zoe ")
    vicksy.add_field(name="Vicksy", value="EUW Master Mid Laner", inline=False)
    vicksy.add_field(
        name="Mobafire Guide",
        value="https://www.mobafire.com/league-of-legends/build/11-18-vicksys-updated-master-zoe",
        inline=False)
    vicksy.set_thumbnail(
        url="https://img.redbull.com/images/c_crop,x_541,y_0,h_1384,w_1614/c_fill,w_650,h_540/q_auto,"
            "f_auto/redbullcom/2018/01/02/e730a429-b62d-4688-856e-f945f2b3db46/zoe-league-of-legends-build-guide"
            "-artwork")
    await c.send(embed=vicksy)
    # pekin woof
    pekin = discord.Embed(color=0xff0000, url="https://www.youtube.com/user/PekinGaming")
    pekin.add_field(
        name="Pekin Woof",
        value="Ex-Pro Player, NA Challenger Mid Laner",
        inline=False)
    pekin.add_field(
        name="Youtube Channel", value="https://www.youtube.com/user/PekinGaming")
    pekin.set_thumbnail\
        (url="https://yt3.ggpht.com/ytc/AKedOLTPLJMSw3i8BAqEGeZjEbYlMPlcYwF8Ted417Omew=s88-c-k-c0x00ffffff-no-rj")
    await c.send(embed=pekin)


@bot.command(brief="Zoe gifs.", description="Beautiful Zoe gifs.")
async def gif(channel):
    await channel.send(random.choice(gifs.gifs))


@bot.command(brief="Show Zoe matchup tips!", description="View Zoe's matchup statistics against a champion")
async def matchup(channel, champion):
    await channel.send(get_zoe_error_message())


@bot.command(brief="Paddle Star Damage Calculator (WIP)",
             description="Zoe Q damage calculator based on items, runes, and masteries")
async def damage_calc(channel):
    await channel.send(get_zoe_error_message())


@bot.command(brief="Show the weekly free champion rotation",
             description="Weekly free to play champion rotation for summoner level 11+ accounts")
async def rotation(c):
    try:
        free_rotation = []
        for champion_id in free_champion_ids['freeChampionIds']:
            free_rotation.append(champ_dict[str(champion_id)])
        free_rotation.sort()
        free_rotation = ', '.join(free_rotation)
        await c.channel.send("The champions in this week's free to play rotation are: " + free_rotation)
    except:
        await c.channel.send(get_zoe_error_message())


@bot.command(brief="Show live gameplay of a champion in professional play",
             description="Given a champion's name, shows a list of all live professional games where the champion is "
                         "being played")
async def pro(message, *champion_name):
    original_message = ' '.join(champion_name)
    if not champion_name:
        await message.channel.send("use '~pro <champion>' to search for a champion currently in pro play!")
        return
    try:
        champion_name = get_fuzzy_match(check_for_special_name_match(original_message))
        if champion_name == '':
            await message.channel.send(f"No champion with name '{original_message}' was found.")
            return
        matches_found = find_pro_play_champion(champion_name)
        if matches_found:
            # embed = discord.Embed(color=0xff0000)
            for match in matches_found:
                embed = discord.Embed(color=0xff0000)
                player_name = match[0]
                champion_role = match[1]
                tournament_name = match[2]
                url = LOL_ESPORTS_LIVE_LINK + match[3]
                embed.add_field(
                    name=f"{player_name}",
                    value=f"Playing {champion_role} in {tournament_name}",
                    inline=False)
                embed.add_field(name="Watch live on LolEsports:", value=f"{url}", inline=False)
                await message.send(embed=embed)
        # await message.send(embed=embed)
        else:
            await message.channel.send(f"{champion_name} isn't on Summoner's Rift right now :(")
    except:
        await message.channel.send(get_zoe_error_message())


def find_pro_play_champion(champion_name):
    matches_found = []
    live_matches = api.get_live()
    matches = live_matches['schedule']['events']
    for live_match in matches:
        if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
            tournament_name = live_match['league']['name']
            block_name = live_match['blockName']
            slug = live_match['league']['slug']
            match_id = get_live_match_id(live_match['match']['games'])
            if match_id is not None:
                match_window_response = api.get_window(match_id, "")
                blue_team = match_window_response['gameMetadata']['blueTeamMetadata']['participantMetadata']
                red_team = match_window_response['gameMetadata']['redTeamMetadata']['participantMetadata']
                red = is_champion_on_team(blue_team, tournament_name, block_name, champion_name)
                blue = is_champion_on_team(red_team, tournament_name, block_name, champion_name)
                match = red if red is not None else blue
                if match:
                    match.append(slug)
                    matches_found.append(match)
    return matches_found


def is_champion_on_team(team, tournament_name, block_name, champion_name):
    for player in team:
        champion = player['championId']
        if champion.lower() == champion_name.lower():
            player_name = player['summonerName']
            role = player['role'].capitalize()
            return [player_name, f"{champion_name} {role}", f"{tournament_name} {block_name}"]
    return None


# Given champion name -> returns a name if it matches the weird names dictionary
# "Renata" -> "Renata Glasc"
def check_for_special_name_match(champion_name):
    for special_name, official_name in SPECIAL_CHAMPION_NAME_MATCHES_DICT.items():
        if fuzz.ratio(special_name.lower(), champion_name.lower()) >= 80:
            return official_name
    return champion_name


def get_fuzzy_match(champion_name):
    for champ in champ_dict.values():
        if fuzz.token_sort_ratio(champ, champion_name) >= 80:
            return champ
    return ''


def get_live_match_id(games):
    for game in games:
        if game['state'] == "inProgress":
            return int(game['id'])


def get_live_game(games):
    for game in games['event']['match']['games']:
        if game['state'] == 'inProgress':
            # "Red vs Blue"
            current_game = api.get_window(game['id'])


def get_zoe_error_message():
    quote = random.choice(Quotes.Zoe_error_message)
    if quote == "*Zoe groans in frustration.*":
        return quote
    else:
        return f'"*{quote}*"'


@matchup.error
async def matchup_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("use '~matchup <champion>' to search for Zoe's matchup statistics against a champion!")


def is_command(message):
    return message.content[0] == '~'


@bot.event
async def on_command_error(channel, error):
    if isinstance(error, commands.CommandNotFound):
        return

""" @bot.command(brief="champs and skins on sale", description="champs and skins on sale")
async def sale(c):
    try:
        
    except:
        await c.channel.send(random.choice(Quotes.Zoe_error_message))"""

if __name__ == "__main__":
    with open ('token') as f:
        token = f.readline()
    bot.run(token)
