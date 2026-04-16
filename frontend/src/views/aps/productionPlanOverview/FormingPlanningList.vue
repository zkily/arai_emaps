<template>
  <div class="forming-plan-list-page">
    <div class="plan-hd">
      <h2 class="plan-hd-title">
        <span class="plan-hd-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path
              d="M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1a3 3 0 0 1 3 3v3H2V7a3 3 0 0 1 3-3h1V3a1 1 0 0 1 1-1ZM2 12h20v5a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3v-5Zm6 3a1 1 0 0 0 0 2h2a1 1 0 0 0 0-2H8Zm5 0a1 1 0 1 0 0 2h3a1 1 0 1 0 0-2h-3Z"
            />
          </svg>
        </span>
        成型計画一覧
      </h2>
      <p class="plan-hd-sub">
        工程・期間を指定し、対象期間に重なる APS 製造指示を<strong>日別ガント</strong>で表示します（計画／実績／残）。
      </p>
    </div>

    <div class="plan-card filter-card">
      <el-form :inline="true" label-position="left" class="filter-form">
        <el-form-item label="期間" required>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            unlink-panels
            range-separator="~"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item label="工程" required>
          <el-select
            v-model="selectedProcessCd"
            filterable
            clearable
            placeholder="工程を選択"
            style="width: 200px"
            :loading="loadingProcesses"
          >
            <el-option
              v-for="p in processOptions"
              :key="p.process_cd"
              :value="p.process_cd"
              :label="`${p.process_cd} — ${p.process_name}`"
            />
          </el-select>
        </el-form-item>
        <el-form-item label-width="0">
          <el-button type="primary" :loading="loading" :disabled="!canSearch" @click="onSearchClick">
            検索
          </el-button>
        </el-form-item>
      </el-form>
      <div v-if="canSearch" class="forming-replan-toolbar">
        <el-button
          type="warning"
          size="small"
          class="forming-replan-toolbar__primary"
          :loading="bulkReplanning"
          :disabled="loading || bulkReplanning"
          @click="replanAllLinesForProcess"
        >
          全設備ライン順で再計算
        </el-button>
        <el-button
          size="small"
          :disabled="!preReplanGridSnapshot || loading || bulkReplanning"
          @click="restorePreReplanGrid"
        >
          再計算前の表示に戻す
        </el-button>
        <span v-if="preReplanGridSnapshot" class="forming-replan-toolbar__note">
          画面上の一覧のみ再計算直前の取得結果に戻します（DB は既に更新済み）。最新データは「検索」で再取得してください。
        </span>
      </div>
    </div>

    <div v-if="searched" v-loading="loading" class="plan-card result-card">
      <el-tabs v-model="activeResultTab" class="result-tabs">
        <el-tab-pane label="ガント（日別）" name="gantt">
          <div class="gantt-legend-bar">
            <span class="legend-item"><span class="legend-dot legend-dot--plan" />計画</span>
            <span class="legend-item"><span class="legend-dot legend-dot--actual" />実績</span>
            <span class="legend-item"><span class="legend-dot legend-dot--remain" />残</span>
            <el-button
              size="small"
              class="gantt-print-btn"
              :icon="Printer"
              :disabled="loading || ganttRows.length === 0"
              @click="handleGanttPrint"
            >
              印刷
            </el-button>
            <span class="gantt-range-note">表示期間：{{ displayRangeText }}</span>
          </div>

          <el-empty
            v-if="!loading && ganttRows.length === 0"
            description="条件に一致する計画がありません"
          />

          <div v-else class="gantt-scroll list-gantt-scroll">
            <table class="gantt-table list-gantt-table">
              <thead>
                <tr>
                  <th class="gantt-sticky gantt-sticky-line">設備</th>
                  <th class="gantt-sticky gantt-sticky-order">順位</th>
                  <th class="gantt-sticky gantt-sticky-name">品名</th>
                  <th class="gantt-sticky gantt-sticky-eff">能率</th>
                  <th class="gantt-sticky gantt-sticky-planned">計画数</th>
                  <th class="gantt-sticky gantt-sticky-actual">実績数</th>
                  <th
                    v-for="d in ganttDates"
                    :key="d"
                    class="gantt-date-col"
                    :class="{ 'is-weekend': isWeekend(d), 'is-today': isToday(d) }"
                  >
                    <div class="gantt-date-text">{{ d.slice(5) }}</div>
                    <div class="gantt-wd-text">{{ getWeekday(d) }}</div>
                  </th>
                </tr>
              </thead>
              <tbody v-for="group in ganttGroups" :key="group.lineLabel">
                <tr class="gantt-group-row">
                  <td
                    class="gantt-sticky gantt-sticky-line gantt-group-cell gantt-group-line"
                    :title="group.lineLabel"
                  >
                    {{ group.lineLabel }}
                  </td>
                  <td class="gantt-sticky gantt-sticky-order gantt-group-cell" />
                  <td class="gantt-sticky gantt-sticky-name gantt-group-cell" />
                  <td class="gantt-sticky gantt-sticky-eff gantt-group-cell gantt-group-num">
                    {{ formatGroupEfficiency(group.avgEfficiencyRate) }}
                  </td>
                  <td class="gantt-sticky gantt-sticky-planned gantt-group-cell gantt-group-num">
                    {{ formatNum(group.plannedTotal) }}
                  </td>
                  <td class="gantt-sticky gantt-sticky-actual gantt-group-cell gantt-group-num">
                    {{ formatNum(group.actualTotal) }}
                  </td>
                  <td
                    v-for="d in ganttDates"
                    :key="`grp-${group.lineLabel}-${d}`"
                    class="gantt-cell gantt-group-date-cell"
                  />
                </tr>
                <tr
                  v-for="(row, gIdx) in group.rows"
                  :key="row.id"
                  :class="['gantt-row', gIdx % 2 === 1 ? 'gantt-row--alt' : 'gantt-row--base']"
                >
                  <td class="gantt-sticky gantt-sticky-line gantt-line-empty" />
                  <td class="gantt-sticky gantt-sticky-order">{{ row.order_no ?? '—' }}</td>
                  <td class="gantt-sticky gantt-sticky-name gantt-name">{{ row.item_name }}</td>
                  <td class="gantt-sticky gantt-sticky-eff">{{ formatEfficiencyRatePiecesPerH(row.efficiency_rate) }}</td>
                  <td class="gantt-sticky gantt-sticky-planned">{{ row.planned_process_qty }}</td>
                  <td class="gantt-sticky gantt-sticky-actual">{{ periodActualForRow(row).toLocaleString() }}</td>
                  <td
                    v-for="d in ganttDates"
                    :key="d"
                    class="gantt-cell"
                    :class="{ 'gantt-cell--tone': ganttCellHasSoftTone(row, d) }"
                    :title="ganttCellTitle(row, d)"
                    :aria-label="ganttCellHasAnyMarker(row, d) ? ganttCellTitle(row, d) : undefined"
                  >
                    <div v-if="ganttCellHasAnyMarker(row, d)" class="gantt-cell-markers">
                      <span v-if="ganttDayQty(row.daily?.[d]) !== 0" class="gantt-seg gantt-seg--plan">
                        <span class="gantt-dot gantt-dot--plan" role="presentation" />
                        <span class="gantt-seg-val">{{ ganttDayQty(row.daily?.[d]) }}</span>
                      </span>
                      <span v-if="ganttDayQty(row.actual_daily?.[d]) !== 0" class="gantt-seg gantt-seg--actual">
                        <span class="gantt-dot gantt-dot--actual" role="presentation" />
                        <span class="gantt-seg-val">{{ ganttDayQty(row.actual_daily?.[d]) }}</span>
                      </span>
                      <span v-if="shouldShowGanttRemain(row, d)" class="gantt-seg gantt-seg--remain">
                        <span class="gantt-dot gantt-dot--remain" role="presentation" />
                        <span class="gantt-seg-val">{{ ganttDayQty(row.remaining_daily?.[d]) }}</span>
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="一覧（表）" name="table">
          <div class="plan-sec-hd plan-sec-hd--inner">
            製造指示一覧
            <span class="plan-sec-badge">{{ rows.length }}</span>
          </div>

          <el-empty
            v-if="!loading && rows.length === 0"
            description="条件に一致する計画がありません"
            class="schedule-empty"
          />

          <div v-else class="schedule-table-group-list">
            <section
              v-for="group in tableGroups"
              :key="group.lineLabel"
              class="schedule-table-wrap schedule-table-group"
            >
              <div class="schedule-group-title">{{ group.lineLabel }}</div>
              <el-table
                :data="group.rows"
                border
                size="small"
                row-key="id"
                class="schedule-list-table nest-table--polish"
                empty-text=" "
                :row-class-name="scheduleTableRowClassName"
              >
                <el-table-column prop="order_no" label="順位" width="72" align="center" />
                <el-table-column :label="'製品名'" width="160" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="product-name-cell">{{ row.item_name || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'開始'" width="110" align="center">
                  <template #default="{ row }">
                    <span class="date-cell">{{ row.start_date || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'終了'" width="110" align="center">
                  <template #default="{ row }">
                    <span class="date-cell">{{ row.end_date || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'計画'" width="92" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell">{{ formatNum(row.planned_process_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'実績'" width="92" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell qty-cell--actual">{{ formatNum(tableActual(row)) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'不良'" width="88" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell qty-cell--defect">{{ formatNum(tableDefect(row)) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'前工程不良'" width="100" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell qty-cell--upstream">{{ formatNum(tableUpstreamDefect(row)) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'残'" width="92" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell">{{ formatNum(tableRemaining(row)) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'進捗'" width="92" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell">{{ tableProgress(row) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'状態'" width="124" align="center">
                  <template #default="{ row }">
                    <div class="status-lamp-cell">
                      <span
                        class="status-lamp-dot"
                        :class="{
                          'status-lamp-dot--done': tableStatusKind(row) === 'done',
                          'status-lamp-dot--ongoing': tableStatusKind(row) === 'ongoing',
                          'status-lamp-dot--pending': tableStatusKind(row) === 'pending',
                        }"
                        :title="tableStatusLabel(row)"
                      />
                      <span class="status-lamp-label">{{ tableStatusLabel(row) }}</span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </section>
          </div>
        </el-tab-pane>

        <el-tab-pane label="設備操業度" name="utilization">
          <div class="plan-sec-hd plan-sec-hd--inner util-sec-hd">
            <span>設備操業度（月次）</span>
            <span class="plan-sec-badge">{{ utilizationRows.length }}</span>
            <span class="util-hd-spacer" />
            <el-button
              size="small"
              type="warning"
              plain
              class="util-print-btn"
              :disabled="loading || utilizationRows.length === 0"
              @click="handleUtilizationPrint"
            >
              印刷
            </el-button>
          </div>
          <div class="util-note">
            <span class="util-note-chip">月初〜本日集計</span>
            <span class="util-note-chip">本日実績0以下は前日まで</span>
            <span class="util-note-chip util-note-chip--formula">差異工時=Σ((実績-計画)/能率)</span>
          </div>

          <el-empty
            v-if="!loading && utilizationRows.length === 0"
            description="集計対象データがありません"
            class="schedule-empty"
          />
          <div v-else class="schedule-table-wrap util-table-wrap">
            <el-table :data="utilizationRows" border size="small" class="schedule-list-table nest-table--polish util-table">
              <el-table-column prop="lineLabel" label="設備" width="85" show-overflow-tooltip />
              <el-table-column prop="scheduleCount" label="指示数" width="75" align="right" />
              <el-table-column label="稼働可能時間(H)" width="135" align="right">
                <template #default="{ row }"><span class="util-num">{{ formatHours(row.availableHours) }}</span></template>
              </el-table-column>
              <el-table-column label="計画数" width="80" align="right">
                <template #default="{ row }"><span class="util-num">{{ formatNum(row.plannedQty) }}</span></template>
              </el-table-column>
              <el-table-column label="実績数" width="80" align="right">
                <template #default="{ row }"><span class="util-num util-num--actual">{{ formatNum(row.actualQty) }}</span></template>
              </el-table-column>
              <el-table-column label="計画時間(H)" width="110" align="right">
                <template #default="{ row }"><span class="util-num">{{ formatHours(row.plannedHours) }}</span></template>
              </el-table-column>
              <el-table-column label="実績時間(H)" width="110" align="right">
                <template #default="{ row }"><span class="util-num util-num--actual">{{ formatHours(row.actualHours) }}</span></template>
              </el-table-column>
              <el-table-column label="計画操業度" width="100" align="right">
                <template #default="{ row }"><span class="util-num">{{ formatPercent(row.planUtilizationPct) }}</span></template>
              </el-table-column>
              <el-table-column label="実績操業度" width="100" align="right">
                <template #default="{ row }"><span class="util-num util-num--actual">{{ formatPercent(row.actualUtilizationPct) }}</span></template>
              </el-table-column>
              <el-table-column label="操業度差異(H)" width="120" align="right">
                <template #default="{ row }"><span class="util-num" :class="{ 'util-num--negative': row.diffHours < 0 }">{{ formatHours(row.diffHours) }}</span></template>
              </el-table-column>
              <el-table-column label="差異操業度(%)" width="130" align="right">
                <template #default="{ row }"><span class="util-num" :class="{ 'util-num--negative': row.diffUtilizationPct < 0 }">{{ formatPercent(row.diffUtilizationPct) }}</span></template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Printer } from '@element-plus/icons-vue'
import {
  fetchLines,
  fetchSchedulingGrid,
  replanLineSequence,
  type ScheduleGridRow,
} from '@/api/aps'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'

defineOptions({ name: 'FormingPlanningList' })

type GanttListRow = ScheduleGridRow & { lineLabel: string; line_id: number }

/** 一覧再計算前の画面状態（DB 巻き戻しは行わない） */
interface PreReplanGridSnapshot {
  rows: GanttListRow[]
  ganttRows: GanttListRow[]
  ganttDates: string[]
  lineCalendarHoursMap: Record<number, Record<string, number>>
  lineDefaultHoursMap: Record<number, number>
}

const preReplanGridSnapshot = ref<PreReplanGridSnapshot | null>(null)
const bulkReplanning = ref(false)

/** 再計算 API のクエリ用アンカー（DB の aps_line_replan_anchors があればサーバ側で優先） */
function formatYmdInJapan(d: Date): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(d)
}

const replanFallbackAnchorDate = computed(() => formatYmdInJapan(new Date()))

function clonePreReplanSnapshot(): PreReplanGridSnapshot {
  return JSON.parse(
    JSON.stringify({
      rows: rows.value,
      ganttRows: ganttRows.value,
      ganttDates: ganttDates.value,
      lineCalendarHoursMap: lineCalendarHoursMap.value,
      lineDefaultHoursMap: lineDefaultHoursMap.value,
    }),
  ) as PreReplanGridSnapshot
}

function offsetDateIso(offsetDays: number): string {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() + offsetDays)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

const dateRange = ref<[string, string]>([offsetDateIso(-1), offsetDateIso(30)])
const selectedProcessCd = ref<string>('')
const processOptions = ref<ProcessItem[]>([])
const loadingProcesses = ref(false)
const rows = ref<GanttListRow[]>([])
const loading = ref(false)
const searched = ref(false)
const activeResultTab = ref<'gantt' | 'table' | 'utilization'>('gantt')
const ganttDates = ref<string[]>([])
const ganttRows = ref<GanttListRow[]>([])
const lineCalendarHoursMap = ref<Record<number, Record<string, number>>>({})
const lineDefaultHoursMap = ref<Record<number, number>>({})

const canSearch = computed(
  () =>
    !!(
      Array.isArray(dateRange.value) &&
      dateRange.value[0] &&
      dateRange.value[1] &&
      (selectedProcessCd.value || '').trim()
    ),
)

const displayRangeText = computed(() => {
  const [startDate, endDate] = dateRange.value || []
  if (!startDate || !endDate) return '—'
  return `${startDate} 〜 ${endDate}`
})

const tableGroups = computed(() => {
  const groups: Array<{ lineLabel: string; rows: GanttListRow[] }> = []
  for (const row of rows.value) {
    const lineLabel = row.lineLabel || `ID ${row.line_id}`
    const last = groups[groups.length - 1]
    if (!last || last.lineLabel !== lineLabel) {
      groups.push({ lineLabel, rows: [row] })
    } else {
      last.rows.push(row)
    }
  }
  return groups
})

const ganttGroups = computed(() => {
  const groups: Array<{
    lineLabel: string
    rows: GanttListRow[]
    plannedTotal: number
    actualTotal: number
    avgEfficiencyRate: number | null
  }> = []
  for (const row of ganttRows.value) {
    const lineLabel = (row.lineLabel || '').trim() || `ID ${row.line_id}`
    const last = groups[groups.length - 1]
    if (!last || last.lineLabel !== lineLabel) {
      groups.push({
        lineLabel,
        rows: [row],
        plannedTotal: Number(row.planned_process_qty ?? 0),
        actualTotal: Number(periodActualForRow(row) ?? 0),
        avgEfficiencyRate: null,
      })
    } else {
      last.rows.push(row)
      last.plannedTotal += Number(row.planned_process_qty ?? 0)
      last.actualTotal += Number(periodActualForRow(row) ?? 0)
    }
  }

  for (const group of groups) {
    let weightedSum = 0
    let weightedDenom = 0
    for (const row of group.rows) {
      const rate = Number(row.efficiency_rate ?? 0)
      const qty = Number(row.planned_process_qty ?? 0)
      if (!Number.isFinite(rate) || !Number.isFinite(qty) || rate <= 0 || qty <= 0) continue
      weightedSum += rate * qty
      weightedDenom += qty
    }
    group.avgEfficiencyRate = weightedDenom > 0 ? weightedSum / weightedDenom : null
  }
  return groups
})

const monthlyStatDates = computed(() => {
  const allDates = [...ganttDates.value].sort((a, b) => a.localeCompare(b))
  if (allDates.length === 0) return [] as string[]
  const [startDate, endDate] = dateRange.value || []
  if (!startDate || !endDate) return allDates
  const today = todayIso.value
  const effectiveEnd = today >= startDate && today <= endDate ? today : endDate
  if (today < startDate) return [] as string[]
  return allDates.filter((d) => d >= startDate && d <= effectiveEnd)
})

interface LineUtilizationRow {
  lineId: number
  lineLabel: string
  scheduleCount: number
  availableHours: number
  plannedQty: number
  actualQty: number
  plannedHours: number
  actualHours: number
  diffQty: number
  diffHours: number
  diffUtilizationPct: number
  planUtilizationPct: number
  actualUtilizationPct: number
}

const utilizationRows = computed<LineUtilizationRow[]>(() => {
  const baseDates = monthlyStatDates.value
  if (baseDates.length === 0) return []
  const lastBaseDate = baseDates[baseDates.length - 1]
  const prevBaseDate = baseDates.length >= 2 ? baseDates[baseDates.length - 2] : lastBaseDate
  const actualOnLastByLine = new Map<number, number>()
  for (const row of ganttRows.value) {
    const lid = row.line_id
    const v = Number(row.actual_daily?.[lastBaseDate] ?? 0)
    actualOnLastByLine.set(lid, (actualOnLastByLine.get(lid) ?? 0) + v)
  }
  const lineDatesMap = new Map<number, string[]>()
  for (const row of ganttRows.value) {
    const lid = row.line_id
    if (lineDatesMap.has(lid)) continue
    const todayActual = Number(actualOnLastByLine.get(lid) ?? 0)
    const endDate = todayActual > 0 ? lastBaseDate : prevBaseDate
    lineDatesMap.set(lid, baseDates.filter((d) => d <= endDate))
  }

  const map = new Map<number, LineUtilizationRow>()
  for (const row of ganttRows.value) {
    const lineId = row.line_id
    const statDates = lineDatesMap.get(lineId) ?? baseDates
    const plannedQty = statDates.reduce((sum, d) => sum + Number(row.daily?.[d] ?? 0), 0)
    const actualQty = statDates.reduce((sum, d) => sum + Number(row.actual_daily?.[d] ?? 0), 0)
    const rate = Number(row.efficiency_rate ?? 0)
    const plannedHours = rate > 0 ? plannedQty / rate : 0
    const actualHours = rate > 0 ? actualQty / rate : 0
    const diffQtyRow = statDates.reduce((sum, d) => {
      const p = Number(row.daily?.[d] ?? 0)
      const a = Number(row.actual_daily?.[d] ?? 0)
      return sum + (a - p)
    }, 0)
    const diffHoursRow = rate > 0 ? diffQtyRow / rate : 0
    const item = map.get(lineId) ?? {
      lineId,
      lineLabel: row.lineLabel || `ID ${lineId}`,
      scheduleCount: 0,
      availableHours: 0,
      plannedQty: 0,
      actualQty: 0,
      plannedHours: 0,
      actualHours: 0,
      diffQty: 0,
      diffHours: 0,
      diffUtilizationPct: 0,
      planUtilizationPct: 0,
      actualUtilizationPct: 0,
    }
    item.scheduleCount += 1
    item.plannedQty += plannedQty
    item.actualQty += actualQty
    item.plannedHours += plannedHours
    item.actualHours += actualHours
    item.diffQty += diffQtyRow
    item.diffHours += diffHoursRow
    map.set(lineId, item)
  }
  const result = Array.from(map.values())
  for (const r of result) {
    const statDates = lineDatesMap.get(r.lineId) ?? baseDates
    const calMap = lineCalendarHoursMap.value[r.lineId] || {}
    const fallback = Number(lineDefaultHoursMap.value[r.lineId] ?? 0)
    const avail = statDates.reduce((sum, d) => {
      const h = Number(calMap[d] ?? fallback)
      return sum + (Number.isFinite(h) ? h : 0)
    }, 0)
    r.availableHours = avail
    r.planUtilizationPct = avail > 0 ? (r.plannedHours / avail) * 100 : 0
    r.actualUtilizationPct = avail > 0 ? (r.actualHours / avail) * 100 : 0
    r.diffUtilizationPct = avail > 0 ? (r.diffHours / avail) * 100 : 0
  }
  result.sort((a, b) => a.lineLabel.localeCompare(b.lineLabel, 'ja'))
  return result
})

onMounted(() => {
  void loadProcessOptions()
})

async function loadProcessOptions() {
  loadingProcesses.value = true
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const list = res.list ?? res.data?.list ?? []
    processOptions.value = Array.isArray(list) ? list : []
    const hasDefault = processOptions.value.some((p) => (p.process_cd || '').trim() === 'KT04')
    if (hasDefault) {
      selectedProcessCd.value = 'KT04'
    } else if (processOptions.value.length === 1) {
      selectedProcessCd.value = (processOptions.value[0].process_cd || '').trim()
    }
  } catch {
    processOptions.value = []
    ElMessage.error('工程一覧の取得に失敗しました')
  } finally {
    loadingProcesses.value = false
  }
}

/** 設備表示名 → 順位 → id の昇順（一覧・ガント共通） */
function compareByLineThenOrder(a: GanttListRow, b: GanttListRow): number {
  const lineCmp = (a.lineLabel || '').localeCompare(b.lineLabel || '', 'ja')
  if (lineCmp !== 0) return lineCmp
  const oa = a.order_no ?? 1_000_000 + a.id
  const ob = b.order_no ?? 1_000_000 + b.id
  if (oa !== ob) return oa - ob
  return a.id - b.id
}

function scheduleTableRowClassName({
  rowIndex,
}: {
  row: GanttListRow
  rowIndex: number
}): string {
  const parts: string[] = []
  if (rowIndex % 2 === 1) parts.push('schedule-row--alt')
  return parts.join(' ')
}

function formatNum(v: number | null | undefined): string {
  return Number(v ?? 0).toLocaleString()
}

function formatHours(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  return Number.isFinite(n) ? n.toFixed(1) : '0.0'
}

function formatPercent(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n)) return '0.0%'
  return `${n.toFixed(1)}%`
}

function escHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** 日別セル値を数値化（文字列・欠損でも表示判定がブレないようにする） */
function ganttDayQty(v: unknown): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function selectedProcessLabel(): string {
  const cd = (selectedProcessCd.value || '').trim()
  if (!cd) return '—'
  const p = processOptions.value.find((x) => (x.process_cd || '').trim() === cd)
  const nm = (p?.process_name || '').trim()
  return nm ? `${cd} — ${nm}` : cd
}

function buildUtilizationPrintHtml(): string {
  const title = '設備操業度（月次）'
  const printedAt = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  const rowsHtml = utilizationRows.value
    .map((r) => {
      const negHours = r.diffHours < 0 ? 'neg' : ''
      const negPct = r.diffUtilizationPct < 0 ? 'neg' : ''
      return `<tr>
        <td class="left">${escHtml(r.lineLabel)}</td>
        <td class="num">${escHtml(String(r.scheduleCount))}</td>
        <td class="num">${escHtml(formatHours(r.availableHours))}</td>
        <td class="num">${escHtml(formatNum(r.plannedQty))}</td>
        <td class="num">${escHtml(formatNum(r.actualQty))}</td>
        <td class="num">${escHtml(formatHours(r.plannedHours))}</td>
        <td class="num">${escHtml(formatHours(r.actualHours))}</td>
        <td class="num">${escHtml(formatPercent(r.planUtilizationPct))}</td>
        <td class="num">${escHtml(formatPercent(r.actualUtilizationPct))}</td>
        <td class="num ${negHours}">${escHtml(formatHours(r.diffHours))}</td>
        <td class="num ${negPct}">${escHtml(formatPercent(r.diffUtilizationPct))}</td>
      </tr>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(title)}</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body { margin: 16px; color: #0f172a; font: 12px/1.4 "Segoe UI", "Yu Gothic UI", Meiryo, sans-serif; }
    .hd { margin-bottom: 10px; }
    .tt { font-size: 18px; font-weight: 700; }
    .meta { margin-top: 4px; color: #475569; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #cbd5e1; padding: 6px 8px; }
    th { background: #eff6ff; font-weight: 700; }
    .left { text-align: left; }
    .num { text-align: right; font-variant-numeric: tabular-nums; }
    .neg { color: #dc2626; font-weight: 700; }
    tbody tr:nth-child(odd) { background: #f8fafc; }
    @media print { @page { size: A4 landscape; margin: 10mm; } }
  </style>
</head>
<body>
  <div class="hd">
    <div class="tt">${escHtml(title)}</div>
    <div class="meta">期間：${escHtml(displayRangeText.value)}　工程：${escHtml(selectedProcessLabel())}　印刷日時：${escHtml(printedAt)}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th class="left">設備</th>
        <th class="num">製造指示数</th>
        <th class="num">稼働可能時間(H)</th>
        <th class="num">計画数</th>
        <th class="num">実績数</th>
        <th class="num">計画時間(H)</th>
        <th class="num">実績時間(H)</th>
        <th class="num">計画操業度</th>
        <th class="num">実績操業度</th>
        <th class="num">操業度差異(H)</th>
        <th class="num">差異操業度(%)</th>
      </tr>
    </thead>
    <tbody>${rowsHtml}</tbody>
  </table>
</body>
</html>`
}

function buildGanttPrintHtml(): string {
  const title = '成型計画一覧（ガント日別）'
  const printedAt = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  const dateCols = ganttDates.value
    .map((d) => `<th class="date-col">${escHtml(d.slice(5))}</th>`)
    .join('')
  const emptyDateCells = ganttDates.value.map(() => '<td></td>').join('')
  const rowsHtml = ganttGroups.value
    .map((group) => {
      const lineLabel = group.lineLabel
      const lineRows = group.rows
      const groupHeader = `<tr class="group-row">
        <td class="left line-col">${escHtml(lineLabel)}</td>
        <td></td>
        <td></td>
        <td class="num eff-col">${escHtml(formatGroupEfficiency(group.avgEfficiencyRate))}</td>
        <td class="num planned-col">${escHtml(formatNum(group.plannedTotal))}</td>
        <td class="num act-col">${escHtml(formatNum(group.actualTotal))}</td>
        ${emptyDateCells}
      </tr>`
      const body = lineRows
        .map((row) => {
          const cells = ganttDates.value
            .map((d) => {
              const p = ganttDayQty(row.daily?.[d])
              const a = ganttDayQty(row.actual_daily?.[d])
              const showRemain = shouldShowGanttRemain(row, d)
              const r = showRemain ? ganttDayQty(row.remaining_daily?.[d]) : 0
              if (p === 0 && a === 0 && r === 0) return '<td></td>'
              const chunks: string[] = []
              if (p !== 0) chunks.push(`${p}`)
              if (a !== 0) chunks.push(`${a}`)
              if (r !== 0) chunks.push(`${r}`)
              return `<td class="num cell-data">${escHtml(chunks.join(' / '))}</td>`
            })
            .join('')
          return `<tr>
            <td class="line-col"></td>
            <td class="num indent-col order-col">${escHtml(String(row.order_no ?? '—'))}</td>
            <td class="left name-col indent-col">${escHtml(row.item_name || '—')}</td>
            <td class="num eff-col">${escHtml(formatEfficiencyRatePiecesPerH(row.efficiency_rate))}</td>
            <td class="num indent-col planned-col">${escHtml(formatNum(row.planned_process_qty))}</td>
            <td class="num act-col">${escHtml(formatNum(periodActualForRow(row)))}</td>
            ${cells}
          </tr>`
        })
        .join('')
      return `<tbody class="group-block">${groupHeader}${body}</tbody>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(title)}</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body { margin: 8px; color: #0f172a; font: 10px/1.35 "Segoe UI", "Yu Gothic UI", Meiryo, sans-serif; background: #f8fafc; }
    .hd { margin-bottom: 8px; padding: 8px 10px; border: 1px solid #dbe5f1; border-radius: 8px; background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%); }
    .tt { font-size: 16px; font-weight: 800; color: #1e3a8a; }
    .meta { margin-top: 3px; color: #475569; font-size: 10px; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #cbd5e1; padding: 3px 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    th { background: linear-gradient(180deg, #eaf3ff 0%, #dceafe 100%); font-weight: 800; color: #334155; }
    .left { text-align: left; }
    .num { text-align: right; font-variant-numeric: tabular-nums; font-family: Consolas, "Courier New", monospace; }
    .date-col { font-size: 9px; }
    .group-block { break-inside: avoid; page-break-inside: avoid; }
    .name-col { color: #0f172a; font-weight: 700; width: 110px; max-width: 110px; }
    .line-col { font-weight: 800; width: 80px; max-width: 80px; white-space: normal; }
    .order-col { width: calc(2ch + 10px); max-width: calc(2ch + 10px); }
    .eff-col { width: calc(6ch + 12px); max-width: calc(6ch + 12px); }
    .planned-col { width: calc(5ch + 20px); max-width: calc(5ch + 20px); }
    .act-col { width: calc(5ch + 20px); max-width: calc(5ch + 20px); }
    .indent-col { padding-left: 10px; }
    .cell-data { font-size: 9px; }
    .group-row td { background: #e2e8f0; color: #1e293b; font-weight: 800; text-align: left; border-top: 2px solid #94a3b8; }
    tbody tr:nth-child(odd) { background: #fcfdff; }
    tbody tr:nth-child(even) { background: #f7fbff; }
    @media print { @page { size: A3 landscape; margin: 8mm; } }
  </style>
</head>
<body>
  <div class="hd">
    <div class="tt">${escHtml(title)}</div>
    <div class="meta">期間：${escHtml(displayRangeText.value)}　工程：${escHtml(selectedProcessLabel())}　表示期間：${escHtml(displayRangeText.value)}　印刷日時：${escHtml(printedAt)}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th class="left line-col">設備</th>
        <th class="num order-col">順位</th>
        <th class="left name-col">品名</th>
        <th class="num eff-col">能率</th>
        <th class="num planned-col">計画数</th>
        <th class="num act-col">実績数</th>
        ${dateCols}
      </tr>
    </thead>
    ${rowsHtml}
  </table>
</body>
</html>`
}

function handleGanttPrint() {
  if (ganttRows.value.length === 0 || ganttDates.value.length === 0) {
    ElMessage.warning('印刷対象のガントデータがありません')
    return
  }
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.error('ポップアップがブロックされました')
    return
  }
  w.document.write(buildGanttPrintHtml())
  w.document.close()
  w.onload = () => {
    w.print()
    setTimeout(() => w.close(), 400)
  }
}

function handleUtilizationPrint() {
  if (utilizationRows.value.length === 0) {
    ElMessage.warning('印刷対象データがありません')
    return
  }
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.error('ポップアップがブロックされました')
    return
  }
  w.document.write(buildUtilizationPrintHtml())
  w.document.close()
  w.onload = () => {
    w.print()
    setTimeout(() => w.close(), 400)
  }
}

function tableActual(row: GanttListRow): number {
  const target = ganttRows.value.find((g) => g.id === row.id)
  if (!target) return 0
  return periodActualForRow(target)
}

/** 不良：schedule_details.defect_qty の期間合計（API の defect_qty_sum） */
function tableDefect(row: GanttListRow): number {
  const v = row.defect_qty_sum
  if (v != null && Number.isFinite(Number(v))) return Math.max(0, Number(v))
  const target = ganttRows.value.find((g) => g.id === row.id)
  return target ? periodDefectForRow(target) : 0
}

/** 前工程不良：FormingPlanning と同様 aps_batch_plans.upstream_defect_qty の当指示合計 */
function tableUpstreamDefect(row: GanttListRow): number {
  const v = row.upstream_defect_qty_total
  if (v != null && Number.isFinite(Number(v))) return Math.max(0, Number(v))
  const target = ganttRows.value.find((g) => g.id === row.id)
  return target ? periodUpstreamDefectForRow(target) : 0
}

function tableRemaining(row: GanttListRow): number {
  const planned = Number(row.planned_process_qty ?? 0)
  const remain = planned - tableActual(row)
  return remain > 0 ? remain : 0
}

function tableProgress(row: GanttListRow): string {
  const planned = Number(row.planned_process_qty ?? 0)
  if (planned <= 0) return '0%'
  const pct = (tableActual(row) / planned) * 100
  return `${Math.round(Math.max(0, Math.min(999, pct)))}%`
}

function parseLocalDay(v: string | undefined | null): Date | null {
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

function tableStatusKind(row: GanttListRow): 'done' | 'ongoing' | 'pending' {
  const today = todayLocalStart()
  const start = parseLocalDay(row.start_date)
  const end = parseLocalDay(row.end_date)
  if (end && end < today) return 'done'
  if (start && end && start <= today && today <= end) return 'ongoing'
  return 'pending'
}

function tableStatusLabel(row: GanttListRow): string {
  const map: Record<'done' | 'ongoing' | 'pending', string> = {
    done: '生産済',
    ongoing: '生産中',
    pending: '準備中',
  }
  return map[tableStatusKind(row)]
}

function formatApiError(e: unknown): string {
  const err = e as {
    response?: { data?: { detail?: string | { msg?: string }[]; message?: string } }
    message?: string
  }
  const d = err?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    const parts = d.map((x) => (typeof x === 'object' && x?.msg ? x.msg : String(x))).filter(Boolean)
    if (parts.length) return parts.join('；')
  }
  return err?.response?.data?.message || err?.message || 'エラーが発生しました'
}

function onSearchClick() {
  void loadSchedules()
}

async function loadSchedules(options?: { clearReplanSnapshot?: boolean }) {
  const clearReplanSnapshot = options?.clearReplanSnapshot !== false
  if (!canSearch.value) {
    ElMessage.warning('期間と工程を選択してください')
    return
  }
  const [sd, ed] = dateRange.value || []
  if (!sd || !ed) {
    ElMessage.warning('期間を入力してください')
    return
  }
  if (sd > ed) {
    ElMessage.warning('期間の開始日は終了日以前にしてください')
    return
  }
  loading.value = true
  searched.value = true
  ganttDates.value = []
  ganttRows.value = []
  lineCalendarHoursMap.value = {}
  lineDefaultHoursMap.value = {}
  try {
    const pc = (selectedProcessCd.value || '').trim()
    const [grid, lines] = await Promise.all([
      fetchSchedulingGrid(sd, ed, undefined, pc),
      fetchLines(pc || undefined),
    ])
    ganttDates.value = Array.isArray(grid.dates) ? grid.dates : []
    const lineNameById = new Map<number, string>()
    for (const line of lines || []) {
      const name = String(line.line_name || '').trim()
      const code = String(line.line_code || '').trim()
      lineNameById.set(line.id, name || code || `ID ${line.id}`)
    }
    const calendarMap: Record<number, Record<string, number>> = {}
    const defaultMap: Record<number, number> = {}
    for (const block of grid.blocks || []) {
      calendarMap[block.line_id] = block.calendar || {}
      defaultMap[block.line_id] = Number(block.default_work_hours ?? 0)
    }
    lineCalendarHoursMap.value = calendarMap
    lineDefaultHoursMap.value = defaultMap

    const flat: GanttListRow[] = []
    for (const block of grid.blocks || []) {
      const label =
        lineNameById.get(block.line_id) ||
        String((block as { line_name?: string }).line_name || '').trim() ||
        block.line_code ||
        `ID ${block.line_id}`
      for (const r of block.rows || []) {
        flat.push({ ...r, lineLabel: label, line_id: block.line_id })
      }
    }
    flat.sort(compareByLineThenOrder)
    rows.value = [...flat]
    ganttRows.value = flat
    if (clearReplanSnapshot) preReplanGridSnapshot.value = null
  } catch (e: unknown) {
    rows.value = []
    ganttDates.value = []
    ganttRows.value = []
    lineCalendarHoursMap.value = {}
    lineDefaultHoursMap.value = {}
    ElMessage.error(String((e as { message?: string })?.message || e))
  } finally {
    loading.value = false
  }
}

function restorePreReplanGrid() {
  const snap = preReplanGridSnapshot.value
  if (!snap) {
    ElMessage.warning('戻せるスナップショットがありません')
    return
  }
  rows.value = JSON.parse(JSON.stringify(snap.rows)) as GanttListRow[]
  ganttRows.value = JSON.parse(JSON.stringify(snap.ganttRows)) as GanttListRow[]
  ganttDates.value = [...snap.ganttDates]
  lineCalendarHoursMap.value = JSON.parse(JSON.stringify(snap.lineCalendarHoursMap))
  lineDefaultHoursMap.value = JSON.parse(JSON.stringify(snap.lineDefaultHoursMap))
  ElMessage.success('再計算前に取得した一覧表示に戻しました（サーバの計画は変わりません）')
}

async function replanAllLinesForProcess() {
  if (!canSearch.value) {
    ElMessage.warning('期間と工程を選択してください')
    return
  }
  const pc = (selectedProcessCd.value || '').trim()
  if (!pc) return
  try {
    await ElMessageBox.confirm(
      `工程「${pc}」の全設備をラインコード順に順次再計算します。実行しますか？`,
      '全設備ライン順で再計算',
      { type: 'warning', confirmButtonText: '実行', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  bulkReplanning.value = true
  try {
    const rawLines = await fetchLines(pc)
    const lines = (Array.isArray(rawLines) ? rawLines : []).filter((l) => l.is_active !== false)
    lines.sort((a, b) => (a.line_code || '').localeCompare(b.line_code || '', 'ja'))
    if (lines.length === 0) {
      ElMessage.warning('対象工程に有効な設備がありません')
      return
    }
    if (rows.value.length > 0 || ganttRows.value.length > 0) {
      preReplanGridSnapshot.value = clonePreReplanSnapshot()
    }
    const anchor = replanFallbackAnchorDate.value
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      await replanLineSequence(line.id, anchor)
    }
    await loadSchedules({ clearReplanSnapshot: false })
    ElMessage.success(`全 ${lines.length} 設備の順次再計算が完了しました`)
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '再計算に失敗しました')
    try {
      await loadSchedules({ clearReplanSnapshot: false })
    } catch {
      /* 一覧取得失敗は無視 */
    }
  } finally {
    bulkReplanning.value = false
  }
}

function formatEfficiencyRatePiecesPerH(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Number(v)
  const s = n % 1 === 0 ? String(Math.round(n)) : n.toFixed(1)
  return `${s}本/H`
}

function formatGroupEfficiency(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(Number(v))) return '—'
  return `${Number(v).toFixed(1)}本/H`
}

const todayIso = computed(() => new Date().toISOString().slice(0, 10))

function isWeekend(d: string): boolean {
  const day = new Date(d).getDay()
  return day === 0 || day === 6
}

function isToday(d: string): boolean {
  return d === todayIso.value
}

function getWeekday(d: string): string {
  const wd = ['日', '月', '火', '水', '木', '金', '土']
  return wd[new Date(d).getDay()]
}

/** 列日付が本日より前（当日は含めない） */
function isPastGanttDate(d: string): boolean {
  return d < todayIso.value
}

/** 当日に実績がある列、または日付が本日より前の列：ガントセルに淡色背景 */
function ganttCellHasSoftTone(row: ScheduleGridRow, d: string): boolean {
  if (ganttDayQty(row.actual_daily?.[d]) !== 0) return true
  if (isPastGanttDate(d)) return true
  return false
}

/**
 * 残の表示ルール：
 * - 当日実績あり → 残も表示対象（残>0 かつトグルON のとき）
 * - 当日実績なし → 本日以降の日付では残を出さない／過去日のみ残を出す（計画未着手・遅れの把握用）
 */
function shouldShowGanttRemain(row: ScheduleGridRow, d: string): boolean {
  const r = ganttDayQty(row.remaining_daily?.[d])
  if (r === 0) return false
  const a = ganttDayQty(row.actual_daily?.[d])
  if (a !== 0) return true
  return isPastGanttDate(d)
}

function ganttCellHasAnyMarker(row: ScheduleGridRow, d: string): boolean {
  const p = ganttDayQty(row.daily?.[d])
  const a = ganttDayQty(row.actual_daily?.[d])
  if (p !== 0 || a !== 0) return true
  return shouldShowGanttRemain(row, d)
}

function ganttCellTitle(row: ScheduleGridRow, d: string): string {
  const planned = ganttDayQty(row.daily?.[d])
  const actual = ganttDayQty(row.actual_daily?.[d])
  const remain = ganttDayQty(row.remaining_daily?.[d])
  if (!ganttCellHasAnyMarker(row, d)) return ''
  const parts: string[] = []
  if (planned !== 0) parts.push(`計画 ${planned}`)
  if (actual !== 0) parts.push(`実績 ${actual}`)
  if (shouldShowGanttRemain(row, d)) parts.push(`残 ${remain}`)
  if (parts.length === 0) return ''
  return `${row.item_name}: ${parts.join(' / ')}`
}

function periodActualForRow(row: ScheduleGridRow): number {
  const m = row.actual_daily || {}
  const dates1 = ganttDates.value.length > 0 ? ganttDates.value : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

/** ガント表示期間内の不良合計（defect_daily の期間合計） */
function periodDefectForRow(row: ScheduleGridRow): number {
  const m = row.defect_daily || {}
  const dates1 = ganttDates.value.length > 0 ? ganttDates.value : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

/** ガント表示期間内の前工程不良合計（upstream_defect_daily の期間合計） */
function periodUpstreamDefectForRow(row: ScheduleGridRow): number {
  const m = row.upstream_defect_daily || {}
  const dates1 = ganttDates.value.length > 0 ? ganttDates.value : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}
</script>

<style scoped>
.forming-plan-list-page {
  --font-sans: inherit;
  --font-mono: inherit;
  --fs-xs: 10.5px;
  --fs-s: 11.5px;
  --fs-base: 13px;
  --c-text-h: #0b1220;
  --c-text-m: #445063;
  --c-text-s: #6b778a;
  --c-border: #dbe3ee;
  --c-border-l: #e9eef6;
  --c-surface: #ffffff;
  --c-bg: #f4f7fb;
  --c-accent: #3b82f6;
  --c-accent-2: #7c3aed;
  --c-success: #10b981;
  --c-warn: #f59e0b;
  /* 左 sticky 列幅（設備列は .list-gantt-table 内で指定） */
  --gl-order: 44px;
  --gl-name: 110px;
  --gl-eff: 70px;
  --gl-plan: 56px;
  --gl-act: var(--gl-plan);

  padding: 10px 12px 12px;
  background:
    radial-gradient(circle at 10% -20%, rgba(59, 130, 246, 0.1), transparent 35%),
    radial-gradient(circle at 110% -30%, rgba(16, 185, 129, 0.08), transparent 30%),
    #f3f6fb;
  min-height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-family: inherit;
  font-size: var(--fs-base);
  color: var(--c-text-m);
  -webkit-font-smoothing: antialiased;
}

.plan-hd {
  margin-bottom: 0;
  padding: 4px 2px 2px;
}
.plan-hd-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.2px;
  line-height: 1.1;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.55);
}
.plan-hd-icon {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow:
    0 6px 14px rgba(37, 99, 235, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.plan-hd-icon svg {
  width: 15px;
  height: 15px;
  fill: #fff;
}
.plan-hd-sub {
  margin: 5px 0 0 34px;
  color: var(--c-text-s);
  font-size: var(--fs-s);
  line-height: 1.45;
  max-width: 980px;
}
.plan-hd-sub strong {
  font-weight: 600;
  color: #4f5f79;
}

.plan-card {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(3px);
  padding: 10px 12px;
  margin-bottom: 0;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 20px rgba(15, 23, 42, 0.04);
}

.filter-card {
  padding: 7px 10px;
  border-color: rgba(191, 219, 254, 0.75);
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.82) 0%, rgba(250, 245, 255, 0.76) 100%),
    rgba(255, 255, 255, 0.95);
  box-shadow:
    0 10px 22px rgba(37, 99, 235, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 2px;
  margin-right: 6px;
}
.filter-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #1e3a8a;
  padding-right: 5px;
  line-height: 30px;
}
.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  min-height: 32px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  transition: box-shadow 0.18s ease, border-color 0.18s ease;
}
.filter-form :deep(.el-input__wrapper:hover),
.filter-form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.12);
}
.filter-form :deep(.el-input__wrapper.is-focus),
.filter-form :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
}
.filter-form :deep(.el-button) {
  border-radius: 999px;
  border: none;
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.2px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow:
    0 8px 18px rgba(37, 99, 235, 0.28),
    0 2px 4px rgba(124, 58, 237, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.34);
  padding-left: 14px;
  padding-right: 14px;
}

.forming-replan-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(191, 219, 254, 0.55);
}
.forming-replan-toolbar__primary {
  border-radius: 999px;
  font-weight: 700;
}
.forming-replan-toolbar__note {
  flex: 1 1 240px;
  font-size: 12px;
  line-height: 1.45;
  color: #475569;
}

.result-card {
  padding: 10px 10px 12px;
}

.result-tabs :deep(.el-tabs__content) {
  padding-top: 8px;
}
.result-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}
.result-tabs :deep(.el-tabs__item) {
  font-weight: 800;
  font-size: var(--fs-base);
  color: #334155;
}
.result-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px;
  background: linear-gradient(90deg, #2563eb 0%, #7c3aed 100%);
}

.gantt-legend-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-bottom: 8px;
  padding: 6px 10px;
  font-size: var(--fs-s);
  color: var(--c-text-m);
  background: linear-gradient(180deg, #f8fbff 0%, #f2f7ff 100%);
  border-radius: 10px;
  border: 1px solid var(--c-border-l);
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  font-weight: 700;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 4px;
  display: inline-block;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.18);
}
.legend-dot--plan {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}
.legend-dot--actual {
  background: linear-gradient(135deg, #10b981, #059669);
}
.legend-dot--remain {
  background: linear-gradient(135deg, #a78bfa, #7c3aed);
}
.gantt-range-note {
  margin-left: auto;
  font-size: var(--fs-xs);
  font-family: var(--font-mono);
  color: var(--c-text-s);
}
.gantt-print-btn {
  margin-left: 12px;
  flex-shrink: 0;
  border-radius: 999px !important;
  padding: 0 16px 0 14px !important;
  min-height: 30px !important;
  font-weight: 700 !important;
  font-size: 12.5px !important;
  letter-spacing: 0.04em;
  color: #334155 !important;
  border: 1px solid rgba(148, 163, 184, 0.55) !important;
  background: linear-gradient(165deg, #ffffff 0%, #f8fafc 42%, #eef2f7 100%) !important;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.06),
    0 6px 16px -6px rgba(37, 99, 235, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  transition:
    transform 0.18s ease,
    box-shadow 0.22s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    background 0.2s ease;
}

.gantt-print-btn:hover:not(.is-disabled) {
  color: #1e3a8a !important;
  border-color: rgba(59, 130, 246, 0.5) !important;
  background: linear-gradient(165deg, #ffffff 0%, #f0f7ff 45%, #e8effc 100%) !important;
  box-shadow:
    0 2px 4px rgba(15, 23, 42, 0.07),
    0 10px 24px -8px rgba(37, 99, 235, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 1);
  transform: translateY(-1px);
}

.gantt-print-btn:active:not(.is-disabled) {
  transform: translateY(0);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.08),
    inset 0 1px 2px rgba(15, 23, 42, 0.06);
}

.gantt-print-btn.is-disabled,
.gantt-print-btn.is-disabled:hover {
  opacity: 0.48 !important;
  transform: none !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
}

.gantt-print-btn :deep(.el-icon) {
  font-size: 15px;
  color: #64748b;
  transition: color 0.2s ease;
}

.gantt-print-btn:hover:not(.is-disabled) :deep(.el-icon) {
  color: #2563eb;
}

.plan-sec-hd {
  font-size: var(--fs-base);
  font-weight: 700;
  color: var(--c-text-h);
  margin: 0 0 12px;
  padding-left: 9px;
  border-left: 3px solid var(--c-accent);
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.3;
}
.plan-sec-hd--inner {
  margin-top: 4px;
}
.plan-sec-badge {
  font-size: var(--fs-xs);
  font-weight: 600;
  background: linear-gradient(90deg, var(--c-accent) 0%, var(--c-accent-2) 100%);
  color: #fff;
  padding: 1px 7px;
  border-radius: 10px;
  line-height: 18px;
}

.line-cell {
  font-size: var(--fs-s);
  font-weight: 700;
  color: var(--c-text-h);
  letter-spacing: 0.01em;
}

.product-name-cell {
  color: var(--c-accent);
  font-weight: 600;
}

.qty-cell {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 800;
  font-size: var(--fs-s);
  color: var(--c-text-h);
}
.qty-cell--actual {
  color: #059669;
}

.qty-cell--defect {
  color: #c2410c;
}

.qty-cell--upstream {
  color: #6d28d9;
}

.date-cell {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: var(--fs-s);
  font-weight: 700;
  color: var(--c-text-m);
}

.schedule-empty :deep(.el-empty__description) {
  color: var(--c-text-s);
  font-size: var(--fs-s);
}

.util-note {
  margin: 6px 0 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.util-sec-hd {
  margin-bottom: 10px;
}
.util-hd-spacer {
  margin-left: auto;
}
.util-print-btn {
  border-radius: 9px;
  font-weight: 700;
  padding: 6px 12px;
}
.util-note-chip {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  background: linear-gradient(180deg, #f8fbff 0%, #edf3fb 100%);
  border: 1px solid #d7e2f0;
}
.util-note-chip--formula {
  color: #1d4ed8;
  background: linear-gradient(180deg, #eef4ff 0%, #e0ebff 100%);
  border-color: #c7d8ff;
}
.util-table-wrap {
  border-color: #dbe6f5;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.92),
    0 8px 20px -16px rgba(30, 64, 175, 0.28);
}
.util-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #eef4ff 0%, #e6effc 100%) !important;
  color: #1f2937 !important;
}
.util-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #eaf2ff !important;
}
.util-num {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 800;
  color: #0f172a;
}
.util-num--actual {
  color: #047857;
}
.util-num--negative {
  color: #dc2626;
}

/* 一覧（表）：ガントと揃えた浅色・区切り・ヘッダー */
.schedule-table-wrap {
  border-radius: 12px;
  border: 1px solid var(--c-border-l);
  overflow: hidden;
  background: linear-gradient(180deg, #f5f9ff 0%, #fafcfe 55%, #f8fafc 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}
.schedule-table-group-list {
  display: grid;
  gap: 10px;
}
.schedule-table-group {
  padding-top: 0;
}
.schedule-group-title {
  padding: 9px 12px;
  font-size: var(--fs-s);
  font-weight: 800;
  letter-spacing: 0.02em;
  color: var(--c-text-h);
  background: linear-gradient(180deg, #edf3fb 0%, #e6eef9 100%);
  border-bottom: 1px solid #d4deeb;
}

.schedule-list-table {
  width: 100%;
  font-size: var(--fs-s);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  --el-table-header-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-border-color: #e2e8f0;
  --el-table-row-hover-bg-color: #e8f0fe;
}

.nest-table--polish {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 32px -24px rgba(15, 23, 42, 0.25);
  --el-table-border-color: color-mix(in srgb, var(--el-border-color) 88%, var(--el-color-primary));
}

.schedule-list-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.schedule-list-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, var(--el-fill-color-lighter) 0%, var(--el-fill-color-blank) 100%) !important;
  color: var(--el-text-color-primary) !important;
  font-weight: 700;
  font-size: var(--fs-s);
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--el-border-color-lighter) !important;
  padding: 8px 10px;
}

.schedule-list-table :deep(.el-table__body td.el-table__cell) {
  padding: 7px 10px;
  border-color: #e2e8f0 !important;
  color: #334155;
  background: #fafcfe !important;
}

.schedule-list-table :deep(.el-table__body tr.schedule-row--alt > td.el-table__cell) {
  background: #f3f6fb !important;
}

.schedule-list-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: color-mix(in srgb, var(--el-color-primary) 4%, var(--el-fill-color-blank)) !important;
}

.schedule-list-table :deep(.el-table__body tr.schedule-row--alt:hover > td.el-table__cell) {
  background: #dbe7fd !important;
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
}
.status-lamp-dot--pending {
  background: var(--el-color-warning);
}
.status-lamp-label {
  font-size: var(--fs-s);
  color: var(--el-text-color-regular);
  font-weight: 500;
}

/* ── Gantt（日別）：对齐 Scheduling.vue 表格风格 ── */
.list-gantt-scroll {
  max-height: 620px;
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.list-gantt-table {
  --gl-line: 80px;
  --gl-name: 110px;
  --gl-plan: 56px;
  --gl-act: var(--gl-plan);
  table-layout: fixed;
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-s);
  line-height: 1.35;
  color: var(--c-text-m);
}

.list-gantt-table th,
.list-gantt-table td {
  border: 1px solid #e6edf5;
  padding: 3px 5px;
  white-space: nowrap;
  box-sizing: border-box;
}

.list-gantt-table thead th {
  position: sticky;
  top: 0;
  z-index: 3;
  background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  font-weight: 700;
  color: var(--c-text-m);
  box-shadow: 0 1px 0 #dbe5f1;
}

.list-gantt-table thead th.gantt-sticky-eff,
.list-gantt-table thead th.gantt-sticky-planned,
.list-gantt-table thead th.gantt-sticky-actual {
  text-align: right;
}

.list-gantt-table tbody tr.gantt-row--base td.gantt-cell,
.list-gantt-table tbody tr.gantt-row--alt td.gantt-cell {
  background: #fff;
}

.list-gantt-table tbody td {
  color: var(--c-text-h);
  font-weight: 400;
}

.list-gantt-table tbody tr.gantt-row--alt td {
  background: #fcfdff;
}

.list-gantt-table tbody tr:hover td {
  background: #f1f7ff;
}

/* 実績あり or 過去日の日別セル：極めて薄いグレー（行の白指定より優先） */
.list-gantt-table tbody tr.gantt-row--base td.gantt-cell.gantt-cell--tone,
.list-gantt-table tbody tr.gantt-row--alt td.gantt-cell.gantt-cell--tone {
  background-color: #f5f5f5;
}

.list-gantt-table tbody tr:hover td.gantt-cell.gantt-cell--tone {
  background-color: #e8ecf2;
}

.list-gantt-table tbody tr.gantt-row--group-start td {
  border-top: 2px solid #bfdbfe;
}

.gantt-group-row td {
  background: #e2e8f0;
  color: var(--c-text-h);
  font-weight: 700;
  border-top: 2px solid #94a3b8;
}

/* グループ行：列クラス（能率・計画・実績は右寄せ）を上書きしない */
.gantt-group-row .gantt-sticky-line,
.gantt-group-row .gantt-sticky-name {
  text-align: left;
}

.gantt-group-row .gantt-sticky-order {
  text-align: center;
}

.gantt-group-row .gantt-sticky-eff,
.gantt-group-row .gantt-sticky-planned,
.gantt-group-row .gantt-sticky-actual {
  text-align: right;
}

.list-gantt-table tbody tr.gantt-group-row .gantt-sticky {
  background: #e2e8f0 !important;
}

.list-gantt-table tbody tr.gantt-group-row:hover .gantt-sticky {
  background: #d8dee8 !important;
}

.gantt-group-cell {
  vertical-align: middle;
}

.gantt-group-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.25;
  font-weight: 800;
}

.gantt-group-num {
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  font-weight: 700;
}

.gantt-group-date-cell {
  background: #e2e8f0;
  padding: 0;
}

.gantt-sticky {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
}

.list-gantt-table thead .gantt-sticky {
  z-index: 4;
}

.gantt-sticky-line {
  left: 0;
  width: var(--gl-line);
  min-width: var(--gl-line);
  max-width: var(--gl-line);
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  color: var(--c-text-h);
}

.gantt-line-empty {
  color: transparent;
}

.gantt-sticky-order {
  left: var(--gl-line);
  width: var(--gl-order);
  min-width: var(--gl-order);
  max-width: var(--gl-order);
  text-align: center;
}

.gantt-sticky-name {
  left: calc(var(--gl-line) + var(--gl-order));
  width: var(--gl-name);
  min-width: var(--gl-name);
  max-width: var(--gl-name);
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--c-text-h);
  font-weight: 400;
}

.gantt-sticky-eff {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name));
  width: var(--gl-eff);
  min-width: var(--gl-eff);
  max-width: var(--gl-eff);
  text-align: right;
  color: var(--c-text-h);
  font-weight: 400;
}

.gantt-sticky-planned {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name) + var(--gl-eff));
  width: var(--gl-plan);
  min-width: var(--gl-plan);
  max-width: var(--gl-plan);
  text-align: right;
  color: var(--c-text-h);
  font-weight: 400;
}

.gantt-sticky-actual {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name) + var(--gl-eff) + var(--gl-plan));
  width: var(--gl-act);
  min-width: var(--gl-act);
  max-width: var(--gl-act);
  text-align: right;
  color: var(--c-text-h);
  font-weight: 400;
}

.gantt-name {
  font-weight: 400;
  color: var(--c-text-h);
}

.gantt-date-col {
  min-width: 54px;
  width: 54px;
}

.gantt-date-text {
  font-size: var(--fs-xs);
  font-weight: 650;
}

.gantt-wd-text {
  font-size: var(--fs-xs);
  color: var(--c-text-s);
}

.list-gantt-table thead .gantt-date-col.is-weekend .gantt-date-text,
.list-gantt-table thead .gantt-date-col.is-weekend .gantt-wd-text {
  color: #dc2626;
}

.list-gantt-table thead .gantt-date-col.is-today {
  background: linear-gradient(180deg, #fff3d4 0%, #ffeab0 100%);
}

.gantt-cell {
  width: 54px;
  min-width: 54px;
  max-width: 54px;
  text-align: left;
  padding: 2px 4px;
  vertical-align: middle;
}

.gantt-cell-markers {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 2px;
  min-height: 12px;
  width: 100%;
}

.gantt-seg {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  line-height: 1.15;
  max-width: 100%;
}

.gantt-seg-val {
  font-size: var(--fs-xs);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  color: var(--c-text-h);
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.gantt-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.12);
}

.gantt-dot--plan {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}

.gantt-dot--actual {
  background: linear-gradient(135deg, #10b981, #059669);
}

.gantt-dot--remain {
  background: linear-gradient(135deg, #a78bfa, #7c3aed);
}

.list-gantt-table tbody tr:hover .gantt-sticky {
  background: #f1f7ff !important;
}
</style>
