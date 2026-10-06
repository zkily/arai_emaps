<template>
  <div class="suppliers-page sp-modern pb-std">
    <!-- 页面头部 -->
    <div class="page-header pb-hero pb-hero--page">
      <div class="head-fx pb-bubbles" aria-hidden="true" />
      <div class="header-left">
        <div class="header-icon-wrap">
          <OfficeBuilding class="header-icon" />
        </div>
        <div class="header-text">
          <h1 class="page-title pb-hero-title">外注先マスタ</h1>
          <p class="page-subtitle pb-hero-desc">
            メッキ・溶接・切断などの外注業者を種別・状態で絞り込み、登録・編集・有効切替
          </p>
        </div>
      </div>
      <div class="header-right">
        <div class="stat-pill">
          <span class="stat-dot" aria-hidden="true" />
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
              <el-button class="ra-btn ra-btn--edit" size="small" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>編集
              </el-button>
              <el-button class="ra-btn ra-btn--delete" size="small" @click="handleDelete(row)">
                削除
              </el-button>
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
      class="supplier-dialog osp-dialog pb-std"
      :close-on-click-modal="false"
      :show-close="false"
      align-center
    >
      <template #header>
        <div class="dialog-header pb-hero" :class="isEdit ? 'is-edit' : 'is-new'">
          <div class="head-fx pb-bubbles" aria-hidden="true" />
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
          <el-icon class="dh-close" @click="dialogVisible = false"><Close /></el-icon>
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
          <el-button class="dlg-btn" @click="dialogVisible = false" size="small">キャンセル</el-button>
          <el-button
            type="primary"
            class="dlg-btn dlg-btn--save"
            @click="handleSubmit"
            :loading="submitting"
            size="small"
          >
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
import { OfficeBuilding, Plus, Search, Edit, Check, Warning, Close } from '@element-plus/icons-vue'
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
  min-height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-sizing: border-box;
  background: linear-gradient(180deg, #f3f1ff 0%, #f8fafc 34%, #f8fafc 100%);
}

/* ============================================================ */
/* 页面美化：现代 UI / 颜色区分（外注先＝インディゴ〜バイオレット系） */
/* ============================================================ */

/* ===== ヒーロー ===== */
.page-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 14px;
  background: linear-gradient(125deg, #4c51bf 0%, #5a67d8 36%, #667eea 62%, #764ba2 100%);
  box-shadow:
    0 12px 28px -18px rgba(102, 126, 234, 0.65),
    0 1px 2px rgba(15, 23, 42, 0.06);

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }

  .header-icon-wrap {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
    border: 1px solid rgba(255, 255, 255, 0.42);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.35),
      inset 0 -2px 0 rgba(49, 46, 129, 0.3);

    .header-icon {
      width: 20px;
      height: 20px;
      color: #fff;
    }
  }

  .header-text {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    min-width: 0;
  }

  .page-title {
    margin: 0;
    font-weight: 800;
    letter-spacing: 0.04em;
    color: #fff;
  }

  .page-subtitle {
    margin: 0;
    letter-spacing: 0.02em;
    color: rgba(255, 255, 255, 0.86);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  /* 件数：白ピル＋同色ドット */
  .stat-pill {
    display: flex;
    align-items: center;
    gap: 4px;
    height: 30px;
    padding: 0 14px 0 12px;
    box-sizing: border-box;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.9);
    background: linear-gradient(180deg, #ffffff 0%, #f3f1ff 100%);
    box-shadow:
      inset 0 1px 0 #ffffff,
      inset 0 -2px 0 rgba(148, 163, 184, 0.25),
      0 6px 14px -10px rgba(15, 23, 42, 0.45);

    .stat-dot {
      width: 7px;
      height: 7px;
      margin-right: 3px;
      border-radius: 50%;
      background: #6d28d9;
      box-shadow: 0 0 0 3px rgba(109, 40, 217, 0.15);
    }

    .stat-num {
      font-size: 16px;
      font-weight: 800;
      color: #5b21b6;
      font-variant-numeric: tabular-nums;
    }

    .stat-label {
      font-size: 11px;
      font-weight: 600;
      color: #64748b;
    }
  }

  /* 新規登録：白ピル（緑文字） */
  .add-btn {
    --k-rgb: 5 150 105;
    height: 30px;
    padding: 0 14px;
    border-radius: 999px;
    font-weight: 700;
    color: #047857;
    border: 1px solid rgba(255, 255, 255, 0.9);
    background: linear-gradient(180deg, #ffffff 0%, #ecfdf5 100%);

    &:hover,
    &:focus-visible {
      color: #065f46;
      border-color: #fff;
      background: #fff;
    }
  }
}

/* ===== 検索カード ===== */
.filter-bar {
  position: relative;
  overflow: hidden;
  padding: 11px 14px 8px;
  border-radius: 12px;
  border: 1px solid #e4e1fb;
  background: linear-gradient(180deg, #ffffff 0%, #faf9ff 100%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(91, 33, 182, 0.45);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #667eea 0%, #8b5cf6 60%, #a78bfa 100%);
  }

  .filter-form {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px 0;
    margin: 0;

    :deep(.el-form-item) {
      margin-bottom: 0;
      margin-right: 12px;
    }

    :deep(.el-form-item__label) {
      height: 22px;
      margin: auto 8px auto 0;
      padding: 0 10px;
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      line-height: 22px;
      color: #4c1d95;
      background: #f1eefe;
      box-shadow:
        inset 0 1px 0 #ffffff,
        inset 0 -1px 0 #ddd6fe;
    }

    /* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
    :deep(.el-input__wrapper),
    :deep(.el-select__wrapper) {
      border-radius: 8px;
      background-color: #fff;
      box-shadow: 0 0 0 1px #dcd7f7 inset;

      &:hover {
        box-shadow: 0 0 0 1px #c4b5fd inset;
      }

      &.is-focus,
      &.is-focused {
        box-shadow:
          0 0 0 1px #7c3aed inset,
          0 0 0 3px rgba(124, 58, 237, 0.14);
      }
    }
  }
}

/* ===== テーブルカード ===== */
.table-card {
  position: relative;
  flex: 1;
  overflow: hidden;
  padding: 12px 10px 10px;
  border-radius: 12px;
  border: 1px solid #e4e1fb;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(91, 33, 182, 0.4);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #667eea 0%, #8b5cf6 60%, #a78bfa 100%);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 50px 20px;

  .empty-icon {
    font-size: 3.5rem;
    opacity: 0.45;
  }

  .empty-text {
    font-size: 13px;
    font-weight: 600;
    color: #64748b;
  }

  :deep(.el-button--primary) {
    --k-rgb: 124 58 237;
    border: 1px solid #6d28d9;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
      linear-gradient(135deg, #8b5cf6, #6d28d9);
  }
}

/* ===== テーブル ===== */
.supplier-table {
  border-radius: 10px;
  --el-table-border-color: #ece9f8;
  --el-table-row-hover-bg-color: #f3f0ff;
  --el-table-current-row-bg-color: #ede9fe;

  :deep(th.el-table__cell) {
    color: #4c1d95 !important;
    font-weight: 700 !important;
    background: #f5f3ff !important;
    border-bottom: 1px solid #ddd6fe !important;
  }

  :deep(td.el-table__cell) {
    color: #1e293b;
    border-bottom: 1px solid #f1eff9 !important;
  }

  :deep(.el-table__row--striped td.el-table__cell) {
    background: #fcfbff;
  }

  :deep(.el-table__body tr:hover > td.el-table__cell) {
    background-color: #f3f0ff !important;
  }

  :deep(.el-table__body tr.current-row > td.el-table__cell) {
    background-color: #ede9fe !important;
  }

  :deep(.el-switch.is-checked .el-switch__core) {
    border-color: #10b981;
    background-color: #10b981;
  }
}

.code-badge {
  padding: 1px 8px;
  border-radius: 999px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #5b21b6;
  background: #f3f0ff;
  box-shadow:
    inset 0 0 0 1px #ddd6fe,
    inset 0 -1px 0 #c4b5fd;
}

.lead-time-badge {
  font-size: 13px;
  font-weight: 800;
  color: #6d28d9;
  font-variant-numeric: tabular-nums;

  em {
    margin-left: 1px;
    font-style: normal;
    font-size: 11px;
    font-weight: 500;
    color: #94a3b8;
  }
}

.status-dot {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11.5px;
  font-weight: 600;

  &::before {
    content: '';
    flex-shrink: 0;
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  &.active {
    color: #26a65b;
    background: rgba(38, 166, 91, 0.09);

    &::before {
      background: #26a65b;
    }
  }

  &.inactive {
    color: #909399;
    background: rgba(144, 147, 153, 0.09);

    &::before {
      background: #c0c4cc;
    }
  }
}

/* 行操作：淡色ピル */
.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;

  .ra-btn {
    height: 22px;
    margin: 0;
    padding: 0 8px;
    border-radius: 999px;
    font-size: 11.5px;
    font-weight: 700;

    .el-icon {
      margin-right: 2px;
    }
  }

  .ra-btn--edit {
    --k-rgb: 79 70 229;
    color: #4338ca;
    border: 1px solid #c7d2fe;
    background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);

    &:hover,
    &:focus-visible {
      color: #3730a3;
      border-color: #a5b4fc;
      background: #fff;
    }
  }

  .ra-btn--delete {
    --k-rgb: 225 29 72;
    color: #be123c;
    border: 1px solid #fecdd3;
    background: linear-gradient(180deg, #ffffff 0%, #fff1f2 100%);

    &:hover,
    &:focus-visible {
      color: #9f1239;
      border-color: #fda4af;
      background: #fff;
    }
  }
}

/* ===== ダイアログ ===== */
:global(.el-dialog.osp-dialog) {
  padding: 0;
  overflow: hidden;
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);
}

:global(.el-dialog.osp-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

:global(.el-dialog.osp-dialog .el-dialog__body) {
  padding: 0;
  max-height: 70vh;
  overflow-y: auto;
}

:global(.el-dialog.osp-dialog .el-dialog__footer) {
  padding: 10px 18px 14px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.dialog-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(125deg, #4c51bf 0%, #5a67d8 36%, #667eea 62%, #764ba2 100%);

  &.is-edit {
    background: linear-gradient(125deg, #b45309 0%, #d97706 45%, #f59e0b 100%);
  }

  .dh-icon-wrap {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 11px;
    background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
    border: 1px solid rgba(255, 255, 255, 0.42);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.35),
      inset 0 -2px 0 rgba(30, 27, 75, 0.25);

    .dh-icon {
      width: 18px;
      height: 18px;
      color: #fff;
    }
  }

  .dh-text {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .dh-title {
    font-size: 16px;
    font-weight: 800;
    line-height: 1.3;
    letter-spacing: 0.03em;
    color: #fff;
  }

  .dh-sub {
    font-size: 11px;
    line-height: 1.5;
    color: rgba(255, 255, 255, 0.86);
  }

  .dh-badge {
    flex-shrink: 0;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
    border: 1px solid rgba(255, 255, 255, 0.9);
    background: #fff;

    &.new {
      color: #4338ca;
    }

    &.edit {
      color: #b45309;
    }
  }

  .dh-close {
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

    &:hover {
      background: rgba(255, 255, 255, 0.3);
      transform: translateY(-1px);
    }
  }
}

/* 表单 */
.supplier-form {
  padding: 14px 18px 6px;

  .form-group {
    position: relative;
    margin-bottom: 10px;
    padding: 12px 12px 10px;
    overflow: hidden;
    border-radius: 10px;
    border: 1px solid #e4e1fb;
    background: linear-gradient(180deg, #ffffff 0%, #fbfaff 100%);

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, #a5b4fc, #8b5cf6);
    }

    &.last {
      margin-bottom: 0;
    }
  }

  .group-label {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 8px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #4c1d95;

    .gl-bar {
      flex-shrink: 0;
      width: 3px;
      height: 13px;
      border-radius: 2px;
      background: linear-gradient(180deg, #667eea, #764ba2);
    }
  }

  :deep(.el-form-item) {
    margin-bottom: 8px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  :deep(.el-form-item__label) {
    padding-right: 8px;
    font-size: 12.5px;
    font-weight: 600;
    line-height: 28px;
    color: #475569;
  }

  :deep(.el-form-item__content) {
    line-height: 28px;
  }

  :deep(.el-form-item__error) {
    padding-top: 2px;
    font-size: 11px;
  }

  :deep(.el-input),
  :deep(.el-select),
  :deep(.el-input-number) {
    width: 100%;
  }

  :deep(.el-input__wrapper),
  :deep(.el-select__wrapper) {
    padding: 0 9px;
    border-radius: 8px;
    box-shadow: 0 0 0 1px #dcd7f7 inset;
    transition:
      box-shadow 0.2s ease,
      background-color 0.2s ease;

    &:hover {
      box-shadow: 0 0 0 1px #c4b5fd inset;
    }

    &.is-focus,
    &.is-focused {
      box-shadow:
        0 0 0 1px #7c3aed inset,
        0 0 0 3px rgba(124, 58, 237, 0.14);
    }
  }

  :deep(.el-input.is-disabled .el-input__wrapper) {
    background-color: #f1f5f9;
    box-shadow: 0 0 0 1px #e2e8f0 inset;
  }

  :deep(.el-input-number .el-input__wrapper) {
    padding-right: 0;
  }

  :deep(.el-textarea .el-textarea__inner) {
    min-height: 56px;
    padding: 7px 10px;
    border-radius: 8px;
    font-size: 12.5px;
    resize: vertical;
    box-shadow: 0 0 0 1px #dcd7f7 inset;
    transition: box-shadow 0.2s ease;

    &:hover {
      box-shadow: 0 0 0 1px #c4b5fd inset;
    }

    &:focus {
      box-shadow:
        0 0 0 1px #7c3aed inset,
        0 0 0 3px rgba(124, 58, 237, 0.14);
    }
  }

  :deep(.is-error-input .el-input__wrapper) {
    box-shadow: 0 0 0 1px #f56c6c inset !important;
  }

  .field-error {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 3px;
    font-size: 11px;
    color: #e11d48;

    .el-icon {
      font-size: 12px;
    }
  }

  .unit-input-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;

    .unit-label {
      font-size: 12.5px;
      font-weight: 600;
      white-space: nowrap;
      color: #64748b;
    }

    :deep(.el-input-number) {
      flex: 1;
    }
  }
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;

  .dlg-btn {
    --k-rgb: 100 116 139;
    min-width: 84px;
    height: 30px;
    margin: 0;
    border-radius: 8px;
    font-weight: 700;
    color: #475569;
    border: 1px solid #cbd5e1;
    background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);

    &:hover,
    &:focus-visible {
      color: #334155;
      border-color: #94a3b8;
      background: #fff;
    }
  }

  .dlg-btn--save {
    --k-rgb: 124 58 237;
    color: #fff;
    border-color: #6d28d9;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
      linear-gradient(135deg, #8b5cf6, #6d28d9);

    &:hover,
    &:focus-visible {
      color: #fff;
      border-color: #5b21b6;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
        linear-gradient(135deg, #9b70f8, #7c3aed);
    }
  }
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .page-header {
    flex-wrap: wrap;
    gap: 8px;

    .header-right {
      width: 100%;
      justify-content: flex-end;
    }
  }

  .filter-bar .filter-form {
    flex-direction: column;
    align-items: stretch;

    :deep(.el-form-item) {
      width: 100%;
      margin-right: 0;
    }
  }

  :global(.el-dialog.osp-dialog) {
    width: 95% !important;
    margin: 5vh auto !important;
  }
}
</style>
