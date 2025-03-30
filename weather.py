import requests

class Weather:
    def __init__(self, config):
        self.config = config
        self.url = config['weather']['url']
        self.api_key = config['weather']['api_key']
        self.lat = config['weather']['lat']
        self.lon = config['weather']['lon']

    def get_weather(self):
        response = requests.get(f'{self.url}?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=metric')
        return response.json()

    def get_temperature(self):
        weather = self.get_weather()
        return weather['main']['temp']

    def get_humidity(self):
        weather = self.get_weather()
        return weather['main']['humidity']

    def get_conditions(self):
        weather = self.get_weather()
        return weather['weather'][0]['id'], weather['weather'][0]['description']

    def get_wind_speed(self):
        weather = self.get_weather()
        return weather['wind']['speed']