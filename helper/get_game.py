import re
from helper.api_manager import APIManager
from helper.logger import logger

# GAME_LIST is a manually kept list, and I won't be adding every game Bisect offers ~
# If you'd like your Bot to automatically grab logs without user input, please submit a Pull Request adding it in the format here
# "<Game_Name>": {
#     "log_file": "<Path to logfile (relative to /home/container)>",
#     "mods_dir": "<Path to Mods/Plugins folder (relative to /home/container)>",
#     "steam": {
#         "query": <True/False>,  # Whether the server supports Steam Query
#         "port": <int>  # Offset from game port to calculate the query port (e.g., 1 means query = game_port + 1)
#     }
# }
GAME_LIST = {
    "Minecraft": {
        "log_file": "logs/latest.log",
        "mods_dir": "mods",
        "steam": {
            "query": False,
            "port": 0
        },
    },
    "Enshrouded": {
        "log_file": "logs/enshrouded_server.log",
        "mods_dir": "",
        "steam": {
            "query": True,
            "port": 1
        },
    },
    "VRising": {
        "log_file": "logs/VRisingServer.log",
        "mods_dir": "BepInEx/plugins",
        "steam": {
            "query": True,
            "port": 1
        }
    }
}

def extract_game_name(docker_image: str) -> str:
    """
    Extracts and normalizes the game name from a Docker image tag.
    Returns a lowercase name with trailing digits stripped.
    """
    try:
        image_with_tag = docker_image.rsplit('/', 1)[-1]
        raw_name = image_with_tag.split(':')[0]
        normalized = re.sub(r'\d+$', '', raw_name.lower())
        return normalized
    except Exception as e:
        logger.error('Failed to extract game name from docker image: %s (%s)', docker_image, e)
        return ""

def match_game_name(normalized_name: str) -> tuple[str, dict] | None:
    """
    Match normalized game name to GAME_LIST using lowercase and digit-stripped comparison.
    Returns (original_key, game_data) or None if no match is found.
    """
    for game_key in GAME_LIST:
        key_normalized = re.sub(r'\d+$', '', game_key.lower())
        if key_normalized == normalized_name:
            return game_key, GAME_LIST[game_key]
    return None

async def get_game_name_and_data(api_manager: APIManager, server_name: str):
    """
    Fetch the docker image for a given server from the API,
    extract and normalize the game name, match it against known games,
    and return (game_name, game_data).

    Returns:
        Tuple[str, dict] | None: (game_name, game_data) or None if not found.
    """
    url = f"{api_manager.base_url}?filter[name]={server_name}"
    response = await api_manager.make_request(url)

    servers = response.get("data", [])
    if not servers:
        return None

    attributes = servers[0].get("attributes", {})
    docker_image = attributes.get("docker_image", "")
    normalized_name = extract_game_name(docker_image)
    if not normalized_name:
        return None

    match = match_game_name(normalized_name)
    if not match:
        return None

    return match  # (game_name, game_data)