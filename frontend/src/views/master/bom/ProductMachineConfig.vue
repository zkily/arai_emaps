<template>
  <div class="product-machine-config-container fade-in">
    <div class="page-header">
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
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ configList?.length || 0 }}</div>
            <div class="stat-label">登録数</div>
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
            type="success"
            @click="handleSync"
            :icon="Refresh"
            class="sync-btn"
            :loading="syncing"
          >
            製品情報同期
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
          />
          <el-table-column prop="product_name" label="製品名" min-width="130" sortable />
          <el-table-column prop="cutting_machine" label="切断機" width="120" align="center" />
          <el-table-column
            prop="chamfering_machine"
            label="面取機"
            width="120"
            align="center"
          />
          <el-table-column prop="sw_machine" label="sw機" width="120" align="center" />
          <el-table-column prop="molding_machine" label="成型機" width="120" align="center" />
          <el-table-column prop="plating_machine" label="メッキ治具" width="120" align="center" />
          <el-table-column prop="welding_machine" label="溶接機" width="120" align="center" />
          <el-table-column prop="inspector_machine" label="検査員" width="120" align="center" />
          <el-table-column
            prop="outsourced_plating_machine"
            label="外注メッキ先"
            width="140"
            align="center"
          />
          <el-table-column
            prop="outsourced_welding_machine"
            label="外注溶接先"
            width="140"
            align="center"
          />
          <el-table-column label="操作" fixed="right" width="140" align="center">
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
</style>
