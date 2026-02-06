<template>
  <div class="customer-order-history">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon>
              <User />
            </el-icon>
          </div>
          <div class="title-text">
            <h1 class="main-title">顧客別受注履歴</h1>
            <p class="subtitle">顧客ごとの受注データを詳細に分析・管理</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选表单 -->
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
                  <User />
                </el-icon>
                <span>顧客</span>
              </div>
            </template>
            <el-select v-model="filters.customer_cd" placeholder="顧客を選択" clearable filterable class="select-input">
              <el-option v-for="item in customerOptions" :key="item.cd" :label="`${item.cd} - ${item.name}`"
                :value="item.cd" />
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
            <el-date-picker v-model="filters.date_range" type="daterange" start-placeholder="開始日" end-placeholder="終了日"
              format="YYYY-MM-DD" value-format="YYYY-MM-DD" class="date-picker" />
          </el-form-item>

          <div class="filter-actions">
            <el-button type="primary" @click="fetchData" class="search-btn">
              <el-icon>
                <Search />
              </el-icon>
              検索
            </el-button>
          </div>
        </div>
      </el-form>
    </div>

    <!-- 月别统计 -->
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

          <el-table-column label="受注数量合計" prop="total_quantity" width="160" align="right">
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
                <span class="unit">件</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="受注金額合計" prop="total_amount" width="180" align="right">
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Money />
                </el-icon>
                <span>受注金額合計</span>
              </div>
            </template>
            <template #default="{ row }">
              <div class="number-cell amount">
                <span class="number">{{ row.total_amount?.toLocaleString() ?? '0' }}</span>
                <span class="unit">円</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 订单明细 -->
    <div class="details-section">
      <div class="section-header">
        <div class="section-title">
          <el-icon class="section-icon">
            <Document />
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
        <el-table :data="filteredOrderList" class="modern-table details-table">
          <el-table-column label="受注日" prop="order_date" width="120" align="center">
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Calendar />
                </el-icon>
                <span>受注日</span>
              </div>
            </template>
            <template #default="{ row }">
              <div class="date-cell">
                {{ row.order_date }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="顧客名" prop="customer_name" min-width="160" align="center" show-overflow-tooltip>
            <template #header>
              <div class="table-header">
                <el-icon>
                  <User />
                </el-icon>
                <span>顧客名</span>
              </div>
            </template>
            <template #default="{ row }">
              <div class="name-cell">
                {{ row.customer_name }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="納入先名" prop="destination_name" min-width="160" align="center" show-overflow-tooltip>
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Location />
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

          <el-table-column label="製品名" prop="product_name" min-width="160" align="center" show-overflow-tooltip>
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Box />
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

          <el-table-column label="数量" prop="quantity" width="110" align="center">
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

          <el-table-column label="単価" prop="unit_price" width="130" align="right">
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Money />
                </el-icon>
                <span>単価</span>
              </div>
            </template>
            <template #default="{ row }">
              <div class="number-cell price">
                <span class="number">{{ row.unit_price?.toLocaleString() ?? '0' }}</span>
                <span class="unit">円</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="金額" prop="amount" width="150" align="right">
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Money />
                </el-icon>
                <span>金額</span>
              </div>
            </template>
            <template #default="{ row }">
              <div class="number-cell amount">
                <span class="number">{{ row.amount?.toLocaleString() ?? '0' }}</span>
                <span class="unit">円</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="状態" prop="status" width="110" align="center">
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Document />
                </el-icon>
                <span>状態</span>
              </div>
            </template>
            <template #default="{ row }">
              <div class="status-cell">
                <el-tag :class="getStatusClass(row.status)" class="status-tag">
                  {{ row.status }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import request from '@/utils/request'
import { getCustomerOptions } from '@/api/options'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import {
  User,
  Printer,
  Search,
  TrendCharts,
  Calendar,
  Document,
  Location,
  Box,
  Money,
} from '@element-plus/icons-vue'

const filters = ref({
  customer_cd: '',
  date_range: [],
})

interface OrderHistoryItem {
  order_date: string
  customer_cd: string
  customer_name: string
  destination_cd: string
  destination_name: string
  product_cd: string
  product_name: string
  quantity: number
  unit_price?: number
  amount?: number
  status: string
}

interface MonthlySummaryItem {
  ym: string
  total_quantity: number
  total_amount?: number
}

const orderList = ref<OrderHistoryItem[]>([])
const summaryList = ref<MonthlySummaryItem[]>([])
const customerOptions = ref<{ cd: string; name: string }[]>([])

// 数量が0より大きい注文をフィルタリング
const filteredOrderList = computed(() => {
  return orderList.value.filter((order) => order.quantity > 0)
})

// 状態ラベルタイプを取得
const getStatusType = (status: string) => {
  switch (status) {
    case '完了':
      return 'success'
    case 'キャンセル':
      return 'danger'
    case '処理中':
      return 'warning'
    default:
      return 'info'
  }
}

// 状態スタイルクラスを取得
const getStatusClass = (status: string) => {
  switch (status) {
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

// 📥 顧客選択肢
const loadOptions = async () => {
  try {
    customerOptions.value = await getCustomerOptions()
  } catch (error) {
    console.error('顧客データ取得エラー:', error)
    ElMessage.error('顧客データの取得に失敗しました')
  }
}

// 📊 検索
const fetchData = async () => {
  if (!filters.value.customer_cd || filters.value.date_range.length !== 2) {
    ElMessage.warning('顧客と期間を選択してください')
    return
  }

  try {
    const [start_date, end_date] = filters.value.date_range
    const [orders, summary] = await Promise.all([
      request.get('/api/order/customer-history', {
        params: { customer_cd: filters.value.customer_cd, start_date, end_date },
      }),
      request.get('/api/order/customer-monthly-summary', {
        params: { customer_cd: filters.value.customer_cd, start_date, end_date },
      }),
    ])

    orderList.value = orders
    summaryList.value = summary
  } catch (error) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データの取得に失敗しました')
  }
}

// 印刷機能
const handlePrint = () => {
  if (filteredOrderList.value.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  // 顧客名を取得
  const customer = customerOptions.value.find((c) => c.cd === filters.value.customer_cd)
  const customerName = customer ? `${customer.cd} - ${customer.name}` : filters.value.customer_cd

  // 検索条件情報を取得
  const filterInfo = []
  if (filters.value.date_range?.length === 2) {
    filterInfo.push(`期間: ${filters.value.date_range[0]} ~ ${filters.value.date_range[1]}`)
  }
  const filterText =
    filterInfo.length > 0
      ? `<div class="filter-info">検索条件: ${filterInfo.join(' / ')}</div>`
      : ''

  // 納入先名でグループ化
  const groupedByDestination = filteredOrderList.value.reduce((acc, item) => {
    const key = item.destination_name || '未設定'
    if (!acc[key]) {
      acc[key] = []
    }
    acc[key].push(item)
    return acc
  }, {} as Record<string, typeof filteredOrderList.value>)

  // 受注明細テーブルHTMLを生成（納入先名でグループ化）
  const detailsTableHtml = Object.entries(groupedByDestination)
    .map(([destinationName, items]) => {
      // 該当納入先の合計を計算
      const itemCount = items.length // 件数
      const totalQuantity = items.reduce((sum, item) => sum + (item.quantity || 0), 0)
      const totalAmount = items.reduce((sum, item) => sum + (item.amount || 0), 0)

      // 該当グループのテーブル行を生成
      const rowsHtml = items
        .map(
          (item) => `
            <tr>
              <td class="center">${item.order_date}</td>
              <td>${item.destination_name}</td>
              <td>${item.product_name}</td>
              <td class="number">${item.quantity?.toLocaleString() ?? '0'}</td>
              <td class="number">${item.unit_price?.toLocaleString() ?? '0'}円</td>
              <td class="number">${item.amount?.toLocaleString() ?? '0'}円</td>
            </tr>
          `,
        )
        .join('')

      // 合計行
      const summaryRow = `
        <tr class="summary-row">
          <td colspan="2" class="summary-label">${destinationName} 小計</td>
          <td class="center summary-value">${itemCount}件</td>
          <td class="number summary-value">${totalQuantity.toLocaleString()}</td>
          <td class="number summary-value">-</td>
          <td class="number summary-value">${totalAmount.toLocaleString()}円</td>
        </tr>
      `

      return rowsHtml + summaryRow
    })
    .join('')

  // 印刷ウィンドウ
  const printWindow = window.open('', '', 'width=1000,height=800')
  if (!printWindow) return ElMessage.error('印刷ウィンドウを開けません')

  printWindow.document.write(`
    <html>
      <head>
        <title>顧客別受注履歴</title>
        <style>
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          body {
            font-family: "Yu Gothic", "Hiragino Kaku Gothic Pro", "Meiryo", sans-serif;
            padding: 10px;
            color: #2c3e50;
            font-size: 11px;
          }
          .filter-info {
            margin: 5px 0 10px;
            padding: 6px;
            background: #f8f9fa;
            border-radius: 3px;
            font-size: 11px;
            color: #666;
          }
          .customer-name {
            font-size: 16px;
            font-weight: bold;
            margin: 10px 0 8px;
            padding: 6px;
            background: #e3f2fd;
            border-left: 3px solid #1a73e8;
            color: #1a73e8;
          }
          h2 {
            text-align: center;
            font-size: 20px;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #1a73e8;
          }
          h3 {
            font-size: 14px;
            margin: 10px 0 5px;
            color: #2c3e50;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
            font-size: 10px;
          }
          th, td {
            border: 1px solid #ddd;
            padding: 4px;
            text-align: left;
          }
          th {
            background-color: #f7faff;
            font-weight: bold;
            font-size: 10px;
          }
          .number {
            text-align: right;
            font-family: 'Roboto Mono', monospace;
          }
          .center {
            text-align: center;
          }
          .summary-row {
            background-color: #f0f7ff;
            font-weight: bold;
          }
          .summary-label {
            text-align: right;
            padding-right: 10px;
          }
          .summary-value {
            font-weight: bold;
            color: #1a73e8;
          }
          .print-info {
            text-align: right;
            color: #666;
            font-size: 10px;
            margin-bottom: 8px;
          }
          @media print {
            body {
              padding: 5px;
            }
            .filter-info {
              margin: 3px 0 6px;
              padding: 4px;
            }
            .customer-name {
              margin: 6px 0 5px;
              padding: 4px;
            }
            h2 {
              margin-bottom: 8px;
              padding-bottom: 4px;
            }
            h3 {
              margin: 8px 0 4px;
            }
            table {
              margin-bottom: 8px;
            }
            th, td {
              padding: 3px;
            }
            table {
              page-break-inside: auto;
            }
            tr {
              page-break-inside: avoid;
              page-break-after: auto;
            }
            thead {
              display: table-header-group;
            }
          }
        </style>
      </head>
      <body>
        <div class="print-info">
          印刷日時: ${dayjs().format('YYYY/MM/DD HH:mm')}
        </div>
        <h2>顧客別受注履歴</h2>
        ${filterText}
        <div class="customer-name">顧客: ${customerName}</div>
        <h3>月別集計</h3>
        <table>
          <thead>
            <tr>
              <th>年月</th>
              <th>受注数量合計</th>
              <th>受注金額合計</th>
            </tr>
          </thead>
          <tbody>
            ${summaryList.value
      .map(
        (item) => `
              <tr>
                <td class="center">${item.ym}</td>
                <td class="number">${item.total_quantity?.toLocaleString() ?? ''}</td>
                <td class="number">${item.total_amount?.toLocaleString() ?? '0'}円</td>
              </tr>
            `,
      )
      .join('')}
          </tbody>
        </table>
        <h3>受注明細</h3>
        <table>
          <thead>
            <tr>
              <th>受注日</th>
              <th>納入先名</th>
              <th>製品名</th>
              <th>数量</th>
              <th>単価</th>
              <th>金額</th>
            </tr>
          </thead>
          <tbody>
            ${detailsTableHtml}
          </tbody>
        </table>
      </body>
    </html>
  `)

  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
  printWindow.close()
}

loadOptions()
</script>

<style scoped>
/* 页面容器 - 紧凑简洁 */
.customer-order-history {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 0;
  position: relative;
}

/* 页面头部 - 紧凑设计 */
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
  position: relative;
  z-index: 2;
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

.main-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: white;
  letter-spacing: -0.01em;
}

.subtitle {
  font-size: 0.875rem;
  margin: 4px 0 0 0;
  opacity: 0.9;
  font-weight: 400;
}

/* 筛选区域 - 紧凑设计 */
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
  width: 220px;
}

.date-picker {
  width: 260px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.search-btn {
  background: #667eea;
  border: none;
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
}

/* 区域样式 - 紧凑设计 */
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
  flex-direction: row;
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

.print-btn {
  background: #667eea;
  border: none;
  color: white;
  padding: 6px 14px;
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

/* 表格样式 - 紧凑设计 */
.modern-table-container {
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.modern-table {
  border: none;
}

:deep(.modern-table .el-table__header) {
  background: #f8fafc;
}

:deep(.modern-table .el-table__header th) {
  background: #f8fafc;
  border: none;
  border-bottom: 1px solid #e5e7eb;
  padding: 10px 8px;
  color: #374151;
  font-weight: 600;
  font-size: 0.875rem;
  text-align: center;
}

:deep(.modern-table .el-table__body tr) {
  transition: background-color 0.15s ease;
}

:deep(.modern-table .el-table__body tr:hover) {
  background-color: #f8fafc;
}

:deep(.modern-table .el-table__body td) {
  border: none;
  padding: 10px 8px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
}

/* 受注明細表格特定样式 */
:deep(.details-table .el-table__header th) {
  padding: 8px 6px;
  font-size: 0.8125rem;
}

:deep(.details-table .el-table__body td) {
  padding: 6px 6px;
  font-size: 0.8125rem;
  text-align: center;
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

/* 单元格样式 */
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

.number-cell.price {
  color: #667eea;
}

.number-cell.amount {
  color: #dc2626;
  font-weight: 600;
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

/* 响应式设计 */
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

  .main-title {
    font-size: 1.375rem;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 12px 16px;
    margin-bottom: 12px;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .title-section {
    gap: 10px;
  }

  .title-icon {
    width: 36px;
    height: 36px;
  }

  .title-icon .el-icon {
    font-size: 18px;
  }

  .main-title {
    font-size: 1.25rem;
  }

  .subtitle {
    font-size: 0.8125rem;
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

@media (max-width: 480px) {
  .page-header {
    padding: 10px 12px;
  }

  .filter-section,
  .summary-section,
  .details-section {
    margin: 0 8px 8px;
    padding: 10px 12px;
  }

  .main-title {
    font-size: 1.125rem;
  }

  .title-section {
    gap: 8px;
  }

  .title-icon {
    width: 32px;
    height: 32px;
  }

  .title-icon .el-icon {
    font-size: 16px;
  }
}

/* 暗黑模式支持 */
@media (prefers-color-scheme: dark) {
  .customer-order-history {
    background: #111827;
  }

  .filter-section,
  .summary-section,
  .details-section {
    background: #1f2937;
    border-color: #374151;
  }

  .filter-title,
  .section-title {
    color: #f9fafb;
  }

  .name-cell {
    color: #d1d5db;
  }

  :deep(.modern-table .el-table__header) {
    background: #1f2937;
  }

  :deep(.modern-table .el-table__header th) {
    background: #1f2937;
    border-bottom-color: #374151;
    color: #f9fafb;
  }

  :deep(.modern-table .el-table__body td) {
    border-bottom-color: #374151;
  }
}
</style>
