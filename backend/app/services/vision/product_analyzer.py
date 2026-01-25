"""
제품 이미지 분석 (Vision AI)
"""
import json
from typing import Optional, Dict
from pathlib import Path
from config import settings
from .providers import GeminiVisionProvider

class ProductAnalyzer:
    """제품 이미지 분석 (Few-shot Learning 지원)"""
    
    def __init__(self, provider: str = "gemini"):
        self.provider = provider
        
        # API 키 확인
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in settings")
        
        # Provider 초기화
        if provider == "gemini":
            self.vision_provider = GeminiVisionProvider(api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        print(f"✅ ProductAnalyzer 초기화 완료: {provider}")
    
    async def analyze(
        self, 
        image_path: str,
        custom_prompt: Optional[str] = None  # ⭐ Few-shot 프롬프트
    ) -> Dict:
        """
        이미지 분석 실행 (Few-shot Learning 지원)
        
        Args:
            image_path: 이미지 파일 경로
            custom_prompt: 커스텀 프롬프트 (Few-shot Learning용, 선택)
            
        Returns:
            Dict: 분석 결과
                - success: bool
                - category, sub_category, color, material, fit, style_tags, confidence
        """
        print(f"\n🔍 이미지 분석 시작: {image_path}")
        
        # 파일 존재 확인
        if not Path(image_path).exists():
            return {
                'success': False,
                'error': f'File not found: {image_path}'
            }
        
        # ⭐ 프롬프트 선택
        if custom_prompt:
            prompt = custom_prompt
            print("🎯 Few-shot 프롬프트 사용")
        else:
            prompt = self._build_default_prompt()
            print("📝 기본 프롬프트 사용")
        
        # Vision AI 호출
        response = await self.vision_provider.analyze_image(image_path, prompt)
        
        if not response.get('success'):
            print(f"❌ Vision AI 실패: {response.get('error')}")
            return {
                'success': False,
                'error': response.get('error', 'Unknown error')
            }
        
        # JSON 파싱
        content = response.get('content', '').strip()
        
        try:
            print(f"📥 원본 응답 ({len(content)} 글자): {content[:100]}...")
            
            # Markdown 코드 블록 제거
            if content.startswith('```'):
                lines = content.split('\n')
                # ```json 또는 ``` 제거
                content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                content = content.strip()
            
            # JSON 앞뒤 불필요한 텍스트 제거
            if '{' in content and '}' in content:
                start = content.index('{')
                end = content.rindex('}') + 1
                content = content[start:end]
            
            print(f"🔧 정제된 JSON ({len(content)} 글자): {content[:100]}...")
            
            # JSON 파싱
            result = json.loads(content)
            
            # 결과 검증
            required_fields = ['category', 'color', 'confidence']
            for field in required_fields:
                if field not in result:
                    print(f"⚠️ 필수 필드 누락: {field}")
            
            print(f"✅ JSON 파싱 성공")
            print(f"   카테고리: {result.get('category')}")
            print(f"   색상: {result.get('color')}")
            print(f"   신뢰도: {result.get('confidence')}")
            
            # success 플래그 추가
            result['success'] = True
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            print(f"   문제 문자열: {content[:200]}")
            
            # Fallback 결과
            return {
                'success': False,
                'error': 'JSON parsing failed',
                'raw_response': content
            }
        except Exception as e:
            print(f"❌ 예외 발생: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_default_prompt(self) -> str:
        """
        기본 프롬프트 생성 (Few-shot 예시 없을 때)
        """
        return """
첨부된 이미지를 분석하여 다음 정보를 JSON 형식으로 반환해주세요:

1. category: 대분류 (상의/하의/아우터/원피스/신발/가방/액세서리 중 하나)
2. sub_category: 세부류 (티셔츠, 데님팬츠, 니트, 청바지, 슬랙스, 코트, 재킷 등 구체적으로)
3. color: 주요 색상 (블랙, 화이트, 네이비, 베이지 등)
4. material: 소재 추정 (면, 폴리에스터, 가죽, 데님 등)
5. fit: 핏/실루엣 (슬림, 레귤러핏, 오버핏, 루즈핏 등)
6. style_tags: 스타일 태그 배열 (["캐주얼", "미니멀"] 형태)
7. confidence: 분석 신뢰도 (0.0~1.0)

**중요**: 반드시 순수한 JSON 형식으로만 답변하고, 다른 설명이나 마크다운은 포함하지 마세요.

예시:
{
  "category": "상의",
  "sub_category": "니트",
  "color": "베이지",
  "material": "울",
  "fit": "루즈핏",
  "style_tags": ["캐주얼", "미니멀"],
  "confidence": 0.92
}
"""