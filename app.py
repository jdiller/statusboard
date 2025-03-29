import requests
from flask import Flask, send_file, make_response
from localconfig import get_config
from logconfig import configure_logging
from io import BytesIO
import drawing

config = get_config()
logger = configure_logging(config)

app = Flask(__name__)

def home_assistant_get_value(entity_id):
    ha_url = config['home_assistant']['url']
    ha_token = config['home_assistant']['token']
    response = requests.get(f'{ha_url}/api/states/{entity_id}', headers={'Authorization': f'Bearer {ha_token}'})
    return response.json()

def get_charging_meter_image():
    # Get car status
    car_state_of_charge = home_assistant_get_value('sensor.ix_xdrive50_remaining_battery_percent')
    car_charging_target = home_assistant_get_value('sensor.ix_xdrive50_charging_target')
    img = drawing.create_charging_meter_image(int(car_state_of_charge['state']), int(car_charging_target['state']))
    return img

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/image_bytes')
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


if __name__ == '__main__':
    app.run(debug=True)