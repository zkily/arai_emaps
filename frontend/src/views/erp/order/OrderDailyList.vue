<template>
  <div class="order-daily-list">
    <div class="page-toolbar">
      <div class="toolbar-left">
        <h1 class="toolbar-title">日受注管理</h1>
      </div>
      <div class="toolbar-right">
        <el-button class="tb-btn tb-btn-green" @click="openDialog()">
          <el-icon><Plus /></el-icon>
          <span class="tb-label">新規登録</span>
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-inline">
        <div class="fi-group">
          <el-icon class="fi-icon"><Calendar /></el-icon>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            clearable
            class="fi-date-range"
          />
        </div>
        <div class="fi-sep"></div>
        <div class="fi-group">
          <el-select v-model="filters.destination_cd" placeholder="納入先" clearable filterable class="fi-dest" popper-class="destination-select-popper">
            <el-option v-for="d in destinationOptions" :key="d.cd" :label="`${d.cd} | ${d.name}`" :value="d.cd" />
          </el-select>
        </div>
        <div class="fi-group">
          <el-select v-model="filters.keyword" placeholder="製品" clearable filterable class="fi-product">
            <el-option
              v-for="p in productOptions"
              :key="p.cd"
              :value="p.cd"
              :label="`${p.cd} | ${p.name} | ${p.destination_name || p.destination_cd || '-'}`"
            >
              <div class="product-option-row">
                <span class="product-option-cd">{{ p.cd }}</span>
                <span class="product-option-name">{{ p.name }}</span>
                <span class="product-option-dest">{{ p.destination_name || p.destination_cd || '－' }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
      </div>
    </div>

    <div class="table-section">
      <el-table :data="list" v-loading="loading" stripe border size="small" class="data-table" :default-sort="{ prop: 'date', order: 'ascending' }">
        <el-table-column prop="date" label="日付" width="110" sortable />
        <el-table-column prop="weekday" label="曜日" width="70" align="center" />
        <el-table-column prop="monthly_order_id" label="月受注ID" width="160" show-overflow-tooltip />
        <el-table-column prop="destination_cd" label="納入先CD" width="100" />
        <el-table-column prop="destination_name" label="納入先名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="product_cd" label="製品CD" width="100" />
        <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="product_type" label="種別" width="90" />
        <el-table-column prop="forecast_units" label="内示本数" width="90" align="right" />
        <el-table-column prop="confirmed_boxes" label="確定箱数" width="90" align="right" />
        <el-table-column prop="confirmed_units" label="確定本数" width="90" align="right" />
        <el-table-column prop="status" label="ステータス" width="90" />
        <el-table-column prop="delivery_date" label="納入日" width="110" />
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openDialog(row)">編集</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          background
        />
      </div>
    </div>

    <el-dialog 
      v-model="dialogVisible" 
      :title="editId ? '日別受注編集' : '新規受注追加（試作品・補給品等）'" 
      width="540px" 
      destroy-on-close 
      @close="resetForm"
      class="daily-order-dialog compact-dialog"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px" class="modern-form compact-form" size="default">
        <!-- 日付情報セクション -->
        <div class="form-section compact-section">
          <div class="section-header compact-header">
            <el-icon class="section-icon"><Calendar /></el-icon>
            <span class="section-title">日付情報</span>
          </div>
          <div class="section-content compact-content">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="出荷日" prop="date" required class="compact-item">
                  <el-date-picker 
                    v-model="form.date" 
                    type="date" 
                    placeholder="選択" 
                    value-format="YYYY-MM-DD" 
                    style="width: 100%" 
                    size="default"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="納入日" prop="delivery_date" class="compact-item">
                  <el-date-picker 
                    v-model="form.delivery_date" 
                    type="date" 
                    placeholder="選択" 
                    value-format="YYYY-MM-DD" 
                    style="width: 100%" 
                    clearable 
                    size="default"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- 基本情報セクション -->
        <div class="form-section compact-section">
          <div class="section-header compact-header">
            <el-icon class="section-icon"><Document /></el-icon>
            <span class="section-title">基本情報</span>
          </div>
          <div class="section-content compact-content">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="納入先" prop="destination_cd" required class="compact-item">
                  <el-select 
                    v-model="form.destination_cd" 
                    placeholder="選択" 
                    filterable 
                    style="width: 100%" 
                    popper-class="destination-select-popper"
                    @change="onDestinationChange"
                    size="default"
                  >
                    <el-option 
                      v-for="d in destinationOptions" 
                      :key="d.cd" 
                      :label="`${d.cd} | ${d.name}`" 
                      :value="d.cd" 
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="製品" prop="product_cd" required class="compact-item">
                  <el-select 
                    v-model="form.product_cd" 
                    placeholder="選択" 
                    filterable 
                    style="width: 100%" 
                    @change="onProductChange"
                    size="default"
                  >
                    <el-option
                      v-for="p in productOptions"
                      :key="p.cd"
                      :value="p.cd"
                      :label="`${p.cd} | ${p.name}`"
                    >
                      <div class="product-option-compact">
                        <span class="opt-cd">{{ p.cd }}</span>
                        <span class="opt-name">{{ p.name }}</span>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="タイプ" prop="product_type" class="compact-item">
              <el-select v-model="form.product_type" placeholder="選択" style="width: 100%" size="default">
                <el-option label="量産品" value="量産品" />
                <el-option label="試作品" value="試作品" />
                <el-option label="別注品" value="別注品" />
                <el-option label="補給品" value="補給品" />
                <el-option label="サンプル品" value="サンプル品" />
                <el-option label="代替品" value="代替品" />
                <el-option label="返却品" value="返却品" />
                <el-option label="その他" value="その他" />
              </el-select>
            </el-form-item>
          </div>
        </div>

        <!-- 数量情報セクション -->
        <div class="form-section compact-section">
          <div class="section-header compact-header">
            <el-icon class="section-icon"><Box /></el-icon>
            <span class="section-title">数量情報</span>
          </div>
          <div class="section-content compact-content">
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item label="入数" prop="unit_per_box" class="compact-item">
                  <el-input-number 
                    v-model="form.unit_per_box" 
                    :min="0" 
                    placeholder="0"
                    style="width: 100%" 
                    @change="calculateConfirmedUnits"
                    size="default"
                    :controls="false"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="箱数" prop="confirmed_boxes" class="compact-item">
                  <el-input-number 
                    v-model="form.confirmed_boxes" 
                    :min="0" 
                    placeholder="0"
                    style="width: 100%" 
                    @change="calculateConfirmedUnits"
                    size="default"
                    :controls="false"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="確定" prop="confirmed_units" class="compact-item">
                  <el-input 
                    :model-value="confirmedUnitsDisplay" 
                    placeholder="自動" 
                    readonly
                    class="calculated-field"
                    size="default"
                  >
                    <template #suffix>
                      <span class="unit-suffix">本</span>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>
            
            <div class="info-tip compact-tip">
              <el-icon><InfoFilled /></el-icon>
              <span>確定本数 = 入数 × 箱数</span>
            </div>
          </div>
        </div>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="dialogVisible = false" class="btn-cancel" size="default">
            <el-icon><Close /></el-icon>
            <span>キャンセル</span>
          </el-button>
          <el-button type="primary" :loading="saving" @click="submitForm" class="btn-save" size="default">
            <el-icon><Check /></el-icon>
            <span>保存</span>
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Calendar, Plus, Document, Box, InfoFilled, Close, Check } from '@element-plus/icons-vue'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { getProductList } from '@/api/master/productMaster'
import {
  fetchOrderDailyList,
  createOrderDaily,
  updateOrderDaily,
  deleteOrderDaily,
  type OrderDailyItem,
  type OrderDailyCreate,
  type OrderDailyFilters,
} from '@/api/erp/orderDaily'

