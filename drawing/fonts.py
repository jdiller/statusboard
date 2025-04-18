from PIL import ImageFont
import logging
import os

# Font file paths
NOTO_SANS_REGULAR = "assets/fonts/NotoSans-Regular.ttf"
NOTO_SANS_MEDIUM = "assets/fonts/NotoSans-Medium.ttf"
SYMBOLS = "assets/fonts/MaterialSymbolsOutlined.ttf"

# Fallback fonts if Noto Sans isn't available
FALLBACK_REGULAR = "LiberationSans-Regular"
FALLBACK_MEDIUM = "LiberationSans-Bold"  # Using bold as fallback for medium

# Font cache to avoid reloading the same fonts repeatedly
_font_cache = {}

def get_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Get a font with the specified name and size.
    Uses caching to improve performance.

    Args:
        font_path: Path to the font file
        size: Font size in points

    Returns:
        PIL ImageFont object
    """
    cache_key = f"{font_path}:{size}"

    # Check if font is already in cache
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    try:
        # First try to load from file (Noto Sans or Material Symbols)
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, size)
            logging.info(f"Loaded font from {font_path} at size {size}")
        else:
            # If file doesn't exist, try to use fallback
            if font_path == NOTO_SANS_REGULAR:
                fallback = FALLBACK_REGULAR
            elif font_path == NOTO_SANS_MEDIUM:
                fallback = FALLBACK_MEDIUM
            else:
                fallback = FALLBACK_REGULAR

            logging.warning(f"Font file not found at {font_path}, falling back to {fallback}")
            font = ImageFont.truetype(fallback, size)

        # Cache the font for future use
        _font_cache[cache_key] = font
        return font

    except Exception as e:
        logging.error(f"Error loading font {font_path} size {size}: {e}")
        # Return a default font as fallback
        return ImageFont.load_default()

# Convenience functions for common fonts
def regular(size: int) -> ImageFont.FreeTypeFont:
    """Get Noto Sans Regular font at the specified size"""
    return get_font(NOTO_SANS_REGULAR, size)

def bold(size: int) -> ImageFont.FreeTypeFont:
    """Get Noto Sans Medium font at the specified size (replaces bold for better e-ink readability)"""
    return get_font(NOTO_SANS_MEDIUM, size)

def symbols(size: int) -> ImageFont.FreeTypeFont:
    """Get Material Symbols font at the specified size"""
    return get_font(SYMBOLS, size)