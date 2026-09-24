<template>
  <div
    class="factory-canvas"
    :class="{ 'is-space': spaceDown }"
    @dragover.prevent
    @drop.prevent="onDrop"
    @wheel.prevent="onWheel"
    @contextmenu.prevent="onContextMenu($event, null)"
  >
    <svg
      ref="svgRef"
      class="factory-canvas__svg"
      :viewBox="viewBox"
      @pointerdown="onBackgroundPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <defs>
        <linearGradient id="factory-floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#f7f9fc" />
          <stop offset="100%" stop-color="#e7eef7" />
        </linearGradient>
        <pattern
          v-if="showGrid"
          id="factory-grid"
          :width="gridSize"
          :height="gridSize"
          patternUnits="userSpaceOnUse"
        >
          <circle :cx="1" :cy="1" r="1.05" fill="#c5d0e0" />
        </pattern>
        <pattern id="factory-aisle-lane" width="18" height="8" patternUnits="userSpaceOnUse">
          <rect width="10" height="2" y="3" rx="1" fill="rgba(255,255,255,0.72)" />
        </pattern>
        <filter id="factory-shadow" x="-30%" y="-30%" width="160%" height="170%">
          <feDropShadow dx="0" dy="3" stdDeviation="3.2" flood-color="#0f172a" flood-opacity="0.18" />
        </filter>
      </defs>

      <rect :width="canvasWidth" :height="canvasHeight" fill="url(#factory-floor)" />
      <rect v-if="showGrid" :width="canvasWidth" :height="canvasHeight" fill="url(#factory-grid)" />
      <rect
        :width="canvasWidth"
        :height="canvasHeight"
        fill="none"
        stroke="#d5deea"
        stroke-width="1.5"
      />

      <g
        v-for="obj in sorted"
        :key="obj.id"
        :data-object-id="obj.id"
        class="factory-canvas__object"
        :class="{ 'is-edit': editMode && !obj.locked, 'is-locked': obj.locked }"
        :transform="rotationTransform(obj)"
        @pointerdown="onObjectPointerDown($event, obj)"
        @dblclick.stop="onObjectDblClick(obj)"
        @pointerenter="onObjectHover($event, obj)"
        @pointermove="onObjectHover($event, obj)"
        @pointerleave="onObjectHoverLeave"
        @contextmenu.prevent.stop="onContextMenu($event, obj.id)"
      >
        <g pointer-events="none" :opacity="(obj.opacity ?? 100) / 100" filter="url(#factory-shadow)">
          <rect
            :x="obj.x"
            :y="obj.y"
            :width="obj.width"
            :height="obj.height"
            :rx="radiusOf(obj)"
            :fill="fillOf(obj)"
            :stroke="strokeOf(obj)"
            :stroke-width="obj.border_color ? 2.6 : 1.25"
          />
          <rect
            v-if="obj.object_type === 'aisle'"
            :x="obj.x + 10"
            :y="obj.y + obj.height * 0.78"
            :width="Math.max(0, obj.width - 20)"
            height="3"
            rx="1.5"
            fill="url(#factory-aisle-lane)"
          />
          <rect
            v-if="obj.object_type === 'material_zone'"
            :x="obj.x + 8"
            :y="obj.y + 8"
            :width="Math.max(0, obj.width - 16)"
            :height="Math.max(0, obj.height - 16)"
            :rx="8"
            fill="none"
            stroke="rgba(255,255,255,0.45)"
            stroke-width="1.4"
          />
          <rect
            v-if="obj.object_type !== 'workshop'"
            :x="obj.x + 8"
            :y="namePlateY(obj)"
            :width="Math.max(0, obj.width - 16)"
            :height="namePlateHeight(obj)"
            rx="7"
            fill="rgba(15,23,42,0.22)"
          />
          <text
            :x="obj.x + obj.width / 2"
            :y="obj.object_type === 'workshop' ? obj.y + obj.height / 2 : nameAnchorY(obj)"
            text-anchor="middle"
            dominant-baseline="middle"
            fill="#ffffff"
            :font-size="obj.object_type === 'workshop' ? 14 : 11"
            font-weight="700"
          >
            {{ obj.label }}
          </text>
          <text
            v-if="obj.object_type !== 'workshop'"
            :x="obj.x + obj.width / 2"
            :y="statusAnchorY(obj)"
            text-anchor="middle"
            dominant-baseline="middle"
            :fill="textFill(obj)"
            font-size="12"
            font-weight="600"
          >
            {{ fitText(statusText(obj), obj.width - 12) }}
          </text>
          <circle
            v-if="obj.object_type === 'machine' && obj.width >= 96 && !obj.locked"
            :cx="obj.x + obj.width - 20"
            :cy="nameAnchorY(obj)"
            r="4.5"
            fill="#ffffff"
            fill-opacity="0.92"
          />
          <circle
            v-if="obj.object_type === 'machine' && obj.width >= 96 && !obj.locked"
            :cx="obj.x + obj.width - 20"
            :cy="nameAnchorY(obj)"
            r="2.4"
            :fill="isAlert(obj) ? '#ef4444' : '#0f172a'"
            fill-opacity="0.55"
          />
          <g v-if="obj.locked">
            <circle :cx="obj.x + obj.width - 14" :cy="obj.y + 14" r="8" fill="rgba(15,23,42,0.55)" />
            <text
              :x="obj.x + obj.width - 14"
              :y="obj.y + 17.5"
              text-anchor="middle"
              fill="#ffffff"
              font-size="9"
              font-weight="700"
            >
              鍵
            </text>
          </g>
        </g>
        <rect
          v-if="isSelected(obj.id)"
          data-pdf-omit=""
          :x="obj.x - 4"
          :y="obj.y - 4"
          :width="obj.width + 8"
          :height="obj.height + 8"
          :rx="radiusOf(obj) + 4"
          fill="none"
          stroke="#4f46e5"
          stroke-width="2"
          pointer-events="none"
        />
        <rect
          v-if="isAlert(obj)"
          class="factory-canvas__pulse"
          data-pdf-omit=""
          :x="obj.x - 2"
          :y="obj.y - 2"
          :width="obj.width + 4"
          :height="obj.height + 4"
          :rx="radiusOf(obj) + 2"
          fill="none"
          stroke="#ef4444"
          stroke-width="2"
          pointer-events="none"
        />
        <rect
          :x="obj.x"
          :y="obj.y"
          :width="obj.width"
          :height="obj.height"
          :rx="radiusOf(obj)"
          fill="transparent"
        />
        <rect
          v-if="editMode && isSelected(obj.id) && selectedIds.length === 1 && !obj.locked && !(obj.rotation % 180)"
          class="factory-canvas__handle"
          data-pdf-omit=""
          :x="obj.x + obj.width - 9"
          :y="obj.y + obj.height - 9"
          width="14"
          height="14"
          rx="7"
          fill="#ffffff"
          stroke="#4f46e5"
          stroke-width="2"
          @pointerdown="onResizePointerDown($event, obj)"
        />
      </g>

      <rect
        v-if="marquee"
        :x="marquee.x"
        :y="marquee.y"
        :width="marquee.width"
        :height="marquee.height"
        fill="rgba(37,99,235,0.12)"
        stroke="#2563eb"
        stroke-dasharray="4 3"
        pointer-events="none"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { FactoryLayoutObject, ObjectStatus } from '@/api/mes/factoryLayout'
