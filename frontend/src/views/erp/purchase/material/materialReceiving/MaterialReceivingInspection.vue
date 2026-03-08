<template>
  <div class="inspection-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <View />
            </el-icon>
            材料受入検品管理
          </h1>
          <p class="subtitle">材料の品質検査・検品作業を管理します</p>
        </div>
      </div>
    </div>

    <!-- 功能タブ -->
    <div class="tabs-section">
      <el-tabs v-model="activeTab" class="modern-tabs" @tab-change="handleTabChange">
        <el-tab-pane label="検品履歴" name="history">
          <template #label>
            <span class="tab-label">
              <el-icon><Document /></el-icon>
              検品履歴
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="品質基準設定" name="standards">
          <template #label>
            <span class="tab-label">
              <el-icon><Setting /></el-icon>
              品質基準設定
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 检品履歴 -->
    <div v-if="activeTab === 'history'" class="content-section">
      <el-card class="history-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">📊 検品履歴</span>
            <div class="header-actions">
              <div class="filter-controls">
                <el-select
                  v-model="selectedSupplier"
                  placeholder="仕入先を選択"
                  clearable
                  multiple
                  collapse-tags
                  collapse-tags-tooltip
                  size="small"
                  style="width: 180px"
                  @change="handleSupplierFilter"
                >
                  <el-option
                    v-for="supplier in supplierOptions"
                    :key="supplier.value"
                    :label="supplier.label"
                    :value="supplier.value"
                  />
                </el-select>
                <el-date-picker
                  v-model="historyDateRange"
                  type="daterange"
                  range-separator="～"
                  start-placeholder="開始日"
                  end-placeholder="終了日"
                  format="YYYY/MM/DD"
                  value-format="YYYY-MM-DD"
                  @change="filterHistory"
                  size="small"
                  style="width: 220px"
                />
                <el-button
                  type="primary"
                  size="small"
                  @click="printInspectionHistory"
                  :icon="Printer"
                >
                  印刷
                </el-button>
              </div>
            </div>
          </div>
        </template>

        <el-table
          :data="filteredInspectionHistory"
          stripe
          class="modern-table"
          :height="tableHeight"
        >
          <el-table-column prop="inspection_date" label="検品日" width="100" align="center">
            <template #default="{ row }">
              <span>{{ formatDate(row.inspection_date) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="log_time" label="時間" width="80" align="center">
            <template #default="{ row }">
              <span>{{ row.log_time || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="material_name" label="材料名" width="160" align="center">
            <template #default="{ row }">
              <span class="material-name">{{ row.material_name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="supplier" label="仕入先" width="120" align="center">
            <template #default="{ row }">
              <span>{{ row.supplier || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="manufacture_no" label="製造番号" width="150" align="center">
            <template #default="{ row }">
              <span>{{ row.manufacture_no || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" align="center">
            <template #default="{ row }">
              <span>{{ row.quantity || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="outer_diameter1" label="外径1" width="80" align="center">
            <template #default="{ row }">
              <span>{{ row.outer_diameter1 || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="outer_diameter2" label="外径2" width="80" align="center">
            <template #default="{ row }">
              <span>{{ row.outer_diameter2 || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="inspector_name" label="検品者" width="100" align="center">
            <template #default="{ row }">
              <span class="inspector-name">{{ row.inspector_name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="100" align="center">
            <template #default="{ row }">
              <el-button size="small" type="info" link @click="viewInspectionDetail(row)"
                >詳細</el-button
              >
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页组件 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalRecords"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 品質基準設定 -->
    <div v-if="activeTab === 'standards'" class="content-section">
      <el-card class="standards-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">⚖️ 品質基準設定</span>
            <div class="header-actions">
              <div class="filter-controls">
                <el-select
                  v-model="selectedMaterialName"
                  placeholder="材料名を検索・選択"
                  clearable
                  filterable
                  size="small"
                  style="width: 220px"
                  @change="handleMaterialNameFilter"
                >
                  <el-option
                    v-for="materialName in materialNameOptions"
                    :key="materialName"
                    :label="materialName"
                    :value="materialName"
                  />
                </el-select>
              </div>
            </div>
          </div>
        </template>

        <el-table
          :data="filteredQualityStandards"
          stripe
          class="modern-table quality-standards-table"
          v-loading="loading"
          :height="tableHeight"
        >
          <el-table-column
            prop="material_name"
            label="材料名"
            width="150"
            show-overflow-tooltip
            sortable
          />
          <el-table-column
            prop="standard_spec"
            label="材料規格"
            width="100"
            show-overflow-tooltip
          />
          <el-table-column
            prop="supplier_name"
            label="仕入先"
            width="110"
            align="center"
            sortable
          />
          <el-table-column prop="tolerance_range" label="許容範囲" width="90" align="center" />
          <el-table-column prop="tolerance_1" label="許容値1" width="90" align="center" />
          <el-table-column prop="tolerance_2" label="許容値2" width="90" align="center" />
          <el-table-column prop="range_value" label="範囲値" width="130" align="center" />
          <el-table-column prop="min_value" label="最小値" width="90" align="center" />
          <el-table-column prop="max_value" label="最大値" width="90" align="center" />
          <el-table-column prop="actual_value_1" label="実測値1" width="90" align="center" />
          <el-table-column prop="actual_value_2" label="実測値2" width="90" align="center" />
          <el-table-column prop="actual_value_3" label="実測値3" width="90" align="center" />
          <el-table-column
            prop="representative_model"
            label="代表品種"
            width="120"
            align="center"
          />
          <el-table-column prop="status" label="状態" width="80" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.status"
                :active-value="1"
                :inactive-value="0"
                inline-prompt
                active-text="有効"
                inactive-text="無効"
                @change="updateStandardStatus(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="80" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="editStandard(row)"
                >編集</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 品質基準編集ダイアログ -->
    <el-dialog
      v-model="editDialogVisible"
      title="品質基準編集"
      width="800px"
      class="edit-dialog"
      :close-on-click-modal="false"
    >
      <div v-if="editingStandard" class="edit-form">
        <!-- 材料情報表示 -->
        <div class="material-info-section">
          <h4 class="section-title">材料情報</h4>
          <div class="info-display">
            <div class="info-item">
              <label>材料名:</label>
              <span>{{ editingStandard.material_name }}</span>
            </div>
            <div class="info-item">
              <label>標準仕様:</label>
              <span>{{ editingStandard.standard_spec }}</span>
            </div>
            <div class="info-item">
              <label>仕入先:</label>
              <span>{{ editingStandard.supplier_name }}</span>
            </div>
          </div>
        </div>

        <!-- 編集フォーム -->
        <div class="edit-form-section">
          <h4 class="section-title">品質基準編集</h4>
          <el-form
            ref="editFormRef"
            :model="editForm"
            :rules="editFormRules"
            label-width="120px"
            class="edit-form-content"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="許容範囲" prop="tolerance_range">
                  <el-input v-model="editForm.tolerance_range" placeholder="例: ±0.1" clearable />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="範囲値" prop="range_value">
                  <el-input v-model="editForm.range_value" placeholder="範囲値を入力" clearable />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="許容値1" prop="tolerance_1">
                  <el-input-number
                    v-model="editForm.tolerance_1"
                    :precision="3"
                    :step="0.1"
                    placeholder="許容値1"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="許容値2" prop="tolerance_2">
                  <el-input-number
                    v-model="editForm.tolerance_2"
                    :precision="3"
                    :step="0.1"
                    placeholder="許容値2"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="最小値" prop="min_value">
                  <el-input-number
                    v-model="editForm.min_value"
                    :precision="3"
                    :step="0.1"
                    placeholder="最小値"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最大値" prop="max_value">
                  <el-input-number
                    v-model="editForm.max_value"
                    :precision="3"
                    :step="0.1"
                    placeholder="最大値"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="実測値1" prop="actual_value_1">
                  <el-input
                    v-model="editForm.actual_value_1"
                    placeholder="実測値1"
                    style="width: 120px"
                    maxlength="10"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="実測値2" prop="actual_value_2">
                  <el-input
                    v-model="editForm.actual_value_2"
                    placeholder="実測値2"
                    style="width: 120px"
                    maxlength="10"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="実測値3" prop="actual_value_3">
                  <el-input
                    v-model="editForm.actual_value_3"
                    placeholder="実測値3"
                    style="width: 120px"
                    maxlength="10"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row>
              <el-col :span="24">
                <el-form-item label="代表モデル" prop="representative_model">
                  <el-input
                    v-model="editForm.representative_model"
                    placeholder="代表モデルを入力"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelEdit">キャンセル</el-button>
          <el-button type="primary" @click="saveEdit" :loading="saving"> 保存 </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 検品詳細ダイアログ -->
    <el-dialog
      v-model="inspectionDetailVisible"
      title="検品詳細情報"
      width="800px"
      class="detail-dialog"
    >
      <div v-if="selectedInspectionDetail" class="inspection-detail">
        <!-- 詳細内容会在这里显示 -->
        <div class="detail-sections">
          <div class="basic-info">
            <h4>基本情報</h4>
            <!-- 基本信息内容 -->
          </div>
          <div class="inspection-results">
            <h4>検品結果</h4>
            <!-- 检品结果内容 -->
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="inspectionDetailVisible = false">閉じる</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Document, Setting, Printer } from '@element-plus/icons-vue'
import request from '@/shared/api/request'
import { getMaterialLogs, getSupplierList } from '@/api/material'

// 接口类型定义

interface QualityStandard {
  id: number
  material_cd: string
  material_name: string
  material_type?: string
  standard_spec: string
  unit?: string
  diameter?: number | null
  thickness?: number | null
  length?: number | null
  supply_classification?: string
  pieces_per_bundle?: number | null
  usegae?: string
  supplier_cd?: string
  supplier_name: string
  unit_price?: number | null
  long_weight?: number | null
  single_price?: number | null
  safety_stock?: number | null
  lead_time?: number | null
  storage_location?: string
  note?: string
  tolerance_range: string
  tolerance_1: number | null
  tolerance_2: number | null
  range_value: string | number | null
  min_value: number | null
  max_value: number | null
  actual_value_1: string | number | null
  actual_value_2: string | number | null
  actual_value_3: string | number | null
  representative_model: string
  status: number
}

// 数据状态
const activeTab = ref('history')
const loading = ref(false)
const saving = ref(false)
const historyDateRange = ref<string[]>([])
const inspectionDetailVisible = ref(false)
const selectedInspectionDetail = ref<any>(null)

// 计算表格高度，使布局更紧凑
const tableHeight = computed(() => {
  return window.innerHeight - 320
})

// 获取唯一的材料名列表（用于筛选）
const materialNameOptions = computed(() => {
  const names = qualityStandards.value
    .map((item) => item.material_name)
    .filter((name) => name && name.trim() !== '')
  return Array.from(new Set(names)).sort()
})

// 根据材料名筛选品质基準
const filteredQualityStandards = computed(() => {
  if (!selectedMaterialName.value || selectedMaterialName.value === '') {
    return qualityStandards.value
  }
  return qualityStandards.value.filter((item) => item.material_name === selectedMaterialName.value)
})

// 検品履歴筛选相关
const selectedSupplier = ref<string[]>([])
const supplierOptions = ref<{ label: string; value: string }[]>([])
const filteredInspectionHistory = ref<any[]>([])

// 分页相关
const currentPage = ref<number>(1)
const pageSize = ref<number>(20)
const totalRecords = ref<number>(0)

// 編集ダイアログ関連
const editDialogVisible = ref(false)
const editingStandard = ref<QualityStandard | null>(null)
const editFormRef = ref()
const editForm = ref({
  tolerance_range: '',
  tolerance_1: null as number | null,
  tolerance_2: null as number | null,
  range_value: '',
  min_value: null as number | null,
  max_value: null as number | null,
  actual_value_1: '',
  actual_value_2: '',
  actual_value_3: '',
  representative_model: '',
})

// フォームバリデーションルール
const editFormRules = {
  tolerance_range: [{ required: false, message: '許容範囲を入力してください', trigger: 'blur' }],
  range_value: [{ required: false, message: '範囲値を入力してください', trigger: 'blur' }],
  tolerance_1: [{ required: false, message: '許容値1を入力してください', trigger: 'blur' }],
  tolerance_2: [{ required: false, message: '許容値2を入力してください', trigger: 'blur' }],
  min_value: [{ required: false, message: '最小値を入力してください', trigger: 'blur' }],
  max_value: [{ required: false, message: '最大値を入力してください', trigger: 'blur' }],
  actual_value_1: [{ required: false, message: '実測値1を入力してください', trigger: 'blur' }],
  actual_value_2: [{ required: false, message: '実測値2を入力してください', trigger: 'blur' }],
  actual_value_3: [{ required: false, message: '実測値3を入力してください', trigger: 'blur' }],
  representative_model: [
    { required: false, message: '代表モデルを入力してください', trigger: 'blur' },
  ],
}

const inspectionHistory = ref<
  {
    id: number
    inspection_date: string
    material_cd: string
    material_name: string
    inspector_name: string
    result: string
    log_time?: string
    hd_no?: string
    manufacture_no?: string
    manufacture_date?: string
    pieces_per_bundle?: number
    length?: number
    quantity?: number
    bundle_quantity?: number
    outer_diameter1?: number
    outer_diameter2?: number
    supplier?: string
    magnetic?: number
    appearance?: number
    remarks?: string
    note?: string
    created_at?: string
    updated_at?: string
  }[]
>([])

const qualityStandards = ref<QualityStandard[]>([])
const selectedMaterialName = ref<string>('')

// API调用函数
const fetchQualityStandards = async (): Promise<void> => {
  try {
    loading.value = true
    const res = await request.get<{ success?: boolean; data?: any[] }>('/api/master/materials')
    const raw = (res as any)?.data ?? res
    const list = Array.isArray((raw as any)?.data) ? (raw as any).data : (Array.isArray(raw) ? raw : [])
    if (list.length >= 0) {
      qualityStandards.value = list.map((material: any) => ({
        id: material.id,
        material_cd: material.material_cd,
        material_name: material.material_name,
        material_type: material.material_type,
        standard_spec: material.standard_spec,
        unit: material.unit,
        diameter: material.diameter,
        thickness: material.thickness,
        length: material.length,
        supply_classification: material.supply_classification,
        pieces_per_bundle: material.pieces_per_bundle,
        usegae: material.usegae,
        supplier_cd: material.supplier_cd,
        supplier_name: material.supplier_name || '-',
        unit_price: material.unit_price,
        long_weight: material.long_weight,
        single_price: material.single_price,
        safety_stock: material.safety_stock,
        lead_time: material.lead_time,
        storage_location: material.storage_location,
        note: material.note,
        tolerance_range: material.tolerance_range,
        tolerance_1: material.tolerance_1,
        tolerance_2: material.tolerance_2,
        range_value: material.range_value,
        min_value: material.min_value,
        max_value: material.max_value,
        actual_value_1: material.actual_value_1,
        actual_value_2: material.actual_value_2,
        actual_value_3: material.actual_value_3,
        representative_model: material.representative_model,
        status: material.status || 1,
      }))
    }
  } catch (error) {
    console.error('品質基準データの取得エラー:', error)
    ElMessage.error('品質基準データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 工具函数
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ja-JP')
}

// 事件处理
const handleTabChange = (tabName: string | number): void => {
  console.log('切换到标签:', tabName)
  // 切换tab时重置材料名筛选
  if (tabName !== 'standards') {
    selectedMaterialName.value = ''
  }
}

// 材料名筛选处理
const handleMaterialNameFilter = (): void => {
  // 筛选逻辑已在computed属性中实现，这里可以添加其他逻辑
  console.log('材料名筛选:', selectedMaterialName.value)
}

const filterHistory = (): void => {
  // 日期筛选时重新获取数据（API层面筛选）
  currentPage.value = 1 // 重置到第一页
  fetchInspectionHistory()
}

const viewInspectionDetail = (row: {
  id: number
  inspection_date: string
  material_cd: string
  material_name: string
  inspector_name: string
  result: string
}): void => {
  selectedInspectionDetail.value = row
  inspectionDetailVisible.value = true
}

const editStandard = async (row: QualityStandard): Promise<void> => {
  try {
    editingStandard.value = row
    // フォームデータを初期化
    editForm.value = {
      tolerance_range: row.tolerance_range || '',
      tolerance_1: row.tolerance_1 || null,
      tolerance_2: row.tolerance_2 || null,
      range_value: row.range_value?.toString() || '', // 转换为字符串，保持文本格式
      min_value: row.min_value || null,
      max_value: row.max_value || null,
      actual_value_1: row.actual_value_1?.toString() || '',
      actual_value_2: row.actual_value_2?.toString() || '',
      actual_value_3: row.actual_value_3?.toString() || '',
      representative_model: row.representative_model || '',
    }
    editDialogVisible.value = true
  } catch (error) {
    console.error('基準編集エラー:', error)
    ElMessage.error('基準編集に失敗しました')
  }
}

const updateStandardStatus = async (row: QualityStandard): Promise<void> => {
  try {
    await request.put(`/api/master/materials/${row.id}`, {
      ...row,
      updated_at: new Date().toISOString(),
    })
    ElMessage.success(`${row.material_name} の状態を更新しました`)
  } catch (error) {
    console.error('状態更新エラー:', error)
    ElMessage.error('状態更新に失敗しました')
    // 恢复原状态
    row.status = row.status === 1 ? 0 : 1
  }
}

// 編集保存
const saveEdit = async (): Promise<void> => {
  if (!editFormRef.value || !editingStandard.value) return

  try {
    // フォームバリデーション
    await editFormRef.value.validate()

    saving.value = true

    // 更新データを準備 - 只更新编辑的字段，保持其他字段不变
    const updateData = {
      // 保持原有的所有字段
      material_cd: editingStandard.value.material_cd,
      material_name: editingStandard.value.material_name,
      material_type: editingStandard.value.material_type || '',
      standard_spec: editingStandard.value.standard_spec,
      unit: editingStandard.value.unit || '',
      diameter: editingStandard.value.diameter || null,
      thickness: editingStandard.value.thickness || null,
      length: editingStandard.value.length || null,
      supply_classification: editingStandard.value.supply_classification || '',
      pieces_per_bundle: editingStandard.value.pieces_per_bundle || null,
      usegae: editingStandard.value.usegae || '',
      supplier_cd: editingStandard.value.supplier_cd || '',
      unit_price: editingStandard.value.unit_price || null,
      long_weight: editingStandard.value.long_weight || null,
      single_price: editingStandard.value.single_price || null,
      safety_stock: editingStandard.value.safety_stock || null,
      lead_time: editingStandard.value.lead_time || null,
      storage_location: editingStandard.value.storage_location || '',
      note: editingStandard.value.note || '',
      // 只更新编辑的字段
      tolerance_range: editForm.value.tolerance_range,
      tolerance_1: editForm.value.tolerance_1,
      tolerance_2: editForm.value.tolerance_2,
      range_value: editForm.value.range_value, // 保持文本格式，不转换为数字
      min_value: editForm.value.min_value,
      max_value: editForm.value.max_value,
      actual_value_1: editForm.value.actual_value_1, // 保持字符串格式
      actual_value_2: editForm.value.actual_value_2, // 保持字符串格式
      actual_value_3: editForm.value.actual_value_3, // 保持字符串格式
      representative_model: editForm.value.representative_model,
      // 保持状态不变
      status: editingStandard.value.status,
      updated_at: new Date().toISOString(),
    }

    await request.put(`/api/master/materials/${editingStandard.value.id}`, updateData)

    // ローカルデータを更新
    const index = qualityStandards.value.findIndex((item) => item.id === editingStandard.value!.id)
    if (index > -1) {
      qualityStandards.value[index] = {
        ...qualityStandards.value[index],
        ...updateData,
      }
    }

    editDialogVisible.value = false
    ElMessage.success('品質基準を保存しました')
  } catch (error) {
    console.error('保存エラー:', error)
    ElMessage.error('保存に失敗しました')
  } finally {
    saving.value = false
  }
}

// 編集キャンセル
const cancelEdit = (): void => {
  editDialogVisible.value = false
  editingStandard.value = null
  // フォームをリセット
  if (editFormRef.value) {
    editFormRef.value.resetFields()
  }
}

// 获取検品履歴数据（服务器端分页，无供应商筛选时使用）
const fetchInspectionHistory = async (): Promise<void> => {
  try {
    loading.value = true
    // 构建查询参数 - 获取所有数据，支持分页
    const params: Record<string, number | string | undefined> = {
      page: currentPage.value,
      pageSize: pageSize.value,
    }
    if (historyDateRange.value && historyDateRange.value.length === 2) {
      params.startDate = historyDateRange.value[0]
      params.endDate = historyDateRange.value[1]
    }
    const result = await getMaterialLogs(params)
    const list = result?.data?.list ?? []

    if (list.length >= 0) {
      inspectionHistory.value = list.map((log: any) => ({
        id: log.id,
        inspection_date: log.log_date,
        material_cd: log.material_cd,
        material_name: log.material_name,
        inspector_name: log.inspector_name || log.item || '検品者', // 优先使用inspector_name，如果没有则使用item
        result: log.material_quality || '合格',
        log_time: log.log_time,
        hd_no: log.hd_no,
        manufacture_no: log.manufacture_no,
        manufacture_date: log.manufacture_date,
        pieces_per_bundle: log.pieces_per_bundle,
        length: log.length,
        quantity: log.quantity,
        bundle_quantity: log.bundle_quantity,
        outer_diameter1: log.outer_diameter1,
        outer_diameter2: log.outer_diameter2,
        supplier: log.supplier,
        magnetic: log.magnetic,
        appearance: log.appearance,
        remarks: log.remarks,
        note: log.note,
        created_at: log.created_at,
        updated_at: log.updated_at,
      }))

      totalRecords.value = result?.data?.total ?? 0
      if (
        !selectedSupplier.value ||
        !Array.isArray(selectedSupplier.value) ||
        selectedSupplier.value.length === 0
      ) {
        filteredInspectionHistory.value = inspectionHistory.value
      } else {
        applyFilters()
      }
    }
  } catch (error) {
    console.error('获取検品履歴数据错误:', error)
    ElMessage.error('検品履歴データの取得中にエラーが発生しました')
  } finally {
    loading.value = false
  }
}

// 获取仕入先选项
const fetchSupplierOptions = async (): Promise<void> => {
  try {
    const result = await getSupplierList()
    supplierOptions.value = result?.data ?? []
  } catch (error) {
    console.error('获取仕入先列表错误:', error)
  }
}

// 仕入先筛选处理
const handleSupplierFilter = (): void => {
  // 确保 selectedSupplier.value 是数组（处理清空后的 null/undefined 情况）
  if (!selectedSupplier.value || !Array.isArray(selectedSupplier.value)) {
    selectedSupplier.value = []
  }

  // 如果有供应商筛选，需要获取所有数据（不分页）进行客户端筛选
  // 如果没有供应商筛选，使用服务器端分页
  if (selectedSupplier.value.length > 0) {
    // 有筛选时，获取所有数据
    currentPage.value = 1 // 重置到第一页
    fetchAllDataForFilter()
  } else {
    // 没有筛选时，使用服务器端分页
    currentPage.value = 1
    fetchInspectionHistory()
  }
}

// 获取所有数据用于客户端筛选（当有供应商筛选时）
const fetchAllDataForFilter = async (): Promise<void> => {
  try {
    loading.value = true
    const params: Record<string, number | string | undefined> = {
      page: 1,
      pageSize: 10000,
    }
    if (historyDateRange.value && historyDateRange.value.length === 2) {
      params.startDate = historyDateRange.value[0]
      params.endDate = historyDateRange.value[1]
    }
    const result = await getMaterialLogs(params)
    const list = result?.data?.list ?? []
    if (list.length >= 0) {
      inspectionHistory.value = list.map((log: any) => ({
        id: log.id,
        inspection_date: log.log_date,
        material_cd: log.material_cd,
        material_name: log.material_name,
        inspector_name: log.inspector_name || log.item || '検品者',
        result: log.material_quality || '合格',
        log_time: log.log_time,
        hd_no: log.hd_no,
        manufacture_no: log.manufacture_no,
        manufacture_date: log.manufacture_date,
        pieces_per_bundle: log.pieces_per_bundle,
        length: log.length,
        quantity: log.quantity,
        bundle_quantity: log.bundle_quantity,
        outer_diameter1: log.outer_diameter1,
        outer_diameter2: log.outer_diameter2,
        supplier: log.supplier,
        magnetic: log.magnetic,
        appearance: log.appearance,
        remarks: log.remarks,
        note: log.note,
        created_at: log.created_at,
        updated_at: log.updated_at,
      }))

      applyFilters()
    }
  } catch (error) {
    console.error('获取数据错误:', error)
    ElMessage.error('データの取得中にエラーが発生しました')
  } finally {
    loading.value = false
  }
}

// 应用筛选条件
const applyFilters = (): void => {
  let filtered = [...inspectionHistory.value]

  // 仕入先筛选（支持多选）
  // 确保 selectedSupplier.value 是数组且不为空
  if (
    selectedSupplier.value &&
    Array.isArray(selectedSupplier.value) &&
    selectedSupplier.value.length > 0
  ) {
    filtered = filtered.filter((item) => {
      // 尝试多个可能的供应商字段
      const supplierValue =
        item.supplier || (item as any).supplier_name || (item as any).supplierName

      // 需要根据选中的ID找到对应的供应商名称进行匹配
      const selectedSupplierNames = selectedSupplier.value.map((selectedId) => {
        const option = supplierOptions.value.find((opt) => opt.value === selectedId)
        return option ? option.label : selectedId
      })

      return supplierValue && selectedSupplierNames.includes(supplierValue)
    })
  }

  // 更新总数（基于筛选后的数据）
  totalRecords.value = filtered.length

  // 应用客户端分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  filteredInspectionHistory.value = filtered.slice(start, end)
}

// 获取所有筛选数据（不分页）
const fetchAllFilteredData = async (): Promise<any[]> => {
  try {
    // 构建查询参数 - 获取所有数据，不分页
    const params = new URLSearchParams()
    params.append('page', '1')
    params.append('page_size', '10000') // 设置一个很大的数字获取所有数据

    // 日期范围筛选（可选）
    if (historyDateRange.value && historyDateRange.value.length === 2) {
      params.append('start_date', historyDateRange.value[0])
      params.append('end_date', historyDateRange.value[1])
    }

    const response = await fetch(`/api/material-logs?${params.toString()}`)
    const result = await response.json()

    if (result.success && result.data) {
      let allData = result.data.map((log: any) => ({
        id: log.id,
        inspection_date: log.log_date,
        material_cd: log.material_cd,
        material_name: log.material_name,
        material_quality: log.material_quality,
        inspector_name: log.inspector_name || log.item || '検品者',
        result: log.material_quality || '合格',
        log_time: log.log_time,
        hd_no: log.hd_no,
        manufacture_no: log.manufacture_no,
        manufacture_date: log.manufacture_date,
        pieces_per_bundle: log.pieces_per_bundle,
        length: log.length,
        quantity: log.quantity,
        bundle_quantity: log.bundle_quantity,
        outer_diameter1: log.outer_diameter1,
        outer_diameter2: log.outer_diameter2,
        supplier: log.supplier,
        magnetic: log.magnetic,
        appearance: log.appearance,
        remarks: log.remarks,
        note: log.note,
        created_at: log.created_at,
        updated_at: log.updated_at,
      }))

      // 应用仕入先筛选
      if (
        selectedSupplier.value &&
        Array.isArray(selectedSupplier.value) &&
        selectedSupplier.value.length > 0
      ) {
        // 根据选中的ID找到对应的供应商名称
        const selectedSupplierNames = selectedSupplier.value.map((selectedId) => {
          const option = supplierOptions.value.find((opt) => opt.value === selectedId)
          return option ? option.label : selectedId
        })

        allData = allData.filter((item: any) => {
          const supplierValue = item.supplier || item.supplier_name || item.supplierName
          return supplierValue && selectedSupplierNames.includes(supplierValue)
        })
      }

      return allData
    } else {
      console.error('获取所有数据失败:', result.message)
      return []
    }
  } catch (error) {
    console.error('获取所有数据错误:', error)
    return []
  }
}

// 获取选中供应商的名称
const getSelectedSupplierNames = (): string => {
  if (!selectedSupplier.value || selectedSupplier.value.length === 0) {
    return '全仕入先'
  }

  const names = selectedSupplier.value.map((selectedId) => {
    const option = supplierOptions.value.find((opt) => opt.value === selectedId)
    return option ? option.label : selectedId
  })

  return names.join(', ')
}

// 打印検品履歴
const printInspectionHistory = async (): Promise<void> => {
  try {
    // 获取所有筛选数据
    const allData = await fetchAllFilteredData()

    if (allData.length === 0) {
      ElMessage.warning('印刷するデータがありません')
      return
    }

    // 按検品日分组
    const groupedData = allData.reduce((groups: any, item: any) => {
      const date = item.inspection_date
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(item)
      return groups
    }, {})

    // 获取所有日期并排序
    const sortedDates = Object.keys(groupedData).sort()

    // 为每个日期创建一页
    const pages = sortedDates.map((date, index) => {
      const dayData = groupedData[date]
      return createPrintPage(dayData, date, index + 1, sortedDates.length)
    })

    // 创建完整的打印内容
    const printContent = `
      <html>
        <head>
          <title>原材料受入チェックシート</title>
          <style>
            body {
              font-family: 'MS Gothic', 'Courier New', monospace;
              margin: 0;
              padding: 0;
              font-size: 14px;
              line-height: 1.3;
            }
            @page {
              margin: 60px 30px 20px 30px;
              size: A4;
            }
            .page-break {
              page-break-before: always;
              margin-top: 0;
              padding-top: 0;
            }
            .page-break:first-child {
              page-break-before: avoid;
            }
            .page-container {
              margin: 0;
              padding: 15px 0 0 0;
              page-break-after: always;
              overflow: hidden;
            }
            .page-container:last-child {
              page-break-after: avoid;
            }
            .header {
              text-align: center;
              margin-bottom: 15px;
              position: relative;
            }
            .main-title {
              font-size: 22px;
              font-weight: 900;
              margin-bottom: 10px;
            }
            .manager-info {
              position: absolute;
              top: 0;
              right: 0;
              font-size: 10px;
            }
            .quality-section {
              margin-bottom: 15px;
              text-align: left;
            }
            .quality-title {
              font-weight: 900;
              font-size: 16px;
              margin-bottom: 4px;
            }
            .quality-item {
              margin-bottom: 2px;
              padding-left: 10px;
              font-size: 13px;
            }
            .arrival-info {
              margin-bottom: 15px;
              border-top: 1px solid #000;
              padding-top: 12px;
              font-size: 19px;
              font-weight: 600;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-top: 5px;
              font-size: 13px;
              page-break-inside: avoid;
            }
            th, td {
              border: 1px solid #000;
              padding: 3px 4px;
              text-align: center;
            }
            tr {
              page-break-inside: avoid;
            }
            th {
              background-color: #f0f0f0;
              font-weight: 900;
              font-size: 14px;
              text-align: center;
            }
            .text-left { text-align: left; }
            .text-right { text-align: right; }
            .footer {
              margin-top: 8px;
              text-align: right;
              font-size: 12px;
              font-weight: 600;
            }
            .circle {
              font-size: 16px;
              font-weight: 900;
            }
          </style>
        </head>
        <body>
          ${pages.join('')}
        </body>
      </html>
    `

    // 打开新窗口进行打印
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(printContent)
      printWindow.document.close()
      printWindow.focus()
      printWindow.print()
      printWindow.close()
    }
  } catch (error) {
    console.error('打印失败:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

// 创建单页打印内容
const createPrintPage = (
  dayData: any[],
  date: string,
  pageNumber: number,
  totalPages: number,
): string => {
  return `
    <div class="page-container ${pageNumber > 1 ? 'page-break' : ''}">
      <div class="header">
        <div class="main-title">材料受入チェックシート</div>
        <div class="manager-info">管理者名 小森 印</div>
      </div>

      <div class="quality-section">
        <div class="quality-title">品質特性:</div>
        <div class="quality-item">① 検品日: 外径・肉厚・長さ・材質を確認し、相違なければ、検品日を記入する</div>
        <div class="quality-item">② 数量: 単位本数</div>
        <div class="quality-item">③ 製造番号: 製造番号を記入する</div>
        <div class="quality-item">④ 外径: 別紙参照 (測定値をn=2記入する事) *注意: 先端10mmより奥で測定</div>
        <div class="quality-item">⑤ 磁気: クリップが二つ以上付かないこと *○×で記入する</div>
        <div class="quality-item">⑥ 外観: 錆、打痕キズ、擦りキズ、連続打痕キズ、縦キズの無いこと *○×で記入する</div>
      </div>

      <div class="arrival-info">
        入荷日 ${date}
        仕入先 ${getSelectedSupplierNames()}
      </div>

      <table>
        <thead>
          <tr>
            <th>入荷日</th>
            <th>材料名</th>
            <th>材質</th>
            <th>数量</th>
            <th>製造番号</th>
            <th>外径</th>
            <th>外径</th>
            <th>外観</th>
            <th>磁気</th>
            <th>検査員</th>
          </tr>
        </thead>
        <tbody>
          ${dayData
            .sort((a, b) => {
              // 按材料名排序
              const nameA = a.material_name || ''
              const nameB = b.material_name || ''
              return nameA.localeCompare(nameB, 'ja', { numeric: true })
            })
            .map(
              (item) => `
            <tr>
              <td class="text-left">${formatDate(item.inspection_date)}</td>
              <td class="text-left">${item.material_name || '-'}</td>
              <td class="text-left">${item.material_quality || '-'}</td>
              <td class="text-right">${item.quantity || '-'}</td>
              <td class="text-left">${item.manufacture_no || '-'}</td>
              <td class="text-right">${item.outer_diameter1 ? parseFloat(item.outer_diameter1).toFixed(3) : '-'}</td>
              <td class="text-right">${item.outer_diameter2 ? parseFloat(item.outer_diameter2).toFixed(3) : '-'}</td>
              <td><span class="circle">○</span></td>
              <td><span class="circle">○</span></td>
              <td>${item.inspector_name || '検査員'}</td>
            </tr>
          `,
            )
            .join('')}
        </tbody>
      </table>

      <div class="footer">
        件数 ${dayData.length}
      </div>
    </div>
  `
}

// 分页处理函数
const handleSizeChange = (val: number): void => {
  pageSize.value = val
  currentPage.value = 1 // 重置到第一页

  // 如果有供应商筛选，使用客户端分页；否则使用服务器端分页
  if (
    selectedSupplier.value &&
    Array.isArray(selectedSupplier.value) &&
    selectedSupplier.value.length > 0
  ) {
    applyFilters()
  } else {
    fetchInspectionHistory()
  }
}

const handleCurrentChange = (val: number): void => {
  currentPage.value = val

  // 如果有供应商筛选，使用客户端分页；否则使用服务器端分页
  if (
    selectedSupplier.value &&
    Array.isArray(selectedSupplier.value) &&
    selectedSupplier.value.length > 0
  ) {
    applyFilters()
  } else {
    fetchInspectionHistory()
  }
}

// 监听日期范围变化
watch(
  historyDateRange,
  () => {
    currentPage.value = 1 // 重置到第一页
    // 如果有供应商筛选，获取所有数据；否则使用服务器端分页
    if (
      selectedSupplier.value &&
      Array.isArray(selectedSupplier.value) &&
      selectedSupplier.value.length > 0
    ) {
      fetchAllDataForFilter()
    } else {
      fetchInspectionHistory()
    }
  },
  { deep: true },
)

onMounted((): void => {
  // 初期化処理
  fetchQualityStandards()
  fetchInspectionHistory()
  fetchSupplierOptions()
})
</script>

<style scoped>
.inspection-container {
  padding: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 4px;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 1.4rem;
  color: #667eea;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
  font-size: 0.875rem;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  color: white;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.stat-pending {
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
}

.stat-progress {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
}

.stat-completed {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 4px;
}

/* タブ区域 */
.tabs-section {
  margin-bottom: 12px;
}

.modern-tabs {
  background: white;
  border-radius: 12px;
  padding: 8px 16px 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.tab-badge {
  margin-left: 8px;
}

/* 内容区域 */
.content-section {
  margin-bottom: 12px;
}

.list-card,
.inspection-card,
.history-card,
.standards-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: none;
}

.list-card :deep(.el-card__header),
.inspection-card :deep(.el-card__header),
.history-card :deep(.el-card__header),
.standards-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.list-card :deep(.el-card__body),
.inspection-card :deep(.el-card__body),
.history-card :deep(.el-card__body),
.standards-card :deep(.el-card__body) {
  padding: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 6px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 8px 0;
  margin-top: 4px;
}

.pagination-container :deep(.el-pagination) {
  font-size: 0.875rem;
}

.pagination-container :deep(.el-pagination .el-pagination__sizes),
.pagination-container :deep(.el-pagination .el-pager li),
.pagination-container :deep(.el-pagination .btn-prev),
.pagination-container :deep(.el-pagination .btn-next) {
  height: 28px;
  line-height: 28px;
  font-size: 0.875rem;
}

/* 表格样式 */
.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

.modern-table :deep(.el-table__header-wrapper) {
  background: #f8fafc;
}

.modern-table :deep(.el-table th) {
  padding: 8px 0;
  font-size: 0.875rem;
}

.modern-table :deep(.el-table td) {
  padding: 8px 0;
  font-size: 0.875rem;
}

.receive-date {
  font-weight: 500;
  color: #667eea;
  font-size: 0.875rem;
}

.material-cd {
  font-family: monospace;
  color: #667eea;
  font-weight: bold;
  background: #f7fafc;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.875rem;
}

.quantity {
  font-weight: 600;
  color: #2d3748;
  font-size: 0.875rem;
}

/* 检品表单样式 */
.no-inspection {
  padding: 60px 20px;
  text-align: center;
}

.inspection-form {
  padding: 20px;
}

.material-info {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-item label {
  font-weight: 600;
  color: #4a5568;
  min-width: 100px;
}

.info-item span {
  color: #2d3748;
  flex: 1;
}

.inspection-items {
  margin-bottom: 24px;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.inspection-item {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
}

.inspection-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.item-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
}

.result-radio {
  display: flex;
  gap: 8px;
}

.result-radio :deep(.el-radio-button__inner) {
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.3s;
}

.result-pass.el-radio-button :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: #10b981;
  border-color: #10b981;
}

.result-fail.el-radio-button :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: #ef4444;
  border-color: #ef4444;
}

.result-check.el-radio-button
  :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: #f59e0b;
  border-color: #f59e0b;
}

.item-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.item-remarks {
  grid-column: span 2;
}

.item-criteria,
.item-measurement,
.item-remarks {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.item-criteria label,
.item-measurement label,
.item-remarks label {
  font-weight: 600;
  color: #4a5568;
  min-width: 80px;
  margin-top: 8px;
}

.overall-judgment {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.judgment-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.judgment-radio {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.judgment-radio :deep(.el-radio-button__inner) {
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 150px;
  justify-content: center;
}

.judgment-pass.el-radio-button
  :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: #10b981;
}

.judgment-fail.el-radio-button
  :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-color: #ef4444;
}

.judgment-conditional.el-radio-button
  :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-color: #f59e0b;
}

.judgment-notes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.judgment-notes label {
  font-weight: 600;
  color: #4a5568;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 20px 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: space-around;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .item-content {
    grid-template-columns: 1fr;
  }

  .item-remarks {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .inspection-container {
    padding: 8px;
  }

  .page-header {
    padding: 12px 16px;
  }

  .main-title {
    font-size: 1.25rem;
  }

  .subtitle {
    font-size: 0.8125rem;
  }

  .filter-controls {
    flex-direction: column;
    width: 100%;
  }

  .filter-controls .el-select,
  .filter-controls .el-date-picker {
    width: 100% !important;
    margin-right: 0 !important;
    margin-bottom: 8px;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .inspection-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .page-header,
  .modern-tabs,
  .list-card,
  .inspection-card,
  .history-card,
  .standards-card {
    background: rgba(45, 55, 72, 0.95);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .main-title,
  .card-title,
  .section-title {
    color: #e2e8f0;
  }

  .subtitle {
    color: #a0aec0;
  }

  .material-info,
  .overall-judgment {
    background: rgba(26, 32, 44, 0.6);
  }

  .inspection-item {
    background: rgba(26, 32, 44, 0.8);
    border-color: rgba(255, 255, 255, 0.1);
  }
}

/* 动画效果 */
.list-card,
.inspection-card,
.history-card,
.standards-card {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-table th) {
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
  padding: 8px 0;
  font-size: 0.875rem;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

:deep(.el-table__row:hover td) {
  background-color: #f0f4f8 !important;
}

:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  padding: 2px 8px;
  font-size: 0.75rem;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__active-bar) {
  background-color: #667eea;
  height: 3px;
}

:deep(.el-tabs__item) {
  padding: 0 16px;
  height: 40px;
  line-height: 40px;
  font-size: 0.875rem;
}

:deep(.el-tabs__item.is-active) {
  color: #667eea;
  font-weight: 600;
}

:deep(.el-button--small) {
  padding: 6px 12px;
  font-size: 0.875rem;
}

:deep(.el-input__wrapper) {
  padding: 4px 8px;
}

:deep(.el-select .el-input__wrapper) {
  padding: 4px 8px;
}

/* 編集ダイアログスタイル */
.edit-dialog {
  border-radius: 12px;
}

.edit-dialog :deep(.el-dialog__header) {
  padding: 16px 20px 12px;
  border-bottom: 1px solid #e5e7eb;
}

.edit-dialog :deep(.el-dialog__body) {
  padding: 16px 20px;
}

.edit-dialog :deep(.el-dialog__footer) {
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
}

.edit-form {
  padding: 12px 0;
}

.material-info-section {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
}

.material-info-section .section-title {
  font-size: 1rem;
  margin-bottom: 10px;
}

.info-display {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item label {
  font-weight: 600;
  color: #4a5568;
  min-width: 70px;
  font-size: 0.875rem;
}

.info-item span {
  color: #2d3748;
  flex: 1;
  font-size: 0.875rem;
}

.edit-form-section {
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
}

.edit-form-section .section-title {
  font-size: 1rem;
  margin-bottom: 12px;
}

.edit-form-content {
  margin-top: 8px;
}

.edit-form-content :deep(.el-form-item) {
  margin-bottom: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* フォームアイテムスタイル */
:deep(.el-form-item__label) {
  font-weight: 600;
  color: #4a5568;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: left;
}

/* 品質基準設定テーブルスタイル */
.quality-standards-table {
  border-radius: 8px;
  overflow: hidden;
}

.quality-standards-table :deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #f8fafc;
}

.quality-standards-table :deep(.el-table__body-wrapper) {
  max-height: calc(100vh - 350px);
  overflow-y: auto;
}

.quality-standards-table :deep(.el-table th),
.quality-standards-table :deep(.el-table td) {
  padding: 6px 0;
  font-size: 0.8125rem;
}

.quality-standards-table :deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 8px;
}

.quality-standards-table :deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: #f1f1f1;
  border-radius: 4px;
}

.quality-standards-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: #c1c1c1;
  border-radius: 4px;
}

.quality-standards-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: #a8a8a8;
}

/* レスポンシブデザイン */
@media (max-width: 768px) {
  .edit-dialog {
    width: 95% !important;
    margin: 0 auto;
  }

  .edit-dialog :deep(.el-dialog__body) {
    padding: 12px 16px;
  }

  .info-display {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .edit-form-content :deep(.el-col) {
    margin-bottom: 12px;
  }

  .quality-standards-table {
    height: calc(100vh - 300px) !important;
    max-height: calc(100vh - 300px) !important;
  }

  .modern-table {
    font-size: 0.8125rem;
  }
}
</style>
