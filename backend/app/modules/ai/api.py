"""
AI 助手 API
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.ai import service
from app.modules.ai.schemas import ChatMessage, ChatRequest, ChatResponse, HealthResponse
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.services.llm_client import OllamaClientError, check_health

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def ai_health(
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    if not settings.AI_ENABLED:
        return HealthResponse(status="disabled", enabled=False, model_ready=False)

    h = await check_health()
    return HealthResponse(
        status=h.get("status", "unknown"),
        enabled=True,
        ollama_url=h.get("ollama_url"),
        model=h.get("model"),
        model_ready=bool(h.get("model_ready")),
        models_available=h.get("models_available") or [],
        error=h.get("error"),
    )


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    if not settings.AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI is disabled")

    try:
        text = await service.chat_sync(db, body.messages)
    except OllamaClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return ChatResponse(
        message=ChatMessage(role="assistant", content=text),
        model=settings.OLLAMA_MODEL,
    )


@router.post("/chat/stream")
async def ai_chat_stream(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    if not settings.AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI is disabled")

    async def event_generator():
        try:
            async for event in service.chat_stream(db, body.messages):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            err = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
