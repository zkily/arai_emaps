"""
出荷クイック編集 API
- PATCH /quick-update: 出荷明細の製品名・納入日・箱数・数量を一括更新
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from pydantic import BaseModel

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db

router = APIRouter()


class QuickUpdateBody(BaseModel):
    """クイック編集のリクエスト body"""
    shipping_no: str
    product_cd: str
    product_name: Optional[str] = None
    delivery_date: Optional[str] = None
    confirmed_boxes: Optional[int] = None
    confirmed_units: Optional[int] = None
    id: Optional[int] = None  # 指定時は該当 id のみ更新、未指定時は shipping_no + product_cd の先頭1件を更新


@router.patch("/quick-update")
async def quick_update_shipping_item(
    body: QuickUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    出荷明細のクイック編集。
    id が指定されていればその1件を更新、否则は shipping_no + product_cd で一致する先頭1件を更新。
    """
    shipping_no = (body.shipping_no or "").strip()
    product_cd = (body.product_cd or "").strip()
    if not shipping_no or not product_cd:
        raise HTTPException(status_code=400, detail="shipping_no と product_cd は必須です")

    # 更新する列のみ SET に含める
    set_parts = []
    params = {}

    if body.product_name is not None:
        set_parts.append("product_name = :product_name")
        params["product_name"] = body.product_name
    if body.delivery_date is not None:
        if body.delivery_date == "" or body.delivery_date == "null":
            set_parts.append("delivery_date = NULL")
        else:
            raw = str(body.delivery_date).strip()[:10]
            if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
                set_parts.append("delivery_date = :delivery_date")
                params["delivery_date"] = raw
    if body.confirmed_boxes is not None:
        set_parts.append("confirmed_boxes = :confirmed_boxes")
        params["confirmed_boxes"] = int(body.confirmed_boxes)
    if body.confirmed_units is not None:
        set_parts.append("confirmed_units = :confirmed_units")
        params["confirmed_units"] = int(body.confirmed_units)

    if not set_parts:
        return {"success": True, "updated": 0}

    params["shipping_no"] = shipping_no
    params["product_cd"] = product_cd
    if body.id is not None:
        params["id"] = body.id

    if body.id is not None:
        # id 指定: 該当 id の行を更新（shipping_no/product_cd は一致確認用としても使う）
        sel = text("SELECT id FROM shipping_items WHERE id = :id AND shipping_no = :shipping_no AND product_cd = :product_cd")
        row = await db.execute(sel, {"id": body.id, "shipping_no": shipping_no, "product_cd": product_cd})
        if row.mappings().first() is None:
            raise HTTPException(status_code=404, detail="指定された出荷明細が見つかりません")
        where_sql = "id = :id"
        params_where = {**params}
    else:
        # shipping_no + product_cd で先頭1件を更新
        where_sql = "shipping_no = :shipping_no AND product_cd = :product_cd"
        params_where = {**params}

    set_sql = ", ".join(set_parts)
    # MySQL: UPDATE ... WHERE ... LIMIT 1
    if body.id is not None:
        q = text(f"UPDATE shipping_items SET {set_sql} WHERE {where_sql}")
        result = await db.execute(q, params_where)
    else:
        q = text(f"UPDATE shipping_items SET {set_sql} WHERE {where_sql} ORDER BY id ASC LIMIT 1")
        result = await db.execute(q, params_where)

    await db.commit()
    return {"success": True, "updated": result.rowcount}
