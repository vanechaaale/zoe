import asyncio
import discord
from tinydb import Query


async def test(message, base_command, *champion_name):
    # format champion_name
    champion_name = base_command.format_champion_name(' '.join(champion_name))
    if not champion_name:
        await message.channel.send(
            f"use '~test <champion>' to be notified when a champion's skins go on sale!")
        return
    # Query champion user id list
    champion = Query()
    user_id = message.author.id
    skin_db = SKIN_DB
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