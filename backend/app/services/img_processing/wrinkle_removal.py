"""
Wrinkle Removal Module
Smoothing and detail preservation for clothing images
"""
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class WrinkleRemoval:
    """Wrinkle removal and fabric smoothing"""
    
    def __init__(self):
        """Initialize wrinkle removal"""
        pass
    
    def bilateral_filter(self, image: np.ndarray, d: int = 9, 
                        sigma_color: int = 75, sigma_space: int = 75) -> np.ndarray:
        """
        Apply bilateral filter for edge-preserving smoothing
        
        Args:
            image: Input image
            d: Diameter of pixel neighborhood
            sigma_color: Filter sigma in color space
            sigma_space: Filter sigma in coordinate space
            
        Returns:
            Filtered image
        """
        return cv2.bilateralFilter(image, d, sigma_color, sigma_space)
    
    def guided_filter(self, image: np.ndarray, radius: int = 8, eps: float = 0.01) -> np.ndarray:
        """
        Apply guided filter for detail-preserving smoothing
        
        Args:
            image: Input image (BGR)
            radius: Radius of guided filter
            eps: Regularization parameter
            
        Returns:
            Filtered image
        """
        # Convert to float
        img = image.astype(np.float32) / 255.0
        
        # Use image itself as guidance
        mean_I = cv2.boxFilter(img, cv2.CV_32F, (radius, radius))
        mean_II = cv2.boxFilter(img * img, cv2.CV_32F, (radius, radius))
        
        var_I = mean_II - mean_I * mean_I
        
        a = var_I / (var_I + eps)
        b = mean_I - a * mean_I
        
        mean_a = cv2.boxFilter(a, cv2.CV_32F, (radius, radius))
        mean_b = cv2.boxFilter(b, cv2.CV_32F, (radius, radius))
        
        result = mean_a * img + mean_b
        result = np.clip(result * 255, 0, 255).astype(np.uint8)
        
        return result
    
    def adaptive_smoothing(self, image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """
        Apply adaptive smoothing based on local variance
        
        Args:
            image: Input image
            kernel_size: Size of smoothing kernel
            
        Returns:
            Smoothed image
        """
        # Convert to grayscale for variance calculation
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate local variance
        mean = cv2.blur(gray, (kernel_size, kernel_size))
        mean_sq = cv2.blur(gray ** 2, (kernel_size, kernel_size))
        variance = mean_sq - mean ** 2
        
        # Normalize variance to [0, 1]
        variance = cv2.normalize(variance, None, 0, 1, cv2.NORM_MINMAX, cv2.CV_32F)
        
        # Create smoothed version
        smoothed = cv2.bilateralFilter(image, 9, 75, 75)
        
        # Blend based on variance (smooth more in low variance areas)
        variance_3ch = cv2.cvtColor((variance * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        variance_3ch = variance_3ch.astype(np.float32) / 255.0
        
        result = image.astype(np.float32) * variance_3ch + \
                 smoothed.astype(np.float32) * (1 - variance_3ch)
        
        return result.astype(np.uint8)
    
    def detail_preserving_smooth(self, image: np.ndarray, strength: float = 0.5) -> np.ndarray:
        """
        Apply detail-preserving smoothing
        
        Args:
            image: Input image
            strength: Smoothing strength (0.0 to 1.0)
            
        Returns:
            Smoothed image
        """
        if strength <= 0:
            return image
        
        # Apply bilateral filter with strength control
        sigma_color = int(75 * strength)
        sigma_space = int(75 * strength)
        d = 9 if strength > 0.5 else 7
        
        smoothed = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
        
        # Blend with original based on strength
        result = cv2.addWeighted(image, 1 - strength, smoothed, strength, 0)
        
        return result
    
    def remove_wrinkles(self, image: Image.Image, strength: str = "medium") -> Image.Image:
        """
        Main wrinkle removal pipeline
        
        Args:
            image: PIL Image (RGB or RGBA)
            strength: Smoothing strength ("light", "medium", "strong")
            
        Returns:
            Smoothed PIL Image
        """
        # Convert PIL to OpenCV format
        has_alpha = image.mode == 'RGBA'
        if has_alpha:
            alpha_channel = np.array(image)[:, :, 3]
            rgb_image = image.convert('RGB')
        else:
            rgb_image = image.convert('RGB')
        
        cv_image = cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)
        
        # Apply smoothing based on strength
        if strength == "light":
            cv_image = self.detail_preserving_smooth(cv_image, strength=0.3)
        elif strength == "medium":
            cv_image = self.bilateral_filter(cv_image, d=9, sigma_color=50, sigma_space=50)
        elif strength == "strong":
            cv_image = self.bilateral_filter(cv_image, d=11, sigma_color=75, sigma_space=75)
            # Apply second pass for very strong smoothing
            cv_image = self.detail_preserving_smooth(cv_image, strength=0.4)
        else:
            logger.warning(f"Unknown strength '{strength}', using medium")
            cv_image = self.bilateral_filter(cv_image, d=9, sigma_color=50, sigma_space=50)
        
        # Convert back to PIL
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        result = Image.fromarray(rgb_image)
        
        # Restore alpha channel if present
        if has_alpha:
            result.putalpha(Image.fromarray(alpha_channel))
        
        logger.info(f"Applied wrinkle removal with strength: {strength}")
        return result