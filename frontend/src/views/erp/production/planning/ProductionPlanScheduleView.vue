<template>
  <div class="plan-schedule-view">
    <div class="page-header psv-surface">
      <div class="header-left">
        <div class="title-wrap">
          <h2 class="psv-title">{{ t('menu.ERP_PRODUCTION_PLAN_SCHEDULES') }}</h2>
        </div>
        <div class="header-stats">
          <span class="psv-stat psv-stat--total">
            <span class="psv-stat__k">{{ t('productionPlanSchedule.totalFetched') }}</span>
            <span class="psv-stat__v">{{ enrichedRows.length }}</span>
          </span>
          <span class="psv-stat psv-stat--shown">
            <span class="psv-stat__k">{{ t('productionPlanSchedule.shown') }}</span>
            <span class="psv-stat__v">{{ displayRows.length }}</span>
          </span>
        </div>
      </div>
      <div class="header-actions">
        <el-button
          class="header-btn header-btn--print"
          type="warning"
          :icon="Printer"
          :disabled="loading || displayRows.length === 0"
          @click="handlePrint"
        >
          {{ t('productionPlanSchedule.print') }}
        </el-button>
        <el-button
          class="header-btn header-btn--query"
          type="primary"
          :icon="Refresh"
          :loading="loading"
          @click="fetchData"
        >
          {{ t('common.query') }}
        </el-button>
      </div>
    </div>

    <div class="filter-bar psv-surface psv-surface--toolbar">
      <el-form :inline="true" size="small" class="filter-form">
        <el-form-item :label="t('productionPlanSchedule.month')">
          <el-select v-model="filterMonth" style="width: 120px" @change="onMonthChange">
            <el-option v-for="m in monthChoices" :key="m" :label="`${m}${t('productionPlanSchedule.monthSuffix')}`" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('productionPlanSchedule.engineering')">
          <el-select
            v-model="filterEngineering"
            clearable
            :placeholder="t('productionPlanSchedule.all')"
            style="width: 130px"
            @change="fetchData"
          >
            <el-option :label="t('productionPlanSchedule.forming')" value="成型" />
            <el-option :label="t('productionPlanSchedule.welding')" value="溶接" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('productionPlanSchedule.machineName')">
          <el-select
            v-model="filterMachineName"
            clearable
            filterable
            :placeholder="t('productionPlanSchedule.all')"
            style="width: 200px"
          >
            <el-option v-for="name in machineOptions" :key="name" :label="name" :value="name" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-card grouped-card psv-surface psv-surface--main" v-loading="loading">
      <div v-if="!loading && groupedSections.length === 0" class="empty-hint">
        <el-empty :description="t('productionPlanSchedule.empty')" />
      </div>
      <div v-else class="grouped-scroll">
        <template v-for="(sec, si) in groupedSections" :key="`sec-${si}-${sec.monthLabel}-${sec.engineering}`">
          <div class="section-head section-head--enter" :style="{ '--psv-enter-delay': `${si * 42}ms` }">
            <span class="section-label">{{ t('productionPlanSchedule.monthCol') }}：{{ sec.monthLabel }}</span>
            <span class="section-gap" />
            <span class="section-label">{{ t('productionPlanSchedule.engineeringCol') }}：{{ sec.engineering }}</span>
            <template v-for="crit in [sectionCriticalProgressLines(sec)]" :key="`${si}-sec-crit`">
              <template v-if="crit.overPlan.length > 0 || crit.severeBehind.length > 0">
                <span class="section-gap section-gap--wide" />
                <div class="section-head-progress-alerts">
                  <span v-if="crit.overPlan.length > 0" class="section-head-alert">
                    <span class="section-head-alert-label">{{ t('productionPlanSchedule.productionProgress') }}</span>
                    <el-tag type="danger" size="small" effect="light" class="section-head-alert-tag">
                      {{ t('productionPlanSchedule.ovProgressOverPlan') }}
                    </el-tag>
                    <span class="section-head-alert-lines">{{ crit.overPlan.join('、') }}</span>
                  </span>
                  <span v-if="crit.severeBehind.length > 0" class="section-head-alert">
                    <span class="section-head-alert-label">{{ t('productionPlanSchedule.productionProgress') }}</span>
                    <el-tag type="danger" size="small" effect="dark" class="section-head-alert-tag">
                      {{ t('productionPlanSchedule.ovProgressSevereBehind') }}
                    </el-tag>
                    <span class="section-head-alert-lines">{{ crit.severeBehind.join('、') }}</span>
                  </span>
                </div>
              </template>
            </template>
          </div>
          <div
            v-for="(mc, mi) in sec.machines"
            :key="`mc-${si}-${mi}-${mc.machineName}`"
            class="machine-block machine-block--enter"
            :style="{ '--psv-m-delay': `${si * 42 + mi * 28}ms` }"
          >
            <div class="machine-head machine-head--sheet">
              <span class="machine-head-line">
                {{ t('productionPlanSchedule.machineName') }}：{{ mc.machineName }}
              </span>
              <span
                v-for="ov in [machineOvHeadParts(sec, mc)]"
                :key="`${sec.engineering}-${mc.machineName}-ov`"
                class="machine-head-ov"
              >
                {{ t('productionPlanSchedule.operationVariance') }}：
                <span
                  class="machine-head-ov-value"
                  :class="{ 'machine-head-ov-value--negative': ov.negative }"
                >
                  {{ ov.display }}
                </span>
                <span class="machine-head-pp-wrap">
                  {{ t('productionPlanSchedule.productionProgress') }}：
                  <el-tag size="small" :type="ov.tagType" :effect="ov.tagEffect" class="machine-head-pp-tag">
                    {{ ov.progressLabel }}
                  </el-tag>
                </span>
              </span>
            </div>
            <el-table :data="mc.rows" size="small" border stripe class="nest-table nest-table--polish">
              <el-table-column
                prop="order_no"
                :label="t('productionPlanSchedule.productionOrder')"
                width="70"
                align="center"
              />
              <el-table-column
                :label="t('productionPlanSchedule.productName')"
                width="140"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span class="product-name-cell" @dblclick.stop="openPlanUpdatesDialog(row)">
                    {{ row.item_name }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column :label="t('productionPlanSchedule.startDate')" width="100">
                <template #default="{ row }">{{ displayDate(scheduleStartIso(row)) }}</template>
              </el-table-column>
              <el-table-column :label="t('productionPlanSchedule.endDate')" width="100">
                <template #default="{ row }">{{ displayDate(scheduleEndIso(row)) }}</template>
              </el-table-column>
              <el-table-column
                :label="t('productionPlanSchedule.plannedQty')"
                width="90"
                align="right"
              >
                <template #default="{ row }">{{ formatNum(row.planned_process_qty) }}</template>
              </el-table-column>
              <el-table-column
                :label="t('productionPlanSchedule.actual')"
                width="90"
                align="right"
              >
                <template #default="{ row }">{{ formatNum(rowActualQty(row)) }}</template>
              </el-table-column>
              <el-table-column
                :label="t('productionPlanSchedule.remaining')"
                width="90"
                align="right"
              >
                <template #default="{ row }">{{ formatRemainder(row) }}</template>
              </el-table-column>
              <el-table-column
                :label="t('productionPlanSchedule.progress')"
                width="90"
                align="right"
              >
                <template #default="{ row }">{{ formatProgress(row) }}</template>
              </el-table-column>
              <el-table-column
                :label="t('productionPlanSchedule.prodStatus')"
                width="120"
                align="center"
              >
                <template #default="{ row }">
                  <div class="status-lamp-cell">
                    <span
                      class="status-lamp-dot"
                      :class="{
                        'status-lamp-dot--done': productionStatusKind(row) === 'done',
                        'status-lamp-dot--ongoing': productionStatusKind(row) === 'ongoing',
                        'status-lamp-dot--pending': productionStatusKind(row) === 'pending',
                      }"
                      :title="productionStatusLabel(row)"
                      role="img"
                      :aria-label="productionStatusLabel(row)"
                    />
                    <span class="status-lamp-label">{{ productionStatusLabel(row) }}</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </div>
    </div>

    <el-dialog
      v-model="planUpdatesVisible"
      :title="planUpdatesDialogTitle"
      width="min(760px, 96vw)"
      destroy-on-close
      class="daily-schedule-dialog"
      append-to-body
      align-center
      @closed="planUpdatesRows = []"
    >
      <div v-loading="planUpdatesLoading" class="daily-schedule-dialog__body">
        <el-table
          v-if="planUpdatesRows.length > 0"
          :data="planUpdatesDisplayRows"
          class="daily-schedule-table"
          size="small"
          border
          stripe
          max-height="440"
          :span-method="planUpdatesSpanMethod"
        >
          <el-table-column
            prop="process_name"
            :label="t('productionPlanSchedule.engineeringCol')"
            width="80"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column
            prop="machine_name"
            :label="t('productionPlanSchedule.machineName')"
            min-width="118"
            show-overflow-tooltip
          />
          <el-table-column
            prop="operator"
            :label="t('productionPlanSchedule.planUpdatesOperator')"
            min-width="100"
            show-overflow-tooltip
          />
          <el-table-column
            prop="plan_date"
            :label="t('productionPlanSchedule.planUpdatesColPlanDate')"
            width="108"
          />
          <el-table-column
            prop="quantity"
            :label="t('productionPlanSchedule.plannedQty')"
            width="88"
            align="right"
          >
            <template #default="{ row }">{{ formatPlanQty(row.quantity) }}</template>
          </el-table-column>
          <el-table-column
            prop="efficiency_rate"
            :label="t('productionPlanSchedule.planUpdatesColEfficiency')"
            width="86"
            align="right"
          >
            <template #default="{ row }">{{ formatOptionalNum(row.efficiency_rate) }}</template>
          </el-table-column>
          <el-table-column
            :label="t('productionPlanSchedule.planUpdatesColRequiredTime')"
            width="92"
            align="right"
          >
            <template #default="{ row }">
              {{ formatRequiredTime(row.quantity, row.efficiency_rate) }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty
          v-else-if="!planUpdatesLoading"
          :description="t('productionPlanSchedule.planUpdatesEmpty')"
          class="daily-schedule-empty"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Printer, Refresh } from '@element-plus/icons-vue'
