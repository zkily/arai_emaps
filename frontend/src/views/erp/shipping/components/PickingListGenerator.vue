<template>
  <div class="picking-list-generator">
    <!-- 上部区域：标题和按钮 -->
    <div class="header-section">
      <!-- 左侧标题区域 -->
      <div class="title-section">
        <h2 class="page-title">
          <el-icon><Box /></el-icon>
          ピッキングリスト
        </h2>
      </div>

      <!-- 右侧按钮区域 -->
      <div class="action-buttons-section">
        <el-button type="warning" @click="syncShippingData" :loading="loading.sync" size="default">
          <el-icon><Download /></el-icon>
          データ読み込み
        </el-button>

        <el-button
          type="primary"
          @click="fetchShippingData"
          :loading="loading.fetch"
          size="default"
        >
          <el-icon><Search /></el-icon>
          データ更新
        </el-button>
      </div>
    </div>

     <!-- 统计卡片：紧凑横並び -->
    <div class="statistics-section">
      <div class="statistics-cards">
        <div class="stat-card total-card">
          <span class="stat-icon"><el-icon><Box /></el-icon></span>
          <span class="stat-value">{{ totalStats.total.toLocaleString() }}</span>
          <span class="stat-label">パレット数</span>
        </div>
        <div class="stat-card pending-card">
          <span class="stat-icon"><el-icon><Clock /></el-icon></span>
          <span class="stat-value">{{ totalStats.pending.toLocaleString() }}</span>
          <span class="stat-label">未ピッキング</span>
        </div>
        <div class="stat-card completed-card">
          <span class="stat-icon"><el-icon><CircleCheck /></el-icon></span>
          <span class="stat-value">{{ totalStats.completed.toLocaleString() }}</span>
          <span class="stat-label">ピッキング済</span>
        </div>
        <div class="stat-card completion-card">
          <span class="stat-icon"><el-icon><TrendCharts /></el-icon></span>
          <span class="stat-value">{{ totalStats.completionRate }}%</span>
          <span class="stat-label">完成率</span>
        </div>
      </div>
    </div>

    <!-- 中部筛选区域 -->
    <div class="filter-section">
      <el-card shadow="hover">
        <template #header>
          <div class="filter-header">
            <span class="filter-title">
              <el-icon><Filter /></el-icon>
              検索条件
            </span>
            <el-tag type="info" size="small">自動読み込み</el-tag>
          </div>
        </template>

        <el-form :inline="true" :model="filters" class="filter-form">
          <el-form-item label="出荷日">
            <div class="date-picker-group">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="〜"
                start-placeholder="開始日"
                end-placeholder="終了日"
                value-format="YYYY-MM-DD"
                class="compact-date-picker"
              />
              <div class="date-quick-buttons">
                <el-button size="small" @click="setDateRange(-1)"> 前日 </el-button>
                <el-button size="small" type="primary" @click="setDateRange(0)"> 今日 </el-button>
                <el-button size="small" @click="setDateRange(1)"> 翌日 </el-button>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="状態">
            <el-select
              v-model="filters.status"
              placeholder="全ての状態"
              clearable
              style="width: 150px"
            >
              <el-option label="未ピッキング" value="未ピッキング" />
              <el-option label="ピッキング済" value="ピッキング済" />
            </el-select>
          </el-form-item>

          <el-form-item label="製品">
            <el-select
              v-model="filters.product_cd"
              placeholder="全ての製品"
              clearable
              filterable
              style="width: 250px"
            >
              <el-option
                v-for="product in productOptions"
                :key="product.product_cd"
                :label="`${product.product_cd} - ${product.product_name}`"
                :value="product.product_cd"
              />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="fetchShippingData" :loading="loading.fetch">
              <el-icon><Search /></el-icon>
              検索
            </el-button>
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              リセット
            </el-button>
            <el-button type="success" @click="handlePrint" :disabled="filteredPalletGroups.length === 0">
              <el-icon><Printer /></el-icon>
              印刷
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 下部列表显示区域 -->
    <div class="list-section">
      <el-card shadow="hover">
        <template #header>
          <div class="list-header">
            <div class="list-title">
              <span>
                <el-icon><List /></el-icon>
                パレット一覧 ({{ filteredPalletGroups.length }}個)
              </span>
            </div>
          </div>
        </template>

        <!-- 加载状态 -->
        <div v-if="loading.fetch" class="loading-state">
          <el-empty description="データを読み込み中...">
            <template #image>
              <el-icon size="64" class="is-loading">
                <Loading />
              </el-icon>
            </template>
          </el-empty>
        </div>

        <!-- 空状态 -->
        <div v-else-if="palletGroups.length === 0" class="empty-state">
          <el-empty description="条件に合う出荷データがありません">
            <template #default>
              <div class="empty-actions">
                <el-button type="warning" @click="syncShippingData" :loading="loading.sync">
                  <el-icon><Download /></el-icon>
                  データ読み込み
                </el-button>
              </div>
              <p class="empty-hint">shipping_itemsテーブルからデータを読み込んでください</p>
            </template>
          </el-empty>
        </div>

        <!-- 托盘表格（分页：每页25件） -->
        <div v-else class="pallet-table">
          <el-table :data="paginatedPalletGroups" border stripe size="default" class="pallet-main-table">
            <!-- 托盘编号 -->
            <el-table-column prop="shipping_no" label="パレット番号" width="150">
              <template #default="{ row }">
                <span class="pallet-number">{{ row.shipping_no }}</span>
              </template>
            </el-table-column>

            <!-- 出荷日 -->
            <el-table-column prop="shipping_date" label="出荷日" width="100" align="center">
              <template #default="{ row }">
                {{ formatDate(row.shipping_date) }}
              </template>
            </el-table-column>

            <!-- 状態 -->
            <el-table-column label="状態" width="130" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>

            <!-- 总箱数 -->
            <el-table-column label="箱数" width="80" align="right">
              <template #default="{ row }">
                <span class="box-value">{{ row.totalBoxes.toLocaleString() }}箱</span>
              </template>
            </el-table-column>

            <!-- 产品列表 -->
            <el-table-column label="製品一覧" min-width="300">
              <template #default="{ row }">
                <div class="product-list">
                  <div v-for="(item, index) in row.items" :key="index" class="product-item">
                    <span class="product-code">{{ item.product_cd }}</span>
                    <span class="product-name">{{ item.product_name }}</span>
                    <span class="product-quantity"
                      >{{
                        (item.confirmed_units || item.confirmed_boxes || 0).toLocaleString()
                      }}箱</span
                    >
                  </div>
                </div>
              </template>
            </el-table-column>

            <!-- 納入先 -->
            <el-table-column label="納入先" width="180">
              <template #default="{ row }">
                <span v-if="row.items[0]?.destination_name" class="destination-name">
                  {{ row.items[0].destination_name }}
                </span>
                <span v-else class="destination-code">-</span>
              </template>
            </el-table-column>

            <!-- 作業者（users.full_name を優先表示） -->
            <el-table-column label="作業者" width="120" align="center">
              <template #default="{ row }">
                <span v-if="row.picker_full_name || row.picker_name || row.picker_id" class="picker-id">{{
                  row.picker_full_name || row.picker_name || row.picker_id
                }}</span>
                <span v-else class="no-picker">未割当</span>
              </template>
            </el-table-column>

          </el-table>

          <el-pagination
            v-if="filteredPalletGroups.length > PAGE_SIZE"
            v-model:current-page="currentPage"
            :page-size="PAGE_SIZE"
            :total="filteredPalletGroups.length"
            layout="total, prev, pager, next, jumper"
            class="pallet-pagination"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Loading,
  Download,
  Box,
  Filter,
  List,
  RefreshLeft,
  Clock,
  CircleCheck,
  TrendCharts,
  Printer,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { getProductList } from '@/api/master/productMaster'

