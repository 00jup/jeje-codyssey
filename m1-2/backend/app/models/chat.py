from pydantic import BaseModel, Field
from typing import Optional
from app.models.data import DataSummary

class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 질문", examples=["이번 달 실적이 어때?"])
    conversation_id: Optional[str] = Field(None, description="기존 대화 세션 ID (없으면 신규 생성)")

class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    summary: DataSummary
