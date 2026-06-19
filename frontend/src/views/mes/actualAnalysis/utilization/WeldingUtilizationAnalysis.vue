<template>
  <div class="iua">
    <div class="iua__bg" aria-hidden="true">
      <div class="iua__orb iua__orb--1" />
      <div class="iua__orb iua__orb--2" />
      <div class="iua__orb iua__orb--3" />
    </div>

    <header class="iua-hero iua-fade-in">
      <div class="iua-hero__main">
        <div class="iua-hero__icon">
          <el-icon :size="24"><Connection /></el-icon>
          <span class="iua-hero__icon-glow" />
        </div>
        <div class="iua-hero__text">
          <div class="iua-hero__eyebrow">MES · 実績分析 · 稼働率</div>
          <div class="iua-hero__title-row">
            <h1 class="iua-hero__title">溶接工程 — 稼働率分析</h1>
            <el-popover
              v-if="hasDataGaps"
              trigger="click"
              placement="bottom-start"
              :width="560"
              popper-class="iua-gaps-popper"
            >
              <template #reference>
                <button type="button" class="iua-gaps-trigger" aria-label="データ上の留意点" @click.stop>
                  <el-icon :size="16"><WarningFilled /></el-icon>
                  <span v-if="dataGapsCount > 0" class="iua-gaps-trigger__badge">{{ dataGapsCount }}</span>
                </button>
              </template>
              <div class="iua-gaps-panel">
                <div class="iua-gaps-panel__head">
                  <el-icon class="iua-gaps-panel__ico"><WarningFilled /></el-icon>
                  <span class="iua-gaps-panel__title">データ上の留意点</span>
                </div>
                <ul class="iua-gaps__list">
                  <li v-for="(g, i) in analysisData?.data_gaps" :key="i">
                    <span>{{ g }}</span>
                    <ul
                      v-if="g.includes('正味稼働時間が算出できない') && sessionsWithoutTimeDetails.length"
                      class="iua-gaps__sublist"
                    >
                      <li v-for="s in sessionsWithoutTimeDetails" :key="s.id" class="iua-gaps__detail">
                        <span class="iua-gaps__detail-id">ID {{ s.id }}</span>
                        <span>{{ s.production_day }}</span>
                        <span>{{ s.operator_name || '溶接作業者未割当' }}</span>
                        <span>{{ sessionProductLabel(s) }}</span>
                        <span class="iua-gaps__detail-reason">{{ sessionTimeGapReason(s) }}</span>
                        <el-tag
                          size="small"
                          :type="s.production_completed_check ? 'success' : 'info'"
                          effect="light"
                        >
                          {{ s.production_completed_check ? '確定' : '未確定' }}
                        </el-tag>
                      </li>
                    </ul>
                  </li>
                </ul>
              </div>
            </el-popover>
          </div>
          <p class="iua-hero__meta">
            welding_management · 溶接作業者別 · 所定
            <template v-if="analysisData?.operator_schedule_applied">溶接作業者マスタ優先</template>
            <template v-else>デフォルト {{ defaultStandardHours }}h/日</template>
            · 会社稼働カレンダー自動反映
          </p>
        </div>
      </div>
      <div class="iua-hero__actions">
        <span v-if="analysisData" class="iua-hero__range">
          {{ analysisData.start_date }} ～ {{ analysisData.end_date }}
        </span>
        <el-dropdown
          trigger="click"
          :disabled="!analysisData || exportBusy"
          popper-class="iua-report-dropdown"
          @command="handleReportCommand"
        >
          <el-button class="iua-btn iua-btn--report" :loading="exportBusy" round>
            <span class="iua-btn__inner">
              <el-icon v-if="!exportBusy" class="iua-btn__icon"><Document /></el-icon>
              <span>レポート</span>
              <el-icon class="iua-btn__caret"><ArrowDown /></el-icon>
            </span>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu class="iua-report-menu">
              <el-dropdown-item
                v-for="item in reportMenuItems"
                :key="item.command"
                :command="item.command"
                :divided="item.divided"
                class="iua-report-item"
                :class="`iua-report-item--${item.tone}`"
              >
                <span class="iua-report-item__icon-wrap">
                  <el-icon><component :is="item.icon" /></el-icon>
                </span>
                <span class="iua-report-item__text">
                  <span class="iua-report-item__label">{{ item.label }}</span>
                  <span v-if="item.hint" class="iua-report-item__hint">{{ item.hint }}</span>
                </span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button class="iua-btn iua-btn--refresh" :loading="loading" round @click="loadAnalysis">
          <span class="iua-btn__inner">
            <el-icon v-if="!loading" class="iua-btn__icon"><Refresh /></el-icon>
            <span>更新</span>
          </span>
        </el-button>
      </div>
    </header>

    <div class="iua-toolbar iua-panel iua-fade-in iua-fade-in--d1">
      <div class="iua-toolbar__fields">
        <div class="iua-field iua-field--period">
          <span class="iua-field__pill"><el-icon><Calendar /></el-icon>期間</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始"
            end-placeholder="終了"
            value-format="YYYY-MM-DD"
            size="small"
            class="iua-field__control iua-field__date"
          />
        </div>
        <div class="iua-field iua-field--inspector">
          <span class="iua-field__pill"><el-icon><User /></el-icon>溶接作業者</span>
          <el-select
            v-model="filterOperatorId"
            placeholder="すべて"
            clearable
            filterable
            size="small"
            class="iua-field__control iua-field__select"
          >
            <el-option label="（すべて）" value="" />
            <el-option v-for="u in operatorOptions" :key="u.id" :label="operatorLabel(u)" :value="u.id" />
          </el-select>
        </div>
        <label class="iua-field iua-field--check">
          <span class="iua-field__pill iua-field__pill--check">オプション</span>
          <el-checkbox v-model="includeIncomplete" size="small">未確定を含む</el-checkbox>
        </label>
      </div>
    </div>

    <div v-if="analysisData" class="iua-cal-banner iua-panel iua-fade-in iua-fade-in--d2">
      <span class="iua-cal-banner__icon-wrap">
        <el-icon><Calendar /></el-icon>
      </span>
      <span class="iua-cal-banner__text">
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

    <div v-loading="loading" class="iua-body">
      <div class="iua-kpi">
        <div
          v-for="(card, idx) in kpiCards"
          :key="card.key"
          class="iua-kpi__card"
          :class="`iua-kpi__card--${card.tone}`"
          :style="{ animationDelay: `${idx * 0.05}s` }"
        >
          <div class="iua-kpi__accent" aria-hidden="true" />
          <div class="iua-kpi__icon-wrap" :class="`iua-kpi__icon-wrap--${card.tone}`">
            <el-icon :size="18"><component :is="card.icon" /></el-icon>
          </div>
          <div class="iua-kpi__content">
            <div class="iua-kpi__label">{{ card.label }}</div>
            <div class="iua-kpi__value">{{ card.value }}</div>
            <div class="iua-kpi__hint">{{ card.hint }}</div>
          </div>
        </div>
      </div>

      <Transition name="iua-reveal">
        <div v-if="analysisData" key="content" class="iua-content">
          <div class="iua-charts">
            <section class="iua-panel iua-panel--chart iua-fade-in iua-fade-in--d3">
              <div class="iua-panel__head">
                <div class="iua-panel__title-wrap">
                  <el-icon class="iua-panel__ico"><TrendCharts /></el-icon>
                  <span class="iua-panel__title">日別稼働率推移</span>
                </div>
                <span class="iua-panel__badge">{{ chartBadgeLabel }}</span>
              </div>
              <div ref="dailyChartRef" class="iua-chart iua-chart--main" />
            </section>

            <section class="iua-panel iua-panel--chart iua-panel--overtime iua-fade-in iua-fade-in--d3b">
              <div class="iua-panel__head">
                <div class="iua-panel__title-wrap">
                  <el-icon class="iua-panel__ico iua-panel__ico--overtime"><Sunny /></el-icon>
                  <span class="iua-panel__title">日別残業推移</span>
                </div>
                <span class="iua-panel__badge iua-panel__badge--overtime">合計 {{ overtimeChartTotalLabel }}</span>
              </div>
              <div ref="overtimeChartRef" class="iua-chart iua-chart--main iua-chart--overtime" />
            </section>
          </div>

          <div class="iua-split">
            <section class="iua-panel iua-panel--operator iua-fade-in iua-fade-in--d4">
              <div class="iua-panel__head">
                <div class="iua-panel__title-wrap">
                  <el-icon class="iua-panel__ico iua-panel__ico--operator"><User /></el-icon>
                  <span class="iua-panel__title">溶接作業者別サマリ</span>
                </div>
                <span class="iua-panel__badge iua-panel__badge--soft">{{ filteredByOperator.length }} 名</span>
              </div>
              <el-table :data="filteredByOperator" size="small" class="iua-table iua-table--operator" stripe>
                <el-table-column label="#" width="36" align="center">
                  <template #default="{ $index }">
                    <span class="iua-row-rank" :class="operatorRankClass($index)">{{ $index + 1 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="operator_name" label="溶接作業者" min-width="100" show-overflow-tooltip />
                <el-table-column label="出勤日" width="72" align="right">
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
                    <span class="iua-num" :class="{ 'iua-num--warn': (row.sum_overtime_sec ?? 0) > 0 }">
                      {{ fmtHours(row.sum_overtime_sec) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="稼働率" width="76" align="right">
                  <template #default="{ row }">
                    <span class="iua-util-pill" :class="utilPillClass(row.utilization_percent)">
                      {{ fmtPct(row.utilization_percent) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="ｶﾚﾝﾀﾞ率" width="76" align="right">
                  <template #default="{ row }">{{ fmtPct(row.calendar_utilization_percent) }}</template>
                </el-table-column>
              </el-table>
            </section>

            <section class="iua-panel iua-panel--daily iua-fade-in iua-fade-in--d5">
              <div class="iua-panel__head">
                <div class="iua-panel__title-wrap">
                  <el-icon class="iua-panel__ico iua-panel__ico--daily"><List /></el-icon>
                  <span class="iua-panel__title">溶接作業者 × 日別明細</span>
                </div>
                <span class="iua-panel__badge iua-panel__badge--daily">{{ filteredDailyRows.length }} 行</span>
              </div>
              <el-table
                :data="filteredDailyRows"
                size="small"
                class="iua-table iua-table--daily"
                max-height="420"
                stripe
              >
                <el-table-column prop="day" label="生産日" width="100" />
                <el-table-column prop="operator_name" label="溶接作業者" min-width="96" show-overflow-tooltip />
                <el-table-column label="区分" width="88" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.is_extra_workday" size="small" type="warning" effect="light">土日出勤</el-tag>
                    <el-tag v-else-if="!row.is_scheduled_workday" size="small" type="info" effect="light">休日実績</el-tag>
                    <el-tag v-else size="small" type="success" effect="light">平日</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="件" width="44" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="所定(h)" width="68" align="right">
                  <template #default="{ row }">{{ fmtScheduledHours(row.scheduled_hours) }}</template>
                </el-table-column>
                <el-table-column label="正味" width="64" align="right">
                  <template #default="{ row }">{{ fmtMin(row.sum_net_production_min) }}</template>
                </el-table-column>
                <el-table-column label="所定内" width="64" align="right">
                  <template #default="{ row }">{{ fmtMin(row.regular_min) }}</template>
                </el-table-column>
                <el-table-column label="残業" width="64" align="right">
                  <template #default="{ row }">
                    <span class="iua-num" :class="{ 'iua-num--warn': (row.overtime_min ?? 0) > 0 }">
                      {{ fmtMin(row.overtime_min) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="稼働率" width="72" align="right">
                  <template #default="{ row }">
                    <span class="iua-util-pill" :class="utilPillClass(row.utilization_percent)">
                      {{ fmtPct(row.utilization_percent) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="負荷率" width="72" align="right">
                  <template #default="{ row }">{{ fmtPct(row.load_percent) }}</template>
                </el-table-column>
              </el-table>
            </section>
          </div>
        </div>
      </Transition>

      <div v-if="!analysisData && !loading" class="iua-empty iua-panel iua-fade-in">
        <el-icon class="iua-empty__icon" :size="40"><Connection /></el-icon>
        <p class="iua-empty__text">期間を選択すると自動で分析されます</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  ArrowDown,
  Calendar,
  DataAnalysis,
  Document,
  List,
  Connection,
  Refresh,
  Sunny,
  Timer,
  TrendCharts,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchWeldingUtilizationAnalysis,
  type WeldingUtilizationAnalysisData,
  type WeldingUtilizationOperatorRow,
  type WeldingUtilizationSessionGap,
} from '@/api/weldingManagement'
import { getJSTToday, parseDateAsJST } from '@/utils/dateFormat'
import { fetchWeldingSectionOperators } from '@/views/mes/shared/weldingOperatorFilter'
import type { UserListItem } from '@/api/system'
import {
  avgUtilizationPercent,
  buildUtilizationDailyChartOption,
  buildUtilizationOvertimeChartOption,
  captureUtilizationChartDataUrl,
  captureUtilizationDailyChartDataUrl,
  overtimeMinFromUtilizationRow,
  printWeldingUtilizationDailyBatch,
  printWeldingUtilizationDailySection,
  printWeldingUtilizationReport,
  sumOvertimeMinFromDaily,
  type WeldingUtilizationReportContext,
  type WeldingUtilizationReportFilters,
  type UtilizationDailyBatchItem,
} from './weldingUtilizationReport'

defineOptions({ name: 'MesWeldingUtilizationAnalysis' })

type ReportMenuTone = 'green' | 'sky' | 'teal'

const reportMenuItems: Array<{
  command: string
  label: string
  hint?: string
  icon: typeof Document
  tone: ReportMenuTone
  divided?: boolean
}> = [
  {
    command: 'print-full',
    label: '印刷（全体）',
    hint: 'KPI · グラフ · 集計表',
    icon: markRaw(Document),
    tone: 'green',
  },
  {
    command: 'print-daily',
    label: '日別稼働率推移（印刷）',
    hint: '現在の溶接作業者フィルタ反映',
    icon: markRaw(TrendCharts),
    tone: 'sky',
    divided: true,
  },
  {
    command: 'print-daily-batch',
    label: '日別稼働率推移（溶接作業者別・一括印刷）',
    hint: '合算 + 溶接作業者ごとに分割',
    icon: markRaw(DataAnalysis),
    tone: 'teal',
  },
]

const loading = ref(false)
const exportBusy = ref(false)
const analysisData = ref<WeldingUtilizationAnalysisData | null>(null)
const operatorOptions = ref<UserListItem[]>([])
const filterOperatorId = ref<number | ''>('')
const includeIncomplete = ref(false)
const dailyChartRef = ref<HTMLElement | null>(null)
const overtimeChartRef = ref<HTMLElement | null>(null)
let dailyChart: ECharts | null = null
let overtimeChart: ECharts | null = null

function shiftJstDate(isoDay: string, deltaDays: number): string {
  const base = parseDateAsJST(isoDay)
  if (!base) return isoDay
  base.setDate(base.getDate() + deltaDays)
  return base.toISOString().slice(0, 10)
}

const dateRange = ref<[string, string]>([shiftJstDate(getJSTToday(), -29), getJSTToday()])
const defaultStandardHours = computed(
  () => analysisData.value?.default_standard_workday_hours ?? analysisData.value?.standard_workday_hours ?? 7.6,
)
const standardHours = computed(() => analysisData.value?.standard_workday_hours ?? 7.6)

const summary = computed(() => analysisData.value?.summary)

const filteredDailyRows = computed(() => {
  const rows = analysisData.value?.daily_by_operator ?? []
  if (filterOperatorId.value === '') return rows
  return rows.filter((r) => r.operator_user_id === filterOperatorId.value)
})

const filteredByOperator = computed(() => {
  const rows = analysisData.value?.by_operator ?? []
  if (filterOperatorId.value === '') return rows
  return rows.filter((r) => r.operator_user_id === filterOperatorId.value)
})

const chartDailyRows = computed(() => {
  const data = analysisData.value
  if (!data) return []
  if (filterOperatorId.value === '') {
    return data.daily ?? []
  }
  return (data.daily_by_operator ?? [])
    .filter((r) => r.operator_user_id === filterOperatorId.value)
    .slice()
    .sort((a, b) => a.day.localeCompare(b.day))
})

const chartBadgeLabel = computed(() => {
  if (filterOperatorId.value === '') return '溶接作業者合算'
  const found = operatorOptions.value.find((o) => o.id === filterOperatorId.value)
  return found ? operatorLabel(found) : '溶接作業者別'
})

const overtimeChartTotalLabel = computed(() => {
  const totalMin = chartDailyRows.value.reduce((sum, d) => sum + overtimeMinFromRow(d), 0)
  return fmtDuration(totalMin)
})

const sessionsWithoutTimeDetails = computed(
  () => analysisData.value?.sessions_without_time ?? [],
)

const hasDataGaps = computed(() => (analysisData.value?.data_gaps?.length ?? 0) > 0)

const dataGapsCount = computed(() => analysisData.value?.data_gaps?.length ?? 0)

const kpiCards = computed(() => {
  const s = summary.value
  return [
    {
      key: 'util',
      label: '平均稼働率',
      value: fmtPct(s?.utilization_percent),
      hint: '出勤日基準7.6h',
      icon: markRaw(TrendCharts),
      tone: 'green',
    },
    {
      key: 'calendar',
      label: 'カレンダー稼働率',
      value: fmtPct(s?.calendar_utilization_percent),
      hint: `会社稼働日 ${s?.calendar_workdays_in_range ?? '—'} 日`,
      icon: markRaw(Calendar),
      tone: 'blue',
    },
    {
      key: 'net',
      label: '正味稼働合計',
      value: fmtDuration(s?.sum_net_production_min),
      hint: `${fmtInt(s?.session_count)} セッション`,
      icon: markRaw(Timer),
      tone: 'indigo',
    },
    {
      key: 'overtime',
      label: '残業合計',
      value: fmtDuration(s?.overtime_min),
      hint: `所定内 ${fmtDuration(s?.regular_min)}`,
      icon: markRaw(Sunny),
      tone: 'amber',
    },
    {
      key: 'operators',
      label: '溶接作業者',
      value: fmtInt(s?.operator_count),
      hint: s?.unassigned_session_count ? `未割当 ${s.unassigned_session_count} 件` : '対象人数',
      icon: markRaw(User),
      tone: 'violet',
    },
  ]
})

function operatorLabel(u: UserListItem): string {
  const name = (u.full_name ?? '').trim()
  const username = (u.username ?? '').trim()
  if (name && username) return `${name}（${username}）`
  return name || username || `#${u.id}`
}

async function loadOperators() {
  try {
    operatorOptions.value = await fetchWeldingSectionOperators()
    const allowed = new Set(operatorOptions.value.map((u) => u.id))
    if (filterOperatorId.value !== '' && !allowed.has(filterOperatorId.value)) {
      filterOperatorId.value = ''
    }
  } catch {
    operatorOptions.value = []
  }
}

function sessionProductLabel(s: WeldingUtilizationSessionGap): string {
  const cd = s.product_cd?.trim()
  const name = s.product_name?.trim()
  if (cd && name) return `${cd}（${name}）`
  return cd || name || '製品情報なし'
}

function sessionTimeGapReason(s: WeldingUtilizationSessionGap): string {
  const started = s.mes_production_started_at
  const ended = s.mes_production_ended_at
  if (!started && !ended) return '開始・終了時刻なし'
  if (!started) return '開始時刻なし'
  if (!ended) return '終了時刻なし'
  return '正味秒未設定'
}

function operatorRankClass(index: number): string {
  if (index === 0) return 'iua-row-rank--gold'
  if (index === 1) return 'iua-row-rank--silver'
  if (index === 2) return 'iua-row-rank--bronze'
  return ''
}

function utilPillClass(pct?: number | null): string {
  const v = Number(pct ?? 0)
  if (v >= 85) return 'iua-util-pill--high'
  if (v >= 60) return 'iua-util-pill--mid'
  if (v > 0) return 'iua-util-pill--low'
  return 'iua-util-pill--none'
}

function fmtScheduledHours(hours?: number | null): string {
  if (hours == null || hours <= 0) return '—'
  return hours.toFixed(1)
}

function fmtInt(v?: number | null): string {
  if (v == null || Number.isNaN(v)) return '—'
  return v.toLocaleString('ja-JP')
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

function overtimeMinFromRow(d: { overtime_min?: number | null; sum_overtime_sec?: number | null }): number {
  return overtimeMinFromUtilizationRow(d)
}

function buildReportFilters(): WeldingUtilizationReportFilters | null {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) return null

  let operatorFilterLabel = '（すべて）'
  if (filterOperatorId.value !== '') {
    const found = operatorOptions.value.find((o) => o.id === filterOperatorId.value)
    operatorFilterLabel = found ? operatorLabel(found) : `#${filterOperatorId.value}`
  }

  return {
    startDate: start,
    endDate: end,
    operatorLabel: operatorFilterLabel,
    includeIncomplete: includeIncomplete.value,
  }
}

function captureChartDataUrl(chart: ECharts | null): string | null {
  if (!chart || chart.isDisposed()) return null
  try {
    return chart.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#ffffff',
    })
  } catch {
    return null
  }
}

function waitForChartPaint(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
}

async function buildReportContext(): Promise<WeldingUtilizationReportContext | null> {
  const filters = buildReportFilters()
  if (!analysisData.value || !filters) return null

  const dailyRows = chartDailyRows.value
  dailyChart?.resize()
  overtimeChart?.resize()
  await nextTick()
  await waitForChartPaint()

  const dailySrc =
    captureChartDataUrl(dailyChart) ?? (await captureUtilizationDailyChartDataUrl(dailyRows))
  const overtimeSrc =
    captureChartDataUrl(overtimeChart) ??
    (await captureUtilizationChartDataUrl(buildUtilizationOvertimeChartOption(dailyRows)))

  return {
    filters,
    kpiCards: kpiCards.value.map((card) => ({
      label: card.label,
      value: card.value,
      hint: card.hint,
      tone: card.tone as 'green' | 'blue' | 'indigo' | 'amber' | 'violet',
    })),
    charts: {
      daily: dailySrc,
      overtime: overtimeSrc,
    },
    operatorRows: filteredByOperator.value,
    dailyDetailRows: filteredDailyRows.value,
  }
}

async function handleBatchDailyPrint() {
  const filters = buildReportFilters()
  const data = analysisData.value
  if (!filters || !data) {
    ElMessage.warning('出力する分析データがありません')
    return
  }

  const items: UtilizationDailyBatchItem[] = []
  const aggDaily = data.daily ?? []
  if (aggDaily.length) {
    items.push({
      operatorUserId: null,
      operatorLabel: '溶接作業者合算',
      chartSrc: await captureUtilizationDailyChartDataUrl(aggDaily),
      dayCount: aggDaily.length,
      avgUtilizationPercent: avgUtilizationPercent(aggDaily),
      sumOvertimeMin: sumOvertimeMinFromDaily(aggDaily),
    })
  }

  for (const op of operatorOptions.value) {
    const daily = (data.daily_by_operator ?? [])
      .filter((r) => r.operator_user_id === op.id)
      .slice()
      .sort((a, b) => a.day.localeCompare(b.day))
    if (!daily.length) continue
    items.push({
      operatorUserId: op.id,
      operatorLabel: operatorLabel(op),
      chartSrc: await captureUtilizationDailyChartDataUrl(daily),
      dayCount: daily.length,
      avgUtilizationPercent: avgUtilizationPercent(daily),
      sumOvertimeMin: sumOvertimeMinFromDaily(daily),
    })
  }

  if (!items.length) {
    ElMessage.warning('印刷できる日別データがありません')
    return
  }

  printWeldingUtilizationDailyBatch(filters, items)
}

async function handleReportCommand(command: string | number | object) {
  const cmd = String(command)
  if (!analysisData.value) {
    ElMessage.warning('出力する分析データがありません')
    return
  }

  exportBusy.value = true
  try {
    if (cmd === 'print-daily-batch') {
      await handleBatchDailyPrint()
      return
    }

    const ctx = await buildReportContext()
    if (!ctx) {
      ElMessage.warning('出力する分析データがありません')
      return
    }

    if (cmd === 'print-full') {
      printWeldingUtilizationReport(ctx)
      return
    }

    if (cmd === 'print-daily') {
      if (!chartDailyRows.value.length) {
        ElMessage.warning('印刷できる日別データがありません')
        return
      }
      printWeldingUtilizationDailySection(ctx)
      return
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : 'レポート出力に失敗しました')
  } finally {
    exportBusy.value = false
  }
}

function disposeCharts() {
  dailyChart?.dispose()
  overtimeChart?.dispose()
  dailyChart = null
  overtimeChart = null
}

function renderDailyChart() {
  const el = dailyChartRef.value
  const daily = chartDailyRows.value
  if (!el || !daily.length) {
    dailyChart?.dispose()
    dailyChart = null
    return
  }
  if (!dailyChart) {
    dailyChart = echarts.init(el)
  }
  dailyChart.setOption(buildUtilizationDailyChartOption(daily), true)
}

function renderOvertimeChart() {
  const el = overtimeChartRef.value
  const daily = chartDailyRows.value
  if (!el || !daily.length) {
    overtimeChart?.dispose()
    overtimeChart = null
    return
  }
  if (!overtimeChart) {
    overtimeChart = echarts.init(el)
  }
  overtimeChart.setOption(buildUtilizationOvertimeChartOption(daily), true)
}

function renderCharts() {
  renderDailyChart()
  renderOvertimeChart()
}

function handleChartResize() {
  dailyChart?.resize()
  overtimeChart?.resize()
}

async function loadAnalysis() {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) {
    ElMessage.warning('期間を選択してください')
    return
  }
  loading.value = true
  try {
    const res = await fetchWeldingUtilizationAnalysis({
      start_date: start,
      end_date: end,
      include_incomplete: includeIncomplete.value,
      use_company_calendar: true,
    })
    if (!res?.success || !res.data) {
      ElMessage.error(res?.message || '分析データの取得に失敗しました')
      analysisData.value = null
      operatorOptions.value = []
      disposeCharts()
      return
    }
    analysisData.value = res.data
    await loadOperators()
    await nextTick()
    renderCharts()
  } catch (e: unknown) {
    analysisData.value = null
    operatorOptions.value = []
    disposeCharts()
    ElMessage.error(e instanceof Error ? e.message : '分析データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

watch(
  chartDailyRows,
  () => nextTick(() => renderCharts()),
)

watch(
  [dateRange, includeIncomplete],
  () => {
    filterOperatorId.value = ''
    loadAnalysis()
  },
  { deep: true, immediate: true },
)

onMounted(async () => {
  window.addEventListener('resize', handleChartResize)
  await loadOperators()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleChartResize)
  disposeCharts()
})
</script>

<style scoped>
.iua {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 12px 20px;
  min-height: 100%;
  overflow: hidden;
}

.iua__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.iua__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  animation: iua-float 14s ease-in-out infinite;
}

.iua__orb--1 {
  width: 280px;
  height: 280px;
  top: -8%;
  right: -4%;
  background: rgba(16, 185, 129, 0.2);
}

.iua__orb--2 {
  width: 220px;
  height: 220px;
  top: 28%;
  left: -6%;
  background: rgba(99, 102, 241, 0.14);
  animation-delay: -5s;
}

.iua__orb--3 {
  width: 180px;
  height: 180px;
  bottom: 8%;
  left: 38%;
  background: rgba(14, 165, 233, 0.16);
  animation-delay: -9s;
}

@keyframes iua-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(10px, -14px) scale(1.04); }
}

.iua-hero,
.iua-toolbar,
.iua-cal-banner,
.iua-body {
  position: relative;
  z-index: 1;
}

.iua-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.94) 0%, rgba(240, 253, 244, 0.78) 100%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 8px 32px rgba(15, 23, 42, 0.07),
    0 2px 8px rgba(16, 185, 129, 0.08);
  backdrop-filter: blur(12px);
}

.iua-hero__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.iua-hero__icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(145deg, #34d399 0%, #10b981 50%, #059669 100%);
  box-shadow:
    0 4px 14px rgba(16, 185, 129, 0.42),
    0 1px 0 rgba(255, 255, 255, 0.35) inset;
  flex-shrink: 0;
}

.iua-hero__icon-glow {
  position: absolute;
  inset: -4px;
  border-radius: 18px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.35), transparent 70%);
  z-index: -1;
  animation: iua-pulse 3s ease-in-out infinite;
}

@keyframes iua-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.08); }
}

