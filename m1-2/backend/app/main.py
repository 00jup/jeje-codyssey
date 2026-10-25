import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.routers import data_router, conversations_router, chat_router

app = FastAPI(
    title="스마트스토어 AI 비서 API",
    description="시계열 매출 데이터 분석, Firestore CRUD 및 컨텍스트 주입 기반 AI 챗봇 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(data_router)
app.include_router(conversations_router)
app.include_router(chat_router)

# 헬스체크 엔드포인트 (Render 콜드스타트 감지 및 웜업용)
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "Daily Sales AI Assistant",
        "version": "1.0.0"
    }

# 프론트엔드 정적 파일 서빙 (로컬 개발 편의를 위해 frontend 폴더가 존재하면 마운트)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
    css_dir = FRONTEND_DIR / "css"
    js_dir = FRONTEND_DIR / "js"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message": "스마트스토어 AI 비서 API 서버가 실행 중입니다.",
            "docs": "/docs",
            "health": "/health"
        }
