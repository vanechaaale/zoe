import BaseMessageResponse
import Data
import asyncio
import constants
import datetime
import discord
import random
import re
import threading
import time
from Data import Quotes, gifs
from discord.ext import commands
from fuzzywuzzy import fuzz
from lolesports_api import Lolesports_API
from riotwatcher import LolWatcher
from threading import Thread
from tinydb import TinyDB, Query, where

# USING LIVE DATABASE
db = TinyDB('Data/database.json')

# read API key
with open('Data/api_key') as f:
    API_KEY = f.readline()
LOL_ESPORTS_LIVE_LINK = 'https://lolesports.com/live/'
API = Lolesports_API()
WATCHER = LolWatcher(API_KEY)
my_region = 'na1'
FREE_CHAMPION_IDS = WATCHER.champion.rotations(my_region)

# check league's latest version
latest = WATCHER.data_dragon.versions_for_region(my_region)['n']['champion']
# Lets get some champions static information
static_champ_list = WATCHER.data_dragon.champions(latest, False, 'en_US')

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

CACHE = dict()

help_command = commands.DefaultHelpCommand(no_category='List of Zoe Bot Commands')
intents = discord.Intents.default()
intents.members = True

BOT = commands.Bot(
    command_prefix='~', help_command=help_command,
    description="I'm Zoe, what's your name?", intents=intents)


