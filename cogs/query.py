from discord.ext import commands
import discord
from helper.steam_query import query_steam_server
from helper.utilities import validate_command_context

class QuerySteam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel

    @commands.command(name="query")
    async def query_steam(self, ctx, *, server_input: str):
        """
        Queries the specified server via Steam Query and replies with an embed showing key info.
        """
        is_valid, _, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await ctx.send(error_message)
            return

        await ctx.send(f"📡 Querying `{server_name}` via Steam...")

        result = await query_steam_server(self.api_manager, self.panel_config, server_input)
        if not result:
            await ctx.send(f"❌ Failed to query server `{server_name}` or no data available.")
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

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QuerySteam(bot))
