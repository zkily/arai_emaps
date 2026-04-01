"""
工程別標準原価増分 API（product_process_unit_prices）
策略A: line_type=component は禁止（BOM滚算で部品コストを得る）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from pydantic import BaseModel
from datetime import date
from decimal import Decimal

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import ProductProcessUnitPrice

router = APIRouter()

FORBIDDEN_LINE_TYPES = {"component"}


# ---------- Schemas ----------

class UnitPriceIn(BaseModel):
    product_cd: str
    route_cd: str
    step_no: int
    line_seq: int = 1
    line_type: str = "process"
    description: Optional[str] = None
    increment_unit_price: float = 0.0
    currency: str = "JPY"
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    status: str = "active"
    bom_line_id: Optional[int] = None
    remarks: Optional[str] = None


class UnitPriceBatchIn(BaseModel):
    items: List[UnitPriceIn]


# ---------- Helpers ----------

def _row_dict(r: ProductProcessUnitPrice) -> dict:
    return {
        "id": r.id,
        "product_cd": r.product_cd,
        "route_cd": r.route_cd,
        "step_no": r.step_no,
        "line_seq": r.line_seq,
        "line_type": r.line_type,
        "description": r.description,
        "increment_unit_price": float(r.increment_unit_price) if r.increment_unit_price else 0,
        "currency": r.currency,
        "effective_from": str(r.effective_from) if r.effective_from else None,
        "effective_to": str(r.effective_to) if r.effective_to else None,
        "status": r.status,
        "bom_line_id": r.bom_line_id,
        "remarks": r.remarks,
        "created_by": r.created_by,
        "updated_by": r.updated_by,
    }


def _validate_line_type(lt: str):
    if lt.lower() in FORBIDDEN_LINE_TYPES:
        raise HTTPException(
            400,
            f"策略A: line_type='{lt}' は禁止されています。部品コストはBOM滚算から取得します。"
        )


# ---------- CRUD ----------

@router.get("")
async def list_unit_prices(
    product_cd: Optional[str] = Query(None),
    route_cd: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """単価行一覧"""
    q = select(ProductProcessUnitPrice)
    if product_cd:
        q = q.where(ProductProcessUnitPrice.product_cd == product_cd)
    if route_cd:
        q = q.where(ProductProcessUnitPrice.route_cd == route_cd)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        q = q.where(ProductProcessUnitPrice.description.like(k))
    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.order_by(
        ProductProcessUnitPrice.product_cd,
        ProductProcessUnitPrice.route_cd,
        ProductProcessUnitPrice.step_no,
        ProductProcessUnitPrice.line_seq,
    )
    q = q.offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": {"list": [_row_dict(r) for r in rows], "total": total}}


@router.post("")
async def create_unit_price(
    body: UnitPriceIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _validate_line_type(body.line_type)
    row = ProductProcessUnitPrice(
        product_cd=body.product_cd,
        route_cd=body.route_cd,
        step_no=body.step_no,
        line_seq=body.line_seq,
        line_type=body.line_type,
        description=body.description,
        increment_unit_price=body.increment_unit_price,
        currency=body.currency,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        status=body.status,
        bom_line_id=body.bom_line_id,
        remarks=body.remarks,
        created_by=current_user.username if current_user else None,
        updated_by=current_user.username if current_user else None,
    )
    db.add(row)
    await db.flush()
    return {"success": True, "data": _row_dict(row)}


@router.post("/batch")
async def batch_save_unit_prices(
    body: UnitPriceBatchIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """一括保存（既存行は上書き、新規行は追加）"""
    results = []
    for item in body.items:
        _validate_line_type(item.line_type)
        existing_q = select(ProductProcessUnitPrice).where(
            ProductProcessUnitPrice.product_cd == item.product_cd,
            ProductProcessUnitPrice.route_cd == item.route_cd,
            ProductProcessUnitPrice.step_no == item.step_no,
            ProductProcessUnitPrice.line_seq == item.line_seq,
        )
        existing = (await db.execute(existing_q)).scalar_one_or_none()
        if existing:
            existing.line_type = item.line_type
            existing.description = item.description
            existing.increment_unit_price = item.increment_unit_price
            existing.currency = item.currency
            existing.effective_from = item.effective_from
            existing.effective_to = item.effective_to
            existing.status = item.status
            existing.bom_line_id = item.bom_line_id
            existing.remarks = item.remarks
            existing.updated_by = current_user.username if current_user else None
            results.append(_row_dict(existing))
        else:
            row = ProductProcessUnitPrice(
                product_cd=item.product_cd,
                route_cd=item.route_cd,
                step_no=item.step_no,
                line_seq=item.line_seq,
                line_type=item.line_type,
                description=item.description,
                increment_unit_price=item.increment_unit_price,
                currency=item.currency,
                effective_from=item.effective_from,
                effective_to=item.effective_to,
                status=item.status,
                bom_line_id=item.bom_line_id,
                remarks=item.remarks,
                created_by=current_user.username if current_user else None,
                updated_by=current_user.username if current_user else None,
            )
            db.add(row)
            await db.flush()
            results.append(_row_dict(row))
    return {"success": True, "data": results}


@router.put("/{price_id}")
async def update_unit_price(
    price_id: int,
    body: UnitPriceIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _validate_line_type(body.line_type)
    row = await db.get(ProductProcessUnitPrice, price_id)
    if not row:
        raise HTTPException(404, "単価行が見つかりません")
    row.product_cd = body.product_cd
    row.route_cd = body.route_cd
    row.step_no = body.step_no
    row.line_seq = body.line_seq
    row.line_type = body.line_type
    row.description = body.description
    row.increment_unit_price = body.increment_unit_price
    row.currency = body.currency
    row.effective_from = body.effective_from
    row.effective_to = body.effective_to
    row.status = body.status
    row.bom_line_id = body.bom_line_id
    row.remarks = body.remarks
    row.updated_by = current_user.username if current_user else None
    return {"success": True, "data": _row_dict(row)}


@router.delete("/{price_id}")
async def delete_unit_price(
    price_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(ProductProcessUnitPrice, price_id)
    if not row:
        raise HTTPException(404, "単価行が見つかりません")
    await db.delete(row)
    return {"success": True, "message": "削除しました"}


# ---------- 累計プレビュー ----------

@router.get("/cumulative")
async def get_cumulative_prices(
    product_cd: str = Query(...),
    route_cd: str = Query(...),
    target_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定製品・ルートの累計単価プレビュー"""
    q = select(ProductProcessUnitPrice).where(
        ProductProcessUnitPrice.product_cd == product_cd,
        ProductProcessUnitPrice.route_cd == route_cd,
        ProductProcessUnitPrice.status == "active",
    )
    if target_date:
        q = q.where(
            (ProductProcessUnitPrice.effective_from.is_(None)) | (ProductProcessUnitPrice.effective_from <= target_date),
            (ProductProcessUnitPrice.effective_to.is_(None)) | (ProductProcessUnitPrice.effective_to > target_date),
        )
    q = q.order_by(ProductProcessUnitPrice.step_no, ProductProcessUnitPrice.line_seq)
    rows = (await db.execute(q)).scalars().all()

    cumulative = Decimal("0")
    result = []
    for r in rows:
        inc = r.increment_unit_price or Decimal("0")
        cumulative += inc
        d = _row_dict(r)
        d["cumulative_unit_price"] = float(cumulative)
        result.append(d)

    return {"success": True, "data": result}
