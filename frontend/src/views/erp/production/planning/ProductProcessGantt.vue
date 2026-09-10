<template>
  <div class="ppg-page">
    <!-- Hero -->
    <header class="ppg-hero">
      <div class="ppg-hero__glow" aria-hidden="true" />
      <div class="ppg-hero__row">
        <div class="ppg-hero__brand">
          <div class="ppg-hero__icon">
            <el-icon :size="22"><Calendar /></el-icon>
          </div>
          <div>
            <p class="ppg-hero__kicker">生産計画</p>
            <h2>製品工程ガント</h2>
          </div>
        </div>
        <div class="ppg-kpis">
          <div class="ppg-kpi">
            <span class="ppg-kpi__label">対象製品</span>
            <strong>{{ products.length }}</strong>
            <em v-if="!hasProductFilter">/ {{ total }}</em>
          </div>
          <div class="ppg-kpi">
            <span class="ppg-kpi__label">期間</span>
            <strong>{{ dateCells.length }}</strong>
            <em>日</em>
          </div>
          <div class="ppg-kpi">
            <span class="ppg-kpi__label">指定</span>
            <strong>{{ selectedProductCds.length || '全' }}</strong>
          </div>
        </div>
      </div>
      <div class="ppg-legend">
        <template v-if="activeTab === 'gantt'">
          <span class="ppg-legend__item">
            <span class="ppg-legend__sample ppg-legend__sample--actual">123</span>実績
          </span>
          <span class="ppg-legend__item">
            <span class="ppg-legend__sample ppg-legend__sample--plan">123</span>計画
          </span>
          <span class="ppg-legend__sep" />
        </template>
        <template v-else>
          <span class="ppg-legend__item">
            <span class="ppg-legend__heat is-pos" />正
          </span>
          <span class="ppg-legend__item">
            <span class="ppg-legend__heat is-zero" />0
          </span>
          <span class="ppg-legend__item">
            <span class="ppg-legend__heat is-neg" />負
          </span>
          <span class="ppg-legend__sep" />
        </template>
        <span
          v-for="p in legendProcesses"
          :key="p.key"
          class="ppg-legend__item"
        >
          <i class="ppg-legend__dot" :style="{ background: processColor(p.key) }" />
          {{ p.label }}
          <em v-if="activeTab === 'gantt' && p.mode === 'inventory_trend'">在庫</em>
          <em v-else-if="activeTab === 'gantt' && p.mode === 'plan'">計画</em>
          <em v-else-if="activeTab !== 'gantt' && p.mode === 'inventory_trend'">在庫</em>
          <em v-else-if="activeTab === 'trend' && p.has_trend">推移</em>
          <em v-else-if="activeTab === 'apt' && p.has_actual_plan_trend">実計</em>
        </span>
      </div>
    </header>

    <!-- 検索条件 -->
    <section class="ppg-filters">
      <el-form inline @submit.prevent class="ppg-filters__form">
        <el-form-item label="期間">
          <el-date-picker
            v-model="range"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="〜"
            start-placeholder="開始日"
            end-placeholder="終了日"
            :clearable="false"
            class="ppg-date"
          />
        </el-form-item>
        <el-form-item>
          <div class="ppg-presets">
            <button
              v-for="preset in presets"
              :key="preset.id"
              type="button"
              class="ppg-chip"
              :class="{ 'is-on': activePreset === preset.id }"
              @click="preset.run()"
            >
              {{ preset.label }}
            </button>
          </div>
        </el-form-item>
        <el-form-item label="製品指定">
          <el-select
            v-model="selectedProductCds"
            multiple
            filterable
            remote
            clearable
            collapse-tags
            collapse-tags-tooltip
            :max-collapse-tags="2"
            :remote-method="searchProducts"
            :loading="productSearchLoading"
            placeholder="検索して複数選択（未選択＝全製品）"
            class="ppg-product-select"
            @visible-change="onProductDropdown"
          >
            <el-option
              v-for="opt in productOptions"
              :key="opt.product_cd"
              :value="opt.product_cd"
              :label="`${opt.product_cd}  ${opt.product_name}`"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!hasProductFilter" label="キーワード">
          <el-input
            v-model="keyword"
            placeholder="製品CD・製品名"
            clearable
            class="ppg-keyword"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" round :loading="loading" class="ppg-search-btn" @click="handleSearch">
            検索
          </el-button>
        </el-form-item>
        <el-form-item label="表示幅">
          <div class="ppg-zoom">
            <button
              v-for="z in zoomOptions"
              :key="z.w"
              type="button"
              class="ppg-chip"
              :class="{ 'is-on': dayWidth === z.w }"
              @click="dayWidth = z.w"
            >
              {{ z.label }}
            </button>
          </div>
        </el-form-item>
      </el-form>
    </section>

    <!-- Tabs + チャート本体 -->
    <el-tabs v-model="activeTab" class="ppg-tabs">
      <el-tab-pane label="工程ガント" name="gantt" />
      <el-tab-pane label="工程推移" name="trend" />
      <el-tab-pane label="実計推移" name="apt" />
    </el-tabs>

    <section v-loading="loading" class="ppg-gantt">
      <div v-if="products.length" class="ppg-scroll">
        <div class="ppg-canvas" :style="{ width: canvasWidth + 'px' }">
          <div class="ppg-head">
            <div class="ppg-row ppg-row--months">
              <div class="ppg-left ppg-left--corner">製品 / 工程</div>
              <div class="ppg-timeline ppg-timeline--head">
                <div
                  v-for="seg in monthSegments"
                  :key="seg.label"
                  class="ppg-month"
                  :style="{ width: seg.span * dayWidth + 'px' }"
                >
                  {{ seg.label }}
                </div>
              </div>
            </div>
            <div class="ppg-row ppg-row--days">
              <div class="ppg-left ppg-left--corner" />
              <div class="ppg-timeline ppg-timeline--head">
                <div
                  v-for="d in dateCells"
                  :key="d.ds"
                  class="ppg-day"
                  :class="{ 'is-weekend': d.isWeekend, 'is-today': d.isToday }"
                  :style="{ width: dayWidth + 'px' }"
                >
                  <span class="ppg-day__num">{{ d.dayNum }}</span>
                  <span v-if="dayWidth >= 32" class="ppg-day__dow">{{ d.dow }}</span>
                </div>
              </div>
            </div>
          </div>

          <template v-for="(pr, pi) in productRows" :key="pr.product.product_cd">
            <div class="ppg-row ppg-row--product" :style="{ '--accent': productAccent(pi) }">
              <div class="ppg-left ppg-left--product">
                <span class="ppg-prod-cd">{{ pr.product.product_cd }}</span>
                <span class="ppg-prod-name" :title="pr.product.product_name">{{ pr.product.product_name }}</span>
                <span v-if="pr.product.route_cd" class="ppg-prod-route">{{ pr.product.route_cd }}</span>
              </div>
              <div class="ppg-timeline ppg-timeline--product" :style="{ backgroundImage: timelineBg }">
                <div
                  v-if="pr.span"
                  class="ppg-span"
                  :style="{ left: pr.span.startIdx * dayWidth + 2 + 'px', width: pr.span.len * dayWidth - 4 + 'px' }"
                  :title="`期間: ${pr.span.startDs} 〜 ${pr.span.endDs}`"
                />
              </div>
            </div>
            <div
              v-for="row in pr.stepRows"
              :key="pr.product.product_cd + '-' + row.step.step_no"
              class="ppg-row ppg-row--step"
              :class="{ 'ppg-row--inv': row.render === 'heat' || row.render === 'inventory' }"
            >
              <div class="ppg-left ppg-left--step">
                <span class="ppg-step-no">{{ row.step.step_no }}</span>
                <i class="ppg-step-dot" :style="{ background: processColor(row.step.process_key) }" />
                <span class="ppg-step-name">{{ stepDisplayName(row.step) }}</span>
                <span
                  class="ppg-step-total"
                  :class="{ 'is-neg': (row.endValue ?? 0) < 0 }"
                  :title="row.totalTitle"
                >
                  {{ row.endValue != null ? formatQty(row.endValue) : '—' }}
                </span>
              </div>
              <div class="ppg-timeline" :style="{ backgroundImage: timelineBg }">
                <!-- 倉庫在庫（ガントTab） / 推移・実計推移 -->
                <template v-if="row.render === 'inventory' || row.render === 'heat'">
                  <div
                    v-for="cell in row.heatCells"
                    :key="cell.d"
                    class="ppg-inv-cell"
                    :class="invCellClass(cell.v)"
                    :style="{
                      left: cell.startIdx * dayWidth + 1 + 'px',
                      width: dayWidth - 2 + 'px',
                      ...invHeatStyle(cell.v, row.heatMaxAbs),
                    }"
                    :title="cell.tooltip"
                  >
                    <span v-if="dayWidth >= 28">{{ formatQty(cell.v) }}</span>
                  </div>
                </template>
                <!-- 計画/実績バー（ガントTab） -->
                <template v-else>
                  <div
                    v-for="(bar, bi) in row.bars"
                    :key="bi"
                    class="ppg-bar"
                    :style="{
                      left: bar.startIdx * dayWidth + 2 + 'px',
                      width: bar.len * dayWidth - 4 + 'px',
                      ...barStyle(row.step.process_key),
                    }"
                    :title="bar.tooltip"
                  >
                    <template v-if="dayWidth >= 32">
                      <span
                        v-for="cell in bar.cells"
                        :key="cell.d"
                        class="ppg-bar__cell"
                        :class="cell.src === 'a' ? 'is-actual' : 'is-plan'"
                        :style="{ width: dayWidth + 'px' }"
                      >{{ formatQty(cell.q) }}</span>
                    </template>
                    <span v-else class="ppg-bar__label">{{ formatQty(bar.totalQty) }}</span>
                  </div>
                </template>
              </div>
            </div>
          </template>
        </div>
      </div>
      <el-empty v-else-if="!loading" description="対象データがありません" />
    </section>

    <div v-if="!hasProductFilter && total > 0" class="ppg-pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 30, 50]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="fetchData"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Calendar, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getProductProcessGantt,
  type GanttDayCell,
  type GanttProcessDef,
  type GanttProcessMode,
  type GanttProduct,
  type GanttRouteStep,
  type TrendDayCell,
} from '@/api/productProcessGantt'
import { getProductList } from '@/api/master/productMaster'