/** API 响应体（request 拦截器已返回 response.data） */
interface ApiResponseBody {
  success?: boolean
  message?: string
  data?: unknown
}

/** tasks/for-display API 返回结构 */
interface TasksForDisplayResponse {
  items?: unknown[]
  total?: number
  page?: number
  page_size?: number
  total_pages?: number
}

interface ShippingItem {
  shipping_no_p?: string
  shipping_no: string
  product_cd: string
  product_name: string
  confirmed_units: number
  confirmed_boxes: number
  box_type: string
  destination_cd: string
  destination_name: string
  shipping_date: string
  delivery_date: string
  status: string
  picker_id: string
  picker_name?: string
  picker_full_name?: string
}

interface PalletGroup {
  shipping_no: string
  shipping_date: string
  items: ShippingItem[]
  totalUnits: number
  totalBoxes: number
  status: string
  picker_id: string
  picker_name?: string
  picker_full_name?: string
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const emit = defineEmits(['refresh'])

// 响应式数据
const loading = ref({
  fetch: false,
  generate: false,
  sync: false,
})

const filters = ref({
  status: '',
  product_cd: '',
})

const productOptions = ref<Array<{ product_cd: string; product_name: string }>>([])

// 获取日本标准时间(JST)的今天日期
const getJSTToday = () => {
  const now = new Date()
  const jstOffset = 9 * 60 // JST是UTC+9
  const jstTime = new Date(now.getTime() + jstOffset * 60 * 1000)
  return jstTime.toISOString().slice(0, 10)
}

const today = getJSTToday()
const dateRange = ref<[string, string]>([today, today])

// 防抖计时器
let debounceTimer: NodeJS.Timeout | null = null

const palletGroups = ref<PalletGroup[]>([])

// 筛选后的托盘组
const filteredPalletGroups = computed(() => {
  let filtered = palletGroups.value

  // 按产品筛选
  if (filters.value.product_cd) {
    filtered = filtered.filter((pallet) =>
      pallet.items.some((item) => item.product_cd === filters.value.product_cd),
    )
  }

  return filtered
})

// 统计数据：按パレット（shipping_no_p）件数。未ピッキング = pending + picking（作業中も含む）
const totalStats = computed(() => {
  const groups = filteredPalletGroups.value
  const total = groups.length
  const completed = groups.filter((p) => p.status === 'completed').length
  const pending = groups.filter(
    (p) => p.status === 'pending' || p.status === 'picking',
  ).length
  const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0
  return { total, completed, pending, completionRate }
})

const PAGE_SIZE = 25
const currentPage = ref(1)
const paginatedPalletGroups = computed(() => {
  const list = filteredPalletGroups.value
  const start = (currentPage.value - 1) * PAGE_SIZE
  return list.slice(start, start + PAGE_SIZE)
})

// API 1ページあたりの件数（全件取得するため複数ページをリクエスト）
const API_PAGE_SIZE = 500

// 方法：全ページを取得してから結合（API はデフォルト 50 件のみ返すため）
async function fetchShippingData() {
  loading.value.fetch = true
  try {
    const statusMap: Record<string, string> = { '未ピッキング': 'pending', 'ピッキング済': 'completed' }
    const baseParams: Record<string, string | number> = {
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      page_size: API_PAGE_SIZE,
    }
    if (filters.value.status) {
      baseParams.status = statusMap[filters.value.status] || filters.value.status
    }

    const allItems: ShippingItem[] = []
    let page = 1
    let totalPages = 1

    // 全ページを取得（API は最大 500 件/ページのため、複数回リクエスト）
    do {
      const params = { ...baseParams, page }
      const response = (await request.get('/api/shipping/picking/tasks/for-display', {
        params,
      })) as ApiResponseBody | TasksForDisplayResponse | unknown[]

      let items: ShippingItem[] = []
      if (
        response &&
        typeof response === 'object' &&
        'items' in response &&
        Array.isArray((response as TasksForDisplayResponse).items)
      ) {
        const res = response as TasksForDisplayResponse
        items = res.items as ShippingItem[]
        const totalFromApi = res.total ?? 0
        totalPages = Math.max(1, Math.ceil(totalFromApi / API_PAGE_SIZE))
      } else if (response && (response as ApiResponseBody).success !== undefined) {
        const res = response as ApiResponseBody
        if (!res.success) {
          ElMessage.error(res.message || 'データの取得に失敗しました')
          return
        }
        items = Array.isArray(res.data) ? (res.data as ShippingItem[]) : []
        totalPages = 1
      } else if (Array.isArray(response)) {
        items = response as ShippingItem[]
        totalPages = 1
      } else {
        ElMessage.error('データ形式が正しくありません')
        return
      }

      if (!Array.isArray(items)) {
        ElMessage.error('データ形式が正しくありません')
        return
      }

      allItems.push(...items)
      page++
    } while (page <= totalPages)

    const items = allItems
    console.log(`获取到 ${items.length} 条原始数据（全ページ取得）`)

    // 过滤掉製品名包含特定关键词的数据
    const excludeKeywords = ['加工', 'アーチ', '料金']
    const filteredItems = items.filter((item: ShippingItem) => {
      const productName = item.product_name || ''
      const shouldExclude = excludeKeywords.some((keyword) => productName.includes(keyword))
      return !shouldExclude
    })

    console.log(
      `过滤后剩余 ${filteredItems.length} 条数据（过滤掉 ${items.length - filteredItems.length} 条包含特定关键词的数据）`,
    )

    // 打印前几条数据用于调试
    if (filteredItems.length > 0) {
      console.log('过滤后数据示例:', filteredItems.slice(0, 2))
    }

    if (filteredItems.length === 0) {
      console.warn('过滤后无数据。请检查后端数据库或当前筛选条件，确认是否有符合条件的数据。')
      ElMessage.warning({
        message:
          '出荷データが見つかりません。データベースに出荷データが存在しないか、現在のフィルター条件に合致するデータがありません。',
        duration: 8000, // Extend duration for more info
        showClose: true, // Allow user to close it
      })
      palletGroups.value = [] // Ensure palletGroups is cleared when no items
      return // Exit function early if no items
    }

    // 按 shipping_no_p（パレット番号）分组，无则退化为 shipping_no，统计按パレット件数
    const palletKey = (item: ShippingItem) => (item.shipping_no_p && item.shipping_no_p.trim()) ? item.shipping_no_p.trim() : (item.shipping_no || '').trim()
    const grouped = filteredItems.reduce((acc: Record<string, PalletGroup>, item: ShippingItem) => {
      const key = palletKey(item)
      if (!key) return acc
      if (!acc[key]) {
        acc[key] = {
          shipping_no: item.shipping_no || item.shipping_no_p || key,
          shipping_date: item.shipping_date,
          items: [],
          totalUnits: 0,
          totalBoxes: 0,
          status: 'pending',
          picker_id: item.picker_id || '',
          picker_name: item.picker_full_name || item.picker_name || item.picker_id || '',
          picker_full_name: item.picker_full_name || '',
        }
      }
      acc[key].items.push(item)
      const units = Number(item.confirmed_units || item.confirmed_boxes) || 0
      const boxes = Number(item.confirmed_boxes) || 0
      acc[key].totalUnits += units
      acc[key].totalBoxes += boxes
      return acc
    }, {})

    // 计算每个托盘的整体状态
    for (const pallet of Object.values(grouped) as PalletGroup[]) {
      const statuses = pallet.items.map((item) => item.status)
      console.log(`托盘 ${pallet.shipping_no} 项目状态:`, statuses)

      // 如果所有项目都是completed，则托盘状态为completed
      if (statuses.every((status) => status === 'completed')) {
        pallet.status = 'completed'
      }
      // 如果有任何项目是picking，则托盘状态为picking
      else if (statuses.some((status) => status === 'picking')) {
        pallet.status = 'picking'
      }
      // 否则默认为pending
      else {
        pallet.status = 'pending'
      }

      console.log(
        `托盘 ${pallet.shipping_no} 最终状态: ${pallet.status}, 累计: units=${pallet.totalUnits}, boxes=${pallet.totalBoxes}`,
      )
    }

    palletGroups.value = Object.values(grouped)
    currentPage.value = 1
    console.log(`分组后的托盘数量: ${palletGroups.value.length}`)
    console.log('完整的托盘数据:', palletGroups.value)

    // 如果产品列表为空或很少，从数据中提取产品列表
    if (palletGroups.value.length > 0 && productOptions.value.length === 0) {
      extractProductsFromData()
    }

    if (palletGroups.value.length > 0) {
      ElMessage.success(`${palletGroups.value.length}個のパレットを取得しました`)
    } else {
      // This path means items had data, but grouping failed (very unlikely if reduce is fine)
      console.error(
        'API返回了数据，但分组后未生成任何托盘组。请检查分组逻辑或数据完整性。',
        filteredItems,
      )
      ElMessage.error(
        'データの処理中に問題が発生しました。詳細については、コンソールログを確認してください。',
      )
    }
  } catch (error: any) {
    console.error('出荷データ取得エラー:', error)

    // 提供更详细的错误信息
    let errorMessage = '出荷データの取得に失敗しました'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }

    ElMessage.error(errorMessage)
  } finally {
    loading.value.fetch = false
  }
}

