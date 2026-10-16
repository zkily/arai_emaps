<template>
  <div class="wit-page wit-modern pb-std">
    <header class="page-toolbar pb-hero pb-hero--page">
      <div class="page-toolbar-glow" aria-hidden="true" />
      <div class="pb-bubbles" aria-hidden="true" />
      <div class="toolbar-left">
        <div class="toolbar-brand">
          <div class="toolbar-icon-wrap">
            <el-icon class="toolbar-icon"><Histogram /></el-icon>
          </div>
          <div class="toolbar-text">
            <h1 class="toolbar-title pb-hero-title">溶接品在庫推移</h1>
            <p class="toolbar-desc pb-hero-desc">
              社内溶接（KT07）の内示・在庫・計画／実績と部品消費を日別に表示します。セルは編集できません。
            </p>
          </div>
        </div>
      </div>
      <div class="toolbar-right wit-kpis" aria-label="件数">
        <article class="wit-kpi wit-kpi--blue">
          <span class="wit-kpi__icon"><el-icon :size="16"><Box /></el-icon></span>
          <div class="wit-kpi__body">
            <span>製品</span>
            <strong>{{ data ? data.product_count : '－' }}</strong>
          </div>
        </article>
        <article class="wit-kpi wit-kpi--rose">
          <span class="wit-kpi__icon"><el-icon :size="16"><WarningFilled /></el-icon></span>
          <div class="wit-kpi__body">
            <span>不足</span>
            <strong>{{ data ? data.shortage_count : '－' }}</strong>
          </div>
        </article>
      </div>
    </header>

    <section class="wit-filter">
      <label class="wit-field">
        <span>期間</span>
        <div class="wit-period">
          <div class="month-quick" role="group" aria-label="月ショートカット">
            <button type="button" class="month-quick__btn" :disabled="loading" @click="setMonth(-1)">前月</button>
            <button
              type="button"
              class="month-quick__btn month-quick__btn--mid"
              :disabled="loading"
              @click="setMonth(0)"
            >
              当月
            </button>
            <button type="button" class="month-quick__btn" :disabled="loading" @click="setMonth(1)">翌月</button>
          </div>
          <el-date-picker
            v-model="range"
            type="daterange"
            size="small"
            value-format="YYYY-MM-DD"
            range-separator="〜"
            start-placeholder="開始"
            end-placeholder="終了"
            :clearable="false"
          />
        </div>
      </label>
      <label class="wit-field">
        <span>製品</span>
        <el-input
          v-model="keyword"
          size="small"
          clearable
          placeholder="製品CD / 名称"
        />
      </label>
      <label class="wit-field">
        <span>部品</span>
        <el-input
          v-model="partCd"
          size="small"
          clearable
          placeholder="部品CD / 名称"
        />
      </label>
      <el-checkbox v-model="shortageOnly" class="wit-check">不足のみ</el-checkbox>
      <div class="wit-filter__btns">
        <el-button class="tb-btn tb-btn-teal" size="small" :disabled="!data?.products.length" @click="toggleAll">
          <el-icon><Expand /></el-icon>
          <span class="tb-label">{{ allExpanded ? 'すべて折りたたむ' : 'すべて展開' }}</span>
        </el-button>
        <el-button class="tb-btn tb-btn-green" size="small" :disabled="!data?.products.length" @click="exportExcel">
          <el-icon><Download /></el-icon>
          <span class="tb-label">Excel</span>
        </el-button>
      </div>
    </section>

    <section v-loading="loading" class="wit-table">
      <WeldingTrendMatrix
        v-if="data"
        :dates="data.dates"
        :rows="matrixRows"
        :expanded="expanded"
        @toggle="toggleProduct"
      />
      <el-empty v-else-if="!loading" description="条件に一致するデータがありません" />
      <footer v-if="data" class="wit-foot">
        <span class="wit-pill">表示 {{ data.products.length }} 件</span>
        <span class="wit-pill wit-pill--rose">不足 {{ data.shortage_count }}</span>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { Box, Download, Expand, Histogram, WarningFilled } from '@element-plus/icons-vue'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'
