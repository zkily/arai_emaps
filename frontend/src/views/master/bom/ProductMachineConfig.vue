<template>
  <div class="product-machine-config-container fade-in pmc-modern">
    <div class="page-header">
      <div class="page-header-fx" aria-hidden="true"><span class="fx-orb orb-a" /><span class="fx-orb orb-b" /><span class="fx-grid" /><span class="fx-sheen" /></div>
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Setting />
            </el-icon>
            製品加工設備設定
          </h1>
          <p class="subtitle">製品ごとの機器設定を管理します</p>
        </div>
        <div class="header-stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
          <div class="stat-card stat-total">
            <div class="stat-number">{{ configList?.length || 0 }}</div>
            <div class="stat-label">登録数</div>
          </div>
          <div class="stat-card stat-shown">
            <div class="stat-number">{{ filteredList.length }}</div>
            <div class="stat-label">表示中</div>
          </div>
          <div class="stat-card stat-weld">
            <div class="stat-number">{{ weldingConfiguredCount }}</div>
            <div class="stat-label">溶接設定</div>
          </div>
          <div class="stat-card stat-out">
            <div class="stat-number">{{ outsourcedCount }}</div>
            <div class="stat-label">外注設定</div>
          </div>
        </div>
      </div>
    </div>

    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・絞り込み</span>
          <div class="filter-inline-summary">
            <el-icon class="summary-icon"><InfoFilled /></el-icon>
            <span>表示 {{ filteredList.length }} / {{ configList?.length || 0 }} 件</span>
          </div>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">
            クリア
          </el-button>
          <el-button
            v-if="canEdit"
            type="success"
            @click="handleSync"
            :icon="Refresh"
            class="sync-btn"
            :loading="syncing"
          >
            製品情報同期
          </el-button>
          <el-button v-if="canCreate" type="primary" @click="openDialog()" :icon="Plus" class="add-btn">
            新規登録
          </el-button>
        </div>
      </div>

      <div class="filters-content">
        <div class="keyword-search">
          <el-input
            v-model="filters.keyword"
            placeholder="製品CD・製品名（リアルタイム絞り込み）"
            clearable
            size="default"
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

    <div class="table-section">
      <el-card class="table-card" shadow="never">
        <el-table
          :data="filteredList"
          v-loading="loading"
          stripe
          border
          size="small"
          style="width: 100%"
          :empty-text="'データがありません'"
          :default-sort="{ prop: 'product_cd', order: 'ascending' }"
          :header-cell-style="{ background: '#f5f7fa', fontWeight: 'bold' }"
          :cell-style="{ padding: '4px 8px' }"
          height="calc(100vh - 268px)"
        >
          <el-table-column
            prop="product_cd"
            label="製品CD"
            width="100"
            align="center"
            fixed="left"
          >
            <template #default="{ row }">
              <span class="code-chip">{{ row.product_cd }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_name" label="製品名" min-width="130" sortable />
          <el-table-column prop="cutting_machine" label="切断機" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.cutting_machine" class="mc-chip mc--cut">{{ row.cutting_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="chamfering_machine"
            label="面取機"
            width="120"
            align="center"
          >
            <template #default="{ row }">
              <span v-if="row.chamfering_machine" class="mc-chip mc--chamfer">{{ row.chamfering_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="sw_machine" label="sw機" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.sw_machine" class="mc-chip mc--sw">{{ row.sw_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="molding_machine" label="成型機" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.molding_machine" class="mc-chip mc--mold">{{ row.molding_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="plating_machine" label="メッキ治具" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.plating_machine" class="mc-chip mc--plating">{{ row.plating_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="welding_machine" label="溶接機" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.welding_machine" class="mc-chip mc--weld">{{ row.welding_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="inspector_machine" label="検査員" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.inspector_machine" class="mc-chip mc--insp">{{ row.inspector_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="outsourced_plating_machine"
            label="外注メッキ先"
            width="140"
            align="center"
          >
            <template #default="{ row }">
              <span v-if="row.outsourced_plating_machine" class="mc-chip mc--out">{{ row.outsourced_plating_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="outsourced_welding_machine"
            label="外注溶接先"
            width="140"
            align="center"
          >
            <template #default="{ row }">
              <span v-if="row.outsourced_welding_machine" class="mc-chip mc--out">{{ row.outsourced_welding_machine }}</span>
            </template>
          </el-table-column>
          <el-table-column v-if="canEdit || canDelete" label="操作" fixed="right" width="140" align="center">
            <template #default="{ row }">
              <div class="action-buttons-table">
                <el-button
                  v-if="canEdit"
                  size="small"
                  type="primary"
                  link
                  @click="openDialog(row)"
                  :icon="Edit"
                >
                  編集
                </el-button>
                <el-button
                  v-if="canDelete"
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
      </el-card>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '機器設定編集' : '機器設定新規登録'"
      width="900px"
      :close-on-click-modal="false"
      class="config-dialog"
      align-center
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        label-position="left"
        class="config-form"
        size="default"
      >
        <!-- 产品信息区域 -->
        <div class="form-section">
          <div class="section-title">
            <el-icon><Box /></el-icon>
            <span>製品情報</span>
          </div>
          <div class="form-grid">
            <el-form-item label="製品コード" prop="product_cd" class="span-2">
              <el-select
                v-model="formData.product_cd"
                placeholder="製品を選択"
                filterable
                style="width: 100%"
                :disabled="isEdit"
                @change="handleProductChange"
              >
                <el-option
                  v-for="product in availableProducts"
                  :key="product.product_cd"
                  :label="`${product.product_name} (${product.product_cd})`"
                  :value="product.product_cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="製品名" prop="product_name" class="span-2">
              <el-input v-model="formData.product_name" disabled />
            </el-form-item>
          </div>
        </div>

        <!-- 内部工程机器区域 -->
        <div class="form-section">
          <div class="section-title">
            <el-icon><Tools /></el-icon>
            <span>内部工程機器</span>
          </div>
          <div class="form-grid">
            <el-form-item label="切断機" prop="cutting_machine">
              <el-select
                v-model="formData.cutting_machine"
                placeholder="切断機を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="面取機" prop="chamfering_machine">
              <el-select
                v-model="formData.chamfering_machine"
                placeholder="面取機を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="sw機" prop="sw_machine">
              <el-select
                v-model="formData.sw_machine"
                placeholder="sw機を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="成型機" prop="molding_machine">
              <el-select
                v-model="formData.molding_machine"
                placeholder="成型機を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="メッキ治具" prop="plating_machine">
              <el-select
                v-model="formData.plating_machine"
                placeholder="メッキ治具を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="溶接機" prop="welding_machine">
              <el-select
                v-model="formData.welding_machine"
                placeholder="溶接機を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="検査員" prop="inspector_machine">
              <el-select
                v-model="formData.inspector_machine"
                placeholder="検査員を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
          </div>
        </div>

        <!-- 外注工程区域 -->
        <div class="form-section">
          <div class="section-title">
            <el-icon><OfficeBuilding /></el-icon>
            <span>外注工程</span>
          </div>
          <div class="form-grid">
            <el-form-item label="外注メッキ先" prop="outsourced_plating_machine">
              <el-select
                v-model="formData.outsourced_plating_machine"
                placeholder="外注メッキ先を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="外注溶接先" prop="outsourced_welding_machine">
              <el-select
                v-model="formData.outsourced_welding_machine"
                placeholder="外注溶接先を選択"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.value"
                  :label="machine.label"
                  :value="machine.value"
                />
              </el-select>
            </el-form-item>
          </div>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" size="default">キャンセル</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" size="default">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  Filter,
  Refresh,
  Plus,
  Search,
  Edit,
  Delete,
  Box,
  Tools,
  OfficeBuilding,
  InfoFilled,
} from '@element-plus/icons-vue'
import {
  fetchProductMachineConfigList,
  createProductMachineConfig,
  updateProductMachineConfig,
  deleteProductMachineConfig,
  syncProducts,
  fetchAvailableProducts,
  type ProductMachineConfig,
  type AvailableProduct,
} from '@/api/master/productMachineConfigMaster'
import { fetchMachines } from '@/api/master/machineMaster'
import type { FormInstance, FormRules } from 'element-plus'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

// 数据状态
const configList = ref<ProductMachineConfig[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const syncing = ref(false)
const availableProducts = ref<AvailableProduct[]>([])
const machineOptions = ref<Array<{ label: string; value: string }>>([])

// 统一处理不同接口返回结构
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

// 表单数据
const formData = ref<Partial<ProductMachineConfig>>({
  product_cd: '',
  product_name: '',
  cutting_machine: '',
  chamfering_machine: '',
  sw_machine: '',
  molding_machine: '',
  plating_machine: '',
  welding_machine: '',
  inspector_machine: '',
  outsourced_plating_machine: '',
  outsourced_welding_machine: '',
})

// 表单验证规则
const formRules: FormRules = {
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
}

// 筛选状态
const filters = ref({
  keyword: '',
})

// 筛选后的列表
const filteredList = computed(() => {
  let result = configList.value || []

  // 按关键词筛选（产品代码或产品名）
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase().trim()
    result = result.filter((item) => {
      const productCd = (item.product_cd || '').toLowerCase()
      const productName = (item.product_name || '').toLowerCase()
      return productCd.includes(keyword) || productName.includes(keyword)
    })
  }

  return result
})

const weldingConfiguredCount = computed(
  () => (configList.value || []).filter((item) => !!item.welding_machine).length,
)
const outsourcedCount = computed(
  () =>
    (configList.value || []).filter(
      (item) => !!item.outsourced_plating_machine || !!item.outsourced_welding_machine,
    ).length,
)

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 14).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 14).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

// 产品选择变化处理
const handleProductChange = (value: string) => {
  const product = availableProducts.value.find((p) => p.product_cd === value)
  if (product) {
    formData.value.product_name = product.product_name
  }
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const result = (await fetchProductMachineConfigList({ limit: 99999 })) as any
    // 处理响应结构：可能是 {list: [], total: number} 或 {success: true, data: {list: [], total: number}}
    if (result.success && result.data) {
      configList.value = result.data.list || []
    } else if (result.list) {
      configList.value = result.list || []
    } else if (Array.isArray(result)) {
      configList.value = result
    } else {
      configList.value = []
    }
  } catch (error) {
    console.error('機器設定データの読み込みに失敗:', error)
    ElMessage.error('機器設定データの読み込みに失敗しました')
    configList.value = []
  } finally {
    loading.value = false
  }
}

// 加载可用产品列表
const loadAvailableProducts = async () => {
  try {
    const result = (await fetchAvailableProducts()) as any
    // 处理响应结构：可能是数组或 {success: true, data: [...]}
    if (result.success && result.data) {
      availableProducts.value = result.data || []
    } else if (Array.isArray(result)) {
      availableProducts.value = result
    } else {
      availableProducts.value = []
    }
  } catch (error) {
    console.error('製品データの読み込みに失敗:', error)
    ElMessage.error('製品データの読み込みに失敗しました')
    availableProducts.value = []
  }
}

// 加载机器选项
const loadMachineOptions = async () => {
  try {
    const result = (await fetchMachines()) as any
    const machineList = extractList(result)
    machineOptions.value = machineList.map((machine: any) => ({
      label: `${machine.machine_name || ''} (${machine.machine_cd || ''})`,
      value: machine.machine_cd || '',
    }))
  } catch (error) {
    console.error('機器データの読み込みに失敗:', error)
    ElMessage.error('機器データの読み込みに失敗しました')
    machineOptions.value = []
  }
}

// 打开对话框
const openDialog = (row?: ProductMachineConfig) => {
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  isEdit.value = !!row
  if (row) {
    formData.value = { ...row }
  } else {
    formData.value = {
      product_cd: '',
      product_name: '',
      cutting_machine: '',
      chamfering_machine: '',
      sw_machine: '',
      molding_machine: '',
      plating_machine: '',
      welding_machine: '',
      inspector_machine: '',
      outsourced_plating_machine: '',
      outsourced_welding_machine: '',
    }
  }
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (isEdit.value ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value && formData.value.id) {
        await updateProductMachineConfig(formData.value.id, formData.value)
        ElMessage.success('機器設定を更新しました')
      } else {
        await createProductMachineConfig(formData.value)
        ElMessage.success('機器設定を登録しました')
      }
      dialogVisible.value = false
      await loadData()
    } catch (error: any) {
      console.error('保存に失敗:', error)
      const errorMessage =
        error?.response?.data?.message || error?.message || '保存に失敗しました'
      ElMessage.error(errorMessage)
    } finally {
      submitting.value = false
    }
  })
}

// 删除处理
const handleDelete = async (id?: number) => {
  if (!guardMasterOperation(canDelete)) return
  if (!id) return

  try {
    await ElMessageBox.confirm('この機器設定を削除しますか？', '確認', {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
    await deleteProductMachineConfig(id)
    ElMessage.success('機器設定を削除しました')
    await loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('削除に失敗:', error)
      ElMessage.error('削除に失敗しました')
    }
  }
}

// 同步产品数据
const handleSync = async () => {
  if (!guardMasterOperation(canEdit)) return
  syncing.value = true
  try {
    const result = (await syncProducts()) as any
    // 响应拦截器返回完整响应对象，所以需要访问result.data
    const added = result?.data?.added ?? 0
    const updated = result?.data?.updated ?? 0
    const total = result?.data?.total ?? 0

    if (result?.success !== false && (added > 0 || updated > 0 || total > 0)) {
      ElMessage.success(`同期完了: 新規追加 ${added}件、更新 ${updated}件`)
      await loadData()
    } else if (result?.success === true && total === 0) {
      ElMessage.success('同期完了: 更新するデータがありませんでした')
      await loadData()
    } else {
      ElMessage.error('同期に失敗しました')
    }
  } catch (error: any) {
    console.error('同期に失敗:', error)
    const errorMessage =
      error?.response?.data?.message || error?.message || '同期に失敗しました'
    ElMessage.error(errorMessage)
  } finally {
    syncing.value = false
  }
}

// 筛选处理
const handleFilter = () => {
  // 筛选逻辑已通过computed属性实现
}

// 清除筛选
const clearFilters = () => {
  filters.value = {
    keyword: '',
  }
}

// 初始化
onMounted(async () => {
  await Promise.all([loadData(), loadAvailableProducts(), loadMachineOptions()])
})
</script>

<style scoped>
.product-machine-config-container {
  min-height: 100%;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  padding: 6px 8px 10px;
  box-sizing: border-box;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 10px 14px;
  margin-bottom: 8px;
  color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.28);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.title-section {
  flex: 1;
  min-width: 0;
}

.main-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0 0 2px 0;
  letter-spacing: -0.02em;
}

.title-icon {
  font-size: 1.35rem;
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.95);
}

.subtitle {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.88);
  margin: 0;
  line-height: 1.35;
}

