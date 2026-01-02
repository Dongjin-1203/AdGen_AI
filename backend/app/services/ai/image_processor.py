<<<<<<< HEAD
from PIL import Image
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    @staticmethod
    def preprocess_canny(image: Image.Image, low_threshold: int = 100, high_threshold: int = 200) -> Image.Image:
        """
        Preprocesses an image for ControlNet Canny edge detection.
        
        Args:
            image (Image.Image): Input image.
            low_threshold (int): Lower threshold for Canny.
            high_threshold (int): Higher threshold for Canny.
            
        Returns:
            Image.Image: The processed image suitable for ControlNet processing.
        """
        try:
            image_array = np.array(image)
            
            # Ensure image is in a format cv2 can handle (remove alpha if present or convert)
            if len(image_array.shape) == 3 and image_array.shape[2] == 4:
                 # Convert RGBA to RGB for Canny detection if needed, or just handle it. 
                 # Canny expects grayscale usually or handles conversion internally?
                 # Standard practice: Convert to grayscale for canny
                 gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGBA2GRAY)
            elif len(image_array.shape) == 3 and image_array.shape[2] == 3:
                 gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                 # Assume grayscale
                 gray_image = image_array

            # Detect edges
            edges = cv2.Canny(gray_image, low_threshold, high_threshold)
            
            # Convert back to 3-channel image for ControlNet input compatibility
            edges_rgb = np.concatenate([edges[:, :, None]], axis=2)
            edges_rgb = np.concatenate([edges_rgb, edges_rgb, edges_rgb], axis=2)
            
            return Image.fromarray(edges_rgb)
        except Exception as e:
            logger.error(f"Error in Canny preprocessing: {str(e)}")
            raise e

    @staticmethod
    def resize_image(image: Image.Image, max_size: int = 1024) -> Image.Image:
        """
        Resizes an image while maintaining aspect ratio.
        """
        width, height = image.size
        if width > max_size or height > max_size:
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        return image
=======
# 이미지 처리
>>>>>>> origin/main
