<template>
  <div class="cap-matrix-page">
    <div class="plan-hd no-print">
      <h2 class="plan-hd-title">設備稼働時間表</h2>
      <p class="plan-hd-sub">設備ごとの日別稼働時間を二次元表で表示します。印刷帳票としても利用できます。</p>
    </div>

    <div class="plan-card filter-card no-print">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="工程">
          <el-select
            v-model="selectedProcessCd"
            clearable
            filterable
            placeholder="全工程"
            style="width: 180px"
            @change="handleProcessChange"
          >
            <el-option
              v-for="p in processOptions"
              :key="p.process_cd"
              :label="`${p.process_cd} — ${p.process_name}`"
              :value="p.process_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="設備">
          <el-select
            v-model="selectedLineIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            filterable
            placeholder="設備を選択（未選択=全件）"
            style="width: 360px"
          >
            <el-option
              v-for="line in lines"
              :key="line.id"
              :label="productionLineOptionLabel(line)"
              :value="line.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="期間" required>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="〜"
            start-placeholder="開始日"
            end-placeholder="終了日"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item label-width="0">
          <el-button type="primary" :loading="loading" @click="loadMatrix">再取得</el-button>
          <el-button
            type="warning"
            plain
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

    <div class="plan-card result-card" v-loading="loading">
      <el-empty v-if="!loading && matrixRows.length === 0" description="データがありません" />
      <div v-else class="matrix-wrap">
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="sticky-col col-line">設備</th>
              <th class="sticky-col col-total">期間合計(h)</th>
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
              <td class="sticky-col col-total numeric">{{ formatHours(row.totalHours) }}</td>
              <td
                v-for="d in dateColumns"
                :key="`${row.lineId}-${d}`"
                class="cell"
                :class="{ 'is-zero': !row.dailyHours[d], 'is-weekend': isWeekend(d) }"
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
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import {
  fetchLineCapacities,
  fetchLines,
  productionLineOptionLabel,
  type ProductionLine,
} from '@/api/aps'

type MatrixRow = {
  lineId: number
  lineLabel: string
  totalHours: number
  dailyHours: Record<string, number>
}

const processOptions = ref<ProcessItem[]>([])
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

function formatHours(v: number) {
  const n = Number(v || 0)
  if (!Number.isFinite(n)) return '-'
  if (n === 0) return ''
  return n.toFixed(1)
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

async function loadLinesByProcess() {
  lines.value = await fetchLines((selectedProcessCd.value || '').trim() || undefined)
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
  const headers = [
    '<th>設備</th>',
    '<th>期間合計(h)</th>',
    ...dateColumns.value.map((d) => `<th>${escHtml(formatDate(d))}<br/><small>${escHtml(getWeekday(d))}</small></th>`),
  ].join('')
  const rowsHtml = matrixRows.value.map((row) => {
    const cells = dateColumns.value
      .map((d) => `<td class="num">${escHtml(formatHours(row.dailyHours[d] || 0))}</td>`)
      .join('')
    return `<tr><td>${escHtml(row.lineLabel)}</td><td class="num">${escHtml(formatHours(row.totalHours))}</td>${cells}</tr>`
  }).join('')

  const html = `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>設備稼働時間表</title>
    <style>
      @page { size: A4 landscape; margin: 8mm; }
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans", "Meiryo", sans-serif; color: #111827; }
      h1 { margin: 0 0 6px; font-size: 16px; }
      .meta { margin: 0 0 8px; font-size: 11px; color: #374151; }
      table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 10px; }
      th, td { border: 1px solid #cbd5e1; padding: 2px 4px; word-break: break-word; }
      th { background: #f1f5f9; font-size: 8px; }
      th small { font-size: 8px; }
      th:nth-child(1), td:nth-child(1) { width: 35px; }
      th:nth-child(2), td:nth-child(2) { width: 28px; }
      .num { text-align: right; }
      thead { display: table-header-group; }
      tr { page-break-inside: avoid; }
    </style>
  </head>
  <body>
    <h1>設備稼働時間表</h1>
    <p class="meta">${escHtml(printRangeText.value)} / 出力日時: ${escHtml(printNowText.value)}</p>
    <table>
      <thead><tr>${headers}</tr></thead>
      <tbody>${rowsHtml}</tbody>
    </table>
    <script>window.onload = () => window.print();<\/script>
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
  padding: 10px 12px 12px;
  background:
    radial-gradient(circle at 8% -20%, rgba(59, 130, 246, 0.08), transparent 34%),
    radial-gradient(circle at 110% -24%, rgba(16, 185, 129, 0.08), transparent 30%),
    #f3f6fb;
  min-height: 100%;
}
.plan-hd {
  margin-bottom: 6px;
}
.plan-hd-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #0b1220;
}
.plan-hd-sub {
  margin: 3px 0 0;
  color: #5f6f86;
  font-size: 12px;
}
.plan-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 12px;
  padding: 8px 10px;
  margin-bottom: 7px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 20px rgba(15, 23, 42, 0.04);
}
.filter-form :deep(.el-form-item) {
  margin-right: 8px;
  margin-bottom: 4px;
}
.filter-form :deep(.el-form-item__label) {
  padding-right: 6px;
  font-weight: 600;
  color: #334155;
}
.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-select__wrapper),
.filter-form :deep(.el-button) {
  border-radius: 8px;
}
.matrix-wrap {
  overflow: auto;
  max-height: calc(100vh - 210px);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}
.matrix-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  table-layout: fixed;
}
.matrix-table th,
.matrix-table td {
  border: 1px solid #e7edf5;
  padding: 5px 8px;
  vertical-align: middle;
}
.matrix-table th {
  position: sticky;
  top: 0;
  z-index: 3;
  background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  color: #42526a;
  box-shadow: 0 1px 0 #dbe5f1;
  font-weight: 700;
  text-align: center;
}
.sticky-col {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
}
.matrix-table th.sticky-col {
  z-index: 4;
}
.col-line {
  width: 80px;
  left: 0;
  text-align: left;
  font-weight: 600;
}
.col-total {
  width: 116px;
  min-width: 116px;
  max-width: 116px;
  left: 80px;
  text-align: right;
  font-weight: 700;
  background: #f7fbff;
}
.numeric {
  text-align: right;
}
.date-col {
  width: 72px;
  min-width: 72px;
  max-width: 72px;
}
.date-hd {
  font-weight: 700;
  font-size: 11px;
}
.wd-hd {
  font-size: 10px;
  color: #6b7a90;
}
.matrix-table tbody tr:nth-child(2n) {
  background: #fcfdff;
}
.matrix-table tbody tr:hover td {
  background: #f1f7ff;
}
.cell.is-zero {
  color: #9aa8bb;
}
.cell.is-weekend,
.date-col.is-weekend {
  background: #fff7f7;
}
.cell-main {
  font-weight: 700;
  color: #0f172a;
  text-align: right;
  min-width: 38px;
  letter-spacing: 0.1px;
}
.matrix-table tbody .sticky-col.col-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.matrix-table tbody .sticky-col.col-total {
  color: #0f172a;
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
    font-size: 10px;
  }
  .matrix-table th,
  .matrix-table td {
    padding: 3px 4px;
  }
  .matrix-table thead {
    display: table-header-group;
  }
}
</style>
