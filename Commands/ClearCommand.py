from tinydb import Query

import utilities
from utilities import Constants


async def clear(message, *args):
    """
    A command to clear the list of a user's favorite or followed champs from the database
    ' ~clear pro, ~clear fav
    """
    user_id = message.author.id
    db_type = ' '.join(args).lower()
    if db_type == 'pro':
        db = Constants.DB
        success_message = f"Successfully cleared <@{user_id}>'s list of champions followed in professional games."
    elif db_type == 'skin':
        db = Constants.SKIN_DB
        success_message = f"Successfully cleared <@{user_id}>'s list of champions followed in weekly skin sales."
    else:
        await message.channel.send(
            f"Use **'{utilities.Constants.COMMAND_PREFIX}clear pro'** to clear your list of champions followed in "
            f"professional play, or **'{utilities.Constants.COMMAND_PREFIX}clear fav'** to clear your list of champions"
            " followed in the weekly skin sales rotation.")
        return
    # Clear user's list of favorites/followed
    for champ_name in Constants.CHAMP_DICT.values():
        champion = Query()
        query_results = db.get(champion['champion_name'] == champ_name)
        if query_results is not None:
            user_ids_list = query_results['user_ids']
            if user_id in user_ids_list:
                user_ids_list.remove(user_id)
                db.update({'user_ids': user_ids_list}, champion['champion_name'] == champ_name)
    await message.channel.send(success_message)
    return
