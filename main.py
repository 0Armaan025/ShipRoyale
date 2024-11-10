import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import os

load_dotenv()

class MyBot(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as: {self.user}')

bot = MyBot(command_prefix='$', intents=discord.Intents.all())

@bot.command()
async def hello(ctx):

    greetings_list = ["Hello!", "Howdy!", "How is it going? :D", "Hi there!", "Hey!", "hola", "Namaste"]

    random_no = random.randint(0, len(greetings_list)-1)

    await ctx.send(greetings_list[random_no])

token = os.getenv('DISCORD_TOKEN')
bot.run('MTMwNTA4MzI5NzY2MzAyOTI5OQ.G_tBK5.DLWbHzXerlR8p2tBefCvZr5_ZY11cffc2BCa8M')
