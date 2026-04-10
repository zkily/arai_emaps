/**
 * 材料管理 API（/api/material/* 与后端 material 模块对应）
 */
import request from '@/shared/api/request'
import type { MaterialInspectionMaster, MaterialLogItem, StockMaterialItem, ProductMaterialAssociationItem } from '@/types/material'

const PREFIX = '/api/material'

// ─────────────────────────────────────────────
// 検品基準マスタ (inspection-master)
// ─────────────────────────────────────────────

export interface InspectionListParams {
  keyword?: string
  page?: number
  pageSize?: number
}

export interface InspectionListResponse {
  success?: boolean
  data?: { list: MaterialInspectionMaster[]; total: number }
}

export function getMaterialInspectionList(
  params?: InspectionListParams
): Promise<InspectionListResponse> {
  return request.get(`${PREFIX}/inspection-master`, { params }) as Promise<InspectionListResponse>
}

export function createMaterialInspection(data: {
  inspection_cd: string
  inspection_standard: string
}): Promise<{ success?: boolean; data?: MaterialInspectionMaster }> {
  return request.post(`${PREFIX}/inspection-master`, data) as Promise<{
    success?: boolean
    data?: MaterialInspectionMaster
  }>
}

export function updateMaterialInspection(
  id: number,
  data: { inspection_cd?: string; inspection_standard?: string }
): Promise<{ success?: boolean; data?: MaterialInspectionMaster }> {
  return request.put(`${PREFIX}/inspection-master/${id}`, data) as Promise<{
    success?: boolean
    data?: MaterialInspectionMaster
  }>
}

export function deleteMaterialInspection(id: number): Promise<{ success?: boolean }> {
  return request.delete(`${PREFIX}/inspection-master/${id}`) as Promise<{ success?: boolean }>
}

export function batchDeleteMaterialInspections(ids: number[]): Promise<{ success?: boolean; deleted?: number }> {
  return request.delete(`${PREFIX}/inspection-master/batch`, { data: ids }) as Promise<{
    success?: boolean
    deleted?: number
  }>
}

// ─────────────────────────────────────────────
// 受入ログ (receiving)
// ─────────────────────────────────────────────

export interface ReceivingListParams {
  page?: number
  pageSize?: number
  keyword?: string
  /** material_logs.material_name 完全一致 */
  materialNameExact?: string
  material_cd?: string
  supplier?: string
  startDate?: string
  endDate?: string
  /** material_cutting_logs と製造番号突合し used_in_cutting を返す */
  includeCuttingUsage?: boolean
}

export function getMaterialLogs(params?: ReceivingListParams): Promise<{
  success?: boolean
  data?: { list: MaterialLogItem[]; total: number }
}> {
  return request.get(`${PREFIX}/receiving`, { params }) as Promise<{
    success?: boolean
    data?: { list: MaterialLogItem[]; total: number }
  }>
}

export function getReceivingLogById(id: number): Promise<{ success?: boolean; data?: MaterialLogItem }> {
  return request.get(`${PREFIX}/receiving/${id}`) as Promise<{
    success?: boolean
    data?: MaterialLogItem
  }>
}

/** 创建受入ログ（材料入出库时调用） */
export function createMaterialLog(data: Partial<MaterialLogItem>): Promise<{ success?: boolean; data?: MaterialLogItem }> {
  const now = new Date()
  const log_date = (data.log_date as string) || now.toISOString().slice(0, 10)
  const log_time = (data.log_time as string) || now.toTimeString().slice(0, 8)
  const body = {
    item: data.item ?? '材料受入',
    material_cd: data.material_cd ?? '',
    material_name: data.material_name ?? '',
    process_cd: data.process_cd ?? 'KT19',
    log_date,
    log_time,
    hd_no: data.hd_no,
    pieces_per_bundle: data.pieces_per_bundle,
    quantity: data.quantity,
    bundle_quantity: data.bundle_quantity,
    manufacture_no: data.manufacture_no,
    manufacture_date: data.manufacture_date,
    length: data.length,
    outer_diameter1: data.outer_diameter1,
    outer_diameter2: data.outer_diameter2,
    magnetic: data.magnetic,
    appearance: data.appearance,
    supplier: data.supplier,
    material_quality: data.material_quality,
    remarks: data.remarks,
    note: data.note,
  }
  return request.post(`${PREFIX}/receiving`, body) as Promise<{
    success?: boolean
    data?: MaterialLogItem
  }>
}

