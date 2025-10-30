import json
import random

import discord
from discord.ext import commands
from discord import app_commands

class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("Data/blahaj.json", "r", encoding="utf-8") as file:
            self.images = json.load(file)

    @app_commands.command(name="blahaj", description="get a random image of blahaj")
    async def blahaj(self, interaction: discord.Interaction):
        img = random.choice(self.images)
        await interaction.response.send_message(f"{img['url']}\n{img['name']}")

async def setup(bot):
    cog = Images(bot)
    await bot.add_cog(cog)