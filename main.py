import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
@bot.event
async def on_ready():
    print(f'Success! Bot has connected as {bot.user.name}')
    print("Ready for business!")
@bot.command()
async def ping(ctx):
    """A simple test command to check the answering time"""
    latency =round(bot.latency * 1000)
    await ctx.send(f'Bam! I answer in {latency} ms')
if __name__ =='__main__':
    bot.run(TOKEN)