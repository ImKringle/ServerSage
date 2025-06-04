import discord
from discord.ext import commands
import asyncio
import signal
from sys import platform
from helper.api_manager import APIManager
from helper.config import *
from helper.logger import logger

# Load the configuration from the YAML file
config = load_config()
if config is None or not validate_config(config):
    logger.info("Invalid or missing config. Creating new config...")
    create_config()
    config = load_config()
    if not validate_config(config):
        logger.error("Config creation failed or is invalid. Exiting.")
        exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.config = config
bot.panel_config = config.get("panel", {})
bot.api_manager = APIManager(bot.panel_config)

shutdown_event = asyncio.Event()

async def shutdown():
    logger.info("Shutdown initiated...")
    await bot.api_manager.close()  # close aiohttp session properly
    await bot.close()
    shutdown_event.set()
    logger.info("Bot has been closed cleanly.")

async def main():
    # Create single shared APIManager instance on bot
    bot.api_manager = APIManager(bot.panel_config)

    # Load your extensions before starting the bot
    await bot.load_extension("cogs.power_actions")
    await bot.load_extension("cogs.list")
    await bot.load_extension("cogs.resources")

    loop = asyncio.get_running_loop()

    if platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    else:
        logger.warning("Signal handlers not supported on Windows, rely on KeyboardInterrupt.")

    try:
        await bot.start(config['discordToken'])
    except asyncio.CancelledError:
        pass

@bot.event
async def on_ready():
    logger.info("Bot is online as %s!", bot.user)

    try:
        # Use the existing APIManager instance
        servers = await bot.api_manager.fetch_all_servers()
        logger.info("Loaded %s servers from StarbaseAPI on Startup:", len(servers))
        for server in servers:
            server_id = server.get("id")
            name = server.get("name", "Unknown")
            print(f"- {name} (ID: {server_id})")
    except Exception as e:
        logger.error("Error loading servers from API on startup: %s!", e)
    logger.info('Successfully finished startup')

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Exiting.")
