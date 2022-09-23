import ast
import datetime
import json
import random
import re
import shutil
import urllib.request
from json import JSONDecodeError

import cv2
import discord
import numpy as np
import requests
from cv2 import imread
from fuzzywuzzy import fuzz
from imageio.v3 import imwrite
from riotwatcher import LolWatcher
from tinydb import TinyDB, Query

from Data import Quotes
from lolesports_api import Lolesports_API


def get_lol_watcher():
    # read API key
    with open('Data/api_key') as file:
        api_key = file.readline()
    return LolWatcher(api_key)


def get_lolesports_api():
    return Lolesports_API()


class Constants:
    REGION = 'na1'
    DB = TinyDB('Data/database.json')
    SKIN_DB = TinyDB('Data/skin_database.json')
    LOL_ESPORTS_LIVE_LINK = 'https://lolesports.com/live/'

    SPECIAL_CHAMPION_NAME_MATCHES_DICT = {
        "Renata": "Renata Glasc",
        "Glasc": "Renata Glasc",
        "Jarvan": "Jarvan IV",
        "JarvanIV": "Jarvan IV",
        "Aurelion": "Aurelion Sol",
        "Lee": "Lee Sin",
        "Yi": "Master Yi",
        "Nunu": "Nunu & Willump",
        "TF": "Twisted Fate",
        "MonkeyKing": "Wukong",
        "Monkey King": "Wukong",
        "Asol": "Aurelion Sol",
        "Powder": "Jinx",
        "Violet": "Vi",
        "The Aspect of Twilight": "Zoe",
        "The First Twilight": "Zoe",
        "Aspect of Change": "Zoe",
        "The Everchild": "Zoe",
        "TK": "Tahm Kench",
        "Tahm": "Tahm Kench",
        "Ali": "Alistar",
        "Mundo": "Dr. Mundo",
        "Kaisa": "Kai'Sa",
        "Khazix": "Kha'Zix",
        "MF": "Miss Fortune",
        "Sarah": "Miss Fortune",
        "Reksai": "Rek'Sai",
        "Velkoz": "Vel'koz",
        "Xin": "Xin Zhao",
    }

    API_URL_NAME_MATCHES = {
        "Jarvan IV": "JarvanIV",
        "Nunu & Willump": "Nunu",
        "Kog\'Maw": "KogMaw",
        "LeBlanc": "Leblanc",
        "Wukong": "MonkeyKing",
        "Rek'Sai": "RekSai",
        "Renata Glasc": "Renata",
    }

    TRACKED_CHAMP_PM_MSG = f"You are receiving this message because you opted to track this champion in League of " \
                           f"Legends professional play. To disable these messages from Zoe Bot, reply with " \
                           f"'**~follow pro <champion_name>'"

    TRACKED_SKIN_PM_MSG = f"You are receiving this message because you opted to track League of " \
                          f"Legends skin sales for this champion. To disable these messages, reply " \
                          f"with '~follow skin <champion_name>'"

    # Class Constants: CHAMP_DICT, CHAMP_SKINS_DICT
    CHAMP_DICT = dict()

    @classmethod
    def get_champ_dict(cls, refresh_dict=False):
        """
        Returns and sets CHAMP_DICT['id'] -> 'champion_name'
        """
        if refresh_dict or not cls.CHAMP_DICT:
            watcher = get_lol_watcher()
            # check league's latest patch version
            latest = watcher.data_dragon.versions_for_region(Constants.REGION)['n']['champion']
            champ_list = watcher.data_dragon.champions(latest, False, 'en_US')
            champ_dict = {}
            for key in champ_list['data']:
                row = champ_list['data'][key]
                name = row['name']
                champ_dict[row['key']] = name
            cls.CHAMP_DICT = champ_dict
        return cls.CHAMP_DICT

    CHAMP_SKINS_DICT = dict()

    @classmethod
    def get_champion_skins_dict(cls):
        with open('Data/all_champion_skins.txt', encoding="ISO-8859-1") as file:
            data = file.read()
            cls.CHAMP_SKINS_DICT = ast.literal_eval(data)
            return cls.CHAMP_SKINS_DICT

    FREE_CHAMPS = []

    @classmethod
    def get_free_champ_rotation(cls):
        # Fetch f2p champ ids
        free_champ_ids = get_free_champion_ids()['freeChampionIds']
        free_rotation = [Constants.CHAMP_DICT[str(champ_id)] for champ_id in free_champ_ids]
        free_rotation.sort()
        cls.FREE_CHAMPS = free_rotation
        return cls.FREE_CHAMPS


