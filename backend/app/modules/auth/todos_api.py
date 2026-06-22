"""連絡事項 API（全ユーザー共有）"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.todos_service import (
    clear_completed_todos,
    create_user_todo,
    delete_user_todo,
    list_todos,
    update_user_todo,
)

router = APIRouter()


class UserTodoOut(BaseModel):
    id: int
    content: str
    is_done: int
    created_by: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    updated_at: str


class UserTodoListResponse(BaseModel):
    list: list[UserTodoOut]
    pending_count: int


class UserTodoCreateBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class UserTodoUpdateBody(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=500)
    is_done: Optional[int] = None


class ClearCompletedResponse(BaseModel):
    deleted_count: int


@router.get("", response_model=UserTodoListResponse, summary="連絡事項一覧")
async def get_user_todos(
    limit: int = Query(200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    rows = await list_todos(db, limit=limit)
    pending_count = sum(1 for row in rows if int(row.get("is_done") or 0) == 0)
    return {"list": rows, "pending_count": pending_count}


@router.post("", response_model=UserTodoOut, summary="連絡事項追加")
async def post_user_todo(
    body: UserTodoCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await create_user_todo(db, current_user, body.content)


@router.patch("/{todo_id}", response_model=UserTodoOut, summary="連絡事項更新")
async def patch_user_todo(
    todo_id: int,
    body: UserTodoUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await update_user_todo(
        db,
        todo_id,
        content=body.content,
        is_done=body.is_done,
    )


@router.delete("/completed", response_model=ClearCompletedResponse, summary="完了連絡事項一括削除")
async def delete_completed_user_todos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    deleted_count = await clear_completed_todos(db)
    return {"deleted_count": deleted_count}


@router.delete("/{todo_id}", summary="連絡事項削除")
async def remove_user_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await delete_user_todo(db, todo_id)
    return {"ok": True}
