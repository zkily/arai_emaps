<template>
  <div class="outsourcing-stock-page osk-modern pb-std">
    <!-- 页面头部：标题 + 统计指标 -->
    <div class="page-header pb-hero pb-hero--page">
      <div class="head-fx pb-bubbles" aria-hidden="true" />
      <div class="header-left">
        <div class="title-icon"><el-icon><Box /></el-icon></div>
        <div class="title-text">
          <h2 class="title pb-hero-title">外注在庫管理</h2>
          <p class="subtitle pb-hero-desc">
            外注溶接品の在庫を外注先・品番・在庫状況で絞り込み、入出庫履歴を確認
          </p>
        </div>
      </div>
      <div class="header-kpis">
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
        <el-button
          type="primary"
          class="tb-btn tb-search"
          @click="handleSearch"
          :loading="loading"
          size="default"
        >
          <el-icon><Search /></el-icon>検索
        </el-button>
        <el-divider direction="vertical" />
        <el-button class="tb-btn tb-refresh" @click="refreshStock" size="default">
          <el-icon><Refresh /></el-icon>更新
        </el-button>
        <el-button class="tb-btn tb-excel" @click="exportData" size="default">
          <el-icon><Download /></el-icon>Excel
        </el-button>
        <el-button class="tb-btn tb-history" @click="viewStockHistory" size="default">
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
    <el-dialog
      v-model="detailVisible"
      title="在庫詳細"
      width="640px"
      class="detail-dialog osk-dialog pb-std"
      :show-close="false"
    >
      <template #header>
        <div class="osk-dlg-hero pb-hero">
          <div class="head-fx pb-bubbles" aria-hidden="true" />
          <span class="osk-dlg-hero__icon"><el-icon><Box /></el-icon></span>
          <div class="osk-dlg-hero__copy">
            <span class="osk-dlg-hero__title">在庫詳細</span>
            <p class="osk-dlg-hero__desc">
              {{ detailData.productCode }} {{ detailData.productName }}
            </p>
          </div>
          <el-icon class="osk-dlg-hero__close" @click="detailVisible = false"><Close /></el-icon>
        </div>
      </template>
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
    <el-dialog
      v-model="historyVisible"
      :title="historyTitle"
      width="820px"
      class="history-dialog osk-dialog pb-std"
      :show-close="false"
    >
      <template #header>
        <div class="osk-dlg-hero osk-dlg-hero--history pb-hero">
          <div class="head-fx pb-bubbles" aria-hidden="true" />
          <span class="osk-dlg-hero__icon"><el-icon><Document /></el-icon></span>
          <div class="osk-dlg-hero__copy">
            <span class="osk-dlg-hero__title">{{ historyTitle }}</span>
            <p class="osk-dlg-hero__desc">入庫・出庫の推移と在庫残を確認</p>
          </div>
          <el-icon class="osk-dlg-hero__close" @click="historyVisible = false"><Close /></el-icon>
        </div>
      </template>
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
  Close,
} from '@element-plus/icons-vue'
import {
  getPlatingStock,
  getWeldingStock,
  getOutsourcingStockHistory,
  getSuppliers,
  type OutsourcingSupplier,
} from '@/api/outsourcing'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = usePurchaseOperationPermission()


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
const activeTab = ref('welding')
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
  if (!guardPurchaseOperation(canEdit)) return

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
  min-height: 100vh;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eaf2ff 0%, #f8fafc 32%, #f8fafc 100%);
}

/* ============================================================ */
/* 页面美化：现代 UI / 颜色区分（外注在庫＝ネイビー〜スカイ系）      */
/* ============================================================ */

/* ===== ヒーロー ===== */
.page-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(125deg, #1e3c72 0%, #2a5298 45%, #3b82f6 75%, #4facfe 100%);
  box-shadow:
    0 12px 28px -18px rgba(42, 82, 152, 0.7),
    0 1px 2px rgba(15, 23, 42, 0.06);
}

.header-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 20px;
  color: #fff;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 35, 80, 0.3);
}

.title-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
}

.subtitle {
  margin: 0;
  letter-spacing: 0.02em;
  color: rgba(255, 255, 255, 0.86);
}

/* KPI：濃色ヒーロー上の白カード（数字色で区別） */
.header-kpis {
  display: flex;
  gap: 6px;
}

.kpi {
  --kc: #1d4ed8;
  min-width: 64px;
  padding: 5px 12px;
  text-align: center;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #eef5ff 100%);
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -2px 0 rgba(148, 163, 184, 0.25),
    0 6px 14px -10px rgba(15, 23, 42, 0.45);
}

.kpi-teal {
  --kc: #0f766e;
}

.kpi-purple {
  --kc: #6d28d9;
}

.kpi-blue {
  --kc: #1d4ed8;
}

.kpi-amber {
  --kc: #b45309;
  background: linear-gradient(180deg, #ffffff 0%, #fffbeb 100%);
}

.kpi-val {
  display: block;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.15;
  color: var(--kc);
  font-variant-numeric: tabular-nums;
}

.kpi-lbl {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
}

/* ===== ツールバー（タブ＋絞り込み） ===== */
.toolbar-strip {
  position: relative;
  overflow: hidden;
  padding: 10px 14px 10px;
  border-radius: 12px;
  border: 1px solid #dbe7fb;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(30, 64, 175, 0.45);
}

.toolbar-strip::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #2a5298 0%, #3b82f6 55%, #4facfe 100%);
}

