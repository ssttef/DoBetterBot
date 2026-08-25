import discord
from discord.ext import commands
from discord import app_commands

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # This decorator turns the function into a Discord Slash Command
    @app_commands.command(name="ping", description="Check if the bot is awake and disciplined.")
    async def ping(self, interaction: discord.Interaction):
        # ephemeral=True means ONLY the user who typed the command can see the reply!
        await interaction.response.send_message(
            "Pong. Stop testing me and go log a habit.",
            ephemeral=True
        )

# This function is required for Discord.py to load the Cog
async def setup(bot):
    await bot.add_cog(GeneralCog(bot))