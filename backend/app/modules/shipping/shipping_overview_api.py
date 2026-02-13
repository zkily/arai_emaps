"""
出荷報告用 API
- GET /overview: 出荷一覧（日付・納入先でフィルタ、報告書用）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db

router = APIRouter()


@router.get("")
async def get_shipping_overview(
    date_from: Optional[str] = Query(None, description="出荷日開始"),
    date_to: Optional[str] = Query(None, description="出荷日終了"),
    destination_cds: Optional[str] = Query(None, description="納入先CD（カンマ区切り）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> List[dict]:
    """出荷報告書用一覧。shipping_items から shipping_date, destination_name, shipping_no, product_name, confirmed_boxes を返す。"""
    conditions = ["1=1"]
    params = {}
    if date_from:
        params["date_from"] = date_from
        conditions.append("shipping_date >= :date_from")
    if date_to:
        params["date_to"] = date_to
        conditions.append("shipping_date <= :date_to")
    if destination_cds:
        dest_list = [d.strip() for d in destination_cds.split(",") if d.strip()]
        if dest_list:
            placeholders = ", ".join([f":dest_{i}" for i in range(len(dest_list))])
            conditions.append(f"destination_cd IN ({placeholders})")
            for i, d in enumerate(dest_list):
                params[f"dest_{i}"] = d

    where_sql = " AND ".join(conditions)
    q = text("""
        SELECT shipping_date, destination_cd, destination_name, shipping_no, product_name, product_type, box_type,
               confirmed_boxes AS quantity, confirmed_units AS units, delivery_date
        FROM shipping_items
        WHERE """ + where_sql + """
        ORDER BY shipping_date, destination_cd, shipping_no, product_cd
    """)
    result = await db.execute(q, params)
    rows = result.mappings().all()
    return [
        {
            "shipping_date": r["shipping_date"].isoformat() if hasattr(r["shipping_date"], "isoformat") else str(r["shipping_date"]),
            "destination_name": r["destination_name"] or "",
            "shipping_no": r["shipping_no"] or "",
            "product_name": r["product_name"] or "",
            "product_type": r.get("product_type"),
            "box_type": r.get("box_type"),
            "quantity": int(r["quantity"] or 0),
            "units": int(r["units"]) if r.get("units") is not None else None,
            "delivery_date": r["delivery_date"].isoformat() if r.get("delivery_date") and hasattr(r["delivery_date"], "isoformat") else (str(r["delivery_date"]) if r.get("delivery_date") else None),
        }
        for r in rows
    ]
