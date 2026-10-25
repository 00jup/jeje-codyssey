import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from app.models.chat import ChatRequest, ChatResponse
from app.services.firebase_service import firebase_service
from app.services.analysis_service import analysis_service
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

@router.post("", response_model=ChatResponse, summary="데이터 기반 AI 채팅 (컨텍스트 주입)")
def chat_with_agent(payload: ChatRequest):
    """
    1. 데이터 요약 조회 (/api/data/summary)
    2. 요약을 시스템 프롬프트에 삽입 (컨텍스트 주입)
    3. GPT API 호출
    4. 대화 내용을 conversations 컬렉션에 자동 저장
    """
    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="메시지 내용이 비어있습니다.")

    # 1. 데이터 요약 조회
    records = firebase_service.get_all_data()
    summary = analysis_service.compute_summary(records)

    # 2. 대화 세션 확인 및 이전 기록 로드
    conv_id = payload.conversation_id
    history_messages = []
    if conv_id:
        existing_conv = firebase_service.get_conversation_by_id(conv_id)
        if existing_conv:
            history_messages = existing_conv.get("messages", [])
        else:
            conv_id = f"conv_{uuid.uuid4().hex[:10]}"
    else:
        conv_id = f"conv_{uuid.uuid4().hex[:10]}"

    # 3. GPT API 호출 (컨텍스트 주입)
    assistant_reply = ai_service.generate_chat_response(
        user_message=user_message,
        summary=summary,
        chat_history=history_messages
    )

    # 4. conversations 컬렉션에 자동 저장
    now = datetime.now().isoformat()
    new_user_msg = {
        "role": "user",
        "content": user_message,
        "timestamp": now
    }
    new_assistant_msg = {
        "role": "assistant",
        "content": assistant_reply,
        "timestamp": datetime.now().isoformat()
    }

    firebase_service.append_messages(
        conv_id=conv_id,
        new_messages=[new_user_msg, new_assistant_msg],
        title_candidate=user_message[:30]
    )

    return ChatResponse(
        conversation_id=conv_id,
        reply=assistant_reply,
        summary=summary
    )
