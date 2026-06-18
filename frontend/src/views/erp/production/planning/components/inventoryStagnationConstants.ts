/** 在庫停滞監視：inventory_column ↔ 工程表示名 */
export const INVENTORY_COLUMN_OPTIONS = [
  { value: 'cutting_inventory', label: '切断' },
  { value: 'chamfering_inventory', label: '面取' },
  { value: 'molding_inventory', label: '成型' },
  { value: 'plating_inventory', label: 'メッキ' },
  { value: 'welding_inventory', label: '溶接' },
  { value: 'inspection_inventory', label: '検査' },
  { value: 'warehouse_inventory', label: '倉庫' },
  { value: 'outsourced_warehouse_inventory', label: '外注倉庫' },
  { value: 'outsourced_plating_inventory', label: '外注メッキ' },
  { value: 'outsourced_welding_inventory', label: '外注溶接' },
  { value: 'pre_welding_inspection_inventory', label: '溶接前検査' },
  { value: 'pre_inspection_inventory', label: '外注支給前' },
  { value: 'pre_outsourcing_inventory', label: '外注検査前' },
] as const

export const INVENTORY_STAGNATION_EVENT = 'INVENTORY_STAGNATION'

export function inventoryColumnLabel(col: string | null | undefined) {
  if (!col) return '全工程'
  return INVENTORY_COLUMN_OPTIONS.find((o) => o.value === col)?.label || col
}

export function inventoryChipClass(col: string | null | undefined) {
  return `inventory-chip--${String(col || '').replace(/_/g, '-')}`
}