export function updateMaterialLog(
  id: number,
  data: Partial<MaterialLogItem>
): Promise<{ success?: boolean; data?: MaterialLogItem; material_cutting_log_id?: number }> {
  return request.put(`${PREFIX}/receiving/${id}`, data) as Promise<{
    success?: boolean
    data?: MaterialLogItem
    material_cutting_log_id?: number
  }>
}

export function deleteMaterialLog(id: number): Promise<{ success?: boolean }> {
  return request.delete(`${PREFIX}/receiving/${id}`) as Promise<{ success?: boolean }>
}

export function getReceivingSuppliers(): Promise<{ success?: boolean; data?: string[] }> {
  return request.get(`${PREFIX}/receiving/suppliers`) as Promise<{
    success?: boolean
    data?: string[]
  }>
}

export function importMaterialLogsFromCSV(
  rows: Partial<MaterialLogItem>[]
): Promise<{ success?: boolean; created?: number }> {
  return request.post(`${PREFIX}/receiving/import-csv`, rows) as Promise<{
    success?: boolean
    created?: number
  }>
}

/** 仕入先一覧（material_logs.supplier 去重・按名称排序。返回仕入先名称数组，用于下拉 label/value 均为 supplier_name） */
export function getSupplierList(): Promise<{ success?: boolean; data?: string[] }> {
  return request.get(`${PREFIX}/receiving/suppliers`) as Promise<{
    success?: boolean
    data?: string[]
  }>
}

/** 仕入先名一覧（material_stock.supplier_name 去重・排序。材料在庫画面のフィルタ用） */
export function getMaterialStockSupplierNames(): Promise<{ success?: boolean; data?: string[] }> {
  return request.get(`${PREFIX}/stock/supplier-names`) as Promise<{
    success?: boolean
    data?: string[]
  }>
}

// ─────────────────────────────────────────────
// 材料在庫 (stock) / 在庫材料 (stock-materials)
// ─────────────────────────────────────────────

export function getMaterialStockList(params?: {
  page?: number
  pageSize?: number
  keyword?: string
  material_cd?: string
  supplier_cd?: string
  /** 仕入先名称のカンマ区切り。material_stock.supplier_name で IN 検索 */
  suppliers?: string
  target_date?: string
  start_date?: string
  end_date?: string
  /** true: 注文数>0 の行のみ（材料注文履歴） */
  order_only?: boolean
}): Promise<{ success?: boolean; data?: { list: unknown[]; total: number } }> {
  return request.get(`${PREFIX}/stock`, { params }) as Promise<{
    success?: boolean
    data?: { list: unknown[]; total: number }
  }>
}

export function updateMaterialStock(
  id: number,
  body: Record<string, unknown>
): Promise<{ success?: boolean; data?: unknown }> {
  return request.put(`${PREFIX}/stock/${id}`, body) as Promise<{
    success?: boolean
    data?: unknown
  }>
}

export function getMaterialStockSubList(params?: {
  page?: number
  pageSize?: number
  keyword?: string
  /** 仕入先名称のカンマ区切り。material_stock_sub.supplier_name で IN 検索 */
  suppliers?: string
  target_date?: string
}): Promise<{ success?: boolean; data?: { list: unknown[]; total: number } }> {
  return request.get(`${PREFIX}/stock/sub`, { params }) as Promise<{
    success?: boolean
    data?: { list: unknown[]; total: number }
  }>
}

