import asyncio
import discord
from constants import format_champion_name
from tinydb import Query


async def favorite(message, base_command, *champion_name):
    # format champion_name
    champion_name = format_champion_name(' '.join(champion_name))
    if not champion_name:
        await message.channel.send(
            f"use '~favorite <champion>' to be notified when that champion's skins go on sale!")
        return
    # Query champion user id list
    champion = Query()
    user_id = message.author.id
    skin_db = base_command.skin_db
    champ_name_user_ids_dict = skin_db.get(champion['champion_name'] == champion_name)
    # I tried using a set but it broke whenever i called db.insert()
    user_ids_list = [] if champ_name_user_ids_dict is None else champ_name_user_ids_dict['user_ids']
    if champ_name_user_ids_dict is None:
        user_ids_list.append(user_id)
        skin_db.insert({'champion_name': champion_name, 'user_ids': user_ids_list})
        await message.channel.send(f"Now tracking skin sales for {champion_name}.")
    elif user_id not in user_ids_list:
        user_ids_list.append(user_id)
        skin_db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
        await message.channel.send(f"Now tracking skin sales for {champion_name}.")
    else:
        user_ids_list.remove(user_id)
        skin_db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
        await message.channel.send(f"No longer tracking skin sales for {champion_name}.")


async def favlist(message, base_command):
    tracked_list = []
    user_id = message.author.id
    user = message.author
    for champ_name in base_command.champ_dict.values():
        champion = Query()
        skin_db = base_command.skin_db
        query_results = skin_db.get(champion['champion_name'] == champ_name)
        if query_results is not None:
            user_ids_list = query_results['user_ids']
            if user_id in user_ids_list:
                tracked_list.append(champ_name)
    if len(tracked_list) != 0:
        await message.channel.send(
            f"{user.nick}'s favorite champions: {', '.join(tracked_list)}")
    else:
        await message.channel.send(f"You have no favorite champions... (Other than Zoe obviously)")