import request from '@/shared/api/request'
import { fetchPlanOperationRate } from '@/api/planBaseline'
import {
  fetchLines,
  fetchSchedulingGrid,
  type ScheduleGridRow,
  type SchedulingGridResponse,
} from '@/api/aps'

/** 一覧（FormingPlanningList）と同じ APS 工程コード */
const PROCESS_CD_FORMING = 'KT04'
const PROCESS_CD_WELDING = 'KT07'
/** 一覧の日次集計用グリッド期間（FormingPlanningList の buildTableGridRange と同趣旨） */
const TABLE_GRID_PAST_YEARS = 10
const TABLE_GRID_FUTURE_YEARS = 5

const { t, locale } = useI18n()

const PRINT_DOCUMENT_STYLES = `
  * { box-sizing: border-box; }
  html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body {
    margin: 0;
    padding: 5.5mm 6.5mm;
    font-family: 'Segoe UI', 'Meiryo', 'Hiragino Sans', 'Microsoft YaHei', sans-serif;
    font-size: 7.5pt;
    color: #0f172a;
    line-height: 1.32;
    background: #fff;
  }
  .print-header {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1.5mm 5mm;
    margin-bottom: 2.8mm;
    padding-bottom: 2mm;
    border-bottom: 2px solid #2563eb;
  }
  .print-title {
    font-size: 11.5pt;
    font-weight: 800;
    letter-spacing: 0.04em;
    color: #0f172a;
    margin: 0;
    line-height: 1.2;
  }
  .print-meta {
    font-size: 6.8pt;
    color: #475569;
    line-height: 1.35;
    text-align: right;
    max-width: 58%;
  }
  .print-meta-line {
    white-space: nowrap;
  }
  .print-section {
    margin-top: 2.6mm;
  }
  .print-section:first-of-type {
    margin-top: 0.5mm;
  }
  .print-section-title {
    font-size: 8pt;
    font-weight: 700;
    padding: 1.4mm 2.2mm;
    margin: 0 0 1.8mm 0;
    background: linear-gradient(90deg, #e8eefe 0%, #f4f7ff 55%, #fafbfc 100%);
    border: 1px solid #a5b4fc;
    border-radius: 2px;
    color: #1e3a8a;
    letter-spacing: 0.02em;
    line-height: 1.45;
  }
  .print-sec-crit {
    font-weight: 800;
    white-space: normal;
  }
  .print-sec-crit--over {
    color: #b91c1c;
  }
  .print-sec-crit--severe {
    color: #7f1d1d;
  }
  /* ライン単位：見出し＋表をまとめて跨がないよう制御 */
  .print-line-block {
    page-break-inside: avoid;
    break-inside: avoid;
    margin: 0 0 2.2mm 0;
    padding: 1.2mm 2mm 1.5mm 2.4mm;
    background: #f8fafc;
    border-radius: 0 3px 3px 0;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #3b82f6;
  }
  .print-machine-title {
    font-size: 7.3pt;
    font-weight: 700;
    margin: 0 0 0.8mm 0;
    padding: 0 0 0.6mm 0;
    color: #1d4ed8;
  }
  .print-ov-negative {
    color: #b91c1c;
    font-weight: 700;
  }
  .print-ov-flag {
    display: inline-block;
    padding: 0.35mm 1.4mm;
    border-radius: 1.2mm;
    font-size: 6.9pt;
    font-weight: 700;
    vertical-align: middle;
  }
  .print-ov-flag--none {
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #cbd5e1;
  }
  .print-ov-flag--normal {
    background: #dcfce7;
    color: #166534;
    border: 1px solid #86efac;
  }
  .print-ov-flag--ahead {
    background: #dbeafe;
    color: #1e40af;
    border: 1px solid #93c5fd;
  }
  .print-ov-flag--behind {
    background: #ffedd5;
    color: #9a3412;
    border: 1px solid #fdba74;
  }
  .print-ov-flag--over_plan,
  .print-ov-flag--severe_behind {
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
  }
  .print-ov-flag--severe_behind {
    font-weight: 800;
  }
  .print-table {
    width: 100%;
    border-collapse: collapse;
    margin: 0;
    font-size: 6.85pt;
    table-layout: fixed;
    border: 1px solid #94a3b8;
  }
  .print-table th,
  .print-table td {
    border: 1px solid #cbd5e1;
    padding: 0.55mm 0.75mm;
    word-wrap: break-word;
    overflow-wrap: break-word;
    vertical-align: middle;
  }
  .print-table th {
    background: #e2e8f0;
    font-weight: 700;
    color: #334155;
    font-size: 6.5pt;
    padding: 0.65mm 0.75mm;
  }
  .print-table tbody tr:nth-child(even) { background: #ffffff; }
  .print-table tbody tr:nth-child(odd) { background: #f9fafb; }
  .print-table .text-left { text-align: left; }
  .print-table .num { text-align: right; font-variant-numeric: tabular-nums; }
  .status-print-cell {
    text-align: center;
    white-space: nowrap;
    font-size: 6.7pt;
  }
  .print-status-dot {
    display: inline-block;
    width: 2.3mm;
    height: 2.3mm;
    border-radius: 50%;
    margin-right: 1.2mm;
    vertical-align: middle;
    box-shadow: 0 0 0 0.1mm rgba(0,0,0,0.12) inset;
  }
  .print-status-dot--done { background: #64748b; }
  .print-status-dot--ongoing { background: #22c55e; }
  .print-status-dot--pending { background: #f59e0b; }
  @media print {
    body { padding: 4.5mm 5.5mm; }
    .print-line-block {
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .print-table thead { display: table-header-group; }
    .print-table tbody tr { page-break-inside: avoid; }
  }
`

interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
}

type ApsGridListRow = ScheduleGridRow & {
  lineLabel: string
  line_id: number
  engineering: string
  product_cd?: string | null
}

interface EnrichedRow extends ApsGridListRow {
  parsedMonth: number | null
  monthLabel: string
}

interface MachineGroup {
  machineName: string
  rows: EnrichedRow[]
}

interface GroupedSection {
  monthLabel: string
  engineering: string
  machines: MachineGroup[]
}

interface PlanUpdateRecord {
  id?: number
  file_name?: string
  plan_date?: string
  quantity?: number
  machine_name?: string
  machine_cd?: string
  process_name?: string
  operator?: string
  product_name?: string
  product_cd?: string
  efficiency_rate?: number
  setup_time?: number
}

function ymdFromLocalDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function buildTableGridRange(): [string, string] {
  const n = new Date()
  n.setHours(0, 0, 0, 0)
  const start = new Date(n.getFullYear() - TABLE_GRID_PAST_YEARS, n.getMonth(), n.getDate())
  const end = new Date(n.getFullYear() + TABLE_GRID_FUTURE_YEARS, n.getMonth(), n.getDate())
  return [ymdFromLocalDate(start), ymdFromLocalDate(end)]
}

function flattenGridToRows(
  grid: SchedulingGridResponse,
  lineNameById: Map<number, string>,
  engineering: string,
): ApsGridListRow[] {
  const flat: ApsGridListRow[] = []
  for (const block of grid.blocks || []) {
    const label =
      lineNameById.get(block.line_id) ||
      String((block as { line_name?: string }).line_name || '').trim() ||
      block.line_code ||
      `ID ${block.line_id}`
    for (const r of block.rows || []) {
      flat.push({ ...r, lineLabel: label, line_id: block.line_id, engineering })
    }
  }
  return flat
}

function compareByLineThenOrder(a: ApsGridListRow, b: ApsGridListRow): number {
  const lineCmp = (a.lineLabel || '').localeCompare(b.lineLabel || '', 'ja')
  if (lineCmp !== 0) return lineCmp
  const oa = a.order_no ?? 1_000_000 + a.id
  const ob = b.order_no ?? 1_000_000 + b.id
  if (oa !== ob) return Number(oa) - Number(ob)
  return a.id - b.id
}

function compareRowsMerged(a: ApsGridListRow, b: ApsGridListRow): number {
  const ek = engineeringSortKey(a.engineering) - engineeringSortKey(b.engineering)
  if (ek !== 0) return ek
  return compareByLineThenOrder(a, b)
}

/** 日次グリッド行からセルに値がある暦日（FormingPlanningList と同じ） */
function isoDatesWithGridActivity(gr: ScheduleGridRow): string[] {
  const keys = new Set<string>()
  const maps: (Record<string, number> | undefined)[] = [
    gr.daily,
    gr.actual_daily,
    gr.defect_daily,
    gr.upstream_defect_daily,
    gr.remaining_daily,
  ]
  for (const mp of maps) {
    if (!mp) continue
    for (const [d, v] of Object.entries(mp)) {
      if (Number(v || 0) !== 0) keys.add(d)
    }
  }
  return [...keys].sort()
}

/** 一覧の開始・終了（FormingPlanningList effectiveScheduleDateSpan と同じ） */
function effectiveScheduleDateSpan(row: ScheduleGridRow): { start: string | null; end: string | null } {
  const dates = isoDatesWithGridActivity(row)
  if (dates.length === 0) {
    return { start: row.start_date ?? null, end: row.end_date ?? null }
  }
  return { start: dates[0] ?? null, end: dates[dates.length - 1] ?? null }
}

function periodActualForRow(row: ScheduleGridRow, datesOverride: string[]): number {
  const m = row.actual_daily || {}
  const dates1 = datesOverride.length > 0 ? datesOverride : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

function periodRemainingForRow(row: ScheduleGridRow, datesOverride: string[]): number {
  const m = row.remaining_daily || {}
  const dates1 = datesOverride.length > 0 ? datesOverride : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

function scheduleStartIso(row: EnrichedRow): string | undefined {
  const s = effectiveScheduleDateSpan(row).start || row.start_date
  return s ?? undefined
}

function scheduleEndIso(row: EnrichedRow): string | undefined {
  const s = effectiveScheduleDateSpan(row).end || row.end_date
  return s ?? undefined
}

function rowActualQty(row: EnrichedRow): number {
  return periodActualForRow(row, tableGanttDates.value)
}

function tableRemainingLikeForming(row: EnrichedRow): number {
  const remainByDaily = periodRemainingForRow(row, tableGanttDates.value)
  if (remainByDaily > 0) return remainByDaily
  const planned = Number(row.planned_process_qty ?? 0)
  const act = rowActualQty(row)
  const remain = planned - act
  return remain > 0 ? remain : 0
}

function rowOverlapsSelectedCalendarMonth(row: ApsGridListRow): boolean {
  const y = new Date().getFullYear()
  const m = filterMonth.value
  if (m < 1 || m > 12) return false
  const mm = String(m).padStart(2, '0')
  const lastDay = new Date(y, m, 0).getDate()
  const ms = `${y}-${mm}-01`
  const me = `${y}-${mm}-${String(lastDay).padStart(2, '0')}`
  const span = effectiveScheduleDateSpan(row)
  let rs = span.start || row.start_date || null
  let re = span.end || row.end_date || null
  if (!rs && !re) return true
  if (!rs) rs = re
  if (!re) re = rs
  if (!rs || !re) return true
  return !(re < ms || rs > me)
}

function engineeringSortKey(eng: string): number {
  if (eng === '成型') return 0
  if (eng === '溶接') return 1
  return 2
}

function toFiniteNumber(x: unknown): number | null {
  if (x === null || x === undefined || x === '') return null
  const n = Number(x)
  return Number.isFinite(n) ? n : null
}

function formatNum(x: unknown): string {
  const n = toFiniteNumber(x)
  if (n === null) return '—'
  if (Math.abs(n - Math.round(n)) < 1e-9) return String(Math.round(n))
  return String(n)
}

function formatRemainder(row: EnrichedRow): string {
  const v = tableRemainingLikeForming(row)
  if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v))
  return String(v)
}

/** 進捗度：一覧（FormingPlanningList tableProgress）と同じく 実績/計画 */
function formatProgress(row: EnrichedRow): string {
  const planned = Number(row.planned_process_qty ?? 0)
  if (planned <= 0) return '0%'
  const pct = (rowActualQty(row) / planned) * 100
  return `${Math.round(Math.max(0, Math.min(999, pct)))}%`
}

function parseLocalDay(v: string | undefined): Date | null {
  if (v == null || v === '') return null
  const part = String(v).trim().slice(0, 10)
  const m = part.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
  if (!m) return null
  const y = parseInt(m[1], 10)
  const mo = parseInt(m[2], 10) - 1
  const d = parseInt(m[3], 10)
  const dt = new Date(y, mo, d)
  if (Number.isNaN(dt.getTime()) || dt.getFullYear() !== y || dt.getMonth() !== mo || dt.getDate() !== d) {
    return null
  }
  return dt
}

function todayLocalStart(): Date {
  const n = new Date()
  return new Date(n.getFullYear(), n.getMonth(), n.getDate())
}

