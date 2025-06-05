from discord.ext import commands
from helper.api_manager import APIManager
from helper.logger import logger

class SendCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = APIManager(bot.panel_config)
        self.control_channel = bot.config.get("discord", {}).get("control_channel") or bot.control_channel
        if not self.control_channel:
            raise logger.critical("Control channel not configured anywhere! Startup will fail!")

    def is_server_hidden(self, server_id: str) -> bool:
        servers = self.bot.panel_config.get("servers", {})
        for s in servers.values():
            if s.get("id", "").lower() == server_id.lower():
                return s.get("hide", False)
        return False

    @commands.command(name="command")
    async def send_command(self, ctx, server_id: str, *, command: str):
        """
        Sends a command to the specified server ID via the API.
        Example: !send 123fa9s1 "say Hello World!"
        """
        if str(ctx.channel.id) != str(self.control_channel):
            await ctx.send("⚠️ ServerSage Commands can only be used in the designated control channel.")
            return

        if self.is_server_hidden(server_id):
            await ctx.send("❌ You do not have permission to use this command on that server.")
            return

        servers = self.bot.panel_config.get("servers", {})
        matched = None
        for server in servers.values():
            if server.get("id") == server_id:
                matched = server
                break

        if not matched:
            await ctx.send(f"❌ No server found with ID `{server_id}` in the config.")
            return

        try:
            url = f"{self.api_manager.base_url}/servers/{server_id}/command"
            payload = {"command": command}

            logger.info(f"Sending command to server {server_id}: {command}")
            response = await self.api_manager.make_request(url, method="POST", payload=payload)

            msg = response.get("message", "✅ Command sent successfully.")
            await ctx.send(f"📤 Sent command to `{server_id}`:\n`{command}`\n\n✅ Response: {msg}")

        except Exception as e:
            logger.error(f"Error sending command to {server_id}: {e}")
            await ctx.send(f"❌ Failed to send command: {e}")

async def setup(bot):
    await bot.add_cog(SendCommand(bot))
