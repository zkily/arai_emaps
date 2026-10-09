"""補給品在庫台帳 API"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, BeforeValidator, Field, field_validator
from sqlalchemy import case, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_inventory_operation
from app.modules.database.models import ProductionSummary
from app.modules.erp.models import OrderMonthly
from app.modules.erp.stock_transaction_log_models import StockTransactionLog
from app.modules.erp.supply_part_models import (
    SupplyPartLocation,
    SupplyPartStock,
    SupplyPartTransaction,
)
from app.modules.master.models import Destination, Product

router = APIRouter(prefix="/supply-parts", tags=["SupplyParts"])

TXN_PRODUCTION_IN = "production_in"
TXN_SHIPMENT_OUT = "shipment_out"
TXN_ADJUST = "adjust"
TXN_TRANSFER_IN = "transfer_in"
TXN_MANUAL_IN = "manual_in"
SOURCE_TRANSFER = "transfer"
SOURCE_MANUAL = "manual"
SUPPLY_PRODUCT_TYPE = "補給品"
# 振替時に在庫取引記録へ登録する製品倉庫の保留（保留更新で倉庫保留に集計され、倉庫在庫から差し引かれる）
STOCK_LOG_TYPE = "製品"
STOCK_LOG_HOLD = "保留"
STOCK_LOG_LOCATION = "製品倉庫"
STOCK_LOG_PROCESS = "KT13"
STOCK_LOG_UNIT = "本"
STOCK_LOG_SOURCE = "補給品へ振替"
# 最終出庫（未出庫なら登録日）からこの日数を超えて在庫が残っていれば長期滞留
STAGNANT_DAYS = 365
# 月平均出荷は対象月を含む直近この月数の受注確定本数で計算する
DEMAND_MONTHS = 6
QUALITY_STATUSES = ("良好", "錆", "汚れ", "その他")
QUALITY_GOOD = QUALITY_STATUSES[0]


def _quality_status(v: Optional[str]) -> str:
    text = (v or "").strip() or QUALITY_GOOD
    if text not in QUALITY_STATUSES:
        raise ValueError(f"品質状態は {' / '.join(QUALITY_STATUSES)} から選択してください")
    return text


QualityStatus = Annotated[str, BeforeValidator(_quality_status)]


class SupplyPartManualCreate(BaseModel):
    product_cd: str
    product_name: str
    product_alias: Optional[str] = None
    part_number: Optional[str] = None
    destination_cd: Optional[str] = None
    destination_name: Optional[str] = None
    opening_qty: int = Field(ge=0)
    storage_location: str
    shelf_no: Optional[str] = None
    keeper: Optional[str] = None
    safety_stock: int = Field(default=0, ge=0)
    quality_status: QualityStatus = QUALITY_GOOD
    note: Optional[str] = None

    @field_validator("product_cd", "product_name", "storage_location")
    @classmethod
    def _required_text(cls, v: str) -> str:
        text = (v or "").strip()
        if not text:
            raise ValueError("必須項目です")
        return text


class SupplyPartTransferBody(BaseModel):
    product_cd: str
    storage_location: str
    product_alias: Optional[str] = None
    part_number: Optional[str] = None
    destination_cd: Optional[str] = None
    destination_name: Optional[str] = None
    shelf_no: Optional[str] = None
    keeper: Optional[str] = None
    safety_stock: int = Field(default=0, ge=0)
    quality_status: QualityStatus = QUALITY_GOOD
    note: Optional[str] = None

    @field_validator("product_cd", "storage_location")
    @classmethod
    def _required_text(cls, v: str) -> str:
        text = (v or "").strip()
        if not text:
            raise ValueError("必須項目です")
        return text


class SupplyPartUpdate(BaseModel):
    product_name: Optional[str] = None
    product_alias: Optional[str] = None
    part_number: Optional[str] = None
    destination_cd: Optional[str] = None
    destination_name: Optional[str] = None
    storage_location: str
    shelf_no: Optional[str] = None
    keeper: Optional[str] = None
    safety_stock: int = Field(default=0, ge=0)
    quality_status: QualityStatus = QUALITY_GOOD
    note: Optional[str] = None

    @field_validator("storage_location")
    @classmethod
    def _location(cls, v: str) -> str:
        text = (v or "").strip()
        if not text:
            raise ValueError("保管場所は必須です")
        return text


class SupplyPartTxnBody(BaseModel):
    txn_type: str
    quantity: int
    occurred_date: date
    note: Optional[str] = None

    @field_validator("txn_type")
    @classmethod
    def _txn_type(cls, v: str) -> str:
        text = (v or "").strip()
        if text not in (TXN_PRODUCTION_IN, TXN_SHIPMENT_OUT, TXN_ADJUST):
            raise ValueError("txn_type が不正です")
        return text


class SupplyPartLocationBody(BaseModel):
    name: str
    sort_order: int = 0
    is_active: bool = True
    note: Optional[str] = None

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        text = (v or "").strip()
        if not text:
            raise ValueError("保管場所名は必須です")
        if len(text) > 100:
            raise ValueError("保管場所名は 100 文字以内です")
        return text


def _clean(value: Optional[str], limit: int | None = None) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if limit is not None:
        return text[:limit]
    return text


def _stock_to_dict(
    row: SupplyPartStock,
    shipment: tuple[int, int] | None = None,
    metrics: dict | None = None,
) -> dict:
    confirmed, forecast = shipment or (0, 0)
    on_hand = int(row.on_hand_qty or 0)
    safety = int(row.safety_stock or 0)
    return {
        **(metrics or {}),
        "id": int(row.id),
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "product_alias": row.product_alias,
        "part_number": row.part_number,
        "destination_cd": row.destination_cd,
        "destination_name": row.destination_name,
        "storage_location": row.storage_location or "",
        "shelf_no": row.shelf_no,
        "keeper": row.keeper,
        "safety_stock": safety,
        "on_hand_qty": on_hand,
        "next_production_date": (
            row.next_production_date.isoformat() if row.next_production_date else None
        ),
        "next_production_qty": int(row.next_production_qty or 0),
        "quality_status": row.quality_status or QUALITY_GOOD,
        "note": row.note,
        "source": row.source,
        "shipment_planned": confirmed,
        "forecast_units": forecast,
        "balance": on_hand - confirmed,
        "below_safety": safety > 0 and on_hand < safety,
        "short_of_shipment": on_hand < confirmed,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _txn_to_dict(row: SupplyPartTransaction) -> dict:
    return {
        "id": int(row.id),
        "stock_id": int(row.stock_id),
        "product_cd": row.product_cd,
        "txn_type": row.txn_type,
        "quantity": int(row.quantity or 0),
        "balance_after": int(row.balance_after or 0),
        "occurred_date": row.occurred_date.isoformat() if row.occurred_date else None,
        "note": row.note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


async def _destination_name(db: AsyncSession, destination_cd: Optional[str]) -> Optional[str]:
    code = _clean(destination_cd, 50)
    if not code:
        return None
    res = await db.execute(
        select(Destination.destination_name).where(Destination.destination_cd == code)
    )
    name = res.scalar_one_or_none()
    return _clean(name, 100) if name else None


async def _load_product(db: AsyncSession, product_cd: str) -> Product | None:
    res = await db.execute(select(Product).where(Product.product_cd == product_cd))
    return res.scalar_one_or_none()


async def _existing_stock(db: AsyncSession, product_cd: str) -> SupplyPartStock | None:
    res = await db.execute(select(SupplyPartStock).where(SupplyPartStock.product_cd == product_cd))
    return res.scalar_one_or_none()


async def _shipment_map(
    db: AsyncSession, product_cds: list[str], year: int, month: int
) -> dict[str, tuple[int, int]]:
    if not product_cds:
        return {}
    stmt = (
        select(
            OrderMonthly.product_cd,
            func.coalesce(func.sum(OrderMonthly.forecast_total_units), 0),
            func.coalesce(func.sum(OrderMonthly.forecast_units), 0),
        )
        .where(
            OrderMonthly.year == year,
            OrderMonthly.month == month,
            OrderMonthly.product_type == SUPPLY_PRODUCT_TYPE,
            OrderMonthly.product_cd.in_(product_cds),
        )
        .group_by(OrderMonthly.product_cd)
    )
    rows = (await db.execute(stmt)).all()
    return {row[0]: (int(row[1] or 0), int(row[2] or 0)) for row in rows if row[0]}


def _month_index(year: int, month: int) -> int:
    return year * 12 + month - 1


def _month_from_index(index: int) -> tuple[int, int]:
    return index // 12, index % 12 + 1


async def _metrics_map(
    db: AsyncSession, rows: list[SupplyPartStock], year: int, month: int
) -> dict[int, dict]:
    """最終入出庫日・月平均出荷・在庫月数・長期滞留"""
    if not rows:
        return {}
    stock_ids = [int(row.id) for row in rows]
    product_cds = [row.product_cd for row in rows]
    last_rows = (
        await db.execute(
            select(
                SupplyPartTransaction.stock_id,
                func.max(
                    case(
                        (
                            SupplyPartTransaction.txn_type == TXN_SHIPMENT_OUT,
                            SupplyPartTransaction.occurred_date,
                        )
                    )
                ),
                func.max(
                    case((SupplyPartTransaction.quantity > 0, SupplyPartTransaction.occurred_date))
                ),
            )
            .where(SupplyPartTransaction.stock_id.in_(stock_ids))
            .group_by(SupplyPartTransaction.stock_id)
        )
    ).all()
    last_map = {int(r[0]): (r[1], r[2]) for r in last_rows}

    end_idx = _month_index(year, month)
    period = OrderMonthly.year * 12 + OrderMonthly.month - 1
    demand_rows = (
        await db.execute(
            select(
                OrderMonthly.product_cd,
                func.coalesce(func.sum(OrderMonthly.forecast_total_units), 0),
            )
            .where(
                OrderMonthly.product_type == SUPPLY_PRODUCT_TYPE,
                OrderMonthly.product_cd.in_(product_cds),
                period.between(end_idx - DEMAND_MONTHS + 1, end_idx),
            )
            .group_by(OrderMonthly.product_cd)
        )
    ).all()
    demand_map = {r[0]: int(r[1] or 0) for r in demand_rows if r[0]}

    today = date.today()
    result: dict[int, dict] = {}
    for row in rows:
        on_hand = int(row.on_hand_qty or 0)
        last_out, last_in = last_map.get(int(row.id), (None, None))
        avg = round(demand_map.get(row.product_cd, 0) / DEMAND_MONTHS, 1)
        base = last_out or (row.created_at.date() if row.created_at else None)
        idle_days = (today - base).days if base else None
        result[int(row.id)] = {
            "last_out_date": last_out.isoformat() if last_out else None,
            "last_in_date": last_in.isoformat() if last_in else None,
            "idle_days": idle_days,
            "idle_months": (
                round(idle_days * 12 / 365, 1) if on_hand > 0 and idle_days is not None else None
            ),
            "avg_monthly_demand": avg,
            "stagnant": on_hand > 0 and idle_days is not None and idle_days >= STAGNANT_DAYS,
        }
    return result


async def _latest_warehouse_lines(db: AsyncSession, product_cd: str, as_of: date) -> list[dict]:
    """基準日以前で最新日付の倉庫在庫（ルート変更前の古い行は含めない）"""
    latest_date = (
        await db.execute(
            select(func.max(ProductionSummary.date)).where(
                ProductionSummary.product_cd == product_cd,
                ProductionSummary.date <= as_of,
            )
        )
    ).scalar_one_or_none()
    if latest_date is None:
        return []
    rows = (
        await db.execute(
            select(ProductionSummary.route_cd, ProductionSummary.warehouse_inventory)
            .where(
                ProductionSummary.product_cd == product_cd,
                ProductionSummary.date == latest_date,
            )
            .order_by(ProductionSummary.route_cd)
        )
    ).all()
    return [
        {
            "route_cd": route_cd or "",
            "date": latest_date.isoformat(),
            "warehouse_inventory": int(qty or 0),
        }
        for route_cd, qty in rows
    ]


def _transfer_note(lines: list[dict], raw_qty: int, transfer_qty: int, extra: Optional[str]) -> str:
    if lines:
        parts = [
            f"{line['route_cd'] or 'ルートなし'} {line['date']} 倉庫在庫 {line['warehouse_inventory']}"
            for line in lines
        ]
        detail = " / ".join(parts)
    else:
        detail = "生産データの倉庫在庫行なし"
    text = (
        f"振替元: {detail}。合計 {raw_qty}。"
        f"入庫数量 {transfer_qty}。種別を補給品にし、在庫取引記録に製品倉庫の保留を登録しました。"
    )
    if raw_qty <= 0:
        text += " 元の倉庫在庫が 0 以下のため入庫数量は 0 です。"
    user_note = _clean(extra)
    if user_note:
        text = f"{text} {user_note}"
    return text


def _apply_card_fields(row: SupplyPartStock, payload, user_id: int) -> None:
    if getattr(payload, "product_name", None):
        row.product_name = _clean(payload.product_name, 200) or row.product_name
    row.product_alias = _clean(getattr(payload, "product_alias", None), 100)
    row.part_number = _clean(getattr(payload, "part_number", None), 50)
    row.destination_cd = _clean(getattr(payload, "destination_cd", None), 50)
    row.destination_name = _clean(getattr(payload, "destination_name", None), 100)
    row.storage_location = _clean(payload.storage_location, 100) or ""
    row.shelf_no = _clean(payload.shelf_no, 50)
    if "keeper" in payload.model_fields_set:
        row.keeper = _clean(payload.keeper, 50)
    row.safety_stock = int(payload.safety_stock or 0)
    row.quality_status = payload.quality_status
    row.note = _clean(payload.note)
    row.updated_by_user_id = user_id


async def _ensure_location(
    db: AsyncSession, name: str, *, allow_current: Optional[str] = None
) -> None:
    if allow_current is not None and name == allow_current:
        return
    res = await db.execute(
        select(SupplyPartLocation.id).where(
            SupplyPartLocation.name == name, SupplyPartLocation.is_active.is_(True)
        )
    )
    if res.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=400, detail=f"保管場所「{name}」はマスタに登録されていません"
        )


def _location_to_dict(row: SupplyPartLocation, usage: int = 0) -> dict:
    return {
        "id": int(row.id),
        "name": row.name,
        "sort_order": int(row.sort_order or 0),
        "is_active": bool(row.is_active),
        "note": row.note,
        "usage_count": int(usage),
    }


async def _fill_destination(db: AsyncSession, payload) -> None:
    if payload.destination_cd and not _clean(payload.destination_name):
        payload.destination_name = await _destination_name(db, payload.destination_cd)


def _add_txn(
    db: AsyncSession,
    stock: SupplyPartStock,
    txn_type: str,
    quantity: int,
    occurred: date,
    note: Optional[str],
    user_id: int,
) -> SupplyPartTransaction:
    balance = int(stock.on_hand_qty or 0) + int(quantity)
    if balance < 0:
        raise HTTPException(status_code=400, detail="在庫が不足しています")
    stock.on_hand_qty = balance
    txn = SupplyPartTransaction(
        stock_id=stock.id,
        product_cd=stock.product_cd,
        txn_type=txn_type,
        quantity=int(quantity),
        balance_after=balance,
        occurred_date=occurred,
        note=_clean(note),
        created_by_user_id=user_id,
    )
    db.add(txn)
    return txn


@router.get("/products")
async def search_supply_part_products(
    keyword: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=2000),
    supply_only: bool = Query(False, description="製品種別が補給品かつ製品CD末尾が 1 のみ"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    # supply_part_stocks と products は照合順序が異なるため、サブクエリではなく値リストで除外する
    registered = (await db.execute(select(SupplyPartStock.product_cd))).scalars().all()
    stmt = (
        select(Product, Destination.destination_name)
        .outerjoin(Destination, Destination.destination_cd == Product.destination_cd)
        .order_by(Product.product_cd)
        .limit(limit)
    )
    if registered:
        stmt = stmt.where(Product.product_cd.not_in(registered))
    if supply_only:
        stmt = stmt.where(
            Product.product_type == SUPPLY_PRODUCT_TYPE, Product.product_cd.like("%1")
        )
    text = (keyword or "").strip()
    if text:
        like = f"%{text}%"
        stmt = stmt.where(
            or_(
                Product.product_cd.like(like),
                Product.product_name.like(like),
                Product.product_alias.like(like),
                Product.part_number.like(like),
            )
        )
    rows = (await db.execute(stmt)).all()
    return {
        "list": [
            {
                "product_cd": product.product_cd,
                "product_name": product.product_name,
                "product_alias": product.product_alias,
                "part_number": product.part_number,
                "product_type": product.product_type,
                "destination_cd": product.destination_cd,
                "destination_name": destination_name,
            }
            for product, destination_name in rows
        ]
    }


@router.get("/transfer-preview")
async def preview_supply_part_transfer(
    product_cd: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    code = product_cd.strip()
    product = await _load_product(db, code)
    if not product:
        raise HTTPException(status_code=404, detail="製品マスタに存在しません")
    existing = await _existing_stock(db, code)
    lines = await _latest_warehouse_lines(db, code, date.today())
    raw_qty = sum(int(line["warehouse_inventory"]) for line in lines)
    dest_name = await _destination_name(db, product.destination_cd)
    warning = None
    if raw_qty <= 0:
        warning = f"今日以前の倉庫在庫合計は {raw_qty} です。種別変更と倉庫在庫の 0 化は行い、入庫数量は 0 になります。"
    return {
        "product_cd": product.product_cd,
        "product_name": product.product_name,
        "product_alias": product.product_alias,
        "part_number": product.part_number,
        "product_type": product.product_type,
        "destination_cd": product.destination_cd,
        "destination_name": dest_name,
        "already_registered": existing is not None,
        "lines": lines,
        "raw_warehouse_qty": raw_qty,
        "transfer_qty": max(raw_qty, 0),
        "warning": warning,
    }


@router.get("")
async def list_supply_parts(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    keyword: Optional[str] = Query(None),
    alert_only: bool = Query(False),
    storage_location: Optional[str] = Query(None),
    destination_cd: Optional[str] = Query(None),
    stagnant_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month
    stmt = select(SupplyPartStock).order_by(SupplyPartStock.product_cd)
    location = _clean(storage_location)
    if location:
        stmt = stmt.where(SupplyPartStock.storage_location == location)
    dest = _clean(destination_cd)
    if dest:
        stmt = stmt.where(SupplyPartStock.destination_cd == dest)
    text = (keyword or "").strip()
    if text:
        like = f"%{text}%"
        stmt = stmt.where(
            or_(
                SupplyPartStock.product_cd.like(like),
                SupplyPartStock.product_name.like(like),
                SupplyPartStock.product_alias.like(like),
                SupplyPartStock.part_number.like(like),
                SupplyPartStock.storage_location.like(like),
                SupplyPartStock.shelf_no.like(like),
            )
        )
    rows = (await db.execute(stmt)).scalars().all()
    ship_map = await _shipment_map(db, [row.product_cd for row in rows], target_year, target_month)
    metric_map = await _metrics_map(db, list(rows), target_year, target_month)
    items = []
    for row in rows:
        item = _stock_to_dict(row, ship_map.get(row.product_cd), metric_map.get(int(row.id)))
        if alert_only and not (item["below_safety"] or item["short_of_shipment"]):
            continue
        if stagnant_only and not item["stagnant"]:
            continue
        items.append(item)
    return {
        "year": target_year,
        "month": target_month,
        "list": items,
        "summary": {
            "count": len(items),
            "on_hand_total": sum(item["on_hand_qty"] for item in items),
            "shipment_total": sum(item["shipment_planned"] for item in items),
            "alert_count": sum(
                1 for item in items if item["below_safety"] or item["short_of_shipment"]
            ),
            "stagnant_count": sum(1 for item in items if item["stagnant"]),
            "quality_issue_count": sum(
                1 for item in items if item["quality_status"] != QUALITY_GOOD
            ),
        },
        "stagnant_days": STAGNANT_DAYS,
        "demand_months": DEMAND_MONTHS,
        "quality_statuses": list(QUALITY_STATUSES),
    }


@router.post("/transfer")
async def transfer_supply_part(
    body: SupplyPartTransferBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("create")),
):
    product = await _load_product(db, body.product_cd)
    if not product:
        raise HTTPException(status_code=404, detail="製品マスタに存在しません")
    if await _existing_stock(db, body.product_cd):
        raise HTTPException(status_code=409, detail="この品番はすでに補給品在庫に登録されています")
    await _ensure_location(db, body.storage_location)

    lines = await _latest_warehouse_lines(db, body.product_cd, date.today())
    raw_qty = sum(int(line["warehouse_inventory"]) for line in lines)
    transfer_qty = max(raw_qty, 0)
    if not body.product_alias:
        body.product_alias = product.product_alias
    if not body.part_number:
        body.part_number = product.part_number
    if not body.destination_cd:
        body.destination_cd = product.destination_cd
    await _fill_destination(db, body)

    await db.execute(
        update(Product)
        .where(Product.product_cd == body.product_cd)
        .values(product_type=SUPPLY_PRODUCT_TYPE)
    )
    stock = SupplyPartStock(
        product_cd=body.product_cd,
        product_name=_clean(product.product_name, 200) or body.product_cd,
        source=SOURCE_TRANSFER,
        on_hand_qty=0,
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
    )
    _apply_card_fields(stock, body, current_user.id)
    stock.product_name = _clean(product.product_name, 200) or body.product_cd
    db.add(stock)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="この品番はすでに補給品在庫に登録されています"
        ) from exc
    note = _transfer_note(lines, raw_qty, transfer_qty, body.note)
    _add_txn(db, stock, TXN_TRANSFER_IN, transfer_qty, date.today(), note, current_user.id)
    log = None
    if transfer_qty > 0:
        op_id = getattr(current_user, "user_id", None) or getattr(current_user, "id", None)
        log = StockTransactionLog(
            stock_type=STOCK_LOG_TYPE,
            transaction_type=STOCK_LOG_HOLD,
            target_cd=body.product_cd,
            location_cd=STOCK_LOG_LOCATION,
            process_cd=STOCK_LOG_PROCESS,
            quantity=Decimal(transfer_qty),
            unit=STOCK_LOG_UNIT,
            operator_id=str(op_id) if op_id is not None else None,
            operator_name=getattr(current_user, "username", None)
            or getattr(current_user, "name", None),
            transaction_time=now_jst(),
            source_file=STOCK_LOG_SOURCE,
            remarks=f"補給品へ振替（保管場所: {body.storage_location}）",
        )
        db.add(log)
    await db.flush()
    await db.refresh(stock)
    warning = None
    if raw_qty <= 0:
        warning = (
            f"元の倉庫在庫は {raw_qty} のため、入庫数量は 0 です。"
            "種別は補給品に変更しました（在庫取引記録の保留はありません）。"
        )
    return {
        "stock": _stock_to_dict(stock),
        "raw_warehouse_qty": raw_qty,
        "transfer_qty": transfer_qty,
        "stock_log_id": int(log.id) if log is not None else None,
        "warning": warning,
    }


@router.post("")
async def create_supply_part_manual(
    body: SupplyPartManualCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("create")),
):
    if await _existing_stock(db, body.product_cd):
        raise HTTPException(status_code=409, detail="この品番はすでに補給品在庫に登録されています")
    await _ensure_location(db, body.storage_location)
    product = await _load_product(db, body.product_cd)
    await _fill_destination(db, body)
    if product:
        if not body.product_alias:
            body.product_alias = product.product_alias
        if not body.part_number:
            body.part_number = product.part_number
        if not body.destination_cd:
            body.destination_cd = product.destination_cd
            body.destination_name = body.destination_name or await _destination_name(
                db, product.destination_cd
            )
    stock = SupplyPartStock(
        product_cd=body.product_cd,
        product_name=_clean(body.product_name, 200) or body.product_cd,
        source=SOURCE_MANUAL,
        on_hand_qty=0,
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
    )
    _apply_card_fields(stock, body, current_user.id)
    stock.product_name = _clean(body.product_name, 200) or body.product_cd
    db.add(stock)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="この品番はすでに補給品在庫に登録されています"
        ) from exc
    note = _clean(body.note) or "手動登録の期初在庫"
    _add_txn(db, stock, TXN_MANUAL_IN, int(body.opening_qty), date.today(), note, current_user.id)
    await db.flush()
    await db.refresh(stock)
    return _stock_to_dict(stock)


@router.get("/locations")
async def list_supply_part_locations(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    stmt = select(SupplyPartLocation).order_by(
        SupplyPartLocation.sort_order, SupplyPartLocation.name
    )
    if not include_inactive:
        stmt = stmt.where(SupplyPartLocation.is_active.is_(True))
    rows = (await db.execute(stmt)).scalars().all()
    usage_rows = (
        await db.execute(
            select(SupplyPartStock.storage_location, func.count()).group_by(
                SupplyPartStock.storage_location
            )
        )
    ).all()
    usage = {name: int(count) for name, count in usage_rows if name}
    return {"list": [_location_to_dict(row, usage.get(row.name, 0)) for row in rows]}


@router.post("/locations")
async def create_supply_part_location(
    body: SupplyPartLocationBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("create")),
):
    row = SupplyPartLocation(
        name=body.name,
        sort_order=int(body.sort_order or 0),
        is_active=bool(body.is_active),
        note=_clean(body.note, 255),
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="同じ名前の保管場所がすでにあります") from exc
    await db.refresh(row)
    return _location_to_dict(row)


@router.put("/locations/{location_id}")
async def update_supply_part_location(
    location_id: int,
    body: SupplyPartLocationBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    res = await db.execute(
        select(SupplyPartLocation).where(SupplyPartLocation.id == location_id).with_for_update()
    )
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="保管場所が見つかりません")
    old_name = row.name
    row.name = body.name
    row.sort_order = int(body.sort_order or 0)
    row.is_active = bool(body.is_active)
    row.note = _clean(body.note, 255)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="同じ名前の保管場所がすでにあります") from exc
    renamed = 0
    if old_name != body.name:
        result = await db.execute(
            update(SupplyPartStock)
            .where(SupplyPartStock.storage_location == old_name)
            .values(storage_location=body.name, updated_by_user_id=current_user.id)
        )
        renamed = int(result.rowcount or 0)
    await db.refresh(row)
    usage = (
        await db.execute(
            select(func.count())
            .select_from(SupplyPartStock)
            .where(SupplyPartStock.storage_location == row.name)
        )
    ).scalar() or 0
    return {**_location_to_dict(row, usage), "renamed_stocks": renamed}


@router.delete("/locations/{location_id}")
async def delete_supply_part_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("delete")),
):
    res = await db.execute(select(SupplyPartLocation).where(SupplyPartLocation.id == location_id))
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="保管場所が見つかりません")
    usage = (
        await db.execute(
            select(func.count())
            .select_from(SupplyPartStock)
            .where(SupplyPartStock.storage_location == row.name)
        )
    ).scalar() or 0
    if usage:
        raise HTTPException(
            status_code=409,
            detail=f"この保管場所は {usage} 件の補給品で使用中のため削除できません。使用停止にしてください。",
        )
    await db.delete(row)
    await db.flush()
    return {"deleted": True}


@router.get("/{stock_id}")
async def get_supply_part(
    stock_id: int,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    res = await db.execute(select(SupplyPartStock).where(SupplyPartStock.id == stock_id))
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="補給品在庫が見つかりません")
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month
    ship_map = await _shipment_map(db, [stock.product_cd], target_year, target_month)
    txn_rows = (
        (
            await db.execute(
                select(SupplyPartTransaction)
                .where(SupplyPartTransaction.stock_id == stock.id)
                .order_by(
                    SupplyPartTransaction.occurred_date.desc(), SupplyPartTransaction.id.desc()
                )
                .limit(200)
            )
        )
        .scalars()
        .all()
    )
    order_rows = (
        (
            await db.execute(
                select(OrderMonthly)
                .where(
                    OrderMonthly.product_cd == stock.product_cd,
                    OrderMonthly.year == target_year,
                    OrderMonthly.month == target_month,
                    OrderMonthly.product_type == SUPPLY_PRODUCT_TYPE,
                )
                .order_by(OrderMonthly.destination_cd, OrderMonthly.id)
            )
        )
        .scalars()
        .all()
    )
    metric_map = await _metrics_map(db, [stock], target_year, target_month)
    return {
        "stock": _stock_to_dict(stock, ship_map.get(stock.product_cd), metric_map.get(stock.id)),
        "year": target_year,
        "month": target_month,
        "transactions": [_txn_to_dict(row) for row in txn_rows],
        "orders": [
            {
                "id": row.id,
                "order_id": row.order_id,
                "destination_cd": row.destination_cd,
                "destination_name": row.destination_name,
                "forecast_units": int(row.forecast_units or 0),
                "forecast_total_units": int(row.forecast_total_units or 0),
            }
            for row in order_rows
        ],
    }


@router.get("/{stock_id}/trend")
async def get_supply_part_trend(
    stock_id: int,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    months: int = Query(12, ge=3, le=36),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月別の入庫・出庫・月末在庫・受注確定本数"""
    res = await db.execute(select(SupplyPartStock).where(SupplyPartStock.id == stock_id))
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="補給品在庫が見つかりません")
    today = date.today()
    end_idx = _month_index(year or today.year, month or today.month)
    start_idx = end_idx - months + 1

    txn_rows = (
        await db.execute(
            select(SupplyPartTransaction.occurred_date, SupplyPartTransaction.quantity).where(
                SupplyPartTransaction.stock_id == stock.id
            )
        )
    ).all()
    balance = 0
    buckets = {idx: [0, 0] for idx in range(start_idx, end_idx + 1)}
    for occurred, qty in txn_rows:
        if not occurred:
            continue
        idx = _month_index(occurred.year, occurred.month)
        qty = int(qty or 0)
        if idx < start_idx:
            balance += qty
        elif idx in buckets:
            buckets[idx][0 if qty > 0 else 1] += abs(qty)

    period = OrderMonthly.year * 12 + OrderMonthly.month - 1
    order_rows = (
        await db.execute(
            select(
                OrderMonthly.year,
                OrderMonthly.month,
                func.coalesce(func.sum(OrderMonthly.forecast_total_units), 0),
            )
            .where(
                OrderMonthly.product_cd == stock.product_cd,
                OrderMonthly.product_type == SUPPLY_PRODUCT_TYPE,
                period.between(start_idx, end_idx),
            )
            .group_by(OrderMonthly.year, OrderMonthly.month)
        )
    ).all()
    order_map = {_month_index(int(r[0]), int(r[1])): int(r[2] or 0) for r in order_rows}

    points = []
    for idx in range(start_idx, end_idx + 1):
        in_qty, out_qty = buckets[idx]
        balance += in_qty - out_qty
        y, m = _month_from_index(idx)
        points.append(
            {
                "month": f"{y}-{m:02d}",
                "in_qty": in_qty,
                "out_qty": out_qty,
                "end_balance": balance,
                "order_qty": order_map.get(idx, 0),
            }
        )
    return {"stock_id": int(stock.id), "points": points}


