"""
出荷不足数一覧印刷：各ページ下部の手書き用固定製品行。
製品名で products を照合し、納入先名・製品種類・箱種を付与する（箱数・本数は空）。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import Destination, Product

# 印刷用紙の手書き欄用・固定製品名（表示順）
HANDWRITING_PRODUCT_NAMES: tuple[str, ...] = (
    "400B FR",
    "032D FR",
    "BY2 FR2",
    "164B FR",
    "567D FR",
    "BY2 FR1",
)


async def fetch_handwriting_product_rows(db: AsyncSession) -> list[dict[str, Any]]:
    """固定製品名で products × destinations をジョインし、印刷用行を返す。"""
    names = list(HANDWRITING_PRODUCT_NAMES)
    _collation = "utf8mb4_unicode_ci"
    join_dest = Product.destination_cd.collate(_collation) == Destination.destination_cd.collate(
        _collation
    )
    result = await db.execute(
        select(
            Product.product_name,
            Product.product_type,
            Product.box_type,
            Destination.destination_name,
        )
        .select_from(Product)
        .outerjoin(Destination, join_dest)
        .where(Product.product_name.in_(names))
        .order_by(Product.product_cd)
    )
    by_name: dict[str, dict[str, Any]] = {}
    for r in result.all():
        pname = (r.product_name or "").strip()
        if not pname or pname in by_name:
            continue
        by_name[pname] = {
            "destination_name": (r.destination_name or "") if r.destination_name else "",
            "product_name": pname,
            "product_type": r.product_type or "",
            "box_type": r.box_type or "",
            "box_quantity": None,
            "units": None,
        }

    out: list[dict[str, Any]] = []
    for name in names:
        found = by_name.get(name)
        if found:
            out.append(found)
        else:
            out.append(
                {
                    "destination_name": "",
                    "product_name": name,
                    "product_type": "",
                    "box_type": "",
                    "box_quantity": None,
                    "units": None,
                }
            )
    return out
