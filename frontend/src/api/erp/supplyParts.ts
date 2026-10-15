import request from '@/utils/request'

const BASE_URL = '/api/erp/supply-parts'

export interface SupplyPartStock {
  id: number
  product_cd: string
  product_name: string
  product_alias?: string | null
  part_number?: string | null
  destination_cd?: string | null
  destination_name?: string | null
  storage_location: string
  shelf_no?: string | null
  keeper?: string | null
  on_hand_qty: number
  next_production_date?: string | null
  next_production_qty: number
  quality_status: string
  note?: string | null
  source: 'transfer' | 'manual' | string
  migration_trigger?: 'mass_end' | 'customer_spec' | string | null
  migration_reason?: string | null
  initial_registered_date?: string | null
  shipment_planned: number
  forecast_units: number
  balance: number
  short_of_shipment: boolean
  updated_at?: string | null
  last_out_date?: string | null
  last_in_date?: string | null
  idle_days?: number | null
  idle_months?: number | null
  avg_monthly_demand?: number
  stagnant?: boolean
}

export interface SupplyPartListResponse {
  year: number
  month: number
  list: SupplyPartStock[]
  summary: {
    count: number
    on_hand_total: number
    shipment_total: number
    alert_count: number
    stagnant_count: number
    quality_issue_count: number
  }
  stagnant_days: number
  demand_months: number
  quality_statuses?: string[]
}

export interface SupplyPartTrendPoint {
  month: string
  in_qty: number
  out_qty: number
  end_balance: number
  order_qty: number
}

export interface SupplyPartProductOption {
  product_cd: string
  product_name: string
  product_alias?: string | null
  part_number?: string | null
  product_type?: string | null
  destination_cd?: string | null
  destination_name?: string | null
}

export interface SupplyPartWarehouseLine {
  route_cd: string
  date: string | null
  warehouse_inventory: number
}

export interface SupplyPartTransferPreview {
  product_cd: string
  product_name: string
  product_alias?: string | null
  part_number?: string | null
  product_type?: string | null
  destination_cd?: string | null
  destination_name?: string | null
  already_registered: boolean
  lines: SupplyPartWarehouseLine[]
  raw_warehouse_qty: number
  transfer_qty: number
  warning?: string | null
}

export interface SupplyPartCardForm {
  product_name?: string
  product_alias?: string | null
  part_number?: string | null
  destination_cd?: string | null
  destination_name?: string | null
  storage_location: string
  shelf_no?: string | null
  keeper?: string | null
  quality_status: string
  initial_registered_date: string
  note?: string | null
}

export interface SupplyPartManualForm extends SupplyPartCardForm {
  product_cd: string
  product_name: string
  opening_qty: number
  auto_product_cd?: boolean
}

export interface SupplyPartTransferForm extends SupplyPartCardForm {
  product_cd: string
  migration_trigger: 'mass_end' | 'customer_spec'
  migration_reason: string
}

export interface SupplyPartTransaction {
  id: number
  stock_id: number
  product_cd: string
  txn_type: string
  quantity: number
  balance_after: number
  occurred_date: string | null
  note?: string | null
  created_at?: string | null
}

export interface SupplyPartOrderLine {
  id: number
  order_id?: string | null
  destination_cd?: string | null
  destination_name?: string | null
  forecast_units: number
  forecast_total_units: number
}

export interface SupplyPartDetail {
  stock: SupplyPartStock
  year: number
  month: number
  transactions: SupplyPartTransaction[]
  orders: SupplyPartOrderLine[]
}

export interface SupplyPartTransferResult {
  stock: SupplyPartStock
  raw_warehouse_qty: number
  transfer_qty: number
  stock_log_id: number | null
  warning?: string | null
}

export interface SupplyPartLocation {
  id: number
  name: string
  sort_order: number
  is_active: boolean
  note?: string | null
  usage_count: number
}

export interface SupplyPartLocationForm {
  name: string
  sort_order: number
  is_active: boolean
  note?: string | null
}

export function getSupplyPartLocations(includeInactive = false) {
  return request.get<{ list: SupplyPartLocation[] }>(`${BASE_URL}/locations`, {
    params: { include_inactive: includeInactive },
  })
}

export function createSupplyPartLocation(data: SupplyPartLocationForm) {
  return request.post<SupplyPartLocation>(`${BASE_URL}/locations`, data)
}

export function updateSupplyPartLocation(id: number, data: SupplyPartLocationForm) {
  return request.put<SupplyPartLocation & { renamed_stocks: number }>(
    `${BASE_URL}/locations/${id}`,
    data
  )
}

export function deleteSupplyPartLocation(id: number) {
  return request.delete<{ deleted: boolean }>(`${BASE_URL}/locations/${id}`)
}