import {
  WELDING_METRICS,
  fetchWeldingInventoryTrend,
  type WeldingMetricKey,
  type WeldingTrendData,
  type WeldingTrendProduct,
} from '@/api/erp/weldingInventoryTrend'
import { getJSTToday } from '@/utils/dateFormat'
import WeldingTrendMatrix, {
  type TrendMatrixRow,
} from './WeldingTrendMatrix.vue'

function monthRange(offset = 0): [string, string] {
  const base = dayjs(getJSTToday()).add(offset, 'month')
  return [base.startOf('month').format('YYYY-MM-DD'), base.endOf('month').format('YYYY-MM-DD')]
}

/** 当日の前営業日（土日を除く） */
function prevWorkday(fromYmd = getJSTToday()) {
  let d = dayjs(fromYmd).subtract(1, 'day')
  while (d.day() === 0 || d.day() === 6) {
    d = d.subtract(1, 'day')
  }
  return d
}

/** デフォルト期間：前営業日 〜 +45日 */
function defaultRange(): [string, string] {
  const start = prevWorkday()
  return [start.format('YYYY-MM-DD'), start.add(45, 'day').format('YYYY-MM-DD')]
}

const range = ref<[string, string]>(defaultRange())
const keyword = ref('')
const partCd = ref('')
const shortageOnly = ref(false)
const loading = ref(false)
const data = ref<WeldingTrendData | null>(null)
const expanded = ref<Set<string>>(new Set())

let loadTimer: ReturnType<typeof setTimeout> | null = null
let loadSeq = 0

function setMonth(offset: number) {
  range.value = monthRange(offset)
}

function scheduleLoad(delay = 0) {
  if (loadTimer) clearTimeout(loadTimer)
  loadTimer = setTimeout(() => {
    loadTimer = null
    void load()
  }, delay)
}

const allProducts = computed(() => data.value?.products ?? [])

const allExpanded = computed(() => {
  const list = allProducts.value
  return list.length > 0 && list.every((p) => expanded.value.has(p.product_cd))
})

const matrixRows = computed(() => {
  const dates = data.value?.dates ?? []
  return buildRows(allProducts.value, dates, expanded.value)
})

function sumOf(daily: Record<string, number>, dates: string[]): number {
  return dates.reduce((s, d) => s + (daily[d] ?? 0), 0)
}

function endOf(daily: Record<string, number>, dates: string[]): number {
  if (!dates.length) return 0
  return daily[dates[dates.length - 1]] ?? 0
}

/** 部品在庫：不足を検知した日以降は「在庫−予定使用」を負数で表示 */
function stockDisplayFromShortage(
  stock: Record<string, number>,
  usage: Record<string, number>,
  dates: string[],
): Record<string, number> {
  const out: Record<string, number> = {}
  let shortStarted = false
  for (const d of dates) {
    const have = stock[d] ?? 0
    const need = usage[d] ?? 0
    if (!shortStarted && need > 0 && have < need) {
      shortStarted = true
    }
    if (shortStarted) {
      out[d] = have - need
    } else if (have) {
      out[d] = have
    }
  }
  return out
}