export function updateMaterialStockSub(
  id: number,
  body: Record<string, unknown>
): Promise<{ success?: boolean; data?: unknown }> {
  return request.put(`${PREFIX}/stock/sub/${id}`, body) as Promise<{
    success?: boolean
    data?: unknown
  }>
}

export function deleteMaterialStockSub(id: number): Promise<{ success?: boolean }> {
  return request.delete(`${PREFIX}/stock/sub/${id}`) as Promise<{ success?: boolean }>
}

/** 主表在庫を半端（material_stock_sub）へ転送 */
export function transferMaterialStockToSub(
  stockId: number,
  quantity: number = 1
): Promise<{ success?: boolean; data?: unknown }> {
  return request.post(`${PREFIX}/stock/transfer-to-sub`, {
    stock_id: stockId,
    quantity,
  }) as Promise<{ success?: boolean; data?: unknown }>
}

/** 手動注文登録：material_stock_sub 新規作成 */
export function createMaterialStockSub(body: {
  material_cd: string
  material_name: string
  date: string
  current_stock?: number
  safety_stock?: number
  max_stock?: number
  unit?: string
  unit_price?: number
  supplier_cd?: string
  supplier_name?: string
  lead_time?: number
  planned_usage?: number
  order_quantity?: number
  order_bundle_quantity?: number
  bundle_weight?: number
  order_amount?: number
  standard_spec?: string
  pieces_per_bundle?: number
  long_weight?: number
  remarks?: string
  label_color?: string
}): Promise<{ success?: boolean; data?: unknown }> {
  return request.post(`${PREFIX}/stock/sub`, body) as Promise<{
    success?: boolean
    data?: unknown
  }>
}

export function getStockMaterialsList(params?: {
  page?: number
  pageSize?: number
  keyword?: string
  /** 材料名完全一致（日別在庫からの詳細ダイアログ用） */
  materialNameExact?: string
  supplier?: string
  is_used?: string
  startDate?: string
  endDate?: string
  sortBy?: string
  sortOrder?: string
}): Promise<{ success?: boolean; data?: { list: StockMaterialItem[]; total: number } }> {
  return request.get(`${PREFIX}/stock-materials`, { params }) as Promise<{
    success?: boolean
    data?: { list: StockMaterialItem[]; total: number }
  }>
}

export function getStockMaterialsSummary(): Promise<{
  success?: boolean
  data?: { total: number; unused: number; used: number; total_quantity: number }
}> {
  return request.get(`${PREFIX}/stock-materials/summary`) as Promise<{
    success?: boolean
    data?: { total: number; unused: number; used: number; total_quantity: number }
  }>
}

export function toggleStockMaterialUsage(id: number): Promise<{ success?: boolean; data?: StockMaterialItem }> {
  return request.patch(`${PREFIX}/stock-materials/${id}/toggle`) as Promise<{
    success?: boolean
    data?: StockMaterialItem
  }>
}

/** 材料マスタ更新: materials → material_stock へ同期（オプションで期間指定） */
export function syncMaterialStockFromMaster(params?: {
  start_date?: string
  end_date?: string
}): Promise<{ success?: boolean; data?: { updated_count: number } }> {
  return request.post(`${PREFIX}/stock/sync-material-master`, params) as Promise<{
    success?: boolean
    data?: { updated_count: number }
  }>
}

// ─────────────────────────────────────────────
// 内示 (forecast) - order_monthly + products + materials + suppliers
// ─────────────────────────────────────────────

/** 製品別明细（list） */
export function getForecastList(params: {
  target_year: number
  target_month: number
  page?: number
  pageSize?: number
  supplier_cd?: string
  keyword?: string
}): Promise<{ success?: boolean; data?: { list: unknown[]; total: number } }> {
  return request.get(`${PREFIX}/forecast/list`, { params }) as Promise<{
    success?: boolean
    data?: { list: unknown[]; total: number }
  }>
}

