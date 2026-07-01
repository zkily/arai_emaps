# -*- coding: utf-8 -*-
"""Generate Forming productivity UI from Cutting template."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "frontend/src/views/mes/actualAnalysis/productivity"

src_vue = (PROD / "CuttingProductivityAnalysis.vue").read_text(encoding="utf-8")
src_report = (PROD / "cuttingProductivityReport.ts").read_text(encoding="utf-8")

VUE_REPLS = [
    ("MesCuttingProductivityAnalysis", "MesFormingProductivityAnalysis"),
    ("CuttingProductivity", "FormingProductivity"),
    ("cuttingProductivityReport", "formingProductivityReport"),
    ("@/api/cuttingProductionIndicator", "@/api/formingProductionIndicator"),
    ("fetchCuttingProductivityAnalysis", "fetchFormingProductivityAnalysis"),
    ("filterCuttingSelectableProducts", "filterFormingSelectableProducts"),
    ("@/views/mes/shared/cuttingProductFilter", "@/views/mes/shared/formingProductFilter"),
    ("printCuttingProductivity", "printFormingProductivity"),
    ("loadCuttingLineOptions", "loadFormingLineOptions"),
    ("@/views/mes/shared/cuttingLineFilter", "@/views/mes/shared/formingLineFilter"),
    ("切断工程 — 生産性分析", "成形工程 — 生産性分析"),
    ("差異率", "不良率"),
    ("差異数", "不良数"),
    ("Scissor", "SetUp"),
    ("CuttingLineOption", "FormingLineOption"),
    ("CuttingProductionIndicatorLineOption", "FormingProductionIndicatorLineOption"),
    ("resolveCuttingMetricsLabel", "resolveFormingMetricsLabel"),
]

REPORT_REPLS = [
    ("@/api/cuttingProductionIndicator", "@/api/formingProductionIndicator"),
    ("CuttingProductivity", "FormingProductivity"),
    ("差異率", "不良率"),
]

form_vue = src_vue
for old, new in VUE_REPLS:
    form_vue = form_vue.replace(old, new)

form_report = src_report
for old, new in REPORT_REPLS:
    form_report = form_report.replace(old, new)

(PROD / "FormingProductivityAnalysis.vue").write_text(form_vue, encoding="utf-8")
(PROD / "formingProductivityReport.ts").write_text(form_report, encoding="utf-8")
print("done")
