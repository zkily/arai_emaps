"""ユーザーのデータ参照範囲（roles.data_scope）を解決し、クエリに適用する。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Set

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User

ScopeKind = Literal["all", "self", "departments"]

_SCOPE_RANK: dict[str, int] = {
    "self": 0,
    "custom": 1,
    "department": 2,
    "department_below": 3,
    "all": 4,
}


@dataclass
class UserDataScope:
    """解決済みデータ範囲（複数ロールは最も広い範囲を採用）。"""

    kind: ScopeKind
    user_id: int
    data_scope: str
    department_ids: Set[int] = field(default_factory=set)

    @property
    def unrestricted(self) -> bool:
        return self.kind == "all"


async def resolve_user_data_scope(db: AsyncSession, user: User) -> UserDataScope:
    from app.modules.auth.permission_service import user_is_super_admin
    from app.modules.system.models import Organization, Role, UserRole

    if await user_is_super_admin(db, user):
        return UserDataScope(kind="all", user_id=user.id, data_scope="all")

    result = await db.execute(
        select(Role.data_scope, Role.custom_departments)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id, Role.is_active == True)
    )
    rows = list(result.all())

    if not rows:
        return await _fallback_scope(db, user)

    max_rank = max(_SCOPE_RANK.get(str(r[0] or "department"), 2) for r in rows)
    if max_rank >= _SCOPE_RANK["all"]:
        return UserDataScope(kind="all", user_id=user.id, data_scope="all")
    if max_rank == _SCOPE_RANK["self"]:
        return UserDataScope(kind="self", user_id=user.id, data_scope="self")

    dept_ids: Set[int] = set()
    for scope_val, custom_names in rows:
        label = str(scope_val or "department")
        if label == "self":
            continue
        if label == "department":
            dept_id = getattr(user, "department_id", None)
            if dept_id is not None:
                dept_ids.add(int(dept_id))
        elif label == "department_below":
            dept_id = getattr(user, "department_id", None)
            if dept_id is not None:
                dept_ids |= await _collect_org_subtree_ids(db, int(dept_id))
        elif label == "custom":
            names = _normalize_custom_department_names(custom_names)
            if names:
                dept_ids |= await _resolve_department_names_to_ids(db, names)

    effective_label = _label_for_rank(max_rank)
    if not dept_ids:
        return UserDataScope(kind="self", user_id=user.id, data_scope="self")

    return UserDataScope(
        kind="departments",
        user_id=user.id,
        data_scope=effective_label,
        department_ids=dept_ids,
    )


def _label_for_rank(rank: int) -> str:
    for label, r in _SCOPE_RANK.items():
        if r == rank:
            return label
    return "department"


async def _fallback_scope(db: AsyncSession, user: User) -> UserDataScope:
    dept_id = getattr(user, "department_id", None)
    if dept_id is not None:
        return UserDataScope(
            kind="departments",
            user_id=user.id,
            data_scope="department",
            department_ids={int(dept_id)},
        )
    return UserDataScope(kind="self", user_id=user.id, data_scope="self")


def _normalize_custom_department_names(raw: object) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []


async def _resolve_department_names_to_ids(db: AsyncSession, names: list[str]) -> Set[int]:
    from app.modules.system.models import Organization

    result = await db.execute(
        select(Organization.id).where(
            Organization.name.in_(names),
            Organization.is_active == True,
        )
    )
    return {int(x) for x in result.scalars().all()}


async def _collect_org_subtree_ids(db: AsyncSession, root_id: int) -> Set[int]:
    from app.modules.system.models import Organization

    result = await db.execute(
        select(Organization.id, Organization.parent_id).where(Organization.is_active == True)
    )
    rows = list(result.all())
    children_map: dict[Optional[int], list[int]] = {}
    for oid, parent_id in rows:
        children_map.setdefault(parent_id, []).append(int(oid))

    seen: Set[int] = set()
    stack = [root_id]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(children_map.get(current, []))
    return seen


def apply_scope_to_users_query(query: Select, scope: UserDataScope, user_model: type) -> Select:
    """users 一覧用: department_id / id で絞り込み。"""
    if scope.unrestricted:
        return query
    if scope.kind == "self":
        return query.where(user_model.id == scope.user_id)
    if scope.department_ids:
        return query.where(user_model.department_id.in_(scope.department_ids))
    return query.where(user_model.id == scope.user_id)


def apply_scope_to_user_id_column(query: Select, scope: UserDataScope, user_id_column) -> Select:
    """操作ログ等: レコードの user_id 列で絞り込み（部門は users サブクエリ）。"""
    if scope.unrestricted:
        return query
    if scope.kind == "self":
        return query.where(
            or_(user_id_column == scope.user_id, user_id_column.is_(None))
        )
    if scope.kind == "departments" and scope.department_ids:
        allowed_users = select(User.id).where(User.department_id.in_(scope.department_ids))
        return query.where(
            or_(user_id_column.in_(allowed_users), user_id_column.is_(None))
        )
    return query.where(
        or_(user_id_column == scope.user_id, user_id_column.is_(None))
    )


def apply_scope_to_owner_user_id(query: Select, scope: UserDataScope, owner_column) -> Select:
    """created_by = users.id の業務テーブル用。"""
    if scope.unrestricted:
        return query
    if scope.kind == "self":
        return query.where(owner_column == scope.user_id)
    if scope.kind == "departments" and scope.department_ids:
        allowed_users = select(User.id).where(User.department_id.in_(scope.department_ids))
        return query.where(owner_column.in_(allowed_users))
    return query.where(owner_column == scope.user_id)


def apply_scope_to_owner_username(query: Select, scope: UserDataScope, username_column, username: str) -> Select:
    """created_by = username の業務テーブル用（self のみ厳密、部門は同部門ユーザーの username）。"""
    if scope.unrestricted:
        return query
    if scope.kind == "self":
        if username:
            return query.where(username_column == username)
        return query.where(username_column.is_(None))
    if scope.kind == "departments" and scope.department_ids:
        allowed_users = select(User.username).where(
            User.department_id.in_(scope.department_ids),
            User.username.isnot(None),
        )
        return query.where(username_column.in_(allowed_users))
    if username:
        return query.where(username_column == username)
    return query.where(username_column.is_(None))
