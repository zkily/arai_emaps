"""
製品機器設定 API（product_machine_config）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import ProductMachineConfig, Product

router = APIRouter()


def _row_to_dict(row: ProductMachineConfig) -> dict:
    return {
        "id": row.id,
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "cutting_machine": row.cutting_machine,
        "chamfering_machine": row.chamfering_machine,
        "molding_machine": row.molding_machine,
        "plating_machine": row.plating_machine,
        "welding_machine": row.welding_machine,
        "inspector_machine": row.inspector_machine,
        "outsourced_plating_machine": row.outsourced_plating_machine,
        "outsourced_welding_machine": row.outsourced_welding_machine,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_product_machine_config_list(
    keyword: Optional[str] = Query(None),
    limit: int = Query(99999, ge=1, le=99999),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品機器設定一覧"""
    query = select(ProductMachineConfig)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                ProductMachineConfig.product_cd.like(k),
                ProductMachineConfig.product_name.like(k),
            )
        )
    query = query.order_by(ProductMachineConfig.product_cd)
    result = await db.execute(query.limit(limit))
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_row_to_dict(r) for r in rows], "total": len(rows)},
        "list": [_row_to_dict(r) for r in rows],
        "total": len(rows),
    }


@router.get("/available-products")
async def get_available_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """登録用の製品一覧（product_cd, product_name）"""
    result = await db.execute(
        select(Product.product_cd, Product.product_name).where(Product.product_cd.isnot(None))
    )
    rows = result.all()
    data = [{"product_cd": r.product_cd, "product_name": r.product_name or ""} for r in rows]
    return {"success": True, "data": data}


@router.get("/{config_id:int}")
async def get_product_machine_config_by_id(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """IDで1件取得"""
    result = await db.execute(select(ProductMachineConfig).where(ProductMachineConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品機器設定が見つかりません")
    return _row_to_dict(row)


@router.post("")
async def create_product_machine_config(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規登録"""
    product_cd = body.get("product_cd")
    product_name = body.get("product_name") or ""
    if not product_cd:
        raise HTTPException(status_code=400, detail="製品コードは必須です")
    existing = await db.execute(
        select(ProductMachineConfig).where(ProductMachineConfig.product_cd == product_cd)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="この製品は既に登録されています")
    row = ProductMachineConfig(
        product_cd=product_cd,
        product_name=product_name,
        cutting_machine=body.get("cutting_machine"),
        chamfering_machine=body.get("chamfering_machine"),
        molding_machine=body.get("molding_machine"),
        plating_machine=body.get("plating_machine"),
        welding_machine=body.get("welding_machine"),
        inspector_machine=body.get("inspector_machine"),
        outsourced_plating_machine=body.get("outsourced_plating_machine"),
        outsourced_welding_machine=body.get("outsourced_welding_machine"),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.put("/{config_id:int}")
async def update_product_machine_config(
    config_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """更新"""
    result = await db.execute(select(ProductMachineConfig).where(ProductMachineConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品機器設定が見つかりません")
    allowed = {
        "product_name", "cutting_machine", "chamfering_machine", "molding_machine",
        "plating_machine", "welding_machine", "inspector_machine",
        "outsourced_plating_machine", "outsourced_welding_machine",
    }
    for key in allowed:
        if key in body:
            setattr(row, key, body[key])
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{config_id:int}")
async def delete_product_machine_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """削除"""
    result = await db.execute(select(ProductMachineConfig).where(ProductMachineConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品機器設定が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


@router.post("/sync")
async def sync_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品マスタから未登録製品を追加"""
    products_result = await db.execute(
        select(Product.product_cd, Product.product_name).where(Product.product_cd.isnot(None))
    )
    products = products_result.all()
    existing_result = await db.execute(select(ProductMachineConfig.product_cd))
    existing_cds = {r[0] for r in existing_result.all()}
    added = 0
    updated = 0
    for p in products:
        product_cd = p.product_cd
        product_name = p.product_name or ""
        if product_cd in existing_cds:
            # 製品名更新
            r = await db.execute(select(ProductMachineConfig).where(ProductMachineConfig.product_cd == product_cd))
            cfg = r.scalar_one_or_none()
            if cfg and cfg.product_name != product_name:
                cfg.product_name = product_name
                updated += 1
            continue
        db.add(
            ProductMachineConfig(
                product_cd=product_cd,
                product_name=product_name,
            )
        )
        added += 1
        existing_cds.add(product_cd)
    await db.commit()
    return {
        "success": True,
        "data": {"added": added, "updated": updated, "total": len(products)},
    }
