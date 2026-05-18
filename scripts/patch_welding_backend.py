"""Patch production_schedule/api.py with welding_management MES support."""
from pathlib import Path

api_path = Path(__file__).resolve().parents[1] / "backend/app/modules/production_schedule/api.py"
text = api_path.read_text(encoding="utf-8")

if "welding-management/list" in text:
    print("already patched")
    raise SystemExit(0)

WELDING_COLS = '''
_WELDING_MGMT_MES_COLUMNS = (
    "mes_production_started_at",
    "mes_production_ended_at",
    "mes_net_production_sec",
    "mes_paused_accum_sec",
    "mes_production_is_paused",
    "mes_operator_user_id",
    "mes_client_instance_id",
    "mes_defect_by_item",
)
'''

# insert columns after inspection columns
needle = "_INSPECTION_MGMT_MES_COLUMNS = ("
idx = text.index(needle)
end_cols = text.index(")\n", idx) + 2
text = text[:end_cols] + WELDING_COLS + text[end_cols:]

# duplicate inspection helpers -> welding (lines between _get_inspection and _parse_mes_defect)
start_helpers = text.index("async def _get_inspection_mgmt_columns")
end_helpers = text.index("def _parse_mes_defect_by_item_for_db")
helper_src = text[start_helpers:end_helpers]
welding_helpers = helper_src
for a, b in [
    ("_get_inspection_mgmt_columns", "_get_welding_mgmt_columns"),
    ("_inspection_mgmt_mes_select_fragment", "_welding_mgmt_mes_select_fragment"),
    ("_INSPECTION_MGMT_MES_COLUMNS", "_WELDING_MGMT_MES_COLUMNS"),
    ("_inspection_mes_column_migration_hint", "_welding_mes_column_migration_hint"),
    ("inspection_management", "welding_management"),
    ("_inspection_row_mes_in_progress", "_welding_row_mes_in_progress"),
    ("_fetch_inspection_row_mes_state", "_fetch_welding_row_mes_state"),
    ("inspection_id", "welding_id"),
    ("_reject_inspection_mes_client_lock_conflict", "_reject_welding_mes_client_lock_conflict"),
    ("検査生産", "溶接生産"),
    ("_inspection_mes_conflict_label", "_welding_mes_conflict_label"),
    ("_reject_concurrent_mes_production_on_inspection_start", "_reject_concurrent_mes_production_on_welding_start"),
    ("検査 MES", "溶接 MES"),
    ("検査員", "溶接作業者"),
    ("mes_inspector_user_id", "mes_operator_user_id"),
    ("inspector_user_id", "operator_user_id"),
    ("need_inspector_col", "need_operator_col"),
    ("row_inspector", "row_operator"),
    ("effective_inspector", "effective_operator"),
    ("inspector_conflict", "operator_conflict"),
    ("inspector", "operator"),
    ("09_inspection_management", "13_welding_management"),
    ("12_inspection_management_mes_client_instance", "13_welding_management"),
    (":iid", ":wid"),
    ('"iid":', '"wid":'),
]:
    welding_helpers = welding_helpers.replace(a, b)

text = text[:end_helpers] + welding_helpers + text[end_helpers:]

# routes block
route_start = text.index("# ---------- 検査指示（inspection_management）")
route_block = text[route_start:]
welding_routes = route_block
for a, b in [
    ("# ---------- 検査指示（inspection_management）・MES検査実績収集 ----------",
     "# ---------- 溶接指示（welding_management）・MES溶接実績収集 ----------"),
    ("inspection-management", "welding-management"),
    ("inspection_management", "welding_management"),
    ("InspectionManagement", "WeldingManagement"),
    ("inspection_id", "welding_id"),
    ("_get_inspection_mgmt_columns", "_get_welding_mgmt_columns"),
    ("_inspection_mgmt_mes_select_fragment", "_welding_mgmt_mes_select_fragment"),
    ("_inspection_mes_column_migration_hint", "_welding_mes_column_migration_hint"),
    ("_fetch_inspection_row_mes_state", "_fetch_welding_row_mes_state"),
    ("_inspection_row_mes_in_progress", "_welding_row_mes_in_progress"),
    ("_reject_inspection_mes_client_lock_conflict", "_reject_welding_mes_client_lock_conflict"),
    ("_reject_concurrent_mes_production_on_inspection_start", "_reject_concurrent_mes_production_on_welding_start"),
    ("_INSPECTION_MGMT_MES_COLUMNS", "_WELDING_MGMT_MES_COLUMNS"),
    ("mes_inspector_user_id", "mes_operator_user_id"),
    ("検査", "溶接"),
    ("検査員", "溶接作業者"),
    ("09_inspection_management", "13_welding_management"),
    ("12_inspection_management_mes_client_instance", "13_welding_management"),
    ("im_cols", "wm_cols"),
    (":iid", ":wid"),
    ('"iid":', '"wid":'),
    ("get_inspection_management_list", "get_welding_management_list"),
    ("create_inspection_management", "create_welding_management"),
    ("update_inspection_management", "update_welding_management"),
]:
    welding_routes = welding_routes.replace(a, b)

text = text[:route_start] + route_block + "\n\n" + welding_routes[len(route_block.split("\n", 1)[0]) :].lstrip()
# fix: append only transformed routes (skip first line duplicate)
welding_only = route_block
for a, b in [
    ("# ---------- 検査指示（inspection_management）・MES検査実績収集 ----------",
     "# ---------- 溶接指示（welding_management）・MES溶接実績収集 ----------"),
    ("inspection-management", "welding-management"),
    ("inspection_management", "welding_management"),
    ("InspectionManagement", "WeldingManagement"),
    ("inspection_id", "welding_id"),
    ("_get_inspection_mgmt_columns", "_get_welding_mgmt_columns"),
    ("_inspection_mgmt_mes_select_fragment", "_welding_mgmt_mes_select_fragment"),
    ("_inspection_mes_column_migration_hint", "_welding_mes_column_migration_hint"),
    ("_fetch_inspection_row_mes_state", "_fetch_welding_row_mes_state"),
    ("_inspection_row_mes_in_progress", "_welding_row_mes_in_progress"),
    ("_reject_inspection_mes_client_lock_conflict", "_reject_welding_mes_client_lock_conflict"),
    ("_reject_concurrent_mes_production_on_inspection_start", "_reject_concurrent_mes_production_on_welding_start"),
    ("_INSPECTION_MGMT_MES_COLUMNS", "_WELDING_MGMT_MES_COLUMNS"),
    ("mes_inspector_user_id", "mes_operator_user_id"),
    ("検査", "溶接"),
    ("検査員", "溶接作業者"),
    ("09_inspection_management", "13_welding_management"),
    ("12_inspection_management_mes_client_instance", "13_welding_management"),
    ("im_cols", "wm_cols"),
    (":iid", ":wid"),
    ('"iid":', '"wid":'),
    ("get_inspection_management_list", "get_welding_management_list"),
    ("create_inspection_management", "create_welding_management"),
    ("update_inspection_management", "update_welding_management"),
]:
    welding_only = welding_only.replace(a, b)

text = text[:route_start] + route_block + "\n\n" + welding_only

api_path.write_text(text, encoding="utf-8")
print("patched api.py")
