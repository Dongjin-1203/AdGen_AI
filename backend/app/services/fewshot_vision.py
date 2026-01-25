"""
Few-shot Learning을 활용한 Vision AI 분석기

보상 점수가 높은 예시를 프롬프트에 포함하여 정확도 향상
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Models import (실제 경로에 맞게 수정 필요)
from app.models.schemas import UserContent
from app.models.reward_system import AIPrediction, RewardScore

class FewShotVisionAnalyzer:
    """보상 점수 기반 Few-shot Learning Vision 분석기"""
    
    def __init__(self, db: Session):
        self.db = db
        self.min_examples = 2  # 최소 예시 개수
        self.max_examples = 5  # 최대 예시 개수
        self.min_score = 5     # 최소 보상 점수 (6점 만점 중 5점)
    
    def get_high_quality_examples(
        self, 
        category: str, 
        limit: int = 5
    ) -> List[Dict]:
        """카테고리별 고품질 예시 가져오기"""
        # 최근 3개월 데이터만 사용 (신선도 유지)
        three_months_ago = datetime.now() - timedelta(days=90)
        
        # 보상 점수 5점 이상 + 같은 카테고리
        high_score_samples = self.db.query(
            RewardScore,
            UserContent
        ).join(
            UserContent, RewardScore.content_id == UserContent.content_id
        ).filter(
            RewardScore.reward_score >= self.min_score,
            UserContent.category == category,
            RewardScore.created_at >= three_months_ago
        ).order_by(
            RewardScore.reward_score.desc(),
            RewardScore.created_at.desc()
        ).limit(limit).all()
        
        examples = []
        for score, content in high_score_samples:
            examples.append({
                "category": content.category,
                "color": content.color,
                "material": content.material,
                "fit": content.fit,
                "style_tags": content.style_tags,
                "pattern": content.pattern,
                "reward_score": score.reward_score,
                "description": self._generate_description(content)
            })
        
        return examples
    
    def _generate_description(self, content) -> str:
        """컨텐츠 정보를 자연어 설명으로 변환"""
        desc_parts = []
        
        if content.category:
            desc_parts.append(f"{content.category}")
        
        if content.color:
            desc_parts.append(f"in {content.color} color")
        
        if content.material:
            desc_parts.append(f"made of {content.material}")
        
        if content.fit:
            desc_parts.append(f"with {content.fit} fit")
        
        return " ".join(desc_parts)
    
    def build_fewshot_prompt(self, category: str) -> Optional[str]:
        """Few-shot 프롬프트 생성"""
        examples = self.get_high_quality_examples(category, self.max_examples)
        
        if len(examples) < self.min_examples:
            print(f"⚠️ Few-shot 예시 부족: {len(examples)}개 (최소 {self.min_examples}개 필요)")
            return None
        
        # 프롬프트 구성
        prompt = "You are an expert fashion product analyzer. Here are some examples of ACCURATE product analysis:\n\n"
        
        for i, ex in enumerate(examples, 1):
            prompt += f"=== Example {i} (Accuracy: {ex['reward_score']}/6) ===\n"
            prompt += f"Product: {ex['description']}\n"
            prompt += f"Analysis:\n"
            prompt += f"  - Category: {ex['category']}\n"
            prompt += f"  - Color: {ex['color']}\n"
            prompt += f"  - Material: {ex['material']}\n"
            prompt += f"  - Fit: {ex['fit']}\n"
            prompt += f"  - Style Tags: {ex['style_tags']}\n"
            prompt += f"  - Pattern: {ex['pattern']}\n\n"
        
        prompt += "Now analyze the new product image with the SAME LEVEL OF ACCURACY.\n"
        prompt += "Follow the exact format shown in the examples above.\n"
        prompt += "Pay special attention to:\n"
        prompt += "1. Precise category classification\n"
        prompt += "2. Accurate color identification\n"
        prompt += "3. Correct material recognition\n"
        prompt += "4. Appropriate fit description\n"
        prompt += "5. Relevant style tags\n"
        prompt += "6. Clear pattern identification\n"
        
        return prompt
    
    def get_category_statistics(self) -> Dict[str, Dict]:
        """카테고리별 통계 정보"""
        
        categories = ["상의", "하의", "드레스", "아우터"]
        stats = {}
        
        for category in categories:
            # 해당 카테고리의 평균 보상 점수
            avg_score = self.db.query(
                func.avg(RewardScore.reward_score)
            ).join(
                UserContent, RewardScore.content_id == UserContent.content_id
            ).filter(
                UserContent.category == category
            ).scalar() or 0
            
            # 고품질 예시 개수
            high_quality_count = self.db.query(
                func.count(RewardScore.reward_score)
            ).join(
                UserContent, RewardScore.content_id == UserContent.content_id
            ).filter(
                UserContent.category == category,
                RewardScore.reward_score >= self.min_score
            ).scalar() or 0
            
            # 총 데이터 개수
            total_count = self.db.query(
                func.count(UserContent.content_id)
            ).filter(
                UserContent.category == category
            ).scalar() or 0
            
            stats[category] = {
                "avg_score": round(avg_score, 2),
                "accuracy": round((avg_score / 6) * 100, 2),
                "high_quality_count": high_quality_count,
                "total_count": total_count,
                "has_enough_examples": high_quality_count >= self.min_examples
            }
        
        return stats
    
    def get_improvement_suggestions(self, category: str) -> List[str]:
        """카테고리별 개선 제안"""
        
        stats = self.get_category_statistics().get(category, {})
        suggestions = []
        
        if not stats:
            return ["No data available for this category"]
        
        accuracy = stats.get("accuracy", 0)
        high_quality_count = stats.get("high_quality_count", 0)
        
        if accuracy < 70:
            suggestions.append(f"⚠️ Low accuracy ({accuracy}%) - Need more training data")
        
        if high_quality_count < self.min_examples:
            suggestions.append(f"⚠️ Not enough examples ({high_quality_count}/{self.min_examples}) - Cannot use Few-shot learning yet")
        
        if accuracy >= 80 and high_quality_count >= 5:
            suggestions.append(f"✅ Good performance ({accuracy}%) - Few-shot learning is working well")
        
        return suggestions


class EnhancedVisionAnalyzer:
    """Few-shot learning을 통합한 Vision AI 분석기"""
    
    def __init__(self, db: Session, base_analyzer):
        """
        Args:
            db: Database session
            base_analyzer: 기존 ProductAnalyzer 인스턴스
        """
        self.db = db
        self.base_analyzer = base_analyzer
        self.fewshot_analyzer = FewShotVisionAnalyzer(db)
    
    async def analyze(
        self, 
        image_path: str, 
        category: str = None,
        use_fewshot: bool = True
    ) -> Dict:
        """이미지 분석 (Few-shot learning 적용)"""
        custom_prompt = None
        
        # Few-shot 프롬프트 생성 시도
        if use_fewshot and category:
            custom_prompt = self.fewshot_analyzer.build_fewshot_prompt(category)
            
            if custom_prompt:
                print(f"✅ Few-shot learning 적용: {category}")
                print(f"   고품질 예시 사용: {self.fewshot_analyzer.max_examples}개")
            else:
                print(f"⚠️ Few-shot 예시 부족, 기본 프롬프트 사용")
        
        # Vision AI 분석 실행
        result = await self.base_analyzer.analyze(
            image_path,
            custom_prompt=custom_prompt  # ⭐ custom_prompt 전달
        )
        
        return result
    
    def get_analytics_dashboard(self) -> Dict:
        """Few-shot learning 대시보드 데이터"""
        
        stats = self.fewshot_analyzer.get_category_statistics()
        
        dashboard = {
            "overall": {
                "total_categories": len(stats),
                "avg_accuracy": round(
                    sum(s["accuracy"] for s in stats.values()) / len(stats), 2
                ) if stats else 0,
                "ready_for_fewshot": sum(
                    1 for s in stats.values() if s["has_enough_examples"]
                )
            },
            "categories": stats,
            "recommendations": []
        }
        
        # 전체 권장사항
        for category, stat in stats.items():
            suggestions = self.fewshot_analyzer.get_improvement_suggestions(category)
            dashboard["recommendations"].extend([
                f"{category}: {sug}" for sug in suggestions
            ])
        
        return dashboard


# ===== 유틸리티 함수 =====

def print_fewshot_statistics(db: Session):
    """Few-shot learning 통계 출력"""
    
    analyzer = FewShotVisionAnalyzer(db)
    stats = analyzer.get_category_statistics()
    
    print("\n" + "="*60)
    print("📊 Few-shot Learning 통계")
    print("="*60)
    
    for category, stat in stats.items():
        print(f"\n{category}:")
        print(f"  평균 점수: {stat['avg_score']}/6 ({stat['accuracy']}%)")
        print(f"  고품질 예시: {stat['high_quality_count']}개")
        print(f"  전체 데이터: {stat['total_count']}개")
        print(f"  Few-shot 준비: {'✅ 가능' if stat['has_enough_examples'] else '❌ 예시 부족'}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # 테스트 코드
    from app.db.base import get_db
    
    db = next(get_db())
    
    # 통계 출력
    print_fewshot_statistics(db)
    
    # Few-shot 프롬프트 생성 테스트
    analyzer = FewShotVisionAnalyzer(db)
    prompt = analyzer.build_fewshot_prompt("상의")
    
    if prompt:
        print("\n" + "="*60)
        print("📝 생성된 Few-shot 프롬프트:")
        print("="*60)
        print(prompt)
    
    db.close()