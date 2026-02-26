"""
外注メッキ：注文・受入 API（outsourcing_plating_orders / outsourcing_plating_receivings）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, or_, text, delete
from typing import Optional, Any
from datetime import date, datetime

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.outsourcing.models import PlatingOrder, PlatingReceiving, PlatingStock, OutsourcingSupplier

router = APIRouter()


def _order_to_dict(
    r: PlatingOrder,
    supplier_name: Optional[str] = None,
    total_receiving_qty_map: Optional[dict] = None,
) -> dict:
    out = {
        "id": r.id,
        "order_no": r.order_no,
        "order_date": r.order_date.isoformat() if r.order_date else None,
        "supplier_cd": r.supplier_cd,
        "supplier_name": supplier_name or r.supplier_cd,
        "product_cd": r.product_cd,
        "product_name": r.product_name,
        "plating_type": r.plating_type,
        "quantity": r.quantity,
        "unit": r.unit,
        "unit_price": float(r.unit_price) if r.unit_price is not None else 0,
        "delivery_date": r.delivery_date.isoformat() if r.delivery_date else None,
        "delivery_location": r.delivery_location,
        "category": r.category,
        "content": r.content,
        "specification": r.specification,
        "received_qty": r.received_qty or 0,
        "status": r.status,
        "remarks": r.remarks,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }
    if total_receiving_qty_map is not None and r.id in total_receiving_qty_map:
        out["total_receiving_qty"] = total_receiving_qty_map[r.id]
    return out


def _parse_date(v: Any) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return datetime.strptime(v[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
    return None


def _order_no_prefix(supplier_cd: str, order_date: date) -> str:
    return f"{supplier_cd}{order_date.strftime('%Y%m%d')}-"


async def _get_next_order_no_seq(db: AsyncSession, prefix: str) -> int:
    q = select(func.max(PlatingOrder.order_no)).where(PlatingOrder.order_no.like(f"{prefix}%"))
    r = await db.execute(q)
    max_no = r.scalar_one_or_none()
    if not max_no:
        return 1
    try:
        seq_part = str(max_no).split("-")[-1]
        return int(seq_part) + 1
    except (IndexError, ValueError):
        return 1


async def _generate_order_no(db: AsyncSession, supplier_cd: str, order_date: date) -> str:
    prefix = _order_no_prefix(supplier_cd, order_date)
    seq = await _get_next_order_no_seq(db, prefix)
    return f"{prefix}{seq:02d}"


def _receiving_to_dict(r: PlatingReceiving, supplier_name: Optional[str] = None) -> dict:
    return {
        "id": r.id,
        "receiving_no": r.receiving_no,
        "receiving_date": r.receiving_date.isoformat() if r.receiving_date else None,
        "order_id": r.order_id,
        "order_no": r.order_no,
        "supplier_cd": r.supplier_cd,
        "supplier_name": supplier_name or r.supplier_cd,
        "product_cd": r.product_cd,
        "product_name": r.product_name,
        "plating_type": r.plating_type,
        "order_qty": r.order_qty,
        "receiving_qty": r.receiving_qty,
        "good_qty": r.good_qty or 0,
        "defect_qty": r.defect_qty or 0,
        "defect_reason": r.defect_reason,
        "status": r.status,
        "inspector": r.inspector,
        "remarks": r.remarks,
    }


def _receiving_no_prefix(receiving_date: date) -> str:
    """受入番号プレフィックス: PR-YYYYMMDD-（メッキ）"""
    return f"PR-{receiving_date.strftime('%Y%m%d')}-"


async def _get_next_receiving_no_seq(db: AsyncSession, receiving_date: date) -> int:
    prefix = _receiving_no_prefix(receiving_date)
    q = select(func.max(PlatingReceiving.receiving_no)).where(
        PlatingReceiving.receiving_no.like(f"{prefix}%")
    )
    r = await db.execute(q)
    max_no = r.scalar_one_or_none()
    if not max_no or not str(max_no).startswith(prefix):
        return 1
    try:
        seq_part = str(max_no).replace(prefix, "").strip()
        return int(seq_part) + 1
    except (ValueError, TypeError):
        return 1


async def _generate_receiving_no(db: AsyncSession, receiving_date: date) -> str:
    prefix = _receiving_no_prefix(receiving_date)
    seq = await _get_next_receiving_no_seq(db, receiving_date)
    return f"{prefix}{seq:02d}"


@router.get("/orders/pending")
async def get_pending_plating_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """未完了のメッキ注文一覧（pending / ordered / partial）"""
    q = select(PlatingOrder).where(
        PlatingOrder.status.in_(["pending", "ordered", "partial"])
    ).order_by(PlatingOrder.delivery_date.asc(), PlatingOrder.id.asc())
    result = await db.execute(q)
    rows = result.scalars().all()
    supplier_cds = list({r.supplier_cd for r in rows})
    supplier_names = {}
    if supplier_cds:
        sq = select(OutsourcingSupplier.supplier_cd, OutsourcingSupplier.supplier_name).where(
            OutsourcingSupplier.supplier_cd.in_(supplier_cds)
        )
        sr = await db.execute(sq)
        for s in sr.all():
            supplier_names[s[0]] = s[1]
    items = []
    for r in rows:
        items.append({
            "id": r.id,
            "order_no": r.order_no,
            "order_date": r.order_date.isoformat() if r.order_date else None,
            "supplier_cd": r.supplier_cd,
            "supplier_name": supplier_names.get(r.supplier_cd) or r.supplier_cd,
            "product_cd": r.product_cd,
            "product_name": r.product_name,
            "plating_type": r.plating_type,
            "quantity": r.quantity,
            "received_qty": r.received_qty or 0,
            "status": r.status,
        })
    return {"success": True, "data": items}


@router.get("/orders")
async def get_plating_orders(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=1000),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    supplierId: Optional[str] = Query(None),
    supplierCd: Optional[str] = Query(None),
    productName: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ注文一覧（ページネーション・日付・条件絞り）"""
    q = select(PlatingOrder)
    if startDate:
        q = q.where(PlatingOrder.order_date >= startDate)
    if endDate:
        q = q.where(PlatingOrder.order_date <= endDate)
    if productName:
        q = q.where(PlatingOrder.product_name == productName)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                PlatingOrder.order_no.ilike(kw),
                PlatingOrder.product_cd.ilike(kw),
                PlatingOrder.product_name.ilike(kw),
            )
        )
    supplier_filter = supplierId or supplierCd
    if supplier_filter:
        try:
            sid = int(supplier_filter)
            sq = select(OutsourcingSupplier.supplier_cd).where(OutsourcingSupplier.id == sid)
            sr = await db.execute(sq)
            sc = sr.scalar_one_or_none()
            if sc:
                q = q.where(PlatingOrder.supplier_cd == sc)
        except ValueError:
            q = q.where(PlatingOrder.supplier_cd == supplier_filter)

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    q = q.order_by(PlatingOrder.order_date.asc(), PlatingOrder.id.asc())
    offset = (page - 1) * pageSize
    q = q.offset(offset).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()
    supplier_cds = list({r.supplier_cd for r in rows})
    supplier_names = {}
    if supplier_cds:
        sq = select(OutsourcingSupplier.supplier_cd, OutsourcingSupplier.supplier_name).where(
            OutsourcingSupplier.supplier_cd.in_(supplier_cds)
        )
        sr = await db.execute(sq)
        for s in sr.all():
            supplier_names[s[0]] = s[1]
    order_ids = [r.id for r in rows]
    total_receiving_qty_map = {}
    if order_ids:
        sum_q = (
            select(PlatingReceiving.order_id, func.coalesce(func.sum(PlatingReceiving.receiving_qty), 0).label("total"))
            .where(PlatingReceiving.order_id.in_(order_ids))
            .group_by(PlatingReceiving.order_id)
        )
        sum_res = await db.execute(sum_q)
        for order_id, total in sum_res.all():
            total_receiving_qty_map[order_id] = int(total)
    items = [_order_to_dict(r, supplier_names.get(r.supplier_cd), total_receiving_qty_map) for r in rows]
    return {"success": True, "data": items, "total": total}


