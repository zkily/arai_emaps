import type { FactoryLayoutObject } from '@/api/mes/factoryLayout'

export type AlignMode = 'left' | 'right' | 'top' | 'bottom' | 'hcenter' | 'vcenter'
export type StackAction = 'front' | 'back' | 'forward' | 'backward'

export function objectBounds(list: FactoryLayoutObject[]) {
  const left = Math.min(...list.map((item) => item.x))
  const top = Math.min(...list.map((item) => item.y))
  const right = Math.max(...list.map((item) => item.x + item.width))
  const bottom = Math.max(...list.map((item) => item.y + item.height))
  return { x: left, y: top, width: right - left, height: bottom - top }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

export function alignObjects(list: FactoryLayoutObject[], mode: AlignMode): FactoryLayoutObject[] {
  const movable = list.filter((item) => !item.locked)
  if (movable.length < 2) return list.map((item) => ({ ...item }))
  const box = objectBounds(movable)
  const midX = box.x + box.width / 2
  const midY = box.y + box.height / 2
  return list.map((item) => {
    if (item.locked) return { ...item }
    const next = { ...item }
    if (mode === 'left') next.x = box.x
    if (mode === 'right') next.x = box.x + box.width - item.width
    if (mode === 'top') next.y = box.y
    if (mode === 'bottom') next.y = box.y + box.height - item.height
    if (mode === 'hcenter') next.x = Math.round(midX - item.width / 2)
    if (mode === 'vcenter') next.y = Math.round(midY - item.height / 2)
    return next
  })
}

export function distributeObjects(
  list: FactoryLayoutObject[],
  axis: 'x' | 'y',
): FactoryLayoutObject[] {
  const movable = list.filter((item) => !item.locked)
  if (movable.length < 3) return list.map((item) => ({ ...item }))
  const sorted = [...movable].sort((a, b) => (axis === 'x' ? a.x - b.x : a.y - b.y) || a.id - b.id)
  const first = sorted[0]
  const last = sorted[sorted.length - 1]
  const span =
    axis === 'x' ? last.x + last.width - first.x : last.y + last.height - first.y
  const total = sorted.reduce((sum, item) => sum + (axis === 'x' ? item.width : item.height), 0)
  const gap = (span - total) / (sorted.length - 1)
  let cursor = axis === 'x' ? first.x : first.y
  const placed = new Map<number, FactoryLayoutObject>()
  for (const item of sorted) {
    const next = { ...item }
    if (axis === 'x') {
      next.x = Math.round(cursor)
      cursor += item.width + gap
    } else {
      next.y = Math.round(cursor)
      cursor += item.height + gap
    }
    placed.set(item.id, next)
  }
  return list.map((item) => placed.get(item.id) ?? { ...item })
}

export function stackObjects(
  all: FactoryLayoutObject[],
  ids: number[],
  action: StackAction,
): FactoryLayoutObject[] {
  const selected = new Set(ids)
  let order = [...all].sort((a, b) => a.z_index - b.z_index || a.id - b.id)
  const take = (wantSelected: boolean) => order.filter((item) => selected.has(item.id) === wantSelected)
  if (action === 'front') order = [...take(false), ...take(true)]
  if (action === 'back') order = [...take(true), ...take(false)]
  if (action === 'forward') {
    for (let index = order.length - 2; index >= 0; index -= 1) {
      if (selected.has(order[index].id) && !selected.has(order[index + 1].id)) {
        const current = order[index]
        order[index] = order[index + 1]
        order[index + 1] = current
      }
    }
  }
  if (action === 'backward') {
    for (let index = 1; index < order.length; index += 1) {
      if (selected.has(order[index].id) && !selected.has(order[index - 1].id)) {
        const current = order[index]
        order[index] = order[index - 1]
        order[index - 1] = current
      }
    }
  }
  const zById = new Map(order.map((item, index) => [item.id, index]))
  return all.map((item) => ({ ...item, z_index: zById.get(item.id) ?? item.z_index }))
}

export function nudgeObjects(
  list: FactoryLayoutObject[],
  dx: number,
  dy: number,
  canvasWidth: number,
  canvasHeight: number,
): FactoryLayoutObject[] {
  return list.map((item) => {
    if (item.locked) return { ...item }
    return {
      ...item,
      x: clamp(item.x + dx, 0, Math.max(0, canvasWidth - item.width)),
      y: clamp(item.y + dy, 0, Math.max(0, canvasHeight - item.height)),
    }
  })
}

export function rotateObjects(list: FactoryLayoutObject[]): FactoryLayoutObject[] {
  return list.map((item) =>
    item.locked ? { ...item } : { ...item, rotation: ((item.rotation || 0) + 90) % 360 },
  )
}

export function setLocked(list: FactoryLayoutObject[], locked: boolean): FactoryLayoutObject[] {
  return list.map((item) => ({ ...item, locked }))
}

export function rectsIntersect(
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
) {
  return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y
}
