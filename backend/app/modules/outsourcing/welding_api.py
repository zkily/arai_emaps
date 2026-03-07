"""
外注溶接：注文・受入 API（outsourcing_welding_orders / outsourcing_welding_receivings）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, or_
from typing import Optional, Any
from datetime import date, datetime

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.outsourcing.models import WeldingOrder, WeldingReceiving, OutsourcingSupplier

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

    q = q.order_by(WeldingOrder.order_date.desc(), WeldingOrder.id.desc())
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


def _order_no_prefix() -> str:
    """注文番号プレフィックス: WO + YYYYMMDD-"""
    return f"WO{date.today().strftime('%Y%m%d')}-"


async def _get_next_order_no_seq(db: AsyncSession, prefix: str) -> int:
    """当日の最大連番を1回だけ取得し、次の連番を返す（1始まり）"""
    q = select(func.max(WeldingOrder.order_no)).where(WeldingOrder.order_no.like(f"{prefix}%"))
    r = await db.execute(q)
    max_no = r.scalar_one_or_none()
    if not max_no or not max_no[0]:
        return 1
    try:
        return int(max_no[0].split("-")[-1]) + 1
    except (IndexError, ValueError):
        return 1


async def _generate_order_no(db: AsyncSession) -> str:
    """生成注文番号: WO + YYYYMMDD + - + 4桁連番（単体登録用）"""
    prefix = _order_no_prefix()
    seq = await _get_next_order_no_seq(db, prefix)
    return f"{prefix}{seq:04d}"


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
    """溶接注文新規登録（order_no は自動採番）"""
    try:
        order_no = await _generate_order_no(db)
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
    """溶接注文一括新規登録（1リクエストで複数件、order_no を先に連番で採番してから一括INSERT）"""
    orders_payload = body.get("orders") or body.get("Orders") or []
    if not orders_payload:
        raise HTTPException(status_code=400, detail="orders は必須です")
    created = []
    try:
        # 先に当日の次の連番を1回だけ取得し、ループでは seq+i で採番（同一トランザクション内の未コミットを参照しない）
        prefix = _order_no_prefix()
        start_seq = await _get_next_order_no_seq(db, prefix)
        for i, item in enumerate(orders_payload):
            order_no = f"{prefix}{start_seq + i:04d}"
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
    """溶接注文削除"""
    q = select(WeldingOrder).where(WeldingOrder.id == order_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="注文が見つかりません")
    await db.delete(row)
    await db.flush()
    return {"success": True, "message": "削除しました"}


@router.post("/orders/batch-order")
async def batch_order_welding(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接注文一括発注（指定IDの status を ordered に更新）"""
    order_ids = body.get("order_ids") or body.get("orderIds") or []
    if not order_ids:
        return {"success": True, "message": "対象がありません"}
    q = select(WeldingOrder).where(WeldingOrder.id.in_(order_ids))
    result = await db.execute(q)
    rows = result.scalars().all()
    for row in rows:
        row.status = "ordered"
    await db.flush()
    return {"success": True, "message": f"{len(rows)}件を発注済に更新しました"}


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
    """溶接受入新規登録"""
    order_id = body.get("order_id") or body.get("orderId")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id は必須です")
    order_no = body.get("order_no") or body.get("orderNo") or ""
    receiving_no = body.get("receiving_no") or body.get("receivingNo")
    if not receiving_no:
        raise HTTPException(status_code=400, detail="受入番号は必須です")
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

    # 重複受入番号チェック
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


# keyword 用の条件は SQLAlchemy で複数カラムに ilike をかける場合、各カラムが None でないことも必要
# 上記の where で (WeldingReceiving.product_name.ilike(kw) if ... else False) は不適切。or_ を使う