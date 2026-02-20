<template>
  <div class="shipping-report">
    <!-- 报告头部 - 单行布局 (第一页) -->
    <div class="report-header">
      <div class="header-content">
        <span class="header-shipping-date"
          >出荷日: {{ formatShippingDate(filters.dateRange) }}</span
        >
        <h1 class="report-title">出荷品報告書</h1>
        <span class="header-print-time">印刷日時: {{ printDateTime }}</span>
      </div>
    </div>

    <!-- 分页预览信息 -->
    <div class="pagination-info" v-if="showPaginationInfo">
      <div class="info-item">
        <span class="label">総ページ数:</span>
        <span class="value">{{ totalPages }}ページ</span>
      </div>
      <div class="info-item">
        <span class="label">納入先数:</span>
        <span class="value">{{ totalDestinations }}件</span>
      </div>
      <div class="info-item">
        <span class="label">最適化率:</span>
        <span class="value">{{ optimizationRate }}%</span>
      </div>
    </div>

    <!-- 报告内容 -->
    <div class="report-body">
      <div
        v-for="(destGroup, index) in optimizedGroupedData"
        :key="`${destGroup.destination_name}-${index}`"
        class="destination-section"
        :class="{
          'page-break-before': destGroup.needPageBreak,
          'first-section': index === 0,
        }"
      >
        <!-- 每页头部 (除第一页外) -->
        <div v-if="destGroup.needPageBreak" class="page-header">
          <div class="header-content">
            <span class="header-shipping-date"
              >出荷日: {{ formatShippingDate(filters.dateRange) }}</span
            >
            <h1 class="report-title">出荷品報告書</h1>
            <span class="header-print-time">印刷日時: {{ printDateTime }}</span>
          </div>
        </div>

        <!-- 納入先名标题 -->
        <h2 class="destination-title">{{ destGroup.destination_name }}</h2>

        <!-- 产品表格 -->
        <table class="report-table">
          <thead>
            <tr>
              <th>出荷No</th>
              <th>製品名</th>
              <th>製品種類</th>
              <th>箱タイプ</th>
              <th>受注数</th>
              <th>受注本数</th>
              <th>納入日</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, itemIndex) in destGroup.items" :key="itemIndex">
              <td>{{ item.shipping_no }}</td>
              <td>{{ item.product_name }}</td>
              <td>{{ item.product_type || '-' }}</td>
              <td>{{ item.box_type || '-' }}</td>
              <td>{{ item.quantity }}</td>
              <td>{{ item.units || '-' }}</td>
              <td>{{ formatDate(item.delivery_date) }}</td>
            </tr>
          </tbody>
        </table>

        <!-- 納入先合計 -->
        <div class="destination-summary">
          <table class="summary-table">
            <tbody>
              <tr>
                <td class="summary-label">{{ destGroup.destination_name }} 合計</td>
                <td class="summary-value">受注箱数: {{ destGroup.totalQuantity }}</td>
                <td class="summary-value">受注本数: {{ destGroup.totalUnits }}</td>
                <td class="summary-value">出荷パレ数: {{ destGroup.shippingNoCount }}</td>
              </tr>
            </tbody>
          </table>
          <div class="separator-line"></div>
        </div>

        <!-- 页面信息 (仅在预览模式下显示) -->
        <div v-if="showPaginationInfo && destGroup.pageInfo" class="page-info">
          <span>ページ {{ destGroup.pageInfo.currentPage }} / {{ totalPages }}</span>
          <span>使用率: {{ destGroup.pageInfo.utilizationRate }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  filters: {
    type: Object,
    default: () => ({}),
  },
  showPaginationInfo: {
    type: Boolean,
    default: false, // 预览模式时显示分页信息
  },
})

const printDateTime = computed(() => {
  const now = new Date()
  return now.toLocaleString('ja-JP')
})

function formatShippingDate(dateRange) {
  if (!dateRange || dateRange.length !== 2) return 'N/A'
  if (dateRange[0] === dateRange[1]) {
    return formatDate(dateRange[0])
  }
  return `${formatDate(dateRange[0])} ~ ${formatDate(dateRange[1])}`
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  // 使用日本标准时间格式化日期
  const date = new Date(dateStr + 'T00:00:00+09:00') // 确保使用JST时区
  return date.toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo' })
}

