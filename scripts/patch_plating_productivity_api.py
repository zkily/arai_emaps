# -*- coding: utf-8
"""Patch plating_productivity_api.py from forming template."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "backend/app/modules/production_schedule/plating_productivity_api.py"
t = p.read_text(encoding="utf-8")

t = t.replace("成形工程", "メッキ工程")
t = t.replace("forming_production_indicator", "plating_production_indicator")
t = t.replace("forming", "plating")
t = t.replace("Forming", "Plating")
t = t.replace("69_forming_production_indicator", "73_plating_production_indicator")

t = re.sub(
    r"PLATING_LINE_METRICS_LOSS_HEADERS = \[.*?\]",
    """PLATING_LINE_METRICS_LOSS_HEADERS = [
    "メンテ時間",
    "トラブル時間",
    "チョコ停",
    "計画停止",
]""",
    t,
    count=1,
    flags=re.S,
)

t = re.sub(
    r"PLATING_LINE_METRICS_LOSS_FIELDS = \[.*?\]",
    """PLATING_LINE_METRICS_LOSS_FIELDS = [
    ("メンテ時間", "maintenance_hours"),
    ("トラブル時間", "trouble_hours"),
    ("チョコ停", "choco_stop_hours"),
    ("計画停止", "planned_stop_hours"),
]""",
    t,
    count=1,
    flags=re.S,
)

# lines endpoint - fixed single line
t = re.sub(
    r'@router\.get\("/plan/plating-production-indicator/lines"\).*?return \{"success": True, "data": \[\{"line_name": name\} for name in lines\]\}',
    '''@router.get("/plan/plating-production-indicator/lines")
    async def get_plating_production_indicator_lines(
        start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
        end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        """メッキ工程は日次集計のため固定ラインを返す（フィルタ互換）"""
        start_d = _parse_date_ymd(start_date)
        end_d = _parse_date_ymd(end_date)
        if start_d is None or end_d is None or start_d > end_d:
            raise HTTPException(status_code=400, detail="日付範囲が不正です。")
        return {"success": True, "data": [{"line_name": "メッキ工程"}]}''',
    t,
    count=1,
    flags=re.S,
)

# productivity-analysis: remove line/product filters, update SQL
t = re.sub(
    r"        line_norm = \(production_line or \"\"\)\.strip\(\)\n        if line_norm:\n            where_parts\.append\(\"production_line = :production_line\"\)\n            params\[\"production_line\"\] = line_norm\n        product_cd_norm = \(product_cd or \"\"\)\.strip\(\)\n        if product_cd_norm:\n            where_parts\.append\(\"product_cd = :product_cd\"\)\n            params\[\"product_cd\"\] = product_cd_norm\n",
    "",
    t,
    count=1,
)

sql_old = r'SELECT id, fiscal_year, production_month, production_day, source_line, source_file,\n                   product_cd, production_line, product_name,\n                   planned_quantity, actual_quantity, defect_quantity,\n                   shift_hours, overtime_hours, setup_hours, repair_hours,\n                   adjustment_hours, break_hours, waiting_repair_hours,\n                   planned_stop_hours, available_work_hours,\n                   work_hours, utilization_rate, work_rate, efficiency_rate,\n                   setup_adjustment_flag, yellow_box_qty, metric_60,\n                   data_source, remarks, created_at, updated_at\n            FROM plating_production_indicator'

sql_new = """SELECT id, fiscal_year, production_month, production_day, source_line, source_file,
                   planned_quantity, actual_quantity, defect_quantity,
                   defect_plating_scratch, defect_moya_kaburi, defect_nickel,
                   defect_contact, defect_other,
                   shift_hours, maintenance_hours, trouble_hours, choco_stop_hours,
                   planned_stop_hours, available_work_hours, work_hours,
                   work_rate, utilization_rate, total_inspection_qty, efficiency_rate,
                   data_source, remarks, created_at, updated_at
            FROM plating_production_indicator"""

t = t.replace(sql_old.replace("\\n", "\n"), sql_new)

# session row building - fixed line name
t = t.replace(
    'line_name = (item.get("production_line") or "").strip() or "—"',
    'line_name = "メッキ工程"',
)
t = t.replace(
    'product_key = (item.get("product_cd") or "").strip() or (\n                (item.get("product_name") or "").strip() or "unknown"\n            )\n            product_name = (item.get("product_name") or "").strip()',
    'product_key = day_key or "daily"\n            product_name = day_key',
)

# line metrics defects
t = t.replace('bucket["defects"]["不良"] = 0', 'bucket["defects"]["不良"] = 0\n    bucket["defects"]["メッキ後キズ"] = 0\n    bucket["defects"]["モヤ/カブリ"] = 0\n    bucket["defects"]["ニッケル"] = 0\n    bucket["defects"]["接触"] = 0\n    bucket["defects"]["メ他"] = 0')

# metrics bucket defect accumulation in loop - find and patch
old_defect_block = """            if defect_qty > 0:
                metrics_bucket["defects"]["不良"] = int(metrics_bucket["defects"].get("不良") or 0) + defect_qty
            for header, field in PLATING_LINE_METRICS_LOSS_FIELDS:"""

new_defect_block = """            if defect_qty > 0:
                metrics_bucket["defects"]["不良"] = int(metrics_bucket["defects"].get("不良") or 0) + defect_qty
            for header, field in (
                ("メッキ後キズ", "defect_plating_scratch"),
                ("モヤ/カブリ", "defect_moya_kaburi"),
                ("ニッケル", "defect_nickel"),
                ("接触", "defect_contact"),
                ("メ他", "defect_other"),
            ):
                d_val = int(item.get(field) or 0)
                if d_val > 0:
                    metrics_bucket["defects"][header] = int(metrics_bucket["defects"].get(header) or 0) + d_val
            for header, field in PLATING_LINE_METRICS_LOSS_FIELDS:"""

t = t.replace(old_defect_block, new_defect_block)

t = t.replace(
    'defect_headers = ["不良", *[h for h, _ in PLATING_LINE_METRICS_LOSS_FIELDS]]',
    'defect_headers = ["不良", "メッキ後キズ", "モヤ/カブリ", "ニッケル", "接触", "メ他", *[h for h, _ in PLATING_LINE_METRICS_LOSS_FIELDS]]',
)

# remove break_hours from metrics (plating has no break_hours)
t = t.replace(
    'metrics_bucket["sum_break_sec"] += max(0, int(round(_to_float(item.get("break_hours")) * 3600)))',
    'metrics_bucket["sum_break_sec"] += 0',
)

p.write_text(t, encoding="utf-8")
print("patched plating productivity api")
