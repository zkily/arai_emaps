/**
 * 外注管理API（メッキ・溶接注文/受入/支給材料/在庫）
 * バックエンド /api/outsourcing を利用
 */
import request from '@/utils/request'

const BASE = '/api/outsourcing'

export interface OutsourcingSupplier {
  id: number
  supplier_cd: string
  supplier_name: string
  supplier_type: string
  /** 納期计算用：注文日 + lead_time_days 工作日 */
  lead_time_days?: number
  is_active?: boolean
  [key: string]: unknown
}

// ========== 外注先マスタ ==========
export function getSuppliers(params?: { type?: string; isActive?: boolean }) {
  return request.get<{ success?: boolean; data?: OutsourcingSupplier[] }>(`${BASE}/suppliers`, { params })
}

export function createSupplier(data: Partial<OutsourcingSupplier>) {
  return request.post<{ success: boolean; data: OutsourcingSupplier }>(`${BASE}/suppliers`, data)
}

export function updateSupplier(id: number, data: Partial<OutsourcingSupplier>) {
  return request.put<{ success: boolean; data: OutsourcingSupplier }>(`${BASE}/suppliers/${id}`, data)
}

export function deleteSupplier(id: number) {
  return request.delete<{ success: boolean; message?: string }>(`${BASE}/suppliers/${id}`)
}

export interface PlatingLedgerRow {
  id: number
  order_date: string
  supplier_cd: string
  supplier_name: string
  product_cd: string
  product_name: string
  unit_price: number
  lead_time_days: number
  delivery_date: string | null
  order_qty: number
  order_no: string | null
  order_amount: number
  order_sheet_issued_at: string | null
  order_sheet_issued_by: string | null
  receiving_qty: number
  receiving_no: string | null
  defect_qty: number
  disposal_no: string | null
  initial_stock: number
  current_stock: number
}

export interface PlatingLedgerOption {
  supplier_cd: string
  supplier_name: string
  product_cd: string
  product_name: string
}

// request のレスポンスインターセプターは body を返すため、戻り値は body 型で宣言する
export function getPlatingLedgerOptions() {
  return request.get(`${BASE}/plating/ledger/options`) as unknown as Promise<{
    success: boolean
    data: PlatingLedgerOption[]
  }>
}

export function getPlatingLedger(params: {
  startDate: string
  endDate: string
  supplierCd?: string
  productCd?: string
  keyword?: string
  firstDayOnly?: boolean
  /** 数量のある行のみ：order=注文数 / receiving=受入数・不良数 / any=いずれか */
  nonZero?: 'order' | 'receiving' | 'any'
  page?: number
  pageSize?: number
}) {
  return request.get(`${BASE}/plating/ledger`, { params }) as unknown as Promise<{
    success: boolean
    data: PlatingLedgerRow[]
    total: number
  }>
}

export function generatePlatingLedger(startDate: string, endDate: string) {
  return request.post(`${BASE}/plating/ledger/generate`, {
    start_date: startDate,
    end_date: endDate,
  }) as unknown as Promise<{
    success: boolean
    data: { generated_count: number; skipped_count: number }
  }>
}

export function calculatePlatingLedger() {
  return request.post(`${BASE}/plating/ledger/calculate`) as unknown as Promise<{
    success: boolean
    data: { calculated_count: number }
  }>
}

export function refreshPlatingLedgerMaster(data: {
  start_date: string
  end_date: string
  supplier_cd?: string
  product_cd?: string
  include_ordered?: boolean
}) {
  return request.post(`${BASE}/plating/ledger/refresh-master`, data) as unknown as Promise<{
    success: boolean
    data: { updated_count: number; missing_count: number }
  }>
}

export function markPlatingOrderSheetIssued(ids: number[]) {
  return request.post(`${BASE}/plating/ledger/order-sheet/issued`, { ids }) as unknown as Promise<{
    success: boolean
    data: { updated_count: number; rows: PlatingLedgerRow[] }
  }>
}

