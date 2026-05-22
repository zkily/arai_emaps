"""
マスタのオプション一覧 API（フロントの /api/master/options/* 呼び出し用）
- GET /destination-options: 納入先オプション（有効のみ）cd/name
- GET /destination-options-with-issue-type: 上記 + issue_type
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Destination

router = APIRouter()


@router.get("/destination-options")
async def get_destination_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先オプション（有効のみ）。返却: [{ cd, name }, ...]"""
    q = select(Destination).where(Destination.status == 1).order_by(Destination.destination_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [{"cd": r.destination_cd, "name": r.destination_name or r.destination_cd} for r in rows]


@router.get("/destination-options-with-issue-type")
async def get_destination_options_with_issue_type(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先オプション（有効のみ）+ issue_type。返却: [{ cd, name, issue_type }, ...]"""
    q = select(Destination).where(Destination.status == 1).order_by(Destination.destination_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "cd": r.destination_cd,
            "name": r.destination_name or r.destination_cd,
            "issue_type": r.issue_type or "自動",
        }
        for r in rows
    ]