function buildRows(
  products: WeldingTrendProduct[],
  dates: string[],
  open: Set<string>,
): TrendMatrixRow[] {
  const rows: TrendMatrixRow[] = []
  for (const p of products) {
    const trend = (p.metrics.welding_trend || {}) as Record<string, number>
    const productLabel = (p.product_name || '').trim() || p.product_cd
    rows.push({
      rowKey: `${p.product_cd}::__summary`,
      productCd: p.product_cd,
      kind: 'summary',
      label: productLabel,
      sub: '溶接推移',
      depth: 0,
      expandable: true,
      dash: false,
      shortage: p.has_shortage,
      daily: trend,
      summaryValue: endOf(trend, dates),
      chartable: true,
    })
    if (!open.has(p.product_cd)) continue
    for (const metric of WELDING_METRICS) {
      const series = p.metrics[metric.key as WeldingMetricKey]
      const dash = series == null
      const daily = series || {}
      rows.push({
        rowKey: `${p.product_cd}::${metric.key}`,
        productCd: p.product_cd,
        kind: 'metric',
        metricKey: metric.key,
        label: metric.label,
        depth: 1,
        expandable: false,
        dash,
        shortage: false,
        daily,
        summaryValue: dash ? 0 : metric.mode === 'sum' ? sumOf(daily, dates) : endOf(daily, dates),
        chartable: !dash,
      })
    }
    for (const part of p.parts) {
      const partLabel = (part.part_name || '').trim() || part.part_cd
      const stockDaily = stockDisplayFromShortage(part.stock, part.planned_usage, dates)
      rows.push({
        rowKey: `${p.product_cd}::stock::${part.part_cd}`,
        productCd: p.product_cd,
        kind: 'part-stock',
        label: `部品在庫 · ${partLabel}`,
        depth: 2,
        expandable: false,
        dash: false,
        shortage: part.has_shortage,
        daily: stockDaily,
        compareDaily: part.planned_usage,
        summaryValue: endOf(stockDaily, dates),
        chartable: true,
      })
      rows.push({
        rowKey: `${p.product_cd}::usage::${part.part_cd}`,
        productCd: p.product_cd,
        kind: 'part-usage',
        label: `予定使用 · ${partLabel}`,
        depth: 2,
        expandable: false,
        dash: false,
        shortage: part.has_shortage,
        daily: part.planned_usage,
        compareDaily: part.stock,
        summaryValue: sumOf(part.planned_usage, dates),
        chartable: true,
      })
    }
  }
  return rows
}

function toggleProduct(cd: string) {
  const next = new Set(expanded.value)
  if (next.has(cd)) next.delete(cd)
  else next.add(cd)
  expanded.value = next
}

function toggleAll() {
  if (allExpanded.value) {
    expanded.value = new Set()
    return
  }
  expanded.value = new Set(allProducts.value.map((p) => p.product_cd))
}

