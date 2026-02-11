<template>
  <div class="product-machine-config-container fade-in">
    <!-- 页面头部 -->
    <div class="page-header surface-card fade-card">
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

    <!-- 功能操作区域 -->
    <div class="action-section surface-card fade-card">
      <!-- 筛选标题 -->
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

      <!-- 筛选内容 -->
      <div class="filters-content">
        <div class="keyword-search">
          <el-input
            v-model="filters.keyword"
            placeholder="製品CDまたは製品名で検索"
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
        <el-table
          :data="filteredList"
          v-loading="loading"
          stripe
          border
          style="width: 100%"
          :empty-text="'データがありません'"
          :default-sort="{ prop: 'product_cd', order: 'ascending' }"
          height="calc(100vh - 320px)"
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

    <!-- 结果统计 -->
    <div class="result-section surface-card fade-card">
      <div class="result-info">
        表示件数: {{ filteredList.length }} / {{ configList?.length || 0 }}
      </div>
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
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 12px 16px 16px;
}

.surface-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(6px);
  transition: all 0.2s ease;
}

.surface-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.06);
}

.fade-card {
  animation: fadeUp 0.35s ease;
}

.page-header {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  padding: 16px 20px;
  margin-bottom: 12px;
  color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.title-section {
  flex: 1;
  min-width: 0;
}

.main-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px 0;
  letter-spacing: -0.02em;
}

.title-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  font-weight: 400;
}

.header-stats {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.stat-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  padding: 10px 14px;
  text-align: center;
  min-width: 70px;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-number {
  font-size: 20px;
  font-weight: 700;
  color: white;
  margin-bottom: 2px;
  line-height: 1.2;
}

.stat-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.95);
  letter-spacing: 0.03em;
  font-weight: 500;
}

.action-section {
  padding: 14px 18px;
  margin-bottom: 12px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.filter-icon {
  font-size: 16px;
  color: #6366f1;
}

.filter-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-actions .el-button {
  transition: all 0.2s ease;
  border-radius: 6px;
  font-size: 13px;
  padding: 6px 12px;
}

.filter-actions .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filters-content {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.keyword-search {
  flex: 1;
  min-width: 240px;
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
  margin-bottom: 12px;
}

.table-card {
  border: none;
  background: transparent;
  border-radius: 12px;
  overflow: hidden;
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

.result-section {
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafbfc;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
}

.result-info {
  font-size: 12px;
  color: #64748b;
  letter-spacing: 0.02em;
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.config-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.config-dialog :deep(.el-dialog__header) {
  padding: 18px 24px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  margin: 0;
}

.config-dialog :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  letter-spacing: 0.02em;
}

.config-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
  background: #ffffff;
  max-height: calc(90vh - 140px);
  overflow-y: auto;
}

.config-dialog :deep(.el-dialog__footer) {
  padding: 16px 24px;
  background: #fafbfc;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
  margin: 0;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 12px;
  padding: 16px 18px;
  transition: all 0.2s ease;
}

.form-section:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #475467;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 2px solid rgba(99, 102, 241, 0.15);
}

.section-title .el-icon {
  font-size: 16px;
  color: #6366f1;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 16px;
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
  gap: 10px;
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
  font-size: 13px;
}

.table-section :deep(.el-table__header) {
  background: #f8fafc;
}

.table-section :deep(.el-table__header th) {
  background: #f8fafc;
  color: #475467;
  font-weight: 600;
  font-size: 12px;
  padding: 10px 8px;
  border-bottom: 2px solid rgba(226, 232, 240, 0.8);
  text-transform: none;
  letter-spacing: 0.01em;
}

.table-section :deep(.el-table__body td) {
  padding: 10px 8px;
  font-size: 13px;
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
  padding: 40px 0;
}

.table-section :deep(.el-table__empty-text) {
  color: #94a3b8;
  font-size: 13px;
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
