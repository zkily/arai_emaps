<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowLeft,
  ArrowRight,
  Calendar,
  CircleCheck,
  Clock,
  DataLine,
  Minus,
  Plus,
  User,
  VideoPause,
  VideoPlay,
} from '@element-plus/icons-vue'
import { setLocale, type LocaleType } from '@/i18n'
import { formatDateTimeJST, localeForIntl } from '@/utils/dateFormat'
import { formatDurationMs, parseDefectsFromRow } from './inspectionActualPersist'
import { useInspectionMesCollection, type InspectionMgmtRow } from './useInspectionMesCollection'

defineOptions({ name: 'InspectionActualDataCollection' })

const { t, locale } = useI18n()
const mes = useInspectionMesCollection()
const {
  INSPECTION_DEFECT_ITEMS,
  productionDay,
  inspectorUserId,
  selectedProductCode,
  activeRow,
  hideCompleted,
  products,
  inspectors,
  completedRows,
  loadingProducts,
  loadingInspectors,
  loadingPlans,
  endDialogVisible,
  endDialogQty,
  endDialogSubmitting,
  defectTotal,
  canStart,
  canPause,
  canResume,
  canEnd,
  canEditDefects,
  showOfflineAlert,
  offlineAlertText,
  endDialogPreview,
  shiftProductionDay,
  setProductionDayToday,
  onStartProduction,
  onPauseProduction,
  onResumeProduction,
  openEndDialog,
  closeEndDialog,
  submitProductionEnd,
  defectCount,
  bumpDefect,
  defectRowsForRecord,
  workSession,
  formatElapsed,
  operationDisplayMs,
  pausedAccumMs,
  timerPhase,
  timerPhaseLabel,
  formatWall,
  init,
  teardownLifecycle,
} = mes

/** タブレット/スマホでは filterable オフ（タップでソフトキーボードを出さない） */
const touchSelectFilterable = ref(true)
let touchSelectMq: MediaQueryList | null = null

function syncTouchSelectFilterable(): void {
  if (typeof window === 'undefined') return
  touchSelectFilterable.value = !window.matchMedia('(hover: none) and (pointer: coarse)').matches
}

function onMesSelectVisibleChange(): void {
  if (touchSelectFilterable.value) return
  nextTick(() => {
    const ae = document.activeElement
    if (ae instanceof HTMLInputElement) ae.blur()
  })
}

const localeUi = ref<LocaleType>((locale.value as LocaleType) || 'ja')
watch(localeUi, (v) => setLocale(v))
watch(
  () => locale.value,
  (v) => {
    if (v === 'en' || v === 'ja' || v === 'zh' || v === 'vi') localeUi.value = v
  },
)
const intlLocale = computed(() => localeForIntl(localeUi.value))

const selectedProduct = computed(() => {
  const code = selectedProductCode.value
  if (!code) return null
  return products.value.find((p) => p.product_code === code) ?? null
})

const displayProductCd = computed(
  () => activeRow.value?.product_cd ?? selectedProduct.value?.product_code ?? '—',
)
const displayProductName = computed(
  () => activeRow.value?.product_name ?? selectedProduct.value?.product_name ?? '—',
)

const currentSession = computed(() => workSession())

