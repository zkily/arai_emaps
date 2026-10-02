<template>
  <div class="cap-matrix-page cm-modern">
    <div class="plan-hd no-print">
      <div class="plan-hd-fx" aria-hidden="true">
        <span class="fx-orb orb-a" />
        <span class="fx-orb orb-b" />
        <span class="fx-grid" />
        <span class="fx-sheen" />
      </div>
      <div class="plan-hd-text">
        <h2 class="plan-hd-title">
          <span class="plan-hd-title-inner">
            <el-icon class="plan-hd-title-icon"><Grid /></el-icon>
            設備稼働時間表
          </span>
        </h2>
        <p class="plan-hd-sub">設備ごとの日別稼働時間を二次元表で表示します。印刷帳票としても利用できます。</p>
      </div>
      <div class="plan-hd-meta">
        <span class="plan-hd-chip">
          <el-icon><Operation /></el-icon>
          {{ selectedProcessLabel }}
        </span>
        <span class="plan-hd-chip">
          <el-icon><Calendar /></el-icon>
          {{ dateRange?.[0] || '—' }} 〜 {{ dateRange?.[1] || '—' }}
        </span>
        <span class="plan-hd-chip">
          <el-icon><Monitor /></el-icon>
          設備 {{ matrixRows.length }}
        </span>
        <span class="plan-hd-chip plan-hd-chip--strong">
          <el-icon><Timer /></el-icon>
          合計 {{ Math.round(grandTotalHours).toLocaleString('ja-JP') }}h
        </span>
      </div>
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
      <div class="print-band-key">
        <span v-for="band in HOUR_BANDS" :key="band.label" class="print-band-key__item">
          <i :style="{ background: band.bg }" />{{ band.label }}
        </span>
      </div>
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
      <div v-if="matrixRows.length > 0" class="matrix-legend no-print">
        <span class="lg-item"><i class="lg-sw lg-sw--empty" />平日0h</span>
        <span class="lg-item"><i class="lg-sw lg-sw--weekend" />土日</span>
        <span v-for="band in HOUR_BANDS" :key="band.label" class="lg-item">
          <i class="lg-sw" :style="{ background: band.bg }" />{{ band.label }}
        </span>
        <span class="lg-item"><i class="lg-sw lg-sw--tech" />技術使用</span>
        <span class="lg-item"><i class="lg-sw lg-sw--maint" />保全</span>
        <span class="lg-item"><i class="lg-sw lg-sw--mixed" />技術・保全</span>
      </div>
      <div v-if="loading || matrixRows.length > 0" class="matrix-wrap">
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="sticky-col col-line">設備</th>
              <th
                v-for="d in dateColumns"
                :key="d"
                class="date-col"
                :class="{ 'is-weekend': isWeekend(d), 'is-today': isToday(d) }"
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
                :class="cellClasses(row.dailyHours[d], d, row.dailyOccupancy[d])"
                :style="hoursCellStyle(row.dailyHours[d])"
                :title="occupancyCellTitle(d, row.dailyHours[d] || 0, row.dailyOccupancy[d])"
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
import {
  Grid,
  Operation,
  Monitor,
  Calendar,
  Refresh,
  Printer,
  Document,
  Timer,
} from '@element-plus/icons-vue'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import {
  fetchLineCapacities,
  fetchLineCapacitySlots,
  fetchLines,
  fetchSchedulingGrid,
  type ProductionLine,
} from '@/api/aps'
import { dayOccupancyKindFromSlots, type DayOccupancyKind } from '@/utils/lineOccupancyDisplay'
import { useApsOperationPermission } from '@/composables/useApsOperationPermission'
import { guardApsOperation } from '@/utils/apsOperationGuard'

const { canExport } = useApsOperationPermission()

