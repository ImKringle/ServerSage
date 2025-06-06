from helper.api_manager import APIManager
from helper.logger import logger

async def fetch_full_player_list(api_manager: APIManager, server_id: str) -> list[dict]:
    """
    Fetches all players across all pages from the API.
    Returns a list of dicts: { 'username': str, 'status': str }.
    """
    players = []
    page = 1
    while True:
        url = f"{api_manager.base_url}/servers/{server_id}/player?page={page}"
        try:
            response = await api_manager.make_request(url)
        except Exception as e:
            logger.error("Failed to fetch player list: %s", e)
            break
        data = response.get("data", [])
        if not data:
            break
        for player_obj in data:
            attr = player_obj.get("attributes", {})
            players.append({
                "id": attr.get("id"),
                "username": attr.get("username", "Unknown"),
                "status": attr.get("status", "unknown"),
                "last_seen": attr.get("last_seen"),
            })
        pagination = response.get("meta", {}).get("pagination", {})
        total_pages = pagination.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1

    return players