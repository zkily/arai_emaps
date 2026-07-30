"""月末在庫予測 集計サービス

基準日の工程別在庫を起点に、日別の生産数量と出荷を用いて月末までの
工程別在庫推移を日次で試算する（Time-phased Projected Available Balance 方式）。

実績の扱い:
  - 当日より後の日付は実績 0 とみなす（*_actual にデータがあっても採用しない）
  - 工程別「実績最終日」＝ 上記を適用した後の *_actual > 0 の最後の日

生産数量（各工程・各日）は工程別の「実績最終日」で切り替える:
  - 実績最終日以前 → 実績（0 の日も実績 0）
  - 実績最終日の翌日以降 → 有効計画（手動修正合計の比例配分 > 生計画 *_plan）
  実績が 1 日も無い工程は常に計画を採用する。

計画合計の手動修正（inventory_projection_plan_overrides）:
  - 工程×日の合計値のみ手入力。当日の生計画構成比で製品明細へ比例配分する
  - 手動修正はその工程だけに適用。他工程（下流含む）の計画は自動計画のまま
  - production_summarys は変更しない（本画面専用の覆盖層）

在庫式（inventory_simulator と同一）:
    在庫(d) = 繰越(d) + 当工程生産(d) - 下流工程生産(d) + 在庫(d-1)
倉庫のみ出荷（社内倉庫ルート製品の内示＝社内倉庫出荷）を差し引く。
倉庫在庫行 = 社内倉庫在庫 + 検査在庫（外注倉庫は含めない。社内倉庫ルート製品のみ）。
外注メッキ在庫（予測区間）:
    繰越 + 外注溶接生産(実績→計画) + 成型次工程移動(外注メッキ) − 外注メッキ生産(実績→計画) + 前日在庫

工程フローは製品ごとの product_route_steps を優先する（例）:
  成型の次 → 社内メッキ / 外注メッキ / 溶接 / 外注溶接 / 検査 …
  社内メッキの次 → 溶接 / 検査 …
"""

from __future__ import annotations

import time
from calendar import monthrange
from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.company_work_calendar import count_scheduled_workdays, load_company_calendar_sets
from app.modules.database.api import (
    PROCESS_CD_TO_PREFIX,
    _get_process_config_by_key,
    _get_route_sequence,
    _num,
    _row_to_dict,
)
from app.modules.database.forming_plan_cascade import PROCESS_KEY_TO_PLAN_FIELD
from app.modules.database.inventory_simulator import compute_plan_inventory_updates
from app.modules.database.models import ProductionSummary
from app.modules.database.order_process_totals_service import (
    load_order_daily_by_product_date,
    order_monthly_base_where,
)
from app.modules.erp.models import OrderDaily, OrderMonthly
from app.modules.master.models import Product, ProductRouteStep

# 表示工程グループ（生産検討会と同一の合算口径 + 検査 + 倉庫）
PROJECTION_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("cutting", "切断", ("cutting_inventory", "chamfering_inventory")),
    ("molding", "成型", ("molding_inventory",)),
    ("plating_inhouse", "社内メッキ", ("plating_inventory", "pre_welding_inspection_inventory")),
    # ※ 社内メッキ在庫行は上の列ではなく、製品ルート上「メッキ直前工程」の在庫を合算する
    (
        "plating_outsource",
        "外注メッキ",
        ("outsourced_plating_inventory", "pre_outsourcing_inventory"),
    ),
    ("welding_inhouse", "溶接", ("welding_inventory",)),
    ("welding_outsource", "外注溶接", ("outsourced_welding_inventory", "pre_inspection_inventory")),
    ("inspection", "検査", ("inspection_inventory",)),
    # ※ 検査在庫行は上の列ではなく、製品ルート上「検査直前工程」の在庫を合算する
    (
        "warehouse",
        "倉庫",
        ("warehouse_inventory", "inspection_inventory"),
    ),
)

# マトリクスの計画/実績行に使う工程キー（グループ内の代表工程）
GROUP_METRIC_PROCESS_KEYS: dict[str, tuple[str, ...]] = {
    "cutting": ("cutting",),
    "molding": ("molding",),
    "plating_inhouse": ("plating",),
    "plating_outsource": ("outsourced_plating",),
    "welding_inhouse": ("welding",),
    "welding_outsource": ("outsourced_welding",),
    "inspection": ("inspection",),
    "warehouse": (),
}

# グループ在庫の出口判定に使うメンバー（ルート上の最後のメンバーの次工程が「次工程移動」）
GROUP_MEMBER_KEYS: dict[str, tuple[str, ...]] = {
    "cutting": ("cutting", "chamfering"),
    "molding": ("molding",),
    "plating_inhouse": ("plating", "pre_welding_inspection"),
    "plating_outsource": ("outsourced_plating", "pre_outsourcing"),
    "welding_inhouse": ("welding",),
    "welding_outsource": ("outsourced_welding", "pre_inspection"),
    "inspection": ("inspection",),
    "warehouse": ("inspection", "warehouse"),
}

GROUP_NEXT_USAGE_LABEL: dict[str, str] = {
    # 切断: 成型実績があれば実績、なければ成型計画
    "cutting": "次工程使用（成型計画）",
    "molding": "次工程移動",
    "plating_inhouse": "次工程移動",
    "plating_outsource": "次工程移動",
    "welding_inhouse": "次工程移動（検査）",
    "welding_outsource": "次工程移動（外注メッキ）",
    "inspection": "次工程使用（倉庫）",
    "warehouse": "社内倉庫出荷",
}

# 成型の次工程移動を工程別に分割（日次で成型実績>0なら実績、なければ計画をルート去向で按分。行合計＝成型実績or計画）
MOLDING_NEXT_USAGE_BRANCHES: tuple[tuple[str, str], ...] = (
    ("plating", "社内メッキ"),
    ("outsourced_plating", "外注メッキ"),
    ("welding", "溶接"),
    ("outsourced_welding", "外注溶接"),
    ("inspection", "検査"),
)
MOLDING_NEXT_USAGE_KEYS = frozenset(pk for pk, _ in MOLDING_NEXT_USAGE_BRANCHES)

# 社内メッキの次工程移動を溶接／検査に分割（合計＝社内メッキ実績 or 計画）
PLATING_INHOUSE_NEXT_USAGE_BRANCHES: tuple[tuple[str, str], ...] = (
    ("welding", "溶接"),
    ("inspection", "検査"),
)
PLATING_INHOUSE_NEXT_USAGE_KEYS = frozenset(pk for pk, _ in PLATING_INHOUSE_NEXT_USAGE_BRANCHES)

# 外注メッキの次工程移動:
#   検査 = 検査工程ルート製品、外注検査 = 外注倉庫ルート製品（合計＝外注メッキ実績 or 計画）
PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES: tuple[tuple[str, str], ...] = (
    ("inspection", "検査"),
    ("outsourced_warehouse", "外注検査"),
)
PLATING_OUTSOURCE_NEXT_USAGE_KEYS = frozenset(pk for pk, _ in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES)

