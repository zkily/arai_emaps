<template>
  <div class="shipping-overview-print">
    <!-- 主要内容 -->
    <div v-for="dateGroup in groupedData" :key="dateGroup.shipping_date">
      <div v-for="(pageData, pageIndex) in getPaginatedData(dateGroup)" :key="`${dateGroup.shipping_date}-${pageIndex}`"
        class="page-container">
        <!-- 页面头部 -->
        <div class="print-header">
          <div class="header-left">
            <span class="label">印刷日時:</span>
            <span class="value">{{ printDateTime }}</span>
          </div>
          <div class="header-center">
            <h1 class="print-title">出荷予定表</h1>
          </div>
          <div class="header-right">
            <span class="label">出荷日:</span>
            <span class="value">{{ formatDate(dateGroup.shipping_date) }}</span>
          </div>
        </div>

        <!-- 页面内容：列数由单页最优分配结果决定 -->
        <div class="print-body" :style="getPrintBodyStyle(pageData)">
          <div class="column" v-for="colIndex in getColumnCount(pageData)" :key="colIndex">
            <div v-for="destGroup in getColumnData(pageData, colIndex - 1)"
              :key="`${destGroup.destination_name}-${pageIndex}-${colIndex}`" class="destination-group">
              <div class="destination-header">
                <h2 class="destination-name">{{ destGroup.destination_name }}</h2>
              </div>
              <table class="print-table">
                <thead>
                  <tr>
                    <th class="col-product">製品名</th>
                    <th class="col-quantity">数量</th>
                    <th class="col-shipping">出荷No</th>
                    <th class="col-check">確認</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in destGroup.items" :key="index" class="data-row">
                    <td class="col-product">{{ item.product_name || '-' }}</td>
                    <td class="col-quantity">{{ item.quantity || '0' }}</td>
                    <td class="col-shipping">
                      {{ item.shipping_no ? item.shipping_no.slice(-2) : '-' }}
                    </td>
                    <td class="col-check">
                      <div class="checkbox-container">
                        <span class="checkbox"></span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDateWithWeekdayJST, formatDateTimeJST, localeForIntl } from '@/utils/dateFormat'

const { locale } = useI18n()

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const printDateTime = computed(() => {
  return formatDateTimeJST(new Date(), localeForIntl(locale.value), {
    hour: '2-digit',
    minute: '2-digit',
    second: undefined,
  })
})

function formatDate(dateStr) {
  if (!dateStr) return 'N/A'
  return formatDateWithWeekdayJST(dateStr, localeForIntl(locale.value))
}

// 数据分组逻辑
const groupedData = computed(() => {
  if (!props.data || props.data.length === 0) return []

  const result = []
  const dateMap = new Map()

  // 按出荷日分组
  props.data.forEach((item) => {
    if (!item || !item.shipping_date) return

    if (!dateMap.has(item.shipping_date)) {
      dateMap.set(item.shipping_date, new Map())
    }
    const destMap = dateMap.get(item.shipping_date)

    const destName = item.destination_name || '未知目的地'
    if (!destMap.has(destName)) {
      destMap.set(destName, [])
    }
    destMap.get(destName).push(item)
  })

  // 转换为数组格式
  dateMap.forEach((destMap, shipping_date) => {
    const destinations = []
    destMap.forEach((items, destination_name) => {
      destinations.push({ destination_name, items })
    })

    // 对目的地进行排序，纳入先优先
    destinations.sort((a, b) => {
      const aIsNounyusen = a.destination_name.includes('納入先')
      const bIsNounyusen = b.destination_name.includes('納入先')

      if (aIsNounyusen && !bIsNounyusen) return -1
      if (!aIsNounyusen && bIsNounyusen) return 1
      return a.destination_name.localeCompare(b.destination_name, 'ja')
    })

    result.push({ shipping_date, destinations })
  })

  return result.sort((a, b) => new Date(a.shipping_date) - new Date(b.shipping_date))
})

// 与现有 CSS 一致的“行高”单位（不改变字体与行高）：表头约 1 行，每数据行 1 行，目的地标题+间距约 2 行
const ROWS_HEADER = 2
const ROWS_PER_ITEM = 1

/** 计算单个納入先块的高度（行单位，与当前样式一致） */
function getDestinationHeightInRows(dest) {
  if (!dest || !dest.items || !Array.isArray(dest.items)) return ROWS_HEADER + 2
  return ROWS_HEADER + dest.items.length * ROWS_PER_ITEM
}

