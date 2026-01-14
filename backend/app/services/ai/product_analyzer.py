import os
import json
from typing import Dict, Any, Optional
from .vision_providers import GeminiVisionProvider

class ProductAnalyzer:
    """
    의류 상품 정보 자동 추출기
    Vision AI를 사용해 이미지에서 카테고리, 색상 등 추출
    """
    
    def __init__(self, provider: str = "gemini"):
    
        # 1. API 키 확인
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다. "
                ".env 파일에 API 키를 추가하세요."
            )
        
        # 2. Provider 객체 생성
        if provider == "gemini":
            self.provider = GeminiVisionProvider(api_key)
            self.provider_name = "Gemini 2.5 Flash"
        elif provider == "claude":
            # 추후 구현
            raise ValueError("Claude는 아직 지원하지 않습니다.")
        elif provider == "gpt4v":
            # 추후 구현
            raise ValueError("GPT-4V는 아직 지원하지 않습니다.")
        else:
            raise ValueError(
                f"지원하지 않는 provider: {provider}\n"
                f"사용 가능: gemini, claude, gpt4v"
            )
        
        print(f"✅ ProductAnalyzer 초기화 완료 (Provider: {self.provider_name})")

    def _create_prompt(self) -> str:
        """Vision AI용 프롬프트 생성"""
        return """
이 의류 이미지를 분석하여 아래 JSON 형식으로만 응답하세요.
다른 설명이나 마크다운 코드블록(```json)은 절대 사용하지 마세요.

{
  "category": "의류 카테고리 (예: 티셔츠, 니트, 바지, 원피스, 아우터, 액세서리)",
  "sub_category": "세부 카테고리 (예: 후드티, 맨투맨, 청바지, 슬랙스, 롱코트)",
  "color": "주요 색상 (예: 블랙, 화이트, 베이지, 네이비, 그레이, 카키)",
  "material_guess": "소재 추정 (예: 면, 폴리에스터, 니트, 데님, 울, 가죽)",
  "fit": "핏 (예: 슬림핏, 오버핏, 레귤러핏, 루즈핏)",
  "style_tags": ["스타일 태그 1-3개", "예: 캐주얼", "미니멀"],
  "confidence": 0.85
}

**주의사항:**
- 반드시 유효한 JSON 형식
- 모든 필드 포함
- confidence는 0.0 ~ 1.0 사이
- 한국어로 응답
- 추가 설명 금지

**예시:**
입력: 검은색 후드티 이미지
출력:
{
  "category": "상의",
  "sub_category": "후드티",
  "color": "블랙",
  "material_guess": "면",
  "fit": "오버핏",
  "style_tags": ["스트릿", "캐주얼"],
  "confidence": 0.88
}
""".strip()
    
    async def analyze(self, image_path: str) -> Dict[str, Any]:
        """이미지에서 상품 정보 추출"""
        try:
            # 1. 프롬프트 생성
            prompt = self._create_prompt()
            
            print(f"🔍 이미지 분석 시작: {image_path}")
            print(f"🤖 Provider: {self.provider_name}")
            
            # 2. Vision AI 호출
            result = await self.provider.analyze_image(
                image_path=image_path,
                prompt=prompt
            )
            
            # 3. 호출 실패 체크
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Vision AI 호출 실패: {error_msg}")
                return {
                    "error": f"Vision AI 호출 실패: {error_msg}",
                    "success": False
                }
            
            # 4. 응답 내용 추출
            content = result.get('content', '')
            if not content:
                print(f"❌ 빈 응답")
                return {
                    "error": "Vision AI가 빈 응답을 반환했습니다.",
                    "success": False
                }
            
            print(f"✅ Vision AI 응답 받음 ({len(content)} 글자)")
            print(f"📄 원본 응답:\n{content[:200]}...")
            
            # 5. JSON 파싱
            parsed_result = self._parse_json_response(content)
            
            return parsed_result
            
        except FileNotFoundError:
            error_msg = f"이미지 파일을 찾을 수 없습니다: {image_path}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "success": False
            }
        
        except Exception as e:
            error_msg = f"예상치 못한 오류: {type(e).__name__}: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "success": False
            }
        
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Vision AI 응답 JSON 파싱"""
        try:
            # 1. 공백 제거
            cleaned = content.strip()
            
            # 2. 마크다운 코드블록 제거
            # ```json { ... } ``` → { ... }
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]  # '```json' 제거
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]   # '```' 제거
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]  # '```' 제거
            
            # 다시 공백 제거
            cleaned = cleaned.strip()
            
            print(f"🧹 정제된 JSON:\n{cleaned[:200]}...")
            
            # 3. JSON 파싱
            parsed = json.loads(cleaned)
            
            # 4. 타입 검증
            if not isinstance(parsed, dict):
                raise ValueError(f"JSON이 dict가 아닙니다: {type(parsed)}")
            
            # 5. 기본값 설정 (누락된 필드)
            parsed.setdefault('category', '미분류')
            parsed.setdefault('sub_category', None)
            parsed.setdefault('color', '알 수 없음')
            parsed.setdefault('material_guess', None)
            parsed.setdefault('fit', None)
            parsed.setdefault('style_tags', [])
            parsed.setdefault('confidence', 0.7)  # 기본 신뢰도
            
            # 6. confidence 범위 검증
            if not (0.0 <= parsed['confidence'] <= 1.0):
                print(f"⚠️ confidence 범위 초과: {parsed['confidence']} → 0.7로 조정")
                parsed['confidence'] = 0.7
            
            # 7. success 플래그 추가
            parsed['success'] = True
            
            print(f"✅ JSON 파싱 성공")
            print(f"   카테고리: {parsed['category']}")
            print(f"   색상: {parsed['color']}")
            print(f"   신뢰도: {parsed['confidence']:.2f}")
            
            return parsed
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패
            error_msg = f"JSON 파싱 실패: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"📄 원본 내용:\n{content[:500]}")
            
            return {
                "error": error_msg,
                "raw_content": content,  # 디버깅용
                "success": False
            }
        
        except Exception as e:
            # 기타 오류
            error_msg = f"파싱 중 오류: {type(e).__name__}: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "error": error_msg,
                "raw_content": content,
                "success": False
            }