# 成型の次工程使用。各行＝「成型の次工程がその工程」の製品だけを合算（工程全体の実績/計画ではない）
MOLDING_NEXT_CONSUME_LABEL = "次工程使用"

# 在庫日数の分母（翌月内示の按分）。None = 全量出荷内示
GROUP_ROUTE_PROCESS_CDS: dict[str, Optional[tuple[str, ...]]] = {
    "cutting": ("KT01", "KT02"),
    "molding": None,
    "plating_inhouse": ("KT05",),
    "plating_outsource": ("KT06",),
    "welding_inhouse": ("KT07",),
    "welding_outsource": ("KT08",),
    "inspection": ("KT09",),
    "warehouse": None,
}

# 工程 key → 実績列（生産数量の優先順位1）
PROCESS_KEY_TO_ACTUAL_FIELD: dict[str, str] = {
    "cutting": "cutting_actual",
    "chamfering": "chamfering_actual",
    "molding": "molding_actual",
    "plating": "plating_actual",
    "outsourced_plating": "outsourced_plating_actual",
    "welding": "welding_actual",
    "outsourced_welding": "outsourced_welding_actual",
    "inspection": "inspection_actual",
    "pre_welding_inspection": "pre_welding_inspection_actual",
    "pre_inspection": "pre_inspection_actual",
    "pre_outsourcing": "pre_outsourcing_actual",
}

# ルート上の生産工程（計画/実績列を持つ工程）
_PRODUCTION_PROCESS_KEYS = frozenset(PROCESS_KEY_TO_PLAN_FIELD.keys())

# 計画合計の手動修正が可能な工程 key（マトリクスの計画行に対応）
EDITABLE_PLAN_PROCESS_KEYS: tuple[str, ...] = (
    "cutting",
    "molding",
    "plating",
    "outsourced_plating",
    "welding",
    "outsourced_welding",
    "inspection",
)

# ルート上に現れうるが計画列を持たない中間バッファ工程
_BUFFER_PROCESS_KEYS = frozenset({"pre_welding_inspection", "pre_inspection", "pre_outsourcing"})

_DEFAULT_SEQUENCE = [
    "cutting",
    "chamfering",
    "molding",
    "plating",
    "welding",
    "inspection",
    "warehouse",
]

# 内示バックフラッシュで先読みする日数（LT 分の需要を月末より先まで参照）
_DEMAND_LOOKAHEAD_DAYS = 45
_MAX_PROJECTION_DAYS = 120

_CACHE_TTL_SEC = 180
_CACHE_MAX_ENTRIES = 8
_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}


def parse_year_month(year_month: str) -> tuple[int, int]:
    parts = (year_month or "").strip().split("-")
    if len(parts) != 2:
        raise ValueError("year_month は YYYY-MM 形式で指定してください")
    y, m = int(parts[0]), int(parts[1])
    if not 1 <= m <= 12:
        raise ValueError("year_month の月が不正です")
    return y, m


def month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def _next_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def _daterange(ps: date, pe: date) -> list[str]:
    out: list[str] = []
    cur = ps
    while cur <= pe:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _normalize_order_cd(cd: str) -> str:
    """order_daily 側の品番正規化（末尾を 1 に）と同じルール。"""
    return f"{cd[:-1]}1" if cd else cd


def _inventory_field(key: str) -> Optional[str]:
    cfg = _get_process_config_by_key(key)
    return (cfg or {}).get("fields", {}).get("inventory")


def _zero_future_actuals(rows: list[dict[str, Any]], actual_until: date) -> None:
    """actual_until より後の日付の実績を 0 に落とす（データがあっても未来実績は使わない）。"""
    limit = actual_until.isoformat()
    fields = tuple(PROCESS_KEY_TO_ACTUAL_FIELD.values())
    for row in rows:
        ds = str(row.get("date") or "")[:10]
        if not ds or ds <= limit:
            continue
        for f in fields:
            if row.get(f):
                row[f] = 0


async def _load_summary_rows(
    db: AsyncSession, ps: date, pe: date, *, actual_until: Optional[date] = None
) -> list[dict[str, Any]]:
    q = (
        select(ProductionSummary)
        .where(and_(ProductionSummary.date >= ps, ProductionSummary.date <= pe))
        .order_by(ProductionSummary.product_cd, ProductionSummary.date)
    )
    res = await db.execute(q)
    rows = [_row_to_dict(r) for r in res.scalars().all()]

    cds = {(r.get("product_cd") or "").strip() for r in rows if r.get("product_cd")}
    inactive: set[str] = set()
    if cds:
        pr = await db.execute(
            select(Product.product_cd, Product.status).where(Product.product_cd.in_(list(cds)))
        )
        for pc, st in pr.all():
            if st and str(st).strip().lower() == "inactive":
                inactive.add(str(pc))
    rows = [r for r in rows if (r.get("product_cd") or "").strip() not in inactive]
    if actual_until is not None:
        _zero_future_actuals(rows, actual_until)
    return rows


def _normalize_sequence(keys: list[str]) -> list[str]:
    """連続重複を除去し、在庫シミュレーション対象の工程のみ残す。"""
    out: list[str] = []
    for k in keys:
        if not k or _get_process_config_by_key(k) is None:
            continue
        if out and out[-1] == k:
            continue
        out.append(k)
    return out


async def _load_product_route_sequences(db: AsyncSession) -> dict[str, list[str]]:
    """製品別工程順序（product_route_steps.step_no 昇順）。

    KT10/KT15 はいずれも外注倉庫として扱う（マスタの工程CD差異対応）。
    """
    q = select(
        ProductRouteStep.product_cd, ProductRouteStep.process_cd, ProductRouteStep.step_no
    ).order_by(ProductRouteStep.product_cd, ProductRouteStep.step_no)
    res = await db.execute(q)
    raw: dict[str, list[str]] = {}
    for product_cd, process_cd, _step in res.all():
        cd = str(product_cd or "").strip()
        pc = str(process_cd or "").strip()
        if not cd or not pc:
            continue
        key = PROCESS_CD_TO_PREFIX.get(pc)
        if not key and pc == "KT10":
            key = "outsourced_warehouse"
        if not key:
            continue
        raw.setdefault(cd, []).append(key)
    return {cd: _normalize_sequence(keys) for cd, keys in raw.items() if keys}


