<template>
  <div class="cap-matrix-page">
    <div class="plan-hd no-print">
      <h2 class="plan-hd-title">
        <span class="plan-hd-title-inner">
          <el-icon class="plan-hd-title-icon"><Grid /></el-icon>
          設備稼働時間表
        </span>
      </h2>
      <p class="plan-hd-sub">設備ごとの日別稼働時間を二次元表で表示します。印刷帳票としても利用できます。</p>
    </div>

    <div class="plan-card filter-card filter-card--panel no-print">
      <el-form :inline="true" class="filter-form" size="small">
        <el-form-item class="filter-form__item">
          <template #label>
            <span class="filter-form__lbl"><el-icon><Operation /></el-icon>工程</span>
          </template>
          <el-select
            v-model="selectedProcessCd"
            clearable
            filterable
            placeholder="全工程"
            class="filter-form__select filter-form__select--process"
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
        <el-form-item class="filter-form__item">
          <template #label>
            <span class="filter-form__lbl"><el-icon><Monitor /></el-icon>設備</span>
          </template>
          <el-select
            v-model="selectedLineIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            filterable
            placeholder="設備を選択"
            class="filter-form__select filter-form__select--lines"
          >
            <el-option
              v-for="line in lines"
              :key="line.id"
              :label="lineOptionLabel(line)"
              :value="line.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-form__item filter-form__item--range" required>
          <template #label>
            <span class="filter-form__lbl"><el-icon><Calendar /></el-icon>期間</span>
          </template>
          <div class="filter-form__range-row">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="〜"
              start-placeholder="開始日"
              end-placeholder="終了日"
              class="filter-form__daterange"
            />
            <div class="filter-form__quick-months">
              <el-button
                type="primary"
                plain
                size="small"
                class="capmx-btn-month-this"
                :icon="Calendar"
                @click="applyThisMonthRange"
              >
                今月
              </el-button>
              <el-button
                type="success"
                plain
                size="small"
                class="capmx-btn-month-next"
                :icon="Calendar"
                @click="applyNextMonthRange"
              >
                次月
              </el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label-width="0" class="filter-form__item filter-form__item--actions">
          <el-button
            type="primary"
            size="small"
            class="capmx-btn-refresh"
            :icon="Refresh"
            :loading="loading"
            @click="loadMatrix"
          >
            再取得
          </el-button>
          <el-button
            type="warning"
            plain
            size="small"
            class="capmx-btn-print"
            :icon="Printer"
            :disabled="loading || matrixRows.length === 0"
            @click="handlePrint"
          >
            印刷
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="print-head print-only">
      <h1>設備稼働時間表</h1>
      <div>{{ printRangeText }}</div>
      <div>出力日時：{{ printNowText }}</div>
    </div>

    <div v-loading="loading" class="plan-card result-card result-card--panel">
      <el-empty
        v-if="!loading && matrixRows.length === 0"
        class="matrix-empty"
        :image-size="72"
        description="データがありません"
      >
        <template #image>
          <el-icon class="matrix-empty__icon"><Document /></el-icon>
        </template>
      </el-empty>
      <div v-else class="matrix-wrap">
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="sticky-col col-line">設備</th>
              <th
                v-for="d in dateColumns"
                :key="d"
                class="date-col"
                :class="{ 'is-weekend': isWeekend(d) }"
              >
                <div class="date-hd">{{ formatDate(d) }}</div>
                <div class="wd-hd">{{ getWeekday(d) }}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in matrixRows" :key="row.lineId">
              <td class="sticky-col col-line">{{ row.lineLabel }}</td>
              <td
                v-for="d in dateColumns"
                :key="`${row.lineId}-${d}`"
                class="cell"
                :class="cellClasses(row.dailyHours[d], d)"
                :title="`${formatDate(d)}: ${formatHours(row.dailyHours[d] || 0)}h`"
              >
                <div class="cell-main">{{ formatHours(row.dailyHours[d] || 0) }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Grid, Operation, Monitor, Calendar, Refresh, Printer, Document } from '@element-plus/icons-vue'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import {
  fetchLineCapacities,
  fetchLines,
  fetchSchedulingGrid,
  type ProductionLine,
} from '@/api/aps'

type MatrixRow = {
  lineId: number
  lineLabel: string
  totalHours: number
  dailyHours: Record<string, number>
}