function formatRecordTime(val: string | number | null | undefined): string {
  if (val == null) return '-'
  return formatDateTimeJST(typeof val === 'number' ? new Date(val) : val, intlLocale.value, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function inspectorNameForUserId(userId: number | null | undefined): string {
  if (userId == null) return '-'
  const u = inspectors.value.find((x) => x.id === userId)
  return (u?.full_name || u?.username || '').trim() || '-'
}

function formatDurationSec(sec: number | null | undefined): string {
  return formatDurationMs(Math.max(0, (sec ?? 0) * 1000))
}

function defectRowsForHistory(rec: InspectionMgmtRow) {
  return defectRowsForRecord(parseDefectsFromRow(rec.mes_defect_by_item))
}

function formatDefectsCell(rec: InspectionMgmtRow): string {
  const rows = defectRowsForHistory(rec)
  if (!rows.length) return '—'
  return rows.map((r) => `${r.label} ${r.qty}`).join('、')
}

const localeIconOptions: { value: LocaleType; label: string; glyph: string }[] = [
  { value: 'ja', label: 'JP', glyph: 'JP' },
  { value: 'en', label: 'EN', glyph: 'EN' },
  { value: 'zh', label: 'ZH', glyph: 'ZH' },
  { value: 'vi', label: 'VI', glyph: 'VI' },
]

onMounted(async () => {
  syncTouchSelectFilterable()
  if (typeof window !== 'undefined') {
    touchSelectMq = window.matchMedia('(hover: none) and (pointer: coarse)')
    touchSelectMq.addEventListener('change', syncTouchSelectFilterable)
  }
  await init()
})

onUnmounted(() => {
  touchSelectMq?.removeEventListener('change', syncTouchSelectFilterable)
  teardownLifecycle()
})
</script>


<template>

  <div class="inspection-actual-page">
    <header class="page-head">
      <div class="page-head-row">
        <div class="page-head-main">
          <h1 class="page-title">
            <span class="page-title__icon" aria-hidden="true">
              <el-icon><DataLine /></el-icon>
            </span>
            <span class="page-title__text">{{ t('mesInspectionActual.title') }}</span>
          </h1>
        </div>
        <div
          class="page-head-locale"
          role="radiogroup"
          :aria-label="t('mesInspectionActual.localeInline')"
        >
          <el-tooltip
            v-for="opt in localeIconOptions"
            :key="opt.value"
            :content="opt.label"
            placement="bottom"
          >
            <button
              type="button"
              role="radio"
              class="locale-glyph-btn"
              :class="{ 'locale-glyph-btn--active': localeUi === opt.value }"
              :aria-label="opt.label"
              :aria-checked="localeUi === opt.value"
              @click="localeUi = opt.value"
            >
              <span class="locale-glyph-btn__glyph" aria-hidden="true">{{ opt.glyph }}</span>
            </button>
          </el-tooltip>
        </div>
      </div>
    </header>

    <el-card shadow="never" class="toolbar-card" role="region" :aria-label="t('mesInspectionActual.title')">
      <div class="toolbar-layout">
        <div class="toolbar-field-row toolbar-field-row--day">
          <span class="toolbar-field-row__icon" aria-hidden="true">
            <el-icon><Calendar /></el-icon>
          </span>
          <span class="toolbar-field-row__label">{{ t('mesInspectionActual.productionDay') }}</span>
          <div class="toolbar-day-wrap">
            <el-date-picker
              v-model="productionDay"
              type="date"
              value-format="YYYY-MM-DD"
              :editable="false"
              teleported
              class="toolbar-control toolbar-day-picker"
            />
            <div class="toolbar-day-shortcuts">
              <el-tooltip :content="t('mesInspectionActual.dayPrev')" placement="top">
                <el-button
                  type="default"
                  size="small"
                  circle
                  :icon="ArrowLeft"
                  :aria-label="t('mesInspectionActual.dayPrev')"
                  @click="shiftProductionDay(-1)"
                />
              </el-tooltip>
              <el-button
                type="default"
                size="small"
                plain
                class="toolbar-day-today-btn"
                @click="setProductionDayToday"
              >
                {{ t('mesInspectionActual.dayToday') }}
              </el-button>
              <el-tooltip :content="t('mesInspectionActual.dayNext')" placement="top">
                <el-button
                  type="default"
                  size="small"
                  circle
                  :icon="ArrowRight"
                  :aria-label="t('mesInspectionActual.dayNext')"
                  @click="shiftProductionDay(1)"
                />
              </el-tooltip>
            </div>
          </div>
        </div>

        <div class="toolbar-field-row toolbar-field-row--inspector">
          <span class="toolbar-field-row__icon" aria-hidden="true">
            <el-icon><User /></el-icon>
          </span>
          <span class="toolbar-field-row__label">{{ t('mesInspectionActual.inspector') }}</span>
          <el-select
            v-model="inspectorUserId"
            :filterable="touchSelectFilterable"
            clearable
            teleported
            class="toolbar-control toolbar-inspector-select"
            :placeholder="t('mesInspectionActual.inspectorPlaceholder')"
            :loading="loadingInspectors"
            @visible-change="onMesSelectVisibleChange"
          >
            <el-option
              v-for="u in inspectors"
              :key="u.id"
              :label="u.full_name || u.username"
              :value="u.id"
            />
          </el-select>
        </div>

        <div class="toolbar-field-row toolbar-field-row--product">
          <span class="toolbar-field-row__icon toolbar-field-row__icon--machine" aria-hidden="true">
            <el-icon><DataLine /></el-icon>
          </span>
          <span class="toolbar-field-row__label">{{ t('mesInspectionActual.selectProduct') }}</span>
          <el-select
            v-model="selectedProductCode"
            :filterable="touchSelectFilterable"
            clearable
            teleported
            class="toolbar-control product-select-toolbar"
            :placeholder="t('mesInspectionActual.productPlaceholder')"
            :loading="loadingProducts"
            :disabled="canEnd"
            @visible-change="onMesSelectVisibleChange"
          >
            <el-option
              v-for="p in products"
              :key="p.product_code"
              :label="`${p.product_code} · ${p.product_name}`"
              :value="p.product_code"
            />
          </el-select>
        </div>

        <div
          class="toolbar-field-row toolbar-field-row--switch toolbar-filter-switch"
          :class="{ 'toolbar-filter-switch--active': hideCompleted }"
        >
          <span class="toolbar-field-row__label toolbar-filter-switch__text">{{
            t('mesInspectionActual.hideCompleted')
          }}</span>
          <el-switch
            v-model="hideCompleted"
            class="toolbar-filter-switch__control"
            inline-prompt
            :active-text="t('mesInspectionActual.filterSwitchOn')"
            :inactive-text="t('mesInspectionActual.filterSwitchOff')"
          />
        </div>
      </div>
    </el-card>

    <div v-if="showOfflineAlert" class="offline-strip" role="status">
      <span class="offline-strip__dot" aria-hidden="true" />
      {{ offlineAlertText }}
    </div>

    <div v-loading="loadingPlans" class="plan-board">
      <template v-if="!selectedProductCode">
        <el-empty :description="t('mesInspectionActual.emptySelectProduct')" />
      </template>
      <template v-else>
      <el-card shadow="hover" class="plan-row-card">
        <div class="plan-row">
          <div class="plan-row__head">
            <el-tag size="small" effect="plain" type="primary">{{ displayProductCd }}</el-tag>
            <el-tag
              v-if="currentSession"
              size="small"
              effect="plain"
              :type="
                timerPhase(currentSession) === 'running'
                  ? 'success'
                  : timerPhase(currentSession) === 'paused'
                    ? 'warning'
                    : 'info'
              "
            >
              {{ timerPhaseLabel(currentSession) }}
            </el-tag>
          </div>

          <div class="plan-row__meta">
            <div class="plan-meta-primary">
              <span class="plan-product-name" :title="displayProductName || ''">{{
                displayProductName || '—'
              }}</span>
            </div>
            <div class="plan-meta-chips">
              <span class="plan-chip plan-chip--qty">
                <span class="plan-chip__label">{{ t('mesInspectionActual.defectTotal') }}</span>
                <span class="plan-chip__value">{{ defectTotal }}</span>
              </span>
              <div class="plan-meta-field plan-meta-field--operator">
              <span class="plan-meta-field__label">
                <el-icon class="plan-meta-field__icon" aria-hidden="true"><User /></el-icon>
                {{ t('mesInspectionActual.inspector') }}
              </span>
              <el-select
                v-model="inspectorUserId"
                :filterable="touchSelectFilterable"
                clearable
                teleported
                :disabled="canEnd"
                :placeholder="t('mesInspectionActual.inspectorPlaceholder')"
                :loading="loadingInspectors"
                class="plan-field__control plan-field__control--operator"
                @visible-change="onMesSelectVisibleChange"
              >
                <el-option
                  v-for="u in inspectors"
                  :key="u.id"
                  :label="u.full_name || u.username"
                  :value="u.id"
                />
              </el-select>
              </div>
            </div>
          </div>

          <div class="plan-row__ops">
            <div class="plan-row__timer">
              <div
                class="timer-compact"
                :class="`timer-compact--${currentSession ? timerPhase(currentSession) : 'idle'}`"
              >
                <div class="timer-compact__top">
                  <span class="timer-compact__label">
                    <el-icon class="timer-compact__label-icon" aria-hidden="true"><Clock /></el-icon>
                    {{ t('mesInspectionActual.elapsed') }}
                  </span>
                  <span class="timer-compact__phase">{{
                    currentSession ? timerPhaseLabel(currentSession) : t('mesInspectionActual.timerIdle')
                  }}</span>
                </div>
                <div class="timer-compact__readout-row">
                  <div
                    class="timer-compact__readout"
                    :class="{
                      'timer-compact__readout--display-frozen':
                        currentSession && timerPhase(currentSession) === 'paused',
                    }"
                  >
                    {{ formatElapsed(currentSession ? operationDisplayMs(currentSession) : 0) }}
                  </div>
                  <div v-if="currentSession?.wallStart != null" class="timer-compact__pause-side">
                    <span class="timer-compact__pause-label">{{ t('mesInspectionActual.pausedAccum') }}</span>
                    <span class="timer-compact__pause-value">{{
                      formatElapsed(pausedAccumMs(currentSession))
                    }}</span>
                  </div>
                </div>
                <div class="timer-compact__walls">
                  <span>{{ formatWall(currentSession?.wallStart ?? null) }}</span>
                  <span class="timer-compact__sep">→</span>
                  <span>{{ formatWall(currentSession?.wallEnd ?? null) }}</span>
                </div>
              </div>
            </div>
            <div class="plan-row__actions">
              <el-button
                class="plan-act-btn plan-act-btn--start"
                :disabled="!canStart"
                @click="onStartProduction"
              >
                <el-icon><VideoPlay /></el-icon>
                {{ t('mesInspectionActual.btnStart') }}
              </el-button>
              <el-button
                v-if="canPause"
                class="plan-act-btn plan-act-btn--pause"
                @click="onPauseProduction"
              >
                <el-icon><VideoPause /></el-icon>
                {{ t('mesInspectionActual.btnPause') }}
              </el-button>
              <el-button
                v-else-if="canResume"
                class="plan-act-btn plan-act-btn--resume"
                @click="onResumeProduction"
              >
                <el-icon><VideoPlay /></el-icon>
                {{ t('mesInspectionActual.btnResume') }}
              </el-button>
              <el-button v-else class="plan-act-btn plan-act-btn--pause" disabled>
                <el-icon><VideoPause /></el-icon>
                {{ t('mesInspectionActual.btnPause') }}
              </el-button>
              <el-button
                class="plan-act-btn plan-act-btn--end"
                :disabled="!canEnd"
                @click="openEndDialog"
              >
                <el-icon><CircleCheck /></el-icon>
                {{ t('mesInspectionActual.btnEnd') }}
              </el-button>
            </div>
          </div>

          <div class="defect-panel">
            <div class="defect-panel__head">
              <h3 class="defect-panel__title">{{ t('mesInspectionActual.defectByItem') }}</h3>
              <p class="defect-panel__hint">{{ t('mesInspectionActual.defectHint') }}</p>
            </div>
            <div class="defect-grid">
              <div
                v-for="item in INSPECTION_DEFECT_ITEMS"
                :key="item.id"
                class="defect-cell"
                :class="{ 'defect-cell--active': defectCount(item.id) > 0 }"
              >
                <span class="defect-cell__label">{{ t(`mesInspectionActual.${item.labelKey}`) }}</span>
                <div class="defect-stepper">
                  <el-button
                    class="defect-stepper__btn"
                    circle
                    :icon="Minus"
                    :disabled="defectCount(item.id) <= 0 || !canEditDefects"
                    @click="bumpDefect(item.id, -1)"
                  />
                  <span class="defect-stepper__val">{{ defectCount(item.id) }}</span>
                  <el-button
                    class="defect-stepper__btn"
                    circle
                    type="primary"
                    :icon="Plus"
                    :disabled="!canEditDefects"
                    @click="bumpDefect(item.id, 1)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
      </template>

      <section v-if="!hideCompleted && completedRows.length > 0" class="inspection-history-section">
        <el-card shadow="never" class="inspection-history-table-card">
          <header class="inspection-history-table-card__head">
            <div class="inspection-history-table-card__title-row">
              <span class="inspection-history-table-card__icon" aria-hidden="true">
                <el-icon :size="18"><CircleCheck /></el-icon>
              </span>
              <h2 class="inspection-history-table-card__title">
                {{ t('mesInspectionActual.historyTitle') }}
              </h2>
            </div>
            <span class="inspection-history-table-card__count">
              {{ completedRows.length }}
            </span>
          </header>
          <div class="inspection-history-table-wrap">
            <el-table
              :data="completedRows"
              stripe
              size="small"
              class="inspection-history-table"
              row-key="id"
            >
              <el-table-column
                :label="t('mesInspectionActual.historyColProductCd')"
                min-width="104"
                fixed="left"
              >
                <template #default="{ row }">
                  <span class="hist-cell-code">{{ row.product_cd || '—' }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.productName')"
                min-width="148"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span class="hist-cell-name">{{ row.product_name || '—' }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.inspector')"
                min-width="100"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span class="hist-cell-inspector">
                    <el-icon class="hist-cell-inspector__icon" aria-hidden="true"><User /></el-icon>
                    {{ inspectorNameForUserId(row.mes_inspector_user_id) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.productionQty')"
                width="92"
                align="right"
              >
                <template #default="{ row }">
                  <span class="hist-cell-qty">{{
                    (row.actual_production_quantity ?? 0).toLocaleString()
                  }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.productionStart')"
                min-width="118"
              >
                <template #default="{ row }">
                  <span class="hist-cell-time">{{ formatRecordTime(row.mes_production_started_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.productionEnd')"
                min-width="118"
              >
                <template #default="{ row }">
                  <span class="hist-cell-time">{{ formatRecordTime(row.mes_production_ended_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.elapsed')"
                width="92"
                align="right"
              >
                <template #default="{ row }">
                  <span class="hist-cell-duration hist-cell-duration--active">{{
                    formatDurationSec(row.mes_net_production_sec)
                  }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.pausedAccum')"
                width="92"
                align="right"
              >
                <template #default="{ row }">
                  <span
                    class="hist-cell-duration"
                    :class="{ 'hist-cell-duration--muted': !(row.mes_paused_accum_sec ?? 0) }"
                  >
                    {{ formatDurationSec(row.mes_paused_accum_sec) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.defectByItem')"
                min-width="140"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <div v-if="defectRowsForHistory(row).length" class="hist-cell-defects">
                    <el-tag
                      v-for="d in defectRowsForHistory(row)"
                      :key="d.id"
                      size="small"
                      type="warning"
                      effect="plain"
                      class="hist-cell-defects__tag"
                    >
                      {{ d.label }} <strong>{{ d.qty }}</strong>
                    </el-tag>
                  </div>
                  <span v-else class="hist-cell-empty">—</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </section>
    </div>

    <el-dialog
      v-model="endDialogVisible"
      :title="t('mesInspectionActual.endDialogTitle')"
      width="480px"
      append-to-body
      destroy-on-close
      align-center
      class="production-end-dialog"
      @close="closeEndDialog"
    >
      <div v-if="endDialogPreview" class="end-dialog-body">
        <p class="end-dialog-product">{{ displayProductCd }} · {{ displayProductName }}</p>
        <div class="end-dialog-meta">
          <div class="end-dialog-meta-item">
            <span class="end-dialog-meta-label">{{ t('mesInspectionActual.inspector') }}</span>
            <span class="end-dialog-meta-value">{{ endDialogPreview.inspectorName }}</span>
          </div>
          <div class="end-dialog-meta-item">
            <span class="end-dialog-meta-label">{{ t('mesInspectionActual.productionStart') }}</span>
            <span class="end-dialog-meta-value">{{ formatRecordTime(endDialogPreview.wallStart) }}</span>
          </div>
          <div class="end-dialog-meta-item">
            <span class="end-dialog-meta-label">{{ t('mesInspectionActual.productionEnd') }}</span>
            <span class="end-dialog-meta-value">{{ formatRecordTime(endDialogPreview.wallEnd) }}</span>
          </div>
        </div>
        <div v-if="endDialogPreview.defectTotal > 0" class="end-dialog-field">
          <span class="end-dialog-label">{{ t('mesInspectionActual.defectByItem') }}</span>
          <ul class="history-defects">
            <li v-for="row in defectRowsForRecord(endDialogPreview.defects)" :key="row.id">
              <span>{{ row.label }}</span>
              <strong>{{ row.qty }}</strong>
            </li>
          </ul>
        </div>
        <div class="end-dialog-field">
          <span class="end-dialog-label">{{ t('mesInspectionActual.productionQty') }}</span>
          <el-input
            v-model="endDialogQty"
            class="end-dialog-input"
            inputmode="numeric"
            :placeholder="t('mesInspectionActual.productionQtyPlaceholder')"
            clearable
            @keyup.enter="submitProductionEnd"
          />
        </div>
        <div class="end-dialog-actions">
          <el-button
            class="end-dialog-btn end-dialog-btn--full"
            type="primary"
            :loading="endDialogSubmitting"
            @click="submitProductionEnd"
          >
            {{ t('mesInspectionActual.btnConfirmEnd') }}
          </el-button>
          <el-button class="end-dialog-btn end-dialog-btn--cancel" :disabled="endDialogSubmitting" @click="closeEndDialog">
            {{ t('common.cancel') }}
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.inspection-actual-page {
  --ca-radius: 10px;
  --ca-gap: 8px;
  padding: 10px 12px 16px;
  padding-bottom: max(16px, env(safe-area-inset-bottom, 0px));
  max-width: min(1680px, 100%);
  margin: 0 auto;
  box-sizing: border-box;
  background: var(--el-bg-color-page);
}

.page-head {
  margin-bottom: 8px;
}

.page-head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px 16px;
}

.page-head-main {
  flex: 1 1 240px;
  min-width: 0;
}

.page-head-locale {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.locale-glyph-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease,
    box-shadow 0.15s ease;
}

.locale-glyph-btn:hover {
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}

.locale-glyph-btn--active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 700;
  box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
}

.locale-glyph-btn__glyph {
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  line-height: 1.25;
}

.page-title__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  color: #fff;
  background: linear-gradient(
    135deg,
    var(--el-color-primary) 0%,
    #38bdf8 48%,
    var(--el-color-success) 100%
  );
  box-shadow:
    0 4px 14px rgba(64, 158, 255, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.page-head:hover .page-title__icon {
  transform: translateY(-1px) scale(1.03);
  box-shadow:
    0 6px 18px rgba(64, 158, 255, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.page-title__icon .el-icon {
  font-size: 20px;
}

.page-title__text {
  color: var(--el-text-color-primary);
}

.offline-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--el-color-warning-dark-2);
  background: var(--el-color-warning-light-9);
  border: 1px solid var(--el-color-warning-light-5);
}

.offline-strip__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--el-color-warning);
  flex-shrink: 0;
  animation: offline-pulse 1.4s ease-in-out infinite;
}

@keyframes offline-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.35;
  }
}

.toolbar-card {
  --toolbar-h: 36px;
  --toolbar-day-picker-w: 150px;
  --toolbar-machine-select-w: 115px;
  --toolbar-machine-gap: 6px;
  --toolbar-day-gap: 5px;
  --toolbar-day-shortcut-size: 28px;
  --toolbar-day-today-min-w: 36px;
  border-radius: var(--ca-radius);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.toolbar-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.toolbar-layout {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
}

.toolbar-field-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  min-height: var(--toolbar-h);
}

.toolbar-field-row__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: var(--toolbar-h);
  height: var(--toolbar-h);
  border-radius: 8px;
  font-size: 16px;
  color: #fff;
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #38bdf8 100%);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.28);
}

.toolbar-field-row__label {
  flex-shrink: 0;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.toolbar-field-row--day {
  flex: 0 1 auto;
  max-width: max-content;
  padding: 0 8px 0 0;
  gap: 6px;
  border-radius: 10px;
  border: 1px solid var(--el-color-primary-light-7);
  background: linear-gradient(
    165deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 55%,
    var(--el-fill-color-light) 100%
  );
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.toolbar-field-row--day .toolbar-field-row__icon {
  margin-left: -1px;
  border-radius: 9px 0 0 9px;
}

.toolbar-field-row--day .toolbar-field-row__label {
  color: var(--el-color-primary-dark-2);
}

.toolbar-control :deep(.el-input__wrapper),
.toolbar-control :deep(.el-select__wrapper) {
  min-height: var(--toolbar-h);
  height: var(--toolbar-h);
  box-sizing: border-box;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.toolbar-control :deep(.el-input__inner) {
  height: calc(var(--toolbar-h) - 2px);
  line-height: calc(var(--toolbar-h) - 2px);
}

.toolbar-day-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--toolbar-day-gap);
  flex: 0 0 auto;
  max-width: calc(
    var(--toolbar-day-picker-w) + var(--toolbar-day-shortcut-size) * 2 +
      var(--toolbar-day-today-min-w) + var(--toolbar-day-gap) * 3
  );
}

.toolbar-day-shortcuts {
  display: inline-flex;
  align-items: center;
  gap: var(--toolbar-day-gap);
  flex-shrink: 0;
}

.toolbar-day-shortcuts :deep(.el-button.is-circle) {
  width: var(--toolbar-day-shortcut-size);
  height: var(--toolbar-day-shortcut-size);
  padding: 0;
}

.toolbar-day-today-btn {
  min-width: var(--toolbar-day-today-min-w);
  height: var(--toolbar-day-shortcut-size);
  padding: 0 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.toolbar-day-picker.el-date-editor {
  --el-date-editor-width: var(--toolbar-day-picker-w);
  width: var(--toolbar-day-picker-w) !important;
  max-width: var(--toolbar-day-picker-w);
  flex: 0 0 var(--toolbar-day-picker-w);
}

.toolbar-day-picker :deep(.el-input__wrapper),
.toolbar-day-picker :deep(.el-input__inner) {
  width: 100%;
}

.toolbar-field-row--machine {
  flex: 0 1 auto;
  max-width: max-content;
  gap: var(--toolbar-machine-gap);
  padding: 0 8px 0 0;
  border-radius: 10px;
  border: 1px solid var(--el-color-warning-light-7);
  background: linear-gradient(
    165deg,
    var(--el-color-warning-light-9) 0%,
    var(--el-fill-color-blank) 55%,
    #fff7ed 100%
  );
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    0 1px 4px rgba(234, 88, 12, 0.06);
}

.toolbar-field-row--machine .toolbar-field-row__icon--machine {
  margin-left: -1px;
  border-radius: 9px 0 0 9px;
  background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);
  box-shadow: 0 2px 8px rgba(234, 88, 12, 0.3);
}

.toolbar-field-row--machine .toolbar-field-row__label {
  color: #9a3412;
}

.toolbar-machine-wrap {
  display: inline-flex;
  flex: 0 0 auto;
  max-width: var(--toolbar-machine-select-w);
}

.toolbar-field-row--switch.toolbar-filter-switch {
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.toolbar-filter-switch--active {
  border-color: var(--el-color-success-light-5);
  background: linear-gradient(180deg, var(--el-color-success-light-9) 0%, var(--el-fill-color-blank) 100%);
  box-shadow: 0 0 0 1px var(--el-color-success-light-7);
}

.toolbar-filter-switch--active .toolbar-filter-switch__text {
  color: var(--el-color-success-dark-2);
}

.toolbar-filter-switch__control {
  --el-switch-on-color: var(--el-color-success);
  --el-switch-off-color: var(--el-border-color);
}

.toolbar-filter-switch__control :deep(.el-switch__core) {
  min-width: 44px;
  height: 22px;
  border-radius: 11px;
}

.toolbar-filter-switch__control :deep(.el-switch__inner) {
  font-size: 10px;
  font-weight: 700;
}

.toolbar-load-btn {
  height: var(--toolbar-h);
  min-height: var(--toolbar-h);
  padding: 0 14px;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.toolbar-load-btn:not(.is-disabled) {
  background: linear-gradient(180deg, #79bbff 0%, var(--el-color-primary) 100%);
}

.full-width-control {
  width: 100%;
}

.toolbar-machine-select {
  width: var(--toolbar-machine-select-w) !important;
  max-width: var(--toolbar-machine-select-w);
  flex: 0 0 var(--toolbar-machine-select-w);
}

.toolbar-machine-select :deep(.el-select__wrapper),
.toolbar-machine-select :deep(.el-input__wrapper) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-color-warning-light-5);
  box-shadow: 0 1px 2px rgba(234, 88, 12, 0.06);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.toolbar-machine-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-warning);
}

.toolbar-machine-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-warning);
  box-shadow: 0 0 0 2px var(--el-color-warning-light-8);
}

.toolbar-machine-select :deep(.el-select__selected-item),
.toolbar-machine-select :deep(.el-select__placeholder) {
  font-weight: 600;
}

.toolbar-machine-select--chosen :deep(.el-select__wrapper) {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: var(--el-color-warning);
}

.toolbar-machine-select--chosen :deep(.el-select__selected-item) {
  color: #9a3412;
}

.toolbar-machine-select :deep(.el-select__caret) {
  color: var(--el-color-warning);
}

/* タッチ端末: 検索用 input を出さずキーボードを抑止 */
@media (hover: none) and (pointer: coarse) {
  .toolbar-machine-select :deep(.el-select__input),
  .toolbar-inspector-select :deep(.el-select__input),
  .product-select-toolbar :deep(.el-select__input),
  .plan-field__control--operator :deep(.el-select__input) {
    display: none !important;
  }
}

.btn-ico {
  margin-right: 4px;
  vertical-align: middle;
}

.plan-board {
  margin-top: 8px;
  min-height: 80px;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-day-group {
  border-radius: var(--ca-radius);
  padding: 0;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.plan-day-group--anchor {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
}

.plan-day-group__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 12px;
  padding: 6px 10px;
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color-blank) 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: sticky;
  top: 0;
  z-index: 3;
}

.plan-day-group--anchor .plan-day-group__head {
  background: linear-gradient(
    180deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 100%
  );
}

.plan-day-group__title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  min-width: 0;
}

.plan-day-group__date-bold {
  font-size: clamp(0.95rem, 2.2vw, 1.05rem);
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.3;
}

.plan-day-group__badge {
  flex-shrink: 0;
}

.plan-day-group__count {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.plan-day-group__cards {
  display: flex;
  flex-direction: column;
}

.plan-day-group .plan-row-card {
  margin: 0 8px 8px;
  border-radius: 8px;
}

.plan-day-group .plan-row-card:first-of-type {
  margin-top: 8px;
}

.plan-row-card__drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 2px 4px;
  margin: -2px 0;
  border-radius: 6px;
  color: var(--el-text-color-secondary);
  cursor: grab;
  touch-action: none;
  user-select: none;
}

.plan-row-card__drag-handle:active {
  cursor: grabbing;
}

.plan-row-card--ghost {
  opacity: 0.42;
}

.plan-row-card--chosen {
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
}

.plan-row-card {
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-warning);
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.plan-row-card:hover {
  border-color: var(--el-border-color);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}

.plan-row-card--confirmed {
  border-left-color: var(--el-color-success);
  opacity: 0.92;
}

.plan-row-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.plan-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plan-row__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.plan-row-scan-remarks-cluster {
  display: inline-flex;
  align-items: center;
  gap: 130px;
  min-width: 0;
  flex: 0 1 auto;
  max-width: 100%;
}

.plan-row-remarks {
  flex: 0 1 auto;
  min-width: 0;
  max-width: min(28rem, 100%);
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--el-color-danger);
  line-height: 1.35;
  background: var(--el-color-danger-light-9);
  border: 1px solid var(--el-color-danger-light-5);
  box-shadow: 0 0 0 1px rgba(245, 108, 108, 0.15);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-row__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 8px 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: linear-gradient(
    165deg,
    var(--el-fill-color-blank) 0%,
    var(--el-color-primary-light-9) 42%,
    var(--el-fill-color-light) 100%
  );
  border: 1px solid var(--el-color-primary-light-8);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.plan-row-card--confirmed .plan-row__meta {
  background: linear-gradient(165deg, var(--el-fill-color-blank) 0%, var(--el-color-success-light-9) 100%);
  border-color: var(--el-color-success-light-7);
}

.plan-meta-primary {
  display: inline-flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  flex: 0 1 auto;
  width: fit-content;
  max-width: min(100%, 28rem);
  min-width: 0;
  padding: 5px 10px;
  border-radius: 8px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid #93c5fd;
}

.plan-row-card--confirmed .plan-meta-primary {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #86efac;
}

.plan-meta-chips {
  --plan-meta-control-h: 32px;
  --plan-meta-block-h: calc(var(--plan-meta-control-h) + 10px);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  flex: 1 1 auto;
  min-width: 0;
}

.plan-meta-chips > .plan-chip,
.plan-meta-chips > .plan-meta-field {
  box-sizing: border-box;
  min-height: var(--plan-meta-block-h);
  height: var(--plan-meta-block-h);
}

.plan-row__ops {
  --plan-run-block-height: 5.25rem;
  --plan-act-btn-width: 6.25rem;
  box-sizing: border-box;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-row__ops .plan-row__timer {
  flex: 0 0 auto;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-row__ops .plan-row__actions {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 6px;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-status-action-btn {
  padding: 0 4px;
  height: 22px;
  font-size: 0.75rem;
  font-weight: 600;
}

.plan-status-action-btn .el-icon {
  margin-right: 2px;
  font-size: 0.85rem;
}

.plan-seq-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  background: var(--el-fill-color-light);
  color: #000;
  border: 1px solid var(--el-border-color-lighter);
}

.plan-field--inline {
  --plan-field-control-width: 108px;
  display: grid;
  grid-template-columns: 7.5rem var(--plan-field-control-width);
  column-gap: 6px;
  align-items: center;
  flex: 0 0 auto;
  width: calc(7.5rem + var(--plan-field-control-width) + 6px);
  max-width: 100%;
}

.plan-meta-field {
  --plan-meta-control-w: 108px;
  display: grid;
  grid-template-columns: auto var(--plan-meta-control-w);
  column-gap: 8px;
  align-items: center;
  min-width: 0;
  padding: 0 8px;
  border-radius: 8px;
  border: 1px solid transparent;
  flex: 0 1 auto;
  width: fit-content;
  max-width: 100%;
}

.plan-meta-field--operator {
  --plan-meta-control-w: 108px;
  background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%);
  border-color: #c4b5fd;
}

.plan-meta-field--setup {
  --plan-meta-control-w: 118px;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #fcd34d;
}

.plan-meta-field__label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  line-height: 1.2;
  white-space: nowrap;
}

.plan-meta-field--operator .plan-meta-field__label {
  color: #5b21b6;
}

.plan-meta-field--setup .plan-meta-field__label {
  color: #b45309;
}

.plan-meta-field__icon {
  font-size: 0.9rem;
}

.plan-meta-field__unit {
  font-weight: 600;
  opacity: 0.85;
}

.plan-meta-field .plan-field__control--operator,
.plan-meta-field .plan-field__number--setup,
.plan-meta-field .plan-field__number--setup :deep(.el-input-number) {
  width: var(--plan-meta-control-w);
  max-width: 100%;
  justify-self: start;
}

.plan-meta-field--operator :deep(.el-select__wrapper) {
  min-height: var(--plan-meta-control-h);
  height: var(--plan-meta-control-h);
  background: rgba(255, 255, 255, 0.92);
  border-color: #c4b5fd;
  box-shadow: 0 1px 2px rgba(91, 33, 182, 0.08);
}

.plan-meta-field--operator :deep(.el-select__wrapper:hover) {
  border-color: #8b5cf6;
}

.plan-meta-field--setup :deep(.el-input-number__decrease),
.plan-meta-field--setup :deep(.el-input-number__increase) {
  background: rgba(255, 255, 255, 0.75);
  border-color: #fcd34d;
  color: #b45309;
}

.plan-meta-field--setup :deep(.el-input-number) {
  height: var(--plan-meta-control-h);
  line-height: var(--plan-meta-control-h);
}

.plan-meta-field--setup :deep(.el-input__wrapper) {
  min-height: var(--plan-meta-control-h);
  height: var(--plan-meta-control-h);
  background: rgba(255, 255, 255, 0.92);
  border-color: #fcd34d;
  box-shadow: 0 1px 2px rgba(180, 83, 9, 0.08);
}

.plan-field--inline .plan-field__label {
  display: block;
  margin-bottom: 0;
  white-space: nowrap;
  text-align: right;
  justify-self: end;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.plan-field__control--operator,
.plan-field__number--setup,
.plan-field__number--setup :deep(.el-input-number) {
  width: var(--plan-field-control-width, 152px);
  justify-self: start;
}

.plan-field__number--setup :deep(.el-input-number__decrease),
.plan-field__number--setup :deep(.el-input-number__increase) {
  width: 34px;
  flex-shrink: 0;
  font-size: 14px;
}

.plan-field__number--setup :deep(.el-input__wrapper) {
  width: 100%;
  padding-left: 6px;
  padding-right: 6px;
}

.plan-field__number--setup :deep(.el-input__inner) {
  text-align: center;
}

.plan-product-name {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 11rem;
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.01em;
  color: #1e3a8a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-row-card--confirmed .plan-product-name {
  color: #166534;
}

.plan-product-material {
  display: inline-flex;
  align-items: center;
  flex: 0 1 auto;
  min-width: 0;
  max-width: 14rem;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1.3;
  color: #0f766e;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #5eead4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  max-width: 100%;
  padding: 0 10px;
  border-radius: 8px;
  line-height: 1.25;
  border: 1px solid transparent;
}

.plan-chip__label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  opacity: 0.9;
}

.plan-chip__value {
  font-size: 0.92rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.plan-chip--qty {
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #60a5fa;
  color: #1e40af;
}

.plan-chip--qty .plan-chip__label {
  color: #1d4ed8;
}

.plan-chip--qty .plan-chip__value {
  color: #1e3a8a;
}

.plan-chip--qty-actual {
  background: linear-gradient(180deg, #dcfce7 0%, #bbf7d0 100%);
  border-color: #4ade80;
  color: #166534;
}

.plan-chip--qty-actual .plan-chip__label {
  color: #15803d;
}

.plan-chip--qty-actual .plan-chip__value {
  color: #14532d;
}

.plan-chip--code {
  background: linear-gradient(180deg, #f3e8ff 0%, #e9d5ff 100%);
  border-color: #c084fc;
  font-size: 0.8rem;
  font-weight: 700;
  color: #6b21a8;
  letter-spacing: 0.02em;
}

/* legacy aliases */
.plan-chip--accent {
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #60a5fa;
  color: #1e40af;
  font-weight: 600;
}

.plan-chip--muted {
  background: linear-gradient(180deg, #f3e8ff 0%, #e9d5ff 100%);
  border-color: #c084fc;
  color: #6b21a8;
}

.plan-row__timer {
  flex-shrink: 0;
}

.timer-compact {
  box-sizing: border-box;
  width: 15.5rem;
  min-width: 15.5rem;
  max-width: 15.5rem;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 1px 4px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.plan-row__ops .timer-compact {
  height: 100%;
  max-height: var(--plan-run-block-height);
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

.plan-row__ops .timer-compact__readout-row {
  margin: 1px 0;
}

.plan-row__ops .timer-compact__readout {
  font-size: 1.1rem;
  line-height: 1.05;
}

.plan-row__ops .timer-compact__pause-value {
  font-size: 0.88rem;
  line-height: 1.05;
}

.plan-row__ops .timer-compact__walls {
  font-size: 0.68rem;
  line-height: 1.1;
}

.timer-compact--idle {
  background: linear-gradient(165deg, #f8fafc 0%, #e2e8f0 100%);
  border-color: #cbd5e1;
}

.timer-compact--running {
  background: linear-gradient(165deg, #ecfdf5 0%, #d1fae5 55%, #f0fdf4 100%);
  border-color: #6ee7b7;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(16, 185, 129, 0.12),
    0 2px 8px rgba(16, 185, 129, 0.12);
}

.timer-compact--paused {
  background: linear-gradient(165deg, #fffbeb 0%, #fef3c7 55%, #fff7ed 100%);
  border-color: #fbbf24;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(245, 158, 11, 0.15);
}

.timer-compact--ended {
  background: linear-gradient(165deg, #eff6ff 0%, #dbeafe 55%, #f8fafc 100%);
  border-color: #93c5fd;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(59, 130, 246, 0.1);
}

.timer-compact__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  min-height: 0;
}

.timer-compact__label {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
  white-space: nowrap;
}

.timer-compact__label-icon {
  font-size: 0.82rem;
}

.timer-compact--running .timer-compact__label {
  color: #047857;
}

.timer-compact--paused .timer-compact__label {
  color: #b45309;
}

.timer-compact--ended .timer-compact__label {
  color: #1d4ed8;
}

.timer-compact__phase {
  flex-shrink: 0;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0.02em;
  border: 1px solid transparent;
}

.timer-compact--idle .timer-compact__phase {
  color: #475569;
  background: rgba(255, 255, 255, 0.75);
  border-color: #cbd5e1;
}

.timer-compact--running .timer-compact__phase {
  color: #065f46;
  background: rgba(255, 255, 255, 0.8);
  border-color: #6ee7b7;
}

.timer-compact--paused .timer-compact__phase {
  color: #92400e;
  background: rgba(255, 255, 255, 0.82);
  border-color: #fcd34d;
}

.timer-compact--ended .timer-compact__phase {
  color: #1e40af;
  background: rgba(255, 255, 255, 0.82);
  border-color: #93c5fd;
}

.timer-compact__readout-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  margin: 2px 0;
}

.timer-compact__readout {
  font-variant-numeric: tabular-nums;
  font-size: clamp(1.2rem, 3vw, 1.5rem);
  font-weight: 800;
  margin: 0;
  line-height: 1.1;
  flex: 1 1 auto;
  min-width: 0;
  color: #0f172a;
}

.timer-compact--running .timer-compact__readout {
  color: #047857;
}

.timer-compact--ended .timer-compact__readout {
  color: #1e3a8a;
}

.timer-compact__readout--display-frozen {
  color: #b45309;
  letter-spacing: 0.02em;
}

.timer-compact__pause-side {
  flex: 0 0 auto;
  text-align: right;
  line-height: 1.15;
  max-width: 46%;
  padding: 1px 5px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.55);
}

.timer-compact__pause-label {
  display: block;
  font-size: 0.58rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #78716c;
  white-space: nowrap;
}

.timer-compact__pause-value {
  display: block;
  font-variant-numeric: tabular-nums;
  font-size: clamp(0.92rem, 2.4vw, 1.1rem);
  font-weight: 700;
  color: #57534e;
}

.timer-compact--paused .timer-compact__pause-label,
.timer-compact--paused .timer-compact__pause-value {
  color: #b45309;
}

.timer-compact__walls {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center;
  gap: 4px 6px;
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
  color: #64748b;
  white-space: nowrap;
  padding-top: 2px;
  border-top: 1px dashed rgba(100, 116, 139, 0.25);
}

.timer-compact--running .timer-compact__walls {
  color: #047857;
  border-top-color: rgba(4, 120, 87, 0.2);
}

.timer-compact--paused .timer-compact__walls {
  color: #b45309;
  border-top-color: rgba(180, 83, 9, 0.25);
}

.timer-compact--ended .timer-compact__walls {
  color: #1d4ed8;
  border-top-color: rgba(29, 78, 216, 0.2);
}

.timer-compact__walls > span:not(.timer-compact__sep) {
  flex-shrink: 0;
}

.timer-compact__sep {
  opacity: 0.5;
  flex-shrink: 0;
  color: inherit;
}

.plan-row__actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  align-items: stretch;
}

.plan-act-btn {
  margin: 0 !important;
  padding: 0 6px;
  font-size: 0.78rem;
  font-weight: 600;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
  white-space: nowrap;
}

.plan-row__ops .plan-act-btn {
  box-sizing: border-box;
  width: var(--plan-act-btn-width, 6.25rem);
  min-width: var(--plan-act-btn-width, 6.25rem);
  max-width: var(--plan-act-btn-width, 6.25rem);
  height: var(--plan-run-block-height);
  min-height: unset;
  max-height: var(--plan-run-block-height);
  flex: 0 0 var(--plan-act-btn-width, 6.25rem);
  line-height: 1.15;
}

.plan-row__ops .plan-act-btn :deep(span) {
  line-height: 1.15;
}

.plan-act-btn :deep(.el-icon) {
  margin-right: 3px;
  font-size: 1rem;
}

.plan-act-btn--start:not(.is-disabled):not(.plan-act-btn--start--locked) {
  --el-button-bg-color: var(--el-color-success);
  --el-button-border-color: var(--el-color-success);
  --el-button-hover-bg-color: #3ecf7a;
  --el-button-hover-border-color: #3ecf7a;
  --el-button-active-bg-color: #529b2e;
  --el-button-active-border-color: #529b2e;
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #4cd787 0%, var(--el-color-success) 100%);
  color: #fff;
}

.plan-act-btn--start.plan-act-btn--start--locked.is-disabled {
  opacity: 1;
  cursor: not-allowed;
  --el-button-disabled-bg-color: var(--el-fill-color);
  --el-button-disabled-border-color: var(--el-border-color);
  --el-button-disabled-text-color: var(--el-text-color-placeholder);
  background: var(--el-fill-color);
  color: var(--el-text-color-placeholder);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: none;
}

.plan-act-btn--pause:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-warning);
  --el-button-border-color: var(--el-color-warning);
  --el-button-text-color: #5c3d00;
  background: linear-gradient(180deg, #ffd06a 0%, var(--el-color-warning) 100%);
  color: #5c3d00;
}

.plan-act-btn--resume:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-primary);
  --el-button-border-color: var(--el-color-primary);
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #79bbff 0%, var(--el-color-primary) 100%);
  color: #fff;
}

.plan-act-btn--end:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-danger);
  --el-button-border-color: var(--el-color-danger);
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #f89898 0%, var(--el-color-danger) 100%);
  color: #fff;
}

.plan-act-btn--machine:not(.is-disabled) {
  --el-button-bg-color: #d3d1d1;
  --el-button-border-color: #d4d2d2;
  --el-button-hover-bg-color: #c9c7c7;
  --el-button-hover-border-color: #bebebe;
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #cfcfcf 0%, #c4c3c3 100%);
  color: #fff;
}

.change-machine-dialog :deep(.el-dialog) {
  max-width: 94vw;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.2);
}

.change-machine-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

.change-machine-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  z-index: 3;
  width: 28px;
  height: 28px;
}

.change-machine-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.92);
}

.change-machine-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.change-machine-dialog :deep(.el-dialog__body) {
  padding: 0 16px 16px;
}

.change-machine-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 44px 14px 16px;
  background: linear-gradient(135deg, #ea580c 0%, #f59e0b 48%, #fbbf24 100%);
  color: #fff;
}

.change-machine-header__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.change-machine-header__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.change-machine-header__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.change-machine-header__title {
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.02em;
}

.change-machine-header__sub {
  font-size: 0.72rem;
  font-weight: 500;
  line-height: 1.3;
  opacity: 0.92;
}

.change-machine-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.change-machine-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border: 1px solid #fdba74;
}

.change-machine-hero__code {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #9a3412;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid #fed7aa;
}

.change-machine-hero__product {
  font-size: 0.88rem;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.change-machine-hero__product strong {
  font-weight: 700;
}

.change-machine-hero__sep {
  margin: 0 4px;
  opacity: 0.45;
}

.change-machine-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 8px;
  align-items: stretch;
}

.change-machine-flow__arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ea580c;
  opacity: 0.85;
}

.change-machine-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
}

.change-machine-card--current {
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color-blank) 100%);
}

