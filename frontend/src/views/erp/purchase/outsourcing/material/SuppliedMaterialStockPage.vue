<template>
  <div class="supplied-material-stock-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2 class="title">
            <div class="title-icon">
              <el-icon><Box /></el-icon>
            </div>
            <span class="title-text">支給材料在庫管理</span>
          </h2>
          <p class="subtitle">外注先に支給した材料の在庫状況を管理します</p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-value">{{ supplierCount }}</span>
            <span class="stat-label">外注先</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ materialCount }}</span>
            <span class="stat-label">材料種</span>
          </div>
          <div class="stat-item warning">
            <span class="stat-value">{{ lowStockCount }}</span>
            <span class="stat-label">在庫僅少</span>
          </div>
        </div>
      </div>
    </div>

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
          <el-select v-model="filters.supplier" placeholder="選択" clearable filterable style="width: 180px">
            <el-option v-for="s in supplierOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="材料">
          <el-input v-model="filters.materialCode" placeholder="材料コード" clearable style="width: 130px" />
        </el-form-item>
        <el-form-item label="在庫状況">
          <el-select v-model="filters.stockStatus" placeholder="選択" clearable style="width: 120px">
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
      </div>
      <div class="right-actions">
        <el-tag type="warning" size="large" class="alert-tag" v-if="lowStockCount > 0">
          <el-icon><Warning /></el-icon>
          {{ lowStockCount }}件の在庫が僅少です
        </el-tag>
      </div>
    </div>

    <!-- 外注先別在庫カード -->
    <div class="supplier-cards">
      <el-card 
        v-for="supplier in filteredSuppliers" 
        :key="supplier.id" 
        class="supplier-card"
        :class="{ 'has-warning': supplier.lowStockItems > 0 }"
      >
        <template #header>
          <div class="supplier-header">
            <div class="supplier-info">
              <el-icon class="supplier-icon"><OfficeBuilding /></el-icon>
              <span class="supplier-name">{{ supplier.name }}</span>
            </div>
            <div class="supplier-badges">
              <el-tag type="primary" size="small">{{ supplier.totalItems }}種</el-tag>
              <el-tag v-if="supplier.lowStockItems > 0" type="warning" size="small">
                <el-icon><Warning /></el-icon>{{ supplier.lowStockItems }}
              </el-tag>
            </div>
          </div>
        </template>
        <el-table 
          :data="supplier.materials" 
          size="small" 
          border
          :row-class-name="getRowClassName"
        >
          <el-table-column prop="materialCode" label="材料コード" width="110" />
          <el-table-column prop="materialName" label="材料名" min-width="120" show-overflow-tooltip />
          <el-table-column prop="spec" label="規格" width="100" />
          <el-table-column prop="issuedQty" label="支給累計" width="90" align="right">
            <template #default="{ row }">
              {{ row.issuedQty.toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="usedQty" label="使用累計" width="90" align="right">
            <template #default="{ row }">
              {{ row.usedQty.toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="stockQty" label="現在庫" width="90" align="right">
            <template #default="{ row }">
              <span :class="getStockClass(row)">{{ row.stockQty.toLocaleString() }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="unit" label="単位" width="50" align="center" />
          <el-table-column label="状況" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="getStockStatusType(row)" size="small">
                {{ getStockStatusLabel(row) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <el-button type="primary" size="small" link @click="viewHistory(supplier, row)">
                <el-icon><View /></el-icon>履歴
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="supplier-footer">
          <span class="footer-item">
            <el-icon><Upload /></el-icon>
            総支給重量: {{ supplier.totalIssuedWeight.toLocaleString() }} kg
          </span>
          <span class="footer-item">
            <el-icon><Box /></el-icon>
            現在庫重量: {{ supplier.currentStockWeight.toLocaleString() }} kg
          </span>
        </div>
      </el-card>
    </div>

    <!-- 履歴对话框 -->
    <el-dialog v-model="historyVisible" :title="historyTitle" width="800px">
      <el-table :data="historyData" border stripe>
        <el-table-column prop="date" label="日付" width="100" />
        <el-table-column prop="type" label="種別" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.type === 'issue' ? 'success' : 'warning'" size="small">
              {{ row.type === 'issue' ? '支給' : '使用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="orderNo" label="関連注文" width="130" />
        <el-table-column prop="quantity" label="数量" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.type === 'issue' ? 'text-success' : 'text-warning'">
              {{ row.type === 'issue' ? '+' : '-' }}{{ row.quantity.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="stockAfter" label="在庫残" width="100" align="right">
          <template #default="{ row }">
            {{ row.stockAfter.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="担当者" width="80" />
        <el-table-column prop="remarks" label="備考" min-width="120" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search, Refresh, Download, Box, OfficeBuilding, Warning, Upload, View
} from '@element-plus/icons-vue'

interface MaterialStock {
  materialCode: string
  materialName: string
  spec: string
  issuedQty: number
  usedQty: number
  stockQty: number
  unit: string
  minStock: number
}

interface SupplierStock {
  id: number
  name: string
  totalItems: number
  lowStockItems: number
  totalIssuedWeight: number
  currentStockWeight: number
  materials: MaterialStock[]
}

interface HistoryItem {
  date: string
  type: 'issue' | 'usage'
  orderNo: string
  quantity: number
  stockAfter: number
  operator: string
  remarks: string
}

const loading = ref(false)
const historyVisible = ref(false)
const historyTitle = ref('')
const historyData = ref<HistoryItem[]>([])

const filters = reactive({
  supplier: '',
  materialCode: '',
  stockStatus: ''
})

const supplierOptions = ref([
  { value: 1, label: '山田メッキ工業' },
  { value: 2, label: '高橋溶接工業' },
  { value: 3, label: '佐藤表面処理' },
  { value: 4, label: '渡辺精密溶接' },
])

const supplierStocks = ref<SupplierStock[]>([
  {
    id: 1,
    name: '山田メッキ工業',
    totalItems: 3,
    lowStockItems: 1,
    totalIssuedWeight: 1250,
    currentStockWeight: 320,
    materials: [
      { materialCode: 'M-001', materialName: 'SUS304丸棒', spec: 'φ10x1000', issuedQty: 500, usedQty: 420, stockQty: 80, unit: '本', minStock: 100 },
      { materialCode: 'M-002', materialName: 'SUS304板材', spec: 't2.0x1000x2000', issuedQty: 100, usedQty: 65, stockQty: 35, unit: '枚', minStock: 20 },
      { materialCode: 'M-003', materialName: 'SUS316角パイプ', spec: '30x30x2.0', issuedQty: 200, usedQty: 180, stockQty: 20, unit: '本', minStock: 50 },
    ]
  },
  {
    id: 2,
    name: '高橋溶接工業',
    totalItems: 2,
    lowStockItems: 0,
    totalIssuedWeight: 5800,
    currentStockWeight: 1520,
    materials: [
      { materialCode: 'M-004', materialName: 'SS400板材', spec: 't3.2x1219x2438', issuedQty: 150, usedQty: 100, stockQty: 50, unit: '枚', minStock: 30 },
      { materialCode: 'M-005', materialName: 'SPHC-P', spec: 't1.6x1219x2438', issuedQty: 80, usedQty: 40, stockQty: 40, unit: '枚', minStock: 20 },
    ]
  },
  {
    id: 3,
    name: '佐藤表面処理',
    totalItems: 2,
    lowStockItems: 1,
    totalIssuedWeight: 890,
    currentStockWeight: 180,
    materials: [
      { materialCode: 'M-006', materialName: 'A5052アルミ板', spec: 't3.0x1000x2000', issuedQty: 60, usedQty: 55, stockQty: 5, unit: '枚', minStock: 15 },
      { materialCode: 'M-007', materialName: 'C1100銅板', spec: 't1.0x365x1200', issuedQty: 30, usedQty: 10, stockQty: 20, unit: '枚', minStock: 10 },
    ]
  },
])

const supplierCount = computed(() => supplierStocks.value.length)
const materialCount = computed(() => supplierStocks.value.reduce((sum, s) => sum + s.totalItems, 0))
const lowStockCount = computed(() => supplierStocks.value.reduce((sum, s) => sum + s.lowStockItems, 0))

const filteredSuppliers = computed(() => {
  let result = supplierStocks.value
  if (filters.supplier) {
    result = result.filter(s => s.id === filters.supplier)
  }
  if (filters.stockStatus) {
    result = result.map(s => ({
      ...s,
      materials: s.materials.filter(m => {
        if (filters.stockStatus === 'low') return m.stockQty > 0 && m.stockQty < m.minStock
        if (filters.stockStatus === 'empty') return m.stockQty === 0
        if (filters.stockStatus === 'normal') return m.stockQty >= m.minStock
        return true
      })
    })).filter(s => s.materials.length > 0)
  }
  return result
})

const getRowClassName = ({ row }: { row: MaterialStock }) => {
  if (row.stockQty === 0) return 'empty-row'
  if (row.stockQty < row.minStock) return 'warning-row'
  return ''
}

const getStockClass = (row: MaterialStock) => {
  if (row.stockQty === 0) return 'stock-empty'
  if (row.stockQty < row.minStock) return 'stock-low'
  return 'stock-normal'
}

const getStockStatusType = (row: MaterialStock) => {
  if (row.stockQty === 0) return 'danger'
  if (row.stockQty < row.minStock) return 'warning'
  return 'success'
}

const getStockStatusLabel = (row: MaterialStock) => {
  if (row.stockQty === 0) return 'なし'
  if (row.stockQty < row.minStock) return '僅少'
  return '正常'
}

const handleSearch = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, { supplier: '', materialCode: '', stockStatus: '' })
  handleSearch()
}

const viewHistory = (supplier: SupplierStock, material: MaterialStock) => {
  historyTitle.value = `${supplier.name} - ${material.materialCode} 履歴`
  historyData.value = [
    { date: '2025-12-03', type: 'issue', orderNo: 'MI-2025-001', quantity: 100, stockAfter: 80, operator: '田中', remarks: '' },
    { date: '2025-12-02', type: 'usage', orderNo: 'PO-2025-001', quantity: 50, stockAfter: -20, operator: '-', remarks: '納品完了' },
    { date: '2025-12-01', type: 'issue', orderNo: 'MI-2025-000', quantity: 200, stockAfter: 30, operator: '鈴木', remarks: '' },
    { date: '2025-11-28', type: 'usage', orderNo: 'PO-2025-000', quantity: 170, stockAfter: -170, operator: '-', remarks: '' },
  ]
  historyVisible.value = true
}

const refreshStock = () => {
  ElMessage.info('在庫情報を更新しています...')
  handleSearch()
}

const exportData = () => {
  ElMessage.info('Excel出力機能は準備中です')
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.supplied-material-stock-page {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
  color: white;
  box-shadow: 0 4px 20px rgba(67, 233, 123, 0.3);
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
  min-width: 65px;
}

.stat-item.warning {
  background: rgba(255, 152, 0, 0.3);
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
  color: #43e97b;
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

.supplier-cards {
  display: grid;
  gap: 16px;
}

.supplier-card {
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.supplier-card.has-warning {
  border-left: 3px solid #e6a23c;
}

.supplier-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.supplier-card :deep(.el-card__header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.supplier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.supplier-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.supplier-icon {
  font-size: 20px;
  color: #43e97b;
}

.supplier-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.supplier-badges {
  display: flex;
  gap: 8px;
}

.supplier-card :deep(.el-card__body) {
  padding: 0;
}

.supplier-card :deep(.warning-row) {
  background-color: #fef9e7;
}

.supplier-card :deep(.empty-row) {
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

.supplier-footer {
  padding: 12px 16px;
  background: #f8f9fa;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
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
  .supplied-material-stock-page {
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
  .supplier-footer {
    flex-direction: column;
    gap: 8px;
  }
}
</style>

