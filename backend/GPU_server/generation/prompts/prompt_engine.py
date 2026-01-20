"""
Dynamic Prompt Engine for Context-Aware Ad Generation
Vision AI 결과 기반 동적 프롬프트 생성
"""
import logging
from typing import Dict, Optional
from .style_prompts import StylePrompts


class PromptEngine:
    """
    동적 프롬프트 생성 엔진
    
    Features:
    - Vision AI 결과 기반 컨텍스트 분석
    - 스타일별 프롬프트 자동 생성
    - NSFW 필터 대응 안전 키워드 자동 추가
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.style_prompts = StylePrompts()
    
    def analyze_image_context(self, 
                             category: str = None,
                             color: str = None,
                             material: str = None,
                             style_tags: list = None) -> Dict[str, str]:
        """
        Vision AI 결과를 기반으로 이미지 컨텍스트 분석
        
        Args:
            category: 제품 카테고리 (e.g., "cardigan", "dress")
            color: 제품 색상
            material: 제품 소재
            style_tags: 스타일 태그 리스트
            
        Returns:
            컨텍스트 정보 (season, vibe, keywords)
        """
        # 카테고리별 컨텍스트 매핑
        context_map = {
            # 상의
            "cardigan": {
                "season": "autumn", 
                "vibe": "cozy cafe atmosphere, warm indoor lighting", 
                "keywords": "soft wool knitwear, casual fashion"
            },
            "sweater": {
                "season": "winter", 
                "vibe": "warm cozy interior, soft natural light", 
                "keywords": "comfortable knitwear, casual style"
            },
            "t-shirt": {
                "season": "summer", 
                "vibe": "bright casual setting, natural daylight", 
                "keywords": "casual everyday wear, comfortable cotton"
            },
            "shirt": {
                "season": "business", 
                "vibe": "professional office environment, clean lighting", 
                "keywords": "formal business attire, professional"
            },
            "blouse": {
                "season": "spring", 
                "vibe": "elegant indoor setting, soft window light", 
                "keywords": "feminine elegant style, professional"
            },
            
            # 하의
            "jeans": {
                "season": "casual", 
                "vibe": "urban street setting, natural outdoor light", 
                "keywords": "denim casual wear, everyday style"
            },
            "pants": {
                "season": "business", 
                "vibe": "professional office, clean environment", 
                "keywords": "formal business pants, professional attire"
            },
            "skirt": {
                "season": "spring", 
                "vibe": "elegant setting, soft natural light", 
                "keywords": "feminine style, elegant fashion"
            },
            
            # 원피스/세트
            "dress": {
                "season": "spring", 
                "vibe": "garden setting, soft sunlight, flowers", 
                "keywords": "elegant flowing fabric, feminine style"
            },
            "suit": {
                "season": "business", 
                "vibe": "professional office, city skyline view", 
                "keywords": "formal business suit, executive style"
            },
            
            # 아우터
            "coat": {
                "season": "winter", 
                "vibe": "urban outdoor, city street background", 
                "keywords": "winter outerwear, stylish coat"
            },
            "jacket": {
                "season": "autumn", 
                "vibe": "urban casual setting, street style", 
                "keywords": "casual jacket, trendy outerwear"
            },
            
            # 액세서리
            "bag": {
                "season": "neutral", 
                "vibe": "minimal studio setup, clean background", 
                "keywords": "fashion accessory, luxury item"
            },
            "shoes": {
                "season": "neutral", 
                "vibe": "minimal studio, professional lighting", 
                "keywords": "footwear, fashion shoes"
            },
            "hat": {
                "season": "fashion", 
                "vibe": "stylish setting, creative background", 
                "keywords": "fashion accessory, headwear"
            }
        }
        
        # 기본값
        default_context = {
            "season": "neutral", 
            "vibe": "professional studio minimal setting, clean white background", 
            "keywords": "fashion product, commercial photography"
        }
        
        # 카테고리로 컨텍스트 찾기
        context = context_map.get(
            category.lower() if category else "default", 
            default_context
        )
        
        # 색상 정보 추가
        if color:
            context["color_mood"] = self._get_color_mood(color)
        
        # 소재 정보 추가
        if material:
            context["material_desc"] = f"{material} fabric"
        
        return context
    
    def _get_color_mood(self, color: str) -> str:
        """
        색상에 따른 분위기 매핑
        
        Args:
            color: 색상명
            
        Returns:
            분위기 설명
        """
        color_moods = {
            "white": "clean bright atmosphere, pure white tones",
            "black": "sophisticated dark elegance, dramatic lighting",
            "red": "vibrant energetic mood, bold red accents",
            "blue": "calm serene atmosphere, cool blue tones",
            "green": "natural fresh feeling, green elements",
            "yellow": "bright cheerful mood, warm yellow lighting",
            "pink": "soft romantic atmosphere, gentle pink tones",
            "gray": "modern neutral mood, sophisticated gray tones",
            "brown": "warm earthy atmosphere, natural brown tones",
            "beige": "neutral elegant mood, soft beige background"
        }
        
        return color_moods.get(
            color.lower() if color else "neutral",
            "neutral professional atmosphere"
        )
    
    def generate_dynamic_prompt(self,
                               style: str = "minimal",
                               category: str = None,
                               color: str = None,
                               material: str = None,
                               style_tags: list = None,
                               user_prompt: str = None) -> Dict[str, str]:
        """
        동적 프롬프트 생성 (Vision AI 결과 기반)
        
        Args:
            style: 기본 스타일 (minimal, emotional, street, instagram)
            category: 제품 카테고리
            color: 제품 색상
            material: 제품 소재
            style_tags: 스타일 태그
            user_prompt: 사용자 커스텀 프롬프트
            
        Returns:
            positive/negative 프롬프트 딕셔너리
        """
        # 컨텍스트 분석
        context = self.analyze_image_context(category, color, material, style_tags)
        
        # 기본 스타일 프롬프트 가져오기
        base_prompts = self.style_prompts.get_safe_prompt(style)
        
        # 동적 요소 생성
        dynamic_elements = []
        
        # 카테고리 관련
        if category:
            dynamic_elements.append(f"professional {category} photography")
            dynamic_elements.append(context.get("keywords", ""))
        
        # 시즌/분위기
        dynamic_elements.append(context.get("vibe", ""))
        
        # 색상 분위기
        if color and "color_mood" in context:
            dynamic_elements.append(context["color_mood"])
        
        # 소재
        if material and "material_desc" in context:
            dynamic_elements.append(context["material_desc"])
        
        # 사용자 프롬프트 우선 적용
        if user_prompt:
            # 사용자 프롬프트에 안전 키워드 추가
            safe_user_prompt = self.style_prompts.enhance_prompt_safety(user_prompt)
            dynamic_positive = f"{safe_user_prompt}, {', '.join(dynamic_elements)}, {base_prompts['positive']}"
        else:
            dynamic_positive = f"{', '.join(dynamic_elements)}, {base_prompts['positive']}"
        
        result = {
            "positive": dynamic_positive,
            "negative": base_prompts["negative"]
        }
        
        self.logger.info(f"Generated Dynamic Prompt for {category} ({style} style)")
        self.logger.debug(f"Positive: {result['positive'][:100]}...")
        
        return result
    
    def generate_simple_prompt(self, user_prompt: str, style: str = "minimal") -> Dict[str, str]:
        """
        간단한 프롬프트 생성 (사용자 입력 기반)
        
        Args:
            user_prompt: 사용자 프롬프트
            style: 스타일
            
        Returns:
            안전성이 강화된 프롬프트
        """
        # 안전 키워드 추가
        safe_prompt = self.style_prompts.enhance_prompt_safety(user_prompt)
        
        # 스타일 프롬프트와 결합
        base_prompts = self.style_prompts.get_prompt(style)
        
        return {
            "positive": f"{safe_prompt}, {base_prompts['positive']}",
            "negative": base_prompts["negative"]
        }


# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = PromptEngine()
    
    # Vision AI 결과 기반 프롬프트
    result1 = engine.generate_dynamic_prompt(
        style="minimal",
        category="cardigan",
        color="beige",
        material="wool"
    )
    print("\n=== Dynamic Prompt (Vision AI) ===")
    print(f"Positive: {result1['positive']}")
    print(f"\nNegative: {result1['negative']}")
    
    # 사용자 입력 기반 프롬프트
    result2 = engine.generate_simple_prompt(
        user_prompt="white studio background with soft lighting",
        style="minimal"
    )
    print("\n=== Simple Prompt (User Input) ===")
    print(f"Positive: {result2['positive']}")
    print(f"\nNegative: {result2['negative']}")