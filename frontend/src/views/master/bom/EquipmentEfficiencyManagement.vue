<template>
  <div class="equipment-efficiency-container fade-in">
    <!-- 页面头部 -->
    <div class="page-header surface-card fade-card">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Tools />
            </el-icon>
            設備能率管理
          </h1>
          <p class="subtitle">設備ごとの加工製品別能率設定・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ efficiencyList?.length || 0 }}</div>
            <div class="stat-label">設定数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ uniqueEquipmentCount }}</div>
            <div class="stat-label">設備数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ uniqueProductCount }}</div>
            <div class="stat-label">製品数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区域 -->
    <div class="action-section surface-card fade-card">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">
            クリア
          </el-button>
          <el-button type="primary" @click="openDialog()" :icon="Plus" class="add-btn">
            新規登録
          </el-button>
        </div>
      </div>
      <div class="filters-content">
        <div class="keyword-search">
          <el-input
            v-model="filters.keyword"
            placeholder="製品名または設備名で検索"
            clearable
            @input="handleFilter"
            class="keyword-input"
          >
            <template #prefix>
              <el-icon>
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-section surface-card fade-card">
      <el-card class="table-card elevated-card" shadow="never">
        <el-tabs v-model="activeProcessTab" @tab-change="handleTabChange" class="process-tabs">
          <el-tab-pane
            v-for="process in processTypes"
            :key="process.value"
            :label="`${process.label} (${getProcessCount(process.value)})`"
            :name="process.value"
          >
            <el-table
              :data="getFilteredListByProcess(process.value)"
              v-loading="loading"
              stripe
              border
              style="width: 100%"
              :empty-text="'データがありません'"
              :default-sort="{ prop: 'machines_name', order: 'ascending' }"
              :row-class-name="getRowClassName"
              height="600"
            >
              <el-table-column type="index" label="No." width="80" align="center" />
              <el-table-column
                prop="machine_cd"
                label="設備コード"
                width="120"
                align="center"
                sortable
              />
              <el-table-column prop="machines_name" label="設備名" width="150" sortable />
              <el-table-column
                prop="product_cd"
                label="製品コード"
                width="120"
                align="center"
                sortable
              />
              <el-table-column prop="product_name" label="製品名" min-width="150" sortable />
              <el-table-column prop="efficiency_rate" label="能率" width="120" align="center">
                <template #default="{ row }">
                  <div class="efficiency-cell">
                    <span class="efficiency-value">{{ row.efficiency_rate?.toFixed(1) }}</span>
                    <span v-if="row.unit" class="efficiency-unit">{{ row.unit }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="step_time" label="段取時間（分）" width="130" align="center" />
              <el-table-column prop="status" label="状態" width="120" align="center">
                <template #default="{ row }">
                  <div class="status-cell">
                    <el-switch
                      v-model="row.status"
                      :active-value="1"
                      :inactive-value="0"
                      :loading="statusUpdatingId === row.id"
                      @change="(value) => handleStatusChange(row, value)"
                    />
                    <span class="status-label" :class="{ active: row.status === 1 }">
                      {{ row.status === 1 ? '有効' : '無効' }}
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="remarks" label="備考" min-width="200" show-overflow-tooltip />
              <el-table-column label="操作" fixed="right" width="180" align="center">
                <template #default="{ row }">
                  <div class="action-buttons-table">
                    <el-button
                      size="small"
                      type="primary"
                      link
                      @click="openDialog(row)"
                      :icon="Edit"
                    >
                      編集
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      link
                      @click="handleDelete(row.id)"
                      :icon="Delete"
                    >
                      削除
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <div class="result-section surface-card fade-card">
      <div class="result-info">
        表示件数: {{ getFilteredListByProcess(activeProcessTab).length }} /
        {{ efficiencyList?.length || 0 }}
        <span v-if="activeProcessTab !== 'all'" class="process-info">
          （{{ processTypes.find((p) => p.value === activeProcessTab)?.label }}工程）
        </span>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '能率設定編集' : '能率設定新規登録'"
      width="600px"
      :close-on-click-modal="false"
      class="efficiency-dialog"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        label-position="left"
        class="efficiency-form"
      >
        <div class="form-grid">
          <el-form-item label="設備" prop="machine_cd" class="span-2">
            <el-select
              v-model="formData.machine_cd"
              placeholder="設備を選択"
              filterable
              style="width: 100%"
              @change="handleEquipmentChange"
            >
              <el-option
                v-for="equipment in equipmentOptions"
                :key="equipment.value"
                :label="`${equipment.label} (${equipment.value})`"
                :value="equipment.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="設備名" prop="machines_name" class="span-2">
            <el-input v-model="formData.machines_name" disabled />
          </el-form-item>
          <el-form-item label="製品" prop="product_cd" class="span-2">
            <el-select
              v-model="formData.product_cd"
              placeholder="製品を選択"
              filterable
              style="width: 100%"
              @change="handleProductChange"
            >
              <el-option
                v-for="product in productOptions"
                :key="product.value"
                :label="`${product.label} (${product.value})`"
                :value="product.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="製品名" prop="product_name" class="span-2">
            <el-input v-model="formData.product_name" disabled />
          </el-form-item>
          <el-form-item label="能率" prop="efficiency_rate">
            <el-input-number
              v-model="formData.efficiency_rate"
              :min="0"
              :max="10000"
              :precision="1"
              :step="0.1"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="段取時間（分）" prop="step_time">
            <el-input-number
              v-model="formData.step_time"
              :min="0"
              :max="9999"
              :precision="0"
              style="width: 100%"
              placeholder="段取時間を入力"
            />
          </el-form-item>
          <el-form-item label="状態" prop="status" class="span-2 status-group">
            <el-radio-group v-model="formData.status">
              <el-radio :label="1">有効</el-radio>
              <el-radio :label="0">無効</el-radio>
            </el-radio-group>
          </el-form-item>
        </div>
        <el-form-item label="備考" prop="remarks" class="remarks-item">
          <el-input v-model="formData.remarks" type="textarea" :rows="3" placeholder="備考を入力" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">キャンセル</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting"> 保存 </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Tools, Filter, Refresh, Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import {
  fetchEquipmentEfficiencyList,
  createEquipmentEfficiency,
  updateEquipmentEfficiency,
  deleteEquipmentEfficiency,
  type EquipmentEfficiency,
} from '@/api/master/equipmentEfficiencyMaster'
import { fetchMachines } from '@/api/master/machineMaster'
import { getProductList } from '@/api/master/productMaster'
import type { FormInstance, FormRules } from 'element-plus'

defineOptions({ name: 'EquipmentEfficiencyManagement' })

const efficiencyList = ref<EquipmentEfficiency[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const activeProcessTab = ref('all')
const statusUpdatingId = ref<number | null>(null)

const processTypes = [
  { label: '全て', value: 'all' },
  { label: '切断', value: 'cutting' },
  { label: '面取', value: 'chamfering' },
  { label: '成型', value: 'forming' },
  { label: '溶接', value: 'welding' },
  { label: 'メッキ', value: 'plating' },
  { label: '検査', value: 'inspection' },
  { label: 'その他', value: 'other' },
]

const extractList = (response: any): any[] => {
  if (!response) return []
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.list)) return response.list
  if (Array.isArray(response?.data?.list)) return response.data.list
  if (Array.isArray(response?.data?.data)) return response.data.data
  if (Array.isArray(response?.result)) return response.result
  return []
}

