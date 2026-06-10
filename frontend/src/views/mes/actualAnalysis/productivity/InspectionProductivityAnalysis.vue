<template>
  <div class="ipa">
    <div class="ipa__bg" aria-hidden="true">
      <div class="ipa__orb ipa__orb--1" />
      <div class="ipa__orb ipa__orb--2" />
      <div class="ipa__orb ipa__orb--3" />
    </div>

    <header class="ipa-hero ipa-fade-in">
      <div class="ipa-hero__main">
        <div class="ipa-hero__icon">
          <el-icon :size="24"><DocumentChecked /></el-icon>
          <span class="ipa-hero__icon-glow" />
        </div>
        <div class="ipa-hero__text">
          <div class="ipa-hero__eyebrow">MES · 実績分析</div>
          <h1 class="ipa-hero__title">検査工程 — 生産性分析</h1>
          <p class="ipa-hero__meta">inspection_management 実績 · 能率 · 不良率 · 稼働</p>
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
            start-placeholder="開始"
            end-placeholder="終了"
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
            >
              <div class="ipa-product-opt">
                <span class="ipa-product-opt__name">{{ p.product_name || p.product_cd }}</span>
                <span class="ipa-product-opt__cd">{{ p.product_cd }}</span>
              </div>
            </el-option>
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
              <span class="ipa-panel__badge">生産数 · 能率</span>
            </div>
            <div ref="dailyChartRef" class="ipa-chart ipa-chart--main" />
          </section>

          <div class="ipa-split">
            <section class="ipa-panel ipa-fade-in ipa-fade-in--d4">
              <div class="ipa-panel__head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico"><User /></el-icon>
                  <span class="ipa-panel__title">検査員別</span>
                </div>
              </div>
              <div ref="inspectorChartRef" class="ipa-chart ipa-chart--side" />
              <el-table :data="analysisData.by_inspector" size="small" class="ipa-table" max-height="240">
                <el-table-column prop="inspector_name" label="検査員" min-width="100" show-overflow-tooltip />
                <el-table-column label="件" width="48" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="72" align="right">
                  <template #default="{ row }">{{ fmtInt(row.sum_actual_qty) }}</template>
                </el-table-column>
                <el-table-column label="不良率" width="68" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtPct(row.defect_rate_percent) }}</span></template>
                </el-table-column>
                <el-table-column label="能率" width="56" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--good">{{ fmtEfficiency(row.efficiency_per_hour) }}</span></template>
                </el-table-column>
              </el-table>
            </section>

            <section class="ipa-panel ipa-fade-in ipa-fade-in--d5">
              <div class="ipa-panel__head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico"><Goods /></el-icon>
                  <span class="ipa-panel__title">製品別</span>
                </div>
                <span class="ipa-panel__badge">{{ analysisData.by_product.length }} 品目</span>
              </div>
              <el-table :data="analysisData.by_product" size="small" class="ipa-table" max-height="340">
                <el-table-column prop="product_cd" label="CD" width="88" />
                <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
                <el-table-column label="件" width="44" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="72" align="right">
                  <template #default="{ row }">{{ fmtInt(row.sum_actual_qty) }}</template>
                </el-table-column>
                <el-table-column label="不良率" width="68" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtPct(row.defect_rate_percent) }}</span></template>
                </el-table-column>
                <el-table-column label="能率" width="56" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--good">{{ fmtEfficiency(row.efficiency_per_hour) }}</span></template>
                </el-table-column>
              </el-table>
            </section>
          </div>

          <section v-if="productRankList.length" class="ipa-panel ipa-panel--rank ipa-fade-in ipa-fade-in--d5b">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><Trophy /></el-icon>
                <span class="ipa-panel__title">製品別 · 検査員能率ランキング</span>
              </div>
              <div class="ipa-rank-picker">
                <span class="ipa-rank-picker__label">製品</span>
                <el-select
                  v-model="rankViewProductCd"
                  filterable
                  size="small"
                  class="ipa-rank-picker__select"
                  placeholder="製品を選択"
                >
                  <el-option
                    v-for="p in productRankList"
                    :key="p.product_cd"
                    :label="productRankOptionLabel(p)"
                    :value="p.product_cd"
                  />
                </el-select>
              </div>
            </div>

            <div v-if="selectedProductRanking" class="ipa-rank-body">
              <div class="ipa-rank-product">
                <span class="ipa-rank-product__cd">{{ selectedProductRanking.product_cd }}</span>
                <span class="ipa-rank-product__name">{{ selectedProductRanking.product_name }}</span>
                <span class="ipa-rank-product__meta">
                  生産 {{ fmtInt(selectedProductRanking.sum_actual_qty) }} ·
                  検査員 {{ selectedProductRanking.ranked_inspector_count ?? 0 }} 名
                </span>
              </div>

              <div v-if="podiumInspectors.length" class="ipa-podium">
                <div
                  v-for="item in podiumInspectors"
                  :key="item.inspector_user_id ?? item.inspector_name"
                  class="ipa-podium__item"
                  :class="`ipa-podium__item--${item.rank}`"
                >
                  <div class="ipa-podium__medal">{{ rankMedal(item.rank) }}</div>
                  <div class="ipa-podium__name">{{ item.inspector_name }}</div>
                  <div class="ipa-podium__eff">{{ fmtEfficiency(item.efficiency_per_hour) }}</div>
                  <div class="ipa-podium__sub">個/時</div>
                </div>
              </div>

              <div ref="productRankChartRef" class="ipa-chart ipa-chart--rank" />

              <el-table
                :data="selectedProductRanking.inspectors"
                size="small"
                class="ipa-table ipa-table--rank"
                max-height="280"
                highlight-current-row
              >
                <el-table-column label="順位" width="64" align="center" fixed>
                  <template #default="{ row }">
                    <span class="ipa-rank-badge" :class="rankBadgeClass(row.rank)">{{ row.rank }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="inspector_name" label="検査員" min-width="120" show-overflow-tooltip />
                <el-table-column label="件" width="48" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="72" align="right">
                  <template #default="{ row }">{{ fmtInt(row.sum_actual_qty) }}</template>
                </el-table-column>
                <el-table-column label="能率" width="72" align="right" sortable :sort-method="sortByEfficiency">
                  <template #default="{ row }">
                    <span class="ipa-num ipa-num--good ipa-num--lg">{{ fmtEfficiency(row.efficiency_per_hour) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="不良率" width="72" align="right">
                  <template #default="{ row }">{{ fmtPct(row.defect_rate_percent) }}</template>
                </el-table-column>
                <el-table-column label="稼働" width="64" align="right">
                  <template #default="{ row }">{{ fmtDurationMin(row.sum_net_production_min) }}</template>
                </el-table-column>
              </el-table>

              <div v-if="!selectedProductRanking.inspectors.length" class="ipa-rank-empty">
                能率を算出できる検査員データがありません（正味稼働時間が必要です）
              </div>
            </div>

            <div class="ipa-rank-overview">
              <div class="ipa-rank-overview__head">全製品 · 能率 TOP1 一覧</div>
              <el-table :data="productRankTopOverview" size="small" class="ipa-table" max-height="220">
                <el-table-column prop="product_cd" label="CD" width="88" />
                <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
                <el-table-column label="TOP検査員" min-width="110" show-overflow-tooltip>
                  <template #default="{ row }">{{ row.top_inspector_name ?? '—' }}</template>
                </el-table-column>
                <el-table-column label="能率" width="72" align="right">
                  <template #default="{ row }">
                    <span class="ipa-num ipa-num--good">{{ fmtEfficiency(row.top_efficiency_per_hour) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="対象人数" width="72" align="center">
                  <template #default="{ row }">{{ row.ranked_inspector_count ?? 0 }}</template>
                </el-table-column>
                <el-table-column label="" width="72" align="center">
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="rankViewProductCd = row.product_cd">
                      詳細
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </section>

          <section v-if="defectRows.length" class="ipa-panel ipa-fade-in ipa-fade-in--d6">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><WarningFilled /></el-icon>
                <span class="ipa-panel__title">不良内訳（KT09）</span>
              </div>
            </div>
            <div class="ipa-defect-grid">
              <div v-for="(row, i) in defectRows.slice(0, 8)" :key="row.defect_cd" class="ipa-defect-chip" :style="{ animationDelay: `${i * 50}ms` }">
                <span class="ipa-defect-chip__name">{{ defectLabel(row.defect_cd) }}</span>
                <span class="ipa-defect-chip__qty">{{ fmtInt(row.qty) }}</span>
              </div>
            </div>
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
                <template #default="{ row }">{{ fmtInt(row.defect_qty) }}</template>
              </el-table-column>
              <el-table-column label="不良率" width="68" align="right">
                <template #default="{ row }">{{ fmtPct(row.defect_rate_percent) }}</template>
              </el-table-column>
              <el-table-column label="能率" width="56" align="right">
                <template #default="{ row }"><span class="ipa-num ipa-num--good">{{ fmtEfficiency(row.efficiency_per_hour) }}</span></template>
              </el-table-column>
              <el-table-column label="稼働" width="56" align="right">
                <template #default="{ row }">{{ row.net_production_min ?? '—' }}</template>
              </el-table-column>
              <el-table-column label="停止" width="52" align="right">
                <template #default="{ row }">{{ row.paused_min ?? '—' }}</template>
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
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  Calendar,
  CircleCheck,
  DataAnalysis,
  DocumentChecked,
  Goods,
  List,
  Refresh,
  Timer,
  TrendCharts,
  Trophy,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchInspectionProductivityAnalysis,
  type InspectionProductivityAnalysisData,
  type InspectionProductivityBucket,
  type InspectionProductivityInspectorRow,
  type InspectionProductivityProductInspectorRanking,
} from '@/api/inspectionManagement'
import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import { getProductList } from '@/api/master/productMaster'
import type { Product } from '@/types/master'
import { getJSTToday, parseDateAsJST } from '@/utils/dateFormat'
import { filterInspectionSelectableProducts } from '@/views/mes/shared/inspectionProductFilter'
import {
  loadMesDefectItemsForProcess,
  resolveMesDefectItemLabel,
} from '@/views/mes/actualDataCollection/shared/loadProcessDefectItems'

defineOptions({ name: 'MesInspectionProductivityAnalysis' })

const { t, te } = useI18n()

const loading = ref(false)
const contentVisible = ref(false)
const analysisData = ref<InspectionProductivityAnalysisData | null>(null)
const inspectorOptions = ref<UserListItem[]>([])
const filterInspectorId = ref<number | null>(null)
const filterProductCd = ref('')
const includeIncomplete = ref(false)
const productOptions = ref<Product[]>([])
const loadingProductOptions = ref(false)
const defectLabelMap = ref<Map<string, string>>(new Map())
const rankViewProductCd = ref('')
const dailyChartRef = ref<HTMLElement | null>(null)
const inspectorChartRef = ref<HTMLElement | null>(null)
const productRankChartRef = ref<HTMLElement | null>(null)
let dailyChart: ECharts | null = null
let inspectorChart: ECharts | null = null
let productRankChart: ECharts | null = null

function shiftJstDate(isoDay: string, deltaDays: number): string {
  const base = parseDateAsJST(isoDay)
  if (!base) return isoDay
  base.setDate(base.getDate() + deltaDays)
  return base.toISOString().slice(0, 10)
}

const dateRange = ref<[string, string]>([shiftJstDate(getJSTToday(), -29), getJSTToday()])

const emptySummary = (): InspectionProductivityBucket => ({
  session_count: 0,
  completed_session_count: 0,
  sum_actual_qty: 0,
  sum_defect_qty: 0,
  sum_net_production_sec: 0,
  sum_net_production_min: 0,
  sum_paused_sec: 0,
  sum_paused_min: 0,
  defect_rate_percent: null,
  efficiency_per_hour: null,
})

const summary = computed(() => analysisData.value?.summary ?? emptySummary())
const defectRows = computed(() => analysisData.value?.defect_by_item ?? [])

const productRankList = computed((): InspectionProductivityProductInspectorRanking[] => {
  const fromApi = analysisData.value?.by_product_inspector_ranking
  if (fromApi?.length) return fromApi
  return buildProductInspectorRankingFromSessions(analysisData.value?.sessions ?? [])
})

function buildProductInspectorRankingFromSessions(
  sessions: InspectionProductivityAnalysisData['sessions'],
): InspectionProductivityProductInspectorRanking[] {
  const productMap = new Map<
    string,
    {
      product_cd: string
      product_name: string
      sum_actual_qty: number
      session_count: number
      inspectors: Map<string, InspectionProductivityInspectorRow>
    }
  >()

  for (const s of sessions) {
    const productCd = (s.product_cd ?? '').trim() || 'unknown'
    const productName = (s.product_name ?? '').trim() || productCd
    if (!productMap.has(productCd)) {
      productMap.set(productCd, {
        product_cd: productCd,
        product_name: productName,
        sum_actual_qty: 0,
        session_count: 0,
        inspectors: new Map(),
      })
    }
    const prod = productMap.get(productCd)!
    prod.sum_actual_qty += Number(s.actual_production_quantity ?? 0)
    prod.session_count += 1

    const inspId = s.mes_inspector_user_id
    const inspKey = inspId != null ? String(inspId) : 'none'
    const inspName = (s.inspector_display_name ?? s.mes_inspector_name ?? '—').trim() || '—'
    if (!prod.inspectors.has(inspKey)) {
      prod.inspectors.set(inspKey, {
        inspector_user_id: inspId ?? null,
        inspector_name: inspName,
        session_count: 0,
        sum_actual_qty: 0,
        sum_defect_qty: 0,
        sum_net_production_sec: 0,
        efficiency_per_hour: null,
      })
    }
    const inv = prod.inspectors.get(inspKey)!
    inv.session_count = (inv.session_count ?? 0) + 1
    inv.sum_actual_qty = (inv.sum_actual_qty ?? 0) + Number(s.actual_production_quantity ?? 0)
    inv.sum_defect_qty = (inv.sum_defect_qty ?? 0) + Number(s.defect_qty ?? 0)
    inv.sum_net_production_sec = (inv.sum_net_production_sec ?? 0) + Number(s.net_production_sec ?? 0)
  }

  const result: InspectionProductivityProductInspectorRanking[] = []
  for (const prod of productMap.values()) {
    const inspectors: InspectionProductivityInspectorRow[] = []
    for (const inv of prod.inspectors.values()) {
      const actual = inv.sum_actual_qty ?? 0
      const netSec = inv.sum_net_production_sec ?? 0
      const defect = inv.sum_defect_qty ?? 0
      inv.defect_rate_percent = actual > 0 ? Math.round((defect / actual) * 1000) / 10 : null
      inv.efficiency_per_hour = actual > 0 && netSec > 0 ? Math.round(actual / (netSec / 3600)) : null
      inv.sum_net_production_min = netSec > 0 ? Math.round(netSec / 60) : 0
      if (inv.efficiency_per_hour != null) inspectors.push(inv)
    }
    inspectors.sort((a, b) => (b.efficiency_per_hour ?? 0) - (a.efficiency_per_hour ?? 0))
    inspectors.forEach((row, i) => {
      row.rank = i + 1
    })
    result.push({
      product_cd: prod.product_cd,
      product_name: prod.product_name,
      sum_actual_qty: prod.sum_actual_qty,
      session_count: prod.session_count,
      inspector_count: prod.inspectors.size,
      ranked_inspector_count: inspectors.length,
      inspectors,
      top_inspector_name: inspectors[0]?.inspector_name ?? null,
      top_efficiency_per_hour: inspectors[0]?.efficiency_per_hour ?? null,
    })
  }
  return result.sort((a, b) => (b.sum_actual_qty ?? 0) - (a.sum_actual_qty ?? 0))
}

const selectedProductRanking = computed(() => {
  const list = productRankList.value
  if (!list.length) return null
  const cd = rankViewProductCd.value
  return list.find((p) => p.product_cd === cd) ?? list[0] ?? null
})

const podiumInspectors = computed(() => {
  const rows = selectedProductRanking.value?.inspectors ?? []
  const top3 = rows.filter((r) => (r.rank ?? 99) <= 3)
  const order = [2, 1, 3]
  return order
    .map((rank) => top3.find((r) => r.rank === rank))
    .filter((r): r is InspectionProductivityInspectorRow => r != null)
})

const productRankTopOverview = computed(() =>
  productRankList.value.filter((p) => p.top_efficiency_per_hour != null),
)

function productRankOptionLabel(p: InspectionProductivityProductInspectorRanking): string {
  const name = (p.product_name ?? '').trim()
  return name ? `${p.product_cd} · ${name}` : p.product_cd
}

function rankMedal(rank?: number): string {
  if (rank === 1) return '🥇'
  if (rank === 2) return '🥈'
  if (rank === 3) return '🥉'
  return String(rank ?? '—')
}

function rankBadgeClass(rank?: number): string {
  if (rank === 1) return 'ipa-rank-badge--gold'
  if (rank === 2) return 'ipa-rank-badge--silver'
  if (rank === 3) return 'ipa-rank-badge--bronze'
  return ''
}

function sortByEfficiency(a: InspectionProductivityInspectorRow, b: InspectionProductivityInspectorRow): number {
  return (b.efficiency_per_hour ?? -1) - (a.efficiency_per_hour ?? -1)
}

function syncRankProductSelection() {
  const list = productRankList.value
  if (!list.length) {
    rankViewProductCd.value = ''
    return
  }
  if (!list.some((p) => p.product_cd === rankViewProductCd.value)) {
    rankViewProductCd.value = list[0].product_cd
  }
}

const kpiCards = computed(() => {
  const s = summary.value
  return [
    {
      key: 'sessions',
      label: '確定セッション',
      value: fmtInt(s.completed_session_count),
      hint: `全 ${fmtInt(s.session_count)} 件`,
      icon: markRaw(CircleCheck),
      tone: 'indigo',
    },
    {
      key: 'actual',
      label: '生産数合計',
      value: fmtInt(s.sum_actual_qty),
      hint: '確定実績合計',
      icon: markRaw(Goods),
      tone: 'sky',
    },
    {
      key: 'defect',
      label: '不良数',
      value: fmtInt(s.sum_defect_qty),
      hint: `不良率 ${fmtPct(s.defect_rate_percent)}`,
      icon: markRaw(WarningFilled),
      tone: 'amber',
    },
    {
      key: 'efficiency',
      label: '総合能率',
      value: fmtEfficiency(s.efficiency_per_hour),
      hint: '個 / 時間',
      icon: markRaw(TrendCharts),
      tone: 'emerald',
    },
    {
      key: 'runtime',
      label: '正味稼働',
      value: fmtDurationMin(s.sum_net_production_min),
      hint: `停止 ${fmtDurationMin(s.sum_paused_min)}`,
      icon: markRaw(Timer),
      tone: 'violet',
    },
  ]
})

function fmtInt(value: number | null | undefined): string {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toLocaleString('ja-JP') : '0'
}

function fmtPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value.toFixed(1)}%`
}

function fmtEfficiency(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${Math.round(value)}`
}

function fmtDurationMin(min: number | null | undefined): string {
  const n = Number(min ?? 0)
  if (!Number.isFinite(n) || n <= 0) return '—'
  const h = Math.floor(n / 60)
  const m = n % 60
  if (h > 0) return `${h}h${m}m`
  return `${m}m`
}

function inspectorLabel(u: UserListItem): string {
  const name = (u.full_name ?? '').trim()
  const username = (u.username ?? '').trim()
  if (name && username) return `${name}（${username}）`
  return name || username || `#${u.id}`
}

function productOptionLabel(p: Product): string {
  const name = (p.product_name ?? '').trim()
  return name || p.product_cd
}

async function loadProductOptions() {
  loadingProductOptions.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    const list = res?.data?.list ?? res?.list ?? []
    productOptions.value = filterInspectionSelectableProducts(list)
  } catch {
    productOptions.value = []
  } finally {
    loadingProductOptions.value = false
  }
}

function defectLabel(defectCd: string): string {
  const cd = (defectCd ?? '').trim()
  return defectLabelMap.value.get(cd) ?? resolveMesDefectItemLabel(cd, cd, t, te)
}

async function loadInspectors() {
  try {
    const res = (await getUsers({ page: 1, page_size: 500, status: 'active' })) as unknown as PaginatedUserResponse
    inspectorOptions.value = res.items ?? []
  } catch {
    inspectorOptions.value = []
  }
}

async function loadDefectLabels() {
  try {
    const items = await loadMesDefectItemsForProcess('KT09')
    const map = new Map<string, string>()
    for (const item of items) map.set(item.id, item.label)
    defectLabelMap.value = map
  } catch {
    defectLabelMap.value = new Map()
  }
}

async function loadAnalysis() {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) {
    ElMessage.warning('集計期間を指定してください')
    return
  }
  contentVisible.value = false
  loading.value = true
  try {
    const res = await fetchInspectionProductivityAnalysis({
      start_date: start,
      end_date: end,
      mes_inspector_user_id: filterInspectorId.value,
      product_cd: filterProductCd.value || null,
      include_incomplete: includeIncomplete.value,
    })
    if (!res.success || !res.data) throw new Error(res.message || '分析データの取得に失敗しました')
    analysisData.value = res.data
    syncRankProductSelection()
    await nextTick()
    contentVisible.value = true
    await nextTick()
    renderCharts()
  } catch (err) {
    analysisData.value = null
    ElMessage.error(err instanceof Error ? err.message : '分析データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function disposeCharts() {
  dailyChart?.dispose()
  inspectorChart?.dispose()
  productRankChart?.dispose()
  dailyChart = null
  inspectorChart = null
  productRankChart = null
}

function chartTheme() {
  return {
    text: '#64748b',
    axis: '#cbd5e1',
    split: 'rgba(148, 163, 184, 0.15)',
  }
}

function renderCharts() {
  disposeCharts()
  const data = analysisData.value
  if (!data) return
  const theme = chartTheme()

  const dailyEl = dailyChartRef.value
  if (dailyEl && data.daily.length > 0) {
    dailyChart = echarts.init(dailyEl)
    dailyChart.setOption({
      animationDuration: 900,
      animationEasing: 'cubicOut',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        borderColor: 'rgba(255,255,255,0.08)',
        textStyle: { color: '#e2e8f0', fontSize: 12 },
      },
      legend: { data: ['生産数', '能率'], top: 0, textStyle: { color: theme.text, fontSize: 11 } },
      grid: { left: 44, right: 44, top: 36, bottom: 24 },
      xAxis: {
        type: 'category',
        data: data.daily.map((d) => d.day.slice(5)),
        axisLine: { lineStyle: { color: theme.axis } },
        axisLabel: { color: theme.text, fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: [
        {
          type: 'value',
          name: '生産数',
          nameTextStyle: { color: theme.text, fontSize: 10 },
          axisLabel: { color: theme.text, fontSize: 10 },
          splitLine: { lineStyle: { color: theme.split, type: 'dashed' } },
        },
        {
          type: 'value',
          name: '能率',
          nameTextStyle: { color: theme.text, fontSize: 10 },
          axisLabel: { color: theme.text, fontSize: 10 },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: '生産数',
          type: 'bar',
          barMaxWidth: 28,
          data: data.daily.map((d) => d.sum_actual_qty ?? 0),
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#38bdf8' },
              { offset: 1, color: '#6366f1' },
            ]),
            shadowColor: 'rgba(99, 102, 241, 0.35)',
            shadowBlur: 10,
            shadowOffsetY: 4,
          },
        },
        {
          name: '能率',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          lineStyle: { width: 3, color: '#10b981', shadowColor: 'rgba(16,185,129,0.4)', shadowBlur: 8 },
          itemStyle: { color: '#10b981', borderWidth: 2, borderColor: '#fff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(16, 185, 129, 0.28)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0.02)' },
            ]),
          },
          data: data.daily.map((d) => d.efficiency_per_hour ?? null),
        },
      ],
    })
  }

  const inspectorEl = inspectorChartRef.value
  const topInspectors = data.by_inspector.slice(0, 8)
  if (inspectorEl && topInspectors.length > 0) {
    inspectorChart = echarts.init(inspectorEl)
    const colors = ['#8b5cf6', '#6366f1', '#0ea5e9', '#10b981', '#14b8a6', '#f59e0b', '#f97316', '#ec4899']
    inspectorChart.setOption({
      animationDuration: 800,
      animationEasing: 'elasticOut',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        borderColor: 'rgba(255,255,255,0.08)',
        textStyle: { color: '#e2e8f0', fontSize: 12 },
      },
      grid: { left: 96, right: 36, top: 8, bottom: 16 },
      xAxis: {
        type: 'value',
        axisLabel: { color: theme.text, fontSize: 10 },
        splitLine: { lineStyle: { color: theme.split, type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: topInspectors.map((r) => r.inspector_name ?? '—'),
        inverse: true,
        axisLabel: { color: '#334155', fontSize: 11, width: 80, overflow: 'truncate' },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: topInspectors.map((r, i) => ({
            value: r.efficiency_per_hour ?? 0,
            itemStyle: {
              borderRadius: [0, 6, 6, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: colors[i % colors.length] },
                { offset: 1, color: `${colors[i % colors.length]}99` },
              ]),
              shadowColor: 'rgba(99, 102, 241, 0.25)',
              shadowBlur: 8,
              shadowOffsetX: 2,
            },
          })),
          label: { show: true, position: 'right', color: '#475569', fontSize: 11, fontWeight: 600 },
        },
      ],
    })
  }

  renderProductRankChart(theme)
}

