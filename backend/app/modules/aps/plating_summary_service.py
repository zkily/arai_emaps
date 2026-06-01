"""メッキ計画画面：在庫／見込ペイン用の軽量 summary 取得（KT05 ルート・SQL 絞り込み）"""

from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.database.api import (
    _enrich_production_summary_rows_pre_plating_inventory,
    _filter_out_inactive_products,
    _row_to_dict,
)
from app.modules.database.models import ProductionSummary
from app.modules.master.models import EquipmentEfficiency, ProcessRouteStep

GEN_SUFFIX_TRY = ("_actual_plan", "_plan", "_actual")

PROCESS_LABEL = {
    "cutting": "切断",
    "chamfering": "面取",
    "molding": "成型",
    "plating": "メッキ",
    "welding": "溶接",
    "inspection": "検査",
    "warehouse": "倉庫",
    "outsourced_warehouse": "外注倉庫",
    "outsourced_plating": "外注メッキ",
    "outsourced_welding": "外注溶接",
    "pre_welding_inspection": "溶接前検査",
    "pre_inspection": "外注支給前",
    "pre_outsourcing": "外注検査前",
}

ROUTE_PROCESS_ORDER = (
    "cutting",
    "chamfering",
    "molding",
    "plating",
    "welding",
    "inspection",
    "warehouse",
    "outsourced_warehouse",
    "outsourced_plating",
    "outsourced_welding",
    "pre_welding_inspection",
    "pre_inspection",
    "pre_outsourcing",
)


def _label_for_prev_key(key: Optional[str]) -> str:
    if not key:
        return "—"
    return PROCESS_LABEL.get(key, key)


def _process_order_rank(prev_key: Optional[str]) -> int:
    if not prev_key:
        return 9999
    try:
        return ROUTE_PROCESS_ORDER.index(prev_key)
    except ValueError:
        return 8000


def _normalize_machine_key(v: str) -> str:
    return str(v or "").strip().lower()


def _format_efficiency_rate(n: float) -> str:
    if n is None or not isinstance(n, (int, float)):
        return "—"
    try:
        f = float(n)
    except (TypeError, ValueError):
        return "—"
    if f != f:  # NaN
        return "—"
    return str(f)


def _pick_prev_process_gen(row: dict, prev_key: Optional[str]) -> Tuple[float, str]:
    if not prev_key:
        return 0.0, ""
    for suf in GEN_SUFFIX_TRY:
        col = f"{prev_key}{suf}"
        if col in row and row[col] is not None:
            try:
                return float(row[col]), col
            except (TypeError, ValueError):
                return 0.0, col
    return 0.0, ""


def _kt05_route_exists():
    return exists(
        select(ProcessRouteStep.id).where(
            ProcessRouteStep.route_cd == ProductionSummary.route_cd,
            ProcessRouteStep.process_cd == "KT05",
        )
    )


async def _load_kt05_summary_rows_raw(db: AsyncSession, work_date: date) -> List[dict]:
    q = (
        select(ProductionSummary)
        .where(
            ProductionSummary.date == work_date,
            _kt05_route_exists(),
        )
        .order_by(ProductionSummary.product_cd.asc())
    )
    rows = list((await db.execute(q)).scalars().all())
    return [_row_to_dict(r) for r in rows]


async def _load_efficiency_lookup(
    db: AsyncSession,
    product_cds: List[str],
) -> dict[str, dict[str, float]]:
    """key: normalize(machine)|product_cd.lower() -> efficiency_rate"""
    cds = [c.strip() for c in product_cds if c and str(c).strip()]
    if not cds:
        return {}
    q = select(EquipmentEfficiency).where(
        EquipmentEfficiency.product_cd.in_(cds),
        or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status != 0),
    )
    eff_rows = list((await db.execute(q)).scalars().all())
    by_cd: dict[str, dict[str, float]] = {}
    by_name: dict[str, dict[str, float]] = {}
    for row in eff_rows:
        eff_raw = row.efficiency_rate
        if eff_raw is None:
            continue
        try:
            eff = float(eff_raw)
        except (TypeError, ValueError):
            continue
        if eff <= 0:
            continue
        machine = str(row.machines_name or "").strip()
        if not machine:
            continue
        mk = _normalize_machine_key(machine)
        cd = str(row.product_cd or "").strip()
        name = str(row.product_name or "").strip()
        if cd:
            by_cd.setdefault(mk, {})[cd.lower()] = eff
        if name:
            by_name.setdefault(mk, {})[name.lower()] = eff
    return {"by_cd": by_cd, "by_name": by_name}


