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
  - 次工程移動が複数分岐の工程で手動計画がある日は、直近実績の去向平均比で各分岐へ配分する

マトリクス在庫行（予測区間）:
  在庫(d) = 繰越 + 当工程生産(実績→計画) − 次工程使用 + 前日在庫
  倉庫のみ: 繰越(検査+倉庫) + 検査生産 − 社内倉庫出荷 + 前日在庫

在庫推移（成型/メッキ/溶接/検査）:
  基準日以前 = 各製品ルート上の前工程在庫の合計
  予測区間 = 前工程繰越 + 上流入庫 − 当該工程生産 + 前日の前工程在庫

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
    (
        "plating_outsource",
        "外注メッキ",
        ("outsourced_plating_inventory", "pre_outsourcing_inventory"),
    ),
    ("welding_inhouse", "溶接", ("welding_inventory",)),
    ("welding_outsource", "外注溶接", ("outsourced_welding_inventory", "pre_inspection_inventory")),
    ("inspection", "検査", ("inspection_inventory",)),
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
    "welding_inhouse": "次工程移動",
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

# 溶接の次工程移動を検査／社内メッキ／外注メッキに分割（合計＝溶接実績 or 計画）
WELDING_INHOUSE_NEXT_USAGE_BRANCHES: tuple[tuple[str, str], ...] = (
    ("inspection", "検査"),
    ("plating", "社内メッキ"),
    ("outsourced_plating", "外注メッキ"),
)
WELDING_INHOUSE_NEXT_USAGE_KEYS = frozenset(pk for pk, _ in WELDING_INHOUSE_NEXT_USAGE_BRANCHES)

# 成型の次工程使用。各行＝「成型の次工程がその工程」の製品だけを合算（工程全体の実績/計画ではない）
MOLDING_NEXT_CONSUME_LABEL = "次工程使用"

# 社内メッキの次工程使用。各行＝「社内メッキの次がその工程」の製品だけ、下流（溶接/検査）の実績→計画
PLATING_INHOUSE_NEXT_CONSUME_LABEL = "次工程使用"

# 外注メッキの次工程使用。各行＝検査ルート→検査生産、外注倉庫ルート→外注倉庫生産（実績→計画）
PLATING_OUTSOURCE_NEXT_CONSUME_LABEL = "次工程使用"

# 溶接の次工程使用。各行＝溶接の次が検査/社内メッキ/外注メッキの製品だけ、下流生産（実績→計画）
WELDING_INHOUSE_NEXT_CONSUME_LABEL = "次工程使用"

# 外注溶接の次工程使用（外注メッキ）
WELDING_OUTSOURCE_NEXT_CONSUME_BRANCHES: tuple[tuple[str, str], ...] = (
    ("outsourced_plating", "外注メッキ"),
)
WELDING_OUTSOURCE_NEXT_CONSUME_KEYS = frozenset(
    pk for pk, _ in WELDING_OUTSOURCE_NEXT_CONSUME_BRANCHES
)
WELDING_OUTSOURCE_NEXT_CONSUME_LABEL = "次工程使用"

# 在庫推移（マトリクス末尾）: 当該工程の「前工程在庫」を起点に予測
# (group_key, 表示ラベル, ルート上のアンカー工程)
INVENTORY_TREND_BRANCHES: tuple[tuple[str, str, str], ...] = (
    ("molding", "成型在庫", "molding"),
    ("plating_inhouse", "メッキ在庫", "plating"),
    ("welding_inhouse", "溶接在庫", "welding"),
    ("inspection", "検査在庫", "inspection"),
)

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
    "outsourced_warehouse": "outsourced_warehouse_actual",
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
# 次工程移動の手動計画配分: 直近この日数分の実績去向合計から平均比を算出
NEXT_MOVE_RATIO_LOOKBACK_DAYS = 30

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


