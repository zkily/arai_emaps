/** welding_management.data_source */

export type WeldingDataSource = 'mes' | 'excel' | 'csv'

export function resolveWeldingDataSource(row: {
  data_source?: string | null
  remarks?: string | null
  external_sync_key?: string | null
}): WeldingDataSource {
  const ds = (row.data_source ?? '').trim().toLowerCase()
  if (ds === 'mes' || ds === 'excel' || ds === 'csv') return ds
  const remarks = (row.remarks ?? '').trim()
  if (remarks.startsWith('EXCEL_SYNC:')) return 'excel'
  if (remarks.startsWith('CSV_IMPORT:')) return 'csv'
  if (row.external_sync_key) return 'excel'
  return 'mes'
}

export function weldingDataSourceTagType(
  source: WeldingDataSource,
): 'success' | 'warning' | 'info' {
  if (source === 'mes') return 'success'
  if (source === 'excel') return 'warning'
  return 'info'
}