const equipmentOptions = ref<Array<{ label: string; value: string }>>([])
const productOptions = ref<Array<{ label: string; value: string }>>([])

const formData = ref<Partial<EquipmentEfficiency>>({
  machine_cd: '',
  machines_name: '',
  product_cd: '',
  product_name: '',
  efficiency_rate: 0,
  step_time: undefined,
  unit: '',
  status: 1,
  remarks: '',
})

const formRules: FormRules = {
  machine_cd: [{ required: true, message: '設備を選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
  efficiency_rate: [
    { required: true, message: '能率を入力してください', trigger: 'blur' },
    { type: 'number', min: 0, message: '能率は0以上である必要があります', trigger: 'blur' },
  ],
}

const filters = ref({ keyword: '' })

const uniqueEquipmentCount = computed(() => {
  const codes = new Set(efficiencyList.value.map((item) => item.machine_cd))
  return codes.size
})

const uniqueProductCount = computed(() => {
  const codes = new Set(efficiencyList.value.map((item) => item.product_cd))
  return codes.size
})

const getProcessType = (item: EquipmentEfficiency): string => {
  const machineName = (item.machines_name || '').toLowerCase()
  const machineCd = (item.machine_cd || '').toLowerCase()
  if (machineName.includes('面取') || machineName.includes('chamfer') || machineCd.includes('chamfer')) return 'chamfering'
  if (machineName.includes('成型') || machineName.includes('forming') || machineCd.includes('forming')) return 'forming'
  if (machineName.includes('溶接') || machineName.includes('welding') || machineCd.includes('welding')) return 'welding'
  if (machineName.includes('メッキ') || machineName.includes('plating') || machineCd.includes('plating')) return 'plating'
  if (machineName.includes('検査') || machineName.includes('inspection') || machineCd.includes('inspection')) return 'inspection'
  if (machineName.includes('切断') || machineName.includes('cutting') || machineCd.includes('cutting')) return 'cutting'
  return 'other'
}

const filteredEfficiencyList = computed(() => {
  let result = efficiencyList.value || []
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase().trim()
    result = result.filter((item) => {
      const productName = (item.product_name || '').toLowerCase()
      const machineName = (item.machines_name || '').toLowerCase()
      return productName.includes(keyword) || machineName.includes(keyword)
    })
  }
  return [...result].sort((a, b) => {
    const machineCompare = (a.machines_name || '').localeCompare(b.machines_name || '', 'ja')
    if (machineCompare !== 0) return machineCompare
    return (a.product_name || '').localeCompare(b.product_name || '', 'ja')
  })
})

const getFilteredListByProcess = (processType: string) => {
  let result = filteredEfficiencyList.value
  if (processType !== 'all') {
    result = result.filter((item) => getProcessType(item) === processType)
  }
  return result
}

const getProcessCount = (processType: string): number => {
  if (processType === 'all') return filteredEfficiencyList.value.length
  return filteredEfficiencyList.value.filter((item) => getProcessType(item) === processType).length
}

const handleTabChange = () => {}

const getRowClassName = () => 'compact-table-row'

const handleStatusChange = async (row: EquipmentEfficiency, value: number | string | boolean) => {
  if (!row.id) return
  const previousStatus = row.status
  const newStatus = typeof value === 'number' ? value : Number(value)
  row.status = newStatus
  statusUpdatingId.value = row.id
  try {
    await updateEquipmentEfficiency(row.id, { status: newStatus })
    ElMessage.success('状態を更新しました')
  } catch (error) {
    row.status = previousStatus
    console.error('状態更新に失敗:', error)
    ElMessage.error('状態の更新に失敗しました')
  } finally {
    statusUpdatingId.value = null
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const result = (await fetchEquipmentEfficiencyList({ limit: 99999 })) as any
    if (result.success && result.data) {
      efficiencyList.value = result.data.list || []
    } else if (result.list) {
      efficiencyList.value = result.list || []
    } else {
      efficiencyList.value = []
    }
  } catch (error) {
    console.error('能率データの読み込みに失敗:', error)
    ElMessage.error('能率データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

const loadEquipmentOptions = async () => {
  try {
    const result = (await fetchMachines()) as any
    const machineList = extractList(result)
    equipmentOptions.value = machineList.map((machine: any) => ({
      label: machine.machine_name || '',
      value: machine.machine_cd || '',
    }))
  } catch (error) {
    console.error('設備データの読み込みに失敗:', error)
    ElMessage.error('設備データの読み込みに失敗しました')
  }
}

const loadProductOptions = async () => {
  try {
    const result = await getProductList({ page: 1, pageSize: 10000 })
    const productList = extractList(result)
    productOptions.value = productList.map((product: any) => ({
      label: product.product_name || '',
      value: product.product_cd || '',
    }))
  } catch (error) {
    console.error('製品データの読み込みに失敗:', error)
    ElMessage.error('製品データの読み込みに失敗しました')
  }
}

const handleEquipmentChange = (value: string) => {
  const equipment = equipmentOptions.value.find((eq) => eq.value === value)
  if (equipment) {
    formData.value.machines_name = equipment.label
    formData.value.machine_cd = value
  }
}

const handleProductChange = (value: string) => {
  const product = productOptions.value.find((prod) => prod.value === value)
  if (product) {
    formData.value.product_name = product.label
    formData.value.product_cd = value
  }
}

const openDialog = (row?: EquipmentEfficiency) => {
  isEdit.value = !!row
  if (row) {
    formData.value = { ...row }
  } else {
    formData.value = {
      machine_cd: '',
      machines_name: '',
      product_cd: '',
      product_name: '',
      efficiency_rate: 0,
      step_time: undefined,
      unit: '',
      status: 1,
      remarks: '',
    }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value && formData.value.id) {
        await updateEquipmentEfficiency(formData.value.id, formData.value)
        ElMessage.success('能率設定を更新しました')
      } else {
        await createEquipmentEfficiency(formData.value)
        ElMessage.success('能率設定を登録しました')
      }
      dialogVisible.value = false
      await loadData()
    } catch (error) {
      console.error('保存に失敗:', error)
      ElMessage.error('保存に失敗しました')
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (id?: number) => {
  if (!id) return
  try {
    await ElMessageBox.confirm('この能率設定を削除しますか？', '確認', {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
    await deleteEquipmentEfficiency(id)
    ElMessage.success('能率設定を削除しました')
    await loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('削除に失敗:', error)
      ElMessage.error('削除に失敗しました')
    }
  }
}

const handleFilter = () => {}

const clearFilters = () => {
  filters.value = { keyword: '' }
}

onMounted(async () => {
  await Promise.all([loadData(), loadEquipmentOptions(), loadProductOptions()])
})
</script>

<style scoped>
.equipment-efficiency-container {
  min-height: 100vh;
  background: radial-gradient(circle at top, #fdfbff 0%, #f2f4f8 45%, #edf1f7 100%);
  padding: 18px 24px 32px;
}

.surface-card {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(210, 214, 233, 0.6);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(6px);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.surface-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.12);
}

.fade-card {
  animation: fadeUp 0.45s ease;
}

.page-header {
  background: linear-gradient(135deg, rgba(101, 116, 205, 0.95), rgba(118, 75, 162, 0.92));
  padding: 24px 32px;
  margin-bottom: 18px;
  color: #fff;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.title-section {
  flex: 1;
}

.main-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 6px 0;
}

.title-icon {
  font-size: 30px;
}

.subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 14px 18px;
  text-align: center;
  min-width: 90px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 28px rgba(255, 255, 255, 0.2);
}

.stat-number {
  font-size: 22px;
  font-weight: 700;
  color: white;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.05em;
}

.action-section {
  padding: 18px 24px;
  margin-bottom: 18px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.filter-icon {
  font-size: 18px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.filter-actions .el-button:hover {
  transform: translateY(-1px);
}

.filters-content {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.keyword-search {
  flex: 1;
  min-width: 260px;
}

.keyword-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.25);
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.08);
}

.keyword-input :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

.status-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.status-label {
  font-size: 12px;
  color: #8b8fa3;
  white-space: nowrap;
}

.status-label.active {
  color: #34d399;
  font-weight: 600;
}

.table-section {
  padding: 0;
  margin-bottom: 18px;
}

.table-card {
  border: none;
  background: transparent;
}

.process-tabs :deep(.el-tabs__header) {
  margin-bottom: 10px;
}

.process-tabs :deep(.el-tabs__item) {
  font-size: 13px;
  font-weight: 500;
  padding: 0 16px;
}

.process-tabs :deep(.el-tabs__item.is-active) {
  color: #6366f1;
  font-weight: 600;
}

:deep(.compact-table-row td) {
  padding: 10px 12px;
  font-size: 13px;
}

:deep(.el-table__body tr:hover > td) {
  background: rgba(99, 102, 241, 0.08);
}

.efficiency-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
}

.efficiency-value {
  font-weight: 600;
  color: #1f2937;
}

.efficiency-unit {
  font-size: 12px;
  color: #94a3b8;
}

.action-buttons-table {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.result-section {
  padding: 12px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-info {
  font-size: 13px;
  color: #5f6477;
  letter-spacing: 0.03em;
}

.process-info {
  margin-left: 6px;
  color: #6366f1;
  font-weight: 600;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.efficiency-dialog :deep(.el-dialog__header) {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
}

.efficiency-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.efficiency-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.form-grid .span-2 {
  grid-column: span 2;
}

@media (max-width: 600px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  .form-grid .span-2 {
    grid-column: span 1;
  }
}

.status-group :deep(.el-radio-group) {
  display: inline-flex;
  gap: 12px;
}

.remarks-item :deep(textarea) {
  min-height: 100px;
  border-radius: 12px;
}

.efficiency-dialog :deep(.el-input__wrapper),
.efficiency-dialog :deep(.el-textarea__inner),
.efficiency-dialog :deep(.el-select .el-input__wrapper) {
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.05);
}

.efficiency-dialog :deep(.el-input__wrapper.is-focus),
.efficiency-dialog :deep(.el-select .el-input__wrapper.is-focus),
.efficiency-dialog :deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

.efficiency-dialog :deep(.el-radio.is-checked .el-radio__label) {
  color: #4f46e5;
  font-weight: 600;
}

.table-section :deep(.el-table) {
  --el-table-border-color: rgba(226, 232, 240, 0.8);
}

.table-section :deep(.el-table__header) th {
  background: #f8f9fc;
  color: #475467;
  font-weight: 600;
}

.fade-in {
  animation: fadeUp 0.4s ease both;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  .header-stats {
    width: 100%;
    flex-wrap: wrap;
  }
  .filters-content {
    flex-direction: column;
  }
}
</style>