@router.delete("/{stock_id}")
async def delete_supply_part(
    stock_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("delete")),
):
    """補給品カードと入出庫履歴を削除。振替分は在庫取引記録の振替保留も削除する。"""
    res = await db.execute(
        select(SupplyPartStock).where(SupplyPartStock.id == stock_id).with_for_update()
    )
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="補給品在庫が見つかりません")
    removed_logs = 0
    if stock.source == SOURCE_TRANSFER:
        log_res = await db.execute(
            delete(StockTransactionLog).where(
                StockTransactionLog.target_cd == stock.product_cd,
                StockTransactionLog.source_file == STOCK_LOG_SOURCE,
            )
        )
        removed_logs = int(log_res.rowcount or 0)
    txn_res = await db.execute(
        delete(SupplyPartTransaction).where(SupplyPartTransaction.stock_id == stock.id)
    )
    product_cd = stock.product_cd
    await db.delete(stock)
    await db.flush()
    return {
        "deleted": True,
        "product_cd": product_cd,
        "removed_transactions": int(txn_res.rowcount or 0),
        "removed_stock_logs": removed_logs,
    }


@router.put("/{stock_id}")
async def update_supply_part(
    stock_id: int,
    body: SupplyPartUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    res = await db.execute(
        select(SupplyPartStock).where(SupplyPartStock.id == stock_id).with_for_update()
    )
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="補給品在庫が見つかりません")
    name = _clean(body.product_name, 200)
    if not name:
        raise HTTPException(status_code=400, detail="品名は必須です")
    await _ensure_location(db, body.storage_location, allow_current=stock.storage_location)
    await _fill_destination(db, body)
    _apply_card_fields(stock, body, current_user.id)
    stock.product_name = name
    await db.flush()
    await db.refresh(stock)
    return _stock_to_dict(stock)


