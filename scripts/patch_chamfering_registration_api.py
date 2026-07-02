# -*- coding: utf-8
"""Patch chamfering_production_indicator_registration_api.py from cutting template."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "backend/app/modules/production_schedule/chamfering_production_indicator_registration_api.py"
t = p.read_text(encoding="utf-8")

t = t.replace("切断工程", "面取工程")
t = t.replace("cutting_production_indicator", "chamfering_production_indicator")
t = t.replace("cut_manual:", "cham_manual:")
t = t.replace("CuttingIndicator", "ChamferingIndicator")
t = t.replace("cutting-production-indicator", "chamfering-production-indicator")
t = t.replace("create_cutting_", "create_chamfering_")
t = t.replace("patch_cutting_", "patch_chamfering_")
t = t.replace("delete_cutting_", "delete_chamfering_")
t = t.replace("list_cutting_", "list_chamfering_")

INSERT = """INSERT_COLUMNS = [
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
    "break_hours",
    "setup_hours",
    "available_work_hours",
    "work_hours",
    "utilization_rate",
    "work_rate",
    "total_production_qty",
    "efficiency_rate",
    "data_source",
    "external_sync_key",
    "remarks",
]"""

old_insert = re.search(r"INSERT_COLUMNS = \[.*?\]", t, re.DOTALL)
if not old_insert:
    raise SystemExit("INSERT_COLUMNS not found")
t = t[: old_insert.start()] + INSERT + t[old_insert.end() :]

compute_old = re.search(
    r"def _compute_metrics\(\n    \*,\n    planned:.*?\n    \}",
    t,
    re.DOTALL,
)
compute_new = '''def _compute_metrics(
    *,
    chamfer_planned: int | None,
    chamfer_actual: int | None,
    chamfer_defect: int | None,
    sw_planned: int | None,
    sw_actual: int | None,
    sw_defect: int | None,
    shift_hours: float | None,
    break_hours: float | None,
    setup_hours: float | None,
) -> dict[str, Any]:
    chamfer_a = int(chamfer_actual or 0)
    sw_a = int(sw_actual or 0)
    total = chamfer_a + sw_a

    shift_h = max(0.0, _to_optional_float(shift_hours) or 0.0)
    break_h = max(0.0, _to_optional_float(break_hours) or 0.0)
    setup_h = max(0.0, _to_optional_float(setup_hours) or 0.0)
    pause_h = break_h + setup_h
    work_h = max(0.0, shift_h - pause_h) if shift_h > 0 else None
    available_h = max(0.0, shift_h - break_h) if shift_h > 0 else None

    efficiency = None
    if total > 0 and work_h and work_h > 0:
        efficiency = round(total / work_h, 2)

    utilization = round(work_h / shift_h, 4) if shift_h > 0 and work_h is not None else None
    work_rate = round(work_h / available_h, 4) if available_h and available_h > 0 and work_h is not None else None

    return {
        "chamfer_planned_quantity": int(chamfer_planned) if chamfer_planned is not None else None,
        "chamfer_actual_quantity": chamfer_a if chamfer_actual is not None else None,
        "chamfer_defect_quantity": int(chamfer_defect) if chamfer_defect is not None else None,
        "sw_planned_quantity": int(sw_planned) if sw_planned is not None else None,
        "sw_actual_quantity": sw_a if sw_actual is not None else None,
        "sw_defect_quantity": int(sw_defect) if sw_defect is not None else None,
        "shift_hours": round(shift_h, 3) if shift_h > 0 else None,
        "break_hours": round(break_h, 3) if break_h > 0 else None,
        "setup_hours": round(setup_h, 3) if setup_h > 0 else None,
        "available_work_hours": round(available_h, 3) if available_h and available_h > 0 else None,
        "work_hours": round(work_h, 3) if work_h and work_h > 0 else None,
        "utilization_rate": utilization,
        "work_rate": work_rate,
        "total_production_qty": total if total > 0 else None,
        "efficiency_rate": efficiency,
    }'''
if not compute_old:
    raise SystemExit("_compute_metrics not found")
t = t[: compute_old.start()] + compute_new + t[compute_old.end() :]

body_old = re.search(
    r"class ChamferingIndicatorManualBody\(BaseModel\):.*?\n\n\nclass ChamferingIndicatorPatchBody",
    t,
    re.DOTALL,
)
body_new = '''class ChamferingIndicatorManualBody(BaseModel):
    production_day: str
    production_line: str
    product_cd: str
    product_name: Optional[str] = None
    chamfer_planned_quantity: Optional[int] = None
    chamfer_actual_quantity: Optional[int] = None
    chamfer_defect_quantity: Optional[int] = None
    sw_planned_quantity: Optional[int] = None
    sw_actual_quantity: Optional[int] = None
    sw_defect_quantity: Optional[int] = None
    shift_hours: Optional[float] = None
    break_hours: Optional[float] = None
    setup_hours: Optional[float] = None
    remarks: Optional[str] = None


class ChamferingIndicatorPatchBody'''
if not body_old:
    raise SystemExit("ManualBody not found")
t = t[: body_old.start()] + body_new + t[body_old.end() :]

t = t.replace(
    """class ChamferingIndicatorPatchBody(ChamferingIndicatorManualBody):
    production_day: Optional[str] = None
    production_line: Optional[str] = None
    product_cd: Optional[str] = None
    actual_quantity: Optional[int] = Field(None, ge=0)""",
    """class ChamferingIndicatorPatchBody(ChamferingIndicatorManualBody):
    production_day: Optional[str] = None
    production_line: Optional[str] = None
    product_cd: Optional[str] = None""",
)

# list SELECT
list_sql = re.search(
    r"sql = f\"\"\"\n            SELECT id, fiscal_year.*?FROM chamfering_production_indicator",
    t,
    re.DOTALL,
)
list_new = '''sql = f"""
            SELECT id, fiscal_year, production_month, production_day, source_line, source_file,
                   product_cd, production_line, product_name,
                   chamfer_planned_quantity, chamfer_actual_quantity, chamfer_defect_quantity,
                   sw_planned_quantity, sw_actual_quantity, sw_defect_quantity,
                   shift_hours, break_hours, setup_hours, repair_hours, adjustment_hours,
                   choco_stop_hours, planned_stop_hours, available_work_hours,
                   work_hours, utilization_rate, work_rate, total_production_qty,
                   efficiency_rate, data_source, external_sync_key, remarks,
                   created_at, updated_at
            FROM chamfering_production_indicator'''
if list_sql:
    t = t[: list_sql.start()] + list_new + t[list_sql.end() :]

# create metrics call
t = t.replace(
    """        metrics = _compute_metrics(
            planned=body.planned_quantity,
            actual=body.actual_quantity,
            variance=body.quantity_variance,
            shift_hours=body.shift_hours,
            break_hours=body.break_hours,
            setup_hours=body.setup_hours,
        )""",
    """        metrics = _compute_metrics(
            chamfer_planned=body.chamfer_planned_quantity,
            chamfer_actual=body.chamfer_actual_quantity,
            chamfer_defect=body.chamfer_defect_quantity,
            sw_planned=body.sw_planned_quantity,
            sw_actual=body.sw_actual_quantity,
            sw_defect=body.sw_defect_quantity,
            shift_hours=body.shift_hours,
            break_hours=body.break_hours,
            setup_hours=body.setup_hours,
        )
        total_qty = int(metrics.get("total_production_qty") or 0)
        if total_qty <= 0:
            raise HTTPException(status_code=400, detail="面取またはSWの生産数を入力してください")""",
)

# patch metrics
patch_old = re.search(
    r"        actual = body\.actual_quantity.*?setup_hours=setup_h,\n        \)",
    t,
    re.DOTALL,
)
patch_new = """        chamfer_actual = (
            body.chamfer_actual_quantity
            if body.chamfer_actual_quantity is not None
            else current.get("chamfer_actual_quantity")
        )
        sw_actual = (
            body.sw_actual_quantity if body.sw_actual_quantity is not None else current.get("sw_actual_quantity")
        )
        chamfer_planned = (
            body.chamfer_planned_quantity
            if body.chamfer_planned_quantity is not None
            else current.get("chamfer_planned_quantity")
        )
        sw_planned = (
            body.sw_planned_quantity if body.sw_planned_quantity is not None else current.get("sw_planned_quantity")
        )
        chamfer_defect = (
            body.chamfer_defect_quantity
            if body.chamfer_defect_quantity is not None
            else current.get("chamfer_defect_quantity")
        )
        sw_defect = (
            body.sw_defect_quantity if body.sw_defect_quantity is not None else current.get("sw_defect_quantity")
        )
        shift_h = body.shift_hours if body.shift_hours is not None else current.get("shift_hours")
        break_h = body.break_hours if body.break_hours is not None else current.get("break_hours")
        setup_h = body.setup_hours if body.setup_hours is not None else current.get("setup_hours")

        metrics = _compute_metrics(
            chamfer_planned=int(chamfer_planned) if chamfer_planned is not None else None,
            chamfer_actual=int(chamfer_actual) if chamfer_actual is not None else None,
            chamfer_defect=int(chamfer_defect) if chamfer_defect is not None else None,
            sw_planned=int(sw_planned) if sw_planned is not None else None,
            sw_actual=int(sw_actual) if sw_actual is not None else None,
            sw_defect=int(sw_defect) if sw_defect is not None else None,
            shift_hours=shift_h,
            break_hours=break_h,
            setup_hours=setup_h,
        )"""
if patch_old:
    t = t[: patch_old.start()] + patch_new + t[patch_old.end() :]

# UPDATE sql
update_old = re.search(
    r"        sql = \"\"\"\n            UPDATE chamfering_production_indicator SET.*?WHERE id = :id\n        \"\"\"",
    t,
    re.DOTALL,
)
update_new = '''        sql = """
            UPDATE chamfering_production_indicator SET
              fiscal_year = :fiscal_year,
              production_month = :production_month,
              production_day = :production_day,
              product_cd = :product_cd,
              production_line = :production_line,
              product_name = :product_name,
              chamfer_planned_quantity = :chamfer_planned_quantity,
              chamfer_actual_quantity = :chamfer_actual_quantity,
              chamfer_defect_quantity = :chamfer_defect_quantity,
              sw_planned_quantity = :sw_planned_quantity,
              sw_actual_quantity = :sw_actual_quantity,
              sw_defect_quantity = :sw_defect_quantity,
              shift_hours = :shift_hours,
              break_hours = :break_hours,
              setup_hours = :setup_hours,
              available_work_hours = :available_work_hours,
              work_hours = :work_hours,
              utilization_rate = :utilization_rate,
              work_rate = :work_rate,
              total_production_qty = :total_production_qty,
              efficiency_rate = :efficiency_rate,
              remarks = :remarks
            WHERE id = :id
        """'''
if update_old:
    t = t[: update_old.start()] + update_new + t[update_old.end() :]

p.write_text(t, encoding="utf-8")
print("patched backend registration api")