type MatrixRow = {
  lineId: number
  lineLabel: string
  totalHours: number
  dailyHours: Record<string, number>
  dailyOccupancy: Record<string, DayOccupancyKind>
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

const selectedProcessLabel = computed(() => {
  const cd = (selectedProcessCd.value || '').trim()
  if (!cd) return '全工程'
  const p = processOptions.value.find((x) => (x.process_cd || '').trim() === cd)
  return p ? processOptionLabel(p) : cd
})

const grandTotalHours = computed(() =>
  matrixRows.value.reduce((acc, r) => acc + Number(r.totalHours || 0), 0),
)

function isToday(d: string) {
  return dayjs(d).isSame(dayjs(), 'day')
}

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

/** 取整後の表示を名目時間へ寄せる（画面・設備稼働時間表印刷・成型ライン稼働予定時間表で共通） */
const DISPLAY_HOURS_ALIAS: Record<number, number> = {
  13: 14,
  15: 16,
  19: 20,
  21: 22,
  23: 24,
}

/** 稼働時間表示：小数部が 0.1 を超える場合は整数部に +1。その後 13/15/19/21/23 は +1 */
function formatHours(v: number) {
  const n = Number(v || 0)
  if (!Number.isFinite(n)) return '-'
  if (n === 0) return ''
  const intPart = Math.floor(n)
  const frac = n - intPart
  let display = frac > 0.1 ? intPart + 1 : intPart
  display = DISPLAY_HOURS_ALIAS[display] ?? display
  return String(display)
}

/** 17h 以上だけ背景色。16 以下は無地。大きいほど濃い淡黄、いずれも薄色で数字は黒のまま */
const HOUR_BANDS: { max: number; label: string; bg: string }[] = [
  { max: 20, label: '17～20h', bg: '#fff7cc' },
  { max: 22, label: '21～22h', bg: '#ffef99' },
  { max: 24, label: '23h～', bg: '#ffe066' },
]

function displayedHourNumber(v: number): number {
  const n = Number(formatHours(v))
  return Number.isFinite(n) && n > 0 ? n : 0
}

function hourBand(rawHours: number) {
  const h = displayedHourNumber(rawHours)
  if (h <= 16) return null
  return HOUR_BANDS.find((b) => h <= b.max) ?? HOUR_BANDS[HOUR_BANDS.length - 1]
}

function hoursCellStyle(rawHours: number | undefined): Record<string, string> | undefined {
  const band = hourBand(Number(rawHours || 0))
  if (!band) return undefined
  return { backgroundColor: band.bg }
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
function occupancyCellTitle(d: string, hours: number, occ: DayOccupancyKind): string {
  const base = `${formatDate(d)}: ${formatHours(hours)}h`
  if (occ === 'tech') return `${base}／技術使用あり`
  if (occ === 'maintenance') return `${base}／保全あり`
  if (occ === 'mixed') return `${base}／技術・保全あり`
  return base
}

function cellClasses(
  rawHours: number | undefined,
  d: string,
  occ: DayOccupancyKind = '',
) {
  const h = Number(rawHours || 0)
  const weekend = isWeekend(d)
  const classes: Record<string, boolean> = {
    'is-zero': !h,
    'is-weekend': weekend,
  }
  if (!h && !weekend) classes['is-weekday-empty'] = true
  if (hourBand(h)) classes['is-hband'] = true
  if (occ === 'tech') classes['is-tech-occ'] = true
  else if (occ === 'maintenance') classes['is-maint-occ'] = true
  else if (occ === 'mixed') classes['is-mixed-occ'] = true
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
      targetLines.map(async (ln) => {
        const [days, slotDays] = await Promise.all([
          fetchLineCapacities(ln.id, startDate, endDate),
          fetchLineCapacitySlots(ln.id, startDate, endDate).catch(() => []),
        ])
        return { line: ln, days, slotDays }
      }),
    )
    matrixRows.value = results.map(({ line, days, slotDays }) => {
      const dailyHours: Record<string, number> = {}
      const dailyOccupancy: Record<string, DayOccupancyKind> = {}
      for (const d of dateColumns.value) {
        dailyHours[d] = 0
        dailyOccupancy[d] = ''
      }
      for (const day of days) {
        dailyHours[day.work_date] = Number(day.available_hours || 0)
      }
      for (const day of slotDays || []) {
        const wd = String(day.work_date || '').slice(0, 10)
        if (!wd) continue
        dailyOccupancy[wd] = dayOccupancyKindFromSlots(day.slots || [])
      }
      const totalHours = Object.values(dailyHours).reduce((acc, h) => acc + Number(h || 0), 0)
      return {
        lineId: line.id,
        lineLabel: String(line.line_name || '').trim() || line.line_code,
        totalHours,
        dailyHours,
        dailyOccupancy,
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
  if (!guardApsOperation(canExport)) return
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
        else if (!rawHours) classes.push('is-weekday-empty')
        const band = hourBand(rawHours)
        const occ = row.dailyOccupancy?.[d] || ''
        if (occ === 'tech') classes.push('is-tech-occ')
        else if (occ === 'maintenance') classes.push('is-maint-occ')
        else if (occ === 'mixed') classes.push('is-mixed-occ')
        const style = band
          ? ` style="background-color:${band.bg};color:#0f172a;font-weight:700"`
          : ''
        return `<td class="${classes.join(' ')}"${style}>${escHtml(formatHours(rawHours))}</td>`
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
      td.is-weekday-empty { background-color: #e5e7eb; color: #64748b; }
      td.is-tech-occ { box-shadow: inset 0 0 0 2px #f5a623; }
      td.is-maint-occ { box-shadow: inset 0 0 0 2px #64748b; }
      td.is-mixed-occ { box-shadow: inset 0 0 0 2px #ea580c; }
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
.cell.is-weekday-empty {
  background: #e5e7eb !important;
}
.date-col.is-weekend .date-hd,
.date-col.is-weekend .wd-hd {
  color: var(--el-color-danger);
}
/* 稼働時間の背景は inline style。文字色は濃い色に固定して薄色背景でも読めるようにする */
.cell.is-hband,
.cell.is-hband .cell-main {
  color: #0f172a;
}
.cell.is-tech-occ {
  box-shadow: inset 0 0 0 2px #f5a623;
}
.cell.is-maint-occ {
  box-shadow: inset 0 0 0 2px #64748b;
}
.cell.is-mixed-occ {
  box-shadow: inset 0 0 0 2px #ea580c;
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

.print-band-key {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 10px;
  margin-top: 6px;
  font-size: 11px;
  color: #0f172a;
}
.print-band-key__item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.print-band-key__item i {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 1px solid rgba(15, 23, 42, 0.25);
}

@media print {
  .no-print {
    display: none !important;
  }
  .matrix-table,
  .matrix-table td,
  .matrix-table th {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
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

/* 页面美化：現代UI・3D動効・色分け（設備稼働時間表 / APS blue→indigo→violet） */
@media screen {
  .cm-modern {
    --cm-c1: #1d4ed8;
    --cm-c2: #4f46e5;
    --cm-c3: #7c3aed;
    --cm-edge: #3730a3;
    padding: 8px 10px 12px;
    background:
      radial-gradient(circle at 4% -10%, rgba(79, 70, 229, 0.1), transparent 36%),
      radial-gradient(circle at 100% -16%, rgba(124, 58, 237, 0.09), transparent 32%),
      var(--el-bg-color-page);
  }

  /* ---- Hero ヘッダー ---- */
  .cm-modern .plan-hd {
    position: relative;
    overflow: hidden;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 16px;
    margin-bottom: 10px;
    padding: 12px 16px;
    border-radius: 14px;
    color: #fff;
    background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 30%, #4f46e5 64%, #7c3aed 100%);
    box-shadow:
      0 14px 30px -16px rgba(55, 48, 163, 0.65),
      inset 0 1px 0 rgba(255, 255, 255, 0.18);
    animation: cmRise 0.45s ease-out backwards;
  }
  .cm-modern .plan-hd-fx {
    position: absolute;
    inset: 0;
    z-index: 0;
    pointer-events: none;
  }
  .cm-modern .fx-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(2px);
    animation: cmOrbFloat 9s ease-in-out infinite;
  }
  .cm-modern .orb-a {
    width: 180px;
    height: 180px;
    top: -80px;
    right: 12%;
    background: radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.32), rgba(165, 180, 252, 0) 70%);
  }
  .cm-modern .orb-b {
    width: 130px;
    height: 130px;
    bottom: -70px;
    left: 30%;
    background: radial-gradient(circle at 40% 40%, rgba(196, 181, 253, 0.4), rgba(196, 181, 253, 0) 70%);
    animation-delay: -4s;
  }
  .cm-modern .fx-grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
    background-size: 22px 22px;
    mask-image: linear-gradient(90deg, transparent 0%, #000 45%, transparent 100%);
  }
  .cm-modern .fx-sheen {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      110deg,
      transparent 30%,
      rgba(255, 255, 255, 0.16) 48%,
      transparent 62%
    );
    background-size: 250% 100%;
    animation: cmSheen 6s ease-in-out infinite;
  }
  .cm-modern .plan-hd-text,
  .cm-modern .plan-hd-meta {
    position: relative;
    z-index: 1;
  }
  .cm-modern .plan-hd-title {
    font-size: 17px;
    color: #fff;
    text-shadow: 0 2px 6px rgba(30, 27, 75, 0.35);
  }
  .cm-modern .plan-hd-title-inner {
    gap: 10px;
  }
  .cm-modern .plan-hd-title-icon {
    width: 34px;
    height: 34px;
    font-size: 19px;
    color: #fff;
    border-radius: 10px;
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.1));
    border: 1px solid rgba(255, 255, 255, 0.38);
    box-shadow:
      0 8px 16px -6px rgba(30, 27, 75, 0.55),
      inset 0 -3px 0 rgba(30, 27, 75, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.45);
    animation: cmIconFloat 4.5s ease-in-out infinite;
  }
  .cm-modern .plan-hd-sub {
    margin-top: 4px;
    color: rgba(255, 255, 255, 0.82);
  }
  .cm-modern .plan-hd-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
  }
  .cm-modern .plan-hd-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    height: 24px;
    padding: 0 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    color: #fff;
    font-variant-numeric: tabular-nums;
    background: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(6px);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  .cm-modern .plan-hd-chip--strong {
    background: rgba(255, 255, 255, 0.26);
    border-color: rgba(255, 255, 255, 0.5);
  }

  /* ---- カード ---- */
  .cm-modern .plan-card {
    position: relative;
    overflow: hidden;
    border: 1px solid color-mix(in srgb, var(--cm-c2) 14%, var(--el-border-color-lighter));
    border-radius: 12px;
    box-shadow:
      0 10px 24px -18px rgba(55, 48, 163, 0.45),
      0 1px 2px rgba(15, 23, 42, 0.05);
  }
  .cm-modern .plan-card::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 3px;
    z-index: 1;
  }
  .cm-modern .filter-card--panel {
    border-left: 1px solid color-mix(in srgb, var(--cm-c2) 14%, var(--el-border-color-lighter));
    padding: 12px 12px 10px;
    background: linear-gradient(
      105deg,
      color-mix(in srgb, var(--cm-c2) 6%, #fff) 0%,
      var(--el-bg-color) 55%
    );
    animation: cmRise 0.45s ease-out 0.06s backwards;
  }
  .cm-modern .filter-card--panel::before {
    background: linear-gradient(90deg, var(--cm-c1), var(--cm-c2), var(--cm-c3));
  }
  .cm-modern .result-card--panel {
    border-left: 1px solid color-mix(in srgb, var(--cm-c2) 14%, var(--el-border-color-lighter));
    padding: 10px 10px 8px;
    animation: cmRise 0.45s ease-out 0.12s backwards;
  }
  .cm-modern .result-card--panel::before {
    background: linear-gradient(90deg, #059669, #0ea5e9, var(--cm-c2));
  }
  .cm-modern .filter-form__lbl .el-icon {
    width: 20px;
    height: 20px;
    border-radius: 6px;
    color: #fff;
    font-size: 12px;
    background: linear-gradient(135deg, var(--cm-c1), var(--cm-c3));
    box-shadow: 0 3px 8px -3px rgba(79, 70, 229, 0.6);
  }
  .cm-modern .filter-form__lbl {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  .cm-modern .filter-form :deep(.el-input__wrapper),
  .cm-modern .filter-form :deep(.el-select__wrapper) {
    border-radius: 8px;
    transition: box-shadow 0.2s ease;
  }
  .cm-modern .filter-form :deep(.el-input__wrapper:hover),
  .cm-modern .filter-form :deep(.el-select__wrapper:hover) {
    box-shadow:
      0 0 0 1px color-mix(in srgb, var(--cm-c2) 45%, transparent) inset,
      0 4px 10px -6px rgba(79, 70, 229, 0.5);
  }

  /* ---- 3D キーキャップボタン ---- */
  .cm-modern .filter-form :deep(.el-button) {
    --k-edge: #3730a3;
    --k-glow: rgba(79, 70, 229, 0.5);
    border-radius: 8px;
    font-weight: 600;
    border: none;
    transition:
      transform 0.15s ease,
      box-shadow 0.15s ease,
      filter 0.15s ease;
    box-shadow:
      0 3px 0 var(--k-edge),
      0 10px 18px -8px var(--k-glow),
      inset 0 1px 0 rgba(255, 255, 255, 0.3);
  }
  .cm-modern .filter-form :deep(.el-button:not(.is-disabled):hover) {
    transform: translateY(-2px);
    filter: brightness(1.05);
    box-shadow:
      0 5px 0 var(--k-edge),
      0 14px 22px -10px var(--k-glow),
      inset 0 1px 0 rgba(255, 255, 255, 0.3);
  }
  .cm-modern .filter-form :deep(.el-button:not(.is-disabled):active) {
    transform: translateY(2px);
    box-shadow:
      0 1px 0 var(--k-edge),
      0 4px 8px -6px var(--k-glow),
      inset 0 1px 0 rgba(255, 255, 255, 0.3);
  }
  .cm-modern .filter-form :deep(.el-button.is-disabled) {
    box-shadow: none;
    transform: none;
  }
  .cm-modern .filter-form :deep(.capmx-btn-month-this) {
    --k-edge: #1e40af;
    --k-glow: rgba(37, 99, 235, 0.45);
    color: #fff;
    background: linear-gradient(180deg, #60a5fa, #2563eb);
  }
  .cm-modern .filter-form :deep(.capmx-btn-month-next) {
    --k-edge: #047857;
    --k-glow: rgba(5, 150, 105, 0.45);
    color: #fff;
    background: linear-gradient(180deg, #34d399, #059669);
  }
  .cm-modern .filter-form :deep(.capmx-btn-refresh) {
    --k-edge: #3730a3;
    --k-glow: rgba(79, 70, 229, 0.55);
    color: #fff;
    background: linear-gradient(180deg, #818cf8, #4f46e5 55%, #6d28d9);
  }
  .cm-modern .filter-form :deep(.capmx-btn-print) {
    --k-edge: #b45309;
    --k-glow: rgba(217, 119, 6, 0.45);
    color: #fff;
    background: linear-gradient(180deg, #fbbf24, #f59e0b 55%, #ea580c);
  }
  .cm-modern .filter-form :deep(.capmx-btn-print.is-disabled) {
    color: #fff;
    opacity: 0.55;
  }

  /* ---- 凡例 ---- */
  .cm-modern .matrix-legend {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin: 2px 0 8px;
  }
  .cm-modern .lg-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    height: 22px;
    padding: 0 9px 0 6px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    color: var(--el-text-color-regular);
    background: var(--el-fill-color-blank);
    border: 1px solid var(--el-border-color-lighter);
    box-shadow: 0 2px 0 var(--el-border-color-lighter);
  }
  .cm-modern .lg-sw {
    width: 12px;
    height: 12px;
    border-radius: 4px;
    border: 1px solid rgba(15, 23, 42, 0.12);
  }
  .cm-modern .lg-sw--empty {
    background: #e5e7eb;
  }
  .cm-modern .lg-sw--weekend {
    background: #fff5f5;
    border-color: #fca5a5;
  }
  .cm-modern .lg-sw--tech {
    background: #fff4e5;
    box-shadow: inset 0 0 0 2px #f5a623aa;
  }
  .cm-modern .lg-sw--maint {
    background: #eef2ff;
    box-shadow: inset 0 0 0 2px #64748baa;
  }
  .cm-modern .lg-sw--mixed {
    background: #ffedd5;
    box-shadow: inset 0 0 0 2px #ea580caa;
  }

  /* ---- マトリクス表 ---- */
  .cm-modern .matrix-wrap {
    max-height: calc(100vh - 262px);
    border-radius: 10px;
    border-color: color-mix(in srgb, var(--cm-c2) 16%, var(--el-border-color-lighter));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.6),
      0 8px 18px -14px rgba(55, 48, 163, 0.4);
  }
  .cm-modern .matrix-wrap::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  .cm-modern .matrix-wrap::-webkit-scrollbar-thumb {
    border-radius: 8px;
    background: linear-gradient(180deg, #818cf8, #6d28d9);
  }
  .cm-modern .matrix-wrap::-webkit-scrollbar-track {
    background: color-mix(in srgb, var(--cm-c2) 6%, #fff);
  }
  .cm-modern .matrix-table thead th {
    color: #fff;
    border-color: rgba(255, 255, 255, 0.18);
    background: linear-gradient(180deg, #4f46e5 0%, #3730a3 100%);
    box-shadow: inset 0 -2px 0 rgba(30, 27, 75, 0.35);
  }
  .cm-modern .matrix-table thead th.sticky-col {
    background: linear-gradient(180deg, #1d4ed8 0%, #312e81 100%);
  }
  .cm-modern .matrix-table thead .wd-hd {
    color: rgba(255, 255, 255, 0.78);
  }
  .cm-modern .matrix-table thead th.date-col.is-weekend {
    background: linear-gradient(180deg, #f43f5e 0%, #be123c 100%);
  }
  .cm-modern .matrix-table thead th.date-col.is-weekend .date-hd,
  .cm-modern .matrix-table thead th.date-col.is-weekend .wd-hd {
    color: #fff;
  }
  .cm-modern .matrix-table thead th.date-col.is-today {
    background: linear-gradient(180deg, #06b6d4 0%, #0e7490 100%);
    box-shadow:
      inset 0 -3px 0 #fde047,
      0 0 0 1px rgba(253, 224, 71, 0.6);
  }
  .cm-modern .matrix-table tbody td.sticky-col {
    color: var(--el-text-color-primary);
    background: linear-gradient(90deg, color-mix(in srgb, var(--cm-c2) 7%, #fff), #fff);
    box-shadow: 1px 0 0 var(--el-border-color-light);
    transition: box-shadow 0.15s ease;
  }
  .cm-modern .matrix-table tbody tr:hover td.sticky-col {
    color: var(--cm-c2);
    background: linear-gradient(90deg, color-mix(in srgb, var(--cm-c2) 14%, #fff), #fff);
    box-shadow:
      inset 3px 0 0 var(--cm-c2),
      1px 0 0 var(--el-border-color-light);
  }
  .cm-modern .matrix-table tbody tr:hover td.cell {
    filter: brightness(0.96) saturate(1.1);
  }
  .cm-modern .matrix-table td.cell {
    transition: filter 0.15s ease;
  }
  .cm-modern .matrix-table tbody tr {
    animation: cmRowIn 0.35s ease-out backwards;
  }
  .cm-modern .matrix-table tbody tr:nth-child(2) {
    animation-delay: 0.03s;
  }
  .cm-modern .matrix-table tbody tr:nth-child(3) {
    animation-delay: 0.06s;
  }
  .cm-modern .matrix-table tbody tr:nth-child(4) {
    animation-delay: 0.09s;
  }
  .cm-modern .matrix-table tbody tr:nth-child(n + 5) {
    animation-delay: 0.12s;
  }
  .cm-modern .matrix-empty__icon {
    width: 72px;
    height: 72px;
    font-size: 40px;
    color: #fff;
    border-radius: 18px;
    background: linear-gradient(145deg, #818cf8, #6d28d9);
    box-shadow:
      0 14px 24px -12px rgba(79, 70, 229, 0.7),
      inset 0 -4px 0 rgba(30, 27, 75, 0.25);
    animation: cmIconFloat 4.5s ease-in-out infinite;
  }
  .cm-modern :deep(.el-loading-spinner .path) {
    stroke: var(--cm-c2);
  }

  @keyframes cmRise {
    from {
      opacity: 0;
      transform: translate3d(0, 10px, 0);
    }
    to {
      opacity: 1;
      transform: none;
    }
  }
  @keyframes cmRowIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  @keyframes cmOrbFloat {
    0%,
    100% {
      transform: translate3d(0, 0, 0);
    }
    50% {
      transform: translate3d(-18px, 12px, 0);
    }
  }
  @keyframes cmSheen {
    0% {
      background-position: 130% 0;
    }
    100% {
      background-position: -30% 0;
    }
  }
  @keyframes cmIconFloat {
    0%,
    100% {
      transform: perspective(300px) rotateX(10deg) rotateY(-14deg) translateY(0);
    }
    50% {
      transform: perspective(300px) rotateX(-4deg) rotateY(12deg) translateY(-2px);
    }
  }
}

@media screen and (prefers-reduced-motion: reduce) {
  .cm-modern .plan-hd,
  .cm-modern .plan-card,
  .cm-modern .fx-orb,
  .cm-modern .fx-sheen,
  .cm-modern .plan-hd-title-icon,
  .cm-modern .matrix-empty__icon,
  .cm-modern .matrix-table tbody tr {
    animation: none;
  }
  .cm-modern .filter-form :deep(.el-button) {
    transition: none;
  }
}
</style>
