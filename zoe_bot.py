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
from tinydb import TinyDB, Query, where

""" CONSTANTS """
# read API key
with open('Data/api_key') as f:
    API_KEY = f.readline()

LOL_ESPORTS_LIVE_LINK = 'https://lolesports.com/live/'
api = Lolesports_API()
watcher = LolWatcher(API_KEY)
my_region = 'na1'
free_champion_ids = watcher.champion.rotations(my_region)
db = TinyDB('Data/database.json')

# check league's latest version
latest = watcher.data_dragon.versions_for_region(my_region)['n']['champion']
# Lets get some champions static information
static_champ_list = watcher.data_dragon.champions(latest, False, 'en_US')

# champ static list data to dict for looking up
# Champ_id : Champ_name
CHAMP_DICT = {}
# init data
for key in static_champ_list['data']:
    row = static_champ_list['data'][key]
    name = row['name']
    CHAMP_DICT[row['key']] = name

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
# async def on_command_error(channel, error):
async def on_command_error(channel, error):
    if isinstance(error, commands.CommandNotFound):
        return


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    for cmd in BaseMessageResponse.RESPONSES:
        if cmd.invoke(message) and not is_command(message):
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
        value="https://www.mobafire.com/league-of-legends/build/vicksys-updated-master-zoe-guide-for-season-12-524904",
        inline=False)
    vicksy.set_thumbnail(
        url="https://static-cdn.jtvnw.net/jtv_user_pictures/37e7e61e-369f-4ba6-8fd6-106f860eca82-profile_image-70x70"
            ".png")
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
            free_rotation.append(CHAMP_DICT[str(champion_id)])
        free_rotation.sort()
        free_rotation = ', '.join(free_rotation)
        await c.channel.send("The champions in this week's free to play rotation are: " + free_rotation)
    except (Exception,):
        await c.channel.send(get_zoe_error_message())


@bot.command(brief="Track a champion in professional play",
             description="Get notified by Zoe Bot whenever a certain champion is being played in a professional match, "
                         "or use the command again to stop receiving notifications from Zoe Bot.")
async def track(message, *champion_name):
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
             description="Show a list of all champions that Zoe Bot will notify a Discord User for when one or more "
                         "champs are being played in a professional game. Remove a champion from this list with the "
                         "command '~track <champion_name>'.")
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
            for match in matches_found:
                await message.send(embed=get_embed_for_player(match))
        else:
            await message.channel.send(f"{champion_name} isn't on Summoner's Rift right now :(")
    except (Exception,):
        await message.channel.send(get_zoe_error_message())


async def pro_all(message):
    all_live_champs = get_all_live_champs()
    if len(all_live_champs) == 0 or all_live_champs is None:
        await message.channel.send("There are currently no live pro games :(")
    else:
        await message.channel.send("All champions in live pro games: " + ', '.join(all_live_champs))


def get_champs_on_team(team):
    live_champs = set()
    for player in team:
        # TODO: MAKE THIS WORK WITH FORMAT CHAMP NAME METHOD
        champion_name = player['championId']
        if champion_name == "JarvanIV":
            current_champ = "Jarvan IV"
        # reformats the string to put spaces between capital letters :D
        else:
            current_champ = check_for_special_name_match(re.sub(r"([A-Z])", r" \1", champion_name)[1:])
        if current_champ not in live_champs:
            live_champs.add(current_champ)
    return live_champs


def find_pro_play_champion(champion_name):
    matches_found = []
    live_matches = get_all_live_matches()
    for live_match in live_matches:
        try:
            if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
                tournament_name = live_match['league']['name']
                block_name = live_match['blockName']
                url_slug = live_match['league']['slug']
                team_icons = get_team_icons(live_match)
                live_game_data = get_live_game_data(live_match)
                blue_team = live_game_data['gameMetadata']['blueTeamMetadata']['participantMetadata']
                red_team = live_game_data['gameMetadata']['redTeamMetadata']['participantMetadata']
                red = is_champion_on_team(blue_team, tournament_name, block_name, champion_name)
                blue = is_champion_on_team(red_team, tournament_name, block_name, champion_name)
                match = red if red is not None else blue
                icon = get_icon(team_icons, red, blue)
                if match:
                    match.append(url_slug)
                    match.append(icon)
                    matches_found.append(match)
        except (Exception,):
            pass
    return matches_found


