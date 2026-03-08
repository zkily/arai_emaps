"""
材料内示（フォーキャスト）API
material_stock を月別集計して返す。
前端の MaterialForecastPage.vue が使用するエンドポイント群。

GET /api/material/forecast/summary          統計サマリー
GET /api/material/forecast/monthly          月別在庫一覧
GET /api/material/forecast/by-supplier      仕入先別集計
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, extract
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.material.models import MaterialStock

router = APIRouter()


@router.get("/summary")
async def get_forecast_summary(
    target_year: Optional[int] = Query(None),
    target_month: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月別サマリー統計（製品種類数・材料種類数・仕入先数・合計数量・合計金額）"""
    q = select(MaterialStock)
    if target_year:
        q = q.where(extract("year", MaterialStock.date) == target_year)
    if target_month:
        q = q.where(extract("month", MaterialStock.date) == target_month)

    material_count = (
        await db.execute(
            select(func.count(distinct(MaterialStock.material_cd))).select_from(q.subquery())
        )
    ).scalar() or 0

    supplier_count = (
        await db.execute(
            select(func.count(distinct(MaterialStock.supplier_cd))).where(
                MaterialStock.supplier_cd.isnot(None)
            )
        )
    ).scalar() or 0

    total_planned = (
        await db.execute(
            select(func.sum(MaterialStock.planned_usage)).select_from(q.subquery())
        )
    ).scalar() or 0

    total_order_amount = (
        await db.execute(
            select(func.sum(MaterialStock.order_amount)).select_from(q.subquery())
        )
    ).scalar() or 0

    return {
        "success": True,
        "data": {
            "material_count": material_count,
            "supplier_count": supplier_count,
            "total_planned_usage": int(total_planned),
            "total_order_amount": float(total_order_amount),
        },
    }


@router.get("/monthly")
async def get_monthly_forecast(
    target_year: int = Query(...),
    target_month: int = Query(...),
    page: int = Query(1, ge=1),
    pageSize: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月別材料在庫一覧"""
    q = (
        select(MaterialStock)
        .where(
            extract("year", MaterialStock.date) == target_year,
            extract("month", MaterialStock.date) == target_month,
        )
        .order_by(MaterialStock.material_cd)
        .offset((page - 1) * pageSize)
        .limit(pageSize)
    )
    rows = (await db.execute(q)).scalars().all()

    total_q = select(func.count()).where(
        extract("year", MaterialStock.date) == target_year,
        extract("month", MaterialStock.date) == target_month,
    )
    total = (await db.execute(total_q)).scalar() or 0

    data = []
    for r in rows:
        data.append({
            "id": r.id,
            "material_cd": r.material_cd,
            "material_name": r.material_name,
            "date": r.date.isoformat() if r.date else None,
            "current_stock": r.current_stock,
            "safety_stock": r.safety_stock,
            "planned_usage": r.planned_usage,
            "order_quantity": r.order_quantity,
            "order_bundle_quantity": r.order_bundle_quantity,
            "order_amount": float(r.order_amount) if r.order_amount is not None else None,
            "supplier_cd": r.supplier_cd,
            "supplier_name": r.supplier_name,
            "unit": r.unit,
            "unit_price": float(r.unit_price) if r.unit_price is not None else None,
            "pieces_per_bundle": r.pieces_per_bundle,
            "bundle_weight": float(r.bundle_weight) if r.bundle_weight is not None else None,
            "lead_time": r.lead_time,
            "standard_spec": r.standard_spec,
        })
    return {"success": True, "data": {"list": data, "total": total}}


@router.get("/by-supplier")
async def get_by_supplier(
    target_year: int = Query(...),
    target_month: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先別集計"""
    q = (
        select(
            MaterialStock.supplier_cd,
            MaterialStock.supplier_name,
            func.count(distinct(MaterialStock.material_cd)).label("material_count"),
            func.sum(MaterialStock.planned_usage).label("total_planned"),
            func.sum(MaterialStock.order_quantity).label("total_order_qty"),
            func.sum(MaterialStock.order_amount).label("total_amount"),
        )
        .where(
            extract("year", MaterialStock.date) == target_year,
            extract("month", MaterialStock.date) == target_month,
            MaterialStock.supplier_cd.isnot(None),
        )
        .group_by(MaterialStock.supplier_cd, MaterialStock.supplier_name)
        .order_by(MaterialStock.supplier_cd)
    )
    rows = (await db.execute(q)).all()
    data = [
        {
            "supplier_cd": r[0],
            "supplier_name": r[1],
            "material_count": r[2],
            "total_planned_usage": int(r[3] or 0),
            "total_order_quantity": int(r[4] or 0),
            "total_order_amount": float(r[5] or 0),
        }
        for r in rows
    ]
    return {"success": True, "data": data}