/** 按 supplier+material 分组汇总（summary） */
export function getForecastSummary(params: {
  target_year: number
  target_month: number
  supplier_cd?: string
  keyword?: string
}): Promise<{ success?: boolean; data?: unknown[] }> {
  return request.get(`${PREFIX}/forecast/summary`, { params }) as Promise<{
    success?: boolean
    data?: unknown[]
  }>
}

/** 统计：製品種類数、材料種類数、仕入先数、内示合計、材料必要数合計（stats） */
export function getForecastStats(params?: {
  target_year?: number
  target_month?: number
  supplier_cd?: string
  keyword?: string
}): Promise<{
  success?: boolean
  data?: {
    total_products: number
    total_materials: number
    total_suppliers: number
    total_forecast_units: number
    total_material_required: number
  }
}> {
  return request.get(`${PREFIX}/forecast/stats`, { params }) as Promise<{
    success?: boolean
    data?: {
      total_products: number
      total_materials: number
      total_suppliers: number
      total_forecast_units: number
      total_material_required: number
    }
  }>
}

/** 筛选用仕入先列表（forecast/suppliers） */
export function getForecastSuppliers(params?: {
  target_year?: number
  target_month?: number
}): Promise<{ success?: boolean; data?: { supplier_cd: string; supplier_name: string }[] }> {
  return request.get(`${PREFIX}/forecast/suppliers`, { params }) as Promise<{
    success?: boolean
    data?: { supplier_cd: string; supplier_name: string }[]
  }>
}

/** 丸一注文書（画像PDF）を社内共有フォルダへ保存（multipart: file） */
export function saveMaruichiOrderPdf(
  blob: Blob,
  filename: string,
): Promise<{ success?: boolean; message?: string; path?: string; detail?: string }> {
  const form = new FormData()
  form.append('file', blob, filename)
  return request.post(`${PREFIX}/stock/maruichi-order-pdf`, form, {
    timeout: 120000,
  }) as Promise<{ success?: boolean; message?: string; path?: string; detail?: string }>
}

// ─────────────────────────────────────────────
// 製品ー材料照会 (product-material-association)
// ─────────────────────────────────────────────

export interface ProductMaterialAssociationParams {
  page?: number
  pageSize?: number
  keyword?: string
  product_cd?: string
  management_code?: string
  material_name?: string
  process_type?: string
  status?: string
  startDate?: string
  endDate?: string
}

export function getProductMaterialAssociation(
  params?: ProductMaterialAssociationParams,
): Promise<{
  success?: boolean
  data?: { list: ProductMaterialAssociationItem[]; total: number }
}> {
  return request.get(`${PREFIX}/product-material-association`, { params }) as Promise<{
    success?: boolean
    data?: { list: ProductMaterialAssociationItem[]; total: number }
  }>
}

export function getProductMaterialProducts(): Promise<{
  success?: boolean
  data?: { product_cd: string; product_name?: string }[]
}> {
  return request.get(`${PREFIX}/product-material-association/products`) as Promise<{
    success?: boolean
    data?: { product_cd: string; product_name?: string }[]
  }>
}

// ─────────────────────────────────────────────
// 切断 materialCutting.csv 取込 (cutting)
// ─────────────────────────────────────────────

export interface MaterialCuttingLogItem {
  id: number
  item?: string | null
  log_date?: string | null
  log_time?: string | null
  hd_no?: string | null
  operator_name?: string | null
  material_cd?: string | null
  /** トリガーで material_cd から算出（荒井/N 接頭辞ルール） */
  manufacture_no?: string | null
  management_code?: string | null
  raw_line?: string | null
  source_file?: string | null
  created_at?: string | null
}

