import discord
from discord.ext import commands
import os

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot online!")

@bot.command()
async def loja(ctx):
    await ctx.send("🛒 Loja funcionando!")

bot.run(os.getenv("TOKEN"))
