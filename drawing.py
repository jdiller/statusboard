from PIL import Image, ImageDraw, ImageFont
from titlecase import titlecase
import logging

def create_error_image(message, width=200, height=80):
    logging.info(f'Creating error image with message: {message}')
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("LiberationSans-Regular", 11)
    draw.text((0, 0), message, font=font, fill=0)
    return image

def create_reminders_image(reminders, width=800, height=240):
    PADDING = 3
    logging.info(f'Creating reminders image for {len(reminders)} reminders')
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("LiberationSans-Bold", 22)
    font = ImageFont.truetype("LiberationSans-Regular", 18)
    sub_font = ImageFont.truetype("LiberationSans-Regular", 12)
    draw.text((0, 0), 'Reminders', font=title_font, fill=0)
    offset = title_font.size + PADDING
    for reminder in reminders:
        logging.info(f'Creating reminder image for {reminder.message}')
        draw.text((0, offset), f'- {reminder.message}', font=font, fill=0)
        offset += (font.size + PADDING)
        if reminder.time:
            draw.text((20, offset), reminder.time, font=sub_font, fill=0)
            offset += (sub_font.size + PADDING)
        if reminder.location:
            draw.text((20, offset), reminder.location, font=sub_font, fill=0)
            offset += (sub_font.size + PADDING)
        offset += (10 + PADDING)
        if offset + font.size > height:
            break
    return image

