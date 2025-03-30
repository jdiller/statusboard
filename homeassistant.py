import requests

class HomeAssistant:
    def __init__(self, config):
        self.config = config
        self.ha_url = config['home_assistant']['url']
        self.ha_token = config['home_assistant']['token']

    def get_value(self, entity_id):
        response = requests.get(f'{self.ha_url}/api/states/{entity_id}', headers={'Authorization': f'Bearer {self.ha_token}'})
        return response.json()