"""成型计划 → 各工程计划级联（内存试算，与 update-plan SQL 规则一致）。"""
from __future__ import annotations

from typing import Any

from app.modules.database.api import ACTUAL_PLAN_COLUMNS, _num

# process_cd 集合 → 路由是否含该工程
KT_CUTTING = "KT01"
KT_CHAMFERING = "KT02"
KT_PLATING = "KT05"
KT_WELDING = "KT07"
KT_INSPECTION = "KT09"
KT_OUTSOURCED_PLATING = "KT06"
KT_OUTSOURCED_WELDING = "KT08"
KT_OUTSOURCED_WAREHOUSE = frozenset({"KT10", "KT15"})

# 各工程合计：品番 routing 含对应 process_cd 时，其 molding_plan 计入该工程
PROCESS_KEY_ROUTE_CDS: dict[str, frozenset[str]] = {
    "cutting": frozenset({KT_CUTTING}),
    "chamfering": frozenset({KT_CHAMFERING}),
    "plating": frozenset({KT_PLATING}),
    "outsourced_plating": frozenset({KT_OUTSOURCED_PLATING}),
    "welding": frozenset({KT_WELDING}),
    "outsourced_welding": frozenset({KT_OUTSOURCED_WELDING}),
    "inspection": frozenset({KT_INSPECTION}),
    "outsourced_warehouse": KT_OUTSOURCED_WAREHOUSE,
}

PROCESS_KEY_TO_PLAN_FIELD: dict[str, str] = {
    "cutting": "cutting_plan",
    "chamfering": "chamfering_plan",
    "molding": "molding_plan",
    "plating": "plating_plan",
    "outsourced_plating": "outsourced_plating_plan",
    "welding": "welding_plan",
    "outsourced_welding": "outsourced_welding_plan",
    "inspection": "inspection_plan",
    "outsourced_warehouse": "outsourced_warehouse_plan",
}

SIMULATION_PROCESS_KEYS = (
    "cutting",
    "chamfering",
    "molding",
    "plating",
    "outsourced_plating",
    "welding",
    "outsourced_welding",
    "inspection",
    "outsourced_warehouse",
)

UNSET_MACHINE_LABEL = "(設備未設定)"

# 工程 key → production_summarys の設備列
PROCESS_KEY_MACHINE_FIELD: dict[str, str] = {
    "cutting": "cutting_machine",
    "chamfering": "chamfering_machine",
    "molding": "molding_machine",
    "plating": "plating_machine",
    "outsourced_plating": "outsourced_plating_machine",
    "welding": "welding_machine",
    "outsourced_welding": "outsourced_welding_machine",
    "inspection": "inspector_machine",
}


def pick_product_machine(product_rows: list[dict[str, Any]], process_key: str) -> str | None:
    """期間内の行から当該工程の設備名を取得（新しい日付優先）。無ければ None。"""
    field = PROCESS_KEY_MACHINE_FIELD.get(process_key)
    if not field or not product_rows:
        return None
    sorted_rows = sorted(product_rows, key=lambda r: str(r.get("date") or ""), reverse=True)
    for row in sorted_rows:
        v = (row.get(field) or "").strip()
        if v:
            return v
    return None


def compute_actual_plans(row: dict[str, Any]) -> None:
    """actual 优先、plan 补齐 → *_actual_plan（原地更新）。"""
    for actual_col, plan_col, target_col in ACTUAL_PLAN_COLUMNS:
        actual = _num(row, actual_col)
        plan = _num(row, plan_col)
        row[target_col] = actual if actual else plan


def apply_molding_cascade_to_row(
    row: dict[str, Any],
    route_process_cds: set[str],
    has_sw_machine: bool,
) -> None:
    """
    按 update-plan 规则，以 molding_plan / molding_actual_plan 为基准更新 row 内各 *_plan。
    plating / welding / inspection 保持 row 原值（来自 DB / APS）。
    """
    compute_actual_plans(row)

    molding_plan = _num(row, "molding_plan")
    molding_actual_plan = _num(row, "molding_actual_plan")

    if KT_CUTTING in route_process_cds:
        row["cutting_plan"] = molding_actual_plan
    if KT_CHAMFERING in route_process_cds:
        row["chamfering_plan"] = molding_actual_plan
    if has_sw_machine:
        row["sw_plan"] = molding_actual_plan
    if KT_OUTSOURCED_PLATING in route_process_cds:
        row["outsourced_plating_plan"] = molding_plan
    if KT_OUTSOURCED_WELDING in route_process_cds:
        row["outsourced_welding_plan"] = molding_plan
    if route_process_cds & KT_OUTSOURCED_WAREHOUSE:
        row["outsourced_warehouse_plan"] = molding_plan


def molding_derived_plan_for_process(
    molding_plan: int,
    process_key: str,
    route_process_cds: set[str],
) -> int:
    """
    由成型计划按路由归属推算各工程计划数。
    仅当 route 含该工程 process_cd 时计入 molding_plan，否则 0。
    """
    if process_key == "molding":
        return int(molding_plan)
    required = PROCESS_KEY_ROUTE_CDS.get(process_key)
    if not required:
        return 0
    if route_process_cds & required:
        return int(molding_plan)
    return 0


def get_final_plan_qty(row: dict[str, Any], process_key: str, override: int | None = None) -> int:
    """override > 级联 plan 列。"""
    if override is not None:
        return int(override)
    field = PROCESS_KEY_TO_PLAN_FIELD.get(process_key)
    if not field:
        return 0
    return _num(row, field)
