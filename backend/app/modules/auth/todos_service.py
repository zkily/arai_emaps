"""連絡事項（全ユーザー共有）ビジネスロジック"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.auth.models import User
from app.modules.auth.todo_models import UserTodo

MAX_CONTENT_LEN = 500
DEFAULT_LIST_LIMIT = 200


def _datetime_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:19]
    return str(value)[:19]


def _serialize_todo(row: UserTodo, *, created_by: Optional[str] = None) -> dict[str, Any]:
    return {
        "id": int(row.id),
        "content": row.content,
        "is_done": int(row.is_done or 0),
        "created_by": created_by,
        "created_at": _datetime_str(row.created_at),
        "completed_at": _datetime_str(row.completed_at),
        "updated_at": _datetime_str(row.updated_at),
    }


async def list_todos(
    db: AsyncSession,
    limit: int = DEFAULT_LIST_LIMIT,
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(UserTodo, User.username, User.full_name)
        .join(User, User.id == UserTodo.user_id)
        .order_by(UserTodo.is_done.asc(), UserTodo.created_at.desc())
        .limit(limit)
    )
    rows = result.all()
    items: list[dict[str, Any]] = []
    for todo, username, full_name in rows:
        display_name = (full_name or "").strip() or (username or "").strip() or None
        items.append(_serialize_todo(todo, created_by=display_name))
    return items


async def create_user_todo(
    db: AsyncSession,
    user: User,
    content: str,
) -> dict[str, Any]:
    text = (content or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="内容を入力してください")
    if len(text) > MAX_CONTENT_LEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"内容は {MAX_CONTENT_LEN} 文字以内にしてください",
        )

    row = UserTodo(
        user_id=user.id,
        content=text,
        is_done=0,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    created_by = (user.full_name or "").strip() or (user.username or "").strip() or None
    return _serialize_todo(row, created_by=created_by)


async def _get_todo(db: AsyncSession, todo_id: int) -> UserTodo:
    result = await db.execute(select(UserTodo).where(UserTodo.id == todo_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="連絡事項が見つかりません")
    return row


async def update_user_todo(
    db: AsyncSession,
    todo_id: int,
    *,
    content: Optional[str] = None,
    is_done: Optional[int] = None,
) -> dict[str, Any]:
    row = await _get_todo(db, todo_id)

    if content is not None:
        text = content.strip()
        if not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="内容を入力してください")
        if len(text) > MAX_CONTENT_LEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"内容は {MAX_CONTENT_LEN} 文字以内にしてください",
            )
        row.content = text

    if is_done is not None:
        done = 1 if int(is_done) == 1 else 0
        row.is_done = done
        row.completed_at = now_jst() if done == 1 else None

    await db.commit()
    await db.refresh(row)

    creator = await db.get(User, row.user_id)
    created_by = None
    if creator:
        created_by = (creator.full_name or "").strip() or (creator.username or "").strip() or None
    return _serialize_todo(row, created_by=created_by)


async def delete_user_todo(db: AsyncSession, todo_id: int) -> None:
    row = await _get_todo(db, todo_id)
    await db.delete(row)
    await db.commit()


async def clear_completed_todos(db: AsyncSession) -> int:
    result = await db.execute(delete(UserTodo).where(UserTodo.is_done == 1))
    await db.commit()
    return int(result.rowcount or 0)
