from PIL import Image, ImageDraw, ImageFont
from titlecase import titlecase
import logging
from datetime import datetime
from tzlocal import get_localzone
from reminder import Reminder
from drawing import LabelValue, ChargingMeter, RemindersPanel, WeatherPanel  # Import from our drawing package
from drawing import fonts  # Import our new fonts module

def create_error_image(message: str, width: int = 390, height: int = 240) -> Image.Image:
    logging.info(f'Creating error image with message: {message}')
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)
    font = fonts.regular(11)
    draw.text((0, 0), message, font=font, fill=0)
    return image

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
            # Set the bit if the pixel is white
            if pixel == 255:
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

def create_statusboard_image(weather_img: Image.Image, battery_img: Image.Image, range_img: Image.Image, ups_img: Image.Image,
                             indoor_cameras_armed_img: Image.Image, outdoor_cameras_armed_img: Image.Image,
                             main_thermostat_img: Image.Image, big_room_thermostat_img: Image.Image,
                             reminders_img: Image.Image, flights_img: Image.Image, width: int = 800, height: int = 480) -> Image.Image:
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
    title_font = fonts.bold(15)
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
    top_offset += outdoor_cameras_armed_img.height + 2
    battery_section.paste(main_thermostat_img, (0, top_offset))
    top_offset += main_thermostat_img.height + 2
    battery_section.paste(big_room_thermostat_img, (0, top_offset))

    #Add a last-updated timestamp to the battery section
    last_updated_font = fonts.regular(12)
    last_updated_text = f'Last updated: {datetime.now(get_localzone()).strftime("%b %d, %I:%M %p")}'
    last_updated_bbox = draw.textbbox((0, 0), last_updated_text, font=last_updated_font)
    last_updated_width = last_updated_bbox[2] - last_updated_bbox[0]
    last_updated_x = quarter_width - last_updated_width - 2
    draw.text((last_updated_x, battery_section.height - last_updated_font.size - 2), last_updated_text, font=last_updated_font, fill=0)

    # Resize the weather image to fit its designated area
    #weather_img = weather_img.resize((quarter_width, quarter_height))
    #reminders_img = reminders_img.resize((width, quarter_height))

    # Paste the images into their respective positions
    image.paste(battery_section, (0, 0))  # Top-left quarter
    image.paste(weather_img, (quarter_width, 0))  # Top-right quarter
    image.paste(reminders_img, (0, quarter_height))  # Bottom left quarter
    image.paste(flights_img, (quarter_width, quarter_height))  # Bottom right quarter


    # Draw dividing lines
    draw = ImageDraw.Draw(image)

    # Vertical line between top-left and top-right
    draw.line([(quarter_width, 0), (quarter_width, quarter_height)], fill=0)

    # Horizontal line between top and bottom
    draw.line([(0, quarter_height), (width, quarter_height)], fill=0)

    logging.info("Statusboard image created successfully")
    return image

