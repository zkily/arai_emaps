"""個人メモ API"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.memos_service import (
    _parse_date,
    ack_reminder,
    complete_memo,
    create_memo,
    delete_memo,
    get_upcoming,
    list_memos,
    update_memo,
)
from app.modules.auth.models import User

router = APIRouter()


class UserMemoOut(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    memo_date: str
    memo_time: Optional[str] = None
    remind_at: Optional[str] = None
    remind_offset_minutes: Optional[int] = None
    color: Optional[str] = None
    status: int
    reminded_at: Optional[str] = None
    created_at: str
    updated_at: str


class UserMemoListResponse(BaseModel):
    list: list[UserMemoOut]


class UserMemoUpcomingResponse(BaseModel):
    due_now: list[UserMemoOut]
    badge_count: int


class UserMemoCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    memo_date: str
    content: Optional[str] = Field(default=None, max_length=2000)
    memo_time: Optional[str] = None
    all_day: bool = False
    remind_offset_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    color: Optional[str] = Field(default=None, max_length=20)


class UserMemoUpdateBody(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, max_length=2000)
    memo_date: Optional[str] = None
    memo_time: Optional[str] = None
    all_day: Optional[bool] = None
    remind_offset_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    color: Optional[str] = Field(default=None, max_length=20)
    status: Optional[int] = None


@router.get("", response_model=UserMemoListResponse, summary="個人メモ一覧（期間）")
async def get_user_memos(
    date_from: str = Query(..., alias="from", description="YYYY-MM-DD"),
    date_to: str = Query(..., alias="to", description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    rows = await list_memos(
        db,
        current_user,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
    )
    return {"list": rows}


@router.get("/upcoming", response_model=UserMemoUpcomingResponse, summary="リマインド・バッジ用")
async def get_user_memos_upcoming(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await get_upcoming(db, current_user)


@router.post("", response_model=UserMemoOut, summary="個人メモ作成")
async def post_user_memo(
    body: UserMemoCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await create_memo(
        db,
        current_user,
        title=body.title,
        memo_date=body.memo_date,
        content=body.content,
        memo_time=body.memo_time,
        remind_offset_minutes=body.remind_offset_minutes,
        color=body.color,
        all_day=body.all_day,
    )


@router.patch("/{memo_id}", response_model=UserMemoOut, summary="個人メモ更新")
async def patch_user_memo(
    memo_id: int,
    body: UserMemoUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    payload = body.model_dump(exclude_unset=True)
    remind_offset = payload.pop("remind_offset_minutes", ...)
    return await update_memo(
        db,
        current_user,
        memo_id,
        remind_offset_minutes=remind_offset,
        **payload,
    )


@router.post("/{memo_id}/complete", response_model=UserMemoOut, summary="個人メモ完了")
async def post_user_memo_complete(
    memo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await complete_memo(db, current_user, memo_id)


@router.post("/{memo_id}/ack-reminder", response_model=UserMemoOut, summary="リマインド確認")
async def post_user_memo_ack_reminder(
    memo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await ack_reminder(db, current_user, memo_id)


@router.delete("/{memo_id}", summary="個人メモ削除")
async def remove_user_memo(
    memo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await delete_memo(db, current_user, memo_id)
    return {"ok": True}
