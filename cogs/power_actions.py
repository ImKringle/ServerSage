from helper.api_manager import APIManager
from discord.ext import commands
from helper.logger import logger

class ServerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api_manager

    def resolve_server_id(self, input_str: str) -> str:
        """
        Attempts to resolve a server name or ID (case-insensitive) to its server ID.
        If input matches a server name or ID in the config, returns the server ID.
        Otherwise, returns the input unchanged.
        """
        input_str = input_str.strip().lower()
        servers = self.bot.panel_config.get("servers", {})

        for _, server_info in servers.items():
            server_name = server_info.get("name", "").lower()
            server_id = server_info.get("id", "").lower()

            if input_str == server_name or input_str == server_id:
                return server_info.get("id", input_str)

        return input_str

    async def _send_power_action(self, ctx, server_input: str, action: str):
        server_id = self.resolve_server_id(server_input)
        url = f"{self.api.base_url}/servers/{server_id}/power"
        payload = {"signal": action}
        try:
            result = await self.api.make_request(url, method='POST', payload=payload)
            display_name = server_input if server_id == server_input else f"{server_input} ({server_id})"
            await ctx.send(
                f"✅ `{action}` signal sent to `{display_name}`.\nResponse: `{result.get('message', result)}`")
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
