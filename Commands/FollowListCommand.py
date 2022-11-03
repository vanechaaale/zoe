import utilities
from utilities import Constants


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
        success_message="following live professional games for:",
        message=message
    )
    skin_following = utilities.get_following_list(
        user_id=user_id,
        db=Constants.SKIN_DB,
        success_message="following skin sales for:",
        message=message,
        second=True
    )
    await message.channel.send(f"{pro_play_following}, and {skin_following}")
