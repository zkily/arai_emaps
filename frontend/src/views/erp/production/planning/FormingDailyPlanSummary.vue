<template>
  <div class="fdp-page">
    <header class="fdp-page__bar">
      <div class="fdp-page__bar-main">
        <h1 class="fdp-page__title">{{ t('formingDailyPlan.title') }}</h1>
        <div class="fdp-page__toolbar">
          <div class="month-quick" role="group">
            <button type="button" class="month-quick__btn" :disabled="loading" @click="shiftMonth(-1)">{{ t('formingDailyPlan.prevMonth') }}</button>
            <button type="button" class="month-quick__btn month-quick__btn--mid" :disabled="loading" @click="shiftMonth(0)">{{ t('formingDailyPlan.thisMonth') }}</button>
            <button type="button" class="month-quick__btn" :disabled="loading" @click="shiftMonth(1)">{{ t('formingDailyPlan.nextMonth') }}</button>
          </div>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            size="small"
            unlink-panels
            :clearable="false"
            class="fdp-page__range"
          />
          <el-checkbox v-model="includeForecast" size="small">{{ t('formingDailyPlan.includeForecast') }}</el-checkbox>
          <el-button type="primary" size="small" :loading="loading" @click="loadSummary">{{ t('common.query') }}</el-button>
        </div>
      </div>
      <div class="fdp-page__actions">
        <el-select
          v-model="currentScenarioId"
          clearable
          size="small"
          :placeholder="t('formingDailyPlan.selectScenario')"
          class="fdp-page__scenario-select"
          @change="onScenarioSelect"
        >
          <el-option v-for="s in scenarios" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button size="small" @click="scenarioDrawerVisible = true">{{ t('formingDailyPlan.scenarioManage') }}</el-button>
        <el-button size="small" type="primary" plain :loading="savingScenario" @click="openSaveDialog">{{ t('formingDailyPlan.saveScenario') }}</el-button>
        <el-button size="small" type="warning" plain :disabled="!currentScenarioId" :loading="applying" @click="confirmApply">{{ t('formingDailyPlan.apply') }}</el-button>
      </div>
    </header>

    <el-alert
      v-if="summary && !summary.kpi.has_molding_plan"
      type="warning"
      :closable="false"
      show-icon
      class="fdp-page__warn"
    >
      {{ t('formingDailyPlan.noMoldingPlanWarn') }}
      <router-link to="/erp/production/data-management" class="fdp-page__link">{{ t('formingDailyPlan.openDataMgmt') }}</router-link>
    </el-alert>

    <div v-loading="loading && !summary" class="fdp-page__body">
      <SimulationKpiCards :kpi="summary?.kpi" :scenario-status="currentScenario?.status" />

      <ProcessPlanTotalsPanel
        :totals="summary?.process_plan_totals"
        :order-totals="summary?.order_process_totals"
        :order-matrix-rows="summary?.order_matrix?.rows ?? []"
        :daily-rows="summary?.process_plan_daily_totals"
        :dates="summary?.dates ?? []"
        :matrix-rows="summary?.daily_matrix.rows ?? []"
        :products="summary?.products ?? []"
        :period-start="periodStart"
        :period-end="periodEnd"
        show-daily-table
      />

      <el-tabs v-model="activeTab" class="fdp-tabs" @tab-change="onTabChange">
        <el-tab-pane :label="t('formingDailyPlan.tabDailyPlan')" name="plan" lazy>
          <DailyPlanMatrix
            :loading="loading"
            :dates="summary?.dates ?? []"
            :rows="summary?.daily_matrix.rows ?? []"
            :products="summary?.products ?? []"
            @override-save="onOverrideSave"
            @export="exportMatrixExcel"
          />
        </el-tab-pane>
        <el-tab-pane :label="t('formingDailyPlan.tabForecast')" name="forecast" lazy>
          <OrderForecastPanel :months="orderForecastMonths" />
        </el-tab-pane>
        <el-tab-pane :label="t('formingDailyPlan.tabInventory')" name="inventory" lazy>
          <InventoryTrendChart :summary="summary" :products="summary?.products ?? []" />
        </el-tab-pane>
        <el-tab-pane :label="t('formingDailyPlan.tabCalendar')" name="calendar" lazy>
          <ProcessRunCalendarPanel
            :start-date="periodStart"
            :end-date="periodEnd"
            :dates="summary?.dates ?? []"
            :items="runCalendarItems"
            :loading="calendarLoading"
            @saved="onCalendarSaved"
            @change="onCalendarChange"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <ScenarioManageDrawer
      v-model:visible="scenarioDrawerVisible"
      :scenarios="scenarios"
      @create="openSaveDialog"
      @select="loadScenarioById"
      @apply="confirmApplyRow"
      @delete="confirmDeleteScenario"
    />

    <el-dialog v-model="saveDialogVisible" :title="t('formingDailyPlan.saveScenario')" width="400px">
      <el-form label-width="80px" size="small">
        <el-form-item :label="t('formingDailyPlan.scenarioName')" required>
          <el-input v-model="newScenarioName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="saveDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button size="small" type="primary" :loading="savingScenario" @click="saveScenario">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  applyFormingPlanScenario,
  createFormingPlanScenario,
  deleteFormingPlanScenario,
  getFormingDailyPlanSummary,
  getFormingPlanScenario,
  getOrderForecast,
  getProcessRunDays,
  listFormingPlanScenarios,
  simulateFormingDailyPlan,
  type FormingDailyPlanSummaryData,
  type FormingPlanScenario,
  type OrderForecastMonth,
  type ProcessRunCalendarItem,
} from '@/api/formingDailyPlan'
import { downloadExcelFromJson } from '@/utils/excelExport'
import { getJSTToday } from '@/utils/dateFormat'
import { processLabel } from './components/formingDailyPlanConstants'
import SimulationKpiCards from './components/SimulationKpiCards.vue'
import ProcessPlanTotalsPanel from './components/ProcessPlanTotalsPanel.vue'
import DailyPlanMatrix from './components/DailyPlanMatrix.vue'

