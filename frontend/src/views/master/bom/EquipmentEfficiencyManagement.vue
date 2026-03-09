<template>
  <div class="ee-container">
    <!-- 页面头部 -->
    <div class="ee-header">
      <div class="ee-header-left">
        <div class="ee-title-row">
          <span class="ee-title-icon"><el-icon :size="20"><Tools /></el-icon></span>
          <h1 class="ee-title">設備能率管理</h1>
        </div>
        <p class="ee-subtitle">設備ごとの加工製品別能率設定・管理</p>
      </div>
      <div class="ee-stats">
        <div class="ee-stat" v-for="s in [
          { n: efficiencyList?.length || 0, l: '設定数' },
          { n: uniqueEquipmentCount, l: '設備数' },
          { n: uniqueProductCount, l: '製品数' }
        ]" :key="s.l">
          <span class="ee-stat-num">{{ s.n }}</span>
          <span class="ee-stat-lbl">{{ s.l }}</span>
        </div>
      </div>
    </div>

    <!-- 工具栏：搜索 + 操作 -->
    <div class="ee-toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="製品名・設備名で検索…"
        clearable
        @input="handleFilter"
        class="ee-search"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div class="ee-toolbar-actions">
        <el-button @click="clearFilters" :icon="Refresh" class="ee-btn-clear">クリア</el-button>
        <el-button type="primary" @click="openDialog()" :icon="Plus" class="ee-btn-add">
          <span class="btn-label">新規登録</span>
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="ee-table-wrap">
      <el-tabs v-model="activeProcessTab" @tab-change="handleTabChange" class="ee-tabs">
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
            size="small"
            style="width: 100%"
            :empty-text="'データがありません'"
            :default-sort="{ prop: 'machines_name', order: 'ascending' }"
            :row-class-name="getRowClassName"
            :header-cell-style="{ background: '#f0f2f8', color: '#374151', fontWeight: 600, fontSize: '11px', padding: '4px 8px', lineHeight: '1.3' }"
            :cell-style="{ padding: '2px 8px', fontSize: '12px', lineHeight: '1.4' }"
            height="calc(100vh - 260px)"
          >
            <el-table-column type="index" label="#" width="48" align="center" />
            <el-table-column prop="machine_cd" label="設備CD" width="90" align="center" sortable />
            <el-table-column prop="machines_name" label="設備名" min-width="120" sortable show-overflow-tooltip />
            <el-table-column prop="product_cd" label="製品CD" width="90" align="center" sortable />
            <el-table-column prop="product_name" label="製品名" min-width="130" sortable show-overflow-tooltip />
            <el-table-column prop="efficiency_rate" label="能率" width="80" align="center">
              <template #default="{ row }">
                <div class="ee-eff-cell">
                  <span class="ee-eff-val">{{ row.efficiency_rate?.toFixed(1) }}</span>
                  <span v-if="row.unit" class="ee-eff-unit">{{ row.unit }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="step_time" label="段取" width="65" align="center">
              <template #default="{ row }">
                <span v-if="row.step_time != null">{{ row.step_time }}<small class="ee-min">分</small></span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状態" width="85" align="center">
              <template #default="{ row }">
                <div class="ee-status-cell">
                  <el-switch
                    v-model="row.status"
                    :active-value="1"
                    :inactive-value="0"
                    :loading="statusUpdatingId === row.id"
                    @change="(value) => handleStatusChange(row, value)"
                    size="small"
                  />
                  <span class="ee-status-lbl" :class="{ on: row.status === 1 }">
                    {{ row.status === 1 ? '有効' : '無効' }}
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="備考" min-width="120" show-overflow-tooltip />
            <el-table-column label="操作" fixed="right" width="110" align="center">
              <template #default="{ row }">
                <div class="ee-row-actions">
                  <el-button size="small" type="primary" link @click="openDialog(row)" :icon="Edit">編集</el-button>
                  <el-button size="small" type="danger" link @click="handleDelete(row.id)" :icon="Delete">削除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <!-- 結果バー -->
      <div class="ee-result-bar">
        <span>表示: <b>{{ getFilteredListByProcess(activeProcessTab).length }}</b> / {{ efficiencyList?.length || 0 }}</span>
        <span v-if="activeProcessTab !== 'all'" class="ee-proc-tag">
          {{ processTypes.find((p) => p.value === activeProcessTab)?.label }}工程
        </span>
      </div>
    </div>

    <!-- ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '能率設定編集' : '能率設定新規登録'"
      width="580px"
      :close-on-click-modal="false"
      class="ee-dialog"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="110px"
        label-position="left"
        class="ee-form"
        size="default"
      >
        <div class="ee-form-section">
          <div class="ee-form-section-title">設備・製品</div>
          <el-form-item label="設備" prop="machine_cd">
            <el-select
              v-model="formData.machine_cd"
              placeholder="選択…"
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
          <el-form-item label="設備名">
            <el-input v-model="formData.machines_name" disabled />
          </el-form-item>
          <el-form-item label="製品" prop="product_cd">
            <el-select
              v-model="formData.product_cd"
              placeholder="選択…"
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
          <el-form-item label="製品名">
            <el-input v-model="formData.product_name" disabled />
          </el-form-item>
        </div>
        <div class="ee-form-section">
          <div class="ee-form-section-title">能率設定</div>
          <div class="ee-form-row">
            <el-form-item label="能率" prop="efficiency_rate" class="ee-form-half">
              <el-input-number
                v-model="formData.efficiency_rate"
                :min="0"
                :max="10000"
                :precision="1"
                :step="0.1"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="段取時間" prop="step_time" class="ee-form-half">
              <el-input-number
                v-model="formData.step_time"
                :min="0"
                :max="9999"
                :precision="0"
                style="width: 100%"
                placeholder="分"
              />
            </el-form-item>
          </div>
          <el-form-item label="状態" prop="status">
            <el-radio-group v-model="formData.status">
              <el-radio :label="1">有効</el-radio>
              <el-radio :label="0">無効</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="備考" prop="remarks">
            <el-input v-model="formData.remarks" type="textarea" :rows="2" placeholder="備考を入力…" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="ee-dialog-footer">
          <el-button @click="dialogVisible = false">キャンセル</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Tools, Refresh, Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
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

const getRowClassName = () => 'ee-row'

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
/* ===== Layout ===== */
.ee-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef1f5 50%, #e8ecf3 100%);
  padding: 12px 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-family: 'Inter', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ===== Header ===== */
.ee-header {
  background: linear-gradient(135deg, #5b5ea6 0%, #7c3aed 60%, #6d28d9 100%);
  border-radius: 12px;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: #fff;
  box-shadow: 0 4px 20px rgba(91, 94, 166, 0.3);
  animation: slideDown 0.35s ease;
}

.ee-header-left {
  flex: 1;
  min-width: 0;
}

.ee-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ee-title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  flex-shrink: 0;
}

.ee-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.01em;
}

