from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="메시지 발신자 ('user', 'assistant', 'system')")
    content: str = Field(..., description="메시지 내용")
    timestamp: Optional[str] = Field(None, description="메시지 전송 시간 (ISO 8601)")

class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, description="대화 세션 제목")
    messages: List[ChatMessage] = Field(default_factory=list, description="대화 메시지 목록")

class ConversationResponse(BaseModel):
    id: str
    title: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: str
    updated_at: str

class ConversationListItem(BaseModel):
    id: str
    title: str
    message_count: int
    last_message: Optional[str] = None
    created_at: str
    updated_at: str
