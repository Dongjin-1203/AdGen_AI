"""
Background Removal Service using rembg
Fallback implementation that doesn't require Hugging Face authentication
"""
from typing import List
from PIL import Image
import logging
from rembg import remove

logger = logging.getLogger(__name__)


class BackgroundRemovalService:
    """Service for AI-powered background removal using rembg"""
    
    def __init__(self):
        """Initialize the background removal service"""
        logger.info("Initializing rembg background removal service")
        self.model_name = "rembg (u2net)"
    
    async def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove background from image using rembg
        
        Args:
            image: Input PIL Image (RGB)
            
        Returns:
            Image with background removed (RGBA with transparent background)
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            original_size = image.size
            
            # Run rembg
            result = remove(image)
            
            logger.info(f"Background removed successfully for image size: {original_size}")
            return result
            
        except Exception as e:
            logger.error(f"Error removing background: {e}")
            raise
    
    async def batch_remove_background(self, images: List[Image.Image]) -> List[Image.Image]:
        """
        Remove background from multiple images
        
        Args:
            images: List of PIL Images
            
        Returns:
            List of images with backgrounds removed
        """
        results = []
        for idx, image in enumerate(images):
            try:
                result = await self.remove_background(image)
                results.append(result)
                logger.info(f"Processed image {idx + 1}/{len(images)}")
            except Exception as e:
                logger.error(f"Error processing image {idx + 1}: {e}")
                # Return original image on error
                results.append(image)
        
        return results