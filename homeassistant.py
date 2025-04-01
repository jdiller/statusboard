import requests

class HomeAssistant:
    def __init__(self, config):
        self.config = config
        self.ha_url = config['home_assistant']['url']
        self.ha_token = config['home_assistant']['token']

    def get_value(self, entity_id):
        try:
            response = requests.get(
                f'{self.ha_url}/api/states/{entity_id}',
                headers={'Authorization': f'Bearer {self.ha_token}'},
                timeout=5
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Log the error
            return {"error": "HTTP error occurred"}
        except requests.exceptions.ConnectionError as conn_err:
            print(f'Connection error occurred: {conn_err}')  # Log the error
            return {"error": "Connection error occurred"}
        except requests.exceptions.Timeout as timeout_err:
            print(f'Timeout error occurred: {timeout_err}')  # Log the error
            return {"error": "Timeout error occurred"}
        except requests.exceptions.RequestException as req_err:
            print(f'An error occurred: {req_err}')  # Log the error
            return {"error": "An unknownerror occurred"}