/** プルダウン表示：工程名のみ（空のときは CD） */
function processOptionLabel(p: ProcessItem): string {
  const nm = (p.process_name || '').trim()
  const cd = (p.process_cd || '').trim()
  return nm || cd || '—'
}

/** プルダウン表示：設備名のみ（空のときはラインコード） */
function lineOptionLabel(line: ProductionLine): string {
  const name = (line.line_name || '').trim()
  return name || (line.line_code || '').trim() || '—'
}

const processOptions = ref<ProcessItem[]>([])
/** 切断・面取・成型・溶接・メッキ（`processes.process_cd`）— 表示順固定 */
const CAPACITY_MATRIX_PROCESS_ORDER = ['KT01', 'KT02', 'KT04', 'KT07', 'KT05'] as const
const CAPACITY_MATRIX_PROCESS_SET = new Set<string>(CAPACITY_MATRIX_PROCESS_ORDER)

const matrixProcessOptions = computed(() => {
  const order = CAPACITY_MATRIX_PROCESS_ORDER
  const list = processOptions.value.filter((p) =>
    CAPACITY_MATRIX_PROCESS_SET.has((p.process_cd || '').trim()),
  )
  const rank = (cd: string) => {
    const i = order.indexOf(cd as (typeof CAPACITY_MATRIX_PROCESS_ORDER)[number])
    return i >= 0 ? i : 999
  }
  return [...list].sort(
    (a, b) => rank((a.process_cd || '').trim()) - rank((b.process_cd || '').trim()),
  )
})

const selectedProcessCd = ref<string>('KT04')
const lines = ref<ProductionLine[]>([])
const selectedLineIds = ref<number[]>([])
const loading = ref(false)
const dateRange = ref<[string, string]>([
  dayjs().startOf('month').format('YYYY-MM-DD'),
  dayjs().endOf('month').format('YYYY-MM-DD'),
])
const matrixRows = ref<MatrixRow[]>([])

const dateColumns = computed(() => {
  const [s, e] = dateRange.value || []
  if (!s || !e) return []
  const out: string[] = []
  let cur = dayjs(s)
  const end = dayjs(e)
  while (cur.isBefore(end) || cur.isSame(end, 'day')) {
    out.push(cur.format('YYYY-MM-DD'))
    cur = cur.add(1, 'day')
  }
  return out
})

const printRangeText = computed(() => {
  const [s, e] = dateRange.value || []
  if (!s || !e) return ''
  return `期間：${s} 〜 ${e}`
})

const printNowText = computed(() => dayjs().format('YYYY-MM-DD HH:mm'))

function isWeekend(d: string) {
  const wd = dayjs(d).day()
  return wd === 0 || wd === 6
}

function getWeekday(d: string) {
  return ['日', '月', '火', '水', '木', '金', '土'][dayjs(d).day()]
}

function formatDate(d: string) {
  return dayjs(d).format('MM/DD')
}

/** 稼働時間表示：小数部が 0.1 を超える場合は整数部に +1（それ以外は整数部のまま） */
function formatHours(v: number) {
  const n = Number(v || 0)
  if (!Number.isFinite(n)) return '-'
  if (n === 0) return ''
  const intPart = Math.floor(n)
  const frac = n - intPart
  const display = frac > 0.1 ? intPart + 1 : intPart
  return String(display)
}

async function applyThisMonthRange() {
  dateRange.value = [
    dayjs().startOf('month').format('YYYY-MM-DD'),
    dayjs().endOf('month').format('YYYY-MM-DD'),
  ]
  await loadMatrix()
}

async function applyNextMonthRange() {
  const d = dayjs().add(1, 'month')
  dateRange.value = [
    d.startOf('month').format('YYYY-MM-DD'),
    d.endOf('month').format('YYYY-MM-DD'),
  ]
  await loadMatrix()
}

/** 画面セル：印刷と同じ稼働時間帯の色分け */
function cellClasses(rawHours: number | undefined, d: string) {
  const h = Number(rawHours || 0)
  const weekend = isWeekend(d)
  const classes: Record<string, boolean> = {
    'is-zero': !h,
    'is-weekend': weekend,
  }
  if (h > 23) classes['is-high-hours'] = true
  else if (h >= 20 && h <= 22) classes['is-mid-hours'] = true
  return classes
}

