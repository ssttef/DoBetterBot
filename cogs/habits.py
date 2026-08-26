import random
import discord
from discord.ext import commands
from discord import app_commands
from services.habit_service import create_new_habit, get_user_habits, log_habit, delete_habit
from services.achievement_service import check_log_achievements, check_specific_achievement


class HabitSelect(discord.ui.Select):
    def __init__(self, habits):
        # Create an option for every habit the user has
        options = [
            discord.SelectOption(label=habit.name, value=str(habit.id),
                                 description=f"Current Streak: {habit.current_streak}")
            for habit in habits
        ]
        super().__init__(placeholder="Select a habit to log...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        habit_id = int(self.values[0])

        # We now unpack 3 variables!
        success, message, event_data = await log_habit(interaction.user.id, habit_id)
        await interaction.response.edit_message(content=message, view=None, embed=None)

        if success:
            # We pass event_data to the achievement engine
            unlocked_achievements = await check_log_achievements(interaction.user.id, habit_id, event_data)

            for name, desc in unlocked_achievements:
                embed = discord.Embed(
                    title=f"🏆 SECRET ACHIEVEMENT UNLOCKED: {name}",
                    description=f"*{desc}*",
                    color=discord.Color.gold()
                )
                await interaction.channel.send(content=f"<@{interaction.user.id}>", embed=embed)


class HabitLogView(discord.ui.View):
    def __init__(self, habits):
        super().__init__()
        self.add_item(HabitSelect(habits))

class HabitDeleteSelect(discord.ui.Select):
        def __init__(self, habits):
            options = [
                discord.SelectOption(label=habit.name, value=str(habit.id), description="Permanently delete this habit",
                                     emoji="🗑️")
                for habit in habits
            ]
            super().__init__(placeholder="Select a habit to abandon...", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            habit_id = int(self.values[0])
            success, message = await delete_habit(interaction.user.id, habit_id)

            await interaction.response.edit_message(content=message, view=None, embed=None)

            # Trigger The Quitter!
            if success:
                unlocked = await check_specific_achievement(interaction.user.id, "The Quitter")
                if unlocked:
                    embed = discord.Embed(
                        title="🏆 SECRET ACHIEVEMENT UNLOCKED: The Quitter",
                        description="*Erasing the evidence doesn't mean it didn't happen.*",
                        color=discord.Color.gold()
                    )
                    await interaction.channel.send(content=f"<@{interaction.user.id}>", embed=embed)

class HabitDeleteView(discord.ui.View):
        def __init__(self, habits):
            super().__init__()
            self.add_item(HabitDeleteSelect(habits))

class HabitsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # The Slash Command group for all things related to habits
    habit_group = app_commands.Group(name="habit", description="Manage your discipline.")

    @habit_group.command(name="create", description="Create a new daily habit to track.")
    @app_commands.describe(name="The name of the habit (e.g., 'Go to the gym')")
    async def create_habit(self, interaction: discord.Interaction, name: str):
        # 1. Call our service layer to do the heavy database lifting
        success, message = await create_new_habit(interaction.user.id, name)

        if not success:
            # If they hit the limit, tell them ephemerally
            await interaction.response.send_message(message, ephemeral=True)
            return

        # 2. Randomized Personality Responses
        quotes = [
            f"Habit '{name}' logged. Let's see if you actually stick to it.",
            f"'{name}' added. No more excuses. Start tomorrow... or better yet, today.",
            f"New habit: '{name}'. Don't disappoint me.",
            f"Registered '{name}'. Motivation gets you started, discipline keeps you going. Prove it."
        ]

        # 3. Send the success message
        response = random.choice(quotes)
        await interaction.response.send_message(response, ephemeral=True)

        # 4. Check for Full Plate (10 habits)
        habits = await get_user_habits(interaction.user.id)
        if len(habits) == 10:
            unlocked = await check_specific_achievement(interaction.user.id, "Full Plate")
            if unlocked:
                embed = discord.Embed(
                    title="🏆 SECRET ACHIEVEMENT UNLOCKED: Full Plate",
                    description="*10 habits active. Let's see if you can juggle them all.*",
                    color=discord.Color.gold()
                )
                await interaction.channel.send(content=f"<@{interaction.user.id}>", embed=embed)

    @habit_group.command(name="list", description="View your current habits and streaks.")
    async def list_habits(self, interaction: discord.Interaction):
        # 1. Get the habits from the database
        habits = await get_user_habits(interaction.user.id)

        # 2. Check if they are slacking
        if not habits:
            await interaction.response.send_message(
                "You are currently tracking 0 habits. Your discipline is non-existent. Use `/habit create` to start.",
                ephemeral=True
            )
            return

        # 3. Build the Embed
        embed = discord.Embed(
            title="Your Discipline Tracker",
            description="Stay focused. Don't break the streak.",
            color=discord.Color.dark_grey()
        )

        # Add the user's avatar thumbnail for a personalized touch
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        # 4. Loop through the habits and add them to the embed
        for habit in habits:
            embed.add_field(
                name=f"📌 {habit.name}",
                value=f"🔥 Streak: {habit.current_streak}",
                inline=False  # False makes them stack vertically on top of each other
            )

        # 5. Send it ephemerally!
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @habit_group.command(name="complete", description="Log a habit for today and increase your streak.")
    async def complete_habit(self, interaction: discord.Interaction):
        # 1. Fetch habits to populate the dropdown
        habits = await get_user_habits(interaction.user.id)

        if not habits:
            await interaction.response.send_message("You have no habits to log. Stop slacking and use `/habit create`.",
                                                    ephemeral=True)
            return

        # 2. Show the dropdown menu
        view = HabitLogView(habits)
        await interaction.response.send_message("What did you accomplish today?", view=view, ephemeral=True)

    @habit_group.command(name="delete", description="Permanently delete a habit and erase its history.")
    async def delete_habit_cmd(self, interaction: discord.Interaction):
        habits = await get_user_habits(interaction.user.id)

        if not habits:
            await interaction.response.send_message("You don't have any habits to delete.", ephemeral=True)
            return

        view = HabitDeleteView(habits)
        await interaction.response.send_message("Giving up already? Choose what you want to abandon.", view=view,
                                                ephemeral=True)


async def setup(bot):
    await bot.add_cog(HabitsCog(bot))