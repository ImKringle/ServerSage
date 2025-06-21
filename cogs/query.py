from discord.ext import commands
import discord
from discord import app_commands
from helper.steam_handler import query_server
from helper.utilities import validate_command_context

class QuerySteam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel

    @app_commands.command(name="query", description="Query a server via Steam Query and show info")
    @app_commands.describe(server_input="Server name or ID to query")
    async def query_steam(self, interaction: discord.Interaction, server_input: str):
        is_valid, _, server_name, error_message = await validate_command_context(
            interaction, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        await interaction.response.send_message(f"📡 Querying `{server_name}` via Steam...")

        result = await query_server(self.api_manager, self.panel_config, server_input)
        if not result:
            await interaction.followup.send(f"❌ Failed to query server `{server_name}` or no data available.")
            return

        info, ip, port = result
        game = info.get("game", "Unknown")
        name = info.get("name", "Unknown")
        players = info.get("players")
        max_players = info.get("max_players")
        ping = info.get("_ping")
        connection_info = f"{ip}:{port}"

        embed = discord.Embed(
            title=f"{name} - Query Results",
            color=discord.Color.blue()
        )
        embed.add_field(name="Game", value=game, inline=False)
        embed.add_field(name="Connection Details", value=connection_info, inline=False)
        if players is not None and max_players is not None:
            embed.add_field(name="Players", value=f"{players} / {max_players}", inline=False)
        if ping is not None:
            embed.add_field(name="Ping (ms)", value=f"{round(ping)}", inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QuerySteam(bot))