const OrderForecastPanel = defineAsyncComponent(() => import('./components/OrderForecastPanel.vue'))
const InventoryTrendChart = defineAsyncComponent(() => import('./components/InventoryTrendChart.vue'))
const ProcessRunCalendarPanel = defineAsyncComponent(() => import('./components/ProcessRunCalendarPanel.vue'))
const ScenarioManageDrawer = defineAsyncComponent(() => import('./components/ScenarioManageDrawer.vue'))

const { t, locale } = useI18n()
let previousLocale: string | undefined

const loading = ref(false)
const calendarLoading = ref(false)
const calendarLoaded = ref(false)
const savingScenario = ref(false)
const applying = ref(false)
const activeTab = ref('plan')
const includeForecast = ref(true)
const summary = ref<FormingDailyPlanSummaryData | null>(null)
const orderForecastMonths = ref<OrderForecastMonth[]>([])
const runCalendarItems = ref<ProcessRunCalendarItem[]>([])
const processOverrides = ref<Record<string, Record<string, Record<string, number>>>>({})

const scenarios = ref<FormingPlanScenario[]>([])
const currentScenarioId = ref<number | undefined>()
const currentScenario = computed(() => scenarios.value.find((s) => s.id === currentScenarioId.value))
const scenarioDrawerVisible = ref(false)
const saveDialogVisible = ref(false)
const newScenarioName = ref('')

const dateRange = ref<[string, string]>([
  dayjs(getJSTToday()).startOf('month').format('YYYY-MM-DD'),
  dayjs(getJSTToday()).endOf('month').format('YYYY-MM-DD'),
])

const periodStart = computed(() => dateRange.value[0])
const periodEnd = computed(() => dateRange.value[1])
const baseMonth = computed(() => dayjs(periodStart.value).format('YYYY-MM'))

let simulateTimer: ReturnType<typeof setTimeout> | null = null

function shiftMonth(delta: number) {
  const base = delta === 0 ? dayjs(getJSTToday()) : dayjs(periodStart.value).add(delta, 'month')
  dateRange.value = [base.startOf('month').format('YYYY-MM-DD'), base.endOf('month').format('YYYY-MM-DD')]
  loadSummary()
}

function jstCompactTimestamp(): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(new Date())
  const pick = (type: string) => parts.find((p) => p.type === type)?.value ?? '00'
  return `${pick('month')}${pick('day')}-${pick('hour')}${pick('minute')}`
}

async function loadScenarios() {
  try {
    const res = await listFormingPlanScenarios()
    scenarios.value = (res as { data?: { items?: FormingPlanScenario[] } }).data?.items ?? []
  } catch {
    scenarios.value = []
  }
}

async function loadRunCalendar() {
  calendarLoading.value = true
  try {
    const res = await getProcessRunDays(periodStart.value, periodEnd.value)
    const data = (res as { data?: { items?: ProcessRunCalendarItem[] } }).data
    runCalendarItems.value = data?.items ?? []
    calendarLoaded.value = true
  } finally {
    calendarLoading.value = false
  }
}

function onTabChange(name: string | number) {
  if (name === 'calendar' && !calendarLoaded.value) {
    void loadRunCalendar()
  }
  if (name === 'forecast' && !includeForecast.value && !orderForecastMonths.value.length) {
    void loadOrderForecastOnly()
  }
}

