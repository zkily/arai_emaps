"""
材料内示（フォーキャスト）API - 设计方案：order_monthly + products + materials + suppliers

GET /api/material/forecast/list      製品別明细（年/月/仕入先/材料/製品/内示数量/ロット/材料必要数）
GET /api/material/forecast/summary   按 supplier+material 分组汇总
GET /api/material/forecast/stats     统计：製品種類数、材料種類数、仕入先数、内示合計、材料必要数合計
GET /api/material/forecast/suppliers 筛选用仕入先列表（存在有效 product/material 的仕入先）

关联: order_monthly → products(product_cd) → materials(material_cd) → suppliers(supplier_cd)
过滤: 产品名不含「加工」「アーチ」、有供应商、products.status='active'、materials.status=1
材料必要数 = 内示数量 / ロットサイズ（lot_size 为 NULL 或 0 时为 NULL）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, case, and_, or_, null
from typing import Optional

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.erp.models import OrderMonthly
from app.modules.master.models import Product, Material, Supplier

router = APIRouter()

# 共通过滤条件：有效产品・材料・有供应商・排除「加工」「アーチ」
def _base_join_filters(om, p, m, s):
    return and_(
        om.product_cd == p.product_cd,
        p.material_cd == m.material_cd,
        m.supplier_cd == s.supplier_cd,
        p.status == "active",
        m.status == 1,
        ~p.product_name.contains("加工"),
        ~p.product_name.contains("アーチ"),
    )


@router.get("/list")
async def get_forecast_list(
    target_year: int = Query(..., description="年"),
    target_month: int = Query(..., description="月"),
    supplier_cd: Optional[str] = Query(None, description="仕入先CDで絞り込み"),
    keyword: Optional[str] = Query(None, description="製品名・材料名・仕入先名"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品別明细（每行：年/月/供应商/材料/产品/内示数量/ロット/材料必要数）"""
    om, p, m, s = OrderMonthly, Product, Material, Supplier
    base = _base_join_filters(om, p, m, s)
    q = (
        select(
            om.year,
            om.month,
            s.supplier_cd,
            s.supplier_name,
            m.material_cd,
            m.material_name,
            p.product_cd,
            p.product_name,
            om.forecast_units,
            p.lot_size,
        )
        .select_from(om)
        .join(p, om.product_cd == p.product_cd)
        .join(m, p.material_cd == m.material_cd)
        .join(s, m.supplier_cd == s.supplier_cd)
        .where(
            base,
            om.year == target_year,
            om.month == target_month,
        )
    )
    if supplier_cd:
        q = q.where(s.supplier_cd == supplier_cd)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                p.product_name.like(kw),
                m.material_name.like(kw),
                s.supplier_name.like(kw),
            )
        )
    q = q.order_by(s.supplier_cd, m.material_cd, p.product_cd)
    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(q)).all()

    def _material_required(forecast_units, lot_size):
        if lot_size is None or lot_size == 0:
            return None
        return round(forecast_units / lot_size, 1)

    data = [
        {
            "year": r.year,
            "month": r.month,
            "supplier_cd": r.supplier_cd,
            "supplier_name": r.supplier_name or "-",
            "material_cd": r.material_cd,
            "material_name": r.material_name or "-",
            "product_cd": r.product_cd,
            "product_name": r.product_name or "-",
            "forecast_units": r.forecast_units or 0,
            "lot_size": r.lot_size,
            "material_required": _material_required(r.forecast_units, r.lot_size),
        }
        for r in rows
    ]
    return {"success": True, "data": {"list": data, "total": total}}


