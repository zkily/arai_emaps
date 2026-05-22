"""
製品工程BOM API（product_process_bom）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import ProductProcessBOM, Product

router = APIRouter()


def _row_to_dict(row: ProductProcessBOM) -> dict:
    return {
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "min_stock_days": row.min_stock_days,
        "safety_stock_days": row.safety_stock_days,
        "material_process": row.material_process,
        "material_process_lt": row.material_process_lt,
        "cuting_process": row.cuting_process,
        "cuting_process_lt": row.cuting_process_lt,
        "chamfering_process": row.chamfering_process,
        "chamfering_process_lt": row.chamfering_process_lt,
        "swaging_process": row.swaging_process,
        "swaging_process_lt": row.swaging_process_lt,
        "forming_process": row.forming_process,
        "forming_process_lt": row.forming_process_lt,
        "plating_process": row.plating_process,
        "plating_process_lt": row.plating_process_lt,
        "outsourced_plating_process": row.outsourced_plating_process,
        "outsourced_plating_process_lt": row.outsourced_plating_process_lt,
        "welding_process": row.welding_process,
        "welding_process_lt": row.welding_process_lt,
        "outsourced_welding_process": row.outsourced_welding_process,
        "outsourced_welding_process_lt": row.outsourced_welding_process_lt,
        "inspection_process": row.inspection_process,
        "inspection_process_lt": row.inspection_process_lt,
        "outsourced_warehouse_process": row.outsourced_warehouse_process,
        "outsourced_warehouse_process_lt": row.outsourced_warehouse_process_lt,
        "pre_plating_welding": row.pre_plating_welding,
        "post_inspection_welding": row.post_inspection_welding,
        "post_inspection_welding_lt": row.post_inspection_welding_lt,
        "is_discontinued": row.is_discontinued,
    }


@router.get("")
async def get_product_process_bom_list(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("product_name"),
    sort_order: Optional[str] = Query("asc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品工程BOM一覧（ページネーション・検索・ソート）"""
    query = select(ProductProcessBOM)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        conds = [ProductProcessBOM.product_name.like(k)]
        try:
            conds.append(ProductProcessBOM.product_cd == int(keyword.strip()))
        except ValueError:
            pass
        query = query.where(or_(*conds))
    # ソート
    if sort_by == "product_cd":
        order_col = ProductProcessBOM.product_cd.asc() if sort_order == "asc" else ProductProcessBOM.product_cd.desc()
    else:
        order_col = ProductProcessBOM.product_name.asc() if sort_order == "asc" else ProductProcessBOM.product_name.desc()
    query = query.order_by(order_col)

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    # 統計: is_discontinued=0 が现行、=1 が終息（全件ベース）
    q_active = select(func.count(ProductProcessBOM.product_cd)).where(ProductProcessBOM.is_discontinued == 0)
    q_disc = select(func.count(ProductProcessBOM.product_cd)).where(ProductProcessBOM.is_discontinued == 1)
    active_res = await db.execute(q_active)
    disc_res = await db.execute(q_disc)
    active_count = active_res.scalar() or 0
    discontinued_count = disc_res.scalar() or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "success": True,
        "data": {
            "list": [_row_to_dict(r) for r in rows],
            "total": total,
            "active_count": active_count,
            "discontinued_count": discontinued_count,
        },
    }


@router.get("/stats")
async def get_product_process_bom_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """件数・现行・終息の集計のみ"""
    total_q = select(func.count(ProductProcessBOM.product_cd))
    active_q = select(func.count(ProductProcessBOM.product_cd)).where(ProductProcessBOM.is_discontinued == 0)
    disc_q = select(func.count(ProductProcessBOM.product_cd)).where(ProductProcessBOM.is_discontinued == 1)
    total = (await db.execute(total_q)).scalar() or 0
    active_count = (await db.execute(active_q)).scalar() or 0
    discontinued_count = (await db.execute(disc_q)).scalar() or 0
    return {
        "success": True,
        "data": {
            "total": total,
            "active_count": active_count,
            "discontinued_count": discontinued_count,
        },
    }


