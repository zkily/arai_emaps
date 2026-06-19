<template>
  <div class="iqa ipa">
    <div class="ipa__bg" aria-hidden="true">
      <div class="ipa__orb ipa__orb--1" />
      <div class="ipa__orb ipa__orb--2" />
      <div class="ipa__orb ipa__orb--3" />
    </div>

    <header class="ipa-hero ipa-fade-in">
      <div class="ipa-hero__main">
        <div class="ipa-hero__icon wqa-hero__icon">
          <el-icon :size="24"><Connection /></el-icon>
          <span class="ipa-hero__icon-glow" />
        </div>
        <div class="ipa-hero__text">
          <div class="ipa-hero__eyebrow">MES · 実績分析</div>
          <h1 class="ipa-hero__title">溶接工程 — 品質分析</h1>
          <p class="ipa-hero__meta">welding_management · 製品不良 · 不良項目 · 不良率</p>
        </div>
      </div>
      <div class="ipa-hero__actions">
        <span v-if="analysisData" class="ipa-hero__range">
          {{ analysisData.start_date }} ～ {{ analysisData.end_date }}
        </span>
        <el-button class="ipa-btn ipa-btn--ghost" :icon="Refresh" :loading="loading" round @click="() => loadAnalysis()">
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
        <div class="ipa-field ipa-field--operator">
          <span class="ipa-field__pill"><el-icon><User /></el-icon>溶接作業者</span>
          <el-select
            v-model="filterOperatorId"
            placeholder="すべて"
            clearable
            filterable
            size="small"
            class="ipa-field__control ipa-field__operator-select"
          >
            <el-option label="（すべて）" value="" />
            <el-option v-for="u in operatorOptions" :key="u.id" :label="operatorLabel(u)" :value="u.id" />
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
            <div v-if="dailyRows.length" class="wqa-daily-table-wrap">
              <el-table
                :data="dailyRows"
                size="small"
                stripe
                class="ipa-table wqa-daily-table"
                :max-height="dailyTableMaxHeight"
              >
                <el-table-column prop="day" label="生産日" min-width="128" />
                <el-table-column label="件数" min-width="96" align="right">
                  <template #default="{ row }">
                    <span class="wqa-daily-num">{{ row.session_count ?? 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="生産数" min-width="120" align="right">
                  <template #default="{ row }">
                    <span class="wqa-daily-num wqa-daily-num--actual">{{ fmtInt(row.sum_actual_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="不良数" min-width="120" align="right">
                  <template #default="{ row }">
                    <span class="wqa-daily-num wqa-daily-num--defect">{{ fmtInt(row.sum_defect_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="不良率" min-width="120" align="right">
                  <template #default="{ row }">
                    <span class="wqa-rate-pill" :class="defectRatePillClass(row.defect_rate_percent)">
                      {{ fmtPct(row.defect_rate_percent) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </section>

          <section v-if="defectRows.length" class="ipa-panel ipa-fade-in ipa-fade-in--d4">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><PieChart /></el-icon>
                <span class="ipa-panel__title">不良項目内訳（KT07）</span>
              </div>
              <span class="ipa-panel__badge">{{ defectRows.length }} 項目</span>
            </div>
            <div class="wqa-defect-layout">
              <div ref="defectChartRef" class="wqa-defect-chart" />
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
            <section class="ipa-panel ipa-panel--product wqa-panel--product ipa-fade-in ipa-fade-in--d5">
              <div class="ipa-panel__head wqa-product-head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico ipa-panel__ico--product"><Goods /></el-icon>
                  <div>
                    <span class="ipa-panel__title">製品別</span>
                    <div class="wqa-section-head__desc">製品ごとの不良状況を比較</div>
                  </div>
                </div>
                <div class="ipa-panel__badges">
                  <span class="ipa-panel__badge ipa-panel__badge--soft">{{ productDisplayRows.length }} 品目</span>
                  <span v-if="productSectionTotalQty > 0" class="ipa-panel__badge ipa-panel__badge--product">
                    生産 {{ fmtInt(productSectionTotalQty) }}
                  </span>
                  <span v-if="productSectionTotalDefect > 0" class="ipa-panel__badge wqa-badge--defect">
                    不良 {{ fmtInt(productSectionTotalDefect) }}
                  </span>
                </div>
              </div>
              <div ref="productChartRef" class="ipa-chart ipa-chart--side ipa-chart--product wqa-product-chart" />
              <el-table
                :data="productDisplayRows"
                size="small"
                stripe
                class="ipa-table ipa-table--product wqa-product-table"
                max-height="360"
              >
                <el-table-column label="#" width="40" align="center" fixed>
                  <template #default="{ $index }">
                    <span class="wqa-row-rank" :class="productRankClass($index)">{{ $index + 1 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="product_cd" label="CD" width="92">
                  <template #default="{ row }">
                    <span class="wqa-product-cd">{{ row.product_cd }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="product_name" label="製品名" min-width="132" show-overflow-tooltip />
                <el-table-column label="件数" width="60" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産数" width="84" align="right">
                  <template #default="{ row }">
                    <span class="wqa-daily-num wqa-daily-num--actual">{{ fmtInt(row.sum_actual_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="不良数" width="72" align="right">
                  <template #default="{ row }">
                    <span class="wqa-daily-num wqa-daily-num--defect">{{ fmtInt(row.sum_defect_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column
                  label="不良率"
                  width="88"
                  align="right"
                  sortable
                  :sort-method="sortByDefectRate"
                >
                  <template #default="{ row }">
                    <span class="wqa-rate-pill" :class="defectRatePillClass(row.defect_rate_percent)">
                      {{ fmtPct(row.defect_rate_percent) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="TOP不良" min-width="128" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span v-if="row.top_defect_cd" class="wqa-top-defect">
                      <span class="wqa-top-defect__name">{{ row.top_defect_name || row.top_defect_cd }}</span>
                      <span class="wqa-top-defect__qty">{{ fmtInt(row.top_defect_qty) }}</span>
                    </span>
                    <span v-else class="wqa-top-defect wqa-top-defect--empty">—</span>
                  </template>
                </el-table-column>
              </el-table>
            </section>

            <section class="ipa-panel ipa-panel--operator wqa-panel--operator ipa-fade-in ipa-fade-in--d5">
              <div class="ipa-panel__head wqa-operator-head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico ipa-panel__ico--operator"><User /></el-icon>
                  <div>
                    <span class="ipa-panel__title">溶接作業者別</span>
                    <div class="wqa-section-head__desc">溶接作業者ごとの不良状況を比較</div>
                  </div>
                </div>
                <div class="ipa-panel__badges">
                  <span class="ipa-panel__badge ipa-panel__badge--soft">{{ operatorDisplayRows.length }} 名</span>
                  <span v-if="operatorSectionTotalQty > 0" class="ipa-panel__badge ipa-panel__badge--operator">
                    生産 {{ fmtInt(operatorSectionTotalQty) }}
                  </span>
                  <span v-if="operatorSectionTotalDefect > 0" class="ipa-panel__badge wqa-badge--defect">
                    不良 {{ fmtInt(operatorSectionTotalDefect) }}
                  </span>
                </div>
              </div>
              <div ref="operatorChartRef" class="ipa-chart ipa-chart--side ipa-chart--operator wqa-operator-chart" />
              <el-table
                :data="operatorDisplayRows"
                size="small"
                stripe
                class="ipa-table ipa-table--operator wqa-operator-table"
                max-height="360"
              >
                <el-table-column label="#" width="40" align="center" fixed>
                  <template #default="{ $index }">
                    <span class="wqa-row-rank" :class="rowRankClass($index)">{{ $index + 1 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="operator_name" label="溶接作業者" min-width="108" show-overflow-tooltip />
                <el-table-column label="件数" width="60" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産数" width="84" align="right">
                  <template #default="{ row }">
                    <span class="wqa-daily-num wqa-daily-num--actual">{{ fmtInt(row.sum_actual_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="不良数" width="72" align="right">
                  <template #default="{ row }">
                    <span class="wqa-daily-num wqa-daily-num--defect">{{ fmtInt(row.sum_defect_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="不良率" width="88" align="right">
                  <template #default="{ row }">
                    <span class="wqa-rate-pill" :class="defectRatePillClass(row.defect_rate_percent)">
                      {{ fmtPct(row.defect_rate_percent) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="不良件" width="72" align="right">
                  <template #default="{ row }">
                    <span class="wqa-defect-session-pill">{{ row.sessions_with_defect_count ?? 0 }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </section>
          </div>

          <section v-if="productDefectDisplayRows.length" class="ipa-panel wqa-panel--product-defect ipa-fade-in ipa-fade-in--d6">
            <div class="ipa-panel__head wqa-product-defect-head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico ipa-panel__ico--matrix"><Grid /></el-icon>
                <div>
                  <span class="ipa-panel__title">製品 × 不良項目</span>
                  <div class="wqa-section-head__desc">製品と不良項目の組み合わせ内訳</div>
                </div>
              </div>
              <div class="ipa-panel__badges">
                <span class="ipa-panel__badge ipa-panel__badge--soft">{{ productDefectDisplayRows.length }} 行</span>
                <span v-if="productDefectTotalQty > 0" class="ipa-panel__badge wqa-badge--matrix">
                  不良合計 {{ fmtInt(productDefectTotalQty) }}
                </span>
              </div>
            </div>
            <el-table
              :data="productDefectDisplayRows"
              size="small"
              stripe
              class="ipa-table wqa-product-defect-table"
              max-height="400"
            >
              <el-table-column label="#" width="44" align="center" fixed>
                <template #default="{ $index }">
                  <span class="wqa-row-rank" :class="rowRankClass($index)">{{ $index + 1 }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_cd" label="製品CD" width="96">
                <template #default="{ row }">
                  <span class="wqa-product-cd">{{ row.product_cd }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="製品名" min-width="140" show-overflow-tooltip />
              <el-table-column label="不良項目" min-width="148" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="wqa-defect-name">{{ row.defect_name || row.defect_cd }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="defect_cd" label="不良CD" width="88">
                <template #default="{ row }">
                  <span class="wqa-defect-cd">{{ row.defect_cd }}</span>
                </template>
              </el-table-column>
              <el-table-column label="数量" width="88" align="right" sortable :sort-method="sortProductDefectByQty">
                <template #default="{ row }">
                  <span class="wqa-qty-pill">{{ fmtInt(row.qty) }}</span>
                </template>
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
              <el-table-column prop="operator_display_name" label="溶接作業者" width="100" show-overflow-tooltip />
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
        <p>期間を選択すると自動で分析結果を表示します</p>
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
  Connection,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchWeldingQualityAnalysis,
  type WeldingQualityAnalysisData,
  type WeldingQualityBucket,
  type WeldingQualityProductRow,
  type WeldingQualityProductDefectRow,
  type WeldingQualitySessionRow,
} from '@/api/weldingManagement'
import { getProductList } from '@/api/master/productMaster'
import type { UserListItem } from '@/api/system'
import type { Product } from '@/types/master'
import { getJSTToday, parseDateAsJST } from '@/utils/dateFormat'
import { filterWeldingSelectableProducts } from '@/views/mes/shared/weldingProductFilter'
import { fetchWeldingSectionOperators } from '@/views/mes/shared/weldingOperatorFilter'

defineOptions({ name: 'MesWeldingQualityAnalysis' })

const loading = ref(false)
const contentVisible = ref(false)
const analysisData = ref<WeldingQualityAnalysisData | null>(null)
const operatorOptions = ref<UserListItem[]>([])
const filterOperatorId = ref<number | ''>('')
const filterProductCd = ref('')
const includeIncomplete = ref(false)
const productOptions = ref<Product[]>([])
const loadingProductOptions = ref(false)
const dailyChartRef = ref<HTMLElement | null>(null)
const defectChartRef = ref<HTMLElement | null>(null)
const productChartRef = ref<HTMLElement | null>(null)
const operatorChartRef = ref<HTMLElement | null>(null)
let dailyChart: ECharts | null = null
let defectChart: ECharts | null = null
let productChart: ECharts | null = null
let operatorChart: ECharts | null = null

function shiftJstDate(isoDay: string, deltaDays: number): string {
  const base = parseDateAsJST(isoDay)
  if (!base) return isoDay
  base.setDate(base.getDate() + deltaDays)
  return base.toISOString().slice(0, 10)
}

const dateRange = ref<[string, string]>([shiftJstDate(getJSTToday(), -29), getJSTToday()])

const DAILY_TABLE_VISIBLE_ROWS = 7
const DAILY_TABLE_ROW_HEIGHT = 40
const DAILY_TABLE_HEADER_HEIGHT = 40
const dailyTableMaxHeight = DAILY_TABLE_HEADER_HEIGHT + DAILY_TABLE_ROW_HEIGHT * DAILY_TABLE_VISIBLE_ROWS

const emptySummary = (): WeldingQualityBucket => ({
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
const dailyRows = computed(() => analysisData.value?.daily ?? [])
const productDisplayRows = computed(() => {
  const rows = analysisData.value?.by_product ?? []
  return [...rows].sort((a, b) => (b.defect_rate_percent ?? 0) - (a.defect_rate_percent ?? 0))
})
const productSectionTotalQty = computed(() =>
  productDisplayRows.value.reduce((sum, row) => sum + (row.sum_actual_qty ?? 0), 0),
)
const productSectionTotalDefect = computed(() =>
  productDisplayRows.value.reduce((sum, row) => sum + (row.sum_defect_qty ?? 0), 0),
)
const operatorDisplayRows = computed(() => {
  const rows = analysisData.value?.by_operator ?? []
  return [...rows].sort((a, b) => (b.defect_rate_percent ?? 0) - (a.defect_rate_percent ?? 0))
})
const operatorSectionTotalQty = computed(() =>
  operatorDisplayRows.value.reduce((sum, row) => sum + (row.sum_actual_qty ?? 0), 0),
)
const operatorSectionTotalDefect = computed(() =>
  operatorDisplayRows.value.reduce((sum, row) => sum + (row.sum_defect_qty ?? 0), 0),
)
const productDefectDisplayRows = computed(() =>
  [...productDefectRows.value].sort((a, b) => (b.qty ?? 0) - (a.qty ?? 0)),
)
const productDefectTotalQty = computed(() =>
  productDefectDisplayRows.value.reduce((sum, row) => sum + (row.qty ?? 0), 0),
)

let analysisRequestSeq = 0
let analysisDebounceTimer: ReturnType<typeof setTimeout> | null = null

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
      icon: markRaw(Connection),
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
      hint: 'KT07 内訳種類',
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

function operatorLabel(u: UserListItem): string {
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

function sortByDefectRate(a: WeldingQualityProductRow, b: WeldingQualityProductRow): number {
  return (a.defect_rate_percent ?? 0) - (b.defect_rate_percent ?? 0)
}

function sortProductDefectByQty(a: WeldingQualityProductDefectRow, b: WeldingQualityProductDefectRow): number {
  return (a.qty ?? 0) - (b.qty ?? 0)
}

function defectRatePillClass(rate?: number | null): string {
  const v = rate ?? 0
  if (v >= 10) return 'wqa-rate-pill--high'
  if (v >= 3) return 'wqa-rate-pill--mid'
  if (v > 0) return 'wqa-rate-pill--low'
  return 'wqa-rate-pill--zero'
}

function rowRankClass(index: number): string {
  if (index === 0) return 'wqa-row-rank--gold'
  if (index === 1) return 'wqa-row-rank--silver'
  if (index === 2) return 'wqa-row-rank--bronze'
  return ''
}

function productRankClass(index: number): string {
  return rowRankClass(index)
}

function defectBreakdownText(row: WeldingQualitySessionRow): string {
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
  productChart?.dispose()
  operatorChart?.dispose()
  dailyChart = null
  defectChart = null
  productChart = null
  operatorChart = null
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
    grid: { left: 48, right: 48, top: 40, bottom: 32 },
    tooltip: { trigger: 'axis' },
    legend: { data: ['不良数', '不良率'], top: 0 },
    xAxis: { type: 'category', data: daily.map((d) => d.day.slice(5)) },
    yAxis: [
      { type: 'value', name: '不良数' },
      { type: 'value', name: '%', min: 0, max: 30, splitLine: { show: false } },
    ],
    series: [
      {
        name: '不良数',
        type: 'bar',
        data: daily.map((d) => d.sum_defect_qty ?? 0),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ffedd5' },
            { offset: 0.55, color: '#fed7aa' },
            { offset: 1, color: '#fdba74' },
          ]),
          borderRadius: [4, 4, 0, 0],
          borderColor: 'rgba(251, 146, 60, 0.35)',
          borderWidth: 1,
        },
        label: {
          show: true,
          position: 'top',
          fontSize: 10,
          fontWeight: 600,
          color: '#ea580c',
          formatter: (params: { value?: number | null }) => {
            const v = Number(params.value ?? 0)
            return Number.isFinite(v) && v > 0 ? fmtInt(v) : ''
          },
        },
      },
      {
        name: '不良率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: daily.map((d) => d.defect_rate_percent ?? 0),
        itemStyle: { color: '#ef4444' },
        areaStyle: { color: 'rgba(239,68,68,0.1)' },
        label: {
          show: true,
          position: 'top',
          fontSize: 10,
          fontWeight: 600,
          color: '#dc2626',
          formatter: (params: { value?: number | null }) => {
            const v = Number(params.value ?? 0)
            return Number.isFinite(v) && v > 0 ? `${v.toFixed(1)}%` : ''
          },
        },
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

function renderProductChart() {
  const el = productChartRef.value
  const rows = productDisplayRows.value.slice(0, 8)
  if (!el || !rows.length) {
    productChart?.dispose()
    productChart = null
    return
  }
  if (!productChart) productChart = echarts.init(el)
  productChart.setOption({
    grid: { left: 96, right: 24, top: 8, bottom: 8 },
    xAxis: { type: 'value', max: 30, splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.2)' } } },
    yAxis: {
      type: 'category',
      data: rows
        .map((r) => (r.product_name || r.product_cd || '—').slice(0, 14))
        .reverse(),
      axisLabel: { fontSize: 10, width: 80, overflow: 'truncate', color: '#64748b' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => r.defect_rate_percent ?? 0).reverse(),
        barMaxWidth: 14,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#fed7aa' },
            { offset: 1, color: '#fb923c' },
          ]),
          borderRadius: [0, 6, 6, 0],
        },
        label: {
          show: true,
          position: 'right',
          formatter: (p: { value?: number | null }) => {
            const v = Number(p.value ?? 0)
            return v > 0 ? `${v.toFixed(1)}%` : ''
          },
          fontSize: 10,
          color: '#c2410c',
        },
      },
    ],
  })
}

function renderOperatorChart() {
  const el = operatorChartRef.value
  const rows = operatorDisplayRows.value.slice(0, 8)
  if (!el || !rows.length) {
    operatorChart?.dispose()
    operatorChart = null
    return
  }
  if (!operatorChart) operatorChart = echarts.init(el)
  operatorChart.setOption({
    grid: { left: 88, right: 28, top: 8, bottom: 8 },
    xAxis: { type: 'value', max: 30, splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.2)' } } },
    yAxis: {
      type: 'category',
      data: rows.map((r) => r.operator_name ?? '—').reverse(),
      axisLabel: { fontSize: 10, width: 72, overflow: 'truncate', color: '#64748b' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => r.defect_rate_percent ?? 0).reverse(),
        barMaxWidth: 14,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#c7d2fe' },
            { offset: 1, color: '#6366f1' },
          ]),
          borderRadius: [0, 6, 6, 0],
        },
        label: {
          show: true,
          position: 'right',
          formatter: (p: { value?: number | null }) => {
            const v = Number(p.value ?? 0)
            return v > 0 ? `${v.toFixed(1)}%` : ''
          },
          fontSize: 10,
          color: '#4338ca',
        },
      },
    ],
  })
}

function renderAllCharts() {
  renderDailyChart()
  renderDefectChart()
  renderProductChart()
  renderOperatorChart()
}

async function loadOperators() {
  try {
    operatorOptions.value = await fetchWeldingSectionOperators()
    if (filterOperatorId.value !== '') {
      const exists = operatorOptions.value.some((u: UserListItem) => u.id === filterOperatorId.value)
      if (!exists) filterOperatorId.value = ''
    }
  } catch {
    operatorOptions.value = []
    if (filterOperatorId.value !== '') filterOperatorId.value = ''
  }
}

async function loadProductOptions() {
  loadingProductOptions.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    const list = res?.data?.list ?? res?.list ?? []
    productOptions.value = filterWeldingSelectableProducts(list)
  } catch {
    productOptions.value = []
  } finally {
    loadingProductOptions.value = false
  }
}

async function loadAnalysis(options?: { silent?: boolean }) {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) {
    if (!options?.silent) ElMessage.warning('期間を選択してください')
    return
  }
  const seq = ++analysisRequestSeq
  loading.value = true
  contentVisible.value = false
  try {
    const res = await fetchWeldingQualityAnalysis({
      start_date: start,
      end_date: end,
      mes_operator_user_id: filterOperatorId.value === '' ? undefined : filterOperatorId.value,
      product_cd: filterProductCd.value || undefined,
      include_incomplete: includeIncomplete.value,
    })
    if (seq !== analysisRequestSeq) return
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
    if (seq !== analysisRequestSeq) return
    analysisData.value = null
    disposeCharts()
    ElMessage.error(e instanceof Error ? e.message : '分析データの取得に失敗しました')
  } finally {
    if (seq === analysisRequestSeq) loading.value = false
  }
}

function scheduleLoadAnalysis() {
  if (analysisDebounceTimer) clearTimeout(analysisDebounceTimer)
  analysisDebounceTimer = setTimeout(() => {
    analysisDebounceTimer = null
    void loadAnalysis({ silent: true })
  }, 350)
}

watch(
  () => [
    analysisData.value?.daily,
    analysisData.value?.defect_by_item,
    analysisData.value?.by_product,
    analysisData.value?.by_operator,
  ],
  () => nextTick(() => renderAllCharts()),
)

watch(dateRange, () => scheduleLoadAnalysis(), { deep: true })
watch(filterOperatorId, scheduleLoadAnalysis)
watch(filterProductCd, scheduleLoadAnalysis)
watch(includeIncomplete, scheduleLoadAnalysis)

onMounted(async () => {
  await Promise.all([loadOperators(), loadProductOptions()])
  await loadAnalysis({ silent: true })
  window.addEventListener('resize', renderAllCharts)
})

onBeforeUnmount(() => {
  if (analysisDebounceTimer) clearTimeout(analysisDebounceTimer)
  window.removeEventListener('resize', renderAllCharts)
  disposeCharts()
})
</script>

<style scoped lang="scss">
@use '../shared/inspectionAnalysisIpa.scss';

.wqa-hero__icon {
  background: linear-gradient(135deg, #fb923c, #ef4444) !important;
}

.wqa-defect-layout {
  display: grid;
  grid-template-columns: minmax(220px, 36%) 1fr;
  gap: 12px;
  align-items: start;
}

.wqa-defect-chart {
  width: 100%;
  height: 260px;
}

.wqa-top-qty {
  color: #94a3b8;
  font-size: 11px;
  margin-left: 4px;
}

.wqa-daily-table-wrap {
  width: 100%;
  margin-top: 14px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
}

.wqa-daily-table {
  width: 100%;

  :deep(.el-table__inner-wrapper) {
    max-height: inherit;
  }

  :deep(.el-table__header table),
  :deep(.el-table__body table) {
    width: 100% !important;
    table-layout: fixed;
  }

  :deep(.el-table__header th) {
    background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
    color: #475569;
    font-size: 11px;
    font-weight: 700;
    padding: 10px 0;
  }

  :deep(.el-table__body td) {
    padding: 9px 0;
    font-size: 12px;
  }

  :deep(.el-table__body tr:hover > td) {
    background: rgba(251, 146, 60, 0.06) !important;
  }
}

.wqa-daily-num {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #334155;
}

.wqa-daily-num--actual {
  color: #0369a1;
}

.wqa-daily-num--defect {
  color: #c2410c;
}

.wqa-rate-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.wqa-rate-pill--zero {
  color: #94a3b8;
  background: rgba(148, 163, 184, 0.12);
}

.wqa-rate-pill--low {
  color: #b45309;
  background: rgba(251, 191, 36, 0.16);
  border: 1px solid rgba(245, 158, 11, 0.22);
}

.wqa-rate-pill--mid {
  color: #c2410c;
  background: rgba(251, 146, 60, 0.16);
  border: 1px solid rgba(249, 115, 22, 0.24);
}

.wqa-rate-pill--high {
  color: #be123c;
  background: rgba(244, 63, 94, 0.12);
  border: 1px solid rgba(244, 63, 94, 0.22);
}

.wqa-panel--product {
  background:
    radial-gradient(ellipse 70% 55% at 100% 0%, rgba(14, 165, 233, 0.1) 0%, transparent 58%),
    linear-gradient(165deg, #ffffff 0%, #f0f9ff 52%, #e0f2fe 100%);
  border-color: rgba(14, 165, 233, 0.2);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 28px rgba(14, 165, 233, 0.08);
  position: relative;
  overflow: hidden;
}

.wqa-panel--product::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #38bdf8, #0ea5e9, #6366f1);
}

.wqa-product-head__desc,
.wqa-section-head__desc {
  margin-top: 2px;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
}

.ipa-panel__badges {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.ipa-panel__badge--soft {
  color: #64748b;
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.wqa-badge--defect {
  color: #c2410c !important;
  background: rgba(251, 146, 60, 0.14) !important;
  border: 1px solid rgba(249, 115, 22, 0.22);
}

.wqa-product-chart {
  margin-bottom: 12px;
  border-color: rgba(186, 230, 253, 0.85);
}

.wqa-product-table {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(186, 230, 253, 0.55);
}

.wqa-product-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #e0f2fe, #bae6fd) !important;
  color: #0369a1;
  padding: 8px 0;
}

.wqa-product-table :deep(.el-table__body td) {
  padding: 7px 0;
}

.wqa-product-table :deep(.el-table__body tr:hover > td) {
  background: rgba(14, 165, 233, 0.07) !important;
}

.wqa-product-cd {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #0369a1;
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.18);
}

.wqa-row-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 5px;
  border-radius: 7px;
  font-size: 10px;
  font-weight: 800;
  color: #64748b;
  background: rgba(148, 163, 184, 0.14);
}

.wqa-row-rank--gold {
  color: #92400e;
  background: linear-gradient(135deg, #fde68a, #fcd34d);
}

.wqa-row-rank--silver {
  color: #475569;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
}

.wqa-row-rank--bronze {
  color: #9a3412;
  background: linear-gradient(135deg, #fed7aa, #fdba74);
}

.wqa-top-defect {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
}

.wqa-top-defect__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: #475569;
}

.wqa-top-defect__qty {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  color: #c2410c;
  background: rgba(251, 146, 60, 0.12);
}

.wqa-top-defect--empty {
  color: #cbd5e1;
}

.ipa-panel__ico--product {
  color: #0ea5e9;
}

.ipa-panel__badge--product {
  color: #0369a1;
  background: rgba(14, 165, 233, 0.12);
  border: 1px solid rgba(14, 165, 233, 0.2);
}

.ipa-chart--product {
  border-color: rgba(186, 230, 253, 0.85);
}

.wqa-panel--operator {
  background:
    radial-gradient(ellipse 70% 55% at 100% 0%, rgba(99, 102, 241, 0.1) 0%, transparent 58%),
    linear-gradient(165deg, #ffffff 0%, #f5f3ff 52%, #ede9fe 100%);
  border-color: rgba(99, 102, 241, 0.2);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 28px rgba(99, 102, 241, 0.08);
  position: relative;
  overflow: hidden;
}

.wqa-panel--operator::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #a5b4fc, #6366f1, #8b5cf6);
}

.wqa-operator-chart {
  margin-bottom: 12px;
  border-color: rgba(199, 210, 254, 0.85);
}

.wqa-operator-table {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(199, 210, 254, 0.55);
}

.wqa-operator-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #e0e7ff, #c7d2fe) !important;
  color: #4338ca;
  padding: 8px 0;
}

.wqa-operator-table :deep(.el-table__body td) {
  padding: 7px 0;
}

.wqa-operator-table :deep(.el-table__body tr:hover > td) {
  background: rgba(99, 102, 241, 0.07) !important;
}

.ipa-panel__ico--operator {
  color: #6366f1;
}

.ipa-panel__badge--operator {
  color: #4338ca;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.ipa-chart--operator {
  border-color: rgba(199, 210, 254, 0.85);
}

.wqa-defect-session-pill {
  display: inline-flex;
  min-width: 28px;
  justify-content: center;
  padding: 1px 7px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #7c3aed;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.18);
}

.wqa-panel--product-defect {
  background:
    radial-gradient(ellipse 75% 60% at 0% 0%, rgba(139, 92, 246, 0.1) 0%, transparent 55%),
    radial-gradient(ellipse 55% 45% at 100% 100%, rgba(244, 63, 94, 0.06) 0%, transparent 50%),
    linear-gradient(165deg, #ffffff 0%, #faf5ff 48%, #f3e8ff 100%);
  border-color: rgba(139, 92, 246, 0.22);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 28px rgba(139, 92, 246, 0.08);
  position: relative;
  overflow: hidden;
}

.wqa-panel--product-defect::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #c4b5fd, #8b5cf6, #f472b6);
}

.ipa-panel__ico--matrix {
  color: #8b5cf6;
}

.wqa-badge--matrix {
  color: #7c3aed !important;
  background: rgba(139, 92, 246, 0.12) !important;
  border: 1px solid rgba(139, 92, 246, 0.22);
}

.wqa-product-defect-table {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(216, 180, 254, 0.55);
}

.wqa-product-defect-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #ede9fe, #ddd6fe) !important;
  color: #6d28d9;
  padding: 9px 0;
  font-size: 11px;
  font-weight: 700;
}

.wqa-product-defect-table :deep(.el-table__body td) {
  padding: 8px 0;
  font-size: 12px;
}

.wqa-product-defect-table :deep(.el-table__body tr:hover > td) {
  background: rgba(139, 92, 246, 0.06) !important;
}

.wqa-defect-name {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}

.wqa-defect-cd {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #9a3412;
  background: rgba(251, 146, 60, 0.12);
  border: 1px solid rgba(249, 115, 22, 0.2);
}

.wqa-qty-pill {
  display: inline-flex;
  min-width: 44px;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #be123c;
  background: rgba(244, 63, 94, 0.1);
  border: 1px solid rgba(244, 63, 94, 0.18);
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
  .wqa-defect-layout {
    grid-template-columns: 1fr;
  }
}
</style>
