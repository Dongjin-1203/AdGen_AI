"""
스타일별 AI 생성 프롬프트 (NSFW 필터 대응 강화)
"""
from typing import Dict, Any

class StylePrompts:
    """스타일별 프롬프트 프리셋"""
    
    MINIMAL = "minimal"
    EMOTIONAL = "emotional"
    STREET = "street"
    INSTAGRAM = "instagram"
    # K-Fashion Styles
    RESORT = "resort"
    RETRO = "retro"
    ROMANTIC = "romantic"

    PROMPTS: Dict[str, Dict[str, str]] = {
        MINIMAL: {
            "positive": (
                "professional product photography, commercial use, "
                "minimalist background, clean lines, solid soft colors, "
                "high quality studio lighting, safe for work, "
                "8k uhd, soft shadows, neutral tones, simple composition, "
                "professional commercial shoot"
            ),
            "negative": (
                "nsfw, inappropriate content, adult content, nudity, "
                "cluttered, messy, distracting elements, harsh shadows, "
                "complex patterns, bright neon, low quality, grainy, "
                "distorted, amateur, unprofessional"
            )
        },
        EMOTIONAL: {
            "positive": (
                "professional lifestyle photography, commercial quality, "
                "warm atmosphere, soft sunlight, nature elements, cozy vibe, "
                "safe for work, depth of field, golden hour, emotional, "
                "cinematic lighting, 8k, highly detailed, "
                "professional commercial shoot"
            ),
            "negative": (
                "nsfw, inappropriate content, adult content, nudity, "
                "cold, sterile, artificial lighting, flat, cartoon, sketch, "
                "monochrome, low resolution, ugly, blurry, "
                "amateur, unprofessional"
            )
        },
        STREET: {
            "positive": (
                "professional urban fashion photography, commercial shoot, "
                "street style, concrete texture, city background, "
                "vibrant colors, safe for work, neon lights, high contrast, "
                "dynamic lighting, trendy, sharp, 8k quality, "
                "professional commercial advertisement"
            ),
            "negative": (
                "nsfw, inappropriate content, adult content, nudity, "
                "rural, rustic, vintage, soft, pastel, plain, "
                "studio background, boring, dull, low quality, "
                "amateur, graffiti, dirty"
            )
        },
        INSTAGRAM: {
            "positive": (
                "professional influencer photography, commercial quality, "
                "instagram aesthetic, lifestyle photography, safe for work, "
                "soft natural lighting, cafe background, high engagement, "
                "trendy, social media ready, 4k quality, "
                "professional commercial shoot"
            ),
            "negative": (
                "nsfw, inappropriate content, adult content, nudity, "
                "ugly, distorted, low quality, watermark, text, "
                "bad composition, oversaturated, blurry, "
                "amateur, unprofessional"
            )
        },
        RESORT: {
            "positive": (
                "k-fashion resort look, professional vacation photography, "
                "luxury resort background, tropical plants, soft sunlight, "
                "beige and sand tones, linen texture, airy atmosphere, "
                "ocean breeze, relaxed high-end vibe, 8k uhd, "
                "commercial fashion editorial"
            ),
            "negative": (
                "nsfw, inappropriate content, adult content, nudity, "
                "cold, urban, concrete, dark, heavy, winter, "
                "crowded, messy, low quality, amateur"
            )
        },
        RETRO: {
            "positive": (
                "k-fashion newtro style, professional retro photography, "
                "90s aesthetic, vintage film grain, warm earthy tones, "
                "nostalgic atmosphere, classic patterns, dots and checks, "
                "analogue photography vibe, trendy vintage, 8k quality, "
                "commercial fashion editorial"
            ),
            "negative": (
                "nsfw, inappropriate content, adult content, nudity, "
                "futuristic, cyberpunk, neon, cold, digital, "
                "too modern, minimal, sterile, low quality"
            )
        },
        ROMANTIC: {
            "positive": (
                "k-fashion romantic style, professional fashion photography, "
                "soft pastel colors, floral garden background, dreamy lighting, "
                "feminine atmosphere, elegant, lace and ruffles vibe, "
                "spring season, lovely, 8k uhd, "
                "commercial fashion editorial"
            ),
            "negative": (
                "nsfw, inappropriate content, adult content, nudity, "
                "dark, edgy, gothic, industrial, sharp, aggressive, "
                "strong contrast, horror, low quality"
            )
        }
    }

    SAFETY_KEYWORDS = {
        "positive": "safe for work, professional, commercial use, advertisement quality",
        "negative": "nsfw, inappropriate content, adult content, nudity, explicit"
    }

    @classmethod
    def get_prompt(cls, style: str) -> Dict[str, str]:
        """스타일별 프롬프트 가져오기"""
        return cls.PROMPTS.get(style.lower(), cls.PROMPTS[cls.MINIMAL])
    
    @classmethod
    def get_safe_prompt(cls, style: str, user_prompt: str = "") -> Dict[str, str]:
        """안전성이 강화된 프롬프트 생성"""
        base_prompt = cls.get_prompt(style)
        
        if user_prompt:
            positive = f"{cls.SAFETY_KEYWORDS['positive']}, {user_prompt}, {base_prompt['positive']}"
        else:
            positive = f"{cls.SAFETY_KEYWORDS['positive']}, {base_prompt['positive']}"
        
        negative = f"{cls.SAFETY_KEYWORDS['negative']}, {base_prompt['negative']}"
        
        return {
            "positive": positive,
            "negative": negative
        }
    
    @classmethod
    def enhance_prompt_safety(cls, prompt: str) -> str:
        """기존 프롬프트에 안전 키워드 추가"""
        safety_check = ["safe for work", "professional", "commercial"]
        
        if any(keyword in prompt.lower() for keyword in safety_check):
            return prompt
        
        return f"{cls.SAFETY_KEYWORDS['positive']}, {prompt}"
    
    @classmethod
    def get_all_styles(cls) -> list:
        """사용 가능한 모든 스타일 목록"""
        return [
            cls.MINIMAL, cls.EMOTIONAL, cls.STREET, cls.INSTAGRAM,
            cls.RESORT, cls.RETRO, cls.ROMANTIC
        ]
