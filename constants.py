import random
import re
import discord
from discord.ext import commands
import Data
from Data import Quotes, gifs, cache
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
import datetime

# read API key
with open('Data/api_key') as f:
    API_KEY = f.readline()
LOL_ESPORTS_LIVE_LINK = 'https://lolesports.com/live/'
API = Lolesports_API()
WATCHER = LolWatcher(API_KEY)
my_region = 'na1'
FREE_CHAMPION_IDS = WATCHER.champion.rotations(my_region)
DB = TinyDB('Data/database.json')

# check league's latest version
latest = WATCHER.data_dragon.versions_for_region(my_region)['n']['champion']
# Lets get some champions static information
static_champ_list = WATCHER.data_dragon.champions(latest, False, 'en_US')


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

    async def pro_all(self, channel):
        all_live_champs = self.get_all_live_champs()
        if len(all_live_champs) == 0 or all_live_champs is None:
            await channel.send("There are currently no live pro games :(")
        else:
            await channel.send("All champions in live pro games: " + ', '.join(all_live_champs))

    def get_champs_on_team(self, team):
        live_champs = set()
        for player in team:
            # TODO: MAKE THIS WORK WITH FORMAT CHAMP NAME METHOD
            champion_name = player['championId']
            if champion_name == "JarvanIV":
                current_champ = "Jarvan IV"
            # reformats the string to put spaces between capital letters :D
            else:
                current_champ = self.check_for_special_name_match(re.sub(r"([A-Z])", r" \1", champion_name)[1:])
            if current_champ not in live_champs:
                live_champs.add(current_champ)
        return live_champs

    # Given a champion name, searches all live pro games and returns a list of tuples containing information about
    # the player, their champ name, role, and tourney
    def find_pro_play_champion(self, champion_name):
        matches_found = []
        live_matches = self.get_all_live_matches()
        for live_match in live_matches:
            try:
                if live_match['type'] != 'show' and live_match['state'] == 'inProgress':
                    tournament_name = live_match['league']['name']
                    block_name = live_match['blockName']
                    url_slug = live_match['league']['slug']
                    team_icons = self.get_team_icons(live_match)
                    live_game_data = self.get_live_game_data(live_match)
                    blue_team = live_game_data['gameMetadata']['blueTeamMetadata']['participantMetadata']
                    red_team = live_game_data['gameMetadata']['redTeamMetadata']['participantMetadata']
                    red = self.is_champion_on_team(blue_team, tournament_name, block_name, champion_name)
                    blue = self.is_champion_on_team(red_team, tournament_name, block_name, champion_name)
                    player_champ_tourney_info = red if red is not None else blue
                    icon = self.get_icon(team_icons, red, blue)
                    if player_champ_tourney_info:
                        player_champ_tourney_info.append(url_slug)
                        player_champ_tourney_info.append(icon)
                        matches_found.append(player_champ_tourney_info)
            except (Exception,):
                pass
        return matches_found

    # Given the red or blue side, tourney name, block name, and champ name, returns the player_champ_tourney_info
    # if the given champ is on the team
    def is_champion_on_team(self, team, tournament_name, block_name, champion_name):
        for player in team:
            # TODO: FIX THE FORMATTING OF THESE NAMES TO WORK WITH FORMAT_CHAMP_NAME()
            champion = self.check_for_special_name_match(re.sub(r"([A-Z])", r" \1", player['championId'])[1:])
            if champion.lower() == champion_name.lower():
                player_name = player['summonerName']
                role = player['role'].capitalize()
                return [player_name, f"{champion_name} {role}", f"{tournament_name} {block_name}"]
        return None

    c = cache.CACHE

    # Every minute, checks all live champions and their db of subscribed users to message the users about a game
    # where the champion is being played, then updates the cache if the user has not already been messaged
    async def check_tracked_champions(self):
        while True:
            all_live_champs = self.get_all_live_champs()
            champion = Query()
            for champ in all_live_champs:
                champ_name_user_ids_dict = db.get(champion['champion_name'] == champ)
                if champ_name_user_ids_dict is not None:
                    for user_id in champ_name_user_ids_dict['user_ids']:
                        matches_found = self.find_pro_play_champion(champ)
                        if matches_found:
                            for player_champ_tourney_info in matches_found:
                                games = player_champ_tourney_info['games']
                                game_id = self.get_live_match_id(games)
                                await self.update_cache(game_id, user_id)
            await asyncio.sleep(60)

    # update cache with new game ids upon seeing them for the first time, else it does nothing and won't msg users
    async def update_cache(self, game_id, user_id):
        if game_id not in cache:
            c[game_id]: datetime.datetime.now()
            user = bot.get_user(user_id)
            if user is not None:
                await user.send(embed=self.get_embed_for_player(player_champ_tourney_info))

    async def clear_cache(self):
        while True:
            # 2 hours in between cache clears
            hours = 2*3600
            present = datetime.datetime.now()
            if cache:
                for key, value in cache:
                    if present - value > hours:
                        cache.pop(key)
            await asyncio.sleep(hours)

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
        red_team_image = teams[0]['image']
        blue_team_image = teams[1]['image']
        return red_team_image, blue_team_image

    def get_icon(self, team_icons, red, blue):
        if red is not None:
            return team_icons[1]
        elif blue is not None:
            return team_icons[0]
        else:
            return None

    def get_live_game_data(self, live_match):
        game_id = self.get_live_match_id(live_match['match']['games'])
        if game_id is not None:
            try:
                return API.get_window(game_id, "")
            # JSONDecodeError occurs if game is unstarted
            except JSONDecodeErorr:
                pass

    def get_live_match_id(self, games):
        for game in games:
            if game['state'] == "inProgress":
                return int(game['id'])

    def get_embed_for_player(self, match):
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

    def get_zoe_error_message(self):
        quote = random.choice(Quotes.Zoe_error_message)
        if quote == "*Zoe groans in frustration.*":
            return quote
        else:
            return f'"*{quote}*"'

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

    def is_command(self, message):
        return message.content[0] == '~'

    def format_champion_name(self, champion_name):
        champion_name = self.get_fuzzy_match(self.check_for_special_name_match(champion_name))
        if champion_name == '':
            return None
        else:
            return champion_name

    async def sendDm(self, user_id, message):
        user = await client.fetch_user(user_id)
        await user.send(message)


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

help_command = commands.DefaultHelpCommand(no_category='List of Zoe Bot Commands')
intents = discord.Intents.default()
intents.members = True

BOT = commands.Bot(
    command_prefix='~', help_command=help_command,
    description="I'm Zoe, what's your name?", intents=intents)
