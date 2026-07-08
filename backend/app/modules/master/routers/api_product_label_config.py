"""
成型用ラベル設定 API（product_label_config）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_master_operation
from app.modules.master.models import Product, ProductLabelConfig
from app.modules.master.product_label_service import (
    PROCESS_SLOT_FIELDS,
    apply_derived_slots_to_config,
    apply_product_master_to_config,
    build_prefill_from_product,
    config_to_dict,
    derive_label_process_slots,
    is_molding_label_target_product_cd,
    set_config_process_slots,
)

router = APIRouter()

# products は utf8mb4_0900_ai_ci、新規テーブルは utf8mb4_unicode_ci になりがち — JOIN 1267 回避
_PRODUCT_CD_COLLATION = "utf8mb4_unicode_ci"


def _product_cd_join():
    return ProductLabelConfig.product_cd.collate(_PRODUCT_CD_COLLATION) == Product.product_cd.collate(
        _PRODUCT_CD_COLLATION
    )


async def _get_master_name(db: AsyncSession, product_cd: str) -> str:
    res = await db.execute(select(Product.product_name).where(Product.product_cd == product_cd))
    row = res.scalar_one_or_none()
    return row or ""


def _parse_body(body: dict) -> dict:
    data: dict = {}
    if "product_cd" in body:
        data["product_cd"] = (body.get("product_cd") or "").strip()
    if "label_product_name" in body:
        val = body.get("label_product_name")
        data["label_product_name"] = (val.strip() if val else None) or None
    if "process_unit_qty" in body:
        qty = body.get("process_unit_qty")
        data["process_unit_qty"] = int(qty) if qty is not None and qty != "" else None
    if "paper_color" in body:
        val = body.get("paper_color")
        data["paper_color"] = (val.strip() if val else None) or None
    if "product_name_color" in body:
        val = body.get("product_name_color")
        data["product_name_color"] = (val.strip() if val else None) or None
    if "upper_slots_locked" in body:
        data["upper_slots_locked"] = bool(body.get("upper_slots_locked"))

    slots = body.get("process_slots")
    if isinstance(slots, list):
        data["process_slots"] = slots
    else:
        slot_values = []
        for field in PROCESS_SLOT_FIELDS:
            if field in body:
                slot_values.append(body.get(field))
        if slot_values:
            data["process_slots"] = slot_values
    return data


@router.get("")
async def list_product_label_config(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    query = select(ProductLabelConfig, Product.product_name).outerjoin(
        Product, _product_cd_join()
    )
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                ProductLabelConfig.product_cd.like(k),
                ProductLabelConfig.label_product_name.like(k),
                Product.product_name.like(k),
            )
        )
    query = query.order_by(ProductLabelConfig.product_cd)
    result = await db.execute(query)
    rows = result.all()
    total = len(rows)
    start = (page - 1) * page_size
    page_rows = rows[start : start + page_size]
    items = [
        config_to_dict(config, master_product_name=master_name or "")
        for config, master_name in page_rows
    ]
    return {"list": items, "total": total, "page": page, "page_size": page_size}


@router.get("/by-product/{product_cd}")
async def get_product_label_config_by_product_cd(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(
        select(ProductLabelConfig).where(ProductLabelConfig.product_cd == product_cd)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="成型用ラベル設定が見つかりません")
    master_name = await _get_master_name(db, product_cd)
    return config_to_dict(row, master_product_name=master_name)


@router.get("/available-products")
async def get_available_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    configured = await db.execute(select(ProductLabelConfig.product_cd))
    configured_cds = {r[0] for r in configured.all()}
    result = await db.execute(
        select(Product.product_cd, Product.product_name)
        .where(Product.product_cd.isnot(None))
        .where(Product.product_cd.endswith("1"))
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


@router.get("/prefill/{product_cd}")
async def get_prefill_from_product_master(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品マスタから編集フォーム用の初期値を取得。"""
    product_cd = (product_cd or "").strip()
    if not product_cd:
        raise HTTPException(status_code=400, detail="製品コードは必須です")
    if not is_molding_label_target_product_cd(product_cd):
        raise HTTPException(status_code=400, detail="製品CDの末尾が1の製品のみ取込対象です")
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
    """製品マスタの未登録製品（製品CD末尾1）を成型用ラベル設定へ一括取込。"""
    products_res = await db.execute(
        select(Product)
        .where(Product.product_cd.isnot(None))
        .where(Product.product_cd.endswith("1"))
        .order_by(Product.product_cd)
    )
    products = products_res.scalars().all()
    existing_res = await db.execute(select(ProductLabelConfig.product_cd))
    existing_cds = {r[0] for r in existing_res.all()}

    added = 0
    for product in products:
        cd = (product.product_cd or "").strip()
        if not cd or cd in existing_cds:
            continue
        slots = await derive_label_process_slots(db, cd)
        row = ProductLabelConfig(product_cd=cd)
        await apply_product_master_to_config(row, product)
        set_config_process_slots(row, slots)
        db.add(row)
        added += 1
        existing_cds.add(cd)

    await db.commit()
    return {
        "success": True,
        "data": {"added": added, "total_products": len(products)},
    }