async def sendDm(bot, user_id, message):
    user = await bot.get_user(user_id)
    await user.send(message)


def get_free_champion_ids():
    return get_lol_watcher().champion.rotations(Constants.REGION)


def init_champion_skins_dict():
    """
    Initialize CHAMP_SKINS_DICT: Dict['champion'] -> {Set of champ's skins by name}
    Should be called every new patch
    """
    watcher = get_lol_watcher()
    latest = watcher.data_dragon.versions_for_region(Constants.REGION)['n']['champion']
    champ_skins_dict = dict()
    for champion in Constants.get_champion_skins_dict().keys():
        url_champion = get_champion_name_url(champion)
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
    # Write the dictionary to a txt file so that I don't have to run this every time i start up the bot
    with open('Data/all_champion_skins.txt', 'w') as file:
        file.write(str(champ_skins_dict))
    return champ_skins_dict


# Does the str start with '~'?
def is_command(message):
    return message.content[0] == '~'


async def clear_cache(cache, h):
    present = datetime.datetime.now()
    if cache:
        for k in list(cache.keys()):
            value = cache[k]
            delta = (present - value).total_seconds()
            if delta > h * 3600:
                cache.pop(k)


async def check_tracked_skins(bot):
    """Message people to notify if a champ they like has a skin on sale"""
    with open("Data/skin_sales_data.json", 'r') as file:
        skins_sale_data = json.load(file)
        index = 0
        # List of image URLs
        image_urls_file = open("Data/image_urls_list.txt", "r")
        image_urls_list = []
        for image_url in image_urls_file:
            image_urls_list.append(image_url)
        # Parse data of every skin on sale
        for entry in skins_sale_data:
            skin_name_rp_cost = " ".join(entry['skin_name_rp_cost'].split())
            skin_image_url = image_urls_list[index]
            skin_data = skin_name_rp_cost.split(' ')
            skin_name = ' '.join(skin_data[0: len(skin_data) - 3])
            skin_rp_cost = ' '.join(skin_data[len(skin_data) - 2: len(skin_data)])
            skin_db = bot.favorite_skin_db
            for champ_name in Constants.CHAMP_DICT.values():
                if skin_name in Constants.CHAMP_SKINS_DICT[champ_name]:
                    champion = Query()
                    query_results = skin_db.get(champion['champion_name'] == champ_name)
                    if query_results is not None:
                        user_ids_list = query_results['user_ids']
                        for user_id in user_ids_list:
                            user = bot.get_user(user_id)
                            await send_ss_embed_user(user, skin_name, skin_rp_cost, skin_image_url)
            index += 1


# TODO: this
async def send_ss_embed_user(user, skin_name, skin_rp_cost, skin_image_url):
    embed = discord.Embed(color=0x87cefa)
    embed.add_field(name='Weekly Champion Skin Sales',
                    value=f"{skin_name} is on sale this week for {skin_rp_cost}!",
                    inline=False)
    embed.set_image(url=skin_image_url)
    embed.set_footer(text=Constants.TRACKED_SKIN_PM_MSG)
    await user.send(embed=embed)


def check_for_special_name_match(champion_name):
    for special_name, official_name in Constants.SPECIAL_CHAMPION_NAME_MATCHES_DICT.items():
        if fuzz.ratio(special_name.lower(), champion_name.lower()) >= 90:
            return official_name
    return champion_name


def get_fuzzy_match(champion_name):
    for champ in Constants.CHAMP_DICT.values():
        if fuzz.token_sort_ratio(champ, champion_name) >= 90:
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


# Return data for all live pro play games
def get_all_live_matches():
    api = get_lolesports_api()
    live_matches = api.get_live()
    matches = live_matches['schedule']['events']
    return matches


# Return the two team icons for a live match
def get_team_icons(live_match):
    teams = live_match['match']['teams']
    icons_dict = dict()
    team1_code = teams[0]['code']
    icons_dict[team1_code] = teams[0]['image']
    team2_code = teams[1]['code']
    icons_dict[team2_code] = teams[1]['image']
    return icons_dict


# Return the icon for a team
def get_icon(player_champ_info, icons_dict):
    player_name = player_champ_info[0]
    info = player_name.split(' ')
    team_code = info[0]
    return icons_dict[team_code]


# Given a bunch of games in a match, return the match id of the one in progress
def get_live_match_id(games):
    for game in games:
        if game['state'] == "inProgress":
            return int(game['id'])


