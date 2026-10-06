<template>
  <div class="order-destination-history odh-modern pb-std">
    <div class="page-shell">
      <!-- 页头 -->
      <header class="hero-panel pb-hero pb-hero--page">
        <div class="hero-fx pb-bubbles" aria-hidden="true" />
        <div class="hero-top">
          <div class="title-block">
            <div class="title-icon" aria-hidden="true">
              <el-icon><OfficeBuilding /></el-icon>
            </div>
            <div class="title-text">
              <h1 class="page-title pb-hero-title">納入先別受注履歴</h1>
              <p class="page-subtitle pb-hero-desc">納入先ごとの受注データ分析・履歴管理</p>
            </div>
          </div>
          <div class="hero-meta">
            <span v-if="selectedDestinationName" class="hero-chip">
              <el-icon><OfficeBuilding /></el-icon>
              {{ selectedDestinationName }}
            </span>
            <span v-if="filters.date_range?.length === 2" class="hero-chip">
              <el-icon><Calendar /></el-icon>
              {{ filters.date_range[0] }} ～ {{ filters.date_range[1] }}
            </span>
            <div v-if="orderList.length > 0" class="hero-badge">
              <span class="badge-label">結果</span>
              <span class="badge-value">{{ filteredOrderList.length }}件</span>
            </div>
          </div>
        </div>
      </header>

      <!-- 筛选：ヒーローの下に独立カード -->
      <section class="filter-strip">
        <div class="filter-strip-label">
          <el-icon class="filter-icon"><Search /></el-icon>
          <span>条件</span>
        </div>
        <el-form :inline="true" class="modern-filter-form" @submit.prevent>
          <div class="filter-row">
            <el-form-item class="filter-item">
              <template #label>
                <div class="custom-label">
                  <el-icon><OfficeBuilding /></el-icon>
                  <span>納入先</span>
                </div>
              </template>
              <el-select
                v-model="filters.destination_cd"
                placeholder="納入先を選択"
                clearable
                filterable
                class="select-input"
              >
                <el-option
                  v-for="item in destinationOptions"
                  :key="item.cd"
                  :label="`${item.cd} - ${item.name}`"
                  :value="item.cd"
                />
              </el-select>
            </el-form-item>

            <el-form-item class="filter-item">
              <template #label>
                <div class="custom-label">
                  <el-icon><Calendar /></el-icon>
                  <span>期間</span>
                </div>
              </template>
              <el-date-picker
                v-model="filters.date_range"
                type="daterange"
                range-separator="～"
                start-placeholder="開始日"
                end-placeholder="終了日"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                class="date-picker"
                clearable
              />
              <div class="month-quick">
                <el-button
                  v-for="m in MONTH_SHORTCUTS"
                  :key="m.offset"
                  size="small"
                  :class="['month-btn', { 'is-active': isMonthRangeActive(m.offset) }]"
                  @click="setMonthRange(m.offset)"
                >
                  {{ m.label }}
                </el-button>
              </div>
            </el-form-item>

            <div class="filter-actions">
              <el-button type="primary" @click="fetchData" class="search-btn" :loading="isFetching">
                <el-icon><Search /></el-icon>
                検索
              </el-button>
            </div>
          </div>
        </el-form>
      </section>

      <!-- KPI（検索結果サマリ） -->
      <section v-if="filteredOrderList.length > 0" class="kpi-strip">
        <article class="kpi-card kpi-card--rows">
          <div class="kpi-icon"><el-icon><List /></el-icon></div>
          <div class="kpi-body">
            <div class="kpi-value">{{ filteredOrderList.length.toLocaleString() }}</div>
            <div class="kpi-label">明細件数</div>
          </div>
        </article>
        <article class="kpi-card kpi-card--qty">
          <div class="kpi-icon"><el-icon><Box /></el-icon></div>
          <div class="kpi-body">
            <div class="kpi-value">{{ totalQuantity.toLocaleString() }}<small>個</small></div>
            <div class="kpi-label">受注数量合計</div>
          </div>
        </article>
        <article class="kpi-card kpi-card--products">
          <div class="kpi-icon"><el-icon><Goods /></el-icon></div>
          <div class="kpi-body">
            <div class="kpi-value">{{ productCount.toLocaleString() }}</div>
            <div class="kpi-label">製品種類</div>
          </div>
        </article>
        <article class="kpi-card kpi-card--avg">
          <div class="kpi-icon"><el-icon><TrendCharts /></el-icon></div>
          <div class="kpi-body">
            <div class="kpi-value">{{ monthlyAverage.toLocaleString() }}<small>個</small></div>
            <div class="kpi-label">月平均数量</div>
          </div>
        </article>
      </section>

      <div class="content-grid">
        <!-- 月別集計 -->
        <section class="summary-section panel-card">
          <div class="section-header">
            <div class="section-title">
              <el-icon class="section-icon"><TrendCharts /></el-icon>
              <span>月別集計</span>
            </div>
            <div class="summary-stats" v-if="summaryList.length > 0">
              <div class="stat-chip">
                <span class="stat-label">期間</span>
                <span class="stat-value">{{ summaryList.length }}ヶ月</span>
              </div>
            </div>
          </div>

          <div class="modern-table-container">
            <el-table
              :data="summaryList"
              class="modern-table summary-table"
              stripe
              :height="isFillLayout ? '100%' : undefined"
              :max-height="isFillLayout ? undefined : SUMMARY_TABLE_MAX_HEIGHT"
            >
              <el-table-column label="年月" prop="ym" width="96" align="center">
                <template #header>
                  <div class="table-header">
                    <el-icon>
                      <Calendar />
                    </el-icon>
                    <span>年月</span>
                  </div>
                </template>
                <template #default="{ row }">
                  <div class="date-cell">
                    {{ row.ym }}
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="受注数量合計" prop="total_quantity" min-width="124" align="right">
                <template #header>
                  <div class="table-header">
                    <el-icon>
                      <Box />
                    </el-icon>
                    <span>受注数量合計</span>
                  </div>
                </template>
                <template #default="{ row }">
                  <div class="number-cell quantity">
                    <span class="number">{{ row.total_quantity?.toLocaleString() }}</span>
                    <span class="unit">個</span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="構成比" min-width="130">
                <template #default="{ row }">
                  <div class="qty-bar">
                    <span class="qty-bar__track">
                      <span
                        class="qty-bar__fill"
                        :style="{ width: `${summaryMax ? (row.total_quantity / summaryMax) * 100 : 0}%` }"
                      />
                    </span>
                    <span class="qty-bar__pct">
                      {{ totalQuantity ? ((row.total_quantity / totalQuantity) * 100).toFixed(1) : '0.0' }}%
                    </span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>

        <!-- 受注明細 -->
        <section class="details-section panel-card">
          <div class="section-header">
            <div class="section-title">
              <el-icon class="section-icon"><List /></el-icon>
              <span>受注明細</span>
            </div>

            <div class="section-actions">
              <div class="details-stats" v-if="filteredOrderList.length > 0">
                <div class="stat-chip">
                  <span class="stat-label">明細</span>
                  <span class="stat-value">{{ filteredOrderList.length }}件</span>
                </div>
              </div>

              <el-button class="print-btn" @click="handlePrint">
                <el-icon><Printer /></el-icon>
                印刷
              </el-button>
            </div>
          </div>

          <div class="modern-table-container modern-table-container--details">
            <el-table
              v-loading="isFetching"
              :data="filteredOrderList"
              class="modern-table details-table"
              stripe
              :height="isFillLayout ? '100%' : DETAILS_TABLE_HEIGHT"
            >
              <el-table-column label="出荷日" prop="date" width="108" align="center">
                <template #header>
                  <div class="table-header">
                    <el-icon>
                      <Calendar />
                    </el-icon>
                    <span>出荷日</span>
                  </div>
                </template>
                <template #default="{ row }">
                  <div class="date-cell">
                    {{ row.date }}
                  </div>
                </template>
              </el-table-column>

              <el-table-column
                label="納入先名"
                prop="destination_name"
                min-width="140"
                align="center"
                show-overflow-tooltip
              >
                <template #header>
                  <div class="table-header">
                    <el-icon>
                      <OfficeBuilding />
                    </el-icon>
                    <span>納入先名</span>
                  </div>
                </template>
                <template #default="{ row }">
                  <div class="name-cell">
                    {{ row.destination_name }}
                  </div>
                </template>
              </el-table-column>

              <el-table-column
                label="製品名"
                prop="product_name"
                min-width="150"
                align="center"
                show-overflow-tooltip
              >
                <template #header>
                  <div class="table-header">
                    <el-icon>
                      <List />
                    </el-icon>
                    <span>製品名</span>
                  </div>
                </template>
                <template #default="{ row }">
                  <div class="name-cell">
                    {{ row.product_name }}
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="数量" prop="quantity" width="112" align="right">
                <template #header>
                  <div class="table-header">
                    <el-icon>
                      <Box />
                    </el-icon>
                    <span>数量</span>
                  </div>
                </template>
                <template #default="{ row }">
                  <div class="number-cell quantity">
                    <span class="number">{{ row.quantity?.toLocaleString() }}</span>
                    <span class="unit">個</span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="状態" prop="status" width="100" align="center">
                <template #header>
                  <div class="table-header">
                    <el-icon>
                      <TrendCharts />
                    </el-icon>
                    <span>状態</span>
                  </div>
                </template>
                <template #default="{ row }">
                  <div class="status-cell">
                    <el-tag :class="getStatusClass(row.status)" class="status-tag">
                      {{ row.status || '-' }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="納入日" prop="delivery_date" width="108" align="center">
                <template #header>
                  <div class="table-header">
                    <el-icon>
                      <Calendar />
                    </el-icon>
                    <span>納入日</span>
                  </div>
                </template>
                <template #default="{ row }">
                  <div class="date-cell">
                    {{ row.delivery_date || '-' }}
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Calendar,
  List,
  OfficeBuilding,
  Printer,
  Search,
  TrendCharts,
  Box,
  Goods,
} from '@element-plus/icons-vue'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { fetchOrderDailyList } from '@/api/erp/orderDaily'
import { getJSTToday } from '@/utils/dateFormat'
import { useSalesOperationPermission } from '@/composables/useSalesOperationPermission'
import { guardSalesOperation } from '@/utils/salesOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useSalesOperationPermission()


