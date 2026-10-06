"""
外注溶接日別台帳。
材料在庫と同じく日付×品目の空行を先に生成し、注文数・受入数・不良数・初期在庫を後から入力する。
3数量は stock_transaction_logs へ上書き同期する（0 で該当ログを消す）。
初期在庫は毎月1日の行にのみ入力できる。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.company_work_calendar import is_scheduled_workday, load_company_calendar_sets
from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_purchase_operation
from app.modules.erp.stock_transaction_log_models import StockTransactionLog
from app.modules.outsourcing.models import (
    OutsourcingProcessProduct,
    OutsourcingSupplier,
    WeldingLedger,
    WeldingOrder,
)

router = APIRouter()

SOURCE_FILE = "outsourcing_welding_ledger"
STOCK_TYPE = "仕掛品"
UNIT = "本"

# (数量フィールド, 工程, 操作種別, 保管場所)
LOG_SPECS = (
    ("order_qty", "KT08", "実績", "外注倉庫"),
    ("receiving_qty", "KT16", "実績", "仕上倉庫"),
    ("defect_qty", "KT16", "不良", "仕上倉庫"),
)

# 現在庫タブから除外する外注先（溶接は対象外なし）
STOCK_EXCLUDED_SUPPLIERS: tuple[str, ...] = ()


class GenerateBody(BaseModel):
    start_date: str
    end_date: str


class UpdateBody(BaseModel):
    order_qty: Optional[int] = None
    receiving_qty: Optional[int] = None
    defect_qty: Optional[int] = None
    initial_stock: Optional[int] = None


class IssuedBody(BaseModel):
    ids: list[int]


class RefreshMasterBody(BaseModel):
    start_date: str
    end_date: str
    supplier_cd: Optional[str] = None
    product_cd: Optional[str] = None
    # True なら注文済みでも注文書未発行の行を更新する（金額も再計算）
    include_ordered: bool = False


# 採番の一意制約衝突（同時保存）時の再試行回数
SAVE_RETRY = 3


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日付の形式が不正です: {value}") from e


def _qty(value: Optional[int], label: str) -> int:
    if value is None:
        return 0
    if value < 0 or value > 9_999_999:
        raise HTTPException(
            status_code=400, detail=f"{label}は 0〜9,999,999 の範囲で指定してください"
        )
    return int(value)


def _money(qty: int, unit_price) -> float:
    price = float(unit_price or 0)
    return round(qty * price, 2)


def _row_dict(r: WeldingLedger) -> dict:
    return {
        "id": r.id,
        "order_date": r.order_date.isoformat() if r.order_date else None,
        "supplier_cd": r.supplier_cd,
        "supplier_name": r.supplier_name or r.supplier_cd,
        "product_cd": r.product_cd,
        "product_name": r.product_name or "",
        "unit_price": float(r.unit_price or 0),
        "lead_time_days": r.lead_time_days or 0,
        "delivery_date": r.delivery_date.isoformat() if r.delivery_date else None,
        "order_qty": r.order_qty or 0,
        "order_no": r.order_no,
        "order_amount": float(r.order_amount or 0),
        "order_sheet_issued_at": (
            r.order_sheet_issued_at.isoformat(sep=" ", timespec="minutes")
            if r.order_sheet_issued_at
            else None
        ),
        "order_sheet_issued_by": r.order_sheet_issued_by,
        "receiving_qty": r.receiving_qty or 0,
        "receiving_no": r.receiving_no,
        "defect_qty": r.defect_qty or 0,
        "disposal_no": r.disposal_no,
        "initial_stock": r.initial_stock or 0,
        "current_stock": r.current_stock or 0,
    }


def _lead_days(product: OutsourcingProcessProduct, supplier: OutsourcingSupplier) -> int:
    """外注先のリードタイム優先、未設定なら製品マスタ、どちらも無ければ 7 日。"""
    lead = supplier.lead_time_days
    if lead is None:
        lead = product.delivery_lead_time if product.delivery_lead_time is not None else 7
    return int(lead)


def _add_business_days(start: date, days: int, scheduled: set[str], off: set[str]) -> date:
    """注文日の翌稼働日から days 日進めた納期。0 日なら注文日当日。"""
    if days <= 0:
        return start
    cur = start
    added = 0
    guard = 0
    limit = days * 4 + 60
    while added < days and guard < limit:
        guard += 1
        cur = cur + timedelta(days=1)
        if is_scheduled_workday(
            cur,
            company_scheduled=scheduled,
            company_off=off,
            extra_workdays=set(),
            extra_holidays=set(),
        ):
            added += 1
    return cur


async def _max_seq(db: AsyncSession, col, prefix: str) -> int:
    """prefix で始まる番号の連番最大値。文字列の max だと -100 < -99 になるため数値で比較する。"""
    values = (
        (await db.execute(select(col).where(col.startswith(prefix, autoescape=True))))
        .scalars()
        .all()
    )
    seq = 0
    for value in values:
        tail = str(value)[len(prefix) :]
        if tail.isdigit():
            seq = max(seq, int(tail))
    return seq


async def _next_order_seq(db: AsyncSession, prefix: str) -> int:
    seq = 0
    for col in (WeldingLedger.order_no, WeldingOrder.order_no):
        seq = max(seq, await _max_seq(db, col, prefix))
    return seq + 1


async def _assign_order_no(db: AsyncSession, row: WeldingLedger) -> None:
    """注文数 > 0 のとき番号を採番、0 なら番号を外す。受入数・不良数とは無関係。"""
    if int(row.order_qty or 0) > 0:
        if row.order_no:
            return
        prefix = f"{row.supplier_cd}{row.order_date.strftime('%Y%m%d')}-"
        seq = await _next_order_seq(db, prefix)
        row.order_no = f"{prefix}{seq:02d}"
        return
    row.order_no = None


# 数量フィールド -> (管理番号フィールド, 番号接頭辞)
MGMT_NO_SPECS = {
    "receiving_qty": ("receiving_no", "R-"),
    "defect_qty": ("disposal_no", "D-"),
}


async def _assign_mgmt_no(db: AsyncSession, row: WeldingLedger, field: str) -> None:
    """受入・不良の管理番号。数量 > 0 で採番、0 で外す。注文番号とは独立。"""
    no_field, head = MGMT_NO_SPECS[field]
    if int(getattr(row, field) or 0) <= 0:
        setattr(row, no_field, None)
        return
    if getattr(row, no_field):
        return
    prefix = f"{head}{row.supplier_cd}{row.order_date.strftime('%Y%m%d')}-"
    seq = await _max_seq(db, getattr(WeldingLedger, no_field), prefix)
    setattr(row, no_field, f"{prefix}{seq + 1:02d}")


def _mgmt_no(row: WeldingLedger, field: str) -> Optional[str]:
    if field == "order_qty":
        return row.order_no
    return getattr(row, MGMT_NO_SPECS[field][0])


async def recalculate_current_stock(
    db: AsyncSession,
    keys: Optional[list[tuple[str, str]]] = None,
) -> list[WeldingLedger]:
    """
    外注先手元の在庫。
    初期在庫は毎月1日の行だけが有効。初期在庫 > 0 の最終月の1日を起点にし、
    それより前の行は計算対象外（前日結転は 0）。
    当天 = 初期在庫 + 注文数 - (受入数 + 不良数) + 前日現在庫
    戻り値は現在庫が変わった行のみ。
    """
    q = select(WeldingLedger)
    if keys:
        conds = [
            (WeldingLedger.supplier_cd == supplier) & (WeldingLedger.product_cd == product)
            for supplier, product in keys
        ]
        q = q.where(or_(*conds)) if conds else q.where(WeldingLedger.id == -1)
    rows = list(
        (await db.execute(q.order_by(WeldingLedger.order_date, WeldingLedger.id))).scalars().all()
    )
    grouped: dict[tuple[str, str], list[WeldingLedger]] = {}
    for row in rows:
        grouped.setdefault((row.supplier_cd, row.product_cd), []).append(row)

    touched: list[WeldingLedger] = []
    for items in grouped.values():
        items.sort(key=lambda r: (r.order_date, r.id))
        with_initial = [r for r in items if r.order_date.day == 1 and int(r.initial_stock or 0) > 0]
        if with_initial:
            latest = max(r.order_date for r in with_initial)
            start = latest.replace(day=1)
            to_calc = [r for r in items if r.order_date >= start]
        else:
            to_calc = items
        prev = 0
        for row in to_calc:
            initial = int(row.initial_stock or 0) if row.order_date.day == 1 else 0
            new_current = (
                initial
                + int(row.order_qty or 0)
                - (int(row.receiving_qty or 0) + int(row.defect_qty or 0))
                + prev
            )
            if int(row.current_stock or 0) != new_current:
                row.current_stock = new_current
                touched.append(row)
            prev = new_current
    return touched


def _log_remarks(row: WeldingLedger, kind: str) -> str:
    name = row.product_name or ""
    if kind == "order_qty":
        return f"外注溶接注文: {name} | 注文番号: {row.order_no or ''} | 外注先: {row.supplier_cd}"
    if kind == "defect_qty":
        return (
            f"外注溶接不良: {name} | 不良番号: {row.disposal_no or ''}"
            f" | 不良数: {int(row.defect_qty or 0)} | 外注先: {row.supplier_cd}"
        )
    return (
        f"外注溶接受入: {name} | 受入番号: {row.receiving_no or ''}"
        f" | 受入数: {int(row.receiving_qty or 0)} | 外注先: {row.supplier_cd}"
    )


async def sync_stock_logs(
    db: AsyncSession,
    row: WeldingLedger,
    operator_name: Optional[str],
    fields: Optional[Iterable[str]] = None,
) -> None:
    """
    同一行・同一種別は1件。数量は上書き。0 なら削除。
    注文数・受入数・不良数のログはそれぞれ独立し、指定 fields のみ同期する。
    order_no には注文番号・受入番号・不良番号をそれぞれ付ける。
    """
    note = str(row.id)
    when = datetime.combine(row.order_date, datetime.min.time())
    targets = set(fields) if fields is not None else None
    for field, process_cd, tx_type, location in LOG_SPECS:
        if targets is not None and field not in targets:
            continue
        qty = int(getattr(row, field) or 0)
        order_no = _mgmt_no(row, field)
        q = select(StockTransactionLog).where(
            StockTransactionLog.source_file == SOURCE_FILE,
            StockTransactionLog.notes == note,
            StockTransactionLog.process_cd == process_cd,
            StockTransactionLog.transaction_type == tx_type,
        )
        existing = list((await db.execute(q)).scalars().all())
        if qty <= 0:
            for old in existing:
                await db.delete(old)
            continue
        keep = existing[0] if existing else None
        for extra in existing[1:]:
            await db.delete(extra)
        if keep is None:
            keep = StockTransactionLog(
                stock_type=STOCK_TYPE,
                transaction_type=tx_type,
                target_cd=row.product_cd,
                location_cd=location,
                process_cd=process_cd,
                quantity=qty,
                unit=UNIT,
                order_no=order_no,
                notes=note,
                operator_name=operator_name,
                transaction_time=when,
                source_file=SOURCE_FILE,
                remarks=_log_remarks(row, field),
            )
            db.add(keep)
        else:
            keep.stock_type = STOCK_TYPE
            keep.transaction_type = tx_type
            keep.target_cd = row.product_cd
            keep.location_cd = location
            keep.process_cd = process_cd
            keep.quantity = qty
            keep.unit = UNIT
            keep.order_no = order_no
            keep.notes = note
            keep.operator_name = operator_name
            keep.transaction_time = when
            keep.source_file = SOURCE_FILE
            keep.remarks = _log_remarks(row, field)


def _operator(user: User) -> str:
    return (user.full_name or user.username or "")[:100]


@router.get("/ledger/options")
async def welding_ledger_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """フィルタ用の外注先×製品。台帳の既存行と有効な外注溶接製品マスタを合わせる。"""
    pairs: dict[tuple[str, str], dict] = {}
    supplier_names: dict[str, str] = {}

    master_rows = (
        await db.execute(
            select(
                OutsourcingProcessProduct.supplier_cd,
                OutsourcingProcessProduct.supplier_name,
                OutsourcingProcessProduct.product_cd,
                OutsourcingProcessProduct.product_name,
                OutsourcingSupplier.supplier_name,
            )
            .outerjoin(
                OutsourcingSupplier,
                OutsourcingSupplier.supplier_cd == OutsourcingProcessProduct.supplier_cd,
            )
            .where(
                OutsourcingProcessProduct.process_type == "welding",
                OutsourcingProcessProduct.is_active == True,  # noqa: E712
            )
        )
    ).all()
    for supplier_cd, pp_supplier_name, product_cd, product_name, master_name in master_rows:
        if not supplier_cd or not product_cd:
            continue
        supplier_names.setdefault(supplier_cd, master_name or pp_supplier_name or supplier_cd)
        pairs[(supplier_cd, product_cd)] = {
            "supplier_cd": supplier_cd,
            "product_cd": product_cd,
            "product_name": product_name or product_cd,
        }

    ledger_rows = (
        await db.execute(
            select(
                WeldingLedger.supplier_cd,
                WeldingLedger.supplier_name,
                WeldingLedger.product_cd,
                WeldingLedger.product_name,
            ).distinct()
        )
    ).all()
    for supplier_cd, supplier_name, product_cd, product_name in ledger_rows:
        if not supplier_cd or not product_cd:
            continue
        supplier_names.setdefault(supplier_cd, supplier_name or supplier_cd)
        pairs.setdefault(
            (supplier_cd, product_cd),
            {
                "supplier_cd": supplier_cd,
                "product_cd": product_cd,
                "product_name": product_name or product_cd,
            },
        )

    for item in pairs.values():
        item["supplier_name"] = supplier_names.get(item["supplier_cd"], item["supplier_cd"])
    items = sorted(
        pairs.values(), key=lambda x: (x["supplier_name"], x["product_name"], x["product_cd"])
    )
    return {"success": True, "data": items}


@router.get("/ledger/order-sheet")
async def welding_ledger_order_sheet(
    orderDate: str = Query(...),
    supplierCd: str = Query(...),
    endDate: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """注文書発行用：注文日（endDate 指定時は orderDate〜endDate）×外注先の注文数>0 の行。
    納品場所・区分・内容は製品マスタから補う。"""
    start = _parse_date(orderDate)
    end = _parse_date(endDate) if endDate else start
    if end < start:
        raise HTTPException(status_code=400, detail="終了日は開始日以降を指定してください")
    if (end - start).days > 62:
        raise HTTPException(status_code=400, detail="期間は62日以内で指定してください")
    supplier_cd = supplierCd.strip()
    if not supplier_cd:
        raise HTTPException(status_code=400, detail="外注先を指定してください")

    rows = (
        (
            await db.execute(
                select(WeldingLedger)
                .where(
                    WeldingLedger.order_date >= start,
                    WeldingLedger.order_date <= end,
                    WeldingLedger.supplier_cd == supplier_cd,
                    WeldingLedger.order_qty > 0,
                )
                .order_by(
                    WeldingLedger.order_date, WeldingLedger.product_name, WeldingLedger.product_cd
                )
            )
        )
        .scalars()
        .all()
    )

    masters = (
        (
            await db.execute(
                select(OutsourcingProcessProduct).where(
                    OutsourcingProcessProduct.process_type == "welding",
                    OutsourcingProcessProduct.supplier_cd == supplier_cd,
                )
            )
        )
        .scalars()
        .all()
    )
    master_by_product: dict[str, OutsourcingProcessProduct] = {}
    for m in masters:
        if m.product_cd not in master_by_product or m.is_active:
            master_by_product[m.product_cd] = m

    supplier = (
        await db.execute(
            select(OutsourcingSupplier).where(OutsourcingSupplier.supplier_cd == supplier_cd)
        )
    ).scalar_one_or_none()
    supplier_name = (
        supplier.supplier_name if supplier else (rows[0].supplier_name if rows else supplier_cd)
    )

    items = []
    for r in rows:
        m = master_by_product.get(r.product_cd)
        d = _row_dict(r)
        d["delivery_location"] = (m.delivery_location if m else None) or ""
        d["category"] = (m.category if m else None) or ""
        d["content"] = (m.content if m else None) or ""
        items.append(d)
    return {
        "success": True,
        "data": {"supplier_cd": supplier_cd, "supplier_name": supplier_name, "items": items},
    }


@router.post("/ledger/order-sheet/issued")
async def mark_welding_order_sheet_issued(
    body: IssuedBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("export")),
):
    """注文書を印刷した行に発行日時・発行者を記録する（再発行は上書き）。"""
    if not body.ids:
        return {"success": True, "data": {"updated_count": 0, "rows": []}}
    rows = (
        (
            await db.execute(
                select(WeldingLedger).where(
                    WeldingLedger.id.in_(body.ids), WeldingLedger.order_qty > 0
                )
            )
        )
        .scalars()
        .all()
    )
    now = datetime.now()
    operator = _operator(current_user)
    for r in rows:
        r.order_sheet_issued_at = now
        r.order_sheet_issued_by = operator
    await db.flush()
    return {
        "success": True,
        "data": {"updated_count": len(rows), "rows": [_row_dict(r) for r in rows]},
    }


@router.get("/ledger/history")
async def welding_ledger_history(
    kind: str = Query(..., pattern="^(order|receiving)$"),
    startDate: str = Query(...),
    endDate: str = Query(...),
    supplierCd: Optional[str] = Query(None),
    productCd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """注文履歴（注文数>0）/ 受入履歴（受入数>0 または不良数>0）。ページングなし。"""
    start = _parse_date(startDate)
    end = _parse_date(endDate)
    if start > end:
        raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")
    if (end - start).days > 366:
        raise HTTPException(status_code=400, detail="期間は366日以内にしてください")
    q = select(WeldingLedger).where(
        WeldingLedger.order_date >= start, WeldingLedger.order_date <= end
    )
    if kind == "order":
        q = q.where(WeldingLedger.order_qty > 0)
    else:
        q = q.where(or_(WeldingLedger.receiving_qty > 0, WeldingLedger.defect_qty > 0))
    if supplierCd and supplierCd.strip():
        q = q.where(WeldingLedger.supplier_cd == supplierCd.strip())
    if productCd and productCd.strip():
        q = q.where(WeldingLedger.product_cd == productCd.strip())
    q = q.order_by(
        WeldingLedger.order_date,
        WeldingLedger.supplier_name,
        WeldingLedger.product_name,
        WeldingLedger.product_cd,
    )
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": [_row_dict(r) for r in rows]}


@router.get("/ledger/stock")
async def welding_ledger_stock(
    asOf: str = Query(...),
    supplierCd: Optional[str] = Query(None),
    productCd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注先×製品ごとの基準日時点の現在庫と、基準日の月の注文・受入・不良累計。"""
    as_of = _parse_date(asOf)
    month_start = as_of.replace(day=1)
    q = select(WeldingLedger).where(
        WeldingLedger.order_date <= as_of,
        WeldingLedger.order_date >= as_of - timedelta(days=366),
    )
    if STOCK_EXCLUDED_SUPPLIERS:
        q = q.where(WeldingLedger.supplier_cd.notin_(STOCK_EXCLUDED_SUPPLIERS))
    if supplierCd and supplierCd.strip():
        q = q.where(WeldingLedger.supplier_cd == supplierCd.strip())
    if productCd and productCd.strip():
        q = q.where(WeldingLedger.product_cd == productCd.strip())
    rows = (await db.execute(q.order_by(WeldingLedger.order_date))).scalars().all()

    items: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r.supplier_cd, r.product_cd)
        it = items.get(key)
        if it is None:
            it = {
                "supplier_cd": r.supplier_cd,
                "supplier_name": r.supplier_name or r.supplier_cd,
                "product_cd": r.product_cd,
                "product_name": r.product_name or "",
                "month_initial": 0,
                "month_order_qty": 0,
                "month_receiving_qty": 0,
                "month_defect_qty": 0,
                "current_stock": 0,
                "last_order_date": None,
                "last_receiving_date": None,
            }
            items[key] = it
        # 日付昇順なので最後の行が基準日時点
        it["current_stock"] = int(r.current_stock or 0)
        if int(r.order_qty or 0) > 0:
            it["last_order_date"] = r.order_date.isoformat()
        if int(r.receiving_qty or 0) > 0:
            it["last_receiving_date"] = r.order_date.isoformat()
        if r.order_date >= month_start:
            if r.order_date == month_start:
                it["month_initial"] = int(r.initial_stock or 0)
            it["month_order_qty"] += int(r.order_qty or 0)
            it["month_receiving_qty"] += int(r.receiving_qty or 0)
            it["month_defect_qty"] += int(r.defect_qty or 0)

    data = sorted(
        items.values(), key=lambda x: (x["supplier_name"], x["product_name"], x["product_cd"])
    )
    return {"success": True, "data": data}


