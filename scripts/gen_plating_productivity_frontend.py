# -*- coding: utf-8
"""Generate Plating productivity UI from Chamfering template."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "frontend/src/views/mes/actualAnalysis/productivity"
API = ROOT / "frontend/src/api"

src_vue = (PROD / "ChamferingProductivityAnalysis.vue").read_text(encoding="utf-8")
src_report = (PROD / "chamferingProductivityReport.ts").read_text(encoding="utf-8")
src_api = (API / "chamferingProductionIndicator.ts").read_text(encoding="utf-8")

VUE_REPLS = [
    ("MesChamferingProductivityAnalysis", "MesPlatingProductivityAnalysis"),
    ("ChamferingProductivity", "PlatingProductivity"),
    ("chamferingProductivityReport", "platingProductivityReport"),
    ("@/api/chamferingProductionIndicator", "@/api/platingProductionIndicator"),
    ("fetchChamferingProductivityAnalysis", "fetchPlatingProductivityAnalysis"),
    ("filterChamferingSelectableProducts", "filterPlatingSelectableProducts"),
    ("@/views/mes/shared/chamferingProductFilter", "@/views/mes/shared/platingProductFilter"),
    ("printChamferingProductivity", "printPlatingProductivity"),
    ("loadChamferingLineOptions", "loadPlatingLineOptions"),
    ("@/views/mes/shared/chamferingLineFilter", "@/views/mes/shared/platingLineFilter"),
    ("面取工程 — 生産性分析", "メッキ工程 — 生産性分析"),
    ("Crop", "GoldMedal"),
    ("ChamferingLineOption", "PlatingLineOption"),
    ("ChamferingProductionIndicatorLineOption", "PlatingProductionIndicatorLineOption"),
    ("resolveChamferingMetricsLabel", "resolvePlatingMetricsLabel"),
]

REPORT_REPLS = [
    ("@/api/chamferingProductionIndicator", "@/api/platingProductionIndicator"),
    ("ChamferingProductivity", "PlatingProductivity"),
    ("面取工程", "メッキ工程"),
]

API_REPLS = [
    ("面取生産管理指標 chamfering_production_indicator", "メッキ生産管理指標 plating_production_indicator"),
    ("Chamfering", "Plating"),
    ("chamfering-production-indicator", "plating-production-indicator"),
    ("chamfer_actual_quantity", "actual_quantity"),
    ("chamfer_defect_quantity", "defect_quantity"),
    ("chamfer_planned_quantity", "planned_quantity"),
    ("sw_actual_quantity", ""),
    ("sw_defect_quantity", ""),
    ("sw_planned_quantity", ""),
    ("total_production_qty", "total_inspection_qty"),
]

form_vue = src_vue
for old, new in VUE_REPLS:
    form_vue = form_vue.replace(old, new)

# メッキは日次集計のためライン・品番フィルタを非表示
form_vue = re.sub(
    r'<div class="toolbar-filter toolbar-filter--line">.*?</div>\s*',
    "",
    form_vue,
    count=1,
    flags=re.S,
)
form_vue = re.sub(
    r'<div class="toolbar-filter toolbar-filter--product">.*?</div>\s*',
    "",
    form_vue,
    count=1,
    flags=re.S,
)

form_report = src_report
for old, new in REPORT_REPLS:
    form_report = form_report.replace(old, new)

form_api = src_api
for old, new in API_REPLS:
    if new:
        form_api = form_api.replace(old, new)
    else:
        form_api = form_api.replace(old + "\n", "")
        form_api = form_api.replace(old, "")

(PROD / "PlatingProductivityAnalysis.vue").write_text(form_vue, encoding="utf-8")
(PROD / "platingProductivityReport.ts").write_text(form_report, encoding="utf-8")
(API / "platingProductionIndicator.ts").write_text(form_api, encoding="utf-8")

# minimal filter stubs (メッキは日次集計・フィルタなし)
(API.parent / ".." / "views/mes/shared/platingLineFilter.ts").resolve()
shared = ROOT / "frontend/src/views/mes/shared"
(shared / "platingLineFilter.ts").write_text(
    """export interface PlatingLineOption {
  line_name: string
}

export async function loadPlatingLineOptions(): Promise<PlatingLineOption[]> {
  return [{ line_name: 'メッキ工程' }]
}
""",
    encoding="utf-8",
)
(shared / "platingProductFilter.ts").write_text(
    """export function filterPlatingSelectableProducts<T extends { product_cd?: string | null }>(
  products: T[],
): T[] {
  return products
}
""",
    encoding="utf-8",
)

print("done")
