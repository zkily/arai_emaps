<template>
  <el-drawer
    :model-value="open"
    :show-close="false"
    size="400px"
    append-to-body
    :z-index="zIndex"
    class="factory-detail-drawer"
    @close="emit('close')"
  >
    <template #header>
      <div class="detail-head">
        <div class="detail-head__titles">
          <span class="detail-head__eyebrow">{{ fl('detail') }}</span>
          <strong>{{ object?.label || fl('unbound') }}</strong>
        </div>
        <button type="button" class="detail-head__close" :aria-label="fl('cancel')" @click="emit('close')">
          ×
        </button>
      </div>
    </template>

    <template v-if="object">
      <div class="detail-hero" :class="{ 'is-ink': darkText }" :style="{ '--accent': color }">
        <span class="detail-hero__glyph" :class="`is-${object.object_type}`" />
        <div class="detail-hero__copy">
          <em>{{ fl(`typeName.${object.object_type}`) }}</em>
          <strong>{{ object.label || fl('unbound') }}</strong>
          <span v-if="object.object_type !== 'workshop'">{{ statusLabel(currentStatus) }}</span>
          <span v-else>{{ childLayoutHint }}</span>
        </div>
      </div>

      <p v-if="selectedCount > 1" class="detail-banner">
        {{ fl('selectionCount', { n: selectedCount }) }}
      </p>

      <section class="detail-card">
        <header class="detail-card__head">{{ fl('sectionBasic') }}</header>
        <div class="detail-card__body">
          <label class="detail-field">
            <span>{{ fl('label') }}</span>
            <el-input
              v-if="editMode"
              ref="labelInputRef"
              :model-value="object.label"
              maxlength="100"
              @focus="emit('historyBegin')"
              @blur="emit('historyEnd')"
              @update:model-value="emit('update-label', $event)"
            />
            <em v-else>{{ object.label || '—' }}</em>
          </label>

          <label v-if="object.object_type === 'machine'" class="detail-field">
            <span>{{ fl('bindMachine') }}</span>
            <el-select
              v-if="editMode"
              :model-value="object.ref_cd || ''"
              filterable
              clearable
              class="detail-field__control"
              :placeholder="fl('unbound')"
              @focus="emit('historyBegin')"
              @blur="emit('historyEnd')"
              @update:model-value="emit('update-ref', $event || null)"
            >
              <el-option
                v-for="item in machines"
                :key="item.cd"
                :label="`${item.cd} ${item.name}`"
                :value="item.cd"
              />
            </el-select>
            <em v-else>{{ object.ref_cd || fl('unbound') }}</em>
          </label>

          <label v-else-if="object.object_type === 'material_zone'" class="detail-field">
            <span>{{ fl('bindLocation') }}</span>
            <el-select
              v-if="editMode"
              :model-value="object.ref_cd || ''"
              filterable
              allow-create
              clearable
              default-first-option
              class="detail-field__control"
              :placeholder="fl('locationPlaceholder')"
              @focus="emit('historyBegin')"
              @blur="emit('historyEnd')"
              @update:model-value="emit('update-ref', $event || null)"
            >
              <el-option v-for="loc in locations" :key="loc" :label="loc" :value="loc" />
            </el-select>
            <em v-else>{{ object.ref_cd || fl('unbound') }}</em>
          </label>
        </div>
      </section>

      <section v-if="object.object_type === 'workshop'" class="detail-card is-accent">
        <header class="detail-card__head">{{ fl('childLayout') }}</header>
        <div class="detail-card__body">
          <label class="detail-field">
            <span>{{ fl('childLayoutSelect') }}</span>
            <el-select
              v-if="editMode"
              :model-value="object.child_layout_id"
              filterable
              clearable
              class="detail-field__control"
              :placeholder="fl('childLayoutNone')"
              @focus="emit('historyBegin')"
              @change="onChildChange"
              @visible-change="onChildVisible"
            >
              <el-option
                v-for="item in childLayouts"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <em v-else>{{ childLayoutName || fl('childLayoutNone') }}</em>
          </label>
          <div class="detail-actions">
            <el-button
              v-if="editMode"
              size="small"
              :loading="creatingChild"
              @click="emit('createChild')"
            >
              {{ fl('createChildLayout') }}
            </el-button>
            <el-button
              size="small"
              type="primary"
              :disabled="!object.child_layout_id"
              @click="emit('enterChild')"
            >
              {{ fl('enterWorkshop') }}
            </el-button>
          </div>
          <p class="detail-hint">{{ fl('childLayoutHint') }}</p>
        </div>
      </section>

      <section v-if="editMode" class="detail-card">
        <header class="detail-card__head">{{ fl('sectionGeometry') }}</header>
        <div class="detail-card__body">
          <div v-if="selectedCount <= 1" class="detail-grid">
            <label class="detail-field">
              <span>X</span>
              <el-input-number
                :model-value="object.x"
                :min="0"
                :step="gridSize"
                size="small"
                controls-position="right"
                class="detail-field__control"
                @change="emitBox('x', $event)"
              />
            </label>
            <label class="detail-field">
              <span>Y</span>
              <el-input-number
                :model-value="object.y"
                :min="0"
                :step="gridSize"
                size="small"
                controls-position="right"
                class="detail-field__control"
                @change="emitBox('y', $event)"
              />
            </label>
            <label class="detail-field">
              <span>W</span>
              <el-input-number
                :model-value="object.width"
                :min="40"
                :step="gridSize"
                size="small"
                controls-position="right"
                class="detail-field__control"
                @change="emitBox('width', $event)"
              />
            </label>
            <label class="detail-field">
              <span>H</span>
              <el-input-number
                :model-value="object.height"
                :min="40"
                :step="gridSize"
                size="small"
                controls-position="right"
                class="detail-field__control"
                @change="emitBox('height', $event)"
              />
            </label>
          </div>
          <div class="detail-row">
            <label class="detail-field is-inline">
              <span>{{ fl('rotation') }}</span>
              <em class="detail-rot">{{ object.rotation || 0 }}°</em>
              <el-button
                size="small"
                :disabled="object.locked && selectedCount <= 1"
                @click="emit('rotate')"
              >
                {{ fl('rotate') }}
              </el-button>
            </label>
            <label class="detail-field is-inline">
              <span>{{ fl('lock') }}</span>
              <el-switch :model-value="object.locked" @change="emit('toggleLock', Boolean($event))" />
            </label>
          </div>
        </div>
      </section>

      <section v-if="editMode" class="detail-card">
        <header class="detail-card__head">{{ fl('sectionStyle') }}</header>
        <div class="detail-card__body">
          <label class="detail-field">
            <span>{{ fl('fill') }}</span>
            <div class="detail-colors">
              <button
                v-for="swatch in FILL_PRESETS"
                :key="swatch"
                type="button"
                class="detail-swatch"
                :class="{ 'is-on': object.fill_color === swatch }"
                :style="{ background: swatch }"
                :disabled="styleLocked"
                @click="emitStyle({ fill_color: swatch })"
              />
              <el-color-picker
                :model-value="object.fill_color || undefined"
                :disabled="styleLocked"
                @change="onFillPicked"
              />
              <el-button
                size="small"
                text
                :disabled="styleLocked || !object.fill_color"
                @click="emitStyle({ fill_color: null })"
              >
                {{ fl('useStatusColor') }}
              </el-button>
            </div>
          </label>
          <label class="detail-field">
            <span>{{ fl('border') }}</span>
            <div class="detail-colors">
              <el-color-picker
                :model-value="object.border_color || undefined"
                :disabled="styleLocked"
                @change="onBorderPicked"
              />
              <el-button
                size="small"
                text
                :disabled="styleLocked || !object.border_color"
                @click="emitStyle({ border_color: null })"
              >
                {{ fl('clearBorder') }}
              </el-button>
            </div>
          </label>
          <label class="detail-field">
            <span>{{ fl('opacity') }}</span>
            <div
              class="detail-opacity"
              @pointerdown="emit('historyBegin')"
              @pointerup="emit('historyEnd')"
              @pointercancel="emit('historyEnd')"
            >
              <el-slider
                :model-value="object.opacity ?? 100"
                :min="10"
                :max="100"
                :disabled="styleLocked"
                :show-tooltip="true"
                @input="onOpacity"
                @change="emit('historyEnd')"
              />
            </div>
          </label>
          <p class="detail-hint">{{ fl('styleHint') }}</p>
        </div>
      </section>

      <section v-if="object.object_type !== 'workshop'" class="detail-card">
        <header class="detail-card__head">{{ fl('sectionStatus') }}</header>
        <div class="detail-card__body">
          <label class="detail-field">
            <span>{{ fl('status') }}</span>
            <el-select
              v-if="canEditStatus"
              v-model="draftStatus"
              class="detail-field__control"
              @change="applyStatus"
            >
              <el-option
                v-for="code in statusOptions"
                :key="code"
                :label="statusLabel(code)"
                :value="code"
              />
            </el-select>
            <span
              v-else
              class="detail-pill"
              :style="{ background: color, color: darkText ? '#1e293b' : '#fff' }"
            >
              {{ statusLabel(currentStatus) }}
            </span>
          </label>
          <label class="detail-field">
            <span>{{ fl('message') }}</span>
            <el-input
              v-if="canEditStatus"
              v-model="draftMessage"
              type="textarea"
              :rows="3"
              maxlength="500"
            />
            <em v-else class="detail-message">{{ status?.message || '—' }}</em>
          </label>
          <div v-if="canEditStatus" class="detail-actions">
            <el-button size="small" type="primary" :loading="savingStatus" @click="applyStatus">
              {{ fl('applyStatus') }}
            </el-button>
          </div>
          <div class="detail-meta">
            <span>{{ fl('source') }} · {{ sourceLabel }}</span>
            <span>{{ fl('updatedAt') }} · {{ updatedText }}</span>
          </div>
          <p v-if="editMode && object.id < 0" class="detail-hint">{{ fl('statusNeedSave') }}</p>
          <p v-else-if="status?.source && status.source !== 'mock'" class="detail-hint">
            {{ fl('plcLocked') }}
          </p>
        </div>
      </section>

      <div v-if="editMode" class="detail-footer">
        <el-button size="small" @click="emit('duplicate')">{{ fl('duplicateObject') }}</el-button>
        <el-button size="small" type="danger" plain @click="emit('delete')">
          {{ fl('deleteObject') }}
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { InputInstance } from 'element-plus'
import dayjs from 'dayjs'
import type { FactoryLayoutObject, FactoryLayoutSummary, ObjectStatus } from '@/api/mes/factoryLayout'
import { fl } from './factoryLayoutJa'
import { FILL_PRESETS, defaultStatus, prefersDarkText, statusColor, statusesFor } from './factoryLayoutMeta'