.change-machine-card--target {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: #fcd34d;
}

.change-machine-card__label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

.change-machine-card--target .change-machine-card__label {
  color: #b45309;
}

.change-machine-card__value {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.3;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.change-machine-select {
  width: 100%;
}

.change-machine-select :deep(.el-select__wrapper) {
  min-height: 40px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-color-warning-light-5);
  box-shadow: 0 1px 2px rgba(234, 88, 12, 0.06);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.change-machine-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-warning);
}

.change-machine-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-warning);
  box-shadow: 0 0 0 2px var(--el-color-warning-light-8);
}

.change-machine-select--chosen :deep(.el-select__wrapper) {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: var(--el-color-warning);
}

.change-machine-select--chosen :deep(.el-select__selected-item) {
  font-weight: 700;
  color: #9a3412;
}

.change-machine-select :deep(.el-select__caret) {
  color: var(--el-color-warning);
}

.change-machine-hint {
  margin: 0;
  padding: 8px 10px;
  font-size: 0.75rem;
  line-height: 1.4;
  color: #92400e;
  border-radius: 8px;
  background: #fffbeb;
  border: 1px dashed #fcd34d;
}

.change-machine-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 2px;
}

.change-machine-actions__submit,
.change-machine-actions__cancel {
  min-height: 42px;
  margin: 0 !important;
  font-weight: 600;
  border-radius: 8px;
}

