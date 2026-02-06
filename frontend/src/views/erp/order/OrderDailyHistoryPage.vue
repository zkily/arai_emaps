<template>
  <div class="modern-daily-history-page">
    <!-- 现代化页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon>
              <Van />
            </el-icon>
          </div>
          <div class="title-text">
            <h1 class="page-title">日別受注履歴</h1>
            <p class="page-subtitle">出荷データの詳細履歴・検索・印刷機能</p>
          </div>
        </div>
      </div>

      <!-- 装饰元素 -->
      <div class="header-decoration">
        <div class="floating-circle circle-1"></div>
        <div class="floating-circle circle-2"></div>
      </div>
    </div>

    <!-- 现代化筛选区域 -->
    <div class="filter-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Search />
          </el-icon>
          <span>検索フィルター</span>
        </div>
        <div class="filter-stats" v-if="!loading">
          <span class="stats-text">{{ filteredOrderList.length }}件の結果</span>
        </div>
      </div>

      <el-form :inline="true" :model="filters" class="modern-filter-form" @submit.prevent>
        <div class="filter-row">
          <el-form-item class="filter-item">
            <template #label>
              <div class="custom-label">
                <el-icon>
                  <Calendar />
                </el-icon>
                <span>期間</span>
              </div>
            </template>
            <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="~" start-placeholder="開始日"
              end-placeholder="終了日" value-format="YYYY-MM-DD" :shortcuts="dateShortcuts" class="date-picker" />
          </el-form-item>

          <el-form-item class="filter-item">
            <template #label>
              <div class="custom-label">
                <el-icon>
                  <OfficeBuilding />
                </el-icon>
                <span>納入先</span>
              </div>
            </template>
            <el-select v-model="filters.destination_cd" placeholder="納入先を選択" filterable clearable class="select-input">
              <el-option v-for="item in destinationOptions" :key="item.cd" :label="`${item.cd} - ${item.name}`"
                :value="item.cd" />
            </el-select>
          </el-form-item>

          <el-form-item class="filter-item">
            <template #label>
              <div class="custom-label">
                <el-icon>
                  <Box />
                </el-icon>
                <span>製品</span>
              </div>
            </template>
            <el-select v-model="filters.product_cd" placeholder="製品を選択" filterable clearable class="select-input">
              <el-option v-for="item in productOptions" :key="item.cd" :label="`${item.cd} - ${item.name}`"
                :value="item.cd" />
            </el-select>
          </el-form-item>

          <div class="filter-actions">
            <el-button type="primary" @click="fetchList" class="search-btn">
              <el-icon>
                <Search />
              </el-icon>
              検索
            </el-button>
            <el-button @click="resetFilter" class="reset-btn">
              <el-icon>
                <RefreshLeft />
              </el-icon>
              リセット
            </el-button>
          </div>
        </div>
      </el-form>
    </div>

    <!-- 现代化数据展示区域 -->
    <div class="data-section">
      <div class="section-header">
        <div class="section-title">
          <el-icon class="section-icon">
            <List />
          </el-icon>
          <span>出荷履歴データ</span>
        </div>
        <div class="section-actions">
          <el-button class="print-btn" @click="handlePrint">
            <el-icon>
              <Printer />
            </el-icon>
            印刷
          </el-button>
        </div>
      </div>

      <div class="simple-table-container">
        <el-table :data="filteredOrderList" v-loading="loading" class="simple-table" :row-class-name="tableRowClassName"
          empty-text="データがありません" stripe>
          <el-table-column label="年月日" align="center" width="110">
            <template #default="{ row }">
              <div class="date-cell">
                {{ formatDate(row) }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="納入先CD" prop="destination_cd" width="130">
            <template #default="{ row }">
              <div class="code-cell">
                {{ row.destination_cd }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="納入先名" prop="destination_name" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="name-cell">
                {{ row.destination_name }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="製品CD" prop="product_cd" width="130">
            <template #default="{ row }">
              <div class="code-cell">
                {{ row.product_cd }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="製品名" prop="product_name" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="name-cell">
                {{ row.product_name }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="確定箱数" prop="confirmed_boxes" width="120" align="right">
            <template #default="{ row }">
              <div class="number-cell">
                <span class="number">{{ row.confirmed_boxes?.toLocaleString() }}</span>
                <span class="unit">箱</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="確定本数" prop="confirmed_units" width="120" align="right">
            <template #default="{ row }">
              <div class="number-cell">
                <span class="number">{{ row.confirmed_units?.toLocaleString() }}</span>
                <span class="unit">本</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="状態" prop="status" width="110" align="center">
            <template #default="{ row }">
              <div class="status-cell">
                <el-tag :class="getStatusClass(row.status)" class="status-tag">
                  {{ row.status }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 现代化分页器 -->
        <div class="modern-pagination">
          <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
            :total="pagination.total" :page-sizes="[10, 20, 50, 100]" background
            layout="total, sizes, prev, pager, next" @size-change="handleSizeChange" @current-change="fetchList" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { fetchDailyAllOrders } from '@/api/order/order'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import type { OrderDaily, FetchDailyOrdersParams } from '@/types/order'
import { getDestinationOptions, getProductOptions } from '@/api/options'
import dayjs from 'dayjs'
import {
  Van,
  Printer,
  Search,
  Calendar,
  OfficeBuilding,
  Box,
  RefreshLeft,
  List,
  Shop,
  Goods,
  Collection,
  Flag,
} from '@element-plus/icons-vue'

// 日期快捷选项
const dateShortcuts = [
  {
    text: '今日',
    value: () => {
      const today = new Date()
      return [today, today]
    },
  },
  {
    text: '昨日',
    value: () => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      return [yesterday, yesterday]
    },
  },
  {
    text: '今週',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - start.getDay())
      return [start, end]
    },
  },
  {
    text: '今月',
    value: () => {
      const end = new Date()
      const start = new Date(end.getFullYear(), end.getMonth(), 1)
      return [start, end]
    },
  },
]

// 筛选条件
const filters = ref({
  dateRange: [dayjs().format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')], // 默认今天
  destination_cd: '',
  product_cd: '',
})

// 納入先選択
interface OptionItem {
  cd: string
  name: string
}

const destinationOptions = ref<OptionItem[]>([])
const productOptions = ref<OptionItem[]>([])

// 获取选项数据
const fetchOptions = async () => {
  try {
    const [destinations, products] = await Promise.all([
      getDestinationOptions(),
      getProductOptions(),
    ])
    destinationOptions.value = destinations
    productOptions.value = products
  } catch (error) {
    console.error('オプション取得失敗', error)
    ElMessage.error('データ取得に失敗しました')
  }
}

// 列表数据
const orderList = ref<OrderDaily[]>([])
const loading = ref(false)

// 过滤后的订单列表（确定箱数大于0）
const filteredOrderList = computed(() => {
  return orderList.value.filter((order) => order.confirmed_boxes > 0)
})

// 分页信息
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

// 处理每页条数变化
const handleSizeChange = (val: number) => {
  pagination.value.pageSize = val
  pagination.value.page = 1
  fetchList()
}

// 格式化日期显示
const formatDate = (row: OrderDaily) => {
  return `${row.year}/${String(row.month).padStart(2, '0')}/${String(row.day).padStart(2, '0')}`
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  switch (status) {
    case '出荷済':
      return 'success'
    case 'キャンセル':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取状态样式类
const getStatusClass = (status: string) => {
  switch (status) {
    case '出荷済':
      return 'status-shipped'
    case 'キャンセル':
      return 'status-cancelled'
    default:
      return 'status-pending'
  }
}

// 表格行样式类名
const tableRowClassName = ({ rowIndex }: { rowIndex: number }) => {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}

// 查询履歴
const fetchList = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = filters.value.dateRange

    const params: FetchDailyOrdersParams = {
      startDate,
      endDate,
      destination_cd: filters.value.destination_cd,
      product_cd: filters.value.product_cd,
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
    }

    const res = await fetchDailyAllOrders(params)
    orderList.value = res.list
    pagination.value.total = res.total
  } catch (error) {
    console.error('履歴取得失敗', error)
    ElMessage.error('データ取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilter = () => {
  filters.value = {
    dateRange: [dayjs().format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')],
    destination_cd: '',
    product_cd: '',
  }
  pagination.value.page = 1
  fetchList()
}

// 打印
const handlePrint = async () => {
  try {
    // 获取所有筛选出的数据（不分页）
    ElMessage.info('データを取得中...')
    const [startDate, endDate] = filters.value.dateRange

    // 循环获取所有分页数据
    const allData: OrderDaily[] = []
    let page = 1
    const pageSize = 1000
    let hasMore = true

    while (hasMore) {
      const params: FetchDailyOrdersParams = {
        startDate,
        endDate,
        destination_cd: filters.value.destination_cd,
        product_cd: filters.value.product_cd,
        page,
        pageSize,
      }

      const res = await fetchDailyAllOrders(params)
      const filteredData = res.list.filter((order) => order.confirmed_boxes > 0)
      allData.push(...filteredData)

      // 如果返回的数据少于pageSize，说明已经是最后一页
      if (res.list.length < pageSize || allData.length >= res.total) {
        hasMore = false
      } else {
        page++
      }
    }

    if (allData.length === 0) {
      ElMessage.warning('印刷するデータがありません')
      return
    }

    const printData = allData

    // 按日期和納入先分组数据
    const groupedData = new Map<string, Map<string, OrderDaily[]>>()

    // 首先按日期和納入先排序
    const sortedData = [...printData].sort((a, b) => {
      // 先按年月日排序
      if (a.year !== b.year) return a.year - b.year
      if (a.month !== b.month) return a.month - b.month
      if (a.day !== b.day) return a.day - b.day
      // 再按納入先CD排序
      return a.destination_cd.localeCompare(b.destination_cd)
    })

    // 组织数据
    sortedData.forEach((order) => {
      const dateKey = `${order.year}年${order.month}月${order.day}日`
      if (!groupedData.has(dateKey)) {
        groupedData.set(dateKey, new Map())
      }
      const destinationMap = groupedData.get(dateKey)!
      const destinationKey = order.destination_cd
      if (!destinationMap.has(destinationKey)) {
        destinationMap.set(destinationKey, [])
      }
      destinationMap.get(destinationKey)!.push(order)
    })

    // 构建打印HTML
    let printContent = ''
    groupedData.forEach((destinationMap, dateKey) => {
      // 计算该日期的合计
      let dateTotalCount = 0 // 件数
      let dateTotalBoxes = 0 // 箱数
      let dateTotalUnits = 0 // 本数

      // 添加日期标题
      printContent += `
        <div class="date-group">
          <h3>${dateKey}</h3>
      `

      destinationMap.forEach((orders, destinationKey) => {
        const firstOrder = orders[0]
        // 添加納入先信息
        printContent += `
          <div class="destination-group">
            <h4>${firstOrder.destination_name} (${firstOrder.destination_cd})</h4>
            <table>
              <thead>
                <tr>
                  <th>製品CD</th>
                  <th>製品名</th>
                  <th>確定箱数</th>
                  <th>確定本数</th>
                  <th>納入日</th>
                </tr>
              </thead>
              <tbody>
        `

        // 添加订单详情
        orders.forEach((order) => {
          const deliveryDate = order.delivery_date
            ? new Date(order.delivery_date).toLocaleDateString('ja-JP', {
              month: 'numeric',
              day: 'numeric',
            })
            : ''

          // 累计合计
          dateTotalCount++
          dateTotalBoxes += order.confirmed_boxes || 0
          dateTotalUnits += order.confirmed_units || 0

          printContent += `
            <tr>
              <td class="center">${order.product_cd ?? ''}</td>
              <td class="center">${order.product_name ?? ''}</td>
              <td class="number center">${order.confirmed_boxes?.toLocaleString() ?? ''}</td>
              <td class="number center">${order.confirmed_units?.toLocaleString() ?? ''}</td>
              <td class="center">${deliveryDate}</td>
            </tr>
          `
        })

        printContent += `
              </tbody>
            </table>
          </div>
        `
      })

      // 添加日期合计行
      printContent += `
        <div class="date-summary">
          <table class="summary-table">
            <tbody>
              <tr class="summary-row">
                <td class="summary-label">合計</td>
                <td class="summary-value">${dateTotalCount}件</td>
                <td class="summary-value">${dateTotalBoxes.toLocaleString()}箱</td>
                <td class="summary-value">${dateTotalUnits.toLocaleString()}本</td>
                <td></td>
              </tr>
            </tbody>
          </table>
        </div>
      `

      printContent += `</div>`
    })

    // 添加筛选条件信息
    const filterInfo = []
    if (filters.value.dateRange[0] === filters.value.dateRange[1]) {
      filterInfo.push(`日付: ${dayjs(filters.value.dateRange[0]).format('YYYY/MM/DD')}`)
    } else {
      filterInfo.push(
        `期間: ${dayjs(filters.value.dateRange[0]).format('YYYY/MM/DD')} ~ ${dayjs(filters.value.dateRange[1]).format('YYYY/MM/DD')}`,
      )
    }
    if (filters.value.destination_cd) {
      const dest = destinationOptions.value.find((d) => d.cd === filters.value.destination_cd)
      filterInfo.push(
        `納入先: ${dest ? `${dest.cd} - ${dest.name}` : filters.value.destination_cd}`,
      )
    }
    if (filters.value.product_cd) {
      const prod = productOptions.value.find((p) => p.cd === filters.value.product_cd)
      filterInfo.push(`製品: ${prod ? `${prod.cd} - ${prod.name}` : filters.value.product_cd}`)
    }
    const filterText =
      filterInfo.length > 0
        ? `<div class="filter-info">検索条件: ${filterInfo.join(' / ')}</div>`
        : ''

    const printWindow = window.open('', '', 'width=1000,height=800')
    if (!printWindow) return ElMessage.error('印刷ウィンドウを開けません')

    printWindow.document.write(`
      <html>
        <head>
          <title>日別出荷履歴 印刷</title>
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
              background: #fff;
              line-height: 1.4;
              font-size: 12px;
            }
            .filter-info {
              margin: 5px 0 10px;
              padding: 6px 8px;
              background: #f8f9fa;
              border-radius: 3px;
              font-size: 11px;
              color: #666;
            }
            h2 {
              text-align: center;
              font-size: 18px;
              margin-bottom: 10px;
              padding: 8px 0;
              color: #1a73e8;
              border-bottom: 2px solid #1a73e8;
            }
            .date-group {
              margin-bottom: 15px;
              break-inside: avoid;
              background: #fff;
              border: 1px solid #e0e6ed;
              padding: 8px;
            }
            .date-group h3 {
              font-size: 14px;
              color: #2c3e50;
              margin-bottom: 8px;
              padding: 6px 10px;
              background: #f8f9fa;
              border-left: 3px solid #1a73e8;
            }
            .destination-group {
              margin-bottom: 12px;
              break-inside: avoid;
              padding: 0 5px;
            }
            .destination-group h4 {
              font-size: 13px;
              color: #444;
              margin: 8px 0 6px;
              padding: 4px 0;
              border-bottom: 1px solid #ddd;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-bottom: 10px;
              font-size: 11px;
              border: 1px solid #e0e6ed;
            }
            th {
              background-color: #f8f9fa;
              color: #2c3e50;
              padding: 6px 6px;
              font-weight: 600;
              border-bottom: 1px solid #e0e6ed;
              white-space: nowrap;
              font-size: 11px;
              text-align: center;
            }
            td {
              padding: 5px 6px;
              border-bottom: 1px solid #f3f4f6;
              color: #444;
              font-size: 11px;
              text-align: center;
            }
            tr:last-child td {
              border-bottom: none;
            }
            td.number {
              text-align: center;
              font-family: 'Roboto Mono', monospace;
              font-size: 11px;
              color: #2c3e50;
            }
            td.center {
              text-align: center;
            }
            .date-summary {
              margin-top: 10px;
              margin-bottom: 5px;
            }
            .summary-table {
              width: 100%;
              border-collapse: collapse;
              border: 2px solid #1a73e8;
              background-color: #f0f7ff;
            }
            .summary-table td {
              padding: 8px 6px;
              font-weight: 600;
              border: none;
            }
            .summary-label {
              text-align: center;
              font-size: 12px;
              color: #1a73e8;
              width: 20%;
            }
            .summary-value {
              text-align: center;
              font-size: 12px;
              color: #2c3e50;
              font-weight: 700;
            }
            .print-date {
              text-align: right;
              color: #666;
              font-size: 10px;
              margin-bottom: 8px;
            }
            .page-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 10px;
            }
            .company-info {
              font-size: 11px;
              color: #666;
            }
            @media print {
              @page {
                margin: 0.5cm;
                size: A4;
              }
              body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                padding: 0;
                background: #fff;
                font-size: 10px;
              }
              .filter-info {
                margin: 3px 0 6px;
                padding: 4px 6px;
                font-size: 10px;
              }
              h2 {
                font-size: 16px;
                margin-bottom: 8px;
                padding: 6px 0;
              }
              .date-group {
                box-shadow: none;
                border: 1px solid #e0e6ed;
                margin-bottom: 12px;
                padding: 6px;
                page-break-inside: avoid;
              }
              .date-group h3 {
                font-size: 12px;
                margin-bottom: 6px;
                padding: 4px 8px;
              }
              .destination-group {
                margin-bottom: 10px;
                page-break-inside: avoid;
              }
              .destination-group h4 {
                font-size: 11px;
                margin: 6px 0 4px;
                padding: 3px 0;
              }
              table {
                margin-bottom: 8px;
                font-size: 10px;
                page-break-inside: auto;
              }
              th {
                padding: 4px 5px;
                font-size: 10px;
                text-align: center;
              }
              td {
                padding: 3px 5px;
                font-size: 10px;
                text-align: center;
              }
              td.number {
                text-align: center;
              }
              tr {
                page-break-inside: avoid;
              }
              thead {
                display: table-header-group;
              }
              tfoot {
                display: table-footer-group;
              }
              h2, h3, h4 {
                page-break-after: avoid;
              }
              .date-summary {
                margin-top: 8px;
                margin-bottom: 4px;
                page-break-inside: avoid;
              }
              .summary-table {
                border: 2px solid #1a73e8;
                background-color: #f0f7ff;
              }
              .summary-table td {
                padding: 6px 5px;
                font-size: 11px;
                text-align: center;
              }
              .summary-label {
                font-size: 11px;
              }
              .summary-value {
                font-size: 11px;
              }
              .page-header {
                margin-bottom: 8px;
              }
              .print-date {
                margin-bottom: 6px;
                font-size: 9px;
              }
            }
          </style>
        </head>
        <body onload="window.print()">
          <div class="page-header">
            <div class="company-info">
              Smart-EMAP 管理システム
            </div>
            <div class="print-date">
              印刷日時: ${new Date().toLocaleString('ja-JP')}
            </div>
          </div>
          <h2>🚚 日別受注履歴</h2>
          ${filterText}
          ${printContent}
        </body>
      </html>
    `)
    printWindow.document.close()
    printWindow.focus()
    printWindow.print()
    printWindow.close()
  } catch (error) {
    console.error('印刷エラー', error)
    ElMessage.error('印刷に失敗しました')
  }
}

// Excel导出履歴
const handleExport = () => {
  if (orderList.value.length === 0) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }
  const exportData = orderList.value.map((item) => ({
    年: item.year,
    月: item.month,
    日: item.day,
    納入先CD: item.destination_cd,
    納入先名: item.destination_name,
    製品CD: item.product_cd,
    製品名: item.product_name,
    確定箱数: item.confirmed_boxes,
    確定本数: item.confirmed_units,
    状態: item.status,
  }))
  const worksheet = XLSX.utils.json_to_sheet(exportData)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '日別出荷履歴')
  const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
  const exportDate = dayjs(filters.value.dateRange[0]).format('YYYY_MM')
  saveAs(
    new Blob([excelBuffer], { type: 'application/octet-stream' }),
    `日別出荷履歴_${exportDate}.xlsx`,
  )
}

onMounted(async () => {
  await fetchOptions()
  fetchList()
})
</script>

<style scoped>
/* 现代化紧凑页面样式 */
.modern-daily-history-page {
  min-height: calc(100vh - 84px);
  background: #f5f7fa;
  position: relative;
  padding: 12px;
}

/* 页面头部样式 - 紧凑版 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  position: relative;
  overflow: hidden;
  margin-bottom: 12px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Ccircle cx='20' cy='20' r='1.5'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
  opacity: 0.5;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
  max-width: 100%;
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
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
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
  line-height: 1.2;
  color: white;
}

.page-subtitle {
  font-size: 0.85rem;
  margin: 4px 0 0;
  opacity: 0.9;
  font-weight: 400;
}


/* 装饰元素 - 简化 */
.header-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.floating-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(5px);
}

.circle-1 {
  width: 60px;
  height: 60px;
  top: -30px;
  right: 10%;
  opacity: 0.6;
}

.circle-2 {
  width: 40px;
  height: 40px;
  bottom: -20px;
  left: 15%;
  opacity: 0.5;
}

/* 筛选区域样式 - 紧凑版 */
.filter-section {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 1;
}

.filter-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px 12px 0 0;
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
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.filter-icon {
  font-size: 16px;
  color: #667eea;
}

.filter-stats {
  display: flex;
  gap: 8px;
}

.stats-text {
  padding: 4px 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.modern-filter-form {
  margin: 0;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.filter-item {
  flex: 1;
  min-width: 200px;
  margin-bottom: 0;
}

.custom-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
  font-size: 13px;
}

.custom-label .el-icon {
  font-size: 14px;
  color: #667eea;
}

.date-picker,
.select-input {
  width: 100%;
  border-radius: 8px;
}

.date-picker :deep(.el-input__wrapper),
.select-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
  padding: 4px 11px;
}

.date-picker :deep(.el-input__wrapper:hover),
.select-input :deep(.el-input__wrapper:hover) {
  border-color: #667eea;
}

.date-picker :deep(.el-input__wrapper.is-focus),
.select-input :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.filter-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.search-btn {
  height: 36px;
  padding: 0 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.search-btn:hover {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  transform: translateY(-1px);
}

.reset-btn {
  height: 36px;
  padding: 0 14px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #64748b;
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.reset-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.reset-btn .el-icon {
  font-size: 14px;
}

/* 数据展示区域样式 - 紧凑版 */
.data-section {
  margin: 0;
  position: relative;
  z-index: 1;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.section-icon {
  font-size: 18px;
  color: #667eea;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-actions .print-btn {
  height: 36px;
  padding: 0 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.section-actions .print-btn:hover {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.section-actions .print-btn .el-icon {
  font-size: 16px;
}

.data-summary {
  display: flex;
  gap: 12px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 14px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  min-width: 80px;
}

.summary-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  margin-bottom: 2px;
}

.summary-value {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

/* 简约风格表格样式 */
.simple-table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.simple-table {
  width: 100%;
}

.simple-table :deep(.el-table__header) th {
  background: #f8f9fa;
  color: #374151;
  font-weight: 600;
  padding: 12px 0;
  border-bottom: 2px solid #e5e7eb;
  font-size: 13px;
  text-align: center;
}

.simple-table :deep(.el-table__header-wrapper) {
  border-bottom: 2px solid #e5e7eb;
}

.simple-table :deep(.el-table__row) {
  transition: background-color 0.15s ease;
}

.simple-table :deep(.el-table__row:hover) {
  background-color: #f8f9fa !important;
}

.simple-table :deep(.el-table__row.even-row) {
  background-color: white;
}

.simple-table :deep(.el-table__row.odd-row) {
  background-color: #fafbfc;
}

.simple-table :deep(.el-table__cell) {
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}

.simple-table :deep(.el-table__body tr:last-child td) {
  border-bottom: none;
}

/* 简约单元格样式 */
.date-cell {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
}

.code-cell {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
}

.name-cell {
  font-weight: 400;
  color: #1f2937;
  font-size: 13px;
}

.number-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  font-weight: 500;
}

.number-cell .number {
  color: #374151;
  font-size: 13px;
}

.number-cell .unit {
  font-size: 12px;
  color: #6b7280;
  font-weight: 400;
}

.status-cell {
  display: flex;
  justify-content: center;
}

.status-tag {
  border-radius: 4px;
  font-weight: 500;
  padding: 4px 10px;
  border: none;
  font-size: 12px;
}

.status-tag.status-shipped {
  background: #d1fae5;
  color: #065f46;
}

.status-tag.status-cancelled {
  background: #fee2e2;
  color: #991b1b;
}

.status-tag.status-pending {
  background: #f3f4f6;
  color: #374151;
}

/* 简约分页器样式 */
.modern-pagination {
  padding: 12px 16px;
  display: flex;
  justify-content: center;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.modern-pagination :deep(.el-pagination) {
  gap: 4px;
}

.modern-pagination :deep(.el-pager li) {
  border-radius: 4px;
  transition: all 0.15s ease;
  min-width: 32px;
  height: 32px;
  line-height: 32px;
  font-size: 13px;
  border: 1px solid #e5e7eb;
  background: white;
}

.modern-pagination :deep(.el-pager li:hover) {
  background: #f8f9fa;
  border-color: #d1d5db;
}

.modern-pagination :deep(.el-pager li.is-active) {
  background: #374151;
  color: white;
  border-color: #374151;
}

.modern-pagination :deep(.btn-prev),
.modern-pagination :deep(.btn-next) {
  min-width: 32px;
  height: 32px;
  line-height: 32px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: white;
}

.modern-pagination :deep(.btn-prev:hover),
.modern-pagination :deep(.btn-next:hover) {
  background: #f8f9fa;
  border-color: #d1d5db;
}

.modern-pagination :deep(.el-pagination__total),
.modern-pagination :deep(.el-pagination__sizes) {
  font-size: 13px;
  height: 32px;
  line-height: 32px;
  color: #6b7280;
}

.modern-pagination :deep(.el-pagination__sizes .el-select .el-input__wrapper) {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .page-header {
    padding: 14px 16px;
  }

  .filter-section {
    padding: 14px;
  }
}

@media screen and (max-width: 768px) {
  .modern-daily-history-page {
    padding: 8px;
  }

  .page-header {
    padding: 12px 14px;
    margin-bottom: 10px;
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

  .page-title {
    font-size: 1.3rem;
  }

  .page-subtitle {
    font-size: 0.8rem;
  }

  .filter-section {
    padding: 12px;
    margin-bottom: 10px;
  }

  .filter-row {
    flex-direction: column;
    gap: 10px;
  }

  .filter-item {
    min-width: unset;
    width: 100%;
  }

  .filter-actions {
    width: 100%;
    justify-content: stretch;
  }

  .search-btn,
  .reset-btn {
    flex: 1;
    justify-content: center;
  }

  .data-summary {
    flex-direction: row;
    gap: 8px;
  }

  .summary-item {
    flex: 1;
    padding: 6px 10px;
  }

  .section-header {
    flex-direction: row;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .section-actions {
    margin-left: auto;
  }

  .section-actions .print-btn {
    height: 32px;
    padding: 0 12px;
    font-size: 13px;
  }

  .circle-1,
  .circle-2 {
    display: none;
  }
}

@media screen and (max-width: 480px) {
  .page-title {
    font-size: 1.2rem;
  }

  .filter-section {
    padding: 10px;
  }

  .modern-pagination {
    padding: 10px 12px;
  }

  .modern-pagination :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }
}

/* 打印样式 */
@media print {

  .filter-section,
  .modern-pagination,
  .section-actions {
    display: none !important;
  }

  .modern-daily-history-page {
    background: white;
    padding: 0;
  }

  .page-header {
    background: white;
    color: black;
    padding: 12px 0;
    margin-bottom: 12px;
  }

  .simple-table-container {
    box-shadow: none;
    border: 1px solid #e5e7eb;
  }
}
</style>
