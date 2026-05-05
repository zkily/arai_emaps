/**
 * 標準原価・月次差異 API
 */
import request from '@/utils/request'

const BASE = '/api/erp/standard-cost'

// --- バージョン ---

export interface CostStandardVersion {
  id: number
  code: string
  fiscal_year: number
  status: string
  effective_from: string
  effective_to?: string | null
  remarks?: string | null
  created_at?: string
  updated_at?: string
}

export function fetchStandardCostVersions(): Promise<CostStandardVersion[]> {
  return request.get(`${BASE}/versions`) as Promise<CostStandardVersion[]>
}

export function createStandardCostVersion(data: {
  code: string
  fiscal_year: number
  status?: string
  effective_from: string
  effective_to?: string | null
  remarks?: string | null
}): Promise<CostStandardVersion> {
  return request.post(`${BASE}/versions`, data)
}

export function updateStandardCostVersion(
  id: number,
  data: Partial<{
    code: string
    fiscal_year: number
    status: string
    effective_from: string
    effective_to: string | null
    remarks: string | null
  }>
): Promise<CostStandardVersion> {
  return request.put(`${BASE}/versions/${id}`, data)
}

export function deleteStandardCostVersion(id: number): Promise<{ ok: boolean }> {
  return request.delete(`${BASE}/versions/${id}`)
}

// --- 製品標準原価 ---

export interface StandardCostListItem {
  id: number
  version_id: number
  product_cd: string
  product_name?: string | null
  material_cost_std: number
  labor_cost_std: number
  overhead_cost_std: number
  total_cost_std: number
  currency: string
  source: string
  remarks?: string | null
  updated_at?: string | null
}

export interface MaterialLine {
  id?: number
  header_id?: number
  line_no: number
  material_cd?: string | null
  material_name?: string | null
  qty_per_unit: number | string
  scrap_pct: number | string
  standard_unit_price: number | string
  amount: number | string
  bom_line_id?: number | null
}

export interface LaborLine {
  id?: number
  header_id?: number
  line_no: number
  process_cd?: string | null
  process_name?: string | null
  std_hours: number | string
  setup_hours: number | string
  labor_rate_per_hour: number | string
  cost_center_cd?: string | null
  amount: number | string
}

export interface OverheadLine {
  id?: number
  header_id?: number
  line_no: number
  cost_center_cd?: string | null
  allocation_basis: string
  basis_qty_per_unit: number | string
  overhead_rate: number | string
  amount: number | string
}

export interface ProductStandardCostDetail extends StandardCostListItem {
  material_lines: MaterialLine[]
  labor_lines: LaborLine[]
  overhead_lines: OverheadLine[]
}

export function fetchProductStandards(params: {
  version_id: number
  product_cd?: string
  page?: number
  page_size?: number
}): Promise<{ items: StandardCostListItem[]; total: number; page: number; page_size: number }> {
  return request.get(`${BASE}/products`, { params }) as Promise<{
    items: StandardCostListItem[]
    total: number
    page: number
    page_size: number
  }>
}

export function getProductStandard(headerId: number): Promise<ProductStandardCostDetail> {
  return request.get(`${BASE}/products/${headerId}`)
}

export function createProductStandard(data: {
  version_id: number
  product_cd: string
  product_name?: string | null
  currency?: string
  source?: string
  remarks?: string | null
  material_lines?: Partial<MaterialLine>[]
  labor_lines?: Partial<LaborLine>[]
  overhead_lines?: Partial<OverheadLine>[]
  material_cost_std?: number | string | null
  labor_cost_std?: number | string | null
  overhead_cost_std?: number | string | null
}): Promise<ProductStandardCostDetail> {
  return request.post(`${BASE}/products`, data)
}

export function updateProductStandard(
  headerId: number,
  data: {
    product_name?: string | null
    currency?: string
    source?: string
    remarks?: string | null
    material_lines?: Partial<MaterialLine>[]
    labor_lines?: Partial<LaborLine>[]
    overhead_lines?: Partial<OverheadLine>[]
    material_cost_std?: number | string | null
    labor_cost_std?: number | string | null
    overhead_cost_std?: number | string | null
  }
): Promise<ProductStandardCostDetail> {
  return request.put(`${BASE}/products/${headerId}`, data)
}

export function deleteProductStandard(headerId: number): Promise<{ ok: boolean }> {
  return request.delete(`${BASE}/products/${headerId}`)
}

// --- 月次 ---

export interface CostAccountingPeriod {
  id: number
  year_month: string
  status: string
  notes?: string | null
  created_at?: string
  updated_at?: string
}

export function fetchCostPeriods(): Promise<CostAccountingPeriod[]> {
  return request.get(`${BASE}/periods`) as Promise<CostAccountingPeriod[]>
}

export function createCostPeriod(data: { year_month: string; notes?: string; status?: string }): Promise<CostAccountingPeriod> {
  return request.post(`${BASE}/periods`, data)
}

export interface CostPeriodProductLine {
  id: number
  period_id: number
  version_id?: number | null
  product_cd: string
  product_name?: string | null
  finished_good_qty: number
  wip_equivalent_qty: number
  actual_material_cost?: number | null
  actual_labor_cost?: number | null
  actual_overhead_cost?: number | null
  standard_material_allowed: number
  standard_labor_allowed: number
  standard_overhead_allowed: number
  variance_material_price: number
  variance_material_qty: number
  variance_labor_rate: number
  variance_labor_efficiency: number
  variance_moh_budget: number
  variance_moh_capacity: number
  variance_moh_efficiency: number
  remarks?: string | null
  updated_at?: string | null
  variance_material_total?: number | null
  variance_labor_total?: number | null
  variance_overhead_total?: number | null
  variance_grand_total?: number | null
}

export function fetchPeriodProducts(periodId: number): Promise<CostPeriodProductLine[]> {
  return request.get(`${BASE}/periods/${periodId}/products`) as Promise<CostPeriodProductLine[]>
}

export function createPeriodProduct(
  periodId: number,
  data: {
    version_id?: number | null
    product_cd: string
    product_name?: string | null
    finished_good_qty?: number | string
    wip_equivalent_qty?: number | string
    actual_material_cost?: number | string | null
    actual_labor_cost?: number | string | null
    actual_overhead_cost?: number | string | null
    variance_material_price?: number | string
    variance_material_qty?: number | string
    variance_labor_rate?: number | string
    variance_labor_efficiency?: number | string
    variance_moh_budget?: number | string
    variance_moh_capacity?: number | string
    variance_moh_efficiency?: number | string
    remarks?: string | null
  }
): Promise<CostPeriodProductLine> {
  return request.post(`${BASE}/periods/${periodId}/products`, data)
}

export function updatePeriodProduct(
  periodId: number,
  lineId: number,
  data: Partial<Parameters<typeof createPeriodProduct>[1]>
): Promise<CostPeriodProductLine> {
  return request.put(`${BASE}/periods/${periodId}/products/${lineId}`, data)
}

export function deletePeriodProduct(periodId: number, lineId: number): Promise<{ ok: boolean }> {
  return request.delete(`${BASE}/periods/${periodId}/products/${lineId}`)
}

export function recalculatePeriodProduct(periodId: number, lineId: number): Promise<CostPeriodProductLine> {
  return request.post(`${BASE}/periods/${periodId}/products/${lineId}/recalculate`)
}
