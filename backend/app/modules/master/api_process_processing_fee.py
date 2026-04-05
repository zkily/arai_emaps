"""
工程加工費マスタ API（process_processing_fees）
工程ごとに加工方法が異なれば加工費も異なる前提のマスタ。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import ProcessProcessingFee, Process

router = APIRouter()


class FeeIn(BaseModel):
    process_cd: str = Field(..., min_length=1, max_length=50)
    method_cd: str = Field(..., min_length=1, max_length=50)
    method_name: Optional[str] = None
    unit_price: float = 0.0
    currency: str = "JPY"
    charge_uom: str = "式"
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    status: str = "active"
    remarks: Optional[str] = None


def _fee_dict(row: ProcessProcessingFee, process_name: Optional[str] = None) -> dict:
    d = {
        "id": row.id,
        "process_cd": row.process_cd,
        "method_cd": row.method_cd,
        "method_name": row.method_name,
        "unit_price": float(row.unit_price) if row.unit_price is not None else 0.0,
        "currency": row.currency,
        "charge_uom": row.charge_uom,
        "effective_from": str(row.effective_from) if row.effective_from else None,
        "effective_to": str(row.effective_to) if row.effective_to else None,
        "status": row.status,
        "remarks": row.remarks,
        "created_by": row.created_by,
        "updated_by": row.updated_by,
    }
    if process_name is not None:
        d["process_name"] = process_name
    return d


@router.get("")
async def list_process_processing_fees(
    process_cd: Optional[str] = Query(None, description="単一工程CDで絞り込み"),
    process_cds: Optional[str] = Query(None, description="カンマ区切り工程CD（ルート内の複数工程用）"),
    keyword: Optional[str] = Query(None, description="方法CD/名称"),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(ProcessProcessingFee)
    proc_filter: List[str] = []
    if process_cd and process_cd.strip():
        proc_filter = [process_cd.strip()]
    elif process_cds and process_cds.strip():
        proc_filter = [x.strip() for x in process_cds.split(",") if x.strip()]
    if proc_filter:
        q = q.where(ProcessProcessingFee.process_cd.in_(proc_filter))
    if status:
        q = q.where(ProcessProcessingFee.status == status)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                ProcessProcessingFee.method_cd.like(k),
                ProcessProcessingFee.method_name.like(k),
            )
        )
    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.order_by(ProcessProcessingFee.process_cd, ProcessProcessingFee.method_cd, ProcessProcessingFee.id.desc())
    q = q.offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    proc_names: dict[str, str] = {}
    if rows:
        cds = {r.process_cd for r in rows}
        pr = await db.execute(select(Process.process_cd, Process.process_name).where(Process.process_cd.in_(cds)))
        for cd, name in pr.all():
            proc_names[cd] = name or cd
    return {
        "success": True,
        "data": {
            "list": [_fee_dict(r, proc_names.get(r.process_cd)) for r in rows],
            "total": total,
        },
    }


@router.get("/{fee_id}")
async def get_process_processing_fee(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(ProcessProcessingFee, fee_id)
    if not row:
        raise HTTPException(404, "工程加工費が見つかりません")
    pn = None
    pr = await db.execute(select(Process.process_name).where(Process.process_cd == row.process_cd))
    pn = pr.scalar_one_or_none()
    return {"success": True, "data": _fee_dict(row, pn)}


@router.post("")
async def create_process_processing_fee(
    body: FeeIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    dup_res = await db.execute(
        select(ProcessProcessingFee).where(
            and_(
                ProcessProcessingFee.process_cd == body.process_cd.strip(),
                ProcessProcessingFee.method_cd == body.method_cd.strip(),
                ProcessProcessingFee.status == "active",
            )
        )
    )
    if dup_res.scalars().first():
        raise HTTPException(400, "同一工程・加工方法の有効行が既に存在します")
    row = ProcessProcessingFee(
        process_cd=body.process_cd.strip(),
        method_cd=body.method_cd.strip(),
        method_name=body.method_name,
        unit_price=body.unit_price,
        currency=body.currency or "JPY",
        charge_uom=body.charge_uom or "式",
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        status=body.status or "active",
        remarks=body.remarks,
        created_by=current_user.username if current_user else None,
        updated_by=current_user.username if current_user else None,
    )
    db.add(row)
    await db.flush()
    return {"success": True, "data": _fee_dict(row)}


@router.put("/{fee_id}")
async def update_process_processing_fee(
    fee_id: int,
    body: FeeIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(ProcessProcessingFee, fee_id)
    if not row:
        raise HTTPException(404, "工程加工費が見つかりません")
    row.process_cd = body.process_cd.strip()
    row.method_cd = body.method_cd.strip()
    row.method_name = body.method_name
    row.unit_price = body.unit_price
    row.currency = body.currency or "JPY"
    row.charge_uom = body.charge_uom or "式"
    row.effective_from = body.effective_from
    row.effective_to = body.effective_to
    row.status = body.status or "active"
    row.remarks = body.remarks
    row.updated_by = current_user.username if current_user else None
    return {"success": True, "data": _fee_dict(row)}


@router.delete("/{fee_id}")
async def delete_process_processing_fee(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(ProcessProcessingFee, fee_id)
    if not row:
        raise HTTPException(404, "工程加工費が見つかりません")
    await db.delete(row)
    return {"success": True, "message": "削除しました"}