/** 終了日＜当日→done；開始日≤当日≤終了日→ongoing（FormingPlanningList tableStatusKind と同じ根拠） */
function productionStatusKind(row: EnrichedRow): 'done' | 'ongoing' | 'pending' {
  const today = todayLocalStart()
  const span = effectiveScheduleDateSpan(row)
  const start = parseLocalDay(span.start || row.start_date || undefined)
  const end = parseLocalDay(span.end || row.end_date || undefined)
  if (end && end < today) return 'done'
  if (start && end && start <= today && today <= end) return 'ongoing'
  return 'pending'
}

function productionStatusLabel(row: EnrichedRow): string {
  const k = productionStatusKind(row)
  if (k === 'done') return t('productionPlanSchedule.statusDone')
  if (k === 'ongoing') return t('productionPlanSchedule.statusOngoing')
  return t('productionPlanSchedule.statusPending')
}

function printStatusCell(row: EnrichedRow): string {
  const k = productionStatusKind(row)
  const dotClass =
    k === 'done'
      ? 'print-status-dot print-status-dot--done'
      : k === 'ongoing'
        ? 'print-status-dot print-status-dot--ongoing'
        : 'print-status-dot print-status-dot--pending'
  return `<span class="${dotClass}"></span>${escHtml(productionStatusLabel(row))}`
}

function displayDate(v: string | undefined): string {
  if (v == null || v === '') return '—'
  const s = String(v)
  return s.length >= 10 ? s.slice(0, 10) : s
}

function escHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function printLocaleTag(): string {
  const loc = locale.value
  if (loc === 'zh' || loc.startsWith('zh')) return 'zh-CN'
  if (loc === 'ja' || loc.startsWith('ja')) return 'ja-JP'
  if (loc === 'vi' || loc.startsWith('vi')) return 'vi-VN'
  return 'en-US'
}

function buildPrintFilterSummary(): string {
  const monthStr = `${filterMonth.value}${t('productionPlanSchedule.monthSuffix')}`
  const eng = filterEngineering.value ? filterEngineering.value : t('productionPlanSchedule.all')
  const mach = filterMachineName.value ? filterMachineName.value : t('productionPlanSchedule.all')
  return `${t('productionPlanSchedule.monthCol')}：${escHtml(monthStr)}　${t('productionPlanSchedule.engineeringCol')}：${escHtml(eng)}　${t('productionPlanSchedule.machineName')}：${escHtml(mach)}`
}

