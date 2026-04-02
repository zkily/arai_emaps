/**
 * 材料コード・管理コード等を、Excel/JSON 由来の指数表記（2.60203E+11）や number 型でも
 * 通常の桁表示にそろえる（テーブル表示用）。
 */
export function toPlainCodeDisplay(val: unknown): string {
  if (val == null || val === '') return ''
  if (typeof val === 'number' && Number.isFinite(val)) {
    const t = Math.trunc(val)
    if (Number.isInteger(val) || Math.abs(val - t) < 1e-9) {
      if (Math.abs(t) <= Number.MAX_SAFE_INTEGER) return String(t)
      try {
        return BigInt(t).toString()
      } catch {
        return String(val)
      }
    }
  }
  const s = String(val).trim()
  if (/^[-+]?[\d.]+\s*[eE]\s*[+-]?\d+$/.test(s)) {
    const n = Number(s.replace(/\s/g, ''))
    if (Number.isFinite(n) && Math.abs(n) <= Number.MAX_SAFE_INTEGER) {
      return String(Math.round(n))
    }
  }
  return s
}