def create_charging_meter_image(current_percentage, target_percentage, width=200, height=80):
    logging.info(f'Creating charging meter image for {current_percentage}% and {target_percentage}%')
    # Create a new image with white background
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)

    # Define dimensions and positions
    padding = 2
    meter_height = 50
    meter_top = height - meter_height - padding
    meter_left = padding
    meter_width = width - padding * 2

    # Draw an empty meter
    draw.rounded_rectangle([meter_left, meter_top, meter_left + meter_width, meter_top + meter_height], 5, outline=0)

    # Calculate positions for current and target percentages
    current_x = int((current_percentage / 100) * meter_width) + meter_left
    target_x = int((target_percentage / 100) * meter_width) + meter_left

    # Draw the filled bar for current percentage
    bar_top = meter_top + padding
    bar_height = meter_height - padding * 2
    draw.rounded_rectangle([meter_left + padding, bar_top, current_x, bar_top + bar_height], 5, fill=0)

    # Add target percentage text above the meter
    font = ImageFont.truetype("LiberationSans-Regular", 11)
    target_text = f'Target = {target_percentage}%'
    text_bbox = draw.textbbox((0, 0), target_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = target_x - (text_width // 2)
    draw.text((text_x, 0), target_text, font=font, fill=0)

    # Draw the target line
    draw.line([(target_x, text_bbox[3] + padding), (target_x, bar_top + bar_height)], fill=0)

    # Add current percentage text inside the bar
    charge_font = ImageFont.truetype("LiberationMono-Regular", 20)
    charge_text = f'{current_percentage}%'
    charge_text_bbox = draw.textbbox((0, 0), charge_text, font=charge_font)
    charge_text_width = charge_text_bbox[2] - charge_text_bbox[0]
    charge_text_height = charge_text_bbox[3] - charge_text_bbox[1]
    charge_text_x = current_x - (charge_text_width // 2) + padding
    charge_text_y = bar_top + (charge_text_height // 2)
    if current_percentage > 30:
        draw.text((charge_text_x // 2, charge_text_y + padding * 2), charge_text, font=charge_font, fill=255)
    else:
        draw.text((meter_width // 2- (charge_text_width // 2) + padding * 2, charge_text_y + padding), charge_text, font=charge_font, fill=0)

    return image

def image_to_packed_bytes(image):
    logging.info('Converting image to packed bytes')
    # Ensure the image is in '1' mode (1-bit pixels, black and white)
    if image.mode != '1':
        image = image.convert('1')

    # Get image dimensions
    width, height = image.size

    # Prepare a byte array
    packed_bytes = bytearray()

    # Iterate over each row
    for y in range(height):
        byte = 0
        bit_count = 0
        for x in range(width):
            # Get the pixel value (0 or 255)
            pixel = image.getpixel((x, y))
            # Set the bit if the pixel is black
            if pixel == 0:
                byte |= (1 << (7 - bit_count))
            bit_count += 1
            # If we've filled a byte, append it to the array
            if bit_count == 8:
                packed_bytes.append(byte)
                byte = 0
                bit_count = 0
        # If there are remaining bits, append the last byte
        if bit_count > 0:
            packed_bytes.append(byte)

    return packed_bytes

def get_weather_icon(condition_id):
    logging.info(f'Getting weather icon for condition ID: {condition_id}')
    match(condition_id):
        case x if x in range(200, 233): #thunderstorm
            return '\uebdb'
        case x if x in range(300, 322): #drizzle
            return '\ue61e'
        case x if x in range(500, 531): #rain
            return '\uf176'
        case x if x in range(600, 622): #snow
            return '\ue2cd'
        case x if x in range(700, 781): #mist
            return '\ue188'
        case 800: #clear
            return '\ue81a'
        case 801 | 802: #partly cloudy
            return '\uf172'
        case 803 | 804: #cloudy
            return '\ue2bd'

def create_weather_image(temperature, humidity, conditions_id, conditions_text, wind_speed, width=300, height=200):
    logging.info(f'Creating weather image with temperature: {temperature}, humidity: {humidity}, conditions: {conditions_text}, wind speed: {wind_speed}')
    padding = 17
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)

    # Draw the temperature
    temp_font = ImageFont.truetype("LiberationSans-Bold", 60)
    temp_text = f'{int(temperature)}°C'
    temp_bbox = draw.textbbox((0, 0), temp_text, font=temp_font)
    temp_width = temp_bbox[2] - temp_bbox[0]
    temp_x = width - temp_width - 10
    draw.text((temp_x, 10), temp_text, font=temp_font, fill=0)

    draw.line([(0, temp_bbox[3] + padding), (width, temp_bbox[3] + padding)], fill=0)

    # Draw the humidity
    hum_font = ImageFont.truetype("LiberationSans-Regular", 20)
    hum_text = f'Humidity: {humidity}%'
    hum_bbox = draw.textbbox((0, 0), hum_text, font=hum_font)
    hum_width = hum_bbox[2] - hum_bbox[0]
    hum_x = width - hum_width - 10
    draw.text((hum_x, temp_bbox[3] + padding), hum_text, font=hum_font, fill=0)

    # Draw the weather icon
    icon = get_weather_icon(conditions_id)
    with open("assets/MaterialIconsOutlined-Regular.otf", "rb") as f:
        icon_font = ImageFont.truetype(f, 64)
        draw.text((10,10), icon, font=icon_font, fill=0)

    # Draw the conditions
    cond_font = ImageFont.truetype("LiberationSans-Regular", 16)
    cond_text = f'{titlecase(conditions_text)}'
    cond_bbox = draw.textbbox((0, 0), cond_text, font=cond_font)
    cond_width = cond_bbox[2] - cond_bbox[0]
    cond_x = width - cond_width - 10
    draw.text((cond_x, temp_bbox[3] + hum_bbox[3] + padding * 2), cond_text, font=cond_font, fill=0)

    wind_font = ImageFont.truetype("LiberationSans-Regular", 16)
    wind_text = f'Wind: {wind_speed} km/h'
    wind_bbox = draw.textbbox((0, 0), wind_text, font=wind_font)
    wind_width = wind_bbox[2] - wind_bbox[0]
    wind_x = width - wind_width - 10
    draw.text((wind_x, temp_bbox[3] + hum_bbox[3] + cond_bbox[3] + padding * 3), wind_text, font=wind_font, fill=0)

    return image