from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def create_charging_meter_image(current_percentage, target_percentage, width=200, height=80):
    current_percentage = 30
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
    font = ImageFont.truetype("Arial", 11)
    target_text = f'Target = {target_percentage}%'
    text_bbox = draw.textbbox((0, 0), target_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = target_x - (text_width // 2)
    draw.text((text_x, 0), target_text, font=font, fill=0)

    # Draw the target line
    draw.line([(target_x, text_bbox[3] + padding), (target_x, bar_top + bar_height)], fill=0)

    # Add current percentage text inside the bar
    charge_font = ImageFont.truetype("Arial Rounded Bold", 20)
    charge_text = f'{current_percentage}%'
    charge_text_bbox = draw.textbbox((0, 0), charge_text, font=charge_font)
    charge_text_width = charge_text_bbox[2] - charge_text_bbox[0]
    charge_text_height = charge_text_bbox[3] - charge_text_bbox[1]
    charge_text_x = current_x - (charge_text_width // 2) + padding
    charge_text_y = bar_top + (charge_text_height // 2)
    if current_percentage > 30:
        draw.text((charge_text_x // 2, charge_text_y + padding), charge_text, font=charge_font, fill=255)
    else:
        draw.text((meter_width // 2- (charge_text_width // 2) + padding, charge_text_y + padding), charge_text, font=charge_font, fill=0)

    return image

def image_to_packed_bytes(image):
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