"""RBAC 権限判定（roles を正とする。users.role は同期用 legacy コード）。"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.auth.role_codes import (
    LEGACY_ROLE_NAME_TO_CODE,
    coarse_permissions_for_role_code,
    legacy_role_code_from_name,
    user_role_code_for_role,
)

__all__ = [
    "LEGACY_ROLE_NAME_TO_CODE",
    "assert_super_admin",
    "coarse_permissions_for_role_code",
    "legacy_role_code_from_name",
    "user_is_super_admin",
    "user_role_code_for_role",
]


async def user_is_super_admin(db: AsyncSession, user: User) -> bool:
    """システム全体の管理者（全メニュー・管理 API）。"""
    if (user.role or "") == "admin":
        return True
    from app.modules.system.models import Role, UserRole

    result = await db.execute(
        select(Role.id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user.id,
            Role.is_active == True,
            Role.is_super_admin == True,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def assert_super_admin(db: AsyncSession, user: User) -> None:
    if not await user_is_super_admin(db, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です",
        )
