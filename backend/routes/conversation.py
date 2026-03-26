import logging

from fastapi import APIRouter, HTTPException, Request

from limiter import limiter
from models.models import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationResponse,
    FollowUpMessageRequest,
)
from services.conversation_service import (
    add_message,
    clear_all_history,
    create_conversation,
    get_conversation,
    list_conversations,
    list_messages,
    load_verification,
)
from services.explanation_service import generate_follow_up_answer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/conversations", response_model=ConversationCreateResponse)
@limiter.limit("30/minute")
def start_conversation(request: Request, payload: ConversationCreateRequest):
    conversation_id, request_id, created_at = create_conversation(payload.verification)

    greeting = (
        "I can answer follow-up questions about this assessment. "
        "I cannot confirm a medicine is definitely authentic, but I can explain the signals and next safest steps."
    )
    first_message = add_message(conversation_id, "assistant", greeting)

    return ConversationCreateResponse(
        conversation_id=conversation_id,
        request_id=request_id,
        created_at=created_at,
        verification=payload.verification,
        messages=[first_message],
    )


@router.get("/conversations")
def list_conversation_history(limit: int = 100):
    return {"conversations": [item.model_dump() for item in list_conversations(limit=limit)]}


@router.delete("/conversations/history")
def clear_conversation_history():
    clear_all_history()
    return {"status": "ok", "detail": "All conversation history cleared."}


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation_history(conversation_id: str):
    row = get_conversation(conversation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")

    verification = load_verification(conversation_id)
    if verification is None:
        raise HTTPException(status_code=500, detail="Conversation context is unavailable")

    return ConversationResponse(
        conversation_id=row["id"],
        request_id=row["request_id"],
        created_at=row["created_at"],
        verification=verification,
        messages=list_messages(conversation_id),
    )


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationResponse)
@limiter.limit("20/minute")
def post_follow_up(request: Request, conversation_id: str, payload: FollowUpMessageRequest):
    row = get_conversation(conversation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")

    text = payload.message.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    verification = load_verification(conversation_id)
    if verification is None:
        raise HTTPException(status_code=500, detail="Conversation context is unavailable")

    add_message(conversation_id, "user", text)
    history = list_messages(conversation_id)

    history_payload = [{"role": m.role, "content": m.content} for m in history]
    answer = generate_follow_up_answer(verification.model_dump(), history_payload, text)
    add_message(conversation_id, "assistant", answer)

    messages = list_messages(conversation_id)
    return ConversationResponse(
        conversation_id=row["id"],
        request_id=row["request_id"],
        created_at=row["created_at"],
        verification=verification,
        messages=messages,
    )