async def _load_forecast_daily_by_product_date(
    db: AsyncSession, ps: date, pe: date
) -> dict[str, dict[str, int]]:
    """order_daily の内示のみ（product_cd 末尾1正規化 × 日付 → forecast_units）。"""
    od = OrderDaily
    norm_cd = func.concat(func.substr(od.product_cd, 1, func.length(od.product_cd) - 1), "1")
    q = (
        select(
            norm_cd.label("product_cd"),
            od.date,
            func.sum(func.coalesce(od.forecast_units, 0)).label("forecast"),
        )
        .where(od.date >= ps, od.date <= pe)
        .group_by(norm_cd, od.date)
    )
    res = await db.execute(q)
    out: dict[str, dict[str, int]] = {}
    for row in res.all():
        cd = str(row.product_cd or "").strip()
        ds = row.date.isoformat() if row.date else ""
        if not cd or not ds:
            continue
        qty = int(row.forecast or 0)
        if qty:
            out.setdefault(cd, {})[ds] = qty
    return out


def _next_plan_process(sequence: list[str], process_key: str) -> Optional[str]:
    """ルート上で process_key の直後にある『計画列を持つ』工程。"""
    if process_key not in sequence:
        return None
    idx = sequence.index(process_key)
    for k in sequence[idx + 1 :]:
        if k in PROCESS_KEY_TO_PLAN_FIELD or k == "warehouse":
            return k
        if k in _BUFFER_PROCESS_KEYS:
            continue
    return None


def _prev_inventory_process(sequence: list[str], process_key: str) -> Optional[str]:
    """ルート上で process_key の直前にある在庫列を持つ工程。"""
    if process_key not in sequence:
        return None
    idx = sequence.index(process_key)
    for k in reversed(sequence[:idx]):
        if _inventory_field(k):
            return k
    return None


def _group_inventory_qty(
    group_key: str,
    sequence: list[str],
    col_vals: dict[str, int],
    cols: tuple[str, ...],
) -> int:
    """グループ在庫行の数量。

    - 社内メッキ: メッキ本工程ではなく、ルート上「メッキの前工程」在庫
    - 検査: 検査本工程ではなく、ルート上「検査の前工程」在庫
    - 倉庫: 社内倉庫在庫 + 検査在庫（外注倉庫は含めない。社内倉庫ルート製品のみ）
    """
    if group_key == "plating_inhouse":
        if "plating" not in sequence:
            return 0
        prev_pk = _prev_inventory_process(sequence, "plating")
        if not prev_pk:
            return 0
        inv_f = _inventory_field(prev_pk)
        return int(col_vals.get(inv_f, 0) or 0) if inv_f else 0
    if group_key == "inspection":
        if "inspection" not in sequence:
            return 0
        prev_pk = _prev_inventory_process(sequence, "inspection")
        if not prev_pk:
            return 0
        inv_f = _inventory_field(prev_pk)
        return int(col_vals.get(inv_f, 0) or 0) if inv_f else 0
    if group_key == "warehouse":
        # 社内倉庫工程を持たない製品（外注倉庫のみ等）は 0
        if "warehouse" not in sequence:
            return 0
        return int(col_vals.get("warehouse_inventory", 0) or 0) + int(
            col_vals.get("inspection_inventory", 0) or 0
        )
    return sum(int(col_vals.get(c, 0) or 0) for c in cols)


def _group_exit_process(sequence: list[str], group_key: str) -> Optional[str]:
    """グループ在庫の出口工程（メンバーのうちルート上最後の工程）。"""
    members = GROUP_MEMBER_KEYS.get(group_key) or ()
    last: Optional[str] = None
    last_idx = -1
    for m in members:
        if m in sequence:
            idx = sequence.index(m)
            if idx > last_idx:
                last_idx = idx
                last = m
    return last


def _group_next_usage_process(sequence: list[str], group_key: str) -> Optional[str]:
    """グループ在庫を消費する次工程（計画列を持つもの）。倉庫は出荷。

    外注溶接はルート上で外注メッキが後続にあればそれを優先する
    （典型: 外注溶接 → 外注支給前 → 外注メッキ）。
    """
    if group_key == "warehouse":
        return None
    if group_key == "welding_outsource":
        if "outsourced_welding" in sequence and "outsourced_plating" in sequence:
            if sequence.index("outsourced_plating") > sequence.index("outsourced_welding"):
                return "outsourced_plating"
    exit_key = _group_exit_process(sequence, group_key)
    if not exit_key:
        return None
    return _next_plan_process(sequence, exit_key)


def _compute_actual_cutoff(rows: list[dict[str, Any]]) -> dict[str, Optional[str]]:
    """工程別「実績最終日」= 実績合計 > 0 の最後の日（ISO）。実績が無ければ None。

    この日以前は実績（0 の日も実績 0 として扱う）、翌日以降は計画を採用する。
    rows は _zero_future_actuals 済みを前提とするため、当日より後は実績最終日にならない。
    """
    cutoff: dict[str, Optional[str]] = {pk: None for pk in PROCESS_KEY_TO_ACTUAL_FIELD}
    for row in rows:
        ds = str(row.get("date") or "")[:10]
        if not ds:
            continue
        for pk, field in PROCESS_KEY_TO_ACTUAL_FIELD.items():
            if _num(row, field) > 0:
                cur = cutoff[pk]
                if cur is None or ds > cur:
                    cutoff[pk] = ds
    return cutoff


def _use_actual_on(ds: str, process_key: str, cutoff: dict[str, Optional[str]]) -> bool:
    """その日に実績を採用するか（実績最終日以前なら実績、以降は計画）。"""
    last = cutoff.get(process_key)
    return last is not None and ds <= last


def _finalize_next_move_by_branch(
    display_dates: list[str],
    group_actual: dict[str, int],
    group_plan: dict[str, int],
    branch_actual: dict[str, dict[str, int]],
    branch_plan: dict[str, dict[str, int]],
    cutoff: dict[str, Optional[str]],
    *,
    process_key: str,
    branches: tuple[tuple[str, str], ...],
    fallback_pk: str,
) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """工程の次工程移動を分岐先別に確定する。

    日次ルール: 当該工程の実績最終日以前は実績で按分、以降は計画で按分。
    分岐行合計は必ずその日の工程実績（または計画）と一致させる。
    """
    branch_out: dict[str, dict[str, int]] = {pk: _empty_daily(display_dates) for pk, _ in branches}
    total_out = _empty_daily(display_dates)
    for ds in display_dates:
        act = int(group_actual.get(ds, 0) or 0)
        plan = int(group_plan.get(ds, 0) or 0)
        use_actual = _use_actual_on(ds, process_key, cutoff)
        base = act if use_actual else plan
        src = branch_actual if use_actual else branch_plan
        parts = {pk: int(src[pk].get(ds, 0) or 0) for pk, _ in branches}
        raw_sum = sum(parts.values())
        if base <= 0:
            continue
        if raw_sum <= 0:
            branch_out[fallback_pk][ds] = base
            total_out[ds] = base
            continue
        if raw_sum == base:
            for pk, v in parts.items():
                branch_out[pk][ds] = v
            total_out[ds] = base
            continue
        allocated = 0
        ordered = sorted(parts.items(), key=lambda x: -x[1])
        for i, (pk, v) in enumerate(ordered):
            if i == len(ordered) - 1:
                qty = base - allocated
            else:
                qty = int(round(base * v / raw_sum))
                allocated += qty
            branch_out[pk][ds] = max(0, qty)
        diff = base - sum(branch_out[pk][ds] for pk, _ in branches)
        if diff != 0:
            top_pk = ordered[0][0]
            branch_out[top_pk][ds] = max(0, branch_out[top_pk][ds] + diff)
        total_out[ds] = base
    return branch_out, total_out


