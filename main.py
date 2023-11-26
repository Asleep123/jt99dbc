import discord
import ast
import os
import time
import datetime
import traceback
import asyncio
import aiohttp
import random
import logging
import html
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.interactions import Interaction
from dotenv import load_dotenv
from typing import Optional, Literal, Union

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


root = logging.getLogger() # logging
root.setLevel(logging.DEBUG)

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

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
    print(f"{Color.GREEN}[SUCCESS]{Color.CYAN} Logged in as {Color.BOLD}{bot.user.name}{Color.RESET}{Color.CYAN} at ID {Color.BOLD}{bot.user.id}{Color.RESET}{Color.CYAN}.\nIn {Color.BOLD}{gc}{Color.RESET}{Color.CYAN} guilds\nwith {Color.BOLD}{mc}{Color.RESET}{Color.CYAN} total members.\nShard count is {Color.BOLD}{bot.shard_count}{Color.RESET}{Color.CYAN}.\nInvite: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=18432&scope=bot%20applications.commands{Color.RESET}")
    # bot is likely to get disconnected from gateway if it tries to make calls the second its connected
    uptime_ping.start()
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

@tasks.loop(seconds=60)
async def uptime_ping():
    async with aiohttp.ClientSession() as s: # call to uptime server to tell them bot is still alive
        p = round(bot.latency * 1000)
        async with s.get(f"http://localhost:3001/api/push/NDOQGRLebP?status=up&msg=OK&ping={p}") as resp:
            return


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
        result = (await eval(f"_eval_expr_()", env))
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
    "Get the ping/uptime of the bot."
    # get bot ping/uptime
    p = round(bot.latency * 1000)
    ut = str(datetime.timedelta(seconds=int(round(time.time()-utime))))
    e = discord.Embed(title="Ping", description=f"Pong!\nLatency is {p}ms.\nUptime is {ut} (H:M:S).")
    await ctx.response.send_message(embed=e)


@tree.command(name="about", description="What is Infinity?")
async def about(ctx: discord.Interaction):
    "Tells you about Infinity and it's functions."
    # self explanatory, tells you about the bot
    desc = """
    Infinity is a Discord bot meant to help you with general activities and make your server a blast! We have commands ranging from games, to reminders, and a lot of other stuff in between! Want to invite me? Run `/invite` to get my invite link. You can also check out some of our commands by running `/help`!
    Fun Fact: This was made for the JT-99 Discord Bot Competition.
    Have fun!
    """
    e = discord.Embed(title="About Infinity", description=desc)
    e.set_author(name=bot.user.name, icon_url=bot.user.avatar)
    await ctx.response.send_message(embed=e)

@tree.command(name="invite", description="Get a link to invite the bot")
async def about(ctx: discord.Interaction):
    "Get a link to invite the bot"
    desc = """
    https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=18432&scope=bot%20applications.commands
    """
    e = discord.Embed(title="Invite Infinity", description=desc)
    e.set_author(name=bot.user.name, icon_url=bot.user.avatar)
    await ctx.response.send_message(embed=e)

@tree.command(name="help", description="List commands and how to use them.")
async def help(ctx: discord.Interaction):
    "Display this list."
    # list all commands
    cmds = ""
    for cmd in bot.tree.get_commands(type=discord.AppCommandType.chat_input):
        func = cmd.callback # get function associated with command
        doc = func.__doc__ # get docstring
        name = f"/{cmd.name}"
        if cmd.parameters:
            for param in cmd.parameters: # sort through params if any and display them
                if param.required:
                    name = name + f" <{param.display_name}>"
                else:
                    name = name + f" [{param.display_name}]"
        cmds = cmds + f"{name} - {doc}\n"
    desc = f"Here are all the commands you can use. Parameters wrapped in [] indicate optional, and parameters wrapped in <> indicate required:\n\n```{cmds}```"
    e = discord.Embed(title="Help", description=desc)
    await ctx.response.send_message(embed=e)

