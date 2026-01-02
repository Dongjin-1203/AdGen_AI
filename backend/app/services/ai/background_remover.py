<<<<<<< HEAD
from PIL import Image
from rembg import remove
import io
import logging

logger = logging.getLogger(__name__)

class BackgroundRemover:
    @staticmethod
    def remove_background(image: Image.Image) -> Image.Image:
        """
        Removes the background from the given image using rembg.
        
        Args:
            image (Image.Image): The input image.
            
        Returns:
            Image.Image: The image with the background removed (RGBA).
        """
        try:
            logger.info("Starting background removal...")
            # rembg works with PIL images directly and returns a PIL image
            output_image = remove(image)
            logger.info("Background removal completed successfully.")
            return output_image
        except Exception as e:
            logger.error(f"Error during background removal: {str(e)}")
            raise e
=======
# 누끼 제거
>>>>>>> origin/main
