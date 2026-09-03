<template>
  <section class="cmp-panel">
    <div class="cmp-panel__glow" aria-hidden="true" />
    <div class="cmp-panel__inner">
      <header class="cmp-head">
        <div class="cmp-head__main">
          <div class="cmp-head__icon">
            <el-icon :size="20"><TrendCharts /></el-icon>
          </div>
          <div class="cmp-head__text">
            <div class="cmp-head__title-row">
              <h2 class="cmp-head__title">製品別月次対比</h2>
              <span class="cmp-head__badge">4か月比較</span>
            </div>
            <p class="cmp-head__note">
              上の製品別集計でチェック、または下で選択。指定月とその前3か月を同指標で比較
            </p>
          </div>
        </div>
        <div class="cmp-head__actions">
          <el-popover placement="bottom-end" :width="300" trigger="click" popper-class="cmp-col-popper">
            <template #reference>
              <button type="button" class="cmp-btn cmp-btn--slate">
                <el-icon><Setting /></el-icon>
                <span>列表示</span>
              </button>
            </template>
            <div class="cmp-col-picker">
              <p class="cmp-col-picker__hint">比較する指標を選んでください（製品CD・製品名は常に表示）</p>
              <el-checkbox-group v-model="visibleFieldKeys" class="cmp-col-picker__group">
                <el-checkbox v-for="f in fieldDefs" :key="f.key" :label="f.key" class="cmp-col-picker__item">
                  {{ f.label }}
                </el-checkbox>
              </el-checkbox-group>
              <el-button size="small" text type="primary" @click="resetVisibleFields">すべて表示</el-button>
            </div>
          </el-popover>
          <button
            type="button"
            class="cmp-btn cmp-btn--indigo"
            :disabled="!compareRows.length || printLoading"
            @click="printCompare"
          >
            <el-icon v-if="printLoading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Printer /></el-icon>
            <span>印刷</span>
          </button>
          <button
            type="button"
            class="cmp-btn cmp-btn--emerald"
            :disabled="!compareRows.length || exportLoading"
            @click="exportExcel"
          >
            <el-icon v-if="exportLoading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Download /></el-icon>
            <span>Excel</span>
          </button>
        </div>
      </header>

      <div class="cmp-toolbar">
        <div class="cmp-chip cmp-chip--grow">
          <span class="cmp-chip__label cmp-chip__label--sky">製品</span>
          <el-select
            v-model="selectedProductCds"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            clearable
            placeholder="上表でチェック、またはここで追加"
            size="default"
            class="cmp-toolbar__product"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.product_cd"
              :label="productOptionLabel(p)"
              :value="p.product_cd"
            />
          </el-select>
        </div>
        <div class="cmp-chip">
          <span class="cmp-chip__label cmp-chip__label--amber">指定月</span>
          <el-date-picker
            v-model="targetMonth"
            type="month"
            placeholder="YYYY-MM"
            value-format="YYYY-MM"
            size="default"
            class="cmp-toolbar__month"
          />
        </div>
        <div class="cmp-chip cmp-chip--months">
          <span class="cmp-chip__label cmp-chip__label--violet">対比月</span>
          <div class="cmp-months">
            <span v-for="m in contrastMonths" :key="m" class="cmp-month-pill">{{ formatYmJp(m) }}</span>
            <span v-if="!contrastMonths.length" class="cmp-months__empty">指定月の前3か月</span>
          </div>
        </div>
        <button type="button" class="cmp-btn cmp-btn--run" :disabled="loading" @click="runCompare">
          <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
          <el-icon v-else><TrendCharts /></el-icon>
          <span>比較</span>
        </button>
      </div>

      <div v-if="hasCompared && tableMonths.length" class="cmp-meta-bar">
        <div class="cmp-meta-bar__left">
          <span class="cmp-meta-pill cmp-meta-pill--period">
            {{ formatYmJp(tableMonths[0] || '') }} ～ {{ formatYmJp(comparedTargetMonth) }}
          </span>
          <span class="cmp-meta-pill">{{ compareRows.length }} 製品</span>
        </div>
        <div class="cmp-legend">
          <span class="cmp-legend__item"><i class="cmp-legend__dot cmp-legend__dot--good" />改善</span>
          <span class="cmp-legend__item"><i class="cmp-legend__dot cmp-legend__dot--bad" />悪化</span>
          <span class="cmp-legend__hint">矢印＝前月比</span>
        </div>
      </div>

      <div v-loading="loading" class="cmp-table-shell">
        <el-table
          v-if="compareRows.length"
          :key="compareTableKey"
          :data="compareRows"
          size="small"
          border
          stripe
          max-height="560"
          class="cmp-table"
        >
          <el-table-column
            prop="product_cd"
            label="製品CD"
            width="96"
            fixed
            class-name="scrap-td--sku"
            label-class-name="scrap-th--sku"
          />
          <el-table-column
            prop="product_name"
            label="製品名"
            min-width="140"
            show-overflow-tooltip
            fixed
            class-name="scrap-td--name"
            label-class-name="scrap-th--name"
          />
          <el-table-column
            v-for="f in visibleFields"
            :key="f.key"
            :label="f.label"
            align="center"
          >
            <el-table-column
              v-for="m in tableMonths"
              :key="`${f.key}-${m}`"
              :label="formatYmShort(m)"
              min-width="108"
              align="right"
              :class-name="monthCellClass(m)"
              :label-class-name="monthHeadClass(m)"
            >
              <template #header>
                <span :class="{ 'cmp-ym--target': m === comparedTargetMonth }">
                  {{ formatYmShort(m) }}
                  <span v-if="m === comparedTargetMonth" class="cmp-ym-badge">指定</span>
                </span>
              </template>
              <template #default="{ row }">
                <span class="cmp-cell">
                  <span class="cmp-cell__val">{{ formatCompareCell(row, m, f.key) }}</span>
                  <el-icon
                    v-if="monthTrend(row, m, f.key) === 'up'"
                    class="cmp-trend"
                    :class="trendToneClass(f.key, 'up')"
                    title="前月比上昇"
                  >
                    <Top />
                  </el-icon>
                  <el-icon
                    v-else-if="monthTrend(row, m, f.key) === 'down'"
                    class="cmp-trend"
                    :class="trendToneClass(f.key, 'down')"
                    title="前月比下降"
                  >
                    <Bottom />
                  </el-icon>
                  <span
                    v-else-if="monthTrend(row, m, f.key) === 'flat'"
                    class="cmp-trend cmp-trend--flat"
                    title="前月と同値"
                  >→</span>
                </span>
              </template>
            </el-table-column>
          </el-table-column>
        </el-table>
        <div v-else class="cmp-empty">
          <div class="cmp-empty__icon">
            <el-icon :size="28"><TrendCharts /></el-icon>
          </div>
          <p class="cmp-empty__title">まだ比較結果がありません</p>
          <p class="cmp-empty__desc">{{ emptyDescription }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Bottom,
  Download,
  Loading,
  Printer,
  Setting,
  Top,
  TrendCharts,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getQualityRateByProduct } from '@/api/database'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import { downloadExcelFromAoa } from '@/utils/excelExport'
