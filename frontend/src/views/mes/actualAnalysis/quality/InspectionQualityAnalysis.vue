<template>
  <div class="iqa ipa">
    <div class="ipa__bg" aria-hidden="true">
      <div class="ipa__orb ipa__orb--1" />
      <div class="ipa__orb ipa__orb--2" />
      <div class="ipa__orb ipa__orb--3" />
    </div>

    <header class="ipa-hero ipa-fade-in">
      <div class="ipa-hero__main">
        <div class="ipa-hero__icon iqa-hero__icon">
          <el-icon :size="24"><WarningFilled /></el-icon>
          <span class="ipa-hero__icon-glow" />
        </div>
        <div class="ipa-hero__text">
          <div class="ipa-hero__eyebrow">MES · 実績分析</div>
          <h1 class="ipa-hero__title">検査工程 — 品質分析</h1>
          <p class="ipa-hero__meta">inspection_management · 製品不良 · 不良項目 · 不良率</p>
        </div>
      </div>
      <div class="ipa-hero__actions">
        <span v-if="analysisData" class="ipa-hero__range">
          {{ analysisData.start_date }} ～ {{ analysisData.end_date }}
        </span>
        <el-button class="ipa-btn ipa-btn--ghost" :icon="Refresh" :loading="loading" round @click="loadAnalysis">
          更新
        </el-button>
      </div>
    </header>

    <div class="ipa-toolbar ipa-panel ipa-fade-in ipa-fade-in--d1">
      <div class="ipa-toolbar__fields">
        <div class="ipa-field ipa-field--period">
          <span class="ipa-field__pill"><el-icon><Calendar /></el-icon>期間</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="～"
            value-format="YYYY-MM-DD"
            size="small"
            class="ipa-field__control ipa-field__date"
          />
        </div>
        <div class="ipa-field ipa-field--inspector">
          <span class="ipa-field__pill"><el-icon><User /></el-icon>検査員</span>
          <el-select
            v-model="filterInspectorId"
            placeholder="すべて"
            clearable
            filterable
            size="small"
            class="ipa-field__control ipa-field__inspector-select"
          >
            <el-option label="（すべて）" :value="null" />
            <el-option v-for="u in inspectorOptions" :key="u.id" :label="inspectorLabel(u)" :value="u.id" />
          </el-select>
        </div>
        <div class="ipa-field ipa-field--product">
          <span class="ipa-field__pill"><el-icon><Goods /></el-icon>製品名</span>
          <el-select
            v-model="filterProductCd"
            placeholder="すべて"
            clearable
            filterable
            size="small"
            class="ipa-field__control ipa-field__product-select"
            :loading="loadingProductOptions"
          >
            <el-option label="（すべて）" value="" />
            <el-option
              v-for="p in productOptions"
              :key="p.product_cd"
              :label="productOptionLabel(p)"
              :value="p.product_cd"
            />
          </el-select>
        </div>
        <label class="ipa-check ipa-field ipa-field--check">
          <span class="ipa-field__pill ipa-field__pill--check">オプション</span>
          <el-checkbox v-model="includeIncomplete" size="small">未確定を含む</el-checkbox>
        </label>
      </div>
      <el-button type="primary" class="ipa-btn ipa-btn--primary" :loading="loading" round @click="loadAnalysis">
        分析実行
      </el-button>
    </div>

    <div v-loading="loading" class="ipa-body">
      <div class="ipa-kpi">
        <div
          v-for="card in kpiCards"
          :key="card.key"
          class="ipa-kpi__card"
          :class="`ipa-kpi__card--${card.tone}`"
        >
          <div class="ipa-kpi__accent" aria-hidden="true" />
          <div class="ipa-kpi__icon-wrap" :class="`ipa-kpi__icon-wrap--${card.tone}`">
            <el-icon :size="18"><component :is="card.icon" /></el-icon>
          </div>
          <div class="ipa-kpi__content">
            <div class="ipa-kpi__label">{{ card.label }}</div>
            <div class="ipa-kpi__value">{{ card.value }}</div>
            <div class="ipa-kpi__hint">{{ card.hint }}</div>
          </div>
        </div>
      </div>

      <Transition name="ipa-reveal">
        <div v-if="analysisData && contentVisible" key="content" class="ipa-content">
          <section class="ipa-panel ipa-panel--chart ipa-fade-in ipa-fade-in--d3">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><TrendCharts /></el-icon>
                <span class="ipa-panel__title">日別推移</span>
              </div>
              <span class="ipa-panel__badge">不良数 · 不良率</span>
            </div>
            <div ref="dailyChartRef" class="ipa-chart ipa-chart--main" />
          </section>

          <section v-if="defectRows.length" class="ipa-panel ipa-fade-in ipa-fade-in--d4">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><PieChart /></el-icon>
                <span class="ipa-panel__title">不良項目内訳（KT09）</span>
              </div>
              <span class="ipa-panel__badge">{{ defectRows.length }} 項目</span>
            </div>
            <div class="iqa-defect-layout">
              <div ref="defectChartRef" class="iqa-defect-chart" />
              <el-table :data="defectRows" size="small" class="ipa-table" max-height="280">
                <el-table-column label="不良項目" min-width="160" show-overflow-tooltip>
                  <template #default="{ row }">{{ row.defect_name || row.defect_cd }}</template>
                </el-table-column>
                <el-table-column prop="defect_cd" label="CD" width="72" />
                <el-table-column label="数量" width="72" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtInt(row.qty) }}</span></template>
                </el-table-column>
                <el-table-column label="構成比" width="72" align="right">
                  <template #default="{ row }">{{ fmtPct(row.share_percent) }}</template>
                </el-table-column>
                <el-table-column label="不良率" width="72" align="right">
                  <template #default="{ row }">{{ fmtPct(row.rate_per_actual_percent) }}</template>
                </el-table-column>
              </el-table>
            </div>
          </section>

          <div class="ipa-split">
            <section class="ipa-panel ipa-fade-in ipa-fade-in--d5">
              <div class="ipa-panel__head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico"><Goods /></el-icon>
                  <span class="ipa-panel__title">製品別</span>
                </div>
                <span class="ipa-panel__badge">{{ analysisData.by_product.length }} 品目</span>
              </div>
              <el-table :data="analysisData.by_product" size="small" class="ipa-table" max-height="360">
                <el-table-column prop="product_cd" label="CD" width="88" />
                <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
                <el-table-column label="件" width="44" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="72" align="right">
                  <template #default="{ row }">{{ fmtInt(row.sum_actual_qty) }}</template>
                </el-table-column>
                <el-table-column label="不良" width="64" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtInt(row.sum_defect_qty) }}</span></template>
                </el-table-column>
                <el-table-column label="不良率" width="72" align="right" sortable :sort-method="sortByDefectRate">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtPct(row.defect_rate_percent) }}</span></template>
                </el-table-column>
                <el-table-column label="TOP不良" min-width="140" show-overflow-tooltip>
                  <template #default="{ row }">
                    <template v-if="row.top_defect_cd">
                      {{ row.top_defect_name || row.top_defect_cd }}
                      <span class="iqa-top-qty">({{ fmtInt(row.top_defect_qty) }})</span>
                    </template>
                    <span v-else>—</span>
                  </template>
                </el-table-column>
              </el-table>
            </section>

            <section class="ipa-panel ipa-fade-in ipa-fade-in--d5">
              <div class="ipa-panel__head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico"><User /></el-icon>
                  <span class="ipa-panel__title">検査員別</span>
                </div>
                <span class="ipa-panel__badge">{{ analysisData.by_inspector.length }} 名</span>
              </div>
              <div ref="inspectorChartRef" class="ipa-chart ipa-chart--side" />
              <el-table :data="analysisData.by_inspector" size="small" class="ipa-table" max-height="260">
                <el-table-column prop="inspector_name" label="検査員" min-width="100" show-overflow-tooltip />
                <el-table-column label="件" width="48" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="72" align="right">
                  <template #default="{ row }">{{ fmtInt(row.sum_actual_qty) }}</template>
                </el-table-column>
                <el-table-column label="不良" width="64" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtInt(row.sum_defect_qty) }}</span></template>
                </el-table-column>
                <el-table-column label="不良率" width="72" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtPct(row.defect_rate_percent) }}</span></template>
                </el-table-column>
                <el-table-column label="不良件" width="64" align="right">
                  <template #default="{ row }">{{ row.sessions_with_defect_count ?? 0 }}</template>
                </el-table-column>
              </el-table>
            </section>
          </div>

          <section v-if="productDefectRows.length" class="ipa-panel ipa-fade-in ipa-fade-in--d6">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><Grid /></el-icon>
                <span class="ipa-panel__title">製品 × 不良項目</span>
              </div>
              <span class="ipa-panel__badge">{{ productDefectRows.length }} 行</span>
            </div>
            <el-table :data="productDefectRows" size="small" class="ipa-table" max-height="360" stripe>
              <el-table-column prop="product_cd" label="CD" width="88" />
              <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
              <el-table-column label="不良項目" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">{{ row.defect_name || row.defect_cd }}</template>
              </el-table-column>
              <el-table-column prop="defect_cd" label="CD" width="72" />
              <el-table-column label="数量" width="72" align="right">
                <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtInt(row.qty) }}</span></template>
              </el-table-column>
            </el-table>
          </section>

          <section class="ipa-panel ipa-fade-in ipa-fade-in--d7">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><List /></el-icon>
                <span class="ipa-panel__title">セッション明細</span>
              </div>
              <span class="ipa-panel__badge">{{ analysisData.sessions.length }} 件</span>
            </div>
            <el-table :data="analysisData.sessions" size="small" class="ipa-table ipa-table--detail" max-height="380">
              <el-table-column prop="production_day" label="生産日" width="102" fixed />
              <el-table-column prop="inspector_display_name" label="検査員" width="100" show-overflow-tooltip />
              <el-table-column prop="product_cd" label="CD" width="88" />
              <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
              <el-table-column label="生産" width="64" align="right">
                <template #default="{ row }">{{ fmtInt(row.actual_production_quantity) }}</template>
              </el-table-column>
              <el-table-column label="不良" width="52" align="right">
                <template #default="{ row }">
                  <span :class="{ 'ipa-num ipa-num--warn': (row.defect_qty ?? 0) > 0 }">{{ fmtInt(row.defect_qty) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="不良率" width="68" align="right">
                <template #default="{ row }">{{ fmtPct(row.defect_rate_percent) }}</template>
              </el-table-column>
              <el-table-column label="不良内訳" min-width="180" show-overflow-tooltip>
                <template #default="{ row }">{{ defectBreakdownText(row) }}</template>
              </el-table-column>
              <el-table-column label="状態" width="72" align="center" fixed="right">
                <template #default="{ row }">
                  <span class="ipa-status" :class="row.is_completed ? 'ipa-status--ok' : 'ipa-status--pending'">
                    {{ row.is_completed ? '確定' : '未確定' }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
      </Transition>

      <div v-if="!loading && !analysisData" class="ipa-empty ipa-fade-in">
        <div class="ipa-empty__icon"><el-icon :size="40"><DataAnalysis /></el-icon></div>
        <p>期間を選択して「分析実行」をクリック</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  Calendar,
  CircleCheck,
  DataAnalysis,
  Goods,
  Grid,
  List,
  PieChart,
  Refresh,
  TrendCharts,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchInspectionQualityAnalysis,
  type InspectionQualityAnalysisData,
  type InspectionQualityBucket,
  type InspectionQualityProductRow,
  type InspectionQualitySessionRow,
} from '@/api/inspectionManagement'
import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import { getProductList } from '@/api/master/productMaster'
import type { Product } from '@/types/master'
import { getJSTToday, parseDateAsJST } from '@/utils/dateFormat'
import { filterInspectionSelectableProducts } from '@/views/mes/shared/inspectionProductFilter'

defineOptions({ name: 'MesInspectionQualityAnalysis' })

const loading = ref(false)
const contentVisible = ref(false)
const analysisData = ref<InspectionQualityAnalysisData | null>(null)
const inspectorOptions = ref<UserListItem[]>([])
const filterInspectorId = ref<number | null>(null)
const filterProductCd = ref('')
const includeIncomplete = ref(false)
const productOptions = ref<Product[]>([])
const loadingProductOptions = ref(false)
const dailyChartRef = ref<HTMLElement | null>(null)
const defectChartRef = ref<HTMLElement | null>(null)
const inspectorChartRef = ref<HTMLElement | null>(null)
let dailyChart: ECharts | null = null
let defectChart: ECharts | null = null
let inspectorChart: ECharts | null = null

function shiftJstDate(isoDay: string, deltaDays: number): string {
  const base = parseDateAsJST(isoDay)
  if (!base) return isoDay
  base.setDate(base.getDate() + deltaDays)
  return base.toISOString().slice(0, 10)
}

const dateRange = ref<[string, string]>([shiftJstDate(getJSTToday(), -29), getJSTToday()])

const emptySummary = (): InspectionQualityBucket => ({
  session_count: 0,
  completed_session_count: 0,
  sum_actual_qty: 0,
  sum_defect_qty: 0,
  defect_rate_percent: null,
  sessions_with_defect_count: 0,
  defect_item_kinds_count: 0,
})

const summary = computed(() => analysisData.value?.summary ?? emptySummary())
const defectRows = computed(() => analysisData.value?.defect_by_item ?? [])
const productDefectRows = computed(() => analysisData.value?.by_product_defect ?? [])

const kpiCards = computed(() => {
  const s = summary.value
  return [
    {
      key: 'actual',
      label: '生産数合計',
      value: fmtInt(s.sum_actual_qty),
      hint: `${fmtInt(s.session_count)} セッション`,
      tone: 'sky',
      icon: markRaw(CircleCheck),
    },
    {
      key: 'defect',
      label: '不良数合計',
      value: fmtInt(s.sum_defect_qty),
      hint: `不良率 ${fmtPct(s.defect_rate_percent)}`,
      tone: 'amber',
      icon: markRaw(WarningFilled),
    },
    {
      key: 'defect-sessions',
      label: '不良セッション',
      value: fmtInt(s.sessions_with_defect_count),
      hint: '不良あり確定/対象',
      tone: 'rose',
      icon: markRaw(List),
    },
    {
      key: 'defect-kinds',
      label: '不良項目数',
      value: fmtInt(s.defect_item_kinds_count),
      hint: 'KT09 内訳種類',
      tone: 'violet',
      icon: markRaw(Grid),
    },
    {
      key: 'rate',
      label: '総合不良率',
      value: fmtPct(s.defect_rate_percent),
      hint: '生産数対比',
      tone: 'emerald',
      icon: markRaw(TrendCharts),
    },
  ]
})

function inspectorLabel(u: UserListItem): string {
  return (u.full_name || u.username || `ID:${u.id}`).trim()
}

function productOptionLabel(p: Product): string {
  const name = (p.product_name || '').trim()
  return name ? `${name} (${p.product_cd})` : p.product_cd
}

function fmtInt(v?: number | null): string {
  if (v == null || Number.isNaN(v)) return '0'
  return v.toLocaleString()
}

function fmtPct(v?: number | null): string {
  if (v == null || Number.isNaN(v)) return '—'
  return `${v.toFixed(1)}%`
}

function sortByDefectRate(a: InspectionQualityProductRow, b: InspectionQualityProductRow): number {
  return (a.defect_rate_percent ?? 0) - (b.defect_rate_percent ?? 0)
}

function defectBreakdownText(row: InspectionQualitySessionRow): string {
  const items = row.defect_breakdown
  if (items?.length) {
    return items.map((item) => `${item.defect_name || item.defect_cd} ${item.qty}`).join(' · ')
  }
  const map = row.mes_defect_by_item
  if (!map || !Object.keys(map).length) return '—'
  return Object.entries(map)
    .filter(([, qty]) => Number(qty) > 0)
    .map(([cd, qty]) => `${cd} ${qty}`)
    .join(' · ')
}

function disposeCharts() {
  dailyChart?.dispose()
  defectChart?.dispose()
  inspectorChart?.dispose()
  dailyChart = null
  defectChart = null
  inspectorChart = null
}

function renderDailyChart() {
  const el = dailyChartRef.value
  const daily = analysisData.value?.daily ?? []
  if (!el || !daily.length) {
    dailyChart?.dispose()
    dailyChart = null
    return
  }
  if (!dailyChart) dailyChart = echarts.init(el)
  dailyChart.setOption({
    grid: { left: 48, right: 48, top: 32, bottom: 32 },
    tooltip: { trigger: 'axis' },
    legend: { data: ['不良数', '不良率'], top: 0 },
    xAxis: { type: 'category', data: daily.map((d) => d.day.slice(5)) },
    yAxis: [
      { type: 'value', name: '不良数' },
      { type: 'value', name: '%', max: 100, splitLine: { show: false } },
    ],
    series: [
      {
        name: '不良数',
        type: 'bar',
        data: daily.map((d) => d.sum_defect_qty ?? 0),
        itemStyle: { color: '#f97316', borderRadius: [4, 4, 0, 0] },
      },
      {
        name: '不良率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: daily.map((d) => d.defect_rate_percent ?? 0),
        itemStyle: { color: '#ef4444' },
        areaStyle: { color: 'rgba(239,68,68,0.1)' },
      },
    ],
  })
}

function renderDefectChart() {
  const el = defectChartRef.value
  const rows = defectRows.value.slice(0, 10)
  if (!el || !rows.length) {
    defectChart?.dispose()
    defectChart = null
    return
  }
  if (!defectChart) defectChart = echarts.init(el)
  defectChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [
      {
        type: 'pie',
        radius: ['42%', '70%'],
        data: rows.map((r) => ({
          name: r.defect_name || r.defect_cd,
          value: r.qty,
        })),
        label: { fontSize: 10 },
      },
    ],
  })
}

