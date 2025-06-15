from PIL import Image, ImageDraw
from .base import Panel
from . import fonts
from .label_value import LabelValue
from .charging_meter import ChargingMeter
from titlecase import titlecase
import asyncio
from typing import Optional

class SensorsPanel(Panel):
    """Panel displaying all sensor data"""

    def __init__(self, width: int = 400, height: int = 240):
        super().__init__(width, height)
        self.ha = None  # HomeAssistant instance
        self.sensor_data = {}

    async def fetch_data(self):
        """Fetch all sensor data in parallel"""
        if not self.ha:
            self.logger.warning("No HomeAssistant instance configured")
            return

        self.logger.info('Fetching all sensor data')

        # Define all sensors to fetch
        sensors = {
            'car_battery': 'sensor.ix_xdrive50_remaining_battery_percent',
            'car_target': 'sensor.ix_xdrive50_charging_target',
            'car_charging': 'binary_sensor.ix_xdrive50_charging_status_2',
            'car_plugged_in': 'binary_sensor.ix_xdrive50_connection_status',
            'car_range': 'sensor.ix_xdrive50_remaining_range_total',
            'ups_battery': 'sensor.cyberpower_battery_charge',
            'indoor_cameras': 'alarm_control_panel.blink_indoor',
            'outdoor_cameras': 'alarm_control_panel.blink_outdoor',
            'main_temp': 'sensor.picton_temperature',
            'main_humidity': 'sensor.picton_humidity',
            'living_temp': 'sensor.living_room_temperature',
            'living_humidity': 'sensor.living_room_humidity'
        }

        # Fetch all values in parallel
        tasks = {key: self.ha.get_value(sensor) for key, sensor in sensors.items()}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Store results
        for (key, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                self.logger.error(f"Error fetching {key}: {result}")
                self.sensor_data[key] = {'error': str(result)}
            else:
                self.sensor_data[key] = resul

    def render(self) -> Image.Image:
        """Render all sensors in a vertical layout"""
        image = Image.new('1', (self.width, self.height), 1)
        draw = ImageDraw.Draw(image)

        # Title
        title_font = fonts.bold(15)
        draw.rectangle([(0, 0), (self.width, title_font.size + 4)], fill=0)
        draw.text((2, 2), 'Sensors', font=title_font, fill=255)

        y_offset = title_font.size + 4

        # Render each sensor componen
        components = self._create_components()
        for component in components:
            try:
                component_img = component.render()
                image.paste(component_img, (0, y_offset))
                y_offset += component_img.height + 2
            except Exception as e:
                self.logger.error(f"Error rendering component: {e}")

        return image

    def _create_components(self):
        """Create sensor display components based on data"""
        components = []

        # Car battery meter
        if all(key in self.sensor_data for key in ['car_battery', 'car_target', 'car_charging', 'car_plugged_in']):
            if 'error' not in self.sensor_data['car_battery']:
                battery_meter = ChargingMeter(width=self.width)
                battery_meter.current_percentage = int(self.sensor_data['car_battery']['state'])
                battery_meter.target_percentage = int(self.sensor_data['car_target']['state'])
                battery_meter.charging = self.sensor_data['car_charging']['state'] == 'on'
                battery_meter.plugged_in = self.sensor_data['car_plugged_in']['state'] == 'on'
                battery_meter.label_text = "iX Battery: "
                components.append(battery_meter)

        # Car range
        if 'car_range' in self.sensor_data and 'error' not in self.sensor_data['car_range']:
            range_label = LabelValue(width=self.width)
            range_label.label = 'Range'
            range_label.value = f"{self.sensor_data['car_range']['state']} km"
            components.append(range_label)

        # UPS battery meter
        if 'ups_battery' in self.sensor_data and 'error' not in self.sensor_data['ups_battery']:
            ups_meter = ChargingMeter(width=self.width)
            ups_meter.current_percentage = int(self.sensor_data['ups_battery']['state'])
            ups_meter.target_percentage = 100
            ups_meter.charging = False
            ups_meter.plugged_in = True
            ups_meter.label_text = "UPS Battery: "
            components.append(ups_meter)

        # Camera status
        if 'indoor_cameras' in self.sensor_data and 'error' not in self.sensor_data['indoor_cameras']:
            indoor_label = LabelValue(width=self.width)
            indoor_label.label = 'Indoor'
            indoor_label.value = titlecase(self.sensor_data['indoor_cameras']['state'].replace("_", " "))
            components.append(indoor_label)

        if 'outdoor_cameras' in self.sensor_data and 'error' not in self.sensor_data['outdoor_cameras']:
            outdoor_label = LabelValue(width=self.width)
            outdoor_label.label = 'Outdoor'
            outdoor_label.value = titlecase(self.sensor_data['outdoor_cameras']['state'].replace("_", " "))
            components.append(outdoor_label)

        # Thermostats
        if all(key in self.sensor_data for key in ['main_temp', 'main_humidity']):
            if 'error' not in self.sensor_data['main_temp']:
                main_thermo = LabelValue(width=self.width)
                main_thermo.label = 'Main Thermostat'
                main_thermo.value = f"{self.sensor_data['main_temp']['state']}°C, {self.sensor_data['main_humidity']['state']}%"
                components.append(main_thermo)

        if all(key in self.sensor_data for key in ['living_temp', 'living_humidity']):
            if 'error' not in self.sensor_data['living_temp']:
                living_thermo = LabelValue(width=self.width)
                living_thermo.label = 'Learning Thermostat'
                living_thermo.value = f"{self.sensor_data['living_temp']['state']}°C, {self.sensor_data['living_humidity']['state']}%"
                components.append(living_thermo)

        return components