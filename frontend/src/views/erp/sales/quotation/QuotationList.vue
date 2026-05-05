<template>
  <div class="page-root">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <!-- Header -->
    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="26"><Document /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">見積管理</h1>
            <span class="header-subtitle">Quotation Management</span>
          </div>
        </div>
        <div class="header-badges">
          <span class="badge badge-total">合計 <b>{{ pagination.total }}</b></span>
          <span class="badge badge-draft">下書き <b>{{ draftCount }}</b></span>
        </div>
      </div>
    </div>

    <!-- Search / Filter -->
    <div class="glass-card filter-bar animate-in" style="animation-delay:.08s">
      <el-input
        v-model="query.keyword"
        placeholder="見積番号・顧客名で検索"
        clearable
        :prefix-icon="Search"
        class="dark-input filter-input"
        @keyup.enter="fetchData"
      />
      <el-select
        v-model="query.status"
        placeholder="ステータス"
        clearable
        class="dark-input filter-select"
        @change="fetchData"
      >
        <el-option label="下書き" value="draft" />
        <el-option label="送付済" value="sent" />
        <el-option label="受諾" value="accepted" />
        <el-option label="却下" value="rejected" />
        <el-option label="期限切れ" value="expired" />
      </el-select>
      <el-date-picker
        v-model="query.dateRange"
        type="daterange"
        range-separator="〜"
        start-placeholder="開始日"
        end-placeholder="終了日"
        value-format="YYYY-MM-DD"
        class="dark-input filter-date"
        @change="fetchData"
      />
      <el-button class="gradient-btn" :icon="Search" @click="fetchData">検索</el-button>
      <el-button class="gradient-btn create-btn" :icon="Plus" @click="openDialog()">新規作成</el-button>
    </div>

    <!-- Table -->
    <div class="glass-card table-card animate-in" style="animation-delay:.14s">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        class="dark-table"
        :header-cell-style="headerStyle"
        :row-style="rowStyle"
        empty-text="データがありません"
      >
        <el-table-column prop="quotation_no" label="見積番号" min-width="140" />
        <el-table-column prop="customer_name" label="顧客名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quotation_date" label="見積日" width="120" />
        <el-table-column prop="valid_until" label="有効期限" width="120" />
        <el-table-column label="合計金額" width="140" align="right">
          <template #default="{ row }">{{ formatYen(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="ステータス" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="dark" round>
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="アクション" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link size="small" class="action-link" @click="openDialog(row)">編集</el-button>
            <el-button
              v-if="row.status === 'draft'"
              link size="small" class="action-link send"
              @click="handleSend(row)"
            >送付</el-button>
            <el-button
              v-if="row.status === 'accepted'"
              link size="small" class="action-link convert"
              @click="handleConvert(row)"
            >受注変換</el-button>
            <el-button
              v-if="row.status === 'draft'"
              link size="small" class="action-link danger"
              @click="handleDelete(row)"
            >削除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- Create / Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '見積編集' : '新規見積作成'"
      width="780px"
      destroy-on-close
      class="dark-dialog"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="110px" class="dark-form">
        <div class="form-grid">
          <el-form-item label="顧客コード" prop="customer_code">
            <el-input v-model="form.customer_code" placeholder="顧客コード" />
          </el-form-item>
          <el-form-item label="顧客名" prop="customer_name">
            <el-input v-model="form.customer_name" placeholder="顧客名" />
          </el-form-item>
          <el-form-item label="見積日" prop="quotation_date">
            <el-date-picker v-model="form.quotation_date" type="date" value-format="YYYY-MM-DD" placeholder="見積日" style="width:100%" />
          </el-form-item>
          <el-form-item label="有効期限" prop="valid_until">
            <el-date-picker v-model="form.valid_until" type="date" value-format="YYYY-MM-DD" placeholder="有効期限" style="width:100%" />
          </el-form-item>
          <el-form-item label="営業担当">
            <el-input v-model="form.sales_person" placeholder="営業担当" />
          </el-form-item>
          <el-form-item label="備考">
            <el-input v-model="form.remarks" type="textarea" :rows="2" placeholder="備考" />
          </el-form-item>
        </div>

        <!-- Dynamic Items -->
        <div class="items-section">
          <div class="items-header">
            <span class="items-title">明細行</span>
            <el-button size="small" class="gradient-btn" :icon="Plus" @click="addItem">行追加</el-button>
          </div>
          <el-table :data="form.items" border class="dark-table items-table" :header-cell-style="headerStyle">
            <el-table-column type="index" label="#" width="45" />
            <el-table-column label="品番" min-width="130">
              <template #default="{ row }">
                <el-input v-model="row.product_code" size="small" placeholder="品番" />
              </template>
            </el-table-column>
            <el-table-column label="品名" min-width="150">
              <template #default="{ row }">
                <el-input v-model="row.product_name" size="small" placeholder="品名" />
              </template>
            </el-table-column>
            <el-table-column label="数量" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" size="small" :min="0" controls-position="right" style="width:100%" @change="calcAmount(row)" />
              </template>
            </el-table-column>
            <el-table-column label="単価" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.unit_price" size="small" :min="0" :precision="2" controls-position="right" style="width:100%" @change="calcAmount(row)" />
              </template>
            </el-table-column>
            <el-table-column label="金額" width="120" align="right">
              <template #default="{ row }">{{ formatYen(row.amount) }}</template>
            </el-table-column>
            <el-table-column label="" width="55" align="center">
              <template #default="{ $index }">
                <el-button link size="small" class="action-link danger" @click="removeItem($index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="items-total">合計: <b>{{ formatYen(itemsTotal) }}</b></div>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" class="gradient-btn" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Document, Search, Plus, Delete } from '@element-plus/icons-vue'
