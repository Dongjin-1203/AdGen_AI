"""
Image Processing Utilities
Handles image resizing, format conversion, and aspect ratio adjustments
"""
from PIL import Image
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Instagram image size presets
INSTAGRAM_RATIOS = {
    "4:5": (1080, 1350),  # Portrait (recommended for feed posts)
    "1:1": (1080, 1080),  # Square
    "16:9": (1080, 566),  # Landscape
}


def resize_to_instagram_ratio(
    image: Image.Image,
    ratio: str = "4:5",
    maintain_aspect: bool = True
) -> Image.Image:
    """
    Resize image to Instagram-compatible dimensions
    
    Args:
        image: Input PIL Image
        ratio: Instagram ratio preset ("4:5", "1:1", "16:9")
        maintain_aspect: If True, fit image within target size maintaining aspect ratio
        
    Returns:
        Resized image
    """
    if ratio not in INSTAGRAM_RATIOS:
        raise ValueError(f"Invalid ratio. Choose from: {list(INSTAGRAM_RATIOS.keys())}")
    
    target_size = INSTAGRAM_RATIOS[ratio]
    
    if maintain_aspect:
        # Calculate scaling to fit within target dimensions
        image_aspect = image.width / image.height
        target_aspect = target_size[0] / target_size[1]
        
        if image_aspect > target_aspect:
            # Image is wider than target
            new_width = target_size[0]
            new_height = int(new_width / image_aspect)
        else:
            # Image is taller than target
            new_height = target_size[1]
            new_width = int(new_height * image_aspect)
        
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create canvas with target size
        canvas = Image.new('RGBA', target_size, (0, 0, 0, 0))
        
        # Center the resized image on canvas
        offset_x = (target_size[0] - new_width) // 2
        offset_y = (target_size[1] - new_height) // 2
        canvas.paste(resized, (offset_x, offset_y), resized if resized.mode == 'RGBA' else None)
        
        logger.info(f"Resized image from {image.size} to {target_size} (ratio: {ratio})")
        return canvas
    else:
        # Direct resize (may distort)
        resized = image.resize(target_size, Image.Resampling.LANCZOS)
        logger.info(f"Resized image to {target_size} (ratio: {ratio})")
        return resized


def add_background_color(
    image: Image.Image,
    background_color: Tuple[int, int, int] = (255, 255, 255)
) -> Image.Image:
    """
    Add solid color background to transparent image
    
    Args:
        image: Input PIL Image with alpha channel
        background_color: RGB tuple for background color
        
    Returns:
        Image with solid background
    """
    if image.mode != 'RGBA':
        logger.warning("Image doesn't have alpha channel, returning as-is")
        return image
    
    # Create background
    background = Image.new('RGB', image.size, background_color)
    
    # Composite image onto background
    background.paste(image, (0, 0), image)
    
    logger.info(f"Added background color: {background_color}")
    return background


def save_with_format(
    image: Image.Image,
    output_path: str,
    format: str = "PNG",
    quality: int = 95
) -> None:
    """
    Save image with specified format and quality
    
    Args:
        image: Input PIL Image
        output_path: Output file path
        format: Image format (PNG, JPEG, etc.)
        quality: Quality for JPEG compression (1-100)
    """
    if format.upper() == "JPEG" and image.mode == 'RGBA':
        # Convert RGBA to RGB for JPEG
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        rgb_image.paste(image, (0, 0), image)
        rgb_image.save(output_path, format=format, quality=quality, optimize=True)
        logger.info(f"Saved JPEG image (converted from RGBA): {output_path}")
    else:
        image.save(output_path, format=format, quality=quality if format.upper() == 'JPEG' else None)
        logger.info(f"Saved {format} image: {output_path}")


def get_image_info(image: Image.Image) -> dict:
    """
    Get image metadata
    
    Args:
        image: Input PIL Image
        
    Returns:
        Dictionary with image information
    """
    return {
        "size": image.size,
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format,
        "aspect_ratio": round(image.width / image.height, 2)
    }