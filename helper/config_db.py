import os
import sqlite3
import json
import platform
import subprocess
from helper.logger import logger
from helper.input_handler import prompt_input

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "serversage_config.db")

class SQLiteConfig:
    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                section TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                PRIMARY KEY (section, key)
            )
        """)

    def set(self, section: str, key: str, value):
        value_str = json.dumps(value)
        self.conn.execute(
            "INSERT OR REPLACE INTO config (section, key, value) VALUES (?, ?, ?)",
            (section, key, value_str)
        )
        self.conn.commit()

    def get(self, section: str, key: str, default=None):
        cur = self.conn.execute(
            "SELECT value FROM config WHERE section = ? AND key = ?",
            (section, key)
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else default

    def get_section(self, section: str):
        cur = self.conn.execute(
            "SELECT key, value FROM config WHERE section = ? ORDER BY key",
            (section,)
        )
        return {key: json.loads(val) for key, val in cur.fetchall()}

    def all(self):
        cur = self.conn.execute("SELECT section, key, value FROM config ORDER BY section, key")
        output = {}
        for section, key, value in cur.fetchall():
            if section not in output:
                output[section] = {}
            output[section][key] = json.loads(value)
        return output

    def delete_section(self, section: str):
        """Delete entire section and commit immediately."""
        self.conn.execute("DELETE FROM config WHERE section = ?", (section,))
        self.conn.commit()

    def save(self):
        """Commit any pending transactions."""
        self.conn.commit()

    def close(self):
        """Commit and close the DB connection."""
        self.conn.commit()
        self.conn.close()

    def all_sections(self):
        """Return a list of all distinct section names in the config."""
        cur = self.conn.execute("SELECT DISTINCT section FROM config")
        return [row[0] for row in cur.fetchall()]

def create_config():
    logger.info("Config Creation has Started!")
    cfg = SQLiteConfig()
    do_resource_loop = (prompt_input("Enable Resource Stats Loop? (yes/no) [yes]:") or "yes").strip().lower() in ("yes", "y")
    do_announcement_loop = (prompt_input("Enable Announcement Loop? (yes/no) [yes]:") or "yes").strip().lower() in ("yes", "y")
    cfg.set("bot", "doResourceLoop", do_resource_loop)
    cfg.set("bot", "doAnnouncementLoop", do_announcement_loop)
    cfg.set("discord", "bot_token", prompt_input("Enter your Discord bot token:"))
    cfg.set("discord", "control_channel", prompt_input("Enter the ID of the Channel where commands should be accepted:"))
    cfg.set("discord", "guild_id", prompt_input("Enter the Discord Guild ID (Server ID) for slash command syncing:"))
    if do_resource_loop:
        cfg.set("discord", "stats_channel", prompt_input("Enter the channel ID for resource stats:"))
        cfg.set("discord", "stats_message_id", "")
    else:
        cfg.set("discord", "stats_channel", None)
        cfg.set("discord", "stats_message_id", None)
    if do_announcement_loop:
        cfg.set("discord", "announcement_channel", prompt_input("Enter the announcement channel ID:"))
    else:
        cfg.set("discord", "announcement_channel", None)
    cfg.set("panel", "APIKey", prompt_input("Enter your panel API key:"))
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
        server_section = f"server_{index}"
        cfg.set(server_section, "id", sid)
        cfg.set(server_section, "name", name)
        cfg.set(server_section, "hide", hide)
        index += 1

    logger.info("Configuration saved to config.db")
    try:
        if platform.system() == "Windows":
            subprocess.call("cls", shell=True)
        else:
            subprocess.call("clear", shell=True)
    except Exception as e:
        logger.warning(f"Failed to clear screen: {e}")

def validate_config(cfg: SQLiteConfig):
    try:
        discord = cfg.get_section("discord")
        if not discord.get("bot_token") or not isinstance(discord["bot_token"], str):
            raise ValueError("Missing or invalid 'bot_token'")
        if not discord.get("control_channel") or not isinstance(discord["control_channel"], str):
            raise ValueError("Missing or invalid 'control_channel'")
        panel = cfg.get_section("panel")
        if not panel.get("APIKey") or not isinstance(panel["APIKey"], str):
            raise ValueError("Missing or invalid 'APIKey'")
        server_keys = [k for k in cfg.all_sections() if k.startswith("server_")]
        if not server_keys:
            raise ValueError("No servers configured.")
        for key in server_keys:
            server = cfg.get_section(key)
            if not server.get("name") or not server.get("id"):
                raise ValueError(f"Incomplete server config for {key}")
        logger.info("Config validated successfully.")
        return True
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        return False

def load_config():
    if not os.path.exists(DB_PATH):
        create_config()

    cfg = SQLiteConfig(DB_PATH)
    if validate_config(cfg):
        return cfg
    return None
