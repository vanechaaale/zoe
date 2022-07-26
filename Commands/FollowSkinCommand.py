from tinydb import Query

import utilities
from utilities import Constants


async def favorite(message, *champion_name):
    # If no args were given
    if not champion_name:
        await message.channel.send(
            "use '~favorite <champion>, <champion>, **...**' to be notified when their skins go on sale!")
        return
    else:
        added = set()
        removed = set()
        not_found = set()
        user_id = message.author.id
        skin_db = Constants.SKIN_DB
        # Format args
        # "Alistar, Kai'sa, Lee Sin, Not a Champion" -> ["Alistar", "Kai'sa", "Lee Sin", None]
        champ_names_list = ' '.join(champion_name).split(',')
        for unformatted_name in champ_names_list:
            champion_name = utilities.format_champion_name(unformatted_name)
            if not champion_name:
                not_found.add(unformatted_name)
                continue
            # Query db for formatted champ name
            champion = Query()
            champ_name_user_ids_dict = skin_db.get(champion['champion_name'] == champion_name)
            user_ids_list = [] if champ_name_user_ids_dict is None else champ_name_user_ids_dict['user_ids']
            # Create DB and add user if it doesn't already exist
            if champ_name_user_ids_dict is None:
                user_ids_list.append(user_id)
                skin_db.insert({'champion_name': champion_name, 'user_ids': user_ids_list})
                added.add(champion_name)
            # DB exists but user is not in it
            elif user_id not in user_ids_list:
                user_ids_list.append(user_id)
                skin_db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
                added.add(champion_name)
            else:
                user_ids_list.remove(user_id)
                skin_db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
                removed.add(champion_name)
        # NGL i have no idea if 'else None' is bad here
        await message.channel.send(f"Now checking weekly skin sales for: {', '.join(added)}.") if added else None
        await message.channel.send(
            f"No longer checking weekly skin sales for: {', '.join(removed)}.") if removed else None
        await message.channel.send(
            f"No champion with name(s): '{' '.join(not_found)}' found.") if not_found else None


async def favlist(message):
    tracked_list = []
    user_id = message.author.id
    # user = message.author
    for champ_name in Constants.CHAMP_DICT.values():
        champion = Query()
        skin_db = Constants.SKIN_DB
        query_results = skin_db.get(champion['champion_name'] == champ_name)
        if query_results is not None:
            user_ids_list = query_results['user_ids']
            if user_id in user_ids_list:
                tracked_list.append(champ_name)
    if len(tracked_list) != 0:
        await message.channel.send(
            f"<@{user_id}>'s favorite champions: {', '.join(tracked_list)}")
    else:
        await message.channel.send(f"You have no favorite champions... (Other than Zoe obviously)")
