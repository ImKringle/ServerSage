import os
import discord
from discord.ext import commands
from helper.logger import logger
from helper.utilities import validate_command_context
from helper.get_game import get_game_name_and_data

CACHE_DIR = "SS.Cache"

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    @commands.command(name="logs")
    async def fetch_logs(self, ctx, server_input: str, log_path: str = None):
        is_valid, server_id, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await ctx.send(error_message)
            return

        if not log_path:
            game_info = await get_game_name_and_data(self.api_manager, server_name)  # use resolved server_name
            if not game_info:
                await ctx.send(
                    "⚠️ Unable to determine the log file path for this game.\n"
                    "Please re-run the command with a specific file path, like:\n"
                    "`!logs <ServerID> <path/to/logfile>`\n"
                    "_(Example: `!logs myserver logs/latest.log`)_\n\n"
                    "**Consider submitting a GitHub request to add this game to auto support.**"
                )
                return

            _, game_data = game_info
            log_path = game_data.get("log_file")
            if not log_path:
                await ctx.send("❌ This game has no known log file entry. Provide the path manually.")
                return

        filename = os.path.basename(log_path)
        file_path = os.path.join(CACHE_DIR, filename)

        try:
            logger.info(f"Fetching log file: {log_path} for server {server_input}")
            file_info = await self.api_manager.make_request(
                f"{self.api_manager.base_url}/servers/{server_id}/files/download?file={log_path}"
            )
            signed_url = file_info.get("attributes", {}).get("url")
            if not signed_url:
                await ctx.send("❌ Failed to get signed URL for the log file.")
                return
            file_data = await self.api_manager.download_file(signed_url)
            with open(file_path, "wb") as f:
                f.write(file_data)
            await ctx.send(file=discord.File(file_path, filename=filename))

        except Exception as e:
            logger.error(f"Error fetching or sending logs: {e}")
            await ctx.send(f"❌ An error occurred while fetching the log file:\n{e}")
        finally:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted cached file: {file_path}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to delete cached file {file_path}: {cleanup_err}")


async def setup(bot):
    await bot.add_cog(Logs(bot))