def _finalize_molding_next_move(
    display_dates: list[str],
    group_actual: dict[str, int],
    group_plan: dict[str, int],
    branch_actual: dict[str, dict[str, int]],
    branch_plan: dict[str, dict[str, int]],
    cutoff: dict[str, Optional[str]],
) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """成型次工程移動を確定する（分岐合計＝成型実績 or 計画）。"""
    return _finalize_next_move_by_branch(
        display_dates,
        group_actual,
        group_plan,
        branch_actual,
        branch_plan,
        cutoff,
        process_key="molding",
        branches=MOLDING_NEXT_USAGE_BRANCHES,
        fallback_pk="plating",
    )


def _sum_metric_qty(row: dict[str, Any], process_keys: tuple[str, ...], *, kind: str) -> int:
    """マトリクスの計画／実績行。production_summarys の生データのみを合算する。"""
    mapping = PROCESS_KEY_TO_ACTUAL_FIELD if kind == "actual" else PROCESS_KEY_TO_PLAN_FIELD
    total = 0
    for pk in process_keys:
        field = mapping.get(pk)
        total += _num(row, field) if field else 0
    return total


def _empty_daily(dates: list[str]) -> dict[str, int]:
    return {ds: 0 for ds in dates}


_EMPTY_EFF: dict[str, int] = {}


def _resolve_day_production_qty(
    row: dict[str, Any],
    process_key: str,
    eff: dict[str, int] = _EMPTY_EFF,
    *,
    ds: str = "",
    cutoff: Optional[dict[str, Optional[str]]] = None,
) -> int:
    """生産数量。

    実績最終日（工程別）以前は実績、以降は有効計画（手動修正 > 生計画）。
    cutoff 未指定時は従来動作（実績 > 0 なら実績）。
    """
    if process_key not in _PRODUCTION_PROCESS_KEYS:
        return 0
    actual_field = PROCESS_KEY_TO_ACTUAL_FIELD.get(process_key)
    actual = _num(row, actual_field) if actual_field else 0
    if cutoff is not None:
        return (
            actual if _use_actual_on(ds, process_key, cutoff) else _plan_qty(row, process_key, eff)
        )
    if actual > 0:
        return actual
    return _plan_qty(row, process_key, eff)


async def _load_next_month_group_forecast(
    db: AsyncSession, year: int, month: int
) -> dict[str, int]:
    """翌月内示（本数）を工程グループ別に集計（product_route_steps で按分）。"""
    om = OrderMonthly
    base = order_monthly_base_where(om, year, month)
    out: dict[str, int] = {}
    for key, kts in GROUP_ROUTE_PROCESS_CDS.items():
        q = select(func.coalesce(func.sum(om.forecast_units), 0)).where(base)
        if kts:
            subq = (
                select(ProductRouteStep.product_cd)
                .where(ProductRouteStep.process_cd.in_(list(kts)))
                .distinct()
            )
            q = q.where(om.product_cd.in_(subq))
        res = await db.execute(q)
        out[key] = int(res.scalar() or 0)
    return out


async def load_plan_overrides(db: AsyncSession, ps: date, pe: date) -> dict[tuple[str, str], int]:
    """期間内の手動計画合計を取得。key=(process_key, 日付ISO)。"""
    res = await db.execute(
        text(
            "SELECT plan_date, process_key, qty FROM inventory_projection_plan_overrides "
            "WHERE plan_date BETWEEN :ps AND :pe"
        ),
        {"ps": ps, "pe": pe},
    )
    out: dict[tuple[str, str], int] = {}
    for plan_date, process_key, qty in res.all():
        out[(str(process_key), plan_date.isoformat())] = int(qty or 0)
    return out


async def upsert_plan_overrides(
    db: AsyncSession, items: list[dict[str, Any]], updated_by: Optional[str] = None
) -> int:
    """手動計画合計を一括保存（qty が None の項目は削除）。"""
    editable = set(EDITABLE_PLAN_PROCESS_KEYS)
    count = 0
    for item in items:
        pk = str(item.get("process_key") or "").strip()
        ds = str(item.get("plan_date") or "").strip()[:10]
        if pk not in editable:
            raise ValueError(f"process_key が不正です: {pk}")
        try:
            d = date.fromisoformat(ds)
        except ValueError:
            raise ValueError(f"plan_date が不正です: {ds}")
        qty = item.get("qty")
        if qty is None:
            await db.execute(
                text(
                    "DELETE FROM inventory_projection_plan_overrides "
                    "WHERE plan_date = :d AND process_key = :pk"
                ),
                {"d": d, "pk": pk},
            )
        else:
            await db.execute(
                text(
                    "INSERT INTO inventory_projection_plan_overrides "
                    "(plan_date, process_key, qty, updated_by) "
                    "VALUES (:d, :pk, :qty, :ub) "
                    "ON DUPLICATE KEY UPDATE qty = VALUES(qty), updated_by = VALUES(updated_by)"
                ),
                {"d": d, "pk": pk, "qty": max(0, int(qty)), "ub": updated_by},
            )
        count += 1
    await db.commit()
    return count


async def delete_plan_override(db: AsyncSession, plan_date: date, process_key: str) -> int:
    res = await db.execute(
        text(
            "DELETE FROM inventory_projection_plan_overrides "
            "WHERE plan_date = :d AND process_key = :pk"
        ),
        {"d": plan_date, "pk": process_key},
    )
    await db.commit()
    return int(res.rowcount or 0)


def _plan_qty(row: dict[str, Any], process_key: str, eff: dict[str, int]) -> int:
    """有効計画: 手動修正（比例配分後）があればそれ、なければ生計画。"""
    if process_key in eff:
        return eff[process_key]
    field = PROCESS_KEY_TO_PLAN_FIELD.get(process_key)
    return _num(row, field) if field else 0


