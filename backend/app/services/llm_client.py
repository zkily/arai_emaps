"""
Ollama LLM クライアント（chat / stream / health）
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import settings


class OllamaClientError(Exception):
    """Ollama API 呼び出し失敗"""


def _base_url() -> str:
    return (settings.OLLAMA_BASE_URL or "http://127.0.0.1:11434").rstrip("/")


def _timeout() -> httpx.Timeout:
    sec = max(int(settings.OLLAMA_TIMEOUT_SECONDS or 120), 30)
    return httpx.Timeout(sec, connect=10.0)


async def chat(
    messages: List[Dict[str, Any]],
    *,
    tools: Optional[List[Dict[str, Any]]] = None,
    stream: bool = False,
) -> Dict[str, Any]:
    """POST /api/chat（非ストリーム）"""
    payload: Dict[str, Any] = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
    }
    if tools:
        payload["tools"] = tools

    url = f"{_base_url()}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        logger.warning("Ollama chat failed: {}", e)
        raise OllamaClientError(str(e)) from e


async def chat_stream(
    messages: List[Dict[str, Any]],
    *,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """POST /api/chat（NDJSON ストリーム）"""
    payload: Dict[str, Any] = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
    }
    if tools:
        payload["tools"] = tools

    url = f"{_base_url()}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = (line or "").strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        logger.debug("Ollama stream skip non-json line: {}", line[:80])
    except httpx.HTTPError as e:
        logger.warning("Ollama chat stream failed: {}", e)
        raise OllamaClientError(str(e)) from e


async def check_health() -> Dict[str, Any]:
    """Ollama 接続とモデル有無を確認"""
    model = settings.OLLAMA_MODEL
    base = _base_url()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            tags_resp = await client.get(f"{base}/api/tags")
            tags_resp.raise_for_status()
            data = tags_resp.json()
            names = [m.get("name", "") for m in data.get("models", [])]
            # ollama list は "qwen2.5:7b" または "qwen2.5:7b-xxx" 形式
            model_ready = any(
                n == model or n.startswith(f"{model}:") or model.startswith(n.split(":")[0])
                for n in names
            )
            return {
                "status": "ok" if model_ready else "model_missing",
                "ollama_url": base,
                "model": model,
                "models_available": names,
                "model_ready": model_ready,
            }
    except httpx.HTTPError as e:
        return {
            "status": "unreachable",
            "ollama_url": base,
            "model": model,
            "error": str(e),
            "model_ready": False,
        }
