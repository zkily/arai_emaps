<template>
  <div class="monthly-load-page">
    <header class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="22"><Histogram /></el-icon>
        </div>
        <div>
          <h1 class="page-title">{{ summary?.header.title_month || titleFallback }}</h1>
          <p class="page-subtitle">工程別の月度計画数量・能率・負荷率を一画面で確認</p>
        </div>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="yearMonth"
          type="month"
          value-format="YYYY-MM"
          format="YYYY年MM月"
          size="default"
          :clearable="false"
          class="month-picker"
          @change="loadSummary"
        />
        <el-button type="primary" :icon="Refresh" :loading="loading" @click="loadSummary">
          再集計
        </el-button>
        <el-button :icon="Download" :disabled="!summary || rows.length === 0" @click="exportCsv">
          CSV
        </el-button>
      </div>
    </header>

    <section class="kpi-row">
      <div class="kpi-card kpi-card--primary">
        <div class="kpi-label">対象月稼働日</div>
        <div class="kpi-value">
          {{ summary ? summary.header.working_days : '—' }}
          <span class="kpi-unit">日</span>
        </div>
        <div class="kpi-sub">production_summarys（土日除く）DISTINCT 日数</div>
      </div>
      <div
        v-for="fc in forecastCards"
        :key="fc.year_month"
        class="kpi-card"
      >
        <div class="kpi-label">日当たり見込生産（{{ fc.month_label }}）</div>
        <div class="kpi-value">
          {{ fc.value_per_day != null ? fc.value_per_day.toFixed(1) : '—' }}
          <span class="kpi-unit">千本/日</span>
        </div>
        <div class="kpi-sub">
          稼働 {{ fc.working_days }} 日 / 内示 {{ formatThousand(fc.forecast_total) }} 千本
        </div>
      </div>
    </section>

    <el-alert
      v-for="msg in warnings"
      :key="msg"
      class="warning-alert"
      type="warning"
      :title="msg"
      show-icon
      :closable="false"
    />

    <el-card class="table-card" shadow="never" v-loading="loading">
      <el-table
        :data="rows"
        :row-class-name="rowClassName"
        size="default"
        stripe
        border
        :header-cell-style="{ background: '#f1f5f9', color: '#1f2937', fontWeight: 700 }"
        empty-text="データがありません"
        class="load-table"
      >
        <el-table-column prop="label" label="工程" width="110" fixed="left" align="center">
          <template #default="{ row }">
            <span class="process-cell">
              <span class="process-cell__name">{{ row.label }}</span>
              <el-tooltip
                v-if="row.annotation"
                effect="dark"
                placement="top"
                :content="row.annotation"
              >
                <span class="process-cell__note">（{{ row.annotation }}）</span>
              </el-tooltip>
            </span>
          </template>
        </el-table-column>

        <el-table-column label="計画（千本）" width="120" align="right">
          <template #default="{ row }">
            <span class="num-cell">{{ formatNumber(row.plan_thousand, 1) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="日当たり（千本）" width="140" align="right">
          <template #default="{ row }">
            <span class="num-cell">{{ formatNumber(row.plan_thousand_per_day, 1) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="設備・人員" width="130" align="center">
          <template #default="{ row }">
            <span v-if="row.resource_count != null" class="resource-cell">
              {{ formatResource(row.resource_count) }}{{ row.resource_unit }}
            </span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="標準能率（本/H）" width="140" align="right">
          <template #default="{ row }">
            <span class="num-cell">{{ formatNumber(row.efficiency, 0) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="標準稼働直" width="110" align="center">
          <template #default="{ row }">
            <span v-if="row.shift_count">
              {{ row.shift_count }}直 × {{ row.resource_unit === '人' ? '7.6H' : `${defaultHoursLabel(row)}H` }}
            </span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="月間定時時間（H）" width="150" align="right">
          <template #default="{ row }">
            <span class="num-cell">{{ formatNumber(row.monthly_regular_hours, 0) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="生産所要時間（H）" width="150" align="right">
          <template #default="{ row }">
            <span class="num-cell">{{ formatNumber(row.required_hours, 0) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="負荷率" min-width="220">
          <template #default="{ row }">
            <div v-if="row.load_pct != null" class="load-cell">
              <el-progress
                :percentage="Math.min(100, row.load_pct)"
                :color="loadColor(row.load_pct)"
                :show-text="false"
                :stroke-width="8"
                class="load-cell__bar"
              />
              <span class="load-cell__value" :class="loadValueClass(row.load_pct)">
                {{ row.load_pct.toFixed(1) }}%
              </span>
              <el-tag v-if="row.load_pct > 100" type="danger" size="small" effect="light">
                超過
              </el-tag>
              <el-tag v-else-if="row.load_pct >= 90" type="warning" size="small" effect="light">
                注意
              </el-tag>
              <el-tag v-else type="success" size="small" effect="light">
                正常
              </el-tag>
            </div>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="日均稼働（H/台・人）" width="170" align="right">
          <template #default="{ row }">
            <span class="num-cell">{{ formatNumber(row.daily_avg_hours, 1) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <p v-if="summary?.config_note" class="config-note">
        ※ {{ summary.config_note }}
      </p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Histogram, Refresh } from '@element-plus/icons-vue'
import {
  fetchMonthlyLoadSummary,
  type MonthlyLoadRow,
  type MonthlyLoadSummary,
} from '@/api/productionMonthlyLoad'

const today = new Date()
const yearMonth = ref<string>(`${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`)
const loading = ref(false)
const summary = ref<MonthlyLoadSummary | null>(null)

const rows = computed<MonthlyLoadRow[]>(() => summary.value?.rows ?? [])
const warnings = computed<string[]>(() => summary.value?.warnings ?? [])
const forecastCards = computed(() => summary.value?.header.forecast_daily_next_months ?? [])

const titleFallback = computed(() => {
  const parts = yearMonth.value.split('-')
  if (parts.length === 2) return `${Number(parts[1])}月生産計画`
  return '月度生産計画'
})

function formatNumber(value: number | null | undefined, digits = 1): string {
  if (value == null || Number.isNaN(value)) return '—'
  return value.toLocaleString('ja-JP', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function formatThousand(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return (value / 1000).toLocaleString('ja-JP', { maximumFractionDigits: 1 })
}

function formatResource(value: number): string {
  return Number.isInteger(value) ? `${value}` : value.toFixed(1)
}

function defaultHoursLabel(row: MonthlyLoadRow): string {
  const hours = row.monthly_regular_hours
  if (!hours || !row.shift_count || !row.resource_count) return '7.6'
  // monthly_regular_hours = workingDays × hoursPerDay × shift × resource_count
  const wd = summary.value?.header.working_days || 0
  if (wd <= 0) return '7.6'
  const computed = hours / wd / row.shift_count / row.resource_count
  return computed.toFixed(1)
}

function rowClassName({ row }: { row: MonthlyLoadRow }): string {
  if (row.key === 'forecast') return 'row-forecast'
  if (row.manual) return 'row-manual'
  if (row.load_pct != null && row.load_pct > 100) return 'row-overload'
  return ''
}

function loadColor(pct: number): string {
  if (pct > 100) return '#ef4444'
  if (pct >= 90) return '#f59e0b'
  return '#10b981'
}

function loadValueClass(pct: number): string {
  if (pct > 100) return 'load-cell__value--over'
  if (pct >= 90) return 'load-cell__value--warn'
  return 'load-cell__value--ok'
}

async function loadSummary() {
  if (!yearMonth.value) return
  loading.value = true
  try {
    const res = await fetchMonthlyLoadSummary(yearMonth.value)
    summary.value = res
  } catch (err) {
    console.error('月度負荷サマリ取得失敗', err)
    ElMessage.error('月度工程負荷データの取得に失敗しました')
    summary.value = null
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  if (!summary.value) return
  const header = [
    '工程',
    '計画(千本)',
    '日当たり(千本)',
    '設備・人員',
    '標準能率(本/H)',
    '直数',
    '月間定時時間(H)',
    '生産所要時間(H)',
    '負荷率(%)',
    '日均稼働(H/台・人)',
    '備考',
  ]
  const lines = [header.join(',')]
  for (const row of rows.value) {
    const resource = row.resource_count != null
      ? `${formatResource(row.resource_count)}${row.resource_unit}`
      : ''
    lines.push(
      [
        row.label,
        row.plan_thousand ?? '',
        row.plan_thousand_per_day ?? '',
        resource,
        row.efficiency ?? '',
        row.shift_count ?? '',
        row.monthly_regular_hours ?? '',
        row.required_hours ?? '',
        row.load_pct ?? '',
        row.daily_avg_hours ?? '',
        row.annotation ?? '',
      ]
        .map((v) => {
          const s = String(v)
          return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
        })
        .join(','),
    )
  }
  const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `工程別月度負荷_${yearMonth.value}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

onMounted(() => {
  void loadSummary()
})
</script>

<style scoped>
.monthly-load-page {
  min-height: 100vh;
  padding: 20px;
  background:
    radial-gradient(circle at top right, rgba(99, 102, 241, 0.1), transparent 38%),
    linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 18px 22px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #2563eb);
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.32);
}

.page-title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
  color: #0f172a;
}

.page-subtitle {
  margin: 4px 0 0;
  font-size: 0.84rem;
  color: #64748b;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.month-picker {
  width: 160px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.kpi-card {
  padding: 16px 18px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
}

.kpi-card--primary {
  background: linear-gradient(135deg, #ede9fe 0%, #dbeafe 100%);
  border-color: #c7d2fe;
}

.kpi-label {
  color: #475569;
  font-size: 0.78rem;
  font-weight: 700;
}

.kpi-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 8px;
  font-size: 1.7rem;
  font-weight: 800;
  color: #1e293b;
}

.kpi-unit {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 600;
}

.kpi-sub {
  margin-top: 4px;
  font-size: 0.74rem;
  color: #94a3b8;
}

.warning-alert {
  margin-bottom: 10px;
  border-radius: 10px;
}

.table-card {
  border: 0;
  border-radius: 16px;
}

.load-table {
  font-variant-numeric: tabular-nums;
}

:deep(.row-forecast) {
  background: linear-gradient(90deg, rgba(219, 234, 254, 0.4), transparent) !important;
  font-weight: 700;
}

:deep(.row-forecast td) {
  color: #1d4ed8;
}

:deep(.row-overload td) {
  background: rgba(254, 226, 226, 0.35) !important;
}

:deep(.row-manual) {
  color: #94a3b8;
}

.process-cell {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
}

.process-cell__name {
  font-weight: 700;
  color: #111827;
}

.process-cell__note {
  font-size: 0.72rem;
  color: #ef4444;
}

.num-cell {
  font-weight: 600;
  color: #1f2937;
}

.resource-cell {
  font-weight: 600;
  color: #1f2937;
}

.muted {
  color: #cbd5e1;
}

.load-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.load-cell__bar {
  flex: 1;
  min-width: 80px;
}

.load-cell__value {
  min-width: 60px;
  font-weight: 700;
  text-align: right;
}

.load-cell__value--ok {
  color: #047857;
}

.load-cell__value--warn {
  color: #b45309;
}

.load-cell__value--over {
  color: #b91c1c;
}

.config-note {
  margin: 12px 4px 0;
  color: #94a3b8;
  font-size: 0.78rem;
}

@media (max-width: 1024px) {
  .kpi-row {
    grid-template-columns: 1fr;
  }
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
