/** MES 不良内訳 JSON（項目→数量、または { qty, at }）の共通パース */

export interface MesDefectEntry {
  qty: number
  at: string | null
}

export type MesDefectByItemPayloadValue = number | { qty: number; at?: string }

export function parseMesDefectEntry(value: unknown): MesDefectEntry {
  if (value != null && typeof value === 'object' && !Array.isArray(value)) {
    const obj = value as Record<string, unknown>
    const qtyRaw = obj.qty ?? obj.quantity ?? obj.count
    const qty = Math.round(Number(qtyRaw))
    const atRaw = obj.at ?? obj.occurred_at ?? obj.occurredAt
    const at = typeof atRaw === 'string' && atRaw.trim() ? atRaw.trim() : null
    return {
      qty: Number.isFinite(qty) && qty > 0 ? qty : 0,
      at,
    }
  }
  const n = Math.round(Number(value))
  return {
    qty: Number.isFinite(n) && n > 0 ? n : 0,
    at: null,
  }
}

export function parseMesDefectMapFromRow(raw: unknown): Record<string, MesDefectEntry> {
  const out: Record<string, MesDefectEntry> = {}
  if (!raw || typeof raw !== 'object') return out
  for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
    const cd = (k ?? '').trim()
    if (!cd) continue
    const entry = parseMesDefectEntry(v)
    if (entry.qty > 0) out[cd] = entry
  }
  return out
}

export function parseDefectsFromRow(raw: unknown): Record<string, number> {
  const map = parseMesDefectMapFromRow(raw)
  const out: Record<string, number> = {}
  for (const [cd, entry] of Object.entries(map)) out[cd] = entry.qty
  return out
}

export function parseDefectAtFromRow(raw: unknown): Record<string, string> {
  const map = parseMesDefectMapFromRow(raw)
  const out: Record<string, string> = {}
  for (const [cd, entry] of Object.entries(map)) {
    if (entry.at) out[cd] = entry.at
  }
  return out
}

export function buildMesDefectByItemPayload(
  defects: Record<string, number>,
  atByItem: Record<string, string> = {},
): Record<string, MesDefectByItemPayloadValue> {
  const out: Record<string, MesDefectByItemPayloadValue> = {}
  for (const [cd, rawQty] of Object.entries(defects)) {
    const qty = Math.max(0, Math.round(rawQty))
    if (qty <= 0) continue
    const at = (atByItem[cd] ?? '').trim()
    out[cd] = at ? { qty, at } : qty
  }
  return out
}