def get_pp_embed_for_player(game_info, message, pm=False):
    """Given game info, returns an embed with all relevant information attached
    """
    embed = discord.Embed(color=0x87cefa)
    player_info = game_info['player']
    player_name = player_info[0]
    player_champ_name_and_role = f'{player_info[1]} {player_info[2]}'
    tournament_name = player_info[3]
    url = Constants.LOL_ESPORTS_LIVE_LINK + player_info[4]
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
        embed.set_footer(text=message)
    return embed


def get_zoe_error_message():
    quote = random.choice(Quotes.Zoe_error_message)
    if quote == "*Zoe groans in frustration.*":
        return quote
    else:
        return f'"*{quote}*"'


# Get champions being played on a team
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


# Gather game data for a live game in a match
def get_live_game_data(live_match):
    api = get_lolesports_api()
    game_id = get_live_match_id(live_match['match']['games'])
    if game_id is not None:
        try:
            return api.get_window(game_id, "")
        # JSONDecodeError occurs if game is unstarted
        except JSONDecodeError:
            pass


# Return a list of all champs currently in pro play
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


# Send list of all champions in live pro games
async def pro_all(channel):
    all_live_champs = get_all_live_champs()
    if len(all_live_champs) == 0 or all_live_champs is None:
        await channel.send("No champions found in live professional games :(")
    else:
        await channel.send("All champions in live professional games: " + ', '.join(all_live_champs))


# Given a team and a role, returns the player in that role
def get_player_info(role, team):
    for player in team:
        r = player['role'].capitalize()
        if r == role:
            player_name = player['summonerName']
            player_champion = player['championId']
            champion_name = check_for_special_name_match(re.sub(r"([A-Z])", r" \1", player_champion)[1:]) if \
                player_champion != 'JarvanIV' else check_for_special_name_match('Jarvan')
            return [player_name, champion_name, role]


# "Is {champion_name} on the given teams? -> Return player_champ_tourney_info
def is_champion_on_team(team, name_match):
    for player in team:
        # player['championId'] wont include spaces which breaks format_champion_name(), hence why it is not used
        player_champion = player['championId']
        champion_name = check_for_special_name_match(re.sub(r"([A-Z])", r" \1", player_champion)[1:]) if \
            player_champion != 'JarvanIV' else check_for_special_name_match('Jarvan')
        if champion_name == name_match:
            # Return player info once we find a result
            return player['summonerName'], champion_name, player['role'].capitalize()
    return None


def find_pro_play_matchup(champion_name):
    """
    Given a champion name, searches all live pro games and returns a list of tuples containing information about
    the player, their champ name, role, and tourney
    """
    matches_found = []
    game_info = dict()
    live_matches = get_all_live_matches()
    for live_match in live_matches:
        try:
            if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
                # LCS, LCK, LEC, etc.
                # live_match['streams'] returns a list of dictionaries with streams info
                # streams['parameter'] returns the server (hopefully)
                # league = live_match['streams']
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
                    player_champ_info = list(player_champ_info) + tournament_info
                    game_info['player'] = player_champ_info
                    game_info['enemy'] = enemy_player_info
                    matches_found.append(game_info)
        except (Exception,):
            pass
    return matches_found


async def check_tracked_champions(bot):
    """Every minute, checks all live champions and their db of subscribed users to message the users about a game
    where the champion is being played, then updates the cache if the user has not already been messaged
    """
    db = Constants.DB
    all_live_champs = get_all_live_champs()
    champion = Query()
    for champ in all_live_champs:
        champ_name_user_ids_dict = db.get(champion['champion_name'] == champ)
        if champ_name_user_ids_dict is not None:
            for user_id in champ_name_user_ids_dict['user_ids']:
                matches_found = find_pro_play_matchup(champ)
                if matches_found:
                    for game_info in matches_found:
                        await update_cache(bot, user_id)
                        await send_pp_embed_user(bot, user_id, game_info)


async def send_pp_embed_user(bot, user_id, game_info):
    user = bot.get_user(user_id)
    await user.send(embed=get_pp_embed_for_player(
        game_info,
        message=Constants.TRACKED_CHAMP_PM_MSG,
        pm=True))


# TODO: this
async def send_msg_user():
    return


async def update_cache(bot, game_info):
    """
    Update cache with new game ids upon seeing them for the first time, else it does nothing and won't msg users
    """
    cache = bot.cache
    game_id = game_info['player'][7]
    champion = game_info['player'][1]
    champ_game_tuple = champion, game_id
    if champ_game_tuple not in cache:
        cache[champ_game_tuple] = datetime.datetime.now()


