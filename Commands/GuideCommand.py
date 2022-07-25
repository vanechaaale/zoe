import discord


async def guide(channel):
    detention = discord.Embed(
        color=0xffb6c1,
    )
    detention.add_field(name="Detention", value="NA Challenger Mid Laner", inline=False)
    detention.set_thumbnail(
        url='https://pbs.twimg.com/profile_images/1465745862940897281/Q_QU3wNS_400x400.png')
    detention.add_field(name="Youtube Guide", value='https://www.youtube.com/watch?v=YW37o9TVTho')
    # vicksy
    vicksy = discord.Embed(
        color=0xffb6c1)
    vicksy.add_field(name="Vicksy", value="EUW Master Mid Laner", inline=False)
    vicksy.add_field(
        name="Mobafire Guide",
        value="https://www.mobafire.com/league-of-legends/build/vicksys-updated-master-zoe-guide-for-season-12"
              "-524904",
        inline=False)
    vicksy.set_thumbnail(
        url="https://static-cdn.jtvnw.net/jtv_user_pictures/37e7e61e-369f-4ba6-8fd6-106f860eca82-profile_image"
            "-70x70.png")
    # pekin woof
    pekin = discord.Embed(color=0xffb6c1, url="https://www.youtube.com/user/PekinGaming")
    pekin.add_field(
        name="Pekin Woof",
        value="Ex-Pro Player, NA Challenger Mid Laner",
        inline=False)
    pekin.add_field(
        name="Youtube Channel", value="https://www.youtube.com/user/PekinGaming")
    pekin.set_thumbnail(
        url="https://yt3.ggpht.com/ytc/AKedOLTPLJMSw3i8BAqEGeZjEbYlMPlcYwF8Ted417Omew=s88-c-k-c0x00ffffff-no-rj")
    await channel.send(
        "Here are some guides to the Aspect of Twilight and some streamers who play her!\n\n")
    await channel.send(embed=detention)
    await channel.send(embed=vicksy)
    await channel.send(embed=pekin)