.change-machine-actions__submit:not(.is-disabled) {
  border: none;
  background: linear-gradient(180deg, #fbbf24 0%, #ea580c 100%);
  color: #fff;
  box-shadow: 0 2px 10px rgba(234, 88, 12, 0.28);
}

.change-machine-actions__submit:not(.is-disabled):hover {
  background: linear-gradient(180deg, #fcd34d 0%, #c2410c 100%);
}

.change-machine-actions__cancel {
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
}

@media (max-width: 420px) {
  .change-machine-flow {
    grid-template-columns: 1fr;
  }

  .change-machine-flow__arrow {
    transform: rotate(90deg);
  }

  .change-machine-actions {
    grid-template-columns: 1fr;
  }
}

.plan-act-btn.is-disabled {
  box-shadow: none;
  opacity: 0.55;
}

.plan-row__fields {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr;
  padding-top: 4px;
  border-top: 1px dashed var(--el-border-color-lighter);
  margin-top: 2px;
}

@media (min-width: 560px) {
  .plan-row__fields:not(.plan-row__fields--stack) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.plan-field__label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--el-text-color-regular);
}

.plan-field__control {
  width: 100%;
}

.plan-field__number {
  width: 100%;
}

.plan-field__number :deep(.el-input-number) {
  width: 100%;
}

.plan-field__number :deep(.el-input__wrapper) {
  width: 100%;
}

.production-end-dialog :deep(.el-dialog) {
  max-width: 94vw;
}

.end-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.end-dialog-product {
  margin: 0;
  font-weight: 700;
  font-size: 0.95rem;
  line-height: 1.35;
  word-break: break-word;
  color: var(--el-text-color-primary);
}

.end-dialog-warn {
  margin: 0;
}

.end-dialog-warn :deep(.el-alert__content) {
  padding: 0;
}

.end-dialog-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.end-dialog-label {
  font-weight: 600;
  font-size: 0.84rem;
  color: var(--el-text-color-regular);
}

.end-dialog-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.end-dialog-meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.end-dialog-meta-label {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--el-text-color-secondary);
}