/** 单页可用的每列最大行数（A4 竖版 body 高度换算，字体/行高不变） */
function getMaxRowsPerColumn() {
  // 270mm - header ~22px，约 260mm 可用；按 24px/行 估算
  const mmPerRow = 6
  const bodyMm = 260
  return Math.floor(bodyMm / mmPerRow)
}

function getColumnData(pageData, columnIndex) {
  if (!pageData || !pageData.destinations) return []
  if (!pageData.columnAllocations) {
    pageData.columnAllocations = allocateDestinationsToOnePage(pageData.destinations)
  }
  return pageData.columnAllocations[columnIndex] || []
}

function getColumnCount(pageData) {
  if (!pageData || !pageData.destinations) return 2
  if (!pageData.columnAllocations) {
    pageData.columnAllocations = allocateDestinationsToOnePage(pageData.destinations)
  }
  return pageData.columnAllocations.length
}

function getPrintBodyStyle(pageData) {
  const n = getColumnCount(pageData)
  return n > 2 ? { display: 'flex', gap: '8px', flexWrap: 'nowrap' } : {}
}

/**
 * 单页最优排版：先算各納入先高度，再从左侧列开始分配，使两列高度尽量均衡（贪心：每次放入当前高度较小的列）。
 * 若两列放不下则尝试 3 列、4 列，保证只出一页。
 */
function allocateDestinationsToOnePage(destinations) {
  if (!destinations || destinations.length === 0) return [[], []]

  const maxRowsPerColumn = getMaxRowsPerColumn()
  const heights = destinations.map((d) => getDestinationHeightInRows(d))
  const totalRows = heights.reduce((a, b) => a + b, 0)

  for (const numCols of [2, 3, 4]) {
    const capacity = maxRowsPerColumn * numCols
    if (totalRows > capacity) continue

    const columns = Array.from({ length: numCols }, () => [])
    const columnHeights = Array(numCols).fill(0)

    // 按高度降序，优先放大的块，有利于平衡
    const indexed = destinations.map((d, i) => ({ dest: d, height: heights[i] }))
    indexed.sort((a, b) => b.height - a.height)

    for (const { dest, height } of indexed) {
      let bestCol = 0
      let minH = columnHeights[0]
      for (let c = 1; c < numCols; c++) {
        if (columnHeights[c] < minH) {
          minH = columnHeights[c]
          bestCol = c
        }
      }
      columns[bestCol].push(dest)
      columnHeights[bestCol] += height
    }

    const maxH = Math.max(...columnHeights)
    if (maxH <= maxRowsPerColumn) return columns
  }

  // 仍用 2 列，尽量均衡（可能超出一页时也只出一页）
  const columns = [[], []]
  const columnHeights = [0, 0]
  const indexed = destinations.map((d, i) => ({ dest: d, height: heights[i] }))
  indexed.sort((a, b) => b.height - a.height)
  for (const { dest, height } of indexed) {
    const bestCol = columnHeights[0] <= columnHeights[1] ? 0 : 1
    columns[bestCol].push(dest)
    columnHeights[bestCol] += height
  }
  return columns
}

/** 每个出荷日只出一页，所有納入先都在这一页内按最优列分配 */
function getPaginatedData(dateGroup) {
  if (!dateGroup || !dateGroup.destinations || dateGroup.destinations.length === 0) {
    return [{ shipping_date: dateGroup?.shipping_date || '', destinations: [], columnAllocations: null }]
  }
  const page = {
    shipping_date: dateGroup.shipping_date,
    destinations: [...dateGroup.destinations],
    columnAllocations: null,
  }
  return [page]
}

</script>

<style scoped>
/* 页面设置 */
@page {
  size: A4 portrait;
  margin: 18mm 10mm 0mm 10mm;
  /* 页面上方保留 1cm 空白 */
}