# let the fun begin
@tree.command(name="meme", description="Get a random meme from r/memes.")
@app_commands.checks.cooldown(1, 5)
async def memegen(ctx: discord.Interaction):
    "Get a random meme from r/memes on Reddit."
    await ctx.response.defer(thinking=True)
    async with aiohttp.ClientSession() as s:
        async with s.get("https://reddit.com/r/memes/hot.json") as resp: # start http session and get most recent posts from r/memes
            if not resp.ok: # status lower than 400 (0-399)
                e = discord.Embed(title="Failed to get image", description="Could not get image from Reddit API.")
                await ctx.followup.send(embed=e)
                return
            num = random.randint(0, 24)
            json = await resp.json()
            img = json["data"]["children"][num]["data"]["url"] # pick random number from posts array, then get the image URL from said array index (post)
            e = discord.Embed(title="Meme")
            e.set_image(url=img)
            await ctx.followup.send(embed=e)

            
@tree.command(name="8ball", description="Ask the magic 8 ball.")
async def eightball(ctx: discord.Interaction, question: str):
    "Ask the Magic 8 Ball a question."
    responses = [
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes, definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful."
  ]
    ans = random.choice(responses) # pick random from responses and reply with it
    e = discord.Embed(title="Magic 8 Ball", description=f"***{question}***\n\nThe sources speak from above.\n**{ans}**")
    await ctx.response.send_message(embed=e)

@tree.command(name="joke", description="Get a random joke.")
@app_commands.checks.cooldown(1, 3)
async def joke(ctx: discord.Interaction):
    "Get a random joke."
    await ctx.response.defer(thinking=True)
    async with aiohttp.ClientSession() as s:
        headers = {
            "Accept": "text/plain"
        }
        async with s.get("https://icanhazdadjoke.com/", headers=headers) as resp: # start http session and get joke as plaintext from api
            if not resp.ok: # status higher than 399
                e = discord.Embed(title="Failed to get joke", description="Could not get joke from API.")
                await ctx.followup.send(embed=e)
                return
            joke = await resp.text()
            e = discord.Embed(title="Joke", description=joke)
            await ctx.followup.send(embed=e)
    
class TriviaBtn(discord.ui.View):

    def __init__(self, answer: str, user: Union[discord.Member, discord.User], ans: list, timeout: float=None):
        self.ans1 = ans[0]
        self.ans2 = ans[1]
        self.ans3 = ans[2]
        self.ans4 = ans[3]
        self.ans = answer
        self.user = user
        super().__init__()
        

    @discord.ui.button(label="A", style=discord.ButtonStyle.green)
    async def ans1btn(self, ctx: discord.Interaction, btn: discord.Button):
        if self.ans1 != self.ans: # check if correct
            e = discord.Embed(title="Incorrect Answer", description=f"{ctx.user.mention} got this question incorrect.", colour=discord.Colour.brand_red())
            await ctx.response.edit_message(embed=e, view=None)
            self.stop()
        else:
            e = discord.Embed(title="Correct Answer", description=f"{ctx.user.mention} got this question correct!", colour=discord.Colour.brand_green())
            await ctx.response.edit_message(embed=e, view=None)
            self.stop()

    @discord.ui.button(label="B", style=discord.ButtonStyle.green)
    async def ans2btn(self, ctx: discord.Interaction, btn: discord.Button):
        if self.ans2 != self.ans:
            e = discord.Embed(title="Incorrect Answer", description=f"{ctx.user.mention} got this question incorrect.", colour=discord.Colour.brand_red())
            await ctx.response.edit_message(embed=e, view=None)
            self.stop()
        else:
            e = discord.Embed(title="Correct Answer", description=f"{ctx.user.mention} got this question correct!", colour=discord.Colour.brand_green())
            await ctx.response.edit_message(embed=e, view=None)
            self.stop()
    
    @discord.ui.button(label="C", style=discord.ButtonStyle.green)
    async def ans3btn(self, ctx: discord.Interaction, btn: discord.Button):
        if self.ans3 != self.ans:
            e = discord.Embed(title="Incorrect Answer", description=f"{ctx.user.mention} got this question incorrect.", colour=discord.Colour.brand_red())
            await ctx.edit_original_response(embed=e, view=None)
            self.stop()
        else:
            e = discord.Embed(title="Correct Answer", description=f"{ctx.user.mention} got this question correct!", colour=discord.Colour.brand_green())
            await ctx.response.edit_message(embed=e, view=None)
            self.stop()

    @discord.ui.button(label="D", style=discord.ButtonStyle.green)
    async def ans4btn(self, ctx: discord.Interaction, btn: discord.Button):
        if self.ans4 != self.ans:
            e = discord.Embed(title="Incorrect Answer", description=f"{ctx.user.mention} got this question incorrect.", colour=discord.Colour.brand_red())
            await ctx.response.edit_message(embed=e, view=None)
            self.stop()
        else:
            e = discord.Embed(title="Correct Answer", description=f"{ctx.user.mention} got this question correct!", colour=discord.Colour.brand_green())
            await ctx.response.edit_message(embed=e, view=None)
            self.stop()

    async def interaction_check(self, ctx: discord.Interaction):
        if ctx.user.id != self.user.id: # check if user is the user that ran the command
            ctx.response.send_message("You do not have permission to interact with this.", ephemeral=True)
            return False
        return True

