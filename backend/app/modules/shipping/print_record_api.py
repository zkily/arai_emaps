"""
印刷記録 API (shipping_records テーブル)
- POST /print-record: 出荷番号の印刷記録を保存
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import List

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db

router = APIRouter()


class PrintRecordBody(BaseModel):
    shipping_numbers: List[str]


@router.post("")
async def save_print_record(
    body: PrintRecordBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """出荷番号の印刷記録を shipping_records に保存（重複は無視または更新）"""
    if not body.shipping_numbers:
        return {"success": True, "count": 0}
    q = text(
        "INSERT INTO shipping_records (shipping_no, status) VALUES (:shipping_no, '印刷済') "
        "ON DUPLICATE KEY UPDATE status = '印刷済'"
    )
    for no in body.shipping_numbers:
        if no and str(no).strip():
            await db.execute(q, {"shipping_no": str(no).strip()})
    await db.commit()
    return {"success": True, "count": len([n for n in body.shipping_numbers if n and str(n).strip()])}