type DestinationOption = { cd: string; name: string }

interface DestinationOrderHistoryItem {
  date: string
  destination_cd: string
  destination_name: string
  product_cd: string
  product_name: string
  quantity: number
  status: string
  delivery_date: string
  ym: string
}

const filters = reactive<{
  destination_cd: string
  date_range: string[]
}>({
  destination_cd: '',
  date_range: [],
})

const destinationOptions = ref<DestinationOption[]>([])
const orderList = ref<DestinationOrderHistoryItem[]>([])

const isFetching = ref(false)

/** 縦積みレイアウト時のテーブル高さ（表頭固定・表体は縦スクロール） */
const DETAILS_TABLE_HEIGHT = 480
const SUMMARY_TABLE_MAX_HEIGHT = 320

/** CSS の全画面レイアウト用メディアクエリと同じ条件にすること */
const FILL_LAYOUT_QUERY = '(min-width: 1280px) and (min-height: 640px)'
const isFillLayout = ref(false)
let fillLayoutMql: MediaQueryList | null = null

function syncFillLayout() {
  isFillLayout.value = !!fillLayoutMql?.matches
}

const filteredOrderList = computed(() => {
  // 界面与打印逻辑保持一致：只显示“数量 > 0”的记录
  return orderList.value.filter((o) => o.quantity > 0)
})