.iua-hero__eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #059669;
}

.iua-hero__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.iua-hero__title {
  margin: 2px 0 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.25;
}

.iua-gaps-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-top: 2px;
  padding: 0;
  border: 1px solid rgba(251, 191, 36, 0.45);
  border-radius: 999px;
  color: #d97706;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.18);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  flex-shrink: 0;
}

.iua-gaps-trigger:hover {
  transform: translateY(-1px);
  border-color: rgba(245, 158, 11, 0.65);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.24);
}

.iua-gaps-trigger__badge {
  position: absolute;
  top: -5px;
  right: -5px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  color: #fff;
  background: #f59e0b;
  box-shadow: 0 1px 4px rgba(245, 158, 11, 0.35);
}

.iua-hero__meta {
  margin: 2px 0 0;
  font-size: 11px;
  color: #64748b;
}

.iua-hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.iua-hero__range {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.18);
}

.iua-btn {
  height: 34px !important;
  padding: 0 16px !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  border: none !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

.iua-btn__inner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.iua-btn__icon {
  font-size: 14px;
}

.iua-btn--refresh {
  background: linear-gradient(135deg, #047857 0%, #10b981 52%, #14b8a6 100%) !important;
  color: #fff !important;
  box-shadow:
    0 4px 14px rgba(16, 185, 129, 0.38),
    0 1px 0 rgba(255, 255, 255, 0.22) inset;
}

.iua-btn--refresh:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.06);
}

