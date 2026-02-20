<template>
  <div class="abc-page">
    <div class="page-bg" aria-hidden="true"></div>

    <!-- ヘッダー：ガラス -->
    <header class="page-header glass">
      <div class="header-left">
        <div class="header-icon">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div>
          <h1 class="header-title">ABC分析</h1>
          <p class="header-desc">品目・納入先の重要度分析（パレート則）</p>
        </div>
      </div>
    </header>

    <!-- 条件＋実行：ガラス -->
    <section class="section-filter glass">
      <el-form :model="params" class="filter-form" inline>
        <el-form-item label="対象" class="filter-item">
          <el-select v-model="params.dimension" placeholder="対象" style="width: 128px" size="default">
            <el-option label="品目（製品）" value="product" />
            <el-option label="納入先" value="destination" />
          </el-select>
        </el-form-item>
        <el-form-item label="基準" class="filter-item">
          <el-select v-model="params.basis" placeholder="基準" style="width: 120px" size="default">
            <el-option label="出荷数量" value="quantity" />
            <el-option label="出荷箱数" value="boxes" />
            <el-option label="出荷回数" value="frequency" />
          </el-select>
        </el-form-item>
        <el-form-item label="期間" class="filter-item">
          <el-date-picker
            v-model="params.dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始"
            end-placeholder="終了"
            value-format="YYYY-MM-DD"
            style="width: 220px"
            size="default"
          />
        </el-form-item>
        <el-form-item label="A/B" class="filter-item threshold">
          <el-input-number v-model="params.aThreshold" :min="50" :max="95" :step="5" size="default" controls-position="right" />%
          <span class="threshold-sep">/</span>
          <el-input-number v-model="params.bThreshold" :min="70" :max="99" :step="5" size="default" controls-position="right" />%
        </el-form-item>
        <el-form-item class="filter-item">
          <el-button type="primary" :loading="loading" @click="runAnalysis" class="btn-run">
            <el-icon><DataAnalysis /></el-icon>
            分析実行
          </el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- ランクサマリー：ガラスカード＋アニメ -->
    <section v-if="summary.totalItems > 0" class="section-ranks">
      <div class="rank-card glass rank-a" :style="{ animationDelay: '0ms' }">
        <span class="rank-badge">A</span>
        <div class="rank-body">
          <div class="rank-count">{{ summary.aCount }}</div>
          <div class="rank-meta">重点（累積{{ params.aThreshold }}%）・{{ summary.aRatio?.toFixed(1) }}%</div>
        </div>
      </div>
      <div class="rank-card glass rank-b" :style="{ animationDelay: '50ms' }">
        <span class="rank-badge">B</span>
        <div class="rank-body">
          <div class="rank-count">{{ summary.bCount }}</div>
          <div class="rank-meta">{{ params.aThreshold }}～{{ params.bThreshold }}%・{{ summary.bRatio?.toFixed(1) }}%</div>
        </div>
      </div>
      <div class="rank-card glass rank-c" :style="{ animationDelay: '100ms' }">
        <span class="rank-badge">C</span>
        <div class="rank-body">
          <div class="rank-count">{{ summary.cCount }}</div>
          <div class="rank-meta">簡易・{{ summary.cRatio?.toFixed(1) }}%</div>
        </div>
      </div>
    </section>

    <!-- 特別枠：Zランク（デッドストック / 長期滞留品）※品目分析時のみ -->
    <section v-if="params.dimension === 'product' && (summary.totalItems > 0 || summary.zCount > 0)" class="section-z glass block-in">
      <div class="z-header">
        <span class="z-badge">Z</span>
        <div class="z-title-wrap">
          <h3 class="z-title">Zランク（長期滞留品）</h3>
          <p class="z-desc">分析期間内に出荷実績のない品目</p>
        </div>
        <div class="z-count">{{ summary.zCount }}</div>
      </div>
      <div v-if="summary.zRankItems.length > 0" class="z-codes">
        <el-tag
          v-for="item in summary.zRankItems.slice(0, 24)"
          :key="item.code"
          size="small"
          type="info"
          effect="plain"
          class="z-tag"
          :title="item.code"
        >
          {{ item.name }}
        </el-tag>
        <span v-if="summary.zRankItems.length > 24" class="z-more">他 {{ summary.zRankItems.length - 24 }} 件</span>
      </div>
      <p v-else class="z-none">該当なし</p>
    </section>

    <!-- パレート＋テーブル -->
    <section class="section-main">
      <div v-if="chartData.labels.length > 0" class="block-chart glass block-in">
        <div class="block-title">累積比率（パレート曲線）</div>
        <div class="chart-wrap" ref="chartRef"></div>
      </div>

      <div class="block-table glass block-in">
        <div class="block-title-row">
          <span class="block-title">分析結果</span>
          <el-button :disabled="tableData.length === 0" @click="handleExport" size="small" link type="primary">
            <el-icon><Download /></el-icon>
            エクスポート
          </el-button>
        </div>
        <el-table
          :data="paginatedTable"
          v-loading="loading"
          stripe
          size="default"
          max-height="400"
          :row-class-name="getRowClass"
          class="result-table"
        >
          <el-table-column type="index" label="#" width="44" align="center" />
          <el-table-column prop="rank" label="ランク" width="72" align="center" fixed>
            <template #default="{ row }">
              <el-tag :type="getRankType(row.rank)" size="small" effect="plain">{{ row.rank }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="params.dimension === 'product'" prop="code" label="品番" width="100" show-overflow-tooltip />
          <el-table-column v-if="params.dimension === 'product'" prop="name" label="品名" min-width="140" show-overflow-tooltip />
          <el-table-column v-if="params.dimension === 'destination'" prop="code" label="納入先CD" width="90" />
          <el-table-column v-if="params.dimension === 'destination'" prop="name" label="納入先名" min-width="140" show-overflow-tooltip />
          <el-table-column prop="quantity" label="数量" width="88" align="right">
            <template #default="{ row }">{{ row.quantity?.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="boxes" label="箱数" width="72" align="right">
            <template #default="{ row }">{{ row.boxes?.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="frequency" label="回数" width="72" align="right" />
          <el-table-column prop="ratio" label="構成比" width="80" align="right">
            <template #default="{ row }">{{ row.ratio?.toFixed(1) }}%</template>
          </el-table-column>
          <el-table-column prop="cumulativeRatio" label="累積" width="80" align="right">
            <template #default="{ row }">{{ row.cumulativeRatio?.toFixed(1) }}%</template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="tableData.length"
            :page-sizes="[20, 50, 100, 200]"
            layout="total, sizes, prev, pager, next"
            size="small"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { getProductList } from '@/api/master/productMaster'

const loading = ref(false)
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const params = reactive({
  dimension: 'product' as 'product' | 'destination',
  basis: 'quantity' as 'quantity' | 'boxes' | 'frequency',
  dateRange: null as string[] | null,
  aThreshold: 70,
  bThreshold: 90,
})

const summary = reactive<{
  totalItems: number
  aCount: number
  bCount: number
  cCount: number
  aRatio: number
  bRatio: number
  cRatio: number
  zCount: number
  zRankItems: { code: string; name: string }[]
}>({
  totalItems: 0,
  aCount: 0,
  bCount: 0,
  cCount: 0,
  aRatio: 0,
  bRatio: 0,
  cRatio: 0,
  zCount: 0,
  zRankItems: [],
})

const tableData = ref<AbcRow[]>([])
const chartData = reactive({ labels: [] as string[], values: [] as number[], cumulative: [] as number[] })

const pagination = reactive({ page: 1, pageSize: 50 })

interface AbcRow {
  rank: string
  code: string
  name: string
  quantity: number
  boxes: number
  frequency: number
  ratio: number
  cumulativeRatio: number
}

const paginatedTable = computed(() => {
  const start = (pagination.page - 1) * pagination.pageSize
  return tableData.value.slice(start, start + pagination.pageSize)
})

function getRankType(rank: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    A: 'danger',
    B: 'warning',
    C: 'info',
  }
  return map[rank] ?? 'info'
}

