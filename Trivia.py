import aiohttp
from discord import app_commands
import discord
from discord.ext import commands

class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://opentdb.com/api.php?"
        self.api_categories = "https://opentdb.com/api_category.php"
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
    async def start_trivia(self, interaction: discord.Interaction, category: str, difficulty: app_commands.Choice[str], question_type: app_commands.Choice[str]):
        question = await self.get_question(interaction, int(category), difficulty.value, question_type.value)

        await interaction.response.send_message(question)

    async def get_question(self, interaction: discord.Interaction, category_id: int = 0, difficulty: str = "any", question_type: str = "any"):
        url = self.api_base + "amount=1"
        if category_id != 0: url += f"&category={category_id}"
        print(category_id)
        if difficulty != "any": url += f"&difficulty={difficulty}"
        print(difficulty)
        if question_type != "any": url += f"&type={question_type}"
        print(question_type)
        
        print (url)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

                code = data["response_code"]
                if code != 0:
                    print(f":x: Error: {self.error_messages[code]}")
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