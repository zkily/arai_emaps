"""通知受信者の解決（notification_recipients 独立表・方案 B）"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.system.settings_models import NotificationRecipient


@dataclass(frozen=True)
class ResolvedRecipient:
    email: str
    name: str
    source: str


async def resolve_notification_recipients(
    db: AsyncSession,
    event_code: str,
    *,
    machine_cd: str | None = None,
) -> list[ResolvedRecipient]:
    """イベントコードに紐づく有効な受信者をメールアドレス単位で重複排除して返す。"""
    result = await db.execute(
        select(NotificationRecipient).where(
            NotificationRecipient.event_code == event_code,
            NotificationRecipient.is_active.is_(True),
        )
    )
    rows = result.scalars().all()
    if machine_cd:
        scoped = [r for r in rows if not r.machine_cd or r.machine_cd == machine_cd]
        if scoped:
            rows = scoped

    resolved: dict[str, ResolvedRecipient] = {}

    user_ids = {r.user_id for r in rows if r.recipient_type == "user" and r.user_id}
    users_by_id: dict[int, User] = {}
    if user_ids:
        user_res = await db.execute(select(User).where(User.id.in_(user_ids), User.is_active.is_(True)))
        users_by_id = {u.id: u for u in user_res.scalars().all()}

    roles = {r.role for r in rows if r.recipient_type == "role" and r.role}
    users_by_role: dict[str, list[User]] = {}
    if roles:
        role_res = await db.execute(select(User).where(User.role.in_(roles), User.is_active.is_(True)))
        for u in role_res.scalars().all():
            users_by_role.setdefault(u.role, []).append(u)

    for row in rows:
        if row.recipient_type == "user" and row.user_id:
            user = users_by_id.get(row.user_id)
            if user and user.email:
                resolved[user.email.lower()] = ResolvedRecipient(
                    email=user.email,
                    name=(user.full_name or user.username or user.email),
                    source="user",
                )
        elif row.recipient_type == "email" and row.email:
            email = row.email.strip()
            if email:
                resolved[email.lower()] = ResolvedRecipient(
                    email=email,
                    name=(row.display_name or email),
                    source="email",
                )
        elif row.recipient_type == "role" and row.role:
            for user in users_by_role.get(row.role, []):
                if user.email:
                    resolved[user.email.lower()] = ResolvedRecipient(
                        email=user.email,
                        name=(user.full_name or user.username or user.email),
                        source=f"role:{row.role}",
                    )

    return list(resolved.values())


@dataclass(frozen=True)
class ResolvedLineRecipient:
    line_user_id: str
    name: str
    source: str


async def resolve_line_recipients(
    db: AsyncSession,
    event_code: str,
    *,
    machine_cd: str | None = None,
) -> list[ResolvedLineRecipient]:
    """イベントに紐づく LINE 受信者（recipient_type=line）を返す。"""
    result = await db.execute(
        select(NotificationRecipient).where(
            NotificationRecipient.event_code == event_code,
            NotificationRecipient.is_active.is_(True),
            NotificationRecipient.recipient_type == "line",
        )
    )
    rows = result.scalars().all()
    if machine_cd:
        scoped = [r for r in rows if not r.machine_cd or r.machine_cd == machine_cd]
        if scoped:
            rows = scoped

    resolved: dict[str, ResolvedLineRecipient] = {}
    for row in rows:
        uid = (row.line_user_id or "").strip()
        if not uid:
            continue
        resolved[uid] = ResolvedLineRecipient(
            line_user_id=uid,
            name=(row.display_name or uid),
            source="line",
        )
    return list(resolved.values())
