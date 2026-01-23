"""
OpenAI API 사용 가능한 모델 확인 스크립트
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드 
load_dotenv() 

def check_available_models():
    """
    현재 API 키로 사용 가능한 모든 모델 조회
    """
    
    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("export OPENAI_API_KEY=sk-proj-xxxxx")
        return
    
    print(f"✅ API Key 확인: {api_key[:20]}...")
    print("\n" + "=" * 70)
    print("사용 가능한 OpenAI 모델 조회 중...")
    print("=" * 70)
    
    try:
        client = OpenAI(api_key=api_key)
        
        # 모든 모델 리스트 가져오기
        models = client.models.list()
        
        # GPT 모델만 필터링
        gpt_models = []
        chat_models = []
        other_models = []
        
        for model in models.data:
            model_id = model.id
            
            if 'gpt' in model_id.lower():
                if 'gpt-4' in model_id.lower():
                    gpt_models.append(model_id)
                elif 'gpt-3.5' in model_id.lower():
                    chat_models.append(model_id)
                else:
                    other_models.append(model_id)
            elif 'text-' in model_id or 'dall-e' in model_id or 'whisper' in model_id or 'tts' in model_id:
                other_models.append(model_id)
        
        # GPT-4 모델 출력
        print("\n🔥 GPT-4 모델 (광고 카피 생성 추천)")
        print("-" * 70)
        if gpt_models:
            for i, model in enumerate(sorted(gpt_models), 1):
                # 가격 정보 추가
                if 'gpt-4o' in model and 'mini' in model:
                    price = "매우 저렴 (~₩4/회)"
                    recommendation = "✅ 추천! (비용 효율적)"
                elif 'gpt-4o' in model:
                    price = "보통 (~₩40/회)"
                    recommendation = "✅ 추천! (고품질)"
                elif 'gpt-4-turbo' in model:
                    price = "비쌈 (~₩80/회)"
                    recommendation = "⚠️ 비용 주의"
                else:
                    price = "가격 확인 필요"
                    recommendation = ""
                
                print(f"{i:2d}. {model:40s} {price:25s} {recommendation}")
        else:
            print("사용 가능한 GPT-4 모델이 없습니다.")
        
        # GPT-3.5 모델 출력
        print("\n💬 GPT-3.5 모델")
        print("-" * 70)
        if chat_models:
            for i, model in enumerate(sorted(chat_models), 1):
                print(f"{i:2d}. {model}")
        else:
            print("사용 가능한 GPT-3.5 모델이 없습니다.")
        
        # 기타 모델
        if other_models:
            print("\n🔧 기타 모델 (일부)")
            print("-" * 70)
            for i, model in enumerate(sorted(other_models)[:10], 1):
                print(f"{i:2d}. {model}")
            
            if len(other_models) > 10:
                print(f"... 외 {len(other_models) - 10}개 모델")
        
        print("\n" + "=" * 70)
        print(f"총 {len(models.data)}개 모델 사용 가능")
        print("=" * 70)
        
        # 추천 모델
        print("\n💡 광고 카피 생성 추천 모델:")
        print("-" * 70)
        
        recommendations = []
        for model in gpt_models:
            if 'gpt-4o-mini' in model:
                recommendations.append((model, "최고 추천! (비용 대비 성능 우수)"))
            elif 'gpt-4o' in model and 'mini' not in model:
                recommendations.append((model, "추천! (고품질 출력)"))
        
        if recommendations:
            for model, reason in recommendations[:3]:
                print(f"✅ {model}")
                print(f"   → {reason}\n")
        else:
            print("⚠️ gpt-4o 모델을 찾을 수 없습니다.")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        print("\nAPI 키를 확인해주세요:")
        print("1. https://platform.openai.com/api-keys")
        print("2. API 키가 유효한지 확인")
        print("3. 요금 한도가 설정되었는지 확인")


def test_chat_completion():
    """
    간단한 채팅 테스트로 API 작동 확인
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return
    
    print("\n" + "=" * 70)
    print("GPT-4o-mini 테스트 (간단한 메시지 전송)")
    print("=" * 70)
    
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API works!' in Korean."}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"\n✅ 테스트 성공!")
        print(f"응답: {result}")
        print(f"사용 토큰: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")


if __name__ == "__main__":
    check_available_models()
    test_chat_completion()