.header-stats {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  padding: 6px 12px;
  text-align: center;
  min-width: 64px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.26);
}

.stat-number {
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
  line-height: 1.1;
}

.stat-label {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.92);
  letter-spacing: 0.04em;
  font-weight: 600;
  margin-top: 2px;
}

.action-section {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 8px 12px 10px;
  margin-bottom: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
  font-size: 0.88rem;
  font-weight: 600;
  color: #334155;
  min-width: 0;
}

.filter-icon {
  font-size: 15px;
  color: #667eea;
  flex-shrink: 0;
}

.filter-inline-summary {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding-left: 10px;
  margin-left: 4px;
  border-left: 1px solid #e2e8f0;
  font-size: 0.78rem;
  font-weight: 500;
  color: #64748b;
}

.summary-icon {
  color: #667eea;
  font-size: 14px;
}

.filter-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-actions .el-button {
  border-radius: 8px;
  font-size: 12px;
  padding: 6px 11px;
}

.filters-content {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.keyword-search {
  flex: 1;
  min-width: 200px;
}

.keyword-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid rgba(203, 213, 225, 0.8);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: all 0.2s ease;
  background: #ffffff;
}

.keyword-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(99, 102, 241, 0.4);
}

.keyword-input :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.table-section {
  padding: 0;
  margin-bottom: 0;
}

