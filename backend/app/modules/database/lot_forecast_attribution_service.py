"""管理コード → 日内示归属（Pegging Layer）。"""
from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.database.api import (
    _get_process_config_by_key,
    _get_route_sequence,
    _num,
    _subtract_business_days,
)
from app.modules.database.forming_daily_plan_service import (
    PROCESS_LT_MAP,
    _load_molding_production_orders,
    daterange_inclusive,
    parse_iso_date,
)
from app.modules.database.models import LotForecastAttribution, ProductionSummary
from app.modules.erp.models import OrderDaily
from app.modules.master.models import Destination, Product

POST_MOLDING_PROCESS_KEYS = (
    "plating",
    "outsourced_plating",
    "welding",
    "outsourced_welding",
    "inspection",
    "warehouse",
    "outsourced_warehouse",
)

# 内示帰属：成型後在庫を先に消化し、その後 7/1 以降の成型計画で FIFO する基準日
ATTRIBUTION_ANCHOR_DATE = date(2026, 7, 1)

SOURCE_ENTITY_PRODUCTION_SUMMARY = "production_summarys"
SOURCE_ENTITY_PS_MOLDING_PLAN = "ps_molding_plan"


def _clip_varchar(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    s = str(value)
    return s if len(s) <= max_len else s[:max_len]


def _stock_allocation_rule(process_key: str) -> str:
    """allocation_rule は varchar(32) のため短い形式にする。"""
    return _clip_varchar(f"STK:{process_key}", 32) or "STK"

def attribution_effective_start(start_date: date) -> date:
    return max(start_date, ATTRIBUTION_ANCHOR_DATE)


def _sql_date_lte(column_sql: str, pe: date | None) -> str:
    """pe が None のときは上限なし（開始日から先をすべて対象）。"""
    return f" AND {column_sql} <= :pe" if pe is not None else ""


def _add_business_days(from_date: date, days: int) -> date:
    """営業日（土日除外）を加算。"""
    if days <= 0:
        return from_date
    current = from_date
    remaining = int(days)
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


async def _load_canonical_route_context(
    db: AsyncSession,
    canonical: str,
) -> tuple[list[str], list[str]] | None:
    """(route_sequence, post_molding_keys)"""
    pq = select(Product.route_cd).where(Product.product_cd == canonical)
    pres = await db.execute(pq)
    prow = pres.first()
    if not prow:
        return None
    route_cd = str(prow.route_cd or "").strip()
    sequence = await _get_route_sequence(db, route_cd)
    if "molding" not in sequence:
        return None
    mold_idx = sequence.index("molding")
    post_keys = [k for k in sequence[mold_idx + 1 :] if k in POST_MOLDING_PROCESS_KEYS]
    return sequence, post_keys


async def _load_production_summary_rows_at_anchor(
    db: AsyncSession,
    canonical: str,
    anchor: date,
) -> list[ProductionSummary]:
    """基準日の production_summarys（等価グループ：canonical + 同一前缀 variant）。"""
    prefix = product_cd_prefix(canonical)
    product_filter = (
        or_(
            ProductionSummary.product_cd == canonical,
            ProductionSummary.product_cd.like(f"{prefix}%"),
        )
        if prefix
        else ProductionSummary.product_cd == canonical
    )

    q = select(ProductionSummary).where(
        ProductionSummary.date == anchor,
        product_filter,
    )
    res = await db.execute(q)
    rows = list(res.scalars().all())
    if rows:
        return rows

    q2 = (
        select(ProductionSummary)
        .where(ProductionSummary.date <= anchor, product_filter)
        .order_by(ProductionSummary.date.desc())
    )
    res2 = await db.execute(q2)
    all_recent = list(res2.scalars().all())
    if not all_recent:
        return []

    latest_date = all_recent[0].date
    return [r for r in all_recent if r.date == latest_date]


async def load_molding_and_post_inventory_pools(
    db: AsyncSession,
    canonical: str,
    anchor: date,
    post_keys: list[str],
) -> dict[str, int]:
    """基準日時点：成型 + 成型後工程在庫（production_summarys、等価グループ合算）。"""
    ps_rows = await _load_production_summary_rows_at_anchor(db, canonical, anchor)
    if not ps_rows:
        return {}

    pools: dict[str, int] = defaultdict(int)
    molding_cfg = _get_process_config_by_key("molding")
    molding_inv_f = molding_cfg.get("fields", {}).get("inventory") if molding_cfg else None

    post_inv_fields: list[tuple[str, str]] = []
    for pk in post_keys:
        cfg = _get_process_config_by_key(pk)
        if not cfg:
            continue
        inv_f = cfg.get("fields", {}).get("inventory")
        if inv_f:
            post_inv_fields.append((pk, inv_f))

    for ps_row in ps_rows:
        row_dict = {c.name: getattr(ps_row, c.name) for c in ps_row.__table__.columns}
        if molding_inv_f:
            pools["molding"] += max(_num(row_dict, molding_inv_f), 0)
        for pk, inv_f in post_inv_fields:
            pools[pk] += max(_num(row_dict, inv_f), 0)

    return dict(pools)


def _pipeline_inventory_process_order(post_keys: list[str], pools: dict[str, int]) -> list[str]:
    """下流→上流の順（倉庫側を先に消化、成型を最後）。"""
    ordered = [pk for pk in post_keys if pk in pools]
    if "molding" in pools:
        ordered.append("molding")
    return ordered


def peg_pipeline_inventory_to_buckets(
    buckets: dict[tuple[str, str, str], int],
    forecast_map: dict[tuple[str, str, str], int],
    pools: dict[str, int],
    post_keys: list[str],
    anchor_date: date,
    lt_by_process: dict[str, int],
    canonical: str,
    mode: str,
) -> tuple[list[AttributionRow], dict[tuple[str, str, str], int]]:
    """
    成型＋成型後在庫を需要桶へ先に FIFO 充当（管理コードなし・INVENTORY_PEG）。

    基準日時点の在庫は内示帰属日 >= 基準日 の需要を日付順 FIFO で消化する。
    （LT 制約はロット側 Layer2 の source_date 反算のみ。在庫充当では適用しない）
    """
    remaining = dict(buckets)
    rows: list[AttributionRow] = []
    if not pools:
        return rows, remaining

    inventory_order = _pipeline_inventory_process_order(post_keys, pools)
    for pk in reversed(inventory_order):
        qty_left = max(int(pools.get(pk, 0)), 0)
        if qty_left <= 0:
            continue

        dates_sorted = sorted({k[2] for k in remaining if remaining.get(k, 0) > 0})
        for ds in dates_sorted:
            if qty_left <= 0:
                break
            try:
                demand_d = parse_iso_date(ds)
            except (ValueError, IndexError):
                continue
            if demand_d < anchor_date:
                continue

            buckets_today = [k for k in remaining if k[2] == ds and remaining[k] > 0]
            if not buckets_today:
                continue
            weights = [remaining[k] for k in buckets_today]
            total_today = sum(weights)
            alloc_today = min(qty_left, total_today)
            shares = largest_remainder_split(alloc_today, weights)

            for k, alloc in zip(buckets_today, shares):
                if alloc <= 0:
                    continue
                dest, demand_cd, _ = k
                rows.append(
                    AttributionRow(
                        management_code=None,
                        aps_batch_plan_id=None,
                        instruction_plan_id=None,
                        product_cd=canonical,
                        canonical_product_cd=canonical,
                        demand_product_cd=demand_cd,
                        destination_cd=dest or None,
                        process_key="molding",
                        source_date=anchor_date,
                        forecast_attribution_date=parse_iso_date(ds),
                        attributed_qty=_forecast_units_for_bucket(forecast_map, k),
                        method="INVENTORY_PEG",
                        allocation_rule=_stock_allocation_rule(pk),
                        attribution_mode=mode,
                        confidence="HIGH",
                        source_entity=SOURCE_ENTITY_PRODUCTION_SUMMARY,
                        source_entity_id=None,
                    )
                )
                remaining[k] -= alloc
            qty_left -= alloc_today

    return rows, remaining


# 後方互換エイリアス
load_post_molding_inventory_pools = load_molding_and_post_inventory_pools
peg_post_molding_inventory_to_buckets = peg_pipeline_inventory_to_buckets


async def load_molding_plan_supplement_lots(
    db: AsyncSession,
    canonical: str,
    ps: date,
    pe: date | None,
    existing_lots: list[LotRecord],
    mode: str,
) -> list[LotRecord]:
    """
    PLAN 時：production_summarys.molding_plan から日別成型計画を補完。
    同日の管理コードロット合計を差し引き、残りを仮想ロットとして追加。
    """
    if mode != "PLAN":
        return existing_lots

    by_date: dict[date, int] = defaultdict(int)
    for lot in existing_lots:
        if lot.start_date:
            by_date[lot.start_date] += _lot_planned_qty(lot, mode)

    ps_filters = [
        ProductionSummary.product_cd == canonical,
        ProductionSummary.date >= ps,
    ]
    if pe is not None:
        ps_filters.append(ProductionSummary.date <= pe)
    q = select(ProductionSummary.date, ProductionSummary.molding_plan).where(and_(*ps_filters))
    res = await db.execute(q)
    out = list(existing_lots)
    synth_id = -1
    for row in res.all():
        d = _to_date(row.date)
        mp = int(row.molding_plan or 0)
        if not d or mp <= 0:
            continue
        remainder = mp - by_date.get(d, 0)
        if remainder <= 0:
            continue
        out.append(
            LotRecord(
                aps_batch_plan_id=None,
                management_code=None,
                instruction_plan_id=None,
                product_cd=canonical,
                canonical_product_cd=canonical,
                planned_quantity=remainder,
                actual_quantity=0,
                start_date=d,
                priority_order=0,
                source_entity=SOURCE_ENTITY_PS_MOLDING_PLAN,
                source_entity_id=synth_id,
            )
        )
        synth_id -= 1
        by_date[d] += remainder
    return out


async def _load_product_lt_map(db: AsyncSession, canonical: str) -> dict[str, int]:
    lt: dict[str, int] = {}
    res = await db.execute(
        text(
            "SELECT cuting_process_lt, chamfering_process_lt, forming_process_lt, "
            "plating_process_lt, welding_process_lt, inspection_process_lt "
            "FROM product_process_bom WHERE product_cd = :cd LIMIT 1"
        ),
        {"cd": canonical},
    )
    row = res.mappings().first()
    if not row:
        return lt
    for pk, col in PROCESS_LT_MAP.items():
        v = row.get(col)
        if v is not None:
            try:
                lt[pk] = int(v)
            except (TypeError, ValueError):
                pass
    return lt


def canonical_product_cd(product_cd: str) -> str:
    s = (product_cd or "").strip()
    if len(s) >= 2:
        return s[:-1] + "1"
    return s


def product_cd_prefix(product_cd: str) -> str:
    s = (product_cd or "").strip()
    return s[:-1] if len(s) >= 2 else s


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()[:10]
    if len(s) == 10:
        try:
            return date.fromisoformat(s)
        except ValueError:
            return None
    return None


def _to_date_str(value: Any) -> str | None:
    d = _to_date(value)
    return d.isoformat() if d else None


def largest_remainder_split(total: int, weights: list[int]) -> list[int]:
    """最大余数法：按 weights 比例分配整数 total。"""
    if total <= 0 or not weights:
        return [0] * len(weights)
    wsum = sum(weights)
    if wsum <= 0:
        base, rem = divmod(total, len(weights))
        out = [base] * len(weights)
        for i in range(rem):
            out[i] += 1
        return out
    raw = [total * w / wsum for w in weights]
    floors = [int(x) for x in raw]
    remainder = total - sum(floors)
    fracs = sorted(
        [(raw[i] - floors[i], i) for i in range(len(weights))],
        reverse=True,
    )
    for k in range(remainder):
        floors[fracs[k % len(fracs)][1]] += 1
    return floors


@dataclass
class ProductVariant:
    product_cd: str
    destination_cd: str
    product_name: str = ""
    product_alias: str = ""


@dataclass
class DemandBucketKey:
    destination_cd: str
    demand_product_cd: str
    forecast_date: str

    def as_tuple(self) -> tuple[str, str, str]:
        return (self.destination_cd, self.demand_product_cd, self.forecast_date)


@dataclass(frozen=True)
class DemandBucketContext:
    """FIFO 消化用需要桶 + order_daily.forecast_units（帰属数表示用）。"""

    buckets: dict[tuple[str, str, str], int]
    forecast_units: dict[tuple[str, str, str], int]


def _forecast_units_for_bucket(
    forecast_map: dict[tuple[str, str, str], int],
    bucket_key: tuple[str, str, str],
) -> int:
    return max(int(forecast_map.get(bucket_key, 0)), 0)


@dataclass
class LotRecord:
    aps_batch_plan_id: int | None
    management_code: str | None
    instruction_plan_id: int | None
    product_cd: str
    canonical_product_cd: str
    planned_quantity: int
    actual_quantity: int
    start_date: date | None
    priority_order: int
    source_entity: str
    source_entity_id: int
    molding_order: int | None = None
    lot_key: str = field(default="")

    def __post_init__(self) -> None:
        if not self.lot_key:
            if self.aps_batch_plan_id is not None:
                self.lot_key = f"aps:{self.aps_batch_plan_id}"
            elif self.management_code:
                self.lot_key = f"mc:{self.management_code}"
            else:
                self.lot_key = f"{self.source_entity}:{self.source_entity_id}"


@dataclass
class AttributionRow:
    management_code: str | None
    aps_batch_plan_id: int | None
    instruction_plan_id: int | None
    product_cd: str
    canonical_product_cd: str
    demand_product_cd: str | None
    destination_cd: str | None
    process_key: str
    source_date: date | None
    forecast_attribution_date: date | None
    attributed_qty: int
    method: str
    allocation_rule: str | None
    attribution_mode: str
    confidence: str
    source_entity: str | None
    source_entity_id: int | None


async def load_product_variants(
    db: AsyncSession,
    canonical: str,
) -> list[ProductVariant]:
    prefix = product_cd_prefix(canonical)
    if not prefix:
        return [ProductVariant(product_cd=canonical, destination_cd="")]

    q = (
        select(
            Product.product_cd,
            Product.destination_cd,
            Product.product_name,
            Product.product_alias,
        )
        .where(Product.product_cd.like(f"{prefix}%"))
        .where(or_(Product.status.is_(None), Product.status != "inactive"))
    )
    res = await db.execute(q)
    variants: list[ProductVariant] = []
    seen: set[str] = set()
    for row in res.all():
        cd = str(row.product_cd or "").strip()
        if not cd or cd in seen:
            continue
        seen.add(cd)
        variants.append(
            ProductVariant(
                product_cd=cd,
                destination_cd=str(row.destination_cd or "").strip(),
                product_name=str(row.product_name or ""),
                product_alias=str(row.product_alias or ""),
            )
        )

    if canonical not in seen:
        pq = select(Product).where(Product.product_cd == canonical)
        pr = await db.execute(pq)
        p = pr.scalar_one_or_none()
        if p:
            variants.insert(
                0,
                ProductVariant(
                    product_cd=canonical,
                    destination_cd=str(p.destination_cd or "").strip(),
                    product_name=str(p.product_name or ""),
                    product_alias=str(p.product_alias or ""),
                ),
            )
        else:
            variants.insert(0, ProductVariant(product_cd=canonical, destination_cd=""))

    # order_daily 中出现但マスタ缺失的 variant
    od = OrderDaily
    norm = func.concat(func.substr(od.product_cd, 1, func.length(od.product_cd) - 1), "1")
    oq = (
        select(od.product_cd, od.destination_cd, od.product_name, od.product_alias)
        .where(norm == canonical)
        .distinct()
    )
    ores = await db.execute(oq)
    for row in ores.all():
        cd = str(row.product_cd or "").strip()
        if not cd or cd in seen:
            continue
        seen.add(cd)
        variants.append(
            ProductVariant(
                product_cd=cd,
                destination_cd=str(row.destination_cd or "").strip(),
                product_name=str(row.product_name or ""),
                product_alias=str(row.product_alias or ""),
            )
        )
    return variants


async def build_demand_buckets(
    db: AsyncSession,
    canonical: str,
    ps: date,
    pe: date | None = None,
) -> DemandBucketContext:
    """
    variant 粒度需求桶，扣除口径与 update-trend 一致（lastOrderQuantityDate）。
    键: (destination_cd, demand_product_cd, date_iso)

    buckets: FIFO 消化用（確定日以前は confirmed_units、以降は forecast_units）
    forecast_units: order_daily.forecast_units 合計（帰属数 attributed_qty の表示値）
    """
    variants = await load_product_variants(db, canonical)
    if not variants:
        return DemandBucketContext(buckets={}, forecast_units={})

    od = OrderDaily
    variant_cds = [v.product_cd for v in variants]
    q = (
        select(
            od.destination_cd,
            od.product_cd,
            od.date,
            func.sum(func.coalesce(od.confirmed_units, 0)).label("confirmed"),
            func.sum(func.coalesce(od.forecast_units, 0)).label("forecast"),
        )
        .where(od.date >= ps)
        .where(od.product_cd.in_(variant_cds))
    )
    if pe is not None:
        q = q.where(od.date <= pe)
    q = q.group_by(od.destination_cd, od.product_cd, od.date)
    res = await db.execute(q)
    raw: dict[tuple[str, str, str], tuple[int, int]] = {}
    for row in res.all():
        dest = str(row.destination_cd or "").strip()
        cd = str(row.product_cd or "").strip()
        ds = _to_date_str(row.date)
        if not cd or not ds:
            continue
        raw[(dest, cd, ds)] = (int(row.confirmed or 0), int(row.forecast or 0))

    # lastOrderQuantityDate at canonical level
    last_order_date: str | None = None
    for (_, _, ds), (confirmed, _) in raw.items():
        if confirmed > 0 and (last_order_date is None or ds > last_order_date):
            last_order_date = ds

    buckets: dict[tuple[str, str, str], int] = {}
    forecast_units: dict[tuple[str, str, str], int] = {}
    for key, (confirmed, forecast) in raw.items():
        forecast_units[key] = max(int(forecast), 0)
        dest, cd, ds = key
        if last_order_date is not None and ds <= last_order_date and confirmed > 0:
            qty = confirmed
        else:
            qty = forecast
        if qty > 0:
            buckets[key] = qty
    return DemandBucketContext(buckets=buckets, forecast_units=forecast_units)


def _lot_planned_qty(lot: LotRecord, mode: str) -> int:
    if mode == "ACTUAL":
        return max(int(lot.actual_quantity or 0), 0)
    pq = int(lot.planned_quantity or 0)
    if pq > 0:
        return pq
    return max(int(lot.actual_quantity or 0), 0)


async def load_lots(
    db: AsyncSession,
    ps: date,
    pe: date | None,
    product_cds: list[str] | None,
    mode: str,
) -> list[LotRecord]:
    """instruction_plans + cutting_management（aps_batch_plan_id 去重，cutting 优先）。"""
    params: dict[str, Any] = {"ps": ps}
    if pe is not None:
        params["pe"] = pe
    ip_end = _sql_date_lte("DATE(start_date)", pe)
    cm_start_end = _sql_date_lte("DATE(start_date)", pe)
    cm_prod_end = _sql_date_lte("production_day", pe)
    product_filter = ""
    if product_cds:
        placeholders = ", ".join(f":pc{i}" for i in range(len(product_cds)))
        product_filter = f" AND product_cd IN ({placeholders})"
        for i, cd in enumerate(product_cds):
            params[f"pc{i}"] = cd

    ip_sql = f"""
        SELECT id, aps_batch_plan_id, management_code, product_cd,
               planned_quantity, production_lot_size, start_date, priority_order,
               actual_production_quantity
        FROM instruction_plans
        WHERE start_date IS NOT NULL
          AND DATE(start_date) >= :ps{ip_end}
          {product_filter}
    """
    cm_sql = f"""
        SELECT id, aps_batch_plan_id, management_code, product_cd,
               planned_quantity, production_lot_size, start_date, production_day,
               priority_order, actual_production_quantity
        FROM cutting_management
        WHERE (
            (start_date IS NOT NULL AND DATE(start_date) >= :ps{cm_start_end})
            OR (production_day >= :ps{cm_prod_end})
        )
        {product_filter}
    """
    ip_res = await db.execute(text(ip_sql), params)
    cm_res = await db.execute(text(cm_sql), params)

    by_key: dict[str, LotRecord] = {}

    def _upsert(row: dict, entity: str) -> None:
        aps_id = row.get("aps_batch_plan_id")
        mc = (row.get("management_code") or "").strip() or None
        if aps_id is not None:
            key = f"aps:{aps_id}"
        elif mc:
            key = f"mc:{mc}"
        else:
            key = f"{entity}:{row['id']}"

        pq = int(row.get("planned_quantity") or 0)
        if pq <= 0:
            pq = int(row.get("production_lot_size") or 0)
        start = _to_date(row.get("start_date")) or _to_date(row.get("production_day"))
        lot = LotRecord(
            aps_batch_plan_id=int(aps_id) if aps_id is not None else None,
            management_code=mc,
            instruction_plan_id=int(row["id"]) if entity == "instruction_plans" else None,
            product_cd=str(row.get("product_cd") or "").strip(),
            canonical_product_cd=canonical_product_cd(str(row.get("product_cd") or "")),
            planned_quantity=pq,
            actual_quantity=int(row.get("actual_production_quantity") or 0),
            start_date=start,
            priority_order=int(row.get("priority_order") or 0),
            source_entity=entity,
            source_entity_id=int(row["id"]),
        )
        # cutting 覆盖 instruction_plans
        if entity == "cutting_management" or key not in by_key:
            by_key[key] = lot

    for row in ip_res.mappings().all():
        _upsert(dict(row), "instruction_plans")
    for row in cm_res.mappings().all():
        _upsert(dict(row), "cutting_management")

    lots = list(by_key.values())
    if not lots:
        return lots

    molding_orders = await _load_molding_production_orders(
        db, ps, pe, list({l.product_cd for l in lots})
    )
    for lot in lots:
        per = molding_orders.get(lot.product_cd) or {}
        if per:
            lot.molding_order = min(per.values())

    def sort_key(l: LotRecord) -> tuple:
        sd = l.start_date or date.min
        mo = l.molding_order if l.molding_order is not None else 999999
        return (mo, sd, l.priority_order, l.source_entity_id)

    lots.sort(key=sort_key)
    return lots


def run_layer1_fifo(
    lots: list[LotRecord],
    buckets: dict[tuple[str, str, str], int],
    forecast_map: dict[tuple[str, str, str], int],
    mode: str,
) -> list[AttributionRow]:
    """组内多桶 FIFO + 同日纳入先占比分摊。"""
    remaining = dict(buckets)
    dates_sorted = sorted({k[2] for k in remaining})
    rows: list[AttributionRow] = []

    for lot in lots:
        qty_left = _lot_planned_qty(lot, mode)
        if qty_left <= 0:
            continue

        for ds in dates_sorted:
            if qty_left <= 0:
                break
            buckets_today = [k for k in remaining if k[2] == ds and remaining[k] > 0]
            if not buckets_today:
                continue
            weights = [remaining[k] for k in buckets_today]
            total_today = sum(weights)
            alloc_today = min(qty_left, total_today)
            shares = largest_remainder_split(alloc_today, weights)

            for k, alloc in zip(buckets_today, shares):
                if alloc <= 0:
                    continue
                dest, demand_cd, _ = k
                rows.append(
                    AttributionRow(
                        management_code=lot.management_code,
                        aps_batch_plan_id=lot.aps_batch_plan_id,
                        instruction_plan_id=lot.instruction_plan_id,
                        product_cd=lot.product_cd,
                        canonical_product_cd=lot.canonical_product_cd,
                        demand_product_cd=demand_cd,
                        destination_cd=dest or None,
                        process_key="molding",
                        source_date=lot.start_date,
                        forecast_attribution_date=parse_iso_date(ds),
                        attributed_qty=_forecast_units_for_bucket(forecast_map, k),
                        method="FIFO_DEMAND",
                        allocation_rule="SAME_DAY_PROPORTIONAL",
                        attribution_mode=mode,
                        confidence="HIGH",
                        source_entity=lot.source_entity,
                        source_entity_id=lot.source_entity_id,
                    )
                )
                remaining[k] -= alloc
            qty_left -= alloc_today

        if qty_left > 0:
            rows.append(
                AttributionRow(
                    management_code=lot.management_code,
                    aps_batch_plan_id=lot.aps_batch_plan_id,
                    instruction_plan_id=lot.instruction_plan_id,
                    product_cd=lot.product_cd,
                    canonical_product_cd=lot.canonical_product_cd,
                    demand_product_cd=None,
                    destination_cd=None,
                    process_key="molding",
                    source_date=lot.start_date,
                    forecast_attribution_date=None,
                    attributed_qty=qty_left,
                    method="FIFO_OVERFLOW",
                    allocation_rule="CROSS_DAY_FIFO",
                    attribution_mode=mode,
                    confidence="OVERFLOW",
                    source_entity=lot.source_entity,
                    source_entity_id=lot.source_entity_id,
                )
            )
    return rows


def _lot_match_params(aps_ids: list[int], mcs: list[str]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for i, aid in enumerate(aps_ids):
        params[f"aid{i}"] = aid
    for i, mc in enumerate(mcs):
        params[f"mc{i}"] = mc
    return params


def _lot_match_where(aps_ids: list[int], mcs: list[str], *, col_prefix: str = "") -> str:
    filters: list[str] = []
    if aps_ids:
        aps_ph = ", ".join(f":aid{i}" for i in range(len(aps_ids)))
        filters.append(f"{col_prefix}aps_batch_plan_id IN ({aps_ph})")
    if mcs:
        mc_ph = ", ".join(f":mc{i}" for i in range(len(mcs)))
        filters.append(f"{col_prefix}management_code IN ({mc_ph})")
    return " OR ".join(filters) if filters else "1=0"


async def run_layer3_chain(
    db: AsyncSession,
    molding_rows: list[AttributionRow],
    mode: str,
) -> list[AttributionRow]:
    """切断/面取链式继承 molding 归属。"""
    by_lot: dict[str, list[AttributionRow]] = defaultdict(list)
    aps_ids: list[int] = []
    mcs: list[str] = []
    seen_aps: set[int] = set()
    seen_mc: set[str] = set()
    for r in molding_rows:
        if r.process_key != "molding" or r.method not in ("FIFO_DEMAND", "CHAIN_INHERIT"):
            continue
        key = f"aps:{r.aps_batch_plan_id}" if r.aps_batch_plan_id else f"mc:{r.management_code}"
        by_lot[key].append(r)
        if r.aps_batch_plan_id is not None and r.aps_batch_plan_id not in seen_aps:
            seen_aps.add(r.aps_batch_plan_id)
            aps_ids.append(r.aps_batch_plan_id)
        elif r.management_code and r.management_code not in seen_mc:
            seen_mc.add(r.management_code)
            mcs.append(r.management_code)

    if not by_lot:
        return []

    params = _lot_match_params(aps_ids, mcs)
    where_clause = _lot_match_where(aps_ids, mcs)

    out: list[AttributionRow] = []

    cm_sql = f"""
        SELECT id, aps_batch_plan_id, management_code, product_cd,
               planned_quantity, production_lot_size, start_date, production_day,
               actual_production_quantity, priority_order
        FROM cutting_management
        WHERE {where_clause}
    """
    cm_res = await db.execute(text(cm_sql), params)
    for row in cm_res.mappings().all():
        r = dict(row)
        aps_id = r.get("aps_batch_plan_id")
        mc = (r.get("management_code") or "").strip()
        key = f"aps:{aps_id}" if aps_id is not None else f"mc:{mc}"
        refs = by_lot.get(key)
        if not refs:
            continue

        qty = int(r.get("actual_production_quantity") or 0) if mode == "ACTUAL" else int(
            r.get("planned_quantity") or r.get("production_lot_size") or 0
        )
        if qty <= 0 and mode == "ACTUAL":
            continue

        for ref in refs:
            if ref.attributed_qty <= 0 or not ref.forecast_attribution_date:
                continue
            out.append(
                AttributionRow(
                    management_code=mc or ref.management_code,
                    aps_batch_plan_id=int(aps_id) if aps_id is not None else ref.aps_batch_plan_id,
                    instruction_plan_id=ref.instruction_plan_id,
                    product_cd=str(r.get("product_cd") or ref.product_cd),
                    canonical_product_cd=ref.canonical_product_cd,
                    demand_product_cd=ref.demand_product_cd,
                    destination_cd=ref.destination_cd,
                    process_key="cutting",
                    source_date=_to_date(r.get("production_day")) or _to_date(r.get("start_date")),
                    forecast_attribution_date=ref.forecast_attribution_date,
                    attributed_qty=ref.attributed_qty,
                    method="CHAIN_INHERIT",
                    allocation_rule=ref.allocation_rule,
                    attribution_mode=mode,
                    confidence=ref.confidence,
                    source_entity="cutting_management",
                    source_entity_id=int(r["id"]),
                )
            )

    ch_where = _lot_match_where(aps_ids, mcs, col_prefix="cm.")
    ch_sql = f"""
        SELECT cm.id, cm.aps_batch_plan_id, cm.management_code, cm.product_cd,
               cm.production_day, cm.start_date, cm.actual_production_quantity,
               cm.planned_quantity, cm.production_lot_size,
               chm.id AS chamfer_id, chm.production_day AS chm_production_day
        FROM chamfering_management chm
        INNER JOIN cutting_management cm ON cm.id = chm.cutting_management_id
        WHERE {ch_where}
    """
    try:
        ch_res = await db.execute(text(ch_sql), params)
    except Exception:
        return out

    for row in ch_res.mappings().all():
        r = dict(row)
        aps_id = r.get("aps_batch_plan_id")
        mc = (r.get("management_code") or "").strip()
        key = f"aps:{aps_id}" if aps_id is not None else f"mc:{mc}"
        refs = by_lot.get(key)
        if not refs:
            continue
        qty = int(r.get("actual_production_quantity") or 0) if mode == "ACTUAL" else int(
            r.get("planned_quantity") or r.get("production_lot_size") or 0
        )
        if qty <= 0 and mode == "ACTUAL":
            continue
        for ref in refs:
            if ref.attributed_qty <= 0 or not ref.forecast_attribution_date:
                continue
            out.append(
                AttributionRow(
                    management_code=mc or ref.management_code,
                    aps_batch_plan_id=int(aps_id) if aps_id is not None else ref.aps_batch_plan_id,
                    instruction_plan_id=ref.instruction_plan_id,
                    product_cd=str(r.get("product_cd") or ref.product_cd),
                    canonical_product_cd=ref.canonical_product_cd,
                    demand_product_cd=ref.demand_product_cd,
                    destination_cd=ref.destination_cd,
                    process_key="chamfering",
                    source_date=_to_date(r.get("chm_production_day"))
                    or _to_date(r.get("production_day"))
                    or _to_date(r.get("start_date")),
                    forecast_attribution_date=ref.forecast_attribution_date,
                    attributed_qty=ref.attributed_qty,
                    method="CHAIN_INHERIT",
                    allocation_rule=ref.allocation_rule,
                    attribution_mode=mode,
                    confidence=ref.confidence,
                    source_entity="chamfering_management",
                    source_entity_id=int(r["chamfer_id"]),
                )
            )
    return out


async def run_layer2_inventory(
    db: AsyncSession,
    molding_rows: list[AttributionRow],
    ps: date,
    pe: date | None,
    mode: str,
) -> list[AttributionRow]:
    """成型后工程：LT 反算 source_date，继承 forecast_attribution_date。"""
    out: list[AttributionRow] = []
    by_canonical: dict[str, list[AttributionRow]] = defaultdict(list)
    for r in molding_rows:
        if r.process_key == "molding" and r.forecast_attribution_date:
            by_canonical[r.canonical_product_cd].append(r)

    lt_cache: dict[str, dict[str, int]] = {}
    route_cache: dict[str, list[str]] = {}

    bom_lt_res = await db.execute(
        text(
            "SELECT product_cd, cuting_process_lt, chamfering_process_lt, forming_process_lt, "
            "plating_process_lt, welding_process_lt, inspection_process_lt FROM product_process_bom"
        )
    )
    for brow in bom_lt_res.mappings().all():
        cd = str(brow.get("product_cd") or "").strip()
        if not cd:
            continue
        lt_cache[cd] = {}
        for pk, col in PROCESS_LT_MAP.items():
            v = brow.get(col)
            if v is not None:
                try:
                    lt_cache[cd][pk] = int(v)
                except (TypeError, ValueError):
                    pass

    for canonical, refs in by_canonical.items():
        pq = select(Product.route_cd, Product.product_cd).where(Product.product_cd == canonical)
        pres = await db.execute(pq)
        prow = pres.first()
        if not prow:
            continue
        route_cd = str(prow.route_cd or "").strip()
        if route_cd not in route_cache:
            route_cache[route_cd] = await _get_route_sequence(db, route_cd)
        sequence = route_cache[route_cd]
        if "molding" not in sequence:
            continue
        mold_idx = sequence.index("molding")
        post_keys = [k for k in sequence[mold_idx + 1 :] if k in POST_MOLDING_PROCESS_KEYS]

        wh_negative: set[str] = set()
        wh_filters = [
            ProductionSummary.product_cd == canonical,
            ProductionSummary.date >= ps,
            ProductionSummary.warehouse_inventory < 0,
        ]
        if pe is not None:
            wh_filters.append(ProductionSummary.date <= pe)
        nq = select(ProductionSummary.date).where(and_(*wh_filters))
        nr = await db.execute(nq)
        for (d,) in nr.all():
            ds = _to_date_str(d)
            if ds:
                wh_negative.add(ds)

        for ref in refs:
            if ref.attributed_qty <= 0 or not ref.forecast_attribution_date:
                continue
            f_str = ref.forecast_attribution_date.isoformat()
            conf = "LOW" if f_str in wh_negative else ref.confidence
            cum_lt = 0
            for pk in reversed(post_keys):
                cum_lt += lt_cache.get(canonical, {}).get(pk, 0)
                src_str = _subtract_business_days(f_str, cum_lt)
                src_d = parse_iso_date(src_str) if src_str else ref.forecast_attribution_date
                out.append(
                    AttributionRow(
                        management_code=ref.management_code,
                        aps_batch_plan_id=ref.aps_batch_plan_id,
                        instruction_plan_id=ref.instruction_plan_id,
                        product_cd=ref.product_cd,
                        canonical_product_cd=ref.canonical_product_cd,
                        demand_product_cd=ref.demand_product_cd,
                        destination_cd=ref.destination_cd,
                        process_key=pk,
                        source_date=src_d,
                        forecast_attribution_date=ref.forecast_attribution_date,
                        attributed_qty=ref.attributed_qty,
                        method="INVENTORY_PEG",
                        allocation_rule=ref.allocation_rule,
                        attribution_mode=mode,
                        confidence=conf,
                        source_entity=ref.source_entity,
                        source_entity_id=ref.source_entity_id,
                    )
                )
    return out


async def _mark_stale(db: AsyncSession, canonical_cds: list[str], mode: str) -> None:
    if not canonical_cds:
        return
    chunk_size = 200
    for i in range(0, len(canonical_cds), chunk_size):
        chunk = canonical_cds[i : i + chunk_size]
        await db.execute(
            update(LotForecastAttribution)
            .where(
                LotForecastAttribution.canonical_product_cd.in_(chunk),
                LotForecastAttribution.attribution_mode == mode,
                LotForecastAttribution.is_current.is_(True),
            )
            .values(is_current=False)
        )


def _row_to_model(row: AttributionRow, run_id: str) -> LotForecastAttribution:
    return LotForecastAttribution(
        management_code=_clip_varchar(row.management_code, 100),
        aps_batch_plan_id=row.aps_batch_plan_id,
        instruction_plan_id=row.instruction_plan_id,
        product_cd=_clip_varchar(row.product_cd, 50) or "",
        canonical_product_cd=_clip_varchar(row.canonical_product_cd, 50) or "",
        demand_product_cd=_clip_varchar(row.demand_product_cd, 50),
        destination_cd=_clip_varchar(row.destination_cd, 50),
        process_key=_clip_varchar(row.process_key, 32) or "molding",
        source_date=row.source_date,
        forecast_attribution_date=row.forecast_attribution_date,
        attributed_qty=row.attributed_qty,
        method=_clip_varchar(row.method, 32) or "FIFO_DEMAND",
        allocation_rule=_clip_varchar(row.allocation_rule, 32),
        attribution_mode=_clip_varchar(row.attribution_mode, 16) or "PLAN",
        confidence=_clip_varchar(row.confidence, 16) or "HIGH",
        source_entity=_clip_varchar(row.source_entity, 32),
        source_entity_id=row.source_entity_id,
        run_id=run_id,
        is_current=True,
    )


async def recompute_attribution(
    db: AsyncSession,
    start_date: date,
    product_cds: list[str] | None = None,
    modes: list[str] | None = None,
) -> dict[str, Any]:
    """主入口：指定開始日から先を重算（終了日上限なし。FIFO ロジックは期間指定時と同一）。"""
    if modes is None:
        modes = ["PLAN", "ACTUAL"]
    effective_start = attribution_effective_start(start_date)
    run_id = uuid.uuid4().hex
    all_rows: list[LotForecastAttribution] = []
    canonicals_touched: set[str] = set()

    for mode in modes:
        lots = await load_lots(db, effective_start, None, product_cds, mode)

        by_canonical: dict[str, list[LotRecord]] = defaultdict(list)
        for lot in lots:
            if lot.start_date and lot.start_date < effective_start:
                continue
            by_canonical[lot.canonical_product_cd].append(lot)

        if mode == "PLAN":
            if product_cds:
                extra_canonicals = {canonical_product_cd(c) for c in product_cds}
            else:
                ps_res = await db.execute(
                    text(
                        "SELECT DISTINCT product_cd FROM production_summarys "
                        "WHERE date >= :ps AND molding_plan > 0"
                    ),
                    {"ps": effective_start},
                )
                extra_canonicals = {
                    canonical_product_cd(str(r[0])) for r in ps_res.all() if r[0]
                }
            for c in extra_canonicals:
                by_canonical.setdefault(c, [])

        if not by_canonical:
            continue

        mode_rows: list[AttributionRow] = []
        for canonical, group_lots in by_canonical.items():
            canonicals_touched.add(canonical)
            bucket_ctx = await build_demand_buckets(db, canonical, effective_start)
            remaining_buckets = dict(bucket_ctx.buckets)
            forecast_map = bucket_ctx.forecast_units

            route_ctx = await _load_canonical_route_context(db, canonical)
            post_keys: list[str] = []
            if route_ctx:
                _, post_keys = route_ctx
            lt_map = await _load_product_lt_map(db, canonical)
            inv_pools = await load_molding_and_post_inventory_pools(
                db, canonical, effective_start, post_keys
            )
            inv_rows, remaining_buckets = peg_pipeline_inventory_to_buckets(
                remaining_buckets,
                forecast_map,
                inv_pools,
                post_keys,
                effective_start,
                lt_map,
                canonical,
                mode,
            )
            mode_rows.extend(inv_rows)

            molding_lots = await load_molding_plan_supplement_lots(
                db, canonical, effective_start, None, group_lots, mode
            )
            molding_lots = [
                lot
                for lot in molding_lots
                if lot.start_date is None or lot.start_date >= effective_start
            ]

            if not remaining_buckets and molding_lots:
                for lot in molding_lots:
                    qty = _lot_planned_qty(lot, mode)
                    if qty <= 0:
                        continue
                    mode_rows.append(
                        AttributionRow(
                            management_code=lot.management_code,
                            aps_batch_plan_id=lot.aps_batch_plan_id,
                            instruction_plan_id=lot.instruction_plan_id,
                            product_cd=lot.product_cd,
                            canonical_product_cd=lot.canonical_product_cd,
                            demand_product_cd=None,
                            destination_cd=None,
                            process_key="molding",
                            source_date=lot.start_date,
                            forecast_attribution_date=None,
                            attributed_qty=qty,
                            method="NO_DEMAND",
                            allocation_rule=None,
                            attribution_mode=mode,
                            confidence="LOW",
                            source_entity=lot.source_entity,
                            source_entity_id=lot.source_entity_id,
                        )
                    )
                continue

            if molding_lots:
                mode_rows.extend(
                    run_layer1_fifo(molding_lots, remaining_buckets, forecast_map, mode)
                )

        layer3 = await run_layer3_chain(db, mode_rows, mode)
        layer2 = await run_layer2_inventory(db, mode_rows, effective_start, None, mode)
        combined = mode_rows + layer3 + layer2

        await _mark_stale(db, list(canonicals_touched), mode)
        for ar in combined:
            if ar.attributed_qty <= 0 and ar.method not in ("FIFO_OVERFLOW", "NO_DEMAND"):
                continue
            all_rows.append(_row_to_model(ar, run_id))

    if all_rows:
        db.add_all(all_rows)
    await db.flush()

    return {
        "run_id": run_id,
        "inserted": len(all_rows),
        "canonical_product_cds": sorted(canonicals_touched),
        "modes": modes,
        "anchor_date": effective_start.isoformat(),
    }


async def build_reconcile_report(
    db: AsyncSession,
    run_id: str | None,
    start_date: date,
    end_date: date,
    canonical_product_cd: str | None = None,
) -> dict[str, Any]:
    """对账报告。"""
    q = select(LotForecastAttribution).where(
        LotForecastAttribution.is_current.is_(True),
        LotForecastAttribution.process_key == "molding",
        LotForecastAttribution.method == "FIFO_DEMAND",
    )
    if run_id:
        q = q.where(LotForecastAttribution.run_id == run_id)
    if canonical_product_cd:
        q = q.where(LotForecastAttribution.canonical_product_cd == canonical_product_cd)

    res = await db.execute(q)
    attr_rows = res.scalars().all()

    demand_violations: list[dict] = []
    overflow_rows: list[dict] = []
    plan_gaps: list[dict] = []

    by_canonical: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    seen_bucket: set[tuple[str, str, str, str]] = set()
    for r in attr_rows:
        if not r.forecast_attribution_date or not r.demand_product_cd:
            continue
        ds = r.forecast_attribution_date.isoformat()
        bk = (
            r.canonical_product_cd,
            str(r.destination_cd or ""),
            str(r.demand_product_cd),
            ds,
        )
        if bk in seen_bucket:
            continue
        seen_bucket.add(bk)
        by_canonical[r.canonical_product_cd][ds] += int(r.attributed_qty or 0)

    canonicals = [canonical_product_cd] if canonical_product_cd else list(by_canonical.keys())
    for canonical in canonicals:
        bucket_ctx = await build_demand_buckets(db, canonical, start_date, end_date)
        demand_by_date: dict[str, int] = defaultdict(int)
        for (_, _, ds), qty in bucket_ctx.buckets.items():
            demand_by_date[ds] += qty

        for ds, attr_qty in by_canonical.get(canonical, {}).items():
            demand = demand_by_date.get(ds, 0)
            if attr_qty > demand:
                demand_violations.append(
                    {
                        "canonical_product_cd": canonical,
                        "date": ds,
                        "attributed": attr_qty,
                        "demand": demand,
                    }
                )

        ps_q = select(ProductionSummary.date, ProductionSummary.molding_plan).where(
            and_(
                ProductionSummary.product_cd == canonical,
                ProductionSummary.date >= start_date,
                ProductionSummary.date <= end_date,
            )
        )
        ps_res = await db.execute(ps_q)
        lot_by_start: dict[str, int] = defaultdict(int)
        for r in attr_rows:
            if r.canonical_product_cd == canonical and r.source_date:
                lot_by_start[r.source_date.isoformat()] += int(r.attributed_qty or 0)

        for prow in ps_res.all():
            ds = _to_date_str(prow.date)
            mp = int(prow.molding_plan or 0)
            lq = lot_by_start.get(ds or "", 0)
            if mp > 0 and abs(mp - lq) > mp * 0.1 + 10:
                plan_gaps.append(
                    {
                        "canonical_product_cd": canonical,
                        "date": ds,
                        "molding_plan": mp,
                        "lot_attributed_sum": lq,
                    }
                )

    oq = select(LotForecastAttribution).where(
        LotForecastAttribution.is_current.is_(True),
        LotForecastAttribution.method == "FIFO_OVERFLOW",
    )
    if run_id:
        oq = oq.where(LotForecastAttribution.run_id == run_id)
    ores = await db.execute(oq)
    for r in ores.scalars().all():
        overflow_rows.append(
            {
                "management_code": r.management_code,
                "aps_batch_plan_id": r.aps_batch_plan_id,
                "attributed_qty": r.attributed_qty,
            }
        )

    return {
        "demand_violations": demand_violations,
        "overflow_rows": overflow_rows,
        "plan_gaps": plan_gaps,
        "summary": {
            "demand_violation_count": len(demand_violations),
            "overflow_count": len(overflow_rows),
            "plan_gap_count": len(plan_gaps),
        },
    }


async def query_attributions(
    db: AsyncSession,
    management_code: str | None = None,
    aps_batch_plan_id: int | None = None,
    product_cd: str | None = None,
    destination_cd: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    process_key: str | None = None,
    attribution_mode: str | None = None,
    prefer_actual: bool = True,
    group_by: str = "destination",
    require_management_code: bool = False,
) -> list[dict[str, Any]]:
    """查询归属；prefer_actual 时 ACTUAL 优先于 PLAN。"""
    q = select(LotForecastAttribution).where(LotForecastAttribution.is_current.is_(True))
    if require_management_code:
        q = q.where(
            LotForecastAttribution.management_code.isnot(None),
            LotForecastAttribution.management_code != "",
        )
    if management_code:
        q = q.where(LotForecastAttribution.management_code == management_code)
    if aps_batch_plan_id is not None:
        q = q.where(LotForecastAttribution.aps_batch_plan_id == aps_batch_plan_id)
    if product_cd:
        q = q.where(
            (LotForecastAttribution.product_cd == product_cd)
            | (LotForecastAttribution.canonical_product_cd == canonical_product_cd(product_cd))
        )
    if destination_cd:
        q = q.where(LotForecastAttribution.destination_cd == destination_cd)
    if start_date:
        q = q.where(LotForecastAttribution.forecast_attribution_date >= start_date)
    if end_date:
        q = q.where(LotForecastAttribution.forecast_attribution_date <= end_date)
    if process_key:
        q = q.where(LotForecastAttribution.process_key == process_key)
    if attribution_mode:
        q = q.where(LotForecastAttribution.attribution_mode == attribution_mode)

    res = await db.execute(q.order_by(LotForecastAttribution.forecast_attribution_date))
    rows = res.scalars().all()

    if prefer_actual and not attribution_mode:
        by_key: dict[tuple, LotForecastAttribution] = {}
        for r in rows:
            k = (
                r.management_code,
                r.source_entity,
                r.source_entity_id,
                r.process_key,
                r.forecast_attribution_date,
                r.destination_cd,
                r.demand_product_cd,
            )
            existing = by_key.get(k)
            if existing is None or (
                r.attribution_mode == "ACTUAL" and existing.attribution_mode != "ACTUAL"
            ):
                by_key[k] = r
        rows = list(by_key.values())

    out: list[dict[str, Any]] = []
    for r in sorted(rows, key=lambda x: (x.forecast_attribution_date or date.min, x.id)):
        out.append(
            {
                "id": r.id,
                "management_code": r.management_code,
                "aps_batch_plan_id": r.aps_batch_plan_id,
                "product_cd": r.product_cd,
                "canonical_product_cd": r.canonical_product_cd,
                "demand_product_cd": r.demand_product_cd,
                "destination_cd": r.destination_cd,
                "process_key": r.process_key,
                "source_date": _to_date_str(r.source_date),
                "forecast_attribution_date": _to_date_str(r.forecast_attribution_date),
                "attributed_qty": r.attributed_qty,
                "method": r.method,
                "allocation_rule": r.allocation_rule,
                "attribution_mode": r.attribution_mode,
                "confidence": r.confidence,
                "source_entity": r.source_entity,
                "source_entity_id": r.source_entity_id,
                "run_id": r.run_id,
            }
        )
    return out


async def enrich_attribution_display_names(
    db: AsyncSession,
    rows: list[dict[str, Any]],
) -> None:
    """製品名・納入先名をマスタ／受注から付与。"""
    if not rows:
        return

    product_cds: set[str] = set()
    dest_cds: set[str] = set()
    for r in rows:
        for key in ("product_cd", "demand_product_cd"):
            cd = str(r.get(key) or "").strip()
            if cd:
                product_cds.add(cd)
        dc = str(r.get("destination_cd") or "").strip()
        if dc:
            dest_cds.add(dc)

    product_name_by_cd: dict[str, str] = {}
    if product_cds:
        pres = await db.execute(
            select(Product.product_cd, Product.product_name).where(
                Product.product_cd.in_(list(product_cds))
            )
        )
        for cd, name in pres.all():
            product_name_by_cd[str(cd)] = str(name or "").strip()

        missing_p = product_cds - set(product_name_by_cd.keys())
        if missing_p:
            od = OrderDaily
            ores = await db.execute(
                select(od.product_cd, od.product_name)
                .where(od.product_cd.in_(list(missing_p)))
                .distinct()
            )
            for cd, name in ores.all():
                s = str(cd or "").strip()
                if s and s not in product_name_by_cd:
                    product_name_by_cd[s] = str(name or "").strip()

    dest_name_by_cd: dict[str, str] = {}
    if dest_cds:
        dres = await db.execute(
            select(Destination.destination_cd, Destination.destination_name).where(
                Destination.destination_cd.in_(list(dest_cds))
            )
        )
        for cd, name in dres.all():
            dest_name_by_cd[str(cd)] = str(name or "").strip()

        missing_d = dest_cds - set(dest_name_by_cd.keys())
        if missing_d:
            od = OrderDaily
            ores = await db.execute(
                select(od.destination_cd, od.destination_name)
                .where(od.destination_cd.in_(list(missing_d)))
                .distinct()
            )
            for cd, name in ores.all():
                s = str(cd or "").strip()
                if s and s not in dest_name_by_cd:
                    dest_name_by_cd[s] = str(name or "").strip()

    for r in rows:
        pcd = str(r.get("product_cd") or "").strip()
        dpcd = str(r.get("demand_product_cd") or "").strip()
        r["product_name"] = product_name_by_cd.get(pcd) or product_name_by_cd.get(dpcd) or None
        dest = str(r.get("destination_cd") or "").strip()
        r["destination_name"] = dest_name_by_cd.get(dest) or None


def _resolve_management_code_process_status(
    management_code: str,
    cm: dict[str, Any] | None,
    ip: dict[str, Any] | None,
    ch_rows: list[dict[str, Any]],
    today: date,
) -> dict[str, Any]:
    """管理コードの成型完了と現工程を判定（切断→面取→成型の順）。"""
    if cm:
        cutting_done = int(cm.get("production_completed_check") or 0) == 1
        if not cutting_done:
            return {
                "molding_completed": False,
                "current_process_key": "cutting",
                "current_process_label": "切断",
            }

        has_ch = int(cm.get("has_chamfering_process") or 0) == 1
        if has_ch:
            cm_id = cm.get("id")
            related = [
                c
                for c in ch_rows
                if c.get("cutting_management_id") == cm_id
                or str(c.get("management_code") or "").strip() == management_code
            ]
            if not related:
                return {
                    "molding_completed": False,
                    "current_process_key": "chamfering_pending",
                    "current_process_label": "面取待ち",
                }
            if any(int(c.get("production_completed_check") or 0) != 1 for c in related):
                return {
                    "molding_completed": False,
                    "current_process_key": "chamfering",
                    "current_process_label": "面取",
                }

        end_d = _to_date(cm.get("end_date"))
        start_d = _to_date(cm.get("start_date"))
        if end_d is not None and end_d <= today:
            return {
                "molding_completed": True,
                "current_process_key": "molding_completed",
                "current_process_label": "成型完了",
            }
        if start_d is not None:
            return {
                "molding_completed": False,
                "current_process_key": "molding",
                "current_process_label": "成型",
            }
        return {
            "molding_completed": False,
            "current_process_key": "molding_pending",
            "current_process_label": "成型待ち",
        }

    if ip:
        return {
            "molding_completed": False,
            "current_process_key": "batch",
            "current_process_label": "生産ロット",
        }

    return {
        "molding_completed": False,
        "current_process_key": "unknown",
        "current_process_label": "不明",
    }


async def batch_resolve_management_code_process_status(
    db: AsyncSession,
    management_codes: list[str],
) -> dict[str, dict[str, Any]]:
    """管理コード一括：成型完了フラグと現工程。"""
    codes = list(dict.fromkeys((c or "").strip() for c in management_codes if (c or "").strip()))
    if not codes:
        return {}

    ph = ", ".join(f":mc{i}" for i in range(len(codes)))
    params = {f"mc{i}": c for i, c in enumerate(codes)}
    today = date.today()

    cm_res = await db.execute(
        text(
            f"""
            SELECT id, management_code, production_completed_check, has_chamfering_process,
                   start_date, end_date
            FROM cutting_management
            WHERE management_code IN ({ph})
            ORDER BY id DESC
            """
        ),
        params,
    )
    ip_res = await db.execute(
        text(
            f"""
            SELECT management_code, start_date, end_date
            FROM instruction_plans
            WHERE management_code IN ({ph})
            ORDER BY id DESC
            """
        ),
        params,
    )
    ch_res = await db.execute(
        text(
            f"""
            SELECT management_code, cutting_management_id, production_completed_check
            FROM chamfering_management
            WHERE management_code IN ({ph})
            ORDER BY id DESC
            """
        ),
        params,
    )

    cm_by_mc: dict[str, dict[str, Any]] = {}
    for row in cm_res.mappings().all():
        mc = str(row.get("management_code") or "").strip()
        if mc and mc not in cm_by_mc:
            cm_by_mc[mc] = dict(row)

    ip_by_mc: dict[str, dict[str, Any]] = {}
    for row in ip_res.mappings().all():
        mc = str(row.get("management_code") or "").strip()
        if mc and mc not in ip_by_mc:
            ip_by_mc[mc] = dict(row)

    ch_by_mc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ch_res.mappings().all():
        mc = str(row.get("management_code") or "").strip()
        if mc:
            ch_by_mc[mc].append(dict(row))

    out: dict[str, dict[str, Any]] = {}
    for mc in codes:
        out[mc] = _resolve_management_code_process_status(
            mc,
            cm_by_mc.get(mc),
            ip_by_mc.get(mc),
            ch_by_mc.get(mc, []),
            today,
        )
    return out


async def get_primary_forecast_summary(
    db: AsyncSession,
    management_codes: list[str],
    process_key: str = "molding",
) -> dict[str, dict[str, Any]]:
    """批量：management_code → 主归属日（数量最大）及纳入先明细。"""
    if not management_codes:
        return {}
    q = select(LotForecastAttribution).where(
        LotForecastAttribution.is_current.is_(True),
        LotForecastAttribution.management_code.in_(management_codes),
        LotForecastAttribution.process_key == process_key,
        LotForecastAttribution.method.in_(("FIFO_DEMAND", "CHAIN_INHERIT")),
    )
    res = await db.execute(q)
    rows = res.scalars().all()

    by_mc: dict[str, list[LotForecastAttribution]] = defaultdict(list)
    for r in rows:
        if r.management_code:
            by_mc[r.management_code].append(r)

    out: dict[str, dict[str, Any]] = {}
    for mc, items in by_mc.items():
        actual = [x for x in items if x.attribution_mode == "ACTUAL"]
        pool = actual if actual else items
        by_date: dict[str, int] = defaultdict(int)
        dests: dict[str, dict[str, Any]] = {}
        for x in pool:
            if x.forecast_attribution_date:
                ds = x.forecast_attribution_date.isoformat()
                by_date[ds] += int(x.attributed_qty or 0)
            if x.destination_cd:
                dests[x.destination_cd] = {
                    "destination_cd": x.destination_cd,
                    "demand_product_cd": x.demand_product_cd,
                    "attributed_qty": int(x.attributed_qty or 0),
                }
        primary_date = max(by_date.items(), key=lambda t: t[1])[0] if by_date else None
        out[mc] = {
            "primary_forecast_date": primary_date,
            "by_date": dict(by_date),
            "destinations": list(dests.values()),
            "attribution_mode": pool[0].attribution_mode if pool else None,
        }
    return out
