"""製品用ラベル設定 API"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_master_operation
from app.modules.master.models import Product, ProductUseLabelConfig
from app.modules.master.product_use_label_service import (
    apply_master_sync_fields,
    apply_product_master_to_config,
    apply_row_fields,
    build_prefill_from_product,
    config_to_dict,
)

router = APIRouter()


def _product_cd_join():
    return Product.product_cd == ProductUseLabelConfig.product_cd


async def _get_master_name(db: AsyncSession, product_cd: str) -> str:
    res = await db.execute(select(Product.product_name).where(Product.product_cd == product_cd))
    row = res.scalar_one_or_none()
    return row or ""


def _parse_body(body: dict, *, include_master_fields: bool = False) -> dict:
    data: dict = {}
    if "product_cd" in body:
        val = body.get("product_cd")
        data["product_cd"] = (val.strip() if val else None) or None
    editable_fields = [
        "use_label_product_name",
        "paper_color",
        "product_name_color",
        "back_no_1",
        "back_no_2",
        "back_no_3",
        "barcode_no",
    ]
    if include_master_fields:
        editable_fields = ["part_no", "destination_name", "unit_qty", *editable_fields]
    for field in editable_fields:
        if field in body:
            val = body.get(field)
            data[field] = (val.strip() if val else None) or None
    if include_master_fields and "unit_qty" in body:
        qty = body.get("unit_qty")
        data["unit_qty"] = int(qty) if qty is not None and qty != "" else None
    return data


@router.get("")
async def list_product_use_label_config(
    keyword: Optional[str] = Query(None),
    product_cd: Optional[str] = Query(None),
    destination_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: Optional[str] = Query("master_product_name"),
    sort_order: Optional[str] = Query("asc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    query = select(ProductUseLabelConfig, Product.product_name, Product.status).outerjoin(
        Product, _product_cd_join()
    )
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                ProductUseLabelConfig.product_cd.like(k),
                ProductUseLabelConfig.use_label_product_name.like(k),
                Product.product_name.like(k),
                ProductUseLabelConfig.part_no.like(k),
                ProductUseLabelConfig.destination_name.like(k),
            )
        )
    if product_cd and product_cd.strip():
        query = query.where(ProductUseLabelConfig.product_cd == product_cd.strip())
    if destination_name and destination_name.strip():
        query = query.where(ProductUseLabelConfig.destination_name == destination_name.strip())

    order = (sort_order or "asc").strip().lower()
    descending = order == "desc"
    sort_field = (sort_by or "master_product_name").strip()
    if sort_field == "master_product_name":
        primary = Product.product_name.desc() if descending else Product.product_name.asc()
    else:
        primary = (
            ProductUseLabelConfig.product_cd.desc()
            if descending
            else ProductUseLabelConfig.product_cd.asc()
        )
    query = query.order_by(primary, ProductUseLabelConfig.product_cd.asc())
    result = await db.execute(query)
    rows = result.all()
    total = len(rows)
    start = (page - 1) * page_size
    page_rows = rows[start : start + page_size]
    items = [
        config_to_dict(config, master_product_name=master_name or "", product_status=product_status)
        for config, master_name, product_status in page_rows
    ]
    return {"list": items, "total": total, "page": page, "page_size": page_size}


@router.get("/by-product/{product_cd}")
async def get_product_use_label_config_by_product_cd(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(
        select(ProductUseLabelConfig).where(ProductUseLabelConfig.product_cd == product_cd)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品用ラベル設定が見つかりません")
    master_name = await _get_master_name(db, product_cd)
    product_res = await db.execute(select(Product.status).where(Product.product_cd == product_cd))
    status = product_res.scalar_one_or_none()
    return config_to_dict(row, master_product_name=master_name, product_status=status)


@router.get("/available-products")
async def get_available_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    configured = await db.execute(select(ProductUseLabelConfig.product_cd))
    configured_cds = {r[0] for r in configured.all()}
    result = await db.execute(
        select(Product.product_cd, Product.product_name)
        .where(Product.product_cd.isnot(None))
        .order_by(Product.product_cd)
    )
    rows = result.all()
    data = [
        {
            "product_cd": r.product_cd,
            "product_name": r.product_name or "",
            "configured": r.product_cd in configured_cds,
        }
        for r in rows
    ]
    return {"success": True, "data": data}


@router.get("/filter-options")
async def get_filter_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """一覧絞込用：登録済み製品・納入先の選択肢"""
    product_result = await db.execute(
        select(ProductUseLabelConfig.product_cd, Product.product_name)
        .outerjoin(Product, _product_cd_join())
        .order_by(Product.product_name.asc(), ProductUseLabelConfig.product_cd.asc())
    )
    products = [
        {"product_cd": cd, "product_name": name or ""}
        for cd, name in product_result.all()
        if cd
    ]

    dest_result = await db.execute(
        select(ProductUseLabelConfig.destination_name)
        .where(
            ProductUseLabelConfig.destination_name.isnot(None),
            ProductUseLabelConfig.destination_name != "",
        )
        .distinct()
        .order_by(ProductUseLabelConfig.destination_name.asc())
    )
    destinations = [name for (name,) in dest_result.all() if name]

    return {"success": True, "data": {"products": products, "destinations": destinations}}


@router.get("/prefill/{product_cd}")
async def get_prefill_from_product_master(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    product_cd = (product_cd or "").strip()
    if not product_cd:
        raise HTTPException(status_code=400, detail="製品コードは必須です")
    try:
        data = await build_prefill_from_product(db, product_cd)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True, "data": data}


@router.post("/sync-from-master")
async def sync_from_product_master(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    """製品マスタから一括取込。未登録は新規追加、登録済みは品番・納入先名を更新。"""
    products_res = await db.execute(
        select(Product).where(Product.product_cd.isnot(None)).order_by(Product.product_cd)
    )
    products = products_res.scalars().all()
    existing_res = await db.execute(select(ProductUseLabelConfig))
    existing_rows = {r.product_cd: r for r in existing_res.scalars().all()}

    added = 0
    updated = 0
    destination_cache: dict[str, str | None] = {}
    for product in products:
        cd = (product.product_cd or "").strip()
        if not cd:
            continue
        row = existing_rows.get(cd)
        if row:
            await apply_master_sync_fields(db, row, product, destination_cache)
            updated += 1
            continue
        row = ProductUseLabelConfig(product_cd=cd)
        await apply_product_master_to_config(db, row, product, destination_cache)
        db.add(row)
        existing_rows[cd] = row
        added += 1

    await db.commit()
    return {
        "success": True,
        "data": {"added": added, "updated": updated, "total_products": len(products)},
    }


@router.post("/by-product/{product_cd}/import-from-master")
async def import_from_product_master(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    product_cd = (product_cd or "").strip()
    product_res = await db.execute(select(Product).where(Product.product_cd == product_cd))
    product = product_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="製品が見つかりません")

    result = await db.execute(
        select(ProductUseLabelConfig).where(ProductUseLabelConfig.product_cd == product_cd)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品用ラベル設定が見つかりません")

    await apply_product_master_to_config(db, row, product)
    await db.commit()
    await db.refresh(row)
    master_name = await _get_master_name(db, product_cd)
    return config_to_dict(row, master_product_name=master_name, product_status=product.status)


@router.get("/{config_id:int}")
async def get_product_use_label_config_by_id(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(
        select(ProductUseLabelConfig).where(ProductUseLabelConfig.id == config_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品用ラベル設定が見つかりません")
    master_name = await _get_master_name(db, row.product_cd)
    product_res = await db.execute(select(Product.status).where(Product.product_cd == row.product_cd))
    status = product_res.scalar_one_or_none()
    return config_to_dict(row, master_product_name=master_name, product_status=status)


@router.post("")
async def create_product_use_label_config(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("create")),
):
    data = _parse_body(body)
    product_cd = data.get("product_cd")
    if not product_cd:
        raise HTTPException(status_code=400, detail="製品コードは必須です")

    product_res = await db.execute(select(Product).where(Product.product_cd == product_cd))
    product = product_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="製品が見つかりません")

    existing = await db.execute(
        select(ProductUseLabelConfig).where(ProductUseLabelConfig.product_cd == product_cd)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="この製品は既に登録されています")

    row = ProductUseLabelConfig(product_cd=product_cd)
    apply_row_fields(row, data)
    await apply_product_master_to_config(db, row, product)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return config_to_dict(row, master_product_name=product.product_name or "", product_status=product.status)


@router.put("/{config_id:int}")
async def update_product_use_label_config(
    config_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    result = await db.execute(
        select(ProductUseLabelConfig).where(ProductUseLabelConfig.id == config_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品用ラベル設定が見つかりません")

    data = _parse_body(body)
    apply_row_fields(row, data)
    await db.commit()
    await db.refresh(row)
    master_name = await _get_master_name(db, row.product_cd)
    product_res = await db.execute(select(Product.status).where(Product.product_cd == row.product_cd))
    status = product_res.scalar_one_or_none()
    return config_to_dict(row, master_product_name=master_name, product_status=status)


@router.delete("/{config_id:int}")
async def delete_product_use_label_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("delete")),
):
    result = await db.execute(
        select(ProductUseLabelConfig).where(ProductUseLabelConfig.id == config_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品用ラベル設定が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True}
