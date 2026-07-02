# -*- coding: utf-8
"""Generate Chamfering productivity UI from Forming template."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "frontend/src/views/mes/actualAnalysis/productivity"

src_vue = (PROD / "FormingProductivityAnalysis.vue").read_text(encoding="utf-8")
src_report = (PROD / "formingProductivityReport.ts").read_text(encoding="utf-8")

VUE_REPLS = [
    ("MesFormingProductivityAnalysis", "MesChamferingProductivityAnalysis"),
    ("FormingProductivity", "ChamferingProductivity"),
    ("formingProductivityReport", "chamferingProductivityReport"),
    ("@/api/formingProductionIndicator", "@/api/chamferingProductionIndicator"),
    ("fetchFormingProductivityAnalysis", "fetchChamferingProductivityAnalysis"),
    ("filterFormingSelectableProducts", "filterChamferingSelectableProducts"),
    ("@/views/mes/shared/formingProductFilter", "@/views/mes/shared/chamferingProductFilter"),
    ("printFormingProductivity", "printChamferingProductivity"),
    ("loadFormingLineOptions", "loadChamferingLineOptions"),
    ("@/views/mes/shared/formingLineFilter", "@/views/mes/shared/chamferingLineFilter"),
    ("成形工程 — 生産性分析", "面取工程 — 生産性分析"),
    ("SetUp", "Crop"),
    ("FormingLineOption", "ChamferingLineOption"),
    ("FormingProductionIndicatorLineOption", "ChamferingProductionIndicatorLineOption"),
    ("resolveFormingMetricsLabel", "resolveChamferingMetricsLabel"),
]

REPORT_REPLS = [
    ("@/api/formingProductionIndicator", "@/api/chamferingProductionIndicator"),
    ("FormingProductivity", "ChamferingProductivity"),
    ("成形工程", "面取工程"),
]

form_vue = src_vue
for old, new in VUE_REPLS:
    form_vue = form_vue.replace(old, new)

form_report = src_report
for old, new in REPORT_REPLS:
    form_report = form_report.replace(old, new)

(PROD / "ChamferingProductivityAnalysis.vue").write_text(form_vue, encoding="utf-8")
(PROD / "chamferingProductivityReport.ts").write_text(form_report, encoding="utf-8")
print("done")
