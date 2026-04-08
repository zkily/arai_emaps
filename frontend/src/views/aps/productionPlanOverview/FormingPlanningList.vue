<template>
  <div class="forming-plan-list-page">
    <div class="plan-hd">
      <h2 class="plan-hd-title">成型計画一覧</h2>
      <p class="plan-hd-sub">
        工程・対象月を指定し、当該月に期間が重なる APS 製造指示を<strong>日別ガント</strong>で表示します（計画／実績／残）。編集は「成型計画作成」でラインを選んで行ってください。
      </p>
    </div>

    <div class="plan-card filter-card">
      <el-form :inline="true" label-position="left" class="filter-form">
        <el-form-item label="対象月" required>
          <el-date-picker
            v-model="productionMonth"
            type="month"
            value-format="YYYY-MM"
            placeholder="YYYY-MM"
            style="width: 140px"
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
          <el-button type="primary" :loading="loading" :disabled="!canSearch" @click="loadSchedules">
            検索
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="searched" v-loading="loading" class="plan-card result-card">
      <el-tabs v-model="activeResultTab" class="result-tabs">
        <el-tab-pane label="ガント（日別）" name="gantt">
          <div class="gantt-legend-bar">
            <span class="legend-item"><span class="legend-dot legend-dot--plan" />計画</span>
            <span class="legend-item"><span class="legend-dot legend-dot--actual" />実績</span>
            <span class="legend-item"><span class="legend-dot legend-dot--remain" />残</span>
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
              <tbody>
                <tr
                  v-for="(row, gIdx) in ganttRows"
                  :key="row.id"
                  :class="[
                    'gantt-row',
                    productPaletteClass(row),
                    gIdx % 2 === 1 ? 'gantt-row--alt' : 'gantt-row--base',
                    { 'gantt-row--group-start': isGanttGroupStart(gIdx) },
                  ]"
                >
                  <td class="gantt-sticky gantt-sticky-line" :title="row.lineLabel">{{ row.lineLabel }}</td>
                  <td class="gantt-sticky gantt-sticky-order">{{ row.order_no ?? '—' }}</td>
                  <td class="gantt-sticky gantt-sticky-name gantt-name">{{ row.item_name }}</td>
                  <td class="gantt-sticky gantt-sticky-eff">{{ formatEfficiencyRatePiecesPerH(row.efficiency_rate) }}</td>
                  <td class="gantt-sticky gantt-sticky-planned">{{ row.planned_process_qty }}</td>
                  <td class="gantt-sticky gantt-sticky-actual">{{ periodActualForRow(row).toLocaleString() }}</td>
                  <td
                    v-for="d in ganttDates"
                    :key="d"
                    class="gantt-cell"
                    :class="ganttCellClass(row, d)"
                    :title="ganttCellTitle(row, d)"
                  >
                    <div
                      v-if="(row.daily[d] || 0) > 0 || (row.actual_daily?.[d] || 0) > 0 || (row.remaining_daily?.[d] || 0) > 0"
                      class="gantt-layered"
                    >
                      <span class="gantt-layer gantt-layer--plan"><b class="gl-lbl">計</b>{{ row.daily[d] || 0 }}</span>
                      <span class="gantt-layer gantt-layer--actual"><b class="gl-lbl">実</b>{{ row.actual_daily?.[d] || 0 }}</span>
                      <span class="gantt-layer gantt-layer--remain"><b class="gl-lbl">残</b>{{ row.remaining_daily?.[d] || 0 }}</span>
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
                <el-table-column :label="'品名'" min-width="180" show-overflow-tooltip>
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
              <el-table-column prop="lineLabel" label="設備" width="130" show-overflow-tooltip />
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
import { ElMessage } from 'element-plus'
import {
  fetchSchedules,
  fetchSchedulingGrid,
  type ScheduleOut,
  type ScheduleGridRow,
} from '@/api/aps'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'

defineOptions({ name: 'FormingPlanningList' })

type GanttListRow = ScheduleGridRow & { lineLabel: string; line_id: number }

