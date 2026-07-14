"""個人メモ ビジネスロジック"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import JST, now_jst
from app.modules.auth.memo_models import UserMemo
from app.modules.auth.models import User

MAX_TITLE_LEN = 200
MAX_CONTENT_LEN = 2000
VALID_COLORS = frozenset({"blue", "green", "amber", "rose", "slate"})
ALL_DAY_REMIND_HOUR = 9


def _datetime_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:19]
    return str(value)[:19]


def _date_str(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    return str(value)[:10]


def _time_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:8]
    return str(value)[:8]


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日付の形式が正しくありません（YYYY-MM-DD）",
        ) from exc


def _parse_time(value: Optional[str]) -> Optional[time]:
    if value is None or not str(value).strip():
        return None
    raw = str(value).strip()
    try:
        if len(raw) <= 5:
            parts = raw.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return time(hour, minute)
        return time.fromisoformat(raw[:8])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="時刻の形式が正しくありません（HH:mm）",
        ) from exc


def _compute_remind_at(
    memo_date: date,
    memo_time: Optional[time],
    remind_offset_minutes: Optional[int],
) -> Optional[datetime]:
    if remind_offset_minutes is None:
        return None
    if memo_time is None:
        base = datetime.combine(memo_date, time(ALL_DAY_REMIND_HOUR, 0))
    else:
        base = datetime.combine(memo_date, memo_time)
    if base.tzinfo is None:
        base = JST.localize(base)
    return base - timedelta(minutes=int(remind_offset_minutes))


def _serialize_memo(row: UserMemo) -> dict[str, Any]:
    return {
        "id": int(row.id),
        "title": row.title,
        "content": row.content,
        "memo_date": _date_str(row.memo_date),
        "memo_time": _time_str(row.memo_time),
        "remind_at": _datetime_str(row.remind_at),
        "remind_offset_minutes": row.remind_offset_minutes,
        "color": row.color,
        "status": int(row.status or 0),
        "reminded_at": _datetime_str(row.reminded_at),
        "created_at": _datetime_str(row.created_at),
        "updated_at": _datetime_str(row.updated_at),
    }


async def _get_user_memo(db: AsyncSession, user: User, memo_id: int) -> UserMemo:
    result = await db.execute(
        select(UserMemo).where(UserMemo.id == memo_id, UserMemo.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="メモが見つかりません")
    return row


def _validate_title(title: str) -> str:
    text = (title or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="タイトルを入力してください")
    if len(text) > MAX_TITLE_LEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"タイトルは {MAX_TITLE_LEN} 文字以内にしてください",
        )
    return text


def _validate_content(content: Optional[str]) -> Optional[str]:
    if content is None:
        return None
    text = content.strip()
    if not text:
        return None
    if len(text) > MAX_CONTENT_LEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"本文は {MAX_CONTENT_LEN} 文字以内にしてください",
        )
    return text


def _validate_color(color: Optional[str]) -> Optional[str]:
    if color is None or not str(color).strip():
        return None
    normalized = str(color).strip().lower()
    if normalized not in VALID_COLORS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効な色が指定されました")
    return normalized


def _validate_remind_offset(remind_offset_minutes: Optional[int]) -> Optional[int]:
    if remind_offset_minutes is None:
        return None
    offset = int(remind_offset_minutes)
    if offset < 0 or offset > 1440:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="リマインドは 0〜1440 分の範囲で指定してください",
        )
    return offset


async def list_memos(
    db: AsyncSession,
    user: User,
    *,
    date_from: date,
    date_to: date,
) -> list[dict[str, Any]]:
    if date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="開始日は終了日以前にしてください",
        )
    result = await db.execute(
        select(UserMemo)
        .where(
            UserMemo.user_id == user.id,
            UserMemo.memo_date >= date_from,
            UserMemo.memo_date <= date_to,
        )
        .order_by(UserMemo.memo_date.asc(), UserMemo.memo_time.asc(), UserMemo.id.asc())
    )
    rows = list(result.scalars().all())
    return [_serialize_memo(row) for row in rows]


async def get_upcoming(db: AsyncSession, user: User) -> dict[str, Any]:
    now = now_jst()
    today = now.date()
    tomorrow_end = now + timedelta(hours=24)

    due_result = await db.execute(
        select(UserMemo)
        .where(
            UserMemo.user_id == user.id,
            UserMemo.status == 0,
            UserMemo.remind_at.isnot(None),
            UserMemo.reminded_at.is_(None),
            UserMemo.remind_at <= now.replace(tzinfo=None),
        )
        .order_by(UserMemo.remind_at.asc())
    )
    due_now = [_serialize_memo(row) for row in due_result.scalars().all()]

    badge_result = await db.execute(
        select(UserMemo.id)
        .where(
            UserMemo.user_id == user.id,
            UserMemo.status == 0,
            or_(
                UserMemo.memo_date == today,
                and_(
                    UserMemo.remind_at.isnot(None),
                    UserMemo.reminded_at.is_(None),
                    UserMemo.remind_at <= tomorrow_end.replace(tzinfo=None),
                ),
            ),
        )
    )
    badge_count = len(list(badge_result.scalars().all()))

    return {"due_now": due_now, "badge_count": badge_count}


async def create_memo(
    db: AsyncSession,
    user: User,
    *,
    title: str,
    memo_date: str,
    content: Optional[str] = None,
    memo_time: Optional[str] = None,
    remind_offset_minutes: Optional[int] = None,
    color: Optional[str] = None,
    all_day: bool = False,
) -> dict[str, Any]:
    parsed_date = _parse_date(memo_date)
    parsed_time = None if all_day else _parse_time(memo_time)
    parsed_title = _validate_title(title)
    parsed_content = _validate_content(content)
    parsed_color = _validate_color(color)
    parsed_offset = _validate_remind_offset(remind_offset_minutes)
    remind_at = _compute_remind_at(parsed_date, parsed_time, parsed_offset)

    row = UserMemo(
        user_id=user.id,
        title=parsed_title,
        content=parsed_content,
        memo_date=parsed_date,
        memo_time=parsed_time,
        remind_at=remind_at.replace(tzinfo=None) if remind_at else None,
        remind_offset_minutes=parsed_offset,
        color=parsed_color,
        status=0,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _serialize_memo(row)


async def update_memo(
    db: AsyncSession,
    user: User,
    memo_id: int,
    *,
    title: Optional[str] = None,
    content: Optional[str] = None,
    memo_date: Optional[str] = None,
    memo_time: Optional[str] = None,
    remind_offset_minutes: Optional[int] = ...,  # type: ignore[assignment]
    color: Optional[str] = None,
    all_day: Optional[bool] = None,
    status: Optional[int] = None,
    clear_reminded: bool = False,
) -> dict[str, Any]:
    row = await _get_user_memo(db, user, memo_id)

    if title is not None:
        row.title = _validate_title(title)
    if content is not None:
        row.content = _validate_content(content)
    if memo_date is not None:
        row.memo_date = _parse_date(memo_date)
    if all_day is True:
        row.memo_time = None
    elif memo_time is not None:
        row.memo_time = _parse_time(memo_time)
    if color is not None:
        row.color = _validate_color(color)
    if status is not None:
        row.status = 1 if int(status) == 1 else 0
        if row.status == 1:
            row.reminded_at = row.reminded_at or now_jst().replace(tzinfo=None)

    if remind_offset_minutes is not ...:
        row.remind_offset_minutes = _validate_remind_offset(remind_offset_minutes)
        if row.remind_offset_minutes is None:
            row.remind_at = None
            row.reminded_at = None
        else:
            row.remind_at = (
                _compute_remind_at(row.memo_date, row.memo_time, row.remind_offset_minutes) or None
            )
            if row.remind_at:
                row.remind_at = row.remind_at.replace(tzinfo=None)
            row.reminded_at = None
    elif clear_reminded:
        row.reminded_at = None
    elif title is not None or content is not None or memo_date is not None or all_day is not None or memo_time is not None:
        if row.remind_offset_minutes is not None:
            row.remind_at = (
                _compute_remind_at(row.memo_date, row.memo_time, row.remind_offset_minutes) or None
            )
            if row.remind_at:
                row.remind_at = row.remind_at.replace(tzinfo=None)
            row.reminded_at = None

    await db.commit()
    await db.refresh(row)
    return _serialize_memo(row)


async def complete_memo(db: AsyncSession, user: User, memo_id: int) -> dict[str, Any]:
    return await update_memo(db, user, memo_id, status=1)


async def delete_memo(db: AsyncSession, user: User, memo_id: int) -> None:
    row = await _get_user_memo(db, user, memo_id)
    await db.delete(row)
    await db.commit()


async def ack_reminder(db: AsyncSession, user: User, memo_id: int) -> dict[str, Any]:
    row = await _get_user_memo(db, user, memo_id)
    if row.reminded_at is not None:
        return _serialize_memo(row)
    row.reminded_at = now_jst().replace(tzinfo=None)
    await db.commit()
    await db.refresh(row)
    return _serialize_memo(row)