function getRowClass({ row }: { row: AbcRow }) {
  return `rank-row-${row.rank.toLowerCase()}`
}

/** 品番の末尾が '1' でない場合は '1' に置き換えて集計用キーにする（例: ABC123 → ABC121） */
function normalizeProductCode(code: string): string {
  const s = (code || '').trim()
  if (!s) return '-'
  if (s.slice(-1) === '1') return s
  return s.slice(0, -1) + '1'
}

/** 製品マスタで product_type=量産品 かつ status=active の品番・品名を取得（Zランク表示用に归一化→品名マップも作成） */
async function fetchValidProducts(): Promise<{
  validCodes: Set<string>
  normalizedToName: Map<string, string>
}> {
  try {
    const res = await getProductList({
      product_type: '量産品',
      status: 'active',
      pageSize: 10000,
      page: 1,
    })
    const list = (res as any)?.data?.list ?? (res as any)?.list ?? []
    const codes = new Set<string>()
    const normalizedToName = new Map<string, string>()
    for (const p of Array.isArray(list) ? list : []) {
      const cd = (p.product_cd || '').toString().trim()
      const name = (p.product_name || p.product_cd || cd || '').toString().trim() || cd
      if (cd) {
        codes.add(cd)
        const norm = normalizeProductCode(cd)
        if (!normalizedToName.has(norm)) normalizedToName.set(norm, name)
      }
    }
    return { validCodes: codes, normalizedToName }
  } catch {
    return { validCodes: new Set(), normalizedToName: new Map() }
  }
}

