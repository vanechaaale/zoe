import discord

from utilities import get_free_champion_ids, Constants


async def rotation(message):
    # Fetch f2p champ ids
    free_champ_ids = get_free_champion_ids()['freeChampionIds']
    free_rotation = [Constants.CHAMP_DICT[str(champ_id)] for champ_id in free_champ_ids]
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
