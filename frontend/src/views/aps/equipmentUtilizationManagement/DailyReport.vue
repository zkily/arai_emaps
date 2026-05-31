<template>
  <div class="daily-report-page">
    <el-card class="daily-report-card" shadow="hover" :body-style="{ padding: '10px 12px 12px' }">
      <template #header>
        <div class="daily-report-head">
          <div class="daily-report-head__main">
            <h3 class="daily-report-head__title">
              <span class="daily-report-head__title-inner">
                <el-icon class="daily-report-head__title-icon"><Document /></el-icon>
                日別設備計画表
              </span>
            </h3>
            <p class="daily-report-head__desc">日付×設備ごとの排産計画をカレンダー形式で一覧表示します。</p>
          </div>
        </div>
      </template>

      <div class="toolbar toolbar--panel no-print">
        <el-form :inline="true" label-position="left" size="small" class="toolbar__form">
          <el-form-item class="toolbar__item">
            <template #label>
              <span class="toolbar__lbl"><el-icon><Calendar /></el-icon>期間</span>
            </template>
            <div class="toolbar__range-row">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="〜"
                start-placeholder="開始"
                end-placeholder="終了"
                value-format="YYYY-MM-DD"
                class="toolbar__daterange"
              />
              <el-button
                type="primary"
                plain
                size="small"
                class="dr-btn-month"
                :icon="Calendar"
                @click="applyThisMonthRange"
              >
                今月
              </el-button>
            </div>
          </el-form-item>
          <el-form-item class="toolbar__item">
            <template #label>
              <span class="toolbar__lbl"><el-icon><Operation /></el-icon>工程</span>
            </template>
            <el-select
              v-model="selectedProcessCd"
              clearable
              filterable
              placeholder="全工程"
              class="toolbar__select-process"
              @change="handleProcessChange"
            >
              <el-option
                v-for="p in matrixProcessOptions"
                :key="p.process_cd"
                :label="processOptionLabel(p)"
                :value="p.process_cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item class="toolbar__item" required>
            <template #label>
              <span class="toolbar__lbl"><el-icon><Monitor /></el-icon>設備</span>
            </template>
            <el-select
              v-model="selectedLineId"
              placeholder="設備を選択"
              filterable
              class="toolbar__select-line"
            >
              <el-option
                v-for="line in lines"
                :key="line.id"
                :value="line.id"
                :label="lineOptionLabel(line)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label-width="0" class="toolbar__item toolbar__item--actions">
            <el-button
              type="primary"
              size="small"
              class="dr-btn-fetch"
              :icon="Refresh"
              :loading="loading"
              :disabled="selectedLineId == null"
              @click="loadReport"
            >
              取得
            </el-button>
            <el-button type="warning" plain size="small" class="dr-btn-print" :icon="Printer" @click="printReport">
              印刷
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-loading="loading" class="report-body">
        <div v-if="calendarViews.length === 0" class="empty">
          <el-icon class="empty__icon"><Calendar /></el-icon>
          <p class="empty__text">期間を指定してください</p>
        </div>

        <template v-else>
          <p v-if="groupedData.length === 0 && !loading" class="calendar-hint no-print">
            「取得」でこの期間の計画を読み込みます（未取得時は日付のみ表示）
          </p>

          <div class="calendar-print-root">
            <div class="print-summary print-only">
              <div class="print-summary__line">
                <span class="print-summary__title">{{ printPeriodTitle }}</span>
                <span class="print-summary__meta">設備名：{{ linePrintLabel }}</span>
                <span class="print-summary__meta">稼働時間：{{ summaryAvailHoursText }}</span>
                <span class="print-summary__meta">計画数：{{ summaryPlannedTotal }}</span>
                <span class="print-summary__meta">実績数：{{ summaryActualTotal }}</span>
              </div>
            </div>
            <div class="calendar-shell">
              <section v-for="cal in calendarViews" :key="cal.yearMonth" class="calendar-month">
                <h4
                  class="calendar-month__title"
                  :class="{ 'calendar-month__title--dup-summary': calendarViews.length === 1 }"
                >{{ cal.title }}</h4>
                <div class="calendar-weekday-row">
                  <span
                    v-for="(w, wi) in weekdayLabels"
                    :key="w"
                    class="calendar-weekday-cell"
                    :class="{ 'calendar-weekday-cell--weekend': wi === 0 || wi === 6 }"
                  >{{ w }}</span>
                </div>
                <div class="calendar-weeks">
                  <div v-for="(week, wi) in cal.weeks" :key="wi" class="calendar-week">
                    <div
                      v-for="(cell, ci) in week"
                      :key="ci"
                      class="calendar-day"
                      :class="{
                        'calendar-day--pad': cell.pad,
                        'calendar-day--out-range': cell.dateStr && !cell.inSelectedRange,
                        'calendar-day--today': cell.isToday,
                        'calendar-day--weekend':
                          !cell.pad && cell.dateStr && isWeekendDate(cell.dateStr),
                      }"
                    >
                      <template v-if="!cell.pad && cell.dateStr">
                        <div class="calendar-day__hd">
                          <span class="calendar-day__num">{{ cell.dayNum }}</span>
                          <span class="calendar-day__wd">{{ getWeekday(cell.dateStr) }}</span>
                        </div>
                        <div v-if="cell.group?.lines?.length" class="calendar-day__scroll">
                          <div
                            v-for="lineGroup in cell.group.lines"
                            :key="lineGroup.line_code"
                            class="line-block line-block--calendar"
                          >
                            <div class="line-header line-header--calendar-row">
                              <span class="line-header__tags">
                                <el-tag
                                  v-if="lineGroup.available_hours != null"
                                  size="small"
                                  type="info"
                                  effect="plain"
                                  round
                                >
                                  {{ lineGroup.available_hours.toFixed(1) }}h
                                </el-tag>
                                <el-tag size="small" type="success" effect="plain" round>
                                  合計 {{ lineGroup.total_qty }}
                                </el-tag>
                              </span>
                            </div>
                            <el-table :data="lineGroup.rows" size="small" border stripe class="report-table">
                              <el-table-column prop="item_name" label="品名" min-width="58" show-overflow-tooltip />
                              <el-table-column prop="planned_qty" label="計画" width="47" align="right" />
                              <el-table-column prop="actual_qty" label="実績" width="52" align="right" />
                            </el-table>
                          </div>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </template>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, nextTick, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Calendar, Operation, Monitor, Refresh, Printer } from '@element-plus/icons-vue'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import {
  fetchLines,
  fetchDailyEquipmentReport,
  type ProductionLine,
  type DailyEquipmentReportRow,
} from '@/api/aps'

