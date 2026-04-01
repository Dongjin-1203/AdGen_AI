"""
Base interfaces and types for background removal processing
"""
from typing import Protocol, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from PIL import Image


class ModelType(str, Enum):
    """Supported background removal model types"""
    U2NET = "u2net"
    RMBG2_LOCAL = "rmbg-2.0-local"
    RMBG2_API = "rmbg-2.0-api"


class ProcessingStatus(str, Enum):
    """Processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # For batch processing with some failures


@dataclass
class ProcessingResult:
    """Result of background removal processing"""
    status: ProcessingStatus
    image: Optional[Image.Image] = None
    model_used: Optional[ModelType] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def success(self) -> bool:
        """Check if processing was successful"""
        return self.status == ProcessingStatus.SUCCESS
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "status": self.status.value,
            "model_used": self.model_used.value if self.model_used else None,
            "processing_time": self.processing_time,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class BatchProcessingResult:
    """Result of batch background removal processing"""
    total: int
    successful: int
    failed: int
    results: List[ProcessingResult]
    total_time: float
    average_time: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        return self.successful / self.total if self.total > 0 else 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.success_rate,
            "total_time": self.total_time,
            "average_time": self.average_time,
            "results": [r.to_dict() for r in self.results],
        }


class BackgroundRemovalProtocol(Protocol):
    """
    Protocol that all background removal services must implement
    This defines the interface that model adapters must follow
    """
    
    async def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove background from a single image
        
        Args:
            image: Input PIL Image (RGB)
            
        Returns:
            Image with background removed (RGBA with transparent background)
        """
        ...
    
    async def batch_remove_background(self, images: List[Image.Image]) -> List[Image.Image]:
        """
        Remove background from multiple images
        
        Args:
            images: List of PIL Images
            
        Returns:
            List of images with backgrounds removed
        """
        ...


class ModelHealthStatus(str, Enum):
    """Model health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ModelHealth:
    """Model health check result"""
    model_type: ModelType
    status: ModelHealthStatus
    message: Optional[str] = None
    last_check: datetime = None
    
    def __post_init__(self):
        if self.last_check is None:
            self.last_check = datetime.now()
    
    @property
    def is_healthy(self) -> bool:
        """Check if model is healthy"""
        return self.status == ModelHealthStatus.HEALTHY