.table-card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.action-buttons-table {
  display: flex;
  gap: 4px;
  justify-content: center;
  align-items: center;
}

.action-buttons-table .el-button {
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.action-buttons-table .el-button:hover {
  transform: translateY(-1px);
}

.config-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.config-dialog :deep(.el-dialog__header) {
  padding: 12px 18px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.08));
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  margin: 0;
}

.config-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  letter-spacing: 0.02em;
}

.config-dialog :deep(.el-dialog__body) {
  padding: 12px 18px;
  background: #ffffff;
  max-height: calc(90vh - 120px);
  overflow-y: auto;
}

.config-dialog :deep(.el-dialog__footer) {
  padding: 10px 18px 12px;
  background: #fafbfc;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
  margin: 0;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-section {
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 10px;
  padding: 10px 12px;
  transition: border-color 0.2s ease;
}

.form-section:hover {
  border-color: rgba(99, 102, 241, 0.28);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #475467;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(99, 102, 241, 0.18);
}

.section-title .el-icon {
  font-size: 16px;
  color: #6366f1;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 12px;
}

.form-grid .span-2 {
  grid-column: span 2;
}

.config-dialog :deep(.el-form-item) {
  margin-bottom: 0;
}

.config-dialog :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: #475467;
  padding-bottom: 6px;
  line-height: 1.4;
}

