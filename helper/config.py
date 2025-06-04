import yaml
import os
from helper.logger import logger

# Custom representer to always quote strings
def quoted_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(str, quoted_str_representer)

def convert_keys_to_str(obj):
    """
    Recursively converts all dictionary keys to strings.
    This ensures numeric keys become strings before dumping YAML.
    """
    if isinstance(obj, dict):
        return {str(k): convert_keys_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys_to_str(elem) for elem in obj]
    else:
        return obj

def create_config():
    config = {
        "discordToken": input("Please enter your Discord bot token: "),
        "panel": {
            "APIKey": input("Please enter your panel API key: "),
            "servers": {}
        }
    }

    logger.info("Enter server IDs one by one. Leave blank to finish.")
    logger.info("You can find the ID in the URL of the Games Panel -> https://games.bisecthosting.com/server/<ID>")
    index = 1
    while True:
        sid = input("Server ID: ").strip()
        if sid == "":
            break
        name = input(f"Name for server {sid}: ").strip()
        # Store servers using string keys
        config["panel"]["servers"][str(index)] = {
            "name": name,
            "id": sid
        }
        index += 1

    # Convert keys to strings recursively before dumping
    config_to_dump = convert_keys_to_str(config)

    with open('config.yaml', 'w') as f:
        yaml.dump(config_to_dump, f, sort_keys=False)

    logger.info("Config file 'config.yaml' created.")

# validate_config and load_config remain unchanged (as your posted code)
def validate_config(config):
    if not isinstance(config, dict):
        logger.error("Config is not a dictionary.")
        return False

    if "discordToken" not in config or not isinstance(config["discordToken"], str):
        logger.error("Missing or invalid 'discordToken'")
        return False

    panel = config.get("panel")
    if not isinstance(panel, dict):
        logger.error("Missing or invalid 'panel' section")
        return False

    if "APIKey" not in panel or not isinstance(panel["APIKey"], str):
        logger.error("Missing or invalid 'APIKey'")
        return False

    servers = panel.get("servers")
    if not isinstance(servers, dict):
        logger.error("Missing or invalid 'servers' dictionary")
        return False

    for idx, server_data in servers.items():
        if not isinstance(idx, str):
            logger.error("Invalid server index key: %s", idx)
            return False
        if not isinstance(server_data, dict):
            logger.error("Invalid server data for index: %s", idx)
            return False
        if "name" not in server_data or not isinstance(server_data["name"], str):
            logger.error("Missing or invalid 'name' for server at index: %s", idx)
            return False
        if "id" not in server_data or not isinstance(server_data["id"], str):
            logger.error("Missing or invalid 'id' for server at index: %s", idx)
            return False

    logger.info("Config file 'config.yaml' validated. Proceeding with Startup..")
    return True


def load_config():
    """
    Load the configuration from the config.yaml file.
    Returns:
        dict: The configuration data if the file exists, otherwise None.
    """
    config_file = 'config.yaml'
    if not os.path.exists(config_file):
        create_config()
        # Immediately load the newly created config
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        return None

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    return config
