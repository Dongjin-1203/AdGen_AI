# AdGen_AI - 소규모 패션 쇼핑몰을 위한 AI 광고 자동 생성 서비스

---

## 서비스 시연 영상
<!-- TODO: 서비스 시연 GIF 또는 동영상 추가 -->
![service_demo](링크 추가 예정)

## 실시간 데모
[접속 링크](서비스 URL 추가 예정)

---

# 1. 프로젝트 개요

- **소규모 오프라인 패션 쇼핑몰 전문 AI 광고 제작 서비스 – 'Fashion AI'**
- 상품 사진을 업로드하고 간단한 명령만 입력하면 1분 내 인스타그램 광고 완성

> **배경**: 소규모 패션 쇼핑몰 사장님들은 신상품이 입고될 때마다 제품 촬영부터 편집, 캡션 작성까지 모든 과정을 혼자 처리해야 합니다. 포토샵이나 디자인 툴을 다루지 못하는 경우가 많고, 디자이너를 고용할 여유도 없어 마케팅에 많은 어려움을 겪고 있습니다.
> 
> **목표**: 휴대폰으로 찍은 상품 사진만으로 AI가 자동으로 배경을 제거하고, 3가지 스타일의 광고 이미지를 생성하며, 인스타그램 캡션과 해시태그까지 작성해주는 서비스를 개발하여 소상공인의 마케팅 부담을 획기적으로 줄이고자 합니다.
> 
> **기대 효과**: AI 기술을 통해 광고 제작 시간을 30분에서 1분으로 단축(97% 감소)하고, 디자이너 외주 비용을 연간 1,000만원 이상 절감할 수 있습니다.

---

# 2. 프로젝트 사용 방법

## 🌐 웹 서비스 사용 (일반 사용자)

**Fashion AI를 바로 사용하세요!**

- 🎨 **데모 서비스**: [Fashion AI 웹앱](서비스 URL 추가 예정)
- 💡 **사용법**:
  1. 위 링크 접속
  2. 상품 사진 업로드 (드래그 앤 드롭 또는 카메라 촬영)
  3. 간단한 명령 입력 (예: "검은색 롱코트, 19만원, 오늘 입고")
  4. AI가 3가지 스타일 이미지 + 캡션 + 해시태그 자동 생성
  5. 인스타그램에 바로 공유
- ⚡ **생성 시간**: 약 30초 이내
- 🎯 **지원 스타일**: 미니멀, 감성, 스트릿

---

## 💻 로컬 개발 환경 구축 (개발자용)

### Prerequisites
- Node.js 18+ 및 npm 설치
- Python 3.11+ 설치
- Docker 및 Docker Compose 설치
- 저장소 클론 완료
- 환경변수 설정 완료

### 환경 설정

**1. .env 파일 생성**

프로젝트 루트에 `.env` 파일 생성:

```env
# OpenAI API (텍스트 생성)
OPENAI_API_KEY="sk-..."

# Replicate API (이미지 생성, 선택 사항)
REPLICATE_API_TOKEN="r8_..."

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/fashionai"
REDIS_URL="redis://localhost:6379"

# Cloud Storage
GCS_BUCKET_NAME="fashion-ai-images"
GCS_PROJECT_ID="your-project-id"

# Instagram API (선택 사항)
INSTAGRAM_CLIENT_ID="..."
INSTAGRAM_CLIENT_SECRET="..."

# Stripe (결제, 선택 사항)
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_PUBLISHABLE_KEY="pk_test_..."

# Application
NODE_ENV="development"
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

**2. 프론트엔드 설정**

```bash
# 프로젝트 루트로 이동
cd AdGen_AI

# 프론트엔드 폴더로 이동
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

**3. 백엔드 설정**

```bash
# 백엔드 폴더로 이동
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 실행
uvicorn main:app --reload --port 8000
```

**4. Docker Compose로 전체 스택 실행**

