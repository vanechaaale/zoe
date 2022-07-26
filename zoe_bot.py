import asyncio
import os

import BaseMessageResponse
from Commands import GuideCommand, LiveCommand, SaleCommand, FollowProCommand, FollowSkinCommand, WeeklyRotationCommand
from Data import gifs
from utilities import *
from discord.ext import commands
# runs the skin sales webscraper and automatically updates all the skins on sale in the league shop
# import skin_sales_spider

help_command = commands.DefaultHelpCommand(no_category='List of Zoe Bot Commands')
intents = discord.Intents.default()
intents.members = True


class BaseCommand(commands.Bot):
    """The parent of all Zoe Bot Commands.
    If I make the files in Commands/ extensions of this BaseCommand class, will it make multiple instances of the bot
    to run the same command a bunch of times? Will it break everything? I have no idea
    """
    def __init__(self):
        super().__init__(
            command_prefix='~',
            help_command=help_command,
            description="I'm Zoe, what's your name?",
            intents=intents
        )
        self.champ_dict = Constants.get_champ_dict()
        self.champ_skins_set = Constants.get_champion_skins_dict()
        self.cache = dict()
        self.bot = commands.Bot(
            command_prefix='~',
            help_command=help_command,
            description="I'm Zoe, what's your name?",
            intents=intents)
        self.db = Constants.DB
        self.favorite_skin_db = Constants.SKIN_DB
        self.free_champ_ids = Constants.FREE_CHAMPION_IDS

        @self.event
        async def on_ready():
            cache_clear_hours = 2
            check_tracked_mins = 3 * 60
            activity = discord.Game(name="Do something fun! The world might be ending... Or not!")
            await bot.change_presence(status=discord.Status.online, activity=activity)
            await check_tracked_skins(self)
            while True:
                # Champions being followed in pro play are tracked in this loop
                await check_tracked_champions(self)
                await clear_cache(self.cache, cache_clear_hours)
                await asyncio.sleep(check_tracked_mins)

        @self.command(hidden=True)
        @commands.is_owner()
        async def shutdown(c):
            await c.channel.send("Logging out...")
            await bot.close()

        @self.command(hidden=True)
        @commands.is_owner()
        async def update_skin_sales(channel, *args):
            """
            Command to manually run the skin sales webscraper AND notify users about their liked champs
            """
            args = ' '.join(args)
            if args.lower() == 'spider':
                os.system('python skin_sales_spider.py')
                await channel.send("Successfully updated this week's champion skin sales.")
            await check_tracked_skins(self)
            await channel.send("Successfully notified users about their favorite champions' skin sales.")

        @self.event
        async def on_guild_join(guild):
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    quote = random.choice(Quotes.Zoe_join_server_message)
                    await channel.send(f'"*{quote}*"')
                break

        @self.event
        async def on_command_error(channel, error):
            if isinstance(error, commands.CommandNotFound):
                return
            else:
                await channel.send(error)

        @self.listen()
        async def on_message(message):
            if message.author == bot.user:
                return
            for cmd in BaseMessageResponse.RESPONSES:
                if cmd.invoke(message) and not is_command(message):
                    await cmd.execute(message)
            if message.is_system() and message.type == discord.MessageType.new_member:
                quote = random.choice(Quotes.Greet)
                await message.channel.send(f'"*{quote}*"')

        @self.command(brief="Show Zoe guides", description="List of Zoe guides and Zoe players!")
        async def guide(channel):
            await GuideCommand.guide(channel)

        @self.command(brief="Zoe gifs.", description="Beautiful Zoe gifs.")
        async def gif(channel):
            await channel.send(random.choice(gifs.gifs))

        @self.command(brief="Show live professional games of a champion",
                      description="Given a champion's name, shows a list of all live professional games where the "
                                  "champion is being played, or use '~live all' to see a list of all champions in "
                                  "live games")
        async def live(channel, *champion_name):
            await LiveCommand.live(channel, *champion_name)

        @self.command(hidden=True,
                      brief="Show Zoe matchup tips! (WIP)",
                      description="View Zoe's matchup statistics against a champion")
        async def matchup(channel, champion):
            """WORK IN PROGRESS"""
            champion.lower()
            await channel.send(get_zoe_error_message())

        @matchup.error
        async def matchup_error(ctx, error):
            if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
                await ctx.send(
                    "use '~matchup <champion>' to search for Zoe's matchup statistics against a champion!")

        @self.command(hidden=True,
                      brief="Paddle Star Damage Calculator (WIP)",
                      description="Zoe Q damage calculator based on items, runes, and masteries")
        async def psdc(channel):
            """WORK IN PROGRESS"""
            await channel.send(get_zoe_error_message())

        @self.command(brief="Show the weekly free champion rotation",
                      description="Weekly free to play champion rotation for summoner level 11+ accounts")
        async def rotation(message):
            await WeeklyRotationCommand.rotation(message)

        @self.command(brief="Show champion skins on sale this week",
                      description="Show list of all champion skins on sale (which refreshes every Monday at 3 pm EST),"
                                  "or use '~sale all' to see a list of all skins on sale "
                                  "(not recommended by yours truly, because I think it's quite ugly, but it's more "
                                  "convenient I guess")
        async def sale(channel, *kwargs):
            command_args = ' '.join(kwargs)
            if channel.channel.type.name != 'private':
                if command_args.lower() == 'all':
                    await SaleCommand.sale_all(channel)
                else:
                    await SaleCommand.sale(channel, self)

        @self.command(brief="Get notified when a champion has a skin on sale",
                      description="Receive messages from Zoe Bot whenever the given champion has a skin on sale")
        async def favorite(message, *champion_name):
            await FollowSkinCommand.favorite(message, *champion_name)

        @self.command(brief="Show list of favorite champions",
                      description="Show a list of all champions that Zoe Bot will notify a Discord User for when one "
                                  "or more champs have skins on sale. Remove a champion from "
                                  "this list with the command '~favorite <champion_name>'.")
        async def favlist(message):
            await FollowSkinCommand.favlist(message)

        @self.command(brief="Follow a champion in professional play",
                      description="Receive messages from Zoe Bot whenever the given champion is being played in a "
                                  "professional game, or use the command again to stop receiving notifications from "
                                  "Zoe Bot.")
        async def follow(message, *champion_name):
            await FollowProCommand.follow(message, *champion_name)

        @self.command(brief="Show all followed champions",
                      description="Show a list of all champions that Zoe Bot will notify a Discord User for when one "
                                  "or more champs are being played in a professional game. Remove a champion from "
                                  "this list with the command '~track <champion_name>'.")
        async def following(message):
            await FollowProCommand.following(message)

        @self.command(hidden=True)
        async def test(channel):
            await SaleCommand.sale_all(channel)


bot = BaseCommand()


def main():
    # Start up the bot
    with open('Data/alpha_token') as file:
        token = file.readline()
    bot.run(token)


if __name__ == "__main__":
    main()
