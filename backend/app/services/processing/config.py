"""
Pipeline Configuration
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class PipelineConfig(BaseModel):
    """Configuration for background removal pipeline"""
    
    # Model selection
    default_model: str = Field(
        default="u2net",
        description="Default model to use (u2net, rmbg-2.0-local, rmbg-2.0-api)"
    )
    
    fallback_enabled: bool = Field(
        default=True,
        description="Enable fallback to other models on failure"
    )
    
    fallback_chain: List[str] = Field(
        default=["rmbg-2.0-local", "rmbg-2.0-api", "u2net"],
        description="Fallback order for models"
    )
    
    # Processing options
    batch_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum batch size for batch processing"
    )
    
    timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Processing timeout in seconds"
    )
    
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum number of retries on failure"
    )
    
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Delay between retries in seconds"
    )
    
    # Quality options
    enable_preprocessing: bool = Field(
        default=True,
        description="Enable image preprocessing"
    )
    
    enable_postprocessing: bool = Field(
        default=True,
        description="Enable image postprocessing"
    )
    
    # Model-specific settings
    device: str = Field(
        default="auto",
        description="Device to use (cuda, cpu, auto)"
    )
    
    local_model_path: Optional[str] = Field(
        default=None,
        description="Path to local RMBG-2.0 model"
    )
    
    # Monitoring
    collect_metrics: bool = Field(
        default=True,
        description="Collect processing metrics"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    class Config:
        validate_assignment = True


# Default configuration instance
default_config = PipelineConfig()
