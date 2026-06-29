"""计划态在库 / 推移试算（复用 production_summarys 公式，plan 替代 actual）。"""
from __future__ import annotations

from typing import Any

from app.modules.database.api import (
    _compute_trend_updates,
    _get_process_config_by_key,
    _num,
)

from app.modules.database.forming_plan_cascade import PROCESS_KEY_TO_PLAN_FIELD

# warehouse 列单独处理
_PLAN_FIELD_WITH_WAREHOUSE = {**PROCESS_KEY_TO_PLAN_FIELD, "warehouse": "warehouse_actual"}


def _plan_field_for_key(key: str) -> str | None:
    return _PLAN_FIELD_WITH_WAREHOUSE.get(key)


def compute_plan_inventory_updates(
    row: dict[str, Any],
    sequence: list[str],
    previous_inventories: dict[str, int],
    is_start_date: bool,
    plan_overrides: dict[str, int] | None = None,
) -> dict[str, int]:
    """
    计划态在库 = 繰越 + 计划生产 - 下游计划消费 + 前日在库。
    plan_overrides: process_key -> qty（试算 override）。
    """
    plan_overrides = plan_overrides or {}
    updates: dict[str, int] = {}

    for i, key in enumerate(sequence):
        config = _get_process_config_by_key(key)
        if not config or config["key"] == "outsourced_warehouse":
            continue
        fields = config.get("fields", {})
        inv_field = fields.get("inventory")
        if not inv_field:
            continue

        carry = _num(row, fields.get("carry", ""))
        plan_field = _plan_field_for_key(key)
        plan_qty = plan_overrides.get(key)
        if plan_qty is None and plan_field:
            plan_qty = _num(row, plan_field)
        elif plan_qty is None:
            plan_qty = 0

        next_plan = 0
        for j in range(i + 1, len(sequence)):
            next_config = _get_process_config_by_key(sequence[j])
            if not next_config:
                continue
            if next_config["key"] == "outsourced_warehouse":
                ow_field = _plan_field_for_key("outsourced_warehouse")
                if ow_field and ow_field in row:
                    next_plan = _num(row, "outsourced_warehouse_plan")
                break
            nk = next_config["key"]
            npf = _plan_field_for_key(nk)
            if npf:
                ov = plan_overrides.get(nk)
                next_plan = ov if ov is not None else _num(row, npf)
                break

        prev_inv = 0 if is_start_date else previous_inventories.get(key, 0)
        inv = carry + plan_qty - next_plan + prev_inv
        updates[inv_field] = inv

    return updates


def compute_plan_trend_updates(row: dict[str, Any], sequence: list[str]) -> dict[str, int]:
    """推移：将 row 内 actual 列临时替换为 plan 后调用 _compute_trend_updates。"""
    shadow = dict(row)
    for key, plan_field in PROCESS_KEY_TO_PLAN_FIELD.items():
        if plan_field in shadow:
            cfg = _get_process_config_by_key(key)
            if cfg and cfg.get("fields", {}).get("actual"):
                shadow[cfg["fields"]["actual"]] = _num(row, plan_field)
    return _compute_trend_updates(shadow, sequence)


def simulate_product_inventory_series(
    rows_by_date: list[tuple[str, dict[str, Any]]],
    sequence: list[str],
    overrides_by_date: dict[str, dict[str, int]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    按日期顺序试算在库与推移。
    rows_by_date: [(date_iso, row_dict), ...] 已排序
    返回 (inventory_by_date, trend_by_date)
    """
    overrides_by_date = overrides_by_date or {}
    prev_inv: dict[str, int] = {}
    inventory_results: list[dict[str, Any]] = []
    trend_results: list[dict[str, Any]] = []

    for idx, (date_iso, row) in enumerate(rows_by_date):
        is_start = idx == 0
        day_overrides = overrides_by_date.get(date_iso, {})
        inv_updates = compute_plan_inventory_updates(row, sequence, prev_inv, is_start, day_overrides)
        trend_updates = compute_plan_trend_updates(row, sequence)

        inv_entry: dict[str, Any] = {"date": date_iso}
        inv_entry.update(inv_updates)
        inventory_results.append(inv_entry)

        trend_entry: dict[str, Any] = {"date": date_iso}
        trend_entry.update(trend_updates)
        trend_results.append(trend_entry)

        prev_inv = {}
        for key in sequence:
            cfg = _get_process_config_by_key(key)
            if not cfg:
                continue
            inv_f = cfg.get("fields", {}).get("inventory")
            if inv_f and inv_f in inv_updates:
                prev_inv[key] = inv_updates[inv_f]

    return inventory_results, trend_results