interface LineBlock {
  line_code: string
  /** 表示用：machines.machine_name（無ければ line_code） */
  line_label: string
  available_hours: number | null
  total_qty: number
  rows: DailyEquipmentReportRow[]
}

function reportLineDisplayLabel(r: DailyEquipmentReportRow): string {
  const nm = (r.line_name || '').trim()
  return nm || (r.line_code || '').trim() || '—'
}

interface DateGroup {
  date: string
  lines: LineBlock[]
}

interface CalendarDayCell {
  pad: boolean
  dateStr: string | null
  dayNum: number | null
  inSelectedRange: boolean
  group: DateGroup | null
  isToday: boolean
}

interface CalendarMonthView {
  title: string
  yearMonth: string
  weeks: CalendarDayCell[][]
}

const weekdayLabels = ['日', '月', '火', '水', '木', '金', '土'] as const

function dayInRange(d: string, start: string, end: string): boolean {
  const x = dayjs(d)
  return !x.isBefore(dayjs(start), 'day') && !x.isAfter(dayjs(end), 'day')
}

function chunkArray<T>(arr: T[], size: number): T[][] {
  const out: T[][] = []
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size))
  return out
}

function padCalendarCell(): CalendarDayCell {
  return {
    pad: true,
    dateStr: null,
    dayNum: null,
    inSelectedRange: false,
    group: null,
    isToday: false,
  }
}

function buildMonthCalendar(
  year: number,
  month: number,
  rangeStart: string,
  rangeEnd: string,
  groupsByDate: Map<string, DateGroup>,
): CalendarMonthView {
  const ym = dayjs(`${year}-${String(month).padStart(2, '0')}-01`)
  const daysInMonth = ym.daysInMonth()
  const lead = ym.day()

  const cells: CalendarDayCell[] = []
  for (let i = 0; i < lead; i++) cells.push(padCalendarCell())

  for (let d = 1; d <= daysInMonth; d++) {
    const cur = ym.date(d)
    const ds = cur.format('YYYY-MM-DD')
    const inR = dayInRange(ds, rangeStart, rangeEnd)
    cells.push({
      pad: false,
      dateStr: ds,
      dayNum: d,
      inSelectedRange: inR,
      group: inR ? groupsByDate.get(ds) ?? null : null,
      isToday: ds === dayjs().format('YYYY-MM-DD'),
    })
  }

  while (cells.length % 7 !== 0) cells.push(padCalendarCell())

  return {
    title: `${year}年${month}月`,
    yearMonth: `${year}-${String(month).padStart(2, '0')}`,
    weeks: chunkArray(cells, 7),
  }
}

