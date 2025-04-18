from PIL import Image, ImageDraw, ImageFont
import logging

class LabelValue:
    """Class for creating label-value pair images"""

    def __init__(self, width: int = 390, height: int = 25):
        # Image dimensions
        self.width = width
        self.height = height
        self.image = Image.new('1', (width, height), 1)
        self.draw = ImageDraw.Draw(self.image)
        self.label_font = ImageFont.truetype("LiberationSans-Bold", 18)
        self.value_font = ImageFont.truetype("LiberationSans-Regular", 18)

        # State properties (private)
        self._label = ""
        self._value = ""

    @property
    def label(self) -> str:
        """Get the label text"""
        return self._label

    @label.setter
    def label(self, text: str) -> 'LabelValue':
        """Set the label text"""
        self._label = text
        return self

    @property
    def value(self) -> str:
        """Get the value text"""
        return self._value

    @value.setter
    def value(self, text: str) -> 'LabelValue':
        """Set the value text"""
        self._value = text
        return self

    def update(self, label: str = None, value: str = None) -> 'LabelValue':
        """Update multiple properties at once"""
        if label is not None:
            self.label = label
        if value is not None:
            self.value = value
        return self

    def render(self) -> Image.Image:
        """Render the label-value pair and return the image"""
        logging.info(f'Creating label-value image: {self.label}={self.value}')

        # Clear the image (in case it's being reused)
        self.draw.rectangle([0, 0, self.width, self.height], fill=1)

        # Draw the label on the left
        self.draw.text((0, 0), f'{self.label}: ', font=self.label_font, fill=0)

        # Draw the value on the right
        value_bbox = self.draw.textbbox((0, 0), self.value, font=self.value_font)
        self.draw.text((self.width - value_bbox[2], 0), self.value, font=self.value_font, fill=0)

        return self.image