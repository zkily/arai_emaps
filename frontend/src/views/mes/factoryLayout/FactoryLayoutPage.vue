<template>
  <div
    ref="pageRef"
    v-loading="loading"
    class="factory-page"
    :class="{ 'is-fullscreen': fullscreen }"
  >
    <div class="factory-page__toolbar">
      <span class="factory-page__mark" />
      <span class="factory-page__title">{{ fl('title') }}</span>
      <el-select
        v-if="!parentLayout && rootLayouts.length"
        :model-value="layoutId"
        size="small"
        class="factory-page__layout"
        @change="onLayoutChange"
      >
        <el-option v-for="item in rootLayouts" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-radio-group
        v-if="canEdit"
        :model-value="editMode ? 'edit' : 'view'"
        size="small"
        @change="onModeChange"
      >
        <el-radio-button value="view">{{ fl('view') }}</el-radio-button>
        <el-radio-button value="edit">{{ fl('edit') }}</el-radio-button>
      </el-radio-group>
      <el-button v-if="canCreate" size="small" @click="openCreate">{{ fl('create') }}</el-button>
      <el-button v-if="canEdit && layoutId" size="small" @click="openCanvasSettings">{{ fl('canvasSettings') }}</el-button>
      <el-button v-if="canCreate && layoutId" size="small" @click="duplicateLayout">{{ fl('duplicateLayout') }}</el-button>
      <el-button
        v-if="canEdit && layoutId"
        size="small"
        type="primary"
        :disabled="!dirty"
        :loading="saving"
        @click="saveObjects"
      >
        {{ fl('save') }}
      </el-button>
      <el-button v-if="layoutId" size="small" :loading="exporting" @click="exportPdf">
        {{ fl('exportPdf') }}
      </el-button>
      <el-button
        v-if="canDelete && layoutId"
        size="small"
        type="danger"
        plain
        @click="removeLayout"
      >
        {{ fl('deleteLayout') }}
      </el-button>
      <div class="factory-page__zoom">
        <el-button size="small" @click="canvasRef?.zoomBy(1 / 1.12)">−</el-button>
        <span>{{ zoomText }}</span>
        <el-button size="small" @click="canvasRef?.zoomBy(1.12)">+</el-button>
      </div>
    </div>

    <div class="factory-page__legend">
      <span class="factory-page__legend-label">{{ fl('legend') }}</span>
      <span v-for="group in legendGroups" :key="group.type" class="factory-page__legend-group">
        <em>{{ fl(`typeName.${group.type}`) }}</em>
        <span v-for="code in group.codes" :key="code" class="factory-page__chip">
          <i :style="{ background: statusColor(code) }" />
          {{ statusLabel(code) }}
        </span>
      </span>
    </div>

    <div v-if="editMode && layoutId" class="factory-page__tools">
      <el-button size="small" :disabled="!canUndo" @click="undo">{{ fl('undo') }}</el-button>
      <el-button size="small" :disabled="!canRedo" @click="redo">{{ fl('redo') }}</el-button>
      <el-button size="small" type="primary" plain :disabled="!selectedIds.length" @click="duplicateSelection">
        {{ fl('duplicateObject') }}
      </el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="copySelection">{{ fl('copy') }}</el-button>
      <el-button size="small" :disabled="!clipboard.length" @click="pasteClipboard">{{ fl('paste') }}</el-button>
      <el-button size="small" type="danger" plain :disabled="!selectedIds.length" @click="removeSelected">
        {{ fl('deleteObject') }}
      </el-button>
      <el-dropdown trigger="click" @command="alignSelection">
        <el-button size="small" :disabled="selectedIds.length < 2">{{ fl('align') }}</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="left">{{ fl('alignLeft') }}</el-dropdown-item>
            <el-dropdown-item command="hcenter">{{ fl('alignHCenter') }}</el-dropdown-item>
            <el-dropdown-item command="right">{{ fl('alignRight') }}</el-dropdown-item>
            <el-dropdown-item command="top">{{ fl('alignTop') }}</el-dropdown-item>
            <el-dropdown-item command="vcenter">{{ fl('alignVCenter') }}</el-dropdown-item>
            <el-dropdown-item command="bottom">{{ fl('alignBottom') }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button size="small" :disabled="selectedIds.length < 3" @click="distributeSelection('x')">
        {{ fl('distributeH') }}
      </el-button>
      <el-button size="small" :disabled="selectedIds.length < 3" @click="distributeSelection('y')">
        {{ fl('distributeV') }}
      </el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="stackSelection('forward')">{{ fl('forward') }}</el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="stackSelection('backward')">{{ fl('backward') }}</el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="stackSelection('front')">{{ fl('toFront') }}</el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="stackSelection('back')">{{ fl('toBack') }}</el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="rotateSelection">{{ fl('rotate') }}</el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="toggleLockSelection()">
        {{ lockActionLabel }}
      </el-button>
      <el-button size="small" :disabled="selectedIds.length < 2" @click="groupSelection">{{ fl('group') }}</el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="ungroupSelection">{{ fl('ungroup') }}</el-button>
      <el-checkbox v-model="snapToGrid" size="small">{{ fl('snap') }}</el-checkbox>
      <el-checkbox v-model="showGrid" size="small">{{ fl('grid') }}</el-checkbox>
      <el-button size="small" @click="selectAll">{{ fl('selectAll') }}</el-button>
      <el-button size="small" :disabled="!selectedIds.length" @click="focusSelection">{{ fl('zoomSelection') }}</el-button>
      <el-button size="small" @click="shortcutsOpen = true">{{ fl('shortcuts') }}</el-button>
    </div>

    <div v-if="!layoutId && !loading" class="factory-page__empty">
      <el-empty :description="fl('empty')">
        <p class="factory-page__empty-hint">{{ fl('emptyHint') }}</p>
        <el-button v-if="canCreate" type="primary" size="small" @click="openCreate">
          {{ fl('create') }}
        </el-button>
      </el-empty>
    </div>

    <div v-else-if="layoutId" class="factory-page__body">
      <aside v-if="editMode" class="factory-page__palette">
        <div class="factory-page__palette-title">{{ fl('palette') }}</div>
        <div
          v-for="type in paletteTypes"
          :key="type"
          class="factory-page__palette-item"
          draggable="true"
          @dragstart="onPaletteDragStart($event, type)"
        >
          <span class="factory-page__glyph" :class="`is-${type}`" />
          {{ fl(`typeName.${type}`) }}
        </div>
        <p class="factory-page__palette-hint">{{ fl('paletteHint') }}</p>
        <div class="factory-page__palette-title">{{ fl('layers') }}</div>
        <div class="factory-page__layers">
          <button
            v-for="item in layerItems"
            :key="item.id"
            type="button"
            class="factory-page__layer"
            :class="{ 'is-on': selectedIds.includes(item.id) }"
            @click="selectLayer(item)"
            @dblclick.stop="openLayerDetail(item)"
          >
            <i
              class="factory-page__dot"
              :style="{ background: item.fill_color || statusColor(statuses[String(item.id)]?.status || defaultStatus(item.object_type)) }"
            />
            <span>{{ item.label }}</span>
            <em v-if="item.locked">{{ fl('lockedMark') }}</em>
          </button>
        </div>
      </aside>
      <div class="factory-page__stage">
        <div class="factory-page__stage-chrome" @pointerdown.stop>
          <div class="factory-page__stage-left">
            <span class="factory-page__stage-kind">
              {{ layoutKind === 'site' ? fl('kindSite') : fl('kindWorkshop') }}
            </span>
            <el-input
              v-if="canvasNaming"
              ref="canvasNameInputRef"
              v-model="renameName"
              size="small"
              maxlength="100"
              class="factory-page__stage-name-input"
              :disabled="renaming"
              @keyup.enter="commitCanvasRename"
              @keyup.esc="cancelCanvasRename"
              @blur="commitCanvasRename"
            />
            <button
              v-else
              type="button"
              class="factory-page__stage-name"
              :disabled="!canEdit"
              :title="canEdit ? fl('rename') : undefined"
              @click="startCanvasRename"
            >
              {{ currentLayoutName || fl('title') }}
            </button>
            <span v-if="parentLayout" class="factory-page__stage-parent">
              {{ parentLayout.name }}
            </span>
          </div>
          <div class="factory-page__stage-right">
            <el-button
              v-if="parentLayout"
              size="small"
              @click="enterLayout(parentLayout.id)"
            >
              {{ fl('backToParent') }}
            </el-button>
            <el-button size="small" @click="canvasRef?.fit()">{{ fl('zoomFit') }}</el-button>
            <el-button
              size="small"
              :type="fullscreen ? 'primary' : 'default'"
              @click="toggleFullscreen"
            >
              {{ fullscreen ? fl('exitFullscreen') : fl('fullscreen') }}
            </el-button>
            <el-button
              v-if="canEdit"
              size="small"
              type="primary"
              :disabled="!dirty"
              :loading="saving"
              @click="saveObjects"
            >
              {{ fl('save') }}
            </el-button>
          </div>
        </div>
        <FactoryCanvas
          ref="canvasRef"
          :canvas-width="canvasWidth"
          :canvas-height="canvasHeight"
          :grid-size="gridSize"
          :edit-mode="editMode"
          :snap-to-grid="snapToGrid"
          :show-grid="showGrid"
          :objects="objects"
          :statuses="statuses"
          :selected-ids="selectedIds"
          @select="onSelect"
          @batch="onBatch"
          @interact-start="onInteractStart"
          @interact-end="onInteractEnd"
          @create="onCreate"
          @zoom="zoomRatio = $event"
          @context="onContext"
          @open-detail="openDetail"
          @hover="onHover"
          @enter="enterLayout"
        />
      </div>
    </div>

    <div
      v-if="hoverTip && hoverObject"
      class="factory-page__hover"
      :style="{ left: `${hoverTip.x}px`, top: `${hoverTip.y}px` }"
    >
      <div class="factory-page__hover-head">
        <em>{{ fl(`typeName.${hoverObject.object_type}`) }}</em>
        <strong>{{ hoverObject.label }}</strong>
      </div>
      <div class="factory-page__hover-status">
        <i :style="{ background: statusColor(hoverStatusCode) }" />
        <span>{{ statusLabel(hoverStatusCode) }}</span>
      </div>
      <p class="factory-page__hover-soon">{{ fl('hoverSoon') }}</p>
    </div>

    <div
      v-if="contextMenu"
      class="factory-page__menu"
      :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
      @pointerdown.stop
      @contextmenu.prevent
    >
      <button type="button" :disabled="!selectedIds.length" @click="runMenu(copySelection)">{{ fl('copy') }}</button>
      <button type="button" :disabled="!clipboard.length" @click="runMenu(pasteClipboard)">{{ fl('paste') }}</button>
      <button type="button" :disabled="!selectedIds.length" @click="runMenu(duplicateSelection)">{{ fl('duplicate') }}</button>
      <button type="button" :disabled="!selectedIds.length" @click="runMenu(removeSelected)">{{ fl('deleteObject') }}</button>
      <button type="button" :disabled="!selectedIds.length" @click="runMenu(rotateSelection)">{{ fl('rotate') }}</button>
      <button type="button" :disabled="!selectedIds.length" @click="runMenu(() => toggleLockSelection())">{{ lockActionLabel }}</button>
      <button type="button" :disabled="selectedIds.length < 2" @click="runMenu(groupSelection)">{{ fl('group') }}</button>
      <button type="button" :disabled="!selectedIds.length" @click="runMenu(ungroupSelection)">{{ fl('ungroup') }}</button>
      <button type="button" :disabled="!selectedIds.length" @click="runMenu(() => stackSelection('front'))">{{ fl('toFront') }}</button>
      <button type="button" :disabled="!selectedIds.length" @click="runMenu(() => stackSelection('back'))">{{ fl('toBack') }}</button>
      <button type="button" :disabled="selectedIds.length !== 1" @click="runMenu(selectSameType)">{{ fl('selectSame') }}</button>
    </div>

    <ObjectDetailDrawer
      :open="drawerOpen && editMode"
      :object="selectedObject"
      :status="selectedStatus"
      :edit-mode="editMode"
      :can-edit="canEdit"
      :machines="machines"
      :locations="locations"
      :child-layouts="childLayoutOptions"
      :creating-child="creatingChild"
      :saving-status="savingStatus"
      :selected-count="selectedIds.length"
      :grid-size="gridSize"
      :focus-label-nonce="focusLabelNonce"
      :z-index="fullscreen ? 5200 : 2000"
      @close="drawerOpen = false"
      @create-child="createSelectedChild"
      @enter-child="enterSelectedChild"
      @update-child="updateSelectedChild"
      @update-label="updateLabel"
      @update-ref="updateRef"
      @apply-status="applyStatus"
      @delete="removeSelected"
      @history-begin="onInteractStart"
      @history-end="onInteractEnd"
      @update-box="updateBox"
      @rotate="rotateSelection"
      @toggle-lock="toggleLockSelection"
      @duplicate="duplicateSelection"
      @update-style="updateStyle"
      @preview-style="previewStyle"
    />

    <el-dialog v-model="canvasOpen" :title="fl('canvasSettings')" width="420px" :z-index="fullscreen ? 5300 : undefined">
      <el-form label-width="88px" size="small">
        <el-form-item :label="fl('canvasWidth')">
          <el-input-number v-model="canvasDraft.width" :min="400" :max="8000" :step="20" />
        </el-form-item>
        <el-form-item :label="fl('canvasHeight')">
          <el-input-number v-model="canvasDraft.height" :min="300" :max="8000" :step="20" />
        </el-form-item>
        <el-form-item :label="fl('gridSize')">
          <el-input-number v-model="canvasDraft.grid" :min="8" :max="80" :step="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="canvasOpen = false">{{ fl('cancel') }}</el-button>
        <el-button size="small" type="primary" :loading="savingCanvas" @click="confirmCanvas">
          {{ fl('confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="shortcutsOpen" :title="fl('shortcuts')" width="460px" :z-index="fullscreen ? 5300 : undefined">
      <ul class="factory-page__shortcuts">
        <li v-for="item in shortcutRows" :key="item.keys">
          <kbd>{{ item.keys }}</kbd>
          <span>{{ item.label }}</span>
        </li>
      </ul>
    </el-dialog>

    <el-dialog v-model="createOpen" :title="fl('createTitle')" width="380px" :z-index="fullscreen ? 5300 : undefined">
      <el-form label-width="72px" size="small" @submit.prevent>
        <el-form-item :label="fl('name')">
          <el-input v-model="createName" maxlength="100" @keyup.enter="confirmCreate" />
        </el-form-item>
        <el-form-item :label="fl('type')">
          <el-radio-group v-model="createKind">
            <el-radio value="site">{{ fl('kindSite') }}</el-radio>
            <el-radio value="workshop">{{ fl('kindWorkshop') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="createOpen = false">{{ fl('cancel') }}</el-button>
        <el-button size="small" type="primary" :loading="creating" @click="confirmCreate">
          {{ fl('confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { InputInstance } from 'element-plus'
import { getMachineList } from '@/api/master/machineMaster'
import {
  createFactoryLayout,
  deleteFactoryLayout,
  getFactoryLayout,
  getFactoryLayoutStatus,
  listFactoryLayouts,
  listFactoryStorageLocations,
  normalizeLayoutObject,
  saveFactoryLayoutObjects,
  updateFactoryLayout,
  updateFactoryObjectStatus,
  type FactoryLayoutObject,
  type FactoryLayoutSummary,
  type LayoutKind,
  type LayoutObjectType,
  type ObjectStatus,
} from '@/api/mes/factoryLayout'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import FactoryCanvas from './FactoryCanvas.vue'
import ObjectDetailDrawer from './ObjectDetailDrawer.vue'
import { exportFactoryLayoutPdf } from './exportFactoryLayoutPdf'
import {
  alignObjects,
  distributeObjects,
  nudgeObjects,
  objectBounds,
  rotateObjects,
  setLocked,
  stackObjects,
  type AlignMode,
  type StackAction,
} from './editorOps'
import { fl } from './factoryLayoutJa'
import { defaultSize, defaultStatus, defaultZ, statusColor, statusesFor, widthForLabel } from './factoryLayoutMeta'

defineOptions({ name: 'FactoryLayoutPage' })
const { canCreate, canEdit, canDelete } = useMesOperationPermission()

const loading = ref(false)
const saving = ref(false)
const exporting = ref(false)
const creating = ref(false)
const creatingChild = ref(false)
const savingStatus = ref(false)
const layouts = ref<FactoryLayoutSummary[]>([])
const layoutId = ref<number | null>(null)
const layoutKind = ref<LayoutKind>('workshop')
const layoutParentId = ref<number | null>(null)
const appliedId = ref<number | null>(null)
const canvasWidth = ref(1600)
const canvasHeight = ref(900)
const gridSize = ref(20)
const objects = ref<FactoryLayoutObject[]>([])
const statuses = ref<Record<string, ObjectStatus>>({})
const editMode = ref(false)
const dirty = ref(false)
const selectedId = ref<number | null>(null)
const selectedIds = ref<number[]>([])
const drawerOpen = ref(false)
const focusLabelNonce = ref(0)
const hoverTip = ref<{ id: number; x: number; y: number } | null>(null)
const snapToGrid = ref(true)
const showGrid = ref(true)
const historyPast = ref<string[]>([])
const historyFuture = ref<string[]>([])
const clipboard = ref<FactoryLayoutObject[]>([])
const contextMenu = ref<{ x: number; y: number; id: number | null } | null>(null)
const renameName = ref('')
const renaming = ref(false)
const canvasNaming = ref(false)
const canvasNameInputRef = ref<InputInstance | null>(null)
let canvasRenameBusy = false
const canvasOpen = ref(false)
const savingCanvas = ref(false)
const canvasDraft = ref({ width: 1600, height: 900, grid: 20 })
const shortcutsOpen = ref(false)
let historyBefore = ''
const machines = ref<{ cd: string; name: string }[]>([])
const locations = ref<string[]>([])
const createOpen = ref(false)
const createName = ref('')
const createKind = ref<LayoutKind>('site')
const canvasRef = ref<InstanceType<typeof FactoryCanvas> | null>(null)
const pageRef = ref<HTMLElement | null>(null)
const fullscreen = ref(false)
const zoomRatio = ref(1)

let tempSeq = -1

function newGroupKey() {
  const cryptoRef = globalThis.crypto
  if (cryptoRef && typeof cryptoRef.randomUUID === 'function') return cryptoRef.randomUUID()
  return `g${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`
}
let pollTimer: ReturnType<typeof setInterval> | null = null

const paletteTypes = computed<LayoutObjectType[]>(() =>
  layoutKind.value === 'site' ? ['workshop', 'aisle'] : ['machine', 'aisle', 'material_zone'],
)

const rootLayouts = computed(() => layouts.value.filter((item) => !item.parent_id))

const parentLayout = computed(() =>
  layoutParentId.value == null
    ? null
    : layouts.value.find((item) => item.id === layoutParentId.value) || null,
)

const currentLayoutName = computed(
  () => layouts.value.find((item) => item.id === layoutId.value)?.name || '',
)

const legendGroups = computed(() =>
  paletteTypes.value
    .map((type) => ({ type, codes: statusesFor(type) }))
    .filter((group) => group.codes.length > 0),
)

const zoomText = computed(() => `${Math.round(zoomRatio.value * 100)}%`)

const selectedObject = computed(
  () => objects.value.find((item) => item.id === selectedId.value) || null,
)

const childLayoutOptions = computed(() => {
  const current = layoutId.value
  const selectedChildId = selectedObject.value?.child_layout_id
  const list = layouts.value
    .filter((item) => item.id !== current && (item.kind !== 'site' || item.id === selectedChildId))
    .slice()
    .sort((a, b) => {
      const ap = a.parent_id === current ? 0 : 1
      const bp = b.parent_id === current ? 0 : 1
      if (ap !== bp) return ap - bp
      return a.name.localeCompare(b.name, 'ja')
    })
  if (selectedChildId && !list.some((item) => item.id === selectedChildId)) {
    const orphan = layouts.value.find((item) => item.id === selectedChildId)
    if (orphan) list.unshift(orphan)
  }
  return list
})

const selectedObjects = computed(() =>
  objects.value.filter((item) => selectedIds.value.includes(item.id)),
)

const layerItems = computed(() =>
  [...objects.value].sort((a, b) => b.z_index - a.z_index || b.id - a.id),
)

const canUndo = computed(() => historyPast.value.length > 0)
const canRedo = computed(() => historyFuture.value.length > 0)

const lockActionLabel = computed(() =>
  selectedObjects.value.some((item) => !item.locked)
    ? fl('lock')
    : fl('unlock'),
)

const shortcutRows = computed(() => [
  { keys: 'F / Esc', label: fl('fullscreen') + ' / ' + fl('exitFullscreen') },
  { keys: 'Double-click', label: fl('editContentHint') },
  { keys: 'Ctrl+Z / Ctrl+Y', label: fl('undo') + ' / ' + fl('redo') },
  { keys: 'Ctrl+C / V / D', label: fl('copy') + ' / ' + fl('paste') + ' / ' + fl('duplicate') },
  { keys: 'Ctrl+A', label: fl('selectAll') },
  { keys: 'Ctrl+G', label: fl('group') },
  { keys: 'Delete', label: fl('deleteObject') },
  { keys: '↑↓←→', label: fl('nudgeHint') },
  { keys: 'Space', label: fl('panHint') },
  { keys: 'Shift', label: fl('shiftHint') },
])

const selectedStatus = computed(() => {
  if (selectedId.value == null) return null
  return statuses.value[String(selectedId.value)] || null
})

const hoverObject = computed(() => {
  if (!hoverTip.value) return null
  return objects.value.find((item) => item.id === hoverTip.value!.id) || null
})

const hoverStatusCode = computed(() => {
  if (!hoverObject.value) return ''
  return statuses.value[String(hoverObject.value.id)]?.status || defaultStatus(hoverObject.value.object_type)
})

function statusLabel(code: string) {
  const label = fl(`statusName.${code}`)
  return label === `statusName.${code}` ? code : label
}

function toastIfSilent(error: unknown, fallback: string) {
  const status = (error as { response?: { status?: number } })?.response?.status
  if (!status || status >= 500) ElMessage.error(fallback)
}

function snap(value: number) {
  const grid = gridSize.value || 20
  return Math.round(value / grid) * grid
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

async function loadLists() {
  try {
    const res = await getMachineList({ pageSize: 9999 })
    const list = res.data?.list || res.list || []
    machines.value = list.map((item) => ({
      cd: item.machine_cd,
      name: item.machine_name || item.machine_cd,
    }))
  } catch {
    machines.value = []
  }
  try {
    locations.value = await listFactoryStorageLocations()
  } catch {
    locations.value = []
  }
}

async function loadStatus(silent = false) {
  if (layoutId.value == null) return
  try {
    const res = await getFactoryLayoutStatus(layoutId.value)
    statuses.value = res.statuses || {}
  } catch (error) {
    if (!silent) toastIfSilent(error, fl('loadFailed'))
  }
}

async function loadDetail(id: number) {
  loading.value = true
  try {
    const detail = await getFactoryLayout(id)
    layoutId.value = detail.id
    appliedId.value = detail.id
    canvasWidth.value = detail.canvas_width
    canvasHeight.value = detail.canvas_height
    gridSize.value = detail.grid_size
    objects.value = expandObjectsForLabels((detail.objects || []).map(normalizeLayoutObject))
    layoutKind.value = detail.kind || 'workshop'
    layoutParentId.value = detail.parent_id ?? null
    dirty.value = false
    historyPast.value = []
    historyFuture.value = []
    historyBefore = ''
    selectedId.value = null
    selectedIds.value = []
    drawerOpen.value = false
    hoverTip.value = null
    contextMenu.value = null
    editMode.value = false
    await loadStatus()
  } catch (error) {
    toastIfSilent(error, fl('loadFailed'))
  } finally {
    loading.value = false
  }
}

async function loadLayouts(preferId?: number) {
  loading.value = true
  try {
    layouts.value = (await listFactoryLayouts()).map((item) => ({
      ...item,
      kind: item.kind || 'workshop',
      parent_id: item.parent_id ?? null,
    }))
    const siteId = layouts.value.find((item) => item.kind === 'site')?.id
    const next =
      (preferId && layouts.value.some((item) => item.id === preferId) && preferId) ||
      siteId ||
      layouts.value.find((item) => !item.parent_id)?.id ||
      layouts.value[0]?.id ||
      null
    if (next == null) {
      layoutId.value = null
      appliedId.value = null
      objects.value = []
      statuses.value = {}
      return
    }
    await loadDetail(next)
  } catch (error) {
    toastIfSilent(error, fl('loadFailed'))
  } finally {
    loading.value = false
  }
}

async function onLayoutChange(next: number) {
  if (dirty.value && appliedId.value != null && next !== appliedId.value) {
    try {
      await ElMessageBox.confirm(fl('unsavedSwitch'), fl('title'), {
        type: 'warning',
        confirmButtonText: fl('confirm'),
        cancelButtonText: fl('cancel'),
      })
    } catch {
      layoutId.value = appliedId.value
      return
    }
  }
  await loadDetail(next)
}

function openCreate() {
  createName.value = ''
  createKind.value = layouts.value.some((item) => item.kind === 'site') ? 'workshop' : 'site'
  createOpen.value = true
}

async function confirmCreate() {
  const name = createName.value.trim()
  if (!name) {
    ElMessage.warning(fl('nameRequired'))
    return
  }
  creating.value = true
  try {
    const created = await createFactoryLayout({ name, kind: createKind.value })
    createOpen.value = false
    ElMessage.success(fl('created'))
    await loadLayouts(created.id)
    if (canEdit.value) editMode.value = true
  } catch (error) {
    toastIfSilent(error, fl('saveFailed'))
  } finally {
    creating.value = false
  }
}

async function enterLayout(id: number) {
  if (id === layoutId.value) return
  if (dirty.value) {
    await saveObjects()
    if (dirty.value) return
  }
  drawerOpen.value = false
  hoverTip.value = null
  await loadDetail(id)
  await nextTick()
  canvasRef.value?.fit()
}

async function createSelectedChild() {
  const item = selectedObject.value
  if (!item || item.object_type !== 'workshop' || layoutId.value == null) return
  creatingChild.value = true
  try {
    const created = await createFactoryLayout({
      name: item.label || fl('typeName.workshop'),
      kind: 'workshop',
      parent_id: layoutId.value,
    })
    const before = snapshotObjects()
    item.child_layout_id = created.id
    layouts.value = [
      ...layouts.value,
      {
        id: created.id,
        name: created.name,
        canvas_width: created.canvas_width,
        canvas_height: created.canvas_height,
        grid_size: created.grid_size,
        kind: created.kind || 'workshop',
        parent_id: created.parent_id ?? layoutId.value,
      },
    ]
    dirty.value = true
    commitHistory(before)
    ElMessage.success(fl('childLayoutCreated'))
  } catch (error) {
    toastIfSilent(error, fl('saveFailed'))
  } finally {
    creatingChild.value = false
  }
}

function updateSelectedChild(id: number | null) {
  const item = selectedObject.value
  if (!item || item.object_type !== 'workshop') return
  item.child_layout_id = id
  dirty.value = true
}

function enterSelectedChild() {
  const id = selectedObject.value?.child_layout_id
  if (id) void enterLayout(id)
}

async function removeLayout() {
  if (layoutId.value == null) return
  try {
    await ElMessageBox.confirm(fl('deleteLayoutConfirm'), fl('title'), {
      type: 'warning',
      confirmButtonText: fl('confirm'),
      cancelButtonText: fl('cancel'),
    })
  } catch {
    return
  }
  try {
    await deleteFactoryLayout(layoutId.value)
    ElMessage.success(fl('deleted'))
    await loadLayouts()
  } catch (error) {
    toastIfSilent(error, fl('saveFailed'))
  }
}

function snapshotObjects() {
  return JSON.stringify(objects.value)
}

function commitHistory(before: string) {
  const now = snapshotObjects()
  if (!before || before === now) return
  historyPast.value.push(before)
  if (historyPast.value.length > 80) historyPast.value.shift()
  historyFuture.value = []
  dirty.value = true
}

function restoreSnapshot(raw: string) {
  const parsed = JSON.parse(raw) as FactoryLayoutObject[]
  objects.value = expandObjectsForLabels(parsed.map(normalizeLayoutObject))
  selectedIds.value = selectedIds.value.filter((id) => objects.value.some((item) => item.id === id))
  if (selectedId.value != null && !selectedIds.value.includes(selectedId.value)) {
    selectedId.value = selectedIds.value[0] ?? null
  }
  if (selectedId.value == null) drawerOpen.value = false
  dirty.value = true
}

function undo() {
  const prev = historyPast.value.pop()
  if (!prev) return
  historyFuture.value.push(snapshotObjects())
  restoreSnapshot(prev)
}

function redo() {
  const next = historyFuture.value.pop()
  if (!next) return
  historyPast.value.push(snapshotObjects())
  restoreSnapshot(next)
}

function onInteractStart() {
  if (!historyBefore) historyBefore = snapshotObjects()
}

function onInteractEnd() {
  if (!historyBefore) return
  commitHistory(historyBefore)
  historyBefore = ''
}

function mergeObjects(updated: FactoryLayoutObject[]) {
  const map = new Map(updated.map((item) => [item.id, item]))
  objects.value = objects.value.map((item) => map.get(item.id) ?? item)
}

function changeSelection(mutator: (list: FactoryLayoutObject[]) => FactoryLayoutObject[]) {
  const before = snapshotObjects()
  mergeObjects(mutator(selectedObjects.value.map((item) => ({ ...item }))))
  commitHistory(before)
}

function onModeChange(value: string | number | boolean) {
  editMode.value = value === 'edit'
  hoverTip.value = null
  if (!editMode.value) drawerOpen.value = false
}

async function setFullscreen(next: boolean) {
  fullscreen.value = next
  if (typeof document !== 'undefined') {
    document.body.classList.toggle('factory-layout-body--fullscreen', next)
  }
  if (next) {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen()
    } catch {
      /* CSS fallback */
    }
  } else if (document.fullscreenElement) {
    try {
      await document.exitFullscreen()
    } catch {
      /* ignore */
    }
  }
  await nextTick()
  canvasRef.value?.fit()
}

async function toggleFullscreen() {
  await setFullscreen(!fullscreen.value)
}

function onBrowserFullscreenChange() {
  if (!document.fullscreenElement && fullscreen.value) {
    fullscreen.value = false
    document.body.classList.remove('factory-layout-body--fullscreen')
    void nextTick(() => canvasRef.value?.fit())
  }
}

function onSelect(ids: number[], primary: number | null) {
  selectedIds.value = ids
  selectedId.value = primary
  if (!editMode.value) drawerOpen.value = false
  contextMenu.value = null
  hoverTip.value = null
}

function onHover(payload: { id: number; clientX: number; clientY: number } | null) {
  if (editMode.value || !payload) {
    hoverTip.value = null
    return
  }
  hoverTip.value = {
    id: payload.id,
    x: Math.min(payload.clientX + 14, window.innerWidth - 240),
    y: Math.min(payload.clientY + 14, window.innerHeight - 140),
  }
}

function openDetail() {
  if (selectedId.value == null) return
  if (!editMode.value) {
    if (!canEdit.value) return
    editMode.value = true
  }
  hoverTip.value = null
  drawerOpen.value = true
  focusLabelNonce.value += 1
}

function onBatch(patches: { id: number; x?: number; y?: number; width?: number; height?: number }[]) {
  const map = new Map(patches.map((item) => [item.id, item]))
  objects.value.forEach((item) => {
    const patch = map.get(item.id)
    if (!patch) return
    if (patch.x != null) item.x = patch.x
    if (patch.y != null) item.y = patch.y
    if (patch.width != null) item.width = patch.width
    if (patch.height != null) item.height = patch.height
    const next = expandForLabel(item)
    if (next.width !== item.width) item.width = next.width
  })
  dirty.value = true
}

function onCreate(payload: { objectType: LayoutObjectType; x: number; y: number }) {
  const size = defaultSize(payload.objectType)
  const count = objects.value.filter((item) => item.object_type === payload.objectType).length + 1
  let x = snap(payload.x)
  let y = snap(payload.y)
  x = clamp(x, 0, Math.max(0, canvasWidth.value - size.width))
  y = clamp(y, 0, Math.max(0, canvasHeight.value - size.height))
  const created: FactoryLayoutObject = expandForLabel({
    id: tempSeq--,
    layout_id: layoutId.value || 0,
    object_type: payload.objectType,
    x,
    y,
    width: size.width,
    height: size.height,
    label: `${fl(`typeName.${payload.objectType}`)} ${count}`,
    ref_cd: null,
    z_index: defaultZ(payload.objectType),
    rotation: 0,
    locked: false,
    group_key: null,
    fill_color: null,
    border_color: null,
    opacity: 100,
    child_layout_id: null,
  })
  x = clamp(created.x, 0, Math.max(0, canvasWidth.value - created.width))
  created.x = x
  const before = snapshotObjects()
  objects.value.push(created)
  statuses.value = {
    ...statuses.value,
    [String(created.id)]: {
      status: defaultStatus(payload.objectType),
      message: '',
      updated_at: null,
      source: 'mock',
      payload: null,
    },
  }
  commitHistory(before)
  onSelect([created.id], created.id)
}

function onPaletteDragStart(event: DragEvent, type: LayoutObjectType) {
  event.dataTransfer?.setData('application/x-factory-object', type)
  event.dataTransfer?.setData('text/plain', type)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'copy'
}

function expandForLabel(item: FactoryLayoutObject): FactoryLayoutObject {
  const width = Math.min(
    widthForLabel(item.label, item.width),
    Math.max(40, canvasWidth.value - item.x),
  )
  return width === item.width ? item : { ...item, width }
}

function expandObjectsForLabels(list: FactoryLayoutObject[]) {
  return list.map(expandForLabel)
}

function updateLabel(value: string) {
  if (!selectedObject.value || selectedObject.value.locked) return
  selectedObject.value.label = value
  const next = expandForLabel(selectedObject.value)
  if (next.width !== selectedObject.value.width) selectedObject.value.width = next.width
  dirty.value = true
}

function updateRef(value: string | null) {
  if (!selectedObject.value || selectedObject.value.locked) return
  selectedObject.value.ref_cd = value
  dirty.value = true
}

function updateBox(patch: { x?: number; y?: number; width?: number; height?: number }) {
  if (!selectedObject.value || selectedObject.value.locked) return
  const before = snapshotObjects()
  Object.assign(selectedObject.value, patch)
  const next = expandForLabel(selectedObject.value)
  if (next.width !== selectedObject.value.width) selectedObject.value.width = next.width
  commitHistory(before)
}

function applyStyle(
  patch: { fill_color?: string | null; border_color?: string | null; opacity?: number },
  record: boolean,
) {
  const targets = selectedObjects.value.filter((item) => !item.locked)
  if (!targets.length) return
  const before = record ? snapshotObjects() : ''
  for (const item of targets) Object.assign(item, patch)
  dirty.value = true
  if (record) commitHistory(before)
}

function updateStyle(patch: { fill_color?: string | null; border_color?: string | null; opacity?: number }) {
  applyStyle(patch, true)
}

function previewStyle(patch: { opacity: number }) {
  applyStyle(patch, false)
}

function removeSelected() {
  const victims = selectedObjects.value.filter((item) => !item.locked)
  if (!victims.length) {
    if (selectedIds.value.length) ElMessage.warning(fl('lockedSkip'))
    return
  }
  const before = snapshotObjects()
  const drop = new Set(victims.map((item) => item.id))
  objects.value = objects.value.filter((item) => !drop.has(item.id))
  const next = { ...statuses.value }
  drop.forEach((id) => delete next[String(id)])
  statuses.value = next
  selectedIds.value = selectedIds.value.filter((id) => !drop.has(id))
  selectedId.value = selectedIds.value[0] ?? null
  if (selectedId.value == null) drawerOpen.value = false
  commitHistory(before)
  contextMenu.value = null
}

async function exportPdf() {
  const svg = canvasRef.value?.getSvgElement()
  if (!svg || layoutId.value == null) return
  const current = layouts.value.find((item) => item.id === layoutId.value)
  exporting.value = true
  try {
    await exportFactoryLayoutPdf({
      svg,
      canvasWidth: canvasWidth.value,
      canvasHeight: canvasHeight.value,
      title: current?.name || fl('title'),
      exportedAtLabel: fl('exportedAt'),
      legend: legendGroups.value.map((group) => ({
        title: fl(`typeName.${group.type}`),
        items: group.codes.map((code) => ({
          label: statusLabel(code),
          color: statusColor(code),
        })),
      })),
    })
    ElMessage.success(fl('exported'))
  } catch (error) {
    toastIfSilent(error, fl('exportFailed'))
  } finally {
    exporting.value = false
  }
}

async function saveObjects() {
  if (layoutId.value == null) return
  const previous = selectedObject.value
  saving.value = true
  try {
    const saved = await saveFactoryLayoutObjects(
      layoutId.value,
      objects.value.map((item) => ({
        id: item.id > 0 ? item.id : null,
        object_type: item.object_type,
        x: item.x,
        y: item.y,
        width: item.width,
        height: item.height,
        label: item.label,
        ref_cd: item.ref_cd,
        z_index: item.z_index,
        rotation: item.rotation || 0,
        locked: item.locked,
        group_key: item.group_key,
        fill_color: item.fill_color,
        border_color: item.border_color,
        opacity: item.opacity ?? 100,
        child_layout_id: item.child_layout_id,
      })),
    )
    objects.value = expandObjectsForLabels(saved.map(normalizeLayoutObject))
    dirty.value = false
    if (previous && previous.id < 0) {
      const match = saved.find(
        (item) =>
          item.object_type === previous.object_type &&
          item.x === previous.x &&
          item.y === previous.y &&
          item.label === previous.label,
      )
      selectedId.value = match?.id ?? null
    } else if (previous && !saved.some((item) => item.id === previous.id)) {
      selectedId.value = null
    }
    if (selectedId.value == null) drawerOpen.value = false
    await loadStatus()
    ElMessage.success(fl('saved'))
  } catch (error) {
    toastIfSilent(error, fl('saveFailed'))
  } finally {
    saving.value = false
  }
}

async function applyStatus(payload: { status: string; message: string }) {
  if (selectedId.value == null || selectedId.value < 0) return
  savingStatus.value = true
  try {
    const updated = await updateFactoryObjectStatus(selectedId.value, payload)
    statuses.value = { ...statuses.value, [String(selectedId.value)]: updated }
    ElMessage.success(fl('statusSaved'))
  } catch (error) {
    toastIfSilent(error, fl('statusFailed'))
  } finally {
    savingStatus.value = false
  }
}

function typingTarget(event: KeyboardEvent) {
  const tag = (event.target as HTMLElement | null)?.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || (event.target as HTMLElement | null)?.isContentEditable
}

function alignSelection(mode: AlignMode) {
  if (selectedObjects.value.length < 2) return
  changeSelection((list) => alignObjects(list, mode))
}

function distributeSelection(axis: 'x' | 'y') {
  if (selectedObjects.value.length < 3) return
  changeSelection((list) => distributeObjects(list, axis))
}

function stackSelection(action: StackAction) {
  if (!selectedIds.value.length) return
  const before = snapshotObjects()
  objects.value = stackObjects(objects.value, selectedIds.value, action)
  commitHistory(before)
}

function rotateSelection() {
  if (!selectedIds.value.length) return
  changeSelection((list) => rotateObjects(list))
}

function toggleLockSelection(locked?: boolean) {
  if (!selectedIds.value.length) return
  const next = typeof locked === 'boolean' ? locked : selectedObjects.value.some((item) => !item.locked)
  changeSelection((list) => setLocked(list, next))
}

function groupSelection() {
  if (selectedIds.value.length < 2) return
  const key = newGroupKey()
  changeSelection((list) => list.map((item) => ({ ...item, group_key: key })))
}

function ungroupSelection() {
  if (!selectedIds.value.length) return
  changeSelection((list) => list.map((item) => ({ ...item, group_key: null })))
}

function selectLayer(item: FactoryLayoutObject) {
  const ids = item.group_key
    ? objects.value.filter((row) => row.group_key === item.group_key).map((row) => row.id)
    : [item.id]
  onSelect(ids, item.id)
}

function openLayerDetail(item: FactoryLayoutObject) {
  selectLayer(item)
  openDetail()
}

function selectAll() {
  const ids = objects.value.map((item) => item.id)
  onSelect(ids, ids[ids.length - 1] ?? null)
}

function selectSameType() {
  const current = selectedObject.value
  if (!current) return
  const ids = objects.value.filter((item) => item.object_type === current.object_type).map((item) => item.id)
  onSelect(ids, current.id)
}

function focusSelection() {
  if (!selectedObjects.value.length) return
  const box = objectBounds(selectedObjects.value)
  canvasRef.value?.focusRect(box.x, box.y, box.width, box.height)
}

function copySelection() {
  if (!selectedObjects.value.length) return
  clipboard.value = selectedObjects.value.map((item) => ({ ...item }))
  contextMenu.value = null
  ElMessage.success(fl('objectCopied'))
}

function placeCopies(source: FactoryLayoutObject[], offset: number) {
  const before = snapshotObjects()
  const groupMap = new Map<string, string>()
  const created = source.map((item) => {
    let groupKey = item.group_key
    if (groupKey) {
      if (!groupMap.has(groupKey)) groupMap.set(groupKey, newGroupKey())
      groupKey = groupMap.get(groupKey) || null
    }
    return expandForLabel({
      ...item,
      id: tempSeq--,
      x: clamp(item.x + offset, 0, Math.max(0, canvasWidth.value - item.width)),
      y: clamp(item.y + offset, 0, Math.max(0, canvasHeight.value - item.height)),
      locked: false,
      group_key: groupKey,
      child_layout_id: item.object_type === 'workshop' ? null : item.child_layout_id,
    })
  })
  objects.value.push(...created)
  const nextStatus = { ...statuses.value }
  created.forEach((item, index) => {
    const sourceId = source[index]?.id
    const from = sourceId != null ? statuses.value[String(sourceId)] : null
    nextStatus[String(item.id)] = {
      status: from?.status || defaultStatus(item.object_type),
      message: from?.message || '',
      updated_at: null,
      source: 'mock',
      payload: from?.payload ?? null,
    }
  })
  statuses.value = nextStatus
  commitHistory(before)
  onSelect(created.map((item) => item.id), created[created.length - 1]?.id ?? null)
  return created
}

function pasteClipboard() {
  if (!clipboard.value.length) return
  placeCopies(clipboard.value, gridSize.value || 20)
  contextMenu.value = null
}

function duplicateSelection() {
  if (!selectedObjects.value.length) return
  const keepDrawer = drawerOpen.value
  placeCopies(selectedObjects.value, gridSize.value || 20)
  ElMessage.success(fl('objectDuplicated'))
  if (keepDrawer) openDetail()
}

function onContext(payload: { clientX: number; clientY: number; id: number | null }) {
  if (payload.id != null && !selectedIds.value.includes(payload.id)) {
    const obj = objects.value.find((item) => item.id === payload.id)
    const ids = obj?.group_key
      ? objects.value.filter((item) => item.group_key === obj.group_key).map((item) => item.id)
      : [payload.id]
    selectedIds.value = ids
    selectedId.value = payload.id
  }
  contextMenu.value = {
    x: Math.min(payload.clientX, window.innerWidth - 180),
    y: Math.min(payload.clientY, window.innerHeight - 320),
    id: payload.id,
  }
}

function runMenu(action: () => void) {
  action()
  contextMenu.value = null
}

async function startCanvasRename() {
  if (!canEdit.value || canvasNaming.value) return
  renameName.value = currentLayoutName.value || ''
  canvasNaming.value = true
  await nextTick()
  canvasNameInputRef.value?.focus()
  const native = (canvasNameInputRef.value as { input?: HTMLInputElement } | null)?.input
  native?.select()
}

function cancelCanvasRename() {
  canvasNaming.value = false
  renameName.value = currentLayoutName.value || ''
}

async function commitCanvasRename() {
  if (!canvasNaming.value || canvasRenameBusy) return
  const name = renameName.value.trim()
  const current = currentLayoutName.value
  if (!name || name === current) {
    canvasNaming.value = false
    renameName.value = current
    return
  }
  if (layoutId.value == null) {
    canvasNaming.value = false
    return
  }
  canvasRenameBusy = true
  renaming.value = true
  try {
    const updated = await updateFactoryLayout(layoutId.value, { name })
    layouts.value = layouts.value.map((item) => (item.id === updated.id ? { ...item, name: updated.name } : item))
    canvasNaming.value = false
    ElMessage.success(fl('renamed'))
  } catch (error) {
    toastIfSilent(error, fl('saveFailed'))
  } finally {
    renaming.value = false
    canvasRenameBusy = false
  }
}

function openCanvasSettings() {
  canvasDraft.value = { width: canvasWidth.value, height: canvasHeight.value, grid: gridSize.value }
  canvasOpen.value = true
}

async function confirmCanvas() {
  if (layoutId.value == null) return
  savingCanvas.value = true
  try {
    const updated = await updateFactoryLayout(layoutId.value, {
      canvas_width: canvasDraft.value.width,
      canvas_height: canvasDraft.value.height,
      grid_size: canvasDraft.value.grid,
    })
    canvasWidth.value = updated.canvas_width
    canvasHeight.value = updated.canvas_height
    gridSize.value = updated.grid_size
    layouts.value = layouts.value.map((item) => (item.id === updated.id ? { ...item, ...updated } : item))
    const before = snapshotObjects()
    objects.value = objects.value.map((item) => ({
      ...item,
      x: clamp(item.x, 0, Math.max(0, canvasWidth.value - item.width)),
      y: clamp(item.y, 0, Math.max(0, canvasHeight.value - item.height)),
    }))
    commitHistory(before)
    canvasOpen.value = false
    ElMessage.success(fl('saved'))
  } catch (error) {
    toastIfSilent(error, fl('saveFailed'))
  } finally {
    savingCanvas.value = false
  }
}

async function duplicateLayout() {
  if (layoutId.value == null) return
  const current = layouts.value.find((item) => item.id === layoutId.value)
  creating.value = true
  try {
    const created = await createFactoryLayout({
      name: `${current?.name || fl('title')} ${fl('copySuffix')}`,
      canvas_width: canvasWidth.value,
      canvas_height: canvasHeight.value,
      grid_size: gridSize.value,
      kind: current?.kind || 'workshop',
    })
    if (objects.value.length) {
      await saveFactoryLayoutObjects(
        created.id,
        objects.value.map((item) => ({
          id: null,
          object_type: item.object_type,
          x: item.x,
          y: item.y,
          width: item.width,
          height: item.height,
          label: item.label,
          ref_cd: item.ref_cd,
          z_index: item.z_index,
          rotation: item.rotation || 0,
          locked: item.locked,
          group_key: item.group_key,
          fill_color: item.fill_color,
          border_color: item.border_color,
          opacity: item.opacity ?? 100,
          child_layout_id: item.object_type === 'workshop' ? null : item.child_layout_id,
        })),
      )
    }
    ElMessage.success(fl('duplicated'))
    await loadLayouts(created.id)
    if (canEdit.value) editMode.value = true
  } catch (error) {
    toastIfSilent(error, fl('saveFailed'))
  } finally {
    creating.value = false
  }
}

function closeContextMenu() {
  contextMenu.value = null
}

function onKeyDown(event: KeyboardEvent) {
  if (typingTarget(event)) return
  const key = event.key.toLowerCase()
  const mod = event.ctrlKey || event.metaKey

  if (event.key === 'Escape' && fullscreen.value) {
    event.preventDefault()
    void setFullscreen(false)
    return
  }
  if (!mod && !event.altKey && key === 'f') {
    event.preventDefault()
    void toggleFullscreen()
    return
  }

  if (!editMode.value) return
  if (mod && key === 'z') {
    event.preventDefault()
    if (event.shiftKey) redo()
    else undo()
    return
  }
  if (mod && key === 'y') {
    event.preventDefault()
    redo()
    return
  }
  if (mod && key === 'c') {
    event.preventDefault()
    copySelection()
    return
  }
  if (mod && key === 'v') {
    event.preventDefault()
    pasteClipboard()
    return
  }
  if (mod && key === 'd') {
    event.preventDefault()
    duplicateSelection()
    return
  }
  if (mod && key === 'a') {
    event.preventDefault()
    selectAll()
    return
  }
  if (mod && key === 'g') {
    event.preventDefault()
    if (event.shiftKey) ungroupSelection()
    else groupSelection()
    return
  }
  if (event.key === 'Escape') {
    onSelect([], null)
    return
  }
  if ((event.key === 'Delete' || event.key === 'Backspace') && selectedIds.value.length) {
    event.preventDefault()
    removeSelected()
    return
  }
  const step = event.shiftKey ? (gridSize.value || 20) * 2 : snapToGrid.value ? gridSize.value || 20 : 1
  const delta: Record<string, [number, number]> = {
    ArrowLeft: [-step, 0],
    ArrowRight: [step, 0],
    ArrowUp: [0, -step],
    ArrowDown: [0, step],
  }
  const move = delta[event.key]
  if (move && selectedIds.value.length) {
    event.preventDefault()
    const before = snapshotObjects()
    const moved = nudgeObjects(selectedObjects.value, move[0], move[1], canvasWidth.value, canvasHeight.value)
    mergeObjects(moved)
    commitHistory(before)
  }
}

onMounted(() => {
  void loadLayouts()
  void loadLists()
  pollTimer = setInterval(() => {
    void loadStatus(true)
  }, 5000)
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('pointerdown', closeContextMenu)
  document.addEventListener('fullscreenchange', onBrowserFullscreenChange)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('pointerdown', closeContextMenu)
  document.removeEventListener('fullscreenchange', onBrowserFullscreenChange)
  document.body.classList.remove('factory-layout-body--fullscreen')
  if (document.fullscreenElement) {
    void document.exitFullscreen().catch(() => undefined)
  }
})
</script>

<style scoped>
.factory-page {
  height: calc(100vh - 96px);
  min-height: 520px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px 14px;
  box-sizing: border-box;
  background:
    radial-gradient(900px 280px at 0% -10%, rgba(79, 70, 229, 0.08), transparent 55%),
    linear-gradient(180deg, #f4f7fb 0%, #eef2f7 100%);
}

.factory-page.is-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 4000;
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  padding: 12px 14px 14px;
  background:
    radial-gradient(1100px 320px at 0% -10%, rgba(79, 70, 229, 0.1), transparent 55%),
    linear-gradient(180deg, #f4f7fb 0%, #e8eef6 100%);
}

.factory-page.is-fullscreen .factory-page__hover,
.factory-page.is-fullscreen .factory-page__menu {
  z-index: 5100;
}

.factory-page__toolbar,
.factory-page__legend,
.factory-page__zoom {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.factory-page__toolbar,
.factory-page__legend,
.factory-page__tools {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
  padding: 8px 10px;
}

.factory-page__mark {
  width: 10px;
  height: 22px;
  border-radius: 999px;
  background: linear-gradient(180deg, #6366f1 0%, #0ea5e9 100%);
  box-shadow: 0 4px 10px rgba(79, 70, 229, 0.35);
}

.factory-page__title {
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 0.01em;
  color: #0f172a;
}

.factory-page__layout {
  width: 180px;
}

.factory-page__zoom {
  margin-left: auto;
  gap: 6px;
}

.factory-page__zoom span {
  min-width: 42px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  color: #475569;
  font-size: 12px;
}

.factory-page__legend {
  gap: 8px 12px;
  font-size: 12px;
  color: #475569;
}

.factory-page__legend-label {
  font-weight: 600;
}

.factory-page__legend-group {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.factory-page__legend-group em {
  font-style: normal;
  font-weight: 700;
  color: #64748b;
}

.factory-page__chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px 3px 6px;
  border-radius: 999px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.factory-page__chip i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
}

.factory-page__body {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 8px;
}

.factory-page__stage {
  position: relative;
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
}

.factory-page__stage-chrome {
  position: absolute;
  z-index: 6;
  top: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  pointer-events: none;
}

.factory-page__stage-left,
.factory-page__stage-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  pointer-events: auto;
}

.factory-page__stage-right {
  justify-content: flex-end;
  padding: 4px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.1);
  border: 1px solid rgba(226, 232, 240, 0.95);
}

.factory-page__stage-left {
  min-width: 0;
  max-width: min(520px, calc(100% - 280px));
  padding: 6px 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.1);
  border: 1px solid rgba(226, 232, 240, 0.95);
}

.factory-page__stage-kind {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef2ff;
  color: #4338ca;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.factory-page__stage-name {
  min-width: 0;
  max-width: 280px;
  padding: 2px 6px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #0f172a;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.3;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}

.factory-page__stage-name:not(:disabled) {
  cursor: pointer;
}

.factory-page__stage-name:not(:disabled):hover {
  background: #f1f5f9;
}

.factory-page__stage-name-input {
  width: 220px;
}

.factory-page__stage-parent {
  min-width: 0;
  max-width: 140px;
  color: #64748b;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.factory-page__stage-parent::before {
  content: '← ';
}

.factory-page__palette {
  width: 196px;
  flex-shrink: 0;
  min-height: 0;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

.factory-page__palette-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.factory-page__palette-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: grab;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.factory-page__palette-item:hover {
  border-color: #c7d2fe;
  box-shadow: 0 8px 16px rgba(79, 70, 229, 0.08);
  transform: translateY(-1px);
}

.factory-page__glyph {
  width: 28px;
  height: 18px;
  flex-shrink: 0;
  position: relative;
}

.factory-page__glyph.is-machine {
  border-radius: 6px;
  background: linear-gradient(180deg, #4ade80 0%, #16a34a 100%);
  box-shadow: inset 0 6px 0 rgba(255, 255, 255, 0.28);
}

.factory-page__glyph.is-aisle {
  height: 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, #38bdf8 0%, #0284c7 100%);
}

.factory-page__glyph.is-aisle::after {
  content: '';
  position: absolute;
  left: 4px;
  right: 4px;
  top: 5px;
  border-top: 2px dashed rgba(255, 255, 255, 0.85);
}

.factory-page__glyph.is-material_zone {
  border-radius: 5px;
  background: linear-gradient(180deg, #2dd4bf 0%, #0f766e 100%);
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.45);
}

.factory-page__glyph.is-workshop {
  border-radius: 6px 6px 4px 4px;
  background: linear-gradient(180deg, #818cf8 0%, #4338ca 100%);
  box-shadow: inset 0 -6px 0 rgba(15, 23, 42, 0.18);
}

.factory-page__crumb {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.factory-page__palette-hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  color: #94a3b8;
}

.factory-page__empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.05);
}

.factory-page__empty-hint {
  margin: 0 0 10px;
  color: #64748b;
  font-size: 13px;
}

.factory-page__tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.factory-page__layers {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: auto;
  min-height: 0;
}

.factory-page__layer {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 10px;
  padding: 6px 8px;
  cursor: pointer;
  text-align: left;
  font-size: 12px;
  color: #0f172a;
}

.factory-page__layer:hover {
  background: #f8fafc;
}

.factory-page__layer.is-on {
  background: #eef2ff;
  border-color: #c7d2fe;
}

.factory-page__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
}

.factory-page__layer span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.factory-page__layer em {
  margin-left: auto;
  font-style: normal;
  color: #94a3b8;
}

.factory-page__hover {
  position: fixed;
  z-index: 2800;
  width: 220px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.16);
  pointer-events: none;
  backdrop-filter: blur(8px);
}

.factory-page__hover-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 8px;
}

.factory-page__hover-head em {
  font-style: normal;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #64748b;
}

.factory-page__hover-head strong {
  font-size: 14px;
  color: #0f172a;
  line-height: 1.3;
  word-break: break-word;
}

.factory-page__hover-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #334155;
}

.factory-page__hover-status i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.factory-page__hover-soon {
  margin: 0;
  padding-top: 8px;
  border-top: 1px dashed #e2e8f0;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.4;
}

.factory-page__menu {
  position: fixed;
  z-index: 3000;
  min-width: 168px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 12px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.factory-page__menu button {
  border: 0;
  background: transparent;
  text-align: left;
  padding: 7px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #0f172a;
}

.factory-page__menu button:hover:not(:disabled) {
  background: #f1f5f9;
}

.factory-page__menu button:disabled {
  color: #cbd5e1;
  cursor: not-allowed;
}

.factory-page__shortcuts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.factory-page__shortcuts li {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
}

.factory-page__shortcuts kbd {
  min-width: 120px;
  font-family: inherit;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-bottom-width: 2px;
  border-radius: 8px;
  padding: 3px 8px;
  color: #334155;
}
</style>

<style>
body.factory-layout-body--fullscreen {
  overflow: hidden;
}
</style>
