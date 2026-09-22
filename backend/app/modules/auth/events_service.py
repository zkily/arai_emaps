"""個人イベント ビジネスロジック"""
from __future__ import annotations

import calendar
import json
from datetime import date, datetime, time, timedelta
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.auth.data_scope_service import resolve_user_data_scope
from app.modules.auth.event_models import UserEvent
from app.modules.auth.models import User

MAX_TITLE_LEN = 200
MAX_DESCRIPTION_LEN = 2000
MAX_LOCATION_LEN = 255
MAX_EXPAND = 400
ALL_DAY_REMIND_HOUR = 9
VALID_COLORS = frozenset({"blue", "green", "amber", "rose", "slate", "violet", "cyan"})
VALID_RECURRENCE = frozenset({"daily", "weekly", "monthly", "yearly"})
VALID_VISIBILITY = frozenset({"self", "department", "all"})
VALID_EDIT_SCOPE = frozenset({"this", "following", "all"})
DEFAULT_VISIBILITY = "department"


def _datetime_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:19]
    return str(value)[:19]


def _date_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    return str(value)[:10]


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日付の形式が正しくありません（YYYY-MM-DD）",
        ) from exc


def _parse_datetime(value: str) -> datetime:
    raw = (value or "").strip().replace("T", " ")
    try:
        if len(raw) <= 10:
            return datetime.combine(_parse_date(raw), time(0, 0))
        return datetime.fromisoformat(raw[:19])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日時の形式が正しくありません（YYYY-MM-DD HH:mm）",
        ) from exc


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


def _validate_optional_text(value: Optional[str], *, max_len: int, label: str) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if len(text) > max_len:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}は {max_len} 文字以内にしてください",
        )
    return text


def _validate_color(color: Optional[str]) -> str:
    if color is None or not str(color).strip():
        return "blue"
    normalized = str(color).strip().lower()
    if normalized not in VALID_COLORS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効な色が指定されました")
    return normalized


def _validate_recurrence(rule: Optional[str]) -> Optional[str]:
    if rule is None:
        return None
    normalized = str(rule).strip().lower()
    if not normalized or normalized == "none":
        return None
    if normalized not in VALID_RECURRENCE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効な繰り返し設定です")
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


def _validate_visibility(visibility: Optional[str]) -> str:
    if visibility is None or not str(visibility).strip():
        return DEFAULT_VISIBILITY
    normalized = str(visibility).strip().lower()
    if normalized not in VALID_VISIBILITY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効な公開範囲です")
    return normalized


def _event_visibility(row: UserEvent) -> str:
    raw = (getattr(row, "visibility", None) or DEFAULT_VISIBILITY).strip().lower()
    return raw if raw in VALID_VISIBILITY else DEFAULT_VISIBILITY


def _normalize_range(
    start_at: datetime,
    end_at: datetime,
    *,
    all_day: bool,
) -> tuple[datetime, datetime, int]:
    if all_day:
        start_norm = datetime.combine(start_at.date(), time(0, 0))
        end_day = end_at.date()
        if end_day < start_at.date():
            end_day = start_at.date()
        end_norm = datetime.combine(end_day, time(23, 59, 59))
        return start_norm, end_norm, 1

    start_norm = start_at.replace(second=0, microsecond=0)
    end_norm = end_at.replace(second=0, microsecond=0)
    if end_norm <= start_norm:
        end_norm = start_norm + timedelta(hours=1)
    return start_norm, end_norm, 0


def _add_months(dt: datetime, months: int) -> datetime:
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(dt.day, max_day)
    return dt.replace(year=year, month=month, day=day, second=0, microsecond=0)


def _advance_recurrence(cursor: datetime, rule: str) -> datetime:
    if rule == "daily":
        return cursor + timedelta(days=1)
    if rule == "weekly":
        return cursor + timedelta(weeks=1)
    if rule == "monthly":
        return _add_months(cursor, 1)
    if rule == "yearly":
        # 閏日でも月加算クランプで安全に進める
        return _add_months(cursor, 12)
    return cursor + timedelta(days=1)


def _parse_date_list(raw: Optional[str]) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    out: list[str] = []
    for item in data:
        text = str(item).strip()[:10]
        if len(text) == 10 and text not in out:
            out.append(text)
    return out


def _dump_date_list(dates: list[str]) -> Optional[str]:
    return json.dumps(dates, ensure_ascii=False) if dates else None


