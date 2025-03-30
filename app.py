from homeassistant import HomeAssistant
from weather import Weather
from flask import Flask, send_file, make_response
from localconfig import get_config
from logconfig import configure_logging
from io import BytesIO
import drawing

config = get_config()
logger = configure_logging(config)

app = Flask(__name__)

def get_charging_meter_image():
    # Get car status
    ha = HomeAssistant(config)
    car_state_of_charge = ha.get_value('sensor.ix_xdrive50_remaining_battery_percent')
    car_charging_target = ha.get_value('sensor.ix_xdrive50_charging_target')
    img = drawing.create_charging_meter_image(int(car_state_of_charge['state']), int(car_charging_target['state']))
    return img

@app.route('/weather_image_bytes')
def weather_image_bytes():
    img = get_weather_image()
    byte_array = drawing.image_to_packed_bytes(img)
    byte_io = BytesIO(byte_array)

    response = make_response(send_file(byte_io, mimetype='application/octet-stream'))
    response.headers['Content-Disposition'] = 'attachment; filename=bytes.bin'
    return response

def get_weather_image():
    weather = Weather(config)
    temperature = weather.get_temperature()
    humidity = weather.get_humidity()
    conditions_id, conditions_text = weather.get_conditions()
    wind_speed = weather.get_wind_speed()
    img = drawing.create_weather_image(temperature, humidity, conditions_id, conditions_text, wind_speed)
    return img

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/car_battery_bytes')
def image_bytes():
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
    img = get_charging_meter_image()
    # Convert image to byte stream
    img_io = BytesIO()
    img.save(img_io, 'BMP')
    img_io.seek(0)

    # Return image as response
    return send_file(img_io, mimetype='image/bmp')

@app.route('/weather')
def weather():
    img = get_weather_image()
    img_io = BytesIO()
    img.save(img_io, 'BMP')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/bmp')

if __name__ == '__main__':
    app.run(debug=True)