.config-dialog :deep(.el-input__wrapper),
.config-dialog :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid rgba(203, 213, 225, 0.8);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: all 0.2s ease;
  background: #ffffff;
}

.config-dialog :deep(.el-input__wrapper:hover),
.config-dialog :deep(.el-select .el-input__wrapper:hover) {
  border-color: rgba(99, 102, 241, 0.4);
}

.config-dialog :deep(.el-input__wrapper.is-focus),
.config-dialog :deep(.el-select .el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.config-dialog :deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f8fafc;
  border-color: rgba(203, 213, 225, 0.6);
}

.config-dialog :deep(.el-select-dropdown) {
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.config-dialog :deep(.el-select-dropdown__item) {
  padding: 8px 12px;
  font-size: 13px;
}

.config-dialog :deep(.el-select-dropdown__item:hover) {
  background-color: rgba(99, 102, 241, 0.08);
}

.config-dialog :deep(.el-select-dropdown__item.is-selected) {
  background-color: rgba(99, 102, 241, 0.12);
  color: #6366f1;
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.dialog-footer .el-button {
  min-width: 90px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.dialog-footer .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

@media (max-width: 600px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-grid .span-2 {
    grid-column: span 1;
  }
}

.table-section :deep(.el-table) {
  --el-table-border-color: rgba(226, 232, 240, 0.6);
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: rgba(99, 102, 241, 0.04);
  font-size: 12px;
}

.table-section :deep(.el-table__header) {
  background: #f8fafc;
}

.table-section :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
  color: #475467;
  font-weight: 600;
  font-size: 11px;
  padding: 6px 6px !important;
  border-bottom: 1px solid #e2e8f0;
  text-transform: none;
  letter-spacing: 0.01em;
}

.table-section :deep(.el-table__body td) {
  padding: 5px 6px !important;
  font-size: 12px;
  color: #334155;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
}

.table-section :deep(.el-table__row) {
  transition: all 0.15s ease;
}

.table-section :deep(.el-table__row:hover) {
  background-color: rgba(99, 102, 241, 0.04);
}

.table-section :deep(.el-table__row:hover td) {
  background-color: transparent;
}

.table-section :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #fafbfc;
}

.table-section :deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover td) {
  background-color: rgba(99, 102, 241, 0.04);
}