@router.post("/{stock_id}/transactions")
async def create_supply_part_transaction(
    stock_id: int,
    body: SupplyPartTxnBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    res = await db.execute(
        select(SupplyPartStock).where(SupplyPartStock.id == stock_id).with_for_update()
    )
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="補給品在庫が見つかりません")
    if body.txn_type == TXN_ADJUST:
        signed = int(body.quantity)
        if signed == 0:
            raise HTTPException(status_code=400, detail="調整数量が 0 です")
    elif body.txn_type == TXN_SHIPMENT_OUT:
        if int(body.quantity) <= 0:
            raise HTTPException(status_code=400, detail="出荷数量は 1 以上にしてください")
        signed = -int(body.quantity)
    else:
        if int(body.quantity) <= 0:
            raise HTTPException(status_code=400, detail="生産数量は 1 以上にしてください")
        signed = int(body.quantity)
    txn = _add_txn(db, stock, body.txn_type, signed, body.occurred_date, body.note, current_user.id)
    await db.flush()
    await db.refresh(stock)
    await db.refresh(txn)
    ship_map = await _shipment_map(
        db, [stock.product_cd], body.occurred_date.year, body.occurred_date.month
    )
    return {
        "stock": _stock_to_dict(stock, ship_map.get(stock.product_cd)),
        "transaction": _txn_to_dict(txn),
    }