import { rectsIntersect } from './editorOps'
import { fl } from './factoryLayoutJa'
import { prefersDarkText, statusColor } from './factoryLayoutMeta'

const props = defineProps<{
  canvasWidth: number
  canvasHeight: number
  gridSize: number
  editMode: boolean
  snapToGrid: boolean
  showGrid: boolean
  objects: FactoryLayoutObject[]
  statuses: Record<string, ObjectStatus>
  selectedIds: number[]
}>()

const emit = defineEmits<{
  select: [ids: number[], primary: number | null]
  batch: [patches: { id: number; x?: number; y?: number; width?: number; height?: number }[]]
  interactStart: []
  interactEnd: []
  create: [payload: { objectType: FactoryLayoutObject['object_type']; x: number; y: number }]
  zoom: [value: number]
  context: [payload: { clientX: number; clientY: number; id: number | null }]
  openDetail: []
  hover: [payload: { id: number; clientX: number; clientY: number } | null]
  enter: [layoutId: number]
}>()

const svgRef = ref<SVGSVGElement | null>(null)
const vx = ref(0)
const vy = ref(0)
const zoom = ref(1)
const spaceDown = ref(false)

const viewBox = computed(() => {
  const w = props.canvasWidth / zoom.value
  const h = props.canvasHeight / zoom.value
  return `${vx.value} ${vy.value} ${w} ${h}`
})

