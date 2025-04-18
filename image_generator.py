import drawing_utils
from homeassistant import HomeAssistant
from weather import Weather
from localconfig import get_config
from logconfig import configure_logging
from repository import Repository
from datetime import datetime
from titlecase import titlecase
import asyncio
from PIL import Image
from drawing import LabelValue, ChargingMeter, RemindersPanel, WeatherPanel

config = get_config()
logger = configure_logging(config)
repo = Repository(config)

async def get_ups_meter_image() -> Image.Image:
    logger.info('Fetching UPS status for meter image')
    ha = HomeAssistant(config)
    ups_status = await ha.get_value('sensor.cyberpower_battery_charge')
    logger.info(f'UPS status: {ups_status}')
    if 'error' in ups_status:
        logger.error('Error fetching UPS status')
        img = await asyncio.to_thread(drawing_utils.create_error_image, ups_status.get('error', 'Unknown error'))
    else:
        # Create ChargingMeter
        def create_meter():
            meter = ChargingMeter()
            meter.current_percentage = int(ups_status['state'])
            meter.target_percentage = 100
            meter.charging = False
            meter.plugged_in = True
            meter.label_text = "UPS Battery: "
            return meter.render()

        img = await asyncio.to_thread(create_meter)
    return img

async def get_charging_meter_image() -> Image.Image:
    logger.info('Fetching car status for charging meter image')
    ha = HomeAssistant(config)
    # Fetch all data in parallel
    car_state_of_charge, car_charging_target, car_charging, car_plugged_in = await asyncio.gather(
        ha.get_value('sensor.ix_xdrive50_remaining_battery_percent'),
        ha.get_value('sensor.ix_xdrive50_charging_target'),
        ha.get_value('binary_sensor.ix_xdrive50_charging_status_2'),
        ha.get_value('binary_sensor.ix_xdrive50_connection_status')
    )

    logger.info(f'Car charging: {car_charging}')
    logger.info(f'Car plugged in: {car_plugged_in}')

    if 'error' in car_state_of_charge or 'error' in car_charging_target:
        logger.error('Error fetching car status')
        # Run image creation in a thread
        img = await asyncio.to_thread(
            drawing_utils.create_error_image,
            car_state_of_charge.get('error', 'Unknown error')
        )
    else:
        # Create ChargingMeter directly
        def create_meter():
            meter = ChargingMeter()
            meter.current_percentage = int(car_state_of_charge['state'])
            meter.target_percentage = int(car_charging_target['state'])
            meter.charging = car_charging['state'] == 'on'
            meter.plugged_in = car_plugged_in['state'] == 'on'
            meter.label_text = "iX Battery: "
            return meter.render()

        img = await asyncio.to_thread(create_meter)
    return img

async def get_range_image() -> Image.Image:
    logger.info('Fetching car status for range image')
    ha = HomeAssistant(config)
    car_range = await ha.get_value('sensor.ix_xdrive50_remaining_range_total')
    logger.info(f'Car range: {car_range}')

    # Create LabelValue directly
    def create_label():
        label_value = LabelValue()
        label_value.label = 'Range'
        label_value.value = f'{car_range["state"]} km'
        return label_value.render()

    img = await asyncio.to_thread(create_label)
    return img

async def get_indoor_cameras_armed_image() -> Image.Image:
    logger.info('Fetching indoor cameras armed status for image')
    ha = HomeAssistant(config)
    indoor_cameras_armed = await ha.get_value('alarm_control_panel.blink_indoor')

    # Create LabelValue directly
    def create_label():
        label_value = LabelValue()
        label_value.label = 'Indoor'
        label_value.value = titlecase(indoor_cameras_armed['state'].replace("_", " "))
        return label_value.render()

    img = await asyncio.to_thread(create_label)
    return img

async def get_outdoor_cameras_armed_image() -> Image.Image:
    logger.info('Fetching outdoor cameras armed status for image')
    ha = HomeAssistant(config)
    outdoor_cameras_armed = await ha.get_value('alarm_control_panel.blink_outdoor')

    # Create LabelValue directly
    def create_label():
        label_value = LabelValue()
        label_value.label = 'Outdoor'
        label_value.value = titlecase(outdoor_cameras_armed['state'].replace("_", " "))
        return label_value.render()

    img = await asyncio.to_thread(create_label)
    return img

async def get_weather_image() -> Image.Image:
    logger.info('Fetching weather data for image')
    weather = Weather(config)
    # Fetch all weather data in parallel
    temperature, humidity, conditions, wind_speed = await asyncio.gather(
        weather.get_temperature(),
        weather.get_humidity(),
        weather.get_conditions(),
        weather.get_wind_speed()
    )
    conditions_id, conditions_text = conditions

    # Create WeatherPanel
    def create_weather_panel():
        panel = WeatherPanel()
        panel.temperature = temperature
        panel.humidity = humidity
        panel.conditions_id = conditions_id
        panel.conditions_text = conditions_text
        panel.wind_speed = wind_speed
        return panel.render()

    img = await asyncio.to_thread(create_weather_panel)
    return img

async def get_statusboard_image() -> Image.Image:
    # Get the individual images in parallel
    weather_img, battery_img, range_img, indoor_cameras_armed_img, outdoor_cameras_armed_img, ups_img = await asyncio.gather(
        get_weather_image(),
        get_charging_meter_image(),
        get_range_image(),
        get_indoor_cameras_armed_image(),
        get_outdoor_cameras_armed_image(),
        get_ups_meter_image()
    )

    # Get reminders and create reminders image
    reminders = repo.get_all_reminders()
    undated_reminders = [reminder for reminder in reminders if reminder.time is None or not isinstance(reminder.time, datetime)]
    logger.info(f'Undated reminders: {len(undated_reminders)}')
    dated_reminders = [reminder for reminder in reminders if (reminder.time is not None and isinstance(reminder.time, datetime))]
    logger.info(f'Dated reminders: {len(dated_reminders)}')
    dated_reminders = sorted(dated_reminders, key=lambda x: x.time)

    display_reminders = undated_reminders + dated_reminders

    # Create RemindersPanel directly
    def create_reminders_panel():
        panel = RemindersPanel()
        panel.reminders = display_reminders
        return panel.render()

    reminders_img = await asyncio.to_thread(create_reminders_panel)

    # Run image combination in a thread
    combined_img = await asyncio.to_thread(
        drawing_utils.create_statusboard_image,
        weather_img,
        battery_img,
        range_img,
        indoor_cameras_armed_img,
        outdoor_cameras_armed_img,
        ups_img,
        reminders_img
    )
    return combined_img

async def get_test_image() -> Image.Image:
    """Get a test image with all icons and battery gauge variants."""
    return await asyncio.to_thread(drawing_utils.create_test_image)