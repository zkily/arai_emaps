<template>
  <div
    v-show="visible"
    ref="panelRef"
    class="pp-float-panel"
    :class="{ 'pp-float-panel--dragging': dragging }"
    :style="panelStyle"
    @mousedown="onPanelFocus"
  >
    <div class="pp-float-panel__head" @mousedown="onDragStart">
      <el-icon class="pp-float-panel__grip" :size="14"><Rank /></el-icon>
      <span class="pp-float-panel__title">{{ title }}</span>
      <div class="pp-float-panel__actions" @mousedown.stop>
        <slot name="actions" />
        <el-button
          v-if="closable"
          type="info"
          text
          size="small"
          circle
          :icon="Close"
          title="閉じる"
          @click="onClose"
        />
      </div>
    </div>
    <div class="pp-float-panel__body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Close, Rank } from '@element-plus/icons-vue'

const props = withDefaults(
  defineProps<{
    visible: boolean
    title?: string
    width?: number
    initialX?: number
    initialY?: number
    zIndex?: number
    closable?: boolean
    /** ドラッグ範囲（ページ root 要素） */
    boundary?: HTMLElement | null
  }>(),
  {
    title: '',
    width: 520,
    initialX: 20,
    initialY: 88,
    zIndex: 40,
    closable: true,
    boundary: null,
  },
)

const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
}>()

const panelRef = ref<HTMLElement | null>(null)
const posX = ref(props.initialX)
const posY = ref(props.initialY)
const stackZ = ref(props.zIndex)
const dragging = ref(false)

/** ヘッダー内のクリック位置（パネル左上基準） */
let dragPointerOffsetX = 0
let dragPointerOffsetY = 0

watch(
  () => props.initialX,
  (v) => {
    if (!dragging.value && v != null) posX.value = v
  },
)
watch(
  () => props.initialY,
  (v) => {
    if (!dragging.value && v != null) posY.value = v
  },
)

const panelStyle = computed(() => ({
  left: `${posX.value}px`,
  top: `${posY.value}px`,
  width: `${props.width}px`,
  zIndex: String(stackZ.value),
}))

function clampPosition(x: number, y: number): { x: number; y: number } {
  const boundary = props.boundary
  const panel = panelRef.value
  if (!boundary || !panel) return { x, y }
  const maxX = Math.max(0, boundary.clientWidth - panel.offsetWidth)
  const maxY = Math.max(0, boundary.clientHeight - panel.offsetHeight)
  return {
    x: Math.min(Math.max(0, x), maxX),
    y: Math.min(Math.max(0, y), maxY),
  }
}

function positionFromClient(clientX: number, clientY: number): { x: number; y: number } {
  const boundary = props.boundary
  if (!boundary) {
    return { x: clientX, y: clientY }
  }
  const b = boundary.getBoundingClientRect()
  return clampPosition(
    clientX - b.left - dragPointerOffsetX,
    clientY - b.top - dragPointerOffsetY,
  )
}

function onPanelFocus() {
  stackZ.value = props.zIndex + 1
}

function onDragStart(e: MouseEvent) {
  if (e.button !== 0) return
  const t = e.target as HTMLElement
  if (t.closest('button, .el-button, input, textarea, .el-input, .el-date-editor, .el-select')) return
  const panel = panelRef.value
  if (!panel) return
  const head = (e.currentTarget as HTMLElement).getBoundingClientRect()
  dragPointerOffsetX = e.clientX - head.left
  dragPointerOffsetY = e.clientY - head.top
  dragging.value = true
  onPanelFocus()
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
  e.preventDefault()
}

function onDragMove(e: MouseEvent) {
  if (!dragging.value) return
  const next = positionFromClient(e.clientX, e.clientY)
  posX.value = next.x
  posY.value = next.y
}

function onDragEnd() {
  dragging.value = false
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

function onClose() {
  emit('update:visible', false)
  emit('close')
}

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
})
</script>

<style scoped>
.pp-float-panel {
  position: absolute;
  display: flex;
  flex-direction: column;
  max-height: min(78vh, 520px);
  border-radius: 12px;
  border: 1px solid color-mix(in oklab, var(--el-border-color) 85%, var(--el-color-primary-light-7));
  background: var(--el-bg-color);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.6) inset,
    0 10px 28px rgba(31, 50, 81, 0.14),
    0 4px 10px rgba(31, 50, 81, 0.08);
  overflow: hidden;
  box-sizing: border-box;
}

.pp-float-panel--dragging {
  user-select: none;
  cursor: grabbing;
}

.pp-float-panel__head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px 5px 10px;
  border-bottom: 1px solid color-mix(in oklab, var(--el-border-color) 80%, transparent);
  background: linear-gradient(180deg, var(--el-fill-color-blank) 0%, var(--el-fill-color-light) 100%);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.75) inset;
  cursor: grab;
  flex-shrink: 0;
}

.pp-float-panel__head:active {
  cursor: grabbing;
}

.pp-float-panel__grip {
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.pp-float-panel__title {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pp-float-panel__actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.pp-float-panel__body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 6px 8px 8px;
}
</style>
