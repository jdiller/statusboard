from PIL import Image, ImageDraw, ImageFont
import logging

class LabelValue:
    """Class for creating label-value pair images"""

    def __init__(self, width: int = 390, height: int = 25):
        self.width = width
        self.height = height
        self.image = Image.new('1', (width, height), 1)
        self.draw = ImageDraw.Draw(self.image)
        self.label_font = ImageFont.truetype("LiberationSans-Bold", 18)
        self.value_font = ImageFont.truetype("LiberationSans-Regular", 18)

    def render(self, label: str, value: str) -> Image.Image:
        """Render the label-value pair and return the image"""
        logging.info(f'Creating label-value image: {label}={value}')

        # Clear the image (in case it's being reused)
        self.draw.rectangle([0, 0, self.width, self.height], fill=1)

        # Draw the label on the left
        self.draw.text((0, 0), f'{label}: ', font=self.label_font, fill=0)

        # Draw the value on the right
        value_bbox = self.draw.textbbox((0, 0), value, font=self.value_font)
        self.draw.text((self.width - value_bbox[2], 0), value, font=self.value_font, fill=0)

        return self.image