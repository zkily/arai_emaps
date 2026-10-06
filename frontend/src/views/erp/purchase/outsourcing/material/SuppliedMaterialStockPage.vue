<template>
  <div class="supplied-material-stock-page sms-modern pb-std">
    <!-- 页面头部 -->
    <div class="page-header pb-hero pb-hero--page">
      <div class="head-fx pb-bubbles" aria-hidden="true" />
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div class="title-copy">
            <h2 class="title pb-hero-title">支給材料在庫管理</h2>
            <p class="subtitle pb-hero-desc">
              外注先に支給した材料の在庫を外注先別に確認し、僅少在庫と支給・使用履歴をチェック
            </p>
          </div>
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
          <el-select
            v-model="filters.supplier"
            placeholder="選択"
            clearable
            filterable
            style="width: 180px"
          >
            <el-option
              v-for="s in supplierOptions"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="材料">
          <el-input
            v-model="filters.materialCode"
            placeholder="材料コード"
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
          <el-button
            type="primary"
            class="sms-btn sms-btn--search"
            @click="handleSearch"
            :loading="loading"
          >
            <el-icon><Search /></el-icon>
            検索
          </el-button>
          <el-button class="sms-btn sms-btn--reset" @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            リセット
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作按钮栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="warning" class="sms-btn sms-btn--excel" @click="exportData">
          <el-icon><Download /></el-icon>
          Excel出力
        </el-button>
        <el-button type="info" class="sms-btn sms-btn--refresh" @click="refreshStock">
          <el-icon><Refresh /></el-icon>
          在庫更新
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
                <el-icon><Warning /></el-icon>
                {{ supplier.lowStockItems }}
              </el-tag>
            </div>
          </div>
        </template>
        <el-table :data="supplier.materials" size="small" border :row-class-name="getRowClassName">
          <el-table-column prop="materialCode" label="材料コード" width="110" />
          <el-table-column
            prop="materialName"
            label="材料名"
            min-width="120"
            show-overflow-tooltip
          />
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
                <el-icon><View /></el-icon>
                履歴
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
    <el-dialog
      v-model="historyVisible"
      :title="historyTitle"
      width="800px"
      class="sms-dialog pb-std"
      :show-close="false"
    >
      <template #header>
        <div class="sms-dlg-hero pb-hero">
          <div class="head-fx pb-bubbles" aria-hidden="true" />
          <span class="sms-dlg-hero__icon"><el-icon><View /></el-icon></span>
          <div class="sms-dlg-hero__copy">
            <span class="sms-dlg-hero__title">{{ historyTitle }}</span>
            <p class="sms-dlg-hero__desc">支給・使用の推移と在庫残を確認</p>
          </div>
          <el-icon class="sms-dlg-hero__close" @click="historyVisible = false"><Close /></el-icon>
        </div>
      </template>
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
  Search,
  Refresh,
  Download,
  Box,
  OfficeBuilding,
  Warning,
  Upload,
  View,
  Close,
} from '@element-plus/icons-vue'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = usePurchaseOperationPermission()


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
  stockStatus: '',
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
      {
        materialCode: 'M-001',
        materialName: 'SUS304丸棒',
        spec: 'φ10x1000',
        issuedQty: 500,
        usedQty: 420,
        stockQty: 80,
        unit: '本',
        minStock: 100,
      },
      {
        materialCode: 'M-002',
        materialName: 'SUS304板材',
        spec: 't2.0x1000x2000',
        issuedQty: 100,
        usedQty: 65,
        stockQty: 35,
        unit: '枚',
        minStock: 20,
      },
      {
        materialCode: 'M-003',
        materialName: 'SUS316角パイプ',
        spec: '30x30x2.0',
        issuedQty: 200,
        usedQty: 180,
        stockQty: 20,
        unit: '本',
        minStock: 50,
      },
    ],
  },
  {
    id: 2,
    name: '高橋溶接工業',
    totalItems: 2,
    lowStockItems: 0,
    totalIssuedWeight: 5800,
    currentStockWeight: 1520,
    materials: [
      {
        materialCode: 'M-004',
        materialName: 'SS400板材',
        spec: 't3.2x1219x2438',
        issuedQty: 150,
        usedQty: 100,
        stockQty: 50,
        unit: '枚',
        minStock: 30,
      },
      {
        materialCode: 'M-005',
        materialName: 'SPHC-P',
        spec: 't1.6x1219x2438',
        issuedQty: 80,
        usedQty: 40,
        stockQty: 40,
        unit: '枚',
        minStock: 20,
      },
    ],
  },
  {
    id: 3,
    name: '佐藤表面処理',
    totalItems: 2,
    lowStockItems: 1,
    totalIssuedWeight: 890,
    currentStockWeight: 180,
    materials: [
      {
        materialCode: 'M-006',
        materialName: 'A5052アルミ板',
        spec: 't3.0x1000x2000',
        issuedQty: 60,
        usedQty: 55,
        stockQty: 5,
        unit: '枚',
        minStock: 15,
      },
      {
        materialCode: 'M-007',
        materialName: 'C1100銅板',
        spec: 't1.0x365x1200',
        issuedQty: 30,
        usedQty: 10,
        stockQty: 20,
        unit: '枚',
        minStock: 10,
      },
    ],
  },
])