.ee-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  margin: 3px 0 0 40px;
}

.ee-stats {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.ee-stat {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 8px 14px;
  text-align: center;
  min-width: 64px;
  transition: transform 0.2s, background 0.2s;
}

.ee-stat:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.22);
}

.ee-stat-num {
  display: block;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.1;
}

.ee-stat-lbl {
  display: block;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 2px;
  letter-spacing: 0.04em;
}

/* ===== Toolbar ===== */
.ee-toolbar {
  background: #fff;
  border-radius: 10px;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  animation: slideDown 0.4s ease;
}

.ee-search {
  flex: 1;
  max-width: 360px;
}

.ee-search :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #e5e7eb;
  height: 32px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ee-search :deep(.el-input__wrapper.is-focus) {
  border-color: #7c3aed;
  box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.12);
}

.ee-toolbar-actions {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.ee-btn-clear {
  --el-button-hover-bg-color: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 12px;
  height: 32px;
}

.ee-btn-add {
  border-radius: 8px;
  font-size: 12px;
  height: 32px;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border: none;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
  transition: transform 0.15s, box-shadow 0.15s;
}

.ee-btn-add:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
}

/* ===== Table Section ===== */
.ee-table-wrap {
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideDown 0.45s ease;
}

.ee-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.ee-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 14px;
  background: #fafbfc;
  border-bottom: 1px solid #eef0f4;
}

.ee-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: transparent;
}

.ee-tabs :deep(.el-tabs__item) {
  font-size: 12px;
  font-weight: 500;
  height: 36px;
  line-height: 36px;
  padding: 0 12px;
  color: #6b7280;
  transition: color 0.2s;
}

.ee-tabs :deep(.el-tabs__item.is-active) {
  color: #7c3aed;
  font-weight: 600;
}

.ee-tabs :deep(.el-tabs__active-bar) {
  background: #7c3aed;
  height: 2px;
  border-radius: 2px;
}

.ee-tabs :deep(.el-tabs__content) {
  flex: 1;
  padding: 0;
}

.ee-tabs :deep(.el-tab-pane) {
  height: 100%;
}

/* Table styles */
.ee-table-wrap :deep(.el-table) {
  --el-table-border-color: #e8eaf0;
  --el-table-row-hover-bg-color: rgba(124, 58, 237, 0.04);
  --el-table-header-bg-color: #f0f2f8;
  font-size: 12px;
}