function buildPrintHtml(): string {
  const sections = groupedSections.value
  const printDate = new Date().toLocaleString(printLocaleTag(), {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  const title = escHtml(t('menu.ERP_PRODUCTION_PLAN_SCHEDULES'))
  const colOrder = escHtml(t('productionPlanSchedule.productionOrder'))
  const colProduct = escHtml(t('productionPlanSchedule.productName'))
  const colPlan = escHtml(t('productionPlanSchedule.plannedQty'))
  const colStart = escHtml(t('productionPlanSchedule.startDate'))
  const colEnd = escHtml(t('productionPlanSchedule.endDate'))
  const colActual = escHtml(t('productionPlanSchedule.actual'))
  const colProgress = escHtml(t('productionPlanSchedule.progress'))
  const colStatus = escHtml(t('productionPlanSchedule.prodStatus'))
  const colRem = escHtml(t('productionPlanSchedule.remaining'))

  const blocks: string[] = []
  for (const sec of sections) {
    blocks.push(`<div class="print-section">`)
    const crit = sectionCriticalProgressLines(sec)
    let critHtml = ''
    if (crit.overPlan.length > 0) {
      critHtml += `　<span class="print-sec-crit print-sec-crit--over">${escHtml(t('productionPlanSchedule.productionProgress'))}（${escHtml(t('productionPlanSchedule.ovProgressOverPlan'))}）${escHtml(crit.overPlan.join('、'))}</span>`
    }
    if (crit.severeBehind.length > 0) {
      critHtml += `　<span class="print-sec-crit print-sec-crit--severe">${escHtml(t('productionPlanSchedule.productionProgress'))}（${escHtml(t('productionPlanSchedule.ovProgressSevereBehind'))}）${escHtml(crit.severeBehind.join('、'))}</span>`
    }
    blocks.push(
      `<div class="print-section-title">${escHtml(t('productionPlanSchedule.monthCol'))}：${escHtml(sec.monthLabel)}　${escHtml(t('productionPlanSchedule.engineeringCol'))}：${escHtml(sec.engineering)}${critHtml}</div>`,
    )
    for (const mc of sec.machines) {
      blocks.push('<div class="print-line-block">')
      const ov = machineOvHeadParts(sec, mc)
      const ovNeg = ov.negative ? 'print-ov-negative' : ''
      const ovPart = `${escHtml(t('productionPlanSchedule.operationVariance'))}：<span class="${ovNeg}">${escHtml(ov.display)}</span>`
      const ppPart = `${escHtml(t('productionPlanSchedule.productionProgress'))}：<span class="print-ov-flag print-ov-flag--${ov.kind}">${escHtml(ov.progressLabel)}</span>`
      blocks.push(
        `<div class="print-machine-title">${escHtml(t('productionPlanSchedule.machineName'))}：${escHtml(mc.machineName)}　${ovPart}　${ppPart}</div>`,
      )
      const rowHtml = mc.rows
        .map(
          (row) => `<tr>
          <td>${escHtml(String(row.order_no ?? ''))}</td>
          <td class="text-left">${escHtml(String(row.item_name ?? ''))}</td>
          <td>${escHtml(displayDate(scheduleStartIso(row)))}</td>
          <td>${escHtml(displayDate(scheduleEndIso(row)))}</td>
          <td class="num">${escHtml(formatNum(row.planned_process_qty))}</td>
          <td class="num">${escHtml(formatNum(rowActualQty(row)))}</td>
          <td class="num">${escHtml(formatRemainder(row))}</td>
          <td class="num">${escHtml(formatProgress(row))}</td>
          <td class="status-print-cell">${printStatusCell(row)}</td>
        </tr>`,
        )
        .join('')
      blocks.push(`<table class="print-table">
        <colgroup>
          <col style="width:7.5%" /><col style="width:19%" />
          <col style="width:9.5%" /><col style="width:9.5%" /><col style="width:8.5%" />
          <col style="width:8%" /><col style="width:8%" /><col style="width:8.5%" /><col style="width:11.5%" />
        </colgroup>
        <thead><tr>
          <th>${colOrder}</th><th>${colProduct}</th><th>${colStart}</th><th>${colEnd}</th><th>${colPlan}</th><th>${colActual}</th><th>${colRem}</th><th>${colProgress}</th><th>${colStatus}</th>
        </tr></thead>
        <tbody>${rowHtml}</tbody>
      </table>`)
      blocks.push('</div>')
    }
    blocks.push(`</div>`)
  }

  const rowCount = displayRows.value.length
  const metaFilter = buildPrintFilterSummary()

  return `
    <div class="print-header">
      <div class="print-title">${title}</div>
      <div class="print-meta">
        <div class="print-meta-line">${escHtml(t('productionPlanSchedule.printMetaTime'))}：${escHtml(printDate)}　｜　${escHtml(t('productionPlanSchedule.printMetaRows'))}：${rowCount}</div>
        <div class="print-meta-line">${escHtml(t('productionPlanSchedule.printMetaFilter'))}：${metaFilter}</div>
      </div>
    </div>
    ${blocks.join('')}
  `
}

function handlePrint() {
  if (displayRows.value.length === 0) {
    ElMessage.warning(t('productionPlanSchedule.empty'))
    return
  }
  const html = buildPrintHtml()
  const docTitle = t('productionPlanSchedule.printDocTitle')
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error(t('productionPlanSchedule.printPopupBlocked'))
    return
  }
  printWindow.document.write(`<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(docTitle)}</title>
  <style>${PRINT_DOCUMENT_STYLES}</style>
</head>
<body>${html}</body>
</html>`)
  printWindow.document.close()
  printWindow.onload = () => {
    printWindow.print()
    setTimeout(() => printWindow.close(), 400)
  }
}

const monthChoices = Array.from({ length: 12 }, (_, i) => i + 1)

const loading = ref(false)
/** APS scheduling/grid 一覧と同じ取得結果（工程・設備・順位付き） */
const rawGridRows = ref<ApsGridListRow[]>([])
/** FormingPlanningList の tableGanttDates：日次実績・残の集計に使用 */
const tableGanttDates = ref<string[]>([])
const filterMonth = ref(new Date().getMonth() + 1)
const filterEngineering = ref('')
const filterMachineName = ref('')

const enrichedRows = computed<EnrichedRow[]>(() => {
  const suffix = t('productionPlanSchedule.monthSuffix')
  const m = filterMonth.value
  return rawGridRows.value
    .filter((r) => rowOverlapsSelectedCalendarMonth(r))
    .map((r) => ({
      ...r,
      monthLabel: `${m}${suffix}`,
      parsedMonth: m,
    }))
})

const afterMonthAndEngineering = computed(() => {
  return enrichedRows.value.filter((r) => {
    if (filterEngineering.value && r.engineering !== filterEngineering.value) return false
    return true
  })
})

const machineOptions = computed(() => {
  const set = new Set<string>()
  afterMonthAndEngineering.value.forEach((r) => {
    const n = (r.lineLabel ?? '').toString().trim()
    if (n) set.add(n)
  })
  return [...set].sort((a, b) => a.localeCompare(b, 'ja'))
})

watch([afterMonthAndEngineering, filterMachineName], () => {
  const names = new Set(machineOptions.value)
  if (filterMachineName.value && !names.has(filterMachineName.value)) {
    filterMachineName.value = ''
  }
})

const displayRows = computed(() => {
  let list = afterMonthAndEngineering.value
  if (filterMachineName.value) {
    list = list.filter((r) => (r.lineLabel ?? '').toString().trim() === filterMachineName.value)
  }
  return [...list].sort((a, b) => {
    const ma = String(a.lineLabel ?? '')
    const mb = String(b.lineLabel ?? '')
    const c = ma.localeCompare(mb, 'ja')
    if (c !== 0) return c
    const oa = a.order_no ?? 1_000_000 + a.id
    const ob = b.order_no ?? 1_000_000 + b.id
    if (oa !== ob) return Number(oa) - Number(ob)
    return a.id - b.id
  })
})

const groupedSections = computed<GroupedSection[]>(() => {
  const rows = displayRows.value
  const sections = new Map<
    string,
    {
      monthLabel: string
      engineering: string
      machineMap: Map<string, EnrichedRow[]>
    }
  >()
  for (const row of rows) {
    const monthLabel = row.monthLabel
    const engineering = row.engineering || '—'
    const key = `${monthLabel}\0${engineering}`
    if (!sections.has(key)) {
      sections.set(key, { monthLabel, engineering, machineMap: new Map() })
    }
    const sec = sections.get(key)!
    const mn = (row.lineLabel ?? '').toString().trim() || '—'
    if (!sec.machineMap.has(mn)) sec.machineMap.set(mn, [])
    sec.machineMap.get(mn)!.push(row)
  }
  const sortedKeys = [...sections.keys()].sort((ka, kb) => {
    const A = sections.get(ka)!
    const B = sections.get(kb)!
    const mc = A.monthLabel.localeCompare(B.monthLabel, 'ja')
    if (mc !== 0) return mc
    const ek =
      engineeringSortKey(A.engineering === '—' ? '' : A.engineering) -
      engineeringSortKey(B.engineering === '—' ? '' : B.engineering)
    if (ek !== 0) return ek
    return A.engineering.localeCompare(B.engineering, 'ja')
  })
  const out: GroupedSection[] = []
  for (const k of sortedKeys) {
    const { monthLabel, engineering, machineMap } = sections.get(k)!
    const machines: MachineGroup[] = [...machineMap.entries()]
      .sort((a, b) => a[0].localeCompare(b[0], 'ja'))
      .map(([machineName, rlist]) => ({
        machineName,
        rows: [...rlist].sort((a, b) => {
          const oa = a.order_no ?? 1_000_000 + a.id
          const ob = b.order_no ?? 1_000_000 + b.id
          if (oa !== ob) return Number(oa) - Number(ob)
          return a.id - b.id
        }),
      }))
    out.push({ monthLabel, engineering, machines })
  }
  return out
})

/** production_plan_rate：当月・工程(成型|溶接)・ライン machine_name → operation_variance */
const planOperationVarianceMap = ref<Map<string, string>>(new Map())

function planOperationVarianceKey(engineering: string, machineName: string): string {
  return `${String(engineering ?? '').trim()}\0${String(machineName ?? '').trim()}`
}

async function loadPlanOperationVarianceMap(): Promise<void> {
  const m = filterMonth.value
  if (m < 1 || m > 12) {
    planOperationVarianceMap.value = new Map()
    return
  }
  try {
    const items = await fetchPlanOperationRate({ monthNum: m })
    const map = new Map<string, string>()
    for (const it of items) {
      const proc = (it.display_process ?? '').toString().trim()
      const mn = (it.machine_name ?? '').toString().trim()
      if (!proc || !mn) continue
      const ov = (it.operation_variance ?? '').toString().trim()
      map.set(planOperationVarianceKey(proc, mn), ov || '—')
    }
    planOperationVarianceMap.value = map
  } catch (e) {
    console.error(e)
    planOperationVarianceMap.value = new Map()
  }
}

function rawOperationVarianceFromMap(sec: GroupedSection, mc: MachineGroup): string | undefined {
  const eng = (sec.engineering ?? '').trim()
  const mn = (mc.machineName ?? '').trim()
  if (!eng || eng === '—' || !mn || mn === '—') return undefined
  return planOperationVarianceMap.value.get(planOperationVarianceKey(eng, mn))
}

function operationVarianceForMachine(sec: GroupedSection, mc: MachineGroup): string {
  const v = rawOperationVarianceFromMap(sec, mc)
  return v !== undefined && v !== '' ? v : '—'
}

function parseOperationVarianceToNumber(raw: string | undefined | null): number | null {
  if (raw === undefined || raw === null) return null
  const s = String(raw).trim()
  if (!s || s === '—' || s === '-') return null
  const n = Number(s.replace(/,/g, '').replace(/%/g, '').trim())
  return Number.isFinite(n) ? n : null
}

function operationVarianceNumericForMachine(sec: GroupedSection, mc: MachineGroup): number | null {
  const raw = rawOperationVarianceFromMap(sec, mc)
  if (raw === undefined || raw === '' || raw === '—') return null
  return parseOperationVarianceToNumber(raw)
}

/** 生産進捗：阈值与显示文案（与操業度差異数值联动） */
type OperationVarianceProgressKind =
  | 'none'
  | 'normal'
  | 'ahead'
  | 'behind'
  | 'over_plan'
  | 'severe_behind'

function operationVarianceProgressKind(n: number | null): OperationVarianceProgressKind {
  if (n === null) return 'none'
  if (n > 10) return 'over_plan'
  if (n < -10) return 'severe_behind'
  if (n > 2) return 'ahead'
  if (n < -2) return 'behind'
  return 'normal'
}

function operationVarianceProgressLabel(kind: OperationVarianceProgressKind): string {
  switch (kind) {
    case 'normal':
      return t('productionPlanSchedule.ovProgressNormal')
    case 'ahead':
      return t('productionPlanSchedule.ovProgressAhead')
    case 'behind':
      return t('productionPlanSchedule.ovProgressBehind')
    case 'over_plan':
      return t('productionPlanSchedule.ovProgressOverPlan')
    case 'severe_behind':
      return t('productionPlanSchedule.ovProgressSevereBehind')
    default:
      return '—'
  }
}

function operationVarianceProgressTagType(
  kind: OperationVarianceProgressKind,
): 'success' | 'primary' | 'warning' | 'danger' | 'info' {
  switch (kind) {
    case 'normal':
      return 'success'
    case 'ahead':
      return 'primary'
    case 'behind':
      return 'warning'
    case 'over_plan':
    case 'severe_behind':
      return 'danger'
    default:
      return 'info'
  }
}

function operationVarianceProgressTagEffect(
  kind: OperationVarianceProgressKind,
): 'light' | 'dark' | 'plain' {
  if (kind === 'severe_behind') return 'dark'
  return 'light'
}

interface MachineOvHeadParts {
  display: string
  num: number | null
  kind: OperationVarianceProgressKind
  negative: boolean
  progressLabel: string
  tagType: 'success' | 'primary' | 'warning' | 'danger' | 'info'
  tagEffect: 'light' | 'dark' | 'plain'
}

function machineOvHeadParts(sec: GroupedSection, mc: MachineGroup): MachineOvHeadParts {
  const display = operationVarianceForMachine(sec, mc)
  const num = operationVarianceNumericForMachine(sec, mc)
  const kind = operationVarianceProgressKind(num)
  return {
    display,
    num,
    kind,
    negative: num !== null && num < 0,
    progressLabel: operationVarianceProgressLabel(kind),
    tagType: operationVarianceProgressTagType(kind),
    tagEffect: operationVarianceProgressTagEffect(kind),
  }
}

/** 该工程区块内 生産進捗 为 計画超過／大幅な遅れ のライン（表格已排序，按 machines 顺序） */
function sectionCriticalProgressLines(sec: GroupedSection): {
  overPlan: string[]
  severeBehind: string[]
} {
  const overPlan: string[] = []
  const severeBehind: string[] = []
  for (const mc of sec.machines) {
    const ov = machineOvHeadParts(sec, mc)
    if (ov.kind === 'over_plan') overPlan.push(mc.machineName)
    else if (ov.kind === 'severe_behind') severeBehind.push(mc.machineName)
  }
  return { overPlan, severeBehind }
}

const planUpdatesVisible = ref(false)
const planUpdatesLoading = ref(false)
const planUpdatesRows = ref<PlanUpdateRecord[]>([])
const planUpdatesDialogTitle = ref('')

/** 日生産スケジュール：工程 → ライン → 生産準 → 生産日 の順に並べ、表示時に前三列をマージ */
function sortPlanUpdatesForGroup(rows: PlanUpdateRecord[]): PlanUpdateRecord[] {
  return [...rows].sort((a, b) => {
    const pa = String(a.process_name ?? '')
    const pb = String(b.process_name ?? '')
    const pk = engineeringSortKey(pa)
    const qk = engineeringSortKey(pb)
    if (pk !== qk) return pk - qk
    if (pa !== pb) return pa.localeCompare(pb, 'ja')
    const ma = String(a.machine_name ?? '')
    const mb = String(b.machine_name ?? '')
    if (ma !== mb) return ma.localeCompare(mb, 'ja')
    const oa = String(a.operator ?? '')
    const ob = String(b.operator ?? '')
    if (oa !== ob) return oa.localeCompare(ob, 'ja')
    return String(a.plan_date ?? '').localeCompare(String(b.plan_date ?? ''))
  })
}

function planUpdateCellKey(x: unknown): string {
  return String(x ?? '')
}

function buildPlanUpdatesMergeSpans(rows: PlanUpdateRecord[]) {
  const n = rows.length
  const process = new Array<number>(n).fill(0)
  const machine = new Array<number>(n).fill(0)
  const operator = new Array<number>(n).fill(0)

  for (let i = 0; i < n; ) {
    const p = planUpdateCellKey(rows[i].process_name)
    let j = i + 1
    while (j < n && planUpdateCellKey(rows[j].process_name) === p) j++
    process[i] = j - i
    for (let k = i + 1; k < j; k++) process[k] = 0
    i = j
  }
  for (let i = 0; i < n; ) {
    const p = planUpdateCellKey(rows[i].process_name)
    const m = planUpdateCellKey(rows[i].machine_name)
    let j = i + 1
    while (
      j < n &&
      planUpdateCellKey(rows[j].process_name) === p &&
      planUpdateCellKey(rows[j].machine_name) === m
    )
      j++
    machine[i] = j - i
    for (let k = i + 1; k < j; k++) machine[k] = 0
    i = j
  }
  for (let i = 0; i < n; ) {
    const p = planUpdateCellKey(rows[i].process_name)
    const m = planUpdateCellKey(rows[i].machine_name)
    const o = planUpdateCellKey(rows[i].operator)
    let j = i + 1
    while (
      j < n &&
      planUpdateCellKey(rows[j].process_name) === p &&
      planUpdateCellKey(rows[j].machine_name) === m &&
      planUpdateCellKey(rows[j].operator) === o
    )
      j++
    operator[i] = j - i
    for (let k = i + 1; k < j; k++) operator[k] = 0
    i = j
  }
  return { process, machine, operator }
}

const planUpdatesDisplayRows = computed(() => sortPlanUpdatesForGroup(planUpdatesRows.value))

const planUpdatesMergeSpans = computed(() => buildPlanUpdatesMergeSpans(planUpdatesDisplayRows.value))

function planUpdatesSpanMethod({
  rowIndex,
  columnIndex,
}: {
  rowIndex: number
  columnIndex: number
}): [number, number] {
  const { process, machine, operator } = planUpdatesMergeSpans.value
  if (columnIndex === 0) {
    const rs = process[rowIndex] ?? 0
    return rs > 0 ? [rs, 1] : [0, 0]
  }
  if (columnIndex === 1) {
    const rs = machine[rowIndex] ?? 0
    return rs > 0 ? [rs, 1] : [0, 0]
  }
  if (columnIndex === 2) {
    const rs = operator[rowIndex] ?? 0
    return rs > 0 ? [rs, 1] : [0, 0]
  }
  return [1, 1]
}

function filterMonthToDateRange(): { startDate: string; endDate: string } {
  const y = new Date().getFullYear()
  const m = filterMonth.value
  const mm = String(m).padStart(2, '0')
  const lastDay = new Date(y, m, 0).getDate()
  const dd = String(lastDay).padStart(2, '0')
  return {
    startDate: `${y}-${mm}-01`,
    endDate: `${y}-${mm}-${dd}`,
  }
}

function formatPlanQty(x: unknown): string {
  return formatNum(x)
}

function formatOptionalNum(x: unknown): string {
  const n = toFiniteNumber(x)
  if (n === null) return '—'
  return String(n)
}

/** 所要時間：計画数 / 能率、小数 1 位；能率为 0 或无效时为 — */
function formatRequiredTime(qty: unknown, efficiencyRate: unknown): string {
  const q = toFiniteNumber(qty)
  const e = toFiniteNumber(efficiencyRate)
  if (q === null || e === null || e === 0) return '—'
  const v = q / e
  if (!Number.isFinite(v)) return '—'
  return v.toFixed(1)
}

async function openPlanUpdatesDialog(row: EnrichedRow) {
  const name = (row.item_name ?? '').trim()
  if (!name) {
    ElMessage.warning(t('productionPlanSchedule.planUpdatesNoProduct'))
    return
  }
  /** スケジュール行の工程（加工→成型／溶接）に合わせ production_plan_updates.process_name を絞込 */
  const processName =
    row.engineering === '成型' || row.engineering === '溶接' ? row.engineering : undefined
  const y = new Date().getFullYear()
  const m = filterMonth.value
  let dlgTitle = t('productionPlanSchedule.planUpdatesTitle', {
    product: name,
    year: y,
    month: m,
  })
  if (processName) {
    dlgTitle += t('productionPlanSchedule.planUpdatesTitleProcess', { process: processName })
  }
  planUpdatesDialogTitle.value = dlgTitle
  planUpdatesVisible.value = true
  planUpdatesLoading.value = true
  planUpdatesRows.value = []
  try {
    const { startDate, endDate } = filterMonthToDateRange()
    const result = (await request.get('/api/excel-monitor/plan-data', {
      params: {
        startDate,
        endDate,
        productNameExact: name,
        ...(processName ? { processName } : {}),
        limit: 10000,
        page: 1,
      },
    })) as ApiResponse<{ records: PlanUpdateRecord[]; total?: number }>
    const pack = result.data
    planUpdatesRows.value =
      pack && typeof pack === 'object' && Array.isArray(pack.records) ? pack.records : []
  } catch (e) {
    console.error(e)
    ElMessage.error(t('productionPlanSchedule.planUpdatesLoadFailed'))
    planUpdatesRows.value = []
  } finally {
    planUpdatesLoading.value = false
  }
}

async function fetchData() {
  loading.value = true
  try {
    await loadPlanOperationVarianceMap()
    const [wideStart, wideEnd] = buildTableGridRange()
    const jobs: { cd: string; engineering: string }[] = []
    const fe = filterEngineering.value
    if (!fe || fe === '成型') jobs.push({ cd: PROCESS_CD_FORMING, engineering: '成型' })
    if (!fe || fe === '溶接') jobs.push({ cd: PROCESS_CD_WELDING, engineering: '溶接' })
    if (jobs.length === 0) {
      rawGridRows.value = []
      tableGanttDates.value = []
      return
    }
    const merged: ApsGridListRow[] = []
    const datesAcc = new Set<string>()
    for (const { cd, engineering } of jobs) {
      const [grid, lines] = await Promise.all([
        fetchSchedulingGrid(wideStart, wideEnd, undefined, cd),
        fetchLines(cd),
      ])
      for (const d of grid.dates || []) datesAcc.add(d)
      const lineNameById = new Map<number, string>()
      for (const line of lines || []) {
        const name = String(line.line_name || '').trim()
        const code = String(line.line_code || '').trim()
        lineNameById.set(line.id, name || code || `ID ${line.id}`)
      }
      merged.push(...flattenGridToRows(grid, lineNameById, engineering))
    }
    merged.sort(compareRowsMerged)
    tableGanttDates.value = [...datesAcc].sort((a, b) => a.localeCompare(b))
    rawGridRows.value = merged
  } catch (e) {
    console.error(e)
    ElMessage.error(t('productionPlanSchedule.loadFailed'))
    rawGridRows.value = []
    tableGanttDates.value = []
  } finally {
    loading.value = false
  }
}

function onMonthChange() {
  void loadPlanOperationVarianceMap()
}

onMounted(fetchData)
</script>

<style scoped>
@keyframes psv-fade-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes psv-dot-glow {
  0%,
  100% {
    box-shadow:
      0 0 0 1px rgba(0, 0, 0, 0.08) inset,
      0 0 0 0 rgba(103, 194, 58, 0.45);
  }
  50% {
    box-shadow:
      0 0 0 1px rgba(0, 0, 0, 0.08) inset,
      0 0 0 7px rgba(103, 194, 58, 0);
  }
}
.plan-schedule-view {
  padding: 18px 22px 28px;
  box-sizing: border-box;
  min-height: calc(100vh - 120px);
  background:
    radial-gradient(900px 420px at 12% -8%, color-mix(in srgb, var(--el-color-primary) 9%, transparent), transparent 55%),
    radial-gradient(700px 380px at 96% 0%, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), transparent 50%),
    linear-gradient(165deg, var(--el-fill-color-extra-light) 0%, var(--el-bg-color) 38%, var(--el-fill-color-blank) 100%);
}
.psv-surface {
  border-radius: 14px;
  border: 1px solid var(--el-border-color-lighter);
  background: color-mix(in srgb, var(--el-bg-color) 92%, var(--el-fill-color-blank));
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.6) inset,
    0 14px 36px -18px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(10px);
  transition:
    box-shadow 0.35s ease,
    border-color 0.35s ease;
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 14px;
  padding: 16px 18px;
}
.psv-surface--toolbar {
  padding: 12px 16px 4px;
  margin-bottom: 14px;
}
.psv-surface--main {
  padding: 10px 14px 18px;
}
.header-left {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 16px 26px;
}
.psv-title {
  margin: 0;
  font-size: 1.28rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  line-height: 1.3;
  color: var(--el-text-color-primary);
}
@supports (-webkit-background-clip: text) or (background-clip: text) {
  .psv-title {
    background: linear-gradient(110deg, var(--el-text-color-primary) 0%, var(--el-color-primary) 160%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
  html.dark .psv-title {
    background: linear-gradient(110deg, var(--el-text-color-primary) 20%, var(--el-color-primary-light-3) 120%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
}
.product-name-cell {
  cursor: pointer;
  color: var(--el-color-primary);
  font-weight: 500;
  padding: 2px 0;
  border-radius: 4px;
  transition:
    color 0.22s ease,
    background-color 0.22s ease,
    box-shadow 0.22s ease;
  box-shadow: 0 1px 0 color-mix(in srgb, var(--el-color-primary) 35%, transparent);
}
.product-name-cell:hover {
  color: var(--el-color-primary-dark-2);
  background: color-mix(in srgb, var(--el-color-primary) 7%, transparent);
  box-shadow: none;
}
.header-stats {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.psv-stat {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}
.psv-stat:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px -8px rgba(15, 23, 42, 0.2);
}
.psv-stat__k {
  color: var(--el-text-color-secondary);
  font-weight: 600;
}
.psv-stat__v {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-primary);
}
.psv-stat--total .psv-stat__v {
  color: var(--el-color-info);
}
.psv-stat--shown .psv-stat__v {
  color: var(--el-color-success);
}
.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.header-actions .header-btn {
  min-width: 108px;
  border-radius: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 10px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}
.header-actions .header-btn:not(:disabled):hover {
  transform: translateY(-1px);
}
.header-actions .header-btn:not(:disabled):active {
  transform: translateY(0);
}
.header-actions :deep(.header-btn--query.el-button--primary) {
  background: linear-gradient(160deg, var(--el-color-primary-light-3), var(--el-color-primary));
  border-color: var(--el-color-primary-dark-2);
}
.header-actions :deep(.header-btn--query.el-button--primary:not(:disabled):hover) {
  background: linear-gradient(160deg, var(--el-color-primary), var(--el-color-primary-dark-2));
  border-color: var(--el-color-primary-dark-2);
  box-shadow: 0 6px 18px rgba(64, 158, 255, 0.38);
}
.header-actions :deep(.header-btn--print.el-button--warning) {
  background: linear-gradient(160deg, var(--el-color-warning-light-5), var(--el-color-warning));
  border-color: var(--el-color-warning-dark-2);
  color: #fff;
}
.header-actions :deep(.header-btn--print.el-button--warning:not(:disabled):hover) {
  background: linear-gradient(160deg, var(--el-color-warning-light-3), var(--el-color-warning-dark-2));
  border-color: var(--el-color-warning-dark-2);
  color: #fff;
  box-shadow: 0 6px 18px rgba(230, 162, 60, 0.45);
}
.header-actions :deep(.header-btn--print.is-disabled) {
  opacity: 0.55;
  background: var(--el-fill-color-dark);
  border-color: var(--el-border-color);
  color: var(--el-text-color-placeholder);
  box-shadow: none;
}
.filter-bar {
  margin-bottom: 0;
}
.filter-form {
  flex-wrap: wrap;
}
.filter-form :deep(.el-form-item) {
  margin-bottom: 10px;
}
.filter-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--el-text-color-regular);
}
.table-card {
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  border: none;
}
.grouped-card {
  padding: 0;
}
.grouped-scroll {
  max-height: calc(100vh - 240px);
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--el-text-color-secondary) 35%, transparent) transparent;
}
.grouped-scroll::-webkit-scrollbar {
  width: 7px;
}
.grouped-scroll::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--el-text-color-secondary) 38%, transparent);
  border-radius: 99px;
}
.empty-hint {
  padding: 56px 0;
}
.section-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
  margin: 14px 0 12px;
  padding: 11px 16px;
  font-weight: 600;
  background: linear-gradient(
    115deg,
    color-mix(in srgb, var(--el-color-primary) 7%, var(--el-fill-color-blank)) 0%,
    var(--el-fill-color-light) 48%,
    var(--el-fill-color-blank) 100%
  );
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 12%, var(--el-border-color-lighter));
  box-shadow: 0 8px 22px -16px color-mix(in srgb, var(--el-color-primary) 35%, transparent);
}
.section-head--enter {
  animation: psv-fade-up 0.48s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--psv-enter-delay, 0ms);
}
.section-head:first-child {
  margin-top: 4px;
}
.section-label {
  font-size: 14px;
  letter-spacing: 0.02em;
}
.section-gap {
  flex: 0 0 8px;
}
.section-gap--wide {
  flex: 0 0 12px;
}
.section-head-progress-alerts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 18px;
  flex: 1;
  min-width: 0;
  font-weight: 600;
}
.section-head-alert {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  font-size: 13px;
}
.section-head-alert-label {
  color: var(--el-text-color-secondary);
  font-weight: 600;
}
.section-head-alert-lines {
  color: var(--el-color-danger-dark-2);
  font-weight: 700;
}
.section-head-alert-tag {
  font-weight: 700;
  border-radius: 6px;
}
.machine-block {
  margin-left: 14px;
  margin-bottom: 18px;
}
.machine-block--enter {
  animation: psv-fade-up 0.44s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--psv-m-delay, 0ms);
}
.machine-head {
  margin: 12px 0 10px;
  padding: 8px 12px 8px 14px;
  font-weight: 500;
  font-size: 13px;
  border-left: 3px solid var(--el-color-primary);
  background: linear-gradient(100deg, var(--el-fill-color-blank) 0%, transparent 100%);
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 18px;
  border-radius: 0 10px 10px 0;
  transition:
    background 0.3s ease,
    box-shadow 0.3s ease;
}
.machine-head--sheet:hover {
  background: linear-gradient(100deg, color-mix(in srgb, var(--el-color-primary) 5%, var(--el-fill-color-blank)) 0%, transparent 100%);
  box-shadow: 0 10px 24px -20px rgba(15, 23, 42, 0.2);
}
.machine-head-ov {
  color: var(--el-text-color-regular);
  font-weight: 600;
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 14px;
}
.machine-head-ov-value--negative {
  color: var(--el-color-danger);
  font-weight: 700;
}
.machine-head-pp-wrap {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.machine-head-pp-tag {
  font-weight: 700;
  border-radius: 6px;
}
.nest-table {
  margin-left: 18px;
  width: calc(100% - 18px);
}
.nest-table--polish {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 32px -24px rgba(15, 23, 42, 0.25);
  --el-table-border-color: color-mix(in srgb, var(--el-border-color) 88%, var(--el-color-primary));
}
.nest-table--polish :deep(.el-table__inner-wrapper::before) {
  display: none;
}
.nest-table--polish :deep(.el-table__header-wrapper th.el-table__cell) {
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.04em;
  color: var(--el-text-color-primary);
  background: linear-gradient(180deg, var(--el-fill-color-lighter) 0%, var(--el-fill-color-blank) 100%) !important;
  border-bottom: 1px solid var(--el-border-color-lighter) !important;
}
.nest-table--polish :deep(.el-table__body tr) {
  transition: background-color 0.18s ease;
}
.nest-table--polish :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: color-mix(in srgb, var(--el-color-primary) 4%, var(--el-fill-color-blank)) !important;
}
.status-lamp-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: nowrap;
}
.status-lamp-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.1) inset,
    0 1px 2px rgba(0, 0, 0, 0.06);
}
.status-lamp-dot--done {
  background: var(--el-text-color-placeholder);
}
.status-lamp-dot--ongoing {
  background: var(--el-color-success);
  animation: psv-dot-glow 2.4s ease-in-out infinite;
}
.status-lamp-dot--pending {
  background: var(--el-color-warning);
}
.status-lamp-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}
@media (prefers-reduced-motion: reduce) {
  .section-head--enter,
  .machine-block--enter {
    animation: none !important;
  }
  .status-lamp-dot--ongoing {
    animation: none !important;
  }
  .product-name-cell,
  .psv-stat,
  .header-actions .header-btn {
    transition: none !important;
  }
}
@supports not (color: color-mix(in srgb, red, blue)) {
  .plan-schedule-view {
    background: var(--el-bg-color);
  }
  .section-head {
    background: var(--el-fill-color-light);
    border-color: var(--el-border-color-lighter);
    box-shadow: 0 8px 20px -16px rgba(0, 0, 0, 0.12);
  }
  .nest-table--polish {
    --el-table-border-color: var(--el-border-color);
  }
  .status-lamp-dot--ongoing {
    animation: none;
  }
}
</style>