.end-dialog-meta-value {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.end-dialog-meta-missing {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--el-color-warning-dark-2);
}

.end-dialog-input {
  width: 100%;
}

.end-dialog-input :deep(.el-input__wrapper) {
  min-height: 40px;
  padding: 0 12px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  box-shadow:
    inset 0 1px 2px rgba(15, 23, 42, 0.04),
    0 0 0 1px var(--el-border-color-lighter);
  transition:
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.end-dialog-input :deep(.el-input__wrapper:hover) {
  box-shadow:
    inset 0 1px 2px rgba(15, 23, 42, 0.04),
    0 0 0 1px var(--el-border-color);
}

.end-dialog-input :deep(.el-input__wrapper.is-focus) {
  background: #fff;
  box-shadow:
    inset 0 1px 2px rgba(15, 23, 42, 0.03),
    0 0 0 1px var(--el-color-primary-light-5),
    0 0 0 3px var(--el-color-primary-light-9);
}

.end-dialog-input :deep(.el-input__inner) {
  font-size: 1rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  text-align: left;
}

@media (max-width: 420px) {
  .end-dialog-meta {
    grid-template-columns: 1fr;
  }
}

.end-dialog-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 4px;
}

.end-dialog-btn {
  min-height: 40px;
  margin: 0 !important;
  font-weight: 600;
  border-radius: 8px;
  border: none;
}

