<template>
  <div class="modern-destination-history">
    <!-- 现代化页面头部 -->
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

    <!-- 现代化筛选区域 -->
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
            <el-select v-model="filters.destination_cd" placeholder="納入先を選択" clearable filterable class="select-input">
              <el-option v-for="item in destinationOptions" :key="item.cd" :label="`${item.cd} - ${item.name}`"
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

    <!-- 月別集計区域 -->
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
                <span class="unit">個</span>
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
                <span class="number">{{ row.total_amount?.toLocaleString() }}</span>
                <span class="unit">円</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 受注明細区域 -->
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

          <el-table-column label="納入先名" prop="destination_name" min-width="160" align="center" show-overflow-tooltip>
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

          <el-table-column label="製品名" prop="product_name" min-width="160" align="center" show-overflow-tooltip>
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Goods />
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

          <el-table-column label="単価" prop="unit_price" width="110" align="center">
            <template #header>
              <div class="table-header">
                <el-icon>
                  <PriceTag />
                </el-icon>
                <span>単価</span>
              </div>
            </template>
            <template #default="{ row }">
              <div class="number-cell price">
                <span class="number">{{ row.unit_price?.toLocaleString() }}</span>
                <span class="unit">円</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="金額" prop="total_price" width="130" align="center">
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
                <span class="number">{{ row.total_price?.toLocaleString() }}</span>
                <span class="unit">円</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="状態" prop="status" width="110" align="center">
            <template #header>
              <div class="table-header">
                <el-icon>
                  <Flag />
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
import { getDestinationOptions } from '@/api/options'
import dayjs from 'dayjs'
import timezone from 'dayjs/plugin/timezone'
import utc from 'dayjs/plugin/utc'
import 'dayjs/locale/ja'

// 配置dayjs
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.locale('ja')
import { ElMessage } from 'element-plus'

// 納入日計算関数（土日と祝日を除外）- 优化版本
const calculateDeliveryDate = (
  orderDate: string,
  leadTime: number = 0,
  holidays: string[] = [],
  workdays: string[] = [],
) => {
  if (leadTime === 0) return orderDate

  try {
    let currentDate = dayjs(orderDate)
    let workDaysCount = 0

    while (workDaysCount < leadTime) {
      currentDate = currentDate.add(1, 'day')
      const dateStr = currentDate.format('YYYY-MM-DD')

      // 土日チェック
      const isWeekend = currentDate.day() === 0 || currentDate.day() === 6

      // 祝日チェック
      const isHoliday = holidays.includes(dateStr)

      // 臨時出勤日チェック
      const isOverrideWorkday = workdays.includes(dateStr)

      // 平日（土日でなく、祝日でない、または臨時出勤日）の場合のみカウント
      if ((!isWeekend && !isHoliday) || isOverrideWorkday) {
        workDaysCount++
      }
    }

    return currentDate.format('YYYY-MM-DD')
  } catch (error) {
    console.error('納入日計算エラー:', error)
    // エラーの場合は単純に日数を足す
    return dayjs(orderDate).add(leadTime, 'day').format('YYYY-MM-DD')
  }
}
import {
  OfficeBuilding,
  Printer,
  Search,
  Calendar,
  TrendCharts,
  Box,
  Money,
  List,
  Goods,
  PriceTag,
  Flag,
} from '@element-plus/icons-vue'