/** プルダウン：設備名のみ（空ならラインコード） */
function lineOptionLabel(line: ProductionLine): string {
  const name = (line.line_name || '').trim()
  return name || (line.line_code || '').trim() || '—'
}

/** プルダウン：工程名のみ（空なら CD） */
function processOptionLabel(p: ProcessItem): string {
  const nm = (p.process_name || '').trim()
  const cd = (p.process_cd || '').trim()
  return nm || cd || '—'
}

/** 設備一覧を絞り込む工程（稼働時間表と同順・同セット） */
const REPORT_PROCESS_ORDER = ['KT01', 'KT02', 'KT04', 'KT07', 'KT05'] as const
const REPORT_PROCESS_SET = new Set<string>(REPORT_PROCESS_ORDER)

const processOptions = ref<ProcessItem[]>([])
const matrixProcessOptions = computed(() => {
  const order = REPORT_PROCESS_ORDER
  const list = processOptions.value.filter((p) => REPORT_PROCESS_SET.has((p.process_cd || '').trim()))
  const rank = (cd: string) => {
    const i = order.indexOf(cd as (typeof REPORT_PROCESS_ORDER)[number])
    return i >= 0 ? i : 999
  }
  return [...list].sort(
    (a, b) => rank((a.process_cd || '').trim()) - rank((b.process_cd || '').trim()),
  )
})

/** 既定：成型（KT04）。空＝全工程（fetchLines 無引数） */
const DEFAULT_PROCESS_CD = 'KT04'
/** 既定設備表示名／コード（マスタに無い場合は先頭設備） */
const DEFAULT_LINE_LABEL = '成型01'

const selectedProcessCd = ref<string | undefined>(DEFAULT_PROCESS_CD)
const lines = ref<ProductionLine[]>([])
const selectedLineId = ref<number | null>(null)
const dateRange = ref<[string, string]>([
  dayjs().startOf('month').format('YYYY-MM-DD'),
  dayjs().endOf('month').format('YYYY-MM-DD'),
])
const loading = ref(false)
const groupedData = ref<DateGroup[]>([])

const calendarViews = computed(() => {
  const [rs, re] = dateRange.value || []
  if (!rs || !re) return []
  const map = new Map<string, DateGroup>()
  for (const g of groupedData.value) map.set(g.date, g)

  const views: CalendarMonthView[] = []
  let cur = dayjs(rs).startOf('month')
  const endMonth = dayjs(re).startOf('month')
  while (cur.isBefore(endMonth, 'month') || cur.isSame(endMonth, 'month')) {
    views.push(buildMonthCalendar(cur.year(), cur.month() + 1, rs, re, map))
    cur = cur.add(1, 'month')
  }
  return views
})

/** 印刷ヘッダー用：期間タイトル（同一月なら「2026年5月」） */
const printPeriodTitle = computed(() => {
  const [s, e] = dateRange.value || []
  if (!s || !e) return ''
  const ds = dayjs(s)
  const de = dayjs(e)
  if (ds.isSame(de, 'month')) return `${ds.year()}年${ds.month() + 1}月`
  return `${ds.format('YYYY年M月D日')}〜${de.format('YYYY年M月D日')}`
})

const linePrintLabel = computed(() => {
  const id = selectedLineId.value
  if (id == null) return '—'
  const ln = lines.value.find((l) => l.id === id)
  return ln ? lineOptionLabel(ln) : `ID ${id}`
})

const summaryPlannedTotal = computed(() => {
  let n = 0
  for (const g of groupedData.value) {
    for (const lb of g.lines) {
      for (const r of lb.rows) n += Number(r.planned_qty ?? 0)
    }
  }
  return n
})

const summaryActualTotal = computed(() => {
  let n = 0
  for (const g of groupedData.value) {
    for (const lb of g.lines) {
      for (const r of lb.rows) n += Number(r.actual_qty ?? 0)
    }
  }
  return n
})

