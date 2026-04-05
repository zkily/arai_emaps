"""
部品マスタ API（part_masters）
単価は原通貨、exchange_rate は 1 原通貨あたりの JPY。標準原価(円) = unit_price * exchange_rate
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import PartMaster, Supplier

router = APIRouter()


def _jpy_standard(row: PartMaster) -> float:
    up = row.unit_price or Decimal("0")
    ex = row.exchange_rate or Decimal("1")
    return float(up * ex)


def _row_dict(row: PartMaster, supplier_name: Optional[str] = None) -> dict:
    d = {
        "id": row.id,
        "part_cd": row.part_cd,
        "part_name": row.part_name,
        "uom": row.uom,
        "unit_price": float(row.unit_price) if row.unit_price is not None else 0.0,
        "currency": row.currency or "JPY",
        "exchange_rate": float(row.exchange_rate) if row.exchange_rate is not None else 1.0,
        "standard_price_jpy": _jpy_standard(row),
        "supplier_cd": row.supplier_cd,
        "status": row.status,
        "remarks": row.remarks,
        "created_by": row.created_by,
        "updated_by": row.updated_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
    if supplier_name is not None:
        d["supplier_name"] = supplier_name
    return d


class PartIn(BaseModel):
    part_cd: str = Field(..., min_length=1, max_length=50)
    part_name: str = Field(..., min_length=1, max_length=200)
    uom: str = Field(default="個", max_length=20)
    unit_price: float = Field(default=0, ge=0)
    currency: str = Field(default="JPY", max_length=10)
    exchange_rate: float = Field(default=1.0, gt=0)
    supplier_cd: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="active", max_length=20)
    remarks: Optional[str] = None


class PartPatch(BaseModel):
    part_name: Optional[str] = Field(None, max_length=200)
    uom: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    exchange_rate: Optional[float] = Field(None, gt=0)
    supplier_cd: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    remarks: Optional[str] = None


@router.get("")
async def list_parts(
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(PartMaster)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        q = q.where(or_(PartMaster.part_cd.like(k), PartMaster.part_name.like(k)))
    if status:
        q = q.where(PartMaster.status == status)
    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.order_by(PartMaster.part_cd).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    sup_cds = {r.supplier_cd for r in rows if r.supplier_cd}
    sup_map = {}
    if sup_cds:
        sq = select(Supplier).where(Supplier.supplier_cd.in_(sup_cds))
        for s in (await db.execute(sq)).scalars().all():
            sup_map[s.supplier_cd] = s.supplier_name
    return {
        "success": True,
        "data": {
            "list": [_row_dict(r, sup_map.get(r.supplier_cd) if r.supplier_cd else None) for r in rows],
            "total": total,
        },
    }


@router.get("/{part_id}")
async def get_part(
    part_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(PartMaster, part_id)
    if not row:
        raise HTTPException(404, "部品が見つかりません")
    sup_name = None
    if row.supplier_cd:
        sq = select(Supplier).where(Supplier.supplier_cd == row.supplier_cd)
        sup = (await db.execute(sq)).scalar_one_or_none()
        if sup:
            sup_name = sup.supplier_name
    return {"success": True, "data": _row_dict(row, sup_name)}


@router.post("")
async def create_part(
    body: PartIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    dup = await db.execute(select(PartMaster).where(PartMaster.part_cd == body.part_cd.strip()))
    if dup.scalar_one_or_none():
        raise HTTPException(400, "部品CDは既に存在します")
    row = PartMaster(
        part_cd=body.part_cd.strip(),
        part_name=body.part_name.strip(),
        uom=body.uom.strip() or "個",
        unit_price=body.unit_price,
        currency=(body.currency or "JPY").strip().upper()[:10],
        exchange_rate=body.exchange_rate,
        supplier_cd=body.supplier_cd.strip() if body.supplier_cd else None,
        status=body.status or "active",
        remarks=body.remarks,
        created_by=current_user.username if current_user else None,
        updated_by=current_user.username if current_user else None,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _row_dict(row)}


@router.put("/{part_id}")
async def update_part(
    part_id: int,
    body: PartPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(PartMaster, part_id)
    if not row:
        raise HTTPException(404, "部品が見つかりません")
    data = body.model_dump(exclude_unset=True)
    if "part_name" in data and data["part_name"] is not None:
        row.part_name = str(data["part_name"]).strip()
    if "uom" in data and data["uom"] is not None:
        row.uom = str(data["uom"]).strip() or "個"
    if "unit_price" in data and data["unit_price"] is not None:
        row.unit_price = data["unit_price"]
    if "currency" in data and data["currency"] is not None:
        row.currency = str(data["currency"]).strip().upper()[:10]
    if "exchange_rate" in data and data["exchange_rate"] is not None:
        row.exchange_rate = data["exchange_rate"]
    if "supplier_cd" in data:
        row.supplier_cd = str(data["supplier_cd"]).strip() if data["supplier_cd"] else None
    if "status" in data and data["status"] is not None:
        row.status = data["status"]
    if "remarks" in data:
        row.remarks = data["remarks"]
    row.updated_by = current_user.username if current_user else None
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _row_dict(row)}


@router.delete("/{part_id}")
async def delete_part(
    part_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(PartMaster, part_id)
    if not row:
        raise HTTPException(404, "部品が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}