const DEFAULT_MONTH = '2026-04'
const productionMonth = ref<string>(DEFAULT_MONTH)
const selectedProcessCd = ref<string>('')
const processOptions = ref<ProcessItem[]>([])
const loadingProcesses = ref(false)
const rows = ref<ScheduleOut[]>([])
const loading = ref(false)
const searched = ref(false)
const activeResultTab = ref<'gantt' | 'table' | 'utilization'>('gantt')
const ganttDates = ref<string[]>([])
const ganttRows = ref<GanttListRow[]>([])
const lineCalendarHoursMap = ref<Record<number, Record<string, number>>>({})
const lineDefaultHoursMap = ref<Record<number, number>>({})

const canSearch = computed(
  () => !!(productionMonth.value && (selectedProcessCd.value || '').trim()),
)

const displayRangeText = computed(() => {
  const m = (productionMonth.value || '').trim()
  if (!m) return '—'
  return `${firstDayOfMonthIso(m)} 〜 ${lastDayOfMonthIso(m)}`
})

const tableGroups = computed(() => {
  const groups: Array<{ lineLabel: string; rows: ScheduleOut[] }> = []
  for (const row of rows.value) {
    const lineLabel = formatLine(row)
    const last = groups[groups.length - 1]
    if (!last || last.lineLabel !== lineLabel) {
      groups.push({ lineLabel, rows: [row] })
    } else {
      last.rows.push(row)
    }
  }
  return groups
})