.ee-table-wrap :deep(.el-table .el-table__cell) {
  padding: 2px 0;
}

.ee-table-wrap :deep(.el-table__header) th {
  background: #f0f2f8 !important;
  color: #374151;
  font-weight: 600;
  font-size: 11px;
  padding: 4px 8px;
  line-height: 1.3;
  border-bottom: 1.5px solid #dde0ea;
}

.ee-table-wrap :deep(.el-table__header) th .cell {
  padding: 0 4px;
  line-height: 1.4;
  white-space: nowrap;
}

.ee-table-wrap :deep(.el-table__body) td {
  padding: 2px 8px;
  line-height: 1.4;
  transition: background 0.15s;
}

.ee-table-wrap :deep(.el-table__body) td .cell {
  padding: 0 4px;
  line-height: 1.5;
}

.ee-table-wrap :deep(.el-table__body tr:hover > td) {
  background: rgba(124, 58, 237, 0.04) !important;
}

.ee-table-wrap :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #f8f9fc;
}

.ee-table-wrap :deep(.el-table--small td, .el-table--small th) {
  padding: 2px 0;
}

/* Cells */
.ee-eff-cell {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
}

.ee-eff-val {
  font-weight: 700;
  color: #1e293b;
  font-size: 12px;
}

.ee-eff-unit {
  font-size: 9px;
  color: #94a3b8;
}

.ee-min {
  font-size: 9px;
  color: #94a3b8;
  margin-left: 1px;
}

.ee-status-cell {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.ee-status-lbl {
  font-size: 10px;
  color: #9ca3af;
}

.ee-status-lbl.on {
  color: #10b981;
  font-weight: 600;
}

.ee-row-actions {
  display: flex;
  gap: 0;
  justify-content: center;
}

.ee-row-actions .el-button {
  font-size: 11px;
  padding: 1px 4px;
}

.ee-row-actions .el-button + .el-button {
  margin-left: 2px;
}

/* Result bar */
.ee-result-bar {
  padding: 6px 16px;
  font-size: 12px;
  color: #6b7280;
  background: #fafbfc;
  border-top: 1px solid #eef0f4;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ee-proc-tag {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  letter-spacing: 0.02em;
}

/* ===== Dialog ===== */
.ee-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.ee-dialog :deep(.el-dialog__header) {
  padding: 14px 20px;
  background: linear-gradient(135deg, #5b5ea6, #7c3aed);
  margin: 0;
}

.ee-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
}

.ee-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.ee-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.ee-dialog :deep(.el-dialog__body) {
  padding: 16px 20px;
  background: #fafbfc;
}

.ee-dialog :deep(.el-dialog__footer) {
  padding: 10px 20px 14px;
  border-top: 1px solid #eef0f4;
}

.ee-form {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.ee-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.ee-form :deep(.el-form-item__label) {
  font-size: 12px;
  color: #4b5563;
  font-weight: 500;
}

.ee-form-section {
  background: #fff;
  border-radius: 10px;
  padding: 12px 14px 4px;
  margin-bottom: 10px;
  border: 1px solid #eef0f4;
}

.ee-form-section-title {
  font-size: 12px;
  font-weight: 700;
  color: #7c3aed;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ee-form-section-title::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 14px;
  background: linear-gradient(180deg, #7c3aed, #a78bfa);
  border-radius: 2px;
}

.ee-form-row {
  display: flex;
  gap: 12px;
}

.ee-form-half {
  flex: 1;
}

.ee-form :deep(.el-input__wrapper),
.ee-form :deep(.el-textarea__inner),
.ee-form :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  box-shadow: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ee-form :deep(.el-input__wrapper.is-focus),
.ee-form :deep(.el-select .el-input__wrapper.is-focus),
.ee-form :deep(.el-textarea__inner:focus) {
  border-color: #7c3aed;
  box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.1);
}

.ee-form :deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f3f4f6;
  border-color: #e5e7eb;
}

.ee-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.ee-dialog-footer .el-button--primary {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
}

.ee-dialog-footer .el-button--primary:hover {
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
}

/* ===== Animations ===== */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .ee-container {
    padding: 8px 10px 16px;
  }
  .ee-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 12px 16px;
  }
  .ee-stats {
    width: 100%;
    flex-wrap: wrap;
  }
  .ee-stat {
    flex: 1;
    min-width: 56px;
  }
  .ee-toolbar {
    flex-wrap: wrap;
  }
  .ee-search {
    max-width: 100%;
    flex-basis: 100%;
  }
  .btn-label {
    display: none;
  }
  .ee-form-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