function renderProductRankChart(theme = chartTheme()) {
  productRankChart?.dispose()
  productRankChart = null
  const ranking = selectedProductRanking.value
  const el = productRankChartRef.value
  const rows = ranking?.inspectors ?? []
  if (!el || rows.length === 0) return

  productRankChart = echarts.init(el)
  const palette = ['#f59e0b', '#94a3b8', '#b45309', '#6366f1', '#0ea5e9', '#10b981', '#8b5cf6', '#ec4899']
  productRankChart.setOption({
    animationDuration: 700,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const p = list[0] as { dataIndex?: number }
        const row = rows[p.dataIndex ?? 0]
        if (!row) return ''
        return [
          `<b>${row.inspector_name ?? '—'}</b>`,
          `順位: ${row.rank ?? '—'}`,
          `能率: ${row.efficiency_per_hour ?? '—'} 個/時`,
          `生産: ${row.sum_actual_qty ?? 0}`,
          `不良率: ${row.defect_rate_percent != null ? `${row.defect_rate_percent}%` : '—'}`,
        ].join('<br/>')
      },
    },
    grid: { left: 100, right: 40, top: 12, bottom: 20 },
    xAxis: {
      type: 'value',
      name: '能率（個/時）',
      nameTextStyle: { color: theme.text, fontSize: 10 },
      axisLabel: { color: theme.text, fontSize: 10 },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => `#${r.rank} ${r.inspector_name ?? '—'}`),
      inverse: true,
      axisLabel: { color: '#334155', fontSize: 11, width: 92, overflow: 'truncate' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r, i) => ({
          value: r.efficiency_per_hour ?? 0,
          itemStyle: {
            borderRadius: [0, 8, 8, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: i === 0 ? '#f59e0b' : palette[i % palette.length] },
              { offset: 1, color: i === 0 ? '#fbbf24' : `${palette[i % palette.length]}aa` },
            ]),
            shadowColor: i === 0 ? 'rgba(245, 158, 11, 0.35)' : 'rgba(99, 102, 241, 0.2)',
            shadowBlur: 8,
            shadowOffsetX: 2,
          },
        })),
        label: {
          show: true,
          position: 'right',
          color: '#475569',
          fontSize: 11,
          fontWeight: 700,
          formatter: '{c}',
        },
      },
    ],
  })
}