.end-dialog-btn--full:not(.is-disabled) {
  background: linear-gradient(180deg, #3ecf7a 0%, var(--el-color-success) 100%);
  color: #fff;
}

.end-dialog-btn--defer:not(.is-disabled) {
  background: linear-gradient(180deg, #ffc857 0%, var(--el-color-warning) 100%);
  color: #5c3d00;
}

.end-dialog-defer-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fcd34d;
}

.end-dialog-defer-day {
  width: 100%;
}

.end-dialog-defer-day :deep(.el-input__wrapper) {
  width: 100%;
}

.end-dialog-defer-remainder {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.35;
  color: #92400e;
}

.end-dialog-defer-subsequent {
  height: auto;
  line-height: 1.35;
  white-space: normal;
}

.end-dialog-defer-subsequent :deep(.el-checkbox__label) {
  font-size: 0.78rem;
  line-height: 1.35;
  color: var(--el-text-color-regular);
}

.end-dialog-btn--cancel {
  grid-column: 1 / -1;
}

.production-end-dialog :deep(.el-dialog__header) {
  padding: 12px 14px 8px;
  margin-right: 0;
}

.production-end-dialog :deep(.el-dialog__body) {
  padding: 8px 14px 14px;
}

.production-end-dialog :deep(.el-dialog__title) {
  font-size: 1rem;
  font-weight: 700;
}

.confirmed-edit-dialog :deep(.el-dialog) {
  max-width: 94vw;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.2);
}

