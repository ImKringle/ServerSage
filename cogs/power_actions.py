from discord.ext import commands
from helper.logger import logger

class ServerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api_manager
        self.control_channel = bot.config.get("discord", {}).get("control_channel") or bot.control_channel
        if not self.control_channel:
            raise logger.critical("Control channel not configured anywhere! Startup will fail!")

    def is_server_hidden(self, server_id: str) -> bool:
        servers = self.bot.panel_config.get("servers", {})
        for s in servers.values():
            if s.get("id", "").lower() == server_id.lower():
                return s.get("hide", False)
        return False

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
        """
        Sends the resolved Server ID a Power Action
        """
        if str(ctx.channel.id) != str(self.control_channel):
            await ctx.send(f"⚠️ ServerSage Commands can only be used in the designated control channel. Ask someone with permission!")
            return
        server_id = self.resolve_server_id(server_input)
        if self.is_server_hidden(server_id):
            await ctx.send(f"❌ Server `{server_input}` is hidden and cannot be controlled via commands.")
            return
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
