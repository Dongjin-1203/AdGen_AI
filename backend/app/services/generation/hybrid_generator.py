"""
하이브리드 배경 생성 매니저
로컬 GPU 또는 Replicate API 자동 선택
"""
import logging
import torch
from typing import Optional
from PIL import Image

from app.services.generation import SDXLGenerator, ReplicateBackgroundGenerator
from config import settings

logger = logging.getLogger(__name__)


class HybridGenerator:
    """
    하이브리드 배경 생성기
    
    GPU 사용 가능 여부에 따라 자동으로 로컬/API 선택
    
    Example:
        >>> # 자동 모드 (GPU 체크)
        >>> generator = HybridGenerator()
        >>> 
        >>> # 강제 로컬 모드
        >>> generator = HybridGenerator(force_mode="local")
        >>> 
        >>> # 강제 Replicate 모드
        >>> generator = HybridGenerator(force_mode="replicate")
        >>> 
        >>> # 배경 생성
        >>> result = generator.generate_background(
        ...     product_image=img,
        ...     prompt_text="white minimal background",
        ...     style="minimal"
        ... )
    """
    
    def __init__(
        self,
        force_mode: Optional[str] = None,
        replicate_api_token: Optional[str] = None
    ):
        """
        Args:
            force_mode: 강제 모드 ("local", "replicate", None=자동)
            replicate_api_token: Replicate API 토큰
        """
        # 속성 초기화
        self.force_mode = force_mode
        self.replicate_api_token = replicate_api_token or settings.REPLICATE_API_TOKEN
        self.generator = None
        self.mode = "unknown"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 생성기 초기화
        self._initialize_generator()
    
    def _check_gpu_available(self) -> bool:
        """
        GPU 사용 가능 여부 확인
        
        Returns:
            True: GPU 사용 가능 (CUDA + 6GB 이상)
            False: GPU 없음 또는 메모리 부족
        """
        # 1. CUDA 사용 가능 체크
        if not torch.cuda.is_available():
            logger.info("⚠️ CUDA not available")
            return False
        
        try:
            # 2. GPU 총 메모리 확인
            gpu_props = torch.cuda.get_device_properties(0)
            total_memory_gb = gpu_props.total_memory / (1024**3)
            
            logger.info(f"🎮 GPU detected: {gpu_props.name}")
            logger.info(f"💾 Total GPU memory: {total_memory_gb:.1f} GB")
            
            # 3. 최소 메모리 요구사항 확인 (6GB)
            min_required_gb = 6.0
            if total_memory_gb < min_required_gb:
                logger.warning(
                    f"⚠️ GPU memory too low: {total_memory_gb:.1f} GB < {min_required_gb} GB"
                )
                return False
            
            # 4. 추가 정보 로깅
            allocated_memory_gb = torch.cuda.memory_allocated(0) / (1024**3)
            reserved_memory_gb = torch.cuda.memory_reserved(0) / (1024**3)
            
            logger.info(f"   Allocated: {allocated_memory_gb:.2f} GB")
            logger.info(f"   Reserved: {reserved_memory_gb:.2f} GB")
            logger.info(f"   Available: {total_memory_gb - reserved_memory_gb:.2f} GB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ GPU check failed: {e}")
            return False
    
    def _use_local_generator(self):
        """로컬 SDXL 생성기 초기화"""
        try:
            # CPU 모드 체크
            if self.device == "cpu":
                raise RuntimeError(
                    "Local SDXL generator requires CUDA GPU. "
                    "CPU mode is not supported due to memory and performance constraints. "
                    "Use Replicate API instead (auto mode will select it automatically)."
                )
            
            # CUDA 사용 가능 체크
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA is not available. Cannot initialize local generator."
                )
            
            logger.info("🚀 Initializing local SDXL generator...")
            self.generator = SDXLGenerator(device=self.device)
            self.generator.load_model()
            self.mode = "local"
            logger.info("✅ Local generator initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize local generator: {e}")
            raise
    
    def _use_replicate_generator(self):
        """Replicate API 생성기 초기화"""
        try:
            logger.info("🌐 Initializing Replicate API generator...")
            
            # 1. API 토큰 확인
            if not self.replicate_api_token:
                raise ValueError(
                    "Replicate API token is required. "
                    "Set REPLICATE_API_TOKEN in environment or pass api_token parameter"
                )
            
            # 2. ReplicateBackgroundGenerator 인스턴스 생성
            self.generator = ReplicateBackgroundGenerator(api_token=self.replicate_api_token)
            
            # 3. mode 설정
            self.mode = "replicate"
            
            logger.info("✅ Replicate generator initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Replicate generator: {e}")
            raise
    
    def _initialize_generator(self):
        """생성기 초기화 (자동 선택)"""
        
        # Case 1: 강제 모드가 설정된 경우
        if self.force_mode:
            if self.force_mode == "local":
                logger.info("🔒 Force mode: LOCAL")
                self._use_local_generator()
                
            elif self.force_mode == "replicate":
                logger.info("🔒 Force mode: REPLICATE")
                self._use_replicate_generator()
                
            else:
                # 잘못된 force_mode
                raise ValueError(
                    f"Invalid force_mode: '{self.force_mode}'. "
                    f"Must be 'local', 'replicate', or None"
                )
            return
        
        # Case 2: 자동 모드 (GPU 체크)
        logger.info("🤖 Auto mode: Checking GPU availability...")
        
        if self._check_gpu_available():
            # GPU 사용 가능 → 로컬 시도
            try:
                self._use_local_generator()
                
            except Exception as e:
                # 로컬 실패 → Replicate Fallback
                logger.warning(f"⚠️ Local generator failed: {e}")
                logger.info("🔄 Falling back to Replicate API...")
                
                try:
                    self._use_replicate_generator()
                    
                except Exception as replicate_error:
                    # 둘 다 실패
                    logger.error("❌ Both generators failed")
                    raise RuntimeError(
                        f"Failed to initialize any generator. "
                        f"Local error: {e}, Replicate error: {replicate_error}"
                    )
        else:
            # GPU 없음 → Replicate 사용
            logger.info("🌐 No GPU available, using Replicate API")
            self._use_replicate_generator()
    
    def generate_background(
        self, 
        product_image: Image.Image, 
        prompt_text: str, 
        **kwargs
    ) -> Image.Image:
        """
        배경 생성 (통합 인터페이스)
        
        Args:
            product_image: 제품 이미지 (배경 제거된 상태)
            prompt_text: 생성 프롬프트
            **kwargs: 추가 파라미터
                - aspect_ratio: "square", "portrait", "landscape"
                - style: "minimal", "emotional", "street", "instagram"
                - negative_prompt: 네거티브 프롬프트
                - num_inference_steps: 생성 스텝
                - controlnet_conditioning_scale: ControlNet 강도
                - padding_percent: 이미지 패딩 (0.0~1.0)
                - vertical_alignment: 수직 정렬 ("top", "center", "bottom")
                - use_ip_adapter: IP-Adapter 사용 (로컬만 지원)
        
        Returns:
            생성된 이미지
        
        Raises:
            RuntimeError: 생성기가 초기화되지 않았거나 생성 실패
        """
        # 1. 생성기 초기화 확인
        if self.generator is None:
            raise RuntimeError("Generator not initialized")
        
        logger.info(f"🎨 Generating background using {self.mode.upper()} mode")
        logger.info(f"   Prompt: {prompt_text}")
        logger.info(f"   Image size: {product_image.size}")
        
        # 2. IP-Adapter 경고 (Replicate 모드)
        if self.mode == "replicate" and kwargs.get("use_ip_adapter"):
            logger.warning("⚠️ IP-Adapter not supported in Replicate mode (ignored)")
        
        try:
            # 3. 생성 실행
            result = self.generator.generate_background(
                product_image=product_image,
                prompt_text=prompt_text,
                **kwargs
            )
            
            logger.info(f"✅ Background generated successfully ({result.size})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Generation failed in {self.mode} mode: {e}")
            
            # 4. Fallback 시도 (자동 모드이고 로컬 실패 시)
            if self.mode == "local" and not self.force_mode:
                logger.info("🔄 Attempting fallback to Replicate...")
                
                try:
                    # Replicate으로 전환
                    self._use_replicate_generator()
                    
                    # 재시도
                    result = self.generator.generate_background(
                        product_image=product_image,
                        prompt_text=prompt_text,
                        **kwargs
                    )
                    
                    logger.info(f"✅ Background generated with fallback ({result.size})")
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {fallback_error}")
                    raise RuntimeError(
                        f"Generation failed in both modes. "
                        f"Local: {e}, Replicate: {fallback_error}"
                    )
            
            # Fallback 불가능 또는 이미 Replicate 모드
            raise RuntimeError(f"Generation failed: {e}")
    
    def get_mode(self) -> str:
        """
        현재 사용 중인 모드 반환
        
        Returns:
            "local", "replicate", "unknown"
        """
        return self.mode
    
    def switch_mode(self, mode: str):
        """
        수동으로 모드 전환
        
        Args:
            mode: "local" or "replicate"
        
        Raises:
            ValueError: 잘못된 mode 값
            RuntimeError: 모드 전환 실패
        
        Example:
            >>> generator = HybridGenerator()
            >>> generator.get_mode()
            'local'
            >>> generator.switch_mode('replicate')
            >>> generator.get_mode()
            'replicate'
        """
        # 1. mode 유효성 검사
        if mode not in ["local", "replicate"]:
            raise ValueError(
                f"Invalid mode: '{mode}'. Must be 'local' or 'replicate'"
            )
        
        # 2. 이미 해당 모드면 스킵
        if self.mode == mode:
            logger.info(f"ℹ️ Already using {mode.upper()} mode")
            return
        
        logger.info(f"🔄 Switching mode: {self.mode.upper()} → {mode.upper()}")
        
        # 3. force_mode 업데이트
        old_mode = self.mode
        self.force_mode = mode
        
        try:
            # 4. 생성기 재초기화
            if mode == "local":
                self._use_local_generator()
            else:
                self._use_replicate_generator()
            
            logger.info(f"✅ Mode switched successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to switch mode: {e}")
            
            # 원래 모드로 복구 시도
            logger.info(f"🔄 Reverting to {old_mode.upper()} mode")
            self.force_mode = old_mode
            self.mode = old_mode
            
            raise RuntimeError(f"Failed to switch to {mode} mode: {e}")