@router.get("/ledger/stock-trend")
async def welding_ledger_stock_trend(
    asOf: str = Query(...),
    supplierCd: Optional[str] = Query(None),
    productCd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """現在庫分析用：基準日の月初〜基準日の日別合計（注文・受入・不良・現在庫）。"""
    as_of = _parse_date(asOf)
    month_start = as_of.replace(day=1)
    q = select(
        WeldingLedger.order_date,
        func.sum(WeldingLedger.order_qty),
        func.sum(WeldingLedger.receiving_qty),
        func.sum(WeldingLedger.defect_qty),
        func.sum(WeldingLedger.current_stock),
    ).where(
        WeldingLedger.order_date >= month_start,
        WeldingLedger.order_date <= as_of,
    )
    if STOCK_EXCLUDED_SUPPLIERS:
        q = q.where(WeldingLedger.supplier_cd.notin_(STOCK_EXCLUDED_SUPPLIERS))
    if supplierCd and supplierCd.strip():
        q = q.where(WeldingLedger.supplier_cd == supplierCd.strip())
    if productCd and productCd.strip():
        q = q.where(WeldingLedger.product_cd == productCd.strip())
    q = q.group_by(WeldingLedger.order_date)
    by_date = {r[0]: r for r in (await db.execute(q)).all()}

    data = []
    prev_stock = 0
    cur = month_start
    while cur <= as_of:
        r = by_date.get(cur)
        # 行が無い日は前日の在庫を引き継ぐ
        stock = int(r[4] or 0) if r else prev_stock
        data.append(
            {
                "date": cur.isoformat(),
                "order_qty": int(r[1] or 0) if r else 0,
                "receiving_qty": int(r[2] or 0) if r else 0,
                "defect_qty": int(r[3] or 0) if r else 0,
                "current_stock": stock,
            }
        )
        prev_stock = stock
        cur += timedelta(days=1)
    return {"success": True, "data": data}


@router.get("/ledger")
async def list_welding_ledger(
    startDate: str = Query(...),
    endDate: str = Query(...),
    supplierCd: Optional[str] = Query(None),
    productCd: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    firstDayOnly: bool = Query(False),
    nonZero: Optional[str] = Query(None, pattern="^(order|receiving|any)$"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(100, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    start = _parse_date(startDate)
    end = _parse_date(endDate)
    if start > end:
        raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")
    q = select(WeldingLedger).where(
        WeldingLedger.order_date >= start, WeldingLedger.order_date <= end
    )
    if supplierCd and supplierCd.strip():
        q = q.where(WeldingLedger.supplier_cd == supplierCd.strip())
    if productCd and productCd.strip():
        q = q.where(WeldingLedger.product_cd == productCd.strip())
    if firstDayOnly:
        q = q.where(func.dayofmonth(WeldingLedger.order_date) == 1)
    # 数量のある行だけ：order=注文数 / receiving=受入数・不良数 / any=いずれか（初期在庫含む）
    if nonZero == "order":
        q = q.where(WeldingLedger.order_qty > 0)
    elif nonZero == "receiving":
        q = q.where(or_(WeldingLedger.receiving_qty > 0, WeldingLedger.defect_qty > 0))
    elif nonZero == "any":
        q = q.where(
            or_(
                WeldingLedger.order_qty > 0,
                WeldingLedger.receiving_qty > 0,
                WeldingLedger.defect_qty > 0,
                WeldingLedger.initial_stock > 0,
            )
        )
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                WeldingLedger.product_cd.like(kw),
                WeldingLedger.product_name.like(kw),
                WeldingLedger.order_no.like(kw),
                WeldingLedger.supplier_name.like(kw),
            )
        )
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    q = q.order_by(
        WeldingLedger.order_date,
        WeldingLedger.supplier_name,
        WeldingLedger.product_name,
        WeldingLedger.product_cd,
        WeldingLedger.id,
    )
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": [_row_dict(r) for r in rows], "total": total}


@router.post("/ledger/generate")
async def generate_welding_ledger(
    body: GenerateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("create")),
):
    """有効な外注溶接製品 × 期間の空行を作る。既存行はスキップし、入力済み数量は保持する。"""
    start = _parse_date(body.start_date)
    end = _parse_date(body.end_date)
    if start > end:
        raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")
    if (end - start).days > 366:
        raise HTTPException(status_code=400, detail="生成期間は366日以内にしてください")

    products = (
        await db.execute(
            select(OutsourcingProcessProduct, OutsourcingSupplier)
            .join(
                OutsourcingSupplier,
                OutsourcingSupplier.supplier_cd == OutsourcingProcessProduct.supplier_cd,
            )
            .where(
                OutsourcingProcessProduct.process_type == "welding",
                OutsourcingProcessProduct.is_active == True,  # noqa: E712
                OutsourcingSupplier.is_active == True,  # noqa: E712
            )
            .order_by(OutsourcingProcessProduct.supplier_cd, OutsourcingProcessProduct.product_cd)
        )
    ).all()
    if not products:
        return {"success": True, "data": {"generated_count": 0, "skipped_count": 0}}

    existing_rows = (
        await db.execute(
            select(
                WeldingLedger.order_date, WeldingLedger.supplier_cd, WeldingLedger.product_cd
            ).where(
                WeldingLedger.order_date >= start,
                WeldingLedger.order_date <= end,
            )
        )
    ).all()
    existing = {(r[0], r[1], r[2]) for r in existing_rows}

    cal_end = end + timedelta(days=90)
    scheduled, off = await load_company_calendar_sets(db, start, cal_end)

    generated = 0
    skipped = 0
    keys: set[tuple[str, str]] = set()
    cur = start
    while cur <= end:
        for product, supplier in products:
            key = (cur, product.supplier_cd, product.product_cd)
            if key in existing:
                skipped += 1
                continue
            lead = _lead_days(product, supplier)
            row = WeldingLedger(
                order_date=cur,
                supplier_cd=product.supplier_cd,
                supplier_name=supplier.supplier_name or product.supplier_name,
                product_cd=product.product_cd,
                product_name=product.product_name,
                unit_price=product.unit_price or 0,
                lead_time_days=lead,
                delivery_date=_add_business_days(cur, lead, scheduled, off),
                order_qty=0,
                receiving_qty=0,
                defect_qty=0,
                initial_stock=0,
                current_stock=0,
                order_amount=0,
            )
            db.add(row)
            existing.add(key)
            keys.add((product.supplier_cd, product.product_cd))
            generated += 1
        cur += timedelta(days=1)

    await db.flush()
    if keys:
        await recalculate_current_stock(db, list(keys))
    return {"success": True, "data": {"generated_count": generated, "skipped_count": skipped}}


@router.post("/ledger/calculate")
async def calculate_welding_ledger(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("edit")),
):
    touched = await recalculate_current_stock(db, None)
    return {"success": True, "data": {"calculated_count": len(touched)}}


