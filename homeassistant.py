import aiohttp
import asyncio
import logging

class HomeAssistant:
    def __init__(self, config):
        self.config = config
        self.ha_url = config['home_assistant']['url']
        self.ha_token = config['home_assistant']['token']
        self.headers = {'Authorization': f'Bearer {self.ha_token}'}

    async def get_value(self, entity_id):
        """Asynchronously fetch a value from Home Assistant."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.ha_url}/api/states/{entity_id}',
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')
            return {"error": f"HTTP error occurred: {http_err}"}
        except aiohttp.ClientConnectorError as conn_err:
            logging.error(f'Connection error occurred: {conn_err}')
            return {"error": f"Connection error occurred: {conn_err}"}
        except asyncio.TimeoutError as timeout_err:
            logging.error(f'Timeout error occurred: {timeout_err}')
            return {"error": "Timeout error occurred"}
        except Exception as req_err:
            logging.error(f'An error occurred: {req_err}')
            return {"error": f"An unknown error occurred: {req_err}"}