export function updatePlatingLedger(
  id: number,
  data: Partial<Pick<PlatingLedgerRow, 'order_qty' | 'receiving_qty' | 'defect_qty' | 'initial_stock'>>,
) {
  return request.put(`${BASE}/plating/ledger/${id}`, data) as unknown as Promise<{
    success: boolean
    data: { row: PlatingLedgerRow; affected: PlatingLedgerRow[] }
  }>
}

export function getPlatingLedgerHistory(params: {
  kind: 'order' | 'receiving'
  startDate: string
  endDate: string
  supplierCd?: string
  productCd?: string
}) {
  return request.get(`${BASE}/plating/ledger/history`, { params }) as unknown as Promise<{
    success: boolean
    data: PlatingLedgerRow[]
  }>
}

export interface PlatingStockItem {
  supplier_cd: string
  supplier_name: string
  product_cd: string
  product_name: string
  month_initial: number
  month_order_qty: number
  month_receiving_qty: number
  month_defect_qty: number
  current_stock: number
  last_order_date: string | null
  last_receiving_date: string | null
}

export function getPlatingLedgerStock(params: {
  asOf: string
  supplierCd?: string
  productCd?: string
}) {
  return request.get(`${BASE}/plating/ledger/stock`, { params }) as unknown as Promise<{
    success: boolean
    data: PlatingStockItem[]
  }>
}

export interface PlatingStockTrendItem {
  date: string
  order_qty: number
  receiving_qty: number
  defect_qty: number
  current_stock: number
}

export function getPlatingLedgerStockTrend(params: {
  asOf: string
  supplierCd?: string
  productCd?: string
}) {
  return request.get(`${BASE}/plating/ledger/stock-trend`, { params }) as unknown as Promise<{
    success: boolean
    data: PlatingStockTrendItem[]
  }>
}

export interface PlatingOrderSheetItem extends PlatingLedgerRow {
  delivery_location: string
  category: string
  content: string
}

export function getPlatingLedgerOrderSheet(startDate: string, endDate: string, supplierCd: string) {
  return request.get(`${BASE}/plating/ledger/order-sheet`, {
    params: { orderDate: startDate, endDate, supplierCd },
  }) as unknown as Promise<{
    success: boolean
    data: { supplier_cd: string; supplier_name: string; items: PlatingOrderSheetItem[] }
  }>
}

export type OutsourcingLedgerRow = PlatingLedgerRow

/** 溶接日別台帳。戻り値の形はメッキ台帳と同じ。 */
const weldingLedgerRoot = `${BASE}/welding/ledger`

export function getWeldingLedgerOptions() {
  return request.get(`${weldingLedgerRoot}/options`) as unknown as Promise<{
    success: boolean
    data: PlatingLedgerOption[]
  }>
}

export function getWeldingLedger(params: Parameters<typeof getPlatingLedger>[0]) {
  return request.get(weldingLedgerRoot, { params }) as unknown as Promise<{
    success: boolean
    data: PlatingLedgerRow[]
    total: number
  }>
}

export function generateWeldingLedger(startDate: string, endDate: string) {
  return request.post(`${weldingLedgerRoot}/generate`, {
    start_date: startDate,
    end_date: endDate,
  }) as unknown as Promise<{
    success: boolean
    data: { generated_count: number; skipped_count: number }
  }>
}

export function calculateWeldingLedger() {
  return request.post(`${weldingLedgerRoot}/calculate`) as unknown as Promise<{
    success: boolean
    data: { calculated_count: number }
  }>
}

export function refreshWeldingLedgerMaster(data: Parameters<typeof refreshPlatingLedgerMaster>[0]) {
  return request.post(`${weldingLedgerRoot}/refresh-master`, data) as unknown as Promise<{
    success: boolean
    data: { updated_count: number; missing_count: number }
  }>
}

export function markWeldingOrderSheetIssued(ids: number[]) {
  return request.post(`${weldingLedgerRoot}/order-sheet/issued`, { ids }) as unknown as Promise<{
    success: boolean
    data: { updated_count: number; rows: PlatingLedgerRow[] }
  }>
}

export function updateWeldingLedger(id: number, data: Parameters<typeof updatePlatingLedger>[1]) {
  return request.put(`${weldingLedgerRoot}/${id}`, data) as unknown as Promise<{
    success: boolean
    data: { row: PlatingLedgerRow; affected: PlatingLedgerRow[] }
  }>
}

