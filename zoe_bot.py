import asyncio
import datetime as dt
import os
from datetime import datetime

from dotenv import load_dotenv
from discord.ext import commands, tasks
import BaseMessageResponse
from Commands import GuideCommand, LiveCommand, SaleCommand, FollowProCommand, FollowSkinCommand, \
    WeeklyRotationCommand, ClearCommand, FollowingListCommand
from Data import gifs
from utilities import *

# runs the skin sales webscraper and automatically updates all the skins on sale in the league shop
# import skin_sales_spider

help_command = commands.DefaultHelpCommand(no_category="List of Zoe Bot Commands, use prefix '~'")
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
        # Remember to re-init champ_dict at the start of every patch/after a new champion release
        # Dict of champion_id : champion_name
        self.champ_dict = Constants.get_champ_dict()
        # Remember to re-init champion_skins_dict() after new skin releases
        # Dict of Champion: {Skins}
        self.champ_skins_dict = Constants.get_champion_skins_dict()
        self.free_champ_rotation = Constants.get_free_champ_rotation()
        self.cache = dict()
        self.bot = commands.Bot(
            command_prefix='~',
            help_command=help_command,
            description="I'm Zoe, what's your name?",
            intents=intents)
        self.db = Constants.DB
        self.favorite_skin_db = Constants.SKIN_DB

        @self.event
        async def on_ready():
            activity = discord.Game(name="Do something fun! The world might be ending... Or not!")
            await bot.change_presence(status=discord.Status.online, activity=activity)
            update_weekly_skin_sales.start()
            update_pro_play.start()
            update_champ_data_skins_info.start()
            update_free_rotation.start()

        @tasks.loop(hours=1)
        async def update_free_rotation():
            """
            Task loop to update the displayed images of champions that are in the weekly free rotation, every week
            on Tuesdays at 12 PM EST
            """
            current_hour = int(dt.datetime.utcnow().strftime("%H"))
            # Check that it is Tuesday at 12 pm EST, 16 UTC and update free rotation image and free rotation list
            if datetime.datetime.today().weekday() == 1 and current_hour == 16:
                update_free_rotation_images()
                self.free_champ_rotation = Constants.get_free_champ_rotation()

        @tasks.loop(hours=1)
        async def update_weekly_skin_sales():
            current_hour = int(dt.datetime.utcnow().strftime("%H"))
            # Check that it is Tuesday at 12 pm EST, 16 UTC
            if datetime.datetime.today().weekday() == 1 and current_hour == 16:
                # Run web scraper
                os.system('python skin_sales_spider.py')
                # Notify users of their favorite champ skins on sale
                await check_tracked_skins(self)

        @tasks.loop(minutes=3)
        # Check every 3 minutes for pro play
        async def update_pro_play():
            cache_clear_hours = 2
            check_tracked_mins = 3 * 60
            # Champions being followed in pro play are tracked here
            await check_tracked_champions(self)
            await clear_cache(self.cache, cache_clear_hours)
            await asyncio.sleep(check_tracked_mins)

        @tasks.loop(hours=1)
        # Update champion data and champion skins dictionaries every day at 12 PM EST
        async def update_champ_data_skins_info():
            current_hour = int(dt.datetime.utcnow().strftime("%H"))
            if current_hour == 16:
                self.champ_skins_dict = init_champion_skins_dict()
                self.champ_dict = Constants.get_champ_dict(refresh_dict=True)

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
                server_name = str(message.guild)
                new_member = message.author.mention
                quote = random.choice(Quotes.Greet)
                await message.channel.send(f'Welcome to {server_name}, {new_member}!\n"*{quote}*"')

        @self.command(brief="Clear list of followed champions",
                      description="Clear your list of champions followed in professional play with '~clear pro', or "
                                  "clear your list of champions followed for weekly skin sales with '~clear fav'.")
        async def clear(channel, *args):
            await ClearCommand.clear(channel, *args)

        @self.command(brief="Follow champions in pro play, or watch for their skin sales",
                      description="Receive messages from Zoe Bot whenever a followed champion is played in a live "
                                  "professional match or when a champion's skin is on sale in the weekly shop "
                                  "rotation. Use the command again to stop receiving these "
                                  "notifications from Zoe Bot.")
        async def follow(message, *champion_name):
            cmd_name = follow.name
            error_message = f"Use **'~{cmd_name} pro <champion>, <champion> ...'** to follow champions in" \
                            f" professional play, or use **'~{cmd_name} skin <champion>, <champion> ...'** to follow " \
                            f"weekly skin sales for champions!"
            if not champion_name:
                await message.channel.send(error_message)
                return
            else:
                mode = champion_name[0].lower()
                champs_str = ' '.join(champion_name[1:])
                if mode == 'pro':
                    await FollowProCommand.follow_pro(message, champs_str) if champs_str else \
                        await message.channel.send(error_message)
                elif mode == 'skin':
                    await FollowSkinCommand.follow_skin(message, champs_str) if champs_str else \
                        await message.channel.send(error_message)
                else:
                    await message.channel.send(error_message)

        @self.command(brief="Show list of favorite champions",
                      description="Show a list of all champions that Zoe Bot will notify a Discord User for when one "
                                  "or more champions are being played in a professional game, or if a champion has a "
                                  "skin on sale this week. Remove a champion from this list with the command "
                                  "'~follow pro <champion>, <champion> ...' for professional play, or use "
                                  "'~follow skin <champion>, <champion> ...' for champion skins.")
        async def following(message):
            await FollowingListCommand.following(message)

        @self.command(brief="Zoe gifs.", description="Beautiful Zoe gifs.")
        async def gif(channel):
            await channel.send(random.choice(gifs.gifs))

        @self.command(brief="Show Zoe guides", description="List of Zoe guides and Zoe players!")
        async def guide(channel):
            await GuideCommand.guide(channel)

        @self.command(brief="Show live professional games of a champion",
                      description="Shows a list of all live professional games where the "
                                  "champion is being played, or use '~live all' to see a list of all champions in "
                                  "live games.")
        async def live(channel, *champion_name):
            await LiveCommand.live(channel, *champion_name)

        @self.command(hidden=True)
        @commands.is_owner()
        async def man_update_champ_data_skins_info():
            self.champ_skins_dict = init_champion_skins_dict()
            self.champ_dict = Constants.get_champ_dict(refresh_dict=True)

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

        @self.command(hidden=True)
        @commands.is_owner()
        async def shutdown(c):
            await c.channel.send("Logging out...")
            await self.bot.close()

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


bot = BaseCommand()

load_dotenv()
token = os.getenv('ALPHA_TOKEN')
bot.run(token)
