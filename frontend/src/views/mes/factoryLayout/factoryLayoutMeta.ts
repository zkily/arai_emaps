import type { LayoutObjectType } from '@/api/mes/factoryLayout'

export const STATUS_COLOR: Record<string, string> = {
  running: '#16a34a',
  idle: '#94a3b8',
  alarm: '#e11d48',
  maintenance: '#d97706',
  offline: '#334155',
  open: '#0284c7',
  blocked: '#ea580c',
  stocked: '#0f766e',
  empty: '#cbd5e1',
  low: '#ca8a04',
}

const DARK_TEXT = new Set(['idle', 'maintenance', 'empty', 'low'])

export function statusesFor(type: LayoutObjectType): string[] {
  if (type === 'machine') return ['running', 'idle', 'alarm', 'maintenance', 'offline']
  if (type === 'aisle') return ['open', 'blocked']
  if (type === 'workshop') return []
  return ['stocked', 'empty', 'low']
}

export function defaultStatus(type: LayoutObjectType): string {
  if (type === 'machine') return 'idle'
  if (type === 'aisle') return 'open'
  if (type === 'workshop') return 'idle'
  return 'empty'
}

export function statusColor(status: string | undefined): string {
  if (!status) return '#94a3b8'
  return STATUS_COLOR[status] || '#94a3b8'
}

export function statusUsesDarkText(status: string | undefined): boolean {
  return !!status && DARK_TEXT.has(status)
}

export const FILL_PRESETS = [
  '#22c55e',
  '#94a3b8',
  '#ef4444',
  '#f59e0b',
  '#475569',
  '#38bdf8',
  '#0ea5e9',
  '#6366f1',
  '#14b8a6',
  '#eab308',
  '#f97316',
  '#ec4899',
]

export function prefersDarkText(hex: string): boolean {
  const raw = hex.replace('#', '')
  if (raw.length !== 6) return false
  const red = Number.parseInt(raw.slice(0, 2), 16)
  const green = Number.parseInt(raw.slice(2, 4), 16)
  const blue = Number.parseInt(raw.slice(4, 6), 16)
  return (red * 299 + green * 587 + blue * 114) / 1000 > 160
}

export function defaultSize(type: LayoutObjectType): { width: number; height: number } {
  if (type === 'machine') return { width: 140, height: 90 }
  if (type === 'aisle') return { width: 280, height: 64 }
  if (type === 'workshop') return { width: 240, height: 150 }
  return { width: 180, height: 120 }
}

export function defaultZ(type: LayoutObjectType): number {
  if (type === 'machine') return 20
  if (type === 'workshop') return 15
  if (type === 'material_zone') return 10
  return 0
}

/** 名称を省略せず表示できる最小幅（font-size 12 想定） */
export function widthForLabel(label: string, currentWidth = 40): number {
  const text = label.trim()
  if (!text) return Math.max(40, currentWidth)
  const needed = Math.ceil(text.length * 12 + 40)
  return Math.max(40, currentWidth, needed)
}
