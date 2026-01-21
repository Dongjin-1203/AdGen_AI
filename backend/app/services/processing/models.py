"""
Model Adapters
Wraps existing background removal models to implement BackgroundRemovalProtocol
"""
from typing import List, Optional
from PIL import Image
import logging

from app.service.processing.base import BackgroundRemovalProtocol
from app.core.background_removal import BackgroundRemovalService
from app.core.background_removal_rmbg_local import BackgroundRemovalServiceRMBGLocal
from app.core.background_removal_rmbg import BackgroundRemovalServiceRMBG

logger = logging.getLogger(__name__)


class U2NetAdapter:
    """
    Adapter for U2-Net (rembg) background removal service
    """
    
    def __init__(self):
        """Initialize U2-Net service"""
        logger.info("Initializing U2NetAdapter")
        self._service = BackgroundRemovalService()
        self.model_name = "U2-Net (rembg)"
    
    async def remove_background(self, image: Image.Image) -> Image.Image:
        """Remove background using U2-Net"""
        return await self._service.remove_background(image)
    
    async def batch_remove_background(self, images: List[Image.Image]) -> List[Image.Image]:
        """Batch remove background using U2-Net"""
        return await self._service.batch_remove_background(images)
    
    def get_info(self) -> dict:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "model_type": "u2net",
            "description": "Reliable U2-Net model via rembg library",
        }


class RMBG2LocalAdapter:
    """
    Adapter for RMBG-2.0 Local background removal service
    """
    
    def __init__(self, device: str = "auto", model_path: Optional[str] = None):
        """
        Initialize RMBG-2.0 Local service
        
        Args:
            device: Device to use (cuda, cpu, or auto)
            model_path: Path to local model
        """
        logger.info("Initializing RMBG2LocalAdapter")
        self._service = BackgroundRemovalServiceRMBGLocal(
            device=device,
            model_path=model_path
        )
        self.model_name = "RMBG-2.0 (Local)"
    
    async def remove_background(self, image: Image.Image) -> Image.Image:
        """Remove background using RMBG-2.0 Local"""
        return await self._service.remove_background(image)
    
    async def batch_remove_background(self, images: List[Image.Image]) -> List[Image.Image]:
        """Batch remove background using RMBG-2.0 Local"""
        return await self._service.batch_remove_background(images)
    
    def get_info(self) -> dict:
        """Get model information"""
        info = self._service.get_model_info() if hasattr(self._service, 'get_model_info') else {}
        return {
            "model_name": self.model_name,
            "model_type": "rmbg-2.0-local",
            "description": "High-quality RMBG-2.0 model with 256-level transparency",
            **info
        }


class RMBG2APIAdapter:
    """
    Adapter for RMBG-2.0 API background removal service
    """
    
    def __init__(self, device: str = "auto"):
        """
        Initialize RMBG-2.0 API service
        
        Args:
            device: Device to use (cuda, cpu, or auto)
        """
        logger.info("Initializing RMBG2APIAdapter")
        self._service = BackgroundRemovalServiceRMBG(device=device)
        self.model_name = "RMBG-2.0 (API)"
    
    async def remove_background(self, image: Image.Image) -> Image.Image:
        """Remove background using RMBG-2.0 API"""
        return await self._service.remove_background(image)
    
    async def batch_remove_background(self, images: List[Image.Image]) -> List[Image.Image]:
        """Batch remove background using RMBG-2.0 API"""
        return await self._service.batch_remove_background(images)
    
    def get_info(self) -> dict:
        """Get model information"""
        info = self._service.get_model_info() if hasattr(self._service, 'get_model_info') else {}
        return {
            "model_name": self.model_name,
            "model_type": "rmbg-2.0-api",
            "description": "RMBG-2.0 via Hugging Face Inference API",
            **info
        }


# Type alias for any adapter
ModelAdapter = U2NetAdapter | RMBG2LocalAdapter | RMBG2APIAdapter