const summaryAvailHoursTotal = computed(() => {
  let n = 0
  for (const g of groupedData.value) {
    for (const lb of g.lines) {
      if (lb.available_hours != null) n += Number(lb.available_hours)
    }
  }
  return n
})

const summaryAvailHoursText = computed(() => {
  const v = summaryAvailHoursTotal.value
  return Number.isFinite(v) ? `${v.toFixed(1)} h` : '—'
})

function applyThisMonthRange() {
  dateRange.value = [
    dayjs().startOf('month').format('YYYY-MM-DD'),
    dayjs().endOf('month').format('YYYY-MM-DD'),
  ]
}

async function loadProcessOptions() {
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const data = (res?.data ?? res) as { list?: ProcessItem[] }
    processOptions.value = Array.isArray(data.list) ? data.list : []
  } catch {
    processOptions.value = []
  }
}

function matchesDefaultFormingLine(line: ProductionLine): boolean {
  const name = (line.line_name || '').trim()
  const code = (line.line_code || '').trim()
  return name === DEFAULT_LINE_LABEL || code === DEFAULT_LINE_LABEL
}

/** 一覧に合わせて既定：成型01（無ければ先頭）。既に有効な選択は維持 */
function ensureSelectedLine() {
  if (lines.value.length === 0) {
    selectedLineId.value = null
    return
  }
  if (selectedLineId.value != null && lines.value.some((ln) => ln.id === selectedLineId.value)) {
    return
  }
  const preferred = lines.value.find(matchesDefaultFormingLine)
  selectedLineId.value = preferred?.id ?? lines.value[0]!.id
}

async function loadLinesByProcess() {
  try {
    const pc = (selectedProcessCd.value ?? '').trim()
    const fetched = await fetchLines(pc || undefined)
    lines.value = fetched.filter((ln) => {
      const lineName = String(ln.line_name || '').trim()
      return !lineName.includes('成型他')
    })
    ensureSelectedLine()
  } catch {
    lines.value = []
    selectedLineId.value = null
  }
}

async function handleProcessChange() {
  await loadLinesByProcess()
}

onMounted(async () => {
  await loadProcessOptions()
  await loadLinesByProcess()
})

async function loadReport() {
  if (!dateRange.value?.[0] || !dateRange.value?.[1]) {
    ElMessage.warning('期間を選択してください')
    return
  }
  if (selectedLineId.value == null) {
    ElMessage.warning('設備を選択してください')
    return
  }
  loading.value = true
  try {
    const res = await fetchDailyEquipmentReport(
      dateRange.value[0],
      dateRange.value[1],
      selectedLineId.value,
    )
    const data: DailyEquipmentReportRow[] = res.data || res as any
    groupedData.value = buildGroups(data)
  } catch (e: any) {
    ElMessage.error(e?.message || 'データ取得失敗')
  } finally {
    loading.value = false
  }
}

function buildGroups(rows: DailyEquipmentReportRow[]): DateGroup[] {
  const dateMap = new Map<string, Map<string, LineBlock>>()

  for (const r of rows) {
    if (!dateMap.has(r.schedule_date)) {
      dateMap.set(r.schedule_date, new Map())
    }
    const lineMap = dateMap.get(r.schedule_date)!
    if (!lineMap.has(r.line_code)) {
      lineMap.set(r.line_code, {
        line_code: r.line_code,
        line_label: reportLineDisplayLabel(r),
        available_hours: r.available_hours,
        total_qty: 0,
        rows: [],
      })
    }
    const block = lineMap.get(r.line_code)!
    block.total_qty += r.planned_qty
    block.rows.push(r)
  }

  const result: DateGroup[] = []
  for (const [d, lineMap] of dateMap) {
    result.push({
      date: d,
      lines: Array.from(lineMap.values()),
    })
  }
  return result.sort((a, b) => a.date.localeCompare(b.date))
}

function getWeekday(d: string): string {
  const wd = ['日', '月', '火', '水', '木', '金', '土']
  return wd[new Date(d).getDay()]
}

/** 土曜・日曜（カレンダー見出し・日付を赤表示） */
function isWeekendDate(d: string): boolean {
  const n = dayjs(d).day()
  return n === 0 || n === 6
}

