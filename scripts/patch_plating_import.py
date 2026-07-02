# -*- coding: utf-8
"""Patch plating_production_indicator_import.py for メッキ daily CSV."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "backend/app/services/plating_production_indicator_import.py"
t = p.read_text(encoding="utf-8")

t = t.replace("面取", "メッキ")
t = t.replace("chamfering_production_indicator", "plating_production_indicator")
t = t.replace("cham_excel:", "plat_excel:")
t = t.replace("ParsedChamferingIndicatorRow", "ParsedPlatingIndicatorRow")
t = t.replace("sync_chamfering_source_file", "sync_plating_source_file")
t = t.replace("iter_chamfering_excel_rows", "iter_plating_excel_rows")
t = t.replace("resolve_chamfering_data_sheet", "resolve_plating_data_sheet")
t = t.replace("_sheet_has_chamfering_headers", "_sheet_has_plating_headers")
t = t.replace("CHAMFERING_SHEET_HEADER_MARKERS", "PLATING_SHEET_HEADER_MARKERS")
t = t.replace(
    'PLATING_SHEET_HEADER_MARKERS = ("日付", "ライン", "品名", "面取計画")',
    'PLATING_SHEET_HEADER_MARKERS = ("日付", "計画数", "実績数")',
)
t = t.replace("PRODUCT_CD_RE = re.compile(r\"^\\d{4,6}$\")\n\n", "")

cols = """COLUMN_FIELD_NAMES = [
    "production_day",
    "planned_quantity",
    "actual_quantity",
    "defect_quantity",
    "defect_plating_scratch",
    "defect_moya_kaburi",
    "defect_nickel",
    "defect_contact",
    "defect_other",
    "shift_hours",
    "maintenance_hours",
    "trouble_hours",
    "choco_stop_hours",
    "planned_stop_hours",
    "available_work_hours",
    "work_hours",
    "work_rate",
    "utilization_rate",
    "total_inspection_qty",
    "efficiency_rate",
]"""

t = re.sub(r"COLUMN_FIELD_NAMES = \[.*?\]", cols, t, count=1, flags=re.S)

t = re.sub(
    r"INT_FIELDS = frozenset\(\n    \{.*?\}\n\)",
    """INT_FIELDS = frozenset(
    {
        "planned_quantity",
        "actual_quantity",
        "defect_quantity",
        "defect_plating_scratch",
        "defect_moya_kaburi",
        "defect_nickel",
        "defect_contact",
        "defect_other",
        "total_inspection_qty",
    }
)""",
    t,
    count=1,
    flags=re.S,
)

t = re.sub(
    r"DECIMAL_FIELDS = frozenset\(\n    \{.*?\}\n\)",
    """DECIMAL_FIELDS = frozenset(
    {
        "shift_hours",
        "maintenance_hours",
        "trouble_hours",
        "choco_stop_hours",
        "planned_stop_hours",
        "available_work_hours",
        "work_hours",
        "work_rate",
        "utilization_rate",
        "efficiency_rate",
    }
)""",
    t,
    count=1,
    flags=re.S,
)

# is_data_row
t = re.sub(
    r"def is_data_row\(fields: dict\[str, Any\]\) -> bool:.*?return True",
    """def is_data_row(fields: dict[str, Any]) -> bool:
    if fields.get("production_day") is None:
        return False
    actual = fields.get("actual_quantity") or 0
    planned = fields.get("planned_quantity") or 0
    work_h = fields.get("work_hours")
    if actual == 0 and planned == 0 and (work_h is None or work_h <= 0):
        return False
    return True""",
    t,
    count=1,
    flags=re.S,
)

parsed = """@dataclass
class ParsedPlatingIndicatorRow:
    source_line: int
    fiscal_year: int | None
    production_month: date | None
    production_day: date
    planned_quantity: int | None
    actual_quantity: int | None
    defect_quantity: int | None
    defect_plating_scratch: int | None
    defect_moya_kaburi: int | None
    defect_nickel: int | None
    defect_contact: int | None
    defect_other: int | None
    shift_hours: float | None
    maintenance_hours: float | None
    trouble_hours: float | None
    choco_stop_hours: float | None
    planned_stop_hours: float | None
    available_work_hours: float | None
    work_hours: float | None
    work_rate: float | None
    utilization_rate: float | None
    total_inspection_qty: int | None
    efficiency_rate: float | None
    external_sync_key: str
    data_source: str
    remarks: str
    source_file: str"""

t = re.sub(
    r"@dataclass\nclass ParsedPlatingIndicatorRow:.*?(?=\n@dataclass\nclass ImportSyncResult)",
    parsed,
    t,
    count=1,
    flags=re.S,
)

t = re.sub(
    r"def make_external_sync_key\(source_file: str, source_line: int, fields: dict\[str, Any\]\) -> str:.*?return f\"\{EXTERNAL_SYNC_KEY_PREFIX\}\{digest\}\"",
    """def make_external_sync_key(source_file: str, source_line: int, fields: dict[str, Any]) -> str:
    parts = [
        source_file,
        str(source_line),
        (fields.get("production_day") or "").isoformat() if fields.get("production_day") else "",
        str(fields.get("planned_quantity") or ""),
        str(fields.get("actual_quantity") or ""),
        str(fields.get("work_hours") or ""),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:40]
    return f"{EXTERNAL_SYNC_KEY_PREFIX}{digest}\"""",
    t,
    count=1,
    flags=re.S,
)