.table-section :deep(.el-table__empty-block) {
  padding: 24px 0;
}

.table-section :deep(.el-table__empty-text) {
  color: #94a3b8;
  font-size: 12px;
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

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（製品加工設備設定 / teal→aqua→mint）
 * ============================================================ */
.pmc-modern {
  --hx-1: #042f2e;
  --hx-2: #115e59;
  --hx-3: #0d9488;
  --hx-4: #2dd4bf;
  --hx-deep: #134e4a;
  --hx-soft: #f0fdfa;
  --hx-line: rgba(13, 148, 136, 0.18);
  background:
    radial-gradient(1100px 360px at 10% -10%, rgba(45, 212, 191, 0.12), transparent 60%),
    radial-gradient(900px 320px at 100% 0%, rgba(14, 165, 233, 0.07), transparent 60%),
    linear-gradient(160deg, #f3fbf9 0%, #eefaf7 40%, #f8fafc 100%);
}

.pmc-modern .page-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 12px 16px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 38%, var(--hx-3) 72%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px rgba(17, 94, 89, 0.6),
    0 6px 14px -6px rgba(45, 212, 191, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.pmc-modern .header-content {
  position: relative;
  z-index: 1;
}

.pmc-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.pmc-modern .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(22px);
  opacity: 0.55;
  animation: pmcOrbFloat 11s ease-in-out infinite;
}

.pmc-modern .fx-orb.orb-a {
  width: 220px;
  height: 220px;
  top: -100px;
  left: 26%;
  background: radial-gradient(circle, rgba(94, 234, 212, 0.7), transparent 70%);
}

.pmc-modern .fx-orb.orb-b {
  width: 180px;
  height: 180px;
  bottom: -90px;
  right: 14%;
  background: radial-gradient(circle, rgba(125, 211, 252, 0.55), transparent 70%);
  animation-delay: -5s;
}

.pmc-modern .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse at 30% 50%, #000 20%, transparent 75%);
}

.pmc-modern .fx-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 30%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.16), transparent);
  transform: skewX(-18deg);
  animation: pmcSheen 7s ease-in-out infinite;
}

