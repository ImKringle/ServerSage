from discord.ext import commands
from discord import Embed, Colour
import re
from datetime import datetime, timezone, timedelta
from helper.logger import logger
from helper.player_list import fetch_full_player_list
from helper.utilities import validate_command_context

def parse_duration(duration_str: str):
    """
    Parse a duration string that may contain multiple time units concatenated,
    e.g. '2d12h15m', '1 week 3 days', '5h30m', etc.
    Returns a timedelta or None if invalid.
    """
    pattern = re.compile(r"(\d+)\s*(d|w|mo|h|m|day|week|month|hour|minute)s?", re.IGNORECASE)
    matches = pattern.findall(duration_str)
    if not matches:
        return None

    total = timedelta()
    for value, unit in matches:
        value = int(value)
        unit = unit.lower()
        if unit in ("d", "day"):
            total += timedelta(days=value)
        elif unit in ("w", "week"):
            total += timedelta(weeks=value)
        elif unit in ("mo", "month"):
            total += timedelta(days=value * 30)  # Approximate month
        elif unit in ("h", "hour"):
            total += timedelta(hours=value)
        elif unit in ("m", "minute"):
            total += timedelta(minutes=value)
        else:
            pass

    return total if total.total_seconds() > 0 else None


class PlayerListControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel

    @commands.command(name="playerlist")
    async def playerlist(self, ctx, server_input: str):
        """Fetch and show the list of online players for the specified server in an embed."""
        is_valid, server_id, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await ctx.send(error_message)
            return

        try:
            players = await fetch_full_player_list(self.api_manager, server_id)
        except Exception as e:
            logger.error(f"Failed to fetch player list for server {server_input}: {e}")
            await ctx.send(f"❌ Failed to fetch player list for server `{server_input}`:\n{e}")
            return

        online_players = [p['username'] for p in players if p.get('status', '').lower() == 'online']
        if not online_players:
            await ctx.send(f"No online players found for server `{server_name}`.")
            return

        embed = Embed(
            title=f"Online Players on Server `{server_name}`",
            color=Colour.green()
        )

        max_field_length = 1024
        players_text = "\n".join(online_players)
        if len(players_text) > max_field_length:
            chunks = []
            current_chunk = ""
            for player in online_players:
                line = f"{player}\n"
                if len(current_chunk) + len(line) > max_field_length:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += line
            if current_chunk:
                chunks.append(current_chunk)
            for i, chunk in enumerate(chunks, start=1):
                embed.add_field(name=f"Players (cont. {i})", value=chunk, inline=False)
        else:
            embed.add_field(name="Players", value=players_text, inline=False)
        embed.set_footer(text=f"Total Online: {len(online_players)}")
        await ctx.send(embed=embed)

    @commands.command(name="clearplayers")
    async def clearplayers(self, ctx, server_input: str, time_str: str):
        """Remove players from a server who haven't been seen within a given timeframe."""
        is_valid, server_id, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await ctx.send(error_message)
            return

        threshold = parse_duration(time_str)
        if not threshold:
            await ctx.send("❌ Invalid time format. Use formats like `1w2d3h`, `3 days`, `5h30m`.")
            return

        try:
            players = await fetch_full_player_list(self.api_manager, server_id)
        except Exception as e:
            logger.error(f"Failed to fetch players: {e}")
            await ctx.send("❌ Failed to fetch player list.")
            return

        now = datetime.now(timezone.utc)
        to_delete = []

        for player in players:
            last_seen_str = player.get("last_seen")
            if not last_seen_str or player.get("status", "").lower() == "online":
                continue
            try:
                last_seen = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
                if now - last_seen > threshold:
                    to_delete.append(player)
            except Exception as e:
                logger.warning(f"Skipping player {player.get('username')} due to time parse issue: {e}")

        deleted_count = 0
        for player in to_delete:
            player_id = player.get("id")
            if not player_id:
                continue
            url = f"{self.api_manager.base_url}/servers/{server_id}/player/{player_id}"
            try:
                await self.api_manager.make_request(url, method="DELETE")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete player {player.get('username')}: {e}")

        embed = Embed(
            title=f"🧹 Cleared Inactive Players",
            description=f"{deleted_count} players removed from `{server_name}` who were inactive for over `{time_str}`.",
            color=Colour.red()
        )
        embed.set_footer(text="Inactive = offline and not seen within time window.")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PlayerListControl(bot))