```bash
# 프로젝트 루트에서
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

### 실행 방법

**1. 전체 서비스 실행**
```bash
# Docker Compose 사용 (권장)
docker-compose up

# 또는 개별 실행
# Terminal 1: Frontend
cd frontend && npm run dev

# Terminal 2: Backend
cd backend && uvicorn main:app --reload

# Terminal 3: Celery Worker
cd backend && celery -A app.celery worker --loglevel=info

# Terminal 4: Redis (Docker)
docker run -d -p 6379:6379 redis:alpine
```

**2. 데이터베이스 초기화**
```bash
cd backend
python scripts/init_db.py
```

**3. AI 모델 테스트**
```bash
cd backend
python scripts/test_models.py
```

> ⚠️ **주의**: 
> - OpenAI API 사용 시 비용이 발생할 수 있습니다.
> - Stable Diffusion 모델은 GPU가 있어야 빠르게 동작합니다.
> - 로컬 테스트 시 Replicate API 사용을 권장합니다.

---

# 3. 프로젝트 구조

```
AdGen_AI/
│
├── README.md
├── docker-compose.yml           # Docker 컨테이너 구성
├── .env.example                 # 환경변수 예시
│
├── frontend/                    # Next.js 프론트엔드
│   ├── public/                  # 정적 파일
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   │   ├── page.tsx         # 메인 페이지
│   │   │   ├── upload/          # 이미지 업로드 페이지
│   │   │   └── dashboard/       # 대시보드
│   │   ├── components/          # React 컴포넌트
│   │   │   ├── ImageUpload.tsx
│   │   │   ├── StyleSelector.tsx
│   │   │   ├── CaptionEditor.tsx
│   │   │   └── PreviewGallery.tsx
│   │   ├── hooks/               # Custom React Hooks
│   │   ├── lib/                 # 유틸리티 함수
│   │   └── styles/              # CSS 스타일
│   ├── package.json
│   ├── next.config.js
│   └── tsconfig.json
│
├── backend/                     # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── api/                 # API 엔드포인트
│   │   │   ├── routes/
│   │   │   │   ├── images.py    # 이미지 업로드/생성
│   │   │   │   ├── users.py     # 사용자 관리
│   │   │   │   ├── products.py  # 상품 관리
│   │   │   │   └── analytics.py # 사용 통계
│   │   │   └── deps.py          # 의존성 주입
│   │   ├── core/                # 핵심 설정
│   │   │   ├── config.py        # 환경 설정
│   │   │   ├── security.py      # JWT 인증
│   │   │   └── celery_app.py    # Celery 설정
│   │   ├── models/              # SQLAlchemy 모델
│   │   │   ├── user.py
│   │   │   ├── shop.py
│   │   │   ├── product.py
│   │   │   └── generated_image.py
│   │   ├── schemas/             # Pydantic 스키마
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   └── image.py
│   │   ├── services/            # 비즈니스 로직
│   │   │   ├── ai/              # AI 서비스
│   │   │   │   ├── image_processor.py    # 이미지 처리
│   │   │   │   ├── background_remover.py # 누끼 제거
│   │   │   │   ├── background_generator.py # 배경 생성
│   │   │   │   ├── caption_generator.py   # 캡션 생성
│   │   │   │   └── ner_parser.py          # 명령어 파싱
│   │   │   ├── storage.py       # 파일 저장
│   │   │   └── instagram.py     # 인스타그램 연동
│   │   ├── workers/             # Celery 워커
│   │   │   ├── image_tasks.py   # 이미지 생성 태스크
│   │   │   └── text_tasks.py    # 텍스트 생성 태스크
│   │   └── db/                  # 데이터베이스
│   │       ├── base.py
│   │       └── session.py
│   ├── alembic/                 # DB 마이그레이션
│   ├── scripts/                 # 유틸리티 스크립트
│   │   ├── init_db.py
│   │   └── test_models.py
│   ├── tests/                   # 테스트 코드
│   ├── requirements.txt
│   └── Dockerfile
│
├── models/                      # AI 모델 파일 (선택)
│   └── .gitkeep
│
├── docs/                        # 프로젝트 문서
│   ├── architecture.md          # 시스템 아키텍처
│   ├── api_reference.md         # API 문서
│   ├── deployment.md            # 배포 가이드
│
│
└── scripts/                     # 개발 스크립트
    ├── setup.sh                 # 초기 설정
    └── deploy.sh                # 배포 스크립트
