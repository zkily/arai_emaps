"""
外注溶接：注文・受入 API（outsourcing_welding_orders / outsourcing_welding_receivings）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, or_, text, delete as sql_delete
from typing import Optional, Any
from datetime import date, datetime

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.outsourcing.models import WeldingOrder, WeldingReceiving, WeldingStock, OutsourcingSupplier
from app.modules.erp.stock_transaction_log_models import StockTransactionLog

router = APIRouter()


def _receiving_to_dict(r: WeldingReceiving, supplier_name: Optional[str] = None) -> dict:
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
        "welding_type": r.welding_type,
        "welding_points": r.welding_points,
        "order_qty": r.order_qty,
        "receiving_qty": r.receiving_qty,
        "good_qty": r.good_qty or 0,
        "defect_qty": r.defect_qty or 0,
        "defect_reason": r.defect_reason,
        "status": r.status,
        "inspector": r.inspector,
        "remarks": r.remarks,
    }


@router.get("/orders/pending")
async def get_pending_welding_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """未完了の溶接注文一覧（pending / ordered / partial）"""
    q = select(WeldingOrder).where(
        WeldingOrder.status.in_(["pending", "ordered", "partial"])
    ).order_by(WeldingOrder.delivery_date.asc(), WeldingOrder.id.asc())
    result = await db.execute(q)
    rows = result.scalars().all()
    items = []
    for r in rows:
        items.append({
            "id": r.id,
            "order_no": r.order_no,
            "order_date": r.order_date.isoformat() if r.order_date else None,
            "supplier_cd": r.supplier_cd,
            "product_cd": r.product_cd,
            "product_name": r.product_name,
            "welding_type": r.welding_type,
            "quantity": r.quantity,
            "received_qty": r.received_qty or 0,
            "status": r.status,
        })
    return {"success": True, "data": items}


@router.get("/orders")
async def get_welding_orders(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=1000),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    supplierId: Optional[str] = Query(None),
    productName: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接注文一覧（ページネーション・日付・条件絞り）"""
    q = select(WeldingOrder)
    if startDate:
        q = q.where(WeldingOrder.order_date >= startDate)
    if endDate:
        q = q.where(WeldingOrder.order_date <= endDate)
    if productName:
        q = q.where(WeldingOrder.product_name == productName)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                WeldingOrder.order_no.ilike(kw),
                WeldingOrder.product_cd.ilike(kw),
                WeldingOrder.product_name.ilike(kw),
            )
        )
    if supplierId:
        try:
            sid = int(supplierId)
            sq = select(OutsourcingSupplier.supplier_cd).where(OutsourcingSupplier.id == sid)
            sr = await db.execute(sq)
            sc = sr.scalar_one_or_none()
            if sc:
                q = q.where(WeldingOrder.supplier_cd == sc)
        except ValueError:
            q = q.where(WeldingOrder.supplier_cd == supplierId)

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    q = q.order_by(WeldingOrder.order_date.asc(), WeldingOrder.id.asc())
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
            "specification": r.specification,
            "welding_type": r.welding_type,
            "welding_points": r.welding_points or 0,
            "quantity": r.quantity,
            "unit": r.unit,
            "unit_price": float(r.unit_price) if r.unit_price is not None else 0,
            "delivery_date": r.delivery_date.isoformat() if r.delivery_date else None,
            "delivery_location": r.delivery_location,
            "category": r.category,
            "content": r.content,
            "received_qty": r.received_qty or 0,
            "status": r.status,
            "remarks": r.remarks,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })
    return {"success": True, "data": items, "total": total}


