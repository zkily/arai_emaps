<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import type { ElInput, ElInputNumber } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  ChatLineSquare,
  Clock,
  DataLine,
  Delete,
  Edit,
  Refresh,
  User,
  Warning,
} from '@element-plus/icons-vue'
import { useCuttingManualRegistration } from './useCuttingManualRegistration'
import { useCuttingBatchRegistration, type CuttingBatchRow } from './useCuttingBatchRegistration'

defineOptions({ name: 'CuttingActualCollectionRegistration' })

const reg = useCuttingManualRegistration()
const {
  productionDay,
  canCreate,
  lineFilterName,
  loading,
  saving,
  deletingRowId,
  filteredRows,
  listSummaryQtyLabel,
  listSummaryEfficiencyLabel,
  products,
  loadingProducts,
  lineOptions,
  loadingLines,
  editingRowId,
  form,
  isEdit,
  canSave,
  canEdit,
  canDelete,
  timeSummary,
  formatMinutesLabel,
  lineLabel,
  computedVariance,
  loadRows,
  onProductChange,
  formatQtyInputValue,
  onPlannedQtyInput,
  onActualQtyInput,
  onVarianceQtyInput,
  startedAtText,
  endedAtText,
  onStartedAtInput,
  onEndedAtInput,
  onStartedAtBlur,
  onEndedAtBlur,
  onProductionDayChange,
  shiftProductionDay,
  goProductionDayToday,
  resetForm,
  loadRowIntoForm,
  deleteRow,
  submitForm,
  formatBreakMin,
  formatStopMin,
  formatWorkHours,
  formatEfficiencyRate,
  isEfficiencyRateOutOfRange,
  dataSourceLabel,
  dataSourceTagType,
  canEditRow,
  canDeleteRow,
  isRowMesInProgress,
  init,
} = reg

const {
  batchLoading,
  batchSaving,
  batchLoadedDay,
  batchLineFilter,
  batchLineOptions,
  visibleBatchRows,
  selectedBatchRows,
  batchRegisteredCount,
  allVisibleSelected,
  someVisibleSelected,
  isBatchRowRegistered,
  toggleAllVisible,
  loadBatch,
  onBatchTimeInput,
  onBatchTimeBlur,
  onBatchQtyInput,
  batchVariance,
  batchWorkMin,
  submitBatch,
} = useCuttingBatchRegistration({
  productionDay,
  registeredRows: reg.rows,
  canCreate,
  onSaved: loadRows,
})

const entryMode = ref<'single' | 'batch'>('single')

watch(entryMode, (mode) => {
  if (mode !== 'batch') return
  if (isEdit.value) resetForm()
  if (batchLoadedDay.value !== productionDay.value) void loadBatch()
})

watch(productionDay, () => {
  if (entryMode.value === 'batch') void loadBatch()
})

function onEditRow(row: Parameters<typeof loadRowIntoForm>[0]): void {
  entryMode.value = 'single'
  loadRowIntoForm(row)
}

function batchRowClass({ row }: { row: CuttingBatchRow }): string {
  if (row.error) return 'car-batch__row--error'
  if (isBatchRowRegistered(row)) return 'car-batch__row--registered'
  return row.selected ? 'car-batch__row--selected' : ''
}

function formatBatchWorkMin(row: CuttingBatchRow): string {
  const m = batchWorkMin(row)
  if (m == null) return '—'
  return m < 0 ? '超過' : formatMinutesLabel(m)
}

/** 生産=0, 開始=1, 終了=2, 休憩=3, 停止=4 */
const BATCH_NAV_LAST_COL = 4
const batchTableWrapRef = ref<HTMLElement | null>(null)

function onBatchNavKeydown(e: KeyboardEvent): void {
  if (e.key !== 'Enter' || e.isComposing) return
  const host = (e.target as HTMLElement | null)?.closest<HTMLElement>('[data-bnav]')
  const wrap = batchTableWrapRef.value
  if (!host || !wrap) return
  e.preventDefault()
  const [r, c] = String(host.dataset.bnav).split('-').map(Number)
  const next = c >= BATCH_NAV_LAST_COL ? `${r + 1}-1` : `${r}-${c + 1}`
  const input = wrap.querySelector<HTMLInputElement>(`[data-bnav="${next}"] input`)
  input?.focus()
  input?.select()
}

const lineSelected = computed(() => Boolean(form.value.productionLine?.trim()))

const productSelected = computed(() => isEdit.value || Boolean(form.value.productCd?.trim()))

const startedAtInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const endedAtInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const breakMinInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const stopMinInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const remarksInputRef = ref<InstanceType<typeof ElInput> | null>(null)

