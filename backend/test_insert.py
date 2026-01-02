"""
테스트 데이터 삽입
실제 DB에 데이터가 잘 들어가는지 확인
"""
from app.db.base import SessionLocal
from app.models.schemas import User, Shop, Product
from sqlalchemy.sql import func
import uuid

def test_insert_data():
    db = SessionLocal()
    
    try:
        # 1. 테스트 사용자 생성
        test_user = User(
            user_id=str(uuid.uuid4()),
            email="test@example.com",
            phone="010-1234-5678",
            name="테스트 사용자",
            hashed_password="temporary_hashed_password"
        )
        db.add(test_user)
        db.commit()
        print(f"✅ User 생성 성공: {test_user.user_id}")
        
        # 2. 테스트 매장 생성
        test_shop = Shop(
            shop_id=str(uuid.uuid4()),
            user_id=test_user.user_id,  # 위에서 만든 사용자
            shop_name="테스트 패션 매장",
            location="서울 강남구"
        )
        db.add(test_shop)
        db.commit()
        print(f"✅ Shop 생성 성공: {test_shop.shop_id}")
        
        # 3. 테스트 상품 생성
        test_product = Product(
            product_id=str(uuid.uuid4()),
            shop_id=test_shop.shop_id,  # 위에서 만든 매장
            product_name="검은색 롱코트",
            category="아우터",
            color="블랙",
            price=190000,
            original_image_url="/uploads/test_coat.jpg"
        )
        db.add(test_product)
        db.commit()
        print(f"✅ Product 생성 성공: {test_product.product_id}")
        
        # 4. 관계 확인
        print("\n📊 관계 확인:")
        print(f"User {test_user.name}의 매장: {test_user.shops}")
        print(f"Shop {test_shop.shop_name}의 상품: {test_shop.products}")
        
        print("\n✅ 모든 테스트 데이터 삽입 성공!")
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_insert_data()