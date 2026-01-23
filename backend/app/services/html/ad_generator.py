"""
광고 카피 생성 서비스
GPT-4를 사용하여 인스타그램 광고 카피를 생성하고 HTML 템플릿과 결합
"""
import os
import json
from typing import Dict, Optional
from openai import OpenAI
from datetime import datetime

from app.templates.ad_templates import AD_TEMPLATES
from app.services.template_selector import select_template


class AdGenerator:
    """광고 카피 생성 및 HTML 생성"""
    
    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-5-chat-latest" 
    
    def _build_prompt(
        self, 
        vision_result: Dict,
        template_name: str,
        user_request: Optional[str] = None
    ) -> str:
        """
        GPT-4 Few-shot 프롬프트 생성
        
        Args:
            vision_result: Vision AI 분석 결과
            template_name: 선택된 템플릿 이름
            user_request: 사용자 추가 요청 (선택)
        
        Returns:
            프롬프트 문자열
        """
        
        # 템플릿별 스타일 가이드
        style_guides = {
            "minimal": "깔끔하고 세련된 느낌. 짧고 간결한 문구. 여백의 미를 강조.",
            "bold": "강렬하고 임팩트 있는 느낌. 대문자 사용. 긴급함과 혜택 강조.",
            "vintage": "따뜻하고 향수를 불러일으키는 느낌. 우아하고 클래식한 표현."
        }
        
        template_info = AD_TEMPLATES[template_name]
        style_guide = style_guides.get(template_name, style_guides["minimal"])
        
        # Few-shot 예시
        examples = self._get_few_shot_examples(template_name)
        
        prompt = f"""당신은 인스타그램 광고 전문 카피라이터입니다.

[템플릿 스타일: {template_info['name']}]
{style_guide}

[상품 정보]
- 카테고리: {vision_result.get('category', 'N/A')}
- 서브 카테고리: {vision_result.get('sub_category', 'N/A')}
- 색상: {vision_result.get('color', 'N/A')}
- 소재: {vision_result.get('material', 'N/A')}
- 핏: {vision_result.get('fit', 'N/A')}
- 스타일: {', '.join(vision_result.get('style_tags', []))}

{f"[사용자 요청사항]\n{user_request}\n" if user_request else ""}

[Few-shot 예시]
{examples}

위 정보를 바탕으로 인스타그램 광고 카피를 생성하세요.

⚠️ 중요: 반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

{{
  "headline": "메인 헤드라인 (20자 이내)",
  "subtext": "부제 또는 서브 텍스트 (15자 이내, 선택)",
  "discount": "할인율 (예: 70% OFF)",
  "period": "기간 (MM.DD - MM.DD 형식)",
  "brand": "브랜드명 또는 이벤트명 (10자 이내)",
  "event_name": "이벤트명 (bold 템플릿용, 선택)",
  "caption": "인스타그램 캡션 (이모지 포함, 50자 이내)"
}}"""
        
        return prompt
    
    def _get_few_shot_examples(self, template_name: str) -> str:
        """
        템플릿별 Few-shot 예시 반환
        """
        examples = {
            "minimal": """예시 1:
입력: 카테고리=아우터, 색상=블랙, 스타일=미니멀
출력:
{
  "headline": "심플의 완성",
  "subtext": "블랙 아우터",
  "discount": "60% OFF",
  "period": "03.15 - 03.22",
  "brand": "SPECIAL SALE",
  "caption": "🖤 심플하게, 세련되게. 블랙 아우터 특가!"
}

예시 2:
입력: 카테고리=상의, 색상=화이트, 스타일=모던
출력:
{
  "headline": "화이트의 매력",
  "subtext": "깔끔한 디자인",
  "discount": "50% OFF",
  "period": "03.20 - 03.27",
  "brand": "NEW ARRIVAL",
  "caption": "✨ 화이트 상의로 완성하는 모던 룩"
}""",
            
            "bold": """예시 1:
입력: 카테고리=아우터, 색상=레드, 스타일=대담한
출력:
{
  "headline": "RED ALERT",
  "subtext": "당신을 위한 특별한",
  "discount": "70% OFF",
  "period": "03.15 - 03.22",
  "brand": "MEGA SALE",
  "event_name": "봄맞이 대박 세일",
  "caption": "🔥 레드 아우터 초특가! 지금 바로 GET"
}

예시 2:
입력: 카테고리=하의, 색상=블루, 스타일=강렬한
출력:
{
  "headline": "BOLD STYLE",
  "subtext": "스타일의 정석",
  "discount": "60% OFF",
  "period": "03.20 - 03.27",
  "brand": "FINAL SALE",
  "event_name": "마지막 기회",
  "caption": "⚡ 블루 하의 끝판왕! 놓치면 후회"
}""",
            
            "vintage": """예시 1:
입력: 카테고리=아우터, 색상=베이지, 스타일=빈티지
출력:
{
  "headline": "시간을 입다",
  "subtext": "빈티지 감성",
  "discount": "50% OFF",
  "period": "03.15 - 03.22",
  "brand": "CLASSIC SALE",
  "caption": "📜 클래식한 빈티지 코트의 매력"
}

예시 2:
입력: 카테고리=상의, 색상=브라운, 스타일=레트로
출력:
{
  "headline": "레트로의 귀환",
  "subtext": "따뜻한 감성",
  "discount": "60% OFF",
  "period": "03.20 - 03.27",
  "brand": "HERITAGE",
  "caption": "🍂 브라운 상의로 완성하는 레트로 룩"
}"""
        }
        
        return examples.get(template_name, examples["minimal"])
    
    def generate_ad_copy(
        self, 
        vision_result: Dict,
        user_request: Optional[str] = None
    ) -> Dict:
        """
        GPT-4로 광고 카피 생성
        
        Args:
            vision_result: Vision AI 분석 결과
            user_request: 사용자 추가 요청
        
        Returns:
            광고 카피 dict
        """
        
        # 1. 템플릿 선택
        style_tags = vision_result.get('style_tags', [])
        template_name = select_template(style_tags)
        
        # 2. 프롬프트 생성
        prompt = self._build_prompt(vision_result, template_name, user_request)
        
        # 3. GPT-4 호출
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 인스타그램 광고 전문 카피라이터입니다. 반드시 JSON 형식으로만 응답합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_completion_tokens=500,
                response_format={"type": "json_object"}  # JSON 모드 강제
            )
            
            # 4. 응답 파싱
            content = response.choices[0].message.content
            ad_copy = json.loads(content)
            
            # 5. 템플릿 이름 추가
            ad_copy['template_used'] = template_name
            
            return ad_copy
            
        except Exception as e:
            print(f"❌ GPT-4 API Error: {e}")
            # 폴백: 기본 카피 반환
            return self._get_fallback_copy(vision_result, template_name)
    
    def _get_fallback_copy(self, vision_result: Dict, template_name: str) -> Dict:
        """
        GPT-4 실패 시 기본 카피 반환
        """
        category = vision_result.get('category', '상품')
        
        return {
            "headline": f"{category} 특가",
            "subtext": "지금 바로",
            "discount": "50% OFF",
            "period": "한정 기간",
            "brand": "SPECIAL SALE",
            "event_name": "특별 이벤트",
            "caption": f"🎉 {category} 특가 진행 중!",
            "template_used": template_name
        }
    
    def generate_html(
        self,
        vision_result: Dict,
        image_url: str,
        user_request: Optional[str] = None
    ) -> Dict:
        """
        광고 카피 생성 + HTML 템플릿 결합
        
        Args:
            vision_result: Vision AI 분석 결과
            image_url: 생성된 모델 이미지 URL
            user_request: 사용자 추가 요청
        
        Returns:
            {
                'html': HTML 문자열,
                'ad_copy': 광고 카피 dict,
                'template_used': 템플릿 이름
            }
        """
        
        # 1. 광고 카피 생성
        ad_copy = self.generate_ad_copy(vision_result, user_request)
        template_name = ad_copy['template_used']
        
        # 2. 템플릿 HTML 가져오기
        template_html = AD_TEMPLATES[template_name]['html']
        
        # 3. 변수 치환
        replacements = {
            "{{IMAGE_URL}}": image_url,
            "{{HEADLINE}}": ad_copy.get('headline', '특가 이벤트'),
            "{{SUBTEXT}}": ad_copy.get('subtext', ''),
            "{{DISCOUNT}}": ad_copy.get('discount', '50% OFF'),
            "{{PERIOD}}": ad_copy.get('period', '한정 기간'),
            "{{BRAND}}": ad_copy.get('brand', 'SALE'),
            "{{EVENT_NAME}}": ad_copy.get('event_name', '특별 이벤트')
        }
        
        html = template_html
        for placeholder, value in replacements.items():
            html = html.replace(placeholder, value)
        
        return {
            'html': html,
            'ad_copy': ad_copy,
            'template_used': template_name
        }


# 테스트용
if __name__ == "__main__":
    # 테스트
    generator = AdGenerator()
    
    test_vision_result = {
        "category": "아우터",
        "sub_category": "코트",
        "material": "울",
        "fit": "오버사이즈",
        "color": "블랙",
        "style_tags": ["미니멀", "모던"]
    }
    
    test_image_url = "https://storage.googleapis.com/test/model.jpg"
    
    print("=" * 50)
    print("광고 카피 생성 테스트")
    print("=" * 50)
    
    result = generator.generate_html(
        vision_result=test_vision_result,
        image_url=test_image_url,
        user_request="세련된 느낌으로"
    )
    
    print(f"\n✅ 템플릿: {result['template_used']}")
    print(f"\n광고 카피:")
    print(json.dumps(result['ad_copy'], indent=2, ensure_ascii=False))
    print(f"\n✅ HTML 생성 완료 (길이: {len(result['html'])} 글자)")