"""
스타일별 AI 생성 프롬프트
"""
from typing import Dict, Any

class StylePrompts:
    MINIMAL = "minimal"
    EMOTIONAL = "emotional"
    STREET = "street"

    PROMPTS: Dict[str, Dict[str, str]] = {
        MINIMAL: {
            "positive": "minimalist background, clean lines, solid soft colors, high quality, studio lighting, product photography, 8k uhd, soft shadows, neutral tones, simple composition, professional",
            "negative": "cluttered, messy, distracting elements, harsh shadows, complex patterns, bright neon, low quality, grainy, distorted"
        },
        EMOTIONAL: {
            "positive": "warm atmosphere, soft sunlight, nature elements, cozy vibe, lifestyle photography, depth of field, golden hour, emotional, cinematic lighting, 8k, highly detailed",
            "negative": "cold, sterile, artificial lighting, flat, cartoon, sketch, monochrome, low resolution, ugly, blurry"
        },
        STREET: {
            "positive": "urban street style, concrete texture, city background, vibrant colors, hip hop vibe, neon lights, high contrast, dynamic lighting, fashion photography, trendy, sharp",
            "negative": "rural, rustic, vintage, soft, pastel, plain, studio background, boring, dull, low quality"
        }
    }

    @classmethod
    def get_prompt(cls, style: str) -> Dict[str, str]:
        return cls.PROMPTS.get(style.lower(), cls.PROMPTS[cls.MINIMAL])