const summaryList = computed(() => {
  const map = new Map<string, number>()
  for (const item of filteredOrderList.value) {
    map.set(item.ym, (map.get(item.ym) ?? 0) + item.quantity)
  }
  const rows = [...map.entries()].map(([ym, total_quantity]) => ({
    ym,
    total_quantity,
  }))
  rows.sort((a, b) => a.ym.localeCompare(b.ym))
  return rows
})

const totalQuantity = computed(() =>
  filteredOrderList.value.reduce((sum, o) => sum + (o.quantity || 0), 0),
)

const productCount = computed(
  () => new Set(filteredOrderList.value.map((o) => o.product_cd || o.product_name)).size,
)

const monthlyAverage = computed(() =>
  summaryList.value.length ? Math.round(totalQuantity.value / summaryList.value.length) : 0,
)

const summaryMax = computed(() =>
  summaryList.value.reduce((max, r) => Math.max(max, r.total_quantity), 0),
)

const MONTH_SHORTCUTS = [
  { label: '前月', offset: -1 },
  { label: '今月', offset: 0 },
  { label: '来月', offset: 1 },
] as const

function getMonthRangeJST(offset: number): string[] {
  const [year, month] = getJSTToday().split('-').map(Number)
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return [fmt(new Date(year, month - 1 + offset, 1)), fmt(new Date(year, month + offset, 0))]
}

function isMonthRangeActive(offset: number) {
  const [start, end] = filters.date_range || []
  const [monthStart, monthEnd] = getMonthRangeJST(offset)
  return start === monthStart && end === monthEnd
}

function setMonthRange(offset: number) {
  filters.date_range = getMonthRangeJST(offset)
  fetchData()
}

const selectedDestinationName = computed(() => {
  const cd = filters.destination_cd
  if (!cd) return ''
  const opt = destinationOptions.value.find((d) => d.cd === cd)
  return opt ? opt.name || opt.cd : cd
})

function getStatusClass(status: string) {
  const s = status || ''
  switch (s) {
    case '完了':
      return 'status-completed'
    case 'キャンセル':
      return 'status-cancelled'
    case '処理中':
      return 'status-processing'
    default:
      return 'status-default'
  }
}

async function loadOptions() {
  destinationOptions.value = await getDestinationOptions()
}

async function fetchData() {
  if (!filters.destination_cd) return
  if (!filters.date_range || filters.date_range.length !== 2) return

  const [start_date, end_date] = filters.date_range

  isFetching.value = true
  try {
    const rows = await fetchOrderDailyList({
      start_date,
      end_date,
      destination_cd: filters.destination_cd,
    })

    orderList.value = (rows ?? []).map((r) => {
      const date = r.date
      const ym = date ? date.slice(0, 7) : ''
      return {
        date,
        destination_cd: r.destination_cd,
        destination_name: r.destination_name || r.destination_cd,
        product_cd: r.product_cd,
        product_name: r.product_name || r.product_cd,
        quantity: Number(r.confirmed_units ?? 0),
        status: r.status || '',
        delivery_date: r.delivery_date || '',
        ym,
      }
    })
  } catch (e: any) {
    const msg = e?.message ?? 'データ取得に失敗しました'
    ElMessage.error(msg)
  } finally {
    isFetching.value = false
  }
}

function escapeHtml(s: string) {
  return (s ?? '')
    .toString()
    .split('&')
    .join('&amp;')
    .split('<')
    .join('&lt;')
    .split('>')
    .join('&gt;')
    .split('"')
    .join('&quot;')
    .split("'")
    .join('&#039;')
}

