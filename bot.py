import discord
from discord.ext import commands
import asyncio
import signal
from sys import platform
import logging
from helper.api_manager import APIManager
from helper.utilities import get_client_id, version_check, version_tuple
from helper.logger import logger, print_colored
from helper.config_db import load_config, validate_config, create_config
import helper.console as console_module

version = "1.0.6"
ansi_art = r"""
----------------------------------------------------------------------------
  _________                                   _________                      
 /   _____/ ______________  __ ___________   /   _____/____     ____   ____  
 \_____  \_/ __ \_  __ \  \/ // __ \_  __ \  \_____  \\__  \   / ___\_/ __ \ 
 /        \  ___/|  | \/\   /\  ___/|  | \/  /        \/ __ \_/ /_/  >  ___/ 
/_______  /\___  >__|    \_/  \___  >__|    /_______  (____  /\___  / \___  >
        \/     \/                 \/                \/     \//_____/      \/ 
----------------------------------------------------------------------------
                      v{} - @GH/ImKringle/ServerSage
                          ~ Your Trusty Companion ~
----------------------------------------------------------------------------
"""
print(ansi_art.format(version))

# Load or create SQLite config
config = load_config()
if config is None or not validate_config(config):
    logger.info("Config invalid or missing. Creating new config...")
    create_config()
    config = load_config()
    if config is None or not validate_config(config):
        logger.error("Config creation failed or is invalid. Exiting.")
        exit(1)

# Version check
update = version_check(version)
if update:
    latest_version = update.lstrip("v")
    if version_tuple(version) < version_tuple(latest_version):
        logger.warning("A new version is available: %s (you have v%s)", update, version)
    elif version_tuple(version) > version_tuple(latest_version):
        logger.warning("You are running a development version (v%s) ahead of latest release %s", version, update)
    else:
        logger.info("ServerSage is Up to date!")
else:
    logger.info("ServerSage is Up to date!")

# Setup bot intents and instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=None, intents=intents, help_command=None)
tree = bot.tree

# Assign config and api_manager to bot instance
bot.config = config
token = config.get("discord", "bot_token")
bot.panel_config = config.get_section("panel")
bot.api_manager = APIManager(bot.panel_config, bot.config)
bot.control_channel = config.get("discord", "control_channel")
shutdown_event = asyncio.Event()
console_task = None
cogs = [
    "players", "power_actions", "list", "resources",
    "command", "help", "logs", "query", "announcements",
    "mods"
]


async def shutdown():
    global console_task
    logger.info("Shutdown initiated...")
    try:
        bot.config.save()
        logger.info("Configuration saved to database.")
    except Exception as e:
        logger.error(f"Error saving config on shutdown: {e}")
    for cog in list(bot.extensions):
        try:
            await bot.unload_extension(cog)
            logger.info(f"Unloaded Cog: {cog}")
        except Exception as e:
            logger.error(f"Failed to unload cog {cog}: {e}")
    await bot.api_manager.close()
    await bot.close()
    bot.config.close()
    shutdown_event.set()
    logger.info("Bot has been closed cleanly.")


async def main():
    global console_task
    try:
        servers = await bot.api_manager.fetch_all_servers()
        logger.info("Loaded %s server(s) from ServerSpawnAPI on Startup:", len(servers))
        for server in servers:
            if server.get("hide"):
                continue
            server_id = server.get("id")
            name = server.get("name", "Unknown")
            print_colored(f"- {name} (ID: {server_id})", logging.INFO)
    except Exception as e:
        logger.error(f"Error loading servers from API on startup: {e}")
    for cog in cogs:
        await bot.load_extension(f"cogs.{cog}")
        logger.info(f"Loaded Cog: {cog}")
    loop = asyncio.get_running_loop()
    if platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    else:
        logger.warning("Signal handlers not supported on Windows, rely on KeyboardInterrupt.")
    try:
        await bot.start(token)
    except asyncio.CancelledError:
        pass


@bot.event
async def on_ready():
    global console_task
    logger.info(f"Bot is online as {bot.user}!")
    logger.info("Successfully finished startup")
    try:
        guild_id = bot.config.get("discord", "guild_id")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            await tree.sync(guild=guild)
            logger.info(f"Slash commands synced to guild {guild_id}.")
        else:
            await tree.sync()
            logger.warning("Guild ID not set in config, synced commands globally.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

    client_id = await get_client_id(token)
    if client_id:
        invite_url = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot%20applications.commands&permissions=551903374336"
        logger.info(f"Invite URL: {invite_url}")
    if console_task is None or console_task.done():
        console_task = asyncio.create_task(console_module.run_console_loop(bot.config, shutdown_func=shutdown))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Exiting.")