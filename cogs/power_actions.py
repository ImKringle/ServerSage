from discord.ext import commands
import discord
from discord import app_commands
from helper.logger import logger
from helper.utilities import validate_command_context

class ServerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.cfg = bot.config
        self.control_channel = bot.control_channel

    async def _send_power_action(self, interaction: discord.Interaction, server_input: str, action: str):
        is_valid, server_id, server_name, error_message = await validate_command_context(
            interaction, self.cfg, self.control_channel, server_input
        )
        if not is_valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        url = f"{self.api_manager.base_url}/servers/{server_id}/power"
        payload = {"signal": action}
        try:
            result = await self.api_manager.make_request(url, method='POST', payload=payload)
            display_name = server_name or server_id
            await interaction.response.send_message(
                f"✅ `{action}` signal sent to `{display_name}`.\nResponse: `{result.get('message', result)}`"
            )
            logger.info("Power Action: %s sent to %s.", action, display_name)
        except Exception as e:
            logger.error("Failed to send Action: %s sent to %s. Error: %s", action, server_input, e)
            await interaction.response.send_message(
                f"❌ Failed to `{action}` server `{server_input}`:\n{str(e)}", ephemeral=True
            )

    @app_commands.command(name="start", description="Start a server")
    @app_commands.describe(server_input="Server name or ID")
    async def start(self, interaction: discord.Interaction, server_input: str):
        await self._send_power_action(interaction, server_input, "start")

    @app_commands.command(name="stop", description="Stop a server")
    @app_commands.describe(server_input="Server name or ID")
    async def stop(self, interaction: discord.Interaction, server_input: str):
        await self._send_power_action(interaction, server_input, "stop")

    @app_commands.command(name="restart", description="Restart a server")
    @app_commands.describe(server_input="Server name or ID")
    async def restart(self, interaction: discord.Interaction, server_input: str):
        await self._send_power_action(interaction, server_input, "restart")

    @app_commands.command(name="kill", description="Kill a server")
    @app_commands.describe(server_input="Server name or ID")
    async def kill(self, interaction: discord.Interaction, server_input: str):
        await self._send_power_action(interaction, server_input, "kill")

async def setup(bot):
    await bot.add_cog(ServerControl(bot))