def _lookup_plating_efficiency(
    lookup: dict,
    product_cd: str,
    product_name: str,
    jig: str,
) -> str:
    jig_key = _normalize_machine_key(jig)
    if not jig_key:
        return "—"
    cd = str(product_cd or "").strip().lower()
    if cd:
        v = lookup.get("by_cd", {}).get(jig_key, {}).get(cd)
        if v is not None:
            return _format_efficiency_rate(v)
    name = str(product_name or "").strip().lower()
    if name:
        v = lookup.get("by_name", {}).get(jig_key, {}).get(name)
        if v is not None:
            return _format_efficiency_rate(v)
    return "—"


def _build_left_rows(raw_rows: List[dict], lookup: dict) -> List[dict]:
    items: List[dict] = []
    for row in raw_rows:
        cd = str(row.get("product_cd") or "").strip()
        if not cd:
            continue
        inv_raw = row.get("pre_kt05_plating_inventory")
        if inv_raw is None:
            continue
        try:
            inv_num = int(inv_raw)
        except (TypeError, ValueError):
            continue
        if inv_num <= 0:
            continue
        prev = row.get("pre_kt05_plating_prev_process")
        prev_key = str(prev).strip() if prev else None
        jig = str(row.get("plating_machine") or "").strip() or "—"
        product_name = str(row.get("product_name") or "")
        items.append(
            {
                "product_cd": cd,
                "product_name": product_name,
                "plating_machine": jig,
                "plating_efficiency": _lookup_plating_efficiency(lookup, cd, product_name, jig),
                "pre_plating_prev_label": _label_for_prev_key(prev_key),
                "pre_plating_inventory": inv_num,
                "_prev_key": prev_key,
            }
        )
    items.sort(
        key=lambda r: (
            str(r["plating_machine"]),
            _process_order_rank(r.get("_prev_key")),
            str(r["product_cd"]),
        )
    )
    for r in items:
        r.pop("_prev_key", None)
    return items


def _build_right_rows(raw_rows: List[dict], lookup: dict) -> List[dict]:
    prev_by_cd = {
        str(row.get("product_cd") or "").strip(): row.get("pre_kt05_plating_prev_process")
        for row in raw_rows
        if str(row.get("product_cd") or "").strip()
    }
    items: List[dict] = []
    for row in raw_rows:
        cd = str(row.get("product_cd") or "").strip()
        if not cd:
            continue
        prev = row.get("pre_kt05_plating_prev_process")
        prev_key = str(prev).strip() if prev else None
        qty, col = _pick_prev_process_gen(row, prev_key)
        if qty <= 0:
            continue
        jig = str(row.get("plating_machine") or "").strip() or "—"
        product_name = str(row.get("product_name") or "")
        items.append(
            {
                "product_cd": cd,
                "product_name": product_name,
                "plating_machine": jig,
                "plating_efficiency": _lookup_plating_efficiency(lookup, cd, product_name, jig),
                "pre_plating_prev_label": _label_for_prev_key(prev_key),
                "gen_qty": qty,
                "gen_source_col": col or "—",
                "_prev_key": prev_key or prev_by_cd.get(cd),
            }
        )
    items.sort(
        key=lambda r: (
            str(r["plating_machine"]),
            _process_order_rank(
                str(r.get("_prev_key")).strip() if r.get("_prev_key") else None
            ),
            str(r["product_name"]),
        )
    )
    for r in items:
        r.pop("_prev_key", None)
    return items


async def load_plating_summary_pair(
    db: AsyncSession,
    left_date: date,
    right_date: date,
) -> dict:
    left_raw = await _load_kt05_summary_rows_raw(db, left_date)
    right_raw = await _load_kt05_summary_rows_raw(db, right_date)
    merged_raw = left_raw + right_raw
    if merged_raw:
        # 旧実装は left / right 各日で enrich + inactive filter を実行していたため重かった。
        # ここで 1 回にまとめて CPU/DB 負荷を削減する。
        await _enrich_production_summary_rows_pre_plating_inventory(db, merged_raw)
        merged_raw = await _filter_out_inactive_products(db, merged_raw)
    left_key = left_date.isoformat()
    right_key = right_date.isoformat()
    left_filtered = [r for r in merged_raw if str(r.get("date") or "")[:10] == left_key]
    right_filtered = [r for r in merged_raw if str(r.get("date") or "")[:10] == right_key]
    product_cds = list(
        {
            str(r.get("product_cd") or "").strip()
            for r in left_filtered + right_filtered
            if str(r.get("product_cd") or "").strip()
        }
    )
    lookup = await _load_efficiency_lookup(db, product_cds)
    return {
        "left_inventory": _build_left_rows(left_filtered, lookup),
        "right_gen": _build_right_rows(right_filtered, lookup),
    }