@router.post("/ledger/refresh-master")
async def refresh_welding_ledger_master(
    body: RefreshMasterBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("edit")),
):
    """
    単価・リードタイム・納期・外注先名・製品名を現在のマスタで更新する。
    既定は未注文の行のみ。include_ordered なら注文書未発行の注文済み行も対象（金額を再計算）。
    """
    start = _parse_date(body.start_date)
    end = _parse_date(body.end_date)
    if start > end:
        raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")
    if (end - start).days > 366:
        raise HTTPException(status_code=400, detail="期間は366日以内にしてください")

    not_ordered = or_(WeldingLedger.order_qty == 0, WeldingLedger.order_qty.is_(None))
    q = select(WeldingLedger).where(
        WeldingLedger.order_date >= start, WeldingLedger.order_date <= end
    )
    if body.supplier_cd and body.supplier_cd.strip():
        q = q.where(WeldingLedger.supplier_cd == body.supplier_cd.strip())
    if body.product_cd and body.product_cd.strip():
        q = q.where(WeldingLedger.product_cd == body.product_cd.strip())
    if body.include_ordered:
        q = q.where(or_(not_ordered, WeldingLedger.order_sheet_issued_at.is_(None)))
    else:
        q = q.where(not_ordered)
    rows = (await db.execute(q)).scalars().all()
    if not rows:
        return {"success": True, "data": {"updated_count": 0, "missing_count": 0}}

    master_rows = (
        await db.execute(
            select(OutsourcingProcessProduct, OutsourcingSupplier)
            .join(
                OutsourcingSupplier,
                OutsourcingSupplier.supplier_cd == OutsourcingProcessProduct.supplier_cd,
            )
            .where(OutsourcingProcessProduct.process_type == "welding")
        )
    ).all()
    masters: dict[tuple[str, str], tuple[OutsourcingProcessProduct, OutsourcingSupplier]] = {}
    for product, supplier in master_rows:
        key = (product.supplier_cd, product.product_cd)
        if key not in masters or product.is_active:
            masters[key] = (product, supplier)

    scheduled, off = await load_company_calendar_sets(db, start, end + timedelta(days=90))
    updated = 0
    missing = 0
    for r in rows:
        pair = masters.get((r.supplier_cd, r.product_cd))
        if not pair:
            missing += 1
            continue
        product, supplier = pair
        lead = _lead_days(product, supplier)
        price = float(product.unit_price or 0)
        delivery = _add_business_days(r.order_date, lead, scheduled, off)
        supplier_name = supplier.supplier_name or product.supplier_name
        product_name = product.product_name
        if (
            float(r.unit_price or 0) == price
            and int(r.lead_time_days or 0) == lead
            and r.delivery_date == delivery
            and r.supplier_name == supplier_name
            and r.product_name == product_name
        ):
            continue
        r.unit_price = product.unit_price or 0
        r.lead_time_days = lead
        r.delivery_date = delivery
        r.supplier_name = supplier_name
        r.product_name = product_name
        if int(r.order_qty or 0) > 0:
            r.order_amount = _money(int(r.order_qty or 0), price)
        updated += 1
    await db.flush()
    return {"success": True, "data": {"updated_count": updated, "missing_count": missing}}


