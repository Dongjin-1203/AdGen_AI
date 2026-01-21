"""
Female Model Selector for K-Fashion Dataset
스타일별 여성 모델 선택기
"""
import os
import json
import random
from typing import Dict, List, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class FemaleModelSelector:
    """
    K-Fashion 데이터셋에서 스타일별 여성 모델 선택
    
    지원 스타일:
    - resort: 리조트 스타일
    - retro: 레트로/빈티지 스타일  
    - romantic: 로맨틱 스타일
    """
    
    # 프론트엔드 스타일 → K-Fashion 스타일 매핑
    STYLE_MAPPING = {
        'minimal': 'resort',      # 미니멀 → 리조트
        'vintage': 'retro',       # 빈티지 → 레트로
        'modern': 'retro',        # 모던 → 레트로
        'natural': 'romantic',    # 내추럴 → 로맨틱
        'luxury': 'romantic',     # 럭셔리 → 로맨틱
        
        # K-Fashion 스타일 직접 사용
        'resort': 'resort',
        'retro': 'retro',
        'romantic': 'romantic',
    }
    
    def __init__(self, assets_dir: str = "assets/female_models"):
        """
        초기화
        
        Args:
            assets_dir: K-Fashion 데이터셋 디렉토리 경로
        """
        self.assets_dir = assets_dir
        self.models_cache: Dict[str, List[Dict]] = {}
        
        # 초기화 시 메타데이터 로드
        self._load_models_metadata()
    
    def _load_models_metadata(self):
        """30개 모델의 메타데이터 로드"""
        logger.info(f"Loading models metadata from {self.assets_dir}")
        
        styles = ['resort', 'retro', 'romantic']
        
        for style in styles:
            style_dir = os.path.join(self.assets_dir, style)
            
            if not os.path.exists(style_dir):
                logger.warning(f"Style directory not found: {style_dir}")
                self.models_cache[style] = []
                continue
            
            models = []
            
            # 스타일 폴더 내의 모든 .json 파일 스캔
            for filename in sorted(os.listdir(style_dir)):
                if not filename.endswith('.json'):
                    continue
                
                json_path = os.path.join(style_dir, filename)
                image_filename = filename.replace('.json', '.jpg')
                image_path = os.path.join(style_dir, image_filename)
                
                # 이미지 파일 존재 확인
                if not os.path.exists(image_path):
                    logger.warning(f"Image not found: {image_path}")
                    continue
                
                # JSON 메타데이터 파싱
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    model_info = {
                        'style': style,
                        'image_path': image_path,
                        'json_path': json_path,
                        'filename': image_filename,
                        'metadata': metadata
                    }
                    
                    models.append(model_info)
                    
                except Exception as e:
                    logger.error(f"Failed to load metadata from {json_path}: {e}")
                    continue
            
            self.models_cache[style] = models
            logger.info(f"Loaded {len(models)} models for style '{style}'")
        
        total_models = sum(len(models) for models in self.models_cache.values())
        logger.info(f"Total models loaded: {total_models}")
    
    def select_model(
        self, 
        style: str, 
        index: Optional[int] = None
    ) -> Dict:
        """
        스타일에 맞는 모델 선택
        
        Args:
            style: 스타일 (minimal, vintage, modern, natural, luxury, resort, retro, romantic)
            index: 특정 모델 인덱스 (None이면 랜덤 선택)
        
        Returns:
            {
                "style": "resort",
                "image_path": "assets/female_models/resort/resort_00.jpg",
                "json_path": "assets/female_models/resort/resort_00.json",
                "filename": "resort_00.jpg",
                "image": PIL.Image,
                "metadata": {...}
            }
        
        Raises:
            ValueError: 지원하지 않는 스타일이거나 모델이 없는 경우
        """
        # 스타일 정규화 (소문자)
        style = style.lower().strip()
        
        # 스타일 매핑
        if style not in self.STYLE_MAPPING:
            available_styles = ', '.join(sorted(self.STYLE_MAPPING.keys()))
            raise ValueError(
                f"Unsupported style: '{style}'. "
                f"Available styles: {available_styles}"
            )
        
        mapped_style = self.STYLE_MAPPING[style]
        
        # 해당 스타일의 모델 리스트 가져오기
        if mapped_style not in self.models_cache:
            raise ValueError(f"No models found for style: '{mapped_style}'")
        
        models = self.models_cache[mapped_style]
        
        if not models:
            raise ValueError(f"No models available for style: '{mapped_style}'")
        
        # 모델 선택
        if index is not None:
            # 특정 인덱스 선택
            if index < 0 or index >= len(models):
                raise ValueError(
                    f"Index {index} out of range. "
                    f"Available indices: 0-{len(models)-1}"
                )
            selected_model = models[index]
            logger.info(
                f"Selected model by index: {selected_model['filename']} "
                f"(style={style}→{mapped_style}, index={index})"
            )
        else:
            # 랜덤 선택
            selected_model = random.choice(models)
            logger.info(
                f"Randomly selected model: {selected_model['filename']} "
                f"(style={style}→{mapped_style})"
            )
        
        # 이미지 로드
        try:
            image = Image.open(selected_model['image_path']).convert('RGB')
            result = selected_model.copy()
            result['image'] = image
            
            logger.info(f"Image loaded: {image.size}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load image: {selected_model['image_path']}: {e}")
            raise RuntimeError(f"Failed to load model image: {e}")
    
    def get_available_styles(self) -> List[str]:
        """사용 가능한 모든 스타일 반환"""
        return sorted(self.STYLE_MAPPING.keys())
    
    def get_model_count(self, style: str) -> int:
        """특정 스타일의 모델 개수 반환"""
        mapped_style = self.STYLE_MAPPING.get(style.lower())
        if not mapped_style:
            return 0
        return len(self.models_cache.get(mapped_style, []))
    
    def get_all_models_info(self) -> Dict[str, int]:
        """모든 스타일별 모델 개수 반환"""
        return {
            style: len(models) 
            for style, models in self.models_cache.items()
        }


# ===== 사용 예시 =====
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 선택기 초기화
    selector = FemaleModelSelector()
    
    # 사용 가능한 스타일 출력
    print("Available styles:", selector.get_available_styles())
    print("Model counts:", selector.get_all_models_info())
    
    # 랜덤 선택
    model = selector.select_model('minimal')
    print(f"\nSelected: {model['filename']}")
    print(f"Style mapping: minimal → {model['style']}")
    print(f"Image size: {model['image'].size}")
    
    # 특정 인덱스 선택
    model = selector.select_model('vintage', index=0)
    print(f"\nSelected by index: {model['filename']}")
    print(f"Style mapping: vintage → {model['style']}")