@router.get("/summary")
async def get_forecast_summary(
    target_year: int = Query(..., description="年"),
    target_month: int = Query(..., description="月"),
    supplier_cd: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """按 supplier + material 分组汇总（内示合计、平均ロット、材料必要数合计、关联产品数）"""
    om, p, m, s = OrderMonthly, Product, Material, Supplier
    base = _base_join_filters(om, p, m, s)
    material_required_expr = case(
        (or_(p.lot_size.is_(None), p.lot_size == 0), null()),
        else_=func.round(om.forecast_units / p.lot_size, 1),
    )
    q = (
        select(
            s.supplier_cd,
            s.supplier_name,
            m.material_cd,
            m.material_name,
            func.count(distinct(p.product_cd)).label("product_count"),
            func.sum(om.forecast_units).label("total_forecast_units"),
            func.avg(p.lot_size).label("avg_lot_size"),
            func.sum(material_required_expr).label("total_material_required"),
        )
        .select_from(om)
        .join(p, om.product_cd == p.product_cd)
        .join(m, p.material_cd == m.material_cd)
        .join(s, m.supplier_cd == s.supplier_cd)
        .where(
            base,
            om.year == target_year,
            om.month == target_month,
        )
        .group_by(s.supplier_cd, s.supplier_name, m.material_cd, m.material_name)
        .order_by(s.supplier_cd, m.material_cd)
    )
    if supplier_cd:
        q = q.where(s.supplier_cd == supplier_cd)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                p.product_name.like(kw),
                m.material_name.like(kw),
                s.supplier_name.like(kw),
            )
        )
    rows = (await db.execute(q)).all()
    data = [
        {
            "supplier_cd": r.supplier_cd,
            "supplier_name": r.supplier_name or "-",
            "material_cd": r.material_cd,
            "material_name": r.material_name or "-",
            "product_count": r.product_count or 0,
            "total_forecast_units": int(r.total_forecast_units or 0),
            "avg_lot_size": float(r.avg_lot_size) if r.avg_lot_size is not None else None,
            "total_material_required": round(r.total_material_required, 1) if r.total_material_required is not None else None,
        }
        for r in rows
    ]
    return {"success": True, "data": data}


@router.get("/stats")
async def get_forecast_stats(
    target_year: Optional[int] = Query(None),
    target_month: Optional[int] = Query(None),
    supplier_cd: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """当前筛选条件下的统计：製品種類数、材料種類数、仕入先数、内示数量合计、材料必要数合计"""
    om, p, m, s = OrderMonthly, Product, Material, Supplier
    base = _base_join_filters(om, p, m, s)
    material_required_expr = case(
        (or_(p.lot_size.is_(None), p.lot_size == 0), null()),
        else_=func.round(om.forecast_units / p.lot_size, 1),
    )
    sub = (
        select(
            om.year,
            om.month,
            p.product_cd,
            m.material_cd,
            s.supplier_cd,
            om.forecast_units,
            material_required_expr.label("material_required"),
        )
        .select_from(om)
        .join(p, om.product_cd == p.product_cd)
        .join(m, p.material_cd == m.material_cd)
        .join(s, m.supplier_cd == s.supplier_cd)
        .where(base)
    )
    if target_year is not None:
        sub = sub.where(om.year == target_year)
    if target_month is not None:
        sub = sub.where(om.month == target_month)
    if supplier_cd:
        sub = sub.where(s.supplier_cd == supplier_cd)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        sub = sub.where(
            or_(
                p.product_name.like(kw),
                m.material_name.like(kw),
                s.supplier_name.like(kw),
            )
        )
    sub = sub.subquery()
    q = select(
        func.count(distinct(sub.c.product_cd)).label("total_products"),
        func.count(distinct(sub.c.material_cd)).label("total_materials"),
        func.count(distinct(sub.c.supplier_cd)).label("total_suppliers"),
        func.coalesce(func.sum(sub.c.forecast_units), 0).label("total_forecast_units"),
        func.coalesce(func.sum(sub.c.material_required), 0).label("total_material_required"),
    ).select_from(sub)
    row = (await db.execute(q)).one()
    return {
        "success": True,
        "data": {
            "total_products": row.total_products or 0,
            "total_materials": row.total_materials or 0,
            "total_suppliers": row.total_suppliers or 0,
            "total_forecast_units": int(row.total_forecast_units or 0),
            "total_material_required": round(float(row.total_material_required or 0), 1),
        },
    }


@router.get("/suppliers")
async def get_forecast_suppliers(
    target_year: Optional[int] = Query(None),
    target_month: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """筛选用供应商列表（仅存在有效 product/material 的供应商）"""
    om, p, m, s = OrderMonthly, Product, Material, Supplier
    base = _base_join_filters(om, p, m, s)
    q = (
        select(distinct(s.supplier_cd), s.supplier_name)
        .select_from(om)
        .join(p, om.product_cd == p.product_cd)
        .join(m, p.material_cd == m.material_cd)
        .join(s, m.supplier_cd == s.supplier_cd)
        .where(base)
        .order_by(s.supplier_cd)
    )
    if target_year is not None:
        q = q.where(om.year == target_year)
    if target_month is not None:
        q = q.where(om.month == target_month)
    rows = (await db.execute(q)).all()
    data = [{"supplier_cd": r[0], "supplier_name": r[1] or r[0] or ""} for r in rows if r[0]]
    return {"success": True, "data": data}
