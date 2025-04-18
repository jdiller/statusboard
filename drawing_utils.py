from PIL import Image, ImageDraw, ImageFont
from titlecase import titlecase
import logging
from datetime import datetime
from tzlocal import get_localzone
from reminder import Reminder
from drawing import LabelValue, ChargingMeter, RemindersPanel, WeatherPanel  # Import from our drawing package

def create_error_image(message: str, width: int = 390, height: int = 240) -> Image.Image:
    logging.info(f'Creating error image with message: {message}')
    image = Image.new('1', (width, height), 1)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("LiberationSans-Regular", 11)
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

    # Create a demonstration of LabelValue usage
    label_value = LabelValue(width=300, height=25)
    label_value.label = "LabelValue Demo"
    label_value.value = "Using Properties"
    label_demo = label_value.render()

    # Draw the demo at the top of the image
    draw.text((padding, padding), "LabelValue Class Example:", font=label_font, fill=0)
    image.paste(label_demo, (padding, padding + 20))

    # Create a demonstration of RemindersPanel usage
    sample_reminders = [
        Reminder(id="1", message="Test reminder", time=datetime.now(), list="default", location="", completed=False),
        Reminder(id="2", message="Another test", time=None, list="default", location="Home", completed=False)
    ]
    reminders_panel = RemindersPanel(width=300, height=100)
    reminders_panel.reminders = sample_reminders
    reminders_demo = reminders_panel.render()

    # Draw the reminders demo below the label demo
    draw.text((padding, padding + 50), "RemindersPanel Class Example:", font=label_font, fill=0)
    image.paste(reminders_demo, (padding, padding + 70))

    # Create a demonstration of WeatherPanel usage
    weather_panel = WeatherPanel(width=300, height=100)
    weather_panel.temperature = 22.5
    weather_panel.humidity = 45
    weather_panel.conditions_id = 800  # Clear
    weather_panel.conditions_text = "clear sky"
    weather_panel.wind_speed = 3.5
    weather_demo = weather_panel.render()

    # Draw the weather demo to the right of the reminders demo
    draw.text((padding + 330, padding + 50), "WeatherPanel Class Example:", font=label_font, fill=0)
    image.paste(weather_demo, (padding + 330, padding + 70))

    # Section 1: Weather Icons
    # Adjust y position to account for the demos
    icon_y = padding + 180

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

        # Set the target percentage for this row
        charging_meter.target_percentage = target

        # Draw battery gauges
        for j, charge in enumerate(charge_percentages):
            gauge_x = padding + j * (battery_width + 10)

            # Set all the meter properties using the fluent interface
            charging_meter.current_percentage = charge
            charging_meter.charging = j % 3 == 0
            charging_meter.plugged_in = j % 3 == 1

            # Create battery gauge using the ChargingMeter class
            gauge = charging_meter.render()

            # Paste it into the main image
            image.paste(gauge, (gauge_x, section_y))

            # Add charge level label below
            text = f"{charge}%"
            text_bbox = draw.textbbox((0, 0), text, font=label_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = gauge_x + (battery_width // 2) - (text_width // 2)
            draw.text((text_x, section_y + battery_height + 5), text, font=label_font, fill=0)

    return image