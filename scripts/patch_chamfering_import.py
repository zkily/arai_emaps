# -*- coding: utf-8
"""Patch chamfering_production_indicator_import.py from forming template."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "backend/app/services/chamfering_production_indicator_import.py"
t = p.read_text(encoding="utf-8")

t = t.replace("成形", "面取")
t = t.replace("forming_production_indicator", "chamfering_production_indicator")
t = t.replace("form_excel:", "cham_excel:")
t = t.replace("ParsedFormingIndicatorRow", "ParsedChamferingIndicatorRow")
t = t.replace("sync_forming_source_file", "sync_chamfering_source_file")
t = t.replace("iter_forming_excel_rows", "iter_chamfering_excel_rows")
t = t.replace("resolve_forming_data_sheet", "resolve_chamfering_data_sheet")
t = t.replace("_sheet_has_forming_headers", "_sheet_has_chamfering_headers")
t = t.replace("FORMING_SHEET_HEADER_MARKERS", "CHAMFERING_SHEET_HEADER_MARKERS")
t = t.replace(
    'CHAMFERING_SHEET_HEADER_MARKERS = ("日付", "ライン", "品名", "生産数")',
    'CHAMFERING_SHEET_HEADER_MARKERS = ("日付", "ライン", "品名", "面取計画")',
)

old_cols = """COLUMN_FIELD_NAMES = [
    "product_cd",
    "production_day",
    "production_line",
    "product_name",
    "planned_quantity",
    "actual_quantity",
    "defect_quantity",
    "shift_hours",
    "overtime_hours",
    "setup_hours",
    "repair_hours",
    "adjustment_hours",
    "break_hours",
    "waiting_repair_hours",
    "planned_stop_hours",
    "available_work_hours",
    "work_hours",
    "utilization_rate",
    "work_rate",
    "efficiency_rate",
    "setup_adjustment_flag",
    "yellow_box_qty",
    "metric_60",
]"""

new_cols = """COLUMN_FIELD_NAMES = [
    "product_cd",
    "production_day",
    "production_line",
    "product_name",
    "chamfer_planned_quantity",
    "chamfer_actual_quantity",
    "chamfer_defect_quantity",
    "sw_planned_quantity",
    "sw_actual_quantity",
    "sw_defect_quantity",
    "shift_hours",
    "overtime_hours",
    "setup_hours",
    "repair_hours",
    "adjustment_hours",
    "choco_stop_hours",
    "break_hours",
    "planned_stop_hours",
    "available_work_hours",
    "work_hours",
    "utilization_rate",
    "work_rate",
    "total_production_qty",
    "efficiency_rate",
]"""

if old_cols not in t:
    raise SystemExit("COLUMN_FIELD_NAMES block not found")
t = t.replace(old_cols, new_cols)

t = t.replace(
    """INT_FIELDS = frozenset(
    {
        "planned_quantity",
        "actual_quantity",
        "defect_quantity",
        "yellow_box_qty",
    }
)""",
    """INT_FIELDS = frozenset(
    {
        "chamfer_planned_quantity",
        "chamfer_actual_quantity",
        "chamfer_defect_quantity",
        "sw_planned_quantity",
        "sw_actual_quantity",
        "sw_defect_quantity",
        "total_production_qty",
    }
)""",
)

t = t.replace(
    """DECIMAL_FIELDS = frozenset(
    {
        "shift_hours",
        "overtime_hours",
        "setup_hours",
        "repair_hours",
        "adjustment_hours",
        "break_hours",
        "waiting_repair_hours",
        "planned_stop_hours",
        "available_work_hours",
        "work_hours",
        "utilization_rate",
        "work_rate",
        "efficiency_rate",
    }
)""",
    """DECIMAL_FIELDS = frozenset(
    {
        "shift_hours",
        "overtime_hours",
        "setup_hours",
        "repair_hours",
        "adjustment_hours",
        "choco_stop_hours",
        "break_hours",
        "planned_stop_hours",
        "available_work_hours",
        "work_hours",
        "utilization_rate",
        "work_rate",
        "efficiency_rate",
    }
)""",
)

t = t.replace(
    """        elif field_name == "metric_60":
            s = _cell_str(raw)
            out[field_name] = s if s else None
        elif field_name == "setup_adjustment_flag":
            s = _cell_str(raw)
            out[field_name] = s if s else None
        else:""",
    "        else:",
)

t = t.replace(
    """    planned = fields.get("planned_quantity") or 0
    actual = fields.get("actual_quantity") or 0
    work_h = fields.get("work_hours")
    if not name and not cd and planned == 0 and actual == 0 and (work_h is None or work_h <= 0):""",
    """    total = fields.get("total_production_qty") or 0
    chamfer = fields.get("chamfer_actual_quantity") or 0
    sw = fields.get("sw_actual_quantity") or 0
    work_h = fields.get("work_hours")
    if not name and not cd and total == 0 and chamfer == 0 and sw == 0 and (work_h is None or work_h <= 0):""",
)

# Parsed row dataclass fields - replace block between @dataclass classes
import re

parsed_old = re.search(
    r"@dataclass\nclass ParsedChamferingIndicatorRow:.*?(?=\n@dataclass\nclass ImportSyncResult)",
    t,
    re.DOTALL,
)
if not parsed_old:
    raise SystemExit("ParsedChamferingIndicatorRow not found")

parsed_new = '''@dataclass
class ParsedChamferingIndicatorRow:
    source_line: int
    fiscal_year: int | None
    production_month: date | None
    production_day: date
    product_cd: str | None
    production_line: str | None
    product_name: str | None
    chamfer_planned_quantity: int | None
    chamfer_actual_quantity: int | None
    chamfer_defect_quantity: int | None
    sw_planned_quantity: int | None
    sw_actual_quantity: int | None
    sw_defect_quantity: int | None
    shift_hours: float | None
    overtime_hours: float | None
    setup_hours: float | None
    repair_hours: float | None
    adjustment_hours: float | None
    choco_stop_hours: float | None
    break_hours: float | None
    planned_stop_hours: float | None
    available_work_hours: float | None
    work_hours: float | None
    utilization_rate: float | None
    work_rate: float | None
    total_production_qty: int | None
    efficiency_rate: float | None
    external_sync_key: str
    data_source: str
    remarks: str
    source_file: str'''

t = t[: parsed_old.start()] + parsed_new + t[parsed_old.end() :]

# make_external_sync_key
t = t.replace(
    """        str(fields.get("planned_quantity") or ""),
        str(fields.get("actual_quantity") or ""),
        str(fields.get("defect_quantity") or ""),""",
    """        str(fields.get("chamfer_actual_quantity") or ""),
        str(fields.get("sw_actual_quantity") or ""),
        str(fields.get("total_production_qty") or ""),""",
)

# parse_logical_row return
parse_old = re.search(
    r"return ParsedChamferingIndicatorRow\(\n        source_line=source_line,.*?\n    \)",
    t,
    re.DOTALL,
)
if not parse_old:
    raise SystemExit("parse_logical_row return not found")

parse_new = """return ParsedChamferingIndicatorRow(
        source_line=source_line,
        fiscal_year=fiscal_year,
        production_month=prod_day.replace(day=1) if prod_day else None,
        production_day=prod_day,
        product_cd=(fields.get("product_cd") or "").strip() or None,
        production_line=(fields.get("production_line") or "").strip() or None,
        product_name=(fields.get("product_name") or "").strip() or None,
        chamfer_planned_quantity=fields.get("chamfer_planned_quantity"),
        chamfer_actual_quantity=fields.get("chamfer_actual_quantity"),
        chamfer_defect_quantity=fields.get("chamfer_defect_quantity"),
        sw_planned_quantity=fields.get("sw_planned_quantity"),
        sw_actual_quantity=fields.get("sw_actual_quantity"),
        sw_defect_quantity=fields.get("sw_defect_quantity"),
        shift_hours=fields.get("shift_hours"),
        overtime_hours=fields.get("overtime_hours"),
        setup_hours=fields.get("setup_hours"),
        repair_hours=fields.get("repair_hours"),
        adjustment_hours=fields.get("adjustment_hours"),
        choco_stop_hours=fields.get("choco_stop_hours"),
        break_hours=fields.get("break_hours"),
        planned_stop_hours=fields.get("planned_stop_hours"),
        available_work_hours=fields.get("available_work_hours"),
        work_hours=fields.get("work_hours"),
        utilization_rate=fields.get("utilization_rate"),
        work_rate=fields.get("work_rate"),
        total_production_qty=fields.get("total_production_qty"),
        efficiency_rate=fields.get("efficiency_rate"),
        external_sync_key=sync_key,
        data_source=DATA_SOURCE_CSV if remarks_prefix == REMARKS_PREFIX_CSV else DATA_SOURCE_EXCEL,
        remarks=f"{remarks_prefix}:{source_label}:L{source_line}",
        source_file=source_label,
    )"""

t = t[: parse_old.start()] + parse_new + t[parse_old.end() :]

# INSERT_COLUMNS + _row_to_insert_tuple
insert_old = re.search(r"INSERT_COLUMNS = \[.*?\]\n\n\ndef _row_to_insert_tuple", t, re.DOTALL)
if not insert_old:
    raise SystemExit("INSERT_COLUMNS not found")

insert_new = """INSERT_COLUMNS = [
    "fiscal_year",
    "production_month",
    "production_day",
    "source_line",
    "source_file",
    "product_cd",
    "production_line",
    "product_name",
    "chamfer_planned_quantity",
    "chamfer_actual_quantity",
    "chamfer_defect_quantity",
    "sw_planned_quantity",
    "sw_actual_quantity",
    "sw_defect_quantity",
    "shift_hours",
    "overtime_hours",
    "setup_hours",
    "repair_hours",
    "adjustment_hours",
    "choco_stop_hours",
    "break_hours",
    "planned_stop_hours",
    "available_work_hours",
    "work_hours",
    "utilization_rate",
    "work_rate",
    "total_production_qty",
    "efficiency_rate",
    "data_source",
    "external_sync_key",
    "remarks",
]