function handleResize() {
  dailyChart?.resize()
  inspectorChart?.resize()
  productRankChart?.resize()
}

watch(rankViewProductCd, async () => {
  await nextTick()
  renderProductRankChart()
})

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  await Promise.all([loadInspectors(), loadDefectLabels(), loadProductOptions()])
  await loadAnalysis()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})
</script>

<style scoped>
.ipa {
  position: relative;
  min-height: 100%;
  padding: 10px 12px 16px;
  overflow: hidden;
}

.ipa__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99, 102, 241, 0.12), transparent 55%),
    radial-gradient(ellipse 60% 40% at 100% 20%, rgba(16, 185, 129, 0.08), transparent 50%),
    linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.ipa__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.45;
  animation: ipa-float 12s ease-in-out infinite;
}

.ipa__orb--1 {
  width: 280px;
  height: 280px;
  top: -80px;
  left: -60px;
  background: rgba(99, 102, 241, 0.35);
}

.ipa__orb--2 {
  width: 220px;
  height: 220px;
  top: 40%;
  right: -40px;
  background: rgba(16, 185, 129, 0.28);
  animation-delay: -4s;
}

.ipa__orb--3 {
  width: 180px;
  height: 180px;
  bottom: 10%;
  left: 35%;
  background: rgba(14, 165, 233, 0.22);
  animation-delay: -8s;
}

