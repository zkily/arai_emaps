# -*- coding: utf-8 -*-
"""Generate welding productivity API block and Vue page from inspection templates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "backend/app/modules/production_schedule/api.py"
INS_VUE = ROOT / "frontend/src/views/mes/actualAnalysis/productivity/InspectionProductivityAnalysis.vue"
WELD_VUE = ROOT / "frontend/src/views/mes/actualAnalysis/productivity/WeldingProductivityAnalysis.vue"
WELD_API_TS = ROOT / "frontend/src/api/weldingManagement.ts"

# --- Backend endpoint ---
api_text = API.read_text(encoding="utf-8")
start = api_text.index("@router.get(\"/plan/inspection-management/productivity-analysis\")")
end = api_text.index("@router.get(\"/plan/inspection-management/utilization-analysis\")")
ins_block = api_text[start:end]

replacements = [
    ("/plan/inspection-management/productivity-analysis", "/plan/welding-management/productivity-analysis"),
    ("get_inspection_productivity_analysis", "get_welding_productivity_analysis"),
    ("mes_inspector_user_id", "mes_operator_user_id"),
    ("検査工程生産性分析（inspection_management 集計）", "溶接工程生産性分析（welding_management 集計）"),
    ("_get_inspection_mgmt_columns", "_get_welding_mgmt_columns"),
    ("inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql", "welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql"),
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
    ("inspectors", "operators"),
    ("top_inspector_name", "top_operator_name"),
    ("inspector_display_name", "operator_display_name"),
    ('"inspectors": {}', '"operators": {}'),
    ("pi_bucket = product_operator_map[product_key][\"operators\"]", 'pi_bucket = product_operator_map[product_key]["operators"]'),
]

weld_block = ins_block
for old, new in replacements:
    weld_block = weld_block.replace(old, new)

# welding_machine column in SELECT
weld_block = weld_block.replace(
    "               welding_management.product_name,\n               welding_management.actual_production_quantity,",
    "               welding_management.product_name,\n               welding_management.welding_machine,\n               welding_management.actual_production_quantity,",
)

marker = '    return {"success": True, "message": "更新しました"}\n'
if marker not in api_text:
    raise SystemExit("api.py marker not found")
if "/plan/welding-management/productivity-analysis" in api_text:
    print("welding productivity API already present, skip api.py")
else:
    api_text = api_text.replace(marker, marker + "\n\n" + weld_block)
    API.write_text(api_text, encoding="utf-8")
    print("wrote welding productivity API")

# --- Frontend Vue ---
vue = INS_VUE.read_text(encoding="utf-8")
vue_replacements = [
    ("MesInspectionProductivityAnalysis", "MesWeldingProductivityAnalysis"),
    ("InspectionProductivityAnalysisData", "WeldingProductivityAnalysisData"),
    ("InspectionProductivityBucket", "WeldingProductivityBucket"),
    ("InspectionProductivityInspectorRow", "WeldingProductivityOperatorRow"),
    ("InspectionProductivityProductInspectorRanking", "WeldingProductivityProductOperatorRanking"),
    ("fetchInspectionProductivityAnalysis", "fetchWeldingProductivityAnalysis"),
    ("@/api/inspectionManagement", "@/api/weldingManagement"),
    ("検査工程 — 生産性分析", "溶接生産性"),
    ("inspection_management 実績", "welding_management 実績"),
    ("DocumentChecked", "Connection"),
    ("検査員", "溶接作業者"),
    ("filterInspectorId", "filterOperatorId"),
    ("inspectorOptions", "operatorOptions"),
    ("inspectorLabel", "operatorLabel"),
    ("loadInspectors", "loadOperators"),
    ("inspectorChartRef", "operatorChartRef"),
    ("inspectorChart", "operatorChart"),
    ("topInspectors", "topOperators"),
    ("podiumInspectors", "podiumOperators"),
    ("by_inspector", "by_operator"),
    ("inspector_name", "operator_name"),
    ("inspector_user_id", "operator_user_id"),
    ("inspector_display_name", "operator_display_name"),
    ("by_product_inspector_ranking", "by_product_operator_ranking"),
    ("top_inspector_name", "top_operator_name"),
    ("ranked_inspector_count", "ranked_operator_count"),
    ("inspector_count", "operator_count"),
    (".inspectors", ".operators"),
    ("buildProductInspectorRankingFromSessions", "buildProductOperatorRankingFromSessions"),
    ("mes_inspector_user_id", "mes_operator_user_id"),
    ("mes_inspector_name", "mes_operator_name"),
    ("mes_inspector_username", "mes_operator_username"),
    ("filterInspectionSelectableProducts", "filterWeldingSelectableProducts"),
    ("@/views/mes/shared/inspectionProductFilter", "@/views/mes/shared/weldingProductFilter"),
    ("KT09", "KT07"),
    ("ipa-field--inspector", "ipa-field--operator"),
    ("ipa-field__inspector-select", "ipa-field__operator-select"),
    ("製品別 · 検査員能率ランキング", "製品別 · 溶接作業者能率ランキング"),
    ("TOP検査員", "TOP作業者"),
    ("能率を算出できる検査員データがありません", "能率を算出できる溶接作業者データがありません"),
]
for old, new in vue_replacements:
    vue = vue.replace(old, new)

WELD_VUE.write_text(vue, encoding="utf-8")
print("wrote WeldingProductivityAnalysis.vue")

# --- weldingProductFilter.ts ---
filter_path = ROOT / "frontend/src/views/mes/shared/weldingProductFilter.ts"
if not filter_path.exists():
    filter_path.write_text(
        """/** 溶接工程向け製品候補（生産性分析） */
