from discord.ext import commands
import yaml
import os
from helper.api_manager import APIManager
from helper.config import convert_keys_to_str
from helper.logger import logger

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

class ServerList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = APIManager(bot.panel_config)
        self.control_channel = bot.config.get("discord", {}).get("control_channel") or bot.control_channel
        if not self.control_channel:
            raise logger.critical("Control channel not configured anywhere! Startup will fail!")

    def save_config(self):
        """
        Save the current bot.config dictionary back to the YAML config file,
        using quoted strings and converted keys.
        """
        try:
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(convert_keys_to_str(self.bot.config), f, sort_keys=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def is_server_hidden(self, server_id: str) -> bool:
        servers = self.bot.panel_config.get("servers", {})
        for s in servers.values():
            if s.get("id", "").lower() == server_id.lower():
                return s.get("hide", False)
        return False

    @commands.command(name="list")
    async def list_servers(self, ctx):
        """
        Responds with a list of all servers found in the API (fresh fetch).
        Updates the config automatically if servers are missing.
        """
        if str(ctx.channel.id) != str(self.control_channel):
            await ctx.send(f"⚠️ ServerSage Commands can only be used in the designated control channel. Ask someone with permission!")
            return
        try:
            updated = False
            response = await self.api_manager.make_request(f"{self.api_manager.base_url}/")
            servers = response.get("data", [])
            if not servers:
                await ctx.send("No accessible servers found.")
                return

            config_servers = self.bot.panel_config.get("servers", {})
            existing_ids = {v.get("id"): k for k, v in config_servers.items()}

            next_index = 1
            if config_servers:
                try:
                    int_keys = [int(k) for k in config_servers.keys() if k.isdigit()]
                    if int_keys:
                        next_index = max(int_keys) + 1
                except ValueError as e:
                    logger.warning(f"Non-integer key found in config: {e}")

            for server in servers:
                if not isinstance(server, dict):
                    continue
                attributes = server.get("attributes")
                if not isinstance(attributes, dict):
                    continue

                server_id = attributes.get("identifier")
                name = attributes.get("name", "Unnamed")
                if not server_id:
                    continue
                if server_id not in existing_ids:
                    key = str(next_index)
                    config_servers[key] = {
                        "name": name,
                        "id": server_id
                    }
                    next_index += 1
                    updated = True
                    logger.info(f"Added missing server '{name}' with ID '{server_id}' to config.")

            if updated:
                self.bot.panel_config["servers"] = config_servers
                self.bot.config["panel"] = self.bot.panel_config
                self.save_config()
                logger.info("Updated config with servers found from API")
                await ctx.send("Config updated with missing servers from API.")

            msg_lines = ["**Accessible Servers:**"]
            for server in servers:
                attributes = server.get("attributes", {})
                if not isinstance(attributes, dict):
                    continue
                name = attributes.get("name", "Unknown")
                server_id = attributes.get("identifier", "Unknown")
                if self.is_server_hidden(server_id):
                    continue
                msg_lines.append(f"- {name} (ID: {server_id})")
            message = "\n".join(msg_lines)
            if len(message) > 2000:
                message = message[:1997] + "..."

            await ctx.send(message)

        except Exception as e:
            logger.error(f"Error fetching servers from API: {e}")
            await ctx.send(f"Error fetching servers from API: {e}")

async def setup(bot):
    await bot.add_cog(ServerList(bot))
