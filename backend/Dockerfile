FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

# requirements.txt 추가
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 전체 앱 복사
COPY . .

RUN mkdir -p uploads

EXPOSE 8080

# uvicorn 명령 그대로
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]