@keyframes ipa-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(12px, -16px) scale(1.05); }
}

.ipa-hero,
.ipa-toolbar,
.ipa-body {
  position: relative;
  z-index: 1;
}

.ipa-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  padding: 12px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(255, 255, 255, 0.72) 100%);
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 8px 32px rgba(15, 23, 42, 0.08),
    0 2px 8px rgba(99, 102, 241, 0.06);
  backdrop-filter: blur(12px);
}

.ipa-hero__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.ipa-hero__icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(145deg, #10b981 0%, #059669 50%, #047857 100%);
  box-shadow:
    0 4px 14px rgba(16, 185, 129, 0.45),
    0 1px 0 rgba(255, 255, 255, 0.35) inset;
  flex-shrink: 0;
}

.ipa-hero__icon-glow {
  position: absolute;
  inset: -4px;
  border-radius: 18px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.35), transparent 70%);
  z-index: -1;
  animation: ipa-pulse 3s ease-in-out infinite;
}

@keyframes ipa-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.08); }
}

.ipa-hero__eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6366f1;
}

.ipa-hero__title {
  margin: 2px 0 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.25;
}

.ipa-hero__meta {
  margin: 2px 0 0;
  font-size: 11px;
  color: #64748b;
}

.ipa-hero__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.ipa-hero__range {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.ipa-panel {
  border-radius: 14px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.88) 100%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 4px 24px rgba(15, 23, 42, 0.06),
    0 1px 3px rgba(15, 23, 42, 0.04);
  backdrop-filter: blur(10px);
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.ipa-panel:hover {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 12px 40px rgba(15, 23, 42, 0.09),
    0 4px 12px rgba(99, 102, 241, 0.06);
}

.ipa-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  margin-bottom: 10px;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98) 0%, rgba(241, 245, 249, 0.92) 100%);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 6px 20px rgba(15, 23, 42, 0.07),
    0 2px 6px rgba(99, 102, 241, 0.05);
}

