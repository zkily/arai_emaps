<template>
  <div class="cmp-page">
    <div class="page-ambient" aria-hidden="true">
      <div class="orb orb-a" />
      <div class="orb orb-b" />
      <div class="orb orb-c" />
    </div>

    <div class="cmp-inner">
      <header class="toolbar toolbar-elevated animate-in" style="--delay: 0ms">
        <div class="toolbar-brand-zone">
          <div class="brand-icon">
            <el-icon :size="18"><DocumentChecked /></el-icon>
          </div>
          <h1 class="toolbar-title">不良・廃棄データ突合</h1>
        </div>

        <div class="toolbar-filters-zone">
          <div class="filter-inline filter-inline--period">
            <span class="filter-inline__label">対象月</span>
            <el-date-picker
              v-model="filters.month"
              type="month"
              placeholder="YYYY-MM"
              value-format="YYYY-MM"
              size="small"
              class="tf-control tf-control--month"
            />
          </div>

          <span class="filter-sep" aria-hidden="true" />

          <div class="filter-inline filter-inline--process">
            <span class="filter-inline__label">工程</span>
            <el-select
              v-model="filters.processCd"
              placeholder="全工程"
              clearable
              filterable
              size="small"
              teleported
              class="tf-control tf-control--process"
            >
              <el-option label="全工程" value="" />
              <el-option
                v-for="p in processOptions"
                :key="p.cd"
                :label="`${p.name} (${p.cd})`"
                :value="p.cd"
              />
            </el-select>
          </div>

          <span class="filter-sep" aria-hidden="true" />

          <div class="filter-inline filter-inline--product">
            <span class="filter-inline__label">製品</span>
            <el-select
              v-model="filters.productCd"
              placeholder="全製品"
              clearable
              filterable
              size="small"
              teleported
              class="tf-control tf-control--product"
              :loading="productOptionsLoading"
            >
              <el-option label="全製品" value="" />
              <el-option
                v-for="p in productOptions"
                :key="p.product_cd"
                :label="`${p.product_name} (${p.product_cd})`"
                :value="p.product_cd"
              />
            </el-select>
          </div>

          <span class="filter-sep" aria-hidden="true" />

          <div class="filter-inline filter-inline--switch">
            <el-switch v-model="filters.onlyDiff" size="small" active-text="差異のみ" />
          </div>
        </div>

        <div class="toolbar-actions-zone">
          <button type="button" class="action-btn action-btn--primary" :disabled="loading" @click="fetchAll">
            <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Search /></el-icon>
            <span>実行</span>
          </button>
          <button type="button" class="action-btn action-btn--ghost" @click="resetFilters">
            <el-icon><RefreshLeft /></el-icon>
            <span>リセット</span>
          </button>
        </div>
      </header>

      <div v-if="dateRangeLabel" class="period-ribbon animate-in" style="--delay: 60ms">
        <span class="period-chip period-chip--month">
          <el-icon :size="14"><Calendar /></el-icon>
          {{ dateRangeLabel }}
        </span>
        <span class="period-divider" />
        <span class="period-meta">生産管理 vs 製造</span>
      </div>

      <div class="notice-bar animate-in" style="--delay: 80ms">
        <el-icon :size="14"><InfoFilled /></el-icon>
        <span>
          数値は不良+廃棄の合算。メッキは日次合計を工程別サマリに反映。製造側データがない工程は製造=0。
        </span>
      </div>

      <div class="dash-section kpi-grid" :class="{ 'is-ready': contentReady }" v-loading="loading">
        <article
          v-for="(card, i) in kpiCards"
          :key="card.key"
          class="kpi-card kpi-card--elevated"
          :class="`kpi-card--${card.tone}`"
          :style="{ '--delay': `${80 + i * 70}ms`, '--i': i }"
        >
          <div class="kpi-card__glow" aria-hidden="true" />
          <header class="kpi-card__head">
            <div class="kpi-icon">
              <el-icon :size="18"><component :is="card.icon" /></el-icon>
            </div>
            <div class="kpi-card__titles">
              <h3 class="kpi-card__name">{{ card.label }}</h3>
              <p v-if="card.desc" class="kpi-card__desc">{{ card.desc }}</p>
            </div>
          </header>
          <div class="kpi-metric">
            <div class="kpi-metric__main">
              <span class="kpi-metric__label">不良+廃棄</span>
              <span class="kpi-metric__value">{{ card.value }}</span>
            </div>
            <div v-if="card.sub" class="kpi-metric__foot">
              <span class="kpi-sub">{{ card.sub }}</span>
            </div>
          </div>
        </article>
      </div>

      <section
        v-if="kpi && contentReady"
        class="vs-panel vs-panel--elevated animate-in"
        style="--delay: 280ms"
      >
        <div class="vs-side vs-side--theoretical">
          <div class="vs-side-head">
            <span class="vs-badge vs-badge--theoretical">生産管理</span>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric vs-metric--theoretical">
              <span class="vs-metric-label">不良+廃棄</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.summary_total) }}</span>
            </div>
          </div>
        </div>
        <div class="vs-center" aria-hidden="true">
          <span class="vs-pulse" />
          <span class="vs-center-text">VS</span>
        </div>
        <div class="vs-side vs-side--stocktake">
          <div class="vs-side-head">
            <span class="vs-badge vs-badge--stocktake">製造</span>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric vs-metric--stocktake">
              <span class="vs-metric-label">不良+廃棄</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.source_total) }}</span>
            </div>
            <div class="vs-metric vs-metric--match">
              <span class="vs-metric-label">一致率</span>
              <span class="vs-metric-value">{{ kpi.match_rate.toFixed(1) }}<small>%</small></span>
            </div>
          </div>
        </div>
        <div class="vs-diff-bar">
          <div class="vs-diff-label">
            <span>差異（製造 − 生産管理）</span>
            <strong :class="diffClass(kpi.total_diff)">{{ fmtSigned(kpi.total_diff) }}</strong>
          </div>
          <span class="vs-diff-hint">不一致 {{ fmtNum(kpi.mismatch_count) }} 件</span>
        </div>
      </section>

      <section class="panel panel--main animate-in" style="--delay: 360ms">
        <div class="panel-head panel-head--tabs">
          <div class="tab-switcher">
            <button
              type="button"
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'summary' }"
              @click="switchTab('summary')"
            >
              <el-icon :size="15"><Histogram /></el-icon>
              工程別サマリ
            </button>
            <button
              type="button"
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'detail' }"
              @click="switchTab('detail')"
            >
              <el-icon :size="15"><List /></el-icon>
              品番×日×工程明細
              <span v-if="detailTotal" class="tab-badge">{{ detailTotal }}</span>
            </button>
          </div>
          <span class="panel-hint">{{ activeTab === 'summary' ? `${summaryRows.length} 工程` : `${detailTotal} 行` }}</span>
        </div>

        <div v-show="activeTab === 'summary'" class="tab-body">
          <div class="table-wrap">
            <el-table
              :data="summaryRows"
              stripe
              border
              size="small"
              class="data-table data-table--summary"
              empty-text="データがありません — 期間を選んで「実行」を押してください"
            >
              <el-table-column prop="process_name" label="工程" min-width="100" fixed />
              <el-table-column label="生産管理" width="120" align="right">
                <template #default="{ row }">{{ fmtNum(row.summary_total) }}</template>
              </el-table-column>
              <el-table-column label="製造" width="100" align="right">
                <template #default="{ row }">{{ fmtNum(row.source_total) }}</template>
              </el-table-column>
              <el-table-column label="差異" width="90" align="right">
                <template #default="{ row }">
                  <span class="diff-pill" :class="diffClass(row.total_diff)">{{ fmtSigned(row.total_diff) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="件数" width="70" align="right">
                <template #default="{ row }">{{ fmtNum(row.item_count) }}</template>
              </el-table-column>
              <el-table-column label="一致率" width="80" align="right">
                <template #default="{ row }">{{ row.match_rate.toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column label="備考" min-width="140" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="na-cell">{{ row.source_note || '' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <div v-show="activeTab === 'detail'" class="tab-body" v-loading="detailLoading">
          <div class="table-wrap">
            <el-table
              :data="detailRows"
              stripe
              border
              size="small"
              class="data-table data-table--detail"
              :row-class-name="detailRowClass"
              empty-text="データがありません"
            >
              <el-table-column prop="product_cd" label="品番" width="100" fixed />
              <el-table-column prop="product_name" label="品名" min-width="120" show-overflow-tooltip />
              <el-table-column prop="production_day" label="日付" width="108" />
              <el-table-column prop="process_name" label="工程" width="88">
                <template #default="{ row }">
                  <span class="process-tag">{{ row.process_name }}</span>
                </template>
              </el-table-column>
              <el-table-column label="生産管理" width="110" align="right">
                <template #default="{ row }">{{ fmtNum(row.summary_total) }}</template>
              </el-table-column>
              <el-table-column label="製造" width="96" align="right">
                <template #default="{ row }">
                  <el-tooltip v-if="row.status === 'not_comparable'" :content="row.source_note || '該当なし'" placement="top">
                    <span class="na-cell">該当なし</span>
                  </el-tooltip>
                  <span v-else>{{ fmtSourceQty(row.source_total) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="差異" width="84" align="right">
                <template #default="{ row }">
                  <span v-if="row.total_diff != null" class="diff-pill" :class="diffClass(row.total_diff)">
                    {{ fmtSigned(row.total_diff) }}
                  </span>
                  <span v-else class="na-cell">—</span>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状態" width="108" align="center">
                <template #default="{ row }">
                  <span class="status-pill" :class="`status-pill--${row.status}`">
                    {{ statusLabel(row.status) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div class="pager-wrap">
            <el-pagination
              v-model:current-page="detailPage"
              v-model:page-size="detailLimit"
              :total="detailTotal"
              :page-sizes="[50, 100, 200, 500]"
              layout="total, sizes, prev, pager, next"
              size="small"
              background
              @current-change="fetchDetail"
              @size-change="onDetailSizeChange"
            />
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import {
  Calendar,
  DocumentChecked,
  Histogram,
  InfoFilled,
  List,
  Loading,
  PieChart,
  RefreshLeft,
  Search,
  Warning,
  WarningFilled,
} from '@element-plus/icons-vue'
import { getProducts, type Product } from '@/api/stocktake/common'
import {
  defectScrapComparisonApi,
  type DefectScrapComparisonDetailRow,
  type DefectScrapComparisonKpi,
  type DefectScrapComparisonStatus,
  type DefectScrapComparisonSummaryRow,
} from '@/api/erp/defectScrapComparison'

const PROCESS_OPTIONS = [
  { cd: 'KT01', name: '切断' },
  { cd: 'KT02', name: '面取' },
  { cd: 'KT04', name: '成型' },
  { cd: 'KT05', name: 'メッキ' },
  { cd: 'KT07', name: '溶接' },
  { cd: 'KT09', name: '検査' },
]

const defaultMonth = dayjs().format('YYYY-MM')

const loading = ref(false)
const detailLoading = ref(false)
const contentReady = ref(false)
const activeTab = ref<'summary' | 'detail'>('summary')
const processOptions = PROCESS_OPTIONS
const productOptions = ref<Product[]>([])
const productOptionsLoading = ref(false)

const filters = ref({
  month: defaultMonth,
  processCd: '',
  productCd: '',
  onlyDiff: false,
})

const kpi = ref<DefectScrapComparisonKpi | null>(null)
const summaryRows = ref<DefectScrapComparisonSummaryRow[]>([])
const detailRows = ref<DefectScrapComparisonDetailRow[]>([])
const detailPage = ref(1)
const detailLimit = ref(50)
const detailTotal = ref(0)

const periodBounds = computed(() => {
  const m = filters.value.month
  if (!m) return { start: '', end: '' }
  const start = dayjs(`${m}-01`).startOf('month').format('YYYY-MM-DD')
  const end = dayjs(`${m}-01`).endOf('month').format('YYYY-MM-DD')
  return { start, end }
})

const dateRangeLabel = computed(() => {
  const { start, end } = periodBounds.value
  if (!start || !end) return ''
  return `${filters.value.month}（${start} ～ ${end}）`
})

const fmtNum = (v?: number | null) => (v == null ? '0' : Number(v).toLocaleString())
const fmtSigned = (v: number) => {
  const n = Number(v)
  if (n > 0) return `+${n.toLocaleString()}`
  return n.toLocaleString()
}
const fmtSourceQty = (v: number | null | undefined) => (v == null ? '—' : fmtNum(v))

const diffClass = (v: number) => {
  if (v > 0) return 'num-pos'
  if (v < 0) return 'num-neg'
  return 'num-zero'
}

const STATUS_LABEL: Record<DefectScrapComparisonStatus, string> = {
  match: '一致',
  mismatch: '不一致',
  only_summary: '生産管理のみ',
  only_source: '製造のみ',
  not_comparable: '突合不可',
  plating_daily_only: '日次のみ',
}

const statusLabel = (s: DefectScrapComparisonStatus) => STATUS_LABEL[s] ?? s

const detailRowClass = ({ row }: { row: DefectScrapComparisonDetailRow }) => {
  if (row.status === 'mismatch') return 'row-mismatch'
  if (row.status === 'only_summary' || row.status === 'only_source') return 'row-partial'
  if (row.status === 'not_comparable') return 'row-muted'
  return ''
}

const kpiCards = computed(() => {
  const k = kpi.value
  return [
    {
      key: 'summary',
      tone: 'theoretical',
      icon: WarningFilled,
      label: '生産管理',
      desc: '不良+廃棄',
      value: fmtNum(k?.summary_total),
      sub: `品番×日×工程 ${fmtNum(k?.item_count)} 件`,
    },
    {
      key: 'source',
      tone: 'stocktake',
      icon: Warning,
      label: '製造',
      desc: '不良+廃棄',
      value: fmtNum(k?.source_total),
    },
    {
      key: 'diff',
      tone: 'diff',
      icon: Warning,
      label: '差異',
      desc: '製造 − 生産管理',
      value: fmtSigned(k?.total_diff ?? 0),
      sub: `生産管理のみ ${fmtNum(k?.only_summary_count)} / 製造のみ ${fmtNum(k?.only_source_count)}`,
    },
    {
      key: 'match',
      tone: 'match',
      icon: PieChart,
      label: '一致率',
      desc: '突合可能件数ベース',
      value: k ? `${k.match_rate.toFixed(1)}%` : '0%',
      sub: `不一致 ${fmtNum(k?.mismatch_count)} / 突合不可 ${fmtNum(k?.not_comparable_count)}`,
    },
  ]
})

function buildParams(extra: { view: 'summary' | 'detail'; page?: number; limit?: number }) {
  const { start, end } = periodBounds.value
  return {
    startDate: start,
    endDate: end,
    processCd: filters.value.processCd || undefined,
    productCd: filters.value.productCd?.trim() || undefined,
    onlyDiff: filters.value.onlyDiff,
    view: extra.view,
    page: extra.page,
    limit: extra.limit,
    sort_by: 'total_diff',
    sort_order: 'desc' as const,
  }
}

async function fetchSummary() {
  const data = await defectScrapComparisonApi.getComparison(buildParams({ view: 'summary' }))
  summaryRows.value = (data.list as DefectScrapComparisonSummaryRow[]) ?? []
  kpi.value = data.kpi
}

async function fetchDetail() {
  const { start, end } = periodBounds.value
  if (!start || !end) return
  detailLoading.value = true
  try {
    const data = await defectScrapComparisonApi.getComparison(
      buildParams({ view: 'detail', page: detailPage.value, limit: detailLimit.value }),
    )
    detailRows.value = (data.list as DefectScrapComparisonDetailRow[]) ?? []
    detailTotal.value = data.total ?? 0
    if (data.kpi) kpi.value = data.kpi
  } finally {
    detailLoading.value = false
  }
}

async function fetchAll() {
  const { start, end } = periodBounds.value
  if (!start || !end) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  loading.value = true
  contentReady.value = false
  try {
    detailPage.value = 1
    await Promise.all([fetchSummary(), fetchDetail()])
    contentReady.value = true
  } catch {
    ElMessage.error('突合データの取得に失敗しました')
    summaryRows.value = []
    detailRows.value = []
    kpi.value = null
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = {
    month: defaultMonth,
    processCd: '',
    productCd: '',
    onlyDiff: false,
  }
  summaryRows.value = []
  detailRows.value = []
  kpi.value = null
  detailTotal.value = 0
  contentReady.value = false
}

function switchTab(name: 'summary' | 'detail') {
  activeTab.value = name
}

function onDetailSizeChange() {
  detailPage.value = 1
  fetchDetail()
}

async function loadProductOptions() {
  productOptionsLoading.value = true
  try {
    productOptions.value = await getProducts()
  } catch {
    productOptions.value = []
  } finally {
    productOptionsLoading.value = false
  }
}

loadProductOptions()
</script>

<style scoped lang="scss">
.cmp-page {
  position: relative;
  min-height: 100%;
  padding: 12px 14px 20px;
  overflow: hidden;
}

.page-ambient {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.35;
}

.orb-a {
  width: 280px;
  height: 280px;
  top: -80px;
  left: -60px;
  background: rgba(99, 102, 241, 0.25);
}

.orb-b {
  width: 220px;
  height: 220px;
  top: 40%;
  right: -40px;
  background: rgba(249, 115, 22, 0.18);
}

.orb-c {
  width: 180px;
  height: 180px;
  bottom: -40px;
  left: 30%;
  background: rgba(16, 185, 129, 0.15);
}

.cmp-inner {
  position: relative;
  z-index: 1;
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.animate-in {
  animation: fadeSlideIn 0.45s ease both;
  animation-delay: var(--delay, 0ms);
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 0;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 12px;
  overflow: hidden;
}

.toolbar-brand-zone {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  min-width: 200px;
}

.brand-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}

.toolbar-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 800;
  color: #0f172a;
}

.toolbar-filters-zone {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  padding: 8px 12px;
  border-left: 1px solid rgba(148, 163, 184, 0.15);
  border-right: 1px solid rgba(148, 163, 184, 0.15);
  min-width: 0;
}

.filter-inline {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-inline__label {
  font-size: 0.68rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}

.filter-sep {
  width: 1px;
  height: 20px;
  background: rgba(148, 163, 184, 0.25);
}

.tf-control--month {
  width: 140px;
}

.tf-control--process {
  width: 150px;
}

.tf-control--product {
  width: 180px;
}

.toolbar-actions-zone {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: all 0.15s ease;
}

.action-btn--primary {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.35);
}

.action-btn--primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn--ghost {
  background: rgba(248, 250, 252, 0.9);
  color: #475569;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.period-ribbon {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.period-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.72rem;
  font-weight: 700;
  color: #334155;
}

.period-divider {
  width: 1px;
  height: 14px;
  background: rgba(148, 163, 184, 0.3);
}

.period-meta {
  font-size: 0.68rem;
  color: #64748b;
}

.notice-bar {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(254, 243, 199, 0.6);
  border: 1px solid rgba(251, 191, 36, 0.35);
  border-radius: 8px;
  font-size: 0.68rem;
  color: #92400e;
  line-height: 1.4;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.kpi-card {
  position: relative;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.2);
  overflow: hidden;
}

.kpi-card__head {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.kpi-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-card--theoretical .kpi-icon {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}

.kpi-card--stocktake .kpi-icon {
  background: rgba(249, 115, 22, 0.12);
  color: #f97316;
}

.kpi-card--diff .kpi-icon {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.kpi-card--match .kpi-icon {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.kpi-card__name {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 800;
  color: #1e293b;
}

.kpi-card__desc {
  margin: 2px 0 0;
  font-size: 0.62rem;
  color: #94a3b8;
}

.kpi-metric__dual {
  display: flex;
  gap: 14px;
}

.kpi-metric__label {
  display: block;
  font-size: 0.62rem;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 2px;
}

.kpi-metric__value {
  font-size: 1.25rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
}

.kpi-metric__dual .kpi-metric__value {
  font-size: 1.1rem;
}

.kpi-sub {
  font-size: 0.62rem;
  color: #64748b;
}

.vs-panel {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.vs-side-head {
  margin-bottom: 8px;
}

.vs-badge {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 6px;
}

.vs-badge--theoretical {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.vs-badge--stocktake {
  background: rgba(249, 115, 22, 0.12);
  color: #ea580c;
}

.vs-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.vs-center-text {
  font-size: 0.75rem;
  font-weight: 900;
  color: #94a3b8;
}

.vs-metric-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.vs-metric-label {
  display: block;
  font-size: 0.62rem;
  color: #94a3b8;
}

.vs-metric-value {
  font-size: 1rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.vs-diff-bar {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 10px;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  font-size: 0.72rem;
}

.panel {
  background: rgba(255, 255, 255, 0.88);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.panel-head--tabs {
  justify-content: space-between;
}

.panel-accent {
  width: 4px;
  height: 16px;
  border-radius: 2px;
}

.panel-accent--blue {
  background: #3b82f6;
}

.panel-accent--amber {
  background: #f59e0b;
}

.panel-title {
  font-size: 0.78rem;
  font-weight: 800;
  color: #1e293b;
}

.panel-hint {
  font-size: 0.65rem;
  color: #94a3b8;
  margin-left: auto;
}

.tab-switcher {
  display: flex;
  gap: 4px;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
}

.tab-btn--active {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.tab-badge {
  background: #3b82f6;
  color: #fff;
  font-size: 0.6rem;
  padding: 1px 5px;
  border-radius: 8px;
}

.tab-body {
  padding: 10px 12px 12px;
}

.table-wrap {
  overflow: auto;
}

.pager-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.process-tag {
  font-size: 0.68rem;
  font-weight: 700;
  color: #475569;
}

.diff-pill {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.num-pos {
  color: #dc2626;
}

.num-neg {
  color: #2563eb;
}

.num-zero {
  color: #94a3b8;
}

.na-cell {
  color: #cbd5e1;
  font-style: italic;
}

.status-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.62rem;
  font-weight: 800;
}

.status-pill--match {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.status-pill--mismatch {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.status-pill--only_summary,
.status-pill--only_source {
  background: rgba(251, 191, 36, 0.15);
  color: #d97706;
}

.status-pill--not_comparable,
.status-pill--plating_daily_only {
  background: rgba(148, 163, 184, 0.15);
  color: #64748b;
}

:deep(.row-mismatch) {
  background: rgba(254, 226, 226, 0.35) !important;
}

:deep(.row-partial) {
  background: rgba(254, 243, 199, 0.25) !important;
}

:deep(.row-muted) {
  opacity: 0.75;
}
</style>