import type { Product } from '@/types/master'

export function filterWeldingSelectableProducts(list: Product[]): Product[] {
  return list
    .filter((p) => p.status !== 'inactive')
    .sort((a, b) =>
      (a.product_name ?? '').localeCompare(b.product_name ?? '', 'ja', { sensitivity: 'base' }),
    )
}
""",
        encoding="utf-8",
    )
    print("wrote weldingProductFilter.ts")

# --- weldingManagement.ts API types ---
ts = WELD_API_TS.read_text(encoding="utf-8")
if "fetchWeldingProductivityAnalysis" in ts:
    print("weldingManagement.ts API already present")
else:
    append = '''

export interface WeldingProductivityBucket {
  session_count?: number
  completed_session_count?: number
  sum_actual_qty?: number
  sum_defect_qty?: number
  sum_net_production_sec?: number
  sum_net_production_min?: number
  sum_paused_sec?: number
  sum_paused_min?: number
  defect_rate_percent?: number | null
  efficiency_per_hour?: number | null
}

export interface WeldingProductivityDailyRow extends WeldingProductivityBucket {
  day: string
}

export interface WeldingProductivityOperatorRow extends WeldingProductivityBucket {
  operator_user_id?: number | null
  operator_name?: string
  rank?: number
}

export interface WeldingProductivityProductOperatorRanking {
  product_cd: string
  product_name?: string
  sum_actual_qty?: number
  session_count?: number
  operator_count?: number
  ranked_operator_count?: number
  top_operator_name?: string | null
  top_efficiency_per_hour?: number | null
  operators: WeldingProductivityOperatorRow[]
}

export interface WeldingProductivityProductRow extends WeldingProductivityBucket {
  product_cd?: string
  product_name?: string
}

export interface WeldingProductivityDefectRow {
  defect_cd: string
  qty: number
}

export interface WeldingProductivitySessionRow extends WeldingManagementListRow {
  net_production_sec?: number
  paused_sec?: number
  net_production_min?: number
  paused_min?: number
  efficiency_per_hour?: number | null
  defect_rate_percent?: number | null
  is_completed?: boolean
  operator_display_name?: string
  mes_operator_name?: string | null
  mes_operator_username?: string | null
}

export interface WeldingProductivityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: WeldingProductivityBucket
  daily: WeldingProductivityDailyRow[]
  by_operator: WeldingProductivityOperatorRow[]
  by_product: WeldingProductivityProductRow[]
  by_product_operator_ranking: WeldingProductivityProductOperatorRanking[]
  defect_by_item: WeldingProductivityDefectRow[]
  sessions: WeldingProductivitySessionRow[]
}

export interface WeldingProductivityAnalysisResponse {
  success?: boolean
  data?: WeldingProductivityAnalysisData
  message?: string
}

export function fetchWeldingProductivityAnalysis(params: {
  start_date: string
  end_date: string
  mes_operator_user_id?: number | null
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<WeldingProductivityAnalysisResponse> {
  return request.get('/api/plan/welding-management/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_operator_user_id: params.mes_operator_user_id ?? undefined,
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<WeldingProductivityAnalysisResponse>
}
'''
    WELD_API_TS.write_text(ts.rstrip() + append + "\n", encoding="utf-8")
    print("wrote weldingManagement.ts API")
