from typing import Any
import aiohttp
import requests
from helper.logger import logger

def is_server_hidden(panel_config, server_id: str) -> bool:
    servers = {
        key: panel_config.get_section(key)
        for key in panel_config.all().keys()
        if key.startswith("server_")
    }
    for server in servers.values():
        if server.get("id", "").lower() == server_id.lower():
            return server.get("hide", False)
    return False

def version_tuple(v: str):
    return tuple(int(x) for x in v.split("."))


def version_check(current_version: str) -> str | None:
    """
    Checks the latest release tag from the ServerSage GitHub repo
    Returns:
        - The latest version string if current_version is not an exact match to latest release (e.g. "v1.0.3")
        - None if current version exactly matches latest release or no releases found
    """
    url = "https://api.github.com/repos/ImKringle/ServerSage/releases/latest"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        latest_tag = data.get("tag_name")
        if not latest_tag:
            return None
        latest_version = latest_tag.lstrip("v")
        if current_version != latest_version:
            return latest_tag
        return None
    except Exception as e:
        print(f"Error checking GitHub releases: {e}")
        return None

def resolve_server(panel_config, input_str: str) -> tuple[str, str] | None:
    input_clean = input_str.strip().lower()
    servers = {
        key: panel_config.get_section(key)
        for key in panel_config.all().keys()
        if key.startswith("server_")
    }
    for server in servers.values():
        server_id = server.get("id", "")
        if input_clean == server_id.lower():
            return server_id, server.get("name", "")
    for server in servers.values():
        server_name = server.get("name", "").lower()
        if input_clean in server_name:
            return server.get("id", ""), server.get("name", "")
    return None

async def validate_command_context(interaction, panel_config, control_channel, server_input):
    if str(interaction.channel.id) != str(control_channel):
        return False, None, None, "⚠️ Commands can only be used in the designated control channel."

    resolved = resolve_server(panel_config, server_input)
    if not resolved:
        return False, None, None, f"No server found matching '{server_input}'. Please check the ID or name."

    server_id, server_name = resolved

    if is_server_hidden(panel_config, server_id):
        return False, None, None, f"❌ Server '{server_input}' is hidden and cannot be viewed."

    return True, server_id, server_name, None

async def get_client_id(bot_token: str) -> Any | None:
    url = "https://discord.com/api/v10/users/@me"
    headers = {
        "Authorization": f"Bot {bot_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data["id"]
            else:
                logger.error(f"Failed to fetch client ID: {response.status}")
                return None