async function fetchShippingItems(): Promise<any[]> {
  if (!params.dateRange || params.dateRange.length !== 2) {
    ElMessage.warning('分析期間を指定してください')
    return []
  }
  const [start, end] = params.dateRange
  const res = await request.get('/api/shipping/items', {
    params: { shipping_date: start, end_date: end },
  })
  const list = Array.isArray(res) ? res : (res as any)?.data ?? []
  const excludeKeywords = ['加工', 'アーチ']
  return list.filter((r: any) => {
    if ((r.status || '') === 'キャンセル') return false
    const name = (r.product_name || '').toString()
    if (excludeKeywords.some((k) => name.includes(k))) return false
    return true
  })
}

function runAnalysis() {
  loading.value = true
  tableData.value = []
  chartData.labels = []
  chartData.values = []
  chartData.cumulative = []
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  summary.totalItems = 0
  summary.aCount = 0
  summary.bCount = 0
  summary.cCount = 0
  summary.aRatio = 0
  summary.bRatio = 0
  summary.cRatio = 0
  summary.zCount = 0
  summary.zRankItems = []

  Promise.all([fetchValidProducts(), fetchShippingItems()])
    .then(([validData, rawRows]) => {
      const validProductCodes = validData.validCodes
      const normalizedToName = validData.normalizedToName
      const rows = rawRows.filter((r: any) => validProductCodes.has((r.product_cd || '').toString().trim()))
      if (rows.length === 0) {
        ElMessage.info('指定期間の出荷データがありません（量産品・active の品目のみ対象）')
        return
      }
      const dim = params.dimension
      const keyCode = dim === 'product' ? 'product_cd' : 'destination_cd'
      const keyName = dim === 'product' ? 'product_name' : 'destination_name'
      const agg = new Map<
        string,
        { code: string; name: string; quantity: number; boxes: number; frequency: number }
      >()
      for (const r of rows) {
        const rawCode = (r[keyCode] || '').trim() || '-'
        const code = dim === 'product' ? normalizeProductCode(rawCode) : rawCode
        const name = (r[keyName] || r[keyCode] || rawCode).trim() || rawCode
        const q = Number(r.confirmed_units) || 0
        const b = Number(r.confirmed_boxes) || 0
        if (!agg.has(code)) {
          agg.set(code, { code, name, quantity: 0, boxes: 0, frequency: 0 })
        }
        const e = agg.get(code)!
        e.quantity += q
        e.boxes += b
        e.frequency += 1
      }
      const basisKey = params.basis === 'quantity' ? 'quantity' : params.basis === 'boxes' ? 'boxes' : 'frequency'
      const sorted = Array.from(agg.values()).sort((a, b) => (b[basisKey] as number) - (a[basisKey] as number))
      const total = sorted.reduce((s, x) => s + (x[basisKey] as number), 0)
      if (total === 0) {
        ElMessage.info('分析基準の合計が0です')
        return
      }
      const aTh = params.aThreshold / 100
      const bTh = params.bThreshold / 100
      let cum = 0
      const result: AbcRow[] = []
      const labels: string[] = []
      const values: number[] = []
      const cumulative: number[] = []
      for (const row of sorted) {
        const v = row[basisKey] as number
        const ratio = total > 0 ? v / total : 0
        cum += ratio
        let rank = 'C'
        if (cum <= aTh) rank = 'A'
        else if (cum <= bTh) rank = 'B'
        result.push({
          rank,
          code: row.code,
          name: row.name,
          quantity: row.quantity,
          boxes: row.boxes,
          frequency: row.frequency,
          ratio: Number((ratio * 100).toFixed(1)),
          cumulativeRatio: Number((cum * 100).toFixed(1)),
        })
        labels.push(row.name)
        values.push(v)
        cumulative.push(cum * 100)
      }
      tableData.value = result
      chartData.labels = labels
      chartData.values = values
      chartData.cumulative = cumulative
      summary.totalItems = result.length
      summary.aCount = result.filter((r) => r.rank === 'A').length
      summary.bCount = result.filter((r) => r.rank === 'B').length
      summary.cCount = result.filter((r) => r.rank === 'C').length
      summary.aRatio = summary.totalItems ? (summary.aCount / summary.totalItems) * 100 : 0
      summary.bRatio = summary.totalItems ? (summary.bCount / summary.totalItems) * 100 : 0
      summary.cRatio = summary.totalItems ? (summary.cCount / summary.totalItems) * 100 : 0
      if (dim === 'product') {
        const normalizedValid = new Set([...validProductCodes].map((c) => normalizeProductCode(c)))
        const aggregatedCodes = new Set(agg.keys())
        const zCodes = [...normalizedValid].filter((c) => !aggregatedCodes.has(c)).sort()
        const excludeKeywords = ['加工', 'アーチ']
        const excludeCodes = ['900B FR', '900B RR', '900B 対米', '410D RR', '410D FR2', '410D FR1', '410D CTR']
        summary.zRankItems = zCodes
          .map((code) => ({ code, name: normalizedToName.get(code) || code }))
          .filter(
            (item) =>
              !excludeKeywords.some((k) => item.name.includes(k)) &&
              !excludeCodes.some((k) => item.name.includes(k) || item.code.includes(k))
          )
        summary.zCount = summary.zRankItems.length
      } else {
        summary.zCount = 0
        summary.zRankItems = []
      }
      pagination.page = 1
      nextTick(() => {
        setTimeout(() => updateChart(), 80)
      })
    })
    .catch((e) => {
      console.error(e)
      ElMessage.error('出荷データの取得に失敗しました')
    })
    .finally(() => {
      loading.value = false
    })
}

