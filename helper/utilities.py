from typing import Any
import aiohttp
from helper.logger import logger

def is_server_hidden(panel_config, server_id: str) -> bool:
    servers = panel_config.get("servers", {})
    for s in servers.values():
        if s.get("id", "").lower() == server_id.lower():
            return s.get("hide", False)
    return False

def resolve_server_id(panel_config, input_str: str) -> str:
    """
    Attempts to resolve a server name or ID (case-insensitive) to its server ID.
    If input matches a server name or ID in the config, returns the server ID.
    Otherwise, returns the input unchanged.
    """
    input_str = input_str.strip().lower()
    servers = panel_config.get("servers", {})

    for _, server_info in servers.items():
        server_name = server_info.get("name", "").lower()
        server_id = server_info.get("id", "").lower()

        if input_str == server_name or input_str == server_id:
            return server_info.get("id", input_str)

    return input_str

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