def _order_to_dict(r: WeldingOrder, supplier_name: Optional[str] = None) -> dict:
    return {
        "id": r.id,
        "order_no": r.order_no,
        "order_date": r.order_date.isoformat() if r.order_date else None,
        "supplier_cd": r.supplier_cd,
        "supplier_name": supplier_name or r.supplier_cd,
        "product_cd": r.product_cd,
        "product_name": r.product_name,
        "specification": r.specification,
        "welding_type": r.welding_type,
        "welding_points": r.welding_points or 0,
        "quantity": r.quantity,
        "unit": r.unit,
        "unit_price": float(r.unit_price) if r.unit_price is not None else 0,
        "delivery_date": r.delivery_date.isoformat() if r.delivery_date else None,
        "delivery_location": r.delivery_location,
        "category": r.category,
        "content": r.content,
        "received_qty": r.received_qty or 0,
        "status": r.status,
        "remarks": r.remarks,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _order_no_prefix(supplier_cd: str, order_date: date) -> str:
    """注文番号プレフィックス: 外注先コード + YYYYMMDD-（例: OS-00520260223-）"""
    return f"{supplier_cd}{order_date.strftime('%Y%m%d')}-"


async def _get_next_order_no_seq(db: AsyncSession, prefix: str) -> int:
    """同一プレフィックスでの最大連番を取得し、次の連番を返す（1始まり）"""
    q = select(func.max(WeldingOrder.order_no)).where(WeldingOrder.order_no.like(f"{prefix}%"))
    r = await db.execute(q)
    max_no = r.scalar_one_or_none()  # 标量：最大 order_no 字符串，如 "OS-00520260223-01"
    if not max_no:
        return 1
    try:
        seq_part = str(max_no).split("-")[-1]
        return int(seq_part) + 1
    except (IndexError, ValueError):
        return 1


async def _generate_order_no(db: AsyncSession, supplier_cd: str, order_date: date) -> str:
    """生成注文番号: 外注先コード + YYYYMMDD + - + 2桁連番（例: OS-00520260223-01）"""
    prefix = _order_no_prefix(supplier_cd, order_date)
    seq = await _get_next_order_no_seq(db, prefix)
    return f"{prefix}{seq:02d}"


def _receiving_no_prefix(receiving_date: date) -> str:
    """受入番号プレフィックス: WR-YYYYMMDD-（例: WR-20260225-）"""
    return f"WR-{receiving_date.strftime('%Y%m%d')}-"


async def _get_next_receiving_no_seq(db: AsyncSession, receiving_date: date) -> int:
    """同一日付での受入番号最大連番を取得し、次の連番を返す（1始まり）。形式 WR-YYYYMMDD-NN"""
    prefix = _receiving_no_prefix(receiving_date)
    q = select(func.max(WeldingReceiving.receiving_no)).where(
        WeldingReceiving.receiving_no.like(f"{prefix}%")
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
    """生成受入番号: WR-YYYYMMDD-NN（例: WR-20260225-01）"""
    prefix = _receiving_no_prefix(receiving_date)
    seq = await _get_next_receiving_no_seq(db, receiving_date)
    return f"{prefix}{seq:02d}"


@router.get("/orders/by-order-no")
async def get_welding_orders_by_order_no(
    order_no: Optional[str] = Query(None, alias="order_no"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """注文番号で溶接注文一覧取得"""
    if not order_no or not order_no.strip():
        return {"success": True, "data": []}
    q = select(WeldingOrder).where(WeldingOrder.order_no == order_no.strip()).order_by(WeldingOrder.id)
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
    items = [_order_to_dict(r, supplier_names.get(r.supplier_cd)) for r in rows]
    return {"success": True, "data": items}


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


@router.post("/orders")
async def create_welding_order(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接注文新規登録（order_no は自動採番: 外注先コード+注文日+2桁連番）"""
    try:
        order_date_val = body.get("order_date") or body.get("orderDate")
        if not order_date_val:
            raise HTTPException(status_code=400, detail="order_date は必須です")
        # 前端可能传 Date 或 ISO 字符串，统一取前10位
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
        welding_type = str(body.get("welding_type") or body.get("weldingType") or "溶接")[:50]
        welding_points = int(body.get("welding_points") or body.get("weldingPoints") or 0)
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
            delivery_location = str(delivery_location)[:100]
        category = body.get("category")
        if category is not None:
            category = str(category)[:50]
        content = body.get("content")
        specification = body.get("specification")
        if specification is not None:
            specification = str(specification)[:200]
        remarks = body.get("remarks")
        created_by = str(body.get("created_by") or "system")[:50]

        row = WeldingOrder(
            order_no=order_no,
            order_date=order_date,
            supplier_cd=supplier_cd,
            product_cd=product_cd,
            product_name=product_name or None,
            specification=specification,
            welding_type=welding_type,
            welding_points=welding_points,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            delivery_date=delivery_date,
            delivery_location=delivery_location,
            category=category,
            content=content,
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
async def update_welding_order(
    order_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接注文更新"""
    q = select(WeldingOrder).where(WeldingOrder.id == order_id)
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
        ("specification", "specification"),
        ("welding_type", "welding_type"),
        ("weldingType", "welding_type"),
        ("welding_points", "welding_points"),
        ("weldingPoints", "welding_points"),
        ("quantity", "quantity"),
        ("unit_price", "unit_price"),
        ("unitPrice", "unit_price"),
        ("delivery_date", "delivery_date"),
        ("deliveryDate", "delivery_date"),
        ("delivery_location", "delivery_location"),
        ("deliveryLocation", "delivery_location"),
        ("category", "category"),
        ("content", "content"),
        ("remarks", "remarks"),
        ("status", "status"),
    ]:
        if key in body and body[key] is not None:
            setattr(row, attr, body[key])
    await db.flush()
    await db.refresh(row)
    return {"success": True, "data": _order_to_dict(row)}


@router.post("/orders/batch")
async def create_welding_orders_batch(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接注文一括新規登録（order_no: 外注先コード+注文日+2桁連番、同一外注先・同一注文日で連番）"""
    orders_payload = body.get("orders") or body.get("Orders") or []
    if not orders_payload:
        raise HTTPException(status_code=400, detail="orders は必須です")
    created = []
    try:
        for i, item in enumerate(orders_payload):
            order_date_val = item.get("order_date") or item.get("orderDate")
            if not order_date_val:
                raise HTTPException(status_code=400, detail=f"orders[{i}].order_date は必須です")
            if hasattr(order_date_val, "isoformat"):
                order_date_val = order_date_val.isoformat()[:10]
            else:
                order_date_val = str(order_date_val)[:10] if order_date_val else ""
            order_date = _parse_date(order_date_val)
            if not order_date:
                raise HTTPException(status_code=400, detail=f"orders[{i}].order_date の形式が不正です")
            supplier_cd = str(item.get("supplier_cd") or item.get("supplierCd") or "").strip()
            if not supplier_cd:
                raise HTTPException(status_code=400, detail=f"orders[{i}].supplier_cd は必須です")
            prefix = _order_no_prefix(supplier_cd, order_date)
            seq = await _get_next_order_no_seq(db, prefix)
            order_no = f"{prefix}{seq:02d}"
            product_cd = str(item.get("product_cd") or item.get("productCode") or "").strip()
            if not product_cd:
                raise HTTPException(status_code=400, detail=f"orders[{i}].product_cd は必須です")
            product_name = str(item.get("product_name") or item.get("productName") or "")[:200]
            welding_type = str(item.get("welding_type") or item.get("weldingType") or "溶接")[:50]
            welding_points = int(item.get("welding_points") or item.get("weldingPoints") or 0)
            quantity = int(float(item.get("quantity") or 0))
            if quantity <= 0:
                raise HTTPException(status_code=400, detail=f"orders[{i}].quantity は1以上で指定してください")
            unit = str(item.get("unit") or "個")[:10]
            unit_price = float(item.get("unit_price") or item.get("unitPrice") or 0)
            delivery_val = item.get("delivery_date") or item.get("deliveryDate")
            if hasattr(delivery_val, "isoformat"):
                delivery_val = delivery_val.isoformat()[:10]
            delivery_date = _parse_date(delivery_val)
            delivery_location = item.get("delivery_location") or item.get("deliveryLocation")
            if delivery_location is not None:
                delivery_location = str(delivery_location)[:100]
            category = item.get("category")
            if category is not None:
                category = str(category)[:50]
            content = item.get("content")
            specification = item.get("specification")
            if specification is not None:
                specification = str(specification)[:200]
            remarks = item.get("remarks")
            created_by = str(item.get("created_by") or "system")[:50]

            row = WeldingOrder(
                order_no=order_no,
                order_date=order_date,
                supplier_cd=supplier_cd,
                product_cd=product_cd,
                product_name=product_name or None,
                specification=specification,
                welding_type=welding_type,
                welding_points=welding_points,
                quantity=quantity,
                unit=unit,
                unit_price=unit_price,
                delivery_date=delivery_date,
                delivery_location=delivery_location,
                category=category,
                content=content,
                received_qty=0,
                status="pending",
                remarks=remarks,
                created_by=created_by,
            )
            db.add(row)
            await db.flush()
            await db.refresh(row)
            created.append(_order_to_dict(row))
        return {"success": True, "data": created, "count": len(created)}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{order_id}")
async def delete_welding_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接注文削除。該当注文の stock_transaction_logs も同時に削除する。"""
    q = select(WeldingOrder).where(WeldingOrder.id == order_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="注文が見つかりません")
    order_no = (row.order_no or "").strip()
    # 該当注文から生成された在庫取引ログを削除（order_no または notes が一致するレコード。トリガーで notes に注文番号が入る場合あり）
    if order_no:
        await db.execute(
            text(
                "DELETE FROM stock_transaction_logs WHERE source_file = 'outsourcing_welding_orders' "
                "AND (order_no = :ono OR notes = :ono)"
            ),
            {"ono": order_no},
        )
    await db.delete(row)
    await db.flush()
    return {"success": True, "message": "削除しました"}


@router.post("/orders/batch-order")
async def batch_order_welding(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """注文書発行：対象 id のうち status='pending' の注文のみ status を 'ordered' に更新し、
    該当注文ごとに outsourcing_welding_receivings に 1 件の受入レコード（待受入）を自動作成する。"""
    raw_ids = body.get("ids") or body.get("order_ids") or body.get("orderIds") or []
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
        # 手動で IN 句を組み立て（expanding 依存を避け、notes 等の誤列を一切含めない）
        placeholders = ", ".join([f":id_{i}" for i in range(len(order_ids))])
        sql = (
            "UPDATE outsourcing_welding_orders SET status = :status "
            f"WHERE id IN ({placeholders}) AND status = 'pending'"
        )
        params = {"status": "ordered", **{f"id_{i}": order_ids[i] for i in range(len(order_ids))}}
        result = await db.execute(text(sql), params)
        count = result.rowcount if result.rowcount is not None else 0

        # 更新された注文（status='ordered'）を取得し、受入が未作成の注文のみ受入レコードを 1 件作成
        q_orders = select(WeldingOrder).where(
            WeldingOrder.id.in_(order_ids),
            WeldingOrder.status == "ordered",
        )
        res_orders = await db.execute(q_orders)
        orders_updated = list(res_orders.scalars().all())
        existing = await db.execute(
            select(WeldingReceiving.order_id).where(WeldingReceiving.order_id.in_(order_ids))
        )
        existing_order_ids = {r[0] for r in existing.all()}
        today = date.today()
        for order in orders_updated:
            if order.id in existing_order_ids:
                continue
            receiving_date = order.delivery_date if order.delivery_date else today
            receiving_no = await _generate_receiving_no(db, receiving_date)
            row = WeldingReceiving(
                receiving_no=receiving_no,
                receiving_date=receiving_date,
                order_id=order.id,
                order_no=order.order_no,
                supplier_cd=order.supplier_cd,
                product_cd=order.product_cd,
                product_name=order.product_name,
                welding_type=order.welding_type,
                welding_points=order.welding_points or 0,
                delivery_location=order.delivery_location,
                category=order.category,
                content=order.content,
                specification=order.specification,
                order_qty=order.quantity,
                receiving_qty=0,
                good_qty=0,
                defect_qty=0,
                status="pending",
                inspector=None,
                remarks=None,
            )
            db.add(row)
            existing_order_ids.add(order.id)
            await db.flush()  # 次の _generate_receiving_no で同日連番を正しく採番するため

        return {"success": True, "message": f"{count}件の注文を発注しました"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/receivings/products")
async def get_welding_receiving_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接注文・受入で使用されている品名一覧（重複排除）"""
    # 注文テーブルから product_name の distinct
    q = select(distinct(WeldingOrder.product_name)).where(
        WeldingOrder.product_name.isnot(None),
        WeldingOrder.product_name != "",
    ).order_by(WeldingOrder.product_name)
    result = await db.execute(q)
    names = [row[0] for row in result.all() if row[0]]
    # 受入テーブルからも追加
    q2 = select(distinct(WeldingReceiving.product_name)).where(
        WeldingReceiving.product_name.isnot(None),
        WeldingReceiving.product_name != "",
    )
    result2 = await db.execute(q2)
    for row in result2.all():
        if row[0] and row[0] not in names:
            names.append(row[0])
    names.sort()
    return {"success": True, "data": names}


@router.get("/stock")
async def get_welding_stock(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
    supplierId: Optional[int] = Query(None, alias="supplierId"),
    productCode: Optional[str] = Query(None, alias="productCode"),
    stockStatus: Optional[str] = Query(None, alias="stockStatus"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注溶接在庫一覧（outsourcing_welding_stock + 外注先名は outsourcing_suppliers と JOIN）"""
    q = (
        select(WeldingStock, OutsourcingSupplier.supplier_name, OutsourcingSupplier.id.label("supplier_id"))
        .join(OutsourcingSupplier, WeldingStock.supplier_cd == OutsourcingSupplier.supplier_cd)
    )
    if supplierId is not None:
        q = q.where(OutsourcingSupplier.id == supplierId)
    if productCode and productCode.strip():
        q = q.where(WeldingStock.product_cd.ilike(f"%{productCode.strip()}%"))
    if stockStatus:
        if stockStatus == "empty":
            q = q.where(WeldingStock.ordered_qty - WeldingStock.used_qty <= 0)
        elif stockStatus == "low":
            q = q.where(
                (WeldingStock.ordered_qty - WeldingStock.used_qty > 0)
                & (WeldingStock.ordered_qty - WeldingStock.used_qty < WeldingStock.min_stock)
            )
        elif stockStatus == "normal":
            q = q.where(
                (WeldingStock.ordered_qty - WeldingStock.used_qty > 0)
                & ((WeldingStock.ordered_qty - WeldingStock.used_qty) >= WeldingStock.min_stock)
            )
    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    q = q.order_by(WeldingStock.product_cd, WeldingStock.supplier_cd, WeldingStock.welding_type)
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
            "welding_type": st.welding_type or "",
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
async def get_welding_receivings(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    supplierId: Optional[str] = Query(None),
    productName: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接受入一覧（ページネーション・日付・条件絞り）"""
    q = select(WeldingReceiving)
    if startDate:
        q = q.where(WeldingReceiving.receiving_date >= startDate)
    if endDate:
        q = q.where(WeldingReceiving.receiving_date <= endDate)
    if productName:
        q = q.where(WeldingReceiving.product_name == productName)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                WeldingReceiving.receiving_no.ilike(kw),
                WeldingReceiving.order_no.ilike(kw),
                WeldingReceiving.product_cd.ilike(kw),
                WeldingReceiving.product_name.ilike(kw),
            )
        )
    # supplierId: 前端传的是 supplier 的 value（可能是 id 或 supplier_cd）
    # 我们表里只有 supplier_cd，需要先查 supplier_cd；若 value 是 id 则从 suppliers 查
    if supplierId:
        try:
            sid = int(supplierId)
            sq = select(OutsourcingSupplier.supplier_cd).where(OutsourcingSupplier.id == sid)
            sr = await db.execute(sq)
            sc = sr.scalar_one_or_none()
            if sc:
                q = q.where(WeldingReceiving.supplier_cd == sc)
        except ValueError:
            q = q.where(WeldingReceiving.supplier_cd == supplierId)

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    q = q.order_by(WeldingReceiving.receiving_date.desc(), WeldingReceiving.id.desc())
    offset = (page - 1) * pageSize
    q = q.offset(offset).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()

    # 外注先名を取得（supplier_cd -> name）
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
async def create_welding_receiving(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接受入新規登録（receiving_no 未指定時は WR-YYYYMMDD-NN 形式を自動作成）"""
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

    # 注文取得
    oq = select(WeldingOrder).where(WeldingOrder.id == order_id)
    or_res = await db.execute(oq)
    order_row = or_res.scalar_one_or_none()
    if not order_row:
        raise HTTPException(status_code=404, detail="注文が見つかりません")

    # 受入番号未指定時は WR-YYYYMMDD-NN 形式を自動作成（例: WR-20260225-01）
    if not receiving_no or not str(receiving_no).strip():
        if hasattr(receiving_date, "isoformat"):
            rec_date = receiving_date
        else:
            rec_date = _parse_date(str(receiving_date)[:10])
        if not rec_date:
            raise HTTPException(status_code=400, detail="受入日の形式が不正です（YYYY-MM-DD）")
        receiving_no = await _generate_receiving_no(db, rec_date)

    # 重複受入番号チェック（手入力で指定した場合）
    ex = await db.execute(select(WeldingReceiving).where(WeldingReceiving.receiving_no == receiving_no))
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="受入番号が既に存在します")

    row = WeldingReceiving(
        receiving_no=receiving_no,
        receiving_date=receiving_date,
        order_id=order_id,
        order_no=order_row.order_no,
        supplier_cd=order_row.supplier_cd,
        product_cd=order_row.product_cd,
        product_name=order_row.product_name,
        welding_type=order_row.welding_type,
        welding_points=order_row.welding_points or 0,
        delivery_location=order_row.delivery_location,
        category=order_row.category,
        content=order_row.content,
        specification=order_row.specification,
        order_qty=order_row.quantity,
        receiving_qty=receiving_qty,
        good_qty=good_qty,
        defect_qty=defect_qty,
        defect_reason=body.get("defect_reason") or body.get("defectReason"),
        status="pending",
        inspector=body.get("inspector"),
        remarks=body.get("remarks"),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return {"success": True, "data": _receiving_to_dict(row)}


@router.put("/receivings/{receiving_id}")
async def update_welding_receiving(
    receiving_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接受入更新"""
    q = select(WeldingReceiving).where(WeldingReceiving.id == receiving_id)
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
async def delete_welding_receiving(
    receiving_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接受入削除。削除後に該当注文の received_qty を再計算して更新する。"""
    q = select(WeldingReceiving).where(WeldingReceiving.id == receiving_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="受入が見つかりません")
    order_id = row.order_id
    await db.delete(row)
    await db.flush()
    # 該当注文の入庫数を再計算（残りの受入の good_qty 合計）
    subq = (
        select(func.coalesce(func.sum(WeldingReceiving.good_qty), 0))
        .where(WeldingReceiving.order_id == order_id)
    )
    r2 = await db.execute(subq)
    new_received = int(r2.scalar_one_or_none() or 0)
    oq = select(WeldingOrder).where(WeldingOrder.id == order_id)
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


# keyword 用の条件は SQLAlchemy で複数カラムに ilike をかける場合、各カラムが None でないことも必要
# 上記の where で (WeldingReceiving.product_name.ilike(kw) if ... else False) は不適切。or_ を使う