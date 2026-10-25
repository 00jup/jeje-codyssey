import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (backend 디렉터리 및 루트 디렉터리 확인)
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

if (BASE_DIR / ".env").exists():
    load_dotenv(BASE_DIR / ".env")
elif (ROOT_DIR / ".env").exists():
    load_dotenv(ROOT_DIR / ".env")
else:
    load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # 교육용 키(sk-cody-...)인 경우 Codyssey AI 게이트웨이 및 모델 자동 적용
    _raw_base_url = os.getenv("OPENAI_BASE_URL", "")
    if not _raw_base_url and OPENAI_API_KEY.startswith("sk-cody-"):
        OPENAI_BASE_URL: str = "https://copa.codyssey.kr/v1"
    else:
        OPENAI_BASE_URL: str = _raw_base_url

    _raw_model = os.getenv("OPENAI_MODEL", "")
    if OPENAI_API_KEY.startswith("sk-cody-"):
        # 교육용 게이트웨이(copa.codyssey.kr)는 gpt-5.4-mini 등을 지원
        if not _raw_model or _raw_model in ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-5-mini"]:
            OPENAI_MODEL: str = "gpt-5.4-mini"
        else:
            OPENAI_MODEL: str = _raw_model
    else:
        OPENAI_MODEL: str = _raw_model or "gpt-4o-mini"
    
    FIREBASE_SERVICE_ACCOUNT_KEY_PATH: str = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_KEY_PATH", 
        str(BASE_DIR / "firebase-service-account.json")
    )
    FIREBASE_SERVICE_ACCOUNT_JSON: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    
    ALLOWED_ORIGINS: list[str] = [
        origin.strip() 
        for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",") 
        if origin.strip()
    ]
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