function formatPrintTime() {
  if (!guardSalesOperation(canExport)) return

  const d = new Date()
  return d.toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function build2DTableHtml(list: DestinationOrderHistoryItem[]) {
  const products = [...new Set(list.map((x) => x.product_name))].sort((a, b) => a.localeCompare(b, 'ja'))
  const dates = [...new Set(list.map((x) => x.date))].sort()

  const qtyMap = new Map<string, number>()
  const dateTotals = new Map<string, number>()

  for (const item of list) {
    const key = `${item.product_name}__${item.date}`
    qtyMap.set(key, (qtyMap.get(key) ?? 0) + item.quantity)
    dateTotals.set(item.date, (dateTotals.get(item.date) ?? 0) + item.quantity)
  }

  let html = '<table class="table-2d">'
  html += '<thead><tr>'
  html += '<th>製品名</th>'
  for (const date of dates) {
    html += `<th class="date-header">${escapeHtml(date)}</th>`
  }
  html += '<th>合計</th>'
  html += '</tr></thead>'
  html += '<tbody>'

  let grandTotal = 0

  for (const product of products) {
    let productTotal = 0
    html += `<tr><td class="product-name">${escapeHtml(product)}</td>`

    for (const date of dates) {
      const key = `${product}__${date}`
      const qty = qtyMap.get(key) ?? 0
      productTotal += qty
      html += `<td class="number">${qty > 0 ? qty.toLocaleString() : ''}</td>`
    }

    grandTotal += productTotal
    html += `<td class="number total">${productTotal.toLocaleString()}</td></tr>`
  }

  html += '<tr class="total-row">'
  html += '<td class="total-label">合計</td>'
  let dateGrandSum = 0
  for (const date of dates) {
    const dateTotal = dateTotals.get(date) ?? 0
    dateGrandSum += dateTotal
    html += `<td class="number total">${dateTotal > 0 ? dateTotal.toLocaleString() : ''}</td>`
  }
  html += `<td class="number grand-total">${(grandTotal ?? dateGrandSum).toLocaleString()}</td>`
  html += '</tr>'

  html += '</tbody></table>'
  return html
}

async function handlePrint() {
  if (!guardSalesOperation(canExport)) return

  const listToPrint = filteredOrderList.value
  if (listToPrint.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  const loadingMessage = ElMessage({
    message: '印刷データを準備中...',
    type: 'info',
    duration: 0,
    showClose: false,
  })

  try {
    const filterInfo: string[] = []
    if (filters.date_range?.length === 2) {
      filterInfo.push(`期間: ${filters.date_range[0]} ~ ${filters.date_range[1]}`)
    }
    if (filters.destination_cd) {
      const dest = destinationOptions.value.find((d) => d.cd === filters.destination_cd)
      filterInfo.push(`納入先: ${dest ? `${dest.cd} - ${dest.name}` : filters.destination_cd}`)
    }

    const filterText =
      filterInfo.length > 0 ? `<div class="filter-info">検索条件: ${filterInfo.join(' / ')}</div>` : ''

    const summaryHtml = `
      <table class="summary-table">
        <thead>
          <tr>
            <th>年月</th>
            <th>受注数量合計</th>
          </tr>
        </thead>
        <tbody>
          ${summaryList.value
            .map(
              (item) => `
              <tr>
                <td class="center">${escapeHtml(item.ym)}</td>
                <td class="number">${(item.total_quantity ?? 0).toLocaleString()}</td>
              </tr>
            `,
            )
            .join('')}
        </tbody>
      </table>
    `

    const printWindow = window.open('', '', 'width=1000,height=900')
    if (!printWindow) {
      loadingMessage.close()
      ElMessage.error('印刷ウィンドウを開けません')
      return
    }

    const listHtml = `
      <table class="list-table">
        <thead>
          <tr>
            <th>出荷日</th>
            <th>納入先名</th>
            <th>製品名</th>
            <th>数量</th>
            <th>状態</th>
            <th>納入日</th>
          </tr>
        </thead>
        <tbody>
          ${listToPrint
            .map(
              (item) => `
              <tr>
                <td class="center">${escapeHtml(item.date)}</td>
                <td>${escapeHtml(item.destination_name)}</td>
                <td>${escapeHtml(item.product_name)}</td>
                <td class="number">${(item.quantity ?? 0).toLocaleString()}</td>
                <td>${escapeHtml(item.status || '-')}</td>
                <td class="center">${escapeHtml(item.delivery_date || '-')}</td>
              </tr>
            `,
            )
            .join('')}
        </tbody>
      </table>
    `

    printWindow.document.write(`
      <html>
        <head>
          <title>納入先別受注履歴</title>
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
              font-family: "Yu Gothic", "Hiragino Kaku Gothic Pro", "Meiryo", sans-serif;
              padding: 10px 12px;
              color: #000;
              font-size: 11px;
              line-height: 1.2;
            }
            .print-info {
              text-align: right;
              font-size: 9.5px;
              margin-bottom: 8px;
            }
            h2 {
              text-align: center;
              font-size: 16px;
              margin-bottom: 10px;
              padding-bottom: 6px;
              border-bottom: 1px solid #000;
            }
            .filter-info {
              margin: 4px 0 10px;
              padding: 4px 6px;
              background: #f8f9fa;
              border-radius: 2px;
              font-size: 9.5px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-bottom: 10px;
            }
            th, td {
              border: 1px solid #000;
              padding: 3px 4px;
              text-align: center;
              vertical-align: middle;
            }
            th {
              background: #f0f0f0;
              font-weight: bold;
              font-size: 9px;
            }
            .table-2d th { font-size: 8px; background: #e6e6e6; }
            .table-2d td { font-size: 8.5px; }
            .date-header {
              writing-mode: vertical-rl;
              text-orientation: mixed;
              width: 24px;
            }
            .product-name {
              text-align: left;
              font-weight: bold;
              max-width: 160px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
            .number { font-family: 'Courier New', monospace; text-align: right; }
            .total { background: #f8f8f8; font-weight: bold; }
            .total-row td { background: #e8e8e8; font-weight: bold; }
            .summary-table th, .summary-table td { font-size: 9px; }
            .list-table th, .list-table td { font-size: 9.5px; }
            .center { text-align: center; }
            @media print {
              body { padding: 6px; }
              tr { page-break-inside: avoid; }
            }
          </style>
        </head>
        <body>
          <div class="print-info">印刷日時: ${formatPrintTime()}</div>
          <h2>納入先別受注履歴</h2>
          ${filterText}
          <h3>月別集計</h3>
          ${summaryHtml}
          <h3>出荷明細（二次元表）</h3>
          ${build2DTableHtml(listToPrint)}
          <h3>出荷明細（一覧表）</h3>
          ${listHtml}
        </body>
      </html>
    `)

    printWindow.document.close()
    printWindow.focus()
    printWindow.print()
    printWindow.close()

    loadingMessage.close()
    ElMessage.success('印刷データの準備が完了しました')
  } catch (e) {
    loadingMessage.close()
    ElMessage.error('印刷データの準備中にエラーが発生しました')
  }
}

onMounted(async () => {
  fillLayoutMql = window.matchMedia(FILL_LAYOUT_QUERY)
  syncFillLayout()
  fillLayoutMql.addEventListener('change', syncFillLayout)
  try {
    await loadOptions()
  } catch {
    destinationOptions.value = []
  }
})

onBeforeUnmount(() => {
  fillLayoutMql?.removeEventListener('change', syncFillLayout)
  fillLayoutMql = null
})
</script>

<style scoped>
.order-destination-history {
  --odh-accent: #4f46e5;
  --odh-accent-2: #7c3aed;
  --odh-surface: #ffffff;
  --odh-border: rgba(15, 23, 42, 0.08);
  --odh-text: #0f172a;
  --odh-muted: #64748b;

  min-height: auto;
  background: linear-gradient(165deg, #eef2ff 0%, #f8fafc 42%, #f1f5f9 100%);
  padding: 10px 12px 14px;
  position: relative;
}

.page-shell {
  max-width: 1480px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hero-panel {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--odh-border);
  background: linear-gradient(135deg, #312e81 0%, var(--odh-accent) 48%, var(--odh-accent-2) 100%);
  box-shadow:
    0 10px 30px rgba(79, 70, 229, 0.22),
    0 1px 0 rgba(255, 255, 255, 0.12) inset;
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px 10px;
}

.title-block {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.title-icon {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.16);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
}

.title-icon .el-icon {
  font-size: 20px;
  color: #fff;
}

.title-text {
  color: #fff;
  min-width: 0;
}

.page-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  color: #fff;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.page-subtitle {
  font-size: 0.8rem;
  margin: 2px 0 0;
  opacity: 0.88;
  font-weight: 400;
  line-height: 1.35;
}

.hero-badge {
  flex-shrink: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(8px);
}

.badge-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.78);
}

.badge-value {
  font-size: 0.85rem;
  font-weight: 700;
  color: #fff;
  font-variant-numeric: tabular-nums;
}

.filter-strip {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 10px 12px 12px;
  background: rgba(255, 255, 255, 0.1);
  border-top: 1px solid rgba(255, 255, 255, 0.14);
}

.filter-strip-label {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.8rem;
  font-weight: 600;
  background: rgba(15, 23, 42, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.filter-strip-label .filter-icon {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
}

.modern-filter-form {
  flex: 1;
  min-width: 0;
  margin: 0;
}

.filter-row {
  display: flex;
  align-items: flex-end;
  gap: 10px 14px;
  flex-wrap: wrap;
}

.filter-item {
  margin-bottom: 0;
}

.custom-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  margin-bottom: 4px;
  font-size: 0.78rem;
  letter-spacing: 0.01em;
}

.custom-label .el-icon {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.88);
}

::deep(.filter-strip .el-form-item__label) {
  padding: 0;
  margin-right: 0;
}

::deep(.filter-strip .el-form-item) {
  margin-right: 0;
  margin-bottom: 0;
}

::deep(.filter-strip .el-input__wrapper),
::deep(.filter-strip .el-select .el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.35) inset;
}