.iua-btn--report {
  background: linear-gradient(135deg, #fff 0%, #f0fdf4 100%) !important;
  color: #047857 !important;
  border: 1px solid rgba(16, 185, 129, 0.28) !important;
  box-shadow: 0 2px 10px rgba(16, 185, 129, 0.12);
}

.iua-btn--report:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(16, 185, 129, 0.45) !important;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.18);
}

.iua-btn__caret {
  font-size: 12px;
  margin-left: 2px;
}

.iua-panel {
  border-radius: 14px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 252, 0.9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 4px 24px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(10px);
  transition: box-shadow 0.25s ease;
}

.iua-panel:hover {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 10px 36px rgba(15, 23, 42, 0.08),
    0 4px 12px rgba(16, 185, 129, 0.06);
}

.iua-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 14px;
}

.iua-toolbar__fields {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  flex: 1;
  min-width: 0;
}

.iua-field {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  min-height: 32px;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 2px 6px rgba(15, 23, 42, 0.05);
  transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
}

.iua-field:hover {
  transform: translateY(-1px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 4px 12px rgba(15, 23, 42, 0.08);
}

.iua-field:focus-within {
  border-color: rgba(16, 185, 129, 0.4);
  box-shadow:
    0 0 0 3px rgba(16, 185, 129, 0.1),
    0 2px 8px rgba(16, 185, 129, 0.12);
}

.iua-field__pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding: 0 11px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
  border-right: 1px solid rgba(255, 255, 255, 0.35);
}

