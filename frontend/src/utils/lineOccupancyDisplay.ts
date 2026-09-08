/** 設備稼働時間帯の技術使用・保全（占用）表示ユーティリティ */

export type OccupancySlotLike = {
  display?: string
  label?: string
  short_range?: string
  work_date?: string
  start_time?: string
  end_time?: string
  note?: string | null
  slot_type?: string
  is_advance_notice?: boolean
  summary?: string
}

/** 08:00 → 8、08:30 → 8:30 */
export function formatOccupancyShortHour(raw?: string | null): string {
  const s = String(raw || '').trim()
  if (!s) return ''
  const m = s.match(/^(\d{1,2}):(\d{2})/)
  if (!m) return s
  const h = Number(m[1])
  const min = Number(m[2])
  if (!Number.isFinite(h) || !Number.isFinite(min)) return s
  return min === 0 ? String(h) : `${h}:${String(min).padStart(2, '0')}`
}

/** 2026-09-09 → 9/9 */
export function formatOccupancyShortDate(raw?: string | null): string {
  const s = String(raw || '').trim().replace(/\//g, '-').slice(0, 10)
  const m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
  if (!m) return ''
  return `${Number(m[2])}/${Number(m[3])}`
}

/** 技術使用 9/9 8–17 */
export function formatOccupancyDisplay(
  occ: OccupancySlotLike,
  _planDate?: string | null,
): string {
  if (occ?.display) {
    const base = String(occ.display)
    const note = String(occ.note || '').trim()
    return note && !base.includes(note) ? `${base} ${note}` : base
  }
  const label = String(occ?.label || '').trim()
  if (occ?.short_range) {
    const base = `${label} ${occ.short_range}`.trim()
    const note = String(occ.note || '').trim()
    return note ? `${base} ${note}` : base
  }
  const dateS = formatOccupancyShortDate(occ?.work_date)
  const startS = formatOccupancyShortHour(occ?.start_time)
  const endS = formatOccupancyShortHour(occ?.end_time)
  const range =
    dateS && startS && endS
      ? `${dateS} ${startS}–${endS}`
      : startS && endS
        ? `${startS}–${endS}`
        : dateS
  return `${label} ${range}`.trim()
}

/** 同一 生産日×設備 の先頭行だけ占用を表示 */
export function shouldShowOccupancyRow<T extends { plan_date?: string; machine_name?: string }>(
  list: T[],
  row: T,
): boolean {
  const d = String(row?.plan_date || '')
  const m = String(row?.machine_name || '').trim()
  const idx = list.findIndex(
    (r) => String(r?.plan_date || '') === d && String(r?.machine_name || '').trim() === m,
  )
  if (idx < 0) return true
  return list[idx] === row
}

export type DayOccupancyKind = 'tech' | 'maintenance' | 'mixed' | ''

/** slots から技術/保全フラグを判定（稼働表・ガント帯用） */
export function dayOccupancyKindFromSlots(
  slots: Array<{ slot_type?: string | null; is_rest?: boolean | null }>,
): DayOccupancyKind {
  let hasTech = false
  let hasMaint = false
  for (const s of slots || []) {
    const st = String(s?.slot_type || '').trim().toLowerCase()
    const normalized =
      st === 'tech' || st === 'maintenance' || st === 'rest' || st === 'work'
        ? st
        : s?.is_rest
          ? 'rest'
          : 'work'
    if (normalized === 'tech') hasTech = true
    if (normalized === 'maintenance') hasMaint = true
  }
  if (hasTech && hasMaint) return 'mixed'
  if (hasTech) return 'tech'
  if (hasMaint) return 'maintenance'
  return ''
}
