"""
Color Correction Module
Automatic color enhancement for fashion product images
"""
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ColorCorrection:
    """Color correction and enhancement for images"""
    
    def __init__(self):
        """Initialize color correction"""
        self.clip_limit = 2.0
        self.tile_grid_size = (8, 8)
    
    def auto_white_balance(self, image: np.ndarray) -> np.ndarray:
        """
        Apply automatic white balance using Gray World algorithm
        
        Args:
            image: BGR image (numpy array)
            
        Returns:
            White balanced image
        """
        result = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])
        
        result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
        
        result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
        return result
    
    def adjust_brightness_contrast(self, image: np.ndarray, brightness: int = 0, 
                                   contrast: int = 0) -> np.ndarray:
        """
        Adjust brightness and contrast
        
        Args:
            image: Input image
            brightness: Brightness adjustment (-100 to 100)
            contrast: Contrast adjustment (-100 to 100)
            
        Returns:
            Adjusted image
        """
        if brightness != 0:
            if brightness > 0:
                shadow = brightness
                highlight = 255
            else:
                shadow = 0
                highlight = 255 + brightness
            alpha_b = (highlight - shadow) / 255
            gamma_b = shadow
            
            image = cv2.addWeighted(image, alpha_b, image, 0, gamma_b)
        
        if contrast != 0:
            f = 131 * (contrast + 127) / (127 * (131 - contrast))
            alpha_c = f
            gamma_c = 127 * (1 - f)
            
            image = cv2.addWeighted(image, alpha_c, image, 0, gamma_c)
        
        return image
    
    def clahe_enhancement(self, image: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        
        Args:
            image: BGR image
            
        Returns:
            Enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Split channels
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, 
                                tileGridSize=self.tile_grid_size)
        l = clahe.apply(l)
        
        # Merge channels
        lab = cv2.merge([l, a, b])
        
        # Convert back to BGR
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        return result
    
    def enhance_saturation(self, image: np.ndarray, saturation_scale: float = 1.2) -> np.ndarray:
        """
        Enhance color saturation
        
        Args:
            image: BGR image
            saturation_scale: Saturation multiplier (1.0 = no change)
            
        Returns:
            Enhanced image
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Scale saturation
        hsv[:, :, 1] = hsv[:, :, 1] * saturation_scale
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # Convert back to BGR
        hsv = hsv.astype(np.uint8)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return result
    
    def adjust_color_temperature(self, image: np.ndarray, temperature: int = 0) -> np.ndarray:
        """
        Adjust color temperature
        
        Args:
            image: BGR image
            temperature: Temperature adjustment (-100 to 100)
                        Negative = cooler (blue), Positive = warmer (yellow/red)
            
        Returns:
            Adjusted image
        """
        if temperature == 0:
            return image
        
        result = image.copy().astype(np.float32)
        
        if temperature > 0:
            # Warm (increase red/yellow, decrease blue)
            result[:, :, 2] = np.clip(result[:, :, 2] * (1 + temperature / 200), 0, 255)  # Red
            result[:, :, 1] = np.clip(result[:, :, 1] * (1 + temperature / 400), 0, 255)  # Green
            result[:, :, 0] = np.clip(result[:, :, 0] * (1 - temperature / 200), 0, 255)  # Blue
        else:
            # Cool (increase blue, decrease red/yellow)
            temperature = abs(temperature)
            result[:, :, 0] = np.clip(result[:, :, 0] * (1 + temperature / 200), 0, 255)  # Blue
            result[:, :, 2] = np.clip(result[:, :, 2] * (1 - temperature / 200), 0, 255)  # Red
        
        return result.astype(np.uint8)
    
    def sharpen(self, image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """
        Apply unsharp masking for sharpening
        
        Args:
            image: Input image
            strength: Sharpening strength (0.5 to 2.0)
            
        Returns:
            Sharpened image
        """
        # Create Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), 3)
        
        # Unsharp mask
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
        
        return sharpened
    
    def auto_enhance(self, image: Image.Image, style: str = "balanced") -> Image.Image:
        """
        Automatic color enhancement pipeline
        
        Args:
            image: PIL Image (RGB or RGBA)
            style: Enhancement style ("balanced", "vivid", "soft")
            
        Returns:
            Enhanced PIL Image
        """
        # Convert PIL to OpenCV format
        has_alpha = image.mode == 'RGBA'
        if has_alpha:
            alpha_channel = np.array(image)[:, :, 3]
            rgb_image = image.convert('RGB')
        else:
            rgb_image = image.convert('RGB')
        
        cv_image = cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)
        
        # Apply enhancements based on style
        if style == "balanced":
            # Balanced: subtle enhancements
            cv_image = self.auto_white_balance(cv_image)
            cv_image = self.clahe_enhancement(cv_image)
            cv_image = self.enhance_saturation(cv_image, 1.1)
            cv_image = self.sharpen(cv_image, 0.5)
            
        elif style == "vivid":
            # Vivid: strong colors and contrast
            cv_image = self.auto_white_balance(cv_image)
            cv_image = self.clahe_enhancement(cv_image)
            cv_image = self.enhance_saturation(cv_image, 1.3)
            cv_image = self.adjust_brightness_contrast(cv_image, brightness=5, contrast=10)
            cv_image = self.sharpen(cv_image, 1.0)
            
        elif style == "soft":
            # Soft: gentle enhancements
            cv_image = self.auto_white_balance(cv_image)
            cv_image = self.enhance_saturation(cv_image, 1.05)
            cv_image = self.adjust_brightness_contrast(cv_image, brightness=10, contrast=5)
            
        else:
            logger.warning(f"Unknown style '{style}', using balanced")
            cv_image = self.auto_white_balance(cv_image)
            cv_image = self.clahe_enhancement(cv_image)
        
        # Convert back to PIL
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        result = Image.fromarray(rgb_image)
        
        # Restore alpha channel if present
        if has_alpha:
            result.putalpha(Image.fromarray(alpha_channel))
        
        logger.info(f"Applied color correction with style: {style}")
        return result