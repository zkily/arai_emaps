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
    """出荷番号の印刷記録を shipping_records に保存し、該当 shipping_items の status を「発行済」に更新"""
    if not body.shipping_numbers:
        return {"success": True, "count": 0}
    numbers = [str(n).strip() for n in body.shipping_numbers if n and str(n).strip()]
    if not numbers:
        return {"success": True, "count": 0}

    # 1) shipping_records に印刷済を保存
    q = text(
        "INSERT INTO shipping_records (shipping_no, status) VALUES (:shipping_no, '印刷済') "
        "ON DUPLICATE KEY UPDATE status = '印刷済'"
    )
    for no in numbers:
        await db.execute(q, {"shipping_no": no})

    # 2) 該当出荷番号の shipping_items の status を「発行済」に更新（一覧の状態欄と一致させる）
    placeholders = ", ".join([f":n{i}" for i in range(len(numbers))])
    params = {f"n{i}": no for i, no in enumerate(numbers)}
    upd_items = text(
        f"UPDATE shipping_items SET status = '発行済' WHERE shipping_no IN ({placeholders})"
    )
    await db.execute(upd_items, params)

    await db.commit()
    return {"success": True, "count": len(numbers)}
