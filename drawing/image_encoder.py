from PIL import Image
import logging

class ImageEncoder:
    """Handles image encoding and format conversion"""

    @staticmethod
    def to_packed_bytes(image: Image.Image) -> bytearray:
        """
        Convert image to packed 1-bit-per-pixel byte array.
        Each byte contains 8 pixels, with the leftmost pixel in the MSB.
        """
        logging.info('Converting image to packed bytes')

        # Ensure the image is in '1' mode (1-bit pixels, black and white)
        if image.mode != '1':
            image = image.convert('1')

        # Get image dimensions
        width, height = image.size

        # Prepare a byte array
        packed_bytes = bytearray()

        # Iterate over each row
        for y in range(height):
            byte = 0
            bit_count = 0
            for x in range(width):
                # Get the pixel value (0 or 255)
                pixel = image.getpixel((x, y))
                # Set the bit if the pixel is white (1 in mode '1')
                if pixel == 1:
                    byte |= (1 << (7 - bit_count))
                bit_count += 1
                # If we've filled a byte, append it to the array
                if bit_count == 8:
                    packed_bytes.append(byte)
                    byte = 0
                    bit_count = 0
            # If there are remaining bits, append the last byte
            if bit_count > 0:
                packed_bytes.append(byte)

        logging.info(f'Converted {width}x{height} image to {len(packed_bytes)} bytes')
        return packed_bytes

    @staticmethod
    def from_packed_bytes(packed_bytes: bytearray, width: int, height: int) -> Image.Image:
        """
        Convert packed 1-bit-per-pixel byte array back to PIL Image.
        Useful for testing and debugging.
        """
        logging.info(f'Converting {len(packed_bytes)} bytes to {width}x{height} image')

        # Create a new 1-bit image
        image = Image.new('1', (width, height), 0)

        byte_index = 0
        bit_index = 0

        for y in range(height):
            for x in range(width):
                if byte_index < len(packed_bytes):
                    # Extract the bi
                    byte = packed_bytes[byte_index]
                    bit = (byte >> (7 - bit_index)) & 1
                    # Set the pixel
                    image.putpixel((x, y), bit)

                    bit_index += 1
                    if bit_index == 8:
                        bit_index = 0
                        byte_index += 1

        return image