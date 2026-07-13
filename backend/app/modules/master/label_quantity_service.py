"""ラベル枚数管理：需要算出・充足判定・複数月ロール計算"""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime
from typing import Any, Literal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.database.models import ProductionSummary
from app.modules.erp.models import OrderMonthly
from app.modules.master.models import (
    LabelQuantityMonthly,
    Product,
    ProductLabelConfig,
    ProductUseLabelConfig,
)

LabelType = Literal["molding", "product_use"]

SAFETY_FACTOR = 1.1
LABELS_PER_SHEET = 6
LABEL_TYPE_MOLDING: LabelType = "molding"
LABEL_TYPE_PRODUCT_USE: LabelType = "product_use"
VALID_LABEL_TYPES = frozenset({LABEL_TYPE_MOLDING, LABEL_TYPE_PRODUCT_USE})
YEAR_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def parse_year_month(year_month: str) -> tuple[int, int, date, date]:
    """YYYY-MM → (year, month, start_date, end_date)。"""
    ym = (year_month or "").strip()
    if not YEAR_MONTH_RE.match(ym):
        raise ValueError("year_month は YYYY-MM 形式で指定してください")
    year = int(ym[:4])
    month = int(ym[5:7])
    if month < 1 or month > 12:
        raise ValueError("year_month の月が不正です")
    last_day = calendar.monthrange(year, month)[1]
    return year, month, date(year, month, 1), date(year, month, last_day)


def add_months(year_month: str, delta: int) -> str:
    year, month, _, _ = parse_year_month(year_month)
    idx = year * 12 + (month - 1) + int(delta)
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def month_range(start_month: str, months: int) -> list[str]:
    n = max(1, min(3, int(months or 1)))
    parse_year_month(start_month)
    return [add_months(start_month.strip(), i) for i in range(n)]


def normalize_label_type(label_type: str | None) -> LabelType:
    val = (label_type or "").strip()
    if val not in VALID_LABEL_TYPES:
        raise ValueError("label_type は molding / product_use のいずれかです")
    return val  # type: ignore[return-value]


def calc_required_qty(demand_units: int, unit_qty: int | None) -> int | None:
    """必要枚数 = CEIL(需要本数 × 1.1 / 入数)。不捨全入。"""
    if unit_qty is None or unit_qty <= 0:
        return None
    demand = max(0, int(demand_units or 0))
    if demand <= 0:
        return 0
    uq = int(unit_qty)
    return (demand * 11 + uq * 10 - 1) // (uq * 10)


def calc_shortage(required_qty: int | None, opening_stock: int) -> int:
    if required_qty is None:
        return 0
    return max(0, int(required_qty) - int(opening_stock or 0))


def calc_issue_paper_sheets(
    required_qty: int | None,
    issued_qty: int = 0,
    *,
    labels_per_sheet: int = LABELS_PER_SHEET,
) -> int:
    """発行予定（紙枚数）= CEIL(max(0, 必要枚数 − 発行済) / 6)。不捨全入。"""
    if required_qty is None:
        return 0
    remain = max(0, int(required_qty) - max(0, int(issued_qty or 0)))
    if remain <= 0:
        return 0
    per = max(1, int(labels_per_sheet or LABELS_PER_SHEET))
    return (remain + per - 1) // per


def calc_closing_theory(
    opening_stock: int,
    issued_qty: int,
    required_qty: int | None,
) -> int | None:
    """月末理論残 = 月初 + 発行済 − 必要枚数。必要枚数未設定時は None。"""
    if required_qty is None:
        return None
    return int(opening_stock or 0) + max(0, int(issued_qty or 0)) - int(required_qty)