async function loadSummary() {
  calendarLoaded.value = false
  runCalendarItems.value = []
  loading.value = true
  try {
    const res = await getFormingDailyPlanSummary({
      startDate: periodStart.value,
      endDate: periodEnd.value,
      includeForecastMonths: includeForecast.value,
      baseMonth: baseMonth.value,
      includeOrderMatrix: false,
    })
    summary.value = (res as { data?: FormingDailyPlanSummaryData }).data ?? null
    if (includeForecast.value) {
      orderForecastMonths.value = summary.value?.order_forecast ?? []
    } else {
      void loadOrderForecastOnly()
    }
    if (activeTab.value === 'calendar') {
      void loadRunCalendar()
    }
  } catch {
    ElMessage.error(t('formingDailyPlan.loadFailed'))
    summary.value = null
  } finally {
    loading.value = false
  }
}

async function loadOrderForecastOnly() {
  try {
    const res = await getOrderForecast({ baseMonth: baseMonth.value, months: 2 })
    orderForecastMonths.value = (res as { data?: { months?: OrderForecastMonth[] } }).data?.months ?? []
  } catch {
    orderForecastMonths.value = []
  }
}

function scheduleSimulate() {
  if (simulateTimer) clearTimeout(simulateTimer)
  simulateTimer = setTimeout(() => runSimulate(), 500)
}

async function runSimulate() {
  if (!periodStart.value || !periodEnd.value) return
  loading.value = true
  try {
    const res = await simulateFormingDailyPlan({
      startDate: periodStart.value,
      endDate: periodEnd.value,
      processOverrides: processOverrides.value,
      runCalendarItems: runCalendarItems.value,
      includeForecastMonths: includeForecast.value,
      baseMonth: baseMonth.value,
    })
    summary.value = (res as { data?: FormingDailyPlanSummaryData }).data ?? null
    if (includeForecast.value) {
      orderForecastMonths.value = summary.value?.order_forecast ?? orderForecastMonths.value
    }
  } catch {
    ElMessage.error(t('formingDailyPlan.simulateFailed'))
  } finally {
    loading.value = false
  }
}

function onOverrideSave(payload: { productCd: string; processKey: string; date: string; value: number | null }) {
  const { productCd, processKey, date, value } = payload
  if (!processOverrides.value[productCd]) processOverrides.value[productCd] = {}
  if (!processOverrides.value[productCd][date]) processOverrides.value[productCd][date] = {}
  if (value === null) {
    delete processOverrides.value[productCd][date][processKey]
  } else {
    processOverrides.value[productCd][date][processKey] = value
  }
  scheduleSimulate()
}

function onCalendarSaved(items: ProcessRunCalendarItem[]) {
  runCalendarItems.value = items
  scheduleSimulate()
}

function onCalendarChange(items: ProcessRunCalendarItem[]) {
  runCalendarItems.value = items
}

function openSaveDialog() {
  newScenarioName.value = `${baseMonth.value}-${t('formingDailyPlan.scenarioNameTrial')}-${jstCompactTimestamp()}`
  saveDialogVisible.value = true
}

async function saveScenario() {
  if (!newScenarioName.value.trim()) {
    ElMessage.warning(t('formingDailyPlan.scenarioNameRequired'))
    return
  }
  savingScenario.value = true
  try {
    const res = await createFormingPlanScenario({
      name: newScenarioName.value.trim(),
      startDate: periodStart.value,
      endDate: periodEnd.value,
      baseMonth: baseMonth.value,
      includeForecastMonths: includeForecast.value,
      processOverrides: processOverrides.value,
      runCalendarItems: runCalendarItems.value,
    })
    const id = (res as { data?: { id?: number } }).data?.id
    ElMessage.success(t('formingDailyPlan.scenarioSaved'))
    saveDialogVisible.value = false
    await loadScenarios()
    if (id) currentScenarioId.value = id
  } catch {
    ElMessage.error(t('formingDailyPlan.scenarioSaveFailed'))
  } finally {
    savingScenario.value = false
  }
}

async function loadScenarioById(row: FormingPlanScenario) {
  currentScenarioId.value = row.id
  await onScenarioSelect(row.id)
  scenarioDrawerVisible.value = false
}

async function onScenarioSelect(id: number | undefined) {
  if (!id) return
  try {
    const res = await getFormingPlanScenario(id)
    const data = (res as { data?: { payload?: { process_overrides?: typeof processOverrides.value; run_calendar_snapshot?: ProcessRunCalendarItem[]; last_simulation?: FormingDailyPlanSummaryData } } }).data
    const payload = data?.payload
    if (payload?.process_overrides) processOverrides.value = payload.process_overrides
    if (payload?.run_calendar_snapshot) {
      runCalendarItems.value = payload.run_calendar_snapshot
      calendarLoaded.value = true
    }
    if (payload?.last_simulation) {
      summary.value = payload.last_simulation
    } else {
      await runSimulate()
    }
  } catch {
    ElMessage.error(t('formingDailyPlan.scenarioLoadFailed'))
  }
}

