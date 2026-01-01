FROM python:3.12-slim

WORKDIR /app

# 환경 변수
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# 시스템 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 업그레이드
RUN pip install --upgrade pip

# FastAPI와 Uvicorn만 설치
RUN pip install fastapi uvicorn[standard]

# 앱 코드 복사
COPY main.py .

# 포트 노출
EXPOSE 8080

# 시작 명령 - 간단하고 명확하게
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]