function renderInspectorChart() {
  const el = inspectorChartRef.value
  const rows = (analysisData.value?.by_inspector ?? []).slice(0, 8)
  if (!el || !rows.length) {
    inspectorChart?.dispose()
    inspectorChart = null
    return
  }
  if (!inspectorChart) inspectorChart = echarts.init(el)
  inspectorChart.setOption({
    grid: { left: 88, right: 16, top: 8, bottom: 8 },
    xAxis: { type: 'value', max: (v: { max: number }) => Math.max(v.max * 1.1, 1) },
    yAxis: {
      type: 'category',
      data: rows.map((r) => r.inspector_name ?? '—').reverse(),
      axisLabel: { fontSize: 10, width: 72, overflow: 'truncate' },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => r.defect_rate_percent ?? 0).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#fb923c' },
            { offset: 1, color: '#ef4444' },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
        label: { show: true, position: 'right', formatter: '{c}%', fontSize: 10 },
      },
    ],
  })
}

function renderAllCharts() {
  renderDailyChart()
  renderDefectChart()
  renderInspectorChart()
}

async function loadInspectors() {
  try {
    const res = (await getUsers({ page: 1, pageSize: 500, status: 'active' })) as PaginatedUserResponse
    inspectorOptions.value = res?.data?.items ?? res?.items ?? []
  } catch {
    inspectorOptions.value = []
  }
}