@tree.command(name="trivia", description="Get a random trivia question.")
@app_commands.checks.cooldown(1, 3)
async def trivia(ctx: discord.Interaction, difficulty: Literal["Easy", "Medium", "Hard"]):
    "Get a trivia question to answer."
    difficulty = difficulty.lower()
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&type=multiple") as resp: # start http session and make request to get question
            json = await resp.json()
    question = json["results"][0]["question"]
    cans = json["results"][0]["correct_answer"]
    answers: list = json["results"][0]["incorrect_answers"]
    answers.append(cans) # list of all answers
    random.shuffle(answers) # shuffle so the last one isnt always correct
    abcdlist = f"```A. {answers[0]}\nB. {answers[1]}\nC. {answers[2]}\nD. {answers[3]}```"
    e = discord.Embed(title="Trivia", description=f"{question}\n>>> {abcdlist}")
    view = TriviaBtn(answer=cans, user=ctx.user, ans=answers) # create view obj
    await ctx.response.send_message(embed=e, view=view)

@tree.command(name="coinflip", description="Flip a coin for a 50/50 chance to win!")
async def coinflip(ctx: discord.Interaction):
    responses = [
        "heads",
        "tails"
    ]
    result = random.choice(responses) # choose between 2
    e = discord.Embed(title="Coin Flip", description=f"And the result is...\n**{result}**!")
    await ctx.response.send_message(embed=e)

@tree.command(name="dice", description="Roll a dice!")
async def dice(ctx: discord.Interaction):
    num = random.randint(1, 6)
    e = discord.Embed(title="Dice Roll", description=f"The dice landed on...\n**{num}**!")
    await ctx.response.send_message(embed=e)

@tree.command(name="affirmation", description="Get a random affirmation.")
@app_commands.checks.cooldown(1, 3)
async def affirmation(ctx: discord.Interaction):
    await ctx.response.defer(thinking=True)
    async with aiohttp.ClientSession() as s:
        async with s.get("https://affirmations.dev") as resp:
            json = await resp.json()
            aff = json["affirmation"]
    e = discord.Embed(title="Affirmation", description=aff)
    await ctx.followup.send(embed=e)

@tree.command(name="roast", description="Roast someone!")
async def roast(ctx: discord.Interaction, user: discord.Member):
    await ctx.response.defer(thinking=True)
    async with aiohttp.ClientSession() as s:
        async with s.get("https://evilinsult.com/generate_insult.php?lang=en&type=json") as resp:
            json = await resp.json()
            roast = json["insult"]

    e = discord.Embed(title="Roast", description=roast)
    await ctx.followup.send(user.mention, embed=e)

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
        # ignore so people just mentioning the bot dont get an error
        return
    print(f"{Color.RED}[ERROR] {Color.RED}{error}\n[TRACEBACK]{Color.RESET}")
    traceback.print_tb(error.__traceback__)
    await ctx.send("There was an error while running this command. The error was logged and sent to developers.")
bot.on_command_error = on_command_error


bot.run(token, log_handler=None)