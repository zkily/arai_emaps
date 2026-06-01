<template>
  <div class="process-actual">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="page-title">
        <div class="title-icon">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="title-content">
          <h1>工程別実績</h1>
          <p>日・月単位で各工程の一日合計実績を集計・可視化します</p>
        </div>
      </div>
      <div class="page-actions">
        <el-button :icon="Download" class="action-btn" @click="handleExportCsv">CSV出力</el-button>
        <el-button :icon="Refresh" class="action-btn" :loading="loading" @click="loadData">再取得</el-button>
      </div>
    </div>

    <!-- 検索カード -->
    <el-card class="search-card" shadow="hover">
      <div class="search-bar">
        <div class="search-field mode-field">
          <span class="field-label">集計単位</span>
          <el-radio-group v-model="mode" class="mode-group" @change="handleModeChange">
            <el-radio-button label="day">日</el-radio-button>
            <el-radio-button label="month">月</el-radio-button>
          </el-radio-group>
        </div>

        <div class="search-field date-field">
          <span class="field-label">{{ mode === 'day' ? '対象日' : '対象月' }}</span>
          <div class="date-input-group">
            <el-date-picker
              v-if="mode === 'day'"
              v-model="selectedDay"
              type="date"
              placeholder="日付を選択"
              format="YYYY/MM/DD"
              value-format="YYYY-MM-DD"
              :clearable="false"
              class="date-picker"
              @change="loadData"
            />
            <el-date-picker
              v-else
              v-model="selectedMonth"
              type="month"
              placeholder="月を選択"
              format="YYYY年MM月"
              value-format="YYYY-MM"
              :clearable="false"
              class="date-picker"
              @change="loadData"
            />
            <div class="quick-buttons">
              <el-button size="small" class="date-btn" @click="shift(-1)">{{ mode === 'day' ? '前日' : '前月' }}</el-button>
              <el-button size="small" class="date-btn current" @click="setCurrent">{{ mode === 'day' ? '今日' : '今月' }}</el-button>
              <el-button size="small" class="date-btn" @click="shift(1)">{{ mode === 'day' ? '翌日' : '翌月' }}</el-button>
            </div>
          </div>
        </div>

        <div class="search-field process-field">
          <span class="field-label">工程</span>
          <el-select
            v-model="selectedProcessCd"
            placeholder="工程を選択"
            filterable
            clearable
            class="process-select"
            @change="handleProcessFilterChange"
          >
            <el-option label="全工程" value="" />
            <el-option
              v-for="opt in processOptions"
              :key="opt.process_cd"
              :label="opt.process_name"
              :value="opt.process_cd"
            />
          </el-select>
        </div>

        <div class="search-field period-field">
          <span class="field-label">対象期間</span>
          <el-tag class="period-tag" type="info" effect="plain">{{ periodLabel }}</el-tag>
        </div>
      </div>
    </el-card>

    <!-- 工程別 日次実績柱状 -->
    <el-card class="process-daily-chart-card" shadow="hover">
      <template #header>
        <div class="chart-header">
          <div class="chart-title">
            <el-icon><Histogram /></el-icon>
            <span>{{ selectedProcessLabel }} — 日次実績（柱状）</span>
          </div>
          <div class="chart-header-meta">
            <el-tag v-if="selectedProcessCd" size="small" type="primary" effect="plain">
              期間合計: {{ formatNumber(selectedProcessPeriodTotal) }} 本
            </el-tag>
            <el-tag v-else size="small" type="info" effect="plain">工程を選択してください</el-tag>
          </div>
        </div>
      </template>
      <div class="chart-panel">
        <el-skeleton v-if="loading" animated :rows="4" class="chart-panel__skeleton" />
        <div ref="processDailyLineRef" class="process-daily-line-chart"></div>
      </div>
    </el-card>

    <!-- 統計カード -->
    <transition-group name="fade-slide" tag="div" class="stats-grid">
      <div v-for="card in statCards" :key="card.key" class="stat-card">
        <div class="stat-icon" :class="card.type">
          <component :is="card.icon" />
        </div>
        <div class="stat-body">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">
            {{ card.value }}
            <small v-if="card.unit">{{ card.unit }}</small>
          </div>
        </div>
      </div>
    </transition-group>

    <!-- 分析チャート -->
    <el-card class="chart-card" shadow="hover">
      <template #header>
        <div class="chart-header">
          <div class="chart-title">
            <el-icon><TrendCharts /></el-icon>
            <span>工程別実績分析</span>
          </div>
          <el-tag size="small" type="info" effect="plain">実績合計: {{ formatNumber(totalQuantity) }} 本</el-tag>
        </div>
      </template>
      <div class="chart-panel chart-panel--grid">
        <el-skeleton v-if="loading" animated :rows="6" class="chart-panel__skeleton" />
        <div class="charts-grid">
          <div class="chart-item">
            <div class="chart-item-header">
              <span class="chart-item-title">工程別合計</span>
            </div>
            <div ref="processBarRef" class="chart-container"></div>
          </div>
          <div class="chart-item">
            <div class="chart-item-header">
              <span class="chart-item-title">工程別構成比</span>
            </div>
            <div ref="processPieRef" class="chart-container"></div>
          </div>
          <div class="chart-item">
            <div class="chart-item-header">
              <span class="chart-item-title">{{ mode === 'day' ? '工程別一日合計' : '日別合計推移' }}</span>
            </div>
            <div ref="dailyTrendRef" class="chart-container"></div>
          </div>
          <div class="chart-item">
            <div class="chart-item-header">
              <span class="chart-item-title">工程別日次推移</span>
            </div>
            <div ref="processStackRef" class="chart-container"></div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 工程別サマリーテーブル -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="table-header">
          <div class="table-title">
            <el-icon><List /></el-icon>
            <span>工程別実績サマリー</span>
          </div>
          <el-tag type="info" size="small">{{ processSummary.length }} 工程</el-tag>
        </div>
      </template>
      <el-skeleton v-if="loading" animated :rows="5" />
      <template v-else>
        <el-table
          v-if="processSummary.length"
          :data="processSummary"
          stripe
          border
          class="data-table"
          :default-sort="{ prop: 'total', order: 'descending' }"
        >
          <el-table-column type="index" label="No" width="56" align="center" />
          <el-table-column prop="process_name" label="工程" min-width="130">
            <template #default="{ row }">
              <div class="process-cell">
                <span class="color-dot" :style="{ background: row.color }"></span>
                <span class="process-name">{{ row.process_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="total" label="合計数量" width="130" align="right" sortable>
            <template #default="{ row }">
              <span class="quantity">{{ formatNumber(row.total) }}</span>
              <small class="unit">本</small>
            </template>
          </el-table-column>
          <el-table-column prop="activeDays" label="稼働日数" width="100" align="center" sortable>
            <template #default="{ row }">{{ row.activeDays }} 日</template>
          </el-table-column>
          <el-table-column prop="avgPerDay" label="平均/稼働日" width="130" align="right" sortable>
            <template #default="{ row }">
              <span class="quantity">{{ formatNumber(row.avgPerDay, 1) }}</span>
              <small class="unit">本</small>
            </template>
          </el-table-column>
          <el-table-column label="構成比" min-width="180">
            <template #default="{ row }">
              <div class="ratio-cell">
                <el-progress
                  :percentage="row.ratio"
                  :stroke-width="10"
                  :color="row.color"
                  :show-text="false"
                  class="ratio-bar"
                />
                <span class="ratio-text">{{ row.ratio.toFixed(1) }}%</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="該当データがありません" />
      </template>
    </el-card>

    <!-- 工程別 × 日別 マトリクス（月モードで有用） -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="table-header">
          <div class="table-title">
            <el-icon><Grid /></el-icon>
            <span>工程別 一日合計マトリクス</span>
          </div>
          <el-tag type="info" size="small">{{ dateColumns.length }} 日</el-tag>
        </div>
      </template>
      <el-skeleton v-if="loading" animated :rows="5" />
      <template v-else>
        <el-table
          v-if="matrixRows.length"
          :data="matrixRows"
          border
          size="small"
          max-height="460"
          class="data-table matrix-table"
          show-summary
          :summary-method="matrixSummary"
        >
          <el-table-column
            prop="process_name"
            label="工程"
            width="120"
            fixed="left"
            align="left"
          >
            <template #default="{ row }">
              <div class="process-cell">
                <span class="color-dot" :style="{ background: row.color }"></span>
                <span class="process-name">{{ row.process_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            v-for="col in dateColumns"
            :key="col.key"
            :label="col.label"
            :prop="col.key"
            width="78"
            align="right"
          >
            <template #default="{ row }">
              <span :class="{ 'cell-zero': !Number(row[col.key]) }">
                {{ Number(row[col.key]) ? formatNumber(Number(row[col.key])) : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="合計" width="110" align="right" fixed="right">
            <template #default="{ row }">
              <span class="quantity row-total">{{ formatNumber(row.total) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="該当データがありません" />
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'ProcessActual' })
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis,
  TrendCharts,
  Refresh,
  Download,
  List,
  Grid,
  CollectionTag,
  DataLine,
  Histogram,
  Calendar,
  Top,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { fetchProcesses } from '@/api/master/processMaster'
import { getStockActualLogs, type StockActualLogRecord } from '@/api/productionActualStockLogs'

const PALETTE = [
  '#3b82f6', '#6366f1', '#10b981', '#f59e0b', '#ef4444',
  '#06b6d4', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
  '#0ea5e9', '#a855f7',
]

const allowedProcessesOrder = [
  '切断', '面取', '成型', 'メッキ', '外注メッキ',
  '溶接', '外注溶接', '検査', '溶接前検査', '倉庫',
]

const loading = ref(false)
const mode = ref<'day' | 'month'>('day')
const records = ref<StockActualLogRecord[]>([])
const processMasterList = ref<{ process_cd: string; process_name: string }[]>([])
const selectedProcessCd = ref('')

// 日本時区での今日
const getJapanDate = () => {
  const now = new Date()
  const utc = now.getTime() + now.getTimezoneOffset() * 60000
  return new Date(utc + 9 * 3600000)
}
const pad = (n: number) => `${n}`.padStart(2, '0')
const toDayStr = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const toMonthStr = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}`

const today = getJapanDate()
const selectedDay = ref<string>(toDayStr(today))
const selectedMonth = ref<string>(toMonthStr(today))

// 期間（date_from / date_to）の算出
const dateRange = computed(() => {
  if (mode.value === 'day') {
    return { from: selectedDay.value, to: selectedDay.value }
  }
  const [y, m] = selectedMonth.value.split('-').map((v) => parseInt(v, 10))
  const first = new Date(y, m - 1, 1)
  const last = new Date(y, m, 0)
  return { from: toDayStr(first), to: toDayStr(last) }
})

const periodLabel = computed(() => {
  const { from, to } = dateRange.value
  if (from === to) return from
  return `${from} 〜 ${to}`
})

// 日付列（マトリクス用）
const dateColumns = computed(() => {
  const cols: { key: string; label: string }[] = []
  const { from, to } = dateRange.value
  const start = new Date(`${from}T00:00:00`)
  const end = new Date(`${to}T00:00:00`)
  const cur = new Date(start)
  let guard = 0
  while (cur <= end && guard < 366) {
    cols.push({ key: toDayStr(cur), label: `${pad(cur.getMonth() + 1)}/${pad(cur.getDate())}` })
    cur.setDate(cur.getDate() + 1)
    guard++
  }
  return cols
})

const extractDate = (timeStr: unknown): string => {
  const s = String(timeStr || '')
  const m = s.match(/^(\d{4}-\d{2}-\d{2})/)
  return m ? m[1] : ''
}

/** 工程マスタ + 実績データから選択肢を構築 */
const processOptions = computed(() => {
  const map = new Map<string, { process_cd: string; process_name: string }>()
  processMasterList.value.forEach((p) => {
    if (p.process_cd) map.set(p.process_cd, p)
  })
  records.value.forEach((r) => {
    const cd = String(r.process_cd || '').trim()
    if (!cd) return
    if (!map.has(cd)) {
      map.set(cd, {
        process_cd: cd,
        process_name: String(r.process_name || cd),
      })
    }
  })
  const list = Array.from(map.values())
  list.sort((a, b) => {
    const ia = allowedProcessesOrder.indexOf(a.process_name)
    const ib = allowedProcessesOrder.indexOf(b.process_name)
    if (ia !== -1 && ib !== -1) return ia - ib
    if (ia !== -1) return -1
    if (ib !== -1) return 1
    return a.process_name.localeCompare(b.process_name, 'ja')
  })
  return list
})

const selectedProcessLabel = computed(() => {
  if (!selectedProcessCd.value) return '工程未選択'
  const opt = processOptions.value.find((p) => p.process_cd === selectedProcessCd.value)
  return opt?.process_name || selectedProcessCd.value
})

const filteredRecords = computed(() => {
  if (!selectedProcessCd.value) return records.value
  return records.value.filter((r) => String(r.process_cd || '') === selectedProcessCd.value)
})

interface ProcessAgg {
  process_cd: string
  process_name: string
  total: number
  dailyMap: Map<string, number>
}

// 工程ごとの集計（工程フィルタ適用後）
const aggregated = computed(() => {
  const map = new Map<string, ProcessAgg>()
  filteredRecords.value.forEach((r) => {
    const cd = String(r.process_cd || '__none__')
    const name = String(r.process_name || r.process_cd || '未分類')
    const qty = Number(r.quantity) || 0
    const date = extractDate(r.transaction_time)
    if (!map.has(cd)) {
      map.set(cd, { process_cd: cd, process_name: name, total: 0, dailyMap: new Map() })
    }
    const agg = map.get(cd)!
    agg.total += qty
    if (date) agg.dailyMap.set(date, (agg.dailyMap.get(date) || 0) + qty)
  })

  // 工程順に並べ替え（既定順 → その他）
  const list = Array.from(map.values())
  list.sort((a, b) => {
    const ia = allowedProcessesOrder.indexOf(a.process_name)
    const ib = allowedProcessesOrder.indexOf(b.process_name)
    if (ia !== -1 && ib !== -1) return ia - ib
    if (ia !== -1) return -1
    if (ib !== -1) return 1
    return b.total - a.total
  })
  return list
})

const colorMap = computed(() => {
  const m = new Map<string, string>()
  aggregated.value.forEach((p, i) => m.set(p.process_cd, PALETTE[i % PALETTE.length]))
  return m
})

const totalQuantity = computed(() => aggregated.value.reduce((s, p) => s + p.total, 0))

const processSummary = computed(() => {
  const total = totalQuantity.value || 1
  return aggregated.value.map((p) => ({
    process_cd: p.process_cd,
    process_name: p.process_name,
    total: p.total,
    activeDays: p.dailyMap.size,
    avgPerDay: p.dailyMap.size ? p.total / p.dailyMap.size : 0,
    ratio: (p.total / total) * 100,
    color: colorMap.value.get(p.process_cd) || PALETTE[0],
  }))
})

const matrixRows = computed(() => {
  return aggregated.value.map((p) => {
    const row: Record<string, unknown> = {
      process_cd: p.process_cd,
      process_name: p.process_name,
      total: p.total,
      color: colorMap.value.get(p.process_cd) || PALETTE[0],
    }
    dateColumns.value.forEach((c) => {
      row[c.key] = p.dailyMap.get(c.key) || 0
    })
    return row
  })
})

const matrixSummary = (param: { columns: any[]; data: any[] }) => {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((col, idx) => {
    if (idx === 0) {
      sums[idx] = '合計'
      return
    }
    const prop = col.property
    if (prop === 'process_name') {
      sums[idx] = ''
      return
    }
    let total = 0
    if (prop) {
      total = data.reduce((s, row) => s + (Number(row[prop]) || 0), 0)
    } else {
      // 合計列（prop なし）
      total = data.reduce((s, row) => s + (Number(row.total) || 0), 0)
    }
    sums[idx] = total ? formatNumber(total) : '-'
  })
  return sums
}

// 統計カード
const formatNumber = (value: number | undefined, fraction = 0) => {
  const num = Number(value || 0)
  return num.toLocaleString(undefined, {
    minimumFractionDigits: fraction,
    maximumFractionDigits: fraction,
  })
}

const activeDaysTotal = computed(() => {
  const days = new Set<string>()
  filteredRecords.value.forEach((r) => {
    const d = extractDate(r.transaction_time)
    if (d) days.add(d)
  })
  return days.size
})

/** 選択工程の期間内日次データ（折線図用） */
const selectedProcessDailyData = computed(() => {
  const dates = dateColumns.value
  if (!selectedProcessCd.value) {
    return { dates, values: [] as number[], color: PALETTE[0], total: 0 }
  }
  const agg = aggregated.value.find((p) => p.process_cd === selectedProcessCd.value)
  if (!agg) {
    return { dates, values: dates.map(() => 0), color: PALETTE[0], total: 0 }
  }
  const values = dates.map((c) => agg.dailyMap.get(c.key) || 0)
  const total = values.reduce((s, v) => s + v, 0)
  return {
    dates,
    values,
    color: colorMap.value.get(agg.process_cd) || PALETTE[0],
    total,
  }
})

const selectedProcessPeriodTotal = computed(() => selectedProcessDailyData.value.total)

const topProcess = computed(() => {
  if (!processSummary.value.length) return { name: '-', total: 0 }
  const top = processSummary.value.reduce((a, b) => (b.total > a.total ? b : a))
  return { name: top.process_name, total: top.total }
})

const statCards = computed(() => [
  {
    key: 'process',
    label: '対象工程数',
    value: formatNumber(aggregated.value.length),
    unit: '工程',
    icon: CollectionTag,
    type: 'primary',
  },
  {
    key: 'quantity',
    label: '実績合計',
    value: formatNumber(totalQuantity.value),
    unit: '本',
    icon: DataLine,
    type: 'success',
  },
  {
    key: 'days',
    label: '稼働日数',
    value: formatNumber(activeDaysTotal.value),
    unit: '日',
    icon: Calendar,
    type: 'info',
  },
  {
    key: 'top',
    label: '最多工程',
    value: topProcess.value.name,
    unit: topProcess.value.total ? `${formatNumber(topProcess.value.total)}本` : '',
    icon: Top,
    type: 'warning',
  },
])

const loadProcessMaster = async () => {
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 500 })
    const list = res.data?.list || res.list || []
    processMasterList.value = list
      .filter((p: { process_cd?: string }) => p.process_cd)
      .map((p: { process_cd: string; process_name?: string }) => ({
        process_cd: p.process_cd,
        process_name: p.process_name || p.process_cd,
      }))
  } catch (e) {
    console.error('工程マスタ取得失敗:', e)
  }
}

const processFilterInitialized = ref(false)

const syncProcessSelection = () => {
  if (selectedProcessCd.value) {
    const exists = processOptions.value.some((p) => p.process_cd === selectedProcessCd.value)
    if (!exists && processOptions.value.length) {
      selectedProcessCd.value = processOptions.value[0].process_cd
    }
    return
  }
  // 初回のみ先頭工程を自動選択（「全工程」選択後の再取得では上書きしない）
  if (!processFilterInitialized.value && processOptions.value.length) {
    selectedProcessCd.value = processOptions.value[0].process_cd
    processFilterInitialized.value = true
  }
}

const handleProcessFilterChange = () => {
  refreshChartsAfterRender()
}

// ===== データ取得 =====
const loadData = async () => {
  loading.value = true
  try {
    const { from, to } = dateRange.value
    const res = await getStockActualLogs({
      page: 1,
      limit: 10000,
      transaction_type: '実績',
      date_from: from,
      date_to: to,
    })
    if (res?.success && res.data) {
      records.value = res.data.list || []
    } else {
      records.value = []
    }
    syncProcessSelection()
  } catch (error: any) {
    console.error('工程別実績取得失敗:', error)
    records.value = []
    if (!(error?.isTokenError || error?.response?.status === 403)) {
      ElMessage.error('実績データの取得に失敗しました')
    }
  } finally {
    loading.value = false
    await refreshChartsAfterRender()
  }
}

const handleModeChange = () => {
  loadData()
}

const shift = (delta: number) => {
  if (mode.value === 'day') {
    const d = new Date(`${selectedDay.value}T00:00:00`)
    d.setDate(d.getDate() + delta)
    selectedDay.value = toDayStr(d)
  } else {
    const [y, m] = selectedMonth.value.split('-').map((v) => parseInt(v, 10))
    const d = new Date(y, m - 1 + delta, 1)
    selectedMonth.value = toMonthStr(d)
  }
  loadData()
}

const setCurrent = () => {
  const now = getJapanDate()
  if (mode.value === 'day') selectedDay.value = toDayStr(now)
  else selectedMonth.value = toMonthStr(now)
  loadData()
}

const handleExportCsv = () => {
  if (!processSummary.value.length) {
    ElMessage.warning('出力するデータがありません')
    return
  }
  const header = ['工程', ...dateColumns.value.map((c) => c.label), '合計']
  const lines = [header.join(',')]
  matrixRows.value.forEach((row) => {
    const cells = [
      String(row.process_name),
      ...dateColumns.value.map((c) => String(Number(row[c.key]) || 0)),
      String(Number(row.total) || 0),
    ]
    lines.push(cells.join(','))
  })
  const csv = '\uFEFF' + lines.join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `工程別実績_${dateRange.value.from}_${dateRange.value.to}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('CSVを出力しました')
}

// ===== チャート =====
const processBarRef = ref<HTMLDivElement>()
const processPieRef = ref<HTMLDivElement>()
const dailyTrendRef = ref<HTMLDivElement>()
const processStackRef = ref<HTMLDivElement>()
const processDailyLineRef = ref<HTMLDivElement>()

let processBar: echarts.ECharts | null = null
let processPie: echarts.ECharts | null = null
let dailyTrend: echarts.ECharts | null = null
let processStack: echarts.ECharts | null = null
let processDailyLine: echarts.ECharts | null = null

const baseGrid = { left: 12, right: 18, top: 24, bottom: 24, containLabel: true }
const axisLabelStyle = { color: '#6b7280', fontSize: 11 }

const disposeCharts = () => {
  processBar?.dispose()
  processPie?.dispose()
  dailyTrend?.dispose()
  processStack?.dispose()
  processDailyLine?.dispose()
  processBar = null
  processPie = null
  dailyTrend = null
  processStack = null
  processDailyLine = null
}

const initChartOn = (el: HTMLDivElement | undefined, instance: echarts.ECharts | null) => {
  if (!el) return null
  if (instance && !instance.isDisposed()) {
    instance.dispose()
  }
  return echarts.init(el)
}

const ensureCharts = () => {
  processBar = initChartOn(processBarRef.value, processBar)
  processPie = initChartOn(processPieRef.value, processPie)
  dailyTrend = initChartOn(dailyTrendRef.value, dailyTrend)
  processStack = initChartOn(processStackRef.value, processStack)
  processDailyLine = initChartOn(processDailyLineRef.value, processDailyLine)
}

/** loading 終了後、DOM 描画完了してからチャートを初期化・更新 */
const refreshChartsAfterRender = async () => {
  await nextTick()
  requestAnimationFrame(() => {
    ensureCharts()
    updateCharts()
    requestAnimationFrame(() => {
      processBar?.resize()
      processPie?.resize()
      dailyTrend?.resize()
      processStack?.resize()
      processDailyLine?.resize()
    })
  })
}

const updateProcessDailyLineChart = () => {
  if (!processDailyLine) return

  const { dates, values, color } = selectedProcessDailyData.value
  const labels = dates.map((c) => c.label)
  const hasSelection = Boolean(selectedProcessCd.value)

  if (!hasSelection) {
    processDailyLine.setOption({
      title: {
        text: '上の「工程」から対象工程を選択してください',
        left: 'center',
        top: 'middle',
        textStyle: { color: '#94a3b8', fontSize: 13, fontWeight: 500 },
      },
      xAxis: { show: false },
      yAxis: { show: false },
      series: [],
    }, true)
    return
  }

  const maxVal = Math.max(...values, 0)
  processDailyLine.setOption({
    title: { show: false },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      formatter: (params: unknown) => {
        const list = Array.isArray(params) ? params : [params]
        const p = list[0] as { axisValue?: string; value?: number }
        return `<div style="font-weight:600;margin-bottom:4px">${p.axisValue ?? ''}</div>
          <div>一日合計: <b>${formatNumber(Number(p.value) || 0)}</b> 本</div>`
      },
    },
    grid: { left: 48, right: 24, top: 44, bottom: dates.length > 15 ? 56 : 36, containLabel: false },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        ...axisLabelStyle,
        rotate: labels.length > 15 ? 45 : 0,
      },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: maxVal > 0 ? undefined : 10,
      axisLabel: axisLabelStyle,
      splitLine: { lineStyle: { color: '#eef2f7', type: 'dashed' } },
    },
    series: [
      {
        name: selectedProcessLabel.value,
        type: 'bar',
        data: values.map((v) => ({
          value: v,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color },
              { offset: 1, color: color + '99' },
            ]),
          },
        })),
        barMaxWidth: dates.length <= 3 ? 48 : dates.length <= 10 ? 36 : 28,
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        label: {
          show: true,
          position: 'top',
          distance: 6,
          fontSize: dates.length > 20 ? 9 : 11,
          fontWeight: 600,
          color: '#334155',
          formatter: (p: { value?: number | { value?: number } }) => {
            const raw = typeof p.value === 'object' && p.value !== null ? p.value.value : p.value
            const num = Number(raw) || 0
            return num > 0 ? formatNumber(num) : ''
          },
        },
      },
    ],
  }, true)
}