function ensureProcessSelectionInMatrixList() {
  const list = matrixProcessOptions.value
  const cur = (selectedProcessCd.value || '').trim()
  if (list.some((p) => (p.process_cd || '').trim() === cur)) return
  const next = list.find((p) => (p.process_cd || '').trim() === 'KT04') ?? list[0]
  selectedProcessCd.value = (next?.process_cd || 'KT04').trim() || 'KT04'
}

async function loadProcessOptions() {
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const data = (res?.data ?? res) as { list?: ProcessItem[] }
    processOptions.value = Array.isArray(data.list) ? data.list : []
  } catch {
    processOptions.value = []
  }
  ensureProcessSelectionInMatrixList()
}

async function loadLinesByProcess() {
  const fetchedLines = await fetchLines((selectedProcessCd.value || '').trim() || undefined)
  lines.value = fetchedLines.filter((ln) => {
    const lineName = String(ln.line_name || '').trim()
    return !lineName.includes('成型他')
  })
  selectedLineIds.value = selectedLineIds.value.filter((id) => lines.value.some((ln) => ln.id === id))
}

async function loadMatrix() {
  const [startDate, endDate] = dateRange.value || []
  if (!startDate || !endDate) {
    ElMessage.warning('期間を選択してください')
    return
  }
  loading.value = true
  try {
    const targetLines = selectedLineIds.value.length > 0
      ? lines.value.filter((ln) => selectedLineIds.value.includes(ln.id))
      : lines.value
    const results = await Promise.all(
      targetLines.map(async (ln) => ({
        line: ln,
        days: await fetchLineCapacities(ln.id, startDate, endDate),
      })),
    )
    matrixRows.value = results.map(({ line, days }) => {
      const dailyHours: Record<string, number> = {}
      for (const d of dateColumns.value) {
        dailyHours[d] = 0
      }
      for (const day of days) {
        dailyHours[day.work_date] = Number(day.available_hours || 0)
      }
      const totalHours = Object.values(dailyHours).reduce((acc, h) => acc + Number(h || 0), 0)
      return {
        lineId: line.id,
        lineLabel: String(line.line_name || '').trim() || line.line_code,
        totalHours,
        dailyHours,
      }
    })
  } finally {
    loading.value = false
  }
}

async function handleProcessChange() {
  await loadLinesByProcess()
  await loadMatrix()
}

