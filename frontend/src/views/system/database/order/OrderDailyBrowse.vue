<template>
  <div class="order-daily-browse">
    <header class="order-daily-browse__header">
      <div class="order-daily-browse__header-main">
        <div class="order-daily-browse__header-icon">
          <el-icon :size="26"><Coin /></el-icon>
        </div>
        <div>
          <h1 class="order-daily-browse__title">order_daily</h1>
          <p class="order-daily-browse__subtitle">日別受注テーブル閲覧・編集</p>
          <p v-if="lastFetchedText" class="order-daily-browse__meta">最終取得: {{ lastFetchedText }}</p>
        </div>
      </div>
      <div class="order-daily-browse__header-actions">
        <el-button size="small" :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>
          再読込
        </el-button>
      </div>
    </header>

    <div class="order-daily-browse__panel order-daily-browse__filters">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="～"
        start-placeholder="開始日"
        end-placeholder="終了日"
        value-format="YYYY-MM-DD"
        size="small"
        clearable
        class="order-daily-browse__date"
      />
      <el-select
        v-model="filters.destination_cd"
        placeholder="納入先"
        clearable
        filterable
        size="small"
        class="order-daily-browse__dest"
        @change="onFilterDestinationChange"
      >
        <el-option
          v-for="d in destinationOptions"
          :key="d.cd"
          :label="`${d.cd} | ${d.name}`"
          :value="d.cd"
        />
      </el-select>
      <el-select
        v-model="filters.product_cd"
        placeholder="製品名"
        clearable
        filterable
        size="small"
        class="order-daily-browse__product"
      >
        <el-option
          v-for="p in productOptions"
          :key="p.cd"
          :label="`${p.cd} | ${p.name}`"
          :value="p.cd"
        />
      </el-select>
    </div>

    <div class="order-daily-browse__panel order-daily-browse__table-wrap">
      <el-table
        v-loading="loading"
        :data="pagedList"
        size="small"
        stripe
        border
        class="order-daily-browse__table"
        :max-height="tableMaxHeight"
        :header-cell-style="tableHeaderStyle"
        highlight-current-row
      >
        <el-table-column prop="id" label="id" width="72" fixed />
        <el-table-column prop="date" label="date" width="108" />
        <el-table-column prop="destination_cd" label="destination_cd" width="108" />
        <el-table-column prop="destination_name" label="destination_name" min-width="110" show-overflow-tooltip />
        <el-table-column prop="product_cd" label="product_cd" width="100" />
        <el-table-column prop="product_name" label="product_name" min-width="120" show-overflow-tooltip />
        <el-table-column prop="forecast_units" label="forecast_units" width="108" align="right" />
        <el-table-column prop="confirmed_units" label="confirmed_units" width="112" align="right" />
        <el-table-column prop="status" label="status" width="96">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="light">{{ row.status || '—' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="shipping_no" label="shipping_no" width="120" show-overflow-tooltip />
        <el-table-column prop="delivery_date" label="delivery_date" width="108" />
        <el-table-column prop="confirmed" label="confirmed" width="88" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.confirmed" type="success" size="small">true</el-tag>
            <span v-else class="order-daily-browse__muted">false</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="updated_at" width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="88" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEdit(row)">編集</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="order-daily-browse__pagination">
        <span class="order-daily-browse__count">全 {{ fullList.length.toLocaleString('ja-JP') }} 件</span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="fullList.length"
          layout="sizes, prev, pager, next"
          background
          size="small"
        />
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      title="order_daily 編集"
      width="640px"
      destroy-on-close
      class="order-daily-browse__dialog"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="140px" size="small" class="edit-form">
        <el-form-item label="id">
          <el-input :model-value="String(editId ?? '')" disabled />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="date" prop="date">
              <el-date-picker
                v-model="form.date"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                @change="onDateChange"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="weekday" prop="weekday">
              <el-input v-model="form.weekday" placeholder="曜日" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="destination_cd" prop="destination_cd">
              <el-input v-model="form.destination_cd" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="destination_name">
              <el-input v-model="form.destination_name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="product_cd" prop="product_cd">
              <el-input v-model="form.product_cd" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="product_type">
              <el-input v-model="form.product_type" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="product_name">
          <el-input v-model="form.product_name" />
        </el-form-item>
        <el-form-item label="product_alias">
          <el-input v-model="form.product_alias" />
        </el-form-item>
        <el-form-item label="monthly_order_id">
          <el-input v-model="form.monthly_order_id" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="forecast_units">
              <el-input-number v-model="form.forecast_units" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="confirmed_boxes">
              <el-input-number
                v-model="form.confirmed_boxes"
                :min="0"
                controls-position="right"
                style="width: 100%"
                @change="calcConfirmedUnits"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="unit_per_box">
              <el-input-number
                v-model="form.unit_per_box"
                :min="0"
                controls-position="right"
                style="width: 100%"
                @change="calcConfirmedUnits"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="confirmed_units">
          <el-input-number v-model="form.confirmed_units" :min="0" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="status">
              <el-select v-model="form.status" style="width: 100%" allow-create filterable>
                <el-option label="未出荷" value="未出荷" />
                <el-option label="出荷済" value="出荷済" />
                <el-option label="出荷済み" value="出荷済み" />
                <el-option label="完了" value="完了" />
                <el-option label="保留" value="保留" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="supply_status">
              <el-input v-model="form.supply_status" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="shipping_no">
              <el-input v-model="form.shipping_no" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="delivery_date">
              <el-date-picker
                v-model="form.delivery_date"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="batch_id">
              <el-input-number v-model="form.batch_id" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="batch_no">
              <el-input v-model="form.batch_no" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="fulfilled_from_stock">
              <el-input-number v-model="form.fulfilled_from_stock" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="fulfilled_from_wip">
              <el-input-number v-model="form.fulfilled_from_wip" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="confirmed">
              <el-switch v-model="form.confirmed" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="remarks">
          <el-input v-model="form.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="dialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Coin, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { getProductList } from '@/api/master/productMaster'
import type { Product } from '@/types/master'
import {
  fetchOrderDailyList,
  updateOrderDaily,
  type OrderDailyItem,
} from '@/api/erp/orderDaily'

interface ProductOption {
  cd: string
  name: string
  destination_cd?: string
}

const WEEKDAY_MAP = ['日', '月', '火', '水', '木', '金', '土'] as const

const tableHeaderStyle = {
  background: '#f1f5f9',
  color: '#334155',
  fontWeight: '600',
  fontSize: '12px',
}

const loading = ref(false)
const saving = ref(false)
const fullList = ref<OrderDailyItem[]>([])
const lastFetchedAt = ref<Date | null>(null)
const filterReady = ref(false)
const dateRange = ref<[string, string] | null>(null)
const destinationOptions = ref<{ cd: string; name: string }[]>([])
const allProductOptions = ref<ProductOption[]>([])
const productOptions = ref<ProductOption[]>([])
const filters = reactive({
  destination_cd: '',
  product_cd: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 50,
})

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const editId = ref<number | null>(null)

const form = reactive({
  monthly_order_id: '',
  destination_cd: '',
  destination_name: '',
  date: '',
  weekday: '',
  product_cd: '',
  product_name: '',
  product_alias: '',
  product_type: '',
  forecast_units: 0,
  confirmed_boxes: 0,
  confirmed_units: 0,
  unit_per_box: 0,
  status: '未出荷',
  remarks: '',
  shipping_no: '' as string | null,
  delivery_date: '' as string | null,
  batch_id: null as number | null,
  batch_no: '' as string | null,
  supply_status: '' as string | null,
  fulfilled_from_stock: 0,
  fulfilled_from_wip: 0,
  confirmed: false,
})

const rules: FormRules = {
  date: [{ required: true, message: 'date を入力してください', trigger: 'change' }],
  destination_cd: [{ required: true, message: 'destination_cd を入力してください', trigger: 'blur' }],
  product_cd: [{ required: true, message: 'product_cd を入力してください', trigger: 'blur' }],
}

const tableMaxHeight = computed(() => Math.max(380, window.innerHeight - 260))

const lastFetchedText = computed(() => {
  if (!lastFetchedAt.value) return ''
  return lastFetchedAt.value.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
})

const pagedList = computed(() => {
  const start = (pagination.page - 1) * pagination.pageSize
  return fullList.value.slice(start, start + pagination.pageSize)
})

function statusTagType(status: string | null | undefined): 'success' | 'warning' | 'info' | 'danger' {
  const s = status || ''
  if (/取消|キャンセル/.test(s)) return 'danger'
  if (/未出荷|保留/.test(s)) return 'warning'
  if (/出荷済|完了/.test(s)) return 'success'
  return 'info'
}

function formatYmd(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function initDefaultRange() {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1)
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  dateRange.value = [formatYmd(start), formatYmd(end)]
}

function formatDateTime(v: string | null | undefined): string {
  if (!v) return '—'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return String(v)
  return d.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
}

function onDateChange(val: string | null) {
  if (!val) {
    form.weekday = ''
    return
  }
  const d = new Date(val)
  if (!Number.isNaN(d.getTime())) form.weekday = WEEKDAY_MAP[d.getDay()] ?? ''
}

function calcConfirmedUnits() {
  form.confirmed_units = (form.unit_per_box || 0) * (form.confirmed_boxes || 0)
}

function refreshProductOptions(destinationCd?: string) {
  const cd = destinationCd ?? filters.destination_cd
  if (cd) {
    const filtered = allProductOptions.value.filter((p) => p.destination_cd === cd)
    productOptions.value = filtered.length > 0 ? filtered : [...allProductOptions.value]
  } else {
    productOptions.value = [...allProductOptions.value]
  }
}

function onFilterDestinationChange(cd: string) {
  refreshProductOptions(cd)
  if (filters.product_cd && !productOptions.value.some((p) => p.cd === filters.product_cd)) {
    filters.product_cd = ''
  }
}

async function loadOptions() {
  try {
    const [destList, productRes] = await Promise.all([
      getDestinationOptions(),
      getProductList({ pageSize: 9999 }),
    ])
    destinationOptions.value = destList
    const rawList: Product[] = productRes?.data?.list ?? productRes?.list ?? []
    allProductOptions.value = rawList.map((p) => ({
      cd: String(p.product_cd ?? ''),
      name: String(p.product_name || p.product_cd || ''),
      destination_cd: p.destination_cd ? String(p.destination_cd) : undefined,
    }))
    refreshProductOptions()
  } catch {
    destinationOptions.value = []
    allProductOptions.value = []
    productOptions.value = []
  }
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
  form.product_type = ''
  form.forecast_units = 0
  form.confirmed_boxes = 0
  form.confirmed_units = 0
  form.unit_per_box = 0
  form.status = '未出荷'
  form.remarks = ''
  form.shipping_no = null
  form.delivery_date = null
  form.batch_id = null
  form.batch_no = null
  form.supply_status = null
  form.fulfilled_from_stock = 0
  form.fulfilled_from_wip = 0
  form.confirmed = false
}

function openEdit(row: OrderDailyItem) {
  editId.value = row.id
  form.monthly_order_id = row.monthly_order_id ?? ''
  form.destination_cd = row.destination_cd
  form.destination_name = row.destination_name ?? ''
  form.date = row.date
  form.weekday = row.weekday ?? ''
  form.product_cd = row.product_cd
  form.product_name = row.product_name ?? ''
  form.product_alias = row.product_alias ?? ''
  form.product_type = row.product_type ?? ''
  form.forecast_units = row.forecast_units ?? 0
  form.confirmed_boxes = row.confirmed_boxes ?? 0
  form.confirmed_units = row.confirmed_units ?? 0
  form.unit_per_box = row.unit_per_box ?? 0
  form.status = row.status ?? '未出荷'
  form.remarks = row.remarks ?? ''
  form.shipping_no = row.shipping_no
  form.delivery_date = row.delivery_date
  form.batch_id = row.batch_id
  form.batch_no = row.batch_no
  form.supply_status = row.supply_status
  form.fulfilled_from_stock = row.fulfilled_from_stock ?? 0
  form.fulfilled_from_wip = row.fulfilled_from_wip ?? 0
  form.confirmed = row.confirmed ?? false
  dialogVisible.value = true
}

async function submitEdit() {
  if (editId.value == null) return
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('入力内容を確認してください')
    return
  }

  saving.value = true
  try {
    const updated = await updateOrderDaily(editId.value, {
      monthly_order_id: form.monthly_order_id || undefined,
      destination_cd: form.destination_cd,
      destination_name: form.destination_name || undefined,
      date: form.date,
      weekday: form.weekday || undefined,
      product_cd: form.product_cd,
      product_name: form.product_name || undefined,
      product_alias: form.product_alias || undefined,
      product_type: form.product_type || undefined,
      forecast_units: form.forecast_units,
      confirmed_boxes: form.confirmed_boxes,
      confirmed_units: form.confirmed_units,
      unit_per_box: form.unit_per_box,
      status: form.status,
      remarks: form.remarks || undefined,
      shipping_no: form.shipping_no?.trim() || null,
      delivery_date: form.delivery_date || undefined,
      batch_id: form.batch_id ?? undefined,
      batch_no: form.batch_no || undefined,
      supply_status: form.supply_status || undefined,
      fulfilled_from_stock: form.fulfilled_from_stock,
      fulfilled_from_wip: form.fulfilled_from_wip,
      confirmed: form.confirmed,
    })
    const idx = fullList.value.findIndex((r) => r.id === editId.value)
    if (idx >= 0) fullList.value[idx] = updated
    ElMessage.success('更新しました')
    dialogVisible.value = false
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '更新に失敗しました'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (dateRange.value?.[0]) params.start_date = dateRange.value[0]
    if (dateRange.value?.[1]) params.end_date = dateRange.value[1]
    if (filters.destination_cd) params.destination_cd = filters.destination_cd
    if (filters.product_cd) params.keyword = filters.product_cd
    fullList.value = await fetchOrderDailyList(params)
    lastFetchedAt.value = new Date()
  } catch (e: unknown) {
    fullList.value = []
    const msg = e instanceof Error ? e.message : 'データの取得に失敗しました'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

watch(
  () => [dateRange.value, filters.destination_cd, filters.product_cd],
  () => {
    if (!filterReady.value) return
    pagination.page = 1
    loadData()
  },
  { deep: true },
)

onMounted(async () => {
  initDefaultRange()
  await loadOptions()
  filterReady.value = true
  pagination.page = 1
  await loadData()
})
</script>

<style scoped>
.order-daily-browse {
  padding: 12px 16px 20px;
  min-height: 100%;
  background: linear-gradient(160deg, #eef2ff 0%, #f8fafc 45%, #f1f5f9 100%);
}

.order-daily-browse__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  box-shadow: 0 8px 24px rgba(79, 70, 229, 0.25);
  color: #fff;
}

.order-daily-browse__header-main {
  display: flex;
  align-items: center;
  gap: 14px;
}

.order-daily-browse__header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.18);
}

.order-daily-browse__title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.order-daily-browse__subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  opacity: 0.9;
}

.order-daily-browse__meta {
  margin: 4px 0 0;
  font-size: 12px;
  opacity: 0.75;
}

.order-daily-browse__header-actions :deep(.el-button) {
  border-color: rgba(255, 255, 255, 0.5);
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.order-daily-browse__header-actions :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.22);
}

.order-daily-browse__panel {
  padding: 12px 14px;
  margin-bottom: 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
}

.order-daily-browse__filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.order-daily-browse__date {
  width: 260px;
  max-width: 100%;
}

.order-daily-browse__dest {
  width: 220px;
  min-width: 160px;
}

.order-daily-browse__product {
  width: 260px;
  min-width: 180px;
}

.order-daily-browse__table-wrap {
  padding-bottom: 8px;
}

.order-daily-browse__table {
  width: 100%;
}

.order-daily-browse__pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 10px;
}

.order-daily-browse__count {
  font-size: 13px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.order-daily-browse__muted {
  color: #94a3b8;
  font-size: 12px;
}

.edit-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.order-daily-browse__dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}
</style>