export function getWeldingLedgerHistory(params: Parameters<typeof getPlatingLedgerHistory>[0]) {
  return request.get(`${weldingLedgerRoot}/history`, { params }) as unknown as Promise<{
    success: boolean
    data: PlatingLedgerRow[]
  }>
}

export function getWeldingLedgerStock(params: Parameters<typeof getPlatingLedgerStock>[0]) {
  return request.get(`${weldingLedgerRoot}/stock`, { params }) as unknown as Promise<{
    success: boolean
    data: PlatingStockItem[]
  }>
}

export function getWeldingLedgerStockTrend(params: Parameters<typeof getPlatingLedgerStockTrend>[0]) {
  return request.get(`${weldingLedgerRoot}/stock-trend`, { params }) as unknown as Promise<{
    success: boolean
    data: PlatingStockTrendItem[]
  }>
}

export function getWeldingLedgerOrderSheet(startDate: string, endDate: string, supplierCd: string) {
  return request.get(`${weldingLedgerRoot}/order-sheet`, {
    params: { orderDate: startDate, endDate, supplierCd },
  }) as unknown as Promise<{
    success: boolean
    data: { supplier_cd: string; supplier_name: string; items: PlatingOrderSheetItem[] }
  }>
}

// ========== 外注工程製品マスタ（一覧・統計・CRUD） ==========
export interface OutsourcingProcessProduct {
  id?: number
  process_type?: string
  process_type_name?: string
  supplier_cd?: string
  supplier_name?: string
  product_cd?: string
  product_name?: string
  specification?: string
  unit_price?: number
  delivery_lead_time?: number
  delivery_location?: string
  category?: string
  content?: string
  remarks?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}

/** 一覧（検索・ページネーション対応） */
export function getProcessProducts(params?: {
  processType?: string
  keyword?: string
  supplierCd?: string
  productCd?: string
  isActive?: string
  page?: number
  pageSize?: number
}) {
  return request.get<{
    success?: boolean
    data?: OutsourcingProcessProduct[]
    pagination?: { page: number; pageSize: number; total: number }
  }>(`${BASE}/process-products`, { params })
}

/** 統計 */
export function getProcessProductStats() {
  return request.get<{
    success?: boolean
    data?: {
      total?: { total_count?: number; active_count?: number; supplier_count?: number }
      byProcessType?: Array<{ process_type: string; total_count: number }>
    }
  }>(`${BASE}/process-products/stats`)
}

/** 工程・外注先で絞り込み（注文画面等） */
export function getProcessProductsByKeys(params: { processType: string; supplierCd: string; isActive?: boolean }) {
  return request.get<{ success?: boolean; data?: OutsourcingProcessProduct[] }>(`${BASE}/process-products/by-keys`, { params })
}

export function createProcessProduct(data: Partial<OutsourcingProcessProduct>) {
  return request.post<{ success: boolean; data: OutsourcingProcessProduct }>(`${BASE}/process-products`, data)
}

export function updateProcessProduct(id: number, data: Partial<OutsourcingProcessProduct>) {
  return request.put<{ success: boolean; data: OutsourcingProcessProduct }>(`${BASE}/process-products/${id}`, data)
}

export function deleteProcessProduct(id: number) {
  return request.delete<{ success: boolean; message?: string }>(`${BASE}/process-products/${id}`)
}

export function toggleProcessProductStatus(id: number) {
  return request.patch<{ success: boolean; data: OutsourcingProcessProduct }>(`${BASE}/process-products/${id}/toggle`)
}

/** 納入先休日（master の納入先休日 API を利用） */
export function getDestinationHolidays(destinationCd?: string) {
  if (!destinationCd || String(destinationCd).trim() === '') {
    return Promise.resolve({ data: [] as { holiday_date?: string; holidayDate?: string }[] })
  }
  return request.get<{ holiday_date?: string; holidayDate?: string }[]>(`/api/master/destinations/holidays/by-destination/${encodeURIComponent(destinationCd)}`)
}