def _compute_effective_plans(
    by_product: dict[str, list[dict[str, Any]]],
    sequence_by_product: dict[str, list[str]],
    overrides: dict[tuple[str, str], int],
) -> tuple[dict[tuple[str, str], dict[str, int]], dict[tuple[str, str], int]]:
    """手動計画合計を、その工程の製品明細へ比例配分する。

    ルール:
      - 手動修正した工程×日のみを対象（生計画合計 0 の日は比例配分できないため無効）
      - 当日合計は最大剰余法で手動値に厳密一致
      - 他工程（下流含む）の計画は自動計画のまま。係数は伝播しない
    戻り値: ((product_cd, 日付ISO) → {工程key: 有効計画}), 適用済み ((工程key, 日付ISO) → 手動値)
    """
    if not overrides:
        return {}, {}

    # 生計画の製品別内訳（override 対象の工程×日のみ）
    raw_shares: dict[tuple[str, str], list[tuple[str, int]]] = {}
    rows_by_prod_date: dict[str, dict[str, dict[str, Any]]] = {}
    override_dates = {ds for (_pk, ds) in overrides}
    for cd, product_rows in by_product.items():
        rbd = {str(r.get("date") or "")[:10]: r for r in product_rows}
        rows_by_prod_date[cd] = rbd
        seq = sequence_by_product.get(cd) or []
        for (pk, ds), _qty in overrides.items():
            if pk not in seq:
                continue
            row = rbd.get(ds)
            if not row:
                continue
            field = PROCESS_KEY_TO_PLAN_FIELD.get(pk)
            raw = _num(row, field) if field else 0
            if raw > 0:
                raw_shares.setdefault((pk, ds), []).append((cd, raw))

    # 手動修正した工程の製品別割当（最大剰余法で合計＝手動値）
    node_alloc: dict[tuple[str, str], dict[str, int]] = {}
    applied: dict[tuple[str, str], int] = {}
    for (pk, ds), qty in overrides.items():
        shares = raw_shares.get((pk, ds)) or []
        auto_total = sum(v for _, v in shares)
        if auto_total <= 0:
            continue  # 生計画が無い日は無効（比例配分できない）
        exact = [(cd, qty * v / auto_total) for cd, v in shares]
        floors = {cd: int(val) for cd, val in exact}
        remain = qty - sum(floors.values())
        by_frac = sorted(exact, key=lambda x: -(x[1] - int(x[1])))
        alloc = dict(floors)
        for i in range(remain):
            alloc[by_frac[i % len(by_frac)][0]] += 1
        node_alloc[(pk, ds)] = alloc
        applied[(pk, ds)] = qty

    if not node_alloc:
        return {}, {}

    # 製品×日×工程の有効計画（手動修正した工程のみ。他工程は自動計画のまま）
    eff_map: dict[tuple[str, str], dict[str, int]] = {}
    for cd, rbd in rows_by_prod_date.items():
        seq = sequence_by_product.get(cd) or []
        if not seq:
            continue
        for ds in override_dates:
            if ds not in rbd:
                continue
            eff: dict[str, int] = {}
            for pk in seq:
                if (pk, ds) in node_alloc:
                    eff[pk] = node_alloc[(pk, ds)].get(cd, 0)
            if eff:
                eff_map[(cd, ds)] = eff
    return eff_map, applied


def _plating_outsource_next_branch(sequence: list[str]) -> Optional[str]:
    """外注メッキ次工程移動の分岐先。

    - 外注倉庫ルート製品 → 外注検査
    - 検査ルート製品 → 検査
    """
    if "outsourced_plating" not in sequence:
        return None
    if "outsourced_warehouse" in sequence:
        return "outsourced_warehouse"
    if "inspection" in sequence:
        return "inspection"
    return None


def _warehouse_prev_plan_key(sequence: list[str]) -> Optional[str]:
    """倉庫直前で計画列を持つ工程 key（倉庫入庫 = その工程の生産とみなす）。"""
    if "warehouse" not in sequence:
        return None
    idx = sequence.index("warehouse")
    for k in reversed(sequence[:idx]):
        if k in PROCESS_KEY_TO_PLAN_FIELD:
            return k
    return None


def _outsourced_plating_inventory_closed(
    row: dict[str, Any],
    sequence: list[str],
    m_next: Optional[str],
    overrides: dict[str, int],
    prev_inv: dict[str, int],
) -> int:
    """外注メッキ在庫の閉形式。

    繰越 + 外注溶接生産(実績/計画) + 成型次工程移動(外注メッキ)
      − 外注メッキ生産(実績/計画) + 前日在庫
    """
    carry = _num(row, "outsourced_plating_carry_over") + _num(row, "pre_outsourcing_carry_over")
    weld_in = 0
    if "outsourced_welding" in sequence and "outsourced_plating" in sequence:
        if sequence.index("outsourced_welding") < sequence.index("outsourced_plating"):
            weld_in = int(overrides.get("outsourced_welding", 0) or 0)
    mold_in = int(overrides.get("molding", 0) or 0) if m_next == "outsourced_plating" else 0
    plate_out = int(overrides.get("outsourced_plating", 0) or 0)
    prev_op = int(prev_inv.get("outsourced_plating", 0) or 0) + int(
        prev_inv.get("pre_outsourcing", 0) or 0
    )
    return carry + weld_in + mold_in - plate_out + prev_op