.confirmed-edit-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  z-index: 3;
  width: 28px;
  height: 28px;
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.92);
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.confirmed-edit-dialog :deep(.el-dialog__body) {
  padding: 8px 12px 6px;
}

.confirmed-edit-dialog :deep(.el-dialog__footer) {
  padding: 6px 12px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.confirmed-edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 40px 9px 12px;
  background: linear-gradient(135deg, #4338ca 0%, #6366f1 52%, #818cf8 100%);
  color: #fff;
}

.confirmed-edit-header__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1 1 auto;
}

.confirmed-edit-header__clear {
  flex-shrink: 0;
  margin: 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.45) !important;
  background: rgba(255, 255, 255, 0.14) !important;
  color: #fff !important;
  font-weight: 600;
  border-radius: 7px;
}

.confirmed-edit-header__clear:hover:not(.is-disabled) {
  background: rgba(254, 226, 226, 0.28) !important;
  border-color: #fecaca !important;
  color: #fff !important;
}

.confirmed-edit-header__clear-icon {
  margin-right: 4px;
}

.confirmed-edit-header__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.confirmed-edit-header__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.confirmed-edit-header__title {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.01em;
}

.confirmed-edit-header__sub {
  font-size: 0.68rem;
  font-weight: 600;
  opacity: 0.88;
  letter-spacing: 0.04em;
}

.confirmed-edit-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.confirmed-edit-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  margin: 0;
  padding: 7px 9px;
  border-radius: 8px;
  background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 100%);
  border: 1px solid #c7d2fe;
}

.confirmed-edit-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #fff;
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  box-shadow: 0 1px 4px rgba(16, 185, 129, 0.35);
}

.confirmed-edit-hero__code {
  flex-shrink: 0;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #4338ca;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.28);
}