export interface MaterialCuttingLogsParams {
  page?: number
  pageSize?: number
  keyword?: string
  startDate?: string
  endDate?: string
}

export interface MaterialCuttingCsvStatus {
  exists: boolean
  path: string
  mtime_ms: number | null
  size: number | null
  /** mtime_ms:size — 更新検知用 */
  signature: string | null
}

export interface ImportMaterialCuttingCsvParams {
  /** true: TRUNCATE 後に全行取込（最速・CSVに無い行も消える） */
  full_replace?: boolean
  /** この日数より古い log_date を先に削除。0 で無視。full_replace 時は無効 */
  retain_days?: number
}

export interface ImportMaterialCuttingCsvResult {
  success?: boolean
  imported?: number
  errors_count?: number
  errors?: string[]
  full_replace?: boolean
  deleted_prune?: number
  deleted_window?: number
  retain_days?: number
  csv_date_min?: string | null
  csv_date_max?: string | null
  skipped_before_retention?: number
}

export function getMaterialCuttingCsvStatus(): Promise<{
  success?: boolean
  data?: MaterialCuttingCsvStatus
}> {
  return request.get(`${PREFIX}/cutting/csv-status`) as Promise<{
    success?: boolean
    data?: MaterialCuttingCsvStatus
  }>
}

export function importMaterialCuttingCsv(
  params?: ImportMaterialCuttingCsvParams,
): Promise<ImportMaterialCuttingCsvResult> {
  const q: Record<string, boolean | number> = {}
  if (params?.full_replace === true) q.full_replace = true
  if (params?.retain_days !== undefined && params.retain_days !== null) {
    q.retain_days = params.retain_days
  }
  return request.post(`${PREFIX}/cutting/import-csv`, undefined, {
    params: Object.keys(q).length ? q : undefined,
  }) as Promise<ImportMaterialCuttingCsvResult>
}

export function getMaterialCuttingLogs(
  params?: MaterialCuttingLogsParams,
): Promise<{
  success?: boolean
  data?: { list: MaterialCuttingLogItem[]; total: number }
}> {
  return request.get(`${PREFIX}/cutting/logs`, { params }) as Promise<{
    success?: boolean
    data?: { list: MaterialCuttingLogItem[]; total: number }
  }>
}

// ─────────────────────────────────────────────
// 材料使用済 material_usage_record
// ─────────────────────────────────────────────

export interface MaterialUsageRecordItem {
  id: number
  usage_date: string | null
  material_cd: string
  material_name: string
  usage_count: number | string
  source: string
  management_codes?: string | null
  management_code?: string | null
  reflected: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface MaterialUsageRecordsParams {
  usage_date?: string
  date_from?: string
  date_to?: string
  material_cd?: string
  material_keyword?: string
  source?: string
  reflected?: boolean
  page?: number
  page_size?: number
}

export function getMaterialUsageRecords(params?: MaterialUsageRecordsParams): Promise<{
  success?: boolean
  data?: { list: MaterialUsageRecordItem[]; total: number }
}> {
  return request.get(`${PREFIX}/usage/records`, { params }) as Promise<{
    success?: boolean
    data?: { list: MaterialUsageRecordItem[]; total: number }
  }>
}

export function getMaterialUsageRecordsChartSummary(params?: {
  usage_date?: string
  date_from?: string
  date_to?: string
  material_cd?: string
  material_keyword?: string
  source?: string
  reflected?: boolean
  material_top_n?: number
}): Promise<{
  success?: boolean
  data?: {
    by_date: Array<{ usage_date: string | null; total: number }>
    by_material: Array<{ material_cd: string; material_name: string; total: number }>
  }
}> {
  return request.get(`${PREFIX}/usage/records/chart-summary`, { params }) as Promise<{
    success?: boolean
    data?: {
      by_date: Array<{ usage_date: string | null; total: number }>
      by_material: Array<{ material_cd: string; material_name: string; total: number }>
    }
  }>
}