def is_champion_on_team(team, tournament_name, block_name, champion_name):
    for player in team:
        # TODO: FIX THE FORMATTING OF THESE NAMES TO WORK WITH FORMAT_CHAMP_NAME()
        champion = check_for_special_name_match(re.sub(r"([A-Z])", r" \1", player['championId'])[1:])
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
    for champ in CHAMP_DICT.values():
        if fuzz.token_sort_ratio(champ, champion_name) >= 80:
            return champ
    return ''


def get_team_icons(live_match):
    teams = live_match['match']['teams']
    red_team_image = teams[0]['image']
    blue_team_image = teams[1]['image']
    return red_team_image, blue_team_image


def get_icon(team_icons, red, blue):
    if red is not None:
        return team_icons[1]
    elif blue is not None:
        return team_icons[0]
    else:
        return None


def get_live_game_data(live_match):
    game_id = get_live_match_id(live_match['match']['games'])
    if game_id is not None:
        try:
            return api.get_window(game_id, "")
        # JSONDecodeError occurs if game is unstarted
        except JSONDecodeErorr:
            pass


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
    icon = match[4]
    embed.add_field(
        name=f"{player_name}",
        value=f"Playing {champion_role} in {tournament_name}",
        inline=False)
    embed.add_field(name="Watch live on LolEsports:", value=f"{url}", inline=False)
    embed.set_thumbnail(url=icon)
    return embed


def get_zoe_error_message():
    quote = random.choice(Quotes.Zoe_error_message)
    if quote == "*Zoe groans in frustration.*":
        return quote
    else:
        return f'"*{quote}*"'


def get_all_live_champs():
    all_live_champs_set = set()
    live_matches = get_all_live_matches()
    for live_match in live_matches:
        try:
            if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
                live_game_data = get_live_game_data(live_match)
                blue_team = live_game_data['gameMetadata']['blueTeamMetadata']['participantMetadata']
                red_team = live_game_data['gameMetadata']['redTeamMetadata']['participantMetadata']
                blue_team_champs = get_champs_on_team(blue_team)
                red_team_champs = get_champs_on_team(red_team)
                all_live_champs_set = all_live_champs_set.union(red_team_champs)
                all_live_champs_set = all_live_champs_set.union(blue_team_champs)
        except (Exception,):
            pass
    all_live_champs = list(all_live_champs_set)
    all_live_champs.sort()
    return all_live_champs


@matchup.error
async def matchup_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("use '~matchup <champion>' to search for Zoe's matchup statistics against a champion!")


def is_command(message):
    return message.content[0] == '~'


# Given a janky version of a champion, format it to be pretty
#     str given_name: name input as a string
#     Return properly formatted champion name as a string
def format_champion_name(champion_name):
    champion_name = get_fuzzy_match(check_for_special_name_match(champion_name))
    if champion_name == '':
        return None
    else:
        return champion_name


async def check_tracked_champions():
    threading.Timer(5.0, printit).start()
    all_live_champs = get_all_live_champs()
    champion = Query()
    for champ in all_live_champs:
        champ_name_user_ids_dict = db.get(champion['champion_name'] == champ)
        for user_id in champ_name_user_ids_dict:
            await pro(user_id, champ)


async def sendDm(user_id, message):
    user = await client.fetch_user(user_id)
    await user.send(message)


""" @bot.command(brief="champs and skins on sale", description="champs and skins on sale")
async def sale(c):
    try:
        
    except:
        await c.channel.send(random.choice(Quotes.Zoe_error_message))"""

if __name__ == "__main__":
    with open('Data/token') as f:
        token = f.readline()
    bot.run(token)
    check_tracked_champions()
