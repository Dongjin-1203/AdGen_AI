"""
Background Removal Pipeline
Main processing pipeline with preprocessing, model execution, and postprocessing
"""
from typing import List, Optional
import time
import asyncio
import logging
from PIL import Image

from app.service.processing.base import (
    ProcessingResult,
    ProcessingStatus,
    BatchProcessingResult,
    ModelType,
)
from app.service.processing.factory import ModelFactory
from app.service.processing.config import PipelineConfig

logger = logging.getLogger(__name__)


class BackgroundRemovalPipeline:
    """
    Main pipeline for background removal processing
    Handles preprocessing, model selection, processing, and postprocessing
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the background removal pipeline
        
        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        self.factory = ModelFactory(self.config)
        self._metrics = {
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "total_time": 0.0,
        }
        logger.info("BackgroundRemovalPipeline initialized")
    
    async def process(
        self,
        image: Image.Image,
        model_type: Optional[ModelType] = None,
        use_fallback: bool = True
    ) -> ProcessingResult:
        """
        Process a single image through the pipeline
        
        Args:
            image: Input PIL Image
            model_type: Specific model to use (None for default)
            use_fallback: Whether to use fallback models on failure
            
        Returns:
            Processing result
        """
        start_time = time.time()
        
        try:
            # Preprocessing
            if self.config.enable_preprocessing:
                image = self._preprocess_image(image)
            
            # Get model
            if model_type:
                model = self.factory.get_model(model_type)
                used_model_type = model_type
            else:
                model = self.factory.get_default_model()
                used_model_type = ModelType(self.config.default_model)
            
            if model is None:
                if use_fallback and self.config.fallback_enabled:
                    logger.warning(f"Primary model failed, trying fallback...")
                    model = self.factory.get_fallback_model(exclude=used_model_type)
                    if model:
                        used_model_type = self._get_model_type_from_adapter(model)
                
                if model is None:
                    raise Exception("No available models")
            
            # Process with retry logic
            result_image = await self._process_with_retry(model, image)
            
            # Postprocessing
            if self.config.enable_postprocessing:
                result_image = self._postprocess_image(result_image)
            
            processing_time = time.time() - start_time
            
            # Update metrics
            if self.config.collect_metrics:
                self._update_metrics(success=True, processing_time=processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                image=result_image,
                model_used=used_model_type,
                processing_time=processing_time,
                metadata={
                    "input_size": image.size,
                    "output_size": result_image.size,
                    "output_mode": result_image.mode,
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Processing failed: {e}")
            
            # Update metrics
            if self.config.collect_metrics:
                self._update_metrics(success=False, processing_time=processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=str(e),
                processing_time=processing_time,
            )
    
    async def process_batch(
        self,
        images: List[Image.Image],
        model_type: Optional[ModelType] = None,
        use_fallback: bool = True
    ) -> BatchProcessingResult:
        """
        Process multiple images through the pipeline
        
        Args:
            images: List of input PIL Images
            model_type: Specific model to use (None for default)
            use_fallback: Whether to use fallback models on failure
            
        Returns:
            Batch processing result
        """
        start_time = time.time()
        results = []
        
        # Process in batches
        batch_size = self.config.batch_size
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            # Process batch concurrently
            batch_results = await asyncio.gather(
                *[self.process(img, model_type, use_fallback) for img in batch],
                return_exceptions=True
            )
            
            # Handle exceptions
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch item {i + idx} failed: {result}")
                    results.append(ProcessingResult(
                        status=ProcessingStatus.FAILED,
                        error=str(result)
                    ))
                else:
                    results.append(result)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        average_time = total_time / len(results) if results else 0.0
        
        return BatchProcessingResult(
            total=len(images),
            successful=successful,
            failed=failed,
            results=results,
            total_time=total_time,
            average_time=average_time,
        )
    
    async def _process_with_retry(self, model, image: Image.Image) -> Image.Image:
        """
        Process image with retry logic
        
        Args:
            model: Model adapter to use
            image: Input image
            
        Returns:
            Processed image
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.config.max_retries}")
                    await asyncio.sleep(self.config.retry_delay)
                
                # Process with timeout
                result = await asyncio.wait_for(
                    model.remove_background(image),
                    timeout=self.config.timeout
                )
                
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Processing timeout after {self.config.timeout}s"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
        
        raise Exception(f"All retries failed. Last error: {last_error}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image before model processing
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            logger.debug(f"Converting image from {image.mode} to RGB")
            image = image.convert('RGB')
        
        # Additional preprocessing can be added here
        # (e.g., resizing, normalization, etc.)
        
        return image
    
    def _postprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Postprocess image after model processing
        
        Args:
            image: Processed image
            
        Returns:
            Postprocessed image
        """
        # Ensure output is RGBA
        if image.mode != 'RGBA':
            logger.debug(f"Converting output from {image.mode} to RGBA")
            image = image.convert('RGBA')
        
        # Additional postprocessing can be added here
        # (e.g., quality enhancement, edge refinement, etc.)
        
        return image
    
    def _get_model_type_from_adapter(self, model) -> ModelType:
        """
        Get ModelType from adapter instance
        
        Args:
            model: Model adapter instance
            
        Returns:
            Model type
        """
        from app.service.processing.models import (
            U2NetAdapter,
            RMBG2LocalAdapter,
            RMBG2APIAdapter,
        )
        
        if isinstance(model, U2NetAdapter):
            return ModelType.U2NET
        elif isinstance(model, RMBG2LocalAdapter):
            return ModelType.RMBG2_LOCAL
        elif isinstance(model, RMBG2APIAdapter):
            return ModelType.RMBG2_API
        else:
            return ModelType.U2NET  # Default fallback
    
    def _update_metrics(self, success: bool, processing_time: float):
        """
        Update processing metrics
        
        Args:
            success: Whether processing was successful
            processing_time: Time taken for processing
        """
        self._metrics["total_processed"] += 1
        if success:
            self._metrics["total_successful"] += 1
        else:
            self._metrics["total_failed"] += 1
        self._metrics["total_time"] += processing_time
    
    def get_metrics(self) -> dict:
        """
        Get current processing metrics
        
        Returns:
            Dictionary of metrics
        """
        total = self._metrics["total_processed"]
        return {
            **self._metrics,
            "success_rate": self._metrics["total_successful"] / total if total > 0 else 0.0,
            "average_time": self._metrics["total_time"] / total if total > 0 else 0.0,
        }
    
    def get_status(self) -> dict:
        """
        Get pipeline status including model health
        
        Returns:
            Status dictionary
        """
        return {
            "pipeline": "active",
            "config": {
                "default_model": self.config.default_model,
                "fallback_enabled": self.config.fallback_enabled,
                "batch_size": self.config.batch_size,
            },
            "models": self.factory.get_all_health_status(),
            "metrics": self.get_metrics(),
        }
    
    def reset_metrics(self):
        """Reset processing metrics"""
        self._metrics = {
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "total_time": 0.0,
        }
        logger.info("Metrics reset")
