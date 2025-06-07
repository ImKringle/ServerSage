from discord.ext import commands
from helper.logger import logger
from helper.utilities import validate_command_context

class SendCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel

    @commands.command(name="command")
    async def send_command(self, ctx, server_input: str, *, command: str):
        """
        Sends a command to the specified server via the API.
        Example: !command myserver "say Hello World!"
        """
        is_valid, server_id, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await ctx.send(error_message)
            return
        try:
            url = f"{self.api_manager.base_url}/servers/{server_id}/command"
            payload = {"command": command}
            logger.info(f"Sending command to server {server_id}: {command}")
            response = await self.api_manager.make_request(url, method="POST", payload=payload)
            msg = response.get("message", "✅ Command sent successfully.")
            await ctx.send(f"📤 Sent command to `{server_name}`:\n`{command}`\n\n✅ Response: {msg}")
        except Exception as e:
            logger.error(f"Error sending command to {server_id}: {e}")
            await ctx.send(f"❌ Failed to send command: {e}")

async def setup(bot):
    await bot.add_cog(SendCommand(bot))
