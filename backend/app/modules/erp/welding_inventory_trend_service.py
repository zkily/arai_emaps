"""溶接品在庫推移（只読）。

製品×日で、内示・溶接前在庫・社内溶接（計画/実績/在庫/推移）・倉庫在庫
（検査在庫 + 倉庫在庫）と、BOM（consume_process_cd=KT07）の部品在庫・予定使用を返す。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession

MAX_SPAN_DAYS = 62
_CHUNK = 400
# 設備能力・能率一覧と同系統。その他も対象外
_EXCLUDED_PRODUCT_TYPES = ("補給品", "試作品", "その他")

METRIC_KEYS = (
    "forecast",
    "molding_actual_plan",
    "pre_welding_inventory",
    "welding_plan",
    "welding_actual",
    "welding_inventory",
    "welding_trend",
    "warehouse_inventory",
)

_SUMMARY_EXTRA = (
    "molding_actual_plan",
    "welding_plan",
    "welding_actual",
    "welding_actual_plan",
    "welding_trend",
    "warehouse_inventory",
    "forecast_quantity",
)


def _as_int(v: Any) -> int:
    if v is None:
        return 0
    if isinstance(v, Decimal):
        return int(round(float(v)))
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return 0


def _iso(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, date):
        return v.isoformat()
    return str(v)[:10]


def _put(bucket: dict[str, int], ds: str, qty: int) -> None:
    if ds and qty:
        bucket[ds] = qty


def date_span(date_from: date, date_to: date) -> list[str]:
    if date_to < date_from:
        raise ValueError("終了日は開始日以降を指定してください")
    days = (date_to - date_from).days + 1
    if days > MAX_SPAN_DAYS:
        raise ValueError(f"期間は {MAX_SPAN_DAYS} 日以内にしてください")
    out: list[str] = []
    cur = date_from
    while cur <= date_to:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _trend_deps():
    """database.api は erp パッケージ初期化中に本モジュールを読むため、関数内で遅延 import する。"""
    from app.modules.database.api import INVENTORY_COLUMNS, _get_process_config_by_key
    from app.modules.inventory_projection.service import (
        _inventory_field,
        _load_forecast_daily_by_product_date,
        _load_product_route_sequences,
        _normalize_order_cd,
    )
    from app.modules.master.models import PartMaster, Product

    return {
        "INVENTORY_COLUMNS": INVENTORY_COLUMNS,
        "get_process_config": _get_process_config_by_key,
        "inventory_field": _inventory_field,
        "load_forecast": _load_forecast_daily_by_product_date,
        "load_sequences": _load_product_route_sequences,
        "normalize_cd": _normalize_order_cd,
        "PartMaster": PartMaster,
        "Product": Product,
    }


def _prev_welding_inventory_field(sequence: list[str], deps: dict[str, Any]) -> Optional[str]:
    """溶接直前工程の在庫列。database.api._pre_welding_inventory_from_row と同じ口径。"""
    if "welding" not in sequence:
        return None
    idx = sequence.index("welding")
    if idx <= 0:
        return None
    prev_key = sequence[idx - 1]
    cfg = deps["get_process_config"](prev_key)
    if not cfg:
        return None
    return (cfg.get("fields") or {}).get("inventory") or deps["inventory_field"](prev_key)


async def _resolve_welding_products(
    db: AsyncSession, deps: dict[str, Any]
) -> tuple[list[str], dict[str, str]]:
    """対象製品CD一覧と名称マップ（末尾1・除外タイプ・製品名昇順）。"""
    sequences = await deps["load_sequences"](db)
    welding_cds = sorted(
        cd for cd, seq in sequences.items() if "welding" in seq and cd.endswith("1")
    )
    if not welding_cds:
        return [], {}

    product_model = deps["Product"]
    name_res = await db.execute(
        select(
            product_model.product_cd,
            product_model.product_name,
            product_model.product_type,
        ).where(product_model.product_cd.in_(welding_cds))
    )
    names: dict[str, str] = {}
    allowed: list[str] = []
    for cd_raw, nm, ptype in name_res.all():
        cd = str(cd_raw or "").strip()
        if not cd:
            continue
        if str(ptype or "").strip() in _EXCLUDED_PRODUCT_TYPES:
            continue
        names[cd] = str(nm or "").strip()
        allowed.append(cd)
    welding_cds = sorted(
        allowed, key=lambda cd: ((names.get(cd) or "").casefold(), cd.casefold())
    )
    return welding_cds, names


async def get_welding_trend_filter_options(db: AsyncSession) -> dict[str, Any]:
    """製品・部品ドロップダウン用の選択肢（対象製品と同じ口径）。"""
    deps = _trend_deps()
    welding_cds, names = await _resolve_welding_products(db, deps)
    products = [
        {"product_cd": cd, "product_name": names.get(cd) or ""} for cd in welding_cds
    ]
    if not welding_cds:
        return {"products": [], "parts": []}

    bom_parts = await _load_bom_parts(db, welding_cds, date.today())
    part_cds = sorted({pcd for parts in bom_parts.values() for pcd in parts})
    part_names: dict[str, str] = {}
    if part_cds:
        part_model = deps["PartMaster"]
        name_res = await db.execute(
            select(part_model.part_cd, part_model.part_name).where(
                part_model.part_cd.in_(part_cds)
            )
        )
        for cd, nm in name_res.all():
            pcd = str(cd or "").strip()
            label = str(nm or "").strip()
            if pcd:
                part_names[pcd] = label
    parts = [
        {
            "part_cd": pcd,
            "part_name": part_names.get(pcd) or "",
        }
        for pcd in sorted(
            part_cds, key=lambda c: ((part_names.get(c) or "").casefold(), c.casefold())
        )
    ]
    return {"products": products, "parts": parts}


async def _chunked(
    db: AsyncSession, sql: str, base: dict[str, Any], cds: list[str], key: str = "cds"
) -> list[Any]:
    rows: list[Any] = []
    stmt = text(sql).bindparams(bindparam(key, expanding=True))
    for i in range(0, len(cds), _CHUNK):
        params = {**base, key: cds[i : i + _CHUNK]}
        res = await db.execute(stmt, params)
        rows.extend(res.mappings().all())
    return rows


def _summary_select_sql(inventory_columns: list[str] | tuple[str, ...]) -> str:
    cols = ["product_cd", "product_name", "date", *inventory_columns, *_SUMMARY_EXTRA]
    # warehouse_inventory は INVENTORY_COLUMNS に含まれるため重複を除く
    seen: list[str] = []
    for c in cols:
        if c not in seen:
            seen.append(c)
    select_list = ", ".join(f"ps.`{c}`" for c in seen)
    return f"""
        SELECT {select_list}
        FROM production_summarys ps
        WHERE ps.date >= :d0 AND ps.date <= :d1
          AND ps.product_cd IN :cds
    """


def _usage_sql() -> str:
    return """
        SELECT
            ps.product_cd AS product_cd,
            ps.date AS eff_date,
            NULLIF(TRIM(l.component_product_cd), '') AS part_cd,
            SUM(
                COALESCE(NULLIF(ps.welding_actual_plan, 0), ps.welding_plan, 0)
                * COALESCE(l.qty_per, 0)
                / NULLIF(COALESCE(h.base_quantity, 1), 0)
                * (1 + COALESCE(l.scrap_rate, 0) / 100)
            ) AS planned_usage
        FROM production_summarys ps
        JOIN product_bom_headers h
          ON h.id = (
              SELECT h2.id
              FROM product_bom_headers h2
              WHERE h2.parent_product_cd = ps.product_cd
                AND h2.status = 'active'
                AND (h2.effective_from IS NULL OR h2.effective_from <= ps.date)
                AND (h2.effective_to IS NULL OR h2.effective_to >= ps.date)
              ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
              LIMIT 1
          )
        JOIN product_bom_lines l
          ON l.header_id = h.id
         AND LOWER(TRIM(COALESCE(l.consume_process_cd, ''))) = 'kt07'
         AND l.component_product_cd IS NOT NULL
         AND TRIM(l.component_product_cd) <> ''
         AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
        WHERE ps.date >= :d0 AND ps.date <= :d1
          AND ps.product_cd IN :cds
        GROUP BY ps.product_cd, ps.date, NULLIF(TRIM(l.component_product_cd), '')
    """


async def get_welding_inventory_trend(
    db: AsyncSession,
    date_from: date,
    date_to: date,
    *,
    keyword: str = "",
    part_cd: str = "",
    shortage_only: bool = False,
) -> dict[str, Any]:
    deps = _trend_deps()
    dates = date_span(date_from, date_to)
    sequences = await deps["load_sequences"](db)
    welding_cds, names = await _resolve_welding_products(db, deps)
    if not welding_cds:
        return _empty(date_from, date_to, dates)

    kw = keyword.strip().lower()
    if kw:
        welding_cds = [
            cd
            for cd in welding_cds
            if kw in cd.lower() or kw in (names.get(cd) or "").lower()
        ]
    if not welding_cds:
        return _empty(date_from, date_to, dates)

    prev_field = {cd: _prev_welding_inventory_field(sequences[cd], deps) for cd in welding_cds}
    forecast_map = await deps["load_forecast"](db, date_from, date_to)

    summary_rows = await _chunked(
        db,
        _summary_select_sql(deps["INVENTORY_COLUMNS"]),
        {"d0": date_from, "d1": date_to},
        welding_cds,
    )
    by_product: dict[str, dict[str, Any]] = {}
    for raw in summary_rows:
        cd = str(raw.get("product_cd") or "").strip()
        ds = _iso(raw.get("date"))
        if not cd or not ds or cd not in prev_field:
            continue
        slot = by_product.setdefault(cd, {"name": "", "days": {}})
        nm = str(raw.get("product_name") or "").strip()
        if nm:
            slot["name"] = nm
        slot["days"][ds] = raw

    usage_rows = await _chunked(
        db, _usage_sql(), {"d0": date_from, "d1": date_to}, welding_cds
    )
    usage: dict[str, dict[str, dict[str, int]]] = {}
    part_cds: set[str] = set()
    for raw in usage_rows:
        cd = str(raw.get("product_cd") or "").strip()
        pcd = str(raw.get("part_cd") or "").strip()
        ds = _iso(raw.get("eff_date"))
        qty = _as_int(raw.get("planned_usage"))
        if not cd or not pcd or not ds or not qty:
            continue
        usage.setdefault(cd, {}).setdefault(pcd, {})[ds] = qty
        part_cds.add(pcd)

    # 部品在庫は日別に無い日もあるため、使用予定が 0 の部品も BOM から拾う
    bom_parts = await _load_bom_parts(db, welding_cds, date_to)
    for cd, parts in bom_parts.items():
        for pcd in parts:
            part_cds.add(pcd)
            usage.setdefault(cd, {}).setdefault(pcd, {})

    stock_map, part_names = await _load_part_stock_and_names(
        db, sorted(part_cds), date_from, date_to, deps
    )
    part_filter = part_cd.strip().lower()

    def _part_hit(pcd: str) -> bool:
        if not part_filter:
            return True
        return part_filter in pcd.lower() or part_filter in (part_names.get(pcd) or "").lower()

    if part_filter:
        welding_cds = [
            cd for cd in welding_cds if any(_part_hit(p) for p in usage.get(cd, {}))
        ]

    products: list[dict[str, Any]] = []
    shortage_count = 0
    for cd in welding_cds:
        slot = by_product.get(cd) or {"name": "", "days": {}}
        product_name = names.get(cd) or slot.get("name") or ""
        field = prev_field.get(cd)
        applicable = bool(field)
        metrics = {k: {} for k in METRIC_KEYS}
        norm = deps["normalize_cd"](cd)
        forecast_series = forecast_map.get(cd) or forecast_map.get(norm) or {}
        use_order_forecast = bool(forecast_series)
        product_shortage = False

        for ds in dates:
            row = (slot.get("days") or {}).get(ds)
            if use_order_forecast:
                _put(metrics["forecast"], ds, int(forecast_series.get(ds) or 0))
            elif row is not None:
                _put(metrics["forecast"], ds, _as_int(row.get("forecast_quantity")))
            if row is None:
                continue
            _put(metrics["molding_actual_plan"], ds, _as_int(row.get("molding_actual_plan")))
            if applicable and field:
                _put(metrics["pre_welding_inventory"], ds, _as_int(row.get(field)))
            plan = _as_int(row.get("welding_plan"))
            actual = _as_int(row.get("welding_actual"))
            inv = _as_int(row.get("welding_inventory"))
            trend = _as_int(row.get("welding_trend"))
            # 倉庫在庫 = 検査在庫 + 倉庫在庫（inventory_api 等と同じ口径）
            wh = _as_int(row.get("warehouse_inventory")) + _as_int(
                row.get("inspection_inventory")
            )
            _put(metrics["welding_plan"], ds, plan)
            _put(metrics["welding_actual"], ds, actual)
            _put(metrics["welding_inventory"], ds, inv)
            _put(metrics["welding_trend"], ds, trend)
            _put(metrics["warehouse_inventory"], ds, wh)
            if inv < 0:
                product_shortage = True

        parts_out: list[dict[str, Any]] = []
        for pcd in sorted(usage.get(cd, {})):
            if not _part_hit(pcd):
                continue
            planned = usage.get(cd, {}).get(pcd) or {}
            stock_daily: dict[str, int] = {}
            part_shortage = False
            for ds in dates:
                stk = stock_map.get((pcd, ds))
                if stk:
                    stock_daily[ds] = stk
                need = int(planned.get(ds) or 0)
                have = int(stock_map.get((pcd, ds)) or 0)
                if need > 0 and have < need:
                    part_shortage = True
                    product_shortage = True
            parts_out.append(
                {
                    "part_cd": pcd,
                    "part_name": part_names.get(pcd) or "",
                    "stock": stock_daily,
                    "planned_usage": {k: v for k, v in planned.items() if v},
                    "has_shortage": part_shortage,
                }
            )

        if shortage_only and not product_shortage:
            continue
        if product_shortage:
            shortage_count += 1
        item: dict[str, Any] = {
            "product_cd": cd,
            "product_name": product_name,
            "pre_welding_applicable": applicable,
            "has_shortage": product_shortage,
            "metrics": metrics if applicable else {**metrics, "pre_welding_inventory": None},
            "parts": parts_out,
        }
        products.append(item)

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "dates": dates,
        "product_count": len(products),
        "shortage_count": shortage_count,
        "products": products,
    }


def _empty(date_from: date, date_to: date, dates: list[str]) -> dict[str, Any]:
    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "dates": dates,
        "product_count": 0,
        "shortage_count": 0,
        "products": [],
    }


async def _load_bom_parts(
    db: AsyncSession, product_cds: list[str], as_of: date
) -> dict[str, list[str]]:
    """対象日に有効な KT07 部品（使用予定が 0 の日でも行を出す）。"""
    sql = """
        SELECT
            h.parent_product_cd AS product_cd,
            NULLIF(TRIM(l.component_product_cd), '') AS part_cd
        FROM product_bom_headers h
        JOIN product_bom_lines l
          ON l.header_id = h.id
         AND LOWER(TRIM(COALESCE(l.consume_process_cd, ''))) = 'kt07'
         AND l.component_product_cd IS NOT NULL
         AND TRIM(l.component_product_cd) <> ''
         AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
        WHERE h.status = 'active'
          AND (h.effective_from IS NULL OR h.effective_from <= :as_of)
          AND (h.effective_to IS NULL OR h.effective_to >= :as_of)
          AND h.parent_product_cd IN :cds
          AND h.id = (
              SELECT h2.id
              FROM product_bom_headers h2
              WHERE h2.parent_product_cd = h.parent_product_cd
                AND h2.status = 'active'
                AND (h2.effective_from IS NULL OR h2.effective_from <= :as_of)
                AND (h2.effective_to IS NULL OR h2.effective_to >= :as_of)
              ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
              LIMIT 1
          )
    """
    rows = await _chunked(db, sql, {"as_of": as_of}, product_cds)
    out: dict[str, list[str]] = {}
    seen: dict[str, set[str]] = {}
    for raw in rows:
        cd = str(raw.get("product_cd") or "").strip()
        pcd = str(raw.get("part_cd") or "").strip()
        if not cd or not pcd:
            continue
        bucket = seen.setdefault(cd, set())
        if pcd in bucket:
            continue
        bucket.add(pcd)
        out.setdefault(cd, []).append(pcd)
    return out


async def _load_part_stock_and_names(
    db: AsyncSession,
    part_cds: list[str],
    date_from: date,
    date_to: date,
    deps: dict[str, Any],
) -> tuple[dict[tuple[str, str], int], dict[str, str]]:
    stock: dict[tuple[str, str], int] = {}
    names: dict[str, str] = {}
    if not part_cds:
        return stock, names
    stock_sql = """
        SELECT part_cd, part_name, date, current_stock
        FROM part_stock
        WHERE date >= :d0 AND date <= :d1
          AND part_cd IN :cds
    """
    for raw in await _chunked(db, stock_sql, {"d0": date_from, "d1": date_to}, part_cds):
        pcd = str(raw.get("part_cd") or "").strip()
        ds = _iso(raw.get("date"))
        if not pcd or not ds:
            continue
        qty = _as_int(raw.get("current_stock"))
        if qty:
            stock[(pcd, ds)] = qty
        nm = str(raw.get("part_name") or "").strip()
        if nm and pcd not in names:
            names[pcd] = nm

    part_model = deps["PartMaster"]
    name_res = await db.execute(
        select(part_model.part_cd, part_model.part_name).where(part_model.part_cd.in_(part_cds))
    )
    for cd, nm in name_res.all():
        pcd = str(cd or "").strip()
        label = str(nm or "").strip()
        if pcd and label:
            names[pcd] = label
    return stock, names