def _row_to_insert_tuple"""

t = t[: insert_old.start()] + insert_new + t[insert_old.end() :]

tuple_old = re.search(r"def _row_to_insert_tuple\(row: ParsedChamferingIndicatorRow\) -> tuple:.*?\n\n\ndef sync_parsed_rows_to_db", t, re.DOTALL)
if not tuple_old:
    raise SystemExit("_row_to_insert_tuple not found")

tuple_new = """def _row_to_insert_tuple(row: ParsedChamferingIndicatorRow) -> tuple:
    return (
        row.fiscal_year,
        row.production_month,
        row.production_day,
        row.source_line,
        row.source_file,
        row.product_cd,
        row.production_line,
        row.product_name,
        row.chamfer_planned_quantity,
        row.chamfer_actual_quantity,
        row.chamfer_defect_quantity,
        row.sw_planned_quantity,
        row.sw_actual_quantity,
        row.sw_defect_quantity,
        row.shift_hours,
        row.overtime_hours,
        row.setup_hours,
        row.repair_hours,
        row.adjustment_hours,
        row.choco_stop_hours,
        row.break_hours,
        row.planned_stop_hours,
        row.available_work_hours,
        row.work_hours,
        row.utilization_rate,
        row.work_rate,
        row.total_production_qty,
        row.efficiency_rate,
        row.data_source,
        row.external_sync_key,
        row.remarks,
    )


def sync_parsed_rows_to_db"""

t = t[: tuple_old.start()] + tuple_new + t[tuple_old.end() :]

p.write_text(t, encoding="utf-8")
print("patched", p)
