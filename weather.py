import aiohttp
import asyncio
import logging

class Weather:
    def __init__(self, config):
        self.config = config
        self.url = config['weather']['url']
        self.api_key = config['weather']['api_key']
        self.lat = config['weather']['lat']
        self.lon = config['weather']['lon']
        self.weather_url = f'{self.url}?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=metric'

    async def get_weather(self):
        """Asynchronously fetch weather data."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.weather_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f'Error fetching weather data: {e}')
            return {"error": str(e)}

    async def get_temperature(self):
        """Asynchronously get temperature."""
        weather = await self.get_weather()
        if "error" in weather:
            return 0
        return weather['main']['temp']

    async def get_humidity(self):
        """Asynchronously get humidity."""
        weather = await self.get_weather()
        if "error" in weather:
            return 0
        return weather['main']['humidity']

    async def get_conditions(self):
        """Asynchronously get weather conditions."""
        weather = await self.get_weather()
        if "error" in weather:
            return 800, "Clear"  # Default to clear weather
        return weather['weather'][0]['id'], weather['weather'][0]['description']

    async def get_wind_speed(self):
        """Asynchronously get wind speed."""
        weather = await self.get_weather()
        if "error" in weather:
            return 0
        return weather['wind']['speed']