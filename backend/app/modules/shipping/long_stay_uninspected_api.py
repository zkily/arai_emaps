"""
長期滞在未検査在庫 API（出荷不足数一覧印刷の備考用）
- GET    /long-stay-uninspected
- POST   /long-stay-uninspected
- PUT    /long-stay-uninspected/{id}
- DELETE /long-stay-uninspected/{id}
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_sales_operation

router = APIRouter()


class LongStayItemCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=128)
    quantity: int = Field(..., ge=0)
    sort_order: Optional[int] = None


class LongStayItemUpdate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=128)
    quantity: int = Field(..., ge=0)
    sort_order: Optional[int] = None


def _row_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": int(r["id"]),
        "product_name": (r["product_name"] or "").strip(),
        "quantity": int(r["quantity"] or 0),
        "sort_order": int(r["sort_order"] or 0),
        "created_at": str(r["created_at"]) if r.get("created_at") is not None else None,
        "updated_at": str(r["updated_at"]) if r.get("updated_at") is not None else None,
    }


async def fetch_long_stay_uninspected_rows(db: AsyncSession) -> list[dict[str, Any]]:
    """印刷備考用：全件を表示順で返す。"""
    result = await db.execute(
        text(
            "SELECT id, product_name, quantity, sort_order, created_at, updated_at "
            "FROM shipping_long_stay_uninspected_stock "
            "ORDER BY sort_order ASC, id ASC"
        )
    )
    return [_row_to_dict(dict(r)) for r in result.mappings().all()]


@router.get("")
async def list_long_stay_uninspected(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    rows = await fetch_long_stay_uninspected_rows(db)
    return {"success": True, "data": rows}


@router.post("")
async def create_long_stay_uninspected(
    body: LongStayItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("create")),
):
    name = (body.product_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="製品名を入力してください")
    qty = int(body.quantity)
    if body.sort_order is None:
        r = await db.execute(
            text("SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_ord FROM shipping_long_stay_uninspected_stock")
        )
        sort_order = int((r.mappings().first() or {}).get("next_ord") or 1)
    else:
        sort_order = int(body.sort_order)

    await db.execute(
        text(
            "INSERT INTO shipping_long_stay_uninspected_stock (product_name, quantity, sort_order) "
            "VALUES (:product_name, :quantity, :sort_order)"
        ),
        {"product_name": name, "quantity": qty, "sort_order": sort_order},
    )
    await db.commit()
    r = await db.execute(text("SELECT LAST_INSERT_ID() AS id"))
    row = r.mappings().first()
    new_id = int(row["id"]) if row else None
    return {"success": True, "id": new_id}


@router.put("/{item_id}")
async def update_long_stay_uninspected(
    item_id: int,
    body: LongStayItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("edit")),
):
    name = (body.product_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="製品名を入力してください")
    params: dict[str, Any] = {
        "id": item_id,
        "product_name": name,
        "quantity": int(body.quantity),
    }
    if body.sort_order is None:
        q = text(
            "UPDATE shipping_long_stay_uninspected_stock "
            "SET product_name = :product_name, quantity = :quantity "
            "WHERE id = :id"
        )
    else:
        params["sort_order"] = int(body.sort_order)
        q = text(
            "UPDATE shipping_long_stay_uninspected_stock "
            "SET product_name = :product_name, quantity = :quantity, sort_order = :sort_order "
            "WHERE id = :id"
        )
    result = await db.execute(q, params)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="対象データが見つかりません")
    return {"success": True}


@router.delete("/{item_id}")
async def delete_long_stay_uninspected(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("delete")),
):
    result = await db.execute(
        text("DELETE FROM shipping_long_stay_uninspected_stock WHERE id = :id"),
        {"id": item_id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="対象データが見つかりません")
    return {"success": True}