@router.put("/ledger/{row_id}")
async def update_welding_ledger(
    row_id: int,
    body: UpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("edit")),
):
    # rollback 後に current_user を参照すると遅延ロードになるため先に取り出す
    operator = _operator(current_user)
    for attempt in range(SAVE_RETRY):
        try:
            return await _apply_update(db, row_id, body, operator)
        except IntegrityError:
            # 同時保存で同じ番号を採番した。巻き戻して最新の番号で採番し直す
            await db.rollback()
            if attempt == SAVE_RETRY - 1:
                raise HTTPException(
                    status_code=409, detail="番号の採番が競合しました。もう一度保存してください"
                )


async def _apply_update(db: AsyncSession, row_id: int, body: UpdateBody, operator: str) -> dict:
    row = (
        await db.execute(select(WeldingLedger).where(WeldingLedger.id == row_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="データが見つかりません")

    old_order_qty = int(row.order_qty or 0)
    if body.order_qty is not None:
        row.order_qty = _qty(body.order_qty, "注文数")
    if body.receiving_qty is not None:
        row.receiving_qty = _qty(body.receiving_qty, "受入数")
    if body.defect_qty is not None:
        row.defect_qty = _qty(body.defect_qty, "不良数")
    if body.initial_stock is not None:
        initial = _qty(body.initial_stock, "初期在庫")
        if initial > 0 and row.order_date.day != 1:
            raise HTTPException(status_code=400, detail="初期在庫は毎月1日の行にのみ入力できます")
        row.initial_stock = initial

    changed = [
        f for f in ("order_qty", "receiving_qty", "defect_qty") if getattr(body, f) is not None
    ]
    if "order_qty" in changed:
        row.order_amount = _money(int(row.order_qty or 0), row.unit_price)
        await _assign_order_no(db, row)
        # 発行後に注文数が変わったら注文書は古いので未発行に戻す
        if int(row.order_qty or 0) != old_order_qty:
            row.order_sheet_issued_at = None
            row.order_sheet_issued_by = None
    for field in changed:
        if field in MGMT_NO_SPECS:
            await _assign_mgmt_no(db, row, field)
    await db.flush()
    if changed:
        await sync_stock_logs(db, row, operator, changed)
    touched = await recalculate_current_stock(db, [(row.supplier_cd, row.product_cd)])
    await db.flush()
    return {
        "success": True,
        "data": {"row": _row_dict(row), "affected": [_row_dict(r) for r in touched]},
    }