const sorted = computed(() =>
  [...props.objects].sort((a, b) => a.z_index - b.z_index || a.id - b.id),
)

const marquee = ref<{ x: number; y: number; width: number; height: number } | null>(null)

type Origin = { id: number; x: number; y: number }
type DragState = {
  mode: 'pan' | 'move' | 'resize' | 'marquee'
  id: number
  pointerId: number
  originClientX: number
  originClientY: number
  originSvgX: number
  originSvgY: number
  originObjX: number
  originObjY: number
  originW: number
  originH: number
  originVx: number
  originVy: number
  origins: Origin[]
  moved: boolean
  started: boolean
}

const drag = ref<DragState | null>(null)

function isSelected(id: number) {
  return props.selectedIds.includes(id)
}

function rotationTransform(obj: FactoryLayoutObject) {
  const rotation = obj.rotation || 0
  if (!rotation) return undefined
  const cx = obj.x + obj.width / 2
  const cy = obj.y + obj.height / 2
  return `rotate(${rotation} ${cx} ${cy})`
}

function clientToSvg(clientX: number, clientY: number) {
  const svg = svgRef.value
  if (!svg) return { x: 0, y: 0 }
  const pt = svg.createSVGPoint()
  pt.x = clientX
  pt.y = clientY
  const ctm = svg.getScreenCTM()
  if (!ctm) return { x: 0, y: 0 }
  const p = pt.matrixTransform(ctm.inverse())
  return { x: p.x, y: p.y }
}

