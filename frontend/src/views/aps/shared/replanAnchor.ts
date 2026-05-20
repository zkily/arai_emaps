/**
 * APS ライン順再計算 API（replan-sequence）のクエリ錨点（フォールバック）。
 * 当該設備に DB（aps_line_replan_anchors）があればサーバ側でそちらが最優先される。
 */

/** 日本時区の暦日（YYYY-MM-DD） */
export function formatYmdInJapan(d: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(d)
}

/** YYYY-MM → 当月初日 YYYY-MM-01 */
export function firstDayOfMonthIso(month: string): string {
  const t = (month || '').trim()
  const m = t.match(/^(\d{4}-\d{2})/)
  return m ? `${m[1]}-01` : t
}

/** YYYY-MM-DD → YYYY-MM */
export function ymFromIsoDate(iso: string): string | null {
  const t = (iso || '').trim()
  const m = t.match(/^(\d{4}-\d{2})/)
  return m ? m[1] : null
}

/**
 * 基準月1日と日本の今日の大きい方（過去の月初に固定しない）。
 */
export function computeEffectiveReplanAnchorDate(
  anchorIso: string,
  todayIso: string = formatYmdInJapan(),
): string {
  const anchor = (anchorIso || '').trim()
  const today = (todayIso || '').trim()
  if (!anchor) return today || formatYmdInJapan()
  if (!today) return anchor
  return anchor >= today ? anchor : today
}
