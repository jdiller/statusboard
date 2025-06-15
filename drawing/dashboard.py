from PIL import Image, ImageDraw
from datetime import datetime
from tzlocal import get_localzone
import asyncio
from typing import List, Tuple, Optional
from .base import Panel
from . import fonts
import logging

class Dashboard:
    """Manages the overall dashboard layout and composition"""

    def __init__(self, width: int = 800, height: int = 480):
        self.width = width
        self.height = heigh
        self.panels: List[Tuple[Panel, int, int]] = []
        self.logger = logging.getLogger(__name__)

    def add_panel(self, panel: Panel, x: int, y: int):
        """Add a panel at specific coordinates"""
        self.panels.append((panel, x, y))

    async def render(self) -> Image.Image:
        """Render all panels to create the final dashboard"""
        self.logger.info("Creating dashboard image")

        # Fetch all panel data in parallel
        await asyncio.gather(*[panel.fetch_data() for panel, _, _ in self.panels])

        # Create base image
        image = Image.new('1', (self.width, self.height), 1)

        # Render and place each panel
        for panel, x, y in self.panels:
            try:
                panel_img = panel.render()
                image.paste(panel_img, (x, y))
            except Exception as e:
                self.logger.error(f"Error rendering panel {panel.__class__.__name__}: {e}")
                error_img = panel.create_error_image(f"Error: {str(e)}")
                image.paste(error_img, (x, y))

        # Draw grid lines
        self._draw_grid(image)

        # Add timestamp
        self._add_timestamp(image)

        self.logger.info("Dashboard image created successfully")
        return image

    def _draw_grid(self, image: Image.Image):
        """Draw dividing lines between panels"""
        draw = ImageDraw.Draw(image)
        quarter_width = self.width // 2
        quarter_height = self.height // 2

        # Vertical line between left and righ
        draw.line([(quarter_width, 0), (quarter_width, self.height)], fill=0)

        # Horizontal line between top and bottom
        draw.line([(0, quarter_height), (self.width, quarter_height)], fill=0)

    def _add_timestamp(self, image: Image.Image):
        """Add last-updated timestamp to bottom right"""
        draw = ImageDraw.Draw(image)
        font = fonts.regular(12)
        text = f'Last updated: {datetime.now(get_localzone()).strftime("%b %d, %I:%M %p")}'
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position in bottom right with padding
        x = self.width - text_width - 5
        y = self.height - text_height - 5
        draw.text((x, y), text, font=font, fill=0)

class QuadrantDashboard(Dashboard):
    """A dashboard with a 2x2 grid layout"""

    def set_quadrant(self, panel: Panel, quadrant: str):
        """Set a panel in a specific quadrant (top-left, top-right, bottom-left, bottom-right)"""
        quarter_width = self.width // 2
        quarter_height = self.height // 2

        positions = {
            'top-left': (0, 0),
            'top-right': (quarter_width, 0),
            'bottom-left': (0, quarter_height),
            'bottom-right': (quarter_width, quarter_height)
        }

        if quadrant in positions:
            x, y = positions[quadrant]
            # Ensure panel fits in quadran
            panel.width = quarter_width
            panel.height = quarter_heigh
            self.add_panel(panel, x, y)
        else:
            raise ValueError(f"Invalid quadrant: {quadrant}")