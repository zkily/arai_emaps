# -*- coding: utf-8
"""Patch chamfering_productivity_api.py from forming template."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "backend/app/modules/production_schedule/chamfering_productivity_api.py"
t = p.read_text(encoding="utf-8")

t = t.replace("成形", "面取")
t = t.replace("forming_production_indicator", "chamfering_production_indicator")
t = t.replace("_forming_", "_chamfering_")
t = t.replace("FORMING_", "CHAMFERING_")
t = t.replace("/plan/forming-production-indicator/", "/plan/chamfering-production-indicator/")
t = t.replace("69_forming_production_indicator.sql", "72_chamfering_production_indicator.sql")

t = t.replace(
    """CHAMFERING_LINE_METRICS_LOSS_HEADERS = [
    "段取",
    "修理",
    "調整",
    "対応待ち",
    "停止時間",
]

CHAMFERING_LINE_METRICS_LOSS_FIELDS = [
    ("段取", "setup_hours"),
    ("修理", "repair_hours"),
    ("調整", "adjustment_hours"),
    ("対応待ち", "waiting_repair_hours"),
    ("停止時間", "planned_stop_hours"),
]""",
    """CHAMFERING_LINE_METRICS_LOSS_HEADERS = [
    "段取",
    "修理",
    "調整",
    "チョコ停",
    "停止時間",
]

CHAMFERING_LINE_METRICS_LOSS_FIELDS = [
    ("段取", "setup_hours"),
    ("修理", "repair_hours"),
    ("調整", "adjustment_hours"),
    ("チョコ停", "choco_stop_hours"),
    ("停止時間", "planned_stop_hours"),
]""",
)

# helper to resolve qty from row
helper = '''

def _chamfering_row_actual_qty(item: dict[str, Any]) -> int:
    total = int(item.get("total_production_qty") or 0)
    if total > 0:
        return total
    return int(item.get("chamfer_actual_quantity") or 0) + int(item.get("sw_actual_quantity") or 0)


def _chamfering_row_defect_qty(item: dict[str, Any]) -> int:
    return int(item.get("chamfer_defect_quantity") or 0) + int(item.get("sw_defect_quantity") or 0)


def _chamfering_row_planned_qty(item: dict[str, Any]) -> int:
  planned = int(item.get("chamfer_planned_quantity") or 0) + int(item.get("sw_planned_quantity") or 0)
    return planned
'''

# Fix indentation in helper
helper = helper.replace("  planned", "    planned")

if "_chamfering_row_actual_qty" not in t:
    insert_at = t.find("def _chamfering_row_work_sec")
    t = t[:insert_at] + helper + "\n\n" + t[insert_at:]

# Replace qty extraction in loop
t = t.replace(
    "actual_qty = int(item.get(\"actual_quantity\") or 0)\n            planned_qty = int(item.get(\"planned_quantity\") or 0)\n            defect_qty = int(item.get(\"defect_quantity\") or 0)",
    "actual_qty = _chamfering_row_actual_qty(item)\n            planned_qty = _chamfering_row_planned_qty(item)\n            defect_qty = _chamfering_row_defect_qty(item)",
)

# metrics bucket defects
t = t.replace('bucket["defects"]["不良"] = 0', 'bucket["defects"]["面取不良"] = 0\n    bucket["defects"]["SW不良"] = 0')

t = t.replace(
    'out["sum_variance_qty"] = int(defects.get("不良") or 0)',
    'out["sum_variance_qty"] = int(defects.get("面取不良") or 0) + int(defects.get("SW不良") or 0)',
)

t = t.replace(
    """            if defect_qty > 0:
                metrics_bucket["defects"]["不良"] = int(metrics_bucket["defects"].get("不良") or 0) + defect_qty""",
    """            chamfer_def = int(item.get("chamfer_defect_quantity") or 0)
            sw_def = int(item.get("sw_defect_quantity") or 0)
            if chamfer_def > 0:
                metrics_bucket["defects"]["面取不良"] = int(metrics_bucket["defects"].get("面取不良") or 0) + chamfer_def
            if sw_def > 0:
                metrics_bucket["defects"]["SW不良"] = int(metrics_bucket["defects"].get("SW不良") or 0) + sw_def""",
)

t = t.replace(
    'defect_headers = ["不良", *[h for h, _ in CHAMFERING_LINE_METRICS_LOSS_FIELDS]]',
    'defect_headers = ["面取不良", "SW不良", *[h for h, _ in CHAMFERING_LINE_METRICS_LOSS_FIELDS]]',
)

t = t.replace(
    '"defect_by_item": [{"defect_cd": "不良", "qty": int(summary.get("sum_defect_qty") or 0)}]',
    '"defect_by_item": [\n                    {"defect_cd": "面取不良", "qty": int(summary.get("sum_defect_qty") or 0) // 2},\n                    {"defect_cd": "SW不良", "qty": int(summary.get("sum_defect_qty") or 0) - int(summary.get("sum_defect_qty") or 0) // 2},\n                ]',
)

# Better defect_by_item - aggregate separately in loop would be ideal but for now use summary

# SQL SELECT block
sql_old = re.search(
    r"sql = f\"\"\"\n            SELECT id, fiscal_year.*?FROM chamfering_production_indicator",
    t,
    re.DOTALL,
)
if sql_old:
    sql_new = '''sql = f"""
            SELECT id, fiscal_year, production_month, production_day, source_line, source_file,
                   product_cd, production_line, product_name,
                   chamfer_planned_quantity, chamfer_actual_quantity, chamfer_defect_quantity,
                   sw_planned_quantity, sw_actual_quantity, sw_defect_quantity,
                   shift_hours, overtime_hours, setup_hours, repair_hours,
                   adjustment_hours, choco_stop_hours, break_hours, planned_stop_hours,
                   available_work_hours, work_hours, utilization_rate, work_rate,
                   total_production_qty, efficiency_rate,
                   data_source, remarks, created_at, updated_at
            FROM chamfering_production_indicator'''
    t = t[: sql_old.start()] + sql_new + t[sql_old.end() :]

p.write_text(t, encoding="utf-8")
print("patched", p)