const props = defineProps<{
  open: boolean
  object: FactoryLayoutObject | null
  status: ObjectStatus | null
  editMode: boolean
  canEdit: boolean
  machines: { cd: string; name: string }[]
  locations: string[]
  childLayouts: FactoryLayoutSummary[]
  creatingChild?: boolean
  savingStatus: boolean
  selectedCount: number
  gridSize: number
  focusLabelNonce?: number
  zIndex?: number
}>()

const emit = defineEmits<{
  close: []
  'update-label': [value: string]
  'update-ref': [value: string | null]
  'update-child': [value: number | null]
  'apply-status': [payload: { status: string; message: string }]
  delete: []
  historyBegin: []
  historyEnd: []
  updateBox: [patch: { x?: number; y?: number; width?: number; height?: number }]
  rotate: []
  toggleLock: [locked: boolean]
  duplicate: []
  updateStyle: [patch: { fill_color?: string | null; border_color?: string | null; opacity?: number }]
  previewStyle: [patch: { opacity: number }]
  createChild: []
  enterChild: []
}>()

const labelInputRef = ref<InputInstance | null>(null)
const draftStatus = ref('')
const draftMessage = ref('')
let childHistoryOpen = false

watch(
  () => [props.open, props.focusLabelNonce, props.editMode, props.object?.id] as const,
  async ([open, , edit]) => {
    if (!open || !edit) return
    await nextTick()
    labelInputRef.value?.focus()
    const native = (labelInputRef.value as { input?: HTMLInputElement } | null)?.input
    native?.select()
  },
)

