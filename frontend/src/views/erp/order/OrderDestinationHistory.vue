<template>
  <div class="order-destination-history">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon>
              <OfficeBuilding />
            </el-icon>
          </div>
          <div class="title-text">
            <h1 class="page-title">納入先別受注履歴</h1>
            <p class="page-subtitle">納入先ごとの受注データ分析・履歴管理</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Search />
          </el-icon>
          <span>検索フィルター</span>
        </div>

        <div class="filter-stats" v-if="orderList.length > 0">
          <span class="stats-text">{{ filteredOrderList.length }}件の結果</span>
        </div>
      </div>

      <el-form :inline="true" class="modern-filter-form">
        <div class="filter-row">
          <el-form-item class="filter-item">
            <template #label>
              <div class="custom-label">
                <el-icon>
                  <OfficeBuilding />
                </el-icon>
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
                <el-icon>
                  <Calendar />
                </el-icon>
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
          </el-form-item>

          <div class="filter-actions">
            <el-button
              type="primary"
              @click="fetchData"
              class="search-btn"
              :loading="isFetching"
            >
              <el-icon>
                <Search />
              </el-icon>
              検索
            </el-button>
          </div>
        </div>
      </el-form>
    </div>

    <!-- 月別集計 -->
    <div class="summary-section">
      <div class="section-header">
        <div class="section-title">
          <el-icon class="section-icon">
            <TrendCharts />
          </el-icon>
          <span>月別集計</span>
        </div>
        <div class="summary-stats" v-if="summaryList.length > 0">
          <div class="stat-item">
            <span class="stat-label">期間数</span>
            <span class="stat-value">{{ summaryList.length }}ヶ月</span>
          </div>
        </div>
      </div>

      <div class="modern-table-container">
        <el-table :data="summaryList" class="modern-table summary-table">
          <el-table-column label="年月" prop="ym" width="140" align="center">
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

          <el-table-column label="受注数量合計" prop="total_quantity" width="200" align="right">
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
        </el-table>
      </div>
    </div>

    <!-- 受注明細 -->
    <div class="details-section">
      <div class="section-header">
        <div class="section-title">
          <el-icon class="section-icon">
            <List />
          </el-icon>
          <span>受注明細</span>
        </div>

        <div class="section-actions">
          <div class="details-stats" v-if="filteredOrderList.length > 0">
            <div class="stat-item">
              <span class="stat-label">明細数</span>
              <span class="stat-value">{{ filteredOrderList.length }}件</span>
            </div>
          </div>

          <el-button class="print-btn" @click="handlePrint">
            <el-icon>
              <Printer />
            </el-icon>
            印刷
          </el-button>
        </div>
      </div>

      <div class="modern-table-container">
        <el-table :data="filteredOrderList" class="modern-table details-table" :v-loading="isFetching">
          <el-table-column label="出荷日" prop="date" width="120" align="center">
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
            min-width="160"
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
            min-width="160"
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

          <el-table-column label="数量" prop="quantity" width="130" align="right">
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

          <el-table-column label="状態" prop="status" width="120" align="center">
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

          <el-table-column label="納入日" prop="delivery_date" width="120" align="center">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Calendar, List, OfficeBuilding, Printer, Search, TrendCharts, Box } from '@element-plus/icons-vue'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { fetchOrderDailyList } from '@/api/erp/orderDaily'

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
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function formatPrintTime() {
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
  try {
    await loadOptions()
  } catch {
    destinationOptions.value = []
  }
})
</script>

<style scoped>
.order-destination-history {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 0;
  position: relative;
}

.page-header {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 24px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.title-icon .el-icon {
  font-size: 20px;
  color: white;
}

.title-text {
  color: white;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: white;
  letter-spacing: -0.01em;
}

.page-subtitle {
  font-size: 0.875rem;
  margin: 4px 0 0 0;
  opacity: 0.9;
  font-weight: 400;
}

.filter-section {
  background: white;
  border-radius: 8px;
  padding: 16px 20px;
  margin: 0 16px 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.filter-icon {
  font-size: 16px;
  color: #667eea;
}

.filter-stats {
  display: flex;
  gap: 12px;
}

.stats-text {
  background: #667eea;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.modern-filter-form {
  margin: 0;
}

.filter-row {
  display: flex;
  align-items: end;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-item {
  margin-bottom: 0;
}

.custom-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
  font-size: 0.875rem;
}

.custom-label .el-icon {
  font-size: 14px;
  color: #667eea;
}

.select-input {
  width: 240px;
}

.date-picker {
  width: 280px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.search-btn {
  background: #667eea;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.search-btn:hover {
  background: #5568d3;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.summary-section,
.details-section {
  background: white;
  border-radius: 8px;
  padding: 16px 20px;
  margin: 0 16px 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.section-icon {
  font-size: 16px;
  color: #667eea;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-stats,
.details-stats {
  display: flex;
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #667eea;
}

.modern-table-container {
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.modern-table {
  border: none;
}

::deep(.modern-table .el-table__header) {
  background: #f8fafc;
}

::deep(.modern-table .el-table__header th) {
  background: #f8fafc;
  border: none;
  border-bottom: 1px solid #e5e7eb;
  padding: 10px 8px;
  color: #374151;
  font-weight: 600;
  font-size: 0.875rem;
  text-align: center;
}

::deep(.modern-table .el-table__body td) {
  border: none;
  padding: 10px 8px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-weight: 600;
}

.table-header .el-icon {
  font-size: 14px;
}

.date-cell {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  font-weight: 500;
  color: #667eea;
  text-align: center;
  font-size: 0.8125rem;
}

.name-cell {
  font-weight: 500;
  color: #374151;
  font-size: 0.8125rem;
  text-align: center;
}

.number-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
}

.number-cell .number {
  font-weight: 600;
  font-size: 0.8125rem;
}

.number-cell .unit {
  font-size: 0.75rem;
  opacity: 0.7;
  font-weight: 500;
}

.number-cell.quantity {
  color: #059669;
}

.status-cell {
  display: flex;
  justify-content: center;
}

.status-tag {
  border: none;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  transition: all 0.2s ease;
}

.status-completed {
  background: #10b981;
  color: white;
}

.status-cancelled {
  background: #ef4444;
  color: white;
}

.status-processing {
  background: #f59e0b;
  color: white;
}

.status-default {
  background: #6b7280;
  color: white;
}

.print-btn {
  background: #667eea;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.print-btn:hover {
  background: #5568d3;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

@media (max-width: 1200px) {
  .page-header {
    padding: 14px 20px;
  }

  .filter-section,
  .summary-section,
  .details-section {
    margin: 0 12px 10px;
    padding: 14px 16px;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 12px 16px;
    margin-bottom: 12px;
  }

  .filter-section,
  .summary-section,
  .details-section {
    margin: 0 12px 10px;
    padding: 12px 14px;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .select-input,
  .date-picker {
    width: 100%;
  }

  .filter-actions {
    justify-content: center;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>

