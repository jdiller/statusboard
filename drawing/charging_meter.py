from PIL import Image, ImageDraw, ImageFont
import logging

class ChargingMeter:
    """Class for creating charging meter images with various styles and configurations"""

    def __init__(self, width: int = 390, height: int = 25):
        self.width = width
        self.height = height
        self.image = Image.new('1', (width, height), 1)
        self.draw = ImageDraw.Draw(self.image)
        self.right_padding = 10
        self.padding = 2
        self.meter_height = height - self.padding * 2
        self.meter_top = self.padding
        self.meter_left = self.padding
        self.meter_width = width - self.padding * 2 - self.right_padding
        self.charge_font = ImageFont.truetype("LiberationMono-Regular", 16)

    def render(self, current_percentage: int, target_percentage: int,
              charging: bool, plugged_in: bool, label_text: str = "") -> Image.Image:
        """Render the charging meter and return the image"""
        logging.info(f'Creating charging meter image for {current_percentage}% and {target_percentage}%')

        # Clear the image (in case it's being reused)
        self.draw.rectangle([0, 0, self.width, self.height], fill=1)

        # Reset meter dimensions
        label_width = 0
        self.meter_left = self.padding
        self.meter_width = self.width - self.padding * 2 - self.right_padding

        if label_text:
            logging.info(f'Adding label: {label_text}')
            # Add a label
            label_font = ImageFont.truetype("LiberationSans-Bold", 18)
            label_bbox = self.draw.textbbox((self.padding, self.padding), label_text, font=label_font)
            label_width = max(label_bbox[2] - label_bbox[0], 125)

            # Calculate vertical center position for the label
            label_height = label_bbox[3] - label_bbox[1]
            meter_center_y = self.meter_top + (self.meter_height / 2)
            label_y = meter_center_y - (label_height / 2)

            # Draw the label text vertically centered relative to the meter
            self.draw.text((self.padding, label_y), label_text, font=label_font, fill=0)

            # Adjust meter dimensions to account for label
            self.meter_left = label_width + self.padding
            self.meter_width = self.width - self.padding * 2 - self.right_padding - label_width

        # Draw an empty meter
        self.draw.rounded_rectangle(
            [self.meter_left, self.meter_top,
             self.meter_left + self.meter_width, self.meter_top + self.meter_height],
            5, outline=0
        )

        # Calculate positions for current and target percentages
        current_x = int((current_percentage / 100) * self.meter_width) + self.meter_left
        target_x = int((target_percentage / 100) * self.meter_width) + self.meter_left

        # Fill the area beyond the target with a diagonal stripe pattern
        bar_top = self.meter_top + self.padding
        bar_height = self.meter_height - self.padding * 2

        # Pattern for the area beyond the target (the portion that will remain empty)
        pattern_left = target_x
        pattern_right = self.meter_left + self.meter_width - self.padding

        # Draw diagonal stripes in the "beyond target" area if target is less than 100%
        if target_percentage < 100:
            self._draw_diagonal_pattern(
                pattern_left, pattern_right,
                ref_left=self.meter_left,
                bar_top=bar_top,
                bar_height=bar_height
            )

        # Draw the filled bar for current percentage (solid black)
        self.draw.rounded_rectangle(
            [self.meter_left + self.padding, bar_top, current_x, bar_top + bar_height],
            5, fill=0
        )

        # Add current percentage text inside the bar
        charge_text = f'{current_percentage}%'
        charge_text_bbox = self.draw.textbbox((0, 0), charge_text, font=self.charge_font)
        charge_text_width = charge_text_bbox[2] - charge_text_bbox[0]
        charge_text_height = charge_text_bbox[3] - charge_text_bbox[1]

        # Center the text horizontally in the meter
        text_x = self.meter_left + (self.meter_width // 2) - (charge_text_width // 2)

        # Precisely center the text vertically in the bar
        meter_center_y = bar_top + (bar_height // 2)
        text_y = meter_center_y - (charge_text_height // 2) - self.padding

        # Choose text color based on charge level
        if current_percentage > 30:
            # White text on black background
            self.draw.text((text_x, text_y), charge_text, font=self.charge_font, fill=255)
        else:
            # Black text on white background
            self.draw.text((text_x, text_y), charge_text, font=self.charge_font, fill=0)

        # Add charging/plugged in indicator
        if charging or plugged_in:
            with open("assets/MaterialSymbolsOutlined.ttf", "rb") as f:
                charging_font = ImageFont.truetype(f, 16)
            charging_glyph = chr(0xec1c) if charging else chr(0xe63c)
            self.draw.text(
                (self.width - self.padding - self.right_padding, bar_top - self.padding),
                charging_glyph, font=charging_font, fill=0
            )

        return self.image

    def _draw_diagonal_pattern(self, pattern_left: int, pattern_right: int,
                             ref_left: int, bar_top: int, bar_height: int,
                             stripe_spacing: int = 4, fill: int = 0, width: int = 1):
        """
        Draw a diagonal stripe pattern within the specified boundaries.

        Args:
            pattern_left: Left boundary of the pattern area
            pattern_right: Right boundary of the pattern area
            ref_left: Left reference point for calculating diagonal lines
            bar_top: Top boundary of the pattern area
            bar_height: Height of the pattern area
            stripe_spacing: Pixels between diagonal stripes
            fill: Color to use for the stripes
            width: Line width for the stripes
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
                self.draw.line([line_points[0], line_points[-1]], fill=fill, width=width)