// 页面配置常量
const PAGE_CONFIG = {
  maxRowsPerPage: 46, // 与 ShippingListReport.vue 保持一致的最大行数
  headerHeight: 4, // 报告头部高度 (单行优化)
  pageHeaderHeight: 4, // 每页头部高度 (除第一页)
  sectionTitleHeight: 1.5, // 納入先标题高度
  tableHeaderHeight: 1, // 表格头部高度
  summaryHeight: 2.5, // 合计区域高度
  marginHeight: 1, // 间距高度 (减少间距)
  minSectionHeight: 6, // 最小section高度
  targetUtilization: 95, // 目标占用率95%
  maxUtilization: 98, // 最大占用率98%
}

// 精确计算每个 section 高度（行数），与现有样式一致，不改变样式
function calculateSectionHeight(destGroup) {
  const { sectionTitleHeight, tableHeaderHeight, summaryHeight, marginHeight } = PAGE_CONFIG
  const itemRows = destGroup.items?.length ?? 0
  return sectionTitleHeight + tableHeaderHeight + itemRows + summaryHeight + marginHeight
}

/** 第一步：先算出所有納入先各自占的行数 */
function getSectionsWithHeights(destinations) {
  return destinations.map((dest, index) => ({
    ...dest,
    height: calculateSectionHeight(dest),
    originalIndex: index,
    id: `${dest.destination_name}-${index}`,
  }))
}

/** 单页背包：在容量内选出总高度最大的一组 section（0/1 背包），用于最少页数 */
function packOnePage(sections, capacity) {
  const UNIT = 0.5
  const toUnit = (v) => Math.round(v / UNIT)
  const capUnit = toUnit(capacity)
  const dp = Array(capUnit + 1).fill(null)
  dp[0] = { height: 0, list: [] }

  sections.forEach((sec) => {
    const hUnit = toUnit(sec.height)
    if (hUnit > capUnit) return
    for (let c = capUnit; c >= hUnit; c--) {
      if (dp[c - hUnit]) {
        const candHeight = dp[c - hUnit].height + hUnit
        if (!dp[c] || candHeight > dp[c].height) {
          dp[c] = {
            height: candHeight,
            list: [...dp[c - hUnit].list, sec],
          }
        }
      }
    }
  })

  let best = null
  for (let c = capUnit; c >= 0; c--) {
    if (dp[c]) {
      best = dp[c]
      break
    }
  }
  const list = best?.list || []
  return { chosen: list, usedHeight: list.reduce((sum, s) => sum + s.height, 0) }
}

/** 第二步：从第一页开始循环试着排版，找到最少打印页数（保持现有样式不变） */
function allocateMinimumPages(destinations) {
  const { maxRowsPerPage, headerHeight, pageHeaderHeight } = PAGE_CONFIG
  const firstPageCap = maxRowsPerPage - headerHeight
  const otherPageCap = maxRowsPerPage - pageHeaderHeight

  const sections = getSectionsWithHeights(destinations)
  const pages = []
  let remaining = [...sections]
  let pageIndex = 0

  while (remaining.length > 0) {
    const capacity = pageIndex === 0 ? firstPageCap : otherPageCap
    const { chosen } = packOnePage(remaining, capacity)

    const chosenList = chosen.length > 0 ? chosen : [remaining[0]]
    const usedHeight = chosenList.reduce((sum, s) => sum + s.height, 0)

    pages.push({
      sections: chosenList,
      height: usedHeight,
      remainingHeight: Math.max(0, capacity - usedHeight),
      utilizationRate: Math.round((usedHeight / capacity) * 100),
      isFirstPage: pageIndex === 0,
    })

    const chosenIds = new Set(chosenList.map((s) => s.id))
    remaining = remaining.filter((s) => !chosenIds.has(s.id))
    pageIndex++
  }

  return generateResultWithHeaders(pages, firstPageCap, otherPageCap)
}

/** 生成带页头信息的最终结果（样式与模板不变） */
function generateResultWithHeaders(pages, firstPageHeight, otherPageHeight) {
  pages.forEach((page, pageIndex) => {
    page.sections.sort((a, b) => a.destination_name.localeCompare(b.destination_name))
    page.sections.forEach((section) => {
      section.pageInfo = {
        currentPage: pageIndex + 1,
        utilizationRate: page.utilizationRate,
      }
    })
  })

  pages.sort((a, b) => {
    const aFirstName = a.sections[0]?.destination_name || ''
    const bFirstName = b.sections[0]?.destination_name || ''
    return aFirstName.localeCompare(bFirstName)
  })

  const result = []
  pages.forEach((page, pageIndex) => {
    page.sections.forEach((section, sectionIndex) => {
      result.push({
        ...section,
        needPageBreak: pageIndex > 0 && sectionIndex === 0,
      })
    })
  })

  return { result, pages }
}

