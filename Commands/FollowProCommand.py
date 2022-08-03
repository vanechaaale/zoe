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


async def following(message):
    """
    Command to show the user the list of champions they follow in pro play, and the list of champions they
    track weekly skin sales for.
    """
    user_id = message.author.id
    # Following for pro play
    pro_play_following = utilities.get_following_list(
        user_id=user_id,
        db=Constants.DB,
        success_message="following live professional games for:"
    )
    skin_following = utilities.get_following_list(
        user_id=user_id,
        db=Constants.SKIN_DB,
        success_message="following skin sales for:",
        second=True
    )
    await message.channel.send(f"{pro_play_following}, and {skin_following}")