.strip-tabs :deep(.el-tabs__header) {
  margin: 2px 0 10px;
}

.strip-tabs :deep(.el-tabs__nav-wrap::after),
.strip-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.strip-tabs :deep(.el-tabs__nav) {
  gap: 4px;
  padding: 3px;
  border-radius: 10px;
  background: #eaf1fd;
  box-shadow: inset 0 1px 2px rgba(30, 64, 175, 0.08);
}

.strip-tabs :deep(.el-tabs__item) {
  height: 32px;
  padding: 0 16px !important;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  line-height: 32px;
  color: #475f8a;
  transition:
    background-color 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease;
}

.strip-tabs :deep(.el-tabs__item:hover) {
  color: #1d4ed8;
}

.strip-tabs :deep(.el-tabs__item.is-active) {
  color: #1e3a8a;
  background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -2px 0 #c7d8f7,
    0 2px 6px -2px rgba(30, 64, 175, 0.3);
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.tab-badge {
  margin-left: 2px;
}

.tab-badge :deep(.el-badge__content) {
  height: 18px;
  padding: 0 6px;
  border: none;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 700;
  line-height: 18px;
  color: #1d4ed8;
  background: #dbeafe;
}

.strip-tabs :deep(.el-tabs__item.is-active) .tab-badge :deep(.el-badge__content) {
  color: #fff;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filter-row :deep(.el-divider--vertical) {
  height: 20px;
  margin: 0 2px;
  border-color: #dbe7fb;
}

/* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
.filter-row :deep(.el-input__wrapper),
.filter-row :deep(.el-select__wrapper) {
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 0 0 1px #d3def3 inset;
}

.filter-row :deep(.el-input__wrapper:hover),
.filter-row :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #93b4ec inset;
}

.filter-row :deep(.el-input__wrapper.is-focus),
.filter-row :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #2563eb inset,
    0 0 0 3px rgba(37, 99, 235, 0.14);
}

/* ツールバーボタン（色で役割を区別） */
.tb-btn {
  height: 32px;
  margin: 0;
  padding: 0 14px;
  border-radius: 8px;
  font-weight: 700;
}

.tb-btn .el-icon {
  margin-right: 4px;
}

.tb-search {
  --k-rgb: 37 99 235;
  color: #fff;
  border: 1px solid #1d4ed8;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #3b82f6, #1d4ed8);
}

.tb-search:hover,
.tb-search:focus-visible {
  color: #fff;
  border-color: #1e40af;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #5b96f7, #2563eb);
}

.tb-refresh,
.tb-excel,
.tb-history {
  --tb-fg: #0369a1;
  --tb-bd: #bae6fd;
  --tb-bg: #f0f9ff;
  --tb-hv: #7dd3fc;
  color: var(--tb-fg);
  border: 1px solid var(--tb-bd);
  background: linear-gradient(180deg, #ffffff 0%, var(--tb-bg) 100%);
}

.tb-refresh:hover,
.tb-excel:hover,
.tb-history:hover,
.tb-refresh:focus-visible,
.tb-excel:focus-visible,
.tb-history:focus-visible {
  color: var(--tb-fg);
  border-color: var(--tb-hv);
  background: #fff;
}

.tb-refresh {
  --k-rgb: 2 132 199;
}

.tb-excel {
  --k-rgb: 5 150 105;
  --tb-fg: #047857;
  --tb-bd: #a7f3d0;
  --tb-bg: #ecfdf5;
  --tb-hv: #34d399;
}

.tb-history {
  --k-rgb: 100 116 139;
  --tb-fg: #475569;
  --tb-bd: #cbd5e1;
  --tb-bg: #f1f5f9;
  --tb-hv: #94a3b8;
}

.tb-btn.is-disabled,
.tb-btn.is-disabled:hover {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ===== 概要指標（色分け・動きなし） ===== */
.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.sm-card {
  --accent: #2563eb;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--accent) 18%, #e2e8f0);
  background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 7%, #fff) 0%, #fff 70%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 18px -16px color-mix(in srgb, var(--accent) 70%, transparent);
}

.sm-card::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 45%, #fff), var(--accent));
}

.sm-blue {
  --accent: #2a5298;
}

.sm-green {
  --accent: #059669;
}

.sm-orange {
  --accent: #d97706;
}

.sm-violet {
  --accent: #7c3aed;
}

.sm-icon {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  padding: 8px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 17px;
  color: #fff;
  background: linear-gradient(
    150deg,
    color-mix(in srgb, var(--accent) 70%, #fff) 0%,
    var(--accent) 100%
  );
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 color-mix(in srgb, var(--accent) 60%, #000 20%);
}

.sm-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.sm-val {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
  color: color-mix(in srgb, var(--accent) 70%, #0f172a);
  font-variant-numeric: tabular-nums;
}

.sm-lbl {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

/* ===== テーブル ===== */
.table-wrap {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #dbe7fb;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(30, 64, 175, 0.4);
}

.table-wrap::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 5;
  height: 3px;
  background: linear-gradient(90deg, #2a5298 0%, #3b82f6 55%, #4facfe 100%);
}

.data-table {
  flex: 1;
  --el-table-border-color: #e8eef9;
  --el-table-row-hover-bg-color: #eef4ff;
  --el-table-current-row-bg-color: #e0ecff;
}

.data-table :deep(th.el-table__cell) {
  font-size: 12px !important;
  font-weight: 700 !important;
  color: #1e3a8a !important;
  background: #f1f6ff !important;
  border-bottom: 1px solid #d6e2f7 !important;
}

.data-table :deep(td.el-table__cell) {
  color: #1e293b;
  border-bottom-color: #f0f4fb;
}

.data-table :deep(.el-table__row--striped td.el-table__cell) {
  background: #fafcff;
}

.data-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #eef4ff !important;
}

.data-table :deep(.warning-row) {
  background-color: #fffbeb !important;
}

.data-table :deep(.empty-row) {
  background-color: #fef2f2 !important;
}

.data-table :deep(.warning-row > td.el-table__cell) {
  background-color: #fffbeb !important;
}

.data-table :deep(.empty-row > td.el-table__cell) {
  background-color: #fef2f2 !important;
}

.data-table :deep(.el-tag) {
  border-radius: 999px;
  font-weight: 700;
}

.data-table :deep(.el-link) {
  font-weight: 700;
}

.stock-normal {
  font-weight: 700;
  color: #16a34a;
}

.stock-low {
  font-weight: 700;
  color: #d97706;
}

.stock-empty {
  font-weight: 700;
  color: #dc2626;
}

.pending-qty {
  font-weight: 600;
  color: #2563eb;
}

/* ===== ページャー ===== */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 8px 14px;
  border-top: 1px solid #e8eef9;
  background: linear-gradient(180deg, #fafcff 0%, #f3f7ff 100%);
}

.pagination-wrapper :deep(.el-pagination__total) {
  font-weight: 700;
  color: #1e3a8a;
}

.pagination-wrapper :deep(.el-pager li),
.pagination-wrapper :deep(.btn-prev),
.pagination-wrapper :deep(.btn-next) {
  min-width: 26px;
  height: 26px;
  margin: 0 2px;
  border-radius: 7px;
  color: #1d4ed8;
  border: 1px solid #dbe7fb;
  background: linear-gradient(180deg, #ffffff 0%, #f5f9ff 100%);
}

.pagination-wrapper :deep(.el-pager li:not(.is-active):hover) {
  border-color: #93b4ec;
  background: #fff;
}

.pagination-wrapper :deep(.el-pager li.is-active) {
  color: #fff;
  border-color: #1d4ed8;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #3b82f6, #1d4ed8);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(30, 58, 138, 0.35),
    0 4px 10px -6px rgba(37, 99, 235, 0.7);
}

.pagination-wrapper :deep(.btn-prev:disabled),
.pagination-wrapper :deep(.btn-next:disabled) {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ===== 辅助文字 ===== */
.text-success {
  font-weight: 700;
  color: #16a34a;
}

.text-warning {
  font-weight: 700;
  color: #d97706;
}

/* ===== ダイアログ ===== */
.osk-dlg-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(125deg, #1e3c72 0%, #2a5298 45%, #3b82f6 75%, #4facfe 100%);
}

.osk-dlg-hero--history {
  background: linear-gradient(125deg, #0f766e 0%, #0d9488 45%, #0ea5e9 100%);
}

.osk-dlg-hero__icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  font-size: 18px;
  color: #fff;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 35, 80, 0.3);
}

.osk-dlg-hero__copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.osk-dlg-hero__title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
  color: #fff;
}

.osk-dlg-hero__desc {
  margin: 0;
  overflow: hidden;
  font-size: 11px;
  line-height: 1.5;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.86);
}

.osk-dlg-hero__close {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  padding: 6px;
  box-sizing: border-box;
  border-radius: 9px;
  font-size: 18px;
  color: #fff;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition:
    transform 0.2s ease,
    background 0.2s ease;
}

.osk-dlg-hero__close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

:global(.el-dialog.osk-dialog) {
  padding: 0;
  overflow: hidden;
  border-radius: 14px;
}

:global(.el-dialog.osk-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
}

:global(.el-dialog.osk-dialog .el-dialog__body) {
  padding: 14px 18px 18px;
}

:global(.el-dialog.osk-dialog .el-descriptions__label) {
  font-weight: 700;
  color: #1e3a8a;
  background: #f1f6ff;
}

:global(.el-dialog.osk-dialog .el-table th.el-table__cell) {
  font-weight: 700;
  color: #134e4a;
  background: #effcf9;
}

/* ===== 响应式 ===== */
@media (max-width: 1200px) {
  .summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .outsourcing-stock-page {
    padding: 8px;
    gap: 6px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .header-kpis {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
  }

  .kpi {
    min-width: unset;
    padding: 4px 8px;
  }

  .summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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