function focusElInput(inputRef: typeof startedAtInputRef): void {
  nextTick(() => {
    inputRef.value?.focus()
    const el = inputRef.value?.$el as HTMLElement | undefined
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

function focusInputNumber(inputRef: typeof breakMinInputRef): void {
  nextTick(() => {
    const root = inputRef.value?.$el as HTMLElement | undefined
    const input = root?.querySelector('input')
    input?.focus()
    input?.select()
    root?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

function onStartedAtEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  onStartedAtBlur()
  focusElInput(endedAtInputRef)
}

function onEndedAtEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  onEndedAtBlur()
  focusInputNumber(breakMinInputRef)
}

function onBreakMinEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  focusInputNumber(stopMinInputRef)
}

function onStopMinEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  focusElInput(remarksInputRef)
}

onMounted(() => {
  void init()
})
</script>


<template>
  <div class="iar car-modern">
    <header class="iar-hero iar-rise">
      <div class="car-hero-fx" aria-hidden="true">
        <span class="fx-orb orb-a" />
        <span class="fx-orb orb-b" />
        <span class="fx-grid" />
      </div>
      <div class="iar-hero__main">
        <div class="iar-hero__icon">
          <el-icon :size="22"><DataLine /></el-icon>
        </div>
        <div>
          <div class="iar-hero__eyebrow">MES · 実績収集登録</div>
          <h1 class="iar-hero__title">切断実績収集登録</h1>
        </div>
      </div>
      <div class="iar-hero__chips">
        <span class="iar-chip iar-chip--blue"><i>①</i>生産日</span>
        <span class="iar-chip iar-chip--violet"><i>②</i>ライン</span>
        <span class="iar-chip iar-chip--teal"><i>③</i>製品</span>
        <span class="iar-chip iar-chip--amber"><i>④</i>生産数</span>
        <span class="iar-chip iar-chip--indigo"><i>⑤</i>時間</span>
        <span class="iar-chip iar-chip--rose"><i>⑥</i>差異</span>
        <span class="iar-chip iar-chip--slate"><i>⑦</i>備考</span>
      </div>
    </header>

    <section class="iar-panel iar-panel--form iar-rise iar-rise--d1" :class="{ 'iar-panel--edit': isEdit }">
      <div class="iar-panel__head">
        <div class="iar-panel__title-wrap">
          <span class="iar-panel__dot" />
          <span class="iar-panel__title">{{ isEdit ? `編集中 #${editingRowId}` : '実績入力' }}</span>
          <el-tag v-if="isEdit" type="warning" size="small" effect="dark" round>編集</el-tag>
          <el-radio-group v-model="entryMode" class="car-mode-switch">
            <el-radio-button value="single">個別入力</el-radio-button>
            <el-radio-button value="batch">指示から一括入力</el-radio-button>
          </el-radio-group>
        </div>
        <div
          v-if="entryMode === 'single' && timeSummary.shiftMin != null"
          class="iar-panel__badge iar-panel__badge--live"
        >
          作業 {{ formatMinutesLabel(timeSummary.workMin ?? 0) }}
        </div>
      </div>

      <div v-show="entryMode === 'batch'" class="car-batch">
        <div class="car-batch__toolbar">
          <div class="car-batch__date">
            <span class="car-batch__label">生産日</span>
            <el-date-picker
              v-model="form.productionDay"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              :clearable="false"
              class="car-batch__date-picker"
              @change="onProductionDayChange"
            />
            <el-button circle :icon="ArrowLeft" title="前日" aria-label="前日" @click="shiftProductionDay(-1)" />
            <el-button class="car-batch__today" @click="goProductionDayToday">今日</el-button>
            <el-button circle :icon="ArrowRight" title="翌日" aria-label="翌日" @click="shiftProductionDay(1)" />
          </div>
          <el-select
            v-model="batchLineFilter"
            clearable
            value-on-clear=""
            placeholder="ライン（全て）"
            class="car-batch__line"
          >
            <el-option v-for="l in batchLineOptions" :key="l" :label="l" :value="l" />
          </el-select>
          <el-button type="primary" :icon="Refresh" :loading="batchLoading" class="car-batch__load" @click="loadBatch">
            指示を読込
          </el-button>
          <div class="car-batch__stats">
            <span class="car-batch__stat">生産完了 <b>{{ visibleBatchRows.length }}</b> 件</span>
            <span class="car-batch__stat car-batch__stat--done">登録済 <b>{{ batchRegisteredCount }}</b> 件</span>
            <span class="car-batch__stat car-batch__stat--sel">選択 <b>{{ selectedBatchRows.length }}</b> 件</span>
          </div>
        </div>

        <div ref="batchTableWrapRef" class="car-batch__table-wrap" @keydown="onBatchNavKeydown">
          <el-table
            v-loading="batchLoading"
            :data="visibleBatchRows"
            row-key="key"
            border
            max-height="560"
            class="car-batch__table"
            :row-class-name="batchRowClass"
            empty-text="生産完了の切断指示がありません（生産日を選んで「指示を読込」）"
          >
            <el-table-column width="48" align="center" header-align="center">
              <template #header>
                <el-checkbox
                  :model-value="allVisibleSelected"
                  :indeterminate="someVisibleSelected"
                  @change="toggleAllVisible"
                />
              </template>
              <template #default="{ row }">
                <el-checkbox v-model="row.selected" />
              </template>
            </el-table-column>
            <el-table-column prop="line" label="ライン" width="110" show-overflow-tooltip />
            <el-table-column prop="productCd" label="CD" width="96" show-overflow-tooltip />
            <el-table-column prop="productName" label="製品名" min-width="150" show-overflow-tooltip />
            <el-table-column label="計画" width="72" align="right" header-align="right">
              <template #default="{ row }">
                <span class="car-batch__num">{{ row.plannedQty ?? '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="生産" width="96" align="center" header-align="center" class-name="cb-col cb-col--qty">
              <template #default="{ row, $index }">
                <div :data-bnav="`${$index}-0`">
                  <el-input
                    :model-value="row.actualQty == null ? '' : String(row.actualQty)"
                    inputmode="numeric"
                    class="car-batch__qty"
                    @update:model-value="(v: string) => onBatchQtyInput(row, v)"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="差異" width="68" align="right" header-align="right">
              <template #default="{ row }">
                <span class="car-batch__num car-batch__num--var">{{ batchVariance(row) ?? '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="開始" width="96" align="center" header-align="center" class-name="cb-col cb-col--start">
              <template #header>
                <div class="cb-th">
                  <span>開始</span>
                  <small>0800 → 08:00</small>
                </div>
              </template>
              <template #default="{ row, $index }">
                <div :data-bnav="`${$index}-1`">
                  <el-input
                    :model-value="row.startedText"
                    inputmode="numeric"
                    maxlength="5"
                    placeholder="08:30"
                    class="car-batch__time"
                    @update:model-value="(v: string) => onBatchTimeInput(row, 'startedText', v)"
                    @blur="onBatchTimeBlur(row, 'startedText')"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="終了" width="96" align="center" header-align="center" class-name="cb-col cb-col--end">
              <template #header>
                <div class="cb-th">
                  <span>終了</span>
                  <small>1700 → 17:00</small>
                </div>
              </template>
              <template #default="{ row, $index }">
                <div :data-bnav="`${$index}-2`">
                  <el-input
                    :model-value="row.endedText"
                    inputmode="numeric"
                    maxlength="5"
                    placeholder="17:00"
                    class="car-batch__time"
                    @update:model-value="(v: string) => onBatchTimeInput(row, 'endedText', v)"
                    @blur="onBatchTimeBlur(row, 'endedText')"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="休憩(分)" width="88" align="center" header-align="center" class-name="cb-col cb-col--break">
              <template #default="{ row, $index }">
                <div :data-bnav="`${$index}-3`">
                  <el-input-number
                    v-model="row.breakMin"
                    :min="0"
                    :max="999"
                    :controls="false"
                    class="car-batch__min"
                    @change="row.error = ''"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="停止(分)" width="88" align="center" header-align="center" class-name="cb-col cb-col--stop">
              <template #default="{ row, $index }">
                <div :data-bnav="`${$index}-4`">
                  <el-input-number
                    v-model="row.stopMin"
                    :min="0"
                    :max="999"
                    :controls="false"
                    class="car-batch__min"
                    @change="row.error = ''"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="作業" width="96" align="center" header-align="center">
              <template #default="{ row }">
                <span
                  class="car-batch__work"
                  :class="{ 'car-batch__work--alert': (batchWorkMin(row) ?? 0) < 0 }"
                >
                  {{ formatBatchWorkMin(row) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="備考" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.remarks" maxlength="500" placeholder="任意" class="car-batch__remarks" />
              </template>
            </el-table-column>
            <el-table-column label="状態" width="128" align="center" header-align="center" fixed="right">
              <template #default="{ row }">
                <span v-if="row.error" class="car-batch__error">{{ row.error }}</span>
                <el-tag v-else-if="isBatchRowRegistered(row)" type="success" effect="dark" round>登録済</el-tag>
                <el-tag v-else type="info" effect="plain" round>未登録</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="car-batch__footer">
          <span class="car-batch__tip">Enter キーで 開始 → 終了 → 休憩 → 停止 → 次の行の開始 へ移動します</span>
          <el-button
            v-if="canCreate"
            type="primary"
            class="iar-btn-save car-batch__submit"
            :loading="batchSaving"
            :disabled="!selectedBatchRows.length"
            @click="submitBatch"
          >
            選択行を一括登録（{{ selectedBatchRows.length }}件）
          </el-button>
        </div>
      </div>

      <div v-show="entryMode === 'single'" class="iar-form">
        <div class="iar-form__row iar-form__row--triple">
          <div class="iar-field iar-field--c1">
            <label class="iar-field__label"><span class="iar-step iar-step--1">①</span>生産日</label>
            <div class="iar-field__date-nav">
              <el-date-picker
                v-model="form.productionDay"
                type="date"
                value-format="YYYY-MM-DD"
                format="YYYY-MM-DD"
                :clearable="false"
                size="default"
                class="iar-field__control iar-field__date"
                @change="onProductionDayChange"
              />
              <div class="iar-date-nav">
                <el-button
                  type="default"
                  size="small"
                  circle
                  :icon="ArrowLeft"
                  title="前日"
                  aria-label="前日"
                  @click="shiftProductionDay(-1)"
                />
                <el-button
                  type="default"
                  size="small"
                  class="iar-date-nav__today"
                  @click="goProductionDayToday"
                >
                  今日
                </el-button>
                <el-button
                  type="default"
                  size="small"
                  circle
                  :icon="ArrowRight"
                  title="翌日"
                  aria-label="翌日"
                  @click="shiftProductionDay(1)"
                />
              </div>
            </div>
          </div>
          <div class="iar-field iar-field--c2">
            <label class="iar-field__label"><span class="iar-step iar-step--2">②</span>ライン</label>
            <el-select
              v-model="form.productionLine"
              filterable
              allow-create
              default-first-option
              clearable
              placeholder="選択または入力"
              class="iar-field__control"
              :loading="loadingLines"
            >
              <template #prefix><el-icon><User /></el-icon></template>
              <el-option
                v-for="u in lineOptions"
                :key="u.line_name"
                :label="lineLabel(u.line_name)"
                :value="u.line_name"
              />
            </el-select>
          </div>
          <div class="iar-field iar-field--c3">
            <label class="iar-field__label"><span class="iar-step iar-step--3">③</span>製品名</label>
            <el-select
              v-if="!isEdit"
              v-model="form.productCd"
              filterable
              placeholder="選択"
              class="iar-field__control"
              :loading="loadingProducts"
              :disabled="!lineSelected"
              @change="onProductChange"
            >
              <el-option
                v-for="p in products"
                :key="p.product_code"
                :label="p.product_name"
                :value="p.product_code ?? ''"
              />
            </el-select>
            <el-input v-else :model-value="form.productName" disabled class="iar-field__control" />
          </div>
        </div>

        <p v-if="!isEdit && !lineSelected" class="iar-form__lock-hint iar-form__lock-hint--pulse">
          <el-icon><Warning /></el-icon>
          ② ラインを選択すると、③ 製品名を入力できます
        </p>
        <p v-else-if="!productSelected" class="iar-form__lock-hint iar-form__lock-hint--pulse">
          <el-icon><Warning /></el-icon>
          ③ 製品名を選択すると、生産数・時間・差異・備考を入力できます
        </p>

        <div class="iar-form__below" :class="{ 'iar-form__below--locked': !productSelected }">
        <div class="iar-form__row--qty-time">
                <div class="iar-qty iar-field--c4">
          <label class="iar-field__label"><span class="iar-step iar-step--4">④</span>生産数</label>
          <div class="iar-qty__panel">
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">計画</span>
              <el-input
                :model-value="formatQtyInputValue(form.plannedQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="計画"
                @update:model-value="onPlannedQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">生産</span>
              <el-input
                :model-value="formatQtyInputValue(form.actualQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="生産"
                @update:model-value="onActualQtyInput"
              />
            </div>
          </div>
        </div>

        <div class="iar-time iar-field--c5">
          <label class="iar-field__label iar-time__heading">
            <span class="iar-step iar-step--5">⑤</span>生産時間
            <el-icon class="iar-time__icon"><Clock /></el-icon>
            <span class="iar-time__hint">開始・終了は 4 桁で入力（例：0800 → 08:00）</span>
          </label>
          <div class="iar-time__grid">
            <div class="iar-time__cell iar-time__cell--start">
              <span>開始</span>
              <el-input
                ref="startedAtInputRef"
                :model-value="startedAtText"
                :disabled="!productSelected"
                inputmode="numeric"
                maxlength="5"
                placeholder="08:30"
                class="iar-field__control iar-time__input"
                @update:model-value="onStartedAtInput"
                @blur="onStartedAtBlur"
                @keydown="onStartedAtEnter"
              />
            </div>
            <div class="iar-time__cell iar-time__cell--end">
              <span>終了</span>
              <el-input
                ref="endedAtInputRef"
                :model-value="endedAtText"
                :disabled="!productSelected"
                inputmode="numeric"
                maxlength="5"
                placeholder="17:00"
                class="iar-field__control iar-time__input"
                @update:model-value="onEndedAtInput"
                @blur="onEndedAtBlur"
                @keydown="onEndedAtEnter"
              />
            </div>
            <div class="iar-time__cell iar-time__cell--break">
              <span>休憩</span>
              <div class="iar-time__num">
                <el-input-number
                  ref="breakMinInputRef"
                  v-model="form.breakMin"
                  :min="0"
                  :max="999"
                  :step="1"
                  :disabled="!productSelected"
                  :controls="false"
                  @keydown="onBreakMinEnter"
                />
                <em>分</em>
              </div>
            </div>
            <div class="iar-time__cell iar-time__cell--stop">
              <span>停止</span>
              <div class="iar-time__num">
                <el-input-number
                  ref="stopMinInputRef"
                  v-model="form.stopMin"
                  :min="0"
                  :max="999"
                  :step="1"
                  :disabled="!productSelected"
                  :controls="false"
                  @keydown="onStopMinEnter"
                />
                <em>分</em>
              </div>
            </div>
          </div>
          <transition name="iar-fade">
            <p v-if="timeSummary.shiftMin != null" class="iar-time__preview">
              シフト <b>{{ formatMinutesLabel(timeSummary.shiftMin) }}</b>
              <span v-if="timeSummary.endsNextDay" class="iar-time__next-day">（終了は翌日）</span>
              · 休憩 <b>{{ timeSummary.breakMin }}</b>分
              · 停止 <b>{{ timeSummary.stopMin }}</b>分
            </p>
          </transition>
        </div>
        </div>

        <div class="iar-variance iar-field--c6">
          <label class="iar-field__label">
            <span class="iar-step iar-step--6">⑥</span>差異
          </label>
          <el-input
            :model-value="formatQtyInputValue(computedVariance)"
            :disabled="!productSelected"
            inputmode="numeric"
            class="iar-field__control iar-field__qty"
            placeholder="自動計算（手入力可）"
            @update:model-value="onVarianceQtyInput"
          />
          <p class="iar-variance__hint">計画 − 生産（未入力時は自動）</p>
        </div>

        <div class="iar-remarks iar-field--c7 iar-form__footer">
          <div class="iar-remarks__row">
            <label class="iar-field__label iar-remarks__label">
              <span class="iar-step iar-step--7">⑦</span>備考
              <el-icon><ChatLineSquare /></el-icon>
            </label>
            <el-input
              v-model="form.registrationNote"
              ref="remarksInputRef"
              class="iar-remarks__input"
              maxlength="500"
              placeholder="任意"
              :disabled="!productSelected"
            />
            <div class="iar-remarks__actions">
              <el-button
                v-if="canSave"
                type="primary"
                class="iar-btn-save"
                :loading="saving"
                :disabled="!productSelected"
                @click="submitForm"
              >
                保存
              </el-button>
              <el-button class="iar-btn-clear" @click="resetForm()">クリア</el-button>
            </div>
          </div>
        </div>
        </div>
      </div>
    </section>

    <section class="iar-panel iar-panel--table iar-rise iar-rise--d2">
      <div class="iar-panel__head">
        <div class="iar-panel__title-wrap">
          <span class="iar-panel__dot iar-panel__dot--teal" />
          <span class="iar-panel__title">登録一覧</span>
          <span class="iar-panel__date">{{ productionDay }}</span>
          <span class="iar-count">{{ filteredRows.length }}件</span>
          <span class="iar-summary iar-summary--qty">生産数合計 {{ listSummaryQtyLabel }}</span>
          <span class="iar-summary iar-summary--eff">平均能率 {{ listSummaryEfficiencyLabel }}</span>
        </div>
        <div class="iar-panel__tools">
          <el-select
            v-model="lineFilterName"
            clearable
            filterable
            allow-create
            default-first-option
            placeholder="ライン"
            size="small"
            class="iar-filter"
            :loading="loadingLines"
          >
            <el-option
              v-for="u in lineOptions"
              :key="u.line_name"
              :label="lineLabel(u.line_name)"
              :value="u.line_name"
            />
          </el-select>
          <el-button
            size="small"
            round
            class="car-btn-refresh"
            :icon="Refresh"
            :loading="loading"
            @click="loadRows"
          >
            更新
          </el-button>
        </div>
      </div>

      <div class="iar-table-wrap">
        <el-table
          v-loading="loading"
          :data="filteredRows"
          size="small"
          stripe
          border
          class="iar-table"
          empty-text="データがありません"
          highlight-current-row
          :row-class-name="({ row }) => (row.id === editingRowId ? 'iar-table__row--active' : '')"
          @row-click="(row) => canEditRow(row) && onEditRow(row)"
        >
                    <el-table-column label="生産日" width="102" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__date">{{ row.production_day ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="ライン" width="96" align="left" header-align="left" show-overflow-tooltip>
            <template #default="{ row }">{{ lineLabel(row.production_line) }}</template>
          </el-table-column>
          <el-table-column prop="product_cd" label="CD" width="84" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="128" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column label="計画" width="64" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.planned_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="生産" width="64" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.actual_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="差異" width="56" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.quantity_variance ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="能率" width="56" align="right" header-align="right">
            <template #default="{ row }">
              <span
                class="iar-table__efficiency"
                :class="{ 'iar-table__efficiency--alert': isEfficiencyRateOutOfRange(row) }"
              >
                {{ formatEfficiencyRate(row) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="作業" width="60" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatWorkHours(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="休憩" width="60" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatBreakMin(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="停止" width="60" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatStopMin(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="取得元" width="72" align="center" header-align="center">
            <template #default="{ row }">
              <el-tag
                :type="dataSourceTagType(row)"
                size="small"
                effect="light"
                class="iar-table__source"
              >
                {{ dataSourceLabel(row) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remarks" label="備考" min-width="72" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column
            v-if="canEdit || canDelete"
            label="操作"
            width="76"
            fixed="right"
            align="center"
            header-align="center"
            class-name="iar-table__op-col"
          >
            <template #default="{ row }">
              <div class="iar-table__ops">
                <el-button
                  v-if="canEditRow(row)"
                  type="primary"
                  link
                  :icon="Edit"
                  @click.stop="onEditRow(row)"
                />
                <el-button
                  v-if="canDeleteRow(row)"
                  type="danger"
                  link
                  :icon="Delete"
                  :loading="deletingRowId === row.id"
                  @click.stop="deleteRow(row)"
                />
                <el-tooltip
                  v-if="!canEditRow(row) && !canDelete && isRowMesInProgress(row)"
                  content="MES生産中"
                >
                  <span class="iar-table__lock">—</span>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.iar {
  --iar-c1: #3b82f6;
  --iar-c2: #8b5cf6;
  --iar-c3: #14b8a6;
  --iar-c4: #f59e0b;
  --iar-c5: #6366f1;
  --iar-c6: #f43f5e;
  --iar-c7: #64748b;
  --iar-surface: rgba(255, 255, 255, 0.88);
  --iar-border: rgba(148, 163, 184, 0.22);
  --iar-shadow: 0 4px 24px rgba(15, 23, 42, 0.07), 0 1px 3px rgba(15, 23, 42, 0.06);
  --iar-shadow-lg: 0 12px 40px rgba(15, 23, 42, 0.1), 0 2px 8px rgba(15, 23, 42, 0.05);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 0 16px;
  min-height: 100%;
}

.iar__bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.iar__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(72px);
  opacity: 0.45;
  animation: iar-float 18s ease-in-out infinite;
}

.iar__orb--1 {
  width: 340px;
  height: 340px;
  top: -80px;
  right: 8%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.35), transparent 70%);
}

.iar__orb--2 {
  width: 280px;
  height: 280px;
  left: -60px;
  top: 28%;
  background: radial-gradient(circle, rgba(20, 184, 166, 0.28), transparent 70%);
  animation-delay: -6s;
}

.iar__orb--3 {
  width: 220px;
  height: 220px;
  right: 20%;
  bottom: 8%;
  background: radial-gradient(circle, rgba(244, 63, 94, 0.18), transparent 70%);
  animation-delay: -12s;
}

@keyframes iar-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(12px, -16px) scale(1.04); }
  66% { transform: translate(-8px, 10px) scale(0.98); }
}

@keyframes iar-rise {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.iar-rise {
  position: relative;
  z-index: 1;
  animation: iar-rise 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.iar-rise--d1 { animation-delay: 0.06s; }
.iar-rise--d2 { animation-delay: 0.12s; }

.iar-fade-enter-active,
.iar-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.iar-fade-enter-from,
.iar-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Hero */
.iar-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
  padding: 10px 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%);
  border: 1px solid var(--iar-border);
  box-shadow: var(--iar-shadow);
  backdrop-filter: blur(12px);
}

.iar-hero__main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.iar-hero__icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(145deg, #6366f1, #4f46e5);
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.iar-hero__glow {
  position: absolute;
  inset: -4px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.4), transparent);
  filter: blur(8px);
  z-index: -1;
  animation: iar-pulse 3s ease-in-out infinite;
}

@keyframes iar-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.iar-hero__eyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #6366f1;
}

.iar-hero__title {
  margin: 2px 0 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.iar-hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.iar-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid transparent;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.iar-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}

.iar-chip i {
  font-style: normal;
  font-size: 10px;
  opacity: 0.85;
}

.iar-chip--blue { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
.iar-chip--violet { background: #f5f3ff; color: #6d28d9; border-color: #ddd6fe; }
.iar-chip--teal { background: #f0fdfa; color: #0f766e; border-color: #99f6e4; }
.iar-chip--amber { background: #fffbeb; color: #b45309; border-color: #fde68a; }
.iar-chip--indigo { background: #eef2ff; color: #4338ca; border-color: #c7d2fe; }
.iar-chip--rose { background: #fff1f2; color: #be123c; border-color: #fecdd3; }
.iar-chip--slate { background: #f8fafc; color: #475569; border-color: #e2e8f0; }

/* Panel */
.iar-panel {
  border-radius: 14px;
  background: var(--iar-surface);
  border: 1px solid var(--iar-border);
  box-shadow: var(--iar-shadow);
  backdrop-filter: blur(10px);
  overflow: hidden;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}

.iar-panel:hover {
  box-shadow: var(--iar-shadow-lg);
}

.iar-panel--edit {
  border-color: rgba(245, 158, 11, 0.45);
  box-shadow: 0 8px 32px rgba(245, 158, 11, 0.12), var(--iar-shadow);
}

.iar-panel__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(255, 255, 255, 0.6));
  border-bottom: 1px solid var(--iar-border);
}

.iar-panel__title-wrap {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.iar-panel__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(145deg, #6366f1, #8b5cf6);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.iar-panel__dot--teal {
  background: linear-gradient(145deg, #14b8a6, #0d9488);
  box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.2);
}

.iar-panel__title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.iar-panel__date {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  padding: 2px 8px;
  border-radius: 6px;
  background: #f1f5f9;
}

.iar-count {
  font-size: 11px;
  font-weight: 700;
  color: #0f766e;
  padding: 2px 8px;
  border-radius: 999px;
  background: #ccfbf1;
}

.iar-summary {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.iar-summary--qty {
  color: #1d4ed8;
  background: #dbeafe;
}

.iar-summary--eff {
  color: #6d28d9;
  background: #ede9fe;
}

.iar-panel__badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
}

.iar-panel__badge--live {
  color: #4338ca;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
  border: 1px solid #c7d2fe;
  animation: iar-pulse 2.5s ease-in-out infinite;
}

.iar-panel__tools {
  display: flex;
  align-items: center;
  gap: 6px;
}

.iar-filter {
  width: 140px;
}

.iar-panel--form .iar-panel__head {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(241, 245, 249, 0.75) 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset;
}

.iar-panel--form .iar-panel__dot {
  animation: iar-dot-glow 2.8s ease-in-out infinite;
}

@keyframes iar-dot-glow {
  0%, 100% { box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18); }
  50% { box-shadow: 0 0 0 5px rgba(99, 102, 241, 0.32); }
}

@keyframes iar-hint-pulse {
  0%, 100% { border-color: rgba(148, 163, 184, 0.35); box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04); }
  50% { border-color: rgba(99, 102, 241, 0.45); box-shadow: 0 4px 14px rgba(99, 102, 241, 0.1); }
}

@keyframes iar-unlock {
  from { opacity: 0.55; transform: translateY(6px); filter: blur(0.4px); }
  to { opacity: 1; transform: translateY(0); filter: blur(0); }
}

@keyframes iar-defect-pop {
  0% { transform: scale(1); }
  40% { transform: scale(1.03); }
  100% { transform: scale(1); }
}

/* Form */
.iar-form {
  padding: 12px 14px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.iar-form__lock-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 9px 12px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.88));
  border: 1px dashed rgba(148, 163, 184, 0.4);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

.iar-form__lock-hint--pulse {
  animation: iar-hint-pulse 2.4s ease-in-out infinite;
}

.iar-form__lock-hint .el-icon {
  color: #6366f1;
  font-size: 15px;
}

.iar-form__below {
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: opacity 0.28s ease, filter 0.28s ease;
}

.iar-form__below:not(.iar-form__below--locked) {
  animation: iar-unlock 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.iar-form__below--locked {
  opacity: 0.48;
  filter: saturate(0.65);
  pointer-events: none;
}

.iar-form__row--triple {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.iar-form__row--triple > .iar-field {
  position: relative;
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.82));
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 4px 14px rgba(15, 23, 42, 0.06),
    0 1px 3px rgba(15, 23, 42, 0.04);
  transition:
    transform 0.22s cubic-bezier(0.34, 1.25, 0.64, 1),
    box-shadow 0.22s ease,
    border-color 0.22s ease;
  overflow: hidden;
}

.iar-form__row--triple > .iar-field::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  opacity: 0.92;
}

.iar-form__row--triple > .iar-field:hover {
  transform: translateY(-2px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 1),
    0 8px 22px rgba(15, 23, 42, 0.09),
    0 2px 6px rgba(15, 23, 42, 0.05);
}

.iar-field--c1::before { background: linear-gradient(90deg, #2563eb, #60a5fa); }
.iar-field--c2::before { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
.iar-field--c3::before { background: linear-gradient(90deg, #0d9488, #2dd4bf); }

.iar-field--c1:hover { border-color: rgba(59, 130, 246, 0.28); }
.iar-field--c2:hover { border-color: rgba(139, 92, 246, 0.28); }
.iar-field--c3:hover { border-color: rgba(20, 184, 166, 0.28); }

@media (max-width: 900px) {
  .iar-form__row--triple {
    grid-template-columns: 1fr;
  }
}

.iar-field__date-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.iar-field__date-nav .iar-field__date {
  flex: 1;
  min-width: 0;
}

.iar-date-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.iar-date-nav__today {
  min-width: 42px;
  padding: 0 8px;
  font-size: 12px;
  font-weight: 700;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.85);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.iar-date-nav__today:hover {
  transform: translateY(-1px);
}

.iar-date-nav :deep(.el-button.is-circle) {
  box-shadow: 0 2px 5px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.15s ease;
}

.iar-date-nav :deep(.el-button.is-circle:hover) {
  transform: translateY(-1px);
}

.iar-form__row--qty-time {
  display: grid;
  grid-template-columns: minmax(240px, 32%) minmax(0, 1fr);
  gap: 10px;
  align-items: stretch;
}

.iar-form__row--qty-time .iar-qty,
.iar-form__row--qty-time .iar-time {
  min-width: 0;
  height: 100%;
}

.iar-form__row--qty-time .iar-qty__panel {
  flex-wrap: nowrap;
  gap: 8px;
}

.iar-form__row--qty-time .iar-qty__cell {
  flex: 1 1 0;
  min-width: 0;
}

.iar-form__row--qty-time .iar-qty__bridge {
  padding-bottom: 8px;
  gap: 4px;
}

.iar-form__row--qty-time .iar-time__grid {
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1.15fr) minmax(0, 0.8fr) minmax(0, 0.8fr);
  gap: 6px;
}

.iar-form__row--qty-time .iar-time__cell {
  padding: 5px 6px;
}

@media (max-width: 1100px) {
  .iar-form__row--qty-time {
    grid-template-columns: 1fr;
  }

  .iar-form__row--qty-time .iar-qty__panel {
    flex-wrap: wrap;
  }
}

.iar-qty {
  position: relative;
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(155deg, rgba(255, 251, 235, 0.95) 0%, rgba(254, 243, 199, 0.45) 100%);
  border: 1px solid rgba(245, 158, 11, 0.28);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 4px 16px rgba(245, 158, 11, 0.12),
    0 1px 3px rgba(15, 23, 42, 0.05);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.iar-qty:hover {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 6px 20px rgba(245, 158, 11, 0.16),
    0 2px 6px rgba(15, 23, 42, 0.06);
}

.iar-qty__hint {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  color: #b45309;
}

.iar-qty__hint--warn {
  color: #dc2626;
}

.iar-qty__panel {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.iar-qty__cell {
  flex: 1 1 120px;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 251, 235, 0.65));
  border: 1px solid rgba(245, 158, 11, 0.28);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 2px 6px rgba(180, 83, 9, 0.08);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, opacity 0.2s ease;
}

.iar-qty__cell:focus-within {
  transform: translateY(-1px);
  border-color: rgba(245, 158, 11, 0.55);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 1),
    0 0 0 3px rgba(245, 158, 11, 0.14),
    0 4px 12px rgba(245, 158, 11, 0.15);
}

.iar-qty__cell--derived {
  border-style: dashed;
  border-color: rgba(148, 163, 184, 0.45);
  background: rgba(248, 250, 252, 0.9);
  opacity: 0.92;
}

.iar-qty__cell-label {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #92400e;
}

.iar-qty__cell--derived .iar-qty__cell-label {
  color: #64748b;
}

.iar-qty__bridge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 10px;
  color: #b45309;
  font-weight: 800;
  font-size: 13px;
  flex-shrink: 0;
}

.iar-qty__upb {
  min-width: 28px;
  text-align: center;
  padding: 3px 8px;
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(254, 243, 199, 0.8));
  border: 1px solid rgba(245, 158, 11, 0.25);
  box-shadow: 0 2px 4px rgba(180, 83, 9, 0.1);
  font-size: 12px;
}

.iar-qty__op {
  opacity: 0.7;
}

.iar-qty__warn {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 8px 0 0;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.45;
  color: #b45309;
  background: rgba(254, 243, 199, 0.65);
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.iar-qty__warn .el-icon {
  margin-top: 1px;
  flex-shrink: 0;
  font-size: 14px;
}

.iar-field__label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}

.iar-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 4px rgba(15, 23, 42, 0.18);
  transition: transform 0.2s cubic-bezier(0.34, 1.3, 0.64, 1);
}

.iar-field__label:hover .iar-step {
  transform: scale(1.08);
}

.iar-step--1 { background: linear-gradient(145deg, #3b82f6, #2563eb); }
.iar-step--2 { background: linear-gradient(145deg, #8b5cf6, #7c3aed); }
.iar-step--3 { background: linear-gradient(145deg, #14b8a6, #0d9488); }
.iar-step--4 { background: linear-gradient(145deg, #f59e0b, #d97706); }
.iar-step--5 { background: linear-gradient(145deg, #6366f1, #4f46e5); }
.iar-step--6 { background: linear-gradient(145deg, #f43f5e, #e11d48); }
.iar-step--7 { background: linear-gradient(145deg, #64748b, #475569); }

.iar-field__control {
  width: 100%;
}

.iar-field__qty {
  width: 100% !important;
}

.iar-field__qty :deep(.el-input__wrapper) {
  width: 100%;
}

.iar-field--c1 :deep(.el-input__wrapper),
.iar-field--c2 :deep(.el-input__wrapper),
.iar-field--c3 :deep(.el-input__wrapper) {
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.iar-field--c1 :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15), 0 2px 8px rgba(59, 130, 246, 0.1);
}

.iar-field--c2 :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15), 0 2px 8px rgba(139, 92, 246, 0.1);
}

.iar-field--c3 :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15), 0 2px 8px rgba(20, 184, 166, 0.1);
}

.iar-qty :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15), 0 2px 8px rgba(245, 158, 11, 0.1);
}

/* Time block */
.iar-time {
  position: relative;
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(155deg, rgba(238, 242, 255, 0.95) 0%, rgba(224, 231, 255, 0.5) 100%);
  border: 1px solid rgba(99, 102, 241, 0.22);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 4px 16px rgba(99, 102, 241, 0.1),
    0 1px 3px rgba(15, 23, 42, 0.05);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.iar-time:hover {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 6px 20px rgba(99, 102, 241, 0.14),
    0 2px 6px rgba(15, 23, 42, 0.06);
}

.iar-time__heading {
  margin-bottom: 6px;
}

.iar-time__icon {
  color: #6366f1;
  font-size: 14px;
}

.iar-time__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1.15fr) minmax(0, 0.8fr) minmax(0, 0.8fr);
  gap: 6px;
}

.iar-time__cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 7px 8px;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.75));
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 2px 8px rgba(15, 23, 42, 0.05);
  transition: transform 0.2s cubic-bezier(0.34, 1.2, 0.64, 1), box-shadow 0.2s ease, border-color 0.2s ease;
}

.iar-time__cell:hover {
  transform: translateY(-2px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 1),
    0 6px 16px rgba(15, 23, 42, 0.08);
}

.iar-time__cell:focus-within {
  transform: translateY(-2px);
}

.iar-time__cell--start:focus-within {
  border-color: rgba(37, 99, 235, 0.45);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 1), 0 0 0 3px rgba(59, 130, 246, 0.14), 0 4px 12px rgba(59, 130, 246, 0.12);
}

.iar-time__cell--end:focus-within {
  border-color: rgba(124, 58, 237, 0.45);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 1), 0 0 0 3px rgba(139, 92, 246, 0.14), 0 4px 12px rgba(139, 92, 246, 0.12);
}

.iar-time__cell--break:focus-within {
  border-color: rgba(13, 148, 136, 0.45);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 1), 0 0 0 3px rgba(20, 184, 166, 0.14), 0 4px 12px rgba(20, 184, 166, 0.12);
}

.iar-time__cell--stop:focus-within {
  border-color: rgba(225, 29, 72, 0.4);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 1), 0 0 0 3px rgba(244, 63, 94, 0.12), 0 4px 12px rgba(244, 63, 94, 0.1);
}

.iar-time__cell > span:first-child {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.iar-time__cell--start > span:first-child { color: #2563eb; }
.iar-time__cell--end > span:first-child { color: #7c3aed; }
.iar-time__cell--break > span:first-child { color: #0d9488; }
.iar-time__cell--stop > span:first-child { color: #e11d48; }

.iar-time__input {
  width: 100%;
}

.iar-time__input :deep(.el-input__wrapper) {
  padding-left: 8px;
  padding-right: 8px;
}

.iar-time__input :deep(.el-input__inner) {
  font-size: 12px;
  text-align: center;
  letter-spacing: 0.04em;
}

.iar-time__num {
  display: flex;
  align-items: center;
  gap: 4px;
}

.iar-time__num :deep(.el-input-number) {
  width: 56px;
  min-width: 56px;
}

.iar-time__num :deep(.el-input-number .el-input__inner) {
  text-align: center;
  padding-left: 4px;
  padding-right: 4px;
}

.iar-time__num em {
  font-style: normal;
  font-size: 11px;
  color: #64748b;
  flex-shrink: 0;
}

.iar-time__preview {
  margin: 8px 0 0;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 11px;
  color: #4338ca;
  background: linear-gradient(90deg, rgba(238, 242, 255, 0.9), rgba(224, 231, 255, 0.5));
  border: 1px solid rgba(199, 210, 254, 0.6);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.iar-time__preview b {
  font-weight: 800;
}

.iar-time__next-day {
  margin-left: 2px;
  font-weight: 700;
  color: #7c3aed;
}

/* Defects */
.iar-field--c6 {
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(165deg, rgba(255, 241, 242, 0.35), rgba(248, 250, 252, 0.9));
  border: 1px solid rgba(244, 63, 94, 0.14);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 4px 16px rgba(244, 63, 94, 0.06);
}

.iar-defects__total {
  margin-left: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, #fb7185, #e11d48);
  box-shadow: 0 2px 8px rgba(225, 29, 72, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.25);
  animation: iar-defect-pop 0.35s ease;
}

.iar-defects__box {
  padding: 8px 10px 10px;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(243, 244, 246, 0.95));
  border: 1px solid rgba(203, 213, 225, 0.65);
  box-shadow: inset 0 2px 6px rgba(15, 23, 42, 0.04);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.iar-defects__group + .iar-defects__group {
  margin-top: 10px;
}

.iar-defects__group-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  padding: 4px 8px 6px;
  margin-bottom: 4px;
  border-radius: 8px;
  border-bottom: none;
  background: rgba(255, 255, 255, 0.65);
  border-left: 3px solid #0d9488;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.iar-defects__group:nth-child(1) .iar-defects__group-head {
  border-left-color: #f59e0b;
  background: linear-gradient(90deg, rgba(255, 251, 235, 0.85), rgba(255, 255, 255, 0.5));
}

.iar-defects__group:nth-child(2) .iar-defects__group-head {
  border-left-color: #6366f1;
  background: linear-gradient(90deg, rgba(238, 242, 255, 0.85), rgba(255, 255, 255, 0.5));
}

.iar-defects__group:nth-child(3) .iar-defects__group-head {
  border-left-color: #14b8a6;
  background: linear-gradient(90deg, rgba(240, 253, 250, 0.85), rgba(255, 255, 255, 0.5));
}

.iar-defects__group:nth-child(1) .iar-defects__group-name { color: #b45309; }
.iar-defects__group:nth-child(2) .iar-defects__group-name { color: #4338ca; }
.iar-defects__group:nth-child(3) .iar-defects__group-name { color: #0f766e; }

.iar-defects__group-label {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.iar-defects__group-name {
  font-size: 13px;
  font-weight: 800;
  color: #0f766e;
  line-height: 1.2;
}

.iar-defects__grid {
  display: grid;
  gap: 4px;
  width: max-content;
  padding-top: 4px;
}

.iar-defect {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  padding: 4px 5px;
  border-radius: 8px;
  border: 1px solid rgba(203, 213, 225, 0.85);
  background: #fff;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.iar-defect:hover {
  border-color: #93c5fd;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.1);
}

.iar-defect--active {
  border-color: #f59e0b;
  background: #fffbeb;
  box-shadow:
    0 0 0 2px rgba(245, 158, 11, 0.2),
    0 4px 12px rgba(245, 158, 11, 0.18);
  animation: iar-defect-pop 0.32s ease;
}

.iar-defect__name {
  font-size: 11px;
  font-weight: 700;
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #1f2937;
}

.iar-defect__ctrl {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2px;
}

.iar-defect__btn {
  width: 24px !important;
  height: 24px !important;
  padding: 0 !important;
  flex-shrink: 0;
}

.iar-defect__btn :deep(.el-icon) {
  font-size: 12px;
}

.iar-defect__btn--minus {
  --el-button-bg-color: #fff;
  --el-button-border-color: #cbd5e1;
  --el-button-text-color: #475569;
  --el-button-hover-bg-color: #f8fafc;
  --el-button-hover-border-color: #94a3b8;
  --el-button-hover-text-color: #334155;
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.iar-defect__btn--minus:active {
  transform: scale(0.92);
}

.iar-defect__btn--plus {
  --el-button-bg-color: #38bdf8;
  --el-button-border-color: #0ea5e9;
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: #0ea5e9;
  --el-button-hover-border-color: #0284c7;
  --el-button-hover-text-color: #fff;
  box-shadow: 0 3px 8px rgba(14, 165, 233, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.iar-defect__btn--plus:hover {
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.iar-defect__btn--plus:active {
  transform: scale(0.92);
}

.iar-defect__qty-input {
  flex: 1;
  min-width: 0;
  max-width: 40px;
}

.iar-defect__qty-input :deep(.el-input__wrapper) {
  padding: 0 2px;
  box-shadow: none;
  background: transparent;
  min-height: 24px;
}

.iar-defect__qty-input :deep(.el-input__inner) {
  text-align: center;
  font-size: 15px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #111827;
  height: 24px;
  line-height: 24px;
}

.iar-defect__qty-input :deep(.el-input__inner::placeholder) {
  color: #9ca3af;
  opacity: 1;
}

/* Remarks */
.iar-form__footer {
  margin: 4px -2px 0;
  padding: 12px 12px 14px;
  border-radius: 0 0 12px 12px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.4), rgba(241, 245, 249, 0.85));
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.iar-remarks__row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.iar-remarks__label {
  margin-bottom: 0;
  flex-shrink: 0;
}

.iar-remarks__input {
  width: 450px;
  flex-shrink: 0;
}

.iar-remarks__input :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: linear-gradient(180deg, #fff, #f8fafc);
  box-shadow:
    inset 0 1px 3px rgba(15, 23, 42, 0.04),
    0 2px 6px rgba(15, 23, 42, 0.04);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.iar-remarks__input :deep(.el-input__wrapper.is-focus) {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 2px rgba(15, 23, 42, 0.03),
    0 0 0 3px rgba(100, 116, 139, 0.12),
    0 4px 12px rgba(15, 23, 42, 0.06);
}

.iar-remarks__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  margin-left: auto;
}

.iar-remarks__actions :deep(.el-button) {
  position: relative;
  isolation: isolate;
  height: 32px;
  min-width: 88px;
  padding: 0 20px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  border: none;
  overflow: hidden;
  transition:
    transform 0.16s cubic-bezier(0.34, 1.35, 0.64, 1),
    box-shadow 0.16s ease,
    filter 0.16s ease;
}

.iar-remarks__actions :deep(.el-button::before) {
  content: '';
  position: absolute;
  inset: 0 0 50%;
  border-radius: 10px 10px 0 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0));
  pointer-events: none;
  z-index: 0;
}

.iar-remarks__actions :deep(.el-button span) {
  position: relative;
  z-index: 1;
}

.iar-btn-save {
  color: #fff !important;
  background: linear-gradient(165deg, #a5b4fc 0%, #818cf8 18%, #6366f1 52%, #4f46e5 100%) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.42),
    inset 0 -1px 0 rgba(49, 46, 129, 0.35),
    0 3px 0 #3730a3,
    0 5px 14px rgba(79, 70, 229, 0.38),
    0 1px 3px rgba(15, 23, 42, 0.12);
  text-shadow: 0 1px 0 rgba(30, 27, 75, 0.35);
}

.iar-btn-save:hover:not(.is-disabled) {
  transform: translateY(-2px);
  filter: brightness(1.04) saturate(1.05);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 -1px 0 rgba(49, 46, 129, 0.3),
    0 4px 0 #3730a3,
    0 8px 22px rgba(79, 70, 229, 0.45),
    0 2px 6px rgba(15, 23, 42, 0.14);
}

.iar-btn-save:active:not(.is-disabled) {
  transform: translateY(2px);
  filter: brightness(0.98);
  box-shadow:
    inset 0 2px 6px rgba(30, 27, 75, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 1px 0 #3730a3,
    0 2px 6px rgba(79, 70, 229, 0.25);
}

.iar-btn-save.is-disabled,
.iar-btn-save:disabled {
  transform: none !important;
  filter: grayscale(0.15) opacity(0.72);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 2px 0 #4338ca,
    0 3px 8px rgba(79, 70, 229, 0.2) !important;
}

.iar-btn-clear {
  color: #475569 !important;
  background: linear-gradient(165deg, #fff 0%, #f8fafc 45%, #f1f5f9 100%) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 -1px 0 rgba(148, 163, 184, 0.2),
    0 3px 0 #cbd5e1,
    0 4px 12px rgba(100, 116, 139, 0.16),
    0 1px 2px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(203, 213, 225, 0.85) !important;
}

.iar-remarks__actions :deep(.iar-btn-clear::before) {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0));
}

.iar-btn-clear:hover {
  transform: translateY(-2px);
  color: #334155 !important;
  filter: brightness(1.02);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 1),
    inset 0 -1px 0 rgba(148, 163, 184, 0.15),
    0 4px 0 #cbd5e1,
    0 7px 18px rgba(100, 116, 139, 0.2),
    0 2px 4px rgba(15, 23, 42, 0.08);
}

.iar-btn-clear:active {
  transform: translateY(2px);
  box-shadow:
    inset 0 2px 5px rgba(148, 163, 184, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    0 1px 0 #cbd5e1,
    0 2px 5px rgba(100, 116, 139, 0.12);
}

/* Table */
.iar-table-wrap {
  padding: 0 10px 10px;
}

.iar-table {
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  --el-table-border-color: rgba(148, 163, 184, 0.2);
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: rgba(248, 250, 252, 0.98);
  --el-fill-color-lighter: #fafbfd;
}

.iar-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.iar-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  letter-spacing: 0.02em;
}

.iar-table :deep(.el-table__header th .cell),
.iar-table :deep(.el-table__body td .cell) {
  padding: 0 8px;
  line-height: 1.45;
}

.iar-table :deep(.el-table__body td) {
  font-size: 12px;
  color: #334155;
  transition: background 0.2s ease;
}

.iar-table :deep(.el-table__row) {
  cursor: pointer;
}

.iar-table :deep(.iar-table__row--active td) {
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.06)) !important;
}

.iar-table :deep(.el-table__row:hover > td) {
  background: rgba(248, 250, 252, 0.95) !important;
}

.iar-table :deep(.iar-table__op-col .cell) {
  padding: 0 4px;
}

.iar-table__ops {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-height: 24px;
}

.iar-table__date {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: #1e293b;
}

.iar-table__source {
  border: none;
}

.iar-table__time {
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  color: #475569;
  white-space: nowrap;
}

.iar-table__qty {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #b45309;
}

.iar-table__defect {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  color: #94a3b8;
  background: #f1f5f9;
}

.iar-table__defect--on {
  color: #be123c;
  background: #ffe4e6;
}

.iar-table__efficiency {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  color: #0369a1;
}

.iar-table__efficiency--alert {
  color: #dc2626;
}

.iar-table__pause {
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  color: #64748b;
}

.iar-table__lock {
  color: #cbd5e1;
}

.iar-variance {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.iar-variance__hint {
  margin: 0;
  font-size: 11px;
  color: #94a3b8;
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（切断実績収集登録 / スチール・シアン系）
 * ============================================================ */
.car-modern {
  background: linear-gradient(160deg, #f0f9ff 0%, #ecfeff 45%, #f8fafc 100%);
}

/* 入場・常時ループのアニメーションは表示速度優先で停止 */
.car-modern .iar-rise,
.car-modern .iar-form__below:not(.iar-form__below--locked),
.car-modern .iar-panel--form .iar-panel__dot,
.car-modern .iar-panel__badge--live,
.car-modern .iar-form__lock-hint--pulse {
  animation: none;
}

/* ---------- ヒーロー ---------- */
.car-modern .iar-hero {
  isolation: isolate;
  overflow: hidden;
  padding: 14px 18px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(125deg, #0f172a 0%, #1e3a5f 32%, #0369a1 66%, #06b6d4 100%);
  backdrop-filter: none;
  box-shadow:
    0 18px 36px -18px rgba(3, 105, 161, 0.6),
    0 4px 12px -6px rgba(6, 182, 212, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.car-modern .car-hero-fx {
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}
.car-modern .fx-orb {
  position: absolute;
  border-radius: 50%;
}
.car-modern .orb-a {
  width: 220px;
  height: 220px;
  top: -110px;
  left: 30%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0) 70%);
}
.car-modern .orb-b {
  width: 200px;
  height: 200px;
  bottom: -130px;
  right: 12%;
  background: radial-gradient(circle, rgba(165, 243, 252, 0.4) 0%, rgba(165, 243, 252, 0) 70%);
}
.car-modern .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  -webkit-mask-image: radial-gradient(ellipse at 12% 50%, #000 0%, transparent 65%);
  mask-image: radial-gradient(ellipse at 12% 50%, #000 0%, transparent 65%);
}
.car-modern .iar-hero__icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow:
    0 3px 0 rgba(15, 23, 42, 0.55),
    0 10px 18px -8px rgba(15, 23, 42, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transform: perspective(300px) rotateX(8deg) rotateY(-10deg);
}
.car-modern .iar-hero__eyebrow {
  color: rgba(255, 255, 255, 0.82);
}
.car-modern .iar-hero__title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
  text-shadow: 0 2px 6px rgba(15, 23, 42, 0.35);
}
.car-modern .iar-chip {
  font-weight: 700;
  box-shadow: 0 2px 0 rgba(15, 23, 42, 0.35);
}
.car-modern .iar-chip:hover {
  transform: none;
  box-shadow: 0 2px 0 rgba(15, 23, 42, 0.35);
}

/* ---------- パネル（入力＝steel / 一覧＝teal / 編集中＝amber） ---------- */
.car-modern .iar-panel {
  --pc: #0369a1;
  --pc-soft: #e0f2fe;
  background: #fff;
  border: 1px solid #dbe7f0;
  border-top: 3px solid var(--pc);
  backdrop-filter: none;
  box-shadow: 0 10px 24px -18px rgba(3, 105, 161, 0.45), 0 1px 2px rgba(15, 23, 42, 0.04);
}
.car-modern .iar-panel:hover {
  box-shadow: 0 10px 24px -18px rgba(3, 105, 161, 0.45), 0 1px 2px rgba(15, 23, 42, 0.04);
}
.car-modern .iar-panel--table {
  --pc: #0d9488;
  --pc-soft: #ccfbf1;
}
.car-modern .iar-panel--edit {
  --pc: #d97706;
  --pc-soft: #fef3c7;
}
.car-modern .iar-panel__head,
.car-modern .iar-panel--form .iar-panel__head {
  background: linear-gradient(90deg, var(--pc-soft) 0%, #fff 70%);
  border-bottom: 1px solid #e2e8f0;
  box-shadow: none;
}
.car-modern .iar-panel__dot,
.car-modern .iar-panel__dot--teal {
  background: var(--pc);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--pc) 20%, transparent);
}
.car-modern .iar-panel__title {
  font-weight: 800;
  color: color-mix(in srgb, var(--pc) 65%, #0f172a);
}
.car-modern .iar-panel__date,
.car-modern .iar-count,
.car-modern .iar-summary {
  font-weight: 800;
  border: 1px solid transparent;
}
.car-modern .iar-panel__date {
  color: #334155;
  background: #fff;
  border-color: #e2e8f0;
}
.car-modern .iar-count {
  color: #0f766e;
  background: #ccfbf1;
}
.car-modern .iar-summary--qty {
  color: #1d4ed8;
  background: #dbeafe;
}
.car-modern .iar-summary--eff {
  color: #6d28d9;
  background: #ede9fe;
}
.car-modern .iar-panel__badge--live {
  color: #075985;
  background: #e0f2fe;
  border-color: #bae6fd;
}

/* ---------- 入力ブロック：文字のにじみを防ぐため移動・拡大はしない ---------- */
.car-modern .iar-form__row--triple > .iar-field {
  background: #fff;
  border-color: #e2e8f0;
  box-shadow:
    0 2px 0 #e2e8f0,
    0 8px 16px -12px rgba(15, 23, 42, 0.3);
}
.car-modern .iar-form__row--triple > .iar-field:hover,
.car-modern .iar-qty:hover,
.car-modern .iar-time:hover,
.car-modern .iar-time__cell:hover,
.car-modern .iar-time__cell:focus-within,
.car-modern .iar-qty__cell:focus-within,
.car-modern .iar-remarks__input :deep(.el-input__wrapper.is-focus),
.car-modern .iar-field__label:hover .iar-step {
  transform: none;
}
.car-modern .iar-form__lock-hint {
  color: #075985;
  background: #f0f9ff;
  border: 1px dashed #7dd3fc;
  box-shadow: none;
}
.car-modern .iar-form__lock-hint .el-icon {
  color: #0284c7;
}
.car-modern .iar-form__below--locked {
  opacity: 0.55;
  filter: none;
}
.car-modern .iar-date-nav__today {
  color: #fff;
  background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
  border: 1px solid #0369a1;
  box-shadow: 0 2px 0 #075985;
}
.car-modern .iar-date-nav__today:hover {
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 3px 0 #075985;
}
.car-modern .iar-date-nav__today:active {
  transform: translateY(1px);
  box-shadow: 0 1px 0 #075985;
}

/* 保存ボタン：無効時も半透明にせずくっきり表示 */
.car-modern .iar-btn-save.is-disabled,
.car-modern .iar-btn-save:disabled {
  color: #64748b !important;
  background: #f1f5f9 !important;
  filter: none;
  text-shadow: none;
  box-shadow: 0 2px 0 #cbd5e1 !important;
}

/* ---------- 一覧 ---------- */
.car-modern .car-btn-refresh {
  font-weight: 600;
  color: #fff;
  background: #0d9488;
  border: 1px solid #0d9488;
}
.car-modern .car-btn-refresh:hover,
.car-modern .car-btn-refresh:focus {
  color: #fff;
  background: #14b8a6;
  border-color: #14b8a6;
}
.car-modern .iar-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f0fdfa 0%, #ccfbf1 100%) !important;
  color: #115e59;
  font-weight: 800;
  box-shadow: inset 0 -2px 0 #5eead4;
}
.car-modern .iar-table :deep(.el-table__row:hover > td) {
  background: #f0fdfa !important;
}
.car-modern .iar-table :deep(.el-table__row:hover > td:first-child) {
  box-shadow: inset 3px 0 0 #0d9488;
}

/* ---------- 実績入力：大きめの文字・細い枠線・ブロック別のアクセント色 ---------- */
.car-modern .iar-panel--form .iar-field--c1 { --fc: #2563eb; --fc-soft: #eff6ff; }
.car-modern .iar-panel--form .iar-field--c2 { --fc: #7c3aed; --fc-soft: #f5f3ff; }
.car-modern .iar-panel--form .iar-field--c3 { --fc: #0d9488; --fc-soft: #f0fdfa; }
.car-modern .iar-panel--form .iar-field--c4 { --fc: #d97706; --fc-soft: #fffbeb; }
.car-modern .iar-panel--form .iar-field--c5 { --fc: #4f46e5; --fc-soft: #eef2ff; }
.car-modern .iar-panel--form .iar-field--c6 { --fc: #e11d48; --fc-soft: #fff1f2; }
.car-modern .iar-panel--form .iar-field--c7 { --fc: #475569; --fc-soft: #f8fafc; }
.car-modern .iar-panel--form .iar-time__cell--start { --fc: #2563eb; --fc-soft: #eff6ff; }
.car-modern .iar-panel--form .iar-time__cell--end { --fc: #7c3aed; --fc-soft: #f5f3ff; }
.car-modern .iar-panel--form .iar-time__cell--break { --fc: #0d9488; --fc-soft: #f0fdfa; }
.car-modern .iar-panel--form .iar-time__cell--stop { --fc: #e11d48; --fc-soft: #fff1f2; }

.car-modern .iar-panel--form .iar-panel__title {
  font-size: 16px;
}
.car-modern .iar-panel--form .iar-panel__badge {
  font-size: 13px;
  padding: 4px 10px;
}
.car-modern .iar-panel--form .iar-form {
  padding: 14px 16px 0;
  gap: 12px;
}
.car-modern .iar-panel--form .iar-form__below {
  gap: 12px;
}

/* ブロック：細いグレー枠＋左端のアクセント色 */
.car-modern .iar-panel--form .iar-form__row--triple > .iar-field,
.car-modern .iar-panel--form .iar-qty,
.car-modern .iar-panel--form .iar-time,
.car-modern .iar-panel--form .iar-variance {
  padding: 10px 14px 12px;
  border: 1px solid #e2e8f0;
  border-left: 3px solid var(--fc);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.car-modern .iar-panel--form .iar-form__footer {
  margin: 0 -16px;
  padding: 12px 16px;
  border: none;
  border-top: 1px solid #e2e8f0;
  border-radius: 0;
  background: #f8fafc;
  box-shadow: none;
}
.car-modern .iar-panel--form .iar-form__row--triple > .iar-field::before {
  display: none;
}

/* ラベル */
.car-modern .iar-panel--form .iar-field__label {
  gap: 8px;
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}
.car-modern .iar-panel--form .iar-remarks__label {
  margin-bottom: 0;
}
.car-modern .iar-panel--form .iar-step {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  font-size: 13px;
  box-shadow: none;
}
.car-modern .iar-panel--form .iar-time__icon {
  font-size: 16px;
  color: var(--fc);
}
.car-modern .iar-panel--form .iar-qty__cell-label {
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 700;
  color: #b45309;
}
.car-modern .iar-panel--form .iar-time__cell > span:first-child {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--fc);
}
.car-modern .iar-panel--form .iar-time__num em {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}
.car-modern .iar-panel--form .iar-variance__hint {
  font-size: 13px;
  color: #64748b;
}
.car-modern .iar-panel--form .iar-time__preview {
  font-size: 13px;
  color: #3730a3;
  background: #f5f7ff;
  border: 1px solid #e0e7ff;
  box-shadow: none;
}
.car-modern .iar-panel--form .iar-form__lock-hint {
  font-size: 14px;
  border: 1px dashed #bae6fd;
}

/* 小セル（生産数・時間）：枠なしの淡い背景 */
.car-modern .iar-panel--form .iar-qty__cell,
.car-modern .iar-panel--form .iar-time__cell {
  padding: 6px 8px 8px;
  background: #f8fafc;
  border: 1px solid transparent;
  border-radius: 6px;
  box-shadow: none;
}
.car-modern .iar-panel--form .iar-qty__cell:focus-within,
.car-modern .iar-panel--form .iar-time__cell:focus-within {
  border-color: transparent;
  background: var(--fc-soft);
  box-shadow: none;
}
.car-modern .iar-panel--form .iar-form__row--qty-time .iar-time__grid {
  gap: 8px;
}

/* 入力コンポーネント共通：1px グレー枠、フォーカス時のみ色付き */
.car-modern .iar-panel--form :deep(.el-input__wrapper),
.car-modern .iar-panel--form :deep(.el-select__wrapper) {
  min-height: 38px;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 0 0 1px #cbd5e1 inset;
  transition: box-shadow 0.15s ease;
}
.car-modern .iar-panel--form :deep(.el-input__wrapper:hover),
.car-modern .iar-panel--form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #94a3b8 inset;
}
.car-modern .iar-panel--form :deep(.el-input__wrapper.is-focus),
.car-modern .iar-panel--form :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px var(--fc, #0369a1) inset,
    0 0 0 3px color-mix(in srgb, var(--fc, #0369a1) 14%, transparent);
}
.car-modern .iar-panel--form :deep(.el-input.is-disabled .el-input__wrapper),
.car-modern .iar-panel--form :deep(.el-select__wrapper.is-disabled) {
  background: #f1f5f9;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.car-modern .iar-panel--form :deep(.el-input__inner),
.car-modern .iar-panel--form :deep(.el-select__selection) {
  font-size: 15px;
  font-weight: 500;
  color: #0f172a;
}
.car-modern .iar-panel--form :deep(.el-select__placeholder:not(.is-transparent)) {
  color: #0f172a;
}
.car-modern .iar-panel--form :deep(.el-input.is-disabled .el-input__inner) {
  color: #475569;
  -webkit-text-fill-color: #475569;
}
.car-modern .iar-panel--form :deep(.el-input__inner::placeholder) {
  font-weight: 500;
  color: #94a3b8;
}
.car-modern .iar-panel--form :deep(.el-input__prefix .el-icon),
.car-modern .iar-panel--form :deep(.el-select__prefix .el-icon) {
  font-size: 15px;
  color: #94a3b8;
}

/* 数量・時刻は少し大きめの数字で */
.car-modern .iar-panel--form .iar-field__qty :deep(.el-input__wrapper),
.car-modern .iar-panel--form .iar-time__input :deep(.el-input__wrapper),
.car-modern .iar-panel--form .iar-time__num :deep(.el-input__wrapper) {
  min-height: 40px;
}
.car-modern .iar-panel--form .iar-field__qty :deep(.el-input__inner) {
  font-size: 18px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.car-modern .iar-panel--form .iar-time__input :deep(.el-input__inner),
.car-modern .iar-panel--form .iar-time__num :deep(.el-input__inner) {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
}
.car-modern .iar-panel--form .iar-time__num :deep(.el-input-number) {
  width: 76px;
  min-width: 76px;
}
.car-modern .iar-panel--form .iar-time__input :deep(.el-input__inner::placeholder),
.car-modern .iar-panel--form .car-batch__time :deep(.el-input__inner::placeholder) {
  font-weight: 400;
  color: #cbd5e1;
}
.car-modern .iar-panel--form .iar-time__hint {
  margin-left: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
}
.car-batch__table :deep(.cb-th) {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.25;
}
.car-batch__table :deep(.cb-th small) {
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
  white-space: nowrap;
}

/* 日付ナビ・保存/クリア */
.car-modern .iar-panel--form .iar-date-nav :deep(.el-button.is-circle) {
  width: 32px;
  height: 32px;
  font-size: 14px;
  color: #475569;
  border: 1px solid #cbd5e1;
  box-shadow: none;
}
.car-modern .iar-panel--form .iar-date-nav__today {
  height: 32px;
  min-width: 52px;
  font-size: 14px;
  font-weight: 600;
  color: #0369a1;
  background: #fff;
  border: 1px solid #cbd5e1;
  box-shadow: none;
}
.car-modern .iar-panel--form .iar-date-nav__today:hover {
  color: #0369a1;
  background: #f0f9ff;
  border-color: #7dd3fc;
  transform: none;
  box-shadow: none;
}
.car-modern .iar-panel--form .iar-remarks__actions :deep(.el-button) {
  height: 38px;
  min-width: 100px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.car-modern .iar-panel--form .iar-remarks__actions :deep(.el-button::before) {
  display: none;
}
.car-modern .iar-panel--form .iar-btn-save {
  color: #fff !important;
  background: #0369a1 !important;
  border: 1px solid #0369a1 !important;
  box-shadow: none !important;
  text-shadow: none;
  transform: none !important;
  filter: none !important;
}
.car-modern .iar-panel--form .iar-btn-save:hover:not(.is-disabled) {
  background: #0284c7 !important;
  border-color: #0284c7 !important;
}
.car-modern .iar-panel--form .iar-btn-save.is-disabled {
  color: #94a3b8 !important;
  background: #f1f5f9 !important;
  border-color: #e2e8f0 !important;
}
.car-modern .iar-panel--form .iar-btn-clear {
  color: #475569 !important;
  background: #fff !important;
  border: 1px solid #cbd5e1 !important;
  box-shadow: none !important;
  transform: none !important;
  filter: none !important;
}
.car-modern .iar-panel--form .iar-btn-clear:hover {
  background: #f8fafc !important;
  border-color: #94a3b8 !important;
}

/* ---------- 入力モード切替 ---------- */
.car-mode-switch {
  margin-left: 12px;
  --el-color-primary: #0369a1;
}
.car-mode-switch :deep(.el-radio-button__inner) {
  height: 32px;
  padding: 0 14px;
  font-size: 14px;
  font-weight: 600;
  line-height: 30px;
}

/* ---------- 指示から一括入力 ---------- */
.car-batch {
  --fc: #0369a1;
  --fc-soft: #e0f2fe;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px 16px;
}
.car-batch__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}
.car-batch__date {
  display: flex;
  align-items: center;
  gap: 6px;
}
.car-batch__label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}
.car-batch__date-picker {
  width: 160px !important;
}
.car-batch__date :deep(.el-button) {
  height: 32px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  border: 1px solid #cbd5e1;
}
.car-batch__date :deep(.el-button.is-circle) {
  width: 32px;
}
.car-batch__line {
  width: 170px;
}
.car-batch__load {
  height: 36px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 600;
  --el-button-bg-color: #0369a1;
  --el-button-border-color: #0369a1;
  --el-button-hover-bg-color: #0284c7;
  --el-button-hover-border-color: #0284c7;
}
.car-batch__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
}
.car-batch__stat {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #075985;
  background: #e0f2fe;
}
.car-batch__stat b {
  font-size: 15px;
  font-weight: 700;
}
.car-batch__stat--done {
  color: #15803d;
  background: #dcfce7;
}
.car-batch__stat--sel {
  color: #4338ca;
  background: #e0e7ff;
}

.car-batch .car-batch__time {
  width: 84px;
}
.car-batch .car-batch__min {
  width: 72px;
}
.car-batch .car-batch__qty {
  width: 80px;
}
.car-batch :deep(.car-batch__time .el-input__inner),
.car-batch :deep(.car-batch__min .el-input__inner),
.car-batch :deep(.car-batch__qty .el-input__inner) {
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.car-batch__table-wrap {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.car-batch__table {
  width: 100%;
  --el-table-border-color: #e2e8f0;
}
.car-batch__table :deep(.el-table__header th) {
  background: #f8fafc !important;
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}
.car-batch__table :deep(.el-table__body td) {
  font-size: 15px;
  color: #0f172a;
}
.car-batch__table :deep(.el-table__body td .cell) {
  padding: 0 6px;
}
.car-batch__table :deep(.cb-col--qty) { --fc: #d97706; --fc-soft: #fffbeb; }
.car-batch__table :deep(.cb-col--start) { --fc: #2563eb; --fc-soft: #eff6ff; }
.car-batch__table :deep(.cb-col--end) { --fc: #7c3aed; --fc-soft: #f5f3ff; }
.car-batch__table :deep(.cb-col--break) { --fc: #0d9488; --fc-soft: #f0fdfa; }
.car-batch__table :deep(.cb-col--stop) { --fc: #e11d48; --fc-soft: #fff1f2; }
.car-batch__table :deep(th.cb-col) {
  color: var(--fc);
  box-shadow: inset 0 -2px 0 color-mix(in srgb, var(--fc) 55%, #fff);
}
.car-modern .iar-panel--form .car-batch__table :deep(.el-input__wrapper) {
  min-height: 36px;
}
.car-batch__table :deep(.car-batch__row--selected > td) {
  background: #f8fbff !important;
}
.car-batch__table :deep(.car-batch__row--registered > td) {
  background: #f6fdf8 !important;
  color: #64748b;
}
.car-batch__table :deep(.car-batch__row--error > td) {
  background: #fef2f2 !important;
}
.car-batch__num {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #334155;
}
.car-batch__num--var {
  color: #be123c;
}
.car-batch__work {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #4338ca;
}
.car-batch__work--alert {
  color: #dc2626;
}
.car-batch__error {
  font-size: 13px;
  font-weight: 700;
  color: #dc2626;
  line-height: 1.3;
}

.car-batch__footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 -16px -16px;
  padding: 12px 16px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}
.car-batch__tip {
  font-size: 13px;
  color: #64748b;
}
.car-batch__submit {
  height: 38px;
  min-width: 200px;
  margin-left: auto;
  padding: 0 20px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

@media (prefers-reduced-motion: reduce) {
  .car-modern .iar-date-nav__today,
  .car-modern .car-btn-refresh {
    transition: none;
    transform: none !important;
  }
}

</style>
