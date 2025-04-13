import drawing
from homeassistant import HomeAssistant
from weather import Weather
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
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
        img = drawing.create_error_image(car_state_of_charge.get('error', 'Unknown error'))
    else:
        img = drawing.create_charging_meter_image(int(car_state_of_charge['state']),
                                                  int(car_charging_target['state']),
                                                  car_charging['state'] == 'on',
                                                  car_plugged_in['state'] == 'on',
                                                  label_text="iX Battery: ")
    return img

async def get_range_image():
    logger.info('Fetching car status for range image')
    ha = HomeAssistant(config)
    car_range = await ha.get_value('sensor.ix_xdrive50_remaining_range_total')
    logger.info(f'Car range: {car_range}')
    img = drawing.create_label_value_image('Range', f'{car_range["state"]} km')
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
    img = drawing.create_weather_image(temperature, humidity, conditions_id, conditions_text, wind_speed)
    return img

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

    # Get the individual images in parallel
    weather_img, battery_img, range_img = await asyncio.gather(
        get_weather_image(),
        get_charging_meter_image(),
        get_range_image()
    )

    # Get reminders and create reminders image
    reminders = repo.get_all_reminders()
    undated_reminders = [reminder for reminder in reminders if reminder.time is None or not isinstance(reminder.time, datetime)]
    logger.info(f'Undated reminders: {len(undated_reminders)}')
    dated_reminders = [reminder for reminder in reminders if (reminder.time is not None and isinstance(reminder.time, datetime))]
    logger.info(f'Dated reminders: {len(dated_reminders)}')
    dated_reminders = sorted(dated_reminders, key=lambda x: x.time)

    display_reminders = undated_reminders + dated_reminders
    reminders_img = drawing.create_reminders_image(display_reminders)

    # Combine the images into one statusboard
    combined_img = drawing.create_statusboard_image(weather_img, battery_img, range_img, reminders_img)

    # Convert image to byte stream
    img_io = BytesIO()
    combined_img.save(img_io, 'BMP')
    img_io.seek(0)

    # Return image as response
    return StreamingResponse(img_io, media_type="image/bmp")

@app.get("/statusboard_bytes")
async def statusboard_bytes():
    logger.info('Generating statusboard image bytes')

    # Get the individual images in parallel
    weather_img, battery_img, range_img = await asyncio.gather(
        get_weather_image(),
        get_charging_meter_image(),
        get_range_image()
    )

    # Get reminders and create reminders image
    reminders = repo.get_all_reminders()
    reminders_img = drawing.create_reminders_image(reminders)

    # Combine the images into one statusboard
    combined_img = drawing.create_statusboard_image(weather_img, battery_img, range_img, reminders_img)

    # Convert to packed bytes
    byte_array = drawing.image_to_packed_bytes(combined_img)
    byte_io = BytesIO(byte_array)

    # Create a response with the byte array
    headers = {"Content-Disposition": "attachment; filename=statusboard.bin"}
    return StreamingResponse(byte_io, media_type="application/octet-stream", headers=headers)

@app.get('/test_image')
async def test_image():
    logger.info('Generating test image with all icons and battery gauges')

    # Generate the test image
    img = drawing.create_test_image()

    # Convert image to byte stream
    img_io = BytesIO()
    img.save(img_io, 'BMP')
    img_io.seek(0)

    # Return image as response
    return StreamingResponse(img_io, media_type="image/bmp")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)