function updateChart() {
  if (!chartRef.value || chartData.labels.length === 0) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const max = Math.min(30, chartData.labels.length)
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: any) => {
        if (!Array.isArray(params) || params.length === 0) return ''
        return params
          .map(
            (p: any) =>
              `${p.marker} ${p.seriesName}: ${
                p.seriesName === '累積比率' ? Number(p.value).toFixed(1) + '%' : p.value
              }`
          )
          .join('<br/>')
      },
    },
    legend: { data: ['分析基準値', '累積比率'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '40', containLabel: true },
    xAxis: {
      type: 'category',
      data: chartData.labels.slice(0, max),
      axisLabel: { rotate: 45, overflow: 'truncate', width: 80 },
    },
    yAxis: [
      { type: 'value', name: '値', position: 'left' },
      {
        type: 'value',
        name: '累積%',
        min: 0,
        max: 100,
        position: 'right',
        axisLabel: { formatter: (v: number) => Number(v).toFixed(1) + '%' },
      },
    ],
    series: [
      { name: '分析基準値', type: 'bar', data: chartData.values.slice(0, max), itemStyle: { color: '#409eff' } },
      {
        name: '累積比率',
        type: 'line',
        yAxisIndex: 1,
        data: chartData.cumulative.slice(0, max),
        itemStyle: { color: '#f56c6c' },
        lineStyle: { width: 2 },
      },
    ],
  }
  chartInstance.setOption(option, true)
  chartInstance.resize()
}

