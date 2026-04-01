"""
Wrinkle Removal Module
Remove wrinkles from fabric using image processing
"""
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class WrinkleRemover:
    """Remove wrinkles and creases from fabric images"""

    def __init__(self):
        """Initialize wrinkle remover"""
        logger.info("WrinkleRemover initialized")

    def remove_wrinkles(self, image: Image.Image, strength: float = 0.5) -> Image.Image:
        """
        Remove wrinkles from fabric image

        Args:
            image: Input PIL Image (RGB or RGBA)
            strength: Removal strength (0.0 to 1.0)

        Returns:
            Image with reduced wrinkles
        """
        # Convert PIL to OpenCV
        has_alpha = image.mode == 'RGBA'
        if has_alpha:
            alpha_channel = np.array(image)[:, :, 3]
            rgb_image = image.convert('RGB')
        else:
            rgb_image = image.convert('RGB')

        cv_image = cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)

        # Apply bilateral filter to smooth while preserving edges
        sigma_color = int(75 * strength)
        sigma_space = int(75 * strength)
        d = int(9 * strength) if strength > 0 else 5

        smoothed = cv2.bilateralFilter(cv_image, d, sigma_color, sigma_space)

        # Blend original and smoothed based on strength
        result = cv2.addWeighted(cv_image, 1 - strength, smoothed, strength, 0)

        # Convert back to PIL
        rgb_result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        pil_result = Image.fromarray(rgb_result)

        # Restore alpha channel if present
        if has_alpha:
            pil_result.putalpha(Image.fromarray(alpha_channel))

        logger.info(f"Applied wrinkle removal with strength: {strength}")
        return pil_result

    def smooth_fabric(self, image: Image.Image) -> Image.Image:
        """
        General fabric smoothing

        Args:
            image: Input PIL Image

        Returns:
            Smoothed image
        """
        return self.remove_wrinkles(image, strength=0.3)