// 按納入先分组数据，并应用智能分页
const optimizedGroupedData = computed(() => {
  if (!props.data || props.data.length === 0) return []

  const destMap = new Map()

  props.data.forEach((item) => {
    const destName = item.destination_name
    if (!destMap.has(destName)) {
      destMap.set(destName, [])
    }
    destMap.get(destName).push(item)
  })

  const destinations = []
  destMap.forEach((items, destination_name) => {
    const sortedItems = items.sort((a, b) => a.product_name.localeCompare(b.product_name))

    const totalQuantity = sortedItems.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0)
    const totalUnits = sortedItems.reduce((sum, item) => sum + (Number(item.units) || 0), 0)
    const uniqueShippingNos = new Set(sortedItems.map((item) => item.shipping_no))
    const shippingNoCount = uniqueShippingNos.size

    destinations.push({
      destination_name,
      items: sortedItems,
      totalQuantity,
      totalUnits,
      shippingNoCount,
    })
  })

  const sortedDestinations = destinations.sort((a, b) =>
    a.destination_name.localeCompare(b.destination_name),
  )

  const { result, pages } = allocateMinimumPages(sortedDestinations)

  // 存储分页信息供其他computed使用
  paginationResult.value = { result, pages }

  return result
})

// 存储分页结果的响应式变量
const paginationResult = ref({ result: [], pages: [] })

// 计算总页数
const totalPages = computed(() => {
  return paginationResult.value.pages?.length || 0
})

// 计算总納入先数
const totalDestinations = computed(() => {
  const destNames = new Set()
  props.data?.forEach((item) => destNames.add(item.destination_name))
  return destNames.size
})

// 计算优化率
const optimizationRate = computed(() => {
  if (!paginationResult.value.pages?.length) return 0

  const avgUtilization =
    paginationResult.value.pages.reduce((sum, page) => sum + page.utilizationRate, 0) /
    paginationResult.value.pages.length

  return Math.round(avgUtilization)
})

// 导出分页分析函数供外部调用
const getPaginationAnalysis = () => {
  const pages = paginationResult.value.pages
  if (!pages?.length) return null

  return {
    totalPages: pages.length,
    totalDestinations: totalDestinations.value,
    averageUtilization: optimizationRate.value,
    pageDetails: pages.map((page, index) => ({
      pageNumber: index + 1,
      sectionsCount: page.sections.length,
      utilizationRate: page.utilizationRate,
      destinationNames: page.sections.map((s) => s.destination_name),
    })),
  }
}

// 暴露给父组件
defineExpose({
  getPaginationAnalysis,
})
</script>

<style scoped>
@page {
  size: A4 portrait;
  margin: 0.8cm;
}

.shipping-report {
  font-family: 'Yu Gothic', 'Hiragino Sans', 'Meiryo', 'MS Gothic', sans-serif;
  color: #1a1a1a;
  background: #fff;
  padding: 16px;
  line-height: 1.3;
  position: relative;
}

.shipping-report::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.03) 0%, transparent 50%);
  pointer-events: none;
  z-index: -1;
}

