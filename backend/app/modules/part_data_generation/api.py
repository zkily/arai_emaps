"""部品在庫データ一括生成（parts.status=0 を除く × 期間 → part_stock。一覧 API と同条件）"""
from datetime import date as date_type, timedelta
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import PartMaster, Supplier
from app.modules.part.models import PartStock

router = APIRouter()


class PartDataGenerationRequest(BaseModel):
    start_date: str
    end_date: str
    overwrite_existing: bool = False


def _parse_date_str(value: str) -> date_type:
    if not value:
        raise ValueError("empty date")
    s = value.strip()
    if len(s) >= 10:
        s = s[:10]
    return date_type.fromisoformat(s)


@router.post("/generate")
async def generate_part_stock_data(
    body: PartDataGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        start = _parse_date_str(body.start_date)
        end = _parse_date_str(body.end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if start > end:
        raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")

    part_stmt = (
        select(
            PartMaster.part_cd,
            PartMaster.part_name,
            PartMaster.category,
            PartMaster.uom,
            PartMaster.unit_price,
            PartMaster.supplier_cd,
            Supplier.supplier_name,
        )
        .select_from(PartMaster)
        .outerjoin(Supplier, PartMaster.supplier_cd == Supplier.supplier_cd)
        .where(PartMaster.status != 0)
        .order_by(PartMaster.part_cd)
    )
    part_rows = (await db.execute(part_stmt)).all()
    if not part_rows:
        return {
            "success": True,
            "data": {
                "generated_count": 0,
                "updated_count": 0,
                "skipped_count": 0,
                "duplicate_count": 0,
            },
        }

    part_cds = [row[0] for row in part_rows]
    existing_stmt = select(PartStock).where(
        PartStock.part_cd.in_(part_cds),
        PartStock.date >= start,
        PartStock.date <= end,
    )
    existing_rows = (await db.execute(existing_stmt)).scalars().all()
    existing_map: dict[Tuple[str, date_type], PartStock] = {(r.part_cd, r.date): r for r in existing_rows}

    dates: List[date_type] = []
    cur = start
    while cur <= end:
        dates.append(cur)
        cur += timedelta(days=1)

    generated_count = 0
    updated_count = 0
    skipped_count = 0
    duplicate_count = 0

    for d in dates:
        for (
            part_cd,
            part_name,
            category,
            uom,
            unit_price,
            supplier_cd,
            supplier_name,
        ) in part_rows:
            key = (part_cd, d)
            existing = existing_map.get(key)
            if existing:
                if body.overwrite_existing:
                    existing.part_name = part_name or ""
                    existing.standard_spec = ((category or "") or "").strip() or ""
                    existing.unit = (uom or "").strip() or None
                    try:
                        existing.unit_price = float(unit_price or 0)
                    except (TypeError, ValueError):
                        existing.unit_price = 0.0
                    existing.supplier_cd = supplier_cd
                    sn = (supplier_name or "").strip()
                    existing.supplier_name = sn[:50] if len(sn) > 50 else sn
                    existing.order_amount = 0
                    updated_count += 1
                else:
                    skipped_count += 1
                    duplicate_count += 1
                continue
            sn = (supplier_name or "").strip()
            row = PartStock(
                part_cd=part_cd,
                part_name=part_name or "",
                date=d,
                current_stock=0,
                unit=(uom or "").strip() or None,
                unit_price=float(unit_price or 0),
                supplier_cd=supplier_cd,
                supplier_name=sn[:50] if len(sn) > 50 else sn,
                lead_time=0,
                pieces_per_bundle=1,
                remarks="",
                order_amount=0,
                standard_spec=((category or "") or "").strip() or "",
            )
            db.add(row)
            generated_count += 1

    await db.commit()
    return {
        "success": True,
        "data": {
            "generated_count": generated_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "duplicate_count": duplicate_count,
        },
    }