async def _load_demand_map(
    db: AsyncSession,
    *,
    label_type: LabelType,
    year: int,
    month: int,
    start_date: date,
    end_date: date,
) -> dict[str, int]:
    if label_type == LABEL_TYPE_PRODUCT_USE:
        q = (
            select(
                OrderMonthly.product_cd,
                func.coalesce(func.sum(OrderMonthly.forecast_units), 0).label("qty"),
            )
            .where(and_(OrderMonthly.year == year, OrderMonthly.month == month))
            .group_by(OrderMonthly.product_cd)
        )
    else:
        q = (
            select(
                ProductionSummary.product_cd,
                func.coalesce(func.sum(ProductionSummary.molding_plan), 0).label("qty"),
            )
            .where(
                and_(
                    ProductionSummary.date >= start_date,
                    ProductionSummary.date <= end_date,
                )
            )
            .group_by(ProductionSummary.product_cd)
        )
    res = await db.execute(q)
    out: dict[str, int] = {}
    for product_cd, qty in res.all():
        if product_cd:
            out[str(product_cd)] = int(qty or 0)
    return out


async def _load_config_rows(
    db: AsyncSession, label_type: LabelType
) -> list[dict[str, Any]]:
    if label_type == LABEL_TYPE_PRODUCT_USE:
        q = (
            select(
                ProductUseLabelConfig.product_cd,
                ProductUseLabelConfig.use_label_product_name,
                ProductUseLabelConfig.unit_qty,
                ProductUseLabelConfig.supply_type,
                Product.product_name,
            )
            .outerjoin(Product, Product.product_cd == ProductUseLabelConfig.product_cd)
            .order_by(ProductUseLabelConfig.product_cd)
        )
        res = await db.execute(q)
        return [
            {
                "product_cd": r.product_cd,
                "label_product_name": r.use_label_product_name,
                "master_product_name": r.product_name,
                "unit_qty": r.unit_qty,
                "supply_type": r.supply_type or "社内",
            }
            for r in res.all()
        ]

    q = (
        select(
            ProductLabelConfig.product_cd,
            ProductLabelConfig.label_product_name,
            ProductLabelConfig.process_unit_qty,
            ProductLabelConfig.supply_type,
            Product.product_name,
        )
        .outerjoin(Product, Product.product_cd == ProductLabelConfig.product_cd)
        .order_by(ProductLabelConfig.product_cd)
    )
    res = await db.execute(q)
    return [
        {
            "product_cd": r.product_cd,
            "label_product_name": r.label_product_name,
            "master_product_name": r.product_name,
            "unit_qty": r.process_unit_qty,
            "supply_type": r.supply_type or "社内",
        }
        for r in res.all()
    ]


async def _load_saved_maps(
    db: AsyncSession, *, year_months: list[str], label_type: LabelType
) -> dict[str, dict[str, LabelQuantityMonthly]]:
    """year_month → product_cd → row"""
    if not year_months:
        return {}
    q = select(LabelQuantityMonthly).where(
        and_(
            LabelQuantityMonthly.year_month.in_(year_months),
            LabelQuantityMonthly.label_type == label_type,
        )
    )
    res = await db.execute(q)
    out: dict[str, dict[str, LabelQuantityMonthly]] = {ym: {} for ym in year_months}
    for row in res.scalars().all():
        out.setdefault(row.year_month, {})[row.product_cd] = row
    return out