@router.get("/{product_cd:int}")
async def get_product_process_bom_by_id(
    product_cd: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品CDで1件取得"""
    result = await db.execute(select(ProductProcessBOM).where(ProductProcessBOM.product_cd == product_cd))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品工程BOMが見つかりません")
    return _row_to_dict(row)


@router.put("/{product_cd:int}")
async def update_product_process_bom(
    product_cd: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品工程BOMを更新（部分更新可）"""
    result = await db.execute(select(ProductProcessBOM).where(ProductProcessBOM.product_cd == product_cd))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品工程BOMが見つかりません")

    allowed = {
        "product_name", "min_stock_days", "safety_stock_days",
        "material_process", "material_process_lt", "cuting_process", "cuting_process_lt",
        "chamfering_process", "chamfering_process_lt", "swaging_process", "swaging_process_lt",
        "forming_process", "forming_process_lt", "plating_process", "plating_process_lt",
        "outsourced_plating_process", "outsourced_plating_process_lt",
        "welding_process", "welding_process_lt", "outsourced_welding_process", "outsourced_welding_process_lt",
        "inspection_process", "inspection_process_lt",
        "outsourced_warehouse_process", "outsourced_warehouse_process_lt",
        "pre_plating_welding", "post_inspection_welding", "post_inspection_welding_lt",
        "is_discontinued",
    }
    for key, value in body.items():
        if key in allowed and hasattr(row, key):
            if isinstance(value, bool):
                value = 1 if value else 0
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{product_cd:int}")
async def delete_product_process_bom(
    product_cd: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品工程BOMを削除"""
    result = await db.execute(select(ProductProcessBOM).where(ProductProcessBOM.product_cd == product_cd))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品工程BOMが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


@router.post("/sync")
async def sync_product_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品マスタから product_process_bom を同期（未登録は新規、既存は製品名のみ更新）"""
    products_result = await db.execute(
        select(Product.product_cd, Product.product_name).where(Product.product_cd.isnot(None))
    )
    products = products_result.all()
    inserted = 0
    updated = 0
    for p in products:
        try:
            product_cd_int = int(p.product_cd) if isinstance(p.product_cd, str) else p.product_cd
        except (ValueError, TypeError):
            continue
        name = p.product_name or ""
        existing = await db.execute(
            select(ProductProcessBOM).where(ProductProcessBOM.product_cd == product_cd_int)
        )
        one = existing.scalar_one_or_none()
        if not one:
            db.add(
                ProductProcessBOM(
                    product_cd=product_cd_int,
                    product_name=name,
                    min_stock_days=None,
                    safety_stock_days=None,
                    material_process=None,
                    material_process_lt=None,
                    cuting_process=None,
                    cuting_process_lt=None,
                    chamfering_process=None,
                    chamfering_process_lt=None,
                    swaging_process=None,
                    swaging_process_lt=None,
                    forming_process=None,
                    forming_process_lt=None,
                    plating_process=None,
                    plating_process_lt=None,
                    outsourced_plating_process=None,
                    outsourced_plating_process_lt=None,
                    welding_process=None,
                    welding_process_lt=None,
                    outsourced_welding_process=None,
                    outsourced_welding_process_lt=None,
                    inspection_process=None,
                    inspection_process_lt=None,
                    outsourced_warehouse_process=None,
                    outsourced_warehouse_process_lt=None,
                    pre_plating_welding=None,
                    post_inspection_welding=None,
                    post_inspection_welding_lt=None,
                    is_discontinued=0,
                )
            )
            inserted += 1
        else:
            if one.product_name != name:
                one.product_name = name
                updated += 1
    await db.commit()
    return {
        "success": True,
        "data": {
            "inserted_count": inserted,
            "updated_count": updated,
            "total_processed": len(products),
            "message": f"新規: {inserted}件、更新: {updated}件",
        },
    }
