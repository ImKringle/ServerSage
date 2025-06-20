from discord.ext import commands, tasks
import discord
import html
import re
import asyncio
from helper.logger import logger
from helper.utilities import validate_command_context

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

class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel
        raw_loop_value = bot.config.get("bot", {}).get("doAnnouncementLoop", False)
        self.do_announcement_loop = str(raw_loop_value).lower() == "true"
        self.announcement_channel_id = (
            bot.config.get("discord", {}).get("announcement_channel") or self.control_channel
        )
        self.seen_announcement_ids = set()
        logger.info(f"Announcement Loop enabled: {self.do_announcement_loop}")
        if self.do_announcement_loop:
            self.announcement_task.start()
        else:
            logger.info("Announcement Loop is disabled in your Config. Skipping..")

    def cog_unload(self):
        if self.do_announcement_loop and self.announcement_task.is_running():
            self.announcement_task.cancel()

    @tasks.loop(hours=1)
    async def announcement_task(self):
        await self.bot.wait_until_ready()

        servers = self.panel_config.get("servers", {})
        if not servers:
            logger.warning("No servers found in config for announcements check.")
            return

        if not self.announcement_channel_id:
            logger.warning("Announcement channel ID not set in config. Skipping announcements loop iteration.")
            return

        channel = self.bot.get_channel(int(self.announcement_channel_id))
        if channel is None:
            logger.error(f"Announcement channel ID {self.announcement_channel_id} not found or bot missing access.")
            # Cancel this loop and schedule retry
            self.announcement_task.cancel()
            asyncio.create_task(self.retry_announcement_task())
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
                    ann_id = ann["attributes"]["id"]
                    if ann_id in self.seen_announcement_ids:
                        continue
                    self.seen_announcement_ids.add(ann_id)
                    embed = create_announcement_embed(ann["attributes"], server_name)
                    await self.send_to_channel(channel, embed)
            except Exception as e:
                logger.warning(f"Failed to check announcements for {server_name} ({server_id}): {e}")

    async def retry_announcement_task(self):
        logger.info("Retrying announcement task in 60 seconds...")
        await asyncio.sleep(60)
        if not self.announcement_task.is_running():
            self.announcement_task.start()
            logger.info("Announcement task restarted after retry.")

    async def send_to_channel(self, channel, embed):
        if not channel:
            logger.warning("Announcement channel not configured or not found.")
            return
        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send announcement embed: {e}")

    @commands.command(name="announcements")
    async def fetch_announcements(self, ctx, *, query: str):
        """
        Fetches announcements for a specific server.
        """
        is_valid, server_id, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, query
        )
        if not is_valid:
            await ctx.send(error_message)
            return

        try:
            url = f"{self.api_manager.base_url}/servers/{server_id}/announcements"
            data = await self.api_manager.make_request(url)
            announcements = data.get("data", [])
            if not announcements:
                await ctx.send(f"✅ **{server_name}** has no active announcements.")
                return
            for ann in announcements:
                embed = create_announcement_embed(ann["attributes"], server_name)
                await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error fetching announcements for {server_name} ({server_id}): {e}")
            await ctx.send(f"⚠️ Failed to fetch announcements for **{server_name}**. Please try again later.")

async def setup(bot):
    await bot.add_cog(Announcements(bot))