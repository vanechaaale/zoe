from tinydb import Query

import utilities
from utilities import Constants


async def follow(message, *champion_name):
    """Command to follow a champion's presence in pro play"""
    # If no args were given
    if not champion_name:
        await message.channel.send(
            "use '~favorite <champion>, <champion>, **...**' to be notified when this champion is played in a "
            "professional game!")
        return
    else:
        await utilities.favorite_pro_skin(
            message=message,
            champion_name=champion_name,
            db=Constants.DB,
            user_id=message.author.id,
            success_message="following live professional matches for:"
        )


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