parse_ret = """return ParsedPlatingIndicatorRow(
        source_line=source_line,
        fiscal_year=fiscal_year,
        production_month=prod_day.replace(day=1) if prod_day else None,
        production_day=prod_day,
        planned_quantity=fields.get("planned_quantity"),
        actual_quantity=fields.get("actual_quantity"),
        defect_quantity=fields.get("defect_quantity"),
        defect_plating_scratch=fields.get("defect_plating_scratch"),
        defect_moya_kaburi=fields.get("defect_moya_kaburi"),
        defect_nickel=fields.get("defect_nickel"),
        defect_contact=fields.get("defect_contact"),
        defect_other=fields.get("defect_other"),
        shift_hours=fields.get("shift_hours"),
        maintenance_hours=fields.get("maintenance_hours"),
        trouble_hours=fields.get("trouble_hours"),
        choco_stop_hours=fields.get("choco_stop_hours"),
        planned_stop_hours=fields.get("planned_stop_hours"),
        available_work_hours=fields.get("available_work_hours"),
        work_hours=fields.get("work_hours"),
        work_rate=fields.get("work_rate"),
        utilization_rate=fields.get("utilization_rate"),
        total_inspection_qty=fields.get("total_inspection_qty"),
        efficiency_rate=fields.get("efficiency_rate"),
        external_sync_key=sync_key,
        data_source=DATA_SOURCE_CSV if remarks_prefix == REMARKS_PREFIX_CSV else DATA_SOURCE_EXCEL,
        remarks=f"{remarks_prefix}:{source_label}:L{source_line}",
        source_file=source_label,
    )"""

t = re.sub(
    r"return ParsedPlatingIndicatorRow\(\n        source_line=source_line,.*?\n    \)",
    parse_ret,
    t,
    count=1,
    flags=re.S,
)

insert = """INSERT_COLUMNS = [
    "fiscal_year",
    "production_month",
    "production_day",
    "source_line",
    "source_file",
    "planned_quantity",
    "actual_quantity",
    "defect_quantity",
    "defect_plating_scratch",
    "defect_moya_kaburi",
    "defect_nickel",
    "defect_contact",
    "defect_other",
    "shift_hours",
    "maintenance_hours",
    "trouble_hours",
    "choco_stop_hours",
    "planned_stop_hours",
    "available_work_hours",
    "work_hours",
    "work_rate",
    "utilization_rate",
    "total_inspection_qty",
    "efficiency_rate",
    "data_source",
    "external_sync_key",
    "remarks",
]"""

t = re.sub(r"INSERT_COLUMNS = \[.*?\]", insert, t, count=1, flags=re.S)

tuple_fn = """def _row_to_insert_tuple(row: ParsedPlatingIndicatorRow) -> tuple:
    return (
        row.fiscal_year,
        row.production_month,
        row.production_day,
        row.source_line,
        row.source_file,
        row.planned_quantity,
        row.actual_quantity,
        row.defect_quantity,
        row.defect_plating_scratch,
        row.defect_moya_kaburi,
        row.defect_nickel,
        row.defect_contact,
        row.defect_other,
        row.shift_hours,
        row.maintenance_hours,
        row.trouble_hours,
        row.choco_stop_hours,
        row.planned_stop_hours,
        row.available_work_hours,
        row.work_hours,
        row.work_rate,
        row.utilization_rate,
        row.total_inspection_qty,
        row.efficiency_rate,
        row.data_source,
        row.external_sync_key,
        row.remarks,
    )"""

t = re.sub(
    r"def _row_to_insert_tuple\(row: ParsedPlatingIndicatorRow\) -> tuple:.*?return \(\n        row\.fiscal_year,.*?\n    \)",
    tuple_fn,
    t,
    count=1,
    flags=re.S,
)

t = t.replace("forming_production_indicator", "plating_production_indicator")
t = t.replace("メッキ生産管理指標のデータシート（日付/ライン/品名/生産数 ヘッダ）", "メッキ生産管理指標のデータシート（日付/計画数/実績数 ヘッダ）")

p.write_text(t, encoding="utf-8")
print("patched plating import")