def _month_snap(
    *,
    year_month: str,
    label_type: LabelType,
    cfg: dict[str, Any],
    demand_units: int,
    opening_stock: int,
    opening_locked: bool,
    issue_qty: int,
    issued_qty: int,
    saved: LabelQuantityMonthly | None,
) -> dict[str, Any]:
    unit_qty = cfg.get("unit_qty")
    unit_qty_int = int(unit_qty) if unit_qty is not None else None
    required_qty = calc_required_qty(demand_units, unit_qty_int)
    suggested_issue = calc_issue_paper_sheets(
        required_qty, issued_qty, labels_per_sheet=LABELS_PER_SHEET
    )
    shortage_qty = calc_shortage(required_qty, opening_stock)
    closing = calc_closing_theory(opening_stock, issued_qty, required_qty)
    unit_missing = unit_qty_int is None or unit_qty_int <= 0
    is_sufficient = (not unit_missing) and required_qty is not None and opening_stock >= required_qty
    return {
        "id": saved.id if saved is not None else None,
        "year_month": year_month,
        "label_type": label_type,
        "demand_units": int(demand_units or 0),
        "required_qty": required_qty,
        "opening_stock": int(opening_stock),
        "opening_locked": bool(opening_locked),
        "shortage_qty": shortage_qty,
        "issue_qty": max(0, int(issue_qty)),
        "issued_qty": max(0, int(issued_qty)),
        "suggested_issue_sheets": suggested_issue,
        "issue_labels": max(0, int(issue_qty)) * LABELS_PER_SHEET,
        "closing_theory": closing,
        "is_sufficient": is_sufficient,
        "unit_qty_missing": unit_missing,
        "labels_per_sheet": LABELS_PER_SHEET,
        "is_saved": saved is not None,
        "updated_by": saved.updated_by if saved is not None else None,
        "updated_at": saved.updated_at.isoformat() if saved is not None and saved.updated_at else None,
    }


def build_period_kpi(products: list[dict[str, Any]]) -> dict[str, Any]:
    month_snaps: list[dict[str, Any]] = []
    for p in products:
        month_snaps.extend(p.get("months") or [])
    total_products = len(products)
    insufficient_products = sum(
        1
        for p in products
        if any(not m.get("is_sufficient") for m in (p.get("months") or []))
    )
    return {
        "total": total_products,
        "sufficient": total_products - insufficient_products,
        "insufficient": insufficient_products,
        "unit_qty_missing": sum(1 for p in products if p.get("unit_qty_missing")),
        "shortage_qty_sum": sum(int(m.get("shortage_qty") or 0) for m in month_snaps),
        "issue_qty_sum": sum(int(m.get("issue_qty") or 0) for m in month_snaps),
        "issued_qty_sum": sum(int(m.get("issued_qty") or 0) for m in month_snaps),
        "opening_stock_sum": sum(int(m.get("opening_stock") or 0) for m in month_snaps),
        "required_qty_sum": sum(
            int(m.get("required_qty") or 0) for m in month_snaps if m.get("required_qty") is not None
        ),
        "demand_units_sum": sum(int(m.get("demand_units") or 0) for m in month_snaps),
        "closing_theory_sum": sum(
            int(m.get("closing_theory") or 0)
            for m in month_snaps
            if m.get("closing_theory") is not None
        ),
    }


def _flatten_for_compat(product: dict[str, Any]) -> dict[str, Any]:
    """1ヶ月表示互換用：先頭月をフラット化。"""
    months = product.get("months") or []
    first = months[0] if months else {}
    return {
        **{k: v for k, v in product.items() if k != "months"},
        **first,
        "months": months,
        "last_issue_history": product.get("last_issue_history"),
        "closing_theory": first.get("closing_theory"),
        "opening_locked": first.get("opening_locked", False),
        "issue_labels": first.get("issue_labels"),
        "issued_qty": first.get("issued_qty"),
    }


