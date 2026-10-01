/** 棚卸リスト一覧：項目・工程ごとの配色 */

export interface ColorToken {
  color: string
  bg: string
  border: string
}

const token = (hex: string): ColorToken => ({
  color: hex,
  bg: `${hex}14`,
  border: `${hex}40`,
})

export const ITEM_COLORS: Record<string, ColorToken> = {
  材料棚卸: token('#059669'),
  部品棚卸: token('#d97706'),
  製品棚卸: token('#4f46e5'),
}

const DEFAULT_ITEM_COLOR = token('#64748b')

export const getItemColor = (item?: string | null): ColorToken =>
  (item && ITEM_COLORS[item]) || DEFAULT_ITEM_COLOR

const PROCESS_COLORS: Record<string, string> = {
  KT01: '#2563eb', // 切断
  KT02: '#0d9488', // 面取
  KT03: '#0891b2', // SW
  KT04: '#7c3aed', // 成型
  KT05: '#d97706', // メッキ
  KT06: '#ea580c', // 外注メッキ
  KT07: '#e11d48', // 溶接
  KT08: '#db2777', // 外注溶接
  KT09: '#16a34a', // 検査
  KT10: '#65a30d', // 外注検査前・外注支給前
  KT11: '#059669', // 溶接前検査
  KT12: '#4f46e5',
  KT13: '#0369a1', // 倉庫
  KT14: '#9333ea',
  KT15: '#0284c7',
  KT16: '#be185d',
  KT17: '#c2410c',
  KT18: '#b45309', // 部品倉庫
}

const FALLBACK_PALETTE = ['#475569', '#0f766e', '#6d28d9', '#b91c1c', '#a16207', '#1d4ed8']

export const getProcessColor = (processCd?: string | null): ColorToken => {
  const cd = String(processCd ?? '').trim()
  if (!cd) return token('#64748b')
  const hex = PROCESS_COLORS[cd]
  if (hex) return token(hex)
  let h = 0
  for (const ch of cd) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return token(FALLBACK_PALETTE[h % FALLBACK_PALETTE.length])
}
