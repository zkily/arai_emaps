/**
 * 部品マスタ（棚卸ダイアログ用の薄いラッパ。API 未整備時は空）
 */
export interface ComponentListItem {
  component_cd: string
  component_name: string
}

export async function getComponentList(_params?: {
  page?: number
  pageSize?: number
  keyword?: string
}): Promise<{ list: ComponentListItem[] }> {
  return { list: [] }
}