def create_test_image(width: int = 800, height: int = 480) -> Image.Image:
    """Create a test image with all class examples and battery gauge variants."""
    logging.info("Creating test image with class examples and battery gauges")

    # Create a new image with white background (ensure it's exactly 800x480)
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)

    # Define overall padding
    padding = 10
    section_spacing = 15

    # Load font for labels
    label_font = fonts.regular(12)
    section_font = fonts.bold(14)

    # ========== SECTION 1: Class Demos ==========
    current_y = padding

    draw.text((padding, current_y), "UI COMPONENT EXAMPLES", font=section_font, fill=0)
    current_y += 20

    # Create a demonstration of LabelValue usage
    label_value = LabelValue(width=350, height=25)
    label_value.label = "LabelValue Demo"
    label_value.value = "Using Properties"
    label_demo = label_value.render()

    # Draw the LabelValue demo
    draw.text((padding, current_y), "LabelValue Class:", font=label_font, fill=0)
    image.paste(label_demo, (padding, current_y + 15))
    current_y += 45

    # Create a demonstration of ChargingMeter usage
    charging_meter = ChargingMeter(width=350, height=30)
    charging_meter.current_percentage = 75
    charging_meter.target_percentage = 90
    charging_meter.charging = True
    charging_meter.label_text = "ChargingMeter Demo:"
    meter_demo = charging_meter.render()

    # Draw the ChargingMeter demo
    draw.text((padding, current_y), "ChargingMeter Class:", font=label_font, fill=0)
    image.paste(meter_demo, (padding, current_y + 15))
    current_y += 50

    # Create a demonstration of RemindersPanel usage
    sample_reminders = [
        Reminder(id="1", message="Test reminder", time=datetime.now(), list="default", location="", completed=False),
        Reminder(id="2", message="Another test", time=None, list="default", location="Home", completed=False)
    ]
    reminders_panel = RemindersPanel(width=350, height=100)
    reminders_panel.reminders = sample_reminders
    reminders_demo = reminders_panel.render()

    # Draw the RemindersPanel demo
    draw.text((padding, current_y), "RemindersPanel Class:", font=label_font, fill=0)
    image.paste(reminders_demo, (padding, current_y + 15))
    current_y += 120

    # Create a demonstration of WeatherPanel usage
    weather_panel = WeatherPanel(width=350, height=130)
    weather_panel.temperature = 22.5
    weather_panel.humidity = 45
    weather_panel.conditions_id = 800  # Clear
    weather_panel.conditions_text = "clear sky"
    weather_panel.wind_speed = 3.5
    weather_demo = weather_panel.render()

    # Draw the WeatherPanel demo
    draw.text((padding, current_y), "WeatherPanel Class:", font=label_font, fill=0)
    image.paste(weather_demo, (padding, current_y + 15))
    current_y += 150

    # ========== SECTION 2: Weather Icons ==========
    # Move weather icons to the right side of the screen
    icon_section_x = width // 2 + 20
    icon_section_y = padding + 20

    draw.text((icon_section_x, padding), "WEATHER ICON EXAMPLES", font=section_font, fill=0)

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

    # Draw weather icons in a grid (4 per row)
    icon_size = 55
    icon_spacing = 20
    icons_per_row = 4

    try:
        for i, (condition_id, label) in enumerate(weather_conditions):
            # Calculate position in grid
            row = i // icons_per_row
            col = i % icons_per_row

            icon_x = icon_section_x + col * (icon_size + icon_spacing)
            icon_y = icon_section_y + row * (icon_size + 25)

            # Create a small weather panel just for the icon
            icon_panel = WeatherPanel(width=icon_size, height=icon_size)
            icon_panel.conditions_id = condition_id

            # Get the icon character
            icon = icon_panel.get_weather_icon()

            # Draw directly with MaterialSymbols font
            icon_font = fonts.symbols(icon_size - 10)

            # Create a small image for the icon
            icon_img = Image.new('1', (icon_size, icon_size), 1)
            icon_draw = ImageDraw.Draw(icon_img)

            # Center the icon in the small image
            icon_draw.text((icon_size//2-20, icon_size//2-25), icon, font=icon_font, fill=0)

            # Paste icon to main image
            image.paste(icon_img, (icon_x, icon_y))

            # Draw label below
            text_bbox = draw.textbbox((0, 0), label, font=label_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = icon_x + (icon_size // 2) - (text_width // 2)
            draw.text((text_x, icon_y + icon_size + 2), label, font=label_font, fill=0)

    except Exception as e:
        logging.error(f"Error rendering weather icons: {e}")
        draw.text((icon_section_x, icon_section_y), f"Error: {e}", font=label_font, fill=0)

    # Add a note about the dimensions at the bottom
    note_text = "Test Image (800x480 pixels)"
    text_bbox = draw.textbbox((0, 0), note_text, font=label_font)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((width - text_width - padding, height - 20), note_text, font=label_font, fill=0)

    return image