async function loadProductOptions() {
  loadingProductOptions.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 500, is_active: true })
    const list = res?.data?.items ?? res?.items ?? []
    productOptions.value = filterInspectionSelectableProducts(list)
  } catch {
    productOptions.value = []
  } finally {
    loadingProductOptions.value = false
  }
}

async function loadAnalysis() {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) {
    ElMessage.warning('期間を選択してください')
    return
  }
  loading.value = true
  contentVisible.value = false
  try {
    const res = await fetchInspectionQualityAnalysis({
      start_date: start,
      end_date: end,
      mes_inspector_user_id: filterInspectorId.value,
      product_cd: filterProductCd.value || undefined,
      include_incomplete: includeIncomplete.value,
    })
    if (!res?.success || !res.data) {
      ElMessage.error(res?.message || '分析データの取得に失敗しました')
      analysisData.value = null
      disposeCharts()
      return
    }
    analysisData.value = res.data
    await nextTick()
    contentVisible.value = true
    await nextTick()
    renderAllCharts()
  } catch (e: unknown) {
    analysisData.value = null
    disposeCharts()
    ElMessage.error(e instanceof Error ? e.message : '分析データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

watch(
  () => [analysisData.value?.daily, analysisData.value?.defect_by_item, analysisData.value?.by_inspector],
  () => nextTick(() => renderAllCharts()),
)

onMounted(() => {
  loadInspectors()
  loadProductOptions()
  loadAnalysis()
  window.addEventListener('resize', renderAllCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderAllCharts)
  disposeCharts()
})
</script>

<style scoped lang="scss">
@use '../shared/inspectionAnalysisIpa.scss';

.iqa-hero__icon {
  background: linear-gradient(135deg, #fb923c, #ef4444) !important;
}

.iqa-defect-layout {
  display: grid;
  grid-template-columns: minmax(220px, 36%) 1fr;
  gap: 12px;
  align-items: start;
}

.iqa-defect-chart {
  width: 100%;
  height: 260px;
}

.iqa-top-qty {
  color: #94a3b8;
  font-size: 11px;
  margin-left: 4px;
}

.ipa-kpi__card--rose {
  background: linear-gradient(160deg, #ffffff 0%, #fff1f2 45%, #ffe4e6 100%);
  border-color: rgba(244, 63, 94, 0.22);
}

.ipa-kpi__card--rose .ipa-kpi__accent {
  background: linear-gradient(90deg, #f43f5e, #fb7185);
}

.ipa-kpi__card--rose .ipa-kpi__label { color: #e11d48; }
.ipa-kpi__card--rose .ipa-kpi__value { color: #be123c; }
.ipa-kpi__card--rose .ipa-kpi__hint { color: #fb7185; }

.ipa-kpi__icon-wrap--rose {
  background: rgba(244, 63, 94, 0.12);
  color: #e11d48;
}

@media (max-width: 960px) {
  .iqa-defect-layout {
    grid-template-columns: 1fr;
  }
}
</style>