@router.get("/orders/by-order-no")
async def get_plating_orders_by_order_no(
    order_no: Optional[str] = Query(None, alias="order_no"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """注文番号でメッキ注文一覧取得"""
    if not order_no or not order_no.strip():
        return {"success": True, "data": []}
    q = select(PlatingOrder).where(PlatingOrder.order_no == order_no.strip()).order_by(PlatingOrder.id)
    result = await db.execute(q)
    rows = result.scalars().all()
    supplier_cds = list({r.supplier_cd for r in rows})
    supplier_names = {}
    if supplier_cds:
        sq = select(OutsourcingSupplier.supplier_cd, OutsourcingSupplier.supplier_name).where(
            OutsourcingSupplier.supplier_cd.in_(supplier_cds)
        )
        sr = await db.execute(sq)
        for s in sr.all():
            supplier_names[s[0]] = s[1]
    order_ids = [r.id for r in rows]
    total_receiving_qty_map = {}
    if order_ids:
        sum_q = (
            select(PlatingReceiving.order_id, func.coalesce(func.sum(PlatingReceiving.receiving_qty), 0).label("total"))
            .where(PlatingReceiving.order_id.in_(order_ids))
            .group_by(PlatingReceiving.order_id)
        )
        sum_res = await db.execute(sum_q)
        for order_id, total in sum_res.all():
            total_receiving_qty_map[order_id] = int(total)
    items = [_order_to_dict(r, supplier_names.get(r.supplier_cd), total_receiving_qty_map) for r in rows]
    return {"success": True, "data": items}


@router.post("/orders")
async def create_plating_order(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ注文新規登録（order_no 自動採番）"""
    try:
        order_date_val = body.get("order_date") or body.get("orderDate")
        if not order_date_val:
            raise HTTPException(status_code=400, detail="order_date は必須です")
        if hasattr(order_date_val, "isoformat"):
            order_date_val = order_date_val.isoformat()[:10]
        else:
            order_date_val = str(order_date_val)[:10] if order_date_val else ""
        order_date = _parse_date(order_date_val)
        if not order_date:
            raise HTTPException(status_code=400, detail="order_date の形式が不正です（YYYY-MM-DD）")
        supplier_cd = str(body.get("supplier_cd") or body.get("supplierCd") or "").strip()
        if not supplier_cd:
            raise HTTPException(status_code=400, detail="supplier_cd は必須です")
        order_no = await _generate_order_no(db, supplier_cd, order_date)
        product_cd = str(body.get("product_cd") or body.get("productCode") or "").strip()
        if not product_cd:
            raise HTTPException(status_code=400, detail="product_cd は必須です")
        product_name = str(body.get("product_name") or body.get("productName") or "")[:200]
        plating_type = str(body.get("plating_type") or body.get("platingType") or "メッキ")[:50]
        quantity = int(float(body.get("quantity") or 0))
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="quantity は1以上で指定してください")
        unit = str(body.get("unit") or "個")[:10]
        unit_price = float(body.get("unit_price") or body.get("unitPrice") or 0)
        delivery_val = body.get("delivery_date") or body.get("deliveryDate")
        if hasattr(delivery_val, "isoformat"):
            delivery_val = delivery_val.isoformat()[:10]
        delivery_date = _parse_date(delivery_val)
        delivery_location = body.get("delivery_location") or body.get("deliveryLocation")
        if delivery_location is not None:
            delivery_location = str(delivery_location)[:50]
        category = body.get("category")
        if category is not None:
            category = str(category)[:50]
        content = body.get("content")
        if content is not None:
            content = str(content)[:50]
        specification = body.get("specification")
        if specification is not None:
            specification = str(specification)[:50]
        remarks = body.get("remarks")
        created_by = str(body.get("created_by") or "system")[:50]

        row = PlatingOrder(
            order_no=order_no,
            order_date=order_date,
            supplier_cd=supplier_cd,
            product_cd=product_cd,
            product_name=product_name or None,
            plating_type=plating_type,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            delivery_date=delivery_date,
            delivery_location=delivery_location,
            category=category,
            content=content,
            specification=specification,
            received_qty=0,
            status="pending",
            remarks=remarks,
            created_by=created_by,
        )
        db.add(row)
        await db.flush()
        await db.refresh(row)
        return {"success": True, "data": _order_to_dict(row)}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}")
async def update_plating_order(
    order_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ注文更新。注文・受入を更新し、トリガーで stock_transaction_logs は「直接更新数量」で反映する（編集時は削除しない）。"""
    q = select(PlatingOrder).where(PlatingOrder.id == order_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="注文が見つかりません")

    for key, attr in [
        ("order_date", "order_date"),
        ("orderDate", "order_date"),
        ("product_cd", "product_cd"),
        ("productCode", "product_cd"),
        ("product_name", "product_name"),
        ("productName", "product_name"),
        ("plating_type", "plating_type"),
        ("platingType", "plating_type"),
        ("quantity", "quantity"),
        ("unit_price", "unit_price"),
        ("unitPrice", "unit_price"),
        ("delivery_date", "delivery_date"),
        ("deliveryDate", "delivery_date"),
        ("delivery_location", "delivery_location"),
        ("deliveryLocation", "delivery_location"),
        ("category", "category"),
        ("content", "content"),
        ("specification", "specification"),
        ("remarks", "remarks"),
        ("status", "status"),
    ]:
        if key in body and body[key] is not None:
            val = body[key]
            if attr == "order_date" or attr == "delivery_date":
                val = _parse_date(val)
            setattr(row, attr, val)
    try:
        await db.flush()
        # 該当注文に紐づく受入レコードを注文の内容で同期する
        q_rec = select(PlatingReceiving).where(PlatingReceiving.order_id == order_id)
        rec_res = await db.execute(q_rec)
        for rec in rec_res.scalars().all():
            rec.order_no = row.order_no
            rec.supplier_cd = row.supplier_cd
            rec.product_cd = row.product_cd
            rec.product_name = row.product_name
            rec.plating_type = row.plating_type
            rec.order_qty = row.quantity
            rec.delivery_location = row.delivery_location
            rec.category = row.category
            rec.content = row.content
            rec.specification = row.specification
        await db.flush()
        await db.refresh(row)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"注文更新失敗: {str(e)}")
    return {"success": True, "data": _order_to_dict(row)}


@router.delete("/orders/{order_id}")
async def delete_plating_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ注文削除。outsourcing_plating_orders の該当行の order_no を元に、
    1) outsourcing_plating_receivings の order_no が同じ行を削除、
    2) stock_transaction_logs の notes が同じ行を削除（該当なしは無視）、
    3) 注文行を削除。"""
    q = select(PlatingOrder).where(PlatingOrder.id == order_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="注文が見つかりません")
    order_no = (row.order_no or "").strip()

    if order_no:
        # stock_transaction_logs: notes に注文番号を格納している行を削除（order_no 列は使わない）
        await db.execute(
            text("DELETE FROM stock_transaction_logs WHERE notes = :ono"),
            {"ono": order_no},
        )
        # outsourcing_plating_receivings: order_no が一致する行を削除（FK のため注文より先）
        await db.execute(delete(PlatingReceiving).where(PlatingReceiving.order_no == order_no))

    await db.delete(row)
    await db.flush()
    return {"success": True, "message": "削除しました"}


@router.post("/orders/batch-order")
async def batch_order_plating(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """注文書発行：対象 id のうち status='pending' の注文のみ status を 'ordered' に更新し、
    該当注文ごとに outsourcing_plating_receivings に 1 件の受入レコード（待受入）を自動作成する。"""
    raw_ids = body.get("order_ids") or body.get("ids") or body.get("orderIds") or []
    order_ids = []
    for x in raw_ids:
        try:
            order_ids.append(int(x))
        except (TypeError, ValueError):
            continue
    order_ids = list(dict.fromkeys(order_ids))
    if not order_ids:
        return {"success": True, "message": "0件の注文を発注しました"}
    try:
        placeholders = ", ".join([f":id_{i}" for i in range(len(order_ids))])
        sql = (
            "UPDATE outsourcing_plating_orders SET status = :status "
            f"WHERE id IN ({placeholders}) AND status = 'pending'"
        )
        params = {"status": "ordered", **{f"id_{i}": order_ids[i] for i in range(len(order_ids))}}
        result = await db.execute(text(sql), params)
        count = result.rowcount if result.rowcount is not None else 0

        # 外注先が「北九州ケミカル」の注文は outsourcing_plating_receivings に挿入しない（注文 status は更新済み、stock_transaction_logs はトリガーで従来通り）
        q_exclude = select(OutsourcingSupplier.supplier_cd).where(
            OutsourcingSupplier.supplier_name == "北九州ケミカル"
        )
        r_exclude = await db.execute(q_exclude)
        exclude_supplier_cds = {row[0] for row in r_exclude.all()}

        # 更新された注文（status='ordered'）を取得し、受入が未作成の注文のみ受入レコードを 1 件作成（北九州ケミカルを除く）
        q_orders = select(PlatingOrder).where(
            PlatingOrder.id.in_(order_ids),
            PlatingOrder.status == "ordered",
        )
        res_orders = await db.execute(q_orders)
        orders_updated = list(res_orders.scalars().all())
        existing = await db.execute(
            select(PlatingReceiving.order_id).where(PlatingReceiving.order_id.in_(order_ids))
        )
        existing_order_ids = {r[0] for r in existing.all()}
        today = date.today()
        for order in orders_updated:
            if order.id in existing_order_ids:
                continue
            if order.supplier_cd in exclude_supplier_cds:
                continue
            receiving_date = order.delivery_date if order.delivery_date else today
            if hasattr(receiving_date, "isoformat"):
                rec_date = receiving_date
            else:
                rec_date = _parse_date(str(receiving_date)[:10]) or today
            receiving_no = await _generate_receiving_no(db, rec_date)
            row = PlatingReceiving(
                receiving_no=receiving_no,
                receiving_date=rec_date,
                order_id=order.id,
                order_no=order.order_no,
                supplier_cd=order.supplier_cd,
                product_cd=order.product_cd,
                product_name=order.product_name,
                plating_type=order.plating_type,
                order_qty=order.quantity,
                receiving_qty=0,
                good_qty=0,
                defect_qty=0,
                status="pending",
                inspector=None,
                remarks=None,
                delivery_location=order.delivery_location,
                category=order.category,
                content=order.content,
                specification=order.specification,
            )
            db.add(row)
            existing_order_ids.add(order.id)
            await db.flush()

        return {"success": True, "message": f"{count}件の注文を発注しました"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock")
async def get_plating_stock(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
    supplierId: Optional[int] = Query(None, alias="supplierId"),
    productCode: Optional[str] = Query(None, alias="productCode"),
    stockStatus: Optional[str] = Query(None, alias="stockStatus"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注メッキ在庫一覧（outsourcing_plating_stock + 外注先名は outsourcing_suppliers と JOIN）"""
    q = (
        select(PlatingStock, OutsourcingSupplier.supplier_name, OutsourcingSupplier.id.label("supplier_id"))
        .join(OutsourcingSupplier, PlatingStock.supplier_cd == OutsourcingSupplier.supplier_cd)
    )
    if supplierId is not None:
        q = q.where(OutsourcingSupplier.id == supplierId)
    if productCode and productCode.strip():
        q = q.where(PlatingStock.product_cd.ilike(f"%{productCode.strip()}%"))
    if stockStatus:
        if stockStatus == "empty":
            q = q.where(PlatingStock.ordered_qty - PlatingStock.used_qty <= 0)
        elif stockStatus == "low":
            q = q.where(
                (PlatingStock.ordered_qty - PlatingStock.used_qty > 0)
                & (PlatingStock.ordered_qty - PlatingStock.used_qty < PlatingStock.min_stock)
            )
        elif stockStatus == "normal":
            q = q.where(
                (PlatingStock.ordered_qty - PlatingStock.used_qty > 0)
                & ((PlatingStock.ordered_qty - PlatingStock.used_qty) >= PlatingStock.min_stock)
            )
    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    q = q.order_by(PlatingStock.product_cd, PlatingStock.supplier_cd)
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(q)
    rows = result.all()
    data = []
    for st, supplier_name, supplier_id in rows:
        stock_qty = (st.ordered_qty or 0) - (st.used_qty or 0)
        data.append({
            "id": st.id,
            "product_cd": st.product_cd,
            "product_name": st.product_name or "",
            "supplier_cd": st.supplier_cd,
            "supplier_name": supplier_name or st.supplier_cd,
            "supplier_id": supplier_id,
            "plating_type": st.plating_type or "",
            "ordered_qty": st.ordered_qty or 0,
            "received_qty": st.received_qty or 0,
            "used_qty": st.used_qty or 0,
            "stock_qty": stock_qty,
            "pending_qty": st.pending_qty or 0,
            "min_stock": st.min_stock or 0,
            "last_receive_date": st.last_receive_date.isoformat() if st.last_receive_date else None,
            "last_issue_date": st.last_issue_date.isoformat() if st.last_issue_date else None,
        })
    return {"success": True, "data": data, "total": total}