function escHtml(v: unknown): string {
  return String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

async function handlePrint() {
  await loadMatrix()
  await nextTick()
  const [startDate, endDate] = dateRange.value || []
  const selectedLineIdSet = new Set(
    (selectedLineIds.value.length > 0 ? selectedLineIds.value : lines.value.map((ln) => ln.id)),
  )
  const selectedLineCount = selectedLineIdSet.size
  let totalPlannedProcessQty = 0
  if (startDate && endDate) {
    const schedulingGrid = await fetchSchedulingGrid(
      startDate,
      endDate,
      undefined,
      (selectedProcessCd.value || '').trim() || undefined,
    )
    totalPlannedProcessQty = (schedulingGrid?.blocks || [])
      .filter((block) => selectedLineIdSet.has(Number(block.line_id)))
      .reduce((sum, block) => {
        const lineSum = Object.values(block.daily_totals || {})
          .reduce((acc, qty) => acc + Number(qty || 0), 0)
        return sum + lineSum
      }, 0)
  }
  const summaryHtml = `
    <section class="print-summary">
      <h2>期間集計（生産計画数量）</h2>
      <div class="summary-grid">
        <div class="summary-item"><span class="k">対象期間</span><span class="v">${escHtml(startDate || '')} 〜 ${escHtml(endDate || '')}</span></div>
        <div class="summary-item"><span class="k">対象設備数</span><span class="v">${escHtml(String(selectedLineCount))}</span></div>
        <div class="summary-item summary-total"><span class="k">生産計画総数量</span><span class="v">${escHtml(Math.round(totalPlannedProcessQty).toLocaleString('ja-JP'))}</span></div>
      </div>
    </section>
  `
  const headers = [
    '<th>設備</th>',
    ...dateColumns.value.map((d) => {
      const weekendClass = isWeekend(d) ? ' class="is-weekend"' : ''
      return `<th${weekendClass}>${escHtml(formatDate(d))}<br/><small>${escHtml(getWeekday(d))}</small></th>`
    }),
  ].join('')
  const rowsHtml = matrixRows.value.map((row) => {
    const cells = dateColumns.value
      .map((d) => {
        const rawHours = Number(row.dailyHours[d] || 0)
        const classes = ['num']
        if (isWeekend(d)) classes.push('is-weekend')
        if (rawHours > 23) {
          classes.push('is-high-hours')
        } else if (rawHours >= 20 && rawHours <= 22) {
          classes.push('is-mid-hours')
        }
        return `<td class="${classes.join(' ')}">${escHtml(formatHours(rawHours))}</td>`
      })
      .join('')
    return `<tr><td>${escHtml(row.lineLabel)}</td>${cells}</tr>`
  }).join('')

  const html = `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>成型ライン稼働予定時間表</title>
    <style>
      @page { size: A4 landscape; margin: 8mm; }
      * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans", "Meiryo", sans-serif; color: #111827; }
      h1 { margin: 0 0 6px; font-size: 16px; }
      .meta { margin: 0 0 8px; font-size: 11px; color: #374151; }
      table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 10px; }
      th, td { border: 1px solid #cbd5e1; padding: 4px 4px; word-break: break-word; line-height: 1.3; }
      th { background-color: #f1f5f9; font-size: 8px; }
      th small { font-size: 8px; }
      th:nth-child(1), td:nth-child(1) { width: 40px; }
      .num { text-align: right; }
      th.is-weekend { color: #dc2626; background-color: #ffecec; }
      td.is-weekend { background-color: #fff5f5; }
      td.is-mid-hours { background-color: #fff7d6; }
      td.is-high-hours { background-color: #f4c98a; }
      thead { display: table-header-group; }
      tr { page-break-inside: avoid; }
      .print-summary { margin-top: 10px; border-top: 1px solid #cbd5e1; padding-top: 8px; }
      .print-summary h2 { margin: 0 0 6px; font-size: 12px; }
      .summary-grid { display: flex; flex-wrap: wrap; gap: 6px; }
      .summary-item { min-width: 220px; border: 1px solid #dbe5f1; background-color: #f8fafc; padding: 5px 7px; }
      .summary-item .k { display: inline-block; color: #475569; margin-right: 8px; }
      .summary-item .v { font-weight: 700; color: #0f172a; }
      .summary-total { background-color: #e6f4ea; border-color: #b7dfc2; }
    </style>
  </head>
  <body>
    <h1>成型ライン稼働予定時間表</h1>
    <p class="meta">${escHtml(printRangeText.value)} / 出力日時: ${escHtml(printNowText.value)}</p>
    <table>
      <thead><tr>${headers}</tr></thead>
      <tbody>${rowsHtml}</tbody>
    </table>
    ${summaryHtml}
    ${'<scr' + 'ipt>window.onload = () => window.print();</scr' + 'ipt>'}
  </body>
</html>`

  const win = window.open('', '_blank')
  if (!win) {
    ElMessage.error('印刷ウィンドウを開けませんでした')
    return
  }
  win.document.open()
  win.document.write(html)
  win.document.close()
}

onMounted(async () => {
  await loadProcessOptions()
  await loadLinesByProcess()
  await loadMatrix()
})
</script>

<style scoped>
.cap-matrix-page {
  padding: 6px 8px 10px;
  max-width: 1920px;
  margin: 0 auto;
  background:
    radial-gradient(circle at 6% -18%, rgba(64, 158, 255, 0.1), transparent 38%),
    radial-gradient(circle at 104% -20%, rgba(103, 194, 58, 0.08), transparent 32%),
    var(--el-bg-color-page);
  min-height: 100%;
}
.plan-hd {
  margin-bottom: 4px;
}
.plan-hd-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.02em;
}
.plan-hd-title-inner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.plan-hd-title-icon {
  font-size: 22px;
  color: var(--el-color-primary);
}
.plan-hd-sub {
  margin: 2px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 11px;
  line-height: 1.45;
}
.plan-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 8px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}
.filter-card--panel {
  border-left: 3px solid var(--el-color-primary);
  background: linear-gradient(
    105deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 38%,
    var(--el-bg-color) 100%
  );
}
.result-card--panel {
  border-left: 3px solid var(--el-color-success);
  padding: 6px 8px;
}
.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 6px 10px;
}
.filter-form :deep(.el-form-item) {
  margin-right: 0;
  margin-bottom: 0;
}
.filter-form :deep(.el-form-item__label) {
  padding-right: 6px;
}
.filter-form__lbl {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}
.filter-form__lbl .el-icon {
  font-size: 14px;
  color: var(--el-color-primary);
}
.filter-form__select--process {
  width: 110px;
}
.filter-form__select--lines {
  width: 120px;
}
.filter-form__range-row {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.filter-form__daterange {
  width: 280px;
}
.filter-form__quick-months {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.capmx-btn-month-this.is-plain {
  --el-button-bg-color: var(--el-color-primary-light-9);
  font-weight: 500;
  border-radius: 6px;
}
.capmx-btn-month-next.is-plain {
  --el-button-bg-color: var(--el-color-success-light-9);
  font-weight: 500;
  border-radius: 6px;
}
.capmx-btn-refresh.el-button--primary:not(.is-loading) {
  font-weight: 600;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.35);
}
.capmx-btn-refresh.el-button--primary:hover:not(.is-disabled) {
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.45);
}
.capmx-btn-print.is-plain:not(.is-disabled) {
  font-weight: 600;
  border-radius: 6px;
  --el-button-bg-color: var(--el-color-warning-light-9);
}
.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-select__wrapper),
.filter-form :deep(.el-button) {
  border-radius: 6px;
}
.matrix-empty {
  padding: 24px 12px;
}
.matrix-empty :deep(.el-empty__description) {
  margin-top: 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.matrix-empty__icon {
  font-size: 56px;
  color: var(--el-color-primary-light-5);
}
.matrix-wrap {
  overflow: auto;
  max-height: calc(100vh - 198px);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-bg-color);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}
