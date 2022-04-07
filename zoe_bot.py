import random
import re
import discord
from discord.ext import commands
import Data
from Data import Quotes, gifs
from riotwatcher import LolWatcher
from lolesports_api import Lolesports_API
from fuzzywuzzy import fuzz

API_KEY = "RGAPI-97357227-08ee-4c50-917c-7ae8d4c23309"

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
    if message.is_system() and message.type == discord.MessageType.new_member:
        quote = random.choice(Quotes.Greet)
        await message.channel.send(f'"*{quote}*"')


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


@bot.command(brief="Show Zoe guides", description="List of Zoe guides and Zoe players!")
async def guide(c):
    await c.send("Here are some guides to the Aspect of Twilight and some streamers who play her!\n\n")
    detention = discord.Embed(
        color=0xffb6c1,
    )
    detention.add_field(name="Detention", value="NA Challenger Mid Laner", inline=False)
    detention.set_thumbnail(url='https://pbs.twimg.com/profile_images/1465745862940897281/Q_QU3wNS_400x400.png')
    detention.add_field(name="Youtube Guide", value='https://www.youtube.com/watch?v=YW37o9TVTho')
    await c.send(embed=detention)
    # vicksy
    vicksy = discord.Embed(
        color=0xffb6c1)
    vicksy.add_field(name="Vicksy", value="EUW Master Mid Laner", inline=False)
    vicksy.add_field(
        name="Mobafire Guide",
        value="https://www.mobafire.com/league-of-legends/build/vicksys-updated-master-zoe-guide-for-season-12-524904",
        inline=False)
    vicksy.set_thumbnail(
        url="https://static-cdn.jtvnw.net/jtv_user_pictures/37e7e61e-369f-4ba6-8fd6-106f860eca82-profile_image-70x70"
            ".png")
    await c.send(embed=vicksy)
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


async def pro_all(message):
    all_live_champs_set = set()
    live_matches = get_all_live_matches()
    for live_match in live_matches:
        if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
            live_game_data = get_live_game_data(live_match)
            blue_team = live_game_data['gameMetadata']['blueTeamMetadata']['participantMetadata']
            red_team = live_game_data['gameMetadata']['redTeamMetadata']['participantMetadata']
            blue_team_champs = get_champs_on_team(blue_team)
            red_team_champs = get_champs_on_team_(red_team).append(blue_team_champs)
            all_live_champs_set.add(red_team_champs)
    all_live_champs = list(all_live_champs_set).sort()
    if all_live_champs is None:
        await message.channel.send("There are currently no live pro games :(")
    else:
        await message.author.send("All champions in live pro games: " + all_live_champs)


def get_champs_on_team(team):
    live_champs = []
    for player in team:
        current_champ = player['championId']
        if current_champ not in live_champs:
            live_champs.append(current_champ)
    return live_champs


@bot.command(brief="Show list of live games with a champion in professional play",
             description="Given a champion's name, shows a list of all live professional games where the champion is "
                         "being played, or use '~pro all' to see a list of all champions in live games")
async def pro(message, *champion_name):
    try:
        original_message = ' '.join(champion_name)
        if not champion_name:
            await message.channel.send("use '~pro <champion>' to search for a champion currently in pro play!")
            return
        if original_message.lower() == "all":
            await pro_all(message)
            return
        champion_name = get_fuzzy_match(check_for_special_name_match(original_message))
        if champion_name == '':
            await message.channel.send(f"No champion with name '{original_message}' was found.")
            return
        matches_found = find_pro_play_champion(champion_name)
        if matches_found:
            # embed = discord.Embed(color=0xff0000)
            for match in matches_found:
                await message.send(embed=get_embed_for_player(match))
        # await message.send(embed=embed)
        else:
            await message.channel.send(f"{champion_name} isn't on Summoner's Rift right now :(")
    except:
        await message.channel.send(get_zoe_error_message())


def find_pro_play_champion(champion_name):
    matches_found = []
    live_matches = get_all_live_matches()
    for live_match in live_matches:
        if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
            tournament_name = live_match['league']['name']
            block_name = live_match['blockName']
            url_slug = live_match['league']['slug']
            live_game_data = get_live_game_data(live_match)
            blue_team = live_game_data['gameMetadata']['blueTeamMetadata']['participantMetadata']
            red_team = live_game_data['gameMetadata']['redTeamMetadata']['participantMetadata']
            red = is_champion_on_team(blue_team, tournament_name, block_name, champion_name)
            blue = is_champion_on_team(red_team, tournament_name, block_name, champion_name)
            match = red if red is not None else blue
            if match:
                match.append(url_slug)
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


def get_all_live_matches():
    live_matches = api.get_live()
    matches = live_matches['schedule']['events']
    return matches


def get_fuzzy_match(champion_name):
    for champ in champ_dict.values():
        if fuzz.token_sort_ratio(champ, champion_name) >= 80:
            return champ
    return ''


def get_live_game_data(live_match):
    match_id = get_live_match_id(live_match['match']['games'])
    if match_id is not None:
        return api.get_window(match_id, "")


def get_live_match_id(games):
    for game in games:
        if game['state'] == "inProgress":
            return int(game['id'])


def get_embed_for_player(match):
    embed = discord.Embed(color=0x87cefa)
    player_name = match[0]
    champion_role = match[1]
    tournament_name = match[2]
    url = LOL_ESPORTS_LIVE_LINK + match[3]
    embed.add_field(
        name=f"{player_name}",
        value=f"Playing {champion_role} in {tournament_name}",
        inline=False)
    embed.add_field(name="Watch live on LolEsports:", value=f"{url}", inline=False)


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
    with open('Data/token') as f:
        token = f.readline()
    bot.run(token)
