from datetime import datetime, time, timedelta
import asyncio
import json
import aiohttp

import discord
from discord import channel
from discord import mentions
from discord.ext import commands, tasks
from discord import app_commands

bot = commands.Bot(command_prefix='haj ', intents=discord.Intents.all())

QOTD_CHANNEL_ID = 1433040386359824494

@bot.event
async def on_ready():
    # load all modules
    await bot.load_extension("QOTD")
    await bot.load_extension("Images")
    await bot.load_extension("Trivia")

    # sync tree commands
    synced = await bot.tree.sync()

    print(f"Logged in as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Error: {str(error)}", ephemeral=True)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command(name="reload")
async def reload_module(ctx: commands.Context, name: str):
    if not await bot.is_owner(ctx.author):
        await ctx.send(f"❌ Only bot owner can reload modules", ephemeral=True)
        return

    try:
        await bot.reload_extension(name)
        await ctx.send(f"✅ Reloaded `{name}` successfully", ephemeral=True)
        await bot.tree.sync()

    except commands.ExtensionNotLoaded:
        await ctx.send(f"⚠ Cog `{name}` is not loaded", ephemeral=True)
    except commands.ExtensionNotFound:
        await ctx.send(f"⚠ Cog `{name}` not found", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Error reloading `{name}`:\n```{e}```", ephemeral=True)

with open("config.json") as file:
    config = json.load(file)

bot.run(config["token"])
