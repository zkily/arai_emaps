"""
AI 助手编排：Ollama + 只读 DB 工具
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.ai.schemas import ChatMessage
from app.modules.ai.tools import execute_tool_call, get_tool_definitions
from app.services.llm_client import OllamaClientError, chat, chat_stream as ollama_chat_stream

SYSTEM_PROMPT = """你是 Smart-EMAP 生产管理系统的 AI 助手。
你只能使用系统提供的工具只读查询本项目 MySQL 数据库 eams_db 中的业务数据。
可用能力：
- list_database_tables：列出库中业务表
- describe_table：查看表结构
- query_table：按表名、关键词、字段条件查询（推荐）
- execute_read_sql：复杂只读 SELECT（含 JOIN），必须有 LIMIT
- 以及客户/部品/供应商/生产计划/材料库存等快捷工具
规则：
1. 回答业务问题前必须先调用工具获取真实数据，禁止编造。
2. 不确定表名时先 list_database_tables，再 describe_table，再 query_table。
3. 密码等敏感字段已脱敏，不要尝试绕过。
4. 若工具返回空结果，说明「数据库中未找到相关记录」。
5. 不要回答与 Smart-EMAP 无关的问题，不要访问互联网。
6. 用用户使用的语言简洁回答（中文/日文/英文均可）。"""


def _to_ollama_messages(messages: List[ChatMessage]) -> List[Dict[str, Any]]:
    return [{"role": m.role, "content": m.content} for m in messages]


async def _run_tool_rounds(
    db: AsyncSession,
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """多轮 tool calling（非流式）"""
    tools = get_tool_definitions()
    max_rounds = max(int(settings.AI_MAX_TOOL_ROUNDS or 5), 1)

    for _ in range(max_rounds):
        try:
            resp = await chat(messages, tools=tools, stream=False)
        except OllamaClientError:
            raise

        msg = resp.get("message") or {}
        if not msg:
            break
        messages.append(msg)

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            break

        for tc in tool_calls:
            result = await execute_tool_call(db, tc)
            fn = tc.get("function") or {}
            tool_name = fn.get("name") or tc.get("name") or "tool"
            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                    "name": tool_name,
                }
            )

    return messages


async def chat_sync(db: AsyncSession, user_messages: List[ChatMessage]) -> str:
    if not settings.AI_ENABLED:
        raise OllamaClientError("AI is disabled")

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *_to_ollama_messages(user_messages),
    ]
    messages = await _run_tool_rounds(db, messages)

    last = messages[-1] if messages else {}
    if last.get("role") == "assistant" and (last.get("content") or "").strip():
        return str(last["content"]).strip()

    try:
        resp = await chat(messages, tools=None, stream=False)
        content = (resp.get("message") or {}).get("content") or ""
        return str(content).strip() or "（无回复内容）"
    except OllamaClientError:
        raise


async def chat_stream(
    db: AsyncSession,
    user_messages: List[ChatMessage],
) -> AsyncIterator[Dict[str, Any]]:
    if not settings.AI_ENABLED:
        yield {"type": "error", "content": "AI is disabled"}
        return

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *_to_ollama_messages(user_messages),
    ]

    tools = get_tool_definitions()
    max_rounds = max(int(settings.AI_MAX_TOOL_ROUNDS or 5), 1)

    try:
        for _ in range(max_rounds):
            resp = await chat(messages, tools=tools, stream=False)
            msg = resp.get("message") or {}
            if not msg:
                break
            messages.append(msg)

            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                content = (msg.get("content") or "").strip()
                if content:
                    yield {"type": "token", "content": content}
                    yield {"type": "done", "content": ""}
                    return
                break

            for tc in tool_calls:
                fn = tc.get("function") or {}
                tool_name = fn.get("name") or "tool"
                yield {"type": "status", "content": f"查询: {tool_name}"}
                result = await execute_tool_call(db, tc)
                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "name": tool_name,
                    }
                )

        yield {"type": "status", "content": "生成回答..."}
        async for chunk in ollama_chat_stream(messages, tools=None):
            delta = (chunk.get("message") or {}).get("content") or ""
            if delta:
                yield {"type": "token", "content": delta}
            if chunk.get("done"):
                break
        yield {"type": "done", "content": ""}
    except OllamaClientError as e:
        logger.warning("AI stream error: {}", e)
        yield {"type": "error", "content": str(e)}
