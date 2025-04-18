import drawing_utils
import asyncio
import image_generator
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from localconfig import get_config
from logconfig import configure_logging
from io import BytesIO
from repository import Repository
from reminder import Reminder
from dataclasses import asdict
from datetime import datetime
from typing import Dict, Any

config = get_config()
logger = configure_logging(config)

app = FastAPI()

repo = Repository(config)

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

    combined_img = await image_generator.get_statusboard_image()

    # Run image conversion in a thread
    img_io = BytesIO()
    await asyncio.to_thread(lambda: combined_img.save(img_io, 'BMP'))
    img_io.seek(0)

    # Return image as response
    return StreamingResponse(img_io, media_type="image/bmp")

@app.get("/statusboard_bytes")
async def statusboard_bytes():
    logger.info('Generating statusboard image bytes')

    combined_img = await image_generator.get_statusboard_image()

    # Run byte packing in a thread
    byte_array = await asyncio.to_thread(drawing_utils.image_to_packed_bytes, combined_img)
    byte_io = BytesIO(byte_array)

    # Create a response with the byte array
    headers = {"Content-Disposition": "attachment; filename=statusboard.bin"}
    return StreamingResponse(byte_io, media_type="application/octet-stream", headers=headers)

@app.get('/test_image')
async def test_image_route():
    logger.info('Generating test image with all icons and battery gauges')

    # Generate the test image
    img = await image_generator.get_test_image()

    # Convert image to byte stream in a thread
    img_io = BytesIO()
    await asyncio.to_thread(lambda: img.save(img_io, 'BMP'))
    img_io.seek(0)

    # Return image as response
    return StreamingResponse(img_io, media_type="image/bmp")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)