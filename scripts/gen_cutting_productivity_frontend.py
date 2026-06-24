# -*- coding: utf-8 -*-
"""Generate Cutting productivity UI from Welding template."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "frontend/src/views/mes/actualAnalysis/productivity"

src_vue = (PROD / "WeldingProductivityAnalysis.vue").read_text(encoding="utf-8")
src_report = (PROD / "weldingProductivityReport.ts").read_text(encoding="utf-8")

VUE_REPLS = [
    ("MesWeldingProductivityAnalysis", "MesCuttingProductivityAnalysis"),
    ("WeldingProductivity", "CuttingProductivity"),
    ("weldingProductivityReport", "cuttingProductivityReport"),
    ("@/api/weldingManagement", "@/api/cuttingProductionIndicator"),
    ("fetchWeldingProductivityAnalysis", "fetchCuttingProductivityAnalysis"),
    ("filterWeldingSelectableProducts", "filterCuttingSelectableProducts"),
    ("@/views/mes/shared/weldingProductFilter", "@/views/mes/shared/cuttingProductFilter"),
    ("printWeldingProductivity", "printCuttingProductivity"),
    ("filterOperatorId", "filterLineName"),
    ("operatorOptions", "lineOptions"),
    ("loadOperators", "loadLines"),
    ("fetchWeldingSectionOperators", "loadCuttingLineOptions"),
    ("溶接工程 — 生産性分析", "切断工程 — 生産性分析"),
    ("溶接作業者", "ライン"),
    ("不良率", "差異率"),
    ("不良数", "差異数"),
    ("Connection", "Scissor"),
    ("operatorLabel(u)", "lineLabel(u)"),
    ("function operatorLabel", "function lineLabel"),
    ("type UserListItem", "type CuttingLineOption"),
    ("UserListItem[]", "CuttingLineOption[]"),
    ("import type { UserListItem } from '@/api/system'", "import type { CuttingProductionIndicatorLineOption as CuttingLineOption } from '@/api/cuttingProductionIndicator'"),
    ("from '@/views/mes/shared/weldingOperatorFilter'", "from '@/views/mes/shared/cuttingLineFilter'"),
    ("loadMesDefectItemsForProcess('KT07')", "/* cutting: no defect master */ Promise.resolve([])"),
    ("resolveMesDefectItemLabel", "resolveCuttingMetricsLabel"),
]

REPORT_REPLS = [
    ("@/api/weldingManagement", "@/api/cuttingProductionIndicator"),
    ("WeldingProductivity", "CuttingProductivity"),
    ("operatorLabel", "lineLabel"),
    ("operatorRows", "lineRows"),
    ("operatorSectionAvgEfficiency", "lineSectionAvgEfficiency"),
    ("不良率", "差異率"),
    ("溶接作業者", "ライン"),
    ("operator_name", "operator_name"),
]

cut_vue = src_vue
for old, new in VUE_REPLS:
    cut_vue = cut_vue.replace(old, new)

cut_vue = cut_vue.replace(
    '<el-option v-for="u in lineOptions" :key="u.id" :label="lineLabel(u)" :value="u.id" />',
    '<el-option v-for="u in lineOptions" :key="u.line_name" :label="lineLabel(u)" :value="u.line_name" />',
)
cut_vue = cut_vue.replace("filterLineName = ref<number | ''>('')", "filterLineName = ref<string>('')")

# loadAnalysis API params
cut_vue = cut_vue.replace(
    "mes_operator_user_id: filterLineName.value === '' ? undefined : filterLineName.value,",
    "production_line: filterLineName.value === '' ? undefined : filterLineName.value,",
)

# load lines filter existence check
cut_vue = cut_vue.replace(
    "lineOptions.value.some((u) => u.id === filterLineName.value)",
    "lineOptions.value.some((u) => u.line_name === filterLineName.value)",
)
cut_vue = cut_vue.replace(
    "const found = lineOptions.value.find((u) => u.id === filterLineName.value)",
    "const found = lineOptions.value.find((u) => u.line_name === filterLineName.value)",
)

(PROD / "CuttingProductivityAnalysis.vue").write_text(cut_vue, encoding="utf-8")

cut_report = src_report
for old, new in REPORT_REPLS:
    cut_report = cut_report.replace(old, new)
(PROD / "cuttingProductivityReport.ts").write_text(cut_report, encoding="utf-8")
print("done")