const updateCharts = () => {
  updateProcessDailyLineChart()
  const summary = processSummary.value

  // 1) 工程別合計（横棒）
  if (processBar) {
    const names = summary.map((s) => s.process_name)
    processBar.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        valueFormatter: (v: number) => `${formatNumber(v)} 本`,
      },
      grid: { ...baseGrid, left: 12 },
      xAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: { lineStyle: { color: '#eef2f7' } } },
      yAxis: {
        type: 'category',
        inverse: true,
        data: names,
        axisLabel: axisLabelStyle,
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: summary.map((s) => ({ value: s.total, itemStyle: { color: s.color } })),
          barMaxWidth: 22,
          itemStyle: { borderRadius: [0, 4, 4, 0] },
          label: {
            show: true,
            position: 'right',
            fontSize: 11,
            color: '#475569',
            formatter: (p: any) => formatNumber(p.value),
          },
        },
      ],
    }, true)
  }

  // 2) 工程別構成比（ドーナツ）
  if (processPie) {
    processPie.setOption({
      tooltip: {
        trigger: 'item',
        formatter: (p: any) => `${p.name}<br/>${formatNumber(p.value)} 本 (${p.percent}%)`,
      },
      legend: { type: 'scroll', bottom: 0, textStyle: { fontSize: 11, color: '#64748b' } },
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          center: ['50%', '44%'],
          avoidLabelOverlap: true,
          itemStyle: { borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 13, fontWeight: 'bold' } },
          data: summary
            .filter((s) => s.total > 0)
            .map((s) => ({ name: s.process_name, value: s.total, itemStyle: { color: s.color } })),
        },
      ],
    }, true)
  }

  // 3) 日別合計推移 or 工程別一日合計
  if (dailyTrend) {
    if (mode.value === 'day') {
      const names = summary.map((s) => s.process_name)
      dailyTrend.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v: number) => `${formatNumber(v)} 本` },
        grid: baseGrid,
        xAxis: { type: 'category', data: names, axisLabel: { ...axisLabelStyle, rotate: names.length > 6 ? 30 : 0 } },
        yAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: { lineStyle: { color: '#eef2f7' } } },
        series: [
          {
            type: 'bar',
            data: summary.map((s) => ({ value: s.total, itemStyle: { color: s.color } })),
            barMaxWidth: 36,
            itemStyle: { borderRadius: [4, 4, 0, 0] },
          },
        ],
      }, true)
    } else {
      const dates = dateColumns.value
      const totals = dates.map((c) => aggregated.value.reduce((s, p) => s + (p.dailyMap.get(c.key) || 0), 0))
      dailyTrend.setOption({
        tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${formatNumber(v)} 本` },
        grid: baseGrid,
        xAxis: { type: 'category', data: dates.map((c) => c.label), boundaryGap: false, axisLabel: { ...axisLabelStyle, rotate: dates.length > 15 ? 45 : 0 } },
        yAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: { lineStyle: { color: '#eef2f7' } } },
        series: [
          {
            name: '日合計',
            type: 'line',
            smooth: true,
            data: totals,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 2.5, color: '#3b82f6' },
            itemStyle: { color: '#3b82f6' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(59,130,246,0.28)' },
                { offset: 1, color: 'rgba(59,130,246,0.02)' },
              ]),
            },
          },
        ],
      }, true)
    }
  }

  // 4) 工程別日次推移（積み上げ棒）
  if (processStack) {
    const dates = dateColumns.value
    const series = aggregated.value.map((p) => ({
      name: p.process_name,
      type: 'bar',
      stack: 'total',
      data: dates.map((c) => p.dailyMap.get(c.key) || 0),
      itemStyle: { color: colorMap.value.get(p.process_cd) },
      barMaxWidth: 28,
    }))
    processStack.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { type: 'scroll', top: 0, textStyle: { fontSize: 11, color: '#64748b' } },
      grid: { ...baseGrid, top: 36 },
      xAxis: { type: 'category', data: dates.map((c) => c.label), axisLabel: { ...axisLabelStyle, rotate: dates.length > 15 ? 45 : 0 } },
      yAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: { lineStyle: { color: '#eef2f7' } } },
      series,
    }, true)
  }
}

const handleResize = () => {
  processBar?.resize()
  processPie?.resize()
  dailyTrend?.resize()
  processStack?.resize()
  processDailyLine?.resize()
}

watch(mode, () => {
  if (!loading.value) refreshChartsAfterRender()
})

watch(selectedProcessCd, () => {
  if (!loading.value) refreshChartsAfterRender()
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadProcessMaster()
  loadData()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})
</script>

<style scoped lang="scss">
$font-stack: 'Inter', 'Noto Sans JP', '游ゴシック', 'Yu Gothic', 'Meiryo', 'Microsoft YaHei', 'PingFang SC', sans-serif;
$font-num: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', sans-serif;

$primary: #3b82f6;
$primary-strong: #2563eb;
$accent: #6366f1;

$text-strong: #0f172a;
$text-base: #1e293b;
$text-soft: #475569;
$text-muted: #64748b;

$border: #e2e8f0;
$border-soft: #eef2f7;

$radius-card: 12px;
$radius-input: 8px;

$gradient-primary: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
$gradient-primary-strong: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
$gradient-surface: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);

$shadow-card: 0 1px 2px rgba(15, 23, 42, 0.04), 0 10px 24px rgba(15, 23, 42, 0.06);
$shadow-card-hover: 0 2px 4px rgba(15, 23, 42, 0.06), 0 18px 32px rgba(15, 23, 42, 0.1);
$shadow-inset-top: inset 0 1px 0 rgba(255, 255, 255, 0.8);

.process-actual {
  padding: 10px 12px 14px;
  min-height: 100vh;
  position: relative;
  font-family: $font-stack;
  font-feature-settings: 'palt' 1;
  color: $text-base;
  background:
    radial-gradient(circle at 4% 0%, rgba(59, 130, 246, 0.14), transparent 34%),
    radial-gradient(circle at 98% 8%, rgba(99, 102, 241, 0.12), transparent 32%),
    linear-gradient(145deg, #f5f8fd 0%, #eef2f9 48%, #e6ecf5 100%);

  > * {
    position: relative;
    z-index: 1;
  }

  :deep(button),
  :deep(input),
  :deep(.el-input__inner),
  :deep(.el-tag),
  :deep(.el-table) {
    font-family: inherit;
  }

  // ===== ヘッダー =====
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding: 12px 18px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
    backdrop-filter: blur(8px);
    box-shadow: $shadow-card, $shadow-inset-top;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      inset: 0 0 auto 0;
      height: 3px;
      background: linear-gradient(90deg, $primary 0%, $accent 50%, $primary 100%);
      opacity: 0.75;
    }

    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;

      .title-icon {
        width: 40px;
        height: 40px;
        border-radius: 11px;
        background: $gradient-primary;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 20px;
        box-shadow: 0 10px 18px rgba(59, 130, 246, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.5);
      }

      h1 {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        color: $text-strong;
        letter-spacing: -0.01em;
        line-height: 1.2;
      }

      p {
        margin: 2px 0 0;
        color: $text-muted;
        font-size: 12px;
      }
    }

    .page-actions {
      display: flex;
      gap: 8px;
    }

    .action-btn {
      border-radius: 8px;
      font-weight: 600;
      font-size: 12px;
      height: 30px;
      padding: 0 14px;
      background: #fff;
      border: 1px solid $border;
      color: $text-soft;
      transition: all 0.2s ease;

      &:hover {
        transform: translateY(-1px);
        color: $primary-strong;
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 0 6px 14px rgba(59, 130, 246, 0.15);
      }
    }
  }

  // ===== 検索カード =====
  .search-card {
    margin-bottom: 10px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background: $gradient-surface;
    box-shadow: $shadow-card, $shadow-inset-top;

    :deep(.el-card__body) {
      padding: 12px 16px;
    }

    .search-bar {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 22px;
    }

    .search-field {
      display: flex;
      align-items: center;
      gap: 10px;

      .field-label {
        font-size: 12px;
        font-weight: 600;
        color: $text-soft;
        white-space: nowrap;
      }
    }

    .process-field {
      .process-select {
        width: 200px;
      }
    }

    .period-field {
      margin-left: auto;

      .period-tag {
        font-weight: 600;
        font-family: $font-num;
        letter-spacing: 0.3px;
      }
    }

    .date-input-group {
      display: flex;
      align-items: center;
      gap: 8px;

      .date-picker {
        width: 180px;
      }

      .quick-buttons {
        display: inline-flex;
        padding: 2px;
        border-radius: $radius-input;
        background: #f1f5f9;
        border: 1px solid $border-soft;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);

        .date-btn {
          font-size: 12px;
          font-weight: 600;
          padding: 4px 10px;
          min-width: 46px;
          height: 26px;
          border-radius: 6px;
          border: 1px solid transparent;
          background: transparent;
          color: $text-muted;
          transition: all 0.2s ease;
          margin: 0 1px;

          &:hover {
            color: $text-base;
            background: rgba(255, 255, 255, 0.9);
          }

          &.current {
            color: #fff;
            background: $gradient-primary;
            box-shadow: 0 4px 10px rgba(59, 130, 246, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35);

            &:hover {
              background: $gradient-primary-strong;
              transform: translateY(-1px);
            }
          }
        }
      }
    }

    :deep(.mode-group .el-radio-button__inner) {
      font-weight: 600;
      padding: 7px 20px;
    }
  }

  // ===== 統計カード =====
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 10px;
    margin-bottom: 10px;

    .stat-card {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 14px;
      border: 1px solid rgba(226, 232, 240, 0.7);
      border-radius: 10px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%);
      position: relative;
      overflow: hidden;
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease, border-color 0.25s ease;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 6px 14px rgba(15, 23, 42, 0.05), $shadow-inset-top;

      &::before {
        content: '';
        position: absolute;
        inset: 0 0 auto 0;
        height: 3px;
        opacity: 0.9;
      }

      &:hover {
        transform: translateY(-3px);
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.06), 0 16px 28px rgba(15, 23, 42, 0.1), $shadow-inset-top;
        border-color: rgba(59, 130, 246, 0.3);
      }

      .stat-icon {
        width: 42px;
        height: 42px;
        border-radius: 11px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 20px;
        flex-shrink: 0;
        box-shadow: 0 6px 12px rgba(15, 23, 42, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.4);

        &.primary { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
        &.success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
        &.warning { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
        &.info { background: linear-gradient(135deg, #06b6d4 0%, #0284c7 100%); }
      }

      &:has(.stat-icon.primary)::before { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
      &:has(.stat-icon.success)::before { background: linear-gradient(90deg, #10b981, #34d399); }
      &:has(.stat-icon.warning)::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
      &:has(.stat-icon.info)::before { background: linear-gradient(90deg, #06b6d4, #38bdf8); }

      .stat-body {
        min-width: 0;
      }

      .stat-label {
        font-size: 11px;
        color: $text-muted;
        font-weight: 600;
        margin-bottom: 2px;
        letter-spacing: 0.3px;
        text-transform: uppercase;
      }

      .stat-value {
        font-size: 20px;
        font-weight: 700;
        color: $text-strong;
        display: flex;
        align-items: baseline;
        gap: 4px;
        letter-spacing: -0.02em;
        line-height: 1.1;
        font-family: $font-num;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;

        small {
          font-size: 11px;
          font-weight: 600;
          color: $text-muted;
          font-family: $font-stack;
        }
      }
    }
  }

  // ===== 工程日次折線 =====
  .process-daily-chart-card {
    margin-bottom: 10px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background: $gradient-surface;
    box-shadow: $shadow-card, $shadow-inset-top;
    transition: transform 0.2s ease, box-shadow 0.25s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow-card-hover, $shadow-inset-top;
    }

    :deep(.el-card__header) {
      padding: 10px 14px;
      border-bottom: 1px solid $border-soft;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.6) 100%);
    }

    :deep(.el-card__body) {
      padding: 8px 12px 12px;
    }

    .chart-header-meta {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .process-daily-line-chart {
      width: 100%;
      height: 320px;
      min-height: 280px;
    }
  }

  .chart-panel {
    position: relative;
    min-height: 280px;

    &--grid {
      min-height: 520px;
    }

    &__skeleton {
      position: absolute;
      inset: 0;
      z-index: 2;
      padding: 12px;
      background: rgba(255, 255, 255, 0.92);
      border-radius: 8px;
    }
  }

  // ===== チャート =====
  .chart-card,
  .table-card {
    margin-bottom: 10px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background: $gradient-surface;
    box-shadow: $shadow-card, $shadow-inset-top;
    transition: transform 0.2s ease, box-shadow 0.25s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow-card-hover, $shadow-inset-top;
    }

    :deep(.el-card__header) {
      padding: 10px 14px;
      border-bottom: 1px solid $border-soft;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.6) 100%);
    }

    :deep(.el-card__body) {
      padding: 12px 14px 14px;
    }
  }

  .chart-header,
  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .chart-title,
    .table-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      color: $text-strong;
      font-size: 13px;

      .el-icon {
        color: $primary;
        font-size: 16px;
      }
    }
  }

  .charts-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;

    .chart-item {
      background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
      border: 1px solid rgba(226, 232, 240, 0.7);
      border-radius: 10px;
      padding: 10px 12px;
      transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03), 0 4px 12px rgba(15, 23, 42, 0.04), $shadow-inset-top;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.05), 0 10px 22px rgba(15, 23, 42, 0.08), $shadow-inset-top;
        border-color: rgba(59, 130, 246, 0.3);
      }

      .chart-item-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        padding-bottom: 7px;
        border-bottom: 1px solid $border-soft;
        position: relative;

        &::before {
          content: '';
          width: 3px;
          height: 14px;
          border-radius: 2px;
          background: $gradient-primary;
          box-shadow: 0 2px 6px rgba(59, 130, 246, 0.35);
        }

        .chart-item-title {
          font-weight: 700;
          color: $text-strong;
          font-size: 12px;
          letter-spacing: 0.3px;
        }
      }

      .chart-container {
        width: 100%;
        height: 260px;
      }
    }
  }

  // ===== テーブル =====
  .data-table {
    border-radius: 8px;
    overflow: hidden;

    :deep(.el-table__header th) {
      background: #f8fafc;
      color: $text-soft;
      font-weight: 700;
      font-size: 12px;
    }

    .process-cell {
      display: flex;
      align-items: center;
      gap: 8px;

      .color-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
      }

      .process-name {
        font-weight: 600;
        color: $text-strong;
        font-size: 13px;
      }
    }

    .quantity {
      font-family: $font-num;
      font-variant-numeric: tabular-nums;
      font-weight: 700;
      color: $text-strong;

      &.row-total {
        color: $primary-strong;
      }
    }

    .unit {
      font-size: 11px;
      color: $text-muted;
      margin-left: 2px;
    }

    .cell-zero {
      color: #cbd5e1;
    }

    .ratio-cell {
      display: flex;
      align-items: center;
      gap: 10px;

      .ratio-bar {
        flex: 1;
      }

      .ratio-text {
        font-family: $font-num;
        font-weight: 700;
        font-size: 12px;
        color: $text-soft;
        min-width: 46px;
        text-align: right;
      }
    }
  }

  .matrix-table {
    :deep(.el-table__footer) {
      font-weight: 700;
    }
  }
}

// ===== トランジション =====
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