def _exdates_of(row: UserEvent) -> set[str]:
    return set(_parse_date_list(getattr(row, "recurrence_exdates", None)))


def _add_exdate(row: UserEvent, occ: date) -> None:
    dates = _parse_date_list(getattr(row, "recurrence_exdates", None))
    key = occ.isoformat()
    if key not in dates:
        dates.append(key)
        dates.sort()
    row.recurrence_exdates = _dump_date_list(dates)


def _reminded_dates_of(row: UserEvent) -> set[str]:
    dates = set(_parse_date_list(getattr(row, "reminded_dates", None)))
    legacy = _date_str(getattr(row, "last_reminded_occurrence", None))
    if legacy:
        dates.add(legacy)
    return dates


def _mark_reminded(row: UserEvent, occ: date) -> None:
    dates = _parse_date_list(getattr(row, "reminded_dates", None))
    key = occ.isoformat()
    if key not in dates:
        dates.append(key)
        dates.sort()
    row.reminded_dates = _dump_date_list(dates)
    row.last_reminded_occurrence = occ
    row.reminded_at = now_jst().replace(tzinfo=None)


def _validate_edit_scope(edit_scope: Optional[str]) -> str:
    if edit_scope is None or not str(edit_scope).strip():
        return "all"
    normalized = str(edit_scope).strip().lower()
    if normalized not in VALID_EDIT_SCOPE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効な編集範囲です")
    return normalized


def _compute_event_remind_at(
    start_at: datetime,
    *,
    all_day: bool,
    remind_offset_minutes: Optional[int],
) -> Optional[datetime]:
    if remind_offset_minutes is None:
        return None
    if all_day:
        base = datetime.combine(start_at.date(), time(ALL_DAY_REMIND_HOUR, 0))
    else:
        base = start_at.replace(second=0, microsecond=0)
    return base - timedelta(minutes=int(remind_offset_minutes))


def _refresh_remind_at(row: UserEvent) -> None:
    remind_at = _compute_event_remind_at(
        row.start_at,
        all_day=bool(row.all_day),
        remind_offset_minutes=row.remind_offset_minutes,
    )
    row.remind_at = remind_at.replace(tzinfo=None) if remind_at else None
    row.reminded_at = None
    row.last_reminded_occurrence = None
    row.reminded_dates = None


async def _create_detached_occurrence(
    db: AsyncSession,
    user: User,
    source: UserEvent,
    *,
    start_at: datetime,
    end_at: datetime,
    all_day: bool,
    overrides: Optional[dict[str, Any]] = None,
    with_recurrence: bool = False,
    recurrence_rule: Optional[str] = None,
    recurrence_until: Optional[date] = None,
) -> UserEvent:
    ov = overrides or {}
    start_norm, end_norm, all_day_flag = _normalize_range(start_at, end_at, all_day=all_day)
    title = ov["title"] if "title" in ov else source.title
    if "description" in ov:
        description = _validate_optional_text(
            ov["description"], max_len=MAX_DESCRIPTION_LEN, label="詳細"
        )
    else:
        description = source.description
    if "location" in ov:
        location = _validate_optional_text(ov["location"], max_len=MAX_LOCATION_LEN, label="場所")
    else:
        location = source.location
    color = ov["color"] if "color" in ov else (source.color or "blue")
    visibility = ov["visibility"] if "visibility" in ov else _event_visibility(source)
    if "remind_offset_minutes" in ov:
        remind_offset = _validate_remind_offset(ov["remind_offset_minutes"])
    else:
        remind_offset = source.remind_offset_minutes

    row = UserEvent(
        user_id=user.id,
        title=_validate_title(str(title)),
        description=description,
        location=location,
        start_at=start_norm,
        end_at=end_norm,
        all_day=all_day_flag,
        color=_validate_color(None if color is None else str(color)),
        visibility=_validate_visibility(None if visibility is None else str(visibility)),
        recurrence_rule=recurrence_rule if with_recurrence else None,
        recurrence_until=recurrence_until if with_recurrence else None,
        remind_offset_minutes=remind_offset,
    )
    if row.remind_offset_minutes is not None:
        _refresh_remind_at(row)
    db.add(row)
    return row


