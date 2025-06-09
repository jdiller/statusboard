import drawing_utils
import asyncio
import image_generator
from fastapi import FastAPI, HTTPException, Depends, Security, status, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from localconfig import get_config
from logconfig import configure_logging
from io import BytesIO
from repository import Repository
from reminder import Reminder
from dataclasses import asdict
from datetime import datetime
from typing import Dict, Any, Optional

config = get_config()
logger = configure_logging(config)

app = FastAPI()

# Add logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    def redact(self, headers: dict) -> dict:
        return {k: v for k, v in headers.items() if k != "Authorization"}

    async def dispatch(self, request: Request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url}")
        logger.info(f"Headers: {self.redact(dict(request.headers))}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)

# Make HTTPBearer optional for debugging
security = HTTPBearer(auto_error=False)

# Get auth token from config or use a default (you should set this in your config file)
AUTH_TOKEN = config.get("security", "auth_token", fallback="your-secret-token")

def verify_token(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):

    if credentials is None:
        logger.warning("No authorization credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    """Verify that the provided token matches the expected token."""
    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

repo = Repository(config)

@app.get("/")
async def index():
    logger.info('Health check endpoint accessed')
    return {"status": "healthy"}

@app.post("/reminders", dependencies=[Depends(verify_token)])
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

@app.get("/reminders/{reminder_id}", dependencies=[Depends(verify_token)])
async def get_reminder(reminder_id: str):
    logger.info(f'Fetching reminder with ID: {reminder_id}')
    reminder = repo.get_reminder(reminder_id)
    if reminder is None:
        logger.warning(f'Reminder with ID {reminder_id} not found')
        raise HTTPException(status_code=404, detail="Reminder not found")

    return asdict(reminder)

@app.get("/reminders", dependencies=[Depends(verify_token)])
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

@app.get("/statusboard_bytes", dependencies=[Depends(verify_token)])
async def statusboard_bytes():
    logger.info('Generating statusboard image bytes')

    combined_img = await image_generator.get_statusboard_image()

    # Run byte packing in a thread
    byte_array = await asyncio.to_thread(drawing_utils.image_to_packed_bytes, combined_img)
    byte_io = BytesIO(byte_array)

    # Create a response with the byte array
    headers = {"Content-Disposition": "attachment; filename=statusboard.bin"}
    return StreamingResponse(byte_io, media_type="application/octet-stream", headers=headers)

@app.get('/test_image', dependencies=[Depends(verify_token)])
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

@app.get('/debug_pattern')
async def debug_pattern_route():
    logger.info('Generating debug pattern image')

    # Generate the debug pattern
    img = await asyncio.to_thread(drawing_utils.create_debug_pattern_image)

    # Convert image to byte stream in a thread
    img_io = BytesIO()
    await asyncio.to_thread(lambda: img.save(img_io, 'BMP'))
    img_io.seek(0)

    # Return image as response
    return StreamingResponse(img_io, media_type="image/bmp")

@app.get('/debug_pattern_bytes')
async def debug_pattern_bytes_route():
    logger.info('Generating debug pattern bytes')

    # Generate the debug pattern
    img = await asyncio.to_thread(drawing_utils.create_debug_pattern_image)

    # Try different bit packing options
    logger.info('Generating with default bit order (MSB first)')
    byte_array = await asyncio.to_thread(drawing_utils.image_to_packed_bytes, img)
    byte_io = BytesIO(byte_array)

    # Create a response with the byte array
    headers = {"Content-Disposition": "attachment; filename=debug_pattern.bin"}
    return StreamingResponse(byte_io, media_type="application/octet-stream", headers=headers)

@app.get('/debug_pattern_bytes_reversed')
async def debug_pattern_bytes_reversed_route():
    logger.info('Generating debug pattern bytes with reversed bit order')

    # Generate the debug pattern
    img = await asyncio.to_thread(drawing_utils.create_debug_pattern_image)

    # Try reversed bit order
    logger.info('Generating with reversed bit order (LSB first)')
    byte_array = await asyncio.to_thread(drawing_utils.image_to_packed_bytes, img, reverse_bits=True)
    byte_io = BytesIO(byte_array)

    # Create a response with the byte array
    headers = {"Content-Disposition": "attachment; filename=debug_pattern_reversed.bin"}
    return StreamingResponse(byte_io, media_type="application/octet-stream", headers=headers)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)