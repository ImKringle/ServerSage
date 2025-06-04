import os
import yaml
import aiohttp
from helper.logger import logger

class APIManager:
    """
    Async helper class for interacting with the BisectHosting API.
    """
    def __init__(self, panel_config, config_path="config.yaml"):
        self.api_key = panel_config.get("APIKey")
        self.base_url = "https://games.bisecthosting.com/api/client"
        self.config_path = config_path
        self.panel_config = panel_config
        self._session = None

    async def _get_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            })
        return self._session

    async def close(self):
        if self._session:
            await self._session.close()

    async def make_request(self, url, method='GET', payload=None):
        session = await self._get_session()
        try:
            if method.upper() == 'GET':
                async with session.get(url) as response:
                    text = await response.text()
                    if response.status not in (200, 204):
                        raise Exception(f"API request failed: {response.status} - {text}")
                    logger.info("API request to %s returned Status Code: %s", url, response.status)
                    if response.content_length == 0:
                        return {"message": "Request completed successfully."}
                    return await response.json()
            elif method.upper() == 'POST':
                async with session.post(url, json=payload) as response:
                    text = await response.text()
                    if response.status not in (200, 204):
                        raise Exception(f"API request failed: {response.status} - {text}")
                    logger.info("API request to %s returned %s: %s", url, response.status, text)
                    if response.content_length == 0:
                        return {"message": "Request completed successfully."}
                    return await response.json()
            else:
                raise ValueError("Unsupported HTTP method.")
        except Exception as e:
            logger.error("Error during API request: %s", e)
            raise

    async def fetch_all_servers(self):
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

        # Remove servers not in API
        to_remove = [key for key, v in config_servers.items() if v.get("id") not in api_server_ids]
        for key in to_remove:
            del config_servers[key]

        # Add new servers from API not in config
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

        # Reindex servers
        new_servers = {}
        sorted_servers = sorted(config_servers.values(), key=lambda s: s["name"].lower())

        for idx, server in enumerate(sorted_servers, 1):
            new_servers[str(idx)] = server

        self.panel_config["servers"] = new_servers
        self._save_config()

        return [{"id": v["id"], "name": v["name"]} for v in new_servers.values()]

    def _save_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r") as file:
            config = yaml.safe_load(file)
        config["panel"] = self.panel_config
        with open(self.config_path, "w") as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)

    async def send_power_action(self, server_id, action):
        url = f"{self.base_url}/servers/{server_id}/power"
        payload = {"signal": action}
        return await self.make_request(url, method='POST', payload=payload)
