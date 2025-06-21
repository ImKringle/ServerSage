from discord.ext import commands
import discord
from helper.logger import logger
from helper.utilities import is_server_hidden
from discord import app_commands

class ServerList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel
        self.cfg = bot.config

    @app_commands.command(name="list", description="List all accessible servers")
    async def slash_list_servers(self, interaction: discord.Interaction):
        if str(interaction.channel.id) != str(self.control_channel):
            await interaction.response.send_message(
                "⚠️ ServerSage Commands can only be used in the designated control channel. Ask someone with permission!",
                ephemeral=True
            )
            return
        await self._list_servers_common(interaction)

    async def _list_servers_common(self, interaction):
        try:
            try:
                keys = self.cfg.all_sections()
            except Exception as e:
                logger.error(f"Error accessing cfg.all_sections(): {e}")
                keys = []

            updated = False
            response = await self.api_manager.make_request(f"{self.api_manager.base_url}")
            servers = response.get("data", [])
            if not servers:
                await interaction.response.send_message("No accessible servers found.", ephemeral=True)
                return

            existing_servers = {}
            for key in keys:
                if key.startswith("server_"):
                    section_data = self.cfg.get_section(key)
                    if section_data is not None:
                        existing_servers[key] = section_data

            existing_ids = {
                v.get("id"): k
                for k, v in existing_servers.items()
                if isinstance(v, dict) and v.get("id")
            }

            existing_indices = [
                int(k.split('_')[1]) for k in existing_servers.keys()
                if k.startswith("server_") and len(k.split('_')) > 1 and k.split('_')[1].isdigit()
            ]
            next_index = max(existing_indices, default=0) + 1

            for server in servers:
                if not isinstance(server, dict):
                    continue
                attributes = server.get("attributes", {})
                if not isinstance(attributes, dict):
                    continue
                server_id = attributes.get("identifier")
                name = attributes.get("name", "Unnamed")
                if not server_id:
                    continue
                if server_id not in existing_ids:
                    section = f"server_{next_index}"
                    self.cfg.set(section, "id", server_id)
                    self.cfg.set(section, "name", name)
                    self.cfg.set(section, "hide", False)
                    next_index += 1
                    updated = True
                    logger.info(f"Added missing server '{name}' with ID '{server_id}' to config.")
            if updated:
                all_servers = {}
                for section in self.cfg.all_sections():
                    if section.startswith("server_"):
                        data = self.cfg.get_section(section)
                        if data is not None:
                            all_servers[section] = data
                servers_dict = {
                    section.split("_", 1)[1]: data
                    for section, data in all_servers.items()
                }
                self.panel_config["servers"] = servers_dict
                self.cfg.set("panel", "servers", servers_dict)
                self.bot.panel_config = self.panel_config
                self.bot.config = self.cfg
                logger.info("Updated config with servers found from API")
                await interaction.followup.send("Config updated with missing servers from API.", ephemeral=True)
            msg_lines = ["**Accessible Servers:**"]
            for server in servers:
                attributes = server.get("attributes", {})
                if not isinstance(attributes, dict):
                    continue
                name = attributes.get("name", "Unknown")
                server_id = attributes.get("identifier", "Unknown")
                if is_server_hidden(self.cfg, server_id):
                    continue
                msg_lines.append(f"- {name} (ID: {server_id})")
            message = "\n".join(msg_lines)
            if len(message) > 2000:
                message = message[:1997] + "..."
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)

        except Exception as e:
            logger.error(f"Error fetching servers from API: {e}")
            if interaction.response.is_done():
                await interaction.followup.send(f"Error fetching servers from API: {e}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Error fetching servers from API: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerList(bot))