```

## 주요 디렉토리 설명

### Frontend (`/frontend`)
- Next.js 14 기반 PWA 웹 애플리케이션
- TypeScript 사용
- Tailwind CSS로 스타일링
- React Hook Form으로 폼 관리

### Backend (`/backend`)
- FastAPI로 RESTful API 제공
- SQLAlchemy로 데이터베이스 ORM
- Celery로 비동기 작업 처리
- JWT 기반 인증

### AI Services (`/backend/app/services/ai`)
- **image_processor.py**: 이미지 처리 파이프라인 orchestration
- **background_remover.py**: RMBG-2.0 모델로 누끼 제거
- **background_generator.py**: Stable Diffusion XL로 배경 생성
- **caption_generator.py**: GPT-5로 캡션 및 해시태그 생성
- **ner_parser.py**: spaCy로 명령어에서 상품 정보 추출

### Models (`/models`)
- AI 모델 파일 저장 (필요 시)
- 대부분 API 사용으로 선택 사항

---

# 4. 팀 소개

> 29일 동안 소상공인을 위한 실용적인 AI 서비스를 만들기 위해 최선을 다하는 팀입니다.

## 👨🏼‍💻 멤버 구성

|지동진|이재영|최귀빈|
|------|-------|-------|
|<img width="120" height="120" alt="image" src="https://github.com/user-attachments/assets/797b4aa0-fcf5-4289-87a3-f2dbaf5ebf7e" />|<img width="120" height="120" alt="image" src="https://github.com/user-attachments/assets/0ef522e3-c04c-4f82-8005-d74892e439e8" />|<img width="120" height="120" alt="image" src="https://github.com/user-attachments/assets/55d8e285-6121-42fd-bc45-c9820b365467" />|
|[![GitHub](https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Dongjin-1203)|[![GitHub](https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/leejaeyoung-cpu)|[![GitHub](https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mjuik98)|
|[![Gmail](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:hambur1203@gmail.com)|[![Gmail](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:brookinljy@gmail.com)|[![Gmail](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:mjuik98@gmail.com)|

## 👨🏼‍💻 역할 분담

|지동진|이재영|최귀빈|
|------|-------|-------|
|PM / 풀스택 개발 / 텍스트 AI / 데이터 엔지니어링|이미지 추출 모델 개발|이미지 생성 모델 개발|
|프로젝트 전체 기획 및 일정 관리. Next.js 프론트엔드 개발 (UI/UX). FastAPI 백엔드 아키텍처 설계. GPT-5 캡션 생성 시스템 구축. NER 명령어 파싱 모델 개발. 인증 및 결제 시스템 통합. 배포 환경 구축 (Docker, GCP). 데이터 엔지니어링 전반 업무|RMBG-2.0 누끼 제거 파이프라인 구축. 이미지 전처리 및 후처리. 색감 보정 알고리즘 개발. Celery 비동기 작업 처리 최적화.|Stable Diffusion XL 배경 생성 시스템. ControlNet 통합 및 구도 제어. Fashion LoRA fine-tuning. 3가지 스타일 프롬프트 엔지니어링.|

---

# 5. 프로젝트 타임라인

```
2025-12-30 ~ 2026-01-28 (29일)

Week 1 (12/30 - 01/05): 기반 구축
├─ 프로젝트 설정 및 환경 구축
├─ Next.js 프론트엔드 기본 UI
├─ FastAPI 백엔드 구조 설계
├─ PostgreSQL/Redis 설정
└─ 이미지 업로드 기능