@router.get("/receivings")
async def get_plating_receivings(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    supplierId: Optional[str] = Query(None),
    supplierCd: Optional[str] = Query(None),
    productName: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ受入一覧（ページネーション・日付・条件絞り）"""
    q = select(PlatingReceiving)
    if startDate:
        q = q.where(PlatingReceiving.receiving_date >= startDate)
    if endDate:
        q = q.where(PlatingReceiving.receiving_date <= endDate)
    if productName:
        q = q.where(PlatingReceiving.product_name == productName)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                PlatingReceiving.receiving_no.ilike(kw),
                PlatingReceiving.order_no.ilike(kw),
                PlatingReceiving.product_cd.ilike(kw),
                PlatingReceiving.product_name.ilike(kw),
            )
        )
    supplier_filter = supplierId or supplierCd
    if supplier_filter:
        try:
            sid = int(supplier_filter)
            sq = select(OutsourcingSupplier.supplier_cd).where(OutsourcingSupplier.id == sid)
            sr = await db.execute(sq)
            sc = sr.scalar_one_or_none()
            if sc:
                q = q.where(PlatingReceiving.supplier_cd == sc)
        except ValueError:
            q = q.where(PlatingReceiving.supplier_cd == supplier_filter)

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    q = q.order_by(PlatingReceiving.receiving_date.desc(), PlatingReceiving.id.desc())
    offset = (page - 1) * pageSize
    q = q.offset(offset).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()

    supplier_cds = list({r.supplier_cd for r in rows})
    supplier_names = {}
    if supplier_cds:
        sq = select(OutsourcingSupplier.supplier_cd, OutsourcingSupplier.supplier_name).where(
            OutsourcingSupplier.supplier_cd.in_(supplier_cds)
        )
        sr = await db.execute(sq)
        for s in sr.all():
            supplier_names[s[0]] = s[1]

    data = [_receiving_to_dict(r, supplier_names.get(r.supplier_cd)) for r in rows]
    return {"success": True, "data": data, "total": total}


@router.post("/receivings")
async def create_plating_receiving(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ受入新規登録（receiving_no 未指定時は PR-YYYYMMDD-NN 形式を自動作成）"""
    order_id = body.get("order_id") or body.get("orderId")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id は必須です")
    receiving_no = body.get("receiving_no") or body.get("receivingNo")
    receiving_date = body.get("receiving_date") or body.get("receivingDate")
    if not receiving_date:
        raise HTTPException(status_code=400, detail="受入日は必須です")
    receiving_qty = int(body.get("receiving_qty") or body.get("receivingQty") or 0)
    good_qty = int(body.get("good_qty") or body.get("goodQty") or 0)
    defect_qty = int(body.get("defect_qty") or body.get("defectQty") or 0)

    oq = select(PlatingOrder).where(PlatingOrder.id == order_id)
    or_res = await db.execute(oq)
    order_row = or_res.scalar_one_or_none()
    if not order_row:
        raise HTTPException(status_code=404, detail="注文が見つかりません")

    if not receiving_no or not str(receiving_no).strip():
        if hasattr(receiving_date, "isoformat"):
            rec_date = receiving_date
        else:
            rec_date = _parse_date(str(receiving_date)[:10])
        if not rec_date:
            raise HTTPException(status_code=400, detail="受入日の形式が不正です（YYYY-MM-DD）")
        receiving_no = await _generate_receiving_no(db, rec_date)

    ex = await db.execute(select(PlatingReceiving).where(PlatingReceiving.receiving_no == receiving_no))
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="受入番号が既に存在します")

    row = PlatingReceiving(
        receiving_no=receiving_no,
        receiving_date=receiving_date,
        order_id=order_id,
        order_no=order_row.order_no,
        supplier_cd=order_row.supplier_cd,
        product_cd=order_row.product_cd,
        product_name=order_row.product_name,
        plating_type=order_row.plating_type,
        order_qty=order_row.quantity,
        receiving_qty=receiving_qty,
        good_qty=good_qty,
        defect_qty=defect_qty,
        defect_reason=body.get("defect_reason") or body.get("defectReason"),
        status="pending",
        inspector=body.get("inspector"),
        remarks=body.get("remarks"),
        delivery_location=order_row.delivery_location,
        category=order_row.category,
        content=order_row.content,
        specification=order_row.specification,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return {"success": True, "data": _receiving_to_dict(row)}


@router.put("/receivings/{receiving_id}")
async def update_plating_receiving(
    receiving_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ受入更新"""
    q = select(PlatingReceiving).where(PlatingReceiving.id == receiving_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="受入が見つかりません")

    for key, attr in [
        ("receiving_date", "receiving_date"),
        ("receivingDate", "receiving_date"),
        ("receiving_qty", "receiving_qty"),
        ("receivingQty", "receiving_qty"),
        ("good_qty", "good_qty"),
        ("goodQty", "good_qty"),
        ("defect_qty", "defect_qty"),
        ("defectQty", "defect_qty"),
        ("defect_reason", "defect_reason"),
        ("defectReason", "defect_reason"),
        ("inspector", "inspector"),
        ("remarks", "remarks"),
        ("status", "status"),
    ]:
        if key in body and body[key] is not None:
            v = body[key]
            if attr == "receiving_date" and v:
                setattr(row, attr, v)
            elif attr in ("receiving_qty", "good_qty", "defect_qty"):
                setattr(row, attr, int(v))
            else:
                setattr(row, attr, v)

    await db.flush()
    await db.refresh(row)
    return {"success": True, "data": _receiving_to_dict(row)}


@router.delete("/receivings/{receiving_id}")
async def delete_plating_receiving(
    receiving_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ受入削除"""
    q = select(PlatingReceiving).where(PlatingReceiving.id == receiving_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="受入が見つかりません")
    order_id = row.order_id
    await db.delete(row)
    await db.flush()

    subq = (
        select(func.coalesce(func.sum(PlatingReceiving.good_qty), 0))
        .where(PlatingReceiving.order_id == order_id)
    )
    r2 = await db.execute(subq)
    new_received = int(r2.scalar_one_or_none() or 0)
    oq = select(PlatingOrder).where(PlatingOrder.id == order_id)
    ores = await db.execute(oq)
    order_row = ores.scalar_one_or_none()
    if order_row:
        order_row.received_qty = new_received
        if new_received >= order_row.quantity:
            order_row.status = "completed"
        elif new_received > 0:
            order_row.status = "partial"
        else:
            order_row.status = "pending"
        await db.flush()
    return {"success": True, "message": "受入を削除しました"}


@router.get("/receivings/products")
async def get_plating_receiving_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メッキ注文・受入で使用されている品名一覧（重複排除）"""
    q = select(distinct(PlatingOrder.product_name)).where(
        PlatingOrder.product_name.isnot(None),
        PlatingOrder.product_name != "",
    ).order_by(PlatingOrder.product_name)
    result = await db.execute(q)
    names = [row[0] for row in result.all() if row[0]]
    q2 = select(distinct(PlatingReceiving.product_name)).where(
        PlatingReceiving.product_name.isnot(None),
        PlatingReceiving.product_name != "",
    )
    result2 = await db.execute(q2)
    for row in result2.all():
        if row[0] and row[0] not in names:
            names.append(row[0])
    names.sort()
    return {"success": True, "data": names}
