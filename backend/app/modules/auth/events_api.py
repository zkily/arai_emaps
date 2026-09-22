"""個人イベント API"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.events_service import (
    _parse_date,
    ack_reminder,
    create_event,
    delete_event,
    get_upcoming,
    get_viewer_scope_label,
    list_events,
    reschedule_event,
    update_event,
)
from app.modules.auth.models import User

router = APIRouter()


class UserEventOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_at: str
    end_at: str
    all_day: bool = False
    color: str = "blue"
    visibility: str = "department"
    recurrence_rule: Optional[str] = None
    recurrence_until: Optional[str] = None
    remind_offset_minutes: Optional[int] = None
    remind_at: Optional[str] = None
    reminded_at: Optional[str] = None
    occurrence_date: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    is_owner: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserEventListResponse(BaseModel):
    list: list[UserEventOut]
    viewer_scope: str = "department"


class UserEventUpcomingResponse(BaseModel):
    due_now: list[UserEventOut]
    badge_count: int
    today_count: int = 0
    week_count: int = 0


class UserEventCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    start_at: str
    end_at: str
    description: Optional[str] = Field(default=None, max_length=2000)
    location: Optional[str] = Field(default=None, max_length=255)
    all_day: bool = False
    color: Optional[str] = Field(default=None, max_length=20)
    visibility: Optional[str] = Field(default="department", max_length=20)
    recurrence_rule: Optional[str] = Field(default=None, max_length=20)
    recurrence_until: Optional[str] = None
    remind_offset_minutes: Optional[int] = Field(default=None, ge=0, le=1440)


class UserEventUpdateBody(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=2000)
    location: Optional[str] = Field(default=None, max_length=255)
    all_day: Optional[bool] = None
    color: Optional[str] = Field(default=None, max_length=20)
    visibility: Optional[str] = Field(default=None, max_length=20)
    recurrence_rule: Optional[str] = Field(default=None, max_length=20)
    recurrence_until: Optional[str] = None
    remind_offset_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    edit_scope: Optional[str] = Field(default="all", max_length=20)
    occurrence_date: Optional[str] = None


class UserEventRescheduleBody(BaseModel):
    start_at: str
    end_at: str
    edit_scope: Optional[str] = Field(default="all", max_length=20)
    occurrence_date: Optional[str] = None


@router.get("", response_model=UserEventListResponse, summary="個人イベント一覧（期間）")
async def get_user_events(
    date_from: str = Query(..., alias="from", description="YYYY-MM-DD"),
    date_to: str = Query(..., alias="to", description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    rows = await list_events(
        db,
        current_user,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
    )
    viewer_scope = await get_viewer_scope_label(db, current_user)
    return {"list": rows, "viewer_scope": viewer_scope}


@router.get("/upcoming", response_model=UserEventUpcomingResponse, summary="リマインド・近日イベント")
async def get_user_events_upcoming(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await get_upcoming(db, current_user)


@router.post("", response_model=UserEventOut, summary="個人イベント作成")
async def post_user_event(
    body: UserEventCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await create_event(
        db,
        current_user,
        title=body.title,
        start_at=body.start_at,
        end_at=body.end_at,
        description=body.description,
        location=body.location,
        all_day=body.all_day,
        color=body.color,
        visibility=body.visibility,
        recurrence_rule=body.recurrence_rule,
        recurrence_until=body.recurrence_until,
        remind_offset_minutes=body.remind_offset_minutes,
    )


@router.patch("/{event_id}", response_model=UserEventOut, summary="個人イベント更新")
async def patch_user_event(
    event_id: int,
    body: UserEventUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    payload = body.model_dump(exclude_unset=True)
    return await update_event(db, current_user, event_id, **payload)


@router.patch("/{event_id}/reschedule", response_model=UserEventOut, summary="ドラッグ等による日時変更")
async def patch_user_event_reschedule(
    event_id: int,
    body: UserEventRescheduleBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await reschedule_event(
        db,
        current_user,
        event_id,
        start_at=body.start_at,
        end_at=body.end_at,
        edit_scope=body.edit_scope,
        occurrence_date=body.occurrence_date,
    )


@router.post("/{event_id}/ack-reminder", response_model=UserEventOut, summary="イベントリマインド確認")
async def post_user_event_ack_reminder(
    event_id: int,
    occurrence_date: Optional[str] = Query(default=None, description="YYYY-MM-DD（繰り返し用）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await ack_reminder(db, current_user, event_id, occurrence_date=occurrence_date)


@router.delete("/{event_id}", summary="個人イベント削除")
async def remove_user_event(
    event_id: int,
    edit_scope: Optional[str] = Query(default="all", description="this|following|all"),
    occurrence_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await delete_event(
        db,
        current_user,
        event_id,
        edit_scope=edit_scope,
        occurrence_date=occurrence_date,
    )
    return {"ok": True}