const filters = ref({
  destination_cd: '',
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
  unit_price: number
  total_price: number
  status: string
  delivery_date: string
}

interface MonthlySummaryItem {
  ym: string
  total_quantity: number
  total_amount: number
}

const orderList = ref<OrderHistoryItem[]>([])
const summaryList = ref<MonthlySummaryItem[]>([])
const destinationOptions = ref<{ cd: string; name: string }[]>([])

// 过滤数量大于0的订单
const filteredOrderList = computed(() => {
  return orderList.value.filter((order) => order.quantity > 0)
})

// 获取状态标签类型
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

// 获取状态样式类
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

// 📥 納入先選択肢取得
const loadOptions = async () => {
  destinationOptions.value = await getDestinationOptions()
}

// 📊 検索
const fetchData = async () => {
  if (!filters.value.destination_cd || filters.value.date_range.length !== 2) {
    return
  }

  const [start_date, end_date] = filters.value.date_range

  try {
    const [orders, summary] = await Promise.all([
      request.get('/api/order/destination-history', {
        params: { destination_cd: filters.value.destination_cd, start_date, end_date },
      }),
      request.get('/api/order/destination-monthly-summary', {
        params: { destination_cd: filters.value.destination_cd, start_date, end_date },
      }),
    ])

    orderList.value = orders
    summaryList.value = summary
  } catch (error) {
    console.error('データ取得エラー:', error)
  }
}

// 打印功能
const handlePrint = async () => {
  if (filteredOrderList.value.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  // 显示加载提示
  const loadingMessage = ElMessage({
    message: '印刷データを準備中...',
    type: 'info',
    duration: 0, // 不自动关闭
    showClose: false,
  })

  try {
    // 获取筛选条件信息
    const filterInfo = []
    if (filters.value.date_range?.length === 2) {
      filterInfo.push(`期間: ${filters.value.date_range[0]} ~ ${filters.value.date_range[1]}`)
    }
    if (filters.value.destination_cd) {
      const dest = destinationOptions.value.find((d) => d.cd === filters.value.destination_cd)
      filterInfo.push(
        `納入先: ${dest ? `${dest.cd} - ${dest.name}` : filters.value.destination_cd}`,
      )
    }
    const filterText =
      filterInfo.length > 0
        ? `<div class="filter-info">検索条件: ${filterInfo.join(' / ')}</div>`
        : ''

    // 打印窗口
    const printWindow = window.open('', '', 'width=1000,height=800')
    if (!printWindow) {
      loadingMessage.close()
      return ElMessage.error('印刷ウィンドウを開けません')
    }

    // 创建二维表式数据
    const create2DTable = () => {
      const products = [...new Set(filteredOrderList.value.map((item) => item.product_name))].sort()
      const dates = [...new Set(filteredOrderList.value.map((item) => item.order_date))].sort()

      let tableHTML = '<table class="table-2d">'

      // 表头
      tableHTML += '<thead><tr><th>製品名</th>'
      dates.forEach((date) => {
        tableHTML += `<th class="date-header">${date}</th>`
      })
      tableHTML += '<th>合計</th></tr></thead>'

      // 表体
      tableHTML += '<tbody>'
      products.forEach((product) => {
        tableHTML += `<tr><td class="product-name">${product}</td>`
        let productTotal = 0

        dates.forEach((date) => {
          const order = filteredOrderList.value.find(
            (item) => item.product_name === product && item.order_date === date,
          )
          const quantity = order ? order.quantity : 0
          productTotal += quantity
          tableHTML += `<td class="number">${quantity > 0 ? quantity.toLocaleString() : ''}</td>`
        })

        tableHTML += `<td class="number total">${productTotal.toLocaleString()}</td></tr>`
      })

      // 合计行
      tableHTML += '<tr class="total-row"><td class="total-label">合計</td>'
      let grandTotal = 0
      dates.forEach((date) => {
        const dateTotal = filteredOrderList.value
          .filter((item) => item.order_date === date)
          .reduce((sum, item) => sum + item.quantity, 0)
        grandTotal += dateTotal
        tableHTML += `<td class="number total">${dateTotal > 0 ? dateTotal.toLocaleString() : ''}</td>`
      })
      tableHTML += `<td class="number grand-total">${grandTotal.toLocaleString()}</td></tr>`

      tableHTML += '</tbody></table>'
      return tableHTML
    }

    // 計算正確的納入日（优化版本）
    const calculateCorrectDeliveryDates = async () => {
      // 获取所有唯一的纳入先代码
      const uniqueDestinationCds = [
        ...new Set(filteredOrderList.value.map((order) => order.destination_cd)),
      ]

      // 批量获取纳入先信息，避免重复请求
      const destinationMap = new Map()
      const holidayMap = new Map()
      const workdayMap = new Map()

      // 检查是否启用假日计算（如果API有问题可以禁用）
      // 如果destination-holiday API持续有问题，可以设置为false来禁用假日计算
      const enableHolidayCalculation = false // 临时禁用假日计算以避免API阻塞

      try {
        // 并发获取所有纳入先的lead time信息
        const destinationPromises = uniqueDestinationCds.map(async (destinationCd) => {
          try {
            const response = await request.get('/api/master/destinations', {
              params: { keyword: destinationCd },
            })
            const leadTime = response.data.length > 0 ? response.data[0].delivery_lead_time || 0 : 0
            destinationMap.set(destinationCd, leadTime)
          } catch (error) {
            console.error(`納入先 ${destinationCd} の情報取得エラー:`, error)
            destinationMap.set(destinationCd, 0)
          }
        })

        // 并发获取所有纳入先的假日信息（可选，添加超时和错误处理）
        const holidayPromises = enableHolidayCalculation
          ? uniqueDestinationCds.map(async (destinationCd) => {
            try {
              // 创建超时Promise
              const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('API请求超时')), 3000) // 3秒超时
              })

              // 创建API请求Promise
              const apiPromise = Promise.all([
                request.get('/api/master/destination-holiday', {
                  params: { destination_cd: destinationCd },
                  timeout: 3000, // 3秒超时
                }),
                request.get('/api/master/destination-holiday/workday', {
                  params: { destination_cd: destinationCd },
                  timeout: 3000, // 3秒超时
                }),
              ])

              // 使用Promise.race来实现超时控制
              const result = (await Promise.race([apiPromise, timeoutPromise])) as [any, any]

              const [holidayResponse, workdayResponse] = result

              const holidays = holidayResponse?.map((h: any) => h.holiday_date) || []
              const workdays = workdayResponse?.map((w: any) => w.work_date) || []

              holidayMap.set(destinationCd, holidays)
              workdayMap.set(destinationCd, workdays)
            } catch (error) {
              console.warn(
                `納入先 ${destinationCd} の祝日情報取得エラー（デフォルト値を使用）:`,
                error,
              )
              // 使用空数组作为默认值，这样计算时只会考虑土日
              holidayMap.set(destinationCd, [])
              workdayMap.set(destinationCd, [])
            }
          })
          : []

        // 等待所有信息获取完成，但不要因为假日API失败而阻塞整个流程
        try {
          await Promise.all([...destinationPromises, ...holidayPromises])
        } catch (error) {
          console.warn('部分API请求失败，继续使用可用数据:', error)
          // 即使部分API失败，也继续处理
        }

        // 批量计算纳入日，使用同步处理（因为不再需要API调用）
        const ordersWithCorrectDeliveryDates = filteredOrderList.value.map((order) => {
          try {
            const leadTime = destinationMap.get(order.destination_cd) || 0
            const holidays = holidayMap.get(order.destination_cd) || []
            const workdays = workdayMap.get(order.destination_cd) || []

            // 如果lead time为0，直接使用订单日期
            if (leadTime === 0) {
              return {
                ...order,
                delivery_date: order.order_date,
              }
            }

            // 计算正确的纳入日
            const correctDeliveryDate = calculateDeliveryDate(
              order.order_date,
              leadTime,
              holidays,
              workdays,
            )

            return {
              ...order,
              delivery_date: correctDeliveryDate,
            }
          } catch (error) {
            console.error('納入日計算エラー:', error)
            // エラーの場合は元のdelivery_dateを使用
            return order
          }
        })

        return ordersWithCorrectDeliveryDates
      } catch (error) {
        console.error('納入日計算処理エラー:', error)
        // 如果批量处理失败，返回原始订单数据
        return filteredOrderList.value
      }
    }

    // 計算正確的納入日
    const ordersWithCorrectDeliveryDates = await calculateCorrectDeliveryDates()

    printWindow.document.write(`
    <html>
      <head>
        <title>納入先別出荷リスト</title>
        <style>
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          body {
            font-family: "Yu Gothic", "Hiragino Kaku Gothic Pro", "Meiryo", sans-serif;
            padding: 8px;
            color: #000000;
            font-size: 10px;
            line-height: 1.2;
          }
          .print-info {
            text-align: right;
            color: #000000;
            font-size: 9px;
            margin-bottom: 8px;
          }
          h2 {
            text-align: center;
            font-size: 16px;
            margin-bottom: 12px;
            padding-bottom: 4px;
            border-bottom: 1px solid #000000;
            color: #000000;
          }
          .filter-info {
            margin: 4px 0 8px;
            padding: 4px 6px;
            background: #f8f9fa;
            border-radius: 2px;
            font-size: 9px;
            color: #000000;
          }
          h3 {
            font-size: 12px;
            margin: 8px 0 4px;
            color: #000000;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 8px;
            font-size: 9px;
          }
          th, td {
            border: 1px solid #000000;
            padding: 2px 3px;
            text-align: center;
            vertical-align: middle;
            color: #000000;
          }
          th {
            background-color: #f0f0f0;
            font-weight: bold;
            font-size: 8px;
            color: #000000;
          }
          .table-2d th {
            background-color: #e0e0e0;
            font-size: 8px;
            padding: 1px 2px;
            color: #000000;
          }
          .table-2d td {
            padding: 1px 2px;
            font-size: 8px;
            color: #000000;
          }
          .date-header {
            writing-mode: vertical-rl;
            text-orientation: mixed;
            width: 20px;
            min-width: 20px;
          }
          .product-name {
            text-align: left;
            font-weight: bold;
            max-width: 80px;
            word-break: break-all;
            color: #000000;
          }
          .number {
            text-align: right;
            font-family: 'Courier New', monospace;
            color: #000000;
          }
          .total {
            background-color: #f8f8f8;
            font-weight: bold;
            color: #000000;
          }
          .total-row {
            background-color: #e8e8e8;
            font-weight: bold;
            color: #000000;
          }
          .total-label {
            text-align: left;
            font-weight: bold;
            color: #000000;
          }
          .grand-total {
            background-color: #d0d0d0;
            font-weight: bold;
            color: #000000;
          }
          .center {
            text-align: center;
            color: #000000;
          }
          @media print {
            body {
              padding: 4px;
            }
            table {
              page-break-inside: auto;
            }
            tr {
              page-break-inside: avoid;
            }
            thead {
              display: table-header-group;
            }
            .table-2d {
              font-size: 7px;
            }
            .table-2d th, .table-2d td {
              padding: 1px;
            }
          }
        </style>
      </head>
      <body>
        <div class="print-info">
          印刷日時: ${dayjs().tz('Asia/Tokyo').format('YYYY年MM月DD日 HH:mm')}
        </div>
        <h2>納入先別出荷履歴</h2>
        ${filterText}
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
                <td class="number">${item.total_amount?.toLocaleString() ?? ''}</td>
              </tr>
            `,
        )
        .join('')}
          </tbody>
        </table>
        <h3>出荷明細（二次元表）</h3>
        ${create2DTable()}
        <h3>出荷明細（一覧表）</h3>
        <table>
          <thead>
            <tr>
              <th>出荷日</th>
              <th>納入先名</th>
              <th>製品名</th>
              <th>数量</th>
              <th>単価</th>
              <th>金額</th>
              <th>納入日</th>
            </tr>
          </thead>
          <tbody>
            ${ordersWithCorrectDeliveryDates
        .map(
          (item) => `
              <tr>
                <td class="center">${item.order_date}</td>
                <td>${item.destination_name}</td>
                <td>${item.product_name}</td>
                <td class="number">${item.quantity?.toLocaleString() ?? ''}</td>
                <td class="number">${item.unit_price?.toLocaleString() ?? '0'}円</td>
                <td class="number">${item.total_price?.toLocaleString() ?? '0'}円</td>
                <td class="center">${item.delivery_date || '-'}</td>
              </tr>
            `,
        )
        .join('')}
          </tbody>
        </table>
      </body>
    </html>
  `)

    printWindow.document.close()
    printWindow.focus()
    printWindow.print()
    printWindow.close()

    // 关闭加载提示
    loadingMessage.close()
    ElMessage.success('印刷データの準備が完了しました')
  } catch (error) {
    console.error('印刷処理エラー:', error)
    loadingMessage.close()
    ElMessage.error('印刷データの準備中にエラーが発生しました')
  }
}

loadOptions()
</script>

<style scoped>
/* 页面容器 - 紧凑简洁 */
.modern-destination-history {
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

.header-actions {
  display: flex;
  gap: 8px;
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

/* 移除装饰元素 */
.header-decoration {
  display: none;
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

.filter-section::before {
  display: none;
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
  color: #dc2626;
}

.number-cell.amount {
  color: #7c3aed;
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

  .page-title {
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

  .page-title {
    font-size: 1.25rem;
  }

  .page-subtitle {
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

  .page-title {
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
  .modern-destination-history {
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
