<template>
  <div class="material-issue-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2 class="title">
            <div class="title-icon">
              <el-icon><Upload /></el-icon>
            </div>
            <span class="title-text">支給材料出庫</span>
            <div class="title-badge">
              <span class="badge-text">{{ issueList.length }}</span>
            </div>
          </h2>
          <p class="subtitle">外注業者への材料支給・出庫管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-value">{{ todayIssueCount }}</span>
            <span class="stat-label">本日出庫</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ pendingCount }}</span>
            <span class="stat-label">準備中</span>
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
        <el-form-item label="状態">
          <el-select v-model="filters.status" placeholder="選択" clearable style="width: 110px">
            <el-option label="準備中" value="preparing" />
            <el-option label="出庫済" value="issued" />
            <el-option label="返却済" value="returned" />
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
        <el-button type="primary" @click="openIssueDialog">
          <el-icon><Plus /></el-icon>新規支給
        </el-button>
        <el-button type="success" @click="batchIssue" :disabled="selectedRows.length === 0">
          <el-icon><Upload /></el-icon>一括出庫
          <span v-if="selectedRows.length > 0" class="btn-badge">{{ selectedRows.length }}</span>
        </el-button>
        <el-button type="warning" @click="exportData">
          <el-icon><Download /></el-icon>Excel出力
        </el-button>
        <el-button type="info" @click="printDeliveryNote" :disabled="selectedRows.length === 0">
          <el-icon><Printer /></el-icon>支給伝票印刷
        </el-button>
      </div>
      <div class="right-actions">
        <el-tag type="primary" size="large" class="total-tag">
          <el-icon><Box /></el-icon>
          本日支給: {{ todayQuantity.toLocaleString() }} kg
        </el-tag>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        ref="tableRef"
        :data="issueList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
        border
        highlight-current-row
        class="data-table"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
      >
        <el-table-column type="selection" width="45" fixed="left" />
        <el-table-column prop="issueNo" label="支給番号" width="130" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row)">{{ row.issueNo }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="issueDate" label="出庫日" width="100" />
        <el-table-column prop="orderNo" label="関連注文" width="130" />
        <el-table-column prop="supplier" label="外注先" width="140" />
        <el-table-column prop="materialCode" label="材料コード" width="110" />
        <el-table-column prop="materialName" label="材料名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="spec" label="規格" width="100" />
        <el-table-column prop="quantity" label="支給数量" width="90" align="right">
          <template #default="{ row }">
            <span class="quantity-cell">{{ row.quantity.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="単位" width="60" align="center" />
        <el-table-column prop="unitWeight" label="単重(kg)" width="80" align="right">
          <template #default="{ row }">
            {{ row.unitWeight.toFixed(3) }}
          </template>
        </el-table-column>
        <el-table-column prop="totalWeight" label="総重量(kg)" width="100" align="right">
          <template #default="{ row }">
            <span class="weight-cell">{{ row.totalWeight.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状態" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="担当者" width="80" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                type="success" 
                size="small" 
                @click="issueItem(row)" 
                :disabled="row.status !== 'preparing'"
              >
                <el-icon><Upload /></el-icon>出庫
              </el-button>
              <el-button type="primary" size="small" @click="editIssue(row)" :icon="Edit" />
              <el-button type="danger" size="small" @click="deleteIssue(row)" :icon="Delete" />
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

    <!-- 新建/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="850px" 
      destroy-on-close
      class="issue-dialog"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="外注先" prop="supplierId">
              <el-select v-model="formData.supplierId" placeholder="選択" filterable style="width: 100%">
                <el-option v-for="s in supplierOptions" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="関連注文">
              <el-select v-model="formData.orderNo" placeholder="選択（任意）" clearable filterable style="width: 100%">
                <el-option v-for="o in orderOptions" :key="o.orderNo" :label="o.orderNo" :value="o.orderNo">
                  <span>{{ o.orderNo }}</span>
                  <span style="color: #8492a6; font-size: 12px; margin-left: 8px">{{ o.productCode }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="出庫日" prop="issueDate">
              <el-date-picker v-model="formData.issueDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="担当者" prop="operator">
              <el-input v-model="formData.operator" placeholder="担当者名" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">材料情報</el-divider>
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
                  v-for="m in materialOptions" 
                  :key="m.code" 
                  :label="m.code" 
                  :value="m.code"
                >
                  <span>{{ m.code }}</span>
                  <span style="color: #8492a6; font-size: 12px; margin-left: 8px">{{ m.name }}</span>
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
            <el-form-item label="規格">
              <el-input v-model="formData.spec" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="在庫数">
              <el-input :model-value="formData.stockQty?.toLocaleString()" disabled>
                <template #suffix>{{ formData.unit }}</template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="単重(kg)">
              <el-input :model-value="formData.unitWeight?.toFixed(3)" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="支給数量" prop="quantity">
              <el-input-number 
                v-model="formData.quantity" 
                :min="1" 
                :max="formData.stockQty || 99999"
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="単位">
              <el-input v-model="formData.unit" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="総重量(kg)">
              <el-input 
                :model-value="((formData.quantity || 0) * (formData.unitWeight || 0)).toFixed(2)" 
                disabled 
                class="weight-input"
              />
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
    <el-dialog v-model="detailVisible" title="支給詳細" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="支給番号">{{ detailData.issueNo }}</el-descriptions-item>
        <el-descriptions-item label="出庫日">{{ detailData.issueDate }}</el-descriptions-item>
        <el-descriptions-item label="外注先">{{ detailData.supplier }}</el-descriptions-item>
        <el-descriptions-item label="関連注文">{{ detailData.orderNo || '-' }}</el-descriptions-item>
        <el-descriptions-item label="材料コード">{{ detailData.materialCode }}</el-descriptions-item>
        <el-descriptions-item label="材料名">{{ detailData.materialName }}</el-descriptions-item>
        <el-descriptions-item label="規格">{{ detailData.spec }}</el-descriptions-item>
        <el-descriptions-item label="単位">{{ detailData.unit }}</el-descriptions-item>
        <el-descriptions-item label="支給数量">{{ detailData.quantity?.toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="単重(kg)">{{ detailData.unitWeight?.toFixed(3) }}</el-descriptions-item>
        <el-descriptions-item label="総重量(kg)">{{ detailData.totalWeight?.toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="状態">
          <el-tag :type="getStatusType(detailData.status)">{{ getStatusLabel(detailData.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="担当者">{{ detailData.operator }}</el-descriptions-item>
        <el-descriptions-item label="備考" :span="2">{{ detailData.remarks || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Refresh, Plus, Download, Edit, Delete, Upload, Box, Printer
} from '@element-plus/icons-vue'

interface IssueItem {
  id: number
  issueNo: string
  issueDate: string
  orderNo: string
  supplier: string
  supplierId: number
  materialCode: string
  materialName: string
  spec: string
  quantity: number
  unit: string
  unitWeight: number
  totalWeight: number
  status: string
  operator: string
  remarks?: string
}

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const selectedRows = ref<IssueItem[]>([])
const tableRef = ref()

const filters = reactive({
  dateRange: [] as string[],
  supplier: '',
  orderNo: '',
  materialCode: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const formRef = ref()
const formData = reactive({
  supplierId: null as number | null,
  orderNo: '',
  issueDate: '',
  operator: '',
  materialCode: '',
  materialName: '',
  spec: '',
  stockQty: 0,
  quantity: 0,
  unit: '',
  unitWeight: 0,
  remarks: ''
})

const formRules = {
  supplierId: [{ required: true, message: '外注先を選択してください', trigger: 'change' }],
  issueDate: [{ required: true, message: '出庫日を選択してください', trigger: 'change' }],
  materialCode: [{ required: true, message: '材料を選択してください', trigger: 'change' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }],
  operator: [{ required: true, message: '担当者を入力してください', trigger: 'blur' }]
}

const detailData = ref<Partial<IssueItem>>({})

const issueList = ref<IssueItem[]>([
  { id: 1, issueNo: 'MI-2025-001', issueDate: '2025-12-03', orderNo: 'PO-2025-001', supplier: '山田メッキ工業', supplierId: 1, materialCode: 'M-001', materialName: 'SUS304丸棒', spec: 'φ10x1000', quantity: 100, unit: '本', unitWeight: 0.62, totalWeight: 62, status: 'issued', operator: '田中', remarks: '' },
  { id: 2, issueNo: 'MI-2025-002', issueDate: '2025-12-03', orderNo: 'WO-2025-001', supplier: '高橋溶接工業', supplierId: 2, materialCode: 'M-002', materialName: 'SS400板材', spec: 't3.2x1219x2438', quantity: 50, unit: '枚', unitWeight: 75.2, totalWeight: 3760, status: 'issued', operator: '鈴木', remarks: '' },
  { id: 3, issueNo: 'MI-2025-003', issueDate: '2025-12-03', orderNo: '', supplier: '佐藤表面処理', supplierId: 3, materialCode: 'M-003', materialName: 'SPHC-P', spec: 't1.6x1219x2438', quantity: 30, unit: '枚', unitWeight: 37.6, totalWeight: 1128, status: 'preparing', operator: '山田', remarks: '午後出庫予定' },
])

const supplierOptions = ref([
  { value: 1, label: '山田メッキ工業' },
  { value: 2, label: '高橋溶接工業' },
  { value: 3, label: '佐藤表面処理' },
  { value: 4, label: '渡辺精密溶接' },
])

const orderOptions = ref([
  { orderNo: 'PO-2025-001', productCode: 'PT-001' },
  { orderNo: 'PO-2025-002', productCode: 'PT-002' },
  { orderNo: 'WO-2025-001', productCode: 'WD-001' },
])

const materialOptions = ref([
  { code: 'M-001', name: 'SUS304丸棒', spec: 'φ10x1000', unit: '本', unitWeight: 0.62, stockQty: 500 },
  { code: 'M-002', name: 'SS400板材', spec: 't3.2x1219x2438', unit: '枚', unitWeight: 75.2, stockQty: 200 },
  { code: 'M-003', name: 'SPHC-P', spec: 't1.6x1219x2438', unit: '枚', unitWeight: 37.6, stockQty: 150 },
])

const todayIssueCount = computed(() => issueList.value.filter(i => i.issueDate === new Date().toISOString().split('T')[0] && i.status === 'issued').length)
const pendingCount = computed(() => issueList.value.filter(i => i.status === 'preparing').length)
const todayQuantity = computed(() => issueList.value.filter(i => i.issueDate === new Date().toISOString().split('T')[0]).reduce((sum, i) => sum + i.totalWeight, 0))
const dialogTitle = computed(() => isEdit.value ? '支給編集' : '新規支給')

const getStatusType = (status: string) => {
  const types: Record<string, string> = { preparing: 'warning', issued: 'success', returned: 'info' }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = { preparing: '準備中', issued: '出庫済', returned: '返却済' }
  return labels[status] || status
}

const handleSearch = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    pagination.total = issueList.value.length
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, { dateRange: [], supplier: '', orderNo: '', materialCode: '', status: '' })
  handleSearch()
}

const handleSelectionChange = (rows: IssueItem[]) => {
  selectedRows.value = rows
}

const openIssueDialog = () => {
  isEdit.value = false
  Object.assign(formData, {
    supplierId: null, orderNo: '', issueDate: new Date().toISOString().split('T')[0], operator: '',
    materialCode: '', materialName: '', spec: '', stockQty: 0, quantity: 0, unit: '', unitWeight: 0, remarks: ''
  })
  dialogVisible.value = true
}

const handleMaterialChange = (code: string) => {
  const material = materialOptions.value.find(m => m.code === code)
  if (material) {
    Object.assign(formData, {
      materialName: material.name,
      spec: material.spec,
      unit: material.unit,
      unitWeight: material.unitWeight,
      stockQty: material.stockQty,
      quantity: Math.min(100, material.stockQty)
    })
  }
}

const editIssue = (row: IssueItem) => {
  isEdit.value = true
  Object.assign(formData, row)
  dialogVisible.value = true
}

const viewDetail = (row: IssueItem) => {
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

const issueItem = async (row: IssueItem) => {
  await ElMessageBox.confirm(`${row.issueNo} を出庫しますか？`, '確認', { type: 'info' })
  row.status = 'issued'
  ElMessage.success('出庫完了しました')
}

const deleteIssue = async (row: IssueItem) => {
  await ElMessageBox.confirm('この支給を削除しますか？', '確認', { type: 'warning' })
  ElMessage.success('削除しました')
  handleSearch()
}

const batchIssue = () => {
  ElMessage.info(`${selectedRows.value.length}件の一括出庫を行います`)
}

const exportData = () => {
  ElMessage.info('Excel出力機能は準備中です')
}

const printDeliveryNote = () => {
  ElMessage.info('支給伝票印刷機能は準備中です')
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.material-issue-page {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
  color: white;
  box-shadow: 0 4px 20px rgba(240, 147, 251, 0.3);
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
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 10px 16px;
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
  color: #f093fb;
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
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.quantity-cell {
  font-weight: 600;
  color: #f093fb;
}

.weight-cell {
  font-weight: 600;
  color: #e6a23c;
}

.pagination-wrapper {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #ebeef5;
}

.issue-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  margin: 0;
  padding: 16px 20px;
  border-radius: 8px 8px 0 0;
}

.issue-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

.weight-input :deep(.el-input__inner) {
  color: #e6a23c;
  font-weight: 600;
}

@media (max-width: 768px) {
  .material-issue-page {
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
  .left-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>