def _prev_process_inventory_qty(
    anchor_pk: str,
    sequence: list[str],
    col_vals: dict[str, int],
) -> int:
    """当該工程を持つ製品について、ルート上の前工程在庫を返す。"""
    if anchor_pk not in sequence:
        return 0
    prev_pk = _prev_inventory_process(sequence, anchor_pk)
    if not prev_pk:
        return 0
    inv_f = _inventory_field(prev_pk)
    return int(col_vals.get(inv_f, 0) or 0) if inv_f else 0


def _prev_process_carry_qty(
    anchor_pk: str,
    sequence: list[str],
    row: dict[str, Any],
) -> int:
    """在庫推移用: アンカー工程の直前工程の繰越（当該工程の繰越ではない）。"""
    if anchor_pk not in sequence:
        return 0
    prev_pk = _prev_inventory_process(sequence, anchor_pk)
    if not prev_pk:
        return 0
    cfg = _get_process_config_by_key(prev_pk)
    carry_f = (cfg or {}).get("fields", {}).get("carry")
    return _num(row, carry_f) if carry_f else 0


def _group_inventory_qty(
    group_key: str,
    sequence: list[str],
    col_vals: dict[str, int],
    cols: tuple[str, ...],
) -> int:
    """グループ在庫行の数量。

    - 倉庫: 社内倉庫在庫 + 検査在庫（外注倉庫は含めない。社内倉庫ルート製品のみ）
    - その他: グループ定義の在庫列合計（当該工程在庫）
    """
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


def _ratios_from_branch_totals(
    totals: dict[str, int],
    branches: tuple[tuple[str, str], ...],
    fallback_pk: str,
) -> dict[str, float]:
    """実績去向合計から各分岐の構成比を返す。合計 0 のときは fallback に 100%。"""
    keys = [pk for pk, _ in branches]
    total = sum(int(totals.get(pk, 0) or 0) for pk in keys)
    if total <= 0:
        return {pk: (1.0 if pk == fallback_pk else 0.0) for pk in keys}
    return {pk: int(totals.get(pk, 0) or 0) / total for pk in keys}


