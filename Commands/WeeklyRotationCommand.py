import discord

from utilities import Constants


async def rotation(message):
    embed = discord.Embed(color=0xe8bffb)
    embed.add_field(
        name="Weekly Free Champion Rotation:",
        value=f"{' | '.join(Constants.FREE_CHAMPS[0:4])}\n{' | '.join(Constants.FREE_CHAMPS[4:8])}\n\n"
              f"{' | '.join(Constants.FREE_CHAMPS[8:12])}\n{' | '.join(Constants.FREE_CHAMPS[12:16])}",
        inline=False
    )
    # Send collage of all champion splash arts
    image_file = discord.File('Data/free_rotation_jpgs/free_rotation_full.jpg', filename='free_rotation_full.jpg')
    embed.set_image(url='attachment://free_rotation_full.jpg')
    embed.set_footer(text=f"Free champion rotation refreshes every Tuesday")
    await message.channel.send(embed=embed, file=image_file)