.ipa-toolbar__fields {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  flex: 1;
  min-width: 0;
}

.ipa-field {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  min-height: 32px;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 2px 6px rgba(15, 23, 42, 0.06),
    0 1px 2px rgba(15, 23, 42, 0.04);
  transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
}

.ipa-field:hover {
  transform: translateY(-1px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 4px 12px rgba(15, 23, 42, 0.09);
}

.ipa-field:focus-within {
  border-color: rgba(99, 102, 241, 0.45);
  box-shadow:
    0 0 0 3px rgba(99, 102, 241, 0.12),
    0 2px 8px rgba(99, 102, 241, 0.15);
}

.ipa-field__pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding: 0 11px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
  border-right: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: inset -1px 0 0 rgba(0, 0, 0, 0.04);
}

.ipa-field__pill .el-icon {
  font-size: 13px;
}

.ipa-field--period .ipa-field__pill {
  color: #3730a3;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
}

.ipa-field--inspector .ipa-field__pill {
  color: #6b21a8;
  background: linear-gradient(180deg, #faf5ff 0%, #f3e8ff 100%);
}

.ipa-field--product .ipa-field__pill {
  color: #047857;
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
}

.ipa-field--check .ipa-field__pill {
  color: #92400e;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
}

.ipa-field--check {
  cursor: default;
}

.ipa-field--check .ipa-field__pill--check {
  padding: 0 9px;
  font-size: 10px;
}

.ipa-field__control {
  flex: 1;
  min-width: 0;
}

.ipa-field__date {
  width: 228px !important;
}

.ipa-field__inspector-select {
  width: 168px;
}

.ipa-field--product {
  flex: 1;
  min-width: 200px;
  max-width: 300px;
}

.ipa-field__product-select {
  width: 100%;
  min-width: 140px;
}

/* 入力枠をフラット化してラベルと一体化 */
.ipa-field :deep(.el-input__wrapper),
.ipa-field :deep(.el-select__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  min-height: 30px !important;
  padding-left: 8px !important;
  padding-right: 8px !important;
}

.ipa-field :deep(.el-input__wrapper:hover),
.ipa-field :deep(.el-select__wrapper:hover),
.ipa-field :deep(.el-input__wrapper.is-focus),
.ipa-field :deep(.el-select__wrapper.is-focused) {
  box-shadow: none !important;
}

.ipa-field :deep(.el-range-editor.el-input__wrapper) {
  padding: 0 8px !important;
}

.ipa-field :deep(.el-range-input) {
  font-size: 12px;
  color: #334155;
}

.ipa-field :deep(.el-select .el-input__inner),
.ipa-field :deep(.el-input__inner) {
  font-size: 12px;
  color: #334155;
}

.ipa-field--check {
  padding-right: 10px;
  gap: 0;
}

.ipa-field--check :deep(.el-checkbox) {
  height: 30px;
  padding: 0 4px 0 8px;
  display: inline-flex;
  align-items: center;
}

.ipa-field--check :deep(.el-checkbox__label) {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding-left: 6px;
}

.ipa-check {
  display: flex;
  align-items: stretch;
}

.ipa-product-opt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.ipa-product-opt__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: #334155;
}

