from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.conversation import ConversationCreate, ConversationResponse, ConversationListItem
from app.services.firebase_service import firebase_service

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED, summary="새 대화 세션 저장")
def create_conversation(payload: ConversationCreate):
    """
    새로운 대화 세션을 생성하고 메시지를 저장합니다.
    """
    item = firebase_service.create_conversation(payload.model_dump())
    return item

@router.get("", response_model=List[ConversationResponse], summary="대화 목록 조회")
def get_conversations():
    """
    저장된 모든 대화 세션 목록을 조회합니다 (최신순 정렬).
    """
    return firebase_service.get_conversations()

@router.get("/{conv_id}", response_model=ConversationResponse, summary="특정 대화 상세 및 메시지 전체 조회")
def get_conversation_detail(conv_id: str):
    """
    지정한 대화 세션의 전체 메시지(히스토리)를 조회합니다 (불러오기 UX 지원).
    """
    conv = firebase_service.get_conversation_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="해당 ID의 대화 기록을 찾을 수 없습니다.")
    return conv

@router.delete("/{conv_id}", status_code=status.HTTP_200_OK, summary="대화 삭제")
def delete_conversation(conv_id: str):
    """
    지정한 대화 세션을 삭제합니다.
    """
    success = firebase_service.delete_conversation(conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="삭제할 대화 기록을 찾을 수 없습니다.")
    return {"message": "대화 기록이 성공적으로 삭제되었습니다.", "id": conv_id}
