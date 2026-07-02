<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
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
import { useChamferingManualRegistration } from './useChamferingManualRegistration'

defineOptions({ name: 'ChamferingActualCollectionRegistration' })

const reg = useChamferingManualRegistration()
const {
  productionDay,
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
  computedTotalQty,
  loadRows,
  onProductChange,
  formatQtyInputValue,
  onChamferPlannedQtyInput,
  onChamferActualQtyInput,
  onSwPlannedQtyInput,
  onSwActualQtyInput,
  onChamferDefectQtyInput,
  onSwDefectQtyInput,
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
  <div class="iar">
    <div class="iar__bg" aria-hidden="true">
      <div class="iar__orb iar__orb--1" />
      <div class="iar__orb iar__orb--2" />
      <div class="iar__orb iar__orb--3" />
    </div>

    <header class="iar-hero iar-rise">
      <div class="iar-hero__main">
        <div class="iar-hero__icon">
          <el-icon :size="22"><DataLine /></el-icon>
          <span class="iar-hero__glow" />
        </div>
        <div>
          <div class="iar-hero__eyebrow">MES · 実績収集登録</div>
          <h1 class="iar-hero__title">面取実績収集登録</h1>
        </div>
      </div>
      <div class="iar-hero__chips">
        <span class="iar-chip iar-chip--blue"><i>①</i>生産日</span>
        <span class="iar-chip iar-chip--violet"><i>②</i>ライン</span>
        <span class="iar-chip iar-chip--teal"><i>③</i>製品</span>
        <span class="iar-chip iar-chip--amber"><i>④</i>生産数</span>
        <span class="iar-chip iar-chip--indigo"><i>⑤</i>時間</span>
        <span class="iar-chip iar-chip--rose"><i>⑥</i>不良</span>
        <span class="iar-chip iar-chip--slate"><i>⑦</i>備考</span>
      </div>
    </header>

    <section class="iar-panel iar-panel--form iar-rise iar-rise--d1" :class="{ 'iar-panel--edit': isEdit }">
      <div class="iar-panel__head">
        <div class="iar-panel__title-wrap">
          <span class="iar-panel__dot" />
          <span class="iar-panel__title">{{ isEdit ? `編集中 #${editingRowId}` : '実績入力' }}</span>
          <el-tag v-if="isEdit" type="warning" size="small" effect="dark" round>編集</el-tag>
        </div>
        <div v-if="timeSummary.shiftMin != null" class="iar-panel__badge iar-panel__badge--live">
          作業 {{ formatMinutesLabel(timeSummary.workMin ?? 0) }}
        </div>
      </div>

      <div class="iar-form">
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
          ③ 製品名を選択すると、生産数・時間・不良・備考を入力できます
        </p>

        <div class="iar-form__below" :class="{ 'iar-form__below--locked': !productSelected }">
        <div class="iar-form__row--qty-time">
                        <div class="iar-qty iar-field--c4">
          <label class="iar-field__label">
            <span class="iar-step iar-step--4">④</span>生産数
            <span v-if="computedTotalQty > 0" class="iar-qty__hint">総数 {{ computedTotalQty }}</span>
          </label>
          <div class="iar-qty__panel iar-qty__panel--quad">
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">面取計画</span>
              <el-input
                :model-value="formatQtyInputValue(form.chamferPlannedQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="面取計画"
                @update:model-value="onChamferPlannedQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">面取生産</span>
              <el-input
                :model-value="formatQtyInputValue(form.chamferActualQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="面取生産"
                @update:model-value="onChamferActualQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">SW計画</span>
              <el-input
                :model-value="formatQtyInputValue(form.swPlannedQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="SW計画"
                @update:model-value="onSwPlannedQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">SW生産</span>
              <el-input
                :model-value="formatQtyInputValue(form.swActualQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="SW生産"
                @update:model-value="onSwActualQtyInput"
              />
            </div>
          </div>
        </div>

        <div class="iar-time iar-field--c5">
          <label class="iar-field__label iar-time__heading">
            <span class="iar-step iar-step--5">⑤</span>生産時間
            <el-icon class="iar-time__icon"><Clock /></el-icon>
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

                <div class="iar-defects-simple iar-field--c6">
          <label class="iar-field__label"><span class="iar-step iar-step--6">⑥</span>不良</label>
          <div class="iar-qty__panel">
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">面取不良</span>
              <el-input
                :model-value="formatQtyInputValue(form.chamferDefectQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onChamferDefectQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">SW不良</span>
              <el-input
                :model-value="formatQtyInputValue(form.swDefectQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onSwDefectQtyInput"
              />
            </div>
          </div>
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
          <el-button size="small" round :icon="Refresh" :loading="loading" @click="loadRows">更新</el-button>
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
          @row-click="(row) => canEditRow(row) && loadRowIntoForm(row)"
        >
                              <el-table-column label="生産日" width="102" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__date">{{ row.production_day ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="ライン" width="88" align="left" header-align="left" show-overflow-tooltip>
            <template #default="{ row }">{{ lineLabel(row.production_line) }}</template>
          </el-table-column>
          <el-table-column prop="product_cd" label="CD" width="76" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="110" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column label="面取" width="52" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.chamfer_actual_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="SW" width="52" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.sw_actual_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="総数" width="56" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.total_production_qty ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="能率" width="52" align="right" header-align="right">
            <template #default="{ row }">
              <span
                class="iar-table__efficiency"
                :class="{ 'iar-table__efficiency--alert': isEfficiencyRateOutOfRange(row) }"
              >
                {{ formatEfficiencyRate(row) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="作業" width="56" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatWorkHours(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="休憩" width="56" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatBreakMin(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="停止" width="56" align="center" header-align="center">
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
                  @click.stop="loadRowIntoForm(row)"
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

.iar-qty__panel--quad {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.iar-defects-simple {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

</style>
