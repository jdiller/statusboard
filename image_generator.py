from drawing import QuadrantDashboard, WeatherPanel, SensorsPanel, RemindersPanel, PlanesPanel
from homeassistant import HomeAssistant
from weather import Weather
from localconfig import get_config
from logconfig import configure_logging
from repository import Repository
from flights import Flights
from PIL import Image
import asyncio

config = get_config()
logger = configure_logging(config)

async def get_statusboard_image() -> Image.Image:
    """Generate the complete statusboard image"""
    logger.info('Generating statusboard image')

    # Create dashboard
    dashboard = QuadrantDashboard(800, 480)

    # Create and configure panels
    sensors_panel = SensorsPanel()
    sensors_panel.ha = HomeAssistant(config)

    weather_panel = WeatherPanel()
    weather_panel.weather = Weather(config)

    reminders_panel = RemindersPanel()
    reminders_panel.repository = Repository(config)

    planes_panel = PlanesPanel()
    planes_panel.flights_service = Flights(config)

    # Add panels to dashboard quadrants
    dashboard.set_quadrant(sensors_panel, 'top-left')
    dashboard.set_quadrant(weather_panel, 'top-right')
    dashboard.set_quadrant(reminders_panel, 'bottom-left')
    dashboard.set_quadrant(planes_panel, 'bottom-right')

    # Render the dashboard
    return await dashboard.render()

async def get_test_image() -> Image.Image:
    """Generate a test image with all components and icons"""
    logger.info("Creating test image with component examples")

    # Create a custom test dashboard
    from PIL import Image, ImageDraw
    from drawing import fonts, LabelValue, ChargingMeter, RemindersPanel, WeatherPanel
    from reminder import Reminder
    from datetime import datetime

    # Create base image
    image = Image.new('1', (800, 480), 1)
    draw = ImageDraw.Draw(image)

    # Define overall padding
    padding = 10
    section_spacing = 15

    # Load fonts
    label_font = fonts.regular(12)
    section_font = fonts.bold(14)

    # SECTION 1: Component Examples
    current_y = padding

    draw.text((padding, current_y), "UI COMPONENT EXAMPLES", font=section_font, fill=0)
    current_y += 20

    # LabelValue demo
    label_value = LabelValue(width=350, height=25)
    label_value.label = "LabelValue Demo"
    label_value.value = "Using Properties"
    label_demo = label_value.render()

    draw.text((padding, current_y), "LabelValue Class:", font=label_font, fill=0)
    image.paste(label_demo, (padding, current_y + 15))
    current_y += 45

    # ChargingMeter demo
    charging_meter = ChargingMeter(width=350, height=30)
    charging_meter.current_percentage = 75
    charging_meter.target_percentage = 90
    charging_meter.charging = True
    charging_meter.label_text = "ChargingMeter Demo:"
    meter_demo = charging_meter.render()

    draw.text((padding, current_y), "ChargingMeter Class:", font=label_font, fill=0)
    image.paste(meter_demo, (padding, current_y + 15))
    current_y += 50

    # RemindersPanel demo
    sample_reminders = [
        Reminder(id="1", message="Test reminder", time=datetime.now(), list="default", location="", completed=False),
        Reminder(id="2", message="Another test", time=None, list="default", location="Home", completed=False)
    ]
    reminders_panel = RemindersPanel(width=350, height=100)
    reminders_panel.reminders = sample_reminders
    reminders_demo = reminders_panel.render()

    draw.text((padding, current_y), "RemindersPanel Class:", font=label_font, fill=0)
    image.paste(reminders_demo, (padding, current_y + 15))
    current_y += 120

    # WeatherPanel demo
    weather_panel = WeatherPanel(width=350, height=130)
    weather_panel.temperature = 22.5
    weather_panel.humidity = 45
    weather_panel.conditions_id = 800  # Clear
    weather_panel.conditions_text = "clear sky"
    weather_panel.wind_speed = 3.5
    weather_demo = weather_panel.render()

    draw.text((padding, current_y), "WeatherPanel Class:", font=label_font, fill=0)
    image.paste(weather_demo, (padding, current_y + 15))
    current_y += 150

    # SECTION 2: Weather Icons
    icon_section_x = 800 // 2 + 20
    icon_section_y = padding + 20

    draw.text((icon_section_x, padding), "WEATHER ICON EXAMPLES", font=section_font, fill=0)

    # Weather conditions to test
    weather_conditions = [
        (210, "Thunderstorm"),
        (310, "Drizzle"),
        (510, "Rain"),
        (610, "Snow"),
        (710, "Mist"),
        (800, "Clear"),
        (801, "Partly Cloudy"),
        (803, "Cloudy")
    ]

    # Draw weather icons in a grid
    icon_size = 55
    icon_spacing = 20
    icons_per_row = 4

    try:
        for i, (condition_id, label) in enumerate(weather_conditions):
            # Calculate position
            row = i // icons_per_row
            col = i % icons_per_row

            icon_x = icon_section_x + col * (icon_size + icon_spacing)
            icon_y = icon_section_y + row * (icon_size + 25)

            # Create a small weather panel for the icon
            icon_panel = WeatherPanel(width=icon_size, height=icon_size)
            icon_panel.conditions_id = condition_id

            # Get the icon character
            icon = icon_panel.get_weather_icon()

            # Draw icon
            icon_font = fonts.symbols(icon_size - 10)

            # Create small image for icon
            icon_img = Image.new('1', (icon_size, icon_size), 1)
            icon_draw = ImageDraw.Draw(icon_img)

            # Center the icon
            icon_draw.text((icon_size//2-20, icon_size//2-25), icon, font=icon_font, fill=0)

            # Paste to main image
            image.paste(icon_img, (icon_x, icon_y))

            # Draw label
            text_bbox = draw.textbbox((0, 0), label, font=label_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = icon_x + (icon_size // 2) - (text_width // 2)
            draw.text((text_x, icon_y + icon_size + 2), label, font=label_font, fill=0)

    except Exception as e:
        logger.error(f"Error rendering weather icons: {e}")
        draw.text((icon_section_x, icon_section_y), f"Error: {e}", font=label_font, fill=0)

    # Add dimensions note
    note_text = "Test Image (800x480 pixels)"
    text_bbox = draw.textbbox((0, 0), note_text, font=label_font)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((800 - text_width - padding, 480 - 20), note_text, font=label_font, fill=0)

    return image