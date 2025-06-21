from discord.ext import commands
import discord
from helper.logger import logger
from helper.utilities import validate_command_context
from discord import app_commands

class SendCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.cfg = bot.config
        self.control_channel = bot.control_channel

    @app_commands.command(name="command", description="Send a command to the specified server")
    @app_commands.describe(
        server_input="Server name or ID to send the command to",
        command="The command text to send"
    )
    async def slash_send_command(self, interaction: discord.Interaction, server_input: str, command: str):
        """
        Sends a command to the specified server via API (slash command).
        """
        is_valid, server_id, server_name, error_message = await validate_command_context(
            interaction, self.cfg, self.control_channel, server_input
        )
        if not is_valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        try:
            url = f"{self.api_manager.base_url}/servers/{server_id}/command"
            payload = {"command": command}
            logger.info(f"Sending command to server {server_id}: {command}")
            response = await self.api_manager.make_request(url, method="POST", payload=payload)
            msg = response.get("message", "✅ Command sent successfully.")
            await interaction.response.send_message(
                f"📤 Sent command to `{server_name}`:\n`{command}`\n\n✅ Response: {msg}"
            )
        except Exception as e:
            logger.error(f"Error sending command to {server_id}: {e}")
            await interaction.response.send_message(f"❌ Failed to send command: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SendCommand(bot))