async function printReport() {
  if (!dateRange.value?.[0] || !dateRange.value?.[1]) {
    ElMessage.warning('期間を選択してください')
    return
  }
  if (selectedLineId.value == null) {
    ElMessage.warning('設備を選択してください')
    return
  }
  await loadReport()
  await nextTick()

  const cleanup = () => {
    document.body.classList.remove('print-daily-calendar-only')
    window.removeEventListener('afterprint', cleanup)
  }
  window.addEventListener('afterprint', cleanup)
  document.body.classList.add('print-daily-calendar-only')
  window.print()
  setTimeout(cleanup, 2500)
}
</script>

<style scoped>
.daily-report-page {
  padding: 6px 8px 12px;
  max-width: 1920px;
  margin: 0 auto;
  min-height: 100%;
  background:
    radial-gradient(circle at 8% -18%, rgba(64, 158, 255, 0.09), transparent 36%),
    radial-gradient(circle at 102% -14%, rgba(103, 194, 58, 0.07), transparent 30%),
    var(--el-bg-color-page);
}

.daily-report-card :deep(.el-card__header) {
  padding: 6px 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-primary);
  background: linear-gradient(
    105deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 42%,
    var(--el-bg-color) 100%
  );
}

.daily-report-card :deep(.el-card__body) {
  min-width: 0;
}

.daily-report-head__main {
  min-width: 0;
}

.daily-report-head__title {
  margin: 0 0 2px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  letter-spacing: 0.02em;
}

.daily-report-head__title-inner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.daily-report-head__title-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}

.daily-report-head__desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
  color: var(--el-text-color-secondary);
}

.toolbar {
  margin-bottom: 10px;
}

.toolbar--panel {
  padding: 8px 10px 10px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, var(--el-fill-color-blank) 0%, var(--el-fill-color-lighter) 100%);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.toolbar__form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px 12px;
}

.toolbar__form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.toolbar__lbl {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.toolbar__lbl .el-icon {
  font-size: 14px;
  color: var(--el-color-primary);
}

.toolbar__range-row {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.toolbar__daterange {
  width: 260px;
}

.toolbar__select-process {
  width: 120px;
}

.toolbar__select-line {
  width: 120px;
}

.dr-btn-month.is-plain {
  --el-button-bg-color: var(--el-color-primary-light-9);
  font-weight: 500;
  border-radius: 6px;
}

.dr-btn-fetch.el-button--primary:not(.is-loading) {
  font-weight: 600;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.35);
}

.dr-btn-fetch.el-button--primary:hover:not(.is-disabled) {
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.45);
}

.dr-btn-print.is-plain {
  font-weight: 600;
  border-radius: 6px;
  --el-button-bg-color: var(--el-color-warning-light-9);
}

.report-body {
  min-height: 120px;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  padding: 28px 16px;
  border-radius: 8px;
  border: 1px dashed var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.empty__icon {
  font-size: 36px;
  color: var(--el-color-primary-light-3);
}

.empty__text {
  margin: 0;
  max-width: 360px;
  line-height: 1.5;
}

.calendar-hint {
  margin: 0 0 10px;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.45;
  color: var(--el-text-color-secondary);
  border-radius: 8px;
  border: 1px dashed var(--el-border-color);
  background: var(--el-fill-color-lighter);
}

.calendar-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-x: auto;
}

.calendar-month__title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.calendar-weekday-row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 6px;
  margin-bottom: 6px;
}

.calendar-weekday-cell {
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  padding: 4px 2px;
}

.calendar-weekday-cell--weekend {
  color: var(--el-color-danger);
  font-weight: 700;
}

.calendar-weeks {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.calendar-week {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 6px;
}

.calendar-day {
  min-width: 0;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  overflow: hidden;
}

.calendar-day--pad {
  min-height: 0;
  border: none;
  background: transparent;
}

.calendar-day--out-range {
  opacity: 0.42;
  background: var(--el-fill-color-lighter);
}

.calendar-day--today {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
}

.calendar-day--weekend:not(.calendar-day--pad) {
  background: #fff7f7;
}

.calendar-day--weekend .calendar-day__hd {
  background: linear-gradient(180deg, #ffeeee 0%, #fff5f5 100%);
  border-bottom-color: rgba(245, 108, 108, 0.25);
}

.calendar-day--weekend .calendar-day__num,
.calendar-day--weekend .calendar-day__wd {
  color: var(--el-color-danger);
}

.calendar-day__hd {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  padding: 6px 8px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-bg-color) 100%);
}

.calendar-day__num {
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-primary);
}

