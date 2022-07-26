from utilities import get_zoe_error_message, Constants


async def rotation(message):
    champ_dict = Constants.CHAMP_DICT
    free_champ_ids = Constants.FREE_CHAMPION_IDS
    try:
        free_rotation = []
        for champion_id in free_champ_ids['freeChampionIds']:
            free_rotation.append(champ_dict[str(champion_id)])
        free_rotation.sort()
        free_rotation = ', '.join(free_rotation)
        await message.channel.send("The champions in this week's free to play rotation are: " + free_rotation)
    except (Exception,):
        await message.channel.send(get_zoe_error_message())
