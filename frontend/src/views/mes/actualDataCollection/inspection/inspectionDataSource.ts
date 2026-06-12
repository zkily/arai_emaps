/** inspection_management.data_source */

export type InspectionDataSource = 'mes' | 'excel' | 'csv'

export function resolveInspectionDataSource(row: {
  data_source?: string | null
  remarks?: string | null
  external_sync_key?: string | null
}): InspectionDataSource {
  const ds = (row.data_source ?? '').trim().toLowerCase()
  if (ds === 'mes' || ds === 'excel' || ds === 'csv') return ds
  const remarks = (row.remarks ?? '').trim()
  if (remarks.startsWith('EXCEL_SYNC:')) return 'excel'
  if (remarks.startsWith('CSV_IMPORT:')) return 'csv'
  if (row.external_sync_key) return 'excel'
  return 'mes'
}

export function inspectionDataSourceTagType(
  source: InspectionDataSource,
): 'success' | 'warning' | 'info' {
  if (source === 'mes') return 'success'
  if (source === 'excel') return 'warning'
  return 'info'
}
