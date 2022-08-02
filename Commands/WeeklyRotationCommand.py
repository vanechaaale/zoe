import discord

from utilities import get_zoe_error_message, get_free_champion_ids, Constants


async def rotation(message):
    champ_dict = Constants.CHAMP_DICT
    free_champ_ids = get_free_champion_ids()
    try:
        free_rotation = []
        for champion_id in free_champ_ids['freeChampionIds']:
            free_rotation.append(champ_dict[str(champion_id)])
        free_rotation.sort()
        embed = discord.Embed(color=0xe8bffb)
        embed.add_field(
            name="Weekly Free Champion Rotation:",
            value=f"{' | '.join(free_rotation[0:4])}\n{' | '.join(free_rotation[4:8])}\n\n"
                  f"{' | '.join(free_rotation[8:12])}\n{' | '.join(free_rotation[12:16])}",
            inline=False
        )
        # Send collage of all champion splash arts
        image_file = discord.File('Data/free_rotation_jpgs/free_rotation_full.jpg', filename='free_rotation_full.jpg')
        embed.set_image(url='attachment://free_rotation_full.jpg')
        embed.set_footer(text=f"Free champion rotation refreshes every Tuesday")
        await message.channel.send(embed=embed, file=image_file)
    except (Exception,):
        await message.channel.send(get_zoe_error_message())