import {
  getQuotations,
  createQuotation,
  updateQuotation,
  sendQuotation,
  deleteQuotation,
  convertQuotationToOrder,
} from '@/api/erp/sales'

interface QuotationItem {
  product_code: string
  product_name: string
  quantity: number
  unit_price: number
  amount: number
}

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const tableData = ref<any[]>([])
const draftCount = computed(() => tableData.value.filter(r => r.status === 'draft').length)

const query = reactive({
  keyword: '',
  status: '',
  dateRange: null as [string, string] | null,
})

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const emptyItem = (): QuotationItem => ({ product_code: '', product_name: '', quantity: 0, unit_price: 0, amount: 0 })

const form = reactive({
  customer_code: '',
  customer_name: '',
  quotation_date: '',
  valid_until: '',
  sales_person: '',
  remarks: '',
  items: [emptyItem()] as QuotationItem[],
})

const formRules: FormRules = {
  customer_code: [{ required: true, message: '顧客コードは必須です', trigger: 'blur' }],
  customer_name: [{ required: true, message: '顧客名は必須です', trigger: 'blur' }],
  quotation_date: [{ required: true, message: '見積日は必須です', trigger: 'change' }],
  valid_until: [{ required: true, message: '有効期限は必須です', trigger: 'change' }],
}

const itemsTotal = computed(() => form.items.reduce((s, i) => s + (i.amount || 0), 0))

const headerStyle = () => ({
  background: 'linear-gradient(135deg, rgba(59,130,246,.25), rgba(139,92,246,.18))',
  color: '#e2e8f0',
  borderBottom: '1px solid rgba(255,255,255,.08)',
  fontSize: '12px',
  padding: '8px 0',
})

const rowStyle = () => ({
  background: 'transparent',
  color: '#cbd5e1',
  fontSize: '13px',
})

function formatYen(n: number | undefined): string {
  if (n == null) return '¥0'
  return `¥${Number(n).toLocaleString('ja-JP')}`
}

const STATUS_MAP: Record<string, { label: string; type: string }> = {
  draft: { label: '下書き', type: 'info' },
  sent: { label: '送付済', type: 'warning' },
  accepted: { label: '受諾', type: 'success' },
  rejected: { label: '却下', type: 'danger' },
  expired: { label: '期限切れ', type: 'info' },
}
function statusLabel(s: string) { return STATUS_MAP[s]?.label ?? s }
function statusType(s: string) { return (STATUS_MAP[s]?.type ?? 'info') as any }

function calcAmount(row: QuotationItem) {
  row.amount = (row.quantity || 0) * (row.unit_price || 0)
}
function addItem() { form.items.push(emptyItem()) }
function removeItem(idx: number) { form.items.splice(idx, 1) }

function resetForm() {
  Object.assign(form, {
    customer_code: '',
    customer_name: '',
    quotation_date: '',
    valid_until: '',
    sales_person: '',
    remarks: '',
    items: [emptyItem()],
  })
  isEdit.value = false
  editId.value = null
}

