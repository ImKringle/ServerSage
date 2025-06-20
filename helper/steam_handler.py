from helper.get_game import get_game_name_and_data
from helper.logger import logger
from helper.utilities import resolve_server
from steam.game_servers import a2s_info
import asyncio

async def query_server(api_manager, panel_config, server_input):
    """
    Query a server's Steam Query info given a server ID or partial name.
    Returns tuple (Steam Query info dict, ip, port) or None.
    """
    resolved = resolve_server(panel_config, server_input)
    if not resolved:
        logger.warning(f"Could not resolve server from input '{server_input}'")
        return None

    server_id, server_name = resolved

    try:
        game_info = await get_game_name_and_data(api_manager, server_name)
        if not game_info:
            logger.warning(f"Game data not found for server '{server_name}'")
            return None

        game_name, game_data = game_info

        steam_settings = game_data.get("steam", {})
        if not steam_settings.get("query", False):
            logger.info(f"Steam Query not supported for game '{game_name}'")
            return None

        url = f"{api_manager.base_url}?filter[name]={server_name}"
        response = await api_manager.make_request(url)
        server_list = response.get("data", [])
        if not server_list:
            logger.warning(f"No server data found for '{server_name}'")
            return None
        server = server_list[0]
        allocations = server.get("attributes", {}).get("relationships", {}).get("allocations", {}).get("data", [])
        if not allocations:
            logger.warning(f"No allocations found for server '{server_name}'")
            return None

        default_allocation = None
        for alloc in allocations:
            alloc_attrs = alloc.get("attributes", {})
            if alloc_attrs.get("is_default", False):
                default_allocation = alloc_attrs
                break

        if not default_allocation:
            logger.warning(f"No valid allocation found for server '{server_name}'")
            return None

        ip = default_allocation.get("ip")
        base_port = default_allocation.get("port")
        try:
            port_offset = int(steam_settings.get("port", 0))
        except (ValueError, TypeError):
            logger.warning(f"Invalid port offset for game '{game_name}', defaulting to 0")
            port_offset = 0
        query_port = base_port + port_offset

        if not ip or not query_port:
            logger.warning(f"Invalid IP or port for server '{server_name}'")
            return None

        query_addr = (ip, query_port)
        try:
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(None, lambda: a2s_info(query_addr, timeout=2))
            logger.info(f"Query ran successfully for server %s - %s:%s", server_id, ip, query_port)
            return info, ip, query_port
        except Exception as e:
            logger.error(f"Query failed for server %s - %s:%s - %s", server_id, ip, query_port, e)
            return None

    except Exception as e:
        logger.error(f"Error querying Steam server: {e}")
        return None