def _serialize_event(
    row: UserEvent,
    *,
    occurrence_date: Optional[str] = None,
    viewer_id: Optional[int] = None,
    owner: Optional[User] = None,
    department_name: Optional[str] = None,
) -> dict[str, Any]:
    rule = (row.recurrence_rule or "").strip().lower() or None
    owner_id = int(row.user_id)
    owner_name = None
    dept_id = None
    if owner is not None:
        owner_name = (owner.full_name or "").strip() or owner.username
        dept_id = owner.department_id
    return {
        "id": int(row.id),
        "title": row.title,
        "description": row.description,
        "location": row.location,
        "start_at": _datetime_str(row.start_at),
        "end_at": _datetime_str(row.end_at),
        "all_day": int(row.all_day or 0) == 1,
        "color": row.color or "blue",
        "visibility": _event_visibility(row),
        "recurrence_rule": rule,
        "recurrence_until": _date_str(row.recurrence_until),
        "remind_offset_minutes": row.remind_offset_minutes,
        "remind_at": _datetime_str(row.remind_at),
        "reminded_at": _datetime_str(row.reminded_at),
        "occurrence_date": occurrence_date,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "department_id": int(dept_id) if dept_id is not None else None,
        "department_name": department_name,
        "is_owner": viewer_id is not None and owner_id == int(viewer_id),
        "created_at": _datetime_str(row.created_at),
        "updated_at": _datetime_str(row.updated_at),
    }


def _event_overlaps_range(start_at: datetime, end_at: datetime, range_start: datetime, range_end: datetime) -> bool:
    return start_at <= range_end and end_at >= range_start