function openDialog(row?: any) {
  resetForm()
  if (row) {
    isEdit.value = true
    editId.value = row.id
    Object.assign(form, {
      customer_code: row.customer_code ?? '',
      customer_name: row.customer_name ?? '',
      quotation_date: row.quotation_date ?? '',
      valid_until: row.valid_until ?? '',
      sales_person: row.sales_person ?? '',
      remarks: row.remarks ?? '',
      items: (row.items?.length ? row.items : [emptyItem()]).map((i: any) => ({ ...i })),
    })
  }
  dialogVisible.value = true
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (query.keyword) params.keyword = query.keyword
    if (query.status) params.status = query.status
    if (query.dateRange?.[0]) params.start_date = query.dateRange[0]
    if (query.dateRange?.[1]) params.end_date = query.dateRange[1]

    const res: any = await getQuotations(params)
    const data = res?.data ?? res
    tableData.value = data?.items ?? data?.records ?? data?.list ?? (Array.isArray(data) ? data : [])
    pagination.total = data?.total ?? tableData.value.length
  } catch (e: any) {
    console.error('Failed to fetch quotations', e)
    tableData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { ...form, total_amount: itemsTotal.value }
    if (isEdit.value && editId.value != null) {
      await updateQuotation(editId.value, payload)
      ElMessage.success('見積を更新しました')
    } else {
      await createQuotation(payload)
      ElMessage.success('見積を作成しました')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function handleSend(row: any) {
  await ElMessageBox.confirm(`見積 ${row.quotation_no} を送付しますか？`, '確認', { type: 'warning' })
  try {
    await sendQuotation(row.id)
    ElMessage.success('送付しました')
    fetchData()
  } catch (e: any) {
    ElMessage.error(e?.message || '送付に失敗しました')
  }
}

async function handleConvert(row: any) {
  await ElMessageBox.confirm(`見積 ${row.quotation_no} を受注に変換しますか？`, '確認', { type: 'info' })
  try {
    await convertQuotationToOrder(row.id)
    ElMessage.success('受注に変換しました')
    fetchData()
  } catch (e: any) {
    ElMessage.error(e?.message || '変換に失敗しました')
  }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm(`見積 ${row.quotation_no} を削除しますか？`, '確認', { type: 'error' })
  try {
    await deleteQuotation(row.id)
    ElMessage.success('削除しました')
    fetchData()
  } catch (e: any) {
    ElMessage.error(e?.message || '削除に失敗しました')
  }
}

onMounted(fetchData)
</script>

<style scoped>
/* ===== Layout ===== */
.page-root {
  position: relative;
  min-height: 100vh;
  padding: 16px;
  overflow: hidden;
}

/* ===== Animated background (matches Sales.vue) ===== */
.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}
.orb-1 { width: 400px; height: 400px; top: -100px; left: -100px; background: radial-gradient(circle, #3b82f6, transparent); }
.orb-2 { width: 350px; height: 350px; top: 40%; right: -80px; background: radial-gradient(circle, #8b5cf6, transparent); animation-delay: -7s; }
.orb-3 { width: 300px; height: 300px; bottom: -50px; left: 30%; background: radial-gradient(circle, #06b6d4, transparent); animation-delay: -14s; }
.noise-overlay {
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
}
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

/* ===== Glass card base ===== */
.glass-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  margin-bottom: 12px;
}

/* ===== Header ===== */
.glass-header {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 14px 22px;
  margin-bottom: 12px;
}
.header-content { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon {
  width: 46px; height: 46px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 13px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
}
.header-title { font-size: 1.35rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.75rem; color: rgba(255, 255, 255, 0.55); }
.header-badges { display: flex; gap: 8px; }
.badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(8px);
}
.badge b { font-weight: 700; margin-left: 2px; }
.badge-total { background: rgba(59, 130, 246, 0.2); }
.badge-draft { background: rgba(139, 92, 246, 0.2); }

/* ===== Filter bar ===== */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  flex-wrap: wrap;
}
.filter-input { width: 220px; }
.filter-select { width: 150px; }
.filter-date { width: 260px; }

/* ===== Dark input overrides ===== */
:deep(.dark-input .el-input__wrapper),
:deep(.dark-input .el-select__wrapper),
:deep(.dark-form .el-input__wrapper),
:deep(.dark-form .el-textarea__inner),
:deep(.dark-form .el-select__wrapper) {
  background: rgba(255, 255, 255, 0.07) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  box-shadow: none !important;
  border-radius: 8px;
  color: #e2e8f0;
}
:deep(.dark-input .el-input__inner),
:deep(.dark-form .el-input__inner) {
  color: #e2e8f0 !important;
}
:deep(.dark-input .el-input__inner::placeholder),
:deep(.dark-form .el-input__inner::placeholder),
:deep(.dark-form .el-textarea__inner::placeholder) {
  color: rgba(255, 255, 255, 0.35);
}
:deep(.dark-form .el-form-item__label) {
  color: rgba(255, 255, 255, 0.7) !important;
  font-size: 13px;
}
:deep(.dark-form .el-textarea__inner) {
  color: #e2e8f0 !important;
}

/* ===== Gradient buttons ===== */
.gradient-btn {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
  border: none !important;
  color: #fff !important;
  border-radius: 8px;
  font-weight: 600;
  transition: transform 0.2s, box-shadow 0.2s;
}
.gradient-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.45);
}
.create-btn {
  background: linear-gradient(135deg, #10b981, #059669) !important;
}
.create-btn:hover {
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.45);
}

/* ===== Table ===== */
.table-card { padding: 0; overflow: hidden; }
:deep(.dark-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-header-bg-color: transparent;
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-text-color: #cbd5e1;
  --el-table-header-text-color: #e2e8f0;
  --el-fill-color-lighter: rgba(255, 255, 255, 0.03);
  background: transparent !important;
}
:deep(.dark-table .el-table__inner-wrapper::before),
:deep(.dark-table .el-table__border-left-patch) {
  display: none;
}
:deep(.dark-table th.el-table__cell) {
  font-weight: 600;
}
:deep(.dark-table td.el-table__cell) {
  padding: 6px 0;
  border-color: rgba(255, 255, 255, 0.05);
}
:deep(.dark-table .el-table__empty-block) {
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
}

.action-link { color: #60a5fa !important; font-weight: 500; }
.action-link.send { color: #fbbf24 !important; }
.action-link.convert { color: #34d399 !important; }
.action-link.danger { color: #f87171 !important; }

/* ===== Pagination ===== */
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
}
:deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: rgba(255, 255, 255, 0.6);
  --el-pagination-button-bg-color: rgba(255, 255, 255, 0.06);
  --el-pagination-button-color: rgba(255, 255, 255, 0.7);
  --el-pagination-hover-color: #60a5fa;
}
:deep(.el-pagination .is-active) {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
  color: #fff !important;
  border-radius: 6px;
}
:deep(.el-pagination button:disabled) { color: rgba(255, 255, 255, 0.2) !important; }

/* ===== Dialog ===== */
:deep(.dark-dialog .el-dialog) {
  background: linear-gradient(160deg, #1e1b4b, #0f172a) !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
}
:deep(.dark-dialog .el-dialog__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 16px 20px 12px;
}
:deep(.dark-dialog .el-dialog__title) { color: #f1f5f9; font-weight: 700; }
:deep(.dark-dialog .el-dialog__headerbtn .el-dialog__close) { color: rgba(255, 255, 255, 0.5); }
:deep(.dark-dialog .el-dialog__body) { padding: 16px 20px; }
:deep(.dark-dialog .el-dialog__footer) {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 12px 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}

/* Items section */
.items-section { margin-top: 10px; }
.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.items-title { font-size: 0.85rem; font-weight: 600; color: rgba(255, 255, 255, 0.8); }
.items-total {
  text-align: right;
  margin-top: 8px;
  font-size: 0.9rem;
  color: #e2e8f0;
}
:deep(.items-table .el-input-number) {
  --el-input-bg-color: transparent;
}

/* ===== Animations ===== */
.animate-in {
  animation: slideIn 0.45s ease forwards;
  opacity: 0;
  transform: translateY(10px);
}
@keyframes slideIn {
  to { opacity: 1; transform: translateY(0); }
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .page-root { padding: 10px; }
  .filter-bar { flex-direction: column; }
  .filter-input, .filter-select, .filter-date { width: 100%; }
  .form-grid { grid-template-columns: 1fr; }
  .header-badges { margin-top: 6px; }
}
</style>
