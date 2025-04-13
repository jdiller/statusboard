import drawing
from homeassistant import HomeAssistant
from weather import Weather
from localconfig import get_config
from logconfig import configure_logging
from repository import Repository
from datetime import datetime
import asyncio
import logging

config = get_config()
logger = configure_logging(config)
repo = Repository(host='redis', port=6379)

async def get_ups_meter_image():
    logger.info('Fetching UPS status for meter image')
    ha = HomeAssistant(config)
    ups_status = await ha.get_value('sensor.cyberpower_battery_charge')
    logger.info(f'UPS status: {ups_status}')
    if 'error' in ups_status:
        logger.error('Error fetching UPS status')
        img = await asyncio.to_thread(drawing.create_error_image, ups_status.get('error', 'Unknown error'))
    else:
        img = await asyncio.to_thread(drawing.create_charging_meter_image, int(ups_status['state']), 100,
                                      False, True, label_text="UPS Battery: ")
    return img

async def get_charging_meter_image():
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
            drawing.create_error_image,
            car_state_of_charge.get('error', 'Unknown error')
        )
    else:
        # Run image creation in a thread
        img = await asyncio.to_thread(
            drawing.create_charging_meter_image,
            int(car_state_of_charge['state']),
            int(car_charging_target['state']),
            car_charging['state'] == 'on',
            car_plugged_in['state'] == 'on',
            label_text="iX Battery: "
        )
    return img

async def get_range_image():
    logger.info('Fetching car status for range image')
    ha = HomeAssistant(config)
    car_range = await ha.get_value('sensor.ix_xdrive50_remaining_range_total')
    logger.info(f'Car range: {car_range}')
    # Run image creation in a thread
    img = await asyncio.to_thread(
        drawing.create_label_value_image,
        'Range',
        f'{car_range["state"]} km'
    )
    return img

async def get_indoor_cameras_armed_image():
    logger.info('Fetching indoor cameras armed status for image')
    ha = HomeAssistant(config)
    indoor_cameras_armed = await ha.get_value('alarm_control_panel.blink_indoor')
    img = await asyncio.to_thread(drawing.create_label_value_image, 'Indoor',
                                  'Armed' if indoor_cameras_armed['state'] == 'on' else 'Disarmed')
    return img

async def get_outdoor_cameras_armed_image():
    logger.info('Fetching outdoor cameras armed status for image')
    ha = HomeAssistant(config)
    outdoor_cameras_armed = await ha.get_value('alarm_control_panel.blink_outdoor')
    img = await asyncio.to_thread(drawing.create_label_value_image, 'Outdoor',
                                  'Armed' if outdoor_cameras_armed['state'] == 'on' else 'Disarmed')
    return img

async def get_weather_image():
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
    # Run image creation in a thread
    img = await asyncio.to_thread(
        drawing.create_weather_image,
        temperature,
        humidity,
        conditions_id,
        conditions_text,
        wind_speed
    )
    return img

async def get_statusboard_image():
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

    # Run image creation in a thread
    reminders_img = await asyncio.to_thread(drawing.create_reminders_image, display_reminders)

    # Run image combination in a thread
    combined_img = await asyncio.to_thread(
        drawing.create_statusboard_image,
        weather_img,
        battery_img,
        range_img,
        indoor_cameras_armed_img,
        outdoor_cameras_armed_img,
        ups_img,
        reminders_img
    )
    return combined_img

async def get_test_image():
    """Get a test image with all icons and battery gauge variants."""
    return await asyncio.to_thread(drawing.create_test_image)