const loading = ref(false)
const list = ref<OrderDailyItem[]>([])
const destinationOptions = ref<{ cd: string; name: string }[]>([])
interface ProductOption {
  cd: string
  name: string
  destination_cd?: string
  destination_name?: string
}
const productOptions = ref<ProductOption[]>([])

const filters = reactive<OrderDailyFilters>({})

// 日本時区の現在日付を取得
function getJapanDate(): Date {
  return new Date(new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }))
}

function getTodayRange(): [string, string] {
  const d = getJapanDate()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return [`${y}-${m}-${day}`, `${y}-${m}-${day}`]
}
const dateRange = ref<[string, string] | null>(getTodayRange())

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

async function loadOptions() {
  try {
    const [d, pr] = await Promise.all([
      getDestinationOptions(),
      getProductList({ pageSize: 9999 }),
    ])
    destinationOptions.value = d.map((x) => ({ cd: x.cd, name: x.name }))
    const destMap: Record<string, string> = {}
    destinationOptions.value.forEach((x) => { destMap[x.cd] = x.name })
    const list = pr?.data?.list ?? pr?.list ?? []
    productOptions.value = list
      .map((p: { product_cd: string; product_name?: string; destination_cd?: string }) => ({
        cd: p.product_cd,
        name: p.product_name || p.product_cd,
        destination_cd: p.destination_cd,
        destination_name: p.destination_cd ? (destMap[p.destination_cd] || p.destination_cd) : undefined,
      }))
      .sort((a, b) => (a.name || '').localeCompare(b.name || '', 'ja'))
  } catch {
    destinationOptions.value = []
    productOptions.value = []
  }
}

