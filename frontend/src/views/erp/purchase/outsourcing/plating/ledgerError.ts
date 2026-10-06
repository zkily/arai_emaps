import { ElMessage } from 'element-plus'

/**
 * request インターセプターが表示しないエラーだけを表示する。
 * 500 はインターセプターが表示しない。通信エラー（response なし・request あり）は表示済み。
 */
export function notifyLedgerError(error: any, fallback: string) {
  const shouldShow = error?.response ? error.response.status === 500 : !error?.request
  if (shouldShow) {
    ElMessage.error(error?.response?.data?.detail || error?.message || fallback)
  }
}
