"""
出荷明細 API (shipping_items テーブル)
- GET /items: 一覧取得（shipping_date / end_date / destination_cd / status 等でフィルタ）
- POST /items/bulk: 一括登録（パレット割当て案 → shipping_items）
- POST /items/{id}/cancel: shipping_no_p で order_daily/picking_tasks を整理後、shipping_items を物理削除
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from pydantic import BaseModel
import re

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db

router = APIRouter()


class ShippingItemBulkRow(BaseModel):
    """bulk 登録の1行（パレット割当て案の1明細に対応）"""
    shipping_no: str
    product_cd: str
    product_name: Optional[str] = ""
    product_type: Optional[str] = ""
    product_alias: Optional[str] = ""
    delivery_date: Optional[str] = None
    destination_cd: str
    destination_name: Optional[str] = ""
    shipping_date: str
    box_type: Optional[str] = ""
    confirmed_boxes: Optional[int] = 0
    confirmed_units: Optional[int] = 0
    unit: Optional[str] = "本"
    remarks: Optional[str] = ""


def _next_suffix_no_p(value: str) -> str:
    """shipping_no_p の次番号（例: 24021801_ABC -> 24021801_ABC_1, 24021801_ABC_1 -> 24021801_ABC_2）"""
    m = re.match(r"^(.+)_(\d+)$", value)
    if m:
        return f"{m.group(1)}_{int(m.group(2)) + 1}"
    return f"{value}_1"


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


# ---------- POST /items/bulk ----------
@router.post("/bulk")
async def bulk_create_shipping_items(
    body: List[ShippingItemBulkRow],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    パレット割当て案から送られた配列を shipping_items に一括 INSERT。
    各要素について shipping_no_p を生成（shipping_no + product_cd、同組は _1, _2...）。
    既存 shipping_no_p と衝突しないよう検索してから挿入。
    """
    if not body:
        return {"success": True, "count": 0}
    try:
        # 1) 候補 shipping_no_p: 同一 (shipping_no, product_cd) は base_productCd, base_productCd_1, ...
        seen: dict = {}
        candidates: List[str] = []
        rows_norm: List[dict] = []
        for idx, row in enumerate(body):
            base = (row.shipping_no or "").strip()
            shipping_date_str = (row.shipping_date or "").strip()
            product_cd = (row.product_cd or "").strip()
            if not base or not shipping_date_str:
                raise HTTPException(status_code=400, detail=f"出荷番号・出荷日は必須です（行{idx + 1}）")
            if not product_cd:
                raise HTTPException(status_code=400, detail=f"製品コードは必須です（行{idx + 1}）")
            key = (base, product_cd)
            if key not in seen:
                seen[key] = 0
                candidate = f"{base}_{product_cd}"
            else:
                seen[key] += 1
                candidate = f"{base}_{product_cd}_{seen[key]}"
            candidates.append(candidate)
            dest_name = (row.destination_name or "").strip() if row.destination_name else ""
            prod_name = (row.product_name or "").strip() if row.product_name else ""
            unit_val = (row.unit or "本").strip() or "本"
            remarks_val = (row.remarks or "").strip() if row.remarks else ""
            box_type_val = (row.box_type or "").strip() if row.box_type else ""
            product_type_val = (row.product_type or "").strip() if row.product_type else ""
            product_alias_val = (row.product_alias or "").strip() if row.product_alias else ""
            delivery_date_val = None
            if row.delivery_date is not None and str(row.delivery_date).strip():
                raw = str(row.delivery_date).strip()[:10]
                if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
                    delivery_date_val = raw
            try:
                confirmed_boxes = int(row.confirmed_boxes) if row.confirmed_boxes is not None else 0
            except (TypeError, ValueError):
                confirmed_boxes = 0
            try:
                confirmed_units = int(row.confirmed_units) if row.confirmed_units is not None else 0
            except (TypeError, ValueError):
                confirmed_units = 0
            rows_norm.append({
                "shipping_no": base,
                "shipping_date": shipping_date_str,
                "destination_cd": (row.destination_cd or "").strip(),
                "destination_name": dest_name,
                "product_cd": product_cd,
                "product_name": prod_name,
                "product_alias": product_alias_val,
                "box_type": box_type_val,
                "confirmed_boxes": confirmed_boxes,
                "confirmed_units": confirmed_units,
                "unit": unit_val,
                "remarks": remarks_val,
                "product_type": product_type_val,
                "delivery_date": delivery_date_val,
            })

        # 2) 既存 shipping_no_p を取得し重複を避ける
        existing_set: set = set()
        if candidates:
            chunk_size = 100
            for i in range(0, len(candidates), chunk_size):
                chunk = candidates[i : i + chunk_size]
                placeholders = ", ".join([f":p{j}" for j in range(len(chunk))])
                q_ex = text(
                    "SELECT shipping_no_p FROM shipping_items WHERE shipping_no_p IN (" + placeholders + ")"
                )
                params_ex = {f"p{j}": c for j, c in enumerate(chunk)}
                res = await db.execute(q_ex, params_ex)
                for r in res.mappings():
                    existing_set.add((r.get("shipping_no_p") or "").strip())
        reserved = set(existing_set)
        final_no_p_list: List[str] = []
        for c in candidates:
            final = c
            while final in reserved:
                final = _next_suffix_no_p(final)
            reserved.add(final)
            final_no_p_list.append(final)

        # 3) INSERT IGNORE（既に同じ shipping_no_p が存在する行はスキップし 500 にしない）
        q = text(
            "INSERT IGNORE INTO shipping_items "
            "(shipping_no, shipping_no_p, shipping_date, destination_cd, destination_name, product_cd, product_name, "
            "product_alias, box_type, confirmed_boxes, confirmed_units, unit, status, remarks, product_type, delivery_date) "
            "VALUES "
            "(:shipping_no, :shipping_no_p, :shipping_date, :destination_cd, :destination_name, :product_cd, :product_name, "
            ":product_alias, :box_type, :confirmed_boxes, :confirmed_units, :unit, '未発行', :remarks, :product_type, :delivery_date)"
        )
        inserted = 0
        for idx, (rn, final_no_p) in enumerate(zip(rows_norm, final_no_p_list)):
            params = {**rn, "shipping_no_p": final_no_p}
            # shipping_date を YYYY-MM-DD に統一（先頭10文字）
            if params.get("shipping_date"):
                params["shipping_date"] = str(params["shipping_date"]).strip()[:10]
            try:
                result = await db.execute(q, params)
                inserted += result.rowcount
            except Exception as row_err:
                await db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"行{idx + 1}でエラー: {type(row_err).__name__}: {row_err}",
                ) from row_err
        await db.commit()
        return {"success": True, "count": len(body), "inserted": inserted}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {e}",
        ) from e


