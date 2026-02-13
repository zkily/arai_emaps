"""
出荷明細 API (shipping_items テーブル)
- GET /items: 一覧取得（shipping_date / end_date / destination_cd / status 等でフィルタ）
- POST /items/{id}/cancel: 指定行をキャンセル（status = 'キャンセル'）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import date

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db

router = APIRouter()


def _row_to_item(r: dict) -> dict:
    """DB 行をフロント用の辞書に変換（日付は文字列）"""
    return {
        "id": r.get("id"),
        "shipping_no": r.get("shipping_no") or "",
        "shipping_date": r.get("shipping_date").isoformat() if hasattr(r.get("shipping_date"), "isoformat") else str(r.get("shipping_date") or ""),
        "delivery_date": r.get("delivery_date").isoformat() if hasattr(r.get("delivery_date"), "isoformat") else (str(r.get("delivery_date")) if r.get("delivery_date") else ""),
        "destination_cd": r.get("destination_cd") or "",
        "destination_name": r.get("destination_name") or "",
        "product_cd": r.get("product_cd") or "",
        "product_name": r.get("product_name") or "",
        "product_alias": r.get("product_alias") or "",
        "box_type": r.get("box_type") or "",
        "confirmed_boxes": int(r.get("confirmed_boxes") or 0),
        "confirmed_units": int(r.get("confirmed_units") or 0),
        "unit": r.get("unit") or "本",
        "status": r.get("status") or "未発行",
        "remarks": r.get("remarks") or "",
        "created_at": str(r.get("created_at")) if r.get("created_at") else "",
        "updated_at": str(r.get("updated_at")) if r.get("updated_at") else "",
        "shipping_no_p": r.get("shipping_no_p") or "",
        "product_type": r.get("product_type") or "",
    }


# ---------- GET /items ----------
@router.get("")
async def list_shipping_items(
    shipping_date: Optional[str] = Query(None, description="出荷日（開始）"),
    end_date: Optional[str] = Query(None, description="出荷日（終了）"),
    destination_cd: Optional[str] = Query(None),
    product_cd: Optional[str] = Query(None),
    product_name: Optional[str] = Query(None),
    box_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    shipping_no: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> List[dict]:
    """shipping_items テーブルから出荷明細一覧を取得"""
    conditions = []
    params = {}
    if shipping_date:
        params["shipping_date"] = shipping_date
        if end_date:
            params["end_date"] = end_date
            conditions.append("shipping_date BETWEEN :shipping_date AND :end_date")
        else:
            conditions.append("shipping_date = :shipping_date")
    if destination_cd:
        dest_list = [d.strip() for d in destination_cd.split(",") if d.strip()]
        if dest_list:
            if len(dest_list) == 1:
                conditions.append("destination_cd = :destination_cd")
                params["destination_cd"] = dest_list[0]
            else:
                placeholders = ", ".join([f":dest_{i}" for i in range(len(dest_list))])
                conditions.append(f"destination_cd IN ({placeholders})")
                for i, d in enumerate(dest_list):
                    params[f"dest_{i}"] = d
    if product_cd:
        conditions.append("product_cd LIKE :product_cd")
        params["product_cd"] = f"%{product_cd}%"
    if product_name:
        conditions.append("product_name LIKE :product_name")
        params["product_name"] = f"%{product_name}%"
    if box_type:
        conditions.append("box_type = :box_type")
        params["box_type"] = box_type
    if status:
        conditions.append("status = :status")
        params["status"] = status
    if shipping_no:
        conditions.append("(shipping_no LIKE :shipping_no OR shipping_no_p LIKE :shipping_no_p)")
        params["shipping_no"] = f"%{shipping_no}%"
        params["shipping_no_p"] = f"%{shipping_no}%"

    where_sql = " AND ".join(conditions) if conditions else "1=1"
    q = text(
        "SELECT id, shipping_no, shipping_date, delivery_date, destination_cd, destination_name, "
        "product_cd, product_name, product_alias, box_type, confirmed_boxes, confirmed_units, "
        "unit, status, remarks, created_at, updated_at, shipping_no_p, product_type "
        "FROM shipping_items WHERE " + where_sql + " ORDER BY shipping_date DESC, shipping_no, id"
    )
    result = await db.execute(q, params)
    rows = result.mappings().all()
    return [_row_to_item(dict(r)) for r in rows]


# ---------- POST /items/{item_id}/cancel ----------
@router.post("/{item_id}/cancel")
async def cancel_shipping_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """出荷明細をキャンセル（status を 'キャンセル' に更新）"""
    q = text(
        "UPDATE shipping_items SET status = 'キャンセル', updated_at = CURRENT_TIMESTAMP WHERE id = :id"
    )
    result = await db.execute(q, {"id": item_id})
    await db.commit()
    if result.rowcount == 0:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="出荷明細が見つかりません")
    return {"success": True, "id": item_id}
