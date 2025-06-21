from discord.ext import commands, tasks
import discord
from discord import app_commands
from helper.logger import logger
from helper.utilities import validate_command_context

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

def extract_resource_data(limits: dict, resources: dict) -> dict:
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
    if cpu_limit > 0:
        cpu_pct = (cpu_used_pct / cpu_limit) * 100
    else:
        cpu_pct = cpu_used_pct
    cpu_pct = min(cpu_pct, 100)

    if disk_limit_gb > 0:
        disk_pct = (disk_used_gb / disk_limit_gb) * 100
    else:
        disk_pct = (disk_used_gb / (disk_used_gb * 10 or 1)) * 100

    return {
        "mem_used_gb": mem_used_gb,
        "mem_pct": mem_pct,
        "cpu_used_pct": cpu_used_pct,
        "cpu_pct": cpu_pct,
        "disk_used_gb": disk_used_gb,
        "disk_pct": disk_pct,
        "uptime_seconds": uptime_seconds
    }

class Resources(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.control_channel = bot.control_channel
        self.cfg = bot.config
        raw_loop_value = bot.config.get("bot", "doResourceLoop", False)
        self.do_resource_loop = str(raw_loop_value).lower() == "true"
        logger.info(f"Resource Loop enabled: {self.do_resource_loop}")
        if self.do_resource_loop:
            self.stats_task.start()
        else:
            logger.info("Resource Loop is disabled in your Config. Skipping..")

    def cog_unload(self):
        if self.do_resource_loop and self.stats_task.is_running():
            self.stats_task.cancel()

    @tasks.loop(seconds=15.0)
    async def stats_task(self):
        await self.bot.wait_until_ready()
        try:
            stats_channel = self.cfg.get_section("discord")
            stats_channel_id = stats_channel.get("stats_channel")
            stats_message_id = stats_channel.get("stats_message_id")
            if not stats_channel_id:
                logger.warning("Stats channel ID not set in config. Skipping stats loop.")
                return
            channel = self.bot.get_channel(int(stats_channel_id))
            if channel is None:
                logger.error(f"Stats channel ID {stats_channel_id} not found or bot missing access.")
                return
            servers = {
                key: self.cfg.get_section(key)
                for key in self.cfg.all_sections()
                if key.startswith("server_")
            }
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
                    limits_data = limits_response.get("attributes", {}).get("limits", {})

                    resources_url = f"{self.api_manager.base_url}/servers/{server_id}/resources"
                    stats_response = await self.api_manager.make_request(resources_url)
                    stats_attributes = stats_response.get("attributes", {})
                    server_state = stats_attributes.get("current_state")
                    resource_data = stats_attributes.get("resources", {})
                    if server_state != "running":
                        combined_text.append(
                            f"~ {server_name} ~\n"
                            "--\n"
                            ":x: **Offline**\n"
                            "--\n"
                            ""
                        )
                        continue
                    stats = extract_resource_data(limits_data, resource_data)
                    uptime_str = format_uptime(stats["uptime_seconds"])
                    combined_text.append(
                        format_server_stats(
                            server_name,
                            stats["mem_used_gb"], stats["mem_pct"],
                            stats["cpu_used_pct"], stats["cpu_pct"],
                            stats["disk_used_gb"], stats["disk_pct"],
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
            try:
                if stats_message_id:
                    msg = await channel.fetch_message(int(stats_message_id))
                    await msg.edit(embed=embed)
                else:
                    msg = await channel.send(embed=embed)
                    self.bot.config.set("discord", "stats_message_id", str(msg.id))
                    logger.info("Sent initial combined stats message and saved message ID.")
            except discord.NotFound:
                msg = await channel.send(embed=embed)
                self.bot.config.set("discord", "stats_message_id", str(msg.id))
                logger.info("Stats message missing, sent new combined message and updated config.")
            except Exception as e:
                logger.error(f"Error editing combined stats message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in stats_task loop: {e}")

    @app_commands.command(name="stats", description="Get resource stats for a server")
    @app_commands.describe(server="Server name or ID to query stats")
    async def stats(self, interaction: discord.Interaction, server: str):
        is_valid, server_id, server_name, error_message = await validate_command_context(
            interaction, self.cfg, self.control_channel, server
        )
        if not is_valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            limits_url = f"{self.api_manager.base_url}/servers/{server_id}"
            stats_url = f"{self.api_manager.base_url}/servers/{server_id}/resources"

            limits_response = await self.api_manager.make_request(limits_url)
            stats_response = await self.api_manager.make_request(stats_url)

            limits_data = limits_response.get("attributes", {}).get("limits", {})
            stats_attributes = stats_response.get("attributes", {})
            server_state = stats_attributes.get("current_state")
            resource_data = stats_attributes.get("resources", {})

            if server_state != "running":
                await interaction.followup.send(
                    f"❌ **{server_name}** is currently offline. Use `/start {server_id}` to power it on."
                )
                return

            stats = extract_resource_data(limits_data, resource_data)
            uptime_str = format_uptime(stats["uptime_seconds"])

            sections = [
                format_stat_section("🧠", "Memory", f"{stats['mem_used_gb']:.2f} GB",
                                    create_bar(stats["mem_pct"]), stats["mem_pct"]),
                format_stat_section("🖥️", "CPU", f"{stats['cpu_used_pct']:.2f}%", create_bar(stats["cpu_pct"]),
                                    stats["cpu_pct"]),
                format_stat_section("📦", "Disk", f"{stats['disk_used_gb']:.2f} GB",
                                    create_bar(stats["disk_pct"]), stats["disk_pct"]),
            ]

            embed = discord.Embed(
                title=f"📊 Resource Stats for {server_name}",
                description="\n\n".join(sections) + f"\n\n⏱️ Uptime: {uptime_str}",
                color=discord.Color.green()
            )

            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error fetching stats for {server_id}: {e}")

async def setup(bot):
    await bot.add_cog(Resources(bot))