from constants import get_zoe_error_message


async def rotation(c, base_command):
    champ_dict = base_command.champ_dict
    free_champ_ids = base_command.free_champ_ids
    try:
        free_rotation = []
        for champion_id in free_champ_ids['freeChampionIds']:
            free_rotation.append(champ_dict[str(champion_id)])
        free_rotation.sort()
        free_rotation = ', '.join(free_rotation)
        await c.channel.send("The champions in this week's free to play rotation are: " + free_rotation)
    except (Exception,):
        await c.channel.send(get_zoe_error_message())