# ---------- POST /items/{item_id}/cancel ----------
@router.post("/{item_id}/cancel")
async def cancel_shipping_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    削除前に shipping_items.shipping_no_p で関連を処理してから物理削除する。
    1) order_daily.shipping_no に同じ値があればクリア（なければスキップ）
    2) picking_tasks.shipping_no_p に同じ値があれば該当行を削除（なければスキップ）
    3) shipping_items の該当行を物理削除
    """
    try:
        sel = text("SELECT id, shipping_no_p FROM shipping_items WHERE id = :id")
        row = await db.execute(sel, {"id": item_id})
        one = row.mappings().first()
        if not one:
            raise HTTPException(status_code=404, detail="出荷明細が見つかりません")

        shipping_no_p = (one.get("shipping_no_p") or "").strip()
        if shipping_no_p:
            # 1) order_daily: shipping_no が shipping_no_p と一致する行の shipping_no をクリア（該当なしでもエラーにしない）
            clear_od = text(
                "UPDATE order_daily SET shipping_no = NULL WHERE shipping_no = :shipping_no_p"
            )
            await db.execute(clear_od, {"shipping_no_p": shipping_no_p})

            # 2) picking_tasks: shipping_no_p が一致する行を削除（該当なしでもエラーにしない）
            del_pt = text("DELETE FROM picking_tasks WHERE shipping_no_p = :shipping_no_p")
            await db.execute(del_pt, {"shipping_no_p": shipping_no_p})

        # 3) shipping_items の該当行を物理削除
        del_q = text("DELETE FROM shipping_items WHERE id = :id")
        await db.execute(del_q, {"id": item_id})

        await db.commit()
        return {"success": True, "id": item_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"キャンセル処理に失敗しました: {type(e).__name__}: {e}",
        ) from e
