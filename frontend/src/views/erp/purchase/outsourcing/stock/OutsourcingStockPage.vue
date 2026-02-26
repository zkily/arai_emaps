<template>
  <div class="outsourcing-stock-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2 class="title">
            <div class="title-icon">
              <el-icon><Box /></el-icon>
            </div>
            <span class="title-text">外注在庫管理</span>
          </h2>
          <p class="subtitle">外注メッキ・溶接品の在庫状況を一元管理します</p>
        </div>
        <div class="header-stats">
          <div class="stat-item plating">
            <span class="stat-value">{{ platingStockCount }}</span>
            <span class="stat-label">メッキ品種</span>
          </div>
          <div class="stat-item welding">
            <span class="stat-value">{{ weldingStockCount }}</span>
            <span class="stat-label">溶接品種</span>
          </div>
          <div class="stat-item total">
            <span class="stat-value">{{ totalStockQty.toLocaleString() }}</span>
            <span class="stat-label">総在庫数</span>
          </div>
        </div>
      </div>
    </div>

    <!-- タブ切替 -->
    <el-tabs v-model="activeTab" type="card" class="stock-tabs">
      <el-tab-pane label="メッキ品在庫" name="plating">
        <template #label>
          <span class="tab-label">
            <el-icon><Brush /></el-icon>
            メッキ品在庫
            <el-badge :value="platingStockCount" class="tab-badge" />
          </span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="溶接品在庫" name="welding">
        <template #label>
          <span class="tab-label">
            <el-icon><Operation /></el-icon>
            溶接品在庫
            <el-badge :value="weldingStockCount" class="tab-badge" />
          </span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <!-- 検索フィルター -->
    <el-card class="filter-card">
      <template #header>
        <div class="filter-header">
          <el-icon class="filter-icon"><Search /></el-icon>
          <span>検索条件</span>
        </div>
      </template>
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="外注先">
          <el-select
            v-model="filters.supplier"
            placeholder="選択"
            clearable
            filterable
            style="width: 160px"
          >
            <el-option
              v-for="s in supplierOptions"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="品番">
          <el-input
            v-model="filters.productCode"
            placeholder="品番入力"
            clearable
            style="width: 130px"
          />
        </el-form-item>
        <el-form-item label="在庫状況">
          <el-select
            v-model="filters.stockStatus"
            placeholder="選択"
            clearable
            style="width: 120px"
          >
            <el-option label="正常" value="normal" />
            <el-option label="僅少" value="low" />
            <el-option label="なし" value="empty" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="loading">
            <el-icon><Search /></el-icon>検索
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>リセット
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作按钮栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="warning" @click="exportData">
          <el-icon><Download /></el-icon>Excel出力
        </el-button>
        <el-button type="info" @click="refreshStock">
          <el-icon><Refresh /></el-icon>在庫更新
        </el-button>
        <el-button type="primary" @click="viewStockHistory">
          <el-icon><Document /></el-icon>入出庫履歴
        </el-button>
      </div>
      <div class="right-actions">
        <el-tag v-if="lowStockCount > 0" type="warning" size="large" class="alert-tag">
          <el-icon><Warning /></el-icon>
          {{ lowStockCount }}件の在庫が僅少です
        </el-tag>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        :data="currentStockList"
        v-loading="loading"
        stripe
        border
        highlight-current-row
        class="data-table"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
        :row-class-name="getRowClassName"
      >
        <el-table-column prop="productCode" label="品番" width="120" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row)">{{ row.productCode }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="productName" label="品名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="supplier" label="外注先" width="140" />
        <el-table-column
          v-if="activeTab === 'plating'"
          prop="platingType"
          label="メッキ種類"
          width="100"
        />
        <el-table-column
          v-if="activeTab === 'welding'"
          prop="weldingType"
          label="溶接種類"
          width="100"
        />
        <el-table-column prop="orderedQty" label="発注累計" width="90" align="right">
          <template #default="{ row }">
            {{ row.orderedQty.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="receivedQty" label="入庫累計" width="90" align="right">
          <template #default="{ row }">
            {{ row.receivedQty.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="usedQty" label="出庫累計" width="90" align="right">
          <template #default="{ row }">
            {{ row.usedQty.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="stockQty" label="現在庫" width="90" align="right">
          <template #default="{ row }">
            <span :class="getStockClass(row)">{{ row.stockQty.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pendingQty" label="入庫予定" width="90" align="right">
          <template #default="{ row }">
            <span class="pending-qty">{{ row.pendingQty.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状況" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStockStatusType(row)" size="small">
              {{ getStockStatusLabel(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastReceiveDate" label="最終入庫日" width="100" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewHistory(row)">
              <el-icon><View /></el-icon>履歴
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>

    <!-- 概要カード -->
    <el-row :gutter="16" class="summary-cards">
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-icon blue">
              <el-icon><Box /></el-icon>
            </div>
            <div class="summary-info">
              <span class="summary-value">{{ totalStockQty.toLocaleString() }}</span>
              <span class="summary-label">総在庫数量</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-icon green">
              <el-icon><Download /></el-icon>
            </div>
            <div class="summary-info">
              <span class="summary-value">{{ totalReceivedQty.toLocaleString() }}</span>
              <span class="summary-label">今月入庫数</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-icon orange">
              <el-icon><Upload /></el-icon>
            </div>
            <div class="summary-info">
              <span class="summary-value">{{ totalUsedQty.toLocaleString() }}</span>
              <span class="summary-label">今月出庫数</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-icon purple">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="summary-info">
              <span class="summary-value">{{ totalPendingQty.toLocaleString() }}</span>
              <span class="summary-label">入庫予定数</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="在庫詳細" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="品番">{{ detailData.productCode }}</el-descriptions-item>
        <el-descriptions-item label="品名">{{ detailData.productName }}</el-descriptions-item>
        <el-descriptions-item label="外注先">{{ detailData.supplier }}</el-descriptions-item>
        <el-descriptions-item :label="activeTab === 'plating' ? 'メッキ種類' : '溶接種類'">
          {{ activeTab === 'plating' ? detailData.platingType : detailData.weldingType }}
        </el-descriptions-item>
        <el-descriptions-item label="発注累計">{{
          detailData.orderedQty?.toLocaleString()
        }}</el-descriptions-item>
        <el-descriptions-item label="入庫累計">{{
          detailData.receivedQty?.toLocaleString()
        }}</el-descriptions-item>
        <el-descriptions-item label="出庫累計">{{
          detailData.usedQty?.toLocaleString()
        }}</el-descriptions-item>
        <el-descriptions-item label="現在庫">
          <span :class="getStockClass(detailData)">{{
            detailData.stockQty?.toLocaleString()
          }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="入庫予定">{{
          detailData.pendingQty?.toLocaleString()
        }}</el-descriptions-item>
        <el-descriptions-item label="状況">
          <el-tag :type="getStockStatusType(detailData)">{{
            getStockStatusLabel(detailData)
          }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最終入庫日">{{
          detailData.lastReceiveDate
        }}</el-descriptions-item>
        <el-descriptions-item label="最終出庫日">{{
          detailData.lastIssueDate || '-'
        }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 履歴对话框 -->
    <el-dialog v-model="historyVisible" :title="historyTitle" width="850px">
      <el-table :data="historyData" border stripe>
        <el-table-column prop="date" label="日付" width="100" />
        <el-table-column prop="type" label="種別" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.type === 'receive' ? 'success' : 'warning'" size="small">
              {{ row.type === 'receive' ? '入庫' : '出庫' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="orderNo" label="関連番号" width="130" />
        <el-table-column prop="quantity" label="数量" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.type === 'receive' ? 'text-success' : 'text-warning'">
              {{ row.type === 'receive' ? '+' : '-' }}{{ row.quantity.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="stockAfter" label="在庫残" width="100" align="right">
          <template #default="{ row }">
            {{ row.stockAfter.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="担当者" width="80" />
        <el-table-column prop="remarks" label="備考" min-width="150" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * 外注在庫管理
 * - 外注先: outsourcing_suppliers（筛选下拉・列表外注先名）
 * - メッキTab: outsourcing_plating_stock（getPlatingStock）
 * - 溶接Tab: outsourcing_welding_stock（getWeldingStock）
 * - 在庫履歴弹窗: outsourcing_stock_transactions（getOutsourcingStockHistory）
 */
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
  Download,
  Box,
  Warning,
  View,
  Document,
  Upload,
  Calendar,
  Brush,
  Operation,
} from '@element-plus/icons-vue'
import {
  getPlatingStock,
  getWeldingStock,
  getOutsourcingStockHistory,
  getSuppliers,
  type OutsourcingSupplier,
} from '@/api/outsourcing'

/** API 响应体（request 拦截器已返回 response.data） */
type SupplierListRes = { success?: boolean; data?: OutsourcingSupplier[] }
type StockListRes = { success?: boolean; data?: unknown[]; total?: number }

interface StockItem {
  id: number
  productCode: string
  productName: string
  supplier: string
  supplierId: number
  supplierCd?: string
  platingType?: string
  weldingType?: string
  orderedQty: number
  receivedQty: number
  usedQty: number
  stockQty: number
  pendingQty: number
  minStock: number
  lastReceiveDate: string
  lastIssueDate?: string
}

interface HistoryItem {
  date: string
  type: 'receive' | 'issue'
  orderNo: string
  quantity: number
  stockAfter: number
  operator: string
  remarks: string
}

const loading = ref(false)
const activeTab = ref('plating')
const detailVisible = ref(false)
const historyVisible = ref(false)
const historyTitle = ref('')

const filters = reactive({
  supplier: '',
  productCode: '',
  stockStatus: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const detailData = ref<Partial<StockItem>>({})
const historyData = ref<HistoryItem[]>([])

const platingStockList = ref<StockItem[]>([])
const weldingStockList = ref<StockItem[]>([])

const supplierOptions = ref<Array<{ value: number; label: string }>>([])

// 数据转换：后端snake_case -> 前端camelCase
const convertStockFromBackend = (item: any): StockItem => {
  return {
    id: item.id,
    productCode: item.product_cd || item.productCode,
    productName: item.product_name || item.productName,
    supplier: item.supplier_name || item.supplier || '',
    supplierId: item.supplier_id || item.supplierId,
    supplierCd: item.supplier_cd || item.supplierCd || '',
    platingType: item.plating_type || item.platingType,
    weldingType: item.welding_type || item.weldingType,
    orderedQty: item.ordered_qty || item.orderedQty || 0,
    receivedQty: item.received_qty || item.receivedQty || 0,
    usedQty: item.used_qty || item.usedQty || 0,
    stockQty: item.stock_qty || item.stockQty || 0,
    pendingQty: item.pending_qty || item.pendingQty || 0,
    minStock: item.min_stock || item.minStock || 0,
    lastReceiveDate: item.last_receive_date || item.lastReceiveDate || '',
    lastIssueDate: item.last_issue_date || item.lastIssueDate,
  }
}

const currentStockList = computed(() => {
  return activeTab.value === 'plating' ? platingStockList.value : weldingStockList.value
})

const platingStockCount = computed(() => platingStockList.value.length)
const weldingStockCount = computed(() => weldingStockList.value.length)
const totalStockQty = computed(() =>
  [...platingStockList.value, ...weldingStockList.value].reduce((sum, i) => sum + i.stockQty, 0),
)
const totalReceivedQty = computed(() =>
  currentStockList.value.reduce((sum, i) => sum + i.receivedQty, 0),
)
const totalUsedQty = computed(() => currentStockList.value.reduce((sum, i) => sum + i.usedQty, 0))
const totalPendingQty = computed(() =>
  currentStockList.value.reduce((sum, i) => sum + i.pendingQty, 0),
)
const lowStockCount = computed(
  () =>
    currentStockList.value.filter((i) => i.stockQty > 0 && i.stockQty < i.minStock).length +
    currentStockList.value.filter((i) => i.stockQty === 0).length,
)

const getRowClassName = ({ row }: { row: StockItem }) => {
  if (row.stockQty === 0) return 'empty-row'
  if (row.stockQty < row.minStock) return 'warning-row'
  return ''
}

const getStockClass = (row: Partial<StockItem>) => {
  if (!row.stockQty && row.stockQty !== 0) return ''
  if (row.stockQty === 0) return 'stock-empty'
  if (row.minStock && row.stockQty < row.minStock) return 'stock-low'
  return 'stock-normal'
}

const getStockStatusType = (row: Partial<StockItem>) => {
  if (!row.stockQty && row.stockQty !== 0) return 'info'
  if (row.stockQty === 0) return 'danger'
  if (row.minStock && row.stockQty < row.minStock) return 'warning'
  return 'success'
}

const getStockStatusLabel = (row: Partial<StockItem>) => {
  if (!row.stockQty && row.stockQty !== 0) return '-'
  if (row.stockQty === 0) return 'なし'
  if (row.minStock && row.stockQty < row.minStock) return '僅少'
  return '正常'
}

// 加载外注先列表
const loadSuppliers = async () => {
  try {
    const res = (await getSuppliers({ isActive: true })) as unknown as SupplierListRes | OutsourcingSupplier[]
    let suppliers: any[] = []

    if (Array.isArray(res)) {
      suppliers = res
    } else if (res?.data && Array.isArray(res.data)) {
      suppliers = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      suppliers = res.data
    }

    supplierOptions.value = suppliers.map((s) => {
      const supplierId = s.id
      const supplierName = s.supplier_name || s.name || ''
      const supplierCd = s.supplier_cd || s.code || ''
      return {
        value: supplierId,
        label: supplierCd ? `${supplierCd} - ${supplierName}` : supplierName,
      }
    })
  } catch (error) {
    console.error('外注先取得エラー:', error)
    ElMessage.error('外注先データの取得に失敗しました')
  }
}

const handleSearch = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      pageSize: pagination.pageSize,
    }

    if (filters.supplier) {
      params.supplierId = filters.supplier
    }

    if (filters.productCode) {
      params.productCode = filters.productCode
    }

    if (filters.stockStatus) {
      params.stockStatus = filters.stockStatus
    }

    if (activeTab.value === 'plating') {
      const res = (await getPlatingStock(params)) as unknown as StockListRes
      let data: any[] = []
      let total = 0

      if (res?.success && res.data) {
        data = Array.isArray(res.data) ? res.data : []
        total = res.total ?? 0
      } else if (Array.isArray(res)) {
        data = res
        total = res.length
      } else if (res?.data && Array.isArray(res.data)) {
        data = res.data
        total = res?.total ?? data.length
      }

      platingStockList.value = data.map(convertStockFromBackend)
      pagination.total = total
    } else {
      const res = (await getWeldingStock(params)) as unknown as StockListRes
      let data: any[] = []
      let total = 0

      if (res?.success && res.data) {
        data = Array.isArray(res.data) ? res.data : []
        total = res.total ?? 0
      } else if (Array.isArray(res)) {
        data = res
        total = res.length
      } else if (res?.data && Array.isArray(res.data)) {
        data = res.data
        total = res?.total ?? data.length
      }

      weldingStockList.value = data.map(convertStockFromBackend)
      pagination.total = total
    }
  } catch (error: any) {
    console.error('在庫データ取得エラー:', error)
    ElMessage.error(error?.message || '在庫データの取得に失敗しました')
    if (activeTab.value === 'plating') {
      platingStockList.value = []
    } else {
      weldingStockList.value = []
    }
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, { supplier: '', productCode: '', stockStatus: '' })
  handleSearch()
}

const viewDetail = (row: StockItem) => {
  detailData.value = row
  detailVisible.value = true
}

const viewHistory = async (row: StockItem) => {
  historyTitle.value = `${row.productCode} - ${row.productName} 入出庫履歴`
  historyVisible.value = true
  loading.value = true

  try {
    const processType = activeTab.value === 'plating' ? 'plating' : 'welding'
    const res = (await getOutsourcingStockHistory({
      processType,
      productCd: row.productCode,
      supplierCd: row.supplierCd || '',
      weldingType: row.weldingType,
    })) as unknown as StockListRes

    let data: any[] = []
    if (res?.success && Array.isArray(res.data)) {
      data = res.data
    } else if (Array.isArray(res)) {
      data = res
    } else if (res?.data && Array.isArray(res.data)) {
      data = res.data
    }

    historyData.value = data.map((item: any) => ({
      date: item.transaction_date || item.date || '',
      type: item.transaction_type === 'receive' ? 'receive' : 'issue',
      orderNo: item.related_no || item.orderNo || '',
      quantity: item.quantity || 0,
      stockAfter: item.stock_after || item.stockAfter || 0,
      operator: item.operator || '',
      remarks: item.remarks || '',
    }))
  } catch (error: any) {
    console.error('履歴データ取得エラー:', error)
    ElMessage.error(error?.message || '履歴データの取得に失敗しました')
    historyData.value = []
  } finally {
    loading.value = false
  }
}

const viewStockHistory = () => {
  ElMessage.info('入出庫履歴画面へ遷移します')
}

const refreshStock = async () => {
  ElMessage.info('在庫情報を更新しています...')
  await handleSearch()
  ElMessage.success('在庫情報を更新しました')
}

const exportData = () => {
  ElMessage.info('Excel出力機能は準備中です')
}

// 监听标签页切换
watch(activeTab, () => {
  pagination.page = 1
  handleSearch()
})

// 监听分页变化
watch(
  () => pagination.page,
  () => {
    handleSearch()
  },
)

watch(
  () => pagination.pageSize,
  () => {
    pagination.page = 1
    handleSearch()
  },
)

onMounted(async () => {
  await loadSuppliers()
  await handleSearch()
})
</script>

<style scoped>
.outsourcing-stock-page {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
  color: white;
  box-shadow: 0 4px 20px rgba(30, 60, 114, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.title-icon {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  opacity: 0.9;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  min-width: 75px;
}

.stat-item.plating {
  background: rgba(78, 205, 196, 0.2);
  border: 1px solid rgba(78, 205, 196, 0.3);
}

.stat-item.welding {
  background: rgba(240, 147, 251, 0.2);
  border: 1px solid rgba(240, 147, 251, 0.3);
}

.stat-item.total {
  background: rgba(255, 255, 255, 0.2);
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
}

.stat-label {
  font-size: 11px;
  opacity: 0.9;
}

.stock-tabs {
  margin-bottom: 16px;
}

.stock-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.stock-tabs :deep(.el-tabs__item) {
  height: 44px;
  line-height: 44px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-badge {
  margin-left: 4px;
}

.filter-card {
  margin-bottom: 16px;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.filter-card :deep(.el-card__header) {
  padding: 12px 16px;
  background: #fafbfc;
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
}

.filter-icon {
  color: #1e3c72;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.left-actions {
  display: flex;
  gap: 10px;
}

.alert-tag {
  display: flex;
  align-items: center;
  gap: 6px;
}

.table-card {
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 16px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.data-table :deep(.warning-row) {
  background-color: #fef9e7;
}

.data-table :deep(.empty-row) {
  background-color: #fdecea;
}

.stock-normal {
  color: #67c23a;
  font-weight: 600;
}

.stock-low {
  color: #e6a23c;
  font-weight: 600;
}

.stock-empty {
  color: #f56c6c;
  font-weight: 600;
}

.pending-qty {
  color: #409eff;
  font-weight: 500;
}

.pagination-wrapper {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #ebeef5;
}

.summary-cards {
  margin-top: 16px;
}

.summary-card {
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.summary-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.summary-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.summary-icon.blue {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
}

.summary-icon.green {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.summary-icon.orange {
  background: linear-gradient(135deg, #ffc107, #ff9800);
}

.summary-icon.purple {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.summary-info {
  display: flex;
  flex-direction: column;
}

.summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.summary-label {
  font-size: 12px;
  color: #909399;
}

.text-success {
  color: #67c23a;
  font-weight: 600;
}

.text-warning {
  color: #e6a23c;
  font-weight: 600;
}

@media (max-width: 768px) {
  .outsourcing-stock-page {
    padding: 12px;
  }
  .page-header {
    padding: 16px;
  }
  .title {
    font-size: 18px;
  }
  .header-stats {
    display: none;
  }
  .action-bar {
    flex-direction: column;
    gap: 12px;
  }
  .summary-cards :deep(.el-col) {
    margin-bottom: 12px;
  }
}
</style>
