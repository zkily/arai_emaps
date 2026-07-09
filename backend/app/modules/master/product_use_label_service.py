"""製品用ラベル設定 共通ロジック"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import Destination, Product, ProductUseLabelConfig

DEFAULT_PAPER_COLOR = "白"
DEFAULT_NAME_COLOR = "#000000"
DEFAULT_MANUFACTURER = "日鉄物産荒井\nオートモーティブ(株)"


def is_inoac_destination(destination_name: str | None) -> bool:
    """N05 (株)東北INOAC小牛田 向けレイアウト判定。"""
    raw = (destination_name or "").strip()
    if not raw:
        return False
    compact = raw.replace(" ", "").replace("　", "").upper()
    if "N05" in compact and (
        "東北INOAC" in compact or "東北イノアック" in compact or "INOAC" in compact
    ):
        return True
    if "東北INOAC小牛田" in compact or "東北イノアック小牛田" in compact:
        return True
    return False


def config_to_dict(
    row: ProductUseLabelConfig,
    master_product_name: str = "",
    product_status: str | None = None,
) -> dict:
    status = (product_status or "active").strip().lower() or "active"
    destination = (row.destination_name or "").strip() or None
    return {
        "id": row.id,
        "product_cd": row.product_cd,
        "master_product_name": master_product_name,
        "use_label_product_name": row.use_label_product_name,
        "unit_qty": row.unit_qty,
        "part_no": row.part_no,
        "destination_name": destination,
        "paper_color": row.paper_color or DEFAULT_PAPER_COLOR,
        "product_name_color": row.product_name_color or DEFAULT_NAME_COLOR,
        "back_no_1": row.back_no_1,
        "back_no_2": row.back_no_2,
        "back_no_3": row.back_no_3,
        "barcode_no": row.barcode_no,
        "is_inoac_layout": is_inoac_destination(destination),
        "product_status": status,
        "is_discontinued": status != "active",
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


async def _get_product(db: AsyncSession, product_cd: str) -> Product | None:
    res = await db.execute(select(Product).where(Product.product_cd == product_cd))
    return res.scalar_one_or_none()


def resolve_part_no_from_product(product: Product) -> str | None:
    """製品マスタの品番（part_number）をラベル用品番へ。"""
    val = (product.part_number or "").strip()
    return val or None


async def resolve_destination_name(
    db: AsyncSession,
    destination_cd: str | None,
    cache: dict[str, str | None] | None = None,
) -> str | None:
    """製品マスタの納入先CDから納入先マスタの名称のみ取得（例: (株)東北INOAC小牛田）。"""
    cd = (destination_cd or "").strip()
    if not cd:
        return None
    if cache is not None and cd in cache:
        return cache[cd]
    res = await db.execute(select(Destination).where(Destination.destination_cd == cd))
    dest = res.scalar_one_or_none()
    name = (dest.destination_name or "").strip() if dest else None
    name = name or None
    if cache is not None:
        cache[cd] = name
    return name


async def build_prefill_from_product(db: AsyncSession, product_cd: str) -> dict:
    product = await _get_product(db, product_cd)
    if not product:
        raise ValueError("製品が見つかりません")
    return {
        "product_cd": product.product_cd,
        "master_product_name": product.product_name or "",
        "use_label_product_name": product.product_name or "",
        "unit_qty": product.unit_per_box,
        "part_no": resolve_part_no_from_product(product),
        "destination_name": await resolve_destination_name(db, product.destination_cd),
        "paper_color": DEFAULT_PAPER_COLOR,
        "product_name_color": DEFAULT_NAME_COLOR,
        "back_no_1": None,
        "back_no_2": None,
        "back_no_3": None,
        "barcode_no": None,
    }


def apply_row_fields(row: ProductUseLabelConfig, data: dict) -> None:
    if "use_label_product_name" in data:
        val = data.get("use_label_product_name")
        row.use_label_product_name = (val.strip() if val else None) or None
    if "unit_qty" in data:
        qty = data.get("unit_qty")
        row.unit_qty = int(qty) if qty is not None and qty != "" else None
    if "part_no" in data:
        val = data.get("part_no")
        row.part_no = (val.strip() if val else None) or None
    if "destination_name" in data:
        val = data.get("destination_name")
        row.destination_name = (val.strip() if val else None) or None
    if "paper_color" in data:
        val = data.get("paper_color")
        row.paper_color = (val.strip() if val else None) or None
    if "product_name_color" in data:
        val = data.get("product_name_color")
        row.product_name_color = (val.strip() if val else None) or None
    for field in ("back_no_1", "back_no_2", "back_no_3", "barcode_no"):
        if field in data:
            val = data.get(field)
            setattr(row, field, (val.strip() if val else None) or None)


async def apply_master_sync_fields(
    db: AsyncSession,
    row: ProductUseLabelConfig,
    product: Product,
    destination_cache: dict[str, str | None] | None = None,
) -> None:
    """マスタ取込：品番・納入先名・入数を既存行へ反映。"""
    row.part_no = resolve_part_no_from_product(product)
    row.destination_name = await resolve_destination_name(
        db, product.destination_cd, cache=destination_cache
    )
    row.unit_qty = product.unit_per_box


async def apply_product_master_to_config(
    db: AsyncSession,
    row: ProductUseLabelConfig,
    product: Product,
    destination_cache: dict[str, str | None] | None = None,
) -> None:
    row.use_label_product_name = product.product_name or row.use_label_product_name
    row.unit_qty = product.unit_per_box
    part_no = resolve_part_no_from_product(product)
    row.part_no = part_no
    row.destination_name = await resolve_destination_name(
        db, product.destination_cd, cache=destination_cache
    )
