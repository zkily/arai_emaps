<template>
  <div class="order-destination-history">
    <div class="page-shell">
      <!-- 页头 + 筛选：紧凑一体 -->
      <header class="hero-panel">
        <div class="hero-top">
          <div class="title-block">
            <div class="title-icon" aria-hidden="true">
              <el-icon><OfficeBuilding /></el-icon>
            </div>
            <div class="title-text">
              <h1 class="page-title">納入先別受注履歴</h1>
              <p class="page-subtitle">納入先ごとの受注データ分析・履歴管理</p>
            </div>
          </div>
          <div v-if="orderList.length > 0" class="hero-badge">
            <span class="badge-label">結果</span>
            <span class="badge-value">{{ filteredOrderList.length }}件</span>
          </div>
        </div>

        <div class="filter-strip">
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
              </el-form-item>

              <div class="filter-actions">
                <el-button type="primary" @click="fetchData" class="search-btn" :loading="isFetching">
                  <el-icon><Search /></el-icon>
                  検索
                </el-button>
              </div>
            </div>
          </el-form>
        </div>
      </header>

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
        <el-table :data="summaryList" class="modern-table summary-table" stripe>
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
          :height="DETAILS_TABLE_HEIGHT"
        >
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
    </section>
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

/** 受注明細テーブル固定高さ（表頭固定・表体は縦スクロール） */
const DETAILS_TABLE_HEIGHT = 480

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
</style>