async function loadList() {
  loading.value = true
  try {
    const params: OrderDailyFilters = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.destination_cd) params.destination_cd = filters.destination_cd
    const allData = await fetchOrderDailyList(params)
    pagination.total = allData.length
    const start = (pagination.page - 1) * pagination.pageSize
    const end = start + pagination.pageSize
    list.value = allData.slice(start, end)
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  pagination.page = page
  loadList()
}

function handleSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  loadList()
}

watch(
  () => [dateRange.value, filters.keyword, filters.destination_cd],
  () => {
    pagination.page = 1
    loadList()
  },
  { deep: true }
)

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const saving = ref(false)
const editId = ref<number | null>(null)

const form = reactive<OrderDailyCreate & { destination_name?: string; product_name?: string }>({
  monthly_order_id: '',
  destination_cd: '',
  destination_name: '',
  date: '',
  weekday: '',
  product_cd: '',
  product_name: '',
  product_alias: '',
  product_type: '量産品',
  forecast_units: 0,
  confirmed_boxes: 0,
  confirmed_units: 0,
  unit_per_box: 0,
  status: '未出荷',
  remarks: '',
  delivery_date: '',
})

const rules: FormRules = {
  destination_cd: [{ required: true, message: '納入先を選択してください', trigger: 'change' }],
  date: [{ required: true, message: '日付を選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
}

function onDestinationChange(cd: string) {
  const d = destinationOptions.value.find((x) => x.cd === cd)
  if (d) form.destination_name = d.name
}

function onProductChange(cd: string) {
  const p = productOptions.value.find((x) => x.cd === cd)
  if (p) form.product_name = p.name
}

// 確定本数の自動計算
const confirmedUnitsDisplay = computed(() => {
  const units = (form.unit_per_box || 0) * (form.confirmed_boxes || 0)
  return units > 0 ? `${units}` : ''
})

function calculateConfirmedUnits() {
  form.confirmed_units = (form.unit_per_box || 0) * (form.confirmed_boxes || 0)
}

function openDialog(row?: OrderDailyItem) {
  editId.value = row?.id ?? null
  if (row) {
    form.monthly_order_id = row.monthly_order_id ?? ''
    form.destination_cd = row.destination_cd
    form.destination_name = row.destination_name ?? ''
    form.date = row.date
    form.weekday = row.weekday ?? ''
    form.product_cd = row.product_cd
    form.product_name = row.product_name ?? ''
    form.product_alias = row.product_alias ?? ''
    form.product_type = row.product_type ?? '量産品'
    form.forecast_units = row.forecast_units ?? 0
    form.confirmed_boxes = row.confirmed_boxes ?? 0
    form.confirmed_units = row.confirmed_units ?? 0
    form.unit_per_box = row.unit_per_box ?? 0
    form.status = row.status ?? '未出荷'
    form.remarks = row.remarks ?? ''
    form.delivery_date = row.delivery_date ?? ''
  } else {
    resetForm()
    const today = getJapanDate()
    form.date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  }
  dialogVisible.value = true
}

function resetForm() {
  editId.value = null
  form.monthly_order_id = ''
  form.destination_cd = ''
  form.destination_name = ''
  form.date = ''
  form.weekday = ''
  form.product_cd = ''
  form.product_name = ''
  form.product_alias = ''
  form.product_type = '量産品'
  form.forecast_units = 0
  form.confirmed_boxes = 0
  form.confirmed_units = 0
  form.unit_per_box = 0
  form.status = '未出荷'
  form.remarks = ''
  form.delivery_date = ''
}

async function submitForm() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const payload: OrderDailyCreate = {
      monthly_order_id: form.monthly_order_id || undefined,
      destination_cd: form.destination_cd,
      destination_name: form.destination_name || undefined,
      date: form.date,
      weekday: form.weekday || undefined,
      product_cd: form.product_cd,
      product_name: form.product_name || undefined,
      product_alias: form.product_alias || undefined,
      product_type: form.product_type,
      forecast_units: form.forecast_units ?? 0,
      confirmed_boxes: form.confirmed_boxes ?? 0,
      confirmed_units: form.confirmed_units ?? 0,
      unit_per_box: form.unit_per_box ?? 0,
      status: form.status,
      remarks: form.remarks || undefined,
      delivery_date: form.delivery_date || undefined,
    }
    if (editId.value != null) {
      await updateOrderDaily(editId.value, payload)
      ElMessage.success('更新しました')
    } else {
      await createOrderDaily(payload)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: OrderDailyItem) {
  try {
    await ElMessageBox.confirm(`日別受注 ID「${row.id}」を削除しますか？`, '確認', { type: 'warning' })
    await deleteOrderDaily(row.id)
    ElMessage.success('削除しました')
    loadList()
  } catch (e: unknown) {
    if ((e as string) !== 'cancel') ElMessage.error('削除に失敗しました')
  }
}

onMounted(() => {
  loadOptions()
  loadList()
})
</script>

<style scoped>
/* ======================================================
   Modern Glassmorphism UI — Daily Order List
   ====================================================== */

/* --- Base --- */
.order-daily-list {
  padding: 12px;
  min-height: 100vh;
  background: linear-gradient(160deg, #f0f4ff 0%, #e8ecf8 40%, #f5f0ff 100%);
}

/* --- Toolbar --- */
.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, rgba(99,102,241,0.88) 0%, rgba(139,92,246,0.92) 50%, rgba(168,85,247,0.88) 100%);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 14px;
  padding: 10px 18px;
  margin-bottom: 10px;
  box-shadow:
    0 4px 24px rgba(99,102,241,0.25),
    inset 0 1px 0 rgba(255,255,255,0.2);
}

.toolbar-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}

