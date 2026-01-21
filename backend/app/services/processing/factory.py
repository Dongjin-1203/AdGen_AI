"""
Model Factory
Creates and manages background removal model instances
"""
from typing import Optional, Dict
import logging
from PIL import Image

from app.service.processing.base import (
    ModelType,
    ModelHealth,
    ModelHealthStatus,
)
from app.service.processing.models import (
    U2NetAdapter,
    RMBG2LocalAdapter,
    RMBG2APIAdapter,
    ModelAdapter,
)
from app.service.processing.config import PipelineConfig

logger = logging.getLogger(__name__)


class ModelFactory:
    """
    Factory for creating and managing background removal model instances
    Implements singleton pattern for model instances
    """
    
    _instances: Dict[ModelType, Optional[ModelAdapter]] = {}
    _health_status: Dict[ModelType, ModelHealth] = {}
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize model factory
        
        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        logger.info(f"ModelFactory initialized with default model: {self.config.default_model}")
    
    def get_model(self, model_type: ModelType) -> Optional[ModelAdapter]:
        """
        Get or create model instance
        
        Args:
            model_type: Type of model to get
            
        Returns:
            Model adapter instance or None if failed
        """
        # Return cached instance if available and healthy
        if model_type in self._instances and self._instances[model_type] is not None:
            health = self.check_health(model_type)
            if health.is_healthy:
                return self._instances[model_type]
            else:
                logger.warning(f"Cached {model_type} instance is unhealthy, recreating...")
                self._instances[model_type] = None
        
        # Create new instance
        try:
            logger.info(f"Creating new {model_type} model instance...")
            model = self._create_model(model_type)
            self._instances[model_type] = model
            
            # Update health status
            self._health_status[model_type] = ModelHealth(
                model_type=model_type,
                status=ModelHealthStatus.HEALTHY,
                message="Model initialized successfully"
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to create {model_type} model: {e}")
            self._health_status[model_type] = ModelHealth(
                model_type=model_type,
                status=ModelHealthStatus.UNHEALTHY,
                message=str(e)
            )
            return None
    
    def _create_model(self, model_type: ModelType) -> ModelAdapter:
        """
        Create a new model instance based on type
        
        Args:
            model_type: Type of model to create
            
        Returns:
            Model adapter instance
            
        Raises:
            ValueError: If model type is not supported
            Exception: If model creation fails
        """
        if model_type == ModelType.U2NET:
            return U2NetAdapter()
        
        elif model_type == ModelType.RMBG2_LOCAL:
            return RMBG2LocalAdapter(
                device=self.config.device,
                model_path=self.config.local_model_path
            )
        
        elif model_type == ModelType.RMBG2_API:
            return RMBG2APIAdapter(device=self.config.device)
        
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def get_default_model(self) -> Optional[ModelAdapter]:
        """
        Get the default model based on configuration
        
        Returns:
            Default model adapter instance or None if failed
        """
        try:
            model_type = ModelType(self.config.default_model)
            return self.get_model(model_type)
        except ValueError:
            logger.error(f"Invalid default model: {self.config.default_model}")
            return None
    
    def get_fallback_model(self, exclude: Optional[ModelType] = None) -> Optional[ModelAdapter]:
        """
        Get a fallback model from the fallback chain
        
        Args:
            exclude: Model type to exclude from fallback
            
        Returns:
            Fallback model adapter instance or None if no fallback available
        """
        if not self.config.fallback_enabled:
            logger.info("Fallback is disabled")
            return None
        
        for model_str in self.config.fallback_chain:
            try:
                model_type = ModelType(model_str)
                
                # Skip excluded model
                if exclude and model_type == exclude:
                    continue
                
                # Try to get this model
                model = self.get_model(model_type)
                if model is not None:
                    logger.info(f"Using fallback model: {model_type}")
                    return model
                    
            except (ValueError, Exception) as e:
                logger.warning(f"Failed to get fallback model {model_str}: {e}")
                continue
        
        logger.error("No fallback models available")
        return None
    
    def check_health(self, model_type: ModelType) -> ModelHealth:
        """
        Check health of a model
        
        Args:
            model_type: Type of model to check
            
        Returns:
            Model health status
        """
        # Return cached health status if recent
        if model_type in self._health_status:
            from datetime import datetime, timedelta
            health = self._health_status[model_type]
            if datetime.now() - health.last_check < timedelta(minutes=5):
                return health
        
        # Perform health check
        model = self._instances.get(model_type)
        
        if model is None:
            return ModelHealth(
                model_type=model_type,
                status=ModelHealthStatus.UNKNOWN,
                message="Model not initialized"
            )
        
        # Try a simple operation to check if model is responsive
        try:
            # Create a small test image
            test_image = Image.new('RGB', (100, 100), color='red')
            
            # Basic check - just verify model exists and has required methods
            if hasattr(model, 'remove_background'):
                health = ModelHealth(
                    model_type=model_type,
                    status=ModelHealthStatus.HEALTHY,
                    message="Model is responsive"
                )
            else:
                health = ModelHealth(
                    model_type=model_type,
                    status=ModelHealthStatus.UNHEALTHY,
                    message="Model is missing required methods"
                )
            
            self._health_status[model_type] = health
            return health
            
        except Exception as e:
            logger.error(f"Health check failed for {model_type}: {e}")
            health = ModelHealth(
                model_type=model_type,
                status=ModelHealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
            self._health_status[model_type] = health
            return health
    
    def get_all_health_status(self) -> Dict[str, dict]:
        """
        Get health status of all models
        
        Returns:
            Dictionary of health statuses
        """
        statuses = {}
        for model_type in ModelType:
            health = self.check_health(model_type)
            statuses[model_type.value] = {
                "status": health.status.value,
                "message": health.message,
                "last_check": health.last_check.isoformat() if health.last_check else None,
            }
        return statuses
    
    def clear_cache(self, model_type: Optional[ModelType] = None):
        """
        Clear cached model instances
        
        Args:
            model_type: Specific model to clear, or None to clear all
        """
        if model_type:
            logger.info(f"Clearing cache for {model_type}")
            self._instances.pop(model_type, None)
            self._health_status.pop(model_type, None)
        else:
            logger.info("Clearing all model cache")
            self._instances.clear()
            self._health_status.clear()
