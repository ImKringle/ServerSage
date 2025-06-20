from discord.ext import commands
import discord
from fnmatch import fnmatch
from helper.utilities import validate_command_context
from helper.get_game import get_game_name_and_data
from helper.logger import logger

class ModsManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_manager = bot.api_manager
        self.panel_config = bot.panel_config
        self.control_channel = bot.control_channel

    async def get_mods_dir_for_server(self, server_name: str):
        try:
            game_info = await get_game_name_and_data(self.api_manager, server_name)
            if not game_info:
                logger.warning(f"Could not find game info for server '{server_name}'")
                return None
            _, game_data = game_info
            mods_dir = game_data.get("mods_dir")
            return mods_dir.strip() if mods_dir and mods_dir.strip() else None
        except Exception as e:
            logger.error(f"Error getting mods_dir for server '{server_name}': {e}")
            return None

    async def list_mods_files(self, server_id: str, mods_dir: str):
        url = f"{self.api_manager.base_url}/servers/{server_id}/files/list?directory=/{mods_dir}"
        response = await self.api_manager.make_request(url)
        return [file["attributes"] for file in response.get("data", []) if "attributes" in file]

    @commands.command(name="mods-list")
    async def mods_list(self, ctx, *, server_input: str):
        is_valid, server_id, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await ctx.send(error_message)
            return

        mods_dir = await self.get_mods_dir_for_server(server_name)
        if not mods_dir:
            await ctx.send(f"❌ Server '{server_name}' does not have a mods directory configured.")
            return

        try:
            files = await self.list_mods_files(server_id, mods_dir)
            if not files:
                await ctx.send(f"ℹ️ No files found in mods directory `{mods_dir}` for server `{server_name}`.")
                return

            file_names = sorted(
                f"{f['name']}/" if not f.get("is_file", False) else f["name"]
                for f in files
            )
            file_list_str = "\n".join(file_names)
            embed = discord.Embed(
                title=f"Mods List for {server_name} (directory: /{mods_dir})",
                description=file_list_str,
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Failed to fetch mods list for `{server_name}`: {e}")

    @commands.command(name="mods-manage")
    async def mods_manage(self, ctx, action: str, mod_pattern: str, *, server_input: str):
        """
        Enable or disable mods by renaming files in the mods directory.
        Usage: !mods-manage enable|disable <mod_pattern> <server>
        """
        action = action.lower()
        if action not in ("enable", "disable"):
            await ctx.send("❌ Action must be 'enable' or 'disable'.")
            return

        is_valid, server_id, server_name, error_message = await validate_command_context(
            ctx, self.panel_config, self.control_channel, server_input
        )
        if not is_valid:
            await ctx.send(error_message)
            return

        mods_dir = await self.get_mods_dir_for_server(server_name)
        if not mods_dir:
            await ctx.send(f"❌ Server '{server_name}' does not have a mods directory configured.")
            return

        try:
            files = await self.list_mods_files(server_id, mods_dir)
            if not files:
                await ctx.send(f"ℹ️ No files found in mods directory `{mods_dir}` for server `{server_name}`.")
                return

            rename_files = []
            affected_names = []
            skipped_folders = []

            for file in files:
                filename = file.get("name", "")
                if not fnmatch(filename, mod_pattern):
                    continue
                if not file.get("is_file", False):
                    skipped_folders.append(filename)
                    continue

                from_path = f"{mods_dir}/{filename}"
                if action == "disable" and not filename.endswith(".disabled"):
                    to_path = f"{from_path}.disabled"
                    rename_files.append({"from": from_path, "to": to_path})
                    affected_names.append(filename)
                elif action == "enable" and filename.endswith(".disabled"):
                    to_path = f"{mods_dir}/{filename[:-9]}"
                    rename_files.append({"from": from_path, "to": to_path})
                    affected_names.append(filename)

            if not rename_files and not skipped_folders:
                await ctx.send(f"ℹ️ No mods matched or required action `{action}` in `{mods_dir}`.")
                return

            if rename_files:
                url = f"{self.api_manager.base_url}/servers/{server_id}/files/rename"
                json_body = {
                    "root": "/",
                    "files": rename_files
                }
                await self.api_manager.make_request(url, method="PUT", json=json_body)

            response_lines = []
            if affected_names:
                response_lines.append(f"✅ Successfully {action}d {len(affected_names)} mod(s):")
                response_lines.append("```" + "\n".join(affected_names) + "```")

            if skipped_folders:
                response_lines.append("⚠️ The following are folders and must be removed manually:")
                response_lines.append("```" + "\n".join(skipped_folders) + "```")

            await ctx.send("\n".join(response_lines))

        except Exception as e:
            await ctx.send(f"⚠️ Failed to {action} mods on `{server_name}`: {e}")

async def setup(bot):
    await bot.add_cog(ModsManager(bot))