Week 2 (01/06 - 01/12): AI 파이프라인 개발
├─ RMBG-2.0 누끼 제거 연동
├─ Stable Diffusion XL 배경 생성
├─ GPT-5 캡션 생성
├─ NER 명령어 파싱
└─ Celery 비동기 처리

Week 3 (01/13 - 01/19): 통합 및 고도화
├─ 3가지 스타일 UI 구현
├─ 실시간 미리보기
├─ 예약 발행 기능
├─ 인스타그램 연동 (선택)
└─ 사용자 대시보드

Week 4 (01/20 - 01/26): 테스트 및 배포
├─ 통합 테스트
├─ 성능 최적화
├─ 버그 수정
├─ Docker 컨테이너화
└─ GCP 배포

Final Days (01/27 - 01/28): 런칭
└─ 최종 점검 및 베타 런칭
```

---

# 6. 서비스 설명

## 서비스 아키텍처

<!-- TODO: 시스템 아키텍처 다이어그램 이미지 추가 -->
![System Architecture](./docs/diagrams/system_architecture.png)

## AI 파이프라인

<!-- TODO: AI 파이프라인 플로우차트 이미지 추가 -->
![AI Pipeline](./docs/diagrams/ai_pipeline.png)

## 데이터베이스 ERD

<!-- TODO: ERD 다이어그램 이미지 추가 -->
![Database ERD](./docs/diagrams/erd.png)

## 주요 기능

### 1. 이미지 자동 생성
- **누끼 제거**: RMBG-2.0 모델로 상품만 추출
- **배경 생성**: Stable Diffusion XL로 3가지 스타일 배경 자동 생성
- **색감 보정**: 원본 색상 유지 및 자동 보정
- **인스타그램 규격**: 1:1, 4:5, 9:16 자동 최적화

### 2. 텍스트 자동 생성
- **캡션 작성**: GPT-5로 패션 톤앤매너 적용
- **해시태그 추천**: 트렌드 분석 및 지역 태그 자동 삽입
- **이모지 삽입**: 자연스러운 이모지 배치

### 3. 간편한 사용성
- **자연어 명령**: "검은색 롱코트 19만원" 같은 간단한 입력
- **드래그 앤 드롭**: 이미지 업로드 UI
- **실시간 미리보기**: 생성 진행률 표시
- **배치 작업**: 여러 상품 한꺼번에 처리

### 4. 추가 기능
- **예약 발행**: 원하는 시간에 자동 발행
- **성과 분석**: 좋아요/댓글 추적 (예정)
- **인스타그램 연동**: 원클릭 발행 (예정)

---

# 7. Further Information

## 개발 스택

### Frontend
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

### AI/ML
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Stable Diffusion](https://img.shields.io/badge/Stable_Diffusion-FF6F00?style=for-the-badge&logo=python&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)

### Infrastructure
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

## 협업 Tools
![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=notion&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

## 기타 링크

### 프로젝트 문서
- [기획서 다운로드](https://github.com/Dongjin-1203/AdGen_AI/issues/1#issue-3769764839)
- [API 문서](./docs/api_reference.md)
- [배포 가이드](./docs/deployment.md)

### 다이어그램
- [시스템 아키텍처](./docs/diagrams/system_architecture.html)
- [AI 파이프라인](./docs/diagrams/ai_pipeline_flowchart.html)
- [ERD](./docs/diagrams/fashion_ai_erd_4x3.html)

### 협업 일지
- 지동진 ([개인 협업일지](링크 추가 예정))
- 이재영 ([개인 협업일지](링크 추가 예정))
- 최귀빈 (https://www.notion.so/2d855ab021a08043b09aeb3653146370?source=copy_link)

---

## 라이선스

MIT License

### AI 모델

## 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.
