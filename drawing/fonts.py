from PIL import ImageFont
import logging
import os

# Font file paths
SANS_REGULAR = "LiberationSans-Regular"
SANS_BOLD = "LiberationSans-Bold"
SYMBOLS = "assets/MaterialSymbolsOutlined.ttf"

# Font cache to avoid reloading the same fonts repeatedly
_font_cache = {}

def get_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Get a font with the specified name and size.
    Uses caching to improve performance.

    Args:
        font_name: Name of the font (use constants from this module)
        size: Font size in points

    Returns:
        PIL ImageFont object
    """
    cache_key = f"{font_name}:{size}"

    # Check if font is already in cache
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    try:
        # Material Symbols font needs special handling as it's loaded from a file
        if font_name == SYMBOLS:
            if os.path.exists(font_name):
                font = ImageFont.truetype(font_name, size)
            else:
                logging.error(f"Material Symbols font file not found at {font_name}")
                # Fall back to a regular font
                font = ImageFont.truetype(SANS_REGULAR, size)
        else:
            # Regular fonts can be loaded by name
            font = ImageFont.truetype(font_name, size)

        # Cache the font for future use
        _font_cache[cache_key] = font
        return font

    except Exception as e:
        logging.error(f"Error loading font {font_name} size {size}: {e}")
        # Return a default font as fallback
        return ImageFont.load_default()

# Convenience functions for common fonts
def regular(size: int) -> ImageFont.FreeTypeFont:
    """Get Liberation Sans Regular font at the specified size"""
    return get_font(SANS_REGULAR, size)

def bold(size: int) -> ImageFont.FreeTypeFont:
    """Get Liberation Sans Bold font at the specified size"""
    return get_font(SANS_BOLD, size)

def symbols(size: int) -> ImageFont.FreeTypeFont:
    """Get Material Symbols font at the specified size"""
    return get_font(SYMBOLS, size)