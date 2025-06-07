from discord.ext import commands
from helper.logger import logger
from helper.utilities import validate_command_context

class ServerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel

    async def _send_power_action(self, ctx, server_input: str, action: str):
        """
        Sends the resolved Server ID a Power Action
        """
        is_valid, server_id, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await ctx.send(error_message)
            return

        url = f"{self.api_manager.base_url}/servers/{server_id}/power"
        payload = {"signal": action}
        try:
            result = await self.api_manager.make_request(url, method='POST', payload=payload)
            display_name = server_name or server_id
            await ctx.send(
                f"✅ `{action}` signal sent to `{display_name}`.\nResponse: `{result.get('message', result)}`"
            )
            logger.info("Power Action: %s sent to %s.", action, display_name)
        except Exception as e:
            logger.error("Failed to send Action: %s sent to %s. Error: %s", action, server_input, e)
            await ctx.send(f"❌ Failed to `{action}` server `{server_input}`:\n{str(e)}")

    @commands.command()
    async def start(self, ctx, server_id: str):
        """Starts the given server."""
        await self._send_power_action(ctx, server_id, "start")

    @commands.command()
    async def stop(self, ctx, server_id: str):
        """Stops the given server."""
        await self._send_power_action(ctx, server_id, "stop")

    @commands.command()
    async def restart(self, ctx, server_id: str):
        """Restarts the given server."""
        await self._send_power_action(ctx, server_id, "restart")

    @commands.command()
    async def kill(self, ctx, server_id: str):
        """Kills the given server."""
        await self._send_power_action(ctx, server_id, "kill")

async def setup(bot):
    await bot.add_cog(ServerControl(bot))
