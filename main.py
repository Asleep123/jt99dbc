import discord
import ast
import os
import time
import datetime
import traceback
import asyncio
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

class Color:
    # Text
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    # Formatting
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    CONCEALED = "\033[8m"

intents = discord.Intents.all()
bot = commands.AutoShardedBot(intents=intents, command_prefix=commands.when_mentioned_or("infinity$"), help_command=None)
tree = bot.tree
token = os.getenv("DSC_TOKEN")

@bot.event
async def on_ready():
    global utime
    utime = time.time()
    gs = bot.guilds
    gc = len(gs)
    mc = 0
    for g in gs:
        mc = mc + len(g.members)

    print(f"{Color.GREEN}[SUCCESS]{Color.CYAN} Logged in as {Color.BOLD}{bot.user.name}{Color.RESET}{Color.CYAN} at ID {Color.BOLD}{bot.user.id}{Color.RESET}{Color.CYAN}.\nIn {Color.BOLD}{gc}{Color.RESET}{Color.CYAN} guilds\nwith {Color.BOLD}{mc}{Color.RESET}{Color.CYAN} total members.\nShard count is {Color.BOLD}{bot.shard_count}{Color.RESET}{Color.CYAN}.\nInvite: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands{Color.RESET}")
    # bot is likely to get disconnected from gateway if it tries to make calls the second its connected
    await asyncio.sleep(2)
    act_update.start()

@tasks.loop(seconds=3600)
async def act_update():
    # calculate bot stats (guild count, member count) and update status every hour
    gs = bot.guilds
    gc = len(gs)
    mc = 0
    for g in gs:
        mc = mc + len(g.members)
    act = discord.Activity(type=discord.ActivityType.watching, name=f"{gc} guilds and {mc} members")
    await bot.change_presence(activity=act)


def insert_returns(body):
    # fix code because discord formats it weird
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


@bot.command(name="eval")
@commands.is_owner()
async def evalcmd(ctx: commands.Context, *, cmd: str):
    # run code
    cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
    body = f"async def _eval_expr_():\n{cmd}"
    parsed = ast.parse(body)
    body = parsed.body[0].body
    insert_returns(body)
    env = {
        'bot': bot,
        'discord': discord,
        'ctx': ctx,
        'os': os,
        'tree': tree,
        '__import__': __import__
    }
    exec(compile(parsed, filename="<ast>", mode="exec"), env)
    try:
        result = (await eval(f"{fn_name}()", env))
    except Exception as e:
        # in case of error, set result to exception
        result = f"Exception:\n{e}"
    result = f"```\n{result}\n```"
    await ctx.channel.send(result)

@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx: commands.Context):
    # sync global commands to discord api
    print(f"{Color.CYAN}[INFO] {Color.RESET}Syncing Tree")
    await ctx.send("Syncing...")
    await tree.sync()
    await ctx.send("Synced!")
    print(f"{Color.GREEN}[SUCCESS] {Color.RESET}Tree Synced")

@bot.command(name="syncguild")
@commands.is_owner()
async def sync(ctx: commands.Context):
    # sync guild specific commands to discord api
    print(f"{Color.CYAN}[INFO] {Color.RESET}Syncing Guild {ctx.guild.id}")
    await ctx.send(f"Syncing guild {ctx.guild.id}...")
    await tree.sync(guild=discord.Object(id=ctx.guild.id))
    await ctx.send("Synced!")
    print(f"{Color.GREEN}[SUCCESS] {Color.RESET}Tree Synced")


@tree.command(name="ping", description="Get the ping of the bot.")
async def ping(ctx: discord.Interaction):
    # get bot ping
    p = round(bot.latency * 1000)
    ut = str(datetime.timedelta(seconds=int(round(time.time()-utime))))
    e = discord.Embed(title="Ping", description=f"Pong!\nLatency is {p}ms.\nUptime is {ut} (H:M:S).")
    await ctx.response.send_message(embed=e)

@tree.command(name="about", description="What is Infinity?")
async def about(ctx: discord.Interaction):
    # self explanatory, tells you about the bot
    desc = """
    Infinity is a Discord bot mean't to help you with general activities and make your server a blast! We have commands ranging from games, to reminders, and a lot of other stuff in between! Want to invite me? Run `/invite` to get my invite link. You can also check out some of our commands by running `/help`!
    Fun Fact: This was made for the JT-99 Discord Bot Competition.
    Have fun!
    """
    e = discord.Embed(title="About Infinity", description=desc)
    e.set_author(name=bot.user.name, icon_url=bot.user.avatar)
    await ctx.response.send_message(embed=e)


async def on_tree_error(ctx, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await ctx.response.send_message(f"This command is on cooldown! Retry in {error.retry_after:.2f} second(s).")
        return
    elif isinstance(error, app_commands.MissingPermissions):
        await ctx.response.send_message("You do not have permission to execute this command.")
        return
    elif isinstance(error, app_commands.CheckFailure):
        await ctx.response.send_message("You do not have permission to execute this command.")
        return
    # handle other errors not caused by user error
    print(f"{Color.RED}[ERROR] {Color.RED}{error}\n[TRACEBACK]{Color.RESET}")
    traceback.print_tb(error.__traceback__)
    try:
        await ctx.response.send_message("There was an error while running this command. The error was logged and sent to developers.", ephemeral=True)
    except:
        # if interaction was already sent, edit interaction
        await ctx.edit_original_response(content="There was an error while running this command. The error was logged and sent to developers.")
tree.on_error = on_tree_error

async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    # same thing, but for prefix commands, which are used for owner only stuff like eval
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to execute this command.")
        return
    elif isinstance(error, commands.NotOwner):
        await ctx.send("You do not have permission to execute this command.")
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing a required argument.")
        return
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
        return
    print(f"{Color.RED}[ERROR] {Color.RED}{error}\n[TRACEBACK]{Color.RESET}")
    traceback.print_tb(error.__traceback__)
    await ctx.send("There was an error while running this command. The error was logged and sent to developers.")
bot.on_command_error = on_command_error

bot.run(token)