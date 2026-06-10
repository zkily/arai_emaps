"""
AI 助手 API スキーマ
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1)


class ChatResponse(BaseModel):
    message: ChatMessage
    model: str


class HealthResponse(BaseModel):
    status: str
    enabled: bool
    ollama_url: Optional[str] = None
    model: Optional[str] = None
    model_ready: bool = False
    models_available: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class StreamEvent(BaseModel):
    type: Literal["status", "token", "error", "done"]
    content: str = ""
    meta: Optional[Dict[str, Any]] = None
