/**
 * ピッキングCSVエクスポートAPI
 * データ範囲: 出荷日 ≥ DB サーバー当日（CURDATE()）。画面の検索条件は使用しない。
 * 無 body、60 分タイムアウト。
 */
import request from '@/utils/request'

export interface ExportPickingCSVResponse {
  copiedCount: number
  totalDataCount: number
  fileName?: string
  csvFilePath?: string | null
  exportTime?: string
}

/** POST /api/shipping/export/export-picking-csv（パラメータなし） */
export const exportPickingCSV = () => {
  return request.post<ExportPickingCSVResponse>(
    '/api/shipping/export/export-picking-csv',
    undefined,
    { timeout: 3600000 },
  )
}
