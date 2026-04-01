"""
Processing Pipeline Package
Background removal, image processing, and generation pipelines
"""
from app.service.processing.pipeline import BackgroundRemovalPipeline
from app.service.processing.factory import ModelFactory
from app.service.processing.base import (
    BackgroundRemovalProtocol,
    ProcessingResult,
    ModelType,
    ProcessingStatus,
)

# New AdGen_AI integrated modules
from app.service.processing.generators import HybridGenerator
from app.service.processing.post_processors import (
    ColorCorrector,
    StyleProcessor,
    WrinkleRemover,
    BackgroundRemovalRembg,
)
from app.service.processing.vision import ProductAnalyzer

__all__ = [
    # Core pipeline
    "BackgroundRemovalPipeline",
    "ModelFactory",
    "BackgroundRemovalProtocol",
    "ProcessingResult",
    "ModelType",
    "ProcessingStatus",
    # Generators (AdGen_AI)
    "HybridGenerator",
    # Post Processors (AdGen_AI)
    "ColorCorrector",
    "StyleProcessor",
    "WrinkleRemover",
    "BackgroundRemovalRembg",
    # Vision (AdGen_AI)
    "ProductAnalyzer",
]