import { guardMesOperation } from '@/utils/mesOperationGuard'
import { openPrintWindow, PRINT_POPUP_BLOCKED_MSG } from '@/utils/printWindow'

const props = defineProps<{
  productOptions: Array<{ product_cd: string; product_name?: string | null }>
}>()

const selectedProductCds = defineModel<string[]>('selectedProductCds', { default: () => [] })

const { canExport } = useMesOperationPermission()

const DEFAULT_MAIN_LINE: Array<{ key: string; label: string }> = [
  { key: 'cutting', label: '切断' },
  { key: 'chamfering', label: '面取' },
  { key: 'molding', label: '成型' },
  { key: 'plating', label: 'メッキ' },
  { key: 'welding', label: '溶接' },
  { key: 'inspection', label: '検査' },
]
const MAIN_LINE_KEYS_ORDER = DEFAULT_MAIN_LINE.map((c) => c.key)
const COL_STORAGE_KEY = 'scrapRate.productMonthCompare.visibleFields'

type ProductMatrixRow = {
  product_cd: string
  product_name: string
  all_processes_defect_scrap: number
  processes: Array<{
    key: string
    label: string
    sum_actual: number
    sum_defect: number
    sum_scrap: number
    sum_defect_and_scrap: number
    rate: number | null
    rate_percent: number | null
  }>
}

type CompareRow = {
  product_cd: string
  product_name: string
  byMonth: Record<string, ProductMatrixRow | undefined>
}

type FieldDef = { key: string; label: string }

const mainLineLabels = ref(DEFAULT_MAIN_LINE)

