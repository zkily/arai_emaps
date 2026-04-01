<template>
  <div class="outsourcing-stock-page">
    <!-- 页面头部：标题 + 统计指标 -->
    <div class="page-header">
      <div class="header-left">
        <div class="title-icon"><el-icon><Box /></el-icon></div>
        <div>
          <h2 class="title">外注在庫管理</h2>
          <p class="subtitle">外注メッキ・溶接品の在庫状況を一元管理</p>
        </div>
      </div>
      <div class="header-kpis">
        <div class="kpi kpi-teal">
          <span class="kpi-val">{{ platingStockCount }}</span>
          <span class="kpi-lbl">メッキ品種</span>
        </div>
        <div class="kpi kpi-purple">
          <span class="kpi-val">{{ weldingStockCount }}</span>
          <span class="kpi-lbl">溶接品種</span>
        </div>
        <div class="kpi kpi-blue">
          <span class="kpi-val">{{ totalStockQty.toLocaleString() }}</span>
          <span class="kpi-lbl">総在庫数</span>
        </div>
        <div class="kpi kpi-amber" v-if="lowStockCount > 0">
          <span class="kpi-val">{{ lowStockCount }}</span>
          <span class="kpi-lbl">僅少警告</span>
        </div>
      </div>
    </div>

    <!-- タブ + フィルター + 操作 一体化 -->
    <div class="toolbar-strip">
      <el-tabs v-model="activeTab" class="strip-tabs">
        <el-tab-pane name="plating">
          <template #label>
            <span class="tab-label"><el-icon><Brush /></el-icon>メッキ品在庫<el-badge :value="platingStockCount" class="tab-badge" /></span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="welding">
          <template #label>
            <span class="tab-label"><el-icon><Operation /></el-icon>溶接品在庫<el-badge :value="weldingStockCount" class="tab-badge" /></span>
          </template>
        </el-tab-pane>
      </el-tabs>

      <div class="filter-row">
        <el-select v-model="filters.supplier" placeholder="外注先" clearable filterable size="default" style="width:155px">
          <el-option v-for="s in supplierOptions" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
        <el-input v-model="filters.productCode" placeholder="品番" clearable size="default" style="width:120px" />
        <el-select v-model="filters.stockStatus" placeholder="在庫状況" clearable size="default" style="width:110px">
          <el-option label="正常" value="normal" />
          <el-option label="僅少" value="low" />
          <el-option label="なし" value="empty" />
        </el-select>
        <el-button type="primary" @click="handleSearch" :loading="loading" size="default">
          <el-icon><Search /></el-icon>検索
        </el-button>
        <el-divider direction="vertical" />
        <el-button @click="refreshStock" size="default">
          <el-icon><Refresh /></el-icon>更新
        </el-button>
        <el-button @click="exportData" size="default">
          <el-icon><Download /></el-icon>Excel
        </el-button>
        <el-button @click="viewStockHistory" size="default">
          <el-icon><Document /></el-icon>履歴
        </el-button>
      </div>
    </div>

    <!-- 概要指標行 -->
    <div class="summary-strip">
      <div class="sm-card sm-blue">
        <el-icon class="sm-icon"><Box /></el-icon>
        <div class="sm-body">
          <span class="sm-val">{{ totalStockQty.toLocaleString() }}</span>
          <span class="sm-lbl">総在庫数量</span>
        </div>
      </div>
      <div class="sm-card sm-green">
        <el-icon class="sm-icon"><Download /></el-icon>
        <div class="sm-body">
          <span class="sm-val">{{ totalReceivedQty.toLocaleString() }}</span>
          <span class="sm-lbl">今月入庫数</span>
        </div>
      </div>
      <div class="sm-card sm-orange">
        <el-icon class="sm-icon"><Upload /></el-icon>
        <div class="sm-body">
          <span class="sm-val">{{ totalUsedQty.toLocaleString() }}</span>
          <span class="sm-lbl">今月出庫数</span>
        </div>
      </div>
      <div class="sm-card sm-violet">
        <el-icon class="sm-icon"><Calendar /></el-icon>
        <div class="sm-body">
          <span class="sm-val">{{ totalPendingQty.toLocaleString() }}</span>
          <span class="sm-lbl">入庫予定数</span>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-wrap">
      <el-table
        :data="currentStockList"
        v-loading="loading"
        stripe
        border
        highlight-current-row
        class="data-table"
        :header-cell-style="{ background: '#f0f2f5', color: '#303133', fontWeight: '600', fontSize: '12px', padding: '6px 0' }"
        :cell-style="{ padding: '4px 0', fontSize: '12.5px' }"
        :row-class-name="getRowClassName"
        size="default"
      >
        <el-table-column prop="productCode" label="製品CD" width="80" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row)">{{ row.productCode }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="productName" label="品名" width="140" show-overflow-tooltip />
        <el-table-column prop="supplier" label="外注先" width="180" show-overflow-tooltip />
        <el-table-column v-if="activeTab === 'plating'" prop="platingType" label="メッキ種類" width="100" align="center" />
        <el-table-column v-if="activeTab === 'welding'" prop="weldingType" label="溶接種類" width="100" align="center" />
        <el-table-column prop="orderedQty" label="発注累計" width="85" align="right">
          <template #default="{ row }">{{ row.orderedQty.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="receivedQty" label="入庫累計" width="85" align="right">
          <template #default="{ row }">{{ row.receivedQty.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="usedQty" label="出庫累計" width="85" align="right">
          <template #default="{ row }">{{ row.usedQty.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="stockQty" label="現在庫" width="85" align="right">
          <template #default="{ row }">
            <span :class="getStockClass(row)">{{ row.stockQty.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pendingQty" label="入庫予定" width="85" align="right">
          <template #default="{ row }">
            <span class="pending-qty">{{ row.pendingQty.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状況" width="72" align="center">
          <template #default="{ row }">
            <el-tag :type="getStockStatusType(row)" size="small" effect="light">{{ getStockStatusLabel(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastReceiveDate" label="最終入庫日" width="96" align="center" />
        <el-table-column label="操作" width="70" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewHistory(row)">
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
          size="small"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="在庫詳細" width="640px" class="detail-dialog">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="品番">{{ detailData.productCode }}</el-descriptions-item>
        <el-descriptions-item label="品名">{{ detailData.productName }}</el-descriptions-item>
        <el-descriptions-item label="外注先">{{ detailData.supplier }}</el-descriptions-item>
        <el-descriptions-item :label="activeTab === 'plating' ? 'メッキ種類' : '溶接種類'">
          {{ activeTab === 'plating' ? detailData.platingType : detailData.weldingType }}
        </el-descriptions-item>
        <el-descriptions-item label="発注累計">{{ detailData.orderedQty?.toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="入庫累計">{{ detailData.receivedQty?.toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="出庫累計">{{ detailData.usedQty?.toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="現在庫">
          <span :class="getStockClass(detailData)">{{ detailData.stockQty?.toLocaleString() }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="入庫予定">{{ detailData.pendingQty?.toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="状況">
          <el-tag :type="getStockStatusType(detailData)" size="small">{{ getStockStatusLabel(detailData) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最終入庫日">{{ detailData.lastReceiveDate }}</el-descriptions-item>
        <el-descriptions-item label="最終出庫日">{{ detailData.lastIssueDate || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 履歴对话框 -->
    <el-dialog v-model="historyVisible" :title="historyTitle" width="820px" class="history-dialog">
      <el-table :data="historyData" border stripe size="small">
        <el-table-column prop="date" label="日付" width="100" />
        <el-table-column prop="type" label="種別" width="72" align="center">
          <template #default="{ row }">
            <el-tag :type="row.type === 'receive' ? 'success' : 'warning'" size="small" effect="light">
              {{ row.type === 'receive' ? '入庫' : '出庫' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="orderNo" label="関連番号" width="130" />
        <el-table-column prop="quantity" label="数量" width="90" align="right">
          <template #default="{ row }">
            <span :class="row.type === 'receive' ? 'text-success' : 'text-warning'">
              {{ row.type === 'receive' ? '+' : '-' }}{{ row.quantity.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="stockAfter" label="在庫残" width="90" align="right">
          <template #default="{ row }">{{ row.stockAfter.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="operator" label="担当者" width="80" />
        <el-table-column prop="remarks" label="備考" min-width="140" show-overflow-tooltip />
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
/* ===== 页面容器 ===== */
.outsourcing-stock-page {
  padding: 10px 12px;
  background: #f0f2f5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ===== 顶部 Header ===== */
.page-header {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 60%, #4facfe 100%);
  border-radius: 10px;
  padding: 12px 18px;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 12px rgba(30, 60, 114, 0.25);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.subtitle {
  margin: 1px 0 0;
  font-size: 11px;
  opacity: 0.85;
}

.header-kpis {
  display: flex;
  gap: 8px;
}

.kpi {
  text-align: center;
  padding: 6px 12px;
  border-radius: 8px;
  min-width: 62px;
}

.kpi-teal {
  background: rgba(78, 205, 196, 0.22);
  border: 1px solid rgba(78, 205, 196, 0.35);
}

.kpi-purple {
  background: rgba(167, 119, 227, 0.22);
  border: 1px solid rgba(167, 119, 227, 0.35);
}

.kpi-blue {
  background: rgba(255, 255, 255, 0.18);
}

.kpi-amber {
  background: rgba(255, 193, 7, 0.25);
  border: 1px solid rgba(255, 193, 7, 0.4);
}

.kpi-val {
  display: block;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.2;
}

.kpi-lbl {
  font-size: 10px;
  opacity: 0.9;
}

/* ===== 工具条 ===== */
.toolbar-strip {
  background: #fff;
  border-radius: 10px;
  padding: 0 14px 10px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
}

.strip-tabs :deep(.el-tabs__header) {
  margin-bottom: 8px;
}

.strip-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}

.strip-tabs :deep(.el-tabs__item) {
  height: 38px;
  line-height: 38px;
  font-size: 13px;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.tab-badge {
  margin-left: 2px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-row :deep(.el-divider--vertical) {
  height: 20px;
  margin: 0 2px;
}

/* ===== 概要指标条 ===== */
.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.sm-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
  transition: transform 0.15s, box-shadow 0.15s;
}

.sm-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
}

.sm-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 17px;
  flex-shrink: 0;
}

.sm-blue .sm-icon {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
}

.sm-green .sm-icon {
  background: linear-gradient(135deg, #34d399, #10b981);
}

.sm-orange .sm-icon {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.sm-violet .sm-icon {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.sm-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sm-val {
  font-size: 17px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.sm-lbl {
  font-size: 10.5px;
  color: #9ca3af;
}

/* ===== 表格 ===== */
.table-wrap {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.data-table {
  flex: 1;
}

.data-table :deep(.warning-row) {
  background-color: #fffbeb !important;
}

.data-table :deep(.empty-row) {
  background-color: #fef2f2 !important;
}

.data-table :deep(.el-table__header th) {
  font-size: 12px;
}

.stock-normal {
  color: #16a34a;
  font-weight: 600;
}

.stock-low {
  color: #d97706;
  font-weight: 600;
}

.stock-empty {
  color: #dc2626;
  font-weight: 600;
}

.pending-qty {
  color: #2563eb;
  font-weight: 500;
}

.pagination-wrapper {
  padding: 8px 14px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #f0f0f0;
}

/* ===== 辅助文字 ===== */
.text-success {
  color: #16a34a;
  font-weight: 600;
}

.text-warning {
  color: #d97706;
  font-weight: 600;
}

/* ===== 对话框微调 ===== */
.detail-dialog :deep(.el-dialog__body) {
  padding: 14px 20px;
}

.history-dialog :deep(.el-dialog__body) {
  padding: 10px 20px;
}

/* ===== 响应式 ===== */
@media (max-width: 1200px) {
  .summary-strip {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .outsourcing-stock-page {
    padding: 8px;
    gap: 6px;
  }

  .page-header {
    flex-direction: column;
    gap: 8px;
    padding: 10px 14px;
    align-items: flex-start;
  }

  .header-kpis {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
  }

  .kpi {
    padding: 4px 8px;
    min-width: unset;
  }

  .kpi-val {
    font-size: 15px;
  }

  .title {
    font-size: 15px;
  }

  .title-icon {
    width: 30px;
    height: 30px;
    font-size: 15px;
  }

  .summary-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .filter-row {
    gap: 6px;
  }

  .filter-row .el-select,
  .filter-row .el-input {
    width: 100% !important;
  }

  .sm-val {
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  .summary-strip {
    grid-template-columns: 1fr;
  }

  .header-kpis {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