.pmc-modern .main-title {
  gap: 10px;
  text-shadow: 0 2px 10px rgba(4, 47, 46, 0.35);
}

.pmc-modern .title-icon {
  width: 40px;
  height: 40px;
  padding: 9px;
  box-sizing: border-box;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 4px 0 rgba(4, 47, 46, 0.5),
    0 10px 18px -6px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  animation: pmcIconFloat 6s ease-in-out infinite;
}

.pmc-modern .title-icon :deep(svg) {
  animation: pmcIconGear 8s linear infinite;
}

.pmc-modern .header-stats {
  perspective: 650px;
  flex-wrap: wrap;
}

.pmc-modern .stat-card {
  --sc: #99f6e4;
  position: relative;
  overflow: hidden;
  min-width: 70px;
  border-radius: 12px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow:
    0 3px 0 rgba(4, 47, 46, 0.4),
    0 10px 20px -10px rgba(0, 0, 0, 0.45);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition: transform 0.18s ease-out, box-shadow 0.25s ease;
}

.pmc-modern .stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: var(--sc);
}

.pmc-modern .stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(255, 255, 255, 0.35), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.pmc-modern .stat-card:hover {
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0.1));
  box-shadow:
    0 5px 0 rgba(4, 47, 46, 0.45),
    0 16px 26px -12px rgba(0, 0, 0, 0.5);
}

.pmc-modern .stat-card:hover::after {
  opacity: 1;
}

.pmc-modern .stat-total { --sc: #fde68a; }
.pmc-modern .stat-shown { --sc: #99f6e4; }
.pmc-modern .stat-weld { --sc: #fca5a5; }
.pmc-modern .stat-out { --sc: #c4b5fd; }

.pmc-modern .stat-number {
  font-variant-numeric: tabular-nums;
  transform: translateZ(14px);
  text-shadow: 0 2px 6px rgba(4, 47, 46, 0.35);
}

.pmc-modern .action-section,
.pmc-modern .table-card {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--hx-line);
  box-shadow:
    0 10px 24px -16px rgba(17, 94, 89, 0.35),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.pmc-modern .action-section::before,
.pmc-modern .table-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, var(--hx-2), var(--hx-3), var(--hx-4), #7dd3fc);
}

.pmc-modern .action-section {
  padding-top: 11px;
}

.pmc-modern .table-card {
  padding-top: 3px;
}

.pmc-modern .filter-icon,
.pmc-modern .summary-icon {
  color: var(--hx-3);
}

.pmc-modern .filter-inline-summary {
  padding: 2px 10px;
  border-left: none;
  border-radius: 999px;
  color: var(--hx-deep);
  background: var(--hx-soft);
  border: 1px solid rgba(13, 148, 136, 0.2);
}

.pmc-modern .keyword-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--hx-3);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.14);
}