.calendar-day__wd {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.calendar-day__scroll {
  flex: 1;
  min-height: 0;
  max-height: min(44vh, 480px);
  overflow-x: hidden;
  overflow-y: auto;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.line-block {
  min-width: 0;
  padding: 8px 10px 10px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.line-block--calendar {
  padding: 6px 6px 8px;
}

.line-block--calendar .line-header {
  margin-bottom: 6px;
}

.line-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

/* 稼働・合計タグのみ（設備名は印刷ヘッダー側） */
.line-header--calendar-row {
  flex-wrap: nowrap;
  gap: 6px;
  min-width: 0;
  justify-content: flex-end;
}

.line-header__tags {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
}

.line-header__tags :deep(.el-tag) {
  white-space: nowrap;
}

.print-only {
  display: none;
}

.print-summary {
  margin-bottom: 0;
}

.print-summary__line {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 14px;
}

.print-summary__title {
  font-weight: 700;
}

.print-summary__meta {
  font-size: 12px;
}

.report-table {
  width: 100%;
  margin-bottom: 0;
  border-radius: 6px;
  overflow: hidden;
}

.report-table :deep(.el-table__header-wrapper th) {
  font-size: 12px;
  font-weight: 600;
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color) 100%) !important;
}

.report-table :deep(.el-table__body td) {
  font-size: 12px;
}

.report-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
</style>

<style>
/**
 * 本ページから「印刷」を押したときのみ body に print-daily-calendar-only が付く。
 * レイアウトのサイドバー・ヘッダーを非表示にし、カレンダー領域のみを A4 横向きで印刷する。
 */
@media print {
  @page {
    size: A4 landscape;
    margin: 8mm;
  }
}

@media print {
  body.print-daily-calendar-only .layout-sidebar,
  body.print-daily-calendar-only .layout-header,
  body.print-daily-calendar-only .layout-overlay {
    display: none !important;
  }

  body.print-daily-calendar-only .layout-main {
    margin: 0 !important;
    width: 100% !important;
    max-width: none !important;
  }

  body.print-daily-calendar-only .layout-content {
    padding: 0 !important;
    overflow: visible !important;
  }

  body.print-daily-calendar-only .daily-report-page {
    padding: 0 !important;
    margin: 0 !important;
    background: white !important;
    max-width: none !important;
  }

  body.print-daily-calendar-only .daily-report-card {
    border: none !important;
    box-shadow: none !important;
  }

  body.print-daily-calendar-only .daily-report-card .el-card__header {
    display: none !important;
  }

  body.print-daily-calendar-only .daily-report-card .el-card__body {
    padding: 0 !important;
  }

  body.print-daily-calendar-only .toolbar,
  body.print-daily-calendar-only .calendar-hint,
  body.print-daily-calendar-only .empty {
    display: none !important;
  }

  body.print-daily-calendar-only .report-body {
    min-height: 0 !important;
  }

  body.print-daily-calendar-only .calendar-print-root {
    width: 100%;
  }

  body.print-daily-calendar-only .print-summary.print-only {
    display: block !important;
    margin-bottom: 8px;
    padding: 0 0 6px;
    border-bottom: 1px solid #e4e7ed;
    page-break-after: avoid;
  }

  body.print-daily-calendar-only .print-summary__line {
    display: flex !important;
    flex-wrap: nowrap;
    align-items: baseline;
    gap: 12px 16px;
    line-height: 1.35;
  }

  body.print-daily-calendar-only .print-summary__title {
    font-size: 14px;
    font-weight: 700;
    flex-shrink: 0;
  }

  body.print-daily-calendar-only .print-summary__meta {
    font-size: 11px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  body.print-daily-calendar-only * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  body.print-daily-calendar-only .calendar-shell {
    overflow: visible !important;
  }

  /* 印刷時は日曜列（各行の第1セル）を非表示し、6列レイアウトにする */
  body.print-daily-calendar-only .calendar-weekday-row {
    grid-template-columns: repeat(6, minmax(0, 1fr)) !important;
  }

  body.print-daily-calendar-only .calendar-weekday-cell:first-child {
    display: none !important;
  }

  body.print-daily-calendar-only .calendar-week {
    grid-template-columns: repeat(6, minmax(0, 1fr)) !important;
  }

  body.print-daily-calendar-only .calendar-week .calendar-day:first-child {
    display: none !important;
  }

  /* 单月時は印刷ヘッダーに同一文言があるため非表示（複数月は各ブロック見出しを残す） */
  body.print-daily-calendar-only .calendar-month__title--dup-summary {
    display: none !important;
  }

  body.print-daily-calendar-only .calendar-month__title {
    font-size: 13px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }

  body.print-daily-calendar-only .calendar-weekday-cell {
    font-size: 9px;
    padding: 2px;
  }

  body.print-daily-calendar-only .calendar-weekday-cell--weekend {
    color: #f56c6c !important;
  }

  body.print-daily-calendar-only .calendar-day {
    min-height: 0;
    border-radius: 4px;
    font-size: 9px;
  }

  body.print-daily-calendar-only .calendar-day__hd {
    padding: 2px 4px;
  }

  body.print-daily-calendar-only .calendar-day__num {
    font-size: 11px;
  }

  body.print-daily-calendar-only .calendar-day__wd {
    font-size: 9px;
  }

  body.print-daily-calendar-only .calendar-day--weekend .calendar-day__num,
  body.print-daily-calendar-only .calendar-day--weekend .calendar-day__wd {
    color: #d03030 !important;
  }

  body.print-daily-calendar-only .calendar-day--weekend:not(.calendar-day--pad) {
    background: #fff5f5 !important;
  }

  body.print-daily-calendar-only .calendar-day__scroll {
    max-height: none !important;
    overflow: visible !important;
    padding: 2px;
  }

  body.print-daily-calendar-only .line-block--calendar {
    padding: 2px;
    border-color: #cbd5e1;
  }

  body.print-daily-calendar-only .line-header--calendar-row {
    margin-bottom: 2px !important;
  }

  body.print-daily-calendar-only .line-header__tags .el-tag {
    font-size: 10px;
    padding: 0 4px;
    height: 18px;
    line-height: 18px;
  }

  body.print-daily-calendar-only .report-table {
    margin: 0 !important;
  }

  body.print-daily-calendar-only .report-table .el-table__inner-wrapper {
    margin: 0 !important;
  }

  body.print-daily-calendar-only .report-table .el-table__header-wrapper th {
    font-size: 8px !important;
    padding: 1px 2px !important;
  }

  body.print-daily-calendar-only .report-table .el-table__body td {
    font-size: 8px !important;
    padding: 1px 2px !important;
  }

  body.print-daily-calendar-only .report-table .cell {
    padding: 0 2px !important;
    line-height: 1.25 !important;
  }

  body.print-daily-calendar-only .report-table .el-table__body .el-table__row td.el-table__cell,
  body.print-daily-calendar-only .report-table .el-table__header-wrapper th.el-table__cell {
    padding: 1px 2px !important;
  }

  /**
   * 印刷時のみ列幅：品名：計画：実績 = 5 : 2.5 : 2.5（50% : 25% : 25%）
   */
  body.print-daily-calendar-only .report-table .el-table__inner-wrapper table {
    table-layout: fixed !important;
    width: 100% !important;
  }

  body.print-daily-calendar-only .report-table colgroup col:nth-child(1) {
    width: 34% !important;
  }

  body.print-daily-calendar-only .report-table colgroup col:nth-child(2) {
    width: 33% !important;
  }

  body.print-daily-calendar-only .report-table colgroup col:nth-child(3) {
    width: 33% !important;
  }

  body.print-daily-calendar-only .report-table .el-table__header-wrapper th:nth-child(1),
  body.print-daily-calendar-only .report-table .el-table__body-wrapper td:nth-child(1) {
    width: 50% !important;
    box-sizing: border-box !important;
  }

  body.print-daily-calendar-only .report-table .el-table__header-wrapper th:nth-child(2),
  body.print-daily-calendar-only .report-table .el-table__body-wrapper td:nth-child(2) {
    width: 25% !important;
    box-sizing: border-box !important;
  }

  body.print-daily-calendar-only .report-table .el-table__header-wrapper th:nth-child(3),
  body.print-daily-calendar-only .report-table .el-table__body-wrapper td:nth-child(3) {
    width: 25% !important;
    box-sizing: border-box !important;
  }

  body.print-daily-calendar-only .calendar-week {
    break-inside: avoid;
  }

  body.print-daily-calendar-only .calendar-month {
    page-break-inside: auto;
    break-inside: auto;
  }

  body.print-daily-calendar-only .line-block {
    box-shadow: none;
    border: 1px solid #dcdfe6;
    break-inside: avoid;
  }
}
</style>