::deep(.filter-strip .el-range-editor.el-input__wrapper) {
  border-radius: 10px;
}

.select-input {
  width: min(260px, 100%);
}

.date-picker {
  width: min(300px, 100%);
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-left: auto;
}

.search-btn {
  border: none;
  color: #fff;
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.82rem;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    background 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(15, 23, 42, 0.28);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
}

.search-btn:hover {
  background: rgba(15, 23, 42, 0.38);
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.22);
}

.panel-card {
  background: var(--odh-surface);
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid var(--odh-border);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.summary-section,
.details-section {
  margin: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  padding: 0 2px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--odh-text);
  letter-spacing: -0.01em;
}

.section-icon {
  font-size: 16px;
  color: var(--odh-accent);
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.summary-stats,
.details-stats {
  display: flex;
  gap: 8px;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eef2ff;
  border: 1px solid rgba(79, 70, 229, 0.18);
}

.stat-label {
  font-size: 0.7rem;
  color: var(--odh-muted);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.stat-value {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--odh-accent);
  font-variant-numeric: tabular-nums;
}

.modern-table-container {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--odh-border);
  background: #fafafa;
}

.modern-table-container--details {
  overflow: hidden;
}

.modern-table {
  border: none;
  --el-table-border-color: transparent;
}

::deep(.modern-table .el-table__header) {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

::deep(.modern-table .el-table__header th) {
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--odh-border);
  padding: 8px 8px;
  color: var(--odh-text);
  font-weight: 700;
  font-size: 0.8rem;
  text-align: center;
}