const currentStatus = computed(() => {
  if (props.status?.status) return props.status.status
  if (!props.object) return ''
  return defaultStatus(props.object.object_type)
})

const statusOptions = computed(() => (props.object ? statusesFor(props.object.object_type) : []))

const canEditStatus = computed(
  () =>
    props.canEdit && !!props.object && props.object.id > 0 && (props.status?.source || 'mock') === 'mock',
)

const styleLocked = computed(() => !!props.object?.locked && props.selectedCount <= 1)

const color = computed(() => props.object?.fill_color || statusColor(currentStatus.value))
const darkText = computed(() => prefersDarkText(color.value))

const childLayoutName = computed(() => {
  const id = props.object?.child_layout_id
  if (!id) return ''
  return props.childLayouts.find((item) => item.id === id)?.name || ''
})

const childLayoutHint = computed(() =>
  childLayoutName.value || (props.object?.child_layout_id ? fl('enterWorkshop') : fl('childLayoutNone')),
)

const sourceLabel = computed(() => {
  const source = props.status?.source || 'mock'
  if (source === 'plc') return fl('sourcePlc')
  return fl('sourceMock')
})

const updatedText = computed(() => {
  const raw = props.status?.updated_at
  if (!raw) return '—'
  const parsed = dayjs(raw)
  return parsed.isValid() ? parsed.format('YYYY-MM-DD HH:mm:ss') : raw
})

watch(
  () => [props.object?.id, props.status?.status, props.status?.message, props.open] as const,
  () => {
    draftStatus.value = currentStatus.value
    draftMessage.value = props.status?.message || ''
  },
  { immediate: true },
)

function statusLabel(code: string) {
  const label = fl(`statusName.${code}`)
  return label === `statusName.${code}` ? code : label
}

