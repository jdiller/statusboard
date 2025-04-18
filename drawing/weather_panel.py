from PIL import Image, ImageDraw, ImageFont
import logging
from titlecase import titlecase
from drawing import fonts

class WeatherPanel:
    """Class for creating and rendering a weather information panel"""

    def __init__(self, width: int = 300, height: int = 200):
        # Image dimensions
        self.width = width
        self.height = height
        self.image = Image.new('1', (width, height), 1)
        self.draw = ImageDraw.Draw(self.image)

        # Font settings
        self.temp_font = fonts.bold(60)
        self.hum_font = fonts.bold(20)
        self.cond_font = fonts.bold(16)
        self.wind_font = fonts.bold(16)
        self.title_font = fonts.bold(15)

        # Content properties
        self._temperature = 0.0
        self._humidity = 0.0
        self._conditions_id = 800  # Default to "clear"
        self._conditions_text = "Clear"
        self._wind_speed = 0.0

        # Layout settings
        self.padding = 17

    @property
    def temperature(self) -> float:
        """Get the temperature value"""
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> 'WeatherPanel':
        """Set the temperature value"""
        self._temperature = value
        return self

    @property
    def humidity(self) -> float:
        """Get the humidity percentage"""
        return self._humidity

    @humidity.setter
    def humidity(self, value: float) -> 'WeatherPanel':
        """Set the humidity percentage"""
        self._humidity = value
        return self

    @property
    def conditions_id(self) -> int:
        """Get the weather condition ID"""
        return self._conditions_id

    @conditions_id.setter
    def conditions_id(self, value: int) -> 'WeatherPanel':
        """Set the weather condition ID"""
        self._conditions_id = value
        return self

    @property
    def conditions_text(self) -> str:
        """Get the weather condition text"""
        return self._conditions_text

    @conditions_text.setter
    def conditions_text(self, value: str) -> 'WeatherPanel':
        """Set the weather condition text"""
        self._conditions_text = value
        return self

    @property
    def wind_speed(self) -> float:
        """Get the wind speed"""
        return self._wind_speed

    @wind_speed.setter
    def wind_speed(self, value: float) -> 'WeatherPanel':
        """Set the wind speed"""
        self._wind_speed = value
        return self

    def get_weather_icon(self) -> str:
        """Get an icon character based on the weather condition ID"""
        logging.info(f'Getting weather icon for condition ID: {self.conditions_id}')
        try:
            match(self.conditions_id):
                case x if x in range(200, 233): #thunderstorm
                    return chr(0xebdb)
                case x if x in range(300, 322): #drizzle
                    return chr(0xf61e)
                case x if x in range(500, 531): #rain
                    return chr(0xf176)
                case x if x in range(600, 622): #snow
                    return chr(0xe80f)
                case x if x in range(700, 781): #mist
                    return chr(0xe818)
                case 800: #clear
                    return chr(0xe518)
                case 801 | 802: #partly cloudy
                    return chr(0xe42d)
                case 803 | 804: #cloudy
                    return chr(0xe42d)
                case _:  # Default case
                    logging.warning(f"Unknown condition ID: {self.conditions_id}")
                    return chr(0xe81a)  # Default to "clear" icon
        except Exception as e:
            logging.error(f"Error getting weather icon: {e}")
            return "?"  # Fallback to a simple character

    def render(self) -> Image.Image:
        """Render the weather panel and return the image"""
        logging.info(f'Creating weather image with temperature: {self.temperature}, humidity: {self.humidity}, '
                     f'conditions: {self.conditions_text}, wind speed: {self.wind_speed}')

        # Clear the image (in case it's being reused)
        self.draw.rectangle([0, 0, self.width, self.height], fill=1)

        # Draw the temperature
        temp_text = f'{int(self.temperature)}°C'
        temp_bbox = self.draw.textbbox((0, 0), temp_text, font=self.temp_font)
        temp_width = temp_bbox[2] - temp_bbox[0]
        temp_x = self.width - temp_width - 10
        self.draw.text((temp_x, 10), temp_text, font=self.temp_font, fill=0)

        # Draw the humidity
        hum_text = f'Humidity: {self.humidity}%'
        hum_bbox = self.draw.textbbox((0, 0), hum_text, font=self.hum_font)
        hum_width = hum_bbox[2] - hum_bbox[0]
        hum_x = self.width - hum_width - 10
        self.draw.text((hum_x, temp_bbox[3] + self.padding), hum_text, font=self.hum_font, fill=0)

        # Draw the weather icon
        try:
            icon = self.get_weather_icon()
            # Load icon font
            icon_font = fonts.material_symbols(84)

            # Verify icon can be drawn
            text_bbox = self.draw.textbbox((0, 0), icon, font=icon_font)
            if text_bbox[2] > 0:  # If width > 0, it's probably valid
                self.draw.text((10, 10), icon, font=icon_font, fill=0)
            else:
                logging.warning(f"Invalid icon for condition {self.conditions_id}")
                self.draw.text((10, 10), "?", font=ImageFont.load_default(), fill=0)
        except Exception as e:
            logging.error(f"Error rendering weather icon: {e}")
            self.draw.text((10, 10), "!", font=ImageFont.load_default(), fill=0)

        # Draw the conditions
        cond_text = f'{titlecase(self.conditions_text)}'
        cond_bbox = self.draw.textbbox((0, 0), cond_text, font=self.cond_font)
        cond_width = cond_bbox[2] - cond_bbox[0]
        cond_x = self.width - cond_width - 10
        self.draw.text((cond_x, temp_bbox[3] + hum_bbox[3] + self.padding * 2), cond_text, font=self.cond_font, fill=0)

        # Draw the wind speed
        wind_text = f'Wind: {self.wind_speed} km/h'
        wind_bbox = self.draw.textbbox((0, 0), wind_text, font=self.wind_font)
        wind_width = wind_bbox[2] - wind_bbox[0]
        wind_x = self.width - wind_width - 10
        self.draw.text((wind_x, temp_bbox[3] + hum_bbox[3] + cond_bbox[3] + self.padding * 3),
                      wind_text, font=self.wind_font, fill=0)

        # Draw the title bar at the bottom
        self.draw.rectangle([(0, self.height-20), (self.width, self.height)], fill=0)
        self.draw.text((10, self.height-18), 'Weather', font=self.title_font, fill=1)

        return self.image