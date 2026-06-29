"""
サイドバー常用ページ：ビジネスロジック
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.auth.api import get_user_menu_codes
from app.modules.auth.models import User
from app.modules.auth.permission_service import user_is_super_admin
from app.modules.auth.shortcut_models import UserPageVisit, UserPinnedPage
from app.modules.system.models import Menu

MAX_PINNED = 12
MAX_VISIT_RECORDS = 100
FREQUENT_LIMIT = 5
VISIT_THROTTLE_MINUTES = 5
EXCLUDED_PATHS = frozenset({"/login", "/dashboard"})


async def _codes_for_path(db: AsyncSession, path: str) -> list[str]:
    result = await db.execute(
        select(Menu.code).where(Menu.path == path, Menu.is_active == True)  # noqa: E712
    )
    return list(result.scalars().all())


async def _can_access_path(
    db: AsyncSession,
    user: User,
    path: str,
    menu_codes: Optional[list[str]] = None,
) -> bool:
    normalized = (path or "").strip()
    if not normalized or normalized in EXCLUDED_PATHS:
        return False
    if normalized == "/access-denied":
        return True
    if normalized == "/system" or normalized.startswith("/system/"):
        return await user_is_super_admin(db, user)

    codes = await _codes_for_path(db, normalized)
    if not codes:
        return False

    if await user_is_super_admin(db, user):
        return True

    allowed = menu_codes if menu_codes is not None else await get_user_menu_codes(db, user)
    return any(code in allowed for code in codes)


async def _menu_code_for_path(db: AsyncSession, path: str) -> Optional[str]:
    codes = await _codes_for_path(db, path)
    return codes[0] if codes else None


def _recency_weight(last_visited_at) -> float:
    now = now_jst()
    if last_visited_at.tzinfo is None:
        from app.core.datetime_utils import JST

        last_visited_at = JST.localize(last_visited_at)
    days = (now - last_visited_at).total_seconds() / 86400
    return max(0.0, 14.0 - days) / 14.0


async def _prune_visit_records(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(
        select(UserPageVisit.id)
        .where(UserPageVisit.user_id == user_id)
        .order_by(UserPageVisit.last_visited_at.asc())
    )
    ids = list(result.scalars().all())
    overflow = len(ids) - MAX_VISIT_RECORDS
    if overflow > 0:
        to_delete = ids[:overflow]
        await db.execute(delete(UserPageVisit).where(UserPageVisit.id.in_(to_delete)))


async def get_shortcuts(db: AsyncSession, user: User) -> dict:
    menu_codes = await get_user_menu_codes(db, user)

    pin_result = await db.execute(
        select(UserPinnedPage)
        .where(UserPinnedPage.user_id == user.id)
        .order_by(UserPinnedPage.sort_order.asc(), UserPinnedPage.id.asc())
    )
    pinned_rows = list(pin_result.scalars().all())

    pinned: list[dict] = []
    pinned_paths: set[str] = set()
    for row in pinned_rows:
        if not await _can_access_path(db, user, row.path, menu_codes):
            continue
        code = await _menu_code_for_path(db, row.path)
        pinned.append({"path": row.path, "menu_code": code})
        pinned_paths.add(row.path)

    visit_result = await db.execute(
        select(UserPageVisit).where(UserPageVisit.user_id == user.id)
    )
    visit_rows = list(visit_result.scalars().all())

    candidates: list[tuple[float, UserPageVisit]] = []
    for row in visit_rows:
        if row.path in pinned_paths or row.path in EXCLUDED_PATHS:
            continue
        if not await _can_access_path(db, user, row.path, menu_codes):
            continue
        score = row.visit_count + _recency_weight(row.last_visited_at)
        candidates.append((score, row))

    candidates.sort(key=lambda x: (-x[0], -x[1].last_visited_at.timestamp()))
    frequent: list[dict] = []
    for _, row in candidates[:FREQUENT_LIMIT]:
        code = await _menu_code_for_path(db, row.path)
        frequent.append(
            {
                "path": row.path,
                "menu_code": code,
                "visit_count": row.visit_count,
                "last_visited_at": row.last_visited_at.isoformat()
                if row.last_visited_at
                else None,
            }
        )

    return {"pinned": pinned, "frequent": frequent}


async def replace_pins(db: AsyncSession, user: User, paths: list[str]) -> dict:
    if len(paths) > MAX_PINNED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ピン留めは最大{MAX_PINNED}件までです",
        )

    seen: set[str] = set()
    normalized_paths: list[str] = []
    for p in paths:
        path = (p or "").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        if not await _can_access_path(db, user, path):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"アクセス権限のないページはピン留めできません: {path}",
            )
        normalized_paths.append(path)

    await db.execute(delete(UserPinnedPage).where(UserPinnedPage.user_id == user.id))
    for idx, path in enumerate(normalized_paths):
        db.add(UserPinnedPage(user_id=user.id, path=path, sort_order=idx))
    await db.commit()
    return await get_shortcuts(db, user)


async def record_visit(db: AsyncSession, user: User, path: str) -> None:
    normalized = (path or "").strip()
    if not normalized or normalized in EXCLUDED_PATHS:
        return
    if not await _can_access_path(db, user, normalized):
        return

    now = now_jst()
    result = await db.execute(
        select(UserPageVisit).where(
            UserPageVisit.user_id == user.id,
            UserPageVisit.path == normalized,
        )
    )
    row = result.scalar_one_or_none()

    if row:
        throttle_before = now - timedelta(minutes=VISIT_THROTTLE_MINUTES)
        last = row.last_visited_at
        if last.tzinfo is None:
            from app.core.datetime_utils import JST

            last = JST.localize(last)
        if last <= throttle_before:
            row.visit_count += 1
        row.last_visited_at = now
    else:
        db.add(
            UserPageVisit(
                user_id=user.id,
                path=normalized,
                visit_count=1,
                last_visited_at=now,
            )
        )

    await db.flush()
    await _prune_visit_records(db, user.id)
    await db.commit()