.confirmed-edit-hero__product {
  flex: 1 1 140px;
  min-width: 0;
  font-size: 0.82rem;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.confirmed-edit-hero__product strong {
  font-weight: 700;
  color: #312e81;
}

.confirmed-edit-hero__sep {
  margin: 0 4px;
  color: var(--el-text-color-placeholder);
}

.confirmed-edit-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.confirmed-edit-section {
  padding: 7px 9px 4px;
  border-radius: 8px;
  border: 1px solid transparent;
}

.confirmed-edit-section--people {
  background: linear-gradient(180deg, #faf5ff 0%, #fff 100%);
  border-color: #e9d5ff;
}

.confirmed-edit-section--time {
  background: linear-gradient(180deg, #eff6ff 0%, #fff 100%);
  border-color: #bfdbfe;
}

.confirmed-edit-section__title {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0 0 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.confirmed-edit-section--people .confirmed-edit-section__title {
  color: #7c3aed;
}

.confirmed-edit-section--time .confirmed-edit-section__title {
  color: #2563eb;
}

.confirmed-edit-form :deep(.confirmed-edit-form-item) {
  margin-bottom: 6px;
}

.confirmed-edit-form :deep(.confirmed-edit-form-item .el-form-item__label) {
  padding-bottom: 2px;
  font-size: 0.74rem;
  font-weight: 600;
  line-height: 1.2;
  color: var(--el-text-color-regular);
}

.confirmed-edit-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 8px;
}

.confirmed-edit-full {
  width: 100%;
}

.confirmed-edit-form :deep(.el-input-number) {
  width: 100%;
}

.confirmed-edit-elapsed {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 30px;
  padding: 5px 8px;
  border-radius: 8px;
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  border: 1px solid #93c5fd;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.confirmed-edit-elapsed__value {
  font-variant-numeric: tabular-nums;
  font-size: 1.05rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: 0.04em;
  color: #1d4ed8;
}

.confirmed-edit-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 0;
  padding: 6px 8px;
  border-radius: 7px;
  font-size: 0.72rem;
  line-height: 1.4;
  color: #92400e;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fcd34d;
}

.confirmed-edit-hint__icon {
  flex-shrink: 0;
  margin-top: 1px;
  color: #d97706;
}

.confirmed-edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.confirmed-edit-btn {
  min-width: 88px;
  margin: 0 !important;
  font-weight: 600;
  border-radius: 8px;
}

.confirmed-edit-btn--save:not(.is-disabled) {
  border: none;
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
}

.confirmed-edit-btn--save:not(.is-disabled):hover {
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
}

.confirmed-edit-btn--cancel {
  border-color: var(--el-border-color);
}

@media (max-width: 480px) {
  .confirmed-edit-form-row,
  .confirmed-edit-form-row--metrics {
    grid-template-columns: 1fr;
  }
}


/* 検査：不良項目パネル */
.defect-panel {
  margin-top: 10px;
  padding: 10px 10px 4px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, var(--el-fill-color-blank) 0%, var(--el-fill-color-light) 100%);
}
.defect-panel__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 8px;
}
.defect-panel__title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--el-text-color-primary);
}
.defect-panel__hint {
  margin: 0;
  font-size: 0.72rem;
  color: var(--el-text-color-secondary);
}
.defect-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
@media (min-width: 520px) { .defect-grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 900px) { .defect-grid { grid-template-columns: repeat(4, 1fr); } }
.defect-cell {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}
.defect-cell--active {
  border-color: var(--el-color-warning-light-5);
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
}
.defect-cell__label {
  font-size: 0.78rem;
  font-weight: 700;
  line-height: 1.3;
  min-height: 2.2em;
}
.defect-stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.defect-stepper__val {
  flex: 1;
  text-align: center;
  font-size: 1.35rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.defect-stepper__btn {
  width: 40px !important;
  height: 40px !important;
  padding: 0 !important;
}
.toolbar-field-row--inspector .toolbar-inspector-select {
  width: min(176px, 100%) !important;
  max-width: 176px;
  flex: 1 1 auto;
}
.toolbar-field-row--product .product-select-toolbar {
  width: min(280px, 100%) !important;
  flex: 1 1 auto;
}
.toolbar-field-row--inspector {
  flex: 0 1 auto;
  max-width: max-content;
  gap: var(--toolbar-machine-gap, 6px);
  padding: 0 8px 0 0;
  border-radius: 10px;
  border: 1px solid #c4b5fd;
  background: linear-gradient(165deg, #f5f3ff 0%, var(--el-fill-color-blank) 55%, #ede9fe 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}
.toolbar-field-row--inspector .toolbar-field-row__icon {
  margin-left: -1px;
  border-radius: 9px 0 0 9px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  box-shadow: 0 2px 8px rgba(109, 40, 217, 0.28);
}
.toolbar-field-row--inspector .toolbar-field-row__label { color: #5b21b6; }
.plan-row-card--confirmed { border-color: var(--el-color-success-light-5); }
.history-defects {
  list-style: none;
  margin: 8px 0 0;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  font-size: 0.78rem;
}
.history-defects li { display: flex; justify-content: space-between; gap: 8px; padding: 2px 0; }

.inspection-history-section {
  --hist-accent: #0d9488;
  --hist-accent-soft: #ccfbf1;
  margin-top: 14px;
}

.inspection-history-table-card {
  border-radius: var(--ca-radius, 10px);
  border: 1px solid var(--el-color-success-light-7);
  overflow: hidden;
  background: var(--el-fill-color-blank);
  box-shadow:
    0 1px 3px rgba(15, 23, 42, 0.05),
    0 4px 14px rgba(13, 148, 136, 0.06);
}

.inspection-history-table-card :deep(.el-card__body) {
  padding: 0;
}

.inspection-history-table-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--el-color-success-light-7);
  background: linear-gradient(
    135deg,
    var(--el-color-success-light-9) 0%,
    #f0fdfa 48%,
    var(--el-fill-color-blank) 100%
  );
}

.inspection-history-table-card__title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.inspection-history-table-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 9px;
  color: var(--hist-accent);
  background: var(--hist-accent-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.inspection-history-table-card__title {
  margin: 0;
  font-size: clamp(0.92rem, 2.2vw, 1.02rem);
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.35;
}

.inspection-history-table-card__count {
  flex-shrink: 0;
  min-width: 1.85rem;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  text-align: center;
  color: var(--el-color-success-dark-2);
  background: var(--el-color-success-light-9);
  border: 1px solid var(--el-color-success-light-5);
  box-shadow: 0 1px 2px rgba(16, 185, 129, 0.12);
}

.inspection-history-table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  padding: 0 0 2px;
}

.inspection-history-table {
  width: 100%;
  min-width: 760px;
  --el-table-border-color: var(--el-border-color-extra-light);
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: #f0fdfa;
  --el-table-tr-bg-color: var(--el-fill-color-blank);
  --el-table-striped-bg-color: #f8fafc;
}

.inspection-history-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.inspection-history-table :deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 2;
}

.inspection-history-table :deep(.el-table__header th.el-table__cell) {
  padding: 10px 8px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #115e59;
  background: linear-gradient(180deg, #ecfdf5 0%, #f0fdfa 100%) !important;
  border-bottom: 2px solid var(--el-color-success-light-5) !important;
}

.inspection-history-table :deep(.el-table__body td.el-table__cell) {
  padding: 11px 8px;
  font-size: 0.8rem;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  vertical-align: middle;
}

.inspection-history-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: #f0fdfa !important;
}

.inspection-history-table :deep(.el-table__row--striped td.el-table__cell) {
  background: #f8fafc;
}

.inspection-history-table :deep(.el-table__fixed-left-patch) {
  background: linear-gradient(180deg, #ecfdf5 0%, #f0fdfa 100%);
}

.hist-cell-code {
  display: inline-block;
  max-width: 100%;
  padding: 2px 8px;
  border-radius: 6px;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--hist-accent);
  background: var(--hist-accent-soft);
  border: 1px solid #99f6e4;
}

.hist-cell-name {
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.35;
}

.hist-cell-inspector {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  color: var(--el-text-color-regular);
}

.hist-cell-inspector__icon {
  flex-shrink: 0;
  font-size: 14px;
  color: #7c3aed;
}

.hist-cell-qty {
  display: inline-block;
  min-width: 2.5em;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.88rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-success-dark-2);
  background: var(--el-color-success-light-9);
}

.hist-cell-time {
  font-variant-numeric: tabular-nums;
  font-size: 0.78rem;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.hist-cell-duration {
  font-variant-numeric: tabular-nums;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.hist-cell-duration--active {
  font-weight: 700;
  color: var(--hist-accent);
}

.hist-cell-duration--muted {
  font-weight: 500;
  color: var(--el-text-color-placeholder);
}

.hist-cell-defects {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 220px;
}

.hist-cell-defects__tag {
  margin: 0;
  border-radius: 6px;
  font-size: 0.72rem;
}

.hist-cell-defects__tag strong {
  font-weight: 800;
  margin-left: 2px;
}

.hist-cell-empty {
  color: var(--el-text-color-placeholder);
  font-size: 0.85rem;
}

@media (max-width: 640px) {
  .inspection-history-table-card__head {
    padding: 8px 10px;
  }

  .inspection-history-table :deep(.el-table__header th.el-table__cell),
  .inspection-history-table :deep(.el-table__body td.el-table__cell) {
    padding: 9px 6px;
  }
}
</style>
