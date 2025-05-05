from PIL import Image, ImageDraw, ImageFont
import logging
from typing import List
from reminder import Reminder
from drawing import fonts
from datetime import time
class RemindersPanel:
    """Class for creating and rendering a panel of reminders"""

    PADDING = 2

    def __init__(self, width: int = 400, height: int = 240):
        # Image dimensions
        self.width = width
        self.height = height
        self.image = Image.new('1', (width, height), 1)
        self.draw = ImageDraw.Draw(self.image)

        # Font settings
        self.title_font = fonts.bold(20)
        self.font = fonts.regular(18)
        self.sub_font = fonts.regular(12)

        # Content
        self._reminders = []

    @property
    def reminders(self) -> List[Reminder]:
        """Get the reminders list"""
        return self._reminders

    @reminders.setter
    def reminders(self, value: List[Reminder]) -> 'RemindersPanel':
        """Set the reminders list"""
        self._reminders = value
        return self

    def render(self) -> Image.Image:
        """Render the reminders panel and return the image"""
        logging.info(f'Creating reminders image for {len(self.reminders)} reminders')

        # Clear the image (in case it's being reused)
        self.draw.rectangle([0, 0, self.width, self.height], fill=1)

        # Draw title
        self.draw.text((0, 0), 'Reminders', font=self.title_font, fill=0)
        offset = self.title_font.size + self.PADDING

        # Draw each reminder that's not completed
        for reminder in [x for x in self.reminders if not x.completed == "Yes"]:
            logging.info(f'Creating reminder image for {reminder.message}')
            self.draw.text((0, offset), f'- {reminder.message}', font=self.font, fill=0)
            offset += (self.font.size + self.PADDING)

            if reminder.time:
                if reminder.time.time() == time(0,0,0):
                    fmt = '%b %d'
                else:
                    fmt = '%b %d, %I:%M %p'
                self.draw.text((20, offset), reminder.time.strftime(fmt), font=self.sub_font, fill=0)
                offset += (self.sub_font.size + self.PADDING)

            if reminder.location:
                self.draw.text((20, offset), reminder.location.replace('\n', ' '), font=self.sub_font, fill=0)
                offset += (self.sub_font.size + self.PADDING)

            offset += (10 + self.PADDING)

            # Stop if we've reached the bottom of the image
            if offset + self.font.size > self.height:
                break

        return self.image
