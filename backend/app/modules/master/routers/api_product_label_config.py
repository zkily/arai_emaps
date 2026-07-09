"""
成型用ラベル設定 API（product_label_config）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_master_operation
from app.modules.master.models import Product, ProductLabelConfig, ProcessRoute
from app.modules.master.product_label_service import (
    PROCESS_SLOT_FIELDS,
    apply_derived_slots_to_config,
    apply_product_master_to_config,
    build_prefill_from_product,
    config_to_dict,
    derive_label_process_slots,
    is_molding_label_target_product_cd,
    normalize_supply_type,
    resolve_route_description_for_product,
    set_config_process_slots,
)

router = APIRouter()


class OutsourceOrderEmailItem(BaseModel):
    product_cd: str
    order_qty: int = Field(ge=0)
    label_product_name: str | None = None
    master_product_name: str | None = None
    process_unit_qty: int | None = None
    paper_color: str | None = None


class OutsourceOrderEmailAttachment(BaseModel):
    filename: str
    mime_type: str = "application/pdf"
    content_base64: str


class SendOutsourceOrderEmailBody(BaseModel):
    user_ids: list[int] = Field(min_length=1)
    items: list[OutsourceOrderEmailItem] = Field(min_length=1)
    attachments: list[OutsourceOrderEmailAttachment] = Field(min_length=1)


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


async def _get_product_status(db: AsyncSession, product_cd: str) -> str:
    res = await db.execute(select(Product.status).where(Product.product_cd == product_cd))
    row = res.scalar_one_or_none()
    return (row or "active").strip().lower() or "active"


async def _config_dict_with_route(
    db: AsyncSession,
    row: ProductLabelConfig,
    master_name: str = "",
    joined_route_description: str | None = None,
    product_status: str | None = None,
) -> dict:
    route_desc = await resolve_route_description_for_product(
        db, row.product_cd, joined_route_description
    )
    if product_status is None:
        product_status = await _get_product_status(db, row.product_cd)
    return config_to_dict(
        row,
        master_product_name=master_name,
        route_description=route_desc,
        product_status=product_status,
    )


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
    if "supply_type" in body:
        try:
            data["supply_type"] = normalize_supply_type(body.get("supply_type"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if "remark" in body:
        val = body.get("remark")
        data["remark"] = (val.strip() if val else None) or None

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
    sort_by: Optional[str] = Query("master_product_name"),
    sort_order: Optional[str] = Query("asc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    query = select(
        ProductLabelConfig, Product.product_name, Product.status, ProcessRoute.description
    ).outerjoin(
        Product, _product_cd_join()
    ).outerjoin(ProcessRoute, Product.route_cd == ProcessRoute.route_cd)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                ProductLabelConfig.product_cd.like(k),
                ProductLabelConfig.label_product_name.like(k),
                Product.product_name.like(k),
            )
        )

    order = (sort_order or "asc").strip().lower()
    descending = order == "desc"
    sort_field = (sort_by or "master_product_name").strip()
    if sort_field == "master_product_name":
        primary = Product.product_name.desc() if descending else Product.product_name.asc()
    else:
        primary = ProductLabelConfig.product_cd.desc() if descending else ProductLabelConfig.product_cd.asc()
    query = query.order_by(primary, ProductLabelConfig.product_cd.asc())
    result = await db.execute(query)
    rows = result.all()
    total = len(rows)
    start = (page - 1) * page_size
    page_rows = rows[start : start + page_size]
    items = []
    for config, master_name, product_status, route_desc_raw in page_rows:
        route_desc = await resolve_route_description_for_product(
            db, config.product_cd, route_desc_raw
        )
        items.append(
            config_to_dict(
                config,
                master_product_name=master_name or "",
                route_description=route_desc,
                product_status=product_status,
            )
        )
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
    return await _config_dict_with_route(db, row, master_name)


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
    return await _config_dict_with_route(db, row, master_name)


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
    return await _config_dict_with_route(db, row, master_name)


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
    if "supply_type" in data:
        row.supply_type = data["supply_type"]
    if "remark" in data:
        row.remark = data["remark"]
    if "process_slots" in data:
        set_config_process_slots(row, data["process_slots"])

    db.add(row)
    await db.commit()
    await db.refresh(row)
    master_name = await _get_master_name(db, product_cd)
    return await _config_dict_with_route(db, row, master_name)


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
    if "supply_type" in data:
        row.supply_type = data["supply_type"]
    if "remark" in data:
        row.remark = data["remark"]
    if "process_slots" in data:
        set_config_process_slots(row, data["process_slots"])

    await db.commit()
    await db.refresh(row)
    master_name = await _get_master_name(db, row.product_cd)
    return await _config_dict_with_route(db, row, master_name)


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
    """登録済みの全成型用ラベル設定について8枠を一括再導出（固定ONは枠1-8を維持）。"""
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
    """工程ルート・設備能率から8枠を再導出し、既存設定があれば更新（固定ONは枠1-8を維持）。"""
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
        data = await _config_dict_with_route(db, row, master_name)
        data["upper_preserved"] = upper_preserved
        return data

    slots = await derive_label_process_slots(db, product_cd)
    return {
        "product_cd": product_cd,
        "process_slots": slots,
        "derived_only": True,
    }


@router.get("/outsource-orders")
async def list_outsource_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """区分が外注の成型用ラベル設定一覧。"""
    from app.services.product_label_outsource_order_email import fetch_outsource_label_configs

    items = await fetch_outsource_label_configs(db)
    return {"list": items, "total": len(items)}


@router.get("/outsource-order/email-preview")
async def preview_outsource_order_email(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注注文メール送信の事前確認。"""
    from app.services.product_label_outsource_order_email import get_outsource_order_email_preview

    return await get_outsource_order_email_preview(db)


@router.post("/outsource-order/send-email")
async def send_outsource_order_email(
    body: SendOutsourceOrderEmailBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    """注文数1以上の外注ラベル注文をメール送信（現品票PDF添付）。"""
    from app.services.product_label_outsource_order_email import send_outsource_order_email as send_email

    return await send_email(
        db,
        user_ids=body.user_ids,
        items=[item.model_dump() for item in body.items],
        attachments_payload=[att.model_dump() for att in body.attachments],
        current_user=current_user,
    )
