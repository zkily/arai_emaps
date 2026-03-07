"""
設備能率管理 API（equipment_efficiency）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional
from decimal import Decimal

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import EquipmentEfficiency

router = APIRouter()


def _row_to_dict(row: EquipmentEfficiency) -> dict:
    eff = row.efficiency_rate
    if eff is not None and hasattr(eff, "__float__"):
        eff = float(eff)
    return {
        "id": row.id,
        "machine_cd": row.machine_cd,
        "machines_name": row.machines_name,
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "efficiency_rate": eff,
        "step_time": row.step_time,
        "unit": row.unit,
        "remarks": row.remarks,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_equipment_efficiency_list(
    keyword: Optional[str] = Query(None),
    limit: int = Query(99999, ge=1, le=99999),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備能率一覧"""
    query = select(EquipmentEfficiency)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                EquipmentEfficiency.machines_name.like(k),
                EquipmentEfficiency.product_name.like(k),
                EquipmentEfficiency.machine_cd.like(k),
                EquipmentEfficiency.product_cd.like(k),
            )
        )
    query = query.order_by(EquipmentEfficiency.machines_name, EquipmentEfficiency.product_name)
    result = await db.execute(query.limit(limit))
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_row_to_dict(r) for r in rows], "total": len(rows)},
        "list": [_row_to_dict(r) for r in rows],
        "total": len(rows),
    }


@router.get("/{item_id:int}")
async def get_equipment_efficiency_by_id(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """IDで1件取得"""
    result = await db.execute(select(EquipmentEfficiency).where(EquipmentEfficiency.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備能率設定が見つかりません")
    return _row_to_dict(row)


@router.post("")
async def create_equipment_efficiency(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規登録"""
    machine_cd = body.get("machine_cd") or ""
    product_cd = body.get("product_cd") or ""
    if not machine_cd or not product_cd:
        raise HTTPException(status_code=400, detail="設備コードと製品コードは必須です")
    existing = await db.execute(
        select(EquipmentEfficiency).where(
            EquipmentEfficiency.machine_cd == machine_cd,
            EquipmentEfficiency.product_cd == product_cd,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="この設備・製品の組み合わせは既に登録されています")
    eff = body.get("efficiency_rate")
    if eff is not None and not isinstance(eff, (int, float, Decimal)):
        try:
            eff = float(eff)
        except (TypeError, ValueError):
            eff = 0.0
    row = EquipmentEfficiency(
        machine_cd=machine_cd,
        machines_name=body.get("machines_name"),
        product_cd=product_cd,
        product_name=body.get("product_name"),
        efficiency_rate=eff if eff is not None else 0.0,
        step_time=body.get("step_time"),
        unit=body.get("unit"),
        remarks=body.get("remarks"),
        status=body.get("status") if body.get("status") is not None else 1,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.put("/{item_id:int}")
async def update_equipment_efficiency(
    item_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """更新"""
    result = await db.execute(select(EquipmentEfficiency).where(EquipmentEfficiency.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備能率設定が見つかりません")
    machine_cd = body.get("machine_cd")
    product_cd = body.get("product_cd")
    if machine_cd is not None:
        row.machine_cd = machine_cd
    if product_cd is not None:
        row.product_cd = product_cd
    if "machines_name" in body:
        row.machines_name = body.get("machines_name")
    if "product_name" in body:
        row.product_name = body.get("product_name")
    if "efficiency_rate" in body:
        eff = body.get("efficiency_rate")
        if eff is not None and not isinstance(eff, (int, float, Decimal)):
            try:
                eff = float(eff)
            except (TypeError, ValueError):
                eff = 0.0
        row.efficiency_rate = eff if eff is not None else 0.0
    if "step_time" in body:
        row.step_time = body.get("step_time")
    if "unit" in body:
        row.unit = body.get("unit")
    if "remarks" in body:
        row.remarks = body.get("remarks")
    if "status" in body:
        row.status = body.get("status")
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{item_id:int}")
async def delete_equipment_efficiency(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """削除"""
    result = await db.execute(select(EquipmentEfficiency).where(EquipmentEfficiency.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備能率設定が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}
