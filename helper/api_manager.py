import aiohttp
import time
from .logger import logger
from .config_db import SQLiteConfig

class APIManager:
    """
    Async helper class for interacting with the BisectHosting API.
    """
    def __init__(self, panel_config: dict, config: SQLiteConfig):
        self.api_key = panel_config.get("APIKey")
        self.base_url = "https://games.bisecthosting.com/api/client"
        self.panel_config = panel_config
        self.cfg = config
        self._session = None
        self._rate_limited_until = 0

    async def download_file(self, url: str) -> bytes:
        session = await self._get_session()
        now = time.monotonic()
        if now < self._rate_limited_until:
            wait_time = self._rate_limited_until - now
            logger.warning(f"API requests are rate limited. Blocking calls for {wait_time:.1f} more seconds.")
            raise Exception(f"API rate limited. Please wait {wait_time:.1f} seconds before retrying.")

        try:
            async with session.get(url) as response:
                if response.status == 429:
                    self._rate_limited_until = time.monotonic() + 60
                    logger.error("Rate limit hit (429). Blocking API calls for 60 seconds.")
                    raise Exception("API rate limit exceeded (429). Pausing requests for 60 seconds.")

                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"File download failed: {response.status} - {text}")

                logger.debug(f"File downloaded successfully from {url}")
                return await response.read()

        except Exception as e:
            logger.error(f"File download error: {e}")
            raise

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

    async def _handle_response(self, response, url):
        status = response.status
        text = await response.text()

        if status == 429:
            self._rate_limited_until = time.monotonic() + 60
            logger.error("Rate limit hit (429). Blocking API calls for 60 seconds.")
            raise Exception("API rate limit exceeded (429). Pausing requests for 60 seconds.")
        if status == 504:
            self._rate_limited_until = time.monotonic() + 600
            logger.error("CloudFlare Timeout (504). Blocking API calls for 10 minutes.")
            raise Exception("API gateway timeout (504). Pausing requests for 10 minutes.")

        if status not in (200, 204, 201):
            raise Exception(f"API request failed: {status} - {text}")
        if status == 204 or response.content_length == 0:
            return {"message": "Request completed successfully."}
        return await response.json()

    async def make_request(self, url, method='GET', payload=None, params=None, json=None):
        session = await self._get_session()
        now = time.monotonic()
        if now < self._rate_limited_until:
            wait_time = self._rate_limited_until - now
            logger.warning(f"API requests are rate limited. Blocking calls for {wait_time:.1f} more seconds.")
            raise Exception(f"API rate limited. Please wait {wait_time:.1f} seconds before retrying.")
        try:
            method_upper = method.upper()
            if method_upper == 'GET':
                async with session.get(url, params=params) as response:
                    return await self._handle_response(response, url)
            elif method_upper == 'POST':
                async with session.post(url, json=json, data=payload) as response:
                    return await self._handle_response(response, url)
            elif method_upper == 'DELETE':
                async with session.delete(url, params=params) as response:
                    return await self._handle_response(response, url)
            elif method_upper == 'PUT':
                async with session.put(url, json=json, data=payload) as response:
                    return await self._handle_response(response, url)
            else:
                raise ValueError("Unsupported HTTP method.")
        except Exception as e:
            logger.error(f"Error during API request: {e}")
            raise

    async def fetch_all_servers(self):
        """
        Fetch the list of servers from the API and synchronize with local config.
        Returns a list of server dicts with 'id', 'name', and 'hide'.
        """
        url = f"{self.base_url}"
        response = await self.make_request(url)
        servers = response.get("data", [])

        current_servers = {
            k: self.cfg.get_section(k)
            for k in self.cfg.all()
            if k.startswith("server_")
        }

        api_server_ids = set()
        api_servers_map = {}

        for server in servers:
            attributes = server.get("attributes", {})
            server_id = attributes.get("identifier")
            name = attributes.get("name")
            if server_id:
                api_server_ids.add(server_id)
                api_servers_map[server_id] = name

        config_id_to_key = {
            v.get("id"): k for k, v in current_servers.items() if "id" in v
        }

        for key, val in list(current_servers.items()):
            if val.get("id") not in api_server_ids:
                self.cfg.delete_section(key)

        index = 1
        for server_id in sorted(api_server_ids):
            name = api_servers_map[server_id]
            existing_key = config_id_to_key.get(server_id)
            section = existing_key or f"server_{index}"

            while section in current_servers and existing_key is None:
                index += 1
                section = f"server_{index}"

            self.cfg.set(section, "id", server_id)
            self.cfg.set(section, "name", name)
            if self.cfg.get(section, "hide", None) is None:
                self.cfg.set(section, "hide", False)

            index += 1

        if hasattr(self.cfg, "save"):
            self.cfg.save()

        return [
            {
                "id": self.cfg.get(k, "id"),
                "name": self.cfg.get(k, "name"),
                "hide": self.cfg.get(k, "hide", False),
            }
            for k in self.cfg.all()
            if k.startswith("server_")
        ]