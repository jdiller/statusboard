from PIL import Image, ImageDraw, ImageFont
import logging
from typing import List
from drawing import fonts
from datetime import time
from flights import Flight

class PlanesPanel:
    """Class for creating and rendering a panel of overhead flights"""

    PADDING = 2

    def __init__(self, width: int = 400, height: int = 240):
        # Image dimensions
        self.width = width
        self.height = height
        self.image = Image.new('1', (width, height), 1)
        self.draw = ImageDraw.Draw(self.image)

        # Font settings
        self.title_font = fonts.bold(22)
        self.font = fonts.regular(18)
        self.sub_font = fonts.regular(12)

        # Content
        self._flights = []

    @property
    def flights(self) -> List[Flight]:
        """Get the flights list"""
        return self._flights

    @flights.setter
    def flights(self, value: List[Flight]) -> 'PlanesPanel':
        """Set the flights list"""
        self._flights = value
        return self

    def render(self) -> Image.Image:
        """Render the flights panel and return the image"""
        logging.info(f'Creating flights image for {len(self.flights)} flights')

        # Clear the image (in case it's being reused)
        self.draw.rectangle([0, 0, self.width, self.height], fill=1)

        # Draw title
        self.draw.text((0, 0), 'Flights', font=self.title_font, fill=0)
        offset = self.title_font.size + self.PADDING

        # Draw each flight
        for flight in self.flights:
            logging.info(f'Creating flight image for {flight.hex}')
            self.draw.text((0, offset), f'- {flight.flight or flight.r}', font=self.font, fill=0)
            offset += (self.font.size + self.PADDING)
            self.draw.text((20, offset), f'{flight.t or "?"} / {flight.alt_baro or "?"}ft / {flight.gs or "?"}kt / {flight.r_dst or "?"}nm', font=self.sub_font, fill=0)
            offset += (self.sub_font.size + self.PADDING)
            if flight.desc or flight.ownOp:
                self.draw.text((20, offset), f'{flight.ownOp or ""} - {flight.desc or ""}', font=self.sub_font, fill=0)
                offset += (self.sub_font.size + self.PADDING)

            # Display route information if available
            if flight.route:
                self.draw.text((20, offset), flight.route, font=self.sub_font, fill=0)
                offset += (self.sub_font.size + self.PADDING)

            offset += (5 + self.PADDING)

            # Stop if we've reached the bottom of the image
            if offset + self.font.size > self.height:
                break

        return self.image
