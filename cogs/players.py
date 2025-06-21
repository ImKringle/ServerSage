import discord
from discord.ext import commands
from discord import app_commands, Embed, Colour
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
        self.cfg = bot.config
        self.control_channel = bot.control_channel

    players = app_commands.Group(name="players", description="Player management commands")

    @players.command(name="list", description="Show online players for a server")
    @app_commands.describe(server_input="Server name or ID")
    async def list(self, interaction: discord.Interaction, server_input: str):
        is_valid, server_id, server_name, error_message = await validate_command_context(
            interaction, self.cfg, self.control_channel, server_input
        )
        if not is_valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        try:
            players = await fetch_full_player_list(self.api_manager, server_id)
        except Exception as e:
            logger.error(f"Failed to fetch player list for server {server_input}: {e}")
            await interaction.response.send_message(
                f"❌ Failed to fetch player list for server `{server_input}`:\n{e}", ephemeral=True
            )
            return

        online_players = [p['username'] for p in players if p.get('status', '').lower() == 'online']
        if not online_players:
            await interaction.response.send_message(f"No online players found for server `{server_name}`.", ephemeral=True)
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
        await interaction.response.send_message(embed=embed)

    @players.command(name="clear", description="Remove players inactive for a certain time")
    @app_commands.describe(server_input="Server name or ID", time_str="Duration threshold (e.g., 1w2d3h)")
    async def clear(self, interaction: discord.Interaction, server_input: str, time_str: str):
        is_valid, server_id, server_name, error_message = await validate_command_context(
            interaction, self.cfg, self.control_channel, server_input
        )
        if not is_valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        threshold = parse_duration(time_str)
        if not threshold:
            await interaction.response.send_message(
                "❌ Invalid time format. Use formats like `1w2d3h`, `3 days`, `5h30m`.", ephemeral=True
            )
            return

        try:
            players = await fetch_full_player_list(self.api_manager, server_id)
        except Exception as e:
            logger.error(f"Failed to fetch players: {e}")
            await interaction.response.send_message("❌ Failed to fetch player list.", ephemeral=True)
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
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(PlayerListControl(bot))