.matrix-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  line-height: 1.25;
  table-layout: fixed;
}
.matrix-table th,
.matrix-table td {
  border: 1px solid var(--el-border-color-lighter);
  padding: 2px 4px;
  vertical-align: middle;
}
.matrix-table th {
  position: sticky;
  top: 0;
  z-index: 3;
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color) 100%);
  color: var(--el-text-color-regular);
  box-shadow: 0 1px 0 var(--el-border-color-light);
  font-weight: 700;
  text-align: center;
}
.sticky-col {
  position: sticky;
  left: 0;
  background: var(--el-bg-color);
  z-index: 2;
}
.matrix-table th.sticky-col {
  z-index: 4;
}
.col-line {
  width: 48px;
  left: 0;
  text-align: left;
  font-weight: 600;
}
.date-col {
  width: 45px;
  min-width: 45px;
  max-width: 45px;
}
.date-hd {
  font-weight: 700;
  font-size: 10px;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.wd-hd {
  font-size: 9px;
  color: var(--el-text-color-secondary);
  line-height: 1.15;
}
.matrix-table tbody tr:nth-child(2n) {
  background: var(--el-fill-color-blank);
}
.matrix-table tbody tr:hover td.cell {
  filter: brightness(0.985);
}
.matrix-table tbody tr:hover td.sticky-col {
  background: var(--el-color-primary-light-9);
}
.cell.is-zero {
  color: var(--el-text-color-placeholder);
}
.cell.is-weekend,
.date-col.is-weekend {
  background: #fff5f5;
}
.date-col.is-weekend .date-hd,
.date-col.is-weekend .wd-hd {
  color: var(--el-color-danger);
}
/* 印刷プレビューと同じ高稼働の段階色 */
.cell.is-mid-hours {
  background: #fff7d6 !important;
}
.cell.is-high-hours {
  background: #f4c98a !important;
}
.cell-main {
  font-weight: 700;
  font-size: 11px;
  color: var(--el-text-color-primary);
  text-align: right;
  min-width: 30px;
  letter-spacing: 0;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.matrix-table tbody .sticky-col.col-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.print-only {
  display: none;
}

@media print {
  .no-print {
    display: none !important;
  }
  .print-only {
    display: block;
    margin-bottom: 8px;
  }
  .print-head h1 {
    margin: 0 0 4px;
    font-size: 16px;
  }
  .cap-matrix-page {
    padding: 0;
  }
  .plan-card {
    border: none;
    padding: 0;
    margin: 0;
  }
  .matrix-wrap {
    max-height: none;
    overflow: visible;
    border: none;
  }
  .matrix-table {
    width: 100%;
    font-size: 9px;
    line-height: 1.2;
  }
  .matrix-table th,
  .matrix-table td {
    padding: 2px 3px;
  }
  .matrix-table thead {
    display: table-header-group;
  }
}
</style>