.ipa-product-opt__cd {
  flex-shrink: 0;
  font-family: ui-monospace, monospace;
  font-size: 10px;
  color: #94a3b8;
}

.ipa-btn--primary {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
  font-weight: 600;
  padding: 0 18px;
  height: 32px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.ipa-btn--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
}

.ipa-btn--ghost {
  background: rgba(255, 255, 255, 0.7) !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
  color: #475569 !important;
}

.ipa-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ipa-kpi {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.ipa-kpi__card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 12px 11px 10px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid transparent;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 3px 0 rgba(15, 23, 42, 0.04),
    0 6px 16px rgba(15, 23, 42, 0.08);
}

.ipa-kpi__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 12px 12px 0 0;
}

.ipa-kpi__card--indigo {
  background: linear-gradient(160deg, #ffffff 0%, #f5f7ff 45%, #eef2ff 100%);
  border-color: rgba(99, 102, 241, 0.2);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 3px 0 rgba(99, 102, 241, 0.1),
    0 8px 20px rgba(99, 102, 241, 0.12);
}

.ipa-kpi__card--indigo .ipa-kpi__accent {
  background: linear-gradient(90deg, #6366f1, #818cf8);
}

.ipa-kpi__card--indigo .ipa-kpi__label { color: #6366f1; }
.ipa-kpi__card--indigo .ipa-kpi__value { color: #4338ca; }
.ipa-kpi__card--indigo .ipa-kpi__hint { color: #818cf8; }

.ipa-kpi__card--sky {
  background: linear-gradient(160deg, #ffffff 0%, #f0f9ff 45%, #e0f2fe 100%);
  border-color: rgba(14, 165, 233, 0.22);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 3px 0 rgba(14, 165, 233, 0.1),
    0 8px 20px rgba(14, 165, 233, 0.12);
}

.ipa-kpi__card--sky .ipa-kpi__accent {
  background: linear-gradient(90deg, #0ea5e9, #38bdf8);
}

.ipa-kpi__card--sky .ipa-kpi__label { color: #0284c7; }
.ipa-kpi__card--sky .ipa-kpi__value { color: #0369a1; }
.ipa-kpi__card--sky .ipa-kpi__hint { color: #38bdf8; }

.ipa-kpi__card--amber {
  background: linear-gradient(160deg, #ffffff 0%, #fff7ed 45%, #ffedd5 100%);
  border-color: rgba(249, 115, 22, 0.22);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 3px 0 rgba(249, 115, 22, 0.1),
    0 8px 20px rgba(249, 115, 22, 0.12);
}

.ipa-kpi__card--amber .ipa-kpi__accent {
  background: linear-gradient(90deg, #f97316, #fb923c);
}

.ipa-kpi__card--amber .ipa-kpi__label { color: #ea580c; }
.ipa-kpi__card--amber .ipa-kpi__value { color: #c2410c; }
.ipa-kpi__card--amber .ipa-kpi__hint { color: #fb923c; }

.ipa-kpi__card--emerald {
  background: linear-gradient(160deg, #ffffff 0%, #ecfdf5 40%, #d1fae5 100%);
  border-color: rgba(16, 185, 129, 0.28);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 4px 0 rgba(16, 185, 129, 0.12),
    0 10px 24px rgba(16, 185, 129, 0.16);
}

.ipa-kpi__card--emerald .ipa-kpi__accent {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.ipa-kpi__card--emerald .ipa-kpi__label { color: #059669; }
.ipa-kpi__card--emerald .ipa-kpi__value { color: #047857; font-size: 22px; }
.ipa-kpi__card--emerald .ipa-kpi__hint { color: #34d399; }

.ipa-kpi__card--violet {
  background: linear-gradient(160deg, #ffffff 0%, #f5f3ff 45%, #ede9fe 100%);
  border-color: rgba(139, 92, 246, 0.22);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 3px 0 rgba(139, 92, 246, 0.1),
    0 8px 20px rgba(139, 92, 246, 0.12);
}

.ipa-kpi__card--violet .ipa-kpi__accent {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.ipa-kpi__card--violet .ipa-kpi__label { color: #7c3aed; }
.ipa-kpi__card--violet .ipa-kpi__value { color: #6d28d9; }
.ipa-kpi__card--violet .ipa-kpi__hint { color: #a78bfa; }

.ipa-kpi__icon-wrap {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  color: #fff;
  flex-shrink: 0;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 4px 10px rgba(15, 23, 42, 0.18);
}

.ipa-kpi__icon-wrap--indigo {
  background: linear-gradient(145deg, #818cf8 0%, #6366f1 50%, #4f46e5 100%);
}

.ipa-kpi__icon-wrap--sky {
  background: linear-gradient(145deg, #38bdf8 0%, #0ea5e9 50%, #0284c7 100%);
}

.ipa-kpi__icon-wrap--amber {
  background: linear-gradient(145deg, #fb923c 0%, #f97316 50%, #ea580c 100%);
}

.ipa-kpi__icon-wrap--emerald {
  background: linear-gradient(145deg, #34d399 0%, #10b981 50%, #059669 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.4) inset,
    0 5px 14px rgba(16, 185, 129, 0.35);
}

.ipa-kpi__icon-wrap--violet {
  background: linear-gradient(145deg, #a78bfa 0%, #8b5cf6 50%, #7c3aed 100%);
}

.ipa-kpi__content {
  position: relative;
  z-index: 1;
  min-width: 0;
  flex: 1;
}

.ipa-kpi__label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.ipa-kpi__value {
  margin-top: 3px;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}

.ipa-kpi__hint {
  margin-top: 3px;
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ipa-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ipa-panel--chart,
.ipa-split > .ipa-panel,
.ipa-content > .ipa-panel {
  padding: 12px 14px 10px;
}

.ipa-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.ipa-panel__title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ipa-panel__ico {
  font-size: 15px;
  color: #6366f1;
}

.ipa-panel__title {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.01em;
}

.ipa-panel__badge {
  font-size: 10px;
  font-weight: 600;
  color: #6366f1;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.1);
}

.ipa-chart {
  width: 100%;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.6) 0%, rgba(255, 255, 255, 0.3) 100%);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.ipa-chart--main {
  height: 260px;
}

.ipa-chart--side {
  height: 180px;
  margin-bottom: 8px;
}

.ipa-chart--rank {
  height: 200px;
  margin-bottom: 10px;
}

.ipa-panel--rank {
  padding: 12px 14px 10px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.97) 0%, rgba(254, 243, 199, 0.15) 100%);
  border-color: rgba(245, 158, 11, 0.18);
}

.ipa-rank-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ipa-rank-picker__label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.ipa-rank-picker__select {
  width: 280px;
}

.ipa-rank-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ipa-rank-product {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(14, 165, 233, 0.06));
  border: 1px solid rgba(99, 102, 241, 0.12);
}

.ipa-rank-product__cd {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  font-weight: 700;
  color: #4338ca;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.8);
}

.ipa-rank-product__name {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}

.ipa-rank-product__meta {
  font-size: 11px;
  color: #64748b;
  margin-left: auto;
}

.ipa-podium {
  display: grid;
  grid-template-columns: 1fr 1.15fr 1fr;
  gap: 8px;
  align-items: end;
  padding: 4px 0 2px;
}

.ipa-podium__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 8px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
  transition: transform 0.25s ease;
  animation: ipa-kpi-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.ipa-podium__item:hover {
  transform: translateY(-4px);
}

.ipa-podium__item--1 {
  min-height: 108px;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 40%, #fff 100%);
  border-color: rgba(245, 158, 11, 0.35);
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.2);
  animation-delay: 0.08s;
}

.ipa-podium__item--2 {
  min-height: 92px;
  animation-delay: 0s;
}

.ipa-podium__item--3 {
  min-height: 84px;
  animation-delay: 0.16s;
}

.ipa-podium__medal {
  font-size: 22px;
  line-height: 1;
}

.ipa-podium__name {
  margin-top: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #334155;
  text-align: center;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ipa-podium__eff {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 800;
  color: #059669;
  letter-spacing: -0.03em;
}

.ipa-podium__sub {
  font-size: 10px;
  color: #94a3b8;
}

.ipa-rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: #475569;
  background: #f1f5f9;
}

.ipa-rank-badge--gold {
  color: #92400e;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.ipa-rank-badge--silver {
  color: #475569;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
}

.ipa-rank-badge--bronze {
  color: #9a3412;
  background: linear-gradient(135deg, #ffedd5, #fed7aa);
}

.ipa-num--lg {
  font-size: 13px;
}

.ipa-rank-empty {
  padding: 20px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  border-radius: 10px;
}

.ipa-rank-overview {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(226, 232, 240, 0.9);
}

.ipa-rank-overview__head {
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.ipa-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.ipa-defect-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ipa-defect-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  border: 1px solid rgba(251, 146, 60, 0.25);
  box-shadow: 0 2px 8px rgba(249, 115, 22, 0.1);
  animation: ipa-kpi-in 0.4s cubic-bezier(0.22, 1, 0.36, 1) both;
  transition: transform 0.2s ease;
}

.ipa-defect-chip:hover {
  transform: translateY(-2px);
}

.ipa-defect-chip__name {
  font-size: 11px;
  font-weight: 600;
  color: #9a3412;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ipa-defect-chip__qty {
  font-size: 13px;
  font-weight: 800;
  color: #c2410c;
}

.ipa-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f1f5f9, #e2e8f0) !important;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  padding: 6px 0;
}

.ipa-table :deep(.el-table__body td) {
  font-size: 11px;
  padding: 5px 0;
}

.ipa-table :deep(.el-table__row) {
  transition: background 0.15s ease;
}

.ipa-table :deep(.el-table__body tr:hover > td) {
  background: rgba(99, 102, 241, 0.06) !important;
}

.ipa-num {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.ipa-num--good {
  color: #059669;
}

.ipa-num--warn {
  color: #ea580c;
}

.ipa-status {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.ipa-status--ok {
  color: #047857;
  background: rgba(16, 185, 129, 0.15);
  box-shadow: 0 1px 4px rgba(16, 185, 129, 0.2);
}

.ipa-status--pending {
  color: #64748b;
  background: rgba(148, 163, 184, 0.2);
}

.ipa-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 20px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px dashed rgba(148, 163, 184, 0.4);
  color: #64748b;
  font-size: 13px;
}

.ipa-empty__icon {
  color: #94a3b8;
  opacity: 0.7;
}

/* Animations */
.ipa-fade-in {
  animation: ipa-fade-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.ipa-fade-in--d1 { animation-delay: 0.05s; }
.ipa-fade-in--d2 { animation-delay: 0.1s; }
.ipa-fade-in--d3 { animation-delay: 0.15s; }
.ipa-fade-in--d4 { animation-delay: 0.2s; }
.ipa-fade-in--d5 { animation-delay: 0.25s; }
.ipa-fade-in--d5b { animation-delay: 0.28s; }
.ipa-fade-in--d6 { animation-delay: 0.3s; }
.ipa-fade-in--d7 { animation-delay: 0.35s; }

@keyframes ipa-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes ipa-kpi-in {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.ipa-reveal-enter-active {
  transition: opacity 0.4s ease, transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.ipa-reveal-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.ipa-reveal-enter-from,
.ipa-reveal-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

@media (max-width: 1200px) {
  .ipa-kpi {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ipa-split {
    grid-template-columns: 1fr;
  }

  .ipa-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .ipa-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .ipa-btn--primary {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .ipa-kpi {
    grid-template-columns: 1fr;
  }

  .ipa-field__date {
    width: 100% !important;
  }

  .ipa-field__control {
    width: 100%;
  }
}
</style>