const INVENTORY_PROCESS_KEYS = new Set(['warehouse', 'outsourced_warehouse'])
const PRODUCT_ACCENTS = ['#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6']

type ViewTab = 'gantt' | 'trend' | 'apt'
const activeTab = ref<ViewTab>('gantt')

const legendProcesses = computed(() => {
  if (activeTab.value === 'gantt') return processDefs.value
  // 工程推移・実計推移: 内示(検査)は非表示
  return processDefs.value.filter((p) => p.key !== 'inspection')
})

function todayJst(): string {
  const jst = new Date(Date.now() + 9 * 60 * 60 * 1000)
  const y = jst.getUTCFullYear()
  const m = String(jst.getUTCMonth() + 1).padStart(2, '0')
  const d = String(jst.getUTCDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function toDs(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

function defaultRange(): [string, string] {
  const start = new Date()
  const end = new Date()
  start.setDate(start.getDate() - 7)
  end.setDate(end.getDate() + 21)
  return [toDs(start), toDs(end)]
}

const range = ref<[string, string]>(defaultRange())
const selectedProductCds = ref<string[]>([])
const keyword = ref('')
const dayWidth = ref(44)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const activePreset = ref('')
const zoomOptions = [
  { w: 22, label: '小' },
  { w: 32, label: '中' },
  { w: 44, label: '大' },
]

const hasProductFilter = computed(() => selectedProductCds.value.length > 0)

const presets = [
  { id: '4w', label: '4週間', run: () => applyPreset(28, '4w') },
  { id: '8w', label: '8週間', run: () => applyPreset(56, '8w') },
  { id: 'this', label: '今月', run: () => applyPresetMonth(0, 'this') },
  { id: 'next', label: '来月', run: () => applyPresetMonth(1, 'next') },
]

function applyPreset(days: number, id: string) {
  const start = new Date()
  const end = new Date()
  end.setDate(end.getDate() + days - 1)
  range.value = [toDs(start), toDs(end)]
  activePreset.value = id
  handleSearch()
}

function applyPresetMonth(offset: number, id: string) {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth() + offset, 1)
  const end = new Date(now.getFullYear(), now.getMonth() + offset + 1, 0)
  range.value = [toDs(start), toDs(end)]
  activePreset.value = id
  handleSearch()
}

interface ProductOption {
  product_cd: string
  product_name: string
}

const productOptions = ref<ProductOption[]>([])
const productSearchLoading = ref(false)

function mergeProductOptions(list: ProductOption[]) {
  const map = new Map<string, ProductOption>()
  for (const o of productOptions.value) map.set(o.product_cd, o)
  for (const o of list) {
    if (o.product_cd) map.set(o.product_cd, o)
  }
  productOptions.value = Array.from(map.values())
}

async function searchProducts(query: string) {
  productSearchLoading.value = true
  try {
    const res = await getProductList({
      keyword: query?.trim() || undefined,
      page: 1,
      pageSize: 40,
    })
    const list = res?.data?.list ?? res?.list ?? []
    mergeProductOptions(
      list.map((p) => ({
        product_cd: String(p.product_cd ?? ''),
        product_name: String(p.product_name ?? ''),
      }))
    )
  } finally {
    productSearchLoading.value = false
  }
}

function onProductDropdown(open: boolean) {
  if (open && productOptions.value.length === 0) searchProducts('')
}

watch(selectedProductCds, () => {
  page.value = 1
  fetchData()
})

const loading = ref(false)
const products = ref<GanttProduct[]>([])
const processDefs = ref<GanttProcessDef[]>([])
const periodStart = ref('')
const periodEnd = ref('')

async function fetchData() {
  const [start, end] = range.value || []
  if (!start || !end) return
  loading.value = true
  try {
    const res = await getProductProcessGantt({
      start_date: start,
      end_date: end,
      product_cd: hasProductFilter.value ? selectedProductCds.value.join(',') : undefined,
      keyword: hasProductFilter.value ? undefined : keyword.value.trim() || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    const data = res.data
    products.value = data.products.map((p) => ({
      ...p,
      days: p.days || {},
      trends: p.trends || {},
      actual_plan_trends: p.actual_plan_trends || {},
    }))
    processDefs.value = data.processes
    periodStart.value = data.period.start
    periodEnd.value = data.period.end
    total.value = data.total
    mergeProductOptions(
      data.products.map((p) => ({ product_cd: p.product_cd, product_name: p.product_name }))
    )
  } catch (e) {
    console.error('製品工程ガントの取得に失敗しました', e)
    ElMessage.error('データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function handleSizeChange() {
  page.value = 1
  fetchData()
}

onMounted(fetchData)

const LEFT_WIDTH = 268

interface DateCell {
  ds: string
  dayNum: number
  dow: string
  isWeekend: boolean
  isToday: boolean
  month: string
}

const DOW_LABELS = ['日', '月', '火', '水', '木', '金', '土']

const dateCells = computed<DateCell[]>(() => {
  if (!periodStart.value || !periodEnd.value) return []
  const cells: DateCell[] = []
  const todayDs = todayJst()
  const cur = new Date(periodStart.value + 'T00:00:00')
  const end = new Date(periodEnd.value + 'T00:00:00')
  while (cur <= end) {
    const ds = toDs(cur)
    const dow = cur.getDay()
    cells.push({
      ds,
      dayNum: cur.getDate(),
      dow: DOW_LABELS[dow],
      isWeekend: dow === 0 || dow === 6,
      isToday: ds === todayDs,
      month: `${cur.getFullYear()}/${cur.getMonth() + 1}`,
    })
    cur.setDate(cur.getDate() + 1)
  }
  return cells
})

const dateIndexMap = computed<Record<string, number>>(() => {
  const m: Record<string, number> = {}
  dateCells.value.forEach((c, i) => {
    m[c.ds] = i
  })
  return m
})

const monthSegments = computed(() => {
  const segs: { label: string; span: number }[] = []
  for (const c of dateCells.value) {
    const last = segs[segs.length - 1]
    if (last && last.label === c.month) last.span += 1
    else segs.push({ label: c.month, span: 1 })
  }
  return segs
})

const canvasWidth = computed(() => LEFT_WIDTH + dateCells.value.length * dayWidth.value)

const timelineBg = computed(() => {
  const w = dayWidth.value
  const cells = dateCells.value
  if (!cells.length) return 'none'
  const layers: string[] = []
  const todayIdx = cells.findIndex((c) => c.isToday)
  if (todayIdx >= 0) {
    const mid = todayIdx * w + w / 2
    layers.push(
      `linear-gradient(90deg, transparent ${todayIdx * w}px, rgba(244,63,94,0.08) ${todayIdx * w}px, rgba(244,63,94,0.08) ${(todayIdx + 1) * w}px, transparent ${(todayIdx + 1) * w}px)`
    )
    layers.push(
      `linear-gradient(90deg, transparent ${mid - 1}px, #f43f5e ${mid - 1}px, #f43f5e ${mid + 1}px, transparent ${mid + 1}px)`
    )
  }
  for (const target of [6, 0]) {
    const off = cells.findIndex((c) => new Date(c.ds + 'T00:00:00').getDay() === target)
    if (off >= 0 && off < 7) {
      layers.push(
        `repeating-linear-gradient(90deg, transparent 0px, transparent ${off * w}px, rgba(148,163,184,0.10) ${off * w}px, rgba(148,163,184,0.10) ${(off + 1) * w}px, transparent ${(off + 1) * w}px, transparent ${7 * w}px)`
      )
    }
  }
  layers.push(
    `repeating-linear-gradient(90deg, rgba(226,232,240,0.9) 0, rgba(226,232,240,0.9) 1px, transparent 1px, transparent ${w}px)`
  )
  return layers.join(', ')
})

const PROCESS_COLORS: Record<string, string> = {
  cutting: '#2563eb',
  chamfering: '#059669',
  molding: '#d97706',
  plating: '#7c3aed',
  outsourced_plating: '#c026d3',
  welding: '#ea580c',
  outsourced_welding: '#e11d48',
  inspection: '#0891b2',
  warehouse: '#0d9488',
  outsourced_warehouse: '#64748b',
}

function processColor(key: string | null): string {
  return (key && PROCESS_COLORS[key]) || '#94a3b8'
}

/** 検査はデータ取得キーそのまま、画面表示のみ「内示」 */
function stepDisplayName(step: GanttRouteStep): string {
  if (step.process_key === 'inspection') return '内示'
  return step.process_name
}

function productAccent(index: number): string {
  return PRODUCT_ACCENTS[index % PRODUCT_ACCENTS.length]
}

function barStyle(key: string | null): Record<string, string> {
  const c = processColor(key)
  return {
    background: `linear-gradient(180deg, ${c} 0%, ${c}dd 100%)`,
    boxShadow: `0 4px 12px ${c}55, inset 0 1px 0 rgba(255,255,255,.28)`,
  }
}

function invHeatStyle(inv: number, maxAbs: number): Record<string, string> {
  if (inv === 0 || maxAbs <= 0) return {}
  const t = Math.min(1, Math.abs(inv) / maxAbs)
  if (inv < 0) {
    return { background: `rgba(225, 29, 72, ${0.12 + t * 0.42})` }
  }
  return { background: `rgba(13, 148, 136, ${0.12 + t * 0.42})` }
}

function formatQty(v: number): string {
  return v.toLocaleString()
}

function processMode(key: string | null | undefined, defs: GanttProcessDef[]): GanttProcessMode | null {
  if (!key) return null
  const def = defs.find((d) => d.key === key)
  if (def) return def.mode
  if (INVENTORY_PROCESS_KEYS.has(key)) return 'inventory_trend'
  return 'plan_actual_merge'
}

function invCellClass(inv: number): string {
  if (inv < 0) return 'is-neg'
  if (inv === 0) return 'is-zero'
  return 'is-pos'
}

type DisplaySrc = 'a' | 'p'

interface DisplayCell {
  d: string
  q: number
  src: DisplaySrc
  p: number
  a: number
}

function resolveDisplay(cell: GanttDayCell, mode: GanttProcessMode, today: string): DisplayCell | null {
  const p = cell.p || 0
  const a = cell.a || 0
  if (mode === 'plan') {
    if (p <= 0) return null
    return { d: cell.d, q: p, src: 'p', p, a }
  }
  let q = 0
  let src: DisplaySrc = 'p'
  if (cell.d < today) {
    q = a
    src = 'a'
  } else if (cell.d === today) {
    if (a > 0) {
      q = a
      src = 'a'
    } else {
      q = p
      src = 'p'
    }
  } else {
    q = p
    src = 'p'
  }
  if (q <= 0) return null
  return { d: cell.d, q, src, p, a }
}

interface GanttBar {
  startIdx: number
  len: number
  totalQty: number
  cells: DisplayCell[]
  tooltip: string
}

interface HeatCellView {
  d: string
  startIdx: number
  v: number
  tooltip: string
}

interface StepRow {
  step: GanttRouteStep
  render: 'bars' | 'inventory' | 'heat'
  bars: GanttBar[]
  heatCells: HeatCellView[]
  heatMaxAbs: number
  endValue: number | null
  totalTitle: string
}

interface ProductRow {
  product: GanttProduct
  stepRows: StepRow[]
  span: { startIdx: number; len: number; startDs: string; endDs: string } | null
}

function buildBars(days: GanttDayCell[], step: GanttRouteStep, mode: GanttProcessMode): GanttBar[] {
  const idxMap = dateIndexMap.value
  const today = todayJst()
  const displayCells: DisplayCell[] = []
  for (const cell of days) {
    const resolved = resolveDisplay(cell, mode, today)
    if (resolved) displayCells.push(resolved)
  }

  const bars: GanttBar[] = []
  let current: (GanttBar & { lastIdx: number }) | null = null
  for (const cell of displayCells) {
    const idx = idxMap[cell.d]
    if (idx == null) continue
    if (current && idx === current.lastIdx + 1) {
      current.len += 1
      current.lastIdx = idx
      current.totalQty += cell.q
      current.cells.push(cell)
    } else {
      if (current) bars.push(current)
      current = {
        startIdx: idx,
        lastIdx: idx,
        len: 1,
        totalQty: cell.q,
        cells: [cell],
        tooltip: '',
      }
    }
  }
  if (current) bars.push(current)

  for (const bar of bars) {
    const lines = bar.cells.map((c) => {
      const tag = c.src === 'a' ? '実績' : '計画'
      return `${c.d}  ${tag} ${formatQty(c.q)}（計画 ${formatQty(c.p)} / 実績 ${formatQty(c.a)}）`
    })
    bar.tooltip = `${stepDisplayName(step)}\n合計 ${formatQty(bar.totalQty)}\n${lines.join('\n')}`
  }
  return bars
}

function buildInventoryHeat(days: GanttDayCell[]): HeatCellView[] {
  const idxMap = dateIndexMap.value
  const out: HeatCellView[] = []
  for (const cell of days) {
    const idx = idxMap[cell.d]
    if (idx == null) continue
    const inv = cell.i ?? 0
    const tr = cell.t ?? 0
    out.push({
      d: cell.d,
      startIdx: idx,
      v: inv,
      tooltip: `${cell.d}\n在庫: ${formatQty(inv)}\n推移: ${formatQty(tr)}`,
    })
  }
  return out
}

function buildSeriesHeat(series: TrendDayCell[], label: string, step: GanttRouteStep): HeatCellView[] {
  const idxMap = dateIndexMap.value
  const out: HeatCellView[] = []
  for (const cell of series) {
    const idx = idxMap[cell.d]
    if (idx == null) continue
    out.push({
      d: cell.d,
      startIdx: idx,
      v: cell.v,
      tooltip: `${stepDisplayName(step)}\n${cell.d}\n${label}: ${formatQty(cell.v)}`,
    })
  }
  return out
}

const productRows = computed<ProductRow[]>(() => {
  const defs = processDefs.value
  const tab = activeTab.value
  return products.value.map((product) => {
    const steps = (product.steps || []).filter((step) => {
      // 工程推移・実計推移では内示(検査)を出さない
      if (tab !== 'gantt' && step.process_key === 'inspection') return false
      return true
    })

    const stepRows: StepRow[] = steps.map((step) => {
      const mode = processMode(step.process_key, defs)
      const key = step.process_key
      const isWarehouse = key != null && INVENTORY_PROCESS_KEYS.has(key)

      // 推移／実計推移タブでも倉庫系は工程ガントと同じ在庫データを表示
      if (tab !== 'gantt' && isWarehouse) {
        const days = key ? product.days?.[key] || [] : []
        const heatCells = buildInventoryHeat(days)
        const last = heatCells.length ? heatCells[heatCells.length - 1] : null
        return {
          step,
          render: 'inventory' as const,
          bars: [],
          heatCells,
          heatMaxAbs: heatCells.reduce((m, c) => Math.max(m, Math.abs(c.v)), 0),
          endValue: last ? last.v : null,
          totalTitle: '期間末日の在庫',
        }
      }

      if (tab === 'trend') {
        const series = key ? product.trends?.[key] || [] : []
        const heatCells = buildSeriesHeat(series, '推移 (*_trend)', step)
        const last = heatCells.length ? heatCells[heatCells.length - 1] : null
        return {
          step,
          render: 'heat' as const,
          bars: [],
          heatCells,
          heatMaxAbs: heatCells.reduce((m, c) => Math.max(m, Math.abs(c.v)), 0),
          endValue: last ? last.v : null,
          totalTitle: '期間末日の推移',
        }
      }

      if (tab === 'apt') {
        const series = key ? product.actual_plan_trends?.[key] || [] : []
        const heatCells = buildSeriesHeat(series, '実計推移 (*_actual_plan_trend)', step)
        const last = heatCells.length ? heatCells[heatCells.length - 1] : null
        return {
          step,
          render: 'heat' as const,
          bars: [],
          heatCells,
          heatMaxAbs: heatCells.reduce((m, c) => Math.max(m, Math.abs(c.v)), 0),
          endValue: last ? last.v : null,
          totalTitle: '期間末日の実計推移',
        }
      }

      const days = key ? product.days?.[key] || [] : []
      if (mode === 'inventory_trend') {
        const heatCells = buildInventoryHeat(days)
        const last = heatCells.length ? heatCells[heatCells.length - 1] : null
        return {
          step,
          render: 'inventory' as const,
          bars: [],
          heatCells,
          heatMaxAbs: heatCells.reduce((m, c) => Math.max(m, Math.abs(c.v)), 0),
          endValue: last ? last.v : null,
          totalTitle: '期間末日の在庫',
        }
      }
      const bars = buildBars(days, step, mode || 'plan_actual_merge')
      const total = bars.reduce((s, b) => s + b.totalQty, 0)
      return {
        step,
        render: 'bars' as const,
        bars,
        heatCells: [],
        heatMaxAbs: 0,
        endValue: total || null,
        totalTitle: '期間内表示合計',
      }
    })

    let minIdx = Infinity
    let maxIdx = -1
    for (const row of stepRows) {
      if (row.render === 'bars') {
        for (const bar of row.bars) {
          if (bar.startIdx < minIdx) minIdx = bar.startIdx
          const endIdx = bar.startIdx + bar.len - 1
          if (endIdx > maxIdx) maxIdx = endIdx
        }
      } else {
        for (const cell of row.heatCells) {
          if (cell.startIdx < minIdx) minIdx = cell.startIdx
          if (cell.startIdx > maxIdx) maxIdx = cell.startIdx
        }
      }
    }
    const span =
      maxIdx >= 0
        ? {
            startIdx: minIdx,
            len: maxIdx - minIdx + 1,
            startDs: dateCells.value[minIdx]?.ds || '',
            endDs: dateCells.value[maxIdx]?.ds || '',
          }
        : null
    return { product, stepRows, span }
  })
})
</script>

<style scoped>
.ppg-page {
  padding: 18px 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
  background:
    radial-gradient(1200px 400px at 10% -10%, rgba(99, 102, 241, 0.08), transparent 55%),
    radial-gradient(900px 320px at 100% 0%, rgba(14, 165, 233, 0.07), transparent 50%),
    #f4f6fb;
}

.ppg-hero {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  padding: 20px 22px 16px;
  color: #eef2ff;
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 48%, #1d4ed8 100%);
  box-shadow: 0 18px 40px rgba(30, 27, 75, 0.28);
}

.ppg-hero__glow {
  position: absolute;
  right: -80px;
  top: -90px;
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(165, 180, 252, 0.35), transparent 68%);
  pointer-events: none;
}

.ppg-hero__row {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.ppg-hero__brand {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.ppg-hero__icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(8px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.ppg-hero__kicker {
  margin: 0 0 2px;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #c7d2fe;
}

.ppg-hero h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 750;
  letter-spacing: -0.02em;
  color: #fff;
}

.ppg-kpis {
  display: flex;
  gap: 8px;
}

.ppg-kpi {
  min-width: 86px;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.ppg-kpi__label {
  display: block;
  font-size: 10px;
  color: #c7d2fe;
  letter-spacing: 0.04em;
}

.ppg-kpi strong {
  font-size: 20px;
  font-weight: 750;
  color: #fff;
}

.ppg-kpi em {
  font-style: normal;
  font-size: 12px;
  color: #c7d2fe;
  margin-left: 2px;
}

.ppg-legend {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 12px;
  color: #e0e7ff;
}

.ppg-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.ppg-legend__sep {
  width: 1px;
  background: rgba(255, 255, 255, 0.18);
  margin: 0 4px;
}

.ppg-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.18);
}

.ppg-legend__sample {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 18px;
  padding: 0 6px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  background: linear-gradient(180deg, #6366f1, #4f46e5);
}

.ppg-legend__sample--actual {
  color: #0f172a;
}

.ppg-legend__sample--plan {
  color: #fff;
}

.ppg-legend__heat {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  display: inline-block;
}

.ppg-legend__heat.is-pos {
  background: rgba(13, 148, 136, 0.45);
}

.ppg-legend__heat.is-zero {
  background: rgba(148, 163, 184, 0.25);
}

.ppg-legend__heat.is-neg {
  background: rgba(225, 29, 72, 0.45);
}

.ppg-legend__item em {
  font-style: normal;
  font-size: 10px;
  color: #c7d2fe;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  padding: 0 6px;
}

.ppg-filters {
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 16px;
  padding: 12px 16px 2px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}

.ppg-tabs {
  margin: -2px 0 -6px;
}

.ppg-tabs :deep(.el-tabs__header) {
  margin: 0;
  border-bottom: none;
}

.ppg-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.ppg-tabs :deep(.el-tabs__item) {
  font-weight: 700;
  color: #64748b;
  padding: 0 18px;
  height: 40px;
}

.ppg-tabs :deep(.el-tabs__item.is-active) {
  color: #4338ca;
}

.ppg-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px;
  background: linear-gradient(90deg, #4f46e5, #2563eb);
}

.ppg-filters__form :deep(.el-form-item) {
  margin-bottom: 12px;
  margin-right: 16px;
}

.ppg-filters__form :deep(.el-form-item__label) {
  color: #64748b;
  font-weight: 600;
}

.ppg-date {
  width: 250px;
}

.ppg-product-select {
  min-width: 340px;
}

.ppg-keyword {
  width: 200px;
}

.ppg-search-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #4f46e5, #2563eb);
  border: none;
}

.ppg-presets,
.ppg-zoom {
  display: flex;
  gap: 6px;
}

.ppg-chip {
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.ppg-chip:hover {
  border-color: #c7d2fe;
  color: #4338ca;
}

.ppg-chip.is-on {
  background: linear-gradient(135deg, #4f46e5, #2563eb);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 6px 14px rgba(79, 70, 229, 0.28);
}

.ppg-gantt {
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 16px;
  min-height: 240px;
  overflow: hidden;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
}

.ppg-scroll {
  overflow: auto;
  max-height: calc(100vh - 360px);
}

.ppg-canvas {
  min-width: 100%;
}

.ppg-row {
  display: flex;
  border-bottom: 1px solid #f1f5f9;
}

.ppg-left {
  flex: 0 0 268px;
  width: 268px;
  position: sticky;
  left: 0;
  z-index: 2;
  background: #fff;
  border-right: 1px solid #e8edf5;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  box-sizing: border-box;
  overflow: hidden;
}

.ppg-timeline {
  position: relative;
  flex: 1 1 auto;
  height: 38px;
}

.ppg-head {
  position: sticky;
  top: 0;
  z-index: 3;
  background: linear-gradient(180deg, #f8fafc, #eef2ff);
}

.ppg-head .ppg-left--corner {
  background: linear-gradient(180deg, #f8fafc, #eef2ff);
  z-index: 4;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  letter-spacing: 0.02em;
}

.ppg-row--months .ppg-timeline--head,
.ppg-row--days .ppg-timeline--head {
  display: flex;
  height: 28px;
  background: transparent;
}

.ppg-row--months {
  border-bottom: 1px solid #e0e7ff;
}

.ppg-month {
  flex: 0 0 auto;
  font-size: 12px;
  font-weight: 700;
  color: #312e81;
  padding-left: 8px;
  border-right: 1px solid #e0e7ff;
  display: flex;
  align-items: center;
  overflow: hidden;
  white-space: nowrap;
  box-sizing: border-box;
}

.ppg-row--days {
  border-bottom: 1px solid #c7d2fe;
}

.ppg-day {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #64748b;
  border-right: 1px solid #eef2ff;
  box-sizing: border-box;
  line-height: 1.1;
}

.ppg-day.is-weekend {
  background: rgba(148, 163, 184, 0.1);
  color: #94a3b8;
}

.ppg-day.is-today {
  background: rgba(244, 63, 94, 0.12);
  color: #e11d48;
  font-weight: 800;
}

.ppg-day__dow {
  font-size: 10px;
  opacity: 0.78;
}

.ppg-row--product {
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 12%, #f8fafc), #f8fafc);
}

.ppg-left--product {
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 18%, #fff), #fff);
  border-left: 4px solid var(--accent);
  font-size: 13px;
}

.ppg-prod-cd {
  font-weight: 800;
  color: #0f172a;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.ppg-prod-name {
  color: #475569;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1 1 auto;
}

.ppg-prod-route {
  flex: 0 0 auto;
  font-size: 10px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 14%, #fff);
  border-radius: 999px;
  padding: 1px 7px;
  white-space: nowrap;
  font-weight: 700;
}

.ppg-timeline--product {
  background-color: #f8fafc;
}

.ppg-span {
  position: absolute;
  top: 15px;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 55%, #fff), var(--accent));
  box-shadow: 0 2px 8px color-mix(in srgb, var(--accent) 40%, transparent);
}

.ppg-left--step {
  padding-left: 18px;
  font-size: 12px;
}

.ppg-row--step:hover .ppg-left--step,
.ppg-row--step:hover .ppg-timeline {
  background: #fafbff;
}

.ppg-step-no {
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  border-radius: 6px;
  background: #eef2ff;
  color: #4338ca;
  font-size: 10px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.ppg-step-dot {
  flex: 0 0 auto;
  width: 8px;
  height: 8px;
  border-radius: 99px;
  box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.04);
}

.ppg-step-name {
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1 1 auto;
  font-weight: 600;
}

.ppg-step-total {
  flex: 0 0 auto;
  font-size: 11px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.ppg-step-total.is-neg {
  color: #e11d48;
}

.ppg-bar {
  position: absolute;
  top: 7px;
  height: 24px;
  border-radius: 8px;
  color: #fff;
  font-size: 11px;
  display: flex;
  align-items: center;
  overflow: hidden;
  cursor: default;
}

.ppg-bar__label {
  width: 100%;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 4px;
  font-weight: 700;
  text-shadow: 0 1px 1px rgba(15, 23, 42, 0.25);
}

.ppg-bar__cell {
  flex: 0 0 auto;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  font-weight: 700;
  border-right: 1px solid rgba(255, 255, 255, 0.22);
  box-sizing: border-box;
}

.ppg-bar__cell:last-child {
  border-right: none;
}

.ppg-bar__cell.is-actual {
  color: #0f172a;
  text-shadow: none;
}

.ppg-bar__cell.is-plan {
  color: #fff;
  text-shadow: 0 1px 1px rgba(15, 23, 42, 0.25);
}

.ppg-row--inv .ppg-left--step {
  background: #f8fafc;
}

.ppg-inv-cell {
  position: absolute;
  top: 6px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  border-radius: 7px;
  box-sizing: border-box;
  overflow: hidden;
  white-space: nowrap;
  cursor: default;
}

.ppg-inv-cell.is-pos {
  color: #0f766e;
}

.ppg-inv-cell.is-zero {
  background: rgba(148, 163, 184, 0.1);
  color: #94a3b8;
}

.ppg-inv-cell.is-neg {
  color: #be123c;
}

.ppg-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 2px 4px 0;
}
</style>