.pmc-modern .clear-btn {
  color: var(--hx-deep);
  background: var(--hx-soft);
  border: 1px solid rgba(13, 148, 136, 0.2);
  box-shadow: 0 2px 0 rgba(13, 148, 136, 0.2);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.pmc-modern .clear-btn:hover {
  transform: translateY(-1px);
  color: var(--hx-deep);
  background: #ccfbf1;
  box-shadow: 0 3px 0 rgba(13, 148, 136, 0.26);
}

.pmc-modern .sync-btn,
.pmc-modern .add-btn {
  border: none;
  font-weight: 700;
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.pmc-modern .sync-btn {
  --k-edge: #1e40af;
  --k-glow: rgba(59, 130, 246, 0.5);
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}

.pmc-modern .add-btn {
  --k-edge: #115e59;
  --k-glow: rgba(13, 148, 136, 0.5);
  background: linear-gradient(135deg, #2dd4bf, #0d9488);
}

.pmc-modern .sync-btn:hover {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}

.pmc-modern .add-btn:hover {
  background: linear-gradient(135deg, #2dd4bf, #0d9488);
}

.pmc-modern .sync-btn:hover,
.pmc-modern .add-btn:hover {
  transform: translateY(-2px);
  filter: brightness(1.06);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.pmc-modern .sync-btn:active,
.pmc-modern .add-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--k-edge);
}

.pmc-modern .table-section :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #134e4a, #115e59) !important;
  color: #fff !important;
  border-bottom: 2px solid var(--hx-4) !important;
}

.pmc-modern .table-section :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #f0fdfa !important;
}

.pmc-modern .table-section :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-3);
}

.pmc-modern .code-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 7px;
  font-family: 'Consolas', monospace;
  font-weight: 700;
  font-size: 11px;
  color: var(--hx-deep);
  background: linear-gradient(135deg, #f0fdfa, #ccfbf1);
  box-shadow: inset 0 0 0 1px rgba(13, 148, 136, 0.3), 0 2px 0 rgba(13, 148, 136, 0.2);
  transition: transform 0.15s ease;
}

.pmc-modern .table-section :deep(tr:hover) .code-chip {
  transform: translateY(-1px);
}

.pmc-modern .mc-chip {
  --mc: #64748b;
  display: inline-block;
  max-width: 100%;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
  color: var(--mc);
  background: color-mix(in srgb, var(--mc) 9%, #fff);
  border: 1px solid color-mix(in srgb, var(--mc) 32%, #fff);
}

.pmc-modern .mc--cut { --mc: #2563eb; }
.pmc-modern .mc--chamfer { --mc: #0891b2; }
.pmc-modern .mc--sw { --mc: #7c3aed; }
.pmc-modern .mc--mold { --mc: #059669; }
.pmc-modern .mc--plating { --mc: #ca8a04; }
.pmc-modern .mc--weld { --mc: #dc2626; }
.pmc-modern .mc--insp { --mc: #db2777; }
.pmc-modern .mc--out { --mc: #475569; }

.pmc-modern .action-buttons-table .el-button--primary:hover {
  background: rgba(37, 99, 235, 0.08);
}

.pmc-modern .action-buttons-table .el-button--danger:hover {
  background: rgba(220, 38, 38, 0.08);
}

@keyframes pmcOrbFloat {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(26px, 14px) scale(1.12);
  }
}

@keyframes pmcSheen {
  0% {
    left: -40%;
  }
  60%,
  100% {
    left: 130%;
  }
}

@keyframes pmcIconFloat {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg);
  }
  50% {
    transform: perspective(300px) rotateX(12deg) rotateY(-14deg);
  }
}

@keyframes pmcIconGear {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .pmc-modern .fx-orb,
  .pmc-modern .fx-sheen,
  .pmc-modern .title-icon,
  .pmc-modern .title-icon :deep(svg) {
    animation: none;
  }

  .pmc-modern .stat-card {
    transform: none;
  }
}
</style>