.iua-field__pill .el-icon {
  font-size: 13px;
}

.iua-field--period .iua-field__pill {
  color: #047857;
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
}

.iua-field--inspector .iua-field__pill {
  color: #4338ca;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
}

.iua-field--check .iua-field__pill {
  color: #92400e;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
}

.iua-field--check {
  cursor: default;
  padding-right: 10px;
}

.iua-field--check .iua-field__pill--check {
  padding: 0 9px;
  font-size: 10px;
}

.iua-field--wide {
  min-width: 220px;
}

.iua-field__control {
  flex: 1;
  min-width: 0;
}

.iua-field__date {
  width: 228px !important;
}

.iua-field__select {
  width: 168px;
}

.iua-field :deep(.el-input__wrapper),
.iua-field :deep(.el-select__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  min-height: 30px !important;
}

.iua-field :deep(.el-input__wrapper:hover),
.iua-field :deep(.el-select__wrapper:hover),
.iua-field :deep(.el-input__wrapper.is-focus),
.iua-field :deep(.el-select__wrapper.is-focused) {
  box-shadow: none !important;
}

.iua-field--check :deep(.el-checkbox) {
  height: 30px;
  padding: 0 4px 0 8px;
  display: inline-flex;
  align-items: center;
}

.iua-field--check :deep(.el-checkbox__label) {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding-left: 6px;
}

