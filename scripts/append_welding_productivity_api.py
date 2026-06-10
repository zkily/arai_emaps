# -*- coding: utf-8 -*-
"""Append single welding productivity-analysis endpoint to api.py (after update_welding_management)."""
from pathlib import Path

API = Path(__file__).resolve().parents[1] / "backend/app/modules/production_schedule/api.py"
text = API.read_text(encoding="utf-8")
if "/plan/welding-management/productivity-analysis" in text:
    print("already present, skip")
    raise SystemExit(0)

start = text.index('@router.get("/plan/inspection-management/productivity-analysis")')
end = text.index("\n\nclass CreateInspectionManagementBody(BaseModel):")
ins_block = text[start:end]

replacements = [
    ("/plan/inspection-management/productivity-analysis", "/plan/welding-management/productivity-analysis"),
    ("get_inspection_productivity_analysis", "get_welding_productivity_analysis"),
    ("mes_inspector_user_id: Optional[int] = Query(None, description=\"検査員 users.id\")",
     "mes_operator_user_id: Optional[int] = Query(None, description=\"溶接作業者 users.id\")"),
    ("検査工程生産性分析（inspection_management 集計）", "溶接工程生産性分析（welding_management 集計）"),
    ("_get_inspection_mgmt_columns", "_get_welding_mgmt_columns"),
    ("inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql",
     "welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql"),
    ("_inspection_mgmt_mes_select_fragment(im_cols)", "_welding_mgmt_mes_select_fragment(wm_cols)"),
    ("im_cols = await", "wm_cols = await"),
    ("if not im_cols:", "if not wm_cols:"),
    ("join_inspector", "join_operator"),
    ("inspector_select", "operator_select"),
    ("mes_inspector_name", "mes_operator_name"),
    ("mes_inspector_username", "mes_operator_username"),
    ("inspector_join", "operator_join"),
    ("inspection_management", "welding_management"),
    ("_INSPECTION_MGMT_MES_COLUMNS", "_WELDING_MGMT_MES_COLUMNS"),
    ("_inspection_mes_column_migration_hint", "_welding_mes_column_migration_hint"),
    ("inspector_map", "operator_map"),
    ("inspector_id", "operator_id"),
    ("inspector_key", "operator_key"),
    ("inspector_name", "operator_name"),
    ("product_inspector_map", "product_operator_map"),
    ("inspectors_raw", "operators_raw"),
    ("inspectors_final", "operators_final"),
    ("by_inspector", "by_operator"),
    ("by_product_inspector_ranking", "by_product_operator_ranking"),
    ("inspector_user_id", "operator_user_id"),
    ("inspector_count", "operator_count"),
    ("ranked_inspector_count", "ranked_operator_count"),
    ('"inspectors": {}', '"operators": {}'),
    ("top_inspector_name", "top_operator_name"),
    ("inspector_display_name", "operator_display_name"),
    ("mes_inspector_user_id", "mes_operator_user_id"),
    ('product_operator_map[product_key]["inspectors"]', 'product_operator_map[product_key]["operators"]'),
    ('"inspectors": operators_final', '"operators": operators_final'),
]

weld_block = ins_block
for old, new in replacements:
    weld_block = weld_block.replace(old, new)

# conditional welding_machine column
weld_block = weld_block.replace(
    "    mes_frag = _welding_mgmt_mes_select_fragment(wm_cols)\n    join_operator",
    "    mes_frag = _welding_mgmt_mes_select_fragment(wm_cols)\n"
    "    wm_machine_col = (\n"
    '        "welding_management.welding_machine,\\n               "\n'
    '        if "welding_machine" in wm_cols\n'
    "        else \"\"\n"
    "    )\n"
    "    join_operator",
)
weld_block = weld_block.replace(
    "               welding_management.product_name,\n               welding_management.actual_production_quantity,",
    "               welding_management.product_name,\n               {wm_machine_col}welding_management.actual_production_quantity,",
)

API.write_text(text.rstrip() + "\n\n" + weld_block, encoding="utf-8")
print("appended welding productivity endpoint")
