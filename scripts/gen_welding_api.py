"""Append welding_management MES API block to production_schedule/api.py from inspection block."""
from pathlib import Path

api = Path(__file__).resolve().parents[1] / "backend/app/modules/production_schedule/api.py"
text = api.read_text(encoding="utf-8")

marker = "# ---------- 検査指示（inspection_management）・MES検査実績収集 ----------"
start = text.index(marker)
# end at file end (inspection block is last)
inspection_block = text[start:]

welding = inspection_block
repl = [
    ("inspection_management", "welding_management"),
    ("inspection-management", "welding-management"),
    ("InspectionManagement", "WeldingManagement"),
    ("inspection_id", "welding_id"),
    ("_inspection_", "_welding_"),
    ("_INSPECTION_", "_WELDING_"),
    ("Inspection", "Welding"),
    ("inspection", "welding"),
    ("検査", "溶接"),
    ("検査員", "溶接作業者"),
    ("mes_inspector_user_id", "mes_operator_user_id"),
    ("09_inspection_management", "13_welding_management"),
    ("12_inspection_management_mes_client_instance", "13_welding_management"),
    ("iid", "wid"),
]
for a, b in repl:
    welding = welding.replace(a, b)

# fix double replacements
welding = welding.replace("welding_mgmt_mes_select_fragment", "_welding_mgmt_mes_select_fragment")
welding = welding.replace("_welding_mgmt_mes_select_fragment", "_welding_mgmt_mes_select_fragment")

header = "\n\n# ---------- 溶接指示（welding_management）・MES溶接実績収集 ----------\n"
if "welding-management/list" not in text:
    api.write_text(text + header + welding[len(marker):], encoding="utf-8")
    print("appended welding API")
else:
    print("welding API already present")