/* 分页信息样式 */
.pagination-info {
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.info-item .label {
  font-size: 12px;
  opacity: 0.9;
  font-weight: 500;
}

.info-item .value {
  font-size: 16px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* 页面信息样式 */
.page-info {
  margin-top: 8px;
  padding: 6px 12px;
  background: rgba(102, 126, 234, 0.1);
  border-left: 3px solid #667eea;
  font-size: 11px;
  color: #667eea;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  border-radius: 0 4px 4px 0;
}

/* 头部样式 - 单行布局优化 */
.report-header {
  border-bottom: 2px solid #2c3e50;
  padding: 8px 0;
  margin-bottom: 16px;
  background: linear-gradient(to right, #f8f9fa, #ffffff, #f8f9fa);
  border-radius: 6px 6px 0 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  position: relative;
  page-break-inside: avoid;
}

.report-header::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(to right, #667eea, #764ba2);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0 15px;
  white-space: nowrap;
}

.header-shipping-date {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  color: #2c3e50;
  text-align: left;
}

.report-title {
  flex: 2;
  font-size: 20px;
  font-weight: 900;
  margin: 0;
  color: #2c3e50;
  text-align: center;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
  letter-spacing: 1.2px;
  position: relative;
}

.report-title::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 2px;
  background: linear-gradient(to right, #e74c3c, #c0392b);
  border-radius: 1px;
}

.header-print-time {
  flex: 1;
  font-size: 11px;
  font-weight: 600;
  color: #6c757d;
  text-align: right;
}

/* 每页头部样式 */
.page-header {
  border-bottom: 2px solid #2c3e50;
  padding: 8px 0;
  margin-bottom: 16px;
  background: linear-gradient(to right, #f8f9fa, #ffffff, #f8f9fa);
  border-radius: 6px 6px 0 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  position: relative;
  page-break-inside: avoid;
}

.page-header::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(to right, #667eea, #764ba2);
}

.page-header .header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0 15px;
  white-space: nowrap;
}

.page-header .header-shipping-date {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  color: #2c3e50;
  text-align: left;
}

.page-header .report-title {
  flex: 2;
  font-size: 20px;
  font-weight: 900;
  margin: 0;
  color: #2c3e50;
  text-align: center;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
  letter-spacing: 1.2px;
  position: relative;
}

.page-header .report-title::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 2px;
  background: linear-gradient(to right, #e74c3c, #c0392b);
  border-radius: 1px;
}

.page-header .header-print-time {
  flex: 1;
  font-size: 11px;
  font-weight: 600;
  color: #6c757d;
  text-align: right;
}

/* 内容区域 - 紧凑优化 */
.report-body {
  width: 100%;
  margin-top: 12px;
}

.destination-section {
  margin-bottom: 12px;
  background: transparent;
  border-radius: 6px;
  overflow: hidden;
  page-break-inside: avoid;
}

.destination-section.first-section {
  margin-top: 0;
}

.page-break-before {
  page-break-before: always;
}

.destination-title {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  padding: 6px 16px;
  color: #2c3e50;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  letter-spacing: 0.3px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 4px 4px 0 0;
  border-bottom: 1px solid #dee2e6;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
  background: transparent;
}

.report-table th {
  background: linear-gradient(135deg, #495057 0%, #6c757d 100%);
  color: white;
  font-weight: 700;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  padding: 4px 3px;
  text-align: center;
  border: none;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.report-table td {
  padding: 3px 3px;
  font-size: 11px;
  color: black;
  text-align: left;
  border: none;
  border-bottom: 1px solid #f1f3f4;
  vertical-align: middle;
  line-height: 1.2;
}

.report-table tbody tr:nth-child(even) {
  background: rgba(248, 249, 250, 0.5);
}

.report-table tbody tr:hover {
  background: rgba(102, 126, 234, 0.05);
}

/* 表格列样式 */
.report-table th:nth-child(1),
.report-table td:nth-child(1) {
  width: 18%;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.report-table th:nth-child(2),
.report-table td:nth-child(2) {
  width: 25%;
  font-weight: 600;
}

.report-table th:nth-child(3),
.report-table td:nth-child(3) {
  width: 12%;
  text-align: center;
  font-weight: 500;
}

.report-table th:nth-child(4),
.report-table td:nth-child(4) {
  width: 13%;
  text-align: center;
  font-weight: 500;
}

.report-table th:nth-child(5),
.report-table td:nth-child(5) {
  width: 11%;
  text-align: center;
  font-weight: 600;
}

.report-table th:nth-child(6),
.report-table td:nth-child(6) {
  width: 11%;
  text-align: center;
  font-weight: 600;
}

.report-table th:nth-child(7),
.report-table td:nth-child(7) {
  width: 10%;
  text-align: center;
}

.destination-summary {
  margin: 0;
  padding: 8px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-top: 1px solid #dee2e6;
  border-radius: 0 0 4px 4px;
}

.summary-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
}

.summary-table td {
  padding: 2px 4px;
  font-weight: 700;
  font-size: 11px;
  border: none;
  background: transparent;
  line-height: 1.2;
}

.summary-label {
  width: 30%;
  text-align: left;
  color: #2c3e50;
  font-size: 11px;
}

.summary-value {
  width: 25%;
  text-align: center;
  color: #2c3e50;
  font-size: 11px;
}

.summary-value:nth-child(2) {
  color: #e74c3c;
}

.summary-value:nth-child(3) {
  color: #27ae60;
}

.summary-value:nth-child(4) {
  color: #3498db;
}

.separator-line {
  width: 100%;
  height: 1px;
  background: linear-gradient(to right, #667eea, #764ba2);
  margin-top: 6px;
  border-radius: 1px;
  box-shadow: 0 1px 2px rgba(102, 126, 234, 0.2);
}

/* 打印样式 */
@media print {
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .pagination-info,
  .page-info {
    display: none !important;
  }

  body {
    background: #fff !important;
    color: #000 !important;
  }

  .shipping-report {
    padding: 16px !important;
    background: #fff !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    margin: 0 !important;
    font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'MS Gothic', sans-serif !important;
    color: #1a1a1a !important;
    line-height: 1.3 !important;
  }

  .shipping-report::before {
    display: none;
  }

  .report-header {
    border-bottom: 3px solid #2c3e50 !important;
    padding: 8px 0 !important;
    margin-bottom: 16px !important;
    background: linear-gradient(to right, #f8f9fa, #ffffff, #f8f9fa) !important;
    border-radius: 0 !important;
    position: relative !important;
    page-break-inside: avoid !important;
  }

  .report-header::after {
    content: '' !important;
    position: absolute !important;
    bottom: -3px !important;
    left: 0 !important;
    right: 0 !important;
    height: 3px !important;
    background: linear-gradient(to right, #667eea, #764ba2) !important;
  }

  .header-content {
    display: flex !important;
    flex-direction: row !important;
    justify-content: space-between !important;
    align-items: center !important;
    width: 100% !important;
    padding: 0 15px !important;
    white-space: nowrap !important;
  }

  .header-shipping-date {
    flex: 1 !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #2c3e50 !important;
    text-align: left !important;
  }

  .report-title {
    flex: 2 !important;
    font-size: 20px !important;
    font-weight: 900 !important;
    margin: 0 !important;
    color: #2c3e50 !important;
    text-align: center !important;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1) !important;
    letter-spacing: 1.2px !important;
    position: relative !important;
  }

  .report-title::after {
    content: '' !important;
    position: absolute !important;
    bottom: -6px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 80px !important;
    height: 2px !important;
    background: linear-gradient(to right, #e74c3c, #c0392b) !important;
    border-radius: 1px !important;
  }

  .header-print-time {
    flex: 1 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #6c757d !important;
    text-align: right !important;
  }

  .page-header {
    border-bottom: 3px solid #2c3e50 !important;
    padding: 8px 0 !important;
    margin-bottom: 16px !important;
    background: linear-gradient(to right, #f8f9fa, #ffffff, #f8f9fa) !important;
    border-radius: 0 !important;
    position: relative !important;
    page-break-inside: avoid !important;
  }

  .page-header::after {
    content: '' !important;
    position: absolute !important;
    bottom: -3px !important;
    left: 0 !important;
    right: 0 !important;
    height: 3px !important;
    background: linear-gradient(to right, #667eea, #764ba2) !important;
  }

  .page-header .header-content {
    display: flex !important;
    flex-direction: row !important;
    justify-content: space-between !important;
    align-items: center !important;
    width: 100% !important;
    padding: 0 15px !important;
    white-space: nowrap !important;
  }

  .page-header .header-shipping-date {
    flex: 1 !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #2c3e50 !important;
    text-align: left !important;
  }

  .page-header .report-title {
    flex: 2 !important;
    font-size: 20px !important;
    font-weight: 900 !important;
    margin: 0 !important;
    color: #2c3e50 !important;
    text-align: center !important;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1) !important;
    letter-spacing: 1.2px !important;
    position: relative !important;
  }

  .page-header .report-title::after {
    content: '' !important;
    position: absolute !important;
    bottom: -6px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 80px !important;
    height: 2px !important;
    background: linear-gradient(to right, #e74c3c, #c0392b) !important;
    border-radius: 1px !important;
  }

  .page-header .header-print-time {
    flex: 1 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #6c757d !important;
    text-align: right !important;
  }

  .report-body {
    width: 100%;
    margin-top: 12px;
  }

  .destination-section {
    margin-bottom: 12px !important;
    background: transparent !important;
    border-radius: 0 !important;
    overflow: visible !important;
    border: none !important;
    page-break-inside: avoid !important;
    box-shadow: none !important;
  }

  .page-break-before {
    page-break-before: always !important;
  }

  .destination-title {
    font-size: 15px !important;
    font-weight: 700 !important;
    margin: 0 !important;
    padding: 6px 16px !important;
    color: #2c3e50 !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    letter-spacing: 0.3px !important;
    border-bottom: 1px solid rgba(0, 0, 0, 0.2) !important;
    background: transparent !important;
  }

  .report-table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 0 !important;
    background: transparent !important;
  }

  .report-table th {
    background: transparent !important;
    color: black !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
    padding: 4px 3px !important;
    text-align: center !important;
    border: none !important;
    border-bottom: 2px solid #dee2e6 !important;
  }

  .report-table td {
    padding: 3px 3px !important;
    font-size: 11px !important;
    color: black !important;
    text-align: left !important;
    border: none !important;
    border-bottom: 1px solid #f1f3f4 !important;
    vertical-align: middle !important;
    line-height: 1.2 !important;
  }

  .report-table tbody tr:nth-child(even) {
    background: transparent;
  }

  .report-table tbody tr:hover {
    background: transparent;
  }

  .destination-summary {
    margin: 0 !important;
    padding: 8px 16px !important;
    background: transparent !important;
    border-top: 1px solid #dee2e6 !important;
  }

  .summary-table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 0 !important;
  }

  .summary-table td {
    padding: 2px 4px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    border: none !important;
    background: transparent !important;
    line-height: 1.2 !important;
  }

  .summary-label {
    width: 30%;
    text-align: left;
    color: #2c3e50;
    font-size: 11px;
  }

  .summary-value {
    width: 25%;
    text-align: center;
    color: #2c3e50;
    font-size: 11px;
  }

  .summary-value:nth-child(2) {
    color: #2c3e50;
  }

  .summary-value:nth-child(3) {
    color: #2c3e50;
  }

  .summary-value:nth-child(4) {
    color: #2c3e50;
  }

  .separator-line {
    width: 100% !important;
    height: 1px !important;
    margin-top: 6px !important;
    border-radius: 1px !important;
    background: #000 !important;
  }

  /* 表格列样式 */
  .report-table th:nth-child(1),
  .report-table td:nth-child(1) {
    width: 18% !important;
    font-family: 'Courier New', monospace !important;
    font-weight: 600 !important;
  }

  .report-table th:nth-child(2),
  .report-table td:nth-child(2) {
    width: 25% !important;
    font-weight: 600 !important;
  }

  .report-table th:nth-child(3),
  .report-table td:nth-child(3) {
    width: 12% !important;
    text-align: center !important;
    font-weight: 500 !important;
  }

  .report-table th:nth-child(4),
  .report-table td:nth-child(4) {
    width: 13% !important;
    text-align: center !important;
    font-weight: 500 !important;
  }

  .report-table th:nth-child(5),
  .report-table td:nth-child(5) {
    width: 11% !important;
    text-align: center !important;
    font-weight: 600 !important;
  }

  .report-table th:nth-child(6),
  .report-table td:nth-child(6) {
    width: 11% !important;
    text-align: center !important;
    font-weight: 600 !important;
  }

  .report-table th:nth-child(7),
  .report-table td:nth-child(7) {
    width: 10% !important;
    text-align: center !important;
  }
}

/* 响应式设计 */
@media screen {
  .shipping-report {
    background: #f8f9fa;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    margin: 20px;
  }
}

@media (max-width: 768px) {
  .report-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }

  .header-content {
    flex-direction: column;
    gap: 8px;
  }

  .header-shipping-date,
  .header-print-time {
    text-align: center;
  }

  .page-header .header-content {
    flex-direction: column;
    gap: 8px;
  }

  .page-header .header-shipping-date,
  .page-header .header-print-time {
    text-align: center;
  }

  .pagination-info {
    flex-direction: column;
    gap: 8px;
  }

  .info-item {
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
  }

  .report-table {
    font-size: 10px;
  }

  .report-table th,
  .report-table td {
    padding: 3px 2px;
  }
}
</style>
