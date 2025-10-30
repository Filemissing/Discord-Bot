from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot;



async def setup(bot):
    bot.add_cog(Moderation(bot))