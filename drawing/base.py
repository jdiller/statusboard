from abc import ABC, abstractmethod
from PIL import Image, ImageDraw
from . import fonts
import logging

class Panel(ABC):
    """Base class for all dashboard panels"""

    def __init__(self, width: int = 400, height: int = 240):
        self.width = width
        self.height = heigh
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def fetch_data(self):
        """Fetch data from external sources"""
        pass

    @abstractmethod
    def render(self) -> Image.Image:
        """Render the panel to an image"""
        pass

    def create_error_image(self, message: str) -> Image.Image:
        """Create an error image with the given message"""
        self.logger.info(f'Creating error image with message: {message}')
        image = Image.new('1', (self.width, self.height), 1)
        draw = ImageDraw.Draw(image)
        font = fonts.regular(11)
        draw.text((0, 0), message, font=font, fill=0)
        return image

class DataSource(ABC):
    """Base interface for data sources"""

    @abstractmethod
    async def get_data(self):
        """Fetch data from the source"""
        pass