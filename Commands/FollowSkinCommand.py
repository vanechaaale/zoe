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
        await utilities.favorite_pro_skin(
            message=message,
            champion_name=champion_name,
            db=Constants.SKIN_DB,
            user_id=message.author.id,
            success_message="following weekly skin sales for:"
        )


async def favlist(message):
    tracked_list = []
    user_id = message.author.id
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
        await message.channel.send(f"<@{user_id}> has no favorite champions... (Other than Zoe obviously)")
