import BaseMessageResponse
import Data
import ast
import asyncio
import constants
import datetime
import discord
import json
import random
import re
import threading
import time
import urllib.request
from Data import Quotes, gifs
from discord.ext import commands
from fuzzywuzzy import fuzz
from lolesports_api import Lolesports_API
from riotwatcher import LolWatcher
from threading import Thread
from tinydb import TinyDB, Query, where

# USING ALPHA DATABASES
db = TinyDB('Data/test_database.json')
SKIN_DB = TinyDB('Data/test_skin_database.json')

# read API key
with open('Data/api_key') as f:
    API_KEY = f.readline()
LOL_ESPORTS_LIVE_LINK = 'https://lolesports.com/live/'
API = Lolesports_API()
WATCHER = LolWatcher(API_KEY)
my_region = 'na1'
FREE_CHAMPION_IDS = WATCHER.champion.rotations(my_region)

# check league's latest patch version
latest = WATCHER.data_dragon.versions_for_region(my_region)['n']['champion']
# get some champions static information
static_champ_list = WATCHER.data_dragon.champions(latest, False, 'en_US')
CHAMP_DICT = {}
for key in static_champ_list['data']:
    row = static_champ_list['data'][key]
    name = row['name']
    CHAMP_DICT[row['key']] = name

