from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):

    # 출처 허용 목록
    allow_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

settings = Settings()