.toolbar-right {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

/* --- Toolbar Buttons --- */
.tb-btn {
  border-radius: 8px;
  padding: 5px 11px;
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid rgba(255,255,255,0.2);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.12);
  position: relative;
  overflow: hidden;
}

.tb-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.05) 100%);
  pointer-events: none;
}

.tb-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  color: #fff;
}

.tb-btn:active {
  transform: translateY(0);
}

/* Green - 新規登録 */
.tb-btn-green {
  background: linear-gradient(135deg, rgba(16,185,129,0.9) 0%, rgba(5,150,105,0.95) 100%);
  box-shadow: 0 2px 10px rgba(16,185,129,0.35);
  font-weight: 600;
}

.tb-btn-green:hover {
  background: linear-gradient(135deg, rgba(16,185,129,1) 0%, rgba(5,150,105,1) 100%);
  box-shadow: 0 4px 18px rgba(16,185,129,0.5);
  color: #fff;
}

/* --- Filter Bar (Glass) --- */
.filter-bar {
  background: rgba(255,255,255,0.65);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  border: 1px solid rgba(255,255,255,0.7);
  padding: 8px 12px;
  margin-bottom: 10px;
}

.filter-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.fi-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.fi-icon {
  font-size: 15px;
  color: #6366f1;
}

.fi-date-range {
  width: 280px;
}

.fi-dest {
  width: 195px;
  min-width: 150px;
}

.fi-product {
  width: 380px;
  min-width: 320px;
}

.fi-sep {
  width: 1px;
  height: 22px;
  background: rgba(0,0,0,0.08);
}

/* Product Option Styling */
.product-option-row {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
}

.product-option-cd {
  min-width: 90px;
  color: #606266;
}

.product-option-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-option-dest {
  min-width: 80px;
  color: #909399;
  font-size: 12px;
}

/* --- Table Section (Glass) --- */
.table-section {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.65);
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  padding: 10px;
}

.data-table {
  width: 100%;
}

.data-table :deep(.el-table__header-wrapper th) {
  background: rgba(248,250,252,0.95) !important;
  color: #000;
  font-weight: 600;
  font-size: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.08);
}

