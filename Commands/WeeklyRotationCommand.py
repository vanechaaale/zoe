import discord

from utilities import get_free_champion_ids, Constants


async def rotation(message):
    champ_dict = Constants.CHAMP_DICT
    free_champ_ids = get_free_champion_ids()['freeChampionIds']
    free_rotation = []
    for champion_id in free_champ_ids['freeChampionIds']:
        free_rotation.append(champ_dict[str(champion_id)])
    free_rotation.sort()
    embed = discord.Embed(color=0xe8bffb)
    # For 2 x 8
    # mid = int(len(free_rotation)/2)
    # free_list1 = free_rotation[0:mid]
    # free_list2 = free_rotation[mid:len(free_rotation)]
    # value = ""
    # for i in range(mid):
    #     current_line = f"{free_list1[i]} | {free_list2[i]}\n"
    #     value += current_line
    # embed.add_field(
    #     name="Weekly Free Champion Rotation:",
    #     value=value,
    #     inline=False
    # )
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
