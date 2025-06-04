from discord.ext import commands
from helper.logger import logger

class Resources(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager  # Your APIManager instance
        self.panel_config = bot.panel_config  # Your config dict

    @commands.command(name="stats")
    async def stats(self, ctx, *, query: str):
        """
        Usage: !stats <server_id or server_name>
        Gets resource usage stats for the specified server.
        """
        # Find server by ID or name (case insensitive)
        servers = self.panel_config.get("servers", {})
        server_id = None
        server_name = None
        query_lower = query.lower()

        for key, info in servers.items():
            if info.get("id", "").lower() == query_lower or info.get("name", "").lower() == query_lower:
                server_id = info.get("id")
                server_name = info.get("name")
                break

        if not server_id:
            await ctx.send(f"No server found matching '{query}'. Please check the ID or name.")
            return

        try:
            url = f"{self.api_manager.base_url}/servers/{server_id}/resources"
            response = await self.api_manager.make_request(url)  # Await async request

            attributes = response.get("attributes", {})
            current_state = attributes.get("current_state")
            resources = attributes.get("resources", {})

            if current_state != "running":
                await ctx.send(f"The server **{server_name}** is not currently running. Run `!start {server_id}` and try again.")
                logger.info("Attempted to check Stats for Server: (%s) but the Server is Offline..", server_id)
                return

            mem_gb = resources.get("memory_bytes", 0) / (1024 ** 3)
            cpu_pct = resources.get("cpu_absolute", 0)
            disk_gb = resources.get("disk_bytes", 0) / (1024 ** 3)

            logger.info(f"Stats for {server_name} (ID: {server_id}): Memory: {mem_gb:.2f} GB, CPU: {cpu_pct:.2f}%, Disk: {disk_gb:.2f} GB")

            await ctx.send(
                f"📊 **Resource Stats for {server_name}**\n"
                f"> **Memory Usage:** {mem_gb:.2f} GB\n"
                f"> **CPU Usage:** {cpu_pct:.2f}%\n"
                f"> **Disk Usage:** {disk_gb:.2f} GB"
            )
        except Exception as e:
            logger.error(f"Error fetching resources for server {server_id}: {e}")
            await ctx.send(f"Failed to retrieve stats for server {server_name}. Please try again later.")

async def setup(bot):
    await bot.add_cog(Resources(bot))