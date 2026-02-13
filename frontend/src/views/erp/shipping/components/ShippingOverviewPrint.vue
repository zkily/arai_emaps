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

        <!-- 页面内容 -->
        <div class="print-body">
          <div class="column" v-for="colIndex in 2" :key="colIndex">
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
})

const printDateTime = computed(() => {
  const now = new Date()
  return now.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
})

function formatDate(dateStr) {
  if (!dateStr) return 'N/A'
  try {
    // 使用日本标准时间格式化日期
    const date = new Date(dateStr + 'T00:00:00+09:00') // 确保使用JST时区
    const year = date.getFullYear()
    const month = date.getMonth() + 1
    const day = date.getDate()

    // 获取星期（日文简写）
    const weekdays = ['日', '月', '火', '水', '木', '金', '土']
    const weekday = weekdays[date.getDay()]

    // 格式: 2025/10/1 水
    return `${year}/${month}/${day} ${weekday}`
  } catch (error) {
    console.error('日期格式化错误:', error)
    return dateStr
  }
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

function getColumnData(pageData, columnIndex) {
  if (!pageData || !pageData.destinations) return []

  // 使用预计算的列分配结果
  if (!pageData.columnAllocations) {
    pageData.columnAllocations = allocateDestinationsToColumns(pageData.destinations)
  }

  return pageData.columnAllocations[columnIndex] || []
}

function getDestinationSize(dest) {
  if (!dest || !dest.items || !Array.isArray(dest.items)) return 4
  // 调整尺寸计算：由于允许换行，每行可能占用更多空间
  // 目的地标题(1行) + 表头(1行) + 数据行数 + 底部间距(1行) + 换行预留空间
  const baseSize = 4
  const itemCount = dest.items.length
  // 预估每行可能需要的额外空间（考虑换行）
  const estimatedExtraSpace = Math.ceil(itemCount * 0.15) // 预留15%的额外空间用于换行
  return baseSize + itemCount + estimatedExtraSpace
}

// 纳入先分配函数 - 基于调整后的容量限制（考虑换行）
function allocateNounyusenToColumns(nounyusenGroup, columns, columnSizes) {
  // 调整后的容量限制 - 考虑换行后的行高增加
  const maxItemsPerColumn = 42 // 增加到36个商品（考虑换行后占用更多空间）
  const maxRowsPerColumn = 60 // 增加到60行（充分利用空间）

  // 计算每列当前的商品数量
  function getColumnItemCount(columnIndex) {
    return columns[columnIndex].reduce((sum, dest) => {
      return sum + (dest.items ? dest.items.length : 0)
    }, 0)
  }

  // 从商品数量较少的列开始分配
  let currentColumnIndex = getColumnItemCount(0) <= getColumnItemCount(1) ? 0 : 1

  for (const dest of nounyusenGroup) {
    const destSize = getDestinationSize(dest)
    const itemCount = dest.items ? dest.items.length : 0
    const currentItems = getColumnItemCount(currentColumnIndex)

    // 检查商品数量和行数限制
    if (
      currentItems + itemCount <= maxItemsPerColumn &&
      columnSizes[currentColumnIndex] + destSize <= maxRowsPerColumn
    ) {
      // 当前列可以容纳
      columns[currentColumnIndex].push(dest)
      columnSizes[currentColumnIndex] += destSize
    } else {
      // 当前列容纳不下，切换到另一列
      const otherColumnIndex = 1 - currentColumnIndex
      currentColumnIndex = otherColumnIndex
      columns[currentColumnIndex].push(dest)
      columnSizes[currentColumnIndex] += destSize
    }
  }
}

// 重新设计的列分配算法 - 基于调整后的容量限制（考虑换行）
function allocateDestinationsToColumns(destinations) {
  const columns = [[], []]
  const columnSizes = [0, 0]
  const maxItemsPerColumn = 36 // 增加到36个商品（考虑换行后占用更多空间）
  const maxRowsPerColumn = 60 // 增加到60行（充分利用空间）

  // 计算列的商品数量
  function getColumnItemCount(columnIndex) {
    return columns[columnIndex].reduce((sum, dest) => {
      return sum + (dest.items ? dest.items.length : 0)
    }, 0)
  }

  let i = 0
  while (i < destinations.length) {
    const dest = destinations[i]

    // 如果是纳入先，收集所有连续的纳入先
    if (dest.destination_name && dest.destination_name.includes('納入先')) {
      const nounyusenGroup = []
      let j = i

      while (
        j < destinations.length &&
        destinations[j].destination_name &&
        destinations[j].destination_name.includes('納入先')
      ) {
        nounyusenGroup.push(destinations[j])
        j++
      }

      // 智能分配纳入先到列中
      allocateNounyusenToColumns(nounyusenGroup, columns, columnSizes)
      i = j // 跳过已处理的纳入先
    } else {
      // 普通目的地，放入商品数量较少的列
      const destSize = getDestinationSize(dest)
      const itemCount = dest.items ? dest.items.length : 0
      const targetColumn = getColumnItemCount(0) <= getColumnItemCount(1) ? 0 : 1

      if (
        getColumnItemCount(targetColumn) + itemCount <= maxItemsPerColumn &&
        columnSizes[targetColumn] + destSize <= maxRowsPerColumn
      ) {
        columns[targetColumn].push(dest)
        columnSizes[targetColumn] += destSize
      } else {
        // 如果当前列放不下，尝试另一列
        const otherColumn = 1 - targetColumn
        if (
          getColumnItemCount(otherColumn) + itemCount <= maxItemsPerColumn &&
          columnSizes[otherColumn] + destSize <= maxRowsPerColumn
        ) {
          columns[otherColumn].push(dest)
          columnSizes[otherColumn] += destSize
        } else {
          // 两列都放不下，放入商品数量较少的列（允许适度超出）
          columns[targetColumn].push(dest)
          columnSizes[targetColumn] += destSize
        }
      }
      i++
    }
  }

  return columns
}

// 基于调整后容量的分页算法 - 考虑换行后的空间需求
function getPaginatedData(dateGroup) {
  if (!dateGroup || !dateGroup.destinations || dateGroup.destinations.length === 0) {
    return [{ shipping_date: dateGroup?.shipping_date || '', destinations: [] }]
  }

  const destinations = dateGroup.destinations
  const pages = []
  // 调整后的容量：考虑换行后需要更多空间
  const maxItemsPerColumn = 36 // 调整到36个商品
  const maxRowsPerColumn = 60 // 增加到60行

  // 计算目的地组的商品数量
  function getDestItemCount(dest) {
    return dest.items ? dest.items.length : 0
  }

  let i = 0
  while (i < destinations.length) {
    const currentPageDestinations = []
    const testColumns = [[], []]
    const testColumnSizes = [0, 0]

    // 计算测试列的商品数量
    function getTestColumnItemCount(columnIndex) {
      return testColumns[columnIndex].reduce((sum, dest) => {
        return sum + getDestItemCount(dest)
      }, 0)
    }

    // 尝试添加目的地到当前页，直到页面满为止
    while (i < destinations.length) {
      const dest = destinations[i]

      // 如果是纳入先，整组处理
      if (dest.destination_name && dest.destination_name.includes('納入先')) {
        const nounyusenGroup = []
        let j = i

        // 收集所有连续的纳入先
        while (
          j < destinations.length &&
          destinations[j].destination_name &&
          destinations[j].destination_name.includes('納入先')
        ) {
          nounyusenGroup.push(destinations[j])
          j++
        }

        // 测试纳入先组是否能放入当前页
        const tempColumns = [
          JSON.parse(JSON.stringify(testColumns[0])),
          JSON.parse(JSON.stringify(testColumns[1])),
        ]
        const tempColumnSizes = [...testColumnSizes]

        // 计算临时列的商品数量
        function getTempColumnItemCount(columnIndex) {
          return tempColumns[columnIndex].reduce((sum, dest) => {
            return sum + getDestItemCount(dest)
          }, 0)
        }

        // 模拟分配纳入先 - 基于调整后的容量限制
        let currentColumnIndex = getTempColumnItemCount(0) <= getTempColumnItemCount(1) ? 0 : 1
        let canFitAll = true

        for (const nounyusenDest of nounyusenGroup) {
          const destSize = getDestinationSize(nounyusenDest)
          const itemCount = getDestItemCount(nounyusenDest)

          // 检查商品数量限制
          if (
            getTempColumnItemCount(currentColumnIndex) + itemCount <= maxItemsPerColumn &&
            tempColumnSizes[currentColumnIndex] + destSize <= maxRowsPerColumn
          ) {
            // 当前列可以容纳
            tempColumns[currentColumnIndex].push(nounyusenDest)
            tempColumnSizes[currentColumnIndex] += destSize
          } else {
            // 当前列容纳不下，切换到另一列
            const otherColumnIndex = 1 - currentColumnIndex
            if (
              getTempColumnItemCount(otherColumnIndex) + itemCount <= maxItemsPerColumn &&
              tempColumnSizes[otherColumnIndex] + destSize <= maxRowsPerColumn
            ) {
              currentColumnIndex = otherColumnIndex
              tempColumns[currentColumnIndex].push(nounyusenDest)
              tempColumnSizes[currentColumnIndex] += destSize
            } else {
              // 两列都放不下
              canFitAll = false
              break
            }
          }
        }

        // 严格的页面容量检查
        if (
          canFitAll &&
          tempColumnSizes[0] <= maxRowsPerColumn &&
          tempColumnSizes[1] <= maxRowsPerColumn &&
          getTempColumnItemCount(0) <= maxItemsPerColumn &&
          getTempColumnItemCount(1) <= maxItemsPerColumn
        ) {
          // 可以放入当前页
          currentPageDestinations.push(...nounyusenGroup)
          testColumns[0] = tempColumns[0]
          testColumns[1] = tempColumns[1]
          testColumnSizes[0] = tempColumnSizes[0]
          testColumnSizes[1] = tempColumnSizes[1]
          i = j
        } else {
          // 如果当前页是空的，将纳入先组拆分处理
          if (currentPageDestinations.length === 0) {
            // 尝试单独放入每个纳入先，确保至少能放入一个
            for (const nounyusenDest of nounyusenGroup) {
              const destSize = getDestinationSize(nounyusenDest)
              const itemCount = getDestItemCount(nounyusenDest)
              const targetColumn = getTestColumnItemCount(0) <= getTestColumnItemCount(1) ? 0 : 1

              if (
                getTestColumnItemCount(targetColumn) + itemCount <= maxItemsPerColumn &&
                testColumnSizes[targetColumn] + destSize <= maxRowsPerColumn
              ) {
                currentPageDestinations.push(nounyusenDest)
                testColumns[targetColumn].push(nounyusenDest)
                testColumnSizes[targetColumn] += destSize
                i++
              } else {
                const otherColumn = 1 - targetColumn
                if (
                  getTestColumnItemCount(otherColumn) + itemCount <= maxItemsPerColumn &&
                  testColumnSizes[otherColumn] + destSize <= maxRowsPerColumn
                ) {
                  currentPageDestinations.push(nounyusenDest)
                  testColumns[otherColumn].push(nounyusenDest)
                  testColumnSizes[otherColumn] += destSize
                  i++
                } else {
                  // 单个纳入先都放不下，强制放入避免无限循环
                  currentPageDestinations.push(nounyusenDest)
                  testColumns[targetColumn].push(nounyusenDest)
                  testColumnSizes[targetColumn] += destSize
                  i++
                  break // 这页只放这一个
                }
              }
            }
            break // 结束当前页
          } else {
            // 不能放入当前页，结束当前页
            break
          }
        }
      } else {
        // 普通目的地
        const destSize = getDestinationSize(dest)
        const itemCount = getDestItemCount(dest)
        const targetColumn = getTestColumnItemCount(0) <= getTestColumnItemCount(1) ? 0 : 1

        // 检查是否能放入（商品数量和行数双重限制）
        if (
          getTestColumnItemCount(targetColumn) + itemCount <= maxItemsPerColumn &&
          testColumnSizes[targetColumn] + destSize <= maxRowsPerColumn
        ) {
          // 可以放入
          currentPageDestinations.push(dest)
          testColumns[targetColumn].push(dest)
          testColumnSizes[targetColumn] += destSize
          i++
        } else {
          // 尝试另一列
          const otherColumn = 1 - targetColumn
          if (
            getTestColumnItemCount(otherColumn) + itemCount <= maxItemsPerColumn &&
            testColumnSizes[otherColumn] + destSize <= maxRowsPerColumn
          ) {
            currentPageDestinations.push(dest)
            testColumns[otherColumn].push(dest)
            testColumnSizes[otherColumn] += destSize
            i++
          } else {
            // 两列都放不下，结束当前页
            break
          }
        }
      }
    }

    // 创建页面
    if (currentPageDestinations.length > 0) {
      pages.push(createPage(dateGroup.shipping_date, currentPageDestinations))
    } else if (i < destinations.length) {
      // 如果没有添加任何目的地但还有剩余，强制添加一个避免无限循环
      const dest = destinations[i]
      pages.push(createPage(dateGroup.shipping_date, [dest]))
      i++
    }
  }

  return pages.length > 0 ? pages : [createPage(dateGroup.shipping_date, [])]
}

function createPage(shipping_date, destinations) {
  return {
    shipping_date,
    destinations: [...destinations],
    columnAllocations: null, // 将在getColumnData中计算
  }
}
</script>

<style scoped>
/* 页面设置 */
@page {
  size: A4 portrait;
  margin: 15mm 10mm 0mm 10mm;
  /* 上边距增加到35mm (约3.5cm) */
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

/* 表格样式 */
.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
  /* 字体增大 */
  line-height: 1.2;
  table-layout: fixed;
  /* 固定表格布局 */
}

.print-table th {
  font-weight: bold;
  text-align: center;
  padding: 1px 3px;
  /* 增大内边距 */
  border: 1px solid #000;
  font-size: 14px;
  /* 字体增大 */
  line-height: 1.1;
  height: 22px;
  /* 增大表头高度 */
}

.print-table td {
  padding: 2px 3px;
  /* 增大内边距 */
  border: 1px solid #000;
  vertical-align: top;
  font-size: 14px;
  /* 字体增大 */
  line-height: 1.1;
  height: auto;
  /* 改为自动高度，允许内容换行 */
  overflow: visible;
  /* 显示溢出内容 */
  text-overflow: clip;
  /* 不使用省略号 */
  white-space: normal;
  /* 允许换行 */
  word-wrap: break-word;
  /* 长单词自动换行 */
  word-break: break-all;
  /* 强制换行，适合长编号 */
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
