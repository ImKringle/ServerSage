import yaml
import os
import platform
import subprocess
from helper.logger import logger
from helper.input_handler import prompt_input

def quoted_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.SafeDumper.add_representer(str, quoted_str_representer)

def convert_keys_to_str(obj):
    if isinstance(obj, dict):
        return {str(k): convert_keys_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys_to_str(elem) for elem in obj]
    else:
        return obj

def save_config(
    *,
    bot=None,
    config=None,
    updates: dict | None = None,
    path: str = "config.yaml"
):
    """
    Save a config dictionary or a bot's config to a YAML file,
    optionally applying updates before saving.
    """
    if bot:
        cfg = bot.config
        if updates:
            for section, values in updates.items():
                if not isinstance(values, dict):
                    continue
                if section not in cfg or not isinstance(cfg[section], dict):
                    cfg[section] = {}
                cfg[section].update(values)
        if hasattr(bot, "panel_config"):
            cfg["panel"] = bot.panel_config
    elif config is not None:
        cfg = config
    else:
        raise ValueError("Must provide either 'bot' or 'config' parameter")
    config_to_dump = convert_keys_to_str(cfg)
    try:
        yaml_str = yaml.dump(
            config_to_dump,
            Dumper=yaml.SafeDumper,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        logger.info(f"Configuration saved successfully to {path}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def create_config():
    config = {
        "discord": {
            "bot_token": prompt_input("Enter your Discord bot token:"),
            "control_channel": prompt_input("Enter the channel ID of the Server Channel where commands should be accepted (Discord): "),
            "stats_channel": prompt_input("Enter the channel ID where Resource Stats / Uptime should be sent (Discord): "),
            "stats_message_id": ""
        },
        "panel": {
            "APIKey": prompt_input("Enter your panel API key: "),
            "servers": {}
        }
    }

    logger.info("Enter server IDs one by one. Leave blank to finish.")
    logger.info("Find the ID in your Game Panel URL → https://games.bisecthosting.com/server/<ID>")
    index = 1
    while True:
        sid = prompt_input("Server ID:")
        if not sid:
            break
        name = prompt_input(f"Name for server {sid}:")
        hide_input = (prompt_input(f"Hide server {sid} from Commands and Stat Tracking? (yes/no) [no]:") or "no").strip().lower()
        hide = hide_input in ("yes", "y")

        config["panel"]["servers"][str(index)] = {
            "name": name,
            "id": sid,
            "hide": hide
        }
        index += 1

    save_config(config=config, path="config.yaml")
    logger.info("Config file 'config.yaml' created.")
    try:
        if platform.system() == "Windows":
            subprocess.call("cls", shell=True)
        else:
            subprocess.call("clear", shell=True)
    except Exception as e:
        logger.warning(f"Failed to clear screen: {e}")

def validate_config(config):
    if not isinstance(config, dict):
        logger.error("Config is not a dictionary.")
        return False

    discord = config.get("discord")
    if not isinstance(discord, dict):
        logger.error("Missing or invalid 'discord' section.")
        return False
    if "bot_token" not in discord or not isinstance(discord["bot_token"], str):
        logger.error("Missing or invalid 'bot_token'.")
        return False
    if "control_channel" not in discord or not isinstance(discord["control_channel"], str):
        logger.error("Missing or invalid 'control_channel'.")
        return False

    panel = config.get("panel")
    if not isinstance(panel, dict):
        logger.error("Missing or invalid 'panel' section.")
        return False
    if "APIKey" not in panel or not isinstance(panel["APIKey"], str):
        logger.error("Missing or invalid 'APIKey'.")
        return False

    servers = panel.get("servers")
    if not isinstance(servers, dict):
        logger.error("Missing or invalid 'servers' dictionary.")
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
    """Load or create config.yaml as needed."""
    config_file = 'config.yaml'
    if not os.path.exists(config_file):
        create_config()
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        return None

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    return config
