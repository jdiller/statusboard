import drawing
from homeassistant import HomeAssistant
from weather import Weather
from flask import Flask, send_file, make_response, request, jsonify
from localconfig import get_config
from logconfig import configure_logging
from io import BytesIO
from repository import Repository
from reminder import Reminder
from dataclasses import asdict
import json
import logging
from datetime import datetime

config = get_config()
logger = configure_logging(config)

app = Flask(__name__)

repo = Repository(host='redis', port=6379)

def get_charging_meter_image():
    logger.info('Fetching car status for charging meter image')
    ha = HomeAssistant(config)
    car_state_of_charge = ha.get_value('sensor.ix_xdrive50_remaining_battery_percent')
    car_charging_target = ha.get_value('sensor.ix_xdrive50_charging_target')
    if 'error' in car_state_of_charge or 'error' in car_charging_target:
        logger.error('Error fetching car status')
        img = drawing.create_error_image(car_state_of_charge.get('error', 'Unknown error'))
    else:
        img = drawing.create_charging_meter_image(int(car_state_of_charge['state']), int(car_charging_target['state']))
    return img

@app.route('/weather_image_bytes')
def weather_image_bytes():
    logger.info('Generating weather image bytes')
    img = get_weather_image()
    byte_array = drawing.image_to_packed_bytes(img)
    byte_io = BytesIO(byte_array)

    response = make_response(send_file(byte_io, mimetype='application/octet-stream'))
    response.headers['Content-Disposition'] = 'attachment; filename=bytes.bin'
    return response

def get_weather_image():
    logger.info('Fetching weather data for image')
    weather = Weather(config)
    temperature = weather.get_temperature()
    humidity = weather.get_humidity()
    conditions_id, conditions_text = weather.get_conditions()
    wind_speed = weather.get_wind_speed()
    img = drawing.create_weather_image(temperature, humidity, conditions_id, conditions_text, wind_speed)
    return img

@app.route('/car_battery_bytes')
def image_bytes():
    logger.info('Generating car battery image bytes')
    img = get_charging_meter_image()
    byte_array = drawing.image_to_packed_bytes(img)

    # Create a BytesIO object from the byte array
    byte_io = BytesIO(byte_array)

    # Create a response with the byte array
    response = make_response(send_file(byte_io, mimetype='application/octet-stream'))
    response.headers['Content-Disposition'] = 'attachment; filename=bytes.bin'
    return response

@app.route('/')
def index():
    logger.info('Health check endpoint accessed')
    return jsonify({'status': 'healthy'})

@app.route('/car_battery')
def car_battery():
    logger.info('Generating car battery image')
    img = get_charging_meter_image()
    img_io = BytesIO()
    img.save(img_io, 'BMP')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/bmp')

@app.route('/weather')
def weather():
    logger.info('Generating weather image')
    img = get_weather_image()
    img_io = BytesIO()
    img.save(img_io, 'BMP')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/bmp')

@app.route('/reminders_image')
def reminders_image():
    logger.info('Generating reminders image')
    reminders = repo.get_all_reminders()
    img = drawing.create_reminders_image(reminders)
    img_io = BytesIO()
    img.save(img_io, 'BMP')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/bmp')

@app.route('/reminders', methods=['POST'])
def create_reminder():
    logger.info('Creating a new reminder')
    data = request.get_json()
    required = ['id', 'message', 'time', 'list', 'location', 'completed']
    logger.info(f'Received data: {data}')
    if not all(key in data for key in required):
        logger.warning('Invalid data for creating reminder')
        return jsonify({'error': 'Invalid data'}), 400

    reminder = Reminder(
        id=data['id'],
        message=data['message'],
        time=datetime.fromisoformat(data['time']) if data['time'] != '' else None,
        list=data['list'],
        location=data['location'],
        completed=data['completed']
    )
    repo.save_reminder(reminder)
    logger.info('Reminder created successfully')
    return jsonify({'message': 'Reminder created successfully'}), 201

@app.route('/reminders/<reminder_id>', methods=['GET'])
def get_reminder(reminder_id):
    logger.info(f'Fetching reminder with ID: {reminder_id}')
    reminder = repo.get_reminder(reminder_id)
    if reminder is None:
        logger.warning(f'Reminder with ID {reminder_id} not found')
        return jsonify({'error': 'Reminder not found'}), 404

    return jsonify(asdict(reminder)), 200

@app.route('/reminders', methods=['GET'])
def get_all_reminders():
    logger.info('Fetching all reminders')
    reminders = repo.get_all_reminders()
    reminders_list = [
        asdict(reminder)
        for reminder in reminders
    ]
    return jsonify(reminders_list), 200

if __name__ == '__main__':
    app.run(debug=True)