const supplierCount = computed(() => supplierStocks.value.length)
const materialCount = computed(() => supplierStocks.value.reduce((sum, s) => sum + s.totalItems, 0))
const lowStockCount = computed(() =>
  supplierStocks.value.reduce((sum, s) => sum + s.lowStockItems, 0),
)

const filteredSuppliers = computed(() => {
  let result = supplierStocks.value
  if (filters.supplier !== '' && filters.supplier != null) {
    result = result.filter((s) => String(s.id) === String(filters.supplier))
  }
  if (filters.stockStatus) {
    result = result
      .map((s) => ({
        ...s,
        materials: s.materials.filter((m) => {
          if (filters.stockStatus === 'low') return m.stockQty > 0 && m.stockQty < m.minStock
          if (filters.stockStatus === 'empty') return m.stockQty === 0
          if (filters.stockStatus === 'normal') return m.stockQty >= m.minStock
          return true
        }),
      }))
      .filter((s) => s.materials.length > 0)
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
  if (!guardPurchaseOperation(canEdit)) return

  loading.value = true
  try {
    await new Promise((resolve) => setTimeout(resolve, 500))
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
    {
      date: '2025-12-03',
      type: 'issue',
      orderNo: 'MI-2025-001',
      quantity: 100,
      stockAfter: 80,
      operator: '田中',
      remarks: '',
    },
    {
      date: '2025-12-02',
      type: 'usage',
      orderNo: 'PO-2025-001',
      quantity: 50,
      stockAfter: -20,
      operator: '-',
      remarks: '納品完了',
    },
    {
      date: '2025-12-01',
      type: 'issue',
      orderNo: 'MI-2025-000',
      quantity: 200,
      stockAfter: 30,
      operator: '鈴木',
      remarks: '',
    },
    {
      date: '2025-11-28',
      type: 'usage',
      orderNo: 'PO-2025-000',
      quantity: 170,
      stockAfter: -170,
      operator: '-',
      remarks: '',
    },
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
  min-height: 100vh;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-sizing: border-box;
  background: linear-gradient(180deg, #e9faf3 0%, #f8fafc 32%, #f8fafc 100%);
}

/* ============================================================ */
/* 页面美化：现代 UI / 颜色区分（支給材料＝エメラルド〜ティール系）  */
/* ============================================================ */

/* ---------- ヒーロー ---------- */
.page-header {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(125deg, #047857 0%, #059669 38%, #10b981 68%, #14b8a6 100%);
  box-shadow:
    0 12px 28px -18px rgba(5, 150, 105, 0.7),
    0 1px 2px rgba(15, 23, 42, 0.06);
}

.header-content {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
}

.title-section {
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
    inset 0 -2px 0 rgba(6, 78, 59, 0.3);
}

.title-copy {
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
  color: rgba(255, 255, 255, 0.88);
}

/* 統計：濃色ヒーロー上の白カード（数字色で区別） */
.header-stats {
  display: flex;
  gap: 6px;
}

.stat-item {
  --sc: #047857;
  min-width: 64px;
  padding: 5px 12px;
  text-align: center;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #effcf6 100%);
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -2px 0 rgba(148, 163, 184, 0.25),
    0 6px 14px -10px rgba(15, 23, 42, 0.45);
}

.stat-item:nth-child(2) {
  --sc: #0f766e;
}

.stat-item.warning {
  --sc: #b45309;
  background: linear-gradient(180deg, #ffffff 0%, #fffbeb 100%);
}

.stat-value {
  display: block;
  font-weight: 800;
  color: var(--sc);
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-weight: 700;
  color: #64748b;
}

/* ---------- 検索カード ---------- */
.filter-card {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #d1f2e4;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(4, 120, 87, 0.45);
}

.filter-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 2;
  height: 3px;
  background: linear-gradient(90deg, #059669 0%, #10b981 55%, #2dd4bf 100%);
}

.filter-card :deep(.el-card__header) {
  padding: 10px 14px 8px;
  background: linear-gradient(180deg, #f6fdf9 0%, #eefbf5 100%);
  border-bottom: 1px solid #d1f2e4;
}

.filter-card :deep(.el-card__body) {
  padding: 12px 14px;
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 800;
  color: #065f46;
}

.filter-icon {
  width: 24px;
  height: 24px;
  padding: 5px;
  box-sizing: border-box;
  border-radius: 7px;
  font-size: 14px;
  color: #fff;
  background: linear-gradient(135deg, #34d399, #059669);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(6, 78, 59, 0.3);
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}

.filter-form :deep(.el-form-item) {
  margin: 0;
}

.filter-form :deep(.el-form-item__label) {
  height: 22px;
  margin: auto 8px auto 0;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  line-height: 22px;
  color: #065f46;
  background: #ecfdf5;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #a7f3d0;
}

/* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-select__wrapper) {
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 0 0 1px #cdeedf inset;
}

.filter-form :deep(.el-input__wrapper:hover),
.filter-form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #6ee7b7 inset;
}

.filter-form :deep(.el-input__wrapper.is-focus),
.filter-form :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #059669 inset,
    0 0 0 3px rgba(5, 150, 105, 0.14);
}

/* ---------- ボタン（色で役割を区別） ---------- */
.sms-btn {
  height: 32px;
  padding: 0 14px;
  border-radius: 8px;
  font-weight: 700;
}

.sms-btn .el-icon {
  margin-right: 4px;
}

.sms-btn--search {
  --k-rgb: 5 150 105;
  color: #fff;
  border: 1px solid #047857;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #34d399, #059669);
}

.sms-btn--search:hover,
.sms-btn--search:focus-visible {
  color: #fff;
  border-color: #065f46;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #4ade80, #10b981);
}

.sms-btn--reset,
.sms-btn--excel,
.sms-btn--refresh {
  --sb-fg: #475569;
  --sb-bd: #cbd5e1;
  --sb-bg: #f1f5f9;
  --sb-hv: #94a3b8;
  color: var(--sb-fg);
  border: 1px solid var(--sb-bd);
  background: linear-gradient(180deg, #ffffff 0%, var(--sb-bg) 100%);
}

.sms-btn--reset:hover,
.sms-btn--excel:hover,
.sms-btn--refresh:hover,
.sms-btn--reset:focus-visible,
.sms-btn--excel:focus-visible,
.sms-btn--refresh:focus-visible {
  color: var(--sb-fg);
  border-color: var(--sb-hv);
  background: #fff;
}

.sms-btn--reset {
  --k-rgb: 100 116 139;
}

.sms-btn--excel {
  --k-rgb: 217 119 6;
  --sb-fg: #b45309;
  --sb-bd: #fde68a;
  --sb-bg: #fffbeb;
  --sb-hv: #fbbf24;
}

.sms-btn--refresh {
  --k-rgb: 13 148 136;
  --sb-fg: #0f766e;
  --sb-bd: #99f6e4;
  --sb-bg: #f0fdfa;
  --sb-hv: #2dd4bf;
}

/* ---------- 操作バー ---------- */
.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid #d1f2e4;
  background: linear-gradient(180deg, #ffffff 0%, #f7fdfa 100%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.left-actions {
  display: flex;
  gap: 8px;
}

.left-actions .el-button + .el-button {
  margin-left: 0;
}

.alert-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  font-weight: 700;
  color: #b45309;
  border-color: #fde68a;
  background: #fffbeb;
}

/* ---------- 外注先別カード ---------- */
.supplier-cards {
  display: grid;
  gap: 10px;
}

.supplier-card {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #d1f2e4;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(4, 120, 87, 0.4);
}

.supplier-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 2;
  height: 3px;
  background: linear-gradient(90deg, #059669 0%, #10b981 55%, #2dd4bf 100%);
}

.supplier-card.has-warning {
  border-color: #fde68a;
}

.supplier-card.has-warning::before {
  background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 55%, #fcd34d 100%);
}

.supplier-card :deep(.el-card__header) {
  padding: 10px 14px 8px;
  background: linear-gradient(180deg, #f6fdf9 0%, #ffffff 100%);
  border-bottom: 1px solid #e3f6ed;
}

.supplier-card.has-warning :deep(.el-card__header) {
  background: linear-gradient(180deg, #fffcf0 0%, #ffffff 100%);
}

.supplier-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.supplier-info {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.supplier-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  padding: 6px;
  box-sizing: border-box;
  border-radius: 8px;
  font-size: 16px;
  color: #fff;
  background: linear-gradient(135deg, #34d399, #059669);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(6, 78, 59, 0.3);
}

.supplier-name {
  font-size: 15px;
  font-weight: 800;
  color: #064e3b;
}

.supplier-badges {
  display: flex;
  gap: 6px;
}

.supplier-badges :deep(.el-tag) {
  border-radius: 999px;
  font-weight: 700;
}

.supplier-card :deep(.el-card__body) {
  padding: 0;
}

.supplier-card :deep(.el-table) {
  --el-table-border-color: #e6f4ed;
  --el-table-row-hover-bg-color: #ecfdf5;
}

.supplier-card :deep(.el-table th.el-table__cell) {
  font-weight: 700;
  color: #065f46;
  background: #f0fbf6;
  border-bottom: 1px solid #cdeedf;
}

.supplier-card :deep(.el-table td.el-table__cell) {
  color: #1e293b;
}

.supplier-card :deep(.el-table .el-tag) {
  border-radius: 999px;
  font-weight: 700;
}

.supplier-card :deep(.warning-row) {
  background-color: #fffbeb;
}

.supplier-card :deep(.empty-row) {
  background-color: #fef2f2;
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

.supplier-footer {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 14px;
  font-size: 12.5px;
  color: #475569;
  border-top: 1px solid #e3f6ed;
  background: linear-gradient(180deg, #fafdfb 0%, #f2fbf7 100%);
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.footer-item .el-icon {
  color: #059669;
}

.text-success {
  font-weight: 700;
  color: #16a34a;
}

.text-warning {
  font-weight: 700;
  color: #d97706;
}

/* ---------- 履歴ダイアログ ---------- */
.sms-dlg-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(125deg, #047857 0%, #059669 38%, #10b981 68%, #14b8a6 100%);
}

.sms-dlg-hero__icon {
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
    inset 0 -2px 0 rgba(6, 78, 59, 0.3);
}

.sms-dlg-hero__copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.sms-dlg-hero__title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
  color: #fff;
}

.sms-dlg-hero__desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.88);
}

.sms-dlg-hero__close {
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

.sms-dlg-hero__close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

:global(.el-dialog.sms-dialog) {
  padding: 0;
  overflow: hidden;
  border-radius: 14px;
}

:global(.el-dialog.sms-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
}

:global(.el-dialog.sms-dialog .el-dialog__body) {
  padding: 14px 18px 18px;
}

:global(.el-dialog.sms-dialog .el-table th.el-table__cell) {
  font-weight: 700;
  color: #065f46;
  background: #f0fbf6;
}

/* ---------- レスポンシブ ---------- */
@media (max-width: 768px) {
  .supplied-material-stock-page {
    padding: 8px;
  }

  .header-stats {
    display: none;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .supplier-footer {
    flex-direction: column;
    gap: 6px;
  }
}
</style>