async function confirmApply() {
  if (!currentScenarioId.value) return
  await confirmApplyRow({ id: currentScenarioId.value } as FormingPlanScenario)
}

async function confirmApplyRow(row: FormingPlanScenario) {
  try {
    await ElMessageBox.confirm(t('formingDailyPlan.applyConfirm'), t('formingDailyPlan.apply'), { type: 'warning' })
  } catch {
    return
  }
  applying.value = true
  try {
    const res = await applyFormingPlanScenario(row.id)
    const msg = (res as { message?: string }).message
    ElMessage.success(msg || t('formingDailyPlan.applySuccess'))
    await loadScenarios()
    await loadSummary()
  } catch {
    ElMessage.error(t('formingDailyPlan.applyFailed'))
  } finally {
    applying.value = false
  }
}

async function confirmDeleteScenario(row: FormingPlanScenario) {
  try {
    await ElMessageBox.confirm(t('formingDailyPlan.deleteConfirm'), t('formingDailyPlan.deleteScenario'), { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteFormingPlanScenario(row.id)
    if (currentScenarioId.value === row.id) currentScenarioId.value = undefined
    ElMessage.success(t('formingDailyPlan.deleteSuccess'))
    await loadScenarios()
  } catch {
    ElMessage.error(t('formingDailyPlan.deleteFailed'))
  }
}

async function exportMatrixExcel() {
  if (!summary.value) return
  const rows: Record<string, string | number>[] = []
  for (const r of summary.value.daily_matrix.rows) {
    for (const d of summary.value.dates) {
      const cell = r.by_date[d]
      if (!cell) continue
      rows.push({
        product_cd: r.product_cd,
        process: processLabel(r.process_key),
        date: d,
        molding_plan: cell.molding_plan ?? 0,
        derived_plan: cell.derived_plan ?? 0,
        final_plan: cell.final_plan ?? cell.derived_plan ?? 0,
        override_plan: cell.override_plan ?? '',
      })
    }
  }
  await downloadExcelFromJson(rows, t('formingDailyPlan.exportSheetDailyPlan'), `forming-plan-${periodStart.value}.xlsx`)
}

onMounted(async () => {
  previousLocale = locale.value
  locale.value = 'ja'
  document.title = `${t('formingDailyPlan.title')} - Smart-EMAP`
  await Promise.all([loadScenarios(), loadSummary()])
})

onBeforeUnmount(() => {
  if (previousLocale) locale.value = previousLocale
})

watch(includeForecast, () => {
  if (summary.value) scheduleSimulate()
})
</script>

<style scoped>
.fdp-page {
  --fdp-accent: #6366f1;
  --fdp-surface: #ffffff;
  --fdp-border: #e2e8f0;
  padding: 8px 12px 10px;
  min-height: 100%;
  background: linear-gradient(180deg, #f1f5f9 0%, #f8fafc 120px, #f8fafc 100%);
}
.fdp-page__bar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px 10px;
  background: var(--fdp-surface);
  border: 1px solid var(--fdp-border);
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}
.fdp-page__bar-main {
  flex: 1;
  min-width: 280px;
}
.fdp-page__title {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
}
.fdp-page__title::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 16px;
  margin-right: 8px;
  vertical-align: -2px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--fdp-accent), #8b5cf6);
}
.fdp-page__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.fdp-page__range {
  width: 240px;
}
.fdp-page__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.fdp-page__scenario-select {
  width: 168px;
}
.fdp-page__warn {
  margin-bottom: 6px;
  padding: 6px 10px;
}
.fdp-page__link {
  margin-left: 6px;
}
.fdp-page__body {
  background: var(--fdp-surface);
  border: 1px solid var(--fdp-border);
  border-radius: 10px;
  padding: 8px 10px 6px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
  min-height: 200px;
}
.month-quick {
  display: inline-flex;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
}
.month-quick__btn {
  border: none;
  background: transparent;
  padding: 4px 9px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
}
.month-quick__btn:hover:not(:disabled) {
  background: #e2e8f0;
  color: #0f172a;
}
.month-quick__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.month-quick__btn--mid {
  border-left: 1px solid #cbd5e1;
  border-right: 1px solid #cbd5e1;
  color: var(--fdp-accent);
}
.fdp-tabs {
  margin-top: 4px;
}
.fdp-tabs :deep(.el-tabs__header) {
  margin-bottom: 6px;
}
.fdp-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: #e2e8f0;
}
.fdp-tabs :deep(.el-tabs__item) {
  height: 32px;
  line-height: 32px;
  font-size: 12px;
  font-weight: 600;
  padding: 0 14px;
}
.fdp-tabs :deep(.el-tabs__item.is-active) {
  color: var(--fdp-accent);
}
.fdp-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, var(--fdp-accent), #8b5cf6);
  height: 2px;
}
</style>