async function load() {
  const [from, to] = range.value || []
  if (!from || !to) return
  const span = dayjs(to).diff(dayjs(from), 'day') + 1
  if (span > 62) {
    ElMessage.warning('期間は 62 日以内にしてください')
    return
  }
  const seq = ++loadSeq
  loading.value = true
  try {
    const res = await fetchWeldingInventoryTrend({
      date_from: from,
      date_to: to,
      keyword: keyword.value.trim(),
      part_cd: partCd.value.trim(),
      shortage_only: shortageOnly.value,
    })
    if (seq !== loadSeq) return
    data.value = res.data
    expanded.value = new Set()
  } catch (e: any) {
    if (seq !== loadSeq) return
    const msg = e?.response?.data?.detail || e?.message || '読み込みに失敗しました'
    ElMessage.error(typeof msg === 'string' ? msg : '読み込みに失敗しました')
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

async function exportExcel() {
  if (!data.value) return
  const dates = data.value.dates
  const nameByCd = new Map(
    data.value.products.map((p) => [p.product_cd, (p.product_name || '').trim() || p.product_cd]),
  )
  const rows = buildRows(data.value.products, dates, new Set(data.value.products.map((p) => p.product_cd)))
  const wb = new ExcelJS.Workbook()
  const ws = wb.addWorksheet('溶接品在庫推移')
  ws.addRow(['製品名', '区分', '合計/期末', ...dates])
  for (const row of rows) {
    if (row.kind === 'summary') continue
    ws.addRow([
      nameByCd.get(row.productCd) || row.productCd,
      row.label,
      row.dash ? null : row.summaryValue,
      ...dates.map((d) => (row.dash ? null : (row.daily[d] ?? 0))),
    ])
  }
  ws.getRow(1).font = { bold: true }
  const buf = await wb.xlsx.writeBuffer()
  saveAs(
    new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
    `溶接品在庫推移_${data.value.date_from}_${data.value.date_to}.xlsx`,
  )
}

watch(
  range,
  () => scheduleLoad(0),
  { deep: true },
)
watch([keyword, partCd], () => scheduleLoad(320))
watch(shortageOnly, () => scheduleLoad(0))

onMounted(() => {
  scheduleLoad(0)
})

onUnmounted(() => {
  if (loadTimer) clearTimeout(loadTimer)
  loadSeq += 1
})
</script>

<style scoped>
.wit-page {
  --wit-chrome: 84px;
  box-sizing: border-box;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: calc(100vh - var(--wit-chrome));
  height: calc(100dvh - var(--wit-chrome));
  max-height: calc(100vh - var(--wit-chrome));
  max-height: calc(100dvh - var(--wit-chrome));
  min-height: 0;
  overflow: hidden;
  padding: 10px 12px;
  background:
    radial-gradient(ellipse 48% 32% at 8% -8%, rgba(180, 83, 9, 0.16), transparent 58%),
    linear-gradient(180deg, #fffbeb 0%, #f8fafc 46%, #f8fafc 100%);
}

.page-toolbar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
  overflow: hidden;
  background: linear-gradient(125deg, #78350f 0%, #b45309 38%, #d97706 72%, #fbbf24 100%);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  box-shadow:
    0 18px 36px -18px rgba(120, 53, 15, 0.55),
    0 4px 12px -6px rgba(180, 83, 9, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.page-toolbar-glow {
  position: absolute;
  inset: -40% -20% auto -10%;
  height: 120%;
  background: radial-gradient(ellipse 80% 55% at 18% 0%, rgba(255, 255, 255, 0.22), transparent 55%);
  pointer-events: none;
}
.toolbar-left {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  min-width: 0;
}
.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.toolbar-icon-wrap {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.38);
}
.toolbar-icon {
  font-size: 20px;
  color: #fff;
}
.toolbar-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.toolbar-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.25;
  color: #fff;
}
.toolbar-desc {
  margin: 2px 0 0;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.86);
}
.toolbar-right {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.wit-filter {
  position: relative;
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px 10px;
  padding: 8px 12px 8px 14px;
  background: #fff;
  border: 1px solid #e7e5e4;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(120, 53, 15, 0.04);
}
.wit-filter::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 4px;
  border-radius: 0 4px 4px 0;
  background: linear-gradient(180deg, #818cf8, #a855f7, #ec4899);
}
.wit-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.wit-field > span {
  font-size: 11px;
  font-weight: 800;
  color: #78716c;
}
.wit-period {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.month-quick {
  display: inline-flex;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  height: 28px;
}
.month-quick__btn {
  border: none;
  background: transparent;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 650;
  color: #475569;
  cursor: pointer;
  line-height: 26px;
}
.month-quick__btn:hover:not(:disabled) {
  background: #e2e8f0;
  color: #0f172a;
}
.month-quick__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.month-quick__btn--mid {
  border-left: 1px solid #e2e8f0;
  border-right: 1px solid #e2e8f0;
  color: #b45309;
  font-weight: 750;
}
.wit-field :deep(.el-date-editor) {
  width: 240px;
}
.wit-field :deep(.el-input) {
  width: 160px;
}
.wit-field :deep(.el-input__wrapper) {
  min-height: 28px;
  border-radius: 9px;
  background: #f8fafc;
  box-shadow: 0 0 0 1px #e7e5e4 inset;
}
.wit-field :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #a5b4fc inset;
}
.wit-field :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #6366f1 inset, 0 0 0 3px rgba(99, 102, 241, 0.16);
}
.wit-check {
  margin: 0 0 4px;
  font-weight: 700;
  color: #44403c;
}
.wit-filter__btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
  align-items: center;
}

.tb-btn {
  --tb-h: 32px;
  --k-rgb: 37 99 235;
  --k-fg: #1d4ed8;
  --k-fg-h: #1e40af;
  --k-bd: #93c5fd;
  --k-bd-h: #60a5fa;
  --k-tint: #dbeafe;
  --k-tint-h: #bfdbfe;
  --k-ico: #3b82f6;
  height: var(--tb-h) !important;
  min-height: var(--tb-h) !important;
  padding: 0 14px 0 12px !important;
  margin: 0 !important;
  border-radius: 999px !important;
  border: 1px solid var(--k-bd) !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  color: var(--k-fg) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%) !important;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.12),
    0 2px 6px -1px rgba(15, 23, 42, 0.18) !important;
}
.tb-btn :deep(.el-icon) {
  margin-right: 4px;
  font-size: 14px;
  color: var(--k-ico);
}
.tb-btn:hover:not(:disabled) {
  color: var(--k-fg-h) !important;
  border-color: var(--k-bd-h) !important;
  background: linear-gradient(135deg, #ffffff 0%, var(--k-tint) 45%, var(--k-tint-h) 100%) !important;
  transform: translateY(-1px);
}
.tb-btn-blue {
  --k-rgb: 37 99 235;
  --k-fg: #1d4ed8;
  --k-fg-h: #1e40af;
  --k-bd: #93c5fd;
  --k-bd-h: #60a5fa;
  --k-tint: #dbeafe;
  --k-tint-h: #bfdbfe;
  --k-ico: #3b82f6;
}
.tb-btn-teal {
  --k-rgb: 13 148 136;
  --k-fg: #0f766e;
  --k-fg-h: #115e59;
  --k-bd: #5eead4;
  --k-bd-h: #2dd4bf;
  --k-tint: #ccfbf1;
  --k-tint-h: #99f6e4;
  --k-ico: #14b8a6;
}
.tb-btn-green {
  --k-rgb: 5 150 105;
  --k-fg: #047857;
  --k-fg-h: #065f46;
  --k-bd: #6ee7b7;
  --k-bd-h: #34d399;
  --k-tint: #d1fae5;
  --k-tint-h: #a7f3d0;
  --k-ico: #10b981;
}

.wit-kpis {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.wit-kpi {
  --accent: #3b82f6;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 112px;
  padding: 6px 12px 6px 8px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 12px;
  border-left: 3px solid var(--accent);
  box-shadow: 0 4px 12px -4px rgba(15, 23, 42, 0.28);
}
.wit-kpi--blue { --accent: #3b82f6; }
.wit-kpi--rose { --accent: #f43f5e; }
.wit-kpi__icon {
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  color: #fff;
}
.wit-kpi--blue .wit-kpi__icon { background: linear-gradient(145deg, #60a5fa, #2563eb); }
.wit-kpi--rose .wit-kpi__icon { background: linear-gradient(145deg, #fb7185, #e11d48); }
.wit-kpi__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.wit-kpi__body span {
  font-size: 10px;
  font-weight: 700;
  color: #78716c;
  line-height: 1.1;
}
.wit-kpi__body strong {
  font-size: 16px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
  line-height: 1.2;
}

.wit-table {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.wit-table :deep(.el-empty) {
  margin: auto;
}
.wit-foot {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-top: 1px solid #eef2f6;
  background: #f8fafc;
}
.wit-pill {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 11.5px;
  font-weight: 600;
}
.wit-pill--rose {
  background: #fef2f2;
  color: #b91c1c;
}

@media (max-width: 768px) {
  .wit-page { padding: 8px; gap: 6px; }
  .toolbar-title { font-size: 17px; }
  .wit-field :deep(.el-date-editor),
  .wit-field :deep(.el-input) { width: 100%; }
  .wit-field { flex: 1 1 140px; }
  .wit-filter__btns { margin-left: 0; width: 100%; }
}
@media (max-width: 480px) {
  .wit-page { padding: 6px; }
  .toolbar-desc { display: none; }
  .wit-kpi { min-width: 96px; padding: 5px 8px 5px 6px; }
  .wit-kpi__body strong { font-size: 14px; }
}
@media (prefers-reduced-motion: reduce) {
  .tb-btn:hover:not(:disabled) { transform: none; }
}
</style>