SPECIAL_CHAMPION_NAME_MATCHES_DICT = {
    "Renata": "Renata Glasc",
    "Glasc": "Renata Glasc",
    "Jarvan": "Jarvan IV",
    "JarvanIV": "Jarvan IV",
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


async def sendDm(user_id, message):
    user = await client.fetch_user(user_id)
    await user.send(message)


# Does the str start with '~'?
def is_command(message):
    return message.content[0] == '~'


async def clear_cache(cache, h):
    present = datetime.datetime.now()
    if cache:
        for key in list(cache.keys()):
            value = cache[key]
            delta = (present - value).total_seconds()
            if delta > h * 3600:
                cache.pop(key)


# Initialize CHAMP_SKINS_DICT: Dict['champion'] -> {Set of champ's skins by name}
def get_champion_skins_set(champ_dict):
    champ_skins_dict = dict()
    API_URL_NAME_MATCHES = {
        "Jarvan IV": "JarvanIV",
        "Nunu & Willump": "Nunu",
        "Kog\'Maw": "KogMaw",
        "LeBlanc": "Leblanc",
        "Wukong": "MonkeyKing",
        "Rek'Sai": "RekSai",
        "Renata Glasc": "Renata",
    }
    for champion in champ_dict.values():
        # Special Case names
        if champion in API_URL_NAME_MATCHES.keys():
            url_champion = API_URL_NAME_MATCHES[champion]
        elif "'" in champion:
            # Account for Void champion names ('Kai'sa') formatting
            url_champion = champion.replace("'", '').lower().capitalize()
        else:
            # and champions with space in their names ('Lee Sin'), as well as '.' (looking at you mundo)
            url_champion = champion.replace(' ', '').replace('.', '') if ' ' in champion or '.' in champion \
                else champion
        with urllib.request.urlopen(
                # Search for all champs' skin data on ddragon
                f'https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/champion/{url_champion}.json') as url:
            curr_champ_skins = set()
            champion_dict = json.loads(url.read().decode())
            # Retrieve list of champ skins
            list_of_champ_skins = champion_dict['data'][url_champion]['skins']
            # Add only the skin names to a set
            for skin in list_of_champ_skins:
                curr_champ_skins.add(skin['name'])
        champ_skins_dict[champion] = curr_champ_skins
    # Write the dictionary to a json file so that I don't have to run this every time i start up the bot
    with open('Data/all_champion_skins.txt', 'w') as file:
        file.write(str(champ_skins_dict))
    return champ_skins_dict


# CHAMP_SKINS_DICT = get_champion_skins_set(CHAMP_DICT)
with open('Data/all_champion_skins.txt') as f:
    data = f.read()
    CHAMP_SKINS_DICT = ast.literal_eval(data)


async def check_tracked_skins(bot):
    """Message people to notify if a champ they like has a skin on sale"""
    with open("Data/skin_sales_data.json", 'r') as file:
        skins_sale_data = json.load(file)
        favorite_skin_db = bot.favorite_skin_db
        # Parse data of every skin on sale
        for entry in skins_sale_data:
            skin_name_rp_cost = " ".join(entry['skin_name_rp_cost'].split())
            skin_data = skin_name_rp_cost.split(' ')
            skin_name = ' '.join(skin_data[0: len(skin_data) - 3])
            skin_rp_cost = ' '.join(skin_data[len(skin_data) - 2: len(skin_data)])
            for champ_name in CHAMP_DICT.values():
                if skin_name in CHAMP_SKINS_DICT[champ_name]:
                    champion = Query()
                    query_results = favorite_skin_db.get(champion['champion_name'] == champ_name)
                    if query_results is not None:
                        user_ids_list = query_results['user_ids']
                        for user_id in user_ids_list:
                            # print(f"{user_id}: {skin_name} is on sale")
                            user = bot.get_user(user_id)
                            await user.send(f"{skin_name} is on sale this week for {skin_rp_cost}!"
                                            f"\n**You are receiving this message because you opted to track League of "
                                            f"Legends skin sales for this champion. To disable these messages, reply "
                                            f"with '~favorite <champion_name>'**")
        #
        #     # Search for current skin in all champions' sets of skins
        # for skin_name in skin_sales_list:
        #     for champ_name in CHAMP_DICT.values():
        #         if skin_name in CHAMP_SKINS_SET[champ_name]:
        #             champion = Query()
        #             query_results = favorite_skin_db.get(champion['champion_name'] == champ_name)
        #             if query_results is not None:
        #                 user_ids_list = query_results['user_ids']
        #                 for user_id in user_ids_list:
        #                     # print(f"{user_id}: {skin_name} is on sale")
        #                     user = bot.get_user(user_id)
        #                     await user.send(f"{skin_name} is on sale this week for {' '.join(skin_rp_cost)}!"
        #                                     f"\n**You are receiving this message because you opted to track League of "
        #                                     f"Legends skin sales for this champion. To disable these messages, reply "
        #                                     f"with '~favorite <champion_name>'**")


def check_for_special_name_match(champion_name):
    for special_name, official_name in SPECIAL_CHAMPION_NAME_MATCHES_DICT.items():
        if fuzz.ratio(special_name.lower(), champion_name.lower()) >= 80:
            return official_name
    return champion_name


def get_fuzzy_match(champion_name):
    for champ in CHAMP_DICT.values():
        if fuzz.token_sort_ratio(champ, champion_name) >= 80:
            return champ
    return ''


# Given a janky version of a champion, format it to be pretty
#     str given_name: name input as a string
#     Return properly formatted champion name as a string
def format_champion_name(champion_name):
    champion_name = get_fuzzy_match(check_for_special_name_match(champion_name))
    if champion_name == '':
        return None
    else:
        return champion_name


def get_all_live_matches():
    live_matches = API.get_live()
    matches = live_matches['schedule']['events']
    return matches


def get_team_icons(live_match):
    teams = live_match['match']['teams']
    icons_dict = dict()
    team1_code = teams[0]['code']
    icons_dict[team1_code] = teams[0]['image']
    team2_code = teams[1]['code']
    icons_dict[team2_code] = teams[1]['image']
    return icons_dict


def get_icon(player_champ_info, icons_dict):
    player_name = player_champ_info[0]
    data = player_name.split(' ')
    team_code = data[0]
    return icons_dict[team_code]


def get_live_match_id(games):
    # Given a bunch of games in a match, return the match id of the one in progress
    for game in games:
        if game['state'] == "inProgress":
            return int(game['id'])


# Given player_champ_tourney_etc info, returns an embed with all relevant information attached
def get_embed_for_player(game_info, pm=False):
    embed = discord.Embed(color=0x87cefa)
    player_info = game_info['player']
    player_name = player_info[0]
    player_champ_name_and_role = f'{player_info[1]} {player_info[2]}'
    tournament_name = player_info[3]
    url = LOL_ESPORTS_LIVE_LINK + player_info[4]
    icon = player_info[5]
    block_name = player_info[6]
    enemy_info = game_info['enemy']
    enemy_player_name = enemy_info[0]
    enemy_champ_name_and_role = f'{enemy_info[1]}  {enemy_info[2]}'
    embed.add_field(
        name=f"{player_name}",
        value=f"Playing {player_champ_name_and_role} vs. {enemy_player_name}'s {enemy_champ_name_and_role} in "
              f"{tournament_name} {block_name}",
        inline=False)
    embed.add_field(name="Watch live on LolEsports:", value=f"{url}", inline=False)
    embed.set_thumbnail(url=icon)
    if pm:
        embed.set_footer(text=f"**You are receiving this message because you opted to track this champion in League of "
                              f"Legends professional play. To disable these messages from Zoe Bot, reply "
                              f"with '~follow <champion_name>'**")
    return embed


def get_zoe_error_message():
    quote = random.choice(Quotes.Zoe_error_message)
    if quote == "*Zoe groans in frustration.*":
        return quote
    else:
        return f'"*{quote}*"'


def get_champs_on_team(team):
    live_champs = set()
    for player in team:
        # self.format_champion_name() doesn't work with spaces so player['championId'] breaks it
        champion_name = player['championId']
        # reformats the string to put spaces between capital letters :D
        current_champ = check_for_special_name_match(re.sub(r"([A-Z])", r" \1", champion_name)[1:])
        if current_champ not in live_champs:
            live_champs.add(current_champ)
    return live_champs


def get_live_game_data(live_match):
    # Gather game data for a live game in a match
    game_id = get_live_match_id(live_match['match']['games'])
    if game_id is not None:
        try:
            return API.get_window(game_id, "")
        # JSONDecodeError occurs if game is unstarted
        except JSONDecodeErorr:
            pass


def get_all_live_champs():
    # Return a list of all champs currently in pro play
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


async def pro_all(channel):
    # Send list of all champions in live pro games
    all_live_champs = get_all_live_champs()
    if len(all_live_champs) == 0 or all_live_champs is None:
        await channel.send("No champions found in live professional games :(")
    else:
        await channel.send("All champions in live professional games: " + ', '.join(all_live_champs))


def get_player_info(role, team):
    # Given a team and a role, returns the player in that role
    for player in team:
        r = player['role'].capitalize()
        if r == role:
            player_name = player['summonerName']
            champion_name = check_for_special_name_match(re.sub(r"([A-Z])", r" \1", player['championId'])[1:])
            return [player_name, champion_name, role]


def is_champion_on_team(team, champion_name):
    # Given the red or blue side, tourney name, block name, and champ name, returns the player_champ_tourney_info
    # if the given champ is on the team
    for player in team:
        # player['championId'] wont include spaces which breaks format_champion_name(), hence why it is not used
        champion = check_for_special_name_match(re.sub(r"([A-Z])", r" \1", player['championId'])[1:])
        role = player['role'].capitalize()
        if champion.lower() == champion_name.lower():
            return get_player_info(role, team)
    return None


def find_pro_play_matchup(champion_name):
    # Given a champion name, searches all live pro games and returns a list of tuples containing information about
    # the player, their champ name, role, and tourney
    matches_found = []
    game_info = dict()
    live_matches = get_all_live_matches()
    for live_match in live_matches:
        try:
            if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
                # LCS, LCK, LEC, etc.
                # live_match['streams'] returns a list of dictionaries with streams info
                # streams['parameter'] returns the server (hopefully)
                league = live_match['streams']
                tournament_name = live_match['league']['name']
                block_name = live_match['blockName']
                url_slug = live_match['league']['slug']
                game_id = get_live_match_id(live_match['match']['games'])
                team_icons = get_team_icons(live_match)
                live_game_data = get_live_game_data(live_match)
                blue_team = live_game_data['gameMetadata']['blueTeamMetadata']['participantMetadata']
                red_team = live_game_data['gameMetadata']['redTeamMetadata']['participantMetadata']
                red = is_champion_on_team(red_team, champion_name)
                blue = is_champion_on_team(blue_team, champion_name)
                if red is not None:
                    player_champ_info = red
                    role = player_champ_info[2]
                    enemy_player_info = get_player_info(role, blue_team)
                    icon = get_icon(player_champ_info, team_icons)
                else:
                    player_champ_info = blue
                    role = player_champ_info[2]
                    enemy_player_info = get_player_info(role, red_team)
                    icon = get_icon(player_champ_info, team_icons)
                if player_champ_info:
                    tournament_info = [tournament_name, url_slug, icon, block_name, game_id]
                    # putting all info together
                    # player = [0 : player_name, 1: champion_name, 2: role, 3: tournament_name, 4: url_slug,
                    # 5: icon, 6: block_name, 7: game_id]
                    # enemy = [enemy_name, champion_name, role]
                    player_champ_info = player_champ_info + tournament_info
                    game_info['player'] = player_champ_info
                    game_info['enemy'] = enemy_player_info
                    matches_found.append(game_info)
        except (Exception,):
            pass
    return matches_found


async def check_tracked_champions(bot):
    # Every minute, checks all live champions and their db of subscribed users to message the users about a game
    # where the champion is being played, then updates the cache if the user has not already been messaged
    all_live_champs = get_all_live_champs()
    champion = Query()
    for champ in all_live_champs:
        champ_name_user_ids_dict = db.get(champion['champion_name'] == champ)
        if champ_name_user_ids_dict is not None:
            for user_id in champ_name_user_ids_dict['user_ids']:
                matches_found = find_pro_play_matchup(champ)
                if matches_found:
                    for game_info in matches_found:
                        await update_cache(bot, user_id, game_info)


async def update_cache(bot, user_id, game_info):
    # update cache with new game ids upon seeing them for the first time, else it does nothing and won't msg users
    game_id = game_info['player'][7]
    champion = game_info['player'][1]
    champ_game_tuple = champion, game_id
    if champ_game_tuple not in bot.cache:
        self.cache[champ_game_tuple] = datetime.datetime.now()
        user = bot.get_user(user_id)
        await user.send(embed=get_embed_for_player(game_info, pm=True))