class Constants:
    def __init__(self):
        # champ static list data to dict for looking up
        # Champ_id : Champ_name
        # init data
        CHAMP_DICT = {}
        for key in static_champ_list['data']:
            row = static_champ_list['data'][key]
            name = row['name']
            CHAMP_DICT[row['key']] = name
        self.champ_dict = CHAMP_DICT

    # Send list of all champions in live pro games
    async def pro_all(self, channel):
        all_live_champs = self.get_all_live_champs()
        if len(all_live_champs) == 0 or all_live_champs is None:
            await channel.send("There are currently no champions in live professional games :(")
        else:
            await channel.send("All champions in live professional games: " + ', '.join(all_live_champs))

    def get_champs_on_team(self, team):
        live_champs = set()
        for player in team:
            # self.format_champion_name() doesn't work with spaces so player['championId'] breaks it
            champion_name = player['championId']
            # reformats the string to put spaces between capital letters :D
            current_champ = self.check_for_special_name_match(re.sub(r"([A-Z])", r" \1", champion_name)[1:])
            if current_champ not in live_champs:
                live_champs.add(current_champ)
        return live_champs

    # Given a champion name, searches all live pro games and returns a list of tuples containing information about
    # the player, their champ name, role, and tourney
    def find_pro_play_matchup(self, champion_name):
        matches_found = []
        game_info = dict()
        live_matches = self.get_all_live_matches()
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
                    game_id = self.get_live_match_id(live_match['match']['games'])
                    team_icons = self.get_team_icons(live_match)
                    live_game_data = self.get_live_game_data(live_match)
                    blue_team = live_game_data['gameMetadata']['blueTeamMetadata']['participantMetadata']
                    red_team = live_game_data['gameMetadata']['redTeamMetadata']['participantMetadata']
                    red = self.is_champion_on_team(red_team, champion_name)
                    blue = self.is_champion_on_team(blue_team, champion_name)
                    if red is not None:
                        player_champ_info = red
                        role = player_champ_info[2]
                        enemy_player_info = self.get_player_info(role, blue_team)
                        icon = self.get_icon(player_champ_info, team_icons)
                    else:
                        player_champ_info = blue
                        role = player_champ_info[2]
                        enemy_player_info = self.get_player_info(role, red_team)
                        icon = self.get_icon(player_champ_info, team_icons)
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

    # Given the red or blue side, tourney name, block name, and champ name, returns the player_champ_tourney_info
    # if the given champ is on the team
    def is_champion_on_team(self, team, champion_name):
        for player in team:
            # player['championId'] wont include spaces which breaks format_champion_name(), hence why it is not used
            champion = self.check_for_special_name_match(re.sub(r"([A-Z])", r" \1", player['championId'])[1:])
            role = player['role'].capitalize()
            if champion.lower() == champion_name.lower():
                return self.get_player_info(role, team)
        return None

    # Given a team and a role, returns the player in that role
    def get_player_info(self, role, team):
        for player in team:
            r = player['role'].capitalize()
            if r == role:
                player_name = player['summonerName']
                champion_name = self.check_for_special_name_match(re.sub(r"([A-Z])", r" \1", player['championId'])[1:])
                return [player_name, champion_name, role]

    # Every minute, checks all live champions and their db of subscribed users to message the users about a game
    # where the champion is being played, then updates the cache if the user has not already been messaged
    async def check_tracked_champions(self):
        all_live_champs = self.get_all_live_champs()
        champion = Query()
        for champ in all_live_champs:
            champ_name_user_ids_dict = db.get(champion['champion_name'] == champ)
            if champ_name_user_ids_dict is not None:
                for user_id in champ_name_user_ids_dict['user_ids']:
                    matches_found = self.find_pro_play_matchup(champ)
                    if matches_found:
                        for game_info in matches_found:
                            await self.update_cache(user_id, game_info)

    # update cache with new game ids upon seeing them for the first time, else it does nothing and won't msg users
    async def update_cache(self, user_id, game_info):
        game_id = game_info['player'][7]
        champion = game_info['player'][1]
        champ_game_tuple = champion, game_id
        if champ_game_tuple not in CACHE:
            CACHE[champ_game_tuple] = datetime.datetime.now()
            user = BOT.get_user(user_id)
            await user.send(embed=self.get_embed_for_player(game_info))

    # Clear cache every h hours
    async def clear_cache(self, h):
        present = datetime.datetime.now()
        if CACHE:
            for key in list(CACHE.keys()):
                value = CACHE[key]
                delta = (present - value).total_seconds()
                if delta > h * 3600:
                    CACHE.pop(key)

    # Renata -> Renata Glasc
    def check_for_special_name_match(self, champion_name):
        for special_name, official_name in SPECIAL_CHAMPION_NAME_MATCHES_DICT.items():
            if fuzz.ratio(special_name.lower(), champion_name.lower()) >= 80:
                return official_name
        return champion_name

    def get_all_live_matches(self):
        live_matches = API.get_live()
        matches = live_matches['schedule']['events']
        return matches

    def get_fuzzy_match(self, champion_name):
        for champ in self.champ_dict.values():
            if fuzz.token_sort_ratio(champ, champion_name) >= 80:
                return champ
        return ''

    def get_team_icons(self, live_match):
        teams = live_match['match']['teams']
        icons_dict = dict()
        team1_code = teams[0]['code']
        icons_dict[team1_code] = teams[0]['image']
        team2_code = teams[1]['code']
        icons_dict[team2_code] = teams[1]['image']
        return icons_dict

    def get_icon(self, player_champ_info, icons_dict):
        player_name = player_champ_info[0]
        data = player_name.split(' ')
        team_code = data[0]
        return icons_dict[team_code]

    # Gather game data for a live game in a match
    def get_live_game_data(self, live_match):
        game_id = self.get_live_match_id(live_match['match']['games'])
        if game_id is not None:
            try:
                return API.get_window(game_id, "")
            # JSONDecodeError occurs if game is unstarted
            except JSONDecodeErorr:
                pass

    # Given a bunch of games in a match, return the match id of the one in progress
    def get_live_match_id(self, games):
        for game in games:
            if game['state'] == "inProgress":
                return int(game['id'])

    # Given player_champ_tourney_etc info, returns an embed with all relevant information attached
    def get_embed_for_player(self, game_info):
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
        return embed

    def get_zoe_error_message(self):
        quote = random.choice(Quotes.Zoe_error_message)
        if quote == "*Zoe groans in frustration.*":
            return quote
        else:
            return f'"*{quote}*"'

    # Return a list of all champs currently in pro play
    def get_all_live_champs(self):
        all_live_champs_set = set()
        live_matches = self.get_all_live_matches()
        for live_match in live_matches:
            try:
                if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
                    live_game_data = self.get_live_game_data(live_match)
                    blue_team = live_game_data['gameMetadata']['blueTeamMetadata']['participantMetadata']
                    red_team = live_game_data['gameMetadata']['redTeamMetadata']['participantMetadata']
                    blue_team_champs = self.get_champs_on_team(blue_team)
                    red_team_champs = self.get_champs_on_team(red_team)
                    all_live_champs_set = all_live_champs_set.union(red_team_champs)
                    all_live_champs_set = all_live_champs_set.union(blue_team_champs)
            except (Exception,):
                pass
        all_live_champs = list(all_live_champs_set)
        all_live_champs.sort()
        return all_live_champs

    # Does the str start with '~'?
    def is_command(self, message):
        return message.content[0] == '~'

    # Given a janky version of a champion, format it to be pretty
    #     str given_name: name input as a string
    #     Return properly formatted champion name as a string
    def format_champion_name(self, champion_name):
        champion_name = self.get_fuzzy_match(self.check_for_special_name_match(champion_name))
        if champion_name == '':
            return None
        else:
            return champion_name

    async def sendDm(self, user_id, message):
        user = await client.fetch_user(user_id)
        await user.send(message)
