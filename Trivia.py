from email.errors import MessageError
import html
import aiohttp
from discord import app_commands, emoji
import discord
from discord.ext import commands, tasks
import asyncio

class Trivia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_base = "https://opentdb.com/api.php?"
        self.api_categories = "https://opentdb.com/api_category.php"
        self.api_token_request = "https://opentdb.com/api_token.php?command=request"
        self.active_trivia = {}
        self.error_messages = {
            1: "No Results, may occur when trying to retrieve to many questions",
            2: "Invalid Parameter",
            3: "Token Not Found, Session has expired. use /trivia to start a new session",
            4: "Token Empty, all questions for this category have been exhausted",
            5: "Rate Limit, api is on cooldown try again in 5 seconds"
            }

    async def cog_load(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_categories) as resp:
                data = await resp.json()
                self.categories: dict = {c["name"]: c["id"] for c in data["trivia_categories"]}
                self.categories["any"] = 0

    @app_commands.command(name="trivia", description="start a new trivia session")
    @app_commands.describe(category="Start typing to see suggestions")
    @app_commands.choices(
        difficulty=[
            app_commands.Choice(name="easy", value="easy"),
            app_commands.Choice(name="medium", value="medium"),
            app_commands.Choice(name="hard", value="hard"),
            app_commands.Choice(name="any", value="any")
        ],
        question_type=[
            app_commands.Choice(name="multiple choice", value="multiple"),
            app_commands.Choice(name="True or False", value="boolean"),
            app_commands.Choice(name="any", value="any")
        ])
    async def start_trivia(self, interaction: discord.Interaction, category: str = "0", difficulty: str = "any", question_type: str = "any"):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_token_request) as resp:
                data = await resp.json()
                if data["response_code"] == 0:
                    session_token = data["token"]
                else:
                    interaction.response.send_message("❌ Failed to get token, try again in a few seconds")
                    return


        question_data = await self.get_question(interaction, session_token, int(category), difficulty, question_type)

        question = html.unescape(question_data["question"])
        answers: list = [html.unescape(answer) for answer in question_data["incorrect_answers"] + [question_data["correct_answer"]]]

        answers.sort(reverse=True)

        message_text = f"Question: {question}\n\nAnswers:\n"

        index = 1
        for answer in answers:
            message_text += f"{index}: {html.unescape(answer)}\n"
            index += 1

        message = await interaction.response.send_message(message_text)

        self.active_trivia[interaction.channel_id] = {
            "session_id": 0, # actually implement session tokens later
            "answer": html.unescape(question_data["correct_answer"]),
            "incorrect_answers": [html.unescape(answer) for answer in question_data["incorrect_answers"]],
            "timeout": asyncio.get_event_loop().time() + 20,
            "message_id": message.message_id,
            "responses": {}
            }

        if not self.monitor_channel.is_running():
            self.monitor_channel.start()
    
    @tasks.loop(seconds=1)
    async def monitor_channel(self):
        to_remove = []
        for channel_id, session in self.active_trivia.items():
            channel = self.bot.get_channel(channel_id)

            if session["timeout"] < asyncio.get_event_loop().time():
                await channel.get_partial_message(session["message_id"]).reply(f"⏰ Time's up! The correct answer was **{session['answer']}**")
                to_remove.append(channel_id)

        for ch_id in to_remove:
            del self.active_trivia[ch_id]

        if len(self.active_trivia) == 0:
            self.monitor_channel.stop()

    @commands.Cog.listener()            
    async def on_message(self, message: discord.Message):
        if message.author.bot: return

        session = self.active_trivia.get(message.channel.id)
        if not session: return

        text = message.content.lower().strip()

        if text == session["answer"].lower().strip():
            del self.active_trivia[message.channel.id]
            await message.reply("✅ Correct")
        elif text in [answer.lower().strip() for answer in session["incorrect_answers"]]:
            await message.add_reaction("❌")

    async def get_question(self, interaction: discord.Interaction, session_token: str, category_id: int = 0, difficulty: str = "any", question_type: str = "any"):
        url = self.api_base + "amount=1"
        if category_id != 0: url += f"&category={category_id}"
        if difficulty != "any": url += f"&difficulty={difficulty}"
        if question_type != "any": url += f"&type={question_type}"
        if session_token != "": url += f"&token={session_token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

                code = data["response_code"]
                if code != 0:
                    print(f"❌ Error: {self.error_messages[code]}")
                    return False

                return data["results"][0]

    @start_trivia.autocomplete("category")
    async def category_autocomplete(self, interaction: discord.Interaction, current: str):
        suggestions = [
            app_commands.Choice(name=name, value=str(value))
            for name, value in self.categories.items()
            if current.lower() in name.lower()
            ]

        return suggestions[:25]

async def setup(bot):
    await bot.add_cog(Trivia(bot))