from fastapi import FastAPI
import os

print("=" * 50)
print("🚀 FastAPI 앱 초기화 시작")
print(f"PORT: {os.getenv('PORT', 'NOT SET')}")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'NOT SET')}")
print("=" * 50)

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "Hello from Cloud Run!",
        "port": os.getenv("PORT"),
        "env": os.getenv("ENVIRONMENT")
    }

@app.get("/health")
def health():
    return {"status": "ok"}

print("✅ FastAPI 앱 초기화 완료")