<style>
/* 日生産スケジュール弹窗（append-to-body，需非 scoped） */
@keyframes psv-dialog-in {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
.daily-schedule-dialog.el-dialog {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 24px 48px -12px rgba(15, 23, 42, 0.28);
  padding: 0;
  animation: psv-dialog-in 0.38s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@media (prefers-reduced-motion: reduce) {
  .daily-schedule-dialog.el-dialog {
    animation: none;
  }
}
.daily-schedule-dialog .el-dialog__header {
  padding: 14px 20px;
  margin: 0;
  background: linear-gradient(125deg, #1e40af 0%, #2563eb 45%, #3b82f6 100%);
  border-bottom: none;
}
.daily-schedule-dialog .el-dialog__title {
  color: #fff !important;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 1.4;
}
.daily-schedule-dialog .el-dialog__headerbtn {
  top: 0;
}
.daily-schedule-dialog .el-dialog__headerbtn .el-dialog__close {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 18px;
}
.daily-schedule-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: #fff !important;
}
.daily-schedule-dialog .el-dialog__body {
  padding: 0;
  background: linear-gradient(180deg, #e2e8f0 0%, #f1f5f9 40%, #f8fafc 100%);
}
.daily-schedule-dialog__body {
  padding: 16px 18px 18px;
  min-height: 132px;
}
.daily-schedule-table {
  --el-table-border-color: #cbd5e1;
  --el-table-header-bg-color: #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}
.daily-schedule-table.el-table .el-table__header th {
  color: #1e3a8a;
  font-weight: 700;
}
.daily-schedule-table.el-table .el-table__body td {
  vertical-align: middle;
}
.daily-schedule-table.el-table--striped .el-table__body tr.el-table__row--striped td {
  background: #f8fafc;
}
.daily-schedule-empty {
  padding: 32px 16px;
}
.daily-schedule-empty .el-empty__description {
  color: #64748b;
  font-size: 14px;
}
</style>