@router.post("/by-product/{product_cd}/import-from-master")
async def import_from_product_master(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    """既存設定を製品マスタ＋工程ルートで上書き取込。"""
    product_cd = (product_cd or "").strip()
    if not is_molding_label_target_product_cd(product_cd):
        raise HTTPException(status_code=400, detail="製品CDの末尾が1の製品のみ取込対象です")
    product_res = await db.execute(select(Product).where(Product.product_cd == product_cd))
    product = product_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="製品が見つかりません")

    result = await db.execute(
        select(ProductLabelConfig).where(ProductLabelConfig.product_cd == product_cd)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="成型用ラベル設定が見つかりません")

    await apply_product_master_to_config(row, product)
    await apply_derived_slots_to_config(db, row, product_cd)
    await db.commit()
    await db.refresh(row)
    master_name = await _get_master_name(db, product_cd)
    return config_to_dict(row, master_product_name=master_name)


@router.get("/{config_id:int}")
async def get_product_label_config_by_id(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(select(ProductLabelConfig).where(ProductLabelConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="成型用ラベル設定が見つかりません")
    master_name = await _get_master_name(db, row.product_cd)
    return config_to_dict(row, master_product_name=master_name)


@router.post("")
async def create_product_label_config(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("create")),
):
    data = _parse_body(body)
    product_cd = data.get("product_cd")
    if not product_cd:
        raise HTTPException(status_code=400, detail="製品コードは必須です")
    if not is_molding_label_target_product_cd(product_cd):
        raise HTTPException(status_code=400, detail="製品CDの末尾が1の製品のみ登録できます")

    product_res = await db.execute(select(Product).where(Product.product_cd == product_cd))
    if not product_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="製品が見つかりません")

    existing = await db.execute(
        select(ProductLabelConfig).where(ProductLabelConfig.product_cd == product_cd)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="この製品は既に登録されています")

    row = ProductLabelConfig(product_cd=product_cd)
    if "label_product_name" in data:
        row.label_product_name = data["label_product_name"]
    if "process_unit_qty" in data:
        row.process_unit_qty = data["process_unit_qty"]
    if "paper_color" in data:
        row.paper_color = data["paper_color"]
    if "product_name_color" in data:
        row.product_name_color = data["product_name_color"]
    if "upper_slots_locked" in data:
        row.upper_slots_locked = bool(data["upper_slots_locked"])
    if "process_slots" in data:
        set_config_process_slots(row, data["process_slots"])

    db.add(row)
    await db.commit()
    await db.refresh(row)
    master_name = await _get_master_name(db, product_cd)
    return config_to_dict(row, master_product_name=master_name)


@router.put("/{config_id:int}")
async def update_product_label_config(
    config_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    result = await db.execute(select(ProductLabelConfig).where(ProductLabelConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="成型用ラベル設定が見つかりません")

    data = _parse_body(body)
    if "label_product_name" in data:
        row.label_product_name = data["label_product_name"]
    if "process_unit_qty" in data:
        row.process_unit_qty = data["process_unit_qty"]
    if "paper_color" in data:
        row.paper_color = data["paper_color"]
    if "product_name_color" in data:
        row.product_name_color = data["product_name_color"]
    if "upper_slots_locked" in data:
        row.upper_slots_locked = bool(data["upper_slots_locked"])
    if "process_slots" in data:
        set_config_process_slots(row, data["process_slots"])

    await db.commit()
    await db.refresh(row)
    master_name = await _get_master_name(db, row.product_cd)
    return config_to_dict(row, master_product_name=master_name)


@router.delete("/{config_id:int}")
async def delete_product_label_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("delete")),
):
    result = await db.execute(select(ProductLabelConfig).where(ProductLabelConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="成型用ラベル設定が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


@router.post("/derive-processes-all")
async def derive_processes_for_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    """登録済みの全成型用ラベル設定について8枠を一括再導出（上段固定ONは枠1-4を維持）。"""
    result = await db.execute(
        select(ProductLabelConfig).order_by(ProductLabelConfig.product_cd)
    )
    rows = result.scalars().all()

    updated = 0
    skipped = 0
    upper_preserved = 0
    for row in rows:
        product_cd = (row.product_cd or "").strip()
        if not product_cd:
            skipped += 1
            continue
        product_res = await db.execute(select(Product).where(Product.product_cd == product_cd))
        if not product_res.scalar_one_or_none():
            skipped += 1
            continue
        preserved = await apply_derived_slots_to_config(db, row, product_cd)
        if preserved:
            upper_preserved += 1
        updated += 1

    await db.commit()
    return {
        "success": True,
        "data": {
            "updated": updated,
            "skipped": skipped,
            "upper_preserved": upper_preserved,
            "total": len(rows),
        },
    }


@router.post("/by-product/{product_cd}/derive-processes")
async def derive_processes_for_product(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    """工程ルート・設備能率から8枠を再導出し、既存設定があれば更新（上段固定ONは枠1-4を維持）。"""
    product_res = await db.execute(select(Product).where(Product.product_cd == product_cd))
    if not product_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="製品が見つかりません")

    result = await db.execute(
        select(ProductLabelConfig).where(ProductLabelConfig.product_cd == product_cd)
    )
    row = result.scalar_one_or_none()
    if row:
        upper_preserved = await apply_derived_slots_to_config(db, row, product_cd)
        await db.commit()
        await db.refresh(row)
        master_name = await _get_master_name(db, product_cd)
        data = config_to_dict(row, master_product_name=master_name)
        data["upper_preserved"] = upper_preserved
        return data

    slots = await derive_label_process_slots(db, product_cd)
    return {
        "product_cd": product_cd,
        "process_slots": slots,
        "derived_only": True,
    }