function resetFilters() {
  filters.value.status = ''
  filters.value.product_cd = ''
  dateRange.value = [today, today]
}

// 加载产品列表 - 加载所有产品
async function loadProductOptions() {
  try {
    // 先获取第一页数据以获取总数
    const firstPageResponse = await getProductList({ page: 1, pageSize: 100 })
    let total = 0
    let allProducts: any[] = []

    if (firstPageResponse?.success && firstPageResponse?.data) {
      total = firstPageResponse.data.total || 0
      allProducts = [...(firstPageResponse.data.list || [])]

      // 如果总数超过100，需要分页加载所有数据
      if (total > 100) {
        const totalPages = Math.ceil(total / 100)
        const promises: Promise<any>[] = []

        // 并行加载剩余页面
        for (let page = 2; page <= totalPages; page++) {
          promises.push(getProductList({ page, pageSize: 100 }))
        }

        const responses = await Promise.all(promises)
        responses.forEach((response) => {
          if (response?.success && response?.data?.list) {
            allProducts.push(...response.data.list)
          } else if (Array.isArray(response)) {
            allProducts.push(...response)
          }
        })
      }
    } else if (Array.isArray(firstPageResponse)) {
      // 如果直接返回数组，使用该数组
      allProducts = [...firstPageResponse]
    }

    // 去重并映射产品选项（只要有product_cd就包含，product_name可以为空）
    const productMap = new Map<string, string>()
    let skippedCount = 0
    allProducts.forEach((p: any) => {
      if (p.product_cd) {
        // 如果product_name为空，使用product_cd作为显示名称
        productMap.set(p.product_cd, p.product_name || p.product_cd || '')
      } else {
        skippedCount++
      }
    })

    productOptions.value = Array.from(productMap.entries())
      .map(([product_cd, product_name]) => ({
        product_cd,
        product_name,
      }))
      .sort((a, b) => {
        // 按产品名称排序（日文排序）
        return (a.product_name || '').localeCompare(b.product_name || '', 'ja')
      })

    console.log(`产品列表加载完成: 总共 ${allProducts.length} 个产品，已加载 ${productOptions.value.length} 个产品选项${skippedCount > 0 ? `，跳过 ${skippedCount} 个无产品代码的产品` : ''}`)
  } catch (error) {
    console.error('产品列表加载失败:', error)
    // 如果API失败，尝试从现有数据中提取产品列表
    extractProductsFromData()
  }
}