def _expand_event_in_range(
    row: UserEvent,
    range_start: datetime,
    range_end: datetime,
    *,
    viewer_id: Optional[int] = None,
    owner: Optional[User] = None,
    department_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    rule = (row.recurrence_rule or "").strip().lower()
    duration = row.end_at - row.start_at
    ser_kw = {
        "viewer_id": viewer_id,
        "owner": owner,
        "department_name": department_name,
    }

    if rule not in VALID_RECURRENCE:
        if _event_overlaps_range(row.start_at, row.end_at, range_start, range_end):
            return [_serialize_event(row, **ser_kw)]
        return []

    until_date = row.recurrence_until or range_end.date()
    if until_date < range_start.date():
        return []

    occurrences: list[dict[str, Any]] = []
    cursor = row.start_at
    guard = 0

    while guard < MAX_EXPAND and cursor.date() <= until_date:
        cursor_end = cursor + duration
        if cursor > range_end:
            break
        if _event_overlaps_range(cursor, cursor_end, range_start, range_end):
            occ_date = cursor.date().isoformat()
            if occ_date not in _exdates_of(row):
                item = _serialize_event(row, occurrence_date=occ_date, **ser_kw)
                item["start_at"] = _datetime_str(cursor)
                item["end_at"] = _datetime_str(cursor_end)
                occurrences.append(item)
        if cursor_end >= range_end and cursor.date() >= until_date:
            break
        cursor = _advance_recurrence(cursor, rule)
        guard += 1

    return occurrences


async def _load_owner_maps(
    db: AsyncSession, owner_ids: set[int]
) -> tuple[dict[int, User], dict[int, str]]:
    if not owner_ids:
        return {}, {}
    result = await db.execute(select(User).where(User.id.in_(owner_ids)))
    owners = {int(u.id): u for u in result.scalars().all()}
    dept_ids = {int(u.department_id) for u in owners.values() if u.department_id is not None}
    dept_names: dict[int, str] = {}
    if dept_ids:
        from app.modules.system.models import Organization

        org_result = await db.execute(
            select(Organization.id, Organization.name).where(Organization.id.in_(dept_ids))
        )
        dept_names = {int(row[0]): str(row[1]) for row in org_result.all()}
    return owners, dept_names


async def _visibility_clause(db: AsyncSession, user: User):
    """可視性:
    - self: 本人のみ
    - department: 同一許可部門のメンバー
    - all: 全社（ログインユーザー全員）
    編集は所有者のみ（別途 API で担保）。
    """
    own = UserEvent.user_id == user.id
    company_visible = UserEvent.visibility == "all"
    dept_visible = or_(
        UserEvent.visibility == "department",
        UserEvent.visibility.is_(None),
    )
    scope = await resolve_user_data_scope(db, user)

    if scope.kind == "departments" and scope.department_ids:
        allowed = select(User.id).where(User.department_id.in_(list(scope.department_ids)))
        return or_(
            own,
            company_visible,
            and_(dept_visible, UserEvent.user_id.in_(allowed)),
        )

    my_dept = getattr(user, "department_id", None)
    if my_dept is not None:
        allowed = select(User.id).where(User.department_id == int(my_dept))
        return or_(
            own,
            company_visible,
            and_(dept_visible, UserEvent.user_id.in_(allowed)),
        )

    return or_(own, company_visible)


async def get_viewer_scope_label(db: AsyncSession, user: User) -> str:
    """カレンダー実効範囲（全社横断はしない）。"""
    scope = await resolve_user_data_scope(db, user)
    if scope.kind == "departments" and scope.department_ids:
        return "department"
    if getattr(user, "department_id", None) is not None:
        return "department"
    return "self"


async def _get_user_event(db: AsyncSession, user: User, event_id: int) -> UserEvent:
    result = await db.execute(
        select(UserEvent).where(UserEvent.id == event_id, UserEvent.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="イベントが見つかりません")
    return row


async def _serialize_owned(
    db: AsyncSession, row: UserEvent, viewer: User, *, occurrence_date: Optional[str] = None
) -> dict[str, Any]:
    owners, dept_names = await _load_owner_maps(db, {int(row.user_id)})
    owner = owners.get(int(row.user_id))
    dept_name = None
    if owner and owner.department_id is not None:
        dept_name = dept_names.get(int(owner.department_id))
    return _serialize_event(
        row,
        occurrence_date=occurrence_date,
        viewer_id=viewer.id,
        owner=owner,
        department_name=dept_name,
    )


async def list_events(
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
    range_start = datetime.combine(date_from, time(0, 0))
    range_end = datetime.combine(date_to, time(23, 59, 59))
    visible = await _visibility_clause(db, user)

    result = await db.execute(
        select(UserEvent)
        .where(
            visible,
            UserEvent.start_at <= range_end,
            or_(
                UserEvent.recurrence_rule.isnot(None),
                UserEvent.end_at >= range_start,
            ),
        )
        .order_by(UserEvent.start_at.asc(), UserEvent.id.asc())
    )
    rows = list(result.scalars().all())
    owners, dept_names = await _load_owner_maps(db, {int(r.user_id) for r in rows})

    expanded: list[dict[str, Any]] = []
    for row in rows:
        owner = owners.get(int(row.user_id))
        dept_name = None
        if owner and owner.department_id is not None:
            dept_name = dept_names.get(int(owner.department_id))
        expanded.extend(
            _expand_event_in_range(
                row,
                range_start,
                range_end,
                viewer_id=user.id,
                owner=owner,
                department_name=dept_name,
            )
        )

    expanded.sort(key=lambda item: (item["start_at"] or "", item["id"]))
    return expanded


async def get_upcoming(db: AsyncSession, user: User) -> dict[str, Any]:
    """リマインドは所有者本人のみ。badge=未確認リマインド件数。"""
    now = now_jst().replace(tzinfo=None)
    today = now.date()
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)  # Sunday-start like JS dayjs
    week_end = week_start + timedelta(days=6)
    scan_start = datetime.combine(today - timedelta(days=1), time(0, 0))
    scan_end = datetime.combine(today + timedelta(days=7), time(23, 59, 59))

    result = await db.execute(
        select(UserEvent).where(
            UserEvent.user_id == user.id,
            UserEvent.remind_offset_minutes.isnot(None),
        )
    )
    rows = list(result.scalars().all())
    owners, dept_names = await _load_owner_maps(db, {int(r.user_id) for r in rows})

    due_now: list[dict[str, Any]] = []

    for row in rows:
        owner = owners.get(int(row.user_id))
        dept_name = None
        if owner and owner.department_id is not None:
            dept_name = dept_names.get(int(owner.department_id))
        reminded = _reminded_dates_of(row)
        for occ in _expand_event_in_range(
            row,
            scan_start,
            scan_end,
            viewer_id=user.id,
            owner=owner,
            department_name=dept_name,
        ):
            start_at = _parse_datetime(occ["start_at"] or "")
            all_day = bool(occ.get("all_day"))
            remind_at = _compute_event_remind_at(
                start_at,
                all_day=all_day,
                remind_offset_minutes=row.remind_offset_minutes,
            )
            if remind_at is None:
                continue

            occ_date = occ.get("occurrence_date") or start_at.date().isoformat()
            if row.recurrence_rule:
                already_ack = occ_date in reminded
            else:
                already_ack = row.reminded_at is not None or occ_date in reminded

            if remind_at <= now and not already_ack:
                due_now.append(occ)

    due_now.sort(key=lambda item: item.get("start_at") or "")
    today_events = await list_events(db, user, date_from=today, date_to=today)
    week_events = await list_events(db, user, date_from=week_start, date_to=week_end)
    return {
        "due_now": due_now,
        "badge_count": len(due_now),
        "today_count": len(today_events),
        "week_count": len(week_events),
    }


async def create_event(
    db: AsyncSession,
    user: User,
    *,
    title: str,
    start_at: str,
    end_at: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    all_day: bool = False,
    color: Optional[str] = None,
    visibility: Optional[str] = None,
    recurrence_rule: Optional[str] = None,
    recurrence_until: Optional[str] = None,
    remind_offset_minutes: Optional[int] = None,
) -> dict[str, Any]:
    start_dt = _parse_datetime(start_at)
    end_dt = _parse_datetime(end_at)
    start_norm, end_norm, all_day_flag = _normalize_range(start_dt, end_dt, all_day=all_day)
    parsed_offset = _validate_remind_offset(remind_offset_minutes)
    parsed_rule = _validate_recurrence(recurrence_rule)
    parsed_until = _parse_date(recurrence_until) if recurrence_until else None
    if parsed_rule and parsed_until and parsed_until < start_norm.date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="繰り返し終了日は開始日以降にしてください",
        )

    row = UserEvent(
        user_id=user.id,
        title=_validate_title(title),
        description=_validate_optional_text(description, max_len=MAX_DESCRIPTION_LEN, label="詳細"),
        location=_validate_optional_text(location, max_len=MAX_LOCATION_LEN, label="場所"),
        start_at=start_norm,
        end_at=end_norm,
        all_day=all_day_flag,
        color=_validate_color(color),
        visibility=_validate_visibility(visibility),
        recurrence_rule=parsed_rule,
        recurrence_until=parsed_until,
        remind_offset_minutes=parsed_offset,
    )
    if parsed_offset is not None:
        _refresh_remind_at(row)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _serialize_owned(db, row, user)


def _occurrence_start_for(row: UserEvent, occ: date) -> datetime:
    """系列アンカーの時計を保ったまま発生日の開始日時を作る。"""
    return datetime.combine(occ, row.start_at.time())


async def update_event(
    db: AsyncSession,
    user: User,
    event_id: int,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    all_day: Optional[bool] = None,
    color: Optional[str] = None,
    visibility: Optional[str] = None,
    recurrence_rule: Optional[str] = None,
    recurrence_until: Optional[str] = None,
    remind_offset_minutes: Optional[int] = ...,  # type: ignore[assignment]
    edit_scope: Optional[str] = None,
    occurrence_date: Optional[str] = None,
) -> dict[str, Any]:
    row = await _get_user_event(db, user, event_id)
    scope = _validate_edit_scope(edit_scope)
    has_recurrence = bool((row.recurrence_rule or "").strip())
    occ_date = _parse_date(occurrence_date) if occurrence_date else None

    # 繰り返しの「この予定のみ / これ以降」
    if has_recurrence and scope in ("this", "following") and occ_date is not None:
        duration = row.end_at - row.start_at
        next_all_day = bool(row.all_day) if all_day is None else bool(all_day)
        if start_at is not None or end_at is not None:
            next_start = _parse_datetime(start_at) if start_at is not None else _occurrence_start_for(row, occ_date)
            next_end = (
                _parse_datetime(end_at)
                if end_at is not None
                else next_start + duration
            )
        else:
            next_start = _occurrence_start_for(row, occ_date)
            next_end = next_start + duration

        overrides: dict[str, Any] = {}
        if title is not None:
            overrides["title"] = title
        if description is not None:
            overrides["description"] = description
        if location is not None:
            overrides["location"] = location
        if color is not None:
            overrides["color"] = color
        if visibility is not None:
            overrides["visibility"] = visibility
        if remind_offset_minutes is not ...:
            overrides["remind_offset_minutes"] = remind_offset_minutes

        if scope == "this":
            _add_exdate(row, occ_date)
            new_row = await _create_detached_occurrence(
                db,
                user,
                row,
                start_at=next_start,
                end_at=next_end,
                all_day=next_all_day,
                overrides=overrides,
                with_recurrence=False,
            )
            await db.commit()
            await db.refresh(new_row)
            return await _serialize_owned(db, new_row, user)

        # following: 元系列を発生日前日で打ち切り、新規系列を作成
        day_before = occ_date - timedelta(days=1)
        if day_before < row.start_at.date():
            # 先頭から「これ以降」= 全件更新扱い
            scope = "all"
        else:
            row.recurrence_until = day_before
            until = row.recurrence_until
            if recurrence_until is not None:
                until = _parse_date(recurrence_until) if recurrence_until.strip() else None
            rule = row.recurrence_rule
            if recurrence_rule is not None:
                rule = _validate_recurrence(recurrence_rule)
            new_row = await _create_detached_occurrence(
                db,
                user,
                row,
                start_at=next_start,
                end_at=next_end,
                all_day=next_all_day,
                overrides=overrides,
                with_recurrence=True,
                recurrence_rule=rule,
                recurrence_until=until,
            )
            await db.commit()
            await db.refresh(new_row)
            return await _serialize_owned(db, new_row, user)

    if title is not None:
        row.title = _validate_title(title)
    if description is not None:
        row.description = _validate_optional_text(
            description, max_len=MAX_DESCRIPTION_LEN, label="詳細"
        )
    if location is not None:
        row.location = _validate_optional_text(location, max_len=MAX_LOCATION_LEN, label="場所")
    if color is not None:
        row.color = _validate_color(color)
    if visibility is not None:
        row.visibility = _validate_visibility(visibility)

    if recurrence_rule is not None:
        row.recurrence_rule = _validate_recurrence(recurrence_rule)
    if recurrence_until is not None:
        row.recurrence_until = _parse_date(recurrence_until) if recurrence_until.strip() else None

    if remind_offset_minutes is not ...:
        row.remind_offset_minutes = _validate_remind_offset(remind_offset_minutes)
        if row.remind_offset_minutes is None:
            row.remind_at = None
            row.reminded_at = None
            row.last_reminded_occurrence = None
            row.reminded_dates = None
        else:
            _refresh_remind_at(row)

    next_all_day = bool(row.all_day) if all_day is None else bool(all_day)
    next_start = row.start_at if start_at is None else _parse_datetime(start_at)
    next_end = row.end_at if end_at is None else _parse_datetime(end_at)
    if start_at is not None or end_at is not None or all_day is not None:
        start_norm, end_norm, all_day_flag = _normalize_range(
            next_start, next_end, all_day=next_all_day
        )
        row.start_at = start_norm
        row.end_at = end_norm
        row.all_day = all_day_flag
        if row.remind_offset_minutes is not None:
            _refresh_remind_at(row)

    await db.commit()
    await db.refresh(row)
    return await _serialize_owned(db, row, user)


async def reschedule_event(
    db: AsyncSession,
    user: User,
    event_id: int,
    *,
    start_at: str,
    end_at: str,
    edit_scope: Optional[str] = None,
    occurrence_date: Optional[str] = None,
) -> dict[str, Any]:
    return await update_event(
        db,
        user,
        event_id,
        start_at=start_at,
        end_at=end_at,
        edit_scope=edit_scope,
        occurrence_date=occurrence_date,
    )


async def ack_reminder(
    db: AsyncSession,
    user: User,
    event_id: int,
    *,
    occurrence_date: Optional[str] = None,
) -> dict[str, Any]:
    row = await _get_user_event(db, user, event_id)
    occ = _parse_date(occurrence_date) if occurrence_date else row.start_at.date()
    _mark_reminded(row, occ)
    await db.commit()
    await db.refresh(row)
    occ_key = occ.isoformat()
    return await _serialize_owned(
        db, row, user, occurrence_date=occ_key if row.recurrence_rule else None
    )


async def delete_event(
    db: AsyncSession,
    user: User,
    event_id: int,
    *,
    edit_scope: Optional[str] = None,
    occurrence_date: Optional[str] = None,
) -> None:
    row = await _get_user_event(db, user, event_id)
    scope = _validate_edit_scope(edit_scope)
    has_recurrence = bool((row.recurrence_rule or "").strip())
    occ_date = _parse_date(occurrence_date) if occurrence_date else None

    if has_recurrence and scope == "this" and occ_date is not None:
        _add_exdate(row, occ_date)
        await db.commit()
        return

    if has_recurrence and scope == "following" and occ_date is not None:
        day_before = occ_date - timedelta(days=1)
        if day_before < row.start_at.date():
            await db.delete(row)
        else:
            row.recurrence_until = day_before
        await db.commit()
        return

    await db.delete(row)
    await db.commit()