function snap(value: number) {
  if (!props.snapToGrid) return Math.round(value)
  const grid = props.gridSize || 20
  return Math.round(value / grid) * grid
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function fillOf(obj: FactoryLayoutObject) {
  if (obj.fill_color) return obj.fill_color
  if (obj.object_type === 'workshop') return '#4338ca'
  return statusColor(props.statuses[String(obj.id)]?.status)
}

function namePlateHeight(obj: FactoryLayoutObject) {
  return Math.min(24, Math.max(16, obj.height * 0.24))
}

function namePlateY(obj: FactoryLayoutObject) {
  return obj.y + 6
}

function nameAnchorY(obj: FactoryLayoutObject) {
  return namePlateY(obj) + namePlateHeight(obj) / 2
}

function statusAnchorY(obj: FactoryLayoutObject) {
  const top = namePlateY(obj) + namePlateHeight(obj)
  const bottom = obj.y + obj.height * 0.72
  return top + Math.max(0, bottom - top) / 2
}

function radiusOf(obj: FactoryLayoutObject) {
  if (obj.object_type === 'aisle') return Math.min(22, Math.max(8, obj.height / 2))
  if (obj.object_type === 'workshop') return 18
  if (obj.object_type === 'machine') return 16
  return 12
}

function strokeOf(obj: FactoryLayoutObject) {
  if (obj.border_color) return obj.border_color
  return prefersDarkText(fillOf(obj)) ? 'rgba(15,23,42,0.16)' : 'rgba(255,255,255,0.7)'
}

function isAlert(obj: FactoryLayoutObject) {
  const status = props.statuses[String(obj.id)]?.status
  return status === 'alarm' || status === 'blocked'
}

function textFill(obj: FactoryLayoutObject) {
  return prefersDarkText(fillOf(obj)) ? '#1e293b' : '#ffffff'
}

function fitText(text: string, width: number) {
  const maxChars = Math.max(2, Math.floor((width - 16) / 14))
  if (text.length <= maxChars) return text
  return `${text.slice(0, maxChars - 1)}…`
}

function statusText(obj: FactoryLayoutObject) {
  if (obj.object_type === 'workshop') {
    return obj.child_layout_id ? fl('enterWorkshop') : fl('workshopUnlinked')
  }
  const status = props.statuses[String(obj.id)]?.status
  if (!status) return ''
  const label = fl(`statusName.${status}`)
  return label === `statusName.${status}` ? status : label
}

function groupIds(id: number) {
  const obj = props.objects.find((item) => item.id === id)
  if (!obj?.group_key) return [id]
  return props.objects.filter((item) => item.group_key === obj.group_key).map((item) => item.id)
}

function selectionAfterClick(id: number, additive: boolean) {
  const grouped = groupIds(id)
  if (!additive) return grouped
  const set = new Set(props.selectedIds)
  const allIn = grouped.every((item) => set.has(item))
  grouped.forEach((item) => (allIn ? set.delete(item) : set.add(item)))
  return [...set]
}

function onWheel(event: WheelEvent) {
  const svg = svgRef.value
  if (!svg) return
  const pt = clientToSvg(event.clientX, event.clientY)
  const factor = event.deltaY < 0 ? 1.12 : 1 / 1.12
  const next = clamp(zoom.value * factor, 0.35, 3)
  const rect = svg.getBoundingClientRect()
  const sx = (event.clientX - rect.left) / rect.width
  const sy = (event.clientY - rect.top) / rect.height
  const w = props.canvasWidth / next
  const h = props.canvasHeight / next
  vx.value = pt.x - sx * w
  vy.value = pt.y - sy * h
  zoom.value = next
}

function zoomBy(factor: number) {
  const svg = svgRef.value
  const next = clamp(zoom.value * factor, 0.35, 3)
  if (!svg) {
    zoom.value = next
    return
  }
  const rect = svg.getBoundingClientRect()
  const pt = clientToSvg(rect.left + rect.width / 2, rect.top + rect.height / 2)
  const w = props.canvasWidth / next
  const h = props.canvasHeight / next
  vx.value = pt.x - w / 2
  vy.value = pt.y - h / 2
  zoom.value = next
}

function fit() {
  vx.value = 0
  vy.value = 0
  zoom.value = 1
}

function focusRect(x: number, y: number, width: number, height: number) {
  const pad = 48
  const viewW = Math.max(80, width + pad * 2)
  const viewH = Math.max(80, height + pad * 2)
  const next = clamp(Math.min(props.canvasWidth / viewW, props.canvasHeight / viewH), 0.35, 3)
  vx.value = x - pad
  vy.value = y - pad
  zoom.value = next
}

watch(zoom, (value) => emit('zoom', value))

function getSvgElement() {
  return svgRef.value
}

defineExpose({ zoomBy, fit, focusRect, getSvgElement })

function beginDrag(event: PointerEvent, extra: Partial<DragState> & Pick<DragState, 'mode'>): DragState {
  svgRef.value?.setPointerCapture(event.pointerId)
  const pt = clientToSvg(event.clientX, event.clientY)
  const state: DragState = {
    mode: extra.mode,
    id: extra.id ?? 0,
    pointerId: event.pointerId,
    originClientX: event.clientX,
    originClientY: event.clientY,
    originSvgX: pt.x,
    originSvgY: pt.y,
    originObjX: extra.originObjX ?? 0,
    originObjY: extra.originObjY ?? 0,
    originW: extra.originW ?? 0,
    originH: extra.originH ?? 0,
    originVx: vx.value,
    originVy: vy.value,
    origins: extra.origins ?? [],
    moved: false,
    started: false,
  }
  drag.value = state
  return state
}

function markInteract(state: DragState) {
  if (!state.started) {
    state.started = true
    emit('interactStart')
  }
}

function onBackgroundPointerDown(event: PointerEvent) {
  if (event.button === 2) return
  const target = event.target as Element | null
  if (target?.closest?.('[data-object-id]')) return
  const pan = event.button === 1 || spaceDown.value || !props.editMode
  beginDrag(event, { mode: pan ? 'pan' : 'marquee' })
}

function onObjectHover(event: PointerEvent, obj: FactoryLayoutObject) {
  if (props.editMode) return
  emit('hover', { id: obj.id, clientX: event.clientX, clientY: event.clientY })
}

function onObjectHoverLeave() {
  if (props.editMode) return
  emit('hover', null)
}

function onObjectDblClick(obj: FactoryLayoutObject) {
  if (!props.editMode && obj.object_type === 'workshop') return
  const ids = props.editMode ? selectionAfterClick(obj.id, false) : [obj.id]
  emit('select', ids, obj.id)
  emit('openDetail')
}

function onObjectPointerDown(event: PointerEvent, obj: FactoryLayoutObject) {
  if (event.button !== 0) return
  event.stopPropagation()
  if (!props.editMode || spaceDown.value) {
    beginDrag(event, { mode: 'pan', id: obj.id })
    return
  }
  const additive = event.shiftKey || event.ctrlKey || event.metaKey
  const ids = selectionAfterClick(obj.id, additive)
  emit('select', ids, obj.id)
  if (obj.locked && ids.every((id) => props.objects.find((item) => item.id === id)?.locked)) return
  const moveIds = ids.filter((id) => !props.objects.find((item) => item.id === id)?.locked)
  beginDrag(event, {
    mode: 'move',
    id: obj.id,
    originObjX: obj.x,
    originObjY: obj.y,
    origins: moveIds.map((id) => {
      const item = props.objects.find((row) => row.id === id)!
      return { id, x: item.x, y: item.y }
    }),
  })
}

function onResizePointerDown(event: PointerEvent, obj: FactoryLayoutObject) {
  if (!props.editMode || event.button !== 0 || obj.locked) return
  event.stopPropagation()
  emit('select', [obj.id], obj.id)
  beginDrag(event, {
    mode: 'resize',
    id: obj.id,
    originObjX: obj.x,
    originObjY: obj.y,
    originW: obj.width,
    originH: obj.height,
  })
}

function onPointerMove(event: PointerEvent) {
  const state = drag.value
  if (!state || state.pointerId !== event.pointerId) return
  if (state.mode === 'pan') {
    const svg = svgRef.value
    if (!svg) return
    const rect = svg.getBoundingClientRect()
    const dx = event.clientX - state.originClientX
    const dy = event.clientY - state.originClientY
    if (Math.abs(dx) + Math.abs(dy) > 2) state.moved = true
    const w = props.canvasWidth / zoom.value
    const h = props.canvasHeight / zoom.value
    vx.value = state.originVx - (dx / rect.width) * w
    vy.value = state.originVy - (dy / rect.height) * h
    return
  }
  const pt = clientToSvg(event.clientX, event.clientY)
  const dx = pt.x - state.originSvgX
  const dy = pt.y - state.originSvgY
  if (Math.abs(dx) + Math.abs(dy) > 2) state.moved = true
  if (state.mode === 'marquee') {
    const x = Math.min(state.originSvgX, pt.x)
    const y = Math.min(state.originSvgY, pt.y)
    marquee.value = { x, y, width: Math.abs(dx), height: Math.abs(dy) }
    return
  }
  if (!state.moved) return
  markInteract(state)
  if (state.mode === 'move') {
    const primary = state.origins.find((item) => item.id === state.id) || state.origins[0]
    if (!primary) return
    const obj = props.objects.find((item) => item.id === primary.id)
    if (!obj) return
    let x = snap(primary.x + dx)
    let y = snap(primary.y + dy)
    x = clamp(x, 0, Math.max(0, props.canvasWidth - obj.width))
    y = clamp(y, 0, Math.max(0, props.canvasHeight - obj.height))
    const ddx = x - primary.x
    const ddy = y - primary.y
    emit(
      'batch',
      state.origins.map((origin) => {
        const row = props.objects.find((item) => item.id === origin.id)
        const width = row?.width ?? 40
        const height = row?.height ?? 40
        return {
          id: origin.id,
          x: clamp(origin.x + ddx, 0, Math.max(0, props.canvasWidth - width)),
          y: clamp(origin.y + ddy, 0, Math.max(0, props.canvasHeight - height)),
        }
      }),
    )
  } else if (state.mode === 'resize') {
    let width = snap(Math.max(40, state.originW + dx))
    let height = snap(Math.max(40, state.originH + dy))
    width = Math.min(width, Math.max(40, props.canvasWidth - state.originObjX))
    height = Math.min(height, Math.max(40, props.canvasHeight - state.originObjY))
    emit('batch', [{ id: state.id, width, height }])
  }
}

function onPointerUp(event: PointerEvent) {
  const state = drag.value
  if (!state || state.pointerId !== event.pointerId) return
  if (state.mode === 'marquee') {
    const box = marquee.value
    marquee.value = null
    if (!box || (box.width < 4 && box.height < 4)) {
      if (!event.shiftKey && !event.ctrlKey && !event.metaKey) emit('select', [], null)
    } else {
      const hit = props.objects.filter((item) => rectsIntersect(item, box)).map((item) => item.id)
      const additive = event.shiftKey || event.ctrlKey || event.metaKey
      const ids = additive ? [...new Set([...props.selectedIds, ...hit])] : hit
      emit('select', ids, ids[ids.length - 1] ?? null)
    }
  } else if (state.mode === 'pan' && !state.moved && event.button === 0 && !spaceDown.value) {
    if (!props.editMode && state.id) {
      const obj = props.objects.find((item) => item.id === state.id)
      if (obj?.object_type === 'workshop' && obj.child_layout_id) {
        emit('enter', obj.child_layout_id)
        drag.value = null
        return
      }
    }
    emit('select', [], null)
  }
  if (state.started) emit('interactEnd')
  drag.value = null
}

function onDrop(event: DragEvent) {
  if (!props.editMode) return
  const raw =
    event.dataTransfer?.getData('application/x-factory-object') ||
    event.dataTransfer?.getData('text/plain') ||
    ''
  if (raw !== 'machine' && raw !== 'aisle' && raw !== 'material_zone' && raw !== 'workshop') return
  const pt = clientToSvg(event.clientX, event.clientY)
  emit('create', { objectType: raw, x: pt.x, y: pt.y })
}

function onContextMenu(event: MouseEvent, id: number | null) {
  if (!props.editMode) return
  emit('context', { clientX: event.clientX, clientY: event.clientY, id })
}

function onKey(event: KeyboardEvent) {
  if (event.code === 'Space') {
    const tag = (event.target as HTMLElement | null)?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA') return
    spaceDown.value = event.type === 'keydown'
    if (event.type === 'keydown') event.preventDefault()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  window.addEventListener('keyup', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('keyup', onKey)
})
</script>

<style scoped>
.factory-canvas {
  flex: 1;
  min-width: 0;
  min-height: 0;
  border-radius: 18px;
  background: linear-gradient(180deg, #eef3f9 0%, #e3ebf5 100%);
  box-shadow:
    inset 0 0 0 1px rgba(148, 163, 184, 0.45),
    0 16px 40px rgba(15, 23, 42, 0.08);
  overflow: hidden;
  touch-action: none;
}

.factory-canvas__svg {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
  user-select: none;
}

.factory-canvas.is-space .factory-canvas__svg {
  cursor: grab;
}

.factory-canvas__object.is-edit {
  cursor: move;
}

.factory-canvas__object.is-locked {
  cursor: not-allowed;
}

.factory-canvas__object:not(.is-edit):not(.is-locked) {
  cursor: pointer;
}

.factory-canvas__handle {
  cursor: nwse-resize;
  filter: drop-shadow(0 1px 2px rgba(15, 23, 42, 0.25));
}

.factory-canvas__pulse {
  animation: factory-pulse 1.8s ease-in-out infinite;
}

@keyframes factory-pulse {
  0%,
  100% {
    stroke-opacity: 0.95;
  }
  50% {
    stroke-opacity: 0.15;
  }
}
</style>
