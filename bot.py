import discord
from discord.ext import commands
import asyncio
import signal
from sys import platform
from helper.api_manager import APIManager
from helper.config import *
from helper.utilities import get_client_id, version_check, version_tuple
import logging
from helper.logger import logger, print_colored

version = "1.0.5"
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

config = load_config()
if config is None or not validate_config(config):
    logger.info("Invalid or missing config. Creating new config...")
    create_config()
    config = load_config()
    if not validate_config(config):
        logger.error("Config creation failed or is invalid. Exiting.")
        exit(1)

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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
bot.config = config
token = (config['discord']['bot_token'])
bot.panel_config = config.get("panel", {})
bot.api_manager = APIManager(bot.panel_config)
bot.control_channel = bot.config.get("discord", {}).get("control_channel")
shutdown_event = asyncio.Event()
cogs = [
    "players", "power_actions", "list", "resources",
    "command", "help", "logs", "query", "announcements",
    "mods"
]

async def shutdown():
    logger.info("Shutdown initiated...")
    for cog in list(bot.extensions):
        try:
            await bot.unload_extension(cog)
            logger.info(f"Unloaded Cog: {cog}")
        except Exception as e:
            logger.error(f"Failed to unload cog {cog}: {e}")
    await bot.api_manager.close()
    await bot.close()
    shutdown_event.set()
    logger.info("Bot has been closed cleanly.")

async def main():
    bot.api_manager = APIManager(bot.panel_config)
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
        logger.error("Error loading servers from API on startup: %s!", e)
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
    logger.info("Bot is online as %s!", bot.user)
    logger.info("Successfully finished startup")
    client_id = await get_client_id(token)
    if client_id:
        invite_url = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions=551903374336"
        logger.info("Invite URL: %s", invite_url)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Exiting.")