async def compute_projection(db: AsyncSession, year_month: str, base_date: date) -> dict[str, Any]:
    """月末在庫予測の全量計算（サマリ + 製品別明細）。"""
    year, month = parse_year_month(year_month)
    month_start, month_end = month_bounds(year, month)

    if base_date < month_end and (month_end - base_date).days > _MAX_PROJECTION_DAYS:
        raise ValueError(f"基準日から月末まで {_MAX_PROJECTION_DAYS} 日以内にしてください")

    sim_start = base_date + timedelta(days=1)
    load_start = min(month_start, base_date)
    display_dates = _daterange(month_start, month_end)

    today = date.today()
    rows = await _load_summary_rows(db, load_start, month_end, actual_until=today)
    order_map = await load_order_daily_by_product_date(
        db, load_start, month_end + timedelta(days=_DEMAND_LOOKAHEAD_DAYS)
    )
    forecast_map = await _load_forecast_daily_by_product_date(
        db, load_start, month_end + timedelta(days=_DEMAND_LOOKAHEAD_DAYS)
    )

    ny, nm = _next_month(year, month)
    _, next_month_end = month_bounds(ny, nm)
    scheduled, off = await load_company_calendar_sets(db, load_start, next_month_end)
    month_workdays = count_scheduled_workdays(
        month_start,
        month_end,
        company_scheduled=scheduled,
        company_off=off,
        extra_workdays=set(),
        extra_holidays=set(),
    )
    next_month_workdays = count_scheduled_workdays(
        *month_bounds(ny, nm),
        company_scheduled=scheduled,
        company_off=off,
        extra_workdays=set(),
        extra_holidays=set(),
    )
    group_forecast_next = await _load_next_month_group_forecast(db, ny, nm)

    # 製品別ルートを優先（分岐: 成型→メッキ/溶接…、社内メッキ→溶接/検査…）
    # 無い製品は route_cd の標準ルート → 最後にデフォルト順
    product_sequences = await _load_product_route_sequences(db)
    route_cd_sequences: dict[str, list[str]] = {}
    by_product: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        cd = (r.get("product_cd") or "").strip()
        if not cd:
            continue
        by_product.setdefault(cd, []).append(r)
        rc = (r.get("route_cd") or "").strip()
        if rc and rc not in route_cd_sequences:
            route_cd_sequences[rc] = await _get_route_sequence(db, rc)

    sequence_by_product: dict[str, list[str]] = {}
    for cd, product_rows in by_product.items():
        route_cd = (product_rows[0].get("route_cd") or "").strip()
        sequence_by_product[cd] = (
            product_sequences.get(cd)
            or product_sequences.get(_normalize_order_cd(cd))
            or route_cd_sequences.get(route_cd)
            or list(_DEFAULT_SEQUENCE)
        )

    # 工程別「実績最終日」（この日以前は実績、以降は計画を採用）
    actual_cutoff = _compute_actual_cutoff(rows)

    # 計画合計の手動修正 → 当該工程の製品明細へ比例配分（他工程へは伝播しない）
    plan_overrides = await load_plan_overrides(db, load_start, month_end)
    eff_plan_map, applied_overrides = _compute_effective_plans(
        by_product, sequence_by_product, plan_overrides
    )

    all_inv_cols = tuple({c for _, _, cols in PROJECTION_GROUPS for c in cols})
    # 工程キー → 在庫列（ルート外工程の予測在庫を凍結/ゼロ判定に使用）
    inv_col_to_key: dict[str, str] = {}
    for cfg in (
        _get_process_config_by_key(k)
        for k in (
            "cutting",
            "chamfering",
            "molding",
            "plating",
            "outsourced_plating",
            "welding",
            "outsourced_welding",
            "inspection",
            "warehouse",
            "outsourced_warehouse",
            "pre_welding_inspection",
            "pre_inspection",
            "pre_outsourcing",
        )
    ):
        if cfg and cfg.get("fields", {}).get("inventory"):
            inv_col_to_key[cfg["fields"]["inventory"]] = cfg["key"]

    group_daily: dict[str, dict[str, int]] = {
        key: _empty_daily(display_dates) for key, _, _ in PROJECTION_GROUPS
    }
    group_plan_daily: dict[str, dict[str, int]] = {
        key: _empty_daily(display_dates) for key, _, _ in PROJECTION_GROUPS
    }
    group_plan_auto_daily: dict[str, dict[str, int]] = {
        key: _empty_daily(display_dates) for key, _, _ in PROJECTION_GROUPS
    }
    group_actual_daily: dict[str, dict[str, int]] = {
        key: _empty_daily(display_dates) for key, _, _ in PROJECTION_GROUPS
    }
    group_next_usage_daily: dict[str, dict[str, int]] = {
        key: _empty_daily(display_dates) for key, _, _ in PROJECTION_GROUPS
    }
    # 成型グループ: 次工程移動を実績/計画それぞれで工程別に集計し、後段で日次確定
    molding_branch_actual: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in MOLDING_NEXT_USAGE_BRANCHES
    }
    molding_branch_plan: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in MOLDING_NEXT_USAGE_BRANCHES
    }
    # 成型次工程使用: ルート上「成型の次＝当該工程」の製品のみ、下流工程の生産数量を合算
    molding_consume_by_branch: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in MOLDING_NEXT_USAGE_BRANCHES
    }
    # 社内メッキグループ: 次工程移動を溶接／検査に分割
    plating_inhouse_branch_actual: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in PLATING_INHOUSE_NEXT_USAGE_BRANCHES
    }
    plating_inhouse_branch_plan: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in PLATING_INHOUSE_NEXT_USAGE_BRANCHES
    }
    # 外注メッキグループ: 次工程移動を検査／外注検査に分割
    plating_outsource_branch_actual: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES
    }
    plating_outsource_branch_plan: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES
    }
    # 倉庫グループ内訳: 外注倉庫出荷 = 外注倉庫ルート製品の内示合計
    outsourced_warehouse_shipment_daily: dict[str, int] = _empty_daily(display_dates)
    demand_daily: dict[str, int] = _empty_daily(display_dates)
    product_detail: dict[str, list[dict[str, Any]]] = {key: [] for key, _, _ in PROJECTION_GROUPS}
    product_names: dict[str, str] = {}
    route_branch_stats: dict[str, dict[str, int]] = {
        "molding_next": {},
        "plating_next": {},
    }

    for product_cd, product_rows in sorted(by_product.items()):
        product_names[product_cd] = product_rows[0].get("product_name") or ""
        sequence = sequence_by_product[product_cd]
        sequence_set = set(sequence)

        # 分岐統計（デバッグ/画面注釈用）
        m_next = _next_plan_process(sequence, "molding")
        if m_next:
            route_branch_stats["molding_next"][m_next] = (
                route_branch_stats["molding_next"].get(m_next, 0) + 1
            )
        p_next = _next_plan_process(sequence, "plating")
        if p_next:
            route_branch_stats["plating_next"][p_next] = (
                route_branch_stats["plating_next"].get(p_next, 0) + 1
            )

        # グループごとの次工程使用キー（製品ルート依存）
        group_next_pk: dict[str, Optional[str]] = {
            key: _group_next_usage_process(sequence, key) for key, _, _ in PROJECTION_GROUPS
        }

        rows_by_date = {str(r.get("date") or "")[:10]: r for r in product_rows}
        demand_by_date = (
            order_map.get(_normalize_order_cd(product_cd)) or order_map.get(product_cd) or {}
        )
        forecast_by_date = (
            forecast_map.get(_normalize_order_cd(product_cd)) or forecast_map.get(product_cd) or {}
        )

        # 期初在庫: 基準日（無ければ直近過去日）の *_inventory
        base_row: dict[str, Any] = {}
        cur = base_date
        while cur >= load_start:
            r = rows_by_date.get(cur.isoformat())
            if r is not None:
                base_row = r
                break
            cur -= timedelta(days=1)
        base_inv_by_col = {c: _num(base_row, c) for c in all_inv_cols}
        prev_inv: dict[str, int] = {}
        for k in sequence:
            f = _inventory_field(k)
            if f:
                prev_inv[k] = base_inv_by_col.get(f, 0)

        wh_prev_key = _warehouse_prev_plan_key(sequence)

        # 日次シミュレーション（基準日翌日 → 月末）
        sim_inv_by_date: dict[str, dict[str, int]] = {}
        sim_prod_by_date: dict[str, dict[str, int]] = {}
        d = sim_start
        while d <= month_end:
            ds = d.isoformat()
            row = rows_by_date.get(ds) or {}
            eff = eff_plan_map.get((product_cd, ds), _EMPTY_EFF)
            overrides: dict[str, int] = {}
            for pk in sequence:
                if pk not in _PRODUCTION_PROCESS_KEYS:
                    continue
                overrides[pk] = _resolve_day_production_qty(
                    row, pk, eff, ds=ds, cutoff=actual_cutoff
                )
            if wh_prev_key and "warehouse" in sequence_set:
                # 入庫は社内倉庫ルート製品のみ（外注倉庫のみの製品は除外）
                overrides["warehouse"] = overrides.get(wh_prev_key, 0)

            updates = compute_plan_inventory_updates(row, sequence, prev_inv, False, overrides)

            # 出庫は社内倉庫出荷（内示）のみ。外注倉庫出荷は差し引かない
            if "warehouse" in sequence_set and "warehouse_inventory" in updates:
                ship = _num(row, "forecast_quantity") or forecast_by_date.get(ds, 0)
                if ship:
                    updates["warehouse_inventory"] -= int(ship or 0)

            # 外注メッキ在庫: 繰越+外注溶接+成型次工程移動(外注メッキ)−外注メッキ+前日在庫
            if "outsourced_plating" in sequence_set:
                op_inv = _outsourced_plating_inventory_closed(
                    row, sequence, m_next, overrides, prev_inv
                )
                updates["outsourced_plating_inventory"] = op_inv
                # グループ合算の二重計上を避ける（閉形式に集約）
                if "pre_outsourcing" in sequence_set:
                    updates["pre_outsourcing_inventory"] = 0

            inv_by_col: dict[str, int] = {}
            for c in all_inv_cols:
                proc_key = inv_col_to_key.get(c)
                if c in updates:
                    inv_by_col[c] = updates[c]
                elif proc_key and proc_key not in sequence_set:
                    inv_by_col[c] = 0
                else:
                    inv_by_col[c] = base_inv_by_col.get(c, 0)
            sim_inv_by_date[ds] = inv_by_col
            sim_prod_by_date[ds] = dict(overrides)

            prev_inv = {}
            for k in sequence:
                f = _inventory_field(k)
                if f and f in updates:
                    prev_inv[k] = updates[f]
            d += timedelta(days=1)

        # グループ集計 + 明細（在庫 / 計画 / 実績 / 次工程使用）
        per_group_series: dict[str, dict[str, int]] = {key: {} for key, _, _ in PROJECTION_GROUPS}
        for ds in display_dates:
            row = rows_by_date.get(ds) or {}
            eff = eff_plan_map.get((product_cd, ds), _EMPTY_EFF)

            if ds <= base_date.isoformat():
                col_vals = {c: _num(row, c) for c in all_inv_cols}
                prod_map = {
                    pk: _resolve_day_production_qty(row, pk, eff, ds=ds, cutoff=actual_cutoff)
                    for pk in sequence
                    if pk in _PRODUCTION_PROCESS_KEYS
                }
                # 倉庫入庫数量 = 直前工程の生産（社内倉庫ルート製品のみ）
                if wh_prev_key and "warehouse" in sequence_set:
                    prod_map["warehouse"] = prod_map.get(wh_prev_key, 0)
            else:
                col_vals = sim_inv_by_date.get(ds) or base_inv_by_col
                prod_map = sim_prod_by_date.get(ds) or {}

            shipment = _num(row, "order_quantity") or _num(row, "forecast_quantity")
            if not shipment:
                shipment = demand_by_date.get(ds, 0)
            demand_daily[ds] += shipment

            for key, _, cols in PROJECTION_GROUPS:
                inv_v = _group_inventory_qty(key, sequence, col_vals, cols)
                per_group_series[key][ds] = inv_v
                group_daily[key][ds] += inv_v

                metric_keys = GROUP_METRIC_PROCESS_KEYS.get(key) or ()
                if metric_keys:
                    group_plan_daily[key][ds] += sum(_plan_qty(row, pk, eff) for pk in metric_keys)
                    group_plan_auto_daily[key][ds] += _sum_metric_qty(row, metric_keys, kind="plan")
                    group_actual_daily[key][ds] += _sum_metric_qty(row, metric_keys, kind="actual")

                if key == "warehouse":
                    # 社内倉庫出荷: ルートに社内倉庫を持つ製品の内示合計
                    if "warehouse" in sequence_set:
                        forecast_qty = _num(row, "forecast_quantity") or forecast_by_date.get(ds, 0)
                        group_next_usage_daily[key][ds] += int(forecast_qty or 0)
                    # 外注倉庫出荷: ルートに外注倉庫を持つ製品の内示合計
                    if "outsourced_warehouse" in sequence_set:
                        forecast_qty = _num(row, "forecast_quantity") or forecast_by_date.get(ds, 0)
                        outsourced_warehouse_shipment_daily[ds] += int(forecast_qty or 0)
                elif key == "molding":
                    # 成型次工程移動: 去向別に実績・計画を別集計（日次の採用は後段で確定）
                    if m_next and m_next in MOLDING_NEXT_USAGE_KEYS:
                        molding_branch_actual[m_next][ds] += _num(row, "molding_actual")
                        molding_branch_plan[m_next][ds] += _plan_qty(row, "molding", eff)
                        # 次工程使用: 成型の次がその工程の製品だけ、下流の生産数量（実績最終日切替）
                        molding_consume_by_branch[m_next][ds] += _resolve_day_production_qty(
                            row, m_next, eff, ds=ds, cutoff=actual_cutoff
                        )
                elif key == "plating_inhouse":
                    # 社内メッキ次工程移動: 溶接／検査へ去向別に集計（後段で確定）
                    if p_next and p_next in PLATING_INHOUSE_NEXT_USAGE_KEYS:
                        plating_inhouse_branch_actual[p_next][ds] += _num(row, "plating_actual")
                        plating_inhouse_branch_plan[p_next][ds] += _plan_qty(row, "plating", eff)
                elif key == "plating_outsource":
                    # 外注メッキ次工程移動: 検査／外注検査（製品の所属工程で分岐）
                    op_branch = _plating_outsource_next_branch(sequence)
                    if op_branch and op_branch in PLATING_OUTSOURCE_NEXT_USAGE_KEYS:
                        plating_outsource_branch_actual[op_branch][ds] += _num(
                            row, "outsourced_plating_actual"
                        )
                        plating_outsource_branch_plan[op_branch][ds] += _plan_qty(
                            row, "outsourced_plating", eff
                        )
                else:
                    next_pk = group_next_pk.get(key)
                    if next_pk:
                        # 下流工程生産（検査→倉庫 含む）。倉庫は直前工程生産を入庫とみなす
                        if next_pk == "warehouse":
                            qty = int(
                                prod_map.get("warehouse", 0)
                                or (prod_map.get(wh_prev_key, 0) if wh_prev_key else 0)
                                or 0
                            )
                        else:
                            qty = int(prod_map.get(next_pk, 0) or 0)
                        group_next_usage_daily[key][ds] += qty

        month_end_iso = month_end.isoformat()
        for key, _, _cols in PROJECTION_GROUPS:
            series = per_group_series[key]
            if any(series.values()):
                product_detail[key].append(
                    {
                        "product_cd": product_cd,
                        "product_name": product_names[product_cd],
                        "route_sequence": sequence,
                        "molding_next": m_next,
                        "plating_next": p_next,
                        "by_date": series,
                        "month_end": series.get(month_end_iso, 0),
                    }
                )

    for key in product_detail:
        product_detail[key].sort(key=lambda x: -abs(x.get("month_end", 0)))

    # 成型次工程移動: 実績最終日以前は実績、以降は計画。行合計＝成型実績 or 成型計画
    molding_next_usage_by_branch, molding_next_total = _finalize_molding_next_move(
        display_dates,
        group_actual_daily["molding"],
        group_plan_daily["molding"],
        molding_branch_actual,
        molding_branch_plan,
        actual_cutoff,
    )
    group_next_usage_daily["molding"] = molding_next_total

    # 社内メッキ次工程移動: 溶接／検査。合計＝社内メッキ実績 or 計画
    plating_inhouse_next_by_branch, plating_inhouse_next_total = _finalize_next_move_by_branch(
        display_dates,
        group_actual_daily["plating_inhouse"],
        group_plan_daily["plating_inhouse"],
        plating_inhouse_branch_actual,
        plating_inhouse_branch_plan,
        actual_cutoff,
        process_key="plating",
        branches=PLATING_INHOUSE_NEXT_USAGE_BRANCHES,
        fallback_pk="welding",
    )
    group_next_usage_daily["plating_inhouse"] = plating_inhouse_next_total

    # 外注メッキ次工程移動: 検査／外注検査。合計＝外注メッキ実績 or 計画
    plating_outsource_next_by_branch, plating_outsource_next_total = _finalize_next_move_by_branch(
        display_dates,
        group_actual_daily["plating_outsource"],
        group_plan_daily["plating_outsource"],
        plating_outsource_branch_actual,
        plating_outsource_branch_plan,
        actual_cutoff,
        process_key="outsourced_plating",
        branches=PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES,
        fallback_pk="inspection",
    )
    group_next_usage_daily["plating_outsource"] = plating_outsource_next_total

    # 成型次工程使用親行 = 子行の合計（いずれも成型ルート去向でフィルタ済み）
    molding_consume_daily: dict[str, int] = _empty_daily(display_dates)
    for pk, _label in MOLDING_NEXT_USAGE_BRANCHES:
        for ds in display_dates:
            molding_consume_daily[ds] += molding_consume_by_branch[pk].get(ds, 0)

    month_end_iso = month_end.isoformat()
    groups_out: list[dict[str, Any]] = []
    for key, name, _cols in PROJECTION_GROUPS:
        month_end_qty = group_daily[key].get(month_end_iso, 0)
        forecast_next = group_forecast_next.get(key, 0)
        daily_avg = (forecast_next / next_month_workdays) if next_month_workdays > 0 else 0
        days_of_supply = round(month_end_qty / daily_avg, 1) if daily_avg > 0 else None
        metric_keys = GROUP_METRIC_PROCESS_KEYS.get(key) or ()
        rep_pk = metric_keys[0] if metric_keys else None
        plan_override_daily = {
            ds: qty for (pk, ds), qty in applied_overrides.items() if pk == rep_pk
        }
        groups_out.append(
            {
                "key": key,
                "name": name,
                "process_key": rep_pk,
                "daily": group_daily[key],
                "plan_daily": group_plan_daily[key],
                "plan_auto_daily": group_plan_auto_daily[key],
                "plan_override_daily": plan_override_daily,
                "actual_daily": group_actual_daily[key],
                "next_usage_daily": group_next_usage_daily[key],
                "next_usage_label": GROUP_NEXT_USAGE_LABEL.get(key, "次工程移動"),
                "next_usage_rows": (
                    [
                        {
                            "key": pk,
                            "label": label,
                            "daily": molding_next_usage_by_branch[pk],
                        }
                        for pk, label in MOLDING_NEXT_USAGE_BRANCHES
                    ]
                    if key == "molding"
                    else (
                        [
                            {
                                "key": pk,
                                "label": label,
                                "daily": plating_inhouse_next_by_branch[pk],
                            }
                            for pk, label in PLATING_INHOUSE_NEXT_USAGE_BRANCHES
                        ]
                        if key == "plating_inhouse"
                        else (
                            [
                                {
                                    "key": pk,
                                    "label": label,
                                    "daily": plating_outsource_next_by_branch[pk],
                                }
                                for pk, label in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES
                            ]
                            if key == "plating_outsource"
                            else None
                        )
                    )
                ),
                "next_consume_daily": molding_consume_daily if key == "molding" else None,
                "next_consume_label": MOLDING_NEXT_CONSUME_LABEL if key == "molding" else None,
                "next_consume_rows": (
                    [
                        {
                            "key": pk,
                            "label": label,
                            "daily": molding_consume_by_branch[pk],
                        }
                        for pk, label in MOLDING_NEXT_USAGE_BRANCHES
                    ]
                    if key == "molding"
                    else None
                ),
                "outsourced_warehouse_shipment_daily": (
                    outsourced_warehouse_shipment_daily if key == "warehouse" else None
                ),
                "month_end": month_end_qty,
                "days_of_supply": days_of_supply,
                "next_month_forecast": forecast_next,
                "next_month_workdays": next_month_workdays,
            }
        )

    return {
        "year_month": f"{year:04d}-{month:02d}",
        "base_date": base_date.isoformat(),
        "projection_start": sim_start.isoformat(),
        "dates": display_dates,
        "groups": groups_out,
        "demand_daily": demand_daily,
        "product_count": len(by_product),
        "month_workdays": month_workdays,
        "production_qty_rule": "actual until last-actual-day, then plan(manual override first)",
        "actual_until": today.isoformat(),
        "actual_cutoff": {pk: ds for pk, ds in actual_cutoff.items() if ds},
        "route_branch_stats": route_branch_stats,
        "_product_detail": product_detail,
    }


async def get_projection_cached(
    db: AsyncSession, year_month: str, base_date: date, force: bool = False
) -> dict[str, Any]:
    key = (year_month, base_date.isoformat())
    now = time.monotonic()
    if not force:
        hit = _cache.get(key)
        if hit and now - hit[0] < _CACHE_TTL_SEC:
            return hit[1]
    payload = await compute_projection(db, year_month, base_date)
    if len(_cache) >= _CACHE_MAX_ENTRIES:
        oldest = min(_cache, key=lambda k: _cache[k][0])
        _cache.pop(oldest, None)
    _cache[key] = (now, payload)
    return payload
