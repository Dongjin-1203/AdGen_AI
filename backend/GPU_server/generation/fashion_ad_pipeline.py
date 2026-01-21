"""
Fashion Ad Pipeline
패션 광고 생성 통합 파이프라인 (IDM-VTON + SDXL)
"""
import torch
import numpy as np
from PIL import Image
from typing import Optional
import logging

from transformers import SegformerImageProcessor, AutoModelForSemanticSegmentation
from controlnet_aux import OpenposeDetector

from generation.female_model_selector import FemaleModelSelector
from generation.idm_vton_generator import IDMVTONGenerator
from generation.local_generator import SDXLGenerator

logger = logging.getLogger(__name__)


# ========================================
# 전처리 함수 (test_idm_vton_integration.py에서 복사)
# ========================================

def get_segmentation_mask(image: Image.Image, device: str = "cuda") -> Image.Image:
    """
    SegFormer로 의류 영역 마스크 생성
    
    Args:
        image: RGB 이미지
        device: 디바이스 ("cuda" or "cpu")
    
    Returns:
        L 모드 마스크 이미지 (흰색=의류, 검은색=배경)
    """
    logger.info("Generating segmentation mask with SegFormer...")
    
    try:
        # SegFormer 로드
        processor = SegformerImageProcessor.from_pretrained(
            "mattmdjaga/segformer_b2_clothes"
        )
        model = AutoModelForSemanticSegmentation.from_pretrained(
            "mattmdjaga/segformer_b2_clothes"
        ).to(device)
        
        # 추론
        inputs = processor(images=image, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits.cpu()
        
        # Upsample to original size
        upsampled_logits = torch.nn.functional.interpolate(
            logits,
            size=image.size[::-1],  # (height, width)
            mode="bilinear",
            align_corners=False
        )
        
        pred_seg = upsampled_logits.argmax(dim=1)[0]
        
        # 의류 레이블 추출
        # Labels: 5 (Upper), 6 (Dress), 7 (Coat), 14 (L-Arm), 15 (R-Arm)
        labels_to_include = [5, 6, 7, 14, 15]
        
        mask = np.zeros_like(pred_seg, dtype=np.uint8)
        for label in labels_to_include:
            mask[pred_seg == label] = 255
        
        mask_img = Image.fromarray(mask).convert("L")
        
        logger.info(f"✅ Segmentation mask generated: {mask_img.size}")
        
        # 메모리 해제
        del model, processor, inputs, outputs, logits
        torch.cuda.empty_cache()
        
        return mask_img
        
    except Exception as e:
        logger.error(f"Segmentation mask generation failed: {e}")
        raise


def get_densepose(image: Image.Image) -> Image.Image:
    """
    DensePose 생성
    
    Args:
        image: RGB 이미지
    
    Returns:
        DensePose RGB 이미지
    """
    logger.info("Generating DensePose...")
    
    try:
        densepose_detector = OpenposeDetector.from_pretrained(
            "lllyasviel/ControlNet"
        )
        pose_img = densepose_detector(image)
        
        logger.info(f"✅ DensePose generated: {pose_img.size}")
        
        # 메모리 해제
        del densepose_detector
        torch.cuda.empty_cache()
        
        return pose_img
        
    except ImportError:
        logger.error("ControlNet Aux not installed. Cannot generate DensePose.")
        # 빈 이미지 반환 (fallback)
        return Image.new("RGB", image.size, (0, 0, 0))
        
    except Exception as e:
        logger.error(f"DensePose generation failed: {e}")
        # 빈 이미지 반환 (fallback)
        return Image.new("RGB", image.size, (0, 0, 0))


# ========================================
# 메인 파이프라인
# ========================================

class FashionAdPipeline:
    """
    패션 광고 생성 파이프라인
    
    워크플로우:
    1. FemaleModelSelector로 K-Fashion 모델 선택
    2. SegFormer + DensePose로 전처리
    3. IDM-VTON으로 가상 착장
    4. SDXL로 배경 생성
    """
    
    def __init__(
        self,
        sdxl_generator: Optional[SDXLGenerator] = None,
        device: str = "cuda",
        assets_dir: str = "assets/female_models"
    ):
        """
        초기화
        
        Args:
            sdxl_generator: SDXL Generator (이미 로드된 것 재사용)
            device: 디바이스
            assets_dir: K-Fashion 데이터셋 경로
        """
        self.device = device
        self.sdxl = sdxl_generator
        
        # Components (Lazy loading)
        self.model_selector = FemaleModelSelector(assets_dir=assets_dir)
        self.idm_vton = None
        
        logger.info("FashionAdPipeline initialized")
    
    def generate(
        self,
        garment_image: Image.Image,
        style: str,
        garment_description: Optional[str] = None,
        aspect_ratio: str = "square",
        prompt_text: Optional[str] = None,
        num_inference_steps: int = 30,
        model_index: Optional[int] = None
    ) -> Image.Image:
        """
        패션 광고 생성
        
        Args:
            garment_image: 옷 이미지 (PIL Image)
            style: 스타일 (minimal, vintage, modern, natural, luxury 등)
            garment_description: 옷 설명 (None이면 자동 생성)
            aspect_ratio: 최종 이미지 비율 (square, portrait, landscape)
            prompt_text: 배경 생성 프롬프트 (None이면 자동 생성)
            num_inference_steps: IDM-VTON 생성 스텝 (기본 30)
            model_index: 특정 모델 인덱스 (None이면 랜덤)
        
        Returns:
            최종 광고 이미지 (PIL Image)
        """
        logger.info("=" * 60)
        logger.info("🎨 Fashion Ad Pipeline START")
        logger.info(f"   Style: {style}")
        logger.info(f"   Aspect Ratio: {aspect_ratio}")
        logger.info(f"   Model Index: {model_index if model_index else 'Random'}")
        logger.info("=" * 60)
        
        try:
            # ===== Step 1: 모델 선택 =====
            logger.info("Step 1/4: Selecting female model...")
            model_data = self.model_selector.select_model(style, index=model_index)
            human_image = model_data['image']
            logger.info(f"✅ Model selected: {model_data['filename']}")
            
            # ===== Step 2: 전처리 (마스크 + 포즈) =====
            logger.info("Step 2/4: Preprocessing (mask + pose)...")
            
            # IDM-VTON 표준 해상도 (768, 1024)
            target_size = (768, 1024)
            
            # Resize
            human_image_resized = human_image.resize(target_size, Image.Resampling.LANCZOS)
            garment_image_resized = garment_image.resize(target_size, Image.Resampling.LANCZOS)
            
            # 마스크 생성
            mask = get_segmentation_mask(human_image_resized, device=self.device)
            mask = mask.resize(target_size, Image.Resampling.NEAREST)
            
            # DensePose 생성
            pose = get_densepose(human_image_resized)
            pose = pose.resize(target_size, Image.Resampling.LANCZOS)
            
            logger.info("✅ Preprocessing complete")
            
            # ===== Step 3: IDM-VTON 가상 착장 =====
            logger.info("Step 3/4: Virtual try-on with IDM-VTON...")
            
            # IDM-VTON 로드 (lazy)
            if self.idm_vton is None:
                logger.info("Loading IDM-VTON model...")
                self.idm_vton = IDMVTONGenerator(device=self.device)
                self.idm_vton.load_model()
            
            # 옷 설명 생성
            if garment_description is None:
                garment_description = "model wearing fashionable clothes"
            
            # 가상 착장 수행
            tryon_result = self.idm_vton.generate(
                human_image=human_image_resized,
                garm_image=garment_image_resized,
                garment_description=garment_description,
                pose_image=pose,
                mask_image=mask,
                num_inference_steps=num_inference_steps
            )
            
            logger.info(f"✅ Virtual try-on complete: {tryon_result.size}")
            
            # 메모리 해제 (IDM-VTON은 큰 모델이므로 즉시 해제)
            del self.idm_vton
            self.idm_vton = None
            torch.cuda.empty_cache()
            logger.info("🧹 IDM-VTON unloaded from memory")
            
            # ===== Step 4: SDXL 배경 생성 =====
            logger.info("Step 4/4: Generating background with SDXL...")
            
            # SDXL 로드 (이미 로드되어 있으면 재사용)
            if self.sdxl is None:
                logger.info("Loading SDXL model...")
                self.sdxl = SDXLGenerator(device=self.device)
                self.sdxl.load_model()
            
            # 배경 프롬프트 생성
            if prompt_text is None:
                # 스타일별 기본 프롬프트 (간단하게)
                prompt_text = f"professional fashion photography, {style} style background"
            
            # 배경 생성
            final_result = self.sdxl.generate_background(
                product_image=tryon_result,
                prompt_text=prompt_text,
                aspect_ratio=aspect_ratio,
                style=style
            )
            
            logger.info(f"✅ Background generation complete: {final_result.size}")
            
            logger.info("=" * 60)
            logger.info("🎉 Fashion Ad Pipeline COMPLETE")
            logger.info("=" * 60)
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Fashion Ad Pipeline failed: {e}")
            logger.exception(e)
            raise
    
    def cleanup(self):
        """메모리 정리"""
        logger.info("Cleaning up pipeline resources...")
        
        if self.idm_vton is not None:
            del self.idm_vton
            self.idm_vton = None
        
        torch.cuda.empty_cache()
        logger.info("✅ Pipeline cleanup complete")


# ===== 사용 예시 =====
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 테스트용 옷 이미지 로드 (실제 경로로 변경 필요)
    try:
        garment = Image.open("path/to/garment.jpg").convert("RGB")
    except:
        # 더미 이미지
        garment = Image.new("RGB", (768, 1024), (255, 200, 200))
        logger.warning("Using dummy garment image")
    
    # 파이프라인 초기화
    pipeline = FashionAdPipeline(device="cuda")
    
    # 광고 생성
    result = pipeline.generate(
        garment_image=garment,
        style="minimal",
        garment_description="elegant white dress",
        aspect_ratio="square"
    )
    
    # 결과 저장
    result.save("fashion_ad_result.jpg")
    logger.info("Result saved to fashion_ad_result.jpg")
    
    # 메모리 정리
    pipeline.cleanup()