async def build_label_quantity_period(
    db: AsyncSession,
    *,
    start_month: str,
    months: int = 1,
    label_type: str,
    keyword: str | None = None,
    sufficiency: str | None = None,
    supply_type: str | None = None,
    apply_roll_preview: bool = True,
) -> dict[str, Any]:
    """期間一覧。apply_roll_preview=True のとき DB未保存月の月初のみ上月末理論残でプレビュー。"""
    lt = normalize_label_type(label_type)
    ym_list = month_range(start_month, months)
    configs = await _load_config_rows(db, lt)
    saved_maps = await _load_saved_maps(db, year_months=ym_list, label_type=lt)

    demand_by_month: dict[str, dict[str, int]] = {}
    for ym in ym_list:
        year, month, start_date, end_date = parse_year_month(ym)
        demand_by_month[ym] = await _load_demand_map(
            db, label_type=lt, year=year, month=month, start_date=start_date, end_date=end_date
        )

    products: list[dict[str, Any]] = []
    for cfg in configs:
        product_cd = cfg["product_cd"]
        unit_qty = cfg.get("unit_qty")
        unit_qty_int = int(unit_qty) if unit_qty is not None else None
        unit_missing = unit_qty_int is None or unit_qty_int <= 0

        month_rows: list[dict[str, Any]] = []
        prev_closing: int | None = None
        history: str | None = None

        for idx, ym in enumerate(ym_list):
            saved = saved_maps.get(ym, {}).get(product_cd)
            if saved and saved.last_issue_history and not history:
                history = saved.last_issue_history

            demand = demand_by_month.get(ym, {}).get(product_cd, 0)
            locked = bool(saved.opening_locked) if saved is not None else False

            if saved is not None:
                opening = int(saved.opening_stock or 0)
                issue_qty = int(saved.issue_qty or 0)
                issued_qty = int(saved.issued_qty or 0)
            else:
                opening = 0
                issued_qty = 0
                issue_qty = calc_issue_paper_sheets(
                    calc_required_qty(demand, unit_qty_int),
                    issued_qty,
                    labels_per_sheet=LABELS_PER_SHEET,
                )

            # ロールプレビュー：DB未保存月のみ上月末理論残を月初に適用
            # （保存済みの月初は再読込で消さない。期間再計算側で未ロック分を書き込む）
            if (
                apply_roll_preview
                and idx > 0
                and saved is None
                and prev_closing is not None
            ):
                opening = int(prev_closing)

            snap = _month_snap(
                year_month=ym,
                label_type=lt,
                cfg=cfg,
                demand_units=demand,
                opening_stock=opening,
                opening_locked=locked,
                issue_qty=issue_qty,
                issued_qty=issued_qty,
                saved=saved,
            )
            month_rows.append(snap)
            prev_closing = snap.get("closing_theory")

        # 履歴：開始月の保存値優先、なければ期間内の最初の非空
        start_saved = saved_maps.get(ym_list[0], {}).get(product_cd)
        if start_saved and start_saved.last_issue_history:
            history = start_saved.last_issue_history

        products.append(
            {
                "product_cd": product_cd,
                "label_product_name": cfg.get("label_product_name"),
                "master_product_name": cfg.get("master_product_name"),
                "supply_type": cfg.get("supply_type") or "社内",
                "unit_qty": unit_qty_int,
                "unit_qty_missing": unit_missing,
                "last_issue_history": history,
                "labels_per_sheet": LABELS_PER_SHEET,
                "safety_factor": SAFETY_FACTOR,
                "months": month_rows,
            }
        )

    kw = (keyword or "").strip().lower()
    if kw:
        products = [
            p
            for p in products
            if kw in (p.get("product_cd") or "").lower()
            or kw in (p.get("label_product_name") or "").lower()
            or kw in (p.get("master_product_name") or "").lower()
        ]

    st = (supply_type or "").strip()
    if st:
        products = [p for p in products if (p.get("supply_type") or "") == st]

    suf = (sufficiency or "").strip().lower()
    if suf in ("ok", "sufficient"):
        products = [p for p in products if all(m.get("is_sufficient") for m in p.get("months") or [])]
    elif suf in ("ng", "insufficient", "shortage"):
        products = [
            p for p in products if any(not m.get("is_sufficient") for m in p.get("months") or [])
        ]

    flat_list = [_flatten_for_compat(p) for p in products]
    return {
        "start_month": ym_list[0],
        "months_count": len(ym_list),
        "month_keys": ym_list,
        "list": flat_list,
        "products": products,
        "kpi": build_period_kpi(products),
        "safety_factor": SAFETY_FACTOR,
        "labels_per_sheet": LABELS_PER_SHEET,
    }


