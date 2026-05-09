import request from '@/utils/request'

// ========== Types ==========
export interface SalesOrderQuery {
  order_no?: string
  customer_code?: string
  status?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface QuotationQuery {
  customer_code?: string
  status?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface InvoiceQuery {
  customer_code?: string
  status?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface CreditQuery {
  customer_code?: string
  risk_level?: string
  status?: string
}

export interface ContractPricingQuery {
  customer_code?: string
  product_code?: string
  status?: string
  page?: number
  page_size?: number
}

export interface ForecastQuery {
  customer_code?: string
  product_code?: string
  forecast_month?: string
  status?: string
  page?: number
  page_size?: number
}

export interface ReturnQuery {
  customer_code?: string
  status?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface DailyConfirmedSeriesItem {
  date: string
  confirmed_units: number
}

export interface DailyConfirmedSeries {
  start_date: string
  end_date: string
  as_of_date: string
  items: DailyConfirmedSeriesItem[]
}

/** GET /api/erp/sales/orders/stats */
export interface SalesStats {
  monthly_order_count: number
  monthly_order_amount: number
  monthly_confirmed_units: number
  pending_delivery_count: number
  completed_count: number
  unpaid_amount: number
}

// ========== Sales Orders (受注) ==========
export function getSalesOrders(params: SalesOrderQuery) {
  return request.get('/api/erp/sales/orders', { params })
}

export function getSalesOrderById(id: number) {
  return request.get(`/api/erp/sales/orders/${id}`)
}

export function createSalesOrder(data: any) {
  return request.post('/api/erp/sales/orders', data)
}

export function updateSalesOrder(id: number, data: any) {
  return request.put(`/api/erp/sales/orders/${id}`, data)
}

export function approveSalesOrder(id: number) {
  return request.post(`/api/erp/sales/orders/${id}/approve`)
}

export function cancelSalesOrder(id: number) {
  return request.post(`/api/erp/sales/orders/${id}/cancel`)
}

export function getSalesStats() {
  return request.get('/api/erp/sales/orders/stats')
}

export function getDailyConfirmedSeries(params?: { start_date?: string; end_date?: string }) {
  return request.get('/api/erp/sales/orders/daily-confirmed-series', { params })
}

// ========== Quotations (見積管理) ==========
export function getQuotations(params: QuotationQuery) {
  return request.get('/api/erp/sales/quotations', { params })
}

export function getQuotationById(id: number) {
  return request.get(`/api/erp/sales/quotations/${id}`)
}

export function createQuotation(data: any) {
  return request.post('/api/erp/sales/quotations', data)
}

export function updateQuotation(id: number, data: any) {
  return request.put(`/api/erp/sales/quotations/${id}`, data)
}

export function sendQuotation(id: number) {
  return request.post(`/api/erp/sales/quotations/${id}/send`)
}

export function convertQuotationToOrder(id: number) {
  return request.post(`/api/erp/sales/quotations/${id}/convert-to-order`)
}

export function deleteQuotation(id: number) {
  return request.delete(`/api/erp/sales/quotations/${id}`)
}

// ========== Invoices (請求書) ==========
export function getInvoices(params: InvoiceQuery) {
  return request.get('/api/erp/sales/invoices', { params })
}

export function getInvoiceById(id: number) {
  return request.get(`/api/erp/sales/invoices/${id}`)
}

export function createInvoice(data: any) {
  return request.post('/api/erp/sales/invoices', data)
}

export function issueInvoice(id: number) {
  return request.post(`/api/erp/sales/invoices/${id}/issue`)
}

export function markInvoicePaid(id: number, data?: any) {
  return request.post(`/api/erp/sales/invoices/${id}/mark-paid`, data)
}

export function deleteInvoice(id: number) {
  return request.delete(`/api/erp/sales/invoices/${id}`)
}

// ========== Credit (与信管理) ==========
export function getCredits(params?: CreditQuery) {
  return request.get('/api/erp/sales/credits', { params })
}

export function getCreditByCustomer(customerCode: string) {
  return request.get(`/api/erp/sales/credits/${customerCode}`)
}

export function createOrUpdateCredit(data: any) {
  return request.post('/api/erp/sales/credits', data)
}

export function updateCreditLimit(customerCode: string, data: any) {
  return request.put(`/api/erp/sales/credits/${customerCode}`, data)
}

export function checkCredit(customerCode: string) {
  return request.get(`/api/erp/sales/credits/check/${customerCode}`)
}

// ========== Contract Pricing (契約単価) ==========
export function getContractPricing(params: ContractPricingQuery) {
  return request.get('/api/erp/sales/contract-pricing', { params })
}

export function createContractPricing(data: any) {
  return request.post('/api/erp/sales/contract-pricing', data)
}

export function updateContractPricing(id: number, data: any) {
  return request.put(`/api/erp/sales/contract-pricing/${id}`, data)
}

export function deleteContractPricing(id: number) {
  return request.delete(`/api/erp/sales/contract-pricing/${id}`)
}

export function lookupContractPrice(customerCode: string, productCode: string) {
  return request.get('/api/erp/sales/contract-pricing/lookup', { params: { customer_code: customerCode, product_code: productCode } })
}

// ========== Forecast (内示) ==========
export function getForecasts(params: ForecastQuery) {
  return request.get('/api/erp/sales/forecasts', { params })
}

export function createForecast(data: any) {
  return request.post('/api/erp/sales/forecasts', data)
}

export function updateForecast(id: number, data: any) {
  return request.put(`/api/erp/sales/forecasts/${id}`, data)
}

export function confirmForecast(id: number) {
  return request.post(`/api/erp/sales/forecasts/${id}/confirm`)
}

export function deleteForecast(id: number) {
  return request.delete(`/api/erp/sales/forecasts/${id}`)
}

// ========== Sales Recordings (売上計上) ==========
export function getSalesRecordings(params?: { start_date?: string; end_date?: string; page?: number; page_size?: number }) {
  return request.get('/api/erp/sales/recordings', { params })
}

export function calculateSalesRecordings(data: { month: string }) {
  return request.post('/api/erp/sales/recordings/calculate', data)
}

export function getSalesRecordingSummary(params?: { month?: string }) {
  return request.get('/api/erp/sales/recordings/summary', { params })
}

// ========== Returns (返品管理) ==========
export function getReturns(params: ReturnQuery) {
  return request.get('/api/erp/sales/returns', { params })
}

export function getReturnById(id: number) {
  return request.get(`/api/erp/sales/returns/${id}`)
}

export function createReturn(data: any) {
  return request.post('/api/erp/sales/returns', data)
}

export function updateReturn(id: number, data: any) {
  return request.put(`/api/erp/sales/returns/${id}`, data)
}

export function approveReturn(id: number) {
  return request.post(`/api/erp/sales/returns/${id}/approve`)
}

export function receiveReturn(id: number) {
  return request.post(`/api/erp/sales/returns/${id}/receive`)
}

// ========== Deliveries (出荷) ==========
export function getDeliveries(params?: any) {
  return request.get('/api/erp/sales/deliveries', { params })
}

export function createDelivery(data: any) {
  return request.post('/api/erp/sales/deliveries', data)
}

export function confirmDelivery(id: number) {
  return request.post(`/api/erp/sales/deliveries/${id}/confirm`)
}
