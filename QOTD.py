from datetime import datetime, time, timedelta
import asyncio
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp

import discord
from discord import channel
from discord import mentions
from discord.ext import commands, tasks
from discord import app_commands

question_time = datetime.time(hour=18)

class QOTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_ids = { 1339303365963677718: 1433040386359824494 }
        with open("Data/Questions.json", "r", encoding="utf-8") as file:
            self.questions = json.load(file)
        self.question_index = 0


    @app_commands.command(name="set_qotd_channel", description="set the qotd channel for this server")
    async def set_qotd_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.channel.permissions_for(interaction.user).administrator and not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(":no_entry: You need to have administrator permissions to use that command", ephemeral=True)
            return

        self.channel_ids[interaction.guild_id] = channel.id
        await interaction.response.send_message(f"Updated QOTD channel to {channel.jump_url}", ephemeral=True)

    @tasks.loop(time=question_time)
    async def post_qotd(self):
        question = self.questions[self.question_index]

        for guild_id, channel_id in self.channel_ids.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                message = await channel.send("@everyone QOTD: " + question)
                thread = await message.create_thread(
                    name=f"QOTD ({datetime.today().date().day}-{datetime.today().date().month})",
                    auto_archive_duration=1440
                    )

        self.question_index += 1

    # async def fetch_qotd(self):
    #     question_url = "https://randomwordgenerator.com/json/questions.json"

    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(question_url) as resp:
    #             data = await resp.json()

    #             return data['data'][self.question_index]['question']

async def setup(bot):
    cog = QOTD(bot)
    await bot.add_cog(cog)
