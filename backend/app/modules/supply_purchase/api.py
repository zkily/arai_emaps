"""備品購入 API：カタログ CRUD と発注ヘッダ/明細"""
import re
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_master_operation, require_purchase_operation
from app.modules.master.models import Supplier
from app.modules.supply_purchase.models import (
    SupplyItem,
    SupplyPurchaseOrder,
    SupplyPurchaseOrderLine,
)
from app.modules.supply_purchase.schemas import (
    SupplyItemCreate,
    SupplyItemUpdate,
    SupplyOrderCreate,
)

router = APIRouter()


def _dec(val: object) -> float:
    if val is None:
        return 0.0
    return float(val)


def _item_dict(row: SupplyItem, supplier_name: str = "") -> dict:
    return {
        "id": row.id,
        "item_cd": row.item_cd,
        "item_name": row.item_name,
        "specification": row.specification or "",
        "unit": row.unit or "個",
        "pack_qty": int(row.pack_qty or 1),
        "order_lot": int(row.order_lot or 1),
        "unit_price": _dec(row.unit_price),
        "supplier_cd": row.supplier_cd,
        "supplier_name": supplier_name or "",
        "is_discontinued": bool(row.is_discontinued),
        "remarks": row.remarks or "",
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _line_dict(row: SupplyPurchaseOrderLine) -> dict:
    return {
        "id": row.id,
        "line_no": row.line_no,
        "item_cd": row.item_cd,
        "item_name": row.item_name or "",
        "specification": row.specification or "",
        "unit": row.unit or "個",
        "pack_qty": int(row.pack_qty or 1),
        "order_lot": int(row.order_lot or 1),
        "order_qty": int(row.order_qty or 0),
        "unit_price": _dec(row.unit_price),
        "amount": _dec(row.amount),
    }


def _order_dict(row: SupplyPurchaseOrder, lines: list[SupplyPurchaseOrderLine] | None = None) -> dict:
    return {
        "id": row.id,
        "order_no": row.order_no,
        "order_date": row.order_date.isoformat() if row.order_date else None,
        "delivery_date": row.delivery_date.isoformat() if row.delivery_date else None,
        "supplier_cd": row.supplier_cd,
        "supplier_name": row.supplier_name or "",
        "status": row.status,
        "total_amount": _dec(row.total_amount),
        "remarks": row.remarks or "",
        "created_by": row.created_by or "",
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "lines": [_line_dict(x) for x in (lines or [])],
    }


async def _supplier_name(db: AsyncSession, supplier_cd: str) -> str:
    q = select(Supplier.supplier_name).where(Supplier.supplier_cd == supplier_cd)
    name = (await db.execute(q)).scalar_one_or_none()
    return (name or "").strip()


async def _supplier_name_map(db: AsyncSession, supplier_cds: set[str]) -> dict[str, str]:
    if not supplier_cds:
        return {}
    rows = (
        await db.execute(
            select(Supplier.supplier_cd, Supplier.supplier_name).where(
                Supplier.supplier_cd.in_(list(supplier_cds))
            )
        )
    ).all()
    return {cd: (name or "").strip() for cd, name in rows}


async def _next_order_no(db: AsyncSession, order_date: date) -> str:
    prefix = f"BH{order_date.strftime('%Y%m%d')}-"
    q = select(func.max(SupplyPurchaseOrder.order_no)).where(
        SupplyPurchaseOrder.order_no.like(f"{prefix}%")
    )
    max_no = (await db.execute(q)).scalar_one_or_none()
    seq = 1
    if max_no and len(str(max_no)) >= len(prefix) + 3:
        try:
            seq = int(str(max_no)[len(prefix) :]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:03d}"


_ITEM_CD_RE = re.compile(r"^B(\d+)$", re.IGNORECASE)


async def _next_item_cd(db: AsyncSession) -> str:
    """備品マスタ全体の最大 B#### から +1（例: B0005 → B0006）。"""
    rows = (await db.execute(select(SupplyItem.item_cd))).scalars().all()
    max_n = 0
    for cd in rows:
        m = _ITEM_CD_RE.match((cd or "").strip())
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"B{max_n + 1:04d}"


@router.get("/items")
async def list_supply_items(
    supplierCd: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    includeDiscontinued: bool = Query(False),
    discontinuedStatus: Optional[str] = Query(None, description="1=終息のみ / 0=有効のみ"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先別備品カタログ一覧。購入画面は includeDiscontinued=false で終息を除外。"""
    _ = current_user
    q = select(SupplyItem)
    conditions = []
    if supplierCd and supplierCd.strip():
        conditions.append(SupplyItem.supplier_cd == supplierCd.strip())
    if discontinuedStatus == "1":
        conditions.append(SupplyItem.is_discontinued.is_(True))
    elif discontinuedStatus == "0" or not includeDiscontinued:
        conditions.append(SupplyItem.is_discontinued.is_(False))
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                SupplyItem.item_cd.like(kw),
                SupplyItem.item_name.like(kw),
                SupplyItem.specification.like(kw),
                SupplyItem.supplier_cd.like(kw),
            )
        )
    if conditions:
        q = q.where(*conditions)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(SupplyItem.supplier_cd, SupplyItem.item_cd).offset((page - 1) * pageSize).limit(
        pageSize
    )
    rows = (await db.execute(q)).scalars().all()
    name_map = await _supplier_name_map(db, {r.supplier_cd for r in rows if r.supplier_cd})
    return {
        "success": True,
        "data": {
            "list": [_item_dict(r, name_map.get(r.supplier_cd, "")) for r in rows],
            "total": total,
        },
    }


@router.get("/items/next-cd")
async def get_next_supply_item_cd(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    return {"success": True, "data": {"item_cd": await _next_item_cd(db)}}


@router.post("/items")
async def create_supply_item(
    body: SupplyItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("create")),
):
    supplier_cd = body.supplier_cd.strip()
    item_cd = (body.item_cd or "").strip() or await _next_item_cd(db)
    name = await _supplier_name(db, supplier_cd)
    if not name:
        raise HTTPException(status_code=400, detail="仕入先マスタに該当する仕入先CDがありません")
    for _ in range(8):
        exists = (
            await db.execute(
                select(SupplyItem.id).where(
                    SupplyItem.supplier_cd == supplier_cd, SupplyItem.item_cd == item_cd
                )
            )
        ).scalar_one_or_none()
        if not exists:
            break
        item_cd = await _next_item_cd(db)
    else:
        raise HTTPException(status_code=400, detail="備品CDの採番に失敗しました。再試行してください")
    row = SupplyItem(
        item_cd=item_cd,
        item_name=body.item_name.strip(),
        specification=(body.specification or "").strip() or None,
        unit=(body.unit or "個").strip() or "個",
        pack_qty=body.pack_qty,
        order_lot=body.order_lot,
        unit_price=body.unit_price,
        supplier_cd=supplier_cd,
        is_discontinued=bool(body.is_discontinued),
        remarks=(body.remarks or "").strip() or None,
        created_by=getattr(current_user, "username", None) or str(getattr(current_user, "id", "")),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _item_dict(row, name)}


@router.put("/items/{item_id}")
async def update_supply_item(
    item_id: int,
    body: SupplyItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    _ = current_user
    row = (await db.execute(select(SupplyItem).where(SupplyItem.id == item_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="備品が見つかりません")
    data = body.model_dump(exclude_unset=True)
    if "supplier_cd" in data and data["supplier_cd"]:
        new_supplier = str(data["supplier_cd"]).strip()
        name = await _supplier_name(db, new_supplier)
        if not name:
            raise HTTPException(status_code=400, detail="仕入先マスタに該当する仕入先CDがありません")
        data["supplier_cd"] = new_supplier
    if "item_cd" in data and data["item_cd"]:
        new_cd = str(data["item_cd"]).strip()
        target_supplier = str(data.get("supplier_cd") or row.supplier_cd)
        dup = (
            await db.execute(
                select(SupplyItem.id).where(
                    SupplyItem.supplier_cd == target_supplier,
                    SupplyItem.item_cd == new_cd,
                    SupplyItem.id != item_id,
                )
            )
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(status_code=400, detail="同じ仕入先に同じ備品CDが既に登録されています")
        data["item_cd"] = new_cd
    elif "supplier_cd" in data:
        dup = (
            await db.execute(
                select(SupplyItem.id).where(
                    SupplyItem.supplier_cd == data["supplier_cd"],
                    SupplyItem.item_cd == row.item_cd,
                    SupplyItem.id != item_id,
                )
            )
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(status_code=400, detail="同じ仕入先に同じ備品CDが既に登録されています")
    for k, v in data.items():
        if k in ("item_name", "specification", "unit", "remarks") and isinstance(v, str):
            v = v.strip() or None
            if k in ("item_name", "unit") and not v:
                continue
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    name = await _supplier_name(db, row.supplier_cd)
    return {"success": True, "data": _item_dict(row, name)}


@router.delete("/items/{item_id}")
async def delete_supply_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("delete")),
):
    _ = current_user
    row = (await db.execute(select(SupplyItem).where(SupplyItem.id == item_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="備品が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}


@router.get("/orders")
async def list_supply_orders(
    supplierCd: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    q = select(SupplyPurchaseOrder)
    if supplierCd and supplierCd.strip():
        q = q.where(SupplyPurchaseOrder.supplier_cd == supplierCd.strip())
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                SupplyPurchaseOrder.order_no.like(kw),
                SupplyPurchaseOrder.supplier_name.like(kw),
            )
        )
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = (
        q.order_by(SupplyPurchaseOrder.order_date.desc(), SupplyPurchaseOrder.id.desc())
        .offset((page - 1) * pageSize)
        .limit(pageSize)
    )
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": {"list": [_order_dict(r) for r in rows], "total": total}}


@router.get("/orders/{order_id}")
async def get_supply_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    row = (
        await db.execute(select(SupplyPurchaseOrder).where(SupplyPurchaseOrder.id == order_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    lines = (
        await db.execute(
            select(SupplyPurchaseOrderLine)
            .where(SupplyPurchaseOrderLine.order_id == order_id)
            .order_by(SupplyPurchaseOrderLine.line_no)
        )
    ).scalars().all()
    return {"success": True, "data": _order_dict(row, list(lines))}


@router.post("/orders")
async def create_supply_order(
    body: SupplyOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("create")),
):
    supplier_cd = body.supplier_cd.strip()
    supplier_name = await _supplier_name(db, supplier_cd)
    if not supplier_name:
        raise HTTPException(status_code=400, detail="仕入先マスタに該当する仕入先CDがありません")

    item_ids = [ln.item_id for ln in body.lines]
    items = (
        await db.execute(select(SupplyItem).where(SupplyItem.id.in_(item_ids)))
    ).scalars().all()
    item_map = {r.id: r for r in items}
    if len(item_map) != len(set(item_ids)):
        raise HTTPException(status_code=400, detail="存在しない備品が含まれています")
    for it in items:
        if it.supplier_cd != supplier_cd:
            raise HTTPException(status_code=400, detail="選択した備品が仕入先と一致しません")
        if it.is_discontinued:
            raise HTTPException(status_code=400, detail=f"終息品は発注できません（{it.item_cd}）")

    order_no = await _next_order_no(db, body.order_date)
    header = SupplyPurchaseOrder(
        order_no=order_no,
        order_date=body.order_date,
        delivery_date=body.delivery_date,
        supplier_cd=supplier_cd,
        supplier_name=supplier_name,
        status="ordered",
        remarks=(body.remarks or "").strip() or None,
        created_by=getattr(current_user, "username", None) or str(getattr(current_user, "id", "")),
    )
    db.add(header)
    await db.flush()

    total = Decimal("0")
    for i, ln in enumerate(body.lines, start=1):
        it = item_map[ln.item_id]
        price = Decimal(str(it.unit_price or 0))
        amount = price * ln.order_qty
        total += amount
        db.add(
            SupplyPurchaseOrderLine(
                order_id=header.id,
                line_no=i,
                item_cd=it.item_cd,
                item_name=it.item_name,
                specification=it.specification,
                unit=it.unit,
                pack_qty=int(it.pack_qty or 1),
                order_lot=int(it.order_lot or 1),
                order_qty=ln.order_qty,
                unit_price=price,
                amount=amount,
            )
        )
    header.total_amount = total
    await db.commit()
    await db.refresh(header)
    lines = (
        await db.execute(
            select(SupplyPurchaseOrderLine)
            .where(SupplyPurchaseOrderLine.order_id == header.id)
            .order_by(SupplyPurchaseOrderLine.line_no)
        )
    ).scalars().all()
    return {"success": True, "data": _order_dict(header, list(lines))}


@router.post("/orders/{order_id}/cancel")
async def cancel_supply_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("delete")),
):
    _ = current_user
    row = (
        await db.execute(select(SupplyPurchaseOrder).where(SupplyPurchaseOrder.id == order_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    if row.status == "cancelled":
        raise HTTPException(status_code=400, detail="既にキャンセル済みです")
    row.status = "cancelled"
    await db.commit()
    return {"success": True, "message": "キャンセルしました"}
