from discord.ext import commands, tasks
import yaml
import discord
from helper.logger import logger

class Resources(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.config.get("discord", {}).get("control_channel") or bot.control_channel
        if not self.control_channel:
            raise logger.critical("Control channel not configured anywhere! Startup will fail!")
        self.stats_channel_id =  bot.config.get("discord", {}).get("stats_channel") or bot.control_channel
        self.stats_message_id =  bot.config.get("stats_message_id") or None
        self.stats_task.start()

    def is_server_hidden(self, server_id: str) -> bool:
        servers = self.bot.panel_config.get("servers", {})
        for s in servers.values():
            if s.get("id", "").lower() == server_id.lower():
                return s.get("hide", False)
        return False

    def cog_unload(self):
        self.stats_task.cancel()

    async def save_config(self):
        if "discord" not in self.bot.config:
            self.bot.config["discord"] = {}
        self.bot.config["discord"]["stats_message_id"] = self.stats_message_id
        self.bot.config["panel"] = self.bot.panel_config
        try:
            with open("config.yaml", "w") as f:
                yaml.dump(self.bot.config, f, sort_keys=False)
            logger.info("Config saved with updated stats_message_id")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    @tasks.loop(seconds=15.0)
    async def stats_task(self):
        await self.bot.wait_until_ready()
        if not self.stats_channel_id:
            logger.warning("Stats channel ID not set in config. Skipping stats loop.")
            return

        channel = self.bot.get_channel(int(self.stats_channel_id))
        if channel is None:
            logger.error(f"Stats channel ID {self.stats_channel_id} not found or bot missing access.")
            return

        servers = self.panel_config.get("servers", {})
        if not servers:
            logger.info("No servers found in panel config for stats loop.")
            return

        embed = discord.Embed(title="Combined Resource Stats", color=discord.Color.blue())
        for key, info in servers.items():
            if info.get("hide", False):
                continue

            server_id = info.get("id")
            server_name = info.get("name")
            if not server_id:
                continue

            try:
                url = f"{self.api_manager.base_url}/servers/{server_id}/resources"
                response = await self.api_manager.make_request(url)
                attributes = response.get("attributes", {})
                current_state = attributes.get("current_state")
                resources = attributes.get("resources", {})

                if current_state != "running":
                    embed.add_field(name=server_name, value=":x: **Offline**", inline=False)
                    continue

                mem_gb = resources.get("memory_bytes", 0) / (1024 ** 3)
                cpu_pct = resources.get("cpu_absolute", 0)
                disk_gb = resources.get("disk_bytes", 0) / (1024 ** 3)

                value_str = (
                    f"Memory: {mem_gb:.2f} GB\n"
                    f"CPU: {cpu_pct:.2f}%\n"
                    f"Disk: {disk_gb:.2f} GB"
                )
                embed.add_field(name=server_name, value=value_str, inline=False)
            except Exception as e:
                logger.error(f"Failed to fetch stats for server {server_name} ({server_id}): {e}")
                embed.add_field(name=server_name, value="Error fetching stats", inline=False)

        if self.stats_message_id:
            try:
                msg = await channel.fetch_message(int(self.stats_message_id))
                await msg.edit(embed=embed)
                logger.info("Updated existing combined stats message.")
            except discord.NotFound:
                msg = await channel.send(embed=embed)
                self.stats_message_id = str(msg.id)
                await self.save_config()
                logger.info("Stats message missing, sent new combined message and updated config.")
            except Exception as e:
                logger.error(f"Error editing combined stats message: {e}")
        else:
            msg = await channel.send(embed=embed)
            self.stats_message_id = str(msg.id)
            await self.save_config()
            logger.info("Sent initial combined stats message and saved message ID.")

    @commands.command(name="stats")
    async def stats(self, ctx, *, query: str):
        if str(ctx.channel.id) != str(self.control_channel):
            await ctx.send(f"⚠️ ServerSage Commands can only be used in the designated control channel. Ask someone with permission!")
            return

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

        # Check if the server is hidden
        if self.is_server_hidden(server_id):
            await ctx.send(f"❌ Server `{server_id}` is hidden and cannot be controlled via commands.")
            return
        hidden = False
        for s in servers.values():
            if s.get("id", "").lower() == server_id.lower():
                hidden = s.get("hide", False)
                break

        if hidden:
            await ctx.send(f"❌ Server `{query}` is hidden and cannot be viewed via commands.")
            return

        try:
            url = f"{self.api_manager.base_url}/servers/{server_id}/resources"
            response = await self.api_manager.make_request(url)

            attributes = response.get("attributes", {})
            current_state = attributes.get("current_state")
            resources = attributes.get("resources", {})

            if current_state != "running":
                await ctx.send(f"The server **{server_name}** is not currently running. Run `!start {server_id}` and try again.")
                logger.info(f"Attempted to check stats for server {server_id} but it is offline.")
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