async def add_remove_favorite(message, champion_name, db, user_id, success_message):
    """Utility method to add/remove champions from their list of favorites"""
    added = set()
    removed = set()
    not_found = set()
    # Format args
    # "Alistar, Kai'sa, Lee Sin, Not a Champion" -> ["Alistar", "Kai'sa", "Lee Sin", None]
    champ_names_list = ' '.join(champion_name).split(',')
    for unformatted_name in champ_names_list:
        champion_name = format_champion_name(unformatted_name)
        if not unformatted_name:
            continue
        elif not champion_name and unformatted_name:
            not_found.add(unformatted_name)
            continue
        # Query db for formatted champ name
        champion = Query()
        champ_name_user_ids_dict = db.get(champion['champion_name'] == champion_name)
        user_ids_list = [] if champ_name_user_ids_dict is None else champ_name_user_ids_dict['user_ids']
        # Create DB and add user if it doesn't already exist
        if champ_name_user_ids_dict is None:
            user_ids_list.append(user_id)
            db.insert({'champion_name': champion_name, 'user_ids': user_ids_list})
            added.add(champion_name)
        # DB exists but user is not in it
        elif user_id not in user_ids_list:
            user_ids_list.append(user_id)
            db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
            added.add(champion_name)
        else:
            user_ids_list.remove(user_id)
            db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
            removed.add(champion_name)
    # NGL i have no idea if 'else None' is bad here
    await message.channel.send(f"<@{user_id}> is now {success_message} {', '.join(added)}.") if added else None
    await message.channel.send(
        f"<@{user_id}> is no longer {success_message} {', '.join(removed)}.") if removed else None
    await message.channel.send(
        f"No champion with name(s): '{' '.join(not_found)}' found.") if not_found else None


def get_following_list(user_id, db, success_message, second=False):
    tracked_list = []
    for champ_name in Constants.CHAMP_DICT.values():
        champion = Query()
        query_results = db.get(champion['champion_name'] == champ_name)
        if query_results is not None:
            user_ids_list = query_results['user_ids']
            if user_id in user_ids_list:
                tracked_list.append(champ_name)
    if len(tracked_list) != 0:
        # following skin sales for:
        # following live professional games for:
        return f"<@{user_id}> is {success_message} {', '.join(tracked_list)}" if not second \
            else f"is {success_message} {', '.join(tracked_list)}"
    else:
        return f"<@{user_id}> is not {success_message} any champion... (Except for Zoe, obviously)" if not second \
            else f"is not {success_message} any champion... (Except for Zoe, obviously)"


def get_champion_name_url(champion):
    # Special Case names
    if champion in Constants.API_URL_NAME_MATCHES.keys():
        return Constants.API_URL_NAME_MATCHES[champion]
    elif "'" in champion:
        # Account for Void champion names ('Kai'sa') formatting
        return champion.replace("'", '').lower().capitalize()
    else:
        # and champions with space in their names ('Lee Sin'), as well as '.' (looking at you mundo)
        url_champion = champion.replace(' ', '').replace('.', '') if ' ' in champion or '.' in champion \
            else champion
        return url_champion


def update_free_rotation_images():
    # Constants.FREE_CHAMPS should have been initialized upon bot startup
    free_rotation = Constants.FREE_CHAMPS
    count = 0
    images = []
    for champion in free_rotation:
        url_champion_name = get_champion_name_url(champion)
        url = f"http://ddragon.leagueoflegends.com/cdn/img/champion/loading/{url_champion_name}_0.jpg"
        # Champion loading icon jpg is 308 x 560
        r = requests.get(url,
                         stream=True, headers={'User-agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            # Write a single skin splashart to the Data/skin_sale_jpgs dir
            with open(f"Data/free_rotation_jpgs/free_champ{count}.jpg", 'wb') as file:
                # write image to file
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, file)
                image = imread(file.name)[..., :3]
                x = int(image.shape[1] * 1)
                y = int(image.shape[0] * 1)
                # resizing image
                image = cv2.resize(image, dsize=(x, y), interpolation=cv2.INTER_CUBIC)
                # cropping image
                # x_crop_amount = int(x * 0)
                # y_crop_amount = int(y * 0)
                # image = image[y_crop_amount: y - y_crop_amount, x_crop_amount:x - x_crop_amount]
                images.append(image)
        count += 1
    # stack 2 rows of 8 champion loading icon images
    rows = np.hstack(images[0:8]), np.hstack(images[8:16])
    image = np.vstack(rows)
    # Convert the image backt to RGB because OpenCV uses BGR as its colour order for images
    full_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Save the full image to a file
    imwrite('Data/free_rotation_jpgs/free_rotation_full.jpg', full_image)