// 从现有数据中提取产品列表（备用方案）
function extractProductsFromData() {
  const productMap = new Map<string, string>()
  palletGroups.value.forEach((pallet) => {
    pallet.items.forEach((item) => {
      if (item.product_cd) {
        // 如果product_name为空，使用product_cd作为显示名称
        productMap.set(item.product_cd, item.product_name || item.product_cd || '')
      }
    })
  })
  productOptions.value = Array.from(productMap.entries())
    .map(([product_cd, product_name]) => ({
      product_cd,
      product_name,
    }))
    .sort((a, b) => {
      // 按产品名称排序（日文排序）
      return (a.product_name || '').localeCompare(b.product_name || '', 'ja')
    })
}

// 打印功能
function handlePrint() {
  if (filteredPalletGroups.value.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされています。ブラウザの設定を確認してください。')
    return
  }

  const currentDate = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

  // 构建筛选条件信息
  const filterInfo: string[] = []
  if (dateRange.value[0] && dateRange.value[1]) {
    filterInfo.push(`出荷日: ${dateRange.value[0]} ～ ${dateRange.value[1]}`)
  }
  if (filters.value.status) {
    filterInfo.push(`状態: ${filters.value.status}`)
  }
  if (filters.value.product_cd) {
    const product = productOptions.value.find((p) => p.product_cd === filters.value.product_cd)
    filterInfo.push(`製品: ${product ? `${product.product_cd} - ${product.product_name}` : filters.value.product_cd}`)
  }

  // 生成打印HTML
  const printContent = generatePrintHTML(filteredPalletGroups.value, filterInfo, currentDate)

  printWindow.document.write(printContent)
  printWindow.document.close()

  const closePreview = () => {
    try {
      if (printWindow && !printWindow.closed) printWindow.close()
    } catch (_) {}
  }

  let fallbackTimer: ReturnType<typeof setTimeout> | null = setTimeout(closePreview, 60000)

  const onAfterPrint = () => {
    if (fallbackTimer) {
      clearTimeout(fallbackTimer)
      fallbackTimer = null
    }
    closePreview()
    printWindow.removeEventListener('afterprint', onAfterPrint)
  }

  printWindow.onafterprint = onAfterPrint
  printWindow.addEventListener('afterprint', onAfterPrint)

  setTimeout(() => {
    printWindow.print()
  }, 250)
}