async def build_label_quantity_list(
    db: AsyncSession,
    *,
    year_month: str,
    label_type: str,
    keyword: str | None = None,
    sufficiency: str | None = None,
    supply_type: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    result = await build_label_quantity_period(
        db,
        start_month=year_month,
        months=1,
        label_type=label_type,
        keyword=keyword,
        sufficiency=sufficiency,
        supply_type=supply_type,
        apply_roll_preview=False,
    )
    return result["list"], result["kpi"]


async def apply_issue_qty_defaults(
    db: AsyncSession,
    *,
    start_month: str,
    months: int = 1,
    label_type: str,
    updated_by: str | None = None,
    only_unsaved: bool = False,
) -> dict[str, Any]:
    """期間内の発行予定（紙枚数）を CEIL(max(0,必要−発行済)/6) で埋める。"""
    lt = normalize_label_type(label_type)
    ym_list = month_range(start_month, months)
    configs = await _load_config_rows(db, lt)
    saved_maps = await _load_saved_maps(db, year_months=ym_list, label_type=lt)

    created = 0
    updated = 0
    for ym in ym_list:
        year, month, start_date, end_date = parse_year_month(ym)
        demand_map = await _load_demand_map(
            db, label_type=lt, year=year, month=month, start_date=start_date, end_date=end_date
        )
        for cfg in configs:
            product_cd = cfg["product_cd"]
            saved = saved_maps.get(ym, {}).get(product_cd)
            if only_unsaved and saved is not None:
                continue
            unit_qty = cfg.get("unit_qty")
            unit_qty_int = int(unit_qty) if unit_qty is not None else None
            issued_now = int(saved.issued_qty or 0) if saved is not None else 0
            issue_sheets = calc_issue_paper_sheets(
                calc_required_qty(demand_map.get(product_cd, 0), unit_qty_int),
                issued_now,
                labels_per_sheet=LABELS_PER_SHEET,
            )
            if saved is None:
                db.add(
                    LabelQuantityMonthly(
                        year_month=ym,
                        label_type=lt,
                        product_cd=product_cd,
                        opening_stock=0,
                        opening_locked=False,
                        issue_qty=issue_sheets,
                        issued_qty=0,
                        last_issue_history=None,
                        updated_by=updated_by,
                    )
                )
                created += 1
            else:
                saved.issue_qty = issue_sheets
                saved.updated_by = updated_by
                updated += 1

    await db.commit()
    period = await build_label_quantity_period(
        db, start_month=start_month, months=months, label_type=lt, apply_roll_preview=True
    )
    return {"created": created, "updated": updated, **period}


async def recalculate_period_roll(
    db: AsyncSession,
    *,
    start_month: str,
    months: int = 1,
    label_type: str,
    fill_issue_qty: bool = True,
    updated_by: str | None = None,
) -> dict[str, Any]:
    """期間再計算：需要再取得・発行紙更新（任意）・未ロック月初へ上月末理論残を書き込み。"""
    lt = normalize_label_type(label_type)
    ym_list = month_range(start_month, months)
    configs = await _load_config_rows(db, lt)
    saved_maps = await _load_saved_maps(db, year_months=ym_list, label_type=lt)

    demand_by_month: dict[str, dict[str, int]] = {}
    for ym in ym_list:
        year, month, start_date, end_date = parse_year_month(ym)
        demand_by_month[ym] = await _load_demand_map(
            db, label_type=lt, year=year, month=month, start_date=start_date, end_date=end_date
        )

    rolled = 0
    issue_updated = 0
    created = 0

    for cfg in configs:
        product_cd = cfg["product_cd"]
        unit_qty = cfg.get("unit_qty")
        unit_qty_int = int(unit_qty) if unit_qty is not None else None
        prev_closing: int | None = None

        for idx, ym in enumerate(ym_list):
            demand = demand_by_month.get(ym, {}).get(product_cd, 0)
            saved = saved_maps.get(ym, {}).get(product_cd)
            locked = bool(saved.opening_locked) if saved is not None else False
            issued_qty = int(saved.issued_qty or 0) if saved is not None else 0
            suggested_issue = calc_issue_paper_sheets(
                calc_required_qty(demand, unit_qty_int),
                issued_qty,
                labels_per_sheet=LABELS_PER_SHEET,
            )

            if saved is None:
                opening = int(prev_closing) if (idx > 0 and prev_closing is not None) else 0
                issue_qty = suggested_issue
                issued_qty = 0
                row = LabelQuantityMonthly(
                    year_month=ym,
                    label_type=lt,
                    product_cd=product_cd,
                    opening_stock=opening,
                    opening_locked=False,
                    issue_qty=issue_qty,
                    issued_qty=0,
                    last_issue_history=None,
                    updated_by=updated_by,
                )
                db.add(row)
                saved_maps.setdefault(ym, {})[product_cd] = row
                created += 1
                if fill_issue_qty:
                    issue_updated += 1
                if idx > 0 and prev_closing is not None:
                    rolled += 1
            else:
                if fill_issue_qty:
                    saved.issue_qty = suggested_issue
                    issue_updated += 1
                if idx > 0 and not locked and prev_closing is not None:
                    saved.opening_stock = int(prev_closing)
                    rolled += 1
                saved.updated_by = updated_by
                opening = int(saved.opening_stock or 0)
                issue_qty = int(saved.issue_qty or 0)
                issued_qty = int(saved.issued_qty or 0)

            required = calc_required_qty(demand, unit_qty_int)
            prev_closing = calc_closing_theory(opening, issued_qty, required)

    await db.commit()
    period = await build_label_quantity_period(
        db, start_month=start_month, months=months, label_type=lt, apply_roll_preview=True
    )
    return {
        "created": created,
        "rolled_openings": rolled,
        "issue_updated": issue_updated,
        **period,
    }


async def batch_upsert_label_quantity(
    db: AsyncSession,
    *,
    label_type: str,
    items: list[dict[str, Any]],
    updated_by: str | None = None,
    start_month: str | None = None,
    months: int = 1,
) -> dict[str, Any]:
    """複数月一括保存。item に year_month 必須（なければ start_month）。"""
    lt = normalize_label_type(label_type)
    ym_hint = start_month.strip() if start_month else None
    if ym_hint:
        parse_year_month(ym_hint)

    # 対象月を収集
    year_months: set[str] = set()
    for raw in items:
        ym = (raw.get("year_month") or ym_hint or "").strip()
        if ym:
            parse_year_month(ym)
            year_months.add(ym)
    if not year_months and ym_hint:
        year_months.update(month_range(ym_hint, months))

    saved_maps = await _load_saved_maps(db, year_months=sorted(year_months), label_type=lt)
    saved_count = 0

    # product 単位の履歴（開始月へ）
    history_by_product: dict[str, str | None] = {}

    for raw in items:
        product_cd = (raw.get("product_cd") or "").strip()
        if not product_cd:
            continue
        ym = (raw.get("year_month") or ym_hint or "").strip()
        if not ym:
            continue
        opening_stock = int(raw.get("opening_stock") or 0)
        issue_qty = max(0, int(raw.get("issue_qty") or 0))
        issued_qty = max(0, int(raw.get("issued_qty") or 0))
        opening_locked = bool(raw.get("opening_locked") or False)
        if "last_issue_history" in raw:
            hist_val = raw.get("last_issue_history")
            history_by_product[product_cd] = (
                str(hist_val).strip() if hist_val is not None and str(hist_val).strip() else None
            )

        row = saved_maps.get(ym, {}).get(product_cd)
        if row is None:
            row = LabelQuantityMonthly(
                year_month=ym,
                label_type=lt,
                product_cd=product_cd,
                opening_stock=opening_stock,
                opening_locked=opening_locked,
                issue_qty=issue_qty,
                issued_qty=issued_qty,
                last_issue_history=None,
                updated_by=updated_by,
            )
            db.add(row)
            saved_maps.setdefault(ym, {})[product_cd] = row
        else:
            row.opening_stock = opening_stock
            row.opening_locked = opening_locked
            row.issue_qty = issue_qty
            row.issued_qty = issued_qty
            row.updated_by = updated_by
        saved_count += 1

    # 履歴は開始月（または当該商品の最初の月）へ保存
    hist_month = ym_hint or (sorted(year_months)[0] if year_months else None)
    if hist_month:
        for product_cd, hist in history_by_product.items():
            row = saved_maps.get(hist_month, {}).get(product_cd)
            if row is None:
                row = LabelQuantityMonthly(
                    year_month=hist_month,
                    label_type=lt,
                    product_cd=product_cd,
                    opening_stock=0,
                    opening_locked=False,
                    issue_qty=0,
                    issued_qty=0,
                    last_issue_history=hist,
                    updated_by=updated_by,
                )
                db.add(row)
                saved_maps.setdefault(hist_month, {})[product_cd] = row
                saved_count += 1
            else:
                row.last_issue_history = hist
                row.updated_by = updated_by

    await db.commit()
    period_start = ym_hint or sorted(year_months)[0]
    period = await build_label_quantity_period(
        db,
        start_month=period_start,
        months=months if ym_hint else len(year_months) or 1,
        label_type=lt,
        apply_roll_preview=True,
    )
    return {"saved": saved_count, **period}


def _format_print_history(
    *,
    paper_sheets: int,
    label_count: int | None = None,
    when: datetime | None = None,
) -> str:
    from app.core.datetime_utils import now_jst

    ts = (when or now_jst()).strftime("%Y-%m-%d %H:%M")
    sheets = max(0, int(paper_sheets or 0))
    if label_count is not None and int(label_count) > 0:
        return f"{ts} 印刷 {sheets}紙（{int(label_count)}枚）"
    return f"{ts} 印刷 {sheets}紙"


async def record_label_print_history(
    db: AsyncSession,
    *,
    label_type: str,
    items: list[dict[str, Any]],
    year_month: str | None = None,
    updated_by: str | None = None,
) -> dict[str, Any]:
    """印刷実行後に最終発行・印刷履歴を当月レコードへ反映。"""
    from app.core.datetime_utils import now_jst

    lt = normalize_label_type(label_type)
    now = now_jst()
    ym = (year_month or "").strip() or now.strftime("%Y-%m")
    parse_year_month(ym)

    saved_map = (await _load_saved_maps(db, year_months=[ym], label_type=lt)).get(ym, {})
    updated = 0
    created = 0
    results: list[dict[str, Any]] = []

    for raw in items:
        product_cd = (raw.get("product_cd") or "").strip()
        if not product_cd:
            continue
        paper_sheets = max(0, int(raw.get("paper_sheets") or 0))
        labels_per_sheet = int(raw.get("labels_per_sheet") or LABELS_PER_SHEET)
        if labels_per_sheet <= 0:
            labels_per_sheet = LABELS_PER_SHEET
        label_count = raw.get("label_count")
        if label_count is None:
            label_count = paper_sheets * labels_per_sheet
        else:
            label_count = max(0, int(label_count))

        history = _format_print_history(
            paper_sheets=paper_sheets, label_count=label_count, when=now
        )
        row = saved_map.get(product_cd)
        if row is None:
            row = LabelQuantityMonthly(
                year_month=ym,
                label_type=lt,
                product_cd=product_cd,
                opening_stock=0,
                opening_locked=False,
                issue_qty=0,
                issued_qty=label_count,
                last_issue_history=history,
                updated_by=updated_by,
            )
            db.add(row)
            saved_map[product_cd] = row
            created += 1
        else:
            # 発行済は当月累計加算（印刷枚数）
            row.issued_qty = max(0, int(row.issued_qty or 0)) + label_count
            row.last_issue_history = history
            row.updated_by = updated_by
            updated += 1
        results.append(
            {
                "product_cd": product_cd,
                "year_month": ym,
                "last_issue_history": history,
                "paper_sheets": paper_sheets,
                "label_count": label_count,
                "issued_qty": int(row.issued_qty or 0),
            }
        )

    await db.commit()
    return {
        "year_month": ym,
        "created": created,
        "updated": updated,
        "items": results,
    }
