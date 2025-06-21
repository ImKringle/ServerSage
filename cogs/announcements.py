from discord.ext import commands, tasks
import discord
import html
import re
import asyncio
from helper.logger import logger
from helper.utilities import validate_command_context
from discord import app_commands

def _clean_html(raw_html):
    text = re.sub(r"<[^>]*>", "", raw_html)
    return html.unescape(text.strip())

def create_announcement_embed(attr, server_name):
    cleaned_message = _clean_html(attr.get("message", ""))
    color = int(attr.get("color", "#3498db").lstrip("#"), 16)

    embed = discord.Embed(
        title=f"📢 [{server_name}] {attr.get('title', 'Announcement')}",
        description=cleaned_message,
        color=color
    )
    if not attr.get("dismissible", True):
        embed.set_footer(text="🚫 This announcement is not dismissible.")
    return embed


async def send_to_channel(channel, embed):
    if not channel:
        logger.warning("Announcement channel not configured or not found.")
        return
    try:
        await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Failed to send announcement embed: {e}")

class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.cfg = bot.config
        self.control_channel = bot.control_channel
        self.announcement_channel_id = bot.config.get("discord", "announcement_channel", self.control_channel or None)
        raw_loop_value = bot.config.get("bot", "doAnnouncementLoop", False)
        self.do_announcement_loop = str(raw_loop_value).lower() == "true"
        seen_str = bot.config.get("bot", "seen_announcements", "")
        if seen_str:
            self.seen_announcement_ids = set(seen_str.split(","))
        else:
            self.seen_announcement_ids = set()
        logger.info(f"Announcement Loop enabled: {self.do_announcement_loop}")
        if self.do_announcement_loop:
            self.announcement_task.start()
        else:
            logger.info("Announcement Loop is disabled in your Config. Skipping..")

    def cog_unload(self):
        if self.do_announcement_loop and self.announcement_task.is_running():
            self.announcement_task.cancel()

    async def _persist_seen_ids(self):
        seen_str = ",".join(self.seen_announcement_ids)
        self.bot.config.set("bot", "seen_announcements", seen_str)

    @tasks.loop(hours=1)
    async def announcement_task(self):
        await self.bot.wait_until_ready()
        if not self.announcement_channel_id:
            logger.warning("Announcement channel ID not set in config. Skipping announcements loop iteration.")
            return
        channel = self.bot.get_channel(int(self.announcement_channel_id))
        if channel is None:
            logger.error(f"Announcement channel ID {self.announcement_channel_id} not found or bot missing access.")
            self.announcement_task.cancel()
            asyncio.create_task(self.retry_announcement_task())
            return

        servers = {
            key: self.cfg.get_section(key)
            for key in self.cfg.all().keys()
            if key.startswith("server_")
        }
        if not servers:
            logger.warning("No servers found in config for announcements check.")
            return
        for key, info in servers.items():
            if info.get("hide", False):
                continue
            server_id = info.get("id")
            server_name = info.get("name")
            if not server_id:
                continue
            try:
                url = f"{self.api_manager.base_url}/servers/{server_id}/announcements"
                data = await self.api_manager.make_request(url)
                announcements = data.get("data", [])
                for ann in announcements:
                    ann_id = str(ann["attributes"]["id"])
                    if ann_id in self.seen_announcement_ids:
                        continue
                    self.seen_announcement_ids.add(ann_id)
                    await self._persist_seen_ids()
                    embed = create_announcement_embed(ann["attributes"], server_name)
                    await send_to_channel(channel, embed)
            except Exception as e:
                logger.warning(f"Failed to check announcements for {server_name} ({server_id}): {e}")

    async def retry_announcement_task(self):
        logger.info("Retrying announcement task in 60 seconds...")
        await asyncio.sleep(60)
        if not self.announcement_task.is_running():
            self.announcement_task.start()
            logger.info("Announcement task restarted after retry.")

    @app_commands.command(name="announcements", description="Fetch announcements for a specific server")
    @app_commands.describe(query="Server name or ID to fetch announcements from")
    async def slash_fetch_announcements(self, interaction: discord.Interaction, query: str):
        """
        Fetches announcements for a specific server via slash command.
        """
        is_valid, server_id, server_name, error_message = await validate_command_context(
            interaction, self.cfg, self.control_channel, query
        )
        if not is_valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return
        try:
            url = f"{self.api_manager.base_url}/servers/{server_id}/announcements"
            data = await self.api_manager.make_request(url)
            announcements = data.get("data", [])
            if not announcements:
                await interaction.response.send_message(f"✅ **{server_name}** has no active announcements.",
                                                        ephemeral=True)
                return
            await interaction.response.defer()
            for ann in announcements:
                embed = create_announcement_embed(ann["attributes"], server_name)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error fetching announcements for {server_name} ({server_id}): {e}")
            await interaction.response.send_message(
                f"⚠️ Failed to fetch announcements for **{server_name}**. Please try again later.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Announcements(bot))