// 印刷用：出荷日 → 納入先 でグループ化し、表は 製品コード・製品名・箱数・状態・納入先
function generatePrintHTML(pallets: PalletGroup[], filterInfo: string[], currentDate: string): string {
  type Row = { product_cd: string; product_name: string; boxes: number; status: string; destination_name: string }
  const byDate = new Map<string, Map<string, Row[]>>()

  for (const pallet of pallets) {
    const dateKey = pallet.shipping_date || ''
    if (!byDate.has(dateKey)) byDate.set(dateKey, new Map())
    const byDest = byDate.get(dateKey)!

    for (const item of pallet.items) {
      const destKey = (item.destination_name || item.destination_cd || '').trim() || '-'
      if (!byDest.has(destKey)) byDest.set(destKey, [])
      byDest.get(destKey)!.push({
        product_cd: item.product_cd || '-',
        product_name: item.product_name || '-',
        boxes: Number(item.confirmed_boxes) || 0,
        status: getStatusText(item.status),
        destination_name: item.destination_name || item.destination_cd || '-',
      })
    }
  }

  const sortedDates = Array.from(byDate.keys()).sort()
  const sections: string[] = []

  for (const dateKey of sortedDates) {
    const byDest = byDate.get(dateKey)!
    const destKeys = Array.from(byDest.keys()).sort((a, b) => (a === '-' ? 1 : b === '-' ? -1 : a.localeCompare(b)))
    const dateLabel = dateKey ? formatDate(dateKey) : '-'

    for (const destKey of destKeys) {
      const rows = byDest.get(destKey)!
      const destLabel = destKey === '-' ? '（納入先未設定）' : destKey
      const rowsHtml = rows
        .map(
          (r) => `
        <tr>
          <td>${escapeHtml(r.product_cd)}</td>
          <td>${escapeHtml(r.product_name)}</td>
          <td class="text-right">${r.boxes.toLocaleString()}</td>
          <td class="text-center">${escapeHtml(r.status)}</td>
          <td>${escapeHtml(r.destination_name)}</td>
        </tr>`,
        )
        .join('')

      sections.push(`
      <div class="print-section">
        <div class="print-section-title">出荷日: ${escapeHtml(dateLabel)}　納入先: ${escapeHtml(destLabel)}</div>
        <table class="print-table">
          <thead>
            <tr>
              <th style="width: 18%">製品コード</th>
              <th style="width: 32%">製品名</th>
              <th style="width: 12%">箱数</th>
              <th style="width: 14%">状態</th>
              <th style="width: 24%">納入先</th>
            </tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>`)
    }
  }

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>ピッキングリスト印刷</title>
      <style>
        @media print {
          @page { size: A4; margin: 12mm; }
        }
        body {
          font-family: 'MS Gothic', 'Yu Gothic', sans-serif;
          font-size: 11px;
          margin: 0;
          padding: 16px;
        }
        .print-header {
          text-align: center;
          margin-bottom: 14px;
          border-bottom: 2px solid #333;
          padding-bottom: 8px;
        }
        .print-title { font-size: 18px; font-weight: bold; margin-bottom: 4px; }
        .print-info { font-size: 10px; color: #555; }
        .print-info div { margin: 2px 0; }
        .print-section { margin-bottom: 16px; break-inside: avoid; }
        .print-section-title {
          font-weight: bold;
          padding: 6px 8px;
          background: #e8f4f8;
          border: 1px solid #333;
          border-bottom: none;
        }
        .print-table {
          width: 100%;
          border-collapse: collapse;
        }
        .print-table th, .print-table td {
          border: 1px solid #333;
          padding: 5px 6px;
          text-align: left;
        }
        .print-table th {
          background: #f0f0f0;
          font-weight: bold;
          text-align: center;
        }
        .print-table .text-right { text-align: right; }
        .print-table .text-center { text-align: center; }
        .print-footer {
          text-align: center;
          font-size: 9px;
          color: #666;
          margin-top: 14px;
          border-top: 1px solid #ccc;
          padding-top: 8px;
        }
      </style>
    </head>
    <body>
      <div class="print-header">
        <div class="print-title">ピッキングリスト</div>
        <div class="print-info">
          <div>印刷日時: ${escapeHtml(currentDate)}</div>
          <div>${filterInfo.length > 0 ? `検索条件: ${filterInfo.join(' | ')}` : '検索条件: 全て'}</div>
        </div>
      </div>
      ${sections.join('')}
      <div class="print-footer">
        この資料は ${escapeHtml(currentDate)} に印刷されました。 | Smart-EMAP
      </div>
    </body>
    </html>
  `
}

function escapeHtml(s: string): string {
  if (s == null || s === '') return ''
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// 快捷日期设置函数
function setDateRange(dayOffset: number) {
  if (dayOffset === 0) {
    // 今日按钮：设置为今天
    const today = new Date()
    const dateStr = today.toISOString().slice(0, 10)
    dateRange.value = [dateStr, dateStr]
  } else {
    // 前日/翌日按钮：基于当前选择的日期进行增减
    const currentDate = dateRange.value[0] ? new Date(dateRange.value[0]) : new Date()
    currentDate.setDate(currentDate.getDate() + dayOffset)
    const dateStr = currentDate.toISOString().slice(0, 10)
    dateRange.value = [dateStr, dateStr]
  }
}

async function syncShippingData() {
  loading.value.sync = true
  try {
    console.log('開始shipping_itemsからpicking_tasksへデータ同期...')

    // 使用已有的同步API
    const response = (await request.post('/api/shipping/picking/sync-data')) as ApiResponseBody

    console.log('データ同期レスポンス:', response)

    if (response.success) {
      ElMessage.success(response.message || 'データ同期が完了しました')
      // 立即刷新数据
      await fetchShippingData()
      console.log(`syncShippingData完成后，palletGroups数量: ${palletGroups.value.length}`)
    } else {
      ElMessage.error(response.message || 'データ同期に失敗しました')
    }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    console.error('データ同期エラー:', error)

    let errorMessage = 'データ同期に失敗しました'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }

    ElMessage.error(errorMessage)
  } finally {
    loading.value.sync = false
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  // 使用日本标准时间格式化日期
  const date = new Date(dateStr + 'T00:00:00+09:00') // 确保使用JST时区
  return date.toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo' })
}

function getStatusText(status: string) {
  switch (status) {
    case 'completed':
      return 'ピッキング済'
    case 'picking':
      return '作業中'
    case 'pending':
      return '未ピッキング'
    default:
      return status || '未ピッキング'
  }
}

function getStatusType(status: string) {
  switch (status) {
    case 'completed':
      return 'success'
    case 'picking':
      return 'primary'
    case 'pending':
      return 'warning'
    default:
      return 'info'
  }
}

// 防抖函数：延迟执行数据获取，避免频繁请求
function debouncedFetchData() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    fetchShippingData()
  }, 500) // 500ms 防抖延迟
}

// クライアント側フィルタ（製品）変更時はページを1に戻す
watch(() => filters.value.product_cd, () => {
  currentPage.value = 1
})

// 监听筛选条件变化，自动重新获取数据
watch(
  [dateRange, () => filters.value.status],
  () => {
    debouncedFetchData()
  },
  { deep: true },
)

// 监听产品筛选变化，不需要重新获取数据，只需要前端筛选
watch(
  () => filters.value.product_cd,
  () => {
    // 产品筛选是前端筛选，不需要重新请求API
    // 但如果数据为空，可能需要重新加载产品选项
    if (palletGroups.value.length > 0 && productOptions.value.length === 0) {
      extractProductsFromData()
    }
  },
)

onMounted(async () => {
  // 加载产品列表
  await loadProductOptions()
  // 页面加载时直接获取数据，不需要用户手动筛选
  await fetchShippingData()
  // 如果产品列表为空，从数据中提取
  if (productOptions.value.length === 0 && palletGroups.value.length > 0) {
    extractProductsFromData()
  }
})
</script>

<style scoped>
.picking-list-generator {
  padding: 0 2px 6px;
}

/* 上部：标题与按钮 - 紧凑 */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.title-section { flex: 1; }

.page-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 2px 0;
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

.page-subtitle {
  margin: 0;
  color: #64748b;
  font-size: 11px;
}

.action-buttons-section {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 筛选区域 - 紧凑 */
.filter-section {
  margin-bottom: 8px;
}

.filter-section :deep(.el-card) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.filter-section :deep(.el-card__header) {
  padding: 6px 12px;
  font-size: 12px;
}
.filter-section :deep(.el-card__body) {
  padding: 8px 12px;
}
.compact-date-picker {
  width: 240px !important;
}
.filter-form :deep(.el-form-item) {
  margin-bottom: 6px;
  margin-right: 12px;
}
.filter-form :deep(.el-form-item__label) {
  font-size: 12px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 13px;
}

.filter-form {
  margin: 0;
}

.filter-form .el-form-item {
  margin-bottom: 0;
}

.date-picker-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-quick-buttons {
  display: flex;
  gap: 4px;
}

.date-quick-buttons .el-button {
  min-width: 42px;
  padding: 5px 10px;
  font-size: 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.date-quick-buttons .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* 列表区域 - 紧凑 */
.list-section {
  margin-bottom: 0;
}

.list-section :deep(.el-card) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.list-section :deep(.el-card__header) {
  padding: 6px 12px;
  font-size: 12px;
}
.list-section :deep(.el-card__body) {
  padding: 8px 12px;
}
.list-section :deep(.el-table) {
  font-size: 12px;
}
.list-section :deep(.el-table th),
.list-section :deep(.el-table td) {
  padding: 6px 8px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 13px;
}

.list-actions {
  display: flex;
  gap: 6px;
}

.loading-state,
.empty-state {
  padding: 24px 12px;
  text-align: center;
}

.is-loading {
  animation: rotating 2s linear infinite;
  color: #409eff;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.empty-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 10px;
}

.empty-hint {
  color: #64748b;
  font-size: 12px;
  margin: 0;
}

.pallet-table {
  overflow: hidden;
}

.pallet-pagination {
  margin-top: 10px;
  justify-content: flex-end;
}
.pallet-pagination :deep(.el-pagination__total) {
  font-size: 12px;
}

.pallet-main-table {
  margin-bottom: 0;
}

.pallet-no-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pallet-number {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.quantity-value {
  font-weight: 600;
  color: #67c23a;
}

.box-value {
  font-weight: 600;
  color: #409eff;
}

.product-list {
  max-height: 100px;
  overflow-y: auto;
}

.product-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}

.product-item:last-child {
  border-bottom: none;
}

.product-code {
  font-family: monospace;
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  min-width: 80px;
}

.product-name {
  flex: 1;
  font-size: 12px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-quantity {
  font-size: 12px;
  font-weight: 600;
  color: #67c23a;
  min-width: 60px;
  text-align: right;
}

.destination-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.destination-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.destination-code {
  font-size: 11px;
  color: #909399;
}

.picker-id {
  font-weight: 600;
  color: #409eff;
  font-size: 13px;
}

.no-picker {
  color: #909399;
  font-size: 12px;
  font-style: italic;
}

/* 响应式设计 */

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .action-buttons-section {
    justify-content: flex-end;
  }

  .filter-form {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .date-picker-group {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .date-quick-buttons {
    justify-content: center;
  }

  .date-quick-buttons .el-button {
    flex: 1;
    max-width: 80px;
  }

  .list-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .pallet-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}

/* 统计卡片 - 紧凑横並び・余白削減 */
.statistics-section {
  margin-bottom: 6px;
}

.statistics-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}
@media (max-width: 992px) {
  .statistics-cards { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .statistics-cards { grid-template-columns: 1fr; }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}
.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
}
.stat-card .stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  flex-shrink: 0;
  font-size: 14px;
  color: #fff;
  background: rgba(255, 255, 255, 0.25);
}
.stat-card .stat-value {
  font-weight: 700;
  font-size: 15px;
  line-height: 1;
  color: #fff;
  letter-spacing: 0.02em;
}
.stat-card .stat-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.9);
  margin-left: auto;
  white-space: nowrap;
}
.total-card { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); }
.pending-card { background: linear-gradient(135deg, #ec4899 0%, #f43f5e 100%); }
.completed-card { background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); }
.completion-card { background: linear-gradient(135deg, #10b981 0%, #34d399 100%); }
</style>
