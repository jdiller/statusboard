import drawing
from homeassistant import HomeAssistant
from weather import Weather
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from localconfig import get_config
from logconfig import configure_logging
from io import BytesIO
from repository import Repository
from reminder import Reminder
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio

config = get_config()
logger = configure_logging(config)

app = FastAPI()

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

@app.get("/")
async def index():
    logger.info('Health check endpoint accessed')
    return {"status": "healthy"}

@app.post("/reminders")
async def create_reminder(reminder_data: Dict[str, Any]):
    logger.info('Creating a new reminder')
    required = ['id', 'message', 'time', 'list', 'location', 'completed']
    logger.info(f'Received data: {reminder_data}')
    if not all(key in reminder_data for key in required):
        logger.warning('Invalid data for creating reminder')
        raise HTTPException(status_code=400, detail="Invalid data")

    reminder = Reminder(
        id=reminder_data['id'],
        message=reminder_data['message'],
        time=datetime.fromisoformat(reminder_data['time']) if reminder_data['time'] != '' else None,
        list=reminder_data['list'],
        location=reminder_data['location'],
        completed=reminder_data['completed']
    )
    repo.save_reminder(reminder)
    logger.info('Reminder created successfully')
    return {"message": "Reminder created successfully"}

@app.get("/reminders/{reminder_id}")
async def get_reminder(reminder_id: str):
    logger.info(f'Fetching reminder with ID: {reminder_id}')
    reminder = repo.get_reminder(reminder_id)
    if reminder is None:
        logger.warning(f'Reminder with ID {reminder_id} not found')
        raise HTTPException(status_code=404, detail="Reminder not found")

    return asdict(reminder)

@app.get("/reminders")
async def get_all_reminders():
    logger.info('Fetching all reminders')
    reminders = repo.get_all_reminders()
    reminders_list = [
        asdict(reminder)
        for reminder in reminders
    ]
    return reminders_list

@app.get("/statusboard")
async def statusboard():
    logger.info('Generating statusboard image')

    combined_img = await get_statusboard_image()

    # Run image conversion in a thread
    img_io = BytesIO()
    await asyncio.to_thread(lambda: combined_img.save(img_io, 'BMP'))
    img_io.seek(0)

    # Return image as response
    return StreamingResponse(img_io, media_type="image/bmp")

@app.get("/statusboard_bytes")
async def statusboard_bytes():
    logger.info('Generating statusboard image bytes')

    combined_img = await get_statusboard_image()

    # Run byte packing in a thread
    byte_array = await asyncio.to_thread(drawing.image_to_packed_bytes, combined_img)
    byte_io = BytesIO(byte_array)

    # Create a response with the byte array
    headers = {"Content-Disposition": "attachment; filename=statusboard.bin"}
    return StreamingResponse(byte_io, media_type="application/octet-stream", headers=headers)

@app.get('/test_image')
async def test_image():
    logger.info('Generating test image with all icons and battery gauges')

    # Generate the test image in a thread
    img = await asyncio.to_thread(drawing.create_test_image)

    # Convert image to byte stream in a thread
    img_io = BytesIO()
    await asyncio.to_thread(lambda: img.save(img_io, 'BMP'))
    img_io.seek(0)

    # Return image as response
    return StreamingResponse(img_io, media_type="image/bmp")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)