.data-table :deep(.el-table__body-wrapper td.el-table__cell) {
  color: #000;
  font-size: 13px;
}

.data-table :deep(.el-table__row) {
  transition: background-color 0.2s;
}

.data-table :deep(.el-table__row:hover > td) {
  background: rgba(99,102,241,0.05) !important;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
  padding: 4px 0;
  font-size: 60%;
}

.pagination-container :deep(.el-pagination) {
  font-size: inherit;
}

.pagination-container :deep(.el-pagination__total),
.pagination-container :deep(.el-pagination__sizes),
.pagination-container :deep(.el-pager),
.pagination-container :deep(.el-pagination__jump) {
  font-size: inherit;
}

.pagination-container :deep(.el-pagination button),
.pagination-container :deep(.el-pagination .el-pager li) {
  font-size: inherit;
  min-width: 1.6em;
  height: 1.6em;
  line-height: 1.6em;
}

.pagination-container :deep(.el-select .el-input__inner) {
  font-size: inherit;
}

.pagination-container :deep(.el-input__inner) {
  font-size: inherit;
}

/* --- Modern Compact Dialog Styles --- */
.compact-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

.daily-order-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  margin: 0;
}

.daily-order-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.daily-order-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
  font-size: 18px;
}

.daily-order-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: #f8f9fa;
}

.compact-form {
  padding: 0;
}

.compact-section {
  background: #fff;
  margin: 10px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  border: 1px solid #e8ecf1;
}

.compact-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f5f7ff 0%, #eef1ff 100%);
  border-bottom: 1px solid #e0e6f7;
}

.section-icon {
  font-size: 16px;
  color: #667eea;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.compact-content {
  padding: 12px;
}

.compact-item {
  margin-bottom: 10px !important;
}

.compact-item:last-child {
  margin-bottom: 0 !important;
}

.compact-item :deep(.el-form-item__label) {
  font-size: 13px;
  padding-right: 8px;
  line-height: 32px;
}

.compact-item :deep(.el-input__inner),
.compact-item :deep(.el-input__wrapper) {
  font-size: 13px;
}

.product-option-compact {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 12px;
}

.opt-cd {
  min-width: 70px;
  color: #606266;
  font-weight: 500;
}

.opt-name {
  flex: 1;
  color: #303133;
}

.calculated-field :deep(.el-input__wrapper) {
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%);
  border: 1px solid #81c784;
  box-shadow: none;
}

.calculated-field :deep(.el-input__inner) {
  color: #2e7d32;
  font-weight: 600;
  text-align: center;
}

.unit-suffix {
  font-size: 12px;
  color: #2e7d32;
  font-weight: 500;
  padding-right: 4px;
}

.compact-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: linear-gradient(135deg, #e3f2fd 0%, #f0f7ff 100%);
  border-radius: 6px;
  border-left: 3px solid #2196f3;
  margin-top: 10px;
  font-size: 11px;
  color: #1976d2;
}

.compact-tip .el-icon {
  font-size: 14px;
  color: #2196f3;
}

.dialog-footer-compact {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
}

.btn-cancel,
.btn-save {
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-save {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 500;
}

.btn-save:hover {
  opacity: 0.9;
}

/* Responsive Design */
@media (max-width: 768px) {
  .order-daily-list {
    padding: 8px;
  }

  .page-toolbar {
    padding: 8px 12px;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .toolbar-title {
    font-size: 15px;
  }

  .filter-inline {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .fi-group {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }

  .fi-date-range,
  .fi-dest,
  .fi-product {
    width: 100%;
  }

  .fi-sep {
    display: none;
  }

  .table-section {
    padding: 8px;
  }

  .data-table {
    font-size: 11px;
  }
}

@media (max-width: 600px) {
  .daily-order-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 0 auto;
  }
  
  .compact-section {
    margin: 8px;
  }
  
  .compact-content {
    padding: 10px;
  }
  
  .compact-item :deep(.el-form-item__label) {
    font-size: 12px;
  }
  
  .dialog-footer-compact {
    padding: 10px 12px;
  }
  
  .btn-cancel span,
  .btn-save span {
    display: none;
  }
}

@media (max-width: 480px) {
  .daily-order-dialog :deep(.el-dialog__title) {
    font-size: 14px;
  }
  
  .section-title {
    font-size: 12px;
  }
  
  .compact-form {
    font-size: 12px;
  }
}
</style>

