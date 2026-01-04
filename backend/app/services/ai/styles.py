"""
Style Processor Module
Style-specific image preprocessing for different Instagram aesthetics
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from typing import Tuple
import logging

from app.core.color_correction import ColorCorrection
from app.core.wrinkle_removal import WrinkleRemoval

logger = logging.getLogger(__name__)


class StyleProcessor:
    """Process images with different style presets"""
    
    def __init__(self):
        """Initialize style processor"""
        self.color_corrector = ColorCorrection()
        self.wrinkle_remover = WrinkleRemoval()
    
    def add_drop_shadow(self, image: Image.Image, offset: Tuple[int, int] = (10, 10),
                       blur_radius: int = 20, shadow_color: Tuple[int, int, int, int] = (0, 0, 0, 100)) -> Image.Image:
        """
        Add professional drop shadow to image
        
        Args:
            image: RGBA image
            offset: Shadow offset (x, y)
            blur_radius: Shadow blur
            shadow_color: Shadow color (RGBA)
            
        Returns:
            Image with shadow
        """
        # Create shadow layer
        shadow = Image.new('RGBA', image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        
        # Get image bounds (non-transparent pixels)
        bbox = image.getbbox()
        if bbox:
            # Draw shadow
            shadow.paste(Image.new('RGBA', image.size, shadow_color), (0, 0))
            shadow.paste((0, 0, 0, 0), (0, 0), image)
            
            # Offset and blur shadow
            shadow = shadow.transform(
                image.size,
                Image.AFFINE,
                (1, 0, -offset[0], 0, 1, -offset[1]),
                Image.BILINEAR
            )
            shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
            
            # Composite shadow with image
            result = Image.alpha_composite(shadow, image)
            return result
        
        return image
    
    def add_vignette(self, image: Image.Image, strength: float = 0.3) -> Image.Image:
        """
        Add vignette effect
        
        Args:
            image: RGB/RGBA image
            strength: Vignette strength (0.0 to 1.0)
            
        Returns:
            Image with vignette
        """
        # Convert to RGB for processing
        has_alpha = image.mode == 'RGBA'
        if has_alpha:
            alpha = image.split()[3]
            rgb_image = image.convert('RGB')
        else:
            rgb_image = image
        
        # Create radial gradient mask
        width, height = rgb_image.size
        center_x, center_y = width // 2, height // 2
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        # Create vignette mask
        vignette = Image.new('L', (width, height), 255)
        vignette_array = np.array(vignette).astype(np.float32)
        
        for y in range(height):
            for x in range(width):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                vignette_array[y, x] = 255 * (1 - strength * (dist / max_dist))
        
        vignette = Image.fromarray(vignette_array.astype(np.uint8))
        
        # Apply vignette
        result = Image.composite(rgb_image, Image.new('RGB', rgb_image.size, (0, 0, 0)), vignette)
        
        # Restore alpha
        if has_alpha:
            result.putalpha(alpha)
        
        return result
    
    def minimal_style(self, image: Image.Image) -> Image.Image:
        """
        Apply minimal style processing
        - Clean white background
        - Professional drop shadow
        - High contrast
        - Sharp details
        
        Args:
            image: RGBA image (background already removed)
            
        Returns:
            Processed image
        """
        logger.info("Applying minimal style")
        
        # 1. Color correction - vivid for clarity
        enhanced = self.color_corrector.auto_enhance(image, style="vivid")
        
        # 2. Remove wrinkles - light to maintain detail
        smoothed = self.wrinkle_remover.remove_wrinkles(enhanced, strength="light")
        
        # 3. Increase contrast and sharpness
        if smoothed.mode == 'RGBA':
            alpha = smoothed.split()[3]
            rgb = smoothed.convert('RGB')
        else:
            rgb = smoothed.convert('RGB')
            alpha = None
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(rgb)
        rgb = enhancer.enhance(1.2)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(rgb)
        rgb = enhancer.enhance(1.5)
        
        # Restore alpha
        if alpha:
            rgb.putalpha(alpha)
        
        # 4. Add professional drop shadow
        result = self.add_drop_shadow(rgb, offset=(8, 8), blur_radius=15, 
                                      shadow_color=(0, 0, 0, 60))
        
        logger.info("Minimal style applied successfully")
        return result
    
    def mood_style(self, image: Image.Image) -> Image.Image:
        """
        Apply mood/emotional style processing
        - Warm color temperature
        - Soft vintage filter
        - Gentle vignette
        - Subtle smoothing
        
        Args:
            image: RGBA image
            
        Returns:
            Processed image
        """
        logger.info("Applying mood style")
        
        # 1. Color correction - soft for gentle feel
        enhanced = self.color_corrector.auto_enhance(image, style="soft")
        
        # 2. Remove wrinkles - medium smoothing
        smoothed = self.wrinkle_remover.remove_wrinkles(enhanced, strength="medium")
        
        # 3. Apply warm color temperature
        if smoothed.mode == 'RGBA':
            alpha = smoothed.split()[3]
            rgb = smoothed.convert('RGB')
        else:
            rgb = smoothed.convert('RGB')
            alpha = None
        
        # Convert to OpenCV for temperature adjustment
        cv_image = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
        cv_image = self.color_corrector.adjust_color_temperature(cv_image, temperature=30)
        
        # 4. Sepia tone (vintage effect) - subtle
        cv_image = cv_image.astype(np.float32)
        sepia_kernel = np.array([[0.272, 0.534, 0.131],
                                [0.349, 0.686, 0.168],
                                [0.393, 0.769, 0.189]])
        sepia = cv2.transform(cv_image, sepia_kernel)
        
        # Blend sepia with original (30% sepia)
        cv_image = cv2.addWeighted(cv_image, 0.7, sepia, 0.3, 0)
        cv_image = np.clip(cv_image, 0, 255).astype(np.uint8)
        
        # Convert back to PIL
        rgb = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        
        # Restore alpha
        if alpha:
            rgb.putalpha(alpha)
        
        # 5. Add subtle vignette
        result = self.add_vignette(rgb, strength=0.2)
        
        # 6. Slightly reduce saturation for soft look
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(0.9)
        
        logger.info("Mood style applied successfully")
        return result
    
    def street_style(self, image: Image.Image) -> Image.Image:
        """
        Apply street/urban style processing
        - Vibrant colors
        - High saturation
        - Strong contrast
        - Sharp edges
        
        Args:
            image: RGBA image
            
        Returns:
            Processed image
        """
        logger.info("Applying street style")
        
        # 1. Color correction - vivid for vibrant look
        enhanced = self.color_corrector.auto_enhance(image, style="vivid")
        
        # 2. Remove wrinkles - light to keep texture
        smoothed = self.wrinkle_remover.remove_wrinkles(enhanced, strength="light")
        
        # 3. Boost saturation and contrast
        if smoothed.mode == 'RGBA':
            alpha = smoothed.split()[3]
            rgb = smoothed.convert('RGB')
        else:
            rgb = smoothed.convert('RGB')
            alpha = None
        
        # Increase saturation significantly
        enhancer = ImageEnhance.Color(rgb)
        rgb = enhancer.enhance(1.4)
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(rgb)
        rgb = enhancer.enhance(1.3)
        
        # Enhance sharpness for edge definition
        enhancer = ImageEnhance.Sharpness(rgb)
        rgb = enhancer.enhance(2.0)
        
        # 4. Cool temperature adjustment (urban feel)
        cv_image = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
        cv_image = self.color_corrector.adjust_color_temperature(cv_image, temperature=-10)
        
        # Convert back to PIL
        rgb = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        
        # Restore alpha
        if alpha:
            rgb.putalpha(alpha)
        
        logger.info("Street style applied successfully")
        return rgb
    
    def process_with_style(self, image: Image.Image, style: str = "minimal") -> Image.Image:
        """
        Process image with specified style
        
        Args:
            image: Input image (RGBA)
            style: Style name ("minimal", "mood", "street")
            
        Returns:
            Styled image
        """
        style = style.lower()
        
        if style == "minimal":
            return self.minimal_style(image)
        elif style == "mood":
            return self.mood_style(image)
        elif style == "street":
            return self.street_style(image)
        else:
            logger.warning(f"Unknown style '{style}', using minimal")
            return self.minimal_style(image)