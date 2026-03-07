<template>
  <div class="usage-management-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2 class="title">
            <div class="title-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <span class="title-text">使用数管理</span>
            <div class="title-badge">
              <span class="badge-text">{{ usageList.length }}</span>
            </div>
          </h2>
          <p class="subtitle">外注先での材料使用数を登録・管理します</p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-value">{{ monthlyUsageQty.toLocaleString() }}</span>
            <span class="stat-label">今月使用</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ pendingReportCount }}</span>
            <span class="stat-label">未報告</span>
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
        <el-form-item label="期間">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="〜"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="外注先">
          <el-select v-model="filters.supplier" placeholder="選択" clearable filterable style="width: 160px">
            <el-option v-for="s in supplierOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="注文番号">
          <el-input v-model="filters.orderNo" placeholder="注文番号" clearable style="width: 130px" />
        </el-form-item>
        <el-form-item label="材料">
          <el-input v-model="filters.materialCode" placeholder="材料コード" clearable style="width: 130px" />
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
        <el-button type="primary" @click="openUsageDialog">
          <el-icon><Plus /></el-icon>使用報告
        </el-button>
        <el-button type="success" @click="batchReport" :disabled="selectedRows.length === 0">
          <el-icon><Document /></el-icon>一括登録
          <span v-if="selectedRows.length > 0" class="btn-badge">{{ selectedRows.length }}</span>
        </el-button>
        <el-button type="warning" @click="exportData">
          <el-icon><Download /></el-icon>Excel出力
        </el-button>
      </div>
      <div class="right-actions">
        <el-tag type="primary" size="large" class="total-tag">
          <el-icon><DataAnalysis /></el-icon>
          今月使用重量: {{ monthlyUsageWeight.toLocaleString() }} kg
        </el-tag>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        ref="tableRef"
        :data="usageList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
        border
        highlight-current-row
        class="data-table"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
      >
        <el-table-column type="selection" width="45" fixed="left" />
        <el-table-column prop="usageNo" label="報告番号" width="130" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row)">{{ row.usageNo }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="usageDate" label="使用日" width="100" />
        <el-table-column prop="orderNo" label="関連注文" width="130" />
        <el-table-column prop="supplier" label="外注先" width="140" />
        <el-table-column prop="materialCode" label="材料コード" width="110" />
        <el-table-column prop="materialName" label="材料名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="usageQty" label="使用数量" width="90" align="right">
          <template #default="{ row }">
            <span class="usage-qty">{{ row.usageQty.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="単位" width="50" align="center" />
        <el-table-column prop="usageWeight" label="使用重量(kg)" width="110" align="right">
          <template #default="{ row }">
            <span class="weight-cell">{{ row.usageWeight.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="productQty" label="製品数量" width="90" align="right">
          <template #default="{ row }">
            {{ row.productQty.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="yieldRate" label="歩留率" width="80" align="right">
          <template #default="{ row }">
            <span :class="getYieldClass(row.yieldRate)">{{ row.yieldRate }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="reporter" label="報告者" width="80" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" size="small" @click="editUsage(row)" :icon="Edit" />
              <el-button type="danger" size="small" @click="deleteUsage(row)" :icon="Delete" />
            </el-button-group>
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

    <!-- 統計カード -->
    <el-row :gutter="16" class="stat-cards">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-icon blue">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stat-card-info">
              <span class="stat-card-value">{{ totalUsageQty.toLocaleString() }}</span>
              <span class="stat-card-label">総使用数量</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-icon green">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-card-info">
              <span class="stat-card-value">{{ avgYieldRate.toFixed(1) }}%</span>
              <span class="stat-card-label">平均歩留率</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-icon orange">
              <el-icon><Box /></el-icon>
            </div>
            <div class="stat-card-info">
              <span class="stat-card-value">{{ totalProductQty.toLocaleString() }}</span>
              <span class="stat-card-label">総製品数量</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="800px" 
      destroy-on-close
      class="usage-dialog"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="外注先" prop="supplierId">
              <el-select v-model="formData.supplierId" placeholder="選択" filterable style="width: 100%" @change="handleSupplierChange">
                <el-option v-for="s in supplierOptions" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="使用日" prop="usageDate">
              <el-date-picker v-model="formData.usageDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="関連注文" prop="orderNo">
              <el-select v-model="formData.orderNo" placeholder="選択" clearable filterable style="width: 100%">
                <el-option v-for="o in orderOptions" :key="o.orderNo" :label="o.orderNo" :value="o.orderNo">
                  <span>{{ o.orderNo }}</span>
                  <span style="color: #8492a6; font-size: 12px; margin-left: 8px">{{ o.productCode }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="報告者" prop="reporter">
              <el-input v-model="formData.reporter" placeholder="報告者名" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">材料使用情報</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="材料" prop="materialCode">
              <el-select 
                v-model="formData.materialCode" 
                placeholder="材料を選択" 
                filterable 
                style="width: 100%"
                @change="handleMaterialChange"
              >
                <el-option 
                  v-for="m in availableMaterials" 
                  :key="m.code" 
                  :label="m.code" 
                  :value="m.code"
                >
                  <span>{{ m.code }}</span>
                  <span style="color: #8492a6; font-size: 12px; margin-left: 8px">在庫: {{ m.stockQty }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="材料名">
              <el-input v-model="formData.materialName" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="使用可能数">
              <el-input :model-value="formData.availableQty?.toLocaleString()" disabled>
                <template #suffix>{{ formData.unit }}</template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="使用数量" prop="usageQty">
              <el-input-number 
                v-model="formData.usageQty" 
                :min="1" 
                :max="formData.availableQty || 99999"
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="単位">
              <el-input v-model="formData.unit" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="単重(kg)">
              <el-input :model-value="formData.unitWeight?.toFixed(3)" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="使用重量(kg)">
              <el-input 
                :model-value="((formData.usageQty || 0) * (formData.unitWeight || 0)).toFixed(2)" 
                disabled 
                class="weight-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="製品数量" prop="productQty">
              <el-input-number v-model="formData.productQty" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="備考">
          <el-input v-model="formData.remarks" type="textarea" :rows="2" placeholder="備考を入力" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">
          {{ isEdit ? '更新' : '登録' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="使用報告詳細" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="報告番号">{{ detailData.usageNo }}</el-descriptions-item>
        <el-descriptions-item label="使用日">{{ detailData.usageDate }}</el-descriptions-item>
        <el-descriptions-item label="外注先">{{ detailData.supplier }}</el-descriptions-item>
        <el-descriptions-item label="関連注文">{{ detailData.orderNo || '-' }}</el-descriptions-item>
        <el-descriptions-item label="材料コード">{{ detailData.materialCode }}</el-descriptions-item>
        <el-descriptions-item label="材料名">{{ detailData.materialName }}</el-descriptions-item>
        <el-descriptions-item label="使用数量">{{ detailData.usageQty?.toLocaleString() }} {{ detailData.unit }}</el-descriptions-item>
        <el-descriptions-item label="使用重量">{{ detailData.usageWeight?.toLocaleString() }} kg</el-descriptions-item>
        <el-descriptions-item label="製品数量">{{ detailData.productQty?.toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="歩留率">
          <span :class="getYieldClass(detailData.yieldRate)">{{ detailData.yieldRate }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="報告者">{{ detailData.reporter }}</el-descriptions-item>
        <el-descriptions-item label="備考" :span="2">{{ detailData.remarks || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Refresh, Plus, Download, Edit, Delete, DataAnalysis, Document, Box, TrendCharts
} from '@element-plus/icons-vue'

interface UsageItem {
  id: number
  usageNo: string
  usageDate: string
  orderNo: string
  supplier: string
  supplierId: number
  materialCode: string
  materialName: string
  usageQty: number
  unit: string
  usageWeight: number
  productQty: number
  yieldRate: number
  reporter: string
  remarks?: string
}

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const selectedRows = ref<UsageItem[]>([])
const tableRef = ref()

const filters = reactive({
  dateRange: [] as string[],
  supplier: '',
  orderNo: '',
  materialCode: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const formRef = ref()
const formData = reactive({
  supplierId: null as number | null,
  usageDate: '',
  orderNo: '',
  reporter: '',
  materialCode: '',
  materialName: '',
  availableQty: 0,
  usageQty: 0,
  unit: '',
  unitWeight: 0,
  productQty: 0,
  remarks: ''
})

const formRules = {
  supplierId: [{ required: true, message: '外注先を選択してください', trigger: 'change' }],
  usageDate: [{ required: true, message: '使用日を選択してください', trigger: 'change' }],
  orderNo: [{ required: true, message: '関連注文を選択してください', trigger: 'change' }],
  materialCode: [{ required: true, message: '材料を選択してください', trigger: 'change' }],
  usageQty: [{ required: true, message: '使用数量を入力してください', trigger: 'blur' }],
  reporter: [{ required: true, message: '報告者を入力してください', trigger: 'blur' }]
}

const detailData = ref<Partial<UsageItem>>({})

const usageList = ref<UsageItem[]>([
  { id: 1, usageNo: 'UR-2025-001', usageDate: '2025-12-03', orderNo: 'PO-2025-001', supplier: '山田メッキ工業', supplierId: 1, materialCode: 'M-001', materialName: 'SUS304丸棒', usageQty: 50, unit: '本', usageWeight: 31, productQty: 480, yieldRate: 96.0, reporter: '外注担当A', remarks: '' },
  { id: 2, usageNo: 'UR-2025-002', usageDate: '2025-12-03', orderNo: 'WO-2025-001', supplier: '高橋溶接工業', supplierId: 2, materialCode: 'M-004', materialName: 'SS400板材', usageQty: 20, unit: '枚', usageWeight: 1504, productQty: 190, yieldRate: 95.0, reporter: '外注担当B', remarks: '' },
  { id: 3, usageNo: 'UR-2025-003', usageDate: '2025-12-02', orderNo: 'PO-2025-002', supplier: '佐藤表面処理', supplierId: 3, materialCode: 'M-006', materialName: 'A5052アルミ板', usageQty: 10, unit: '枚', usageWeight: 87, productQty: 92, yieldRate: 92.0, reporter: '外注担当C', remarks: '' },
])

const supplierOptions = ref([
  { value: 1, label: '山田メッキ工業' },
  { value: 2, label: '高橋溶接工業' },
  { value: 3, label: '佐藤表面処理' },
])

const orderOptions = ref([
  { orderNo: 'PO-2025-001', productCode: 'PT-001' },
  { orderNo: 'PO-2025-002', productCode: 'PT-002' },
  { orderNo: 'WO-2025-001', productCode: 'WD-001' },
])

const availableMaterials = ref([
  { code: 'M-001', name: 'SUS304丸棒', unit: '本', unitWeight: 0.62, stockQty: 80 },
  { code: 'M-004', name: 'SS400板材', unit: '枚', unitWeight: 75.2, stockQty: 50 },
])

const monthlyUsageQty = computed(() => usageList.value.reduce((sum, i) => sum + i.usageQty, 0))
const monthlyUsageWeight = computed(() => usageList.value.reduce((sum, i) => sum + i.usageWeight, 0))
const pendingReportCount = ref(2)
const totalUsageQty = computed(() => usageList.value.reduce((sum, i) => sum + i.usageQty, 0))
const totalProductQty = computed(() => usageList.value.reduce((sum, i) => sum + i.productQty, 0))
const avgYieldRate = computed(() => {
  if (usageList.value.length === 0) return 0
  return usageList.value.reduce((sum, i) => sum + i.yieldRate, 0) / usageList.value.length
})
const dialogTitle = computed(() => isEdit.value ? '使用報告編集' : '新規使用報告')

const getYieldClass = (rate: number | undefined) => {
  if (!rate) return ''
  if (rate >= 95) return 'yield-good'
  if (rate >= 90) return 'yield-normal'
  return 'yield-low'
}

const handleSearch = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    pagination.total = usageList.value.length
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, { dateRange: [], supplier: '', orderNo: '', materialCode: '' })
  handleSearch()
}

const handleSelectionChange = (rows: UsageItem[]) => {
  selectedRows.value = rows
}

const openUsageDialog = () => {
  isEdit.value = false
  Object.assign(formData, {
    supplierId: null, usageDate: new Date().toISOString().split('T')[0], orderNo: '', reporter: '',
    materialCode: '', materialName: '', availableQty: 0, usageQty: 0, unit: '', unitWeight: 0, productQty: 0, remarks: ''
  })
  dialogVisible.value = true
}

const handleSupplierChange = () => {
  formData.materialCode = ''
  formData.materialName = ''
}

const handleMaterialChange = (code: string) => {
  const material = availableMaterials.value.find(m => m.code === code)
  if (material) {
    Object.assign(formData, {
      materialName: material.name,
      unit: material.unit,
      unitWeight: material.unitWeight,
      availableQty: material.stockQty
    })
  }
}

const editUsage = (row: UsageItem) => {
  isEdit.value = true
  Object.assign(formData, row)
  dialogVisible.value = true
}

const viewDetail = (row: UsageItem) => {
  detailData.value = row
  detailVisible.value = true
}

const submitForm = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return
  submitLoading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success(isEdit.value ? '更新しました' : '登録しました')
    dialogVisible.value = false
    handleSearch()
  } catch (error) {
    ElMessage.error('エラーが発生しました')
  } finally {
    submitLoading.value = false
  }
}

const deleteUsage = async (row: UsageItem) => {
  await ElMessageBox.confirm('この使用報告を削除しますか？', '確認', { type: 'warning' })
  ElMessage.success('削除しました')
  handleSearch()
}

const batchReport = () => {
  ElMessage.info(`${selectedRows.value.length}件の一括登録を行います`)
}

const exportData = () => {
  ElMessage.info('Excel出力機能は準備中です')
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.usage-management-page {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
  color: white;
  box-shadow: 0 4px 20px rgba(255, 193, 7, 0.3);
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

.title-badge {
  background: rgba(255, 255, 255, 0.25);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
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
  min-width: 70px;
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
  color: #ffc107;
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

.btn-badge {
  margin-left: 6px;
  background: rgba(255, 255, 255, 0.3);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.total-tag {
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

.usage-qty {
  font-weight: 600;
  color: #ffc107;
}

.weight-cell {
  font-weight: 600;
  color: #e6a23c;
}

.yield-good {
  color: #67c23a;
  font-weight: 600;
}

.yield-normal {
  color: #e6a23c;
  font-weight: 600;
}

.yield-low {
  color: #f56c6c;
  font-weight: 600;
}

.pagination-wrapper {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #ebeef5;
}

.stat-cards {
  margin-top: 16px;
}

.stat-card {
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.stat-card-icon.blue {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.stat-card-icon.green {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.stat-card-icon.orange {
  background: linear-gradient(135deg, #ffc107, #ff9800);
}

.stat-card-info {
  display: flex;
  flex-direction: column;
}

.stat-card-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.stat-card-label {
  font-size: 13px;
  color: #909399;
}

.usage-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
  color: white;
  margin: 0;
  padding: 16px 20px;
  border-radius: 8px 8px 0 0;
}

.usage-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

.weight-input :deep(.el-input__inner) {
  color: #e6a23c;
  font-weight: 600;
}

@media (max-width: 768px) {
  .usage-management-page {
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
  .stat-cards :deep(.el-col) {
    margin-bottom: 12px;
  }
}
</style>

