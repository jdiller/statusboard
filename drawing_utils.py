from PIL import Image, ImageDraw, ImageFont
from titlecase import titlecase
import logging
from datetime import datetime
from tzlocal import get_localzone
from reminder import Reminder
from drawing import LabelValue, ChargingMeter  # Import from our drawing package

def create_error_image(message: str, width: int = 390, height: int = 240) -> Image.Image:
    logging.info(f'Creating error image with message: {message}')
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("LiberationSans-Regular", 11)
    draw.text((0, 0), message, font=font, fill=0)
    return image

def create_reminders_image(reminders: list[Reminder], width: int = 800, height: int = 240) -> Image.Image:
    PADDING = 3
    logging.info(f'Creating reminders image for {len(reminders)} reminders')
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("LiberationSans-Bold", 22)
    font = ImageFont.truetype("LiberationSans-Regular", 18)
    sub_font = ImageFont.truetype("LiberationSans-Regular", 12)
    draw.text((0, 0), 'Reminders', font=title_font, fill=0)
    offset = title_font.size + PADDING

    for reminder in [x for x in reminders if not x.completed == "Yes"]:
        logging.info(f'Creating reminder image for {reminder.message}')
        draw.text((0, offset), f'- {reminder.message}', font=font, fill=0)
        offset += (font.size + PADDING)
        if reminder.time:
            draw.text((20, offset), reminder.time.strftime('%b %d, %I:%M %p'), font=sub_font, fill=0)
            offset += (sub_font.size + PADDING)
        if reminder.location:
            draw.text((20, offset), reminder.location.replace('\n', ' '), font=sub_font, fill=0)
            offset += (sub_font.size + PADDING)
        offset += (10 + PADDING)
        if offset + font.size > height:
            break
    return image

def create_label_value_image(label: str, value: str, width: int = 390, height: int = 25) -> Image.Image:
    """Legacy wrapper function for compatibility"""
    label_value = LabelValue(width, height)
    return label_value.render(label, value)

def create_charging_meter_image(current_percentage: int, target_percentage: int,
                              charging: bool, plugged_in: bool,
                              label_text: str = "", width: int = 390, height: int = 25) -> Image.Image:
    """Legacy wrapper function for compatibility"""
    meter = ChargingMeter(width, height)
    return meter.render(current_percentage, target_percentage, charging, plugged_in, label_text)

def draw_diagonal_pattern(draw: ImageDraw, pattern_left: int, pattern_right: int,
                          ref_left: int, bar_top: int , bar_height: int, stripe_spacing: int=4,
                          fill: int =0, width: int =1):
    """
    Legacy function kept for backward compatibility.
    Draw a diagonal stripe pattern within the specified boundaries.
    """
    # Calculate the total width needed for diagonal calculation
    total_width = pattern_right - ref_left

    # Calculate diagonal lines across the entire area to ensure they're parallel
    for offset in range(0, total_width + bar_height, stripe_spacing):
        x1 = ref_left + offset
        y1 = bar_top
        x2 = ref_left + offset - bar_height
        y2 = bar_top + bar_height

        # Create a line segment based on the diagonal line
        line_points = []

        # Only draw the portion of the line that's within the pattern area
        if x1 >= pattern_left and x1 <= pattern_right:
            line_points.append((x1, y1))
        if x2 >= pattern_left and x2 <= pattern_right:
            line_points.append((x2, y2))

        # If line crosses the pattern boundaries
        if (x1 < pattern_left and x2 > pattern_left) or (x1 > pattern_left and x2 < pattern_left):
            # Find the y-coordinate where the line crosses the left boundary
            slope = (y2 - y1) / (x2 - x1) if x2 != x1 else 0
            y_at_left = y1 + slope * (pattern_left - x1)
            line_points.append((pattern_left, y_at_left))

        if (x1 < pattern_right and x2 > pattern_right) or (x1 > pattern_right and x2 < pattern_right):
            # Find the y-coordinate where the line crosses the right boundary
            slope = (y2 - y1) / (x2 - x1) if x2 != x1 else 0
            y_at_right = y1 + slope * (pattern_right - x1)
            line_points.append((pattern_right, y_at_right))

        # Sort points by x-coordinate to ensure proper line drawing
        line_points.sort(key=lambda p: p[0])

        # Draw the line if we have at least 2 points
        if len(line_points) >= 2:
            draw.line([line_points[0], line_points[-1]], fill=fill, width=width)

def image_to_packed_bytes(image: Image.Image) -> bytearray:
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

