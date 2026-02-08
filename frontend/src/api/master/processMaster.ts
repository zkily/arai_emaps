/**
 * 工程マスタ API（スタブ）
 * 工程マスタ画面未実装時は空リスト・デフォルト値を返す。
 * 実装時は本ファイルを実APIに差し替える。
 */
export interface ProcessListParams {
  keyword?: string
  page?: number
  pageSize?: number
}

export interface ProcessItem {
  id?: number
  process_cd: string
  process_name?: string
  default_yield?: number
  default_cycle_sec?: number
}

export function getProcessList(_params?: ProcessListParams): Promise<{ list?: ProcessItem[]; data?: { list: ProcessItem[] } }> {
  return Promise.resolve({ list: [], data: { list: [] } })
}

export function getProcessByIdOrCd(_idOrCd: string | number): Promise<ProcessItem | null> {
  return Promise.resolve(null)
}
