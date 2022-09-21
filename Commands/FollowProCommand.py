import utilities
from utilities import Constants


async def follow_pro(message, *champion_name):
    """Command to follow a champion's presence in pro play"""
    # If no args were given
    if not champion_name:
        await message.channel.send(
            "use '***~follow pro <champion>, <champion>, ...***' to be notified when this champion is played in a "
            "professional game!")
        return
    else:
        await utilities.add_remove_favorite(
            message=message,
            champion_name=champion_name,
            db=Constants.DB,
            user_id=message.author.id,
            success_message="following live professional matches for:"
        )