export function swapSupplyPartLocations(locationIdA: number, locationIdB: number) {
  return request.post<{
    location_a: SupplyPartLocation
    location_b: SupplyPartLocation
    moved_a_to_b: number
    moved_b_to_a: number
  }>(`${BASE_URL}/locations/swap`, {
    location_id_a: locationIdA,
    location_id_b: locationIdB,
  })
}

export function getSupplyPartList(params: {
  year: number
  month: number
  keyword?: string
  alert_only?: boolean
  storage_location?: string
  destination_cd?: string
  stagnant_only?: boolean
}) {
  return request.get<SupplyPartListResponse>(BASE_URL, { params })
}

export type SupplyPartShipmentStatus =
  | 'not_shipped'
  | 'partial'
  | 'done'
  | 'shipped'
  | 'over'
  | 'no_plan'
  | string

export interface SupplyPartShipmentPlanned {
  product_cd: string
  product_name: string
  part_number?: string | null
  stock_id: number | null
  on_hand_qty: number | null
  destination_summary: string
  planned_date?: string | null
  planned_date_count?: number
  planned_date_source?: 'order_daily' | null
  is_shipped?: boolean
  planned_qty: number
  actual_qty: number
  diff_qty: number
  status: SupplyPartShipmentStatus
}

export interface SupplyPartShipmentActual {
  id: number
  stock_id: number
  product_cd: string
  product_name: string
  part_number?: string | null
  destination_cd?: string | null
  destination_name?: string | null
  occurred_date: string | null
  quantity: number
  balance_after: number
  note?: string | null
}

export interface SupplyPartShipmentResponse {
  year: number
  month: number
  actual_date_from?: string | null
  actual_date_to?: string | null
  summary: {
    planned_total: number
    actual_total: number
    not_shipped_count: number
    short_count: number
    actual_list_total?: number
    actual_list_count?: number
  }
  planned: SupplyPartShipmentPlanned[]
  actual: SupplyPartShipmentActual[]
}

export function getSupplyPartShipments(params: {
  year: number
  month: number
  keyword?: string
  destination_cd?: string
  actual_date_from?: string
  actual_date_to?: string
}) {
  return request.get<SupplyPartShipmentResponse>(`${BASE_URL}/shipments`, { params })
}

export function updateSupplyPartShipmentPlan(data: {
  year: number
  month: number
  product_cd: string
  is_shipped: boolean
}) {
  return request.put<{
    product_cd: string
    year: number
    month: number
    is_shipped: boolean
    shipment_txn_id?: number | null
    shipped_qty?: number
  }>(`${BASE_URL}/shipments/plan`, data)
}

export function getSupplyPartTrend(id: number, year: number, month: number, months = 12) {
  return request.get<{ stock_id: number; points: SupplyPartTrendPoint[] }>(
    `${BASE_URL}/${id}/trend`,
    { params: { year, month, months } }
  )
}

export function getNextSupplyProductCd() {
  return request.get<{ product_cd: string }>(`${BASE_URL}/next-product-cd`)
}

export function searchSupplyPartProducts(keyword?: string, limit?: number, supplyOnly = false) {
  return request.get<{ list: SupplyPartProductOption[] }>(`${BASE_URL}/products`, {
    params: { keyword: keyword || undefined, limit, supply_only: supplyOnly || undefined },
  })
}

export function previewSupplyPartTransfer(productCd: string) {
  return request.get<SupplyPartTransferPreview>(`${BASE_URL}/transfer-preview`, {
    params: { product_cd: productCd },
  })
}

export function transferSupplyPart(data: SupplyPartTransferForm) {
  return request.post<SupplyPartTransferResult>(`${BASE_URL}/transfer`, data)
}

export function createSupplyPartManual(data: SupplyPartManualForm) {
  return request.post<SupplyPartStock>(BASE_URL, data)
}

export function getSupplyPartDetail(id: number, year: number, month: number) {
  return request.get<SupplyPartDetail>(`${BASE_URL}/${id}`, { params: { year, month } })
}

export function deleteSupplyPart(id: number) {
  return request.delete<{
    deleted: boolean
    product_cd: string
    removed_transactions: number
    removed_stock_logs: number
  }>(`${BASE_URL}/${id}`)
}

export function updateSupplyPart(id: number, data: SupplyPartCardForm) {
  return request.put<SupplyPartStock>(`${BASE_URL}/${id}`, data)
}

export function createSupplyPartTransaction(
  id: number,
  data: { txn_type: string; quantity: number; occurred_date: string; note?: string | null }
) {
  return request.post<{ stock: SupplyPartStock; transaction: SupplyPartTransaction }>(
    `${BASE_URL}/${id}/transactions`,
    data
  )
}
