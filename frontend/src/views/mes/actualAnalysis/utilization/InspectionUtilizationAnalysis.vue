<template>
  <div class="iua">
    <header class="iua-hero">
      <div class="iua-hero__main">
        <div class="iua-hero__icon">
          <el-icon :size="24"><Odometer /></el-icon>
        </div>
        <div>
          <div class="iua-hero__eyebrow">MES · 実績分析 · 稼働率</div>
          <h1 class="iua-hero__title">検査工程 — 稼働率分析</h1>
          <p class="iua-hero__meta">
            inspection_management · 検査員別 · 所定 {{ standardHours }}h/日 · 会社稼働カレンダー自動反映
          </p>
        </div>
      </div>
      <div class="iua-hero__actions">
        <span v-if="analysisData" class="iua-hero__range">
          {{ analysisData.start_date }} ～ {{ analysisData.end_date }}
        </span>
        <el-button :icon="Refresh" :loading="loading" round @click="loadAnalysis">更新</el-button>
      </div>
    </header>

    <div class="iua-toolbar iua-panel">
      <div class="iua-toolbar__fields">
        <div class="iua-field">
          <span class="iua-field__label">期間</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="～"
            value-format="YYYY-MM-DD"
            size="small"
            class="iua-field__date"
          />
        </div>
        <div class="iua-field">
          <span class="iua-field__label">検査員</span>
          <el-select
            v-model="filterInspectorId"
            placeholder="すべて"
            clearable
            filterable
            size="small"
            class="iua-field__select"
          >
            <el-option label="（すべて）" :value="null" />
            <el-option v-for="u in inspectorOptions" :key="u.id" :label="inspectorLabel(u)" :value="u.id" />
          </el-select>
        </div>
        <label class="iua-check">
          <el-checkbox v-model="includeIncomplete" size="small">未確定を含む</el-checkbox>
        </label>
      </div>
      <el-button type="primary" :loading="loading" round @click="loadAnalysis">分析実行</el-button>
    </div>

    <div v-if="analysisData" class="iua-cal-banner iua-panel">
      <el-icon class="iua-cal-banner__icon"><Calendar /></el-icon>
      <span>
        会社稼働カレンダー反映
        · 通常稼働日 <strong>{{ analysisData.calendar_workdays_in_range }}</strong> 日
        <template v-if="analysisData.company_calendar_extra_workdays?.length">
          · 臨時出勤 {{ analysisData.company_calendar_extra_workdays.length }}
        </template>
        <template v-if="analysisData.company_calendar_holidays?.length">
          · 休日 {{ analysisData.company_calendar_holidays.length }}
        </template>
      </span>
      <router-link to="/master/company-work-calendar" class="iua-cal-banner__link">カレンダー管理</router-link>
    </div>

    <el-collapse v-model="overridePanel" class="iua-override">
      <el-collapse-item name="override">
        <template #title>
          <span class="iua-override__title">分析上書き（任意）</span>
          <span class="iua-override__hint">会社カレンダーに追加指定 · 未設定時はマスタのみ</span>
        </template>
        <div class="iua-override__body">
          <div class="iua-field iua-field--wide">
            <span class="iua-field__label">臨時出勤</span>
            <el-date-picker
              v-model="extraWorkdays"
              type="dates"
              placeholder="分析期間内の追加出勤日"
              value-format="YYYY-MM-DD"
              size="small"
              class="iua-field__dates"
            />
          </div>
          <div class="iua-field iua-field--wide">
            <span class="iua-field__label">臨時休日</span>
            <el-date-picker
              v-model="extraHolidays"
              type="dates"
              placeholder="分析期間内の追加休日"
              value-format="YYYY-MM-DD"
              size="small"
              class="iua-field__dates"
            />
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <el-alert
      v-if="analysisData?.data_gaps?.length"
      type="info"
      :closable="false"
      show-icon
      class="iua-gaps"
      title="データ上の留意点"
    >
      <ul class="iua-gaps__list">
        <li v-for="(g, i) in analysisData.data_gaps" :key="i">{{ g }}</li>
      </ul>
    </el-alert>

    <div v-loading="loading" class="iua-body">
      <div class="iua-kpi">
        <div v-for="card in kpiCards" :key="card.key" class="iua-kpi__card" :class="`iua-kpi__card--${card.tone}`">
          <div class="iua-kpi__label">{{ card.label }}</div>
          <div class="iua-kpi__value">{{ card.value }}</div>
          <div class="iua-kpi__hint">{{ card.hint }}</div>
        </div>
      </div>

      <div v-if="analysisData" class="iua-content">
        <section class="iua-panel">
          <div class="iua-panel__head">
            <span class="iua-panel__title">日別稼働率推移</span>
            <span class="iua-panel__badge">検査員合算</span>
          </div>
          <div ref="dailyChartRef" class="iua-chart" />
        </section>

        <section class="iua-panel">
          <div class="iua-panel__head">
            <span class="iua-panel__title">検査員別サマリ</span>
            <span class="iua-panel__badge">{{ analysisData.by_inspector.length }} 名</span>
          </div>
          <el-table :data="analysisData.by_inspector" size="small" class="iua-table" stripe>
            <el-table-column prop="inspector_name" label="検査員" min-width="110" show-overflow-tooltip />
            <el-table-column label="出勤日" width="64" align="right">
              <template #default="{ row }">{{ row.scheduled_work_day_count }}/{{ row.work_day_count }}</template>
            </el-table-column>
            <el-table-column label="件数" width="52" align="right">
              <template #default="{ row }">{{ row.session_count }}</template>
            </el-table-column>
            <el-table-column label="正味(h)" width="72" align="right">
              <template #default="{ row }">{{ fmtHours(row.sum_net_production_sec) }}</template>
            </el-table-column>
            <el-table-column label="所定内(h)" width="80" align="right">
              <template #default="{ row }">{{ fmtHours(row.sum_regular_sec) }}</template>
            </el-table-column>
            <el-table-column label="残業(h)" width="72" align="right">
              <template #default="{ row }">
                <span :class="{ 'iua-num--warn': (row.sum_overtime_sec ?? 0) > 0 }">
                  {{ fmtHours(row.sum_overtime_sec) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="稼働率" width="76" align="right">
              <template #default="{ row }">
                <span class="iua-num--good">{{ fmtPct(row.utilization_percent) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="ｶﾚﾝﾀﾞ率" width="76" align="right">
              <template #default="{ row }">{{ fmtPct(row.calendar_utilization_percent) }}</template>
            </el-table-column>
          </el-table>
        </section>

        <section class="iua-panel">
          <div class="iua-panel__head">
            <span class="iua-panel__title">検査員 × 日別明細</span>
            <span class="iua-panel__badge">{{ filteredDailyRows.length }} 行</span>
          </div>
          <el-table :data="filteredDailyRows" size="small" class="iua-table" max-height="420" stripe>
            <el-table-column prop="day" label="生産日" width="100" />
            <el-table-column prop="inspector_name" label="検査員" min-width="100" show-overflow-tooltip />
            <el-table-column label="区分" width="88" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_extra_workday" size="small" type="warning">土日出勤</el-tag>
                <el-tag v-else-if="!row.is_scheduled_workday" size="small" type="info">休日実績</el-tag>
                <el-tag v-else size="small" type="success">平日</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="件" width="44" align="right">
              <template #default="{ row }">{{ row.session_count }}</template>
            </el-table-column>
            <el-table-column label="正味" width="64" align="right">
              <template #default="{ row }">{{ fmtMin(row.sum_net_production_min) }}</template>
            </el-table-column>
            <el-table-column label="所定内" width="64" align="right">
              <template #default="{ row }">{{ fmtMin(row.regular_min) }}</template>
            </el-table-column>
            <el-table-column label="残業" width="64" align="right">
              <template #default="{ row }">
                <span :class="{ 'iua-num--warn': (row.overtime_min ?? 0) > 0 }">{{ fmtMin(row.overtime_min) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="稼働率" width="72" align="right">
              <template #default="{ row }">{{ fmtPct(row.utilization_percent) }}</template>
            </el-table-column>
            <el-table-column label="負荷率" width="72" align="right">
              <template #default="{ row }">{{ fmtPct(row.load_percent) }}</template>
            </el-table-column>
          </el-table>
        </section>
      </div>

      <div v-else-if="!loading" class="iua-empty iua-panel">
        <el-empty description="期間を選択して「分析実行」をクリック" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { Odometer, Refresh, Calendar } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchInspectionUtilizationAnalysis,
  type InspectionUtilizationAnalysisData,
} from '@/api/inspectionManagement'
import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import { getJSTToday, parseDateAsJST } from '@/utils/dateFormat'

defineOptions({ name: 'MesInspectionUtilizationAnalysis' })

const loading = ref(false)
const analysisData = ref<InspectionUtilizationAnalysisData | null>(null)
const inspectorOptions = ref<UserListItem[]>([])
const filterInspectorId = ref<number | null>(null)
const includeIncomplete = ref(false)
const extraWorkdays = ref<string[]>([])
const extraHolidays = ref<string[]>([])
const overridePanel = ref<string[]>([])
const dailyChartRef = ref<HTMLElement | null>(null)
let dailyChart: ECharts | null = null

function shiftJstDate(isoDay: string, deltaDays: number): string {
  const base = parseDateAsJST(isoDay)
  if (!base) return isoDay
  base.setDate(base.getDate() + deltaDays)
  return base.toISOString().slice(0, 10)
}

const dateRange = ref<[string, string]>([shiftJstDate(getJSTToday(), -29), getJSTToday()])
const standardHours = computed(() => analysisData.value?.standard_workday_hours ?? 7.6)

const summary = computed(() => analysisData.value?.summary)

const filteredDailyRows = computed(() => {
  const rows = analysisData.value?.daily_by_inspector ?? []
  if (filterInspectorId.value == null) return rows
  return rows.filter((r) => r.inspector_user_id === filterInspectorId.value)
})

const kpiCards = computed(() => {
  const s = summary.value
  return [
    {
      key: 'util',
      label: '平均稼働率',
      value: fmtPct(s?.utilization_percent),
      hint: '所定7.6h内 / 出勤日基準',
      tone: 'green',
    },
    {
      key: 'calendar',
      label: 'カレンダー稼働率',
      value: fmtPct(s?.calendar_utilization_percent),
      hint: `会社稼働日 ${s?.calendar_workdays_in_range ?? '—'} 日`,
      tone: 'blue',
    },
    {
      key: 'net',
      label: '正味稼働合計',
      value: fmtDuration(s?.sum_net_production_min),
      hint: `${fmtInt(s?.session_count)} セッション`,
      tone: 'indigo',
    },
    {
      key: 'overtime',
      label: '残業合計',
      value: fmtDuration(s?.overtime_min),
      hint: `所定内 ${fmtDuration(s?.regular_min)}`,
      tone: 'amber',
    },
    {
      key: 'inspectors',
      label: '検査員',
      value: fmtInt(s?.inspector_count),
      hint: s?.unassigned_session_count ? `未割当 ${s.unassigned_session_count} 件` : '対象人数',
      tone: 'violet',
    },
  ]
})

function inspectorLabel(u: UserListItem): string {
  return (u.full_name || u.username || `ID:${u.id}`).trim()
}

function fmtInt(v?: number | null): string {
  if (v == null || Number.isNaN(v)) return '—'
  return v.toLocaleString()
}

function fmtPct(v?: number | null): string {
  if (v == null || Number.isNaN(v)) return '—'
  return `${v.toFixed(1)}%`
}

function fmtMin(v?: number | null): string {
  if (v == null || v <= 0) return '—'
  return `${v}m`
}

function fmtDuration(min?: number | null): string {
  if (min == null || min <= 0) return '0m'
  const h = Math.floor(min / 60)
  const m = min % 60
  if (h <= 0) return `${m}m`
  return m > 0 ? `${h}h${m}m` : `${h}h`
}

function fmtHours(sec?: number | null): string {
  if (sec == null || sec <= 0) return '—'
  return (sec / 3600).toFixed(1)
}

function disposeChart() {
  dailyChart?.dispose()
  dailyChart = null
}

function renderDailyChart() {
  const el = dailyChartRef.value
  const daily = analysisData.value?.daily ?? []
  if (!el || !daily.length) {
    disposeChart()
    return
  }
  if (!dailyChart) dailyChart = echarts.init(el)
  dailyChart.setOption({
    grid: { left: 48, right: 16, top: 28, bottom: 32 },
    tooltip: { trigger: 'axis' },
    legend: { data: ['稼働率', '正味(分)'], top: 0 },
    xAxis: { type: 'category', data: daily.map((d) => d.day.slice(5)) },
    yAxis: [
      { type: 'value', name: '%', max: 120 },
      { type: 'value', name: '分', splitLine: { show: false } },
    ],
    series: [
      {
        name: '稼働率',
        type: 'line',
        smooth: true,
        data: daily.map((d) => d.utilization_percent ?? 0),
        itemStyle: { color: '#10b981' },
        areaStyle: { color: 'rgba(16,185,129,0.12)' },
      },
      {
        name: '正味(分)',
        type: 'bar',
        yAxisIndex: 1,
        data: daily.map((d) => d.sum_net_production_min ?? 0),
        itemStyle: { color: '#6366f1', opacity: 0.75 },
      },
    ],
  })
}

async function loadInspectors() {
  try {
    const res = (await getUsers({ page: 1, pageSize: 500, status: 'active' })) as PaginatedUserResponse
    inspectorOptions.value = res?.data?.items ?? res?.items ?? []
  } catch {
    inspectorOptions.value = []
  }
}

async function loadAnalysis() {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) {
    ElMessage.warning('期間を選択してください')
    return
  }
  loading.value = true
  try {
    const res = await fetchInspectionUtilizationAnalysis({
      start_date: start,
      end_date: end,
      mes_inspector_user_id: filterInspectorId.value,
      include_incomplete: includeIncomplete.value,
      use_company_calendar: true,
      extra_workdays: extraWorkdays.value.length ? extraWorkdays.value.join(',') : undefined,
      extra_holidays: extraHolidays.value.length ? extraHolidays.value.join(',') : undefined,
    })
    if (!res?.success || !res.data) {
      ElMessage.error(res?.message || '分析データの取得に失敗しました')
      analysisData.value = null
      return
    }
    analysisData.value = res.data
    await nextTick()
    renderDailyChart()
  } catch (e: unknown) {
    analysisData.value = null
    ElMessage.error(e instanceof Error ? e.message : '分析データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

watch(
  () => analysisData.value?.daily,
  () => nextTick(() => renderDailyChart()),
)

onMounted(() => {
  loadInspectors()
  loadAnalysis()
  window.addEventListener('resize', renderDailyChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderDailyChart)
  disposeChart()
})
</script>

<style scoped>
.iua {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 12px 20px;
  min-height: 100%;
}

.iua-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #fff 0%, #f0fdf4 100%);
  border: 1px solid rgba(16, 185, 129, 0.15);
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.08);
}

.iua-hero__main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.iua-hero__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(145deg, #34d399, #059669);
}

.iua-hero__eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #059669;
  text-transform: uppercase;
}

.iua-hero__title {
  margin: 2px 0 0;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.iua-hero__meta {
  margin: 2px 0 0;
  font-size: 11px;
  color: #64748b;
}

.iua-hero__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.iua-hero__range {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.1);
}

.iua-panel {
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
  padding: 12px 14px;
}

.iua-cal-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 6px 10px;
  font-size: 11px;
  color: #047857;
  background: linear-gradient(90deg, #ecfdf5, #f0fdf4);
  border-color: rgba(16, 185, 129, 0.2);
}

.iua-cal-banner__icon {
  color: #059669;
  font-size: 14px;
}

.iua-cal-banner strong {
  font-weight: 700;
  color: #065f46;
}

.iua-cal-banner__link {
  margin-left: auto;
  font-size: 10px;
  font-weight: 600;
  color: #2563eb;
  text-decoration: none;
}

.iua-cal-banner__link:hover {
  text-decoration: underline;
}

.iua-override {
  border: none;
  background: transparent;
}

.iua-override :deep(.el-collapse-item__header) {
  height: 32px;
  line-height: 32px;
  padding: 0 10px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
  font-size: 11px;
}

.iua-override :deep(.el-collapse-item__wrap) {
  border: none;
}

.iua-override :deep(.el-collapse-item__content) {
  padding: 6px 0 0;
}

.iua-override__title {
  font-weight: 700;
  color: #334155;
}

.iua-override__hint {
  margin-left: 8px;
  font-size: 10px;
  font-weight: 400;
  color: #94a3b8;
}

.iua-override__body {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
}

.iua-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.iua-toolbar__fields {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.iua-field {
  display: flex;
  align-items: center;
  gap: 6px;
}

.iua-field--wide {
  min-width: 180px;
}

.iua-field__label {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}

.iua-field__date {
  width: 240px !important;
}

.iua-field__select {
  width: 160px;
}

.iua-field__dates {
  width: 200px !important;
}

.iua-check {
  display: flex;
  align-items: center;
  padding-left: 4px;
}

.iua-gaps {
  margin: 0;
}

.iua-gaps__list {
  margin: 4px 0 0;
  padding-left: 18px;
  font-size: 12px;
}

.iua-kpi {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.iua-kpi__card {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

.iua-kpi__card--green {
  background: linear-gradient(160deg, #fff, #ecfdf5);
  border-color: rgba(16, 185, 129, 0.2);
}

.iua-kpi__card--blue {
  background: linear-gradient(160deg, #fff, #eff6ff);
  border-color: rgba(59, 130, 246, 0.2);
}

.iua-kpi__card--indigo {
  background: linear-gradient(160deg, #fff, #eef2ff);
  border-color: rgba(99, 102, 241, 0.2);
}

.iua-kpi__card--amber {
  background: linear-gradient(160deg, #fff, #fff7ed);
  border-color: rgba(249, 115, 22, 0.2);
}

.iua-kpi__card--violet {
  background: linear-gradient(160deg, #fff, #f5f3ff);
  border-color: rgba(139, 92, 246, 0.2);
}

.iua-kpi__label {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
}

.iua-kpi__value {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.iua-kpi__hint {
  margin-top: 2px;
  font-size: 10px;
  color: #94a3b8;
}

.iua-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.iua-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.iua-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.iua-panel__title {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}

.iua-panel__badge {
  font-size: 10px;
  font-weight: 600;
  color: #059669;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.1);
}

.iua-chart {
  width: 100%;
  height: 260px;
}

.iua-table :deep(.el-table__header th) {
  background: #f8fafc !important;
  font-size: 11px;
}

.iua-table :deep(.el-table__body td) {
  font-size: 11px;
}

.iua-num--good {
  color: #059669;
  font-weight: 700;
}

.iua-num--warn {
  color: #ea580c;
  font-weight: 700;
}

.iua-empty {
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1200px) {
  .iua-kpi {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .iua-kpi {
    grid-template-columns: 1fr;
  }

  .iua-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
