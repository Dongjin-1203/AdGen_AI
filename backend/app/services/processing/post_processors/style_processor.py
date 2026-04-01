"""
Style Processor Module
Apply various style effects to product images
"""
from PIL import Image, ImageFilter, ImageEnhance
import logging

logger = logging.getLogger(__name__)


class StyleProcessor:
    """Apply various artistic styles to images"""

    def __init__(self):
        """Initialize style processor"""
        logger.info("StyleProcessor initialized")

    def apply_minimal_style(self, image: Image.Image) -> Image.Image:
        """
        Apply minimal/clean style

        Args:
            image: Input PIL Image

        Returns:
            Styled image
        """
        # Slightly increase brightness and reduce contrast for clean look
        enhancer = ImageEnhance.Brightness(image)
        result = enhancer.enhance(1.1)
        
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(0.95)
        
        logger.info("Applied minimal style")
        return result

    def apply_vintage_style(self, image: Image.Image) -> Image.Image:
        """
        Apply vintage/retro style

        Args:
            image: Input PIL Image

        Returns:
            Styled image
        """
        # Reduce saturation and add warmth
        enhancer = ImageEnhance.Color(image)
        result = enhancer.enhance(0.8)
        
        # Reduce sharpness for softer look
        result = result.filter(ImageFilter.SMOOTH)
        
        logger.info("Applied vintage style")
        return result

    def apply_dramatic_style(self, image: Image.Image) -> Image.Image:
        """
        Apply dramatic/high-contrast style

        Args:
            image: Input PIL Image

        Returns:
            Styled image
        """
        # Increase contrast and saturation
        enhancer = ImageEnhance.Contrast(image)
        result = enhancer.enhance(1.3)
        
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(1.2)
        
        # Sharpen
        result = result.filter(ImageFilter.SHARPEN)
        
        logger.info("Applied dramatic style")
        return result

    def apply_soft_style(self, image: Image.Image) -> Image.Image:
        """
        Apply soft/dreamy style

        Args:
            image: Input PIL Image

        Returns:
            Styled image
        """
        # Soften and brighten
        result = image.filter(ImageFilter.SMOOTH_MORE)
        
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(1.15)
        
        logger.info("Applied soft style")
        return result

    def apply_style(self, image: Image.Image, style: str = "minimal") -> Image.Image:
        """
        Apply selected style to image

        Args:
            image: Input PIL Image
            style: Style name ("minimal", "vintage", "dramatic", "soft")

        Returns:
            Styled image
        """
        style_map = {
            "minimal": self.apply_minimal_style,
            "vintage": self.apply_vintage_style,
            "dramatic": self.apply_dramatic_style,
            "soft": self.apply_soft_style,
        }

        processor = style_map.get(style, self.apply_minimal_style)
        return processor(image)