const monthlyStatDates = computed(() => {
  const allDates = [...ganttDates.value].sort((a, b) => a.localeCompare(b))
  if (allDates.length === 0) return [] as string[]
  const month = (productionMonth.value || '').trim()
  if (!month) return allDates
  const start = firstDayOfMonthIso(month)
  const monthEnd = lastDayOfMonthIso(month)
  const today = todayIso.value
  let end = monthEnd
  if (today >= start && today <= monthEnd) end = today
  if (today < start) return [] as string[]
  return allDates.filter((d) => d >= start && d <= end)
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

function firstDayOfMonthIso(month: string): string {
  return `${month}-01`
}

function lastDayOfMonthIso(month: string): string {
  const [y, m] = month.split('-').map((v) => Number(v))
  if (!Number.isFinite(y) || !Number.isFinite(m) || m < 1 || m > 12) return `${month}-28`
  const d = new Date(y, m, 0)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mm}-${dd}`
}

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

function formatLine(row: ScheduleOut): string {
  const code = (row.line_code || '').trim()
  const name = (row.line_name || '').trim()
  if (code && name) return `${code} — ${name}`
  return code || name || `ID ${row.line_id}`
}

/** 設備表示名 → 順位 → id の昇順（一覧・ガント共通） */
function compareByLineThenOrder(a: ScheduleOut, b: ScheduleOut): number {
  const lineCmp = formatLine(a).localeCompare(formatLine(b), 'ja')
  if (lineCmp !== 0) return lineCmp
  const oa = a.order_no ?? 1_000_000 + a.id
  const ob = b.order_no ?? 1_000_000 + b.id
  if (oa !== ob) return oa - ob
  return a.id - b.id
}

/** 設備グループ先頭行の上に余白（先頭行は除く） */
function isGanttGroupStart(index: number): boolean {
  if (index <= 0) return false
  const cur = ganttRows.value[index]
  const prev = ganttRows.value[index - 1]
  return cur.lineLabel !== prev.lineLabel
}

function scheduleTableRowClassName({
  rowIndex,
}: {
  row: ScheduleOut
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
    <div class="meta">対象月：${escHtml(productionMonth.value || '—')}　工程：${escHtml(selectedProcessLabel())}　印刷日時：${escHtml(printedAt)}</div>
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

function tableActual(row: ScheduleOut): number {
  const target = ganttRows.value.find((g) => g.id === row.id)
  if (!target) return 0
  return periodActualForRow(target)
}

function tableRemaining(row: ScheduleOut): number {
  const planned = Number(row.planned_process_qty ?? 0)
  const remain = planned - tableActual(row)
  return remain > 0 ? remain : 0
}

function tableProgress(row: ScheduleOut): string {
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

function tableStatusKind(row: ScheduleOut): 'done' | 'ongoing' | 'pending' {
  const today = todayLocalStart()
  const start = parseLocalDay(row.start_date)
  const end = parseLocalDay(row.end_date)
  if (end && end < today) return 'done'
  if (start && end && start <= today && today <= end) return 'ongoing'
  return 'pending'
}

function tableStatusLabel(row: ScheduleOut): string {
  const map: Record<'done' | 'ongoing' | 'pending', string> = {
    done: '生産済',
    ongoing: '生産中',
    pending: '準備中',
  }
  return map[tableStatusKind(row)]
}

async function loadSchedules() {
  if (!canSearch.value) {
    ElMessage.warning('対象月と工程を選択してください')
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
    const month = productionMonth.value
    const sd = firstDayOfMonthIso(month)
    const ed = lastDayOfMonthIso(month)
    const [scheduleList, grid] = await Promise.all([
      fetchSchedules({ processCd: pc, productionMonth: month }),
      fetchSchedulingGrid(sd, ed, undefined, pc),
    ])
    const listRaw = Array.isArray(scheduleList) ? scheduleList : []
    rows.value = [...listRaw].sort(compareByLineThenOrder)
    ganttDates.value = Array.isArray(grid.dates) ? grid.dates : []
    const calendarMap: Record<number, Record<string, number>> = {}
    const defaultMap: Record<number, number> = {}
    for (const block of grid.blocks || []) {
      calendarMap[block.line_id] = block.calendar || {}
      defaultMap[block.line_id] = Number(block.default_work_hours ?? 0)
    }
    lineCalendarHoursMap.value = calendarMap
    lineDefaultHoursMap.value = defaultMap

    const allowed = new Set(rows.value.map((r) => r.id))
    const lineLabelById = new Map<number, string>()
    for (const s of rows.value) {
      if (!lineLabelById.has(s.line_id)) lineLabelById.set(s.line_id, formatLine(s))
    }

    const flat: GanttListRow[] = []
    for (const block of grid.blocks || []) {
      const label = lineLabelById.get(block.line_id) ?? block.line_code ?? `ID ${block.line_id}`
      for (const r of block.rows || []) {
        if (!allowed.has(r.id)) continue
        flat.push({ ...r, lineLabel: label, line_id: block.line_id })
      }
    }
    flat.sort((a, b) => {
      const lc = a.lineLabel.localeCompare(b.lineLabel, 'ja')
      if (lc !== 0) return lc
      const oa = a.order_no ?? 1_000_000 + a.id
      const ob = b.order_no ?? 1_000_000 + b.id
      if (oa !== ob) return oa - ob
      return a.id - b.id
    })
    ganttRows.value = flat
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

function formatEfficiencyRatePiecesPerH(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Number(v)
  const s = n % 1 === 0 ? String(Math.round(n)) : n.toFixed(1)
  return `${s}本/H`
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

function ganttCellClass(row: ScheduleGridRow, d: string): Record<string, boolean> {
  const qty = row.daily[d] || 0
  const actual = row.actual_daily?.[d] || 0
  const remain = row.remaining_daily?.[d] || 0
  const active = qty > 0 || actual > 0 || remain > 0
  const inRange = row.start_date && row.end_date && d >= row.start_date && d <= row.end_date
  return {
    'gantt-active': active,
    'gantt-has-actual': actual > 0,
    'gantt-range': !!inRange && !active,
    'is-weekend': isWeekend(d),
    'is-today': isToday(d),
  }
}

function productPaletteClass(row: ScheduleGridRow): string {
  const base = (row.item_name || '').trim()
  if (!base) return 'gpc-0'
  let h = 0
  for (let i = 0; i < base.length; i += 1) {
    h = ((h << 5) - h + base.charCodeAt(i)) | 0
  }
  return `gpc-${Math.abs(h) % 10}`
}

function ganttCellTitle(row: ScheduleGridRow, d: string): string {
  const planned = row.daily[d] || 0
  const actual = row.actual_daily?.[d] || 0
  const remain = row.remaining_daily?.[d] || 0
  if (planned > 0 || actual > 0 || remain > 0) {
    return `${row.item_name}: 計画 ${planned} / 実績 ${actual} / 残 ${remain}`
  }
  return ''
}

function periodActualForRow(row: ScheduleGridRow): number {
  const m = row.actual_daily || {}
  const dates1 = ganttDates.value.length > 0 ? ganttDates.value : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}
</script>

<style scoped>
.forming-plan-list-page {
  --font-sans: YuGothic, system-ui, -apple-system, 'Segoe UI', 'Yu Gothic UI', 'Meiryo',
    'Hiragino Sans', Arial, sans-serif;
  --font-mono: Consolas, 'Courier New', monospace;
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
  /* 左 sticky 列幅（設備列を広めに） */
  --gl-line: 168px;
  --gl-order: 44px;
  --gl-name: 132px;
  --gl-eff: 70px;
  --gl-plan: 56px;
  --gl-act: 72px;

  padding: 12px 14px;
  background: var(--c-bg);
  min-height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plan-hd {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  padding: 2px 2px 0;
}
.plan-hd-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text-h);
  margin: 0;
  letter-spacing: 0.3px;
}
.plan-hd-sub {
  font-size: 12px;
  color: var(--c-text-s);
  margin: 0;
  line-height: 1.5;
  max-width: 980px;
}
.plan-hd-sub strong {
  font-weight: 600;
  color: #64748b;
}

.plan-card {
  background: var(--c-surface);
  border-radius: 12px;
  padding: 12px 12px;
  border: 1px solid var(--c-border-l);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06), 0 10px 24px rgba(15, 23, 42, 0.05);
}

.filter-card {
  padding: 10px 10px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 1) 0%, rgba(248, 251, 255, 1) 100%);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}
.filter-form :deep(.el-form-item__label) {
  font-size: var(--fs-s);
  color: var(--c-text-m);
  font-weight: 700;
}
.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-select__wrapper) {
  border-radius: 10px;
}
.filter-form :deep(.el-button) {
  border-radius: 10px;
  font-weight: 800;
  letter-spacing: 0.02em;
  padding-left: 14px;
  padding-right: 14px;
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
}
.result-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--c-accent) 0%, var(--c-accent-2) 100%);
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

.plan-sec-hd {
  font-size: 13px;
  font-weight: 700;
  color: #1f2329;
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
  font-size: 11px;
  font-weight: 600;
  background: linear-gradient(90deg, var(--c-accent) 0%, var(--c-accent-2) 100%);
  color: #fff;
  padding: 1px 7px;
  border-radius: 10px;
  line-height: 18px;
}

.line-cell {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
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
  font-size: 12px;
  color: #0f172a;
}
.qty-cell--actual {
  color: #059669;
}

.date-cell {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11.5px;
  font-weight: 700;
  color: #475569;
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
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #334155;
  background: linear-gradient(180deg, #edf3fb 0%, #e6eef9 100%);
  border-bottom: 1px solid #d4deeb;
}

.schedule-list-table {
  width: 100%;
  font-size: 12px;
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
  font-size: 12px;
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
  font-size: 12px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

/* ── Gantt（日別）：浅色分区 + 清晰字体 + 现代表格 ── */
.list-gantt-scroll {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid var(--c-border-l);
  background: linear-gradient(180deg, #f5f9ff 0%, #fafcfe 45%, #f8fafc 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}
.list-gantt-scroll::-webkit-scrollbar {
  height: 8px;
}
.list-gantt-scroll::-webkit-scrollbar-track {
  background: #e8eef6;
  border-radius: 6px;
}
.list-gantt-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #c7d2e0, #a8b6c9);
  border-radius: 6px;
  border: 2px solid #e8eef6;
}
.list-gantt-table {
  border-collapse: collapse;
  font-size: 12px;
  line-height: 1.35;
  font-family: var(--font-sans);
  white-space: nowrap;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
.list-gantt-table th,
.list-gantt-table td {
  border: 1px solid #e2e8f0;
  padding: 0 6px;
  text-align: center;
  height: 30px;
  vertical-align: middle;
}
.list-gantt-table thead th {
  background: linear-gradient(180deg, #eef4fc 0%, #e3ecf8 100%);
  font-weight: 800;
  color: #334155;
  font-size: 11.5px;
  letter-spacing: 0.04em;
  border-bottom: 2px solid #c7d5ea;
}
.list-gantt-table tbody tr {
  transition: background 0.15s ease;
}
.list-gantt-table tbody tr.gantt-row--base td.gantt-cell {
  background-color: #fafcfe;
}
.list-gantt-table tbody tr.gantt-row--alt td.gantt-cell {
  background-color: #f3f6fb;
}
.list-gantt-table tbody tr.gantt-row--group-start td {
  border-top: 10px solid #e2ebf8;
}

.gantt-sticky {
  position: sticky;
  background: #f5f9ff;
  background-color: #f5f9ff !important;
  z-index: 100;
  text-align: left;
  border-right: 0 !important;
  box-sizing: border-box;
  background-clip: padding-box;
  overflow: hidden;
  box-shadow: inset -1px 0 0 #d5deeb, 4px 0 10px rgba(15, 23, 42, 0.06);
}
.list-gantt-table tbody tr.gantt-row--alt .gantt-sticky {
  background: #edf2fb !important;
  background-color: #edf2fb !important;
  box-shadow: inset -1px 0 0 #d5deeb, 4px 0 10px rgba(15, 23, 42, 0.05);
}
.list-gantt-table thead .gantt-sticky {
  background: linear-gradient(180deg, #e8f0fb 0%, #dce8f6 100%) !important;
  background-color: #e8f0fb !important;
  z-index: 110;
  box-shadow: inset -1px 0 0 #c8d7ea, 4px 0 12px rgba(15, 23, 42, 0.07);
}
.gantt-sticky-line {
  left: 0;
  width: var(--gl-line);
  min-width: var(--gl-line);
  max-width: var(--gl-line);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 700;
  color: #334155;
  font-size: 12px;
}
.gantt-sticky-order {
  left: var(--gl-line);
  width: var(--gl-order);
  min-width: var(--gl-order);
  max-width: var(--gl-order);
  text-align: center;
  color: #64748b;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}
.gantt-sticky-name {
  left: calc(var(--gl-line) + var(--gl-order));
  width: var(--gl-name);
  min-width: var(--gl-name);
  max-width: var(--gl-name);
  text-align: left;
  padding-left: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gantt-sticky-eff {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name));
  width: var(--gl-eff);
  min-width: var(--gl-eff);
  max-width: var(--gl-eff);
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 12px;
  font-family: var(--font-mono);
  color: #475569;
}
.gantt-sticky-planned {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name) + var(--gl-eff));
  width: var(--gl-plan);
  min-width: var(--gl-plan);
  max-width: var(--gl-plan);
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 800;
  font-size: 12px;
  font-family: var(--font-mono);
  color: #0f172a;
}
.gantt-sticky-actual {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name) + var(--gl-eff) + var(--gl-plan));
  width: var(--gl-act);
  min-width: var(--gl-act);
  max-width: var(--gl-act);
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 800;
  font-size: 12px;
  font-family: var(--font-mono);
  color: #047857;
  box-shadow: inset -1px 0 0 #b8cadc, 6px 0 14px rgba(15, 23, 42, 0.08);
}
.list-gantt-table thead .gantt-sticky-actual {
  box-shadow: inset -1px 0 0 #b8cadc, 6px 0 14px rgba(15, 23, 42, 0.08);
}
.gantt-name {
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.01em;
  font-size: 12px;
}

.gantt-date-col {
  min-width: 46px;
  padding: 5px 2px 4px !important;
}
.gantt-date-text {
  font-size: 11.5px;
  font-weight: 800;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
  color: #334155;
}
.gantt-wd-text {
  font-size: 10px;
  color: #64748b;
  margin-top: 2px;
  font-weight: 700;
  letter-spacing: 0.06em;
}
.list-gantt-table thead .gantt-date-col.is-weekend {
  background: linear-gradient(180deg, #fdf2f8 0%, #fce7f3 100%) !important;
}
.gantt-date-col.is-weekend .gantt-date-text,
.gantt-date-col.is-weekend .gantt-wd-text {
  color: #be185d;
  font-weight: 800;
}
.gantt-date-col.is-today {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border-bottom: 2px solid #f59e0b !important;
}

.gantt-cell {
  min-width: 46px;
  height: 38px;
  transition:
    background 0.12s ease,
    box-shadow 0.12s ease;
}
.list-gantt-table tbody td.gantt-cell {
  text-align: left;
  padding-left: 4px;
}
.gantt-layered {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 1px;
  line-height: 1;
  padding: 2px 0;
}
.gantt-layer {
  font-size: 10.5px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  letter-spacing: 0.02em;
}
.gantt-layer--plan {
  color: rgba(255, 255, 255, 0.98);
  font-weight: 900;
  font-size: 11px;
}
.gantt-layer--actual {
  color: rgba(255, 255, 255, 0.9);
  font-size: 10px;
  font-weight: 700;
}
.gantt-layer--remain {
  color: rgba(255, 255, 255, 0.93);
  font-size: 10px;
  font-weight: 700;
}
.gl-lbl {
  font-weight: 600;
  opacity: 0.88;
  margin-right: 2px;
  font-size: 9.5px;
  font-family: var(--font-sans);
}
.gantt-cell.is-weekend:not(.gantt-active):not(.gantt-has-actual) {
  background-color: #fdf2f8 !important;
  opacity: 1;
}
.gantt-cell.is-today:not(.gantt-active):not(.gantt-has-actual) {
  background: linear-gradient(180deg, #fffbeb 0%, #fef9c3 100%) !important;
  box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.2);
}
.gantt-cell.gantt-range {
  background: #e8f0fe !important;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.12);
}
.gantt-cell.gantt-active {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -1px 0 rgba(0, 0, 0, 0.06);
}

.gantt-row.gpc-0 td.gantt-active {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 55%, #2563eb 100%);
  color: #fff;
}
.gantt-row.gpc-1 td.gantt-active {
  background: linear-gradient(135deg, #34d399 0%, #10b981 55%, #059669 100%);
  color: #fff;
}
.gantt-row.gpc-2 td.gantt-active {
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 55%, #7c3aed 100%);
  color: #fff;
}
.gantt-row.gpc-3 td.gantt-active {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 55%, #d97706 100%);
  color: #fff;
}
.gantt-row.gpc-4 td.gantt-active {
  background: linear-gradient(135deg, #f472b6 0%, #ec4899 55%, #db2777 100%);
  color: #fff;
}
.gantt-row.gpc-5 td.gantt-active {
  background: linear-gradient(135deg, #22d3ee 0%, #06b6d4 55%, #0891b2 100%);
  color: #fff;
}
.gantt-row.gpc-6 td.gantt-active {
  background: linear-gradient(135deg, #fb7185 0%, #f43f5e 55%, #e11d48 100%);
  color: #fff;
}
.gantt-row.gpc-7 td.gantt-active {
  background: linear-gradient(135deg, #a3e635 0%, #84cc16 55%, #65a30d 100%);
  color: #fff;
}
.gantt-row.gpc-8 td.gantt-active {
  background: linear-gradient(135deg, #818cf8 0%, #6366f1 55%, #4f46e5 100%);
  color: #fff;
}
.gantt-row.gpc-9 td.gantt-active {
  background: linear-gradient(135deg, #2dd4bf 0%, #14b8a6 55%, #0d9488 100%);
  color: #fff;
}
td.gantt-has-actual {
  background: linear-gradient(135deg, #34d399 0%, #10b981 65%, #059669 100%) !important;
  color: #fff !important;
}

.list-gantt-table tbody tr:hover td.gantt-cell:not(.gantt-active):not(.gantt-has-actual) {
  background-color: #e8f0fe !important;
}
.list-gantt-table tbody tr:hover td.gantt-cell.is-weekend:not(.gantt-active):not(.gantt-has-actual) {
  background-color: #fce7f3 !important;
}
.list-gantt-table tbody tr:hover td.gantt-cell.is-today:not(.gantt-active):not(.gantt-has-actual) {
  background: linear-gradient(180deg, #fff7d6 0%, #fef08a 55%) !important;
}
.list-gantt-table tbody tr.gantt-row--base:hover .gantt-sticky {
  background-color: #e8f0fe !important;
}
.list-gantt-table tbody tr.gantt-row--alt:hover .gantt-sticky {
  background-color: #dbe7fd !important;
}
</style>