.iua-cal-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 12px;
  font-size: 11px;
  color: #047857;
  background: linear-gradient(90deg, rgba(236, 253, 245, 0.95), rgba(240, 253, 244, 0.9));
  border-color: rgba(16, 185, 129, 0.22);
}

.iua-cal-banner__icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  color: #059669;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(16, 185, 129, 0.2);
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

.iua-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.iua-kpi {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.iua-kpi__card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 12px 11px 10px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid transparent;
  animation: iua-kpi-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.iua-kpi__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.iua-kpi__card--green {
  background: linear-gradient(160deg, #fff 0%, #ecfdf5 45%, #d1fae5 100%);
  border-color: rgba(16, 185, 129, 0.24);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.12);
}

.iua-kpi__card--green .iua-kpi__accent { background: linear-gradient(90deg, #10b981, #34d399); }
.iua-kpi__card--green .iua-kpi__label { color: #059669; }
.iua-kpi__card--green .iua-kpi__value { color: #047857; font-size: 22px; }

.iua-kpi__card--blue {
  background: linear-gradient(160deg, #fff 0%, #eff6ff 45%, #dbeafe 100%);
  border-color: rgba(59, 130, 246, 0.22);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.1);
}

.iua-kpi__card--blue .iua-kpi__accent { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.iua-kpi__card--blue .iua-kpi__label { color: #2563eb; }
.iua-kpi__card--blue .iua-kpi__value { color: #1d4ed8; }

.iua-kpi__card--indigo {
  background: linear-gradient(160deg, #fff 0%, #eef2ff 45%, #e0e7ff 100%);
  border-color: rgba(99, 102, 241, 0.22);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.1);
}

.iua-kpi__card--indigo .iua-kpi__accent { background: linear-gradient(90deg, #6366f1, #818cf8); }
.iua-kpi__card--indigo .iua-kpi__label { color: #6366f1; }
.iua-kpi__card--indigo .iua-kpi__value { color: #4338ca; }

.iua-kpi__card--amber {
  background: linear-gradient(160deg, #fff 0%, #fff7ed 45%, #ffedd5 100%);
  border-color: rgba(249, 115, 22, 0.22);
  box-shadow: 0 8px 20px rgba(249, 115, 22, 0.1);
}

.iua-kpi__card--amber .iua-kpi__accent { background: linear-gradient(90deg, #f97316, #fb923c); }
.iua-kpi__card--amber .iua-kpi__label { color: #ea580c; }
.iua-kpi__card--amber .iua-kpi__value { color: #c2410c; }

.iua-kpi__card--violet {
  background: linear-gradient(160deg, #fff 0%, #f5f3ff 45%, #ede9fe 100%);
  border-color: rgba(139, 92, 246, 0.22);
  box-shadow: 0 8px 20px rgba(139, 92, 246, 0.1);
}

.iua-kpi__card--violet .iua-kpi__accent { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.iua-kpi__card--violet .iua-kpi__label { color: #7c3aed; }
.iua-kpi__card--violet .iua-kpi__value { color: #6d28d9; }

.iua-kpi__icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.15);
}

.iua-kpi__icon-wrap--green { background: linear-gradient(145deg, #34d399, #059669); }
.iua-kpi__icon-wrap--blue { background: linear-gradient(145deg, #60a5fa, #2563eb); }
.iua-kpi__icon-wrap--indigo { background: linear-gradient(145deg, #818cf8, #4f46e5); }
.iua-kpi__icon-wrap--amber { background: linear-gradient(145deg, #fb923c, #ea580c); }
.iua-kpi__icon-wrap--violet { background: linear-gradient(145deg, #a78bfa, #7c3aed); }

.iua-kpi__content {
  min-width: 0;
  flex: 1;
}

.iua-kpi__label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.iua-kpi__value {
  margin-top: 3px;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
}

.iua-kpi__hint {
  margin-top: 3px;
  font-size: 10px;
  color: #94a3b8;
}

.iua-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.iua-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.iua-panel--chart {
  padding: 12px 14px;
}

.iua-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.iua-panel--overtime {
  background: linear-gradient(165deg, #fff 0%, #fffbeb 100%);
  border-color: rgba(245, 158, 11, 0.16);
}

.iua-panel__ico--overtime {
  color: #f59e0b;
}

.iua-panel__badge--overtime {
  color: #b45309;
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.2);
}

.iua-chart--overtime {
  background: linear-gradient(180deg, #fffbeb 0%, #fff 100%);
  border-color: rgba(253, 230, 138, 0.65);
}

.iua-fade-in--d3b {
  animation-delay: 0.14s;
}

.iua-panel--operator {
  padding: 12px 14px;
  background: linear-gradient(165deg, #fff 0%, #f5f3ff 100%);
  border-color: rgba(99, 102, 241, 0.14);
}

.iua-panel--daily {
  padding: 12px 14px;
  background: linear-gradient(165deg, #fff 0%, #f0fdf4 100%);
  border-color: rgba(16, 185, 129, 0.14);
}

.iua-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.iua-panel__title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.iua-panel__ico {
  color: #059669;
  font-size: 16px;
}

.iua-panel__ico--operator {
  color: #6366f1;
}

.iua-panel__ico--daily {
  color: #10b981;
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
  border: 1px solid rgba(16, 185, 129, 0.16);
}

.iua-panel__badge--soft {
  color: #64748b;
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.2);
}

.iua-panel__badge--daily {
  color: #047857;
  background: rgba(16, 185, 129, 0.12);
}

.iua-chart {
  width: 100%;
  border-radius: 12px;
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.iua-chart--main {
  height: 300px;
}

.iua-table :deep(.el-table__header th) {
  background: #f8fafc !important;
  font-size: 11px;
}

.iua-table :deep(.el-table__body td) {
  font-size: 11px;
}

.iua-table--operator :deep(.el-table__header th) {
  background: linear-gradient(180deg, #eef2ff, #e0e7ff) !important;
  color: #4338ca;
}

.iua-table--daily :deep(.el-table__header th) {
  background: linear-gradient(180deg, #ecfdf5, #d1fae5) !important;
  color: #047857;
}

.iua-table--operator :deep(.el-table__body tr:hover > td) {
  background: rgba(99, 102, 241, 0.06) !important;
}

.iua-table--daily :deep(.el-table__body tr:hover > td) {
  background: rgba(16, 185, 129, 0.06) !important;
}

.iua-row-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 4px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  background: rgba(148, 163, 184, 0.15);
}

.iua-row-rank--gold {
  color: #92400e;
  background: linear-gradient(135deg, #fde68a, #fcd34d);
}

.iua-row-rank--silver {
  color: #475569;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
}

.iua-row-rank--bronze {
  color: #9a3412;
  background: linear-gradient(135deg, #fed7aa, #fdba74);
}

.iua-util-pill {
  display: inline-block;
  min-width: 44px;
  padding: 1px 6px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.iua-util-pill--high {
  color: #047857;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.iua-util-pill--mid {
  color: #0369a1;
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.18);
}

.iua-util-pill--low {
  color: #c2410c;
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.18);
}

.iua-util-pill--none {
  color: #94a3b8;
  background: rgba(148, 163, 184, 0.1);
}

.iua-num {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.iua-num--warn {
  color: #ea580c;
}

.iua-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 280px;
  padding: 48px 20px;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  background: rgba(255, 255, 255, 0.6);
  color: #64748b;
}

.iua-empty__icon {
  color: #94a3b8;
  opacity: 0.7;
}

.iua-empty__text {
  margin: 0;
  font-size: 13px;
}

.iua-fade-in {
  animation: iua-fade-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.iua-fade-in--d1 { animation-delay: 0.05s; }
.iua-fade-in--d2 { animation-delay: 0.1s; }
.iua-fade-in--d3 { animation-delay: 0.15s; }
.iua-fade-in--d4 { animation-delay: 0.2s; }
.iua-fade-in--d5 { animation-delay: 0.25s; }

@keyframes iua-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes iua-kpi-in {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.iua-reveal-enter-active {
  transition: opacity 0.4s ease, transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.iua-reveal-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.iua-reveal-enter-from,
.iua-reveal-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

@media (max-width: 1200px) {
  .iua-kpi {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .iua-split {
    grid-template-columns: 1fr;
  }

  .iua-hero {
    flex-direction: column;
    align-items: flex-start;
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

  .iua-field__date,
  .iua-field__select {
    width: 100% !important;
  }
}
</style>

<style>
.iua-gaps-popper {
  padding: 0 !important;
  border: 1px solid rgba(251, 191, 36, 0.35) !important;
  border-radius: 12px !important;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.12) !important;
}

.iua-gaps-panel {
  padding: 12px 14px;
  max-height: 360px;
  overflow: auto;
}

.iua-gaps-panel__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
}

.iua-gaps-panel__ico {
  color: #d97706;
  font-size: 16px;
}

.iua-gaps-panel__title {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.iua-gaps-popper .iua-gaps__list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #475569;
}

.iua-gaps-popper .iua-gaps__sublist {
  margin: 6px 0 0;
  padding: 8px 10px;
  list-style: none;
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.95);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.iua-gaps-popper .iua-gaps__detail {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  padding: 4px 0;
  font-size: 11px;
  color: #475569;
}

.iua-gaps-popper .iua-gaps__detail + .iua-gaps__detail {
  border-top: 1px dashed rgba(226, 232, 240, 0.95);
}

.iua-gaps-popper .iua-gaps__detail-id {
  font-weight: 700;
  color: #334155;
}

.iua-gaps-popper .iua-gaps__detail-reason {
  color: #b45309;
  font-weight: 600;
}

.iua-report-dropdown.el-popper {
  padding: 6px !important;
  border-radius: 12px !important;
  border: 1px solid rgba(16, 185, 129, 0.2) !important;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.12) !important;
}

.iua-report-dropdown .el-popper__arrow::before {
  border-color: rgba(16, 185, 129, 0.2) !important;
}

.iua-report-dropdown .iua-report-menu {
  padding: 4px !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.iua-report-dropdown .el-dropdown-menu__item {
  padding: 0 !important;
  line-height: 1.3 !important;
  border-radius: 8px !important;
  margin-bottom: 2px !important;
}

.iua-report-dropdown .el-dropdown-menu__item:last-child {
  margin-bottom: 0 !important;
}

.iua-report-dropdown .el-dropdown-menu__item--divided {
  margin-top: 6px !important;
  padding-top: 6px !important;
  border-top: 1px solid rgba(226, 232, 240, 0.9) !important;
}

.iua-report-dropdown .iua-report-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px !important;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.iua-report-dropdown .iua-report-item__icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  flex-shrink: 0;
  font-size: 14px;
}

.iua-report-dropdown .iua-report-item__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.iua-report-dropdown .iua-report-item__label {
  font-size: 12px;
  font-weight: 700;
  color: #1e293b;
}

.iua-report-dropdown .iua-report-item__hint {
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.3;
}

.iua-report-dropdown .iua-report-item--green .iua-report-item__icon-wrap {
  color: #047857;
  background: rgba(16, 185, 129, 0.12);
}

.iua-report-dropdown .iua-report-item--sky .iua-report-item__icon-wrap {
  color: #0369a1;
  background: rgba(14, 165, 233, 0.12);
}

.iua-report-dropdown .iua-report-item--teal .iua-report-item__icon-wrap {
  color: #0f766e;
  background: rgba(20, 184, 166, 0.12);
}

.iua-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .iua-report-item--green {
  background: rgba(16, 185, 129, 0.08);
}

.iua-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .iua-report-item--sky {
  background: rgba(14, 165, 233, 0.08);
}

.iua-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .iua-report-item--teal {
  background: rgba(20, 184, 166, 0.08);
}
</style>