def get_weather_icon(condition_id: int) -> str:
    logging.info(f'Getting weather icon for condition ID: {condition_id}')
    try:
        match(condition_id):
            case x if x in range(200, 233): #thunderstorm
                return chr(0xebdb)
            case x if x in range(300, 322): #drizzle
                return chr(0xf61e)
            case x if x in range(500, 531): #rain
                return chr(0xf176)
            case x if x in range(600, 622): #snow
                return chr(0xe80f)
            case x if x in range(700, 781): #mist
                return chr(0xe818)
            case 800: #clear
                return chr(0xe518)
            case 801 | 802: #partly cloudy
                return chr(0xe42d)
            case 803 | 804: #cloudy
                return chr(0xe42d)
            case _:  # Default case
                logging.warning(f"Unknown condition ID: {condition_id}")
                return chr(0xe81a)  # Default to "clear" icon
    except Exception as e:
        logging.error(f"Error getting weather icon: {e}")
        return "?"  # Fallback to a simple character

def create_weather_image(temperature: float, humidity: float,
                         conditions_id: int, conditions_text: str,
                         wind_speed: float, width: int = 300,
                         height: int = 200) -> Image.Image:
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

    # Draw the humidity
    hum_font = ImageFont.truetype("LiberationSans-Bold", 20)
    hum_text = f'Humidity: {humidity}%'
    hum_bbox = draw.textbbox((0, 0), hum_text, font=hum_font)
    hum_width = hum_bbox[2] - hum_bbox[0]
    hum_x = width - hum_width - 10
    draw.text((hum_x, temp_bbox[3] + padding), hum_text, font=hum_font, fill=0)

    # Draw the weather icon
    try:
        icon = get_weather_icon(conditions_id)
        # Load icon font
        with open("assets/MaterialSymbolsOutlined.ttf", "rb") as f:
            icon_font = ImageFont.truetype(f, 84)

        # Verify icon can be drawn
        text_bbox = draw.textbbox((0, 0), icon, font=icon_font)
        if text_bbox[2] > 0:  # If width > 0, it's probably valid
            draw.text((10, 10), icon, font=icon_font, fill=0)
        else:
            logging.warning(f"Invalid icon for condition {conditions_id}")
            draw.text((10, 10), "?", font=ImageFont.load_default(), fill=0)
    except Exception as e:
        logging.error(f"Error rendering weather icon: {e}")
        draw.text((10, 10), "!", font=ImageFont.load_default(), fill=0)

    # Draw the conditions
    cond_font = ImageFont.truetype("LiberationSans-Bold", 16)
    cond_text = f'{titlecase(conditions_text)}'
    cond_bbox = draw.textbbox((0, 0), cond_text, font=cond_font)
    cond_width = cond_bbox[2] - cond_bbox[0]
    cond_x = width - cond_width - 10
    draw.text((cond_x, temp_bbox[3] + hum_bbox[3] + padding * 2), cond_text, font=cond_font, fill=0)

    wind_font = ImageFont.truetype("LiberationSans-Bold", 16)
    wind_text = f'Wind: {wind_speed} km/h'
    wind_bbox = draw.textbbox((0, 0), wind_text, font=wind_font)
    wind_width = wind_bbox[2] - wind_bbox[0]
    wind_x = width - wind_width - 10
    draw.text((wind_x, temp_bbox[3] + hum_bbox[3] + cond_bbox[3] + padding * 3), wind_text, font=wind_font, fill=0)

    draw.rectangle([(0, height-20), (width, height)], fill=0)
    title_font = ImageFont.truetype("LiberationSans-Bold", 15)
    draw.text((10, height-18), 'Weather', font=title_font, fill=1)
    return image

def create_statusboard_image(weather_img: Image.Image, battery_img: Image.Image, range_img: Image.Image, ups_img: Image.Image,
                             indoor_cameras_armed_img: Image.Image, outdoor_cameras_armed_img: Image.Image,
                             reminders_img: Image.Image, width: int = 800, height: int = 480) -> Image.Image:
    """Combine weather, battery, and reminders images into a single statusboard image."""
    logging.info("Creating statusboard image")
    # Create a new image with white background
    image = Image.new('1', (width, height), 1)

    # Calculate dimensions
    quarter_width = width // 2
    quarter_height = height // 2

    # Create a blank quarter-sized image for the battery section
    battery_section = Image.new('1', (quarter_width, quarter_height), 1)
    #put a title on the battery section
    title_font = ImageFont.truetype("LiberationSans-Bold", 15)
    draw = ImageDraw.Draw(battery_section)
    draw.rectangle([(0, 0), (quarter_width, title_font.size + 4)], fill=0)
    draw.text((2, 2), 'Sensors', font=title_font, fill=255)
    top_offset = title_font.size + 4
    battery_section.paste(battery_img, (0, top_offset))
    top_offset += battery_img.height + 2
    battery_section.paste(range_img, (0, top_offset))
    top_offset += range_img.height + 2
    battery_section.paste(ups_img, (0, top_offset))
    top_offset += ups_img.height + 2
    battery_section.paste(indoor_cameras_armed_img, (0, top_offset))
    top_offset += indoor_cameras_armed_img.height + 2
    battery_section.paste(outdoor_cameras_armed_img, (0, top_offset))

    #Add a last-updated timestamp to the battery section
    last_updated_font = ImageFont.truetype("LiberationSans-Regular", 12)
    last_updated_text = f'Last updated: {datetime.now(get_localzone()).strftime("%b %d, %I:%M %p")}'
    last_updated_bbox = draw.textbbox((0, 0), last_updated_text, font=last_updated_font)
    last_updated_width = last_updated_bbox[2] - last_updated_bbox[0]
    last_updated_x = quarter_width - last_updated_width - 2
    draw.text((last_updated_x, battery_section.height - last_updated_font.size - 2), last_updated_text, font=last_updated_font, fill=0)

    # Resize the weather image to fit its designated area
    weather_img = weather_img.resize((quarter_width, quarter_height))
    reminders_img = reminders_img.resize((width, quarter_height))

    # Paste the images into their respective positions
    image.paste(battery_section, (0, 0))  # Top-left quarter
    image.paste(weather_img, (quarter_width, 0))  # Top-right quarter
    image.paste(reminders_img, (0, quarter_height))  # Bottom half


    # Draw dividing lines
    draw = ImageDraw.Draw(image)

    # Vertical line between top-left and top-right
    draw.line([(quarter_width, 0), (quarter_width, quarter_height)], fill=0)

    # Horizontal line between top and bottom
    draw.line([(0, quarter_height), (width, quarter_height)], fill=0)

    logging.info("Statusboard image created successfully")
    return image

