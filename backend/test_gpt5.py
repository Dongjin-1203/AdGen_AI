"""
GPT-5 시리즈 모델 테스트 (수정 버전)
max_completion_tokens 파라미터 사용
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import time

load_dotenv()


def test_gpt5_with_correct_params():
    """
    GPT-5 모델 올바른 파라미터로 테스트
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        return
    
    client = OpenAI(api_key=api_key)
    
    # 테스트할 모델들
    models = [
        "gpt-5-chat-latest",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
    ]
    
    print("=" * 80)
    print("GPT-5 시리즈 테스트 (올바른 파라미터)")
    print("=" * 80)
    
    results = []
    
    for model in models:
        print(f"\n🧪 {model}")
        print("-" * 80)
        
        try:
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello' in Korean."}
                ],
                max_completion_tokens=50  # ← max_tokens 대신 사용
            )
            
            elapsed = time.time() - start_time
            result = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            print(f"✅ 성공!")
            print(f"   응답: {result}")
            print(f"   토큰: {tokens}")
            print(f"   시간: {elapsed:.2f}초")
            
            results.append({
                "model": model,
                "status": "성공",
                "tokens": tokens,
                "time": elapsed
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 실패: {error_msg[:150]}")
            
            results.append({
                "model": model,
                "status": "실패",
                "error": error_msg[:200]
            })
    
    return results


def test_ad_copy_generation():
    """
    광고 카피 생성 테스트 (GPT-5 vs GPT-4o-mini)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return
    
    client = OpenAI(api_key=api_key)
    
    print("\n" + "=" * 80)
    print("광고 카피 생성 비교 테스트")
    print("=" * 80)
    
    # 광고 카피 생성 프롬프트
    prompt = """당신은 인스타그램 광고 전문 카피라이터입니다.

[상품 정보]
- 카테고리: 아우터
- 서브 카테고리: 코트
- 색상: 블랙
- 소재: 울
- 스타일: 미니멀, 모던

반드시 아래 JSON 형식으로만 응답하세요:
{
  "headline": "메인 헤드라인 (20자 이내)",
  "discount": "할인율 (예: 70% OFF)",
  "period": "기간 (MM.DD - MM.DD)",
  "brand": "브랜드명",
  "caption": "인스타그램 캡션 (이모지 포함)"
}"""
    
    models_to_test = [
        ("gpt-4o-mini", "max_tokens", 300),
        ("gpt-5-chat-latest", "max_completion_tokens", 300),
    ]
    
    for model, token_param, token_value in models_to_test:
        print(f"\n🎨 {model}")
        print("-" * 80)
        
        try:
            start_time = time.time()
            
            # 파라미터 동적 설정
            params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a creative copywriter. Always respond in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            # 모델에 따라 다른 토큰 파라미터 사용
            if token_param == "max_tokens":
                params["max_tokens"] = token_value
            else:
                params["max_completion_tokens"] = token_value
            
            response = client.chat.completions.create(**params)
            
            elapsed = time.time() - start_time
            result = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            print(f"✅ 성공!")
            print(f"\n응답:")
            print(result)
            print(f"\n토큰: {tokens}")
            print(f"시간: {elapsed:.2f}초")
            
            # JSON 파싱 시도
            try:
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].split("```")[0].strip()
                else:
                    json_str = result.strip()
                
                ad_copy = json.loads(json_str)
                print(f"\n✅ JSON 파싱 성공!")
                print(json.dumps(ad_copy, indent=2, ensure_ascii=False))
                
            except Exception as parse_error:
                print(f"\n⚠️ JSON 파싱 실패: {parse_error}")
            
        except Exception as e:
            print(f"❌ 실패: {str(e)[:200]}")


def performance_comparison():
    """
    성능 비교: 속도, 토큰, 품질
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return
    
    client = OpenAI(api_key=api_key)
    
    print("\n" + "=" * 80)
    print("성능 비교 (10번 평균)")
    print("=" * 80)
    
    test_prompt = "인스타그램 광고 카피: 블랙 미니멀 코트, 70% 할인"
    
    models = [
        ("gpt-4o-mini", "max_tokens"),
        ("gpt-5-chat-latest", "max_completion_tokens"),
    ]
    
    for model, token_param in models:
        print(f"\n📊 {model}")
        print("-" * 80)
        
        times = []
        tokens_list = []
        
        for i in range(3):  # 3번 테스트
            try:
                start = time.time()
                
                params = {
                    "model": model,
                    "messages": [{"role": "user", "content": test_prompt}]
                }
                
                if token_param == "max_tokens":
                    params["max_tokens"] = 100
                else:
                    params["max_completion_tokens"] = 100
                
                response = client.chat.completions.create(**params)
                
                elapsed = time.time() - start
                times.append(elapsed)
                tokens_list.append(response.usage.total_tokens)
                
            except Exception as e:
                print(f"   {i+1}회차 실패: {str(e)[:50]}")
                continue
        
        if times:
            avg_time = sum(times) / len(times)
            avg_tokens = sum(tokens_list) / len(tokens_list)
            
            print(f"   평균 응답 시간: {avg_time:.2f}초")
            print(f"   평균 토큰: {avg_tokens:.1f}")
            print(f"   성공률: {len(times)}/3")


if __name__ == "__main__":
    # 1. 기본 작동 테스트
    results = test_gpt5_with_correct_params()
    
    # 2. 광고 카피 생성 테스트
    test_ad_copy_generation()
    
    # 3. 성능 비교
    performance_comparison()
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📋 최종 결론")
    print("=" * 80)
    
    if results:
        working_models = [r for r in results if r['status'] == '성공']
        
        if working_models:
            print("\n✅ 작동하는 GPT-5 모델:")
            for r in working_models:
                print(f"   - {r['model']}")
                print(f"     토큰: {r['tokens']}, 시간: {r['time']:.2f}초")
            
            print("\n💡 추천:")
            print("   gpt-5-chat-latest 사용 가능")
            print("   → 성능 및 비용을 gpt-4o-mini와 비교 후 결정")
        else:
            print("\n⚠️ 모든 GPT-5 모델 실패")
            print("   → gpt-4o-mini 사용 권장")