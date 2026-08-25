import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from database.connection import init_db

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TEST_GUILD_ID = os.getenv("TEST_GUILD_ID")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN is missing from the .env file!")


class DoBetterBot(commands.Bot):
    def __init__(self):
        # Intents dictate what events the bot is allowed to listen to
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned,  # We use Slash Commands, so no text prefix needed
            intents=intents,
            help_command=None  # We will build our own custom UI help command later
        )

    async def setup_hook(self):
        """This function runs exactly ONCE before the bot fully connects to Discord."""
        print("Initializing database connection...")
        await init_db()

        print("Loading Cogs (Command Modules)...")
        await self.load_extension("cogs.general")
        await self.load_extension("cogs.habits")

        # Syncing Slash Commands to your private test server for instant updates
        if TEST_GUILD_ID:
            guild = discord.Object(id=int(TEST_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Slash commands synced instantly to Test Server: {TEST_GUILD_ID}")
        else:
            await self.tree.sync()
            print("Slash commands synced globally (this can take up to an hour).")

    async def on_ready(self):
        """This function runs when the bot has successfully logged into Discord."""
        print(f"No excuses. {self.user} is now online.")

        # Set the custom presence
        activity = discord.Activity(type=discord.ActivityType.watching, name="your excuses")
        await self.change_presence(status=discord.Status.online, activity=activity)


# --- Start the Bot ---
if __name__ == "__main__":
    bot = DoBetterBot()
    bot.run(TOKEN)