def create_test_image(width: int = 800, height: int = 480) -> Image.Image:
    """Create a test image with all weather icons and battery gauge variants."""
    logging.info("Creating test image with all icons and battery gauges")

    # Create a new image with white background
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)

    # Define overall padding
    padding = 10

    # Load font for labels
    label_font = ImageFont.truetype("LiberationSans-Regular", 12)

    # Section 1: Weather Icons
    # Weather icon condition IDs to test
    weather_conditions = [
        (210, "Thunderstorm"),  # 200-232 range
        (310, "Drizzle"),       # 300-321 range
        (510, "Rain"),          # 500-531 range
        (610, "Snow"),          # 600-622 range
        (710, "Mist"),          # 700-781 range
        (800, "Clear"),         # 800
        (801, "Partly Cloudy"), # 801-802 range
        (803, "Cloudy")         # 803-804 range
    ]

    # Draw weather icons
    icon_size = 64
    icon_spacing = 20
    icon_x = padding
    icon_y = padding

    draw.text((icon_x, icon_y), "Weather Icons:", font=label_font, fill=0)
    icon_y += 25

    try:
        with open("assets/MaterialSymbolsOutlined.ttf", "rb") as f:
            icon_font = ImageFont.truetype(f, icon_size)

        for i, (condition_id, label) in enumerate(weather_conditions):
            # Draw icon
            icon = get_weather_icon(condition_id)
            draw.text((icon_x, icon_y), icon, font=icon_font, fill=0)

            # Draw label below
            text_bbox = draw.textbbox((0, 0), label, font=label_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = icon_x + (icon_size // 2) - (text_width // 2)
            draw.text((text_x, icon_y + icon_size + 5), label, font=label_font, fill=0)

            # Move to next position
            icon_x += icon_size + icon_spacing

            # Wrap to next row if needed
            if icon_x + icon_size > width - padding:
                icon_x = padding
                icon_y += icon_size + 35
    except Exception as e:
        logging.error(f"Error rendering weather icons: {e}")
        draw.text((padding, icon_y), f"Error: {e}", font=label_font, fill=0)

    # Move down to the battery gauge section
    y_offset = icon_y + icon_size + 40

    # Section 2, 3, 4: Battery gauges with different targets
    battery_section_height = (height - y_offset - padding * 2) // 3
    battery_width = 150
    battery_height = 30

    # Create meter instances for reuse
    charging_meter = ChargingMeter(width=battery_width, height=battery_height)

    # Draw three sections with different target percentages
    target_percentages = [50, 80, 100]
    charge_percentages = [10, 30, 50, 80, 100]

    for i, target in enumerate(target_percentages):
        section_y = y_offset + i * battery_section_height

        # Draw section label
        draw.text((padding, section_y), f"Battery Gauges (Target: {target}%):", font=label_font, fill=0)
        section_y += 20
        charging = False
        # Draw battery gauges
        for j, charge in enumerate(charge_percentages):
            gauge_x = padding + j * (battery_width + 10)
            charging = j % 3 == 0
            plugged_in = j % 3 == 1
            # Create battery gauge using the ChargingMeter class
            gauge = charging_meter.render(charge, target, charging, plugged_in)

            # Paste it into the main image
            image.paste(gauge, (gauge_x, section_y))

            # Add charge level label below
            text = f"{charge}%"
            text_bbox = draw.textbbox((0, 0), text, font=label_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = gauge_x + (battery_width // 2) - (text_width // 2)
            draw.text((text_x, section_y + battery_height + 5), text, font=label_font, fill=0)

    return image