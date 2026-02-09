"""
製品マスタ API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import io
import csv

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Product
from app.modules.master.schemas import ProductCreate, ProductUpdate

router = APIRouter()


def _row_to_dict(row: Product) -> dict:
    return {
        "id": row.id,
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "product_type": row.product_type,
        "location_cd": row.location_cd,
        "start_use_date": row.start_use_date.isoformat() if row.start_use_date else None,
        "category": row.category,
        "department_id": row.department_id,
        "destination_cd": row.destination_cd,
        "process_count": row.process_count,
        "lead_time": row.lead_time,
        "lot_size": row.lot_size,
        "is_multistage": bool(row.is_multistage),
        "priority": row.priority,
        "status": row.status,
        "part_number": row.part_number,
        "vehicle_model": row.vehicle_model,
        "box_type": row.box_type,
        "unit_per_box": row.unit_per_box,
        "dimensions": row.dimensions,
        "weight": float(row.weight) if row.weight is not None else None,
        "material_cd": row.material_cd,
        "cut_length": float(row.cut_length) if row.cut_length is not None else None,
        "chamfer_length": float(row.chamfer_length) if row.chamfer_length is not None else None,
        "developed_length": float(row.developed_length) if row.developed_length is not None else None,
        "take_count": row.take_count,
        "scrap_length": float(row.scrap_length) if row.scrap_length is not None else None,
        "bom_id": row.bom_id,
        "route_cd": row.route_cd,
        "note": row.note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "safety_days": row.safety_days,
        "unit_price": float(row.unit_price) if row.unit_price is not None else None,
        "product_alias": row.product_alias,
    }


@router.get("")
async def get_product_list(
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    product_cd: Optional[str] = Query(None),
    material_cd: Optional[str] = Query(None),
    route_cd: Optional[str] = Query(None),
    location_cd: Optional[str] = Query(None),
    destination_cd: Optional[str] = Query(None, description="納入先CD（該当納入先の製品のみ）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品一覧取得（検索・ページネーション）"""
    query = select(Product)
    if keyword:
        query = query.where(
            or_(
                Product.product_name.like(f"%{keyword}%"),
                Product.product_alias.like(f"%{keyword}%"),
                Product.part_number.like(f"%{keyword}%"),
                Product.product_cd.like(f"%{keyword}%"),
            )
        )
    if category:
        query = query.where(Product.category == category)
    if product_type:
        query = query.where(Product.product_type == product_type)
    if status:
        query = query.where(Product.status == status)
    if product_cd:
        query = query.where(Product.product_cd == product_cd)
    if material_cd:
        query = query.where(Product.material_cd == material_cd)
    if route_cd:
        query = query.where(Product.route_cd == route_cd)
    if location_cd:
        query = query.where(Product.location_cd == location_cd)
    if destination_cd:
        query = query.where(Product.destination_cd == destination_cd)

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "success": True,
        "data": {
            "list": [_row_to_dict(r) for r in rows],
            "total": total,
        },
    }


@router.get("/by-destination/{destination_cd}")
async def get_products_by_destination_for_batch(
    destination_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月注文一括登録用：指定納入先の製品のみ。条件は destination_cd=納入先、status=active、product_type=量産品"""
    query = (
        select(Product)
        .where(Product.destination_cd == destination_cd)
        .where(Product.status == "active")
        .where(Product.product_type == "量産品")
        .order_by(Product.product_cd)
    )
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_row_to_dict(r) for r in rows], "total": len(rows)},
        "list": [_row_to_dict(r) for r in rows],
    }


@router.get("/max-cd")
async def get_max_product_cd(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """最大製品CD取得（新規登録時の初期値用）"""
    q = select(Product.product_cd)
    res = await db.execute(q)
    codes = [r for r in res.scalars().all() if r and str(r).isdigit()]
    if not codes:
        return 90000
    return max(int(c) for c in codes)


@router.post("")
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品新規登録"""
    q = select(Product).where(Product.product_cd == body.product_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="製品CDは既に存在します")
    row = Product(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品更新"""
    q = select(Product).where(Product.id == product_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品が見つかりません")
    for k, v in body.model_dump().items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品削除"""
    q = select(Product).where(Product.id == product_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


class ExportCsvItem(BaseModel):
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    unit_per_box: Optional[int] = None


@router.post("/export-csv")
async def export_products_csv(
    body: list[ExportCsvItem],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """CSV出力（body: [{ product_cd, product_name, unit_per_box }]）"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["product_cd", "product_name", "unit_per_box"])
    for item in body:
        writer.writerow([
            item.product_cd or "",
            item.product_name or "",
            item.unit_per_box if item.unit_per_box is not None else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )
