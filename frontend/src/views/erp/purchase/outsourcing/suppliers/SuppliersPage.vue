<template>
  <div class="suppliers-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon-wrap">
          <OfficeBuilding class="header-icon" />
        </div>
        <div class="header-text">
          <h1 class="page-title">外注先マスタ</h1>
          <span class="page-subtitle">外注業者の登録・管理</span>
        </div>
      </div>
      <div class="header-right">
        <div class="stat-pill">
          <span class="stat-num">{{ tableData.length }}</span>
          <span class="stat-label">件</span>
        </div>
        <el-button type="primary" size="small" @click="handleAdd" class="add-btn">
          <el-icon><Plus /></el-icon>
          新規登録
        </el-button>
      </div>
    </div>

    <!-- 搜索过滤区 -->
    <div class="filter-bar">
      <el-form :inline="true" :model="filterForm" size="small" class="filter-form">
        <el-form-item label="種別">
          <el-select v-model="filterForm.type" placeholder="すべて" clearable style="width: 120px">
            <el-option label="メッキ" value="plating" />
            <el-option label="溶接" value="welding" />
            <el-option label="切断" value="cutting" />
            <el-option label="成型" value="forming" />
            <el-option label="部品加工" value="parts_processing" />
          </el-select>
        </el-form-item>
        <el-form-item label="状態">
          <el-select v-model="filterForm.isActive" placeholder="すべて" clearable style="width: 100px">
            <el-option label="有効" :value="true" />
            <el-option label="無効" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="キーワード">
          <el-input
            v-model="filterForm.keyword"
            placeholder="外注先名/コード"
            clearable
            style="width: 180px"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <div v-if="!loading && tableData.length === 0" class="empty-state">
        <div class="empty-icon">🏭</div>
        <div class="empty-text">外注先が登録されていません</div>
        <el-button type="primary" size="small" @click="handleAdd">
          <el-icon><Plus /></el-icon> 新規登録
        </el-button>
      </div>
      <el-table
        v-else
        :data="tableData"
        v-loading="loading"
        stripe
        border
        size="small"
        :header-cell-style="{ background: 'linear-gradient(180deg,#f0f4ff 0%,#e8edf8 100%)', fontWeight: '600', color: '#374151', padding: '7px 0', fontSize: '12px' }"
        :cell-style="{ padding: '5px 0', fontSize: '12.5px' }"
        class="supplier-table"
        highlight-current-row
      >
        <el-table-column prop="supplier_cd" label="外注先コード" width="115" fixed="left">
          <template #default="{ row }">
            <span class="code-badge">{{ row.supplier_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="外注先名" min-width="155" show-overflow-tooltip />
        <el-table-column prop="supplier_type" label="種別" width="88" align="center">
          <template #default="{ row }">
            <el-tag :type="getTypeTagColor(row.supplier_type) as any" size="small" effect="light" round>
              {{ getTypeLabel(row.supplier_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="住所" min-width="175" show-overflow-tooltip />
        <el-table-column prop="phone" label="電話番号" width="125" />
        <el-table-column prop="contact_person" label="担当者" width="100" />
        <el-table-column prop="lead_time_days" label="リードタイム" width="95" align="center">
          <template #default="{ row }">
            <span class="lead-time-badge">{{ row.lead_time_days }}<em>日</em></span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状態" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              active-text="有効"
              inactive-text="無効"
              inline-prompt
              :loading="row._statusLoading"
              @change="(val: string | number | boolean) => handleToggleStatus(row, !!val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button type="primary" link size="small" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>編集
              </el-button>
              <el-divider direction="vertical" />
              <el-button type="danger" link size="small" @click="handleDelete(row)">削除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新規/編集ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="680px"
      destroy-on-close
      class="supplier-dialog"
      :close-on-click-modal="false"
      :show-close="false"
      align-center
    >
      <template #header>
        <div class="dialog-header">
          <div class="dh-icon-wrap">
            <OfficeBuilding class="dh-icon" />
          </div>
          <div class="dh-text">
            <span class="dh-title">{{ dialogTitle }}</span>
            <span class="dh-sub">{{ isEdit ? '情報を更新します' : '新しい外注先を登録します' }}</span>
          </div>
          <div class="dh-badge" :class="isEdit ? 'edit' : 'new'">
            {{ isEdit ? '編集' : '新規' }}
          </div>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="105px"
        class="supplier-form"
        size="small"
      >
        <!-- 基本情報 -->
        <div class="form-group">
          <div class="group-label"><span class="gl-bar"></span>基本情報</div>
          <el-row :gutter="14">
            <el-col :span="12">
              <el-form-item label="外注先コード" prop="supplier_cd">
                <el-input
                  v-model="formData.supplier_cd"
                  :disabled="isEdit"
                  placeholder="例: OS-001"
                  clearable
                  @blur="checkSupplierCode"
                  :class="{ 'is-error-input': duplicateCodeError }"
                />
                <div v-if="duplicateCodeError && !isEdit" class="field-error">
                  <el-icon><Warning /></el-icon> {{ duplicateCodeError }}
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="外注先名" prop="supplier_name">
                <el-input v-model="formData.supplier_name" placeholder="例: (株)○○金属" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="外注種別" prop="supplier_type">
                <el-select v-model="formData.supplier_type" placeholder="選択" style="width:100%" clearable>
                  <el-option label="メッキ" value="plating" />
                  <el-option label="溶接" value="welding" />
                  <el-option label="切断" value="cutting" />
                  <el-option label="成型" value="forming" />
                  <el-option label="部品加工" value="parts_processing" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="リードタイム">
                <div class="unit-input-wrap">
                  <el-input-number
                    v-model="formData.lead_time_days"
                    :min="1"
                    :max="90"
                    style="width:100%"
                    controls-position="right"
                  />
                  <span class="unit-label">日</span>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 連絡先 -->
        <div class="form-group">
          <div class="group-label"><span class="gl-bar"></span>連絡先情報</div>
          <el-form-item label="住所">
            <el-input v-model="formData.address" placeholder="住所を入力" clearable />
          </el-form-item>
          <el-row :gutter="14">
            <el-col :span="12">
              <el-form-item label="電話番号">
                <el-input v-model="formData.phone" placeholder="052-123-4567" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="FAX番号">
                <el-input v-model="formData.fax" placeholder="052-123-4568" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="担当者">
                <el-input v-model="formData.contact_person" placeholder="担当者名" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="メール">
                <el-input v-model="formData.email" placeholder="example@co.jp" clearable type="email" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- その他 -->
        <div class="form-group last">
          <div class="group-label"><span class="gl-bar"></span>その他情報</div>
          <el-form-item label="支払条件">
            <el-input v-model="formData.payment_terms" placeholder="例: 月末締め翌月末払い" clearable />
          </el-form-item>
          <el-form-item label="備考">
            <el-input
              v-model="formData.remarks"
              type="textarea"
              :rows="2"
              placeholder="備考を入力"
              :maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" size="small">キャンセル</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" size="small">
            <el-icon v-if="!submitting"><Check /></el-icon>
            {{ isEdit ? '更新' : '登録' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { OfficeBuilding, Plus, Search, Edit, Check, Warning } from '@element-plus/icons-vue'
import { getSuppliers, createSupplier, updateSupplier, deleteSupplier } from '@/api/outsourcing'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = usePurchaseOperationPermission()


// 状态
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const tableData = ref<any[]>([])
const formRef = ref<FormInstance>()
const duplicateCodeError = ref('')
const checkingCode = ref(false)

// 筛选表单
const filterForm = reactive({
  type: '',
  isActive: true as boolean | string,
  keyword: '',
})

// 编辑表单
const formData = reactive({
  id: undefined as number | undefined,
  supplier_cd: '',
  supplier_name: '',
  supplier_type: '',
  address: '',
  phone: '',
  fax: '',
  contact_person: '',
  email: '',
  payment_terms: '',
  lead_time_days: 7,
  remarks: '',
  is_active: true,
})

// 表单验证规则
const formRules: FormRules = {
  supplier_cd: [
    { required: true, message: '外注先コードを入力してください', trigger: 'blur' },
    {
      pattern: /^[A-Z0-9\-_]+$/i,
      message: '外注先コードは英数字、ハイフン、アンダースコアのみ使用できます',
      trigger: 'blur',
    },
    { min: 2, max: 20, message: '外注先コードは2〜20文字で入力してください', trigger: 'blur' },
  ],
  supplier_name: [
    { required: true, message: '外注先名を入力してください', trigger: 'blur' },
    { max: 100, message: '外注先名は100文字以内で入力してください', trigger: 'blur' },
  ],
  supplier_type: [{ required: true, message: '外注種別を選択してください', trigger: 'change' }],
  email: [{ type: 'email', message: '有効なメールアドレスを入力してください', trigger: 'blur' }],
}

const dialogTitle = ref('外注先登録')

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (filterForm.type) params.type = filterForm.type
    if (filterForm.isActive !== '') params.isActive = filterForm.isActive

    const res = await getSuppliers(params)
    const body = res?.data as { success?: boolean; data?: unknown[] } | unknown[] | undefined
    let data: any[] = []

    if (Array.isArray(body)) {
      data = body
    } else if (body && typeof body === 'object' && Array.isArray((body as { data?: unknown[] }).data)) {
      data = (body as { data: unknown[] }).data
    }

    if (filterForm.keyword && data.length > 0) {
      const keyword = filterForm.keyword.toLowerCase()
      data = data.filter(
        (item: any) =>
          item.supplier_cd?.toLowerCase().includes(keyword) ||
          item.supplier_name?.toLowerCase().includes(keyword),
      )
    }

    tableData.value = data || []
  } catch (error) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データの取得に失敗しました')
    tableData.value = []
  } finally {
    loading.value = false
  }
}

// 筛选条件变化时自动刷新列表
let filterDebounceTimer: ReturnType<typeof setTimeout> | null = null
watch(
  () => ({ type: filterForm.type, isActive: filterForm.isActive, keyword: filterForm.keyword }),
  () => {
    if (filterDebounceTimer) clearTimeout(filterDebounceTimer)
    filterDebounceTimer = setTimeout(() => fetchData(), 300)
  },
  { deep: true },
)

const handleToggleStatus = async (row: any, newVal: boolean) => {
  if (!guardPurchaseOperation(canEdit)) return

  const prev = row.is_active
  row._statusLoading = true
  try {
    await updateSupplier(row.id, { ...row, is_active: newVal })
    ElMessage.success(newVal ? '有効にしました' : '無効にしました')
  } catch (e) {
    row.is_active = prev
    ElMessage.error('状態の更新に失敗しました')
  } finally {
    row._statusLoading = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '外注先登録'
  resetForm()
  duplicateCodeError.value = ''
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  dialogTitle.value = '外注先編集'
  Object.assign(formData, row)
  duplicateCodeError.value = ''
  dialogVisible.value = true
}

const checkSupplierCode = async () => {
  if (isEdit.value || !formData.supplier_cd || formData.supplier_cd.length < 2) {
    duplicateCodeError.value = ''
    return
  }
  checkingCode.value = true
  duplicateCodeError.value = ''
  try {
    const res = await getSuppliers({})
    const body = res?.data as { success?: boolean; data?: { supplier_cd?: string }[] } | undefined
    const list = body && typeof body === 'object' && Array.isArray((body as { data?: unknown[] }).data)
      ? (body as { data: { supplier_cd?: string }[] }).data
      : []
    const exists = list.some((item: any) => item.supplier_cd === formData.supplier_cd)
    if (exists) {
      duplicateCodeError.value = `外注先コード「${formData.supplier_cd}」は既に使用されています`
      formRef.value?.validateField('supplier_cd', () => {})
    }
  } catch (error) {
    console.warn('コード重複チェックエラー:', error)
  } finally {
    checkingCode.value = false
  }
}

const handleDelete = async (row: any) => {
  if (!guardPurchaseOperation(canDelete)) return

  try {
    await ElMessageBox.confirm(`「${row.supplier_name}」を削除しますか？削除後は元に戻せません。`, '削除確認', {
      type: 'warning',
    })
    await deleteSupplier(row.id)
    ElMessage.success('削除しました')
    fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('削除に失敗しました')
    }
  }
}

const handleSubmit = async () => {
  if (!guardPurchaseOperation(canEdit)) return

  if (!formRef.value) return
  if (duplicateCodeError.value && !isEdit.value) {
    ElMessage.warning(duplicateCodeError.value)
    return
  }
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value && formData.id) {
        const { id, ...updateData } = formData
        await updateSupplier(id, updateData)
        ElMessage.success('更新しました')
      } else {
        const { id, ...createData } = formData
        await createSupplier(createData)
        ElMessage.success('登録しました')
      }
      dialogVisible.value = false
      duplicateCodeError.value = ''
      fetchData()
    } catch (error: any) {
      let errorMessage = isEdit.value ? '更新に失敗しました' : '登録に失敗しました'
      if (error?.response?.data) {
        const errorData = error.response.data
        if (errorData.message) errorMessage = errorData.message
        if (errorData.error === 'DUPLICATE_ENTRY' || errorData.error === 'DUPLICATE_SUPPLIER_CD') {
          errorMessage = errorData.message || `外注先コード「${formData.supplier_cd}」は既に登録されています`
          duplicateCodeError.value = errorMessage
          formRef.value?.validateField('supplier_cd', () => {})
        }
      } else if (error?.message) {
        if (error.message.includes('Duplicate') || error.message.includes('重複')) {
          errorMessage = `外注先コード「${formData.supplier_cd}」は既に登録されています`
          duplicateCodeError.value = errorMessage
          formRef.value?.validateField('supplier_cd', () => {})
        }
      }
      ElMessage.error(errorMessage)
    } finally {
      submitting.value = false
    }
  })
}

const resetForm = () => {
  formData.id = undefined
  formData.supplier_cd = ''
  formData.supplier_name = ''
  formData.supplier_type = ''
  formData.address = ''
  formData.phone = ''
  formData.fax = ''
  formData.contact_person = ''
  formData.email = ''
  formData.payment_terms = ''
  formData.lead_time_days = 7
  formData.remarks = ''
  formData.is_active = true
  duplicateCodeError.value = ''
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    plating: 'メッキ', welding: '溶接', cutting: '切断', forming: '成型', parts_processing: '部品加工',
  }
  return labels[type] || type
}

const getTypeTagColor = (type: string): 'warning' | 'danger' | 'primary' | 'info' | 'success' => {
  const colors: Record<string, 'warning' | 'danger' | 'primary' | 'info' | 'success'> = {
    plating: 'warning', welding: 'danger', cutting: 'success', forming: 'primary', parts_processing: 'info',
  }
  return colors[type] || 'info'
}

onMounted(() => { fetchData() })
</script>

<style scoped lang="scss">
/* ===== 页面容器 ===== */
.suppliers-page {
  padding: 10px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ===== 页面头部 ===== */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255,255,255,0.97);
  border-radius: 10px;
  padding: 10px 16px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.10);
  backdrop-filter: blur(12px);

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .header-icon-wrap {
    width: 36px;
    height: 36px;
    border-radius: 9px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(102,126,234,0.35);
    flex-shrink: 0;
    .header-icon {
      width: 20px;
      height: 20px;
      color: #fff;
    }
  }

  .header-text {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .page-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0;
    line-height: 1.3;
    letter-spacing: 0.2px;
  }

  .page-subtitle {
    font-size: 0.78rem;
    color: #888;
    line-height: 1;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .stat-pill {
    display: flex;
    align-items: baseline;
    gap: 2px;
    background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08));
    border: 1px solid rgba(102,126,234,0.18);
    border-radius: 20px;
    padding: 3px 12px;

    .stat-num {
      font-size: 1.1rem;
      font-weight: 700;
      color: #667eea;
    }
    .stat-label {
      font-size: 0.75rem;
      color: #888;
    }
  }

  .add-btn {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    box-shadow: 0 2px 8px rgba(102,126,234,0.35);
    font-weight: 600;
    transition: all 0.25s ease;
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 14px rgba(102,126,234,0.45);
    }
  }
}

/* ===== 搜索过滤区 ===== */
.filter-bar {
  background: rgba(255,255,255,0.97);
  border-radius: 10px;
  padding: 8px 14px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  backdrop-filter: blur(10px);

  .filter-form {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0;
    margin: 0;

    :deep(.el-form-item) {
      margin-bottom: 0;
      margin-right: 10px;
    }
    :deep(.el-form-item__label) {
      font-size: 0.82rem;
      color: #555;
      padding-right: 6px;
    }
    :deep(.el-input__wrapper),
    :deep(.el-select .el-input__wrapper) {
      border-radius: 6px;
      box-shadow: 0 0 0 1px #dcdfe6 inset;
      &:hover { box-shadow: 0 0 0 1px #c0c4cc inset; }
      &.is-focus { box-shadow: 0 0 0 1px #667eea inset; }
    }
  }
}

/* ===== 表格容器 ===== */
.table-card {
  background: rgba(255,255,255,0.98);
  border-radius: 10px;
  padding: 10px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.09);
  backdrop-filter: blur(10px);
  flex: 1;
  overflow: hidden;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  gap: 12px;

  .empty-icon { font-size: 3.5rem; opacity: 0.4; }
  .empty-text { font-size: 0.9rem; color: #909399; }
}

/* ===== 表格样式 ===== */
.supplier-table {
  :deep(.el-table__header-wrapper) {
    th { border-bottom: 2px solid #e2e8f5 !important; }
  }
  :deep(.el-table__body-wrapper) {
    tr { transition: background 0.15s; }
    td { border-bottom: 1px solid #f3f4f6 !important; }
  }
  :deep(.el-table__fixed-right) { box-shadow: -2px 0 8px rgba(0,0,0,0.05); }
  :deep(.el-table__fixed) { box-shadow: 2px 0 8px rgba(0,0,0,0.05); }
}

.code-badge {
  font-size: 11.5px;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #5b6de0;
  background: rgba(91,109,224,0.07);
  border-radius: 4px;
  padding: 1px 6px;
  letter-spacing: 0.3px;
}

.lead-time-badge {
  font-size: 13px;
  font-weight: 700;
  color: #667eea;
  em {
    font-style: normal;
    font-size: 11px;
    font-weight: 400;
    color: #999;
    margin-left: 1px;
  }
}

.status-dot {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  font-weight: 600;
  border-radius: 10px;
  padding: 2px 8px;

  &::before {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  &.active {
    color: #26a65b;
    background: rgba(38,166,91,0.09);
    &::before { background: #26a65b; }
  }
  &.inactive {
    color: #909399;
    background: rgba(144,147,153,0.09);
    &::before { background: #c0c4cc; }
  }
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;

  :deep(.el-divider--vertical) {
    height: 14px;
    margin: 0 2px;
    border-color: #e4e7ed;
  }
  :deep(.el-button) {
    padding: 0 5px;
    font-size: 12px;
  }
}

/* ===== 对话框 ===== */
.supplier-dialog {
  :deep(.el-dialog) {
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0,0,0,0.18);
  }
  :deep(.el-dialog__header) {
    padding: 0;
    border-bottom: none;
  }
  :deep(.el-dialog__headerbtn) {
    top: 14px;
    right: 14px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: rgba(255,255,255,0.2);
    &:hover { background: rgba(255,255,255,0.35); }
    .el-dialog__close { color: #fff; font-size: 16px; }
  }
  :deep(.el-dialog__body) {
    padding: 0;
    max-height: 70vh;
    overflow-y: auto;
    &::-webkit-scrollbar { width: 5px; }
    &::-webkit-scrollbar-track { background: #f5f5f5; }
    &::-webkit-scrollbar-thumb { background: #d0d0d0; border-radius: 3px; }
  }
  :deep(.el-dialog__footer) {
    padding: 10px 18px;
    border-top: 1px solid #ebeef5;
    background: #fafbfc;
  }
}

/* 对话框头部 */
.dialog-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .dh-icon-wrap {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: rgba(255,255,255,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    .dh-icon { width: 18px; height: 18px; color: #fff; }
  }

  .dh-text {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .dh-title {
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    line-height: 1.3;
  }

  .dh-sub {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.75);
    line-height: 1;
  }

  .dh-badge {
    font-size: 0.7rem;
    font-weight: 700;
    border-radius: 6px;
    padding: 3px 9px;
    letter-spacing: 0.5px;
    &.new {
      background: rgba(255,255,255,0.25);
      color: #fff;
      border: 1px solid rgba(255,255,255,0.4);
    }
    &.edit {
      background: rgba(255,200,80,0.25);
      color: #ffe07a;
      border: 1px solid rgba(255,200,80,0.4);
    }
  }
}

/* 表单 */
.supplier-form {
  padding: 14px 18px 6px;

  .form-group {
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f0f2f5;
    &.last {
      margin-bottom: 0;
      padding-bottom: 0;
      border-bottom: none;
    }
  }

  .group-label {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.78rem;
    font-weight: 700;
    color: #667eea;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    text-transform: uppercase;

    .gl-bar {
      width: 3px;
      height: 13px;
      border-radius: 2px;
      background: linear-gradient(180deg, #667eea, #764ba2);
      flex-shrink: 0;
    }
  }

  :deep(.el-form-item) {
    margin-bottom: 8px;
    &:last-child { margin-bottom: 0; }
  }

  :deep(.el-form-item__label) {
    font-size: 0.82rem;
    font-weight: 500;
    color: #555;
    line-height: 28px;
    padding-right: 8px;
  }

  :deep(.el-form-item__content) { line-height: 28px; }

  :deep(.el-form-item__error) {
    font-size: 0.72rem;
    padding-top: 2px;
  }

  :deep(.el-input),
  :deep(.el-select),
  :deep(.el-input-number) { width: 100%; }

  :deep(.el-input__wrapper),
  :deep(.el-select .el-input__wrapper) {
    box-shadow: 0 0 0 1px #dcdfe6 inset;
    border-radius: 6px;
    transition: all 0.2s;
    padding: 0 9px;
    &:hover { box-shadow: 0 0 0 1px #c0c4cc inset; background: #fafafa; }
    &.is-focus { box-shadow: 0 0 0 1px #667eea inset, 0 0 0 3px rgba(102,126,234,0.1); }
  }

  :deep(.el-input-number .el-input__wrapper) { padding-right: 0; }

  :deep(.el-textarea .el-textarea__inner) {
    border-radius: 6px;
    box-shadow: 0 0 0 1px #dcdfe6 inset;
    padding: 7px 10px;
    font-size: 0.82rem;
    resize: vertical;
    min-height: 56px;
    transition: all 0.2s;
    &:hover { box-shadow: 0 0 0 1px #c0c4cc inset; }
    &:focus { box-shadow: 0 0 0 1px #667eea inset, 0 0 0 3px rgba(102,126,234,0.1); }
  }

  :deep(.is-error-input .el-input__wrapper) {
    box-shadow: 0 0 0 1px #f56c6c inset !important;
  }

  .field-error {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 3px;
    font-size: 0.72rem;
    color: #f56c6c;
    animation: fadeSlideIn 0.25s ease;
    .el-icon { font-size: 12px; }
  }

  .unit-input-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    .unit-label {
      font-size: 0.82rem;
      color: #888;
      font-weight: 500;
      white-space: nowrap;
    }
    :deep(.el-input-number) { flex: 1; }
  }
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;

  :deep(.el-button) {
    min-width: 80px;
    font-weight: 600;
    transition: all 0.25s ease;
    &:hover { transform: translateY(-1px); }
  }
  :deep(.el-button--primary) {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    box-shadow: 0 2px 8px rgba(102,126,234,0.35);
    &:hover { box-shadow: 0 4px 14px rgba(102,126,234,0.45); }
  }
}

@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(-3px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .page-header {
    flex-wrap: wrap;
    gap: 8px;
    .header-right { width: 100%; justify-content: flex-end; }
  }
  .filter-bar .filter-form {
    flex-direction: column;
    align-items: stretch;
    :deep(.el-form-item) { width: 100%; margin-right: 0; }
  }
  .supplier-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 5vh auto !important;
  }
}
</style>