const fieldDefs = computed<FieldDef[]>(() => [
  { key: 'all_processes_defect_scrap', label: '不良＋廃棄' },
  ...mainLineLabels.value.map((c) => ({ key: c.key, label: `${c.label}（％）` })),
  { key: 'rty_loss', label: '廃棄率' },
  { key: 'rty', label: '合格率' },
])

const allFieldKeys = computed(() => fieldDefs.value.map((f) => f.key))

function loadVisibleFields(): string[] {
  try {
    const raw = localStorage.getItem(COL_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((k): k is string => typeof k === 'string')
  } catch {
    return []
  }
}

const storedKeys = loadVisibleFields()
const visibleFieldKeys = ref<string[]>(storedKeys.length ? storedKeys : [...allFieldKeys.value])

watch(
  allFieldKeys,
  (keys) => {
    const allowed = new Set(keys)
    const next = visibleFieldKeys.value.filter((k) => allowed.has(k))
    if (!next.length) {
      visibleFieldKeys.value = [...keys]
      return
    }
    if (next.length !== visibleFieldKeys.value.length) {
      visibleFieldKeys.value = next
    }
  },
  { immediate: true },
)

watch(
  visibleFieldKeys,
  (keys) => {
    try {
      localStorage.setItem(COL_STORAGE_KEY, JSON.stringify(keys))
    } catch {
      /* ignore */
    }
  },
  { deep: true },
)

const visibleFields = computed(() => fieldDefs.value.filter((f) => visibleFieldKeys.value.includes(f.key)))

const compareTableKey = computed(
  () => `${visibleFieldKeys.value.join('|')}|${tableMonths.value.join('|')}|${comparedTargetMonth.value}`,
)

function resetVisibleFields() {
  visibleFieldKeys.value = [...allFieldKeys.value]
}

const today = new Date()
const targetMonth = ref(
  `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`,
)
const loading = ref(false)
const printLoading = ref(false)
const exportLoading = ref(false)
const hasCompared = ref(false)
const compareRows = ref<CompareRow[]>([])
const tableMonths = ref<string[]>([])
const comparedTargetMonth = ref('')

const contrastMonths = computed(() => {
  const ym = targetMonth.value
  if (!ym) return []
  return [-3, -2, -1].map((d) => shiftMonth(ym, d))
})

const emptyDescription = computed(() => {
  if (!hasCompared.value) {
    return '上の製品別集計で製品をチェック（またはここで選択）し、指定月を選んで「比較」'
  }
  return '該当データがありません'
})

function shiftMonth(ym: string, delta: number): string {
  const [ys, ms] = ym.split('-')
  const y = Number(ys)
  const m = Number(ms)
  const d = new Date(y, m - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function monthDateRange(ym: string): [string, string] {
  const [ys, ms] = ym.split('-')
  const y = Number(ys)
  const m = Number(ms)
  const last = new Date(y, m, 0).getDate()
  const pad = String(m).padStart(2, '0')
  return [`${y}-${pad}-01`, `${y}-${pad}-${String(last).padStart(2, '0')}`]
}

function formatYmJp(ym: string) {
  const [ys, ms] = ym.split('-')
  return `${ys}年${Number(ms)}月`
}

function formatYmShort(ym: string) {
  const [ys, ms] = ym.split('-')
  return `${ys}/${ms}`
}

function productOptionLabel(p: { product_cd: string; product_name?: string | null }) {
  const name = (p.product_name || '').trim()
  return name ? `${name}（${p.product_cd}）` : p.product_cd
}

function monthCellClass(m: string) {
  return m === comparedTargetMonth.value
    ? 'scrap-td--num cmp-td--target'
    : 'scrap-td--num'
}

function monthHeadClass(m: string) {
  return m === comparedTargetMonth.value
    ? 'scrap-th--num cmp-th--target'
    : 'scrap-th--num'
}

function fmtInt(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return '—'
  return n.toLocaleString('ja-JP')
}

function computeProductMainLineRty(row: ProductMatrixRow): { rty: number; loss: number } | null {
  let prod = 1
  let used = false
  for (const key of MAIN_LINE_KEYS_ORDER) {
    const p = row.processes?.find((x) => x.key === key)
    if (!p) continue
    const sa = p.sum_actual ?? 0
    if (sa <= 0) continue
    const bad = p.sum_defect_and_scrap ?? 0
    let r = bad / sa
    if (r > 1) r = 1
    if (r < 0) r = 0
    prod *= 1 - r
    used = true
  }
  if (!used) return null
  return { rty: prod * 100, loss: (1 - prod) * 100 }
}

function formatCompareCell(row: CompareRow, ym: string, fieldKey: string) {
  const metrics = row.byMonth[ym]
  if (!metrics) return '—'
  if (fieldKey === 'all_processes_defect_scrap') return fmtInt(metrics.all_processes_defect_scrap)
  if (fieldKey === 'rty_loss') {
    const x = computeProductMainLineRty(metrics)
    return x ? `${x.loss.toFixed(2)} %` : '—'
  }
  if (fieldKey === 'rty') {
    const x = computeProductMainLineRty(metrics)
    return x ? `${x.rty.toFixed(2)} %` : '—'
  }
  const p = metrics.processes?.find((x) => x.key === fieldKey)
  if (!p || p.rate_percent == null) return '—'
  return `${p.rate_percent.toFixed(2)} %`
}

/** 比較用の数値。欠損は null */
function numericCompareValue(row: CompareRow, ym: string, fieldKey: string): number | null {
  const metrics = row.byMonth[ym]
  if (!metrics) return null
  if (fieldKey === 'all_processes_defect_scrap') {
    const n = Number(metrics.all_processes_defect_scrap)
    return Number.isFinite(n) ? n : null
  }
  if (fieldKey === 'rty_loss') {
    const x = computeProductMainLineRty(metrics)
    return x ? Number(x.loss.toFixed(4)) : null
  }
  if (fieldKey === 'rty') {
    const x = computeProductMainLineRty(metrics)
    return x ? Number(x.rty.toFixed(4)) : null
  }
  const p = metrics.processes?.find((x) => x.key === fieldKey)
  if (!p || p.rate_percent == null) return null
  const n = Number(p.rate_percent)
  return Number.isFinite(n) ? n : null
}

function previousMonth(ym: string): string | null {
  const idx = tableMonths.value.indexOf(ym)
  if (idx <= 0) return null
  return tableMonths.value[idx - 1] ?? null
}

type MonthTrend = 'up' | 'down' | 'flat' | null

function monthTrend(row: CompareRow, ym: string, fieldKey: string): MonthTrend {
  const prev = previousMonth(ym)
  if (!prev) return null
  const cur = numericCompareValue(row, ym, fieldKey)
  const before = numericCompareValue(row, prev, fieldKey)
  if (cur == null || before == null) return null
  const eps = fieldKey === 'all_processes_defect_scrap' ? 0 : 0.005
  if (Math.abs(cur - before) <= eps) return 'flat'
  return cur > before ? 'up' : 'down'
}

/** 合格率のみ上昇＝良い（緑）。それ以外（廃棄・不良系）は上昇＝悪い（赤） */
function fieldHigherIsBetter(fieldKey: string) {
  return fieldKey === 'rty'
}

function trendToneClass(fieldKey: string, trend: 'up' | 'down') {
  const good = fieldHigherIsBetter(fieldKey) ? trend === 'up' : trend === 'down'
  return good ? 'cmp-trend--good' : 'cmp-trend--bad'
}

function trendArrowChar(trend: MonthTrend): string {
  if (trend === 'up') return '↑'
  if (trend === 'down') return '↓'
  if (trend === 'flat') return '→'
  return ''
}

function excelCellValue(row: CompareRow, ym: string, fieldKey: string): string | number {
  const metrics = row.byMonth[ym]
  if (!metrics) return ''
  if (fieldKey === 'all_processes_defect_scrap') {
    const n = metrics.all_processes_defect_scrap
    return n == null || Number.isNaN(n) ? '' : n
  }
  if (fieldKey === 'rty_loss') {
    const x = computeProductMainLineRty(metrics)
    return x ? Number(x.loss.toFixed(2)) : ''
  }
  if (fieldKey === 'rty') {
    const x = computeProductMainLineRty(metrics)
    return x ? Number(x.rty.toFixed(2)) : ''
  }
  const p = metrics.processes?.find((x) => x.key === fieldKey)
  if (!p || p.rate_percent == null) return ''
  return Number(p.rate_percent.toFixed(2))
}

type QualityProductPayload = {
  main_line_labels?: Array<{ key: string; label: string }>
  products?: ProductMatrixRow[]
}

function unwrapQualityRateByProductPayload(res: unknown): QualityProductPayload | null {
  if (res == null || typeof res !== 'object') return null
  const r = res as Record<string, unknown>
  const inner = r.data
  if (inner != null && typeof inner === 'object') {
    const mid = inner as Record<string, unknown>
    const nested = mid.data
    if (nested != null && typeof nested === 'object' && Array.isArray((nested as QualityProductPayload).products)) {
      return nested as QualityProductPayload
    }
    if (Array.isArray((inner as QualityProductPayload).products)) {
      return inner as QualityProductPayload
    }
  }
  if (Array.isArray((r as QualityProductPayload).products)) {
    return r as QualityProductPayload
  }
  return null
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

async function runCompare() {
  const cds = selectedProductCds.value.map((c) => String(c).trim()).filter(Boolean)
  if (!cds.length) {
    ElMessage.warning('製品を選択してください')
    return
  }
  if (cds.length > 100) {
    ElMessage.warning('製品は最大100件まで選択できます')
    return
  }
  const ym = targetMonth.value
  if (!ym) {
    ElMessage.warning('指定月を選択してください')
    return
  }
  const months = [...contrastMonths.value, ym]
  loading.value = true
  try {
    const results = await Promise.all(
      months.map(async (m) => {
        const [startDate, endDate] = monthDateRange(m)
        const res = await getQualityRateByProduct({
          startDate,
          endDate,
          page: 1,
          limit: 500,
          productCds: cds.join(','),
        })
        return { ym: m, payload: unwrapQualityRateByProductPayload(res) }
      }),
    )
    const labels = results
      .map((r) => r.payload?.main_line_labels)
      .find((x) => x && x.length)
    if (labels?.length) mainLineLabels.value = labels

    const byCd = new Map<string, Record<string, ProductMatrixRow>>()
    for (const { ym: m, payload } of results) {
      for (const p of payload?.products ?? []) {
        const cd = (p.product_cd || '').trim()
        if (!cd) continue
        if (!byCd.has(cd)) byCd.set(cd, {})
        byCd.get(cd)![m] = p
      }
    }

    const nameByCd = new Map(props.productOptions.map((p) => [p.product_cd, p.product_name || '']))
    compareRows.value = cds.map((cd) => {
      const monthMap = byCd.get(cd) || {}
      const named =
        Object.values(monthMap).find((r) => (r.product_name || '').trim())?.product_name ||
        nameByCd.get(cd) ||
        ''
      return { product_cd: cd, product_name: named, byMonth: monthMap }
    })
    tableMonths.value = months
    comparedTargetMonth.value = ym
    hasCompared.value = true
  } catch (e) {
    console.error(e)
    ElMessage.error('月次対比データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function selectedProductSummary(): string {
  const names = selectedProductCds.value.map((cd) => {
    const p = props.productOptions.find((x) => x.product_cd === cd)
    return p ? productOptionLabel(p) : cd
  })
  if (names.length <= 8) return names.join('、')
  return `${names.slice(0, 8).join('、')} ほか ${names.length - 8} 件`
}

function buildComparePrintHtml(): string {
  const months = tableMonths.value
  const fields = visibleFields.value
  const target = comparedTargetMonth.value
  const contrastLabel = contrastMonthsForPrint()
  const monthTh = months
    .map((m) => {
      const mark = m === target ? ' class="target"' : ''
      return `<th${mark}>${escapeHtml(formatYmShort(m))}</th>`
    })
    .join('')
  const groupTh = fields
    .map((f) => `<th colspan="${months.length}">${escapeHtml(f.label)}</th>`)
    .join('')
  const bodyRows = compareRows.value
    .map((row) => {
      const tds = [
        `<td class="num">${escapeHtml(row.product_cd)}</td>`,
        `<td>${escapeHtml(row.product_name || '')}</td>`,
        ...fields.flatMap((f) =>
          months.map((m) => {
            const mark = m === target ? ' target' : ''
            const trend = monthTrend(row, m, f.key)
            const arrow = trendArrowChar(trend)
            let trendHtml = ''
            if (arrow && trend && trend !== 'flat') {
              const tone = trendToneClass(f.key, trend)
              const cls = tone === 'cmp-trend--good' ? 'good' : 'bad'
              trendHtml = ` <span class="${cls}">${arrow}</span>`
            } else if (trend === 'flat') {
              trendHtml = ' <span class="flat">→</span>'
            }
            return `<td class="num${mark}">${escapeHtml(formatCompareCell(row, m, f.key))}${trendHtml}</td>`
          }),
        ),
      ]
      return `<tr>${tds.join('')}</tr>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>製品別月次対比</title>
  <style>
    @page { size: A4 landscape; margin: 8mm 10mm; }
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body {
      font-family: 'Segoe UI', 'Hiragino Sans', 'Meiryo', sans-serif;
      font-size: 10px;
      color: #0f172a;
      margin: 14px 18px;
    }
    h1 { font-size: 15px; margin: 0 0 8px; }
    .meta { margin: 3px 0; color: #475569; font-size: 10.5px; }
    table { border-collapse: collapse; width: 100%; margin-top: 8px; }
    th, td { border: 1px solid #94a3b8; padding: 3px 5px; vertical-align: middle; }
    th { background: #e2e8f0; font-weight: 600; text-align: center; font-size: 9.5px; }
    th.target, td.target { background: #fef3c7; font-weight: 700; }
    td.num { text-align: right; font-variant-numeric: tabular-nums; }
    span.good { color: #059669; font-weight: 700; }
    span.bad { color: #e11d48; font-weight: 700; }
    span.flat { color: #94a3b8; }
    @media print {
      body { margin: 0; padding: 0; font-size: 9px; }
    }
  </style>
</head>
<body>
  <h1>廃棄率分析 · 製品別月次対比</h1>
  <p class="meta">指定月: ${escapeHtml(formatYmJp(target))}　対比月: ${escapeHtml(contrastLabel)}</p>
  <p class="meta">製品: ${escapeHtml(selectedProductSummary())}</p>
  <p class="meta">件数: ${compareRows.value.length} 件</p>
  <table>
    <thead>
      <tr>
        <th rowspan="2">製品CD</th>
        <th rowspan="2">製品名</th>
        ${groupTh}
      </tr>
      <tr>${fields.map(() => monthTh).join('')}</tr>
    </thead>
    <tbody>${bodyRows}</tbody>
  </table>
</body>
</html>`
}

function contrastMonthsForPrint() {
  const months = tableMonths.value.filter((m) => m !== comparedTargetMonth.value)
  return months.map(formatYmJp).join('、') || '—'
}

async function printCompare() {
  if (!guardMesOperation(canExport)) return
  if (!compareRows.value.length) {
    ElMessage.info('印刷するデータがありません')
    return
  }
  if (!visibleFields.value.length) {
    ElMessage.warning('表示する指標を1つ以上選んでください')
    return
  }
  printLoading.value = true
  try {
    const html = buildComparePrintHtml()
    const ok = openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 400 })
    if (!ok) ElMessage.warning(PRINT_POPUP_BLOCKED_MSG)
  } catch (e) {
    console.error(e)
    ElMessage.error('印刷に失敗しました')
  } finally {
    printLoading.value = false
  }
}

async function exportExcel() {
  if (!guardMesOperation(canExport)) return
  if (!compareRows.value.length) {
    ElMessage.info('出力するデータがありません')
    return
  }
  if (!visibleFields.value.length) {
    ElMessage.warning('表示する指標を1つ以上選んでください')
    return
  }
  exportLoading.value = true
  try {
    const months = tableMonths.value
    const fields = visibleFields.value
    const header: (string | number)[] = ['製品CD', '製品名']
    for (const f of fields) {
      for (const m of months) {
        const mark = m === comparedTargetMonth.value ? '（指定）' : ''
        header.push(`${f.label} ${formatYmShort(m)}${mark}`)
      }
    }
    const aoa: (string | number)[][] = [header]
    for (const row of compareRows.value) {
      const line: (string | number)[] = [row.product_cd, row.product_name || '']
      for (const f of fields) {
        for (const m of months) {
          const v = excelCellValue(row, m, f.key)
          const trend = monthTrend(row, m, f.key)
          const arrow = trendArrowChar(trend)
          if (arrow && (typeof v === 'number' || (typeof v === 'string' && v !== ''))) {
            line.push(`${v}${arrow}`)
          } else {
            line.push(v)
          }
        }
      }
      aoa.push(line)
    }
    const ym = comparedTargetMonth.value || targetMonth.value
    await downloadExcelFromAoa(aoa, '製品月次対比', `廃棄率分析_製品月次対比_${ym}.xlsx`)
  } catch (e) {
    console.error(e)
    ElMessage.error('Excel出力に失敗しました')
  } finally {
    exportLoading.value = false
  }
}
</script>

<style scoped>
.cmp-panel {
  --cmp-sky: #0284c7;
  --cmp-sky-soft: #e0f2fe;
  --cmp-amber: #d97706;
  --cmp-amber-soft: #fffbeb;
  --cmp-indigo: #4f46e5;
  --cmp-emerald: #059669;
  --cmp-rose: #e11d48;
  position: relative;
  margin-top: 14px;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(14, 165, 233, 0.18);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.97) 0%, rgba(240, 249, 255, 0.94) 48%, rgba(255, 251, 235, 0.9) 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 10px 28px rgba(14, 165, 233, 0.08),
    0 22px 48px rgba(15, 23, 42, 0.07);
}

.cmp-panel::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: linear-gradient(90deg, #0ea5e9 0%, #38bdf8 35%, #f59e0b 70%, #fbbf24 100%);
  z-index: 2;
}

.cmp-panel__glow {
  position: absolute;
  width: 280px;
  height: 180px;
  right: -40px;
  top: -60px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.16), transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.cmp-panel__inner {
  position: relative;
  z-index: 1;
  padding: 16px 16px 18px;
}

.cmp-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px 16px;
  margin-bottom: 14px;
}

.cmp-head__main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.cmp-head__icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(145deg, #38bdf8 0%, #0284c7 55%, #0369a1 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 10px 22px rgba(2, 132, 199, 0.35);
  flex-shrink: 0;
}

.cmp-head__text {
  min-width: 0;
}

.cmp-head__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.cmp-head__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.cmp-head__badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #0369a1;
  background: linear-gradient(180deg, #e0f2fe, #bae6fd);
  border: 1px solid rgba(14, 165, 233, 0.28);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset;
}

.cmp-head__note {
  margin: 4px 0 0;
  font-size: 0.72rem;
  line-height: 1.45;
  color: #64748b;
}

.cmp-head__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cmp-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.15s ease;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.4) inset;
}

.cmp-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.cmp-btn:active:not(:disabled) {
  transform: translateY(0);
}

.cmp-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.cmp-btn--slate {
  color: #334155;
  background: linear-gradient(180deg, #f8fafc, #e2e8f0);
  border-color: rgba(100, 116, 139, 0.28);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 10px rgba(15, 23, 42, 0.06);
}

.cmp-btn--slate:hover:not(:disabled) {
  background: linear-gradient(180deg, #fff, #e2e8f0);
}

.cmp-btn--indigo {
  color: #fff;
  background: linear-gradient(145deg, #818cf8 0%, #4f46e5 55%, #4338ca 100%);
  border-color: rgba(67, 56, 202, 0.35);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.28) inset,
    0 8px 16px rgba(79, 70, 229, 0.28);
}

.cmp-btn--indigo:hover:not(:disabled) {
  filter: brightness(1.05);
}

.cmp-btn--emerald {
  color: #fff;
  background: linear-gradient(145deg, #34d399 0%, #059669 55%, #047857 100%);
  border-color: rgba(4, 120, 87, 0.35);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.28) inset,
    0 8px 16px rgba(5, 150, 105, 0.28);
}

.cmp-btn--emerald:hover:not(:disabled) {
  filter: brightness(1.05);
}

.cmp-btn--run {
  height: 38px;
  padding: 0 18px;
  color: #fff;
  font-size: 0.82rem;
  border-radius: 12px;
  background: linear-gradient(145deg, #38bdf8 0%, #0284c7 50%, #0369a1 100%);
  border-color: rgba(3, 105, 161, 0.4);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 10px 22px rgba(2, 132, 199, 0.35);
}

.cmp-btn--run:hover:not(:disabled) {
  filter: brightness(1.06);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 14px 28px rgba(2, 132, 199, 0.42);
}

.cmp-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 12px;
  padding: 12px;
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.85), rgba(248, 250, 252, 0.72));
  border: 1px solid rgba(148, 163, 184, 0.28);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 6px 18px rgba(15, 23, 42, 0.04);
}

.cmp-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 6px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}

.cmp-chip--grow {
  flex: 1 1 260px;
}

.cmp-chip--months {
  flex: 1 1 200px;
}

.cmp-chip__label {
  flex-shrink: 0;
  padding: 3px 8px;
  border-radius: 8px;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.cmp-chip__label--sky {
  color: #0369a1;
  background: linear-gradient(180deg, #e0f2fe, #bae6fd);
}

.cmp-chip__label--amber {
  color: #92400e;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
}

.cmp-chip__label--violet {
  color: #5b21b6;
  background: linear-gradient(180deg, #ede9fe, #ddd6fe);
}

.cmp-toolbar__product {
  width: min(360px, 100%);
  flex: 1 1 180px;
}

.cmp-toolbar__month {
  width: 132px;
}

.cmp-months {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
}

.cmp-month-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #5b21b6;
  background: linear-gradient(180deg, #f5f3ff, #ede9fe);
  border: 1px solid rgba(139, 92, 246, 0.22);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.85) inset;
}

.cmp-months__empty {
  font-size: 0.72rem;
  color: #94a3b8;
}

.cmp-meta-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
  margin-bottom: 10px;
}

.cmp-meta-bar__left {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.cmp-meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.cmp-meta-pill--period {
  color: #0369a1;
  background: linear-gradient(180deg, #f0f9ff, #e0f2fe);
  border-color: rgba(14, 165, 233, 0.28);
}

.cmp-legend {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(226, 232, 240, 0.95);
}

.cmp-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  color: #475569;
}

.cmp-legend__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
}

.cmp-legend__dot--good {
  background: #059669;
}

.cmp-legend__dot--bad {
  background: #e11d48;
}

.cmp-legend__hint {
  font-size: 0.65rem;
  color: #94a3b8;
}

.cmp-table-shell {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  min-height: 180px;
  border: 1px solid rgba(148, 163, 184, 0.32);
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 8px 24px rgba(15, 23, 42, 0.05);
}

.cmp-table {
  width: 100%;
}

.cmp-table :deep(.el-table__header-wrapper .el-table__cell) {
  padding: 8px 8px;
  font-size: 11px;
  font-weight: 700;
  color: #334155;
  background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%) !important;
}

.cmp-table :deep(.el-table__body .el-table__cell) {
  padding: 7px 8px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.cmp-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: rgba(224, 242, 254, 0.45) !important;
}

.cmp-table :deep(th.cmp-th--target) {
  background: linear-gradient(180deg, #fef3c7 0%, #fbbf24 100%) !important;
  color: #78350f !important;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.45) inset;
}

.cmp-table :deep(td.cmp-td--target) {
  background: linear-gradient(180deg, rgba(254, 243, 199, 0.55), rgba(253, 230, 138, 0.35));
  font-weight: 700;
  box-shadow: inset 2px 0 0 rgba(245, 158, 11, 0.55);
}

.cmp-ym--target {
  color: #92400e;
}

.cmp-ym-badge {
  display: inline-block;
  margin-left: 3px;
  padding: 1px 5px;
  border-radius: 6px;
  font-size: 9px;
  font-weight: 800;
  background: linear-gradient(145deg, #fbbf24, #d97706);
  color: #fff;
  vertical-align: middle;
  box-shadow: 0 2px 6px rgba(217, 119, 6, 0.35);
}

.cmp-cell {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 3px;
  width: 100%;
}

.cmp-cell__val {
  min-width: 0;
}

.cmp-trend {
  flex-shrink: 0;
  font-size: 13px;
  filter: drop-shadow(0 1px 1px rgba(15, 23, 42, 0.12));
}

.cmp-trend--good {
  color: #059669;
}

.cmp-trend--bad {
  color: #e11d48;
}

.cmp-trend--flat {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.cmp-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 180px;
  padding: 28px 16px;
  text-align: center;
}

.cmp-empty__icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  margin-bottom: 4px;
  border-radius: 16px;
  color: #0284c7;
  background: linear-gradient(145deg, #e0f2fe, #bae6fd);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 8px 18px rgba(2, 132, 199, 0.15);
}

.cmp-empty__title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 800;
  color: #334155;
}

.cmp-empty__desc {
  margin: 0;
  max-width: 360px;
  font-size: 0.72rem;
  line-height: 1.5;
  color: #94a3b8;
}

.cmp-col-picker__hint {
  margin: 0 0 8px;
  font-size: 12px;
  color: #64748b;
}

.cmp-col-picker__group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 8px;
  margin-bottom: 8px;
}

.cmp-col-picker__item {
  margin-right: 0 !important;
}

@media (max-width: 768px) {
  .cmp-panel__inner {
    padding: 14px 12px 16px;
  }

  .cmp-toolbar__product,
  .cmp-toolbar__month {
    width: 100%;
  }

  .cmp-chip,
  .cmp-chip--grow,
  .cmp-chip--months {
    flex: 1 1 100%;
  }

  .cmp-btn--run {
    width: 100%;
    justify-content: center;
  }

  .cmp-head__note {
    display: none;
  }
}
</style>