watch(
  () => [chartData.labels.length, chartRef.value],
  () => {
    if (chartRef.value && chartData.labels.length > 0) {
      nextTick(() => {
        setTimeout(() => updateChart(), 50)
      })
    }
  }
)

function handleExport() {
  if (tableData.value.length === 0) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }
  const headers = ['ランク', 'コード', '名称', '出荷数量', '出荷箱数', '出荷回数', '構成比%', '累積比率%']
  const rows = tableData.value.map((r) =>
    [r.rank, r.code, r.name, r.quantity, r.boxes, r.frequency, r.ratio.toFixed(1), r.cumulativeRatio.toFixed(1)].join(
      ','
    )
  )
  const csv = '\uFEFF' + [headers.join(','), ...rows].join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `shipping_abc_analysis_${params.dimension}_${params.basis}_${params.dateRange?.join('_') || 'range'}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('CSVをダウンロードしました')
}

function onResize() {
  if (chartInstance && chartRef.value) {
    chartInstance.resize()
  }
}

onMounted(() => {
  const today = new Date()
  const end = today.toISOString().slice(0, 10)
  const start = new Date(today)
  start.setMonth(start.getMonth() - 3)
  params.dateRange = [start.toISOString().slice(0, 10), end]
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
/* フォント・変数 */
.abc-page {
  --radius: 12px;
  --space: 14px;
  --space-sm: 10px;
  --font-ui: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', Meiryo, sans-serif;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #64748b;
  font-family: var(--font-ui);
  padding: var(--space);
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  min-height: 100vh;
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(160deg, #f1f5f9 0%, #e2e8f0 40%, #cbd5e1 100%);
  pointer-events: none;
}

/* ガラス */
.glass {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

/* ヘッダー */
.page-header {
  margin-bottom: var(--space);
  padding: var(--space) 16px;
  border-radius: var(--radius);
  animation: fadeIn 0.4s ease-out;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.header-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.35);
}
.header-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.03em;
  line-height: 1.3;
}
.header-desc {
  margin: 4px 0 0 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

/* フィルター */
.section-filter {
  padding: var(--space) 16px;
  margin-bottom: var(--space);
  border-radius: var(--radius);
  animation: slideIn 0.4s ease-out 0.05s backwards;
}
.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}
.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 4px;
}
.filter-form :deep(.el-form-item .el-form-item__label) {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding-right: 8px;
}
.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-date-editor) {
  font-family: var(--font-ui);
}
.threshold .threshold-sep {
  margin: 0 6px;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
}
.btn-run {
  font-weight: 600;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.btn-run:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* ランクカード */
.section-ranks {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space);
  margin-bottom: var(--space);
}
.rank-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: var(--radius);
  animation: cardIn 0.4s ease-out backwards;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.rank-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}
.rank-card.rank-a {
  border-left: 4px solid #f56c6c;
}
.rank-card.rank-b {
  border-left: 4px solid #e6a23c;
}
.rank-card.rank-c {
  border-left: 4px solid #909399;
}
.rank-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 15px;
  flex-shrink: 0;
  font-family: var(--font-ui);
  letter-spacing: -0.02em;
}
.rank-a .rank-badge { background: #f56c6c; color: #fff; }
.rank-b .rank-badge { background: #e6a23c; color: #fff; }
.rank-c .rank-badge { background: #909399; color: #fff; }
.rank-body {
  min-width: 0;
}
.rank-count {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
  font-family: var(--font-ui);
  letter-spacing: -0.02em;
}
.rank-meta {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* 特別枠：Zランク */
.section-z {
  padding: var(--space) 16px;
  margin-bottom: var(--space);
  border-radius: var(--radius);
  border-left: 4px solid #8b5cf6;
  animation-delay: 0.12s;
}
.z-header {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.z-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  color: #fff;
  font-weight: 800;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-ui);
  flex-shrink: 0;
}
.z-title-wrap {
  flex: 1;
  min-width: 0;
}
.z-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.z-desc {
  margin: 2px 0 0 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
}
.z-count {
  font-size: 1.35rem;
  font-weight: 800;
  color: #8b5cf6;
  font-family: var(--font-ui);
  letter-spacing: -0.02em;
}
.z-codes {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 8px;
  align-items: center;
}
.z-tag {
  font-weight: 500;
  font-family: var(--font-ui);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.z-more {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
}
.z-none {
  margin: 12px 0 0 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* メイン */
.section-main {
  display: flex;
  flex-direction: column;
  gap: var(--space);
}
.block-chart,
.block-table {
  padding: var(--space) 16px;
  border-radius: var(--radius);
}
.block-in {
  animation: blockIn 0.45s ease-out backwards;
}
.block-table.block-in {
  animation-delay: 0.08s;
}
.block-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
  letter-spacing: -0.01em;
}
.block-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}
.block-title-row .block-title {
  margin-bottom: 0;
}
.chart-wrap {
  width: 100%;
  height: 300px;
  border-radius: 8px;
}
.result-table {
  font-size: 13px;
  font-family: var(--font-ui);
}
.result-table :deep(.el-table__header th) {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
}
.result-table :deep(.el-table__body td) {
  font-weight: 500;
  color: var(--text-primary);
}
.pagination-wrap {
  margin-top: var(--space-sm);
  display: flex;
  justify-content: flex-end;
}
.pagination-wrap :deep(.el-pagination) {
  font-weight: 500;
  font-family: var(--font-ui);
}

:deep(.rank-row-a) {
  background-color: rgba(245, 108, 108, 0.06) !important;
}
:deep(.rank-row-b) {
  background-color: rgba(230, 162, 60, 0.06) !important;
}
:deep(.rank-row-c) {
  background-color: rgba(144, 147, 153, 0.05) !important;
}

@keyframes blockIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========== 响应式：平板・手机 ========== */
@media (max-width: 1024px) {
  .abc-page {
    padding: 12px;
    max-width: 100%;
  }
  .page-header {
    padding: 12px 14px;
  }
  .section-filter {
    padding: 12px 14px;
  }
  .filter-form {
    gap: 8px 10px;
  }
  .filter-form :deep(.el-form-item) {
    flex: 1 1 auto;
    min-width: 140px;
  }
  .filter-form :deep(.el-form-item.threshold) {
    flex: 1 1 100%;
    min-width: 100%;
  }
  .section-ranks {
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  .rank-card {
    padding: 10px 12px;
  }
  .rank-count {
    font-size: 1.2rem;
  }
  .section-z {
    padding: 12px 14px;
  }
  .section-main {
    gap: 10px;
  }
  .block-chart,
  .block-table {
    padding: 12px 14px;
  }
  .chart-wrap {
    height: 260px;
  }
  .result-table :deep(.el-table__header th),
  .result-table :deep(.el-table__body td) {
    font-size: 12px;
  }
  .pagination-wrap :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }
}

@media (max-width: 900px) {
  .section-ranks {
    grid-template-columns: 1fr;
  }
  .filter-form {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-form :deep(.el-form-item) {
    min-width: 100%;
  }
  .filter-form :deep(.el-select),
  .filter-form :deep(.el-date-editor) {
    width: 100% !important;
  }
  .filter-form :deep(.el-form-item.threshold) {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
  }
  .filter-form :deep(.el-form-item.threshold .el-input-number) {
    flex: 1;
    min-width: 80px;
  }
}

@media (max-width: 768px) {
  .abc-page {
    padding: 10px;
    --space: 10px;
    --space-sm: 8px;
  }
  .page-header {
    padding: 10px 12px;
    margin-bottom: 10px;
  }
  .header-left {
    flex-wrap: wrap;
    gap: 10px;
  }
  .header-icon {
    width: 38px;
    height: 38px;
    font-size: 18px;
  }
  .header-title {
    font-size: 1.15rem;
  }
  .header-desc {
    font-size: 12px;
  }
  .section-filter {
    padding: 10px 12px;
    margin-bottom: 10px;
  }
  .section-ranks {
    gap: 8px;
    margin-bottom: 10px;
  }
  .rank-card {
    padding: 10px 12px;
    gap: 10px;
  }
  .rank-badge {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
  .rank-count {
    font-size: 1.15rem;
  }
  .rank-meta {
    font-size: 11px;
  }
  .section-z {
    padding: 10px 12px;
    margin-bottom: 10px;
  }
  .z-header {
    gap: 10px;
  }
  .z-badge {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
  .z-title {
    font-size: 13px;
  }
  .z-desc {
    font-size: 11px;
  }
  .z-count {
    font-size: 1.15rem;
  }
  .z-tag {
    max-width: 140px;
  }
  .section-main {
    gap: 8px;
  }
  .block-chart,
  .block-table {
    padding: 10px 12px;
    border-radius: 10px;
  }
  .block-title,
  .block-title-row .block-title {
    font-size: 13px;
  }
  .chart-wrap {
    height: 220px;
  }
  .result-table {
    font-size: 12px;
  }
  .result-table :deep(.el-table) {
    min-width: 560px;
  }
  .result-table :deep(.el-table__header th),
  .result-table :deep(.el-table__body td) {
    font-size: 11px;
    padding: 8px 6px;
  }
  .block-table {
    overflow-x: auto;
  }
  .pagination-wrap {
    margin-top: 8px;
    justify-content: center;
  }
  .pagination-wrap :deep(.el-pagination) {
    font-size: 12px;
  }
  .pagination-wrap :deep(.el-pagination .el-pager li),
  .pagination-wrap :deep(.el-pagination .btn-prev),
  .pagination-wrap :deep(.el-pagination .btn-next) {
    min-width: 28px;
    height: 28px;
    line-height: 28px;
  }
}

@media (max-width: 480px) {
  .abc-page {
    padding: 8px;
    --space: 8px;
    --space-sm: 6px;
  }
  .page-header {
    padding: 8px 10px;
    margin-bottom: 8px;
    border-radius: 10px;
  }
  .header-title {
    font-size: 1rem;
  }
  .header-desc {
    font-size: 11px;
  }
  .section-filter {
    padding: 8px 10px;
    margin-bottom: 8px;
    border-radius: 10px;
  }
  .btn-run {
    width: 100%;
  }
  .section-ranks {
    gap: 6px;
    margin-bottom: 8px;
  }
  .rank-card {
    padding: 8px 10px;
    gap: 8px;
  }
  .rank-count {
    font-size: 1.05rem;
  }
  .section-z {
    padding: 8px 10px;
    margin-bottom: 8px;
    border-radius: 10px;
  }
  .z-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .z-count {
    font-size: 1.2rem;
  }
  .z-codes {
    margin-top: 8px;
    gap: 4px 6px;
  }
  .z-tag {
    max-width: 120px;
    font-size: 11px;
  }
  .block-chart,
  .block-table {
    padding: 8px 10px;
    border-radius: 10px;
  }
  .block-title-row {
    flex-wrap: wrap;
    gap: 8px;
  }
  .block-title-row .el-button {
    width: 100%;
    justify-content: center;
  }
  .chart-wrap {
    height: 200px;
  }
  .pagination-wrap :deep(.el-pagination) {
    font-size: 11px;
  }
  .pagination-wrap :deep(.el-pagination .el-pager li),
  .pagination-wrap :deep(.el-pagination .btn-prev),
  .pagination-wrap :deep(.el-pagination .btn-next) {
    min-width: 26px;
    height: 26px;
    line-height: 26px;
  }
}
</style>
