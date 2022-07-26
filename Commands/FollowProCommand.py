from tinydb import Query
from utilities import format_champion_name, Constants


async def follow(message, *champion_name):
    # Save input
    old_champion_name = champion_name
    # Format given champ name
    champion_name = format_champion_name(' '.join(champion_name))
    if not champion_name and not old_champion_name:
        await message.channel.send(
            "use '~follow <champion>' to be notified when a champion is live in pro play!")
        return
    elif not champion_name and old_champion_name:
        await message.channel.send(
            f"No champion with name '{' '.join(old_champion_name)}' was found.")
        return
    # Query champion user id list
    champion = Query()
    db = Constants.DB
    user_id = message.author.id
    champ_name_user_ids_dict = db.get(champion['champion_name'] == champion_name)
    # I tried using a set but it broke whenever i called db.insert()
    user_ids_list = [] if champ_name_user_ids_dict is None else champ_name_user_ids_dict['user_ids']
    if champ_name_user_ids_dict is None:
        user_ids_list.append(user_id)
        db.insert({'champion_name': champion_name, 'user_ids': user_ids_list})
        await message.channel.send(f"Now following live professional games for {champion_name}.")
    elif user_id not in user_ids_list:
        user_ids_list.append(user_id)
        db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
        await message.channel.send(f"Now following live professional games for {champion_name}.")
    else:
        user_ids_list.remove(user_id)
        db.update({'user_ids': user_ids_list}, champion['champion_name'] == champion_name)
        await message.channel.send(f"No longer following live professional games for {champion_name}.")


async def following(message):
    tracked_list = []
    user_id = message.author.id
    for champ_name in Constants.CHAMP_DICT.values():
        champion = Query()
        db = Constants.DB
        query_results = db.get(champion['champion_name'] == champ_name)
        if query_results is not None:
            user_ids_list = query_results['user_ids']
            if user_id in user_ids_list:
                tracked_list.append(champ_name)
    if len(tracked_list) != 0:
        await message.channel.send(
            f"<@{user_id}> is currently following professional games for: "
            f"{', '.join(tracked_list)}")
    else:
        await message.channel.send(f"<@{user_id}> is currently not following professional games for any champions!")
