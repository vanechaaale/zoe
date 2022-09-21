import utilities
from utilities import Constants


async def follow_skin(message, *champion_name):
    # If no args were given
    if not champion_name:
        await message.channel.send(
            "use '~favorite <champion>, <champion>, **...**' to be notified when their skins go on sale!")
        return
    else:
        await utilities.add_remove_favorite(
            message=message,
            champion_name=champion_name,
            db=Constants.SKIN_DB,
            user_id=message.author.id,
            success_message="following weekly skin sales for:"
        )
