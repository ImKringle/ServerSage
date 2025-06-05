import os
import yaml
import aiohttp
import time
from helper.logger import logger

class APIManager:
    """
    Async helper class for interacting with the BisectHosting API.
    """
    def __init__(self, panel_config, config_path="config.yaml"):
        """
        Initialize the APIManager with panel config and optional config file path.
        Sets API key, base URL, and initializes internal state.
        """
        self.api_key = panel_config.get("APIKey")
        self.base_url = "https://games.bisecthosting.com/api/client"
        self.config_path = config_path
        self.panel_config = panel_config
        self._session = None
        self._rate_limited_until = 0

    async def _get_session(self):
        """
        Lazily create and return an aiohttp ClientSession with proper headers.
        Reuses the session if already created.
        """
        if self._session is None:
            self._session = aiohttp.ClientSession(headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            })
        return self._session

    async def close(self):
        """
        Close the aiohttp ClientSession if it exists.
        Should be called when shutting down to clean up resources.
        """
        if self._session:
            await self._session.close()

    async def _handle_response(self, response, url):
        status = response.status
        text = await response.text()

        if status == 429:
            self._rate_limited_until = time.monotonic() + 60
            logger.error("Rate limit hit (429). Blocking API calls for 60 seconds.")
            raise Exception("API rate limit exceeded (429). Pausing requests for 60 seconds.")

        if status not in (200, 204, 201):
            raise Exception(f"API request failed: {status} - {text}")

        logger.debug(f"API request to {url} returned Status Code: {status}")

        # ✅ Handle 204 No Content (successful, but no body)
        if status == 204 or response.content_length == 0:
            return {"message": "Request completed successfully."}

        return await response.json()

    async def make_request(self, url, method='GET', payload=None):
        """
        Make an asynchronous HTTP request to the API.
        Supports GET and POST methods, respects rate limits, and returns JSON data.
        """
        session = await self._get_session()
        now = time.monotonic()
        if now < self._rate_limited_until:
            wait_time = self._rate_limited_until - now
            logger.warning(f"API requests are rate limited. Blocking calls for {wait_time:.1f} more seconds.")
            raise Exception(f"API rate limited. Please wait {wait_time:.1f} seconds before retrying.")
        try:
            if method.upper() == 'GET':
                async with session.get(url) as response:
                    return await self._handle_response(response, url)
            elif method.upper() == 'POST':
                async with session.post(url, json=payload) as response:
                    return await self._handle_response(response, url)
            else:
                raise ValueError("Unsupported HTTP method.")
        except Exception as e:
            logger.error(f"Error during API request: {e}")
            raise

    async def fetch_all_servers(self):
        """
        Fetch the list of servers from the API and synchronize with local config.
        Updates local config with any new or removed servers, and reindexes the list.
        Returns a list of server dicts with 'id' and 'name'.
        """
        url = f"{self.base_url}/"
        response = await self.make_request(url)
        servers = response.get("data", [])

        config_servers = self.panel_config.get("servers", {})

        api_server_ids = set()
        api_servers_map = {}

        for server in servers:
            attributes = server.get("attributes", {})
            server_id = attributes.get("identifier")
            name = attributes.get("name")
            if server_id:
                api_server_ids.add(server_id)
                api_servers_map[server_id] = name

        config_id_to_key = {v["id"]: k for k, v in config_servers.items() if "id" in v}

        to_remove = [key for key, v in config_servers.items() if v.get("id") not in api_server_ids]
        for key in to_remove:
            del config_servers[key]

        for server_id in api_server_ids:
            if server_id not in config_id_to_key:
                config_servers[server_id] = {
                    "name": api_servers_map[server_id],
                    "id": server_id
                }
            else:
                key = config_id_to_key[server_id]
                if config_servers[key]["name"] != api_servers_map[server_id]:
                    config_servers[key]["name"] = api_servers_map[server_id]

        new_servers = {}
        sorted_servers = sorted(config_servers.values(), key=lambda s: s["name"].lower())

        for idx, server in enumerate(sorted_servers, 1):
            new_servers[str(idx)] = server

        self.panel_config["servers"] = new_servers
        self._save_config()

        return [{"id": v["id"], "name": v["name"]} for v in new_servers.values()]

    def _save_config(self):
        """
        Save the updated panel config back to the YAML config file.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r") as file:
            config = yaml.safe_load(file)
        config["panel"] = self.panel_config
        with open(self.config_path, "w") as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)
