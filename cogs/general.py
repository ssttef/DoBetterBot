import discord
from discord.ext import commands
from discord import app_commands
from services.achievement_service import get_user_achievements


class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check if the bot is awake and disciplined.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong. Stop testing me and go log a habit.", ephemeral=True)

    @app_commands.command(name="achievements", description="View your secret trophy case.")
    async def achievements(self, interaction: discord.Interaction):
        achievements = await get_user_achievements(interaction.user.id)

        if not achievements:
            await interaction.response.send_message(
                "Your trophy case is completely empty. Start working.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏆 Secret Trophy Case",
            description="Achievements unlocked through pure discipline (or failure).",
            color=discord.Color.gold()
        )

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        for achv in achievements:
            # Format the date so it looks clean (YYYY-MM-DD)
            date_str = achv.unlocked_at.strftime("%Y-%m-%d")
            embed.add_field(name=achv.achievement_name, value=f"Unlocked: {date_str}", inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(GeneralCog(bot))