::deep(.modern-table .el-table__body td) {
  border: none;
  padding: 7px 8px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  font-size: 0.8125rem;
}

::deep(.modern-table .el-table__body tr:hover > td) {
  background: rgba(79, 70, 229, 0.04) !important;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  font-weight: 700;
}

.table-header .el-icon {
  font-size: 13px;
  color: var(--odh-accent);
}

.date-cell {
  font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-weight: 600;
  color: var(--odh-accent);
  text-align: center;
  font-size: 0.78rem;
}

.name-cell {
  font-weight: 500;
  color: var(--odh-text);
  font-size: 0.78rem;
  text-align: center;
}

.number-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Code', monospace;
}

.number-cell .number {
  font-weight: 700;
  font-size: 0.78rem;
}

.number-cell .unit {
  font-size: 0.7rem;
  opacity: 0.65;
  font-weight: 600;
}

.number-cell.quantity {
  color: #047857;
}

.status-cell {
  display: flex;
  justify-content: center;
}

.status-tag {
  border: none;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 0.72rem;
  transition: transform 0.15s ease;
}

.status-tag:hover {
  transform: translateY(-1px);
}

.status-completed {
  background: linear-gradient(180deg, #34d399, #10b981);
  color: white;
}

.status-cancelled {
  background: linear-gradient(180deg, #fb7185, #ef4444);
  color: white;
}

.status-processing {
  background: linear-gradient(180deg, #fbbf24, #f59e0b);
  color: white;
}

.status-default {
  background: #64748b;
  color: white;
}

.print-btn {
  border: 1px solid rgba(79, 70, 229, 0.35);
  color: var(--odh-accent);
  background: #fff;
  padding: 7px 12px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.8rem;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    background 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.print-btn:hover {
  background: #eef2ff;
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(79, 70, 229, 0.15);
}

@media (max-width: 1200px) {
  .order-destination-history {
    padding: 8px 10px 12px;
  }

  .page-shell {
    gap: 8px;
  }

  .panel-card {
    padding: 9px 10px;
  }
}

@media (max-width: 768px) {
  .hero-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-strip {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-strip-label {
    width: fit-content;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-actions {
    margin-left: 0;
    justify-content: stretch;
  }

  .search-btn {
    width: 100%;
    justify-content: center;
  }

  .select-input,
  .date-picker {
    width: 100%;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .section-actions {
    width: 100%;
    justify-content: space-between;
  }
}

/* ============================================================
 * 页面美化：現代UI・色分け・レスポンシブ全画面（納入先別受注履歴 / 受注 = indigo→violet）
 * ============================================================ */

/* ---------- ページ骨格：コンテンツ領域いっぱいに広げる ---------- */
.order-destination-history.odh-modern {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 8px;
  background:
    radial-gradient(1000px 360px at 0% 0%, rgba(99, 102, 241, 0.1), transparent 60%),
    radial-gradient(900px 360px at 100% 0%, rgba(139, 92, 246, 0.08), transparent 60%),
    #f4f5fb;
}

.odh-modern .page-shell {
  flex: 1 1 auto;
  width: 100%;
  max-width: none;
  min-height: 0;
  margin: 0;
  gap: 8px;
}

/* ---------- ヒーロー ---------- */
.odh-modern .hero-panel {
  position: relative;
  flex-shrink: 0;
  border: none;
  border-radius: 14px;
  background: linear-gradient(125deg, #312e81 0%, #4338ca 34%, #6d28d9 70%, #8b5cf6 100%);
  box-shadow:
    0 12px 28px -18px rgba(76, 29, 149, 0.6),
    0 1px 2px rgba(15, 23, 42, 0.06);
}

.odh-modern .hero-top {
  flex-wrap: wrap;
  padding: 0;
}

.odh-modern .title-block {
  gap: 12px;
}

.odh-modern .title-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.42);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(30, 27, 75, 0.3);
}

.odh-modern .title-icon .el-icon {
  font-size: 20px;
}

.odh-modern .title-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.odh-modern .page-title {
  font-weight: 800;
  letter-spacing: 0.04em;
}

.odh-modern .page-subtitle {
  opacity: 1;
  color: rgba(255, 255, 255, 0.86);
  letter-spacing: 0.02em;
}

.odh-modern .hero-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.odh-modern .hero-chip,
.odh-modern .hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.odh-modern .badge-label {
  font-size: 11px;
  letter-spacing: 0.02em;
  text-transform: none;
}

.odh-modern .badge-value {
  font-size: 12px;
}

/* ---------- 絞り込み（独立カード） ---------- */
.odh-modern .filter-strip {
  position: relative;
  flex-shrink: 0;
  overflow: hidden;
  align-items: center;
  gap: 12px;
  padding: 10px 12px 8px;
  border-radius: 12px;
  border: 1px solid #e0e7ff;
  border-top: 1px solid #e0e7ff;
  background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(67, 56, 202, 0.45);
}

.odh-modern .filter-strip::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 60%, #a78bfa 100%);
}

.odh-modern .filter-strip-label {
  padding: 0 12px;
  height: 30px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  border: 1px solid #4338ca;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -2px 0 rgba(49, 46, 129, 0.3);
}

.odh-modern .filter-strip-label .filter-icon {
  color: #fff;
}

.odh-modern .filter-row {
  align-items: center;
}

.odh-modern .filter-item {
  margin: 0;
}

.odh-modern .filter-item :deep(.el-form-item__label) {
  height: auto;
  padding: 0 8px 0 0;
  line-height: 1;
}

.odh-modern .custom-label {
  height: 22px;
  margin-bottom: 0;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 700;
  color: #3730a3;
  border-radius: 999px;
  background: #eef2ff;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #c7d2fe;
}

.odh-modern .custom-label .el-icon {
  color: #4f46e5;
}

/* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
.odh-modern .filter-strip :deep(.el-input__wrapper),
.odh-modern .filter-strip :deep(.el-select__wrapper) {
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 0 0 1px #d6dcf5 inset;
}

.odh-modern .filter-strip :deep(.el-input__wrapper:hover),
.odh-modern .filter-strip :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #a5b4fc inset;
}

.odh-modern .filter-strip :deep(.el-input__wrapper.is-active),
.odh-modern .filter-strip :deep(.el-input__wrapper.is-focus),
.odh-modern .filter-strip :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #6366f1 inset,
    0 0 0 3px rgba(99, 102, 241, 0.14);
}

/* ---------- ボタン：軽い立体（影・動きは共通ボタン標準） ---------- */
.odh-modern .search-btn {
  --k-rgb: 79 70 229;
  height: 32px;
  padding: 0 16px;
  color: #fff;
  font-weight: 700;
  border: 1px solid #4338ca;
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
}

.odh-modern .search-btn:not(.is-disabled):hover,
.odh-modern .search-btn:focus-visible {
  color: #fff;
  border-color: #4338ca;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
}

.odh-modern .print-btn {
  --k-rgb: 79 70 229;
  height: 28px;
  padding: 0 12px;
  font-weight: 700;
  color: #4338ca;
  border: 1px solid #c7d2fe;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #f5f7ff 100%);
}

.odh-modern .print-btn:not(.is-disabled):hover,
.odh-modern .print-btn:focus-visible {
  color: #3730a3;
  border-color: #a5b4fc;
  background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
}

/* 期間の月ショートカット（前月・今月・来月） */
.odh-modern .month-quick {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: 6px;
}

.odh-modern .month-quick .month-btn {
  --k-rgb: 79 70 229;
  height: 28px;
  margin-left: 0;
  padding: 0 11px;
  font-weight: 700;
  color: #4338ca;
  border: 1px solid #c7d2fe;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #f5f7ff 100%);
}

.odh-modern .month-quick .month-btn:not(.is-disabled):hover,
.odh-modern .month-quick .month-btn:focus-visible {
  color: #3730a3;
  border-color: #a5b4fc;
  background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
}

.odh-modern .month-quick .month-btn.is-active,
.odh-modern .month-quick .month-btn.is-active:hover,
.odh-modern .month-quick .month-btn.is-active:focus-visible {
  color: #fff;
  border-color: #4338ca;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
}

/* ---------- KPIカード（色分け・動きなし） ---------- */
.odh-modern .kpi-strip {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.odh-modern .kpi-card {
  --kpi: #4f46e5;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--kpi) 18%, #e2e8f0);
  background: linear-gradient(160deg, color-mix(in srgb, var(--kpi) 7%, #fff) 0%, #fff 70%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 18px -16px color-mix(in srgb, var(--kpi) 70%, transparent);
}

.odh-modern .kpi-card--qty { --kpi: #059669; }
.odh-modern .kpi-card--products { --kpi: #d97706; }
.odh-modern .kpi-card--avg { --kpi: #7c3aed; }

.odh-modern .kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--kpi) 45%, #fff), var(--kpi));
}

.odh-modern .kpi-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  font-size: 16px;
  color: #fff;
  background: linear-gradient(145deg, color-mix(in srgb, var(--kpi) 60%, #fff) 0%, var(--kpi) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 23, 42, 0.15),
    0 4px 10px -4px color-mix(in srgb, var(--kpi) 70%, transparent);
}

.odh-modern .kpi-body {
  min-width: 0;
}

.odh-modern .kpi-value {
  font-size: 19px;
  font-weight: 800;
  line-height: 1.15;
  color: color-mix(in srgb, var(--kpi) 40%, #0f172a);
  font-variant-numeric: tabular-nums;
}

.odh-modern .kpi-value small {
  margin-left: 3px;
  font-size: 11px;
  font-weight: 700;
  opacity: 0.6;
}

.odh-modern .kpi-label {
  margin-top: 1px;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}

/* ---------- 月別集計・受注明細（左右 2 カラム） ---------- */
.odh-modern .content-grid {
  display: grid;
  grid-template-columns: minmax(340px, 28%) minmax(0, 1fr);
  gap: 8px;
  flex: 1 1 auto;
  min-height: 0;
}

.odh-modern .panel-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  padding: 10px 10px 8px;
  border-radius: 12px;
  border: 1px solid #e0e7ff;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(67, 56, 202, 0.45);
}

.odh-modern .panel-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  pointer-events: none;
}

.odh-modern .summary-section::before {
  background: linear-gradient(90deg, #10b981 0%, #14b8a6 100%);
}

.odh-modern .details-section::before {
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 60%, #a78bfa 100%);
}

.odh-modern .section-header {
  flex-shrink: 0;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.odh-modern .section-title {
  gap: 8px;
  font-size: 14px;
  color: #1e1b4b;
}

.odh-modern .section-icon {
  width: 26px;
  height: 26px;
  padding: 6px;
  box-sizing: border-box;
  border-radius: 8px;
  color: #fff;
  background: linear-gradient(145deg, #818cf8 0%, #4f46e5 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(49, 46, 129, 0.3);
}

.odh-modern .summary-section .section-icon {
  background: linear-gradient(145deg, #34d399 0%, #059669 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(6, 95, 70, 0.3);
}

.odh-modern .stat-chip {
  padding: 2px 10px;
  border-color: #e0e7ff;
  box-shadow: inset 0 1px 0 #ffffff;
}

.odh-modern .stat-label {
  font-size: 11px;
}

.odh-modern .stat-value {
  font-size: 12px;
  color: #4338ca;
}

.odh-modern .summary-section .stat-chip {
  background: #ecfdf5;
  border-color: #a7f3d0;
}

.odh-modern .summary-section .stat-value {
  color: #047857;
}

/* ---------- テーブル ---------- */
.odh-modern .modern-table-container {
  flex: 1 1 auto;
  min-height: 0;
  border-radius: 10px;
  border: 1px solid #eef2f7;
  background: #fff;
}

.odh-modern .modern-table {
  --el-table-border-color: #eef2f7;
  --el-table-row-hover-bg-color: #f5f7ff;
  color: #1e293b;
}

.odh-modern .modern-table :deep(.el-table__header-wrapper th.el-table__cell) {
  padding: 7px 6px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #3730a3;
  background: linear-gradient(180deg, #f8f9ff 0%, #eef2ff 100%);
  border-bottom: 1px solid #c7d2fe;
}

.odh-modern .summary-table :deep(.el-table__header-wrapper th.el-table__cell) {
  color: #065f46;
  background: linear-gradient(180deg, #f5fdf9 0%, #e7f9ef 100%);
  border-bottom-color: #a7f3d0;
}

.odh-modern .summary-table .table-header .el-icon {
  color: #059669;
}

.odh-modern .modern-table :deep(.el-table__body td.el-table__cell) {
  padding: 5px 6px;
  font-size: 13px;
  line-height: 1.45;
  border-bottom: 1px solid #f1f5f9;
}

.odh-modern .modern-table :deep(.el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #fafbff;
}

.odh-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #f5f7ff !important;
}

.odh-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #6366f1;
}

.odh-modern .summary-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #f2fbf6 !important;
}

.odh-modern .summary-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #10b981;
}

.odh-modern .modern-table :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #c7d2fe transparent;
}

.odh-modern .date-cell {
  font-size: 12px;
  color: #4338ca;
  font-variant-numeric: tabular-nums;
}

.odh-modern .name-cell {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.odh-modern .number-cell .number {
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

/* 月別構成比バー */
.odh-modern .qty-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.odh-modern .qty-bar__track {
  position: relative;
  flex: 1;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: #eef2f7;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.1);
}

.odh-modern .qty-bar__fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: linear-gradient(90deg, #6ee7b7 0%, #10b981 60%, #0d9488 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
  transition: width 0.4s ease;
}

.odh-modern .qty-bar__pct {
  min-width: 44px;
  text-align: right;
  font-size: 12px;
  font-weight: 700;
  color: #047857;
  font-variant-numeric: tabular-nums;
}

/* 状態タグ：淡色ピル（動きなし） */
.odh-modern .status-tag {
  height: 22px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 700;
  transition: none;
}

.odh-modern .status-tag:hover {
  transform: none;
}

.odh-modern .status-tag.status-completed {
  color: #047857;
  background: #ecfdf5;
  box-shadow: inset 0 0 0 1px #a7f3d0;
}

.odh-modern .status-tag.status-cancelled {
  color: #be123c;
  background: #fff1f2;
  box-shadow: inset 0 0 0 1px #fecdd3;
}

.odh-modern .status-tag.status-processing {
  color: #b45309;
  background: #fffbeb;
  box-shadow: inset 0 0 0 1px #fde68a;
}

.odh-modern .status-tag.status-default {
  color: #475569;
  background: #f1f5f9;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}

/* ---------- 全画面レイアウト：高さもコンテンツ領域にそろえ、表の中だけスクロール ----------
 * 条件はスクリプト側 FILL_LAYOUT_QUERY と同じにすること */
@media (min-width: 1280px) and (min-height: 640px) {
  .order-destination-history.odh-modern {
    height: 100%;
    overflow: hidden;
  }
}

/* ---------- 縦積みレイアウト（幅または高さが足りない場合はページ全体をスクロール） ---------- */
@media (max-width: 1279.98px), (max-height: 639.98px) {
  .odh-modern .content-grid {
    grid-template-columns: minmax(0, 1fr);
    flex: 0 0 auto;
  }

  .odh-modern .modern-table-container {
    flex: 0 0 auto;
  }
}

@media (max-width: 1100px) {
  .odh-modern .kpi-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .order-destination-history.odh-modern {
    padding: 6px;
  }

  .odh-modern .hero-meta {
    justify-content: flex-start;
  }

  .odh-modern .filter-strip {
    align-items: stretch;
  }

  .odh-modern .filter-item {
    width: 100%;
  }

  .odh-modern .filter-item :deep(.el-form-item__content) {
    flex: 1;
  }

  .odh-modern .month-quick {
    margin: 6px 0 0;
  }
}

@media (max-width: 480px) {
  .odh-modern .kpi-strip {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>

