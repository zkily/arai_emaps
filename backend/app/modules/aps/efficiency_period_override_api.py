"""
設備能率の期間指定 API（equipment_efficiency_period_override）

製品 + 設備 + 期間（終了日必須）で本/H を上書き。
未指定日は従来の equipment_efficiency ロジックを使用。
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_aps_operation
from app.modules.master.models import EquipmentEfficiencyPeriodOverride, Machine

router = APIRouter(prefix="/efficiency-period-overrides", tags=["APS能率期間指定"])


class EfficiencyPeriodOverrideBody(BaseModel):
    machine_cd: str = Field(..., min_length=1)
    product_cd: str = Field(..., min_length=1)
    efficiency_rate: float = Field(..., gt=0)
    period_from: date
    period_to: date
    machines_name: Optional[str] = None
    product_name: Optional[str] = None
    remarks: Optional[str] = None
    status: Optional[int] = 1


def _row_to_dict(row: EquipmentEfficiencyPeriodOverride) -> Dict[str, Any]:
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
        "period_from": row.period_from.isoformat() if row.period_from else None,
        "period_to": row.period_to.isoformat() if row.period_to else None,
        "status": row.status,
        "remarks": row.remarks,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _parse_rate(value: Any) -> float:
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail="能率（本/H）が不正です") from e


async def _ensure_no_overlap(
    db: AsyncSession,
    *,
    machine_cd: str,
    product_cd: str,
    period_from: date,
    period_to: date,
    exclude_id: Optional[int] = None,
) -> None:
    clauses = [
        EquipmentEfficiencyPeriodOverride.machine_cd == machine_cd,
        EquipmentEfficiencyPeriodOverride.product_cd == product_cd,
        or_(
            EquipmentEfficiencyPeriodOverride.status.is_(None),
            EquipmentEfficiencyPeriodOverride.status == 1,
        ),
        # overlap: NOT (to < from OR from > to)
        EquipmentEfficiencyPeriodOverride.period_from <= period_to,
        EquipmentEfficiencyPeriodOverride.period_to >= period_from,
    ]
    if exclude_id is not None:
        clauses.append(EquipmentEfficiencyPeriodOverride.id != exclude_id)
    res = await db.execute(select(EquipmentEfficiencyPeriodOverride).where(and_(*clauses)).limit(1))
    if res.scalars().first() is not None:
        raise HTTPException(
            status_code=400,
            detail="同一設備・製品で期間が重複する指定が既にあります",
        )


@router.get("")
async def list_efficiency_period_overrides(
    machine_cd: Optional[str] = Query(None, alias="machineCd"),
    product_cd: Optional[str] = Query(None, alias="productCd"),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    active_only: bool = Query(True, alias="activeOnly"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """期間指定能率一覧。"""
    clauses: List[Any] = []
    mcd = (machine_cd or "").strip()
    pcd = (product_cd or "").strip()
    if mcd:
        clauses.append(EquipmentEfficiencyPeriodOverride.machine_cd == mcd)
    if pcd:
        clauses.append(EquipmentEfficiencyPeriodOverride.product_cd == pcd)
    if active_only:
        clauses.append(
            or_(
                EquipmentEfficiencyPeriodOverride.status.is_(None),
                EquipmentEfficiencyPeriodOverride.status == 1,
            )
        )
    if from_date is not None and to_date is not None:
        clauses.append(EquipmentEfficiencyPeriodOverride.period_from <= to_date)
        clauses.append(EquipmentEfficiencyPeriodOverride.period_to >= from_date)
    elif from_date is not None:
        clauses.append(EquipmentEfficiencyPeriodOverride.period_to >= from_date)
    elif to_date is not None:
        clauses.append(EquipmentEfficiencyPeriodOverride.period_from <= to_date)

    stmt = select(EquipmentEfficiencyPeriodOverride)
    if clauses:
        stmt = stmt.where(and_(*clauses))
    stmt = stmt.order_by(
        EquipmentEfficiencyPeriodOverride.machine_cd,
        EquipmentEfficiencyPeriodOverride.product_cd,
        EquipmentEfficiencyPeriodOverride.period_from.desc(),
        EquipmentEfficiencyPeriodOverride.id.desc(),
    )
    try:
        res = await db.execute(stmt)
        rows = res.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                "equipment_efficiency_period_override テーブルがありません。"
                "backend/database/migrations/117_equipment_efficiency_period_override.sql を適用してください。"
            ),
        ) from e
    return {"success": True, "data": [_row_to_dict(r) for r in rows]}


@router.post("")
async def create_efficiency_period_override(
    body: EfficiencyPeriodOverrideBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    machine_cd = body.machine_cd.strip()
    product_cd = body.product_cd.strip()
    if body.period_from > body.period_to:
        raise HTTPException(status_code=400, detail="開始日は終了日以前である必要があります")
    rate = _parse_rate(body.efficiency_rate)
    if rate <= 0:
        raise HTTPException(status_code=400, detail="能率（本/H）は 0 より大きい値にしてください")

    await _ensure_no_overlap(
        db,
        machine_cd=machine_cd,
        product_cd=product_cd,
        period_from=body.period_from,
        period_to=body.period_to,
    )

    machines_name = (body.machines_name or "").strip() or None
    if not machines_name:
        mres = await db.execute(select(Machine).where(Machine.machine_cd == machine_cd).limit(1))
        m = mres.scalars().first()
        if m is not None:
            machines_name = (m.machine_name or "").strip() or None

    row = EquipmentEfficiencyPeriodOverride(
        machine_cd=machine_cd,
        machines_name=machines_name,
        product_cd=product_cd,
        product_name=(body.product_name or "").strip() or None,
        efficiency_rate=rate,
        period_from=body.period_from,
        period_to=body.period_to,
        status=1 if body.status is None else int(body.status),
        remarks=(body.remarks or "").strip() or None,
    )
    db.add(row)
    try:
        await db.commit()
        await db.refresh(row)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=503,
            detail=(
                "equipment_efficiency_period_override テーブルがありません。"
                "backend/database/migrations/117_equipment_efficiency_period_override.sql を適用してください。"
            ),
        ) from e
    return {"success": True, "data": _row_to_dict(row)}


@router.put("/{item_id:int}")
async def update_efficiency_period_override(
    item_id: int,
    body: EfficiencyPeriodOverrideBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    res = await db.execute(
        select(EquipmentEfficiencyPeriodOverride).where(EquipmentEfficiencyPeriodOverride.id == item_id)
    )
    row = res.scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="期間指定能率が見つかりません")

    machine_cd = body.machine_cd.strip()
    product_cd = body.product_cd.strip()
    if body.period_from > body.period_to:
        raise HTTPException(status_code=400, detail="開始日は終了日以前である必要があります")
    rate = _parse_rate(body.efficiency_rate)
    if rate <= 0:
        raise HTTPException(status_code=400, detail="能率（本/H）は 0 より大きい値にしてください")

    status_val = 1 if body.status is None else int(body.status)
    if status_val == 1:
        await _ensure_no_overlap(
            db,
            machine_cd=machine_cd,
            product_cd=product_cd,
            period_from=body.period_from,
            period_to=body.period_to,
            exclude_id=item_id,
        )

    row.machine_cd = machine_cd
    row.product_cd = product_cd
    row.efficiency_rate = rate
    row.period_from = body.period_from
    row.period_to = body.period_to
    row.status = status_val
    if body.machines_name is not None:
        row.machines_name = body.machines_name.strip() or None
    if body.product_name is not None:
        row.product_name = body.product_name.strip() or None
    if body.remarks is not None:
        row.remarks = body.remarks.strip() or None
    row.updated_at = datetime.now()

    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _row_to_dict(row)}


@router.delete("/{item_id:int}")
async def delete_efficiency_period_override(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    res = await db.execute(
        select(EquipmentEfficiencyPeriodOverride).where(EquipmentEfficiencyPeriodOverride.id == item_id)
    )
    row = res.scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="期間指定能率が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True}