function emitBox(key: 'x' | 'y' | 'width' | 'height', value: number | undefined) {
  if (value == null || Number.isNaN(value)) return
  emit('updateBox', { [key]: value })
}

function emitStyle(patch: { fill_color?: string | null; border_color?: string | null; opacity?: number }) {
  if (styleLocked.value) return
  emit('updateStyle', patch)
}

function onFillPicked(value: string | null) {
  emitStyle({ fill_color: value || null })
}

function onBorderPicked(value: string | null) {
  emitStyle({ border_color: value || null })
}

function onOpacity(value: number | number[]) {
  const next = Array.isArray(value) ? value[0] : value
  if (next == null || styleLocked.value) return
  emit('previewStyle', { opacity: next })
}

function onChildVisible(open: boolean) {
  if (open) {
    emit('historyBegin')
    childHistoryOpen = true
  } else if (childHistoryOpen) {
    emit('historyEnd')
    childHistoryOpen = false
  }
}

function onChildChange(value: number | null | undefined) {
  emit('update-child', value ?? null)
  if (childHistoryOpen) {
    emit('historyEnd')
    childHistoryOpen = false
  }
}

function applyStatus() {
  if (!canEditStatus.value || !draftStatus.value) return
  emit('apply-status', { status: draftStatus.value, message: draftMessage.value })
}
</script>

<style scoped>
.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding-right: 4px;
}

.detail-head__titles {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-head__eyebrow {
  font-size: 11px;
  letter-spacing: 0.08em;
  color: #64748b;
  text-transform: uppercase;
}

.detail-head__titles strong {
  font-size: 16px;
  line-height: 1.3;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-head__close {
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 8px;
  background: #f1f5f9;
  color: #475569;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.detail-head__close:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.detail-hero {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  background:
    radial-gradient(120% 140% at 0% 0%, rgba(255, 255, 255, 0.28), transparent 55%),
    linear-gradient(135deg, color-mix(in srgb, var(--accent) 72%, white) 0%, var(--accent) 100%);
  color: #fff;
  box-shadow: 0 12px 28px color-mix(in srgb, var(--accent) 26%, transparent);
}

.detail-hero.is-ink {
  color: #0f172a;
}

.detail-hero__glyph {
  width: 48px;
  height: 32px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 0 0 1.5px rgba(255, 255, 255, 0.5);
}

.detail-hero__glyph.is-machine {
  border-radius: 10px;
}

.detail-hero__glyph.is-aisle {
  height: 16px;
  border-radius: 999px;
}

.detail-hero__glyph.is-material_zone {
  border-radius: 8px;
}

.detail-hero__glyph.is-workshop {
  height: 36px;
  border-radius: 10px 10px 5px 5px;
}

.detail-hero__copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-hero__copy em {
  font-style: normal;
  font-size: 11px;
  letter-spacing: 0.06em;
  opacity: 0.82;
}

.detail-hero__copy strong {
  font-size: 17px;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-hero__copy span {
  font-size: 12px;
  opacity: 0.9;
}

.detail-banner {
  margin: 0 0 12px;
  padding: 8px 12px;
  border-radius: 10px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
}

.detail-card {
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.detail-card.is-accent {
  border-color: #c7d2fe;
  background: linear-gradient(180deg, #f8faff 0%, #fff 48%);
}

.detail-card__head {
  padding: 10px 14px 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #64748b;
}

.detail-card__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 14px 14px;
}

.detail-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.detail-field > span {
  font-size: 12px;
  color: #64748b;
}

.detail-field > em {
  font-style: normal;
  color: #0f172a;
  font-size: 13px;
  line-height: 1.4;
}

.detail-field.is-inline {
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.detail-field.is-inline > span {
  min-width: 48px;
}

.detail-field__control {
  width: 100%;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.detail-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
}

.detail-rot {
  min-width: 36px;
  font-style: normal;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-hint {
  margin: 0;
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.45;
}

.detail-colors {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.detail-swatch {
  width: 20px;
  height: 20px;
  padding: 0;
  border: 1px solid rgba(15, 23, 42, 0.18);
  border-radius: 6px;
  cursor: pointer;
}

.detail-swatch.is-on {
  outline: 2px solid #4f46e5;
  outline-offset: 1px;
}

.detail-swatch:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.detail-opacity {
  width: 100%;
  padding: 0 4px;
}

.detail-pill {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  line-height: 24px;
  width: fit-content;
}

.detail-message {
  white-space: pre-wrap;
}

.detail-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: #94a3b8;
  font-size: 11px;
}

.detail-footer {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 4px;
  padding-top: 4px;
}
</style>

<style>
.factory-detail-drawer .el-drawer__header {
  margin-bottom: 12px;
  padding: 16px 16px 0;
}

.factory-detail-drawer .el-drawer__body {
  padding: 0 16px 20px;
  background:
    linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}
</style>