/* 全局重置 */
* {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.shipping-overview-print {
  font-family: 'MS Gothic', 'Hiragino Sans', 'Yu Gothic', sans-serif;
  font-size: 16px;
  /* 字体增大 */
  line-height: 1.2;
  color: #000;
}

/* 页面容器 */
.page-container {
  width: 100%;
  height: 260mm;
  /* 调整页面高度 A4-调整后的上下边距 */
  page-break-after: always;
  page-break-inside: avoid;
  display: flex;
  flex-direction: column;
  position: relative;
  /* overflow: hidden;  */
}

.page-container:last-child {
  page-break-after: auto;
}

/* 页面头部 */
.print-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 2px solid #000;
  margin-bottom: 6px;
  page-break-after: avoid;
  height: 20px;
  /* 增大头部高度 */
  flex-shrink: 0;
  /* 防止头部被压缩 */
}

.header-left,
.header-right {
  flex: 2;
  font-size: 14px;
  /* 字体增大 */
  font-weight: bold;
  margin-left: 8px;
}

.header-right {
  text-align: right;
  margin-left: 0;
  margin-right: 8px;
}

.header-center {
  flex: 2;
  text-align: center;
}

.label {
  font-weight: bold;
  margin-right: 4px;
}

.value {
  font-weight: normal;
}

.header-right .value {
  font-size: 16px;
  /* 出荷日字体大一号 */
}

.print-title {
  font-size: 22px;
  /* 标题字体增大 */
  font-weight: bold;
  margin: 0;
  letter-spacing: 1px;
}

/* 页面主体 */
.print-body {
  flex: 1;
  display: flex;
  gap: 8px;
  margin-top: 4px;
  margin-bottom: 4px;
  height: calc(260mm - 22px);
  /* 页面高度减去头部高度 */
  /* overflow: hidden;  */
}

.column {
  flex: 1;
  min-width: 0;
  max-height: 100%;
  /* 限制列的最大高度 */
  overflow: hidden;
  /* 防止单列内容溢出 */
}

/* 目的地组 */
.destination-group {
  margin-bottom: 4px;
  page-break-inside: avoid;
  break-inside: avoid;
  /* 现代浏览器支持 */
  overflow: hidden;
  /* 强制目的地组不跨页 */
  display: block;
}

.destination-header {
  border-bottom: 1px solid #000;
  page-break-after: avoid;
}

.destination-name {
  font-size: 16px;
  /* 字体增大 */
  font-weight: bold;
  text-align: left;
  margin: 0;
  padding: 3px 4px;
  /* 增大内边距 */
  line-height: 1.2;
}

/* 表格样式（行高较原样增加约 10%） */
.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
  line-height: 1.32;
  /* 1.2 * 1.1 */
  table-layout: fixed;
}

.print-table th {
  font-weight: bold;
  text-align: center;
  padding: 2px 3px;
  border: 1px solid #000;
  font-size: 14px;
  line-height: 1.21;
  height: 24px;
  /* 22px * 1.1 ≈ 24px */
}

.print-table td {
  padding: 3px 3px;
  border: 1px solid #000;
  vertical-align: top;
  font-size: 14px;
  line-height: 1.21;
  /* 1.1 * 1.1 */
  height: auto;
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
  word-wrap: break-word;
  word-break: break-all;
}

/* 列宽设置 */
.col-product {
  width: 45%;
  /* 稍微缩小产品名列，给其他列更多空间 */
}

.col-quantity {
  width: 18%;
  /* 增加数量列宽度 */
  text-align: center;
}

.col-shipping {
  width: 22%;
  /* 增加出荷No列宽度 */
  text-align: center;
}

.col-check {
  width: 15%;
  text-align: center;
}

/* 复选框 */
.checkbox-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.checkbox {
  width: 12px;
  /* 复选框增大 */
  height: 12px;
  border: 1.5px solid #000;
  display: inline-block;
}

/* 打印优化 */
@media print {
  .page-container {
    margin: 0;
    box-shadow: none;
    height: 270mm !important;
    /* 强制固定页面高度 */
    /* overflow: hidden !important; */
  }

  .print-body {
    height: calc(270mm - 22px) !important;
    /* overflow: hidden !important; */
  }

  .column {
    max-height: calc(260mm - 22px) !important;
    /* overflow: hidden !important; */
  }

  .destination-group {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  /* 确保纳入先组不被分页 */
  /* .destination-group {
    display: block !important;
    overflow: hidden !important;
  } */
}

/* 响应式调整 */
@media screen and (max-width: 768px) {
  .print-body {
    flex-direction: column;
    gap: 10px;
  }

  .print-header {
    flex-direction: column;
    text-align: center;
    gap: 5px;
  }

  .header-left,
  .header-right {
    text-align: center;
  }
}
</style>