def _allocate_by_ratios(
    base: int,
    ratios: dict[str, float],
    branches: tuple[tuple[str, str], ...],
    fallback_pk: str,
) -> dict[str, int]:
    """base を ratios で最大剰余法配分（合計＝base）。"""
    keys = [pk for pk, _ in branches]
    if base <= 0:
        return {pk: 0 for pk in keys}
    if not keys:
        return {}
    exact = [(pk, base * float(ratios.get(pk, 0.0) or 0.0)) for pk in keys]
    floors = {pk: int(val) for pk, val in exact}
    remain = base - sum(floors.values())
    by_frac = sorted(exact, key=lambda x: -(x[1] - int(x[1])))
    out = dict(floors)
    if remain > 0 and by_frac:
        for i in range(remain):
            out[by_frac[i % len(by_frac)][0]] += 1
    elif remain > 0:
        out[fallback_pk] = out.get(fallback_pk, 0) + remain
    # 丸め誤差の最終調整
    diff = base - sum(out.get(pk, 0) for pk in keys)
    if diff != 0:
        top = max(keys, key=lambda pk: float(ratios.get(pk, 0.0) or 0.0))
        out[top] = max(0, out.get(top, 0) + diff)
    return {pk: max(0, int(out.get(pk, 0) or 0)) for pk in keys}


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
    historical_ratios: Optional[dict[str, float]] = None,
    override_dates: Optional[set[str]] = None,
) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """工程の次工程移動を分岐先別に確定する。

    日次ルール:
      - 実績最終日以前 → 当日実績の去向比で按分
      - 計画日かつ手動修正あり → 直近実績の平均去向比で手動計画合計を按分
      - それ以外の計画日 → 当日計画の去向比で按分
    分岐行合計は必ずその日の工程実績（または計画）と一致させる。
    """
    branch_out: dict[str, dict[str, int]] = {pk: _empty_daily(display_dates) for pk, _ in branches}
    total_out = _empty_daily(display_dates)
    override_dates = override_dates or set()
    for ds in display_dates:
        act = int(group_actual.get(ds, 0) or 0)
        plan = int(group_plan.get(ds, 0) or 0)
        use_actual = _use_actual_on(ds, process_key, cutoff)
        base = act if use_actual else plan
        if base <= 0:
            continue

        # 手動計画日: 直近実績平均比で配分
        if (
            not use_actual
            and ds in override_dates
            and historical_ratios
            and any(float(historical_ratios.get(pk, 0.0) or 0.0) > 0 for pk, _ in branches)
        ):
            allocated = _allocate_by_ratios(base, historical_ratios, branches, fallback_pk)
            for pk, v in allocated.items():
                branch_out[pk][ds] = v
            total_out[ds] = base
            continue

        src = branch_actual if use_actual else branch_plan
        parts = {pk: int(src[pk].get(ds, 0) or 0) for pk, _ in branches}
        raw_sum = sum(parts.values())
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
    *,
    historical_ratios: Optional[dict[str, float]] = None,
    override_dates: Optional[set[str]] = None,
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
        historical_ratios=historical_ratios,
        override_dates=override_dates,
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
    ratio_start = month_start - timedelta(days=NEXT_MOVE_RATIO_LOOKBACK_DAYS)
    load_start = min(month_start, base_date, ratio_start)
    display_dates = _daterange(month_start, month_end)

    today = date.today()
    rows = await _load_summary_rows(db, load_start, month_end, actual_until=today)
    order_map = await load_order_daily_by_product_date(
        db, month_start, month_end + timedelta(days=_DEMAND_LOOKAHEAD_DAYS)
    )
    forecast_map = await _load_forecast_daily_by_product_date(
        db, month_start, month_end + timedelta(days=_DEMAND_LOOKAHEAD_DAYS)
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
    plan_overrides = await load_plan_overrides(db, month_start, month_end)
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
    # グループ別 繰越（メンバー工程の carry 列合計。閉形式在庫の入力）
    group_carry_daily: dict[str, dict[str, int]] = {
        key: _empty_daily(display_dates) for key, _, _ in PROJECTION_GROUPS
    }
    group_carry_fields: dict[str, tuple[str, ...]] = {}
    for key, _, _cols in PROJECTION_GROUPS:
        fields: list[str] = []
        for mk in GROUP_MEMBER_KEYS.get(key) or ():
            cfg = _get_process_config_by_key(mk)
            cf = (cfg or {}).get("fields", {}).get("carry")
            if cf:
                fields.append(cf)
        group_carry_fields[key] = tuple(fields)
    # 基準日のグループ在庫（基準日が対象月外のときの閉形式の起点）
    group_base_inventory: dict[str, int] = {key: 0 for key, _, _ in PROJECTION_GROUPS}
    # 在庫推移（前工程在庫起点）
    trend_daily: dict[str, dict[str, int]] = {
        key: _empty_daily(display_dates) for key, _, _ in INVENTORY_TREND_BRANCHES
    }
    trend_base: dict[str, int] = {key: 0 for key, _, _ in INVENTORY_TREND_BRANCHES}
    # 前工程の繰越（在庫推移の閉形式用。group_carry = 当該工程繰越とは別）
    trend_carry_daily: dict[str, dict[str, int]] = {
        key: _empty_daily(display_dates) for key, _, _ in INVENTORY_TREND_BRANCHES
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
    # 社内メッキ次工程使用: ルート上「社内メッキの次＝溶接/検査」の製品のみ、下流の生産数量を合算
    plating_inhouse_consume_by_branch: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in PLATING_INHOUSE_NEXT_USAGE_BRANCHES
    }
    # 外注メッキ次工程使用: 検査／外注検査（外注倉庫）へ去向別に下流生産を合算
    plating_outsource_consume_by_branch: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES
    }
    # 溶接次工程使用: 検査／社内メッキ／外注メッキへ去向別に下流生産を合算
    welding_inhouse_consume_by_branch: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in WELDING_INHOUSE_NEXT_USAGE_BRANCHES
    }
    # 外注溶接次工程使用: 外注メッキへ去向の下流生産を合算
    welding_outsource_consume_by_branch: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in WELDING_OUTSOURCE_NEXT_CONSUME_BRANCHES
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
    # 溶接グループ: 次工程移動を検査／社内メッキに分割
    welding_inhouse_branch_actual: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in WELDING_INHOUSE_NEXT_USAGE_BRANCHES
    }
    welding_inhouse_branch_plan: dict[str, dict[str, int]] = {
        pk: _empty_daily(display_dates) for pk, _ in WELDING_INHOUSE_NEXT_USAGE_BRANCHES
    }
    # 手動計画の次工程移動配分用: 直近実績の去向合計（数量加重）
    hist_molding_branch_totals: dict[str, int] = {
        pk: 0 for pk, _ in MOLDING_NEXT_USAGE_BRANCHES
    }
    hist_plating_inhouse_branch_totals: dict[str, int] = {
        pk: 0 for pk, _ in PLATING_INHOUSE_NEXT_USAGE_BRANCHES
    }
    hist_plating_outsource_branch_totals: dict[str, int] = {
        pk: 0 for pk, _ in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES
    }
    hist_welding_inhouse_branch_totals: dict[str, int] = {
        pk: 0 for pk, _ in WELDING_INHOUSE_NEXT_USAGE_BRANCHES
    }
    ratio_end = min(base_date, today)
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
        w_next = _next_plan_process(sequence, "welding")
        ow_next = _next_plan_process(sequence, "outsourced_welding")
        op_branch_hist = _plating_outsource_next_branch(sequence)

        # 直近実績の去向合計（手動計画の次工程移動配分比）
        for r in product_rows:
            ds_h = str(r.get("date") or "")[:10]
            if not ds_h:
                continue
            try:
                d_h = date.fromisoformat(ds_h)
            except ValueError:
                continue
            if d_h < ratio_start or d_h > ratio_end:
                continue
            if m_next and m_next in MOLDING_NEXT_USAGE_KEYS:
                a = _num(r, "molding_actual")
                if a > 0:
                    hist_molding_branch_totals[m_next] += a
            if p_next and p_next in PLATING_INHOUSE_NEXT_USAGE_KEYS:
                a = _num(r, "plating_actual")
                if a > 0:
                    hist_plating_inhouse_branch_totals[p_next] += a
            if op_branch_hist and op_branch_hist in PLATING_OUTSOURCE_NEXT_USAGE_KEYS:
                a = _num(r, "outsourced_plating_actual")
                if a > 0:
                    hist_plating_outsource_branch_totals[op_branch_hist] += a
            if w_next and w_next in WELDING_INHOUSE_NEXT_USAGE_KEYS:
                a = _num(r, "welding_actual")
                if a > 0:
                    hist_welding_inhouse_branch_totals[w_next] += a

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
        for key, _, cols in PROJECTION_GROUPS:
            group_base_inventory[key] += _group_inventory_qty(key, sequence, base_inv_by_col, cols)
        for trend_key, _label, anchor_pk in INVENTORY_TREND_BRANCHES:
            trend_base[trend_key] += _prev_process_inventory_qty(
                anchor_pk, sequence, base_inv_by_col
            )

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
                group_carry_daily[key][ds] += sum(
                    _num(row, f) for f in group_carry_fields.get(key) or ()
                )

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
                        # 次工程使用: 社内メッキの次がその工程の製品だけ、下流の生産数量（実績最終日切替）
                        plating_inhouse_consume_by_branch[p_next][ds] += _resolve_day_production_qty(
                            row, p_next, eff, ds=ds, cutoff=actual_cutoff
                        )
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
                        # 次工程使用: 検査＝検査生産、外注検査＝外注倉庫生産（実績最終日切替）
                        plating_outsource_consume_by_branch[op_branch][ds] += (
                            _resolve_day_production_qty(
                                row, op_branch, eff, ds=ds, cutoff=actual_cutoff
                            )
                        )
                elif key == "welding_inhouse":
                    # 溶接次工程移動: 検査／社内メッキ／外注メッキへ去向別に集計（後段で確定）
                    if w_next and w_next in WELDING_INHOUSE_NEXT_USAGE_KEYS:
                        welding_inhouse_branch_actual[w_next][ds] += _num(row, "welding_actual")
                        welding_inhouse_branch_plan[w_next][ds] += _plan_qty(row, "welding", eff)
                        # 次工程使用: 溶接の次がその工程の製品だけ、下流の生産数量（実績最終日切替）
                        welding_inhouse_consume_by_branch[w_next][ds] += _resolve_day_production_qty(
                            row, w_next, eff, ds=ds, cutoff=actual_cutoff
                        )
                elif key == "welding_outsource":
                    # 次工程使用（外注メッキ）: 外注溶接の次が外注メッキの製品のみ
                    if ow_next and ow_next in WELDING_OUTSOURCE_NEXT_CONSUME_KEYS:
                        welding_outsource_consume_by_branch[ow_next][ds] += (
                            _resolve_day_production_qty(
                                row, ow_next, eff, ds=ds, cutoff=actual_cutoff
                            )
                        )
                    next_pk = group_next_pk.get(key)
                    if next_pk:
                        group_next_usage_daily[key][ds] += int(prod_map.get(next_pk, 0) or 0)
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

            # 在庫推移: 基準日以前は前工程在庫を合算（予測区間は後段の閉形式）
            # 前工程繰越は予測閉形式用に全日集計
            for trend_key, _label, anchor_pk in INVENTORY_TREND_BRANCHES:
                trend_carry_daily[trend_key][ds] += _prev_process_carry_qty(
                    anchor_pk, sequence, row
                )
                if ds <= base_date.isoformat():
                    trend_daily[trend_key][ds] += _prev_process_inventory_qty(
                        anchor_pk, sequence, col_vals
                    )

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

    # 手動計画日の次工程移動配分比（直近実績の数量加重平均）
    molding_hist_ratios = _ratios_from_branch_totals(
        hist_molding_branch_totals, MOLDING_NEXT_USAGE_BRANCHES, "plating"
    )
    plating_inhouse_hist_ratios = _ratios_from_branch_totals(
        hist_plating_inhouse_branch_totals, PLATING_INHOUSE_NEXT_USAGE_BRANCHES, "welding"
    )
    plating_outsource_hist_ratios = _ratios_from_branch_totals(
        hist_plating_outsource_branch_totals, PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES, "inspection"
    )
    welding_inhouse_hist_ratios = _ratios_from_branch_totals(
        hist_welding_inhouse_branch_totals, WELDING_INHOUSE_NEXT_USAGE_BRANCHES, "inspection"
    )
    override_dates_by_process: dict[str, set[str]] = {}
    for pk, ds in applied_overrides:
        override_dates_by_process.setdefault(pk, set()).add(ds)

    # 成型次工程移動: 実績最終日以前は実績、以降は計画。行合計＝成型実績 or 成型計画
    molding_next_usage_by_branch, molding_next_total = _finalize_molding_next_move(
        display_dates,
        group_actual_daily["molding"],
        group_plan_daily["molding"],
        molding_branch_actual,
        molding_branch_plan,
        actual_cutoff,
        historical_ratios=molding_hist_ratios,
        override_dates=override_dates_by_process.get("molding"),
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
        historical_ratios=plating_inhouse_hist_ratios,
        override_dates=override_dates_by_process.get("plating"),
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
        historical_ratios=plating_outsource_hist_ratios,
        override_dates=override_dates_by_process.get("outsourced_plating"),
    )
    group_next_usage_daily["plating_outsource"] = plating_outsource_next_total

    # 溶接次工程移動: 検査／社内メッキ／外注メッキ。合計＝溶接実績 or 計画
    welding_inhouse_next_by_branch, welding_inhouse_next_total = _finalize_next_move_by_branch(
        display_dates,
        group_actual_daily["welding_inhouse"],
        group_plan_daily["welding_inhouse"],
        welding_inhouse_branch_actual,
        welding_inhouse_branch_plan,
        actual_cutoff,
        process_key="welding",
        branches=WELDING_INHOUSE_NEXT_USAGE_BRANCHES,
        fallback_pk="inspection",
        historical_ratios=welding_inhouse_hist_ratios,
        override_dates=override_dates_by_process.get("welding"),
    )
    group_next_usage_daily["welding_inhouse"] = welding_inhouse_next_total

    # ---- 次工程使用の日次合計（在庫閉形式の減算に使用） ----
    def _group_prod(key: str, rep_pk: str, ds: str) -> int:
        return int(
            (
                group_actual_daily[key][ds]
                if _use_actual_on(ds, rep_pk, actual_cutoff)
                else group_plan_daily[key][ds]
            )
            or 0
        )

    # 切断の次工程使用（成型計画）= 成型生産（実績最終日以前は実績、以降は計画）
    for ds in display_dates:
        group_next_usage_daily["cutting"][ds] = _group_prod("molding", "molding", ds)

    molding_consume_daily: dict[str, int] = _empty_daily(display_dates)
    for pk, _label in MOLDING_NEXT_USAGE_BRANCHES:
        for ds in display_dates:
            molding_consume_daily[ds] += molding_consume_by_branch[pk].get(ds, 0)

    plating_inhouse_consume_daily: dict[str, int] = _empty_daily(display_dates)
    for pk, _label in PLATING_INHOUSE_NEXT_USAGE_BRANCHES:
        for ds in display_dates:
            plating_inhouse_consume_daily[ds] += plating_inhouse_consume_by_branch[pk].get(ds, 0)

    plating_outsource_consume_daily: dict[str, int] = _empty_daily(display_dates)
    for pk, _label in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES:
        for ds in display_dates:
            plating_outsource_consume_daily[ds] += plating_outsource_consume_by_branch[pk].get(
                ds, 0
            )

    welding_inhouse_consume_daily: dict[str, int] = _empty_daily(display_dates)
    for pk, _label in WELDING_INHOUSE_NEXT_USAGE_BRANCHES:
        for ds in display_dates:
            welding_inhouse_consume_daily[ds] += welding_inhouse_consume_by_branch[pk].get(ds, 0)

    welding_outsource_consume_daily: dict[str, int] = _empty_daily(display_dates)
    for pk, _label in WELDING_OUTSOURCE_NEXT_CONSUME_BRANCHES:
        for ds in display_dates:
            welding_outsource_consume_daily[ds] += welding_outsource_consume_by_branch[pk].get(
                ds, 0
            )

    # ---- マトリクス在庫行: 繰越 + 当工程生産 − 次工程使用 + 前日在庫 ----
    def _inv_own_prod(key: str, ds: str) -> int:
        if key == "cutting":
            return _group_prod("cutting", "cutting", ds)
        if key == "molding":
            return _group_prod("molding", "molding", ds)
        if key == "plating_inhouse":
            return _group_prod("plating_inhouse", "plating", ds)
        if key == "plating_outsource":
            return _group_prod("plating_outsource", "outsourced_plating", ds)
        if key == "welding_inhouse":
            return _group_prod("welding_inhouse", "welding", ds)
        if key == "welding_outsource":
            return _group_prod("welding_outsource", "outsourced_welding", ds)
        if key == "inspection":
            return _group_prod("inspection", "inspection", ds)
        if key == "warehouse":
            # 倉庫入庫 = 検査生産
            return _group_prod("inspection", "inspection", ds)
        return 0

    def _inv_next_consume(key: str, ds: str) -> int:
        if key == "cutting":
            return int(group_next_usage_daily["cutting"][ds] or 0)
        if key == "molding":
            return int(molding_consume_daily[ds] or 0)
        if key == "plating_inhouse":
            return int(plating_inhouse_consume_daily[ds] or 0)
        if key == "plating_outsource":
            return int(plating_outsource_consume_daily[ds] or 0)
        if key == "welding_inhouse":
            return int(welding_inhouse_consume_daily[ds] or 0)
        if key == "welding_outsource":
            return int(welding_outsource_consume_daily[ds] or 0)
        if key == "inspection":
            # 次工程使用（倉庫）
            return int(group_next_usage_daily["inspection"][ds] or 0)
        if key == "warehouse":
            # 社内倉庫出荷
            return int(group_next_usage_daily["warehouse"][ds] or 0)
        return 0

    base_iso = base_date.isoformat()
    for key, _, _cols in PROJECTION_GROUPS:
        prev = group_base_inventory.get(key, 0)
        for ds in display_dates:
            if ds <= base_iso:
                prev = group_daily[key][ds]
                continue
            val = (
                group_carry_daily[key][ds]
                + _inv_own_prod(key, ds)
                - _inv_next_consume(key, ds)
                + prev
            )
            group_daily[key][ds] = val
            prev = val

    # ---- 在庫推移: 前工程繰越 + 上流入庫 − 当該工程生産 + 前日 ----
    def _trend_inflow(trend_key: str, ds: str) -> int:
        if trend_key == "molding":
            return _group_prod("cutting", "cutting", ds)
        if trend_key == "plating_inhouse":
            return int(molding_next_usage_by_branch["plating"][ds] or 0) + int(
                welding_inhouse_next_by_branch["plating"][ds] or 0
            )
        if trend_key == "welding_inhouse":
            return int(molding_next_usage_by_branch["welding"][ds] or 0) + int(
                plating_inhouse_next_by_branch["welding"][ds] or 0
            )
        if trend_key == "inspection":
            # 社内メッキ／外注メッキ／成型／溶接 → 検査
            return (
                int(plating_inhouse_next_by_branch["inspection"][ds] or 0)
                + int(plating_outsource_next_by_branch["inspection"][ds] or 0)
                + int(molding_next_usage_by_branch["inspection"][ds] or 0)
                + int(welding_inhouse_next_by_branch["inspection"][ds] or 0)
            )
        return 0

    def _trend_out_prod(trend_key: str, ds: str) -> int:
        if trend_key == "molding":
            return _group_prod("molding", "molding", ds)
        if trend_key == "plating_inhouse":
            return _group_prod("plating_inhouse", "plating", ds)
        if trend_key == "welding_inhouse":
            return _group_prod("welding_inhouse", "welding", ds)
        if trend_key == "inspection":
            return _group_prod("inspection", "inspection", ds)
        return 0

    for trend_key, _label, _anchor in INVENTORY_TREND_BRANCHES:
        prev = trend_base.get(trend_key, 0)
        for ds in display_dates:
            if ds <= base_iso:
                prev = trend_daily[trend_key][ds]
                continue
            val = (
                trend_carry_daily[trend_key][ds]
                + _trend_inflow(trend_key, ds)
                - _trend_out_prod(trend_key, ds)
                + prev
            )
            trend_daily[trend_key][ds] = val
            prev = val

    # 成型次工程使用親行 = 子行の合計（いずれも成型ルート去向でフィルタ済み）
    next_consume_by_group: dict[str, tuple[str, dict[str, int], list[dict[str, Any]]]] = {
        "molding": (
            MOLDING_NEXT_CONSUME_LABEL,
            molding_consume_daily,
            [
                {"key": pk, "label": label, "daily": molding_consume_by_branch[pk]}
                for pk, label in MOLDING_NEXT_USAGE_BRANCHES
            ],
        ),
        "plating_inhouse": (
            PLATING_INHOUSE_NEXT_CONSUME_LABEL,
            plating_inhouse_consume_daily,
            [
                {"key": pk, "label": label, "daily": plating_inhouse_consume_by_branch[pk]}
                for pk, label in PLATING_INHOUSE_NEXT_USAGE_BRANCHES
            ],
        ),
        "plating_outsource": (
            PLATING_OUTSOURCE_NEXT_CONSUME_LABEL,
            plating_outsource_consume_daily,
            [
                {"key": pk, "label": label, "daily": plating_outsource_consume_by_branch[pk]}
                for pk, label in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES
            ],
        ),
        "welding_inhouse": (
            WELDING_INHOUSE_NEXT_CONSUME_LABEL,
            welding_inhouse_consume_daily,
            [
                {"key": pk, "label": label, "daily": welding_inhouse_consume_by_branch[pk]}
                for pk, label in WELDING_INHOUSE_NEXT_USAGE_BRANCHES
            ],
        ),
        "welding_outsource": (
            WELDING_OUTSOURCE_NEXT_CONSUME_LABEL,
            welding_outsource_consume_daily,
            [
                {"key": pk, "label": label, "daily": welding_outsource_consume_by_branch[pk]}
                for pk, label in WELDING_OUTSOURCE_NEXT_CONSUME_BRANCHES
            ],
        ),
    }

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
        next_usage_rows_by_key: dict[str, list[dict[str, Any]]] = {
            "molding": [
                {"key": pk, "label": label, "daily": molding_next_usage_by_branch[pk]}
                for pk, label in MOLDING_NEXT_USAGE_BRANCHES
            ],
            "plating_inhouse": [
                {"key": pk, "label": label, "daily": plating_inhouse_next_by_branch[pk]}
                for pk, label in PLATING_INHOUSE_NEXT_USAGE_BRANCHES
            ],
            "plating_outsource": [
                {"key": pk, "label": label, "daily": plating_outsource_next_by_branch[pk]}
                for pk, label in PLATING_OUTSOURCE_NEXT_USAGE_BRANCHES
            ],
            "welding_inhouse": [
                {"key": pk, "label": label, "daily": welding_inhouse_next_by_branch[pk]}
                for pk, label in WELDING_INHOUSE_NEXT_USAGE_BRANCHES
            ],
        }
        consume_meta = next_consume_by_group.get(key)
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
                "next_usage_rows": next_usage_rows_by_key.get(key),
                "next_consume_daily": consume_meta[1] if consume_meta else None,
                "next_consume_label": consume_meta[0] if consume_meta else None,
                "next_consume_rows": consume_meta[2] if consume_meta else None,
                "outsourced_warehouse_shipment_daily": (
                    outsourced_warehouse_shipment_daily if key == "warehouse" else None
                ),
                "month_end": month_end_qty,
                "days_of_supply": days_of_supply,
                "next_month_forecast": forecast_next,
                "next_month_workdays": next_month_workdays,
            }
        )

    inventory_trend_rows = [
        {
            "key": key,
            "label": label,
            "daily": trend_daily[key],
            "month_end": trend_daily[key].get(month_end_iso, 0),
        }
        for key, label, _anchor in INVENTORY_TREND_BRANCHES
    ]

    return {
        "year_month": f"{year:04d}-{month:02d}",
        "base_date": base_date.isoformat(),
        "projection_start": sim_start.isoformat(),
        "dates": display_dates,
        "groups": groups_out,
        "inventory_trend_rows": inventory_trend_rows,
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
