from discord.ext import commands, tasks
import yaml
import discord
import random
from helper.logger import logger

def create_bar(percent: float, size: int = 15) -> str:
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 100
    filled_blocks = int(round((percent / 100) * size))
    if percent > 0 and filled_blocks == 0:
        filled_blocks = 1
    filled_blocks = min(filled_blocks, size)
    return "▓" * filled_blocks + "░" * (size - filled_blocks)

def format_stat_section(emoji: str, label: str, value: str, bar: str, percent: float) -> str:
    return f"{emoji} - **{label}:**\n{value} {bar} ({percent:.0f}%)"

def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 and days == 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

    if not parts:
        return "less than a minute"
    return "about " + " ".join(parts)

def format_server_stats(server_name: str,
                        mem_used_gb: float, mem_pct: float,
                        cpu_used_pct: float, cpu_pct: float,
                        disk_used_gb: float, disk_pct: float,
                        uptime_str: str) -> str:
    sections = [
        format_stat_section("🧠", "Memory", f"{mem_used_gb:.2f} GB", create_bar(mem_pct), mem_pct),
        format_stat_section("🖥️", "CPU", f"{cpu_used_pct:.2f}%", create_bar(cpu_pct), cpu_pct),
        format_stat_section("📦", "Disk", f"{disk_used_gb:.2f} GB", create_bar(disk_pct), disk_pct),
    ]
    return "\n".join([
        f"~ {server_name} ~",
        "--",
        *sections,
        "--",
        f"⏱️ Uptime: {uptime_str}",
        "--",
        ""
    ])

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
        combined_text = []

        for key, info in servers.items():
            if info.get("hide", False):
                continue

            server_id = info.get("id")
            server_name = info.get("name")
            if not server_id:
                continue

            try:
                server_details_url = f"{self.api_manager.base_url}/servers/{server_id}"
                limits_response = await self.api_manager.make_request(server_details_url)
                limits = limits_response.get("attributes", {}).get("limits", {})

                resources_url = f"{self.api_manager.base_url}/servers/{server_id}/resources"
                stats_response = await self.api_manager.make_request(resources_url)
                attributes = stats_response.get("attributes", {})
                current_state = attributes.get("current_state")
                resources = attributes.get("resources", {})

                if current_state != "running":
                    combined_text.append(
                        f"~ {server_name} ~\n"
                        "--\n"
                        ":x: **Offline**\n"
                        "--\n"
                        ""
                    )
                    continue

                mem_limit_mb = limits.get("memory", 0)
                mem_limit_gb = mem_limit_mb / 1024 if mem_limit_mb else 0
                cpu_limit = limits.get("cpu", 0)
                disk_limit_mb = limits.get("disk", 0)
                disk_limit_gb = disk_limit_mb / 1024 if disk_limit_mb else 0

                mem_used_gb = resources.get("memory_bytes", 0) / (1024 ** 3)
                cpu_used_pct = resources.get("cpu_absolute", 0)
                disk_used_gb = resources.get("disk_bytes", 0) / (1024 ** 3)
                uptime_ms = resources.get("uptime", 0)
                uptime_seconds = uptime_ms / 1000

                mem_pct = (mem_used_gb / mem_limit_gb) * 100 if mem_limit_gb else 0
                if cpu_limit and cpu_limit > 0:
                    cpu_pct = (cpu_used_pct / cpu_limit) * 100
                else:
                    cpu_pct = cpu_used_pct
                cpu_pct = min(cpu_pct, 100)
                if disk_limit_gb > 0:
                    disk_pct = (disk_used_gb / disk_limit_gb) * 100
                else:
                    # Simulate a limit 10x the current usage so the bar isn't maxed
                    disk_pct = (disk_used_gb / (disk_used_gb * 10 or 1)) * 100

                uptime_str = format_uptime(uptime_seconds)

                combined_text.append(
                    format_server_stats(
                        server_name,
                        mem_used_gb, mem_pct,
                        cpu_used_pct, cpu_pct,
                        disk_used_gb, disk_pct,
                        uptime_str
                    )
                )
            except Exception as e:
                logger.error(f"Failed to fetch stats for server {server_name} ({server_id}): {e}")
                combined_text.append(
                    f"~ {server_name} ~\n"
                    "--\n"
                    "⚠️ Error fetching stats\n"
                    "--\n"
                    ""
                )

        if combined_text:
            embed.description = "\n".join(combined_text)

        if self.stats_message_id:
            try:
                msg = await channel.fetch_message(int(self.stats_message_id))
                await msg.edit(embed=embed)
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
            await ctx.send("⚠️ ServerSage Commands can only be used in the designated control channel.")
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

        if self.is_server_hidden(server_id):
            await ctx.send(f"❌ Server `{query}` is hidden and cannot be viewed via commands.")
            return

        try:
            # Fetch details and resource usage
            limits_url = f"{self.api_manager.base_url}/servers/{server_id}"
            stats_url = f"{self.api_manager.base_url}/servers/{server_id}/resources"

            limits_response = await self.api_manager.make_request(limits_url)
            stats_response = await self.api_manager.make_request(stats_url)

            limits = limits_response.get("attributes", {}).get("limits", {})
            attributes = stats_response.get("attributes", {})
            current_state = attributes.get("current_state")
            resources = attributes.get("resources", {})

            if current_state != "running":
                await ctx.send(f"❌ **{server_name}** is currently offline. Use `!start {server_id}` to power it on.")
                return

            # Extract and format values
            mem_limit_mb = limits.get("memory", 0)
            mem_limit_gb = mem_limit_mb / 1024 if mem_limit_mb else 0
            cpu_limit = limits.get("cpu", 0)
            disk_limit_mb = limits.get("disk", 0)
            disk_limit_gb = disk_limit_mb / 1024 if disk_limit_mb else 0

            mem_used_gb = resources.get("memory_bytes", 0) / (1024 ** 3)
            cpu_used_pct = resources.get("cpu_absolute", 0)
            disk_used_gb = resources.get("disk_bytes", 0) / (1024 ** 3)
            uptime_ms = resources.get("uptime", 0)
            uptime_seconds = uptime_ms / 1000

            mem_pct = (mem_used_gb / mem_limit_gb) * 100 if mem_limit_gb else 0
            cpu_pct = (cpu_used_pct / cpu_limit) * 100 if cpu_limit else cpu_used_pct
            cpu_pct = min(cpu_pct, 100)
            disk_pct = (disk_used_gb / disk_limit_gb) * 100 if disk_limit_gb else 50

            uptime_str = format_uptime(uptime_seconds)

            sections = [
                format_stat_section("🧠", "Memory", f"{mem_used_gb:.2f} GB", create_bar(mem_pct), mem_pct),
                format_stat_section("🖥️", "CPU", f"{cpu_used_pct:.2f}%", create_bar(cpu_pct), cpu_pct),
                format_stat_section("📦", "Disk", f"{disk_used_gb:.2f} GB", create_bar(disk_pct), disk_pct),
            ]

            embed = discord.Embed(
                title=f"📊 Resource Stats for {server_name}",
                description="\n\n".join(sections) + f"\n\n⏱️ Uptime: {uptime_str}",
                color=discord.Color.green()
            )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error fetching stats for {server_id}: {e}")
            await ctx.send(f"⚠️ Failed to fetch resource stats for **{server_name}**. Please try again later.")

async def setup(bot):
    await bot.add_cog(Resources(bot))
