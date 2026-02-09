<template>
  <div class="order-monthly-list">
    <div class="page-header">
      <div class="header-content">
        <h1 class="main-title">月受注管理</h1>
        <el-button type="primary" class="batch-register-btn" @click="openBatchDialog">
          <el-icon><Upload /></el-icon>
          <span>月注文一括登録</span>
        </el-button>
      </div>
    </div>

    <div class="filter-card">
      <div class="filter-row">
        <!-- 期間 -->
        <div class="filter-group filter-period">
          <div class="filter-label">
            <el-icon class="label-icon"><Calendar /></el-icon>
            <span>期間</span>
          </div>
          <div class="period-controls">
            <el-select v-model="filters.year" placeholder="年" clearable class="period-select year-select">
              <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
            </el-select>
            <el-select v-model="filters.month" placeholder="月" clearable class="period-select month-select">
              <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
            </el-select>
            <div class="period-nav">
              <el-button class="nav-btn" :icon="ArrowLeft" circle @click="goPrevPeriod" />
              <el-button class="btn-current" @click="goCurrentMonth">今月</el-button>
              <el-button class="nav-btn" :icon="ArrowRight" circle @click="goNextPeriod" />
            </div>
          </div>
        </div>

        <!-- 条件 納入先 -->
        <div class="filter-group filter-destination">
          <div class="filter-label"><span class="label-condition">条件</span> <span>納入先</span></div>
          <el-select v-model="filters.destination_cd" placeholder="納入先を選択" clearable filterable class="destination-select">
            <el-option v-for="d in destinationOptions" :key="d.cd" :label="`${d.cd} | ${d.name}`" :value="d.cd" />
          </el-select>
        </div>

        <!-- 製品検索 -->
        <div class="filter-group filter-product">
          <div class="filter-label">製品検索</div>
          <el-input v-model="filters.keyword" placeholder="製品CD・製品名で検索..." clearable class="product-search-input">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
    </div>

    <div class="table-section">
      <el-table :data="list" v-loading="loading" stripe border size="small" class="data-table">
        <el-table-column prop="order_id" label="受注ID" width="160" show-overflow-tooltip />
        <el-table-column prop="destination_cd" label="納入先CD" width="100" />
        <el-table-column prop="destination_name" label="納入先名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="year" label="年" width="70" align="center" />
        <el-table-column prop="month" label="月" width="60" align="center" />
        <el-table-column prop="product_cd" label="製品CD" width="100" />
        <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="product_type" label="種別" width="90" />
        <el-table-column prop="forecast_units" label="内示本数" width="90" align="right" />
        <el-table-column prop="forecast_total_units" label="日内示合計" width="100" align="right" />
        <el-table-column prop="forecast_diff" label="内示差異" width="90" align="right">
          <template #default="{ row }">
            <span :class="row.forecast_diff !== 0 ? 'text-warning' : ''">{{ row.forecast_diff }}</span>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dialogVisible" :title="editId ? '月別受注編集' : '月別受注登録'" width="520px" destroy-on-close @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="納入先CD" prop="destination_cd">
          <el-select v-model="form.destination_cd" placeholder="選択" filterable style="width: 100%" @change="onDestinationChange">
            <el-option v-for="d in destinationOptions" :key="d.cd" :label="`${d.cd} ${d.name}`" :value="d.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="納入先名" prop="destination_name">
          <el-input v-model="form.destination_name" placeholder="納入先名" />
        </el-form-item>
        <el-form-item label="年" prop="year">
          <el-select v-model="form.year" placeholder="年" style="width: 100%">
            <el-option v-for="y in yearOptions" :key="y" :label="String(y)" :value="y" />
          </el-select>
        </el-form-item>
        <el-form-item label="月" prop="month">
          <el-select v-model="form.month" placeholder="月" style="width: 100%">
            <el-option v-for="m in 12" :key="m" :label="String(m)" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="製品CD" prop="product_cd">
          <el-select v-model="form.product_cd" placeholder="選択" filterable style="width: 100%" @change="onProductChange">
            <el-option v-for="p in productOptions" :key="p.cd" :label="`${p.cd} ${p.name}`" :value="p.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="製品名" prop="product_name">
          <el-input v-model="form.product_name" placeholder="製品名" />
        </el-form-item>
        <el-form-item label="製品別名" prop="product_alias">
          <el-input v-model="form.product_alias" placeholder="任意" />
        </el-form-item>
        <el-form-item label="製品種別" prop="product_type">
          <el-select v-model="form.product_type" placeholder="種別" style="width: 100%">
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
        <el-form-item label="内示本数" prop="forecast_units">
          <el-input-number v-model="form.forecast_units" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="日内示合計" prop="forecast_total_units">
          <el-input-number v-model="form.forecast_total_units" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="内示差異" prop="forecast_diff">
          <el-input-number v-model="form.forecast_diff" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <!-- Batch Registration Dialog -->
    <el-dialog v-model="batchDialogVisible" width="900px" destroy-on-close @close="resetBatchForm">
      <template #header>
        <div class="dialog-header compact-header">
          <el-icon class="dialog-icon">
            <Upload />
          </el-icon>
          <span class="dialog-title">月注文一括登録</span>
        </div>
      </template>
      <div class="batch-form-container">
        <div class="batch-form compact-form">
          <el-form :model="batchForm" :inline="true" class="compact-form-inner batch-form-inline">
            <el-form-item label="年" class="inline-form-item">
              <el-select v-model="batchForm.year" placeholder="年を選択" class="year-select">
                <el-option v-for="y in batchYearOptions" :key="y" :label="`${y}年`" :value="y" />
              </el-select>
            </el-form-item>

            <el-form-item label="月" class="inline-form-item">
              <div class="month-select-with-nav">
                <el-select v-model="batchForm.month" placeholder="月を選択" class="month-select">
                  <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
                </el-select>
                <div class="month-nav-buttons">
                  <el-button
                    class="month-nav-btn prev-month-btn"
                    @click="handleBatchPrevMonth"
                    size="small"
                  >
                    <el-icon>
                      <ArrowLeft />
                    </el-icon>
                  </el-button>
                  <el-button
                    class="month-nav-btn current-month-btn"
                    :class="{ active: isBatchCurrentMonth }"
                    @click="handleBatchCurrentMonth"
                    size="small"
                  >
                    今月
                  </el-button>
                  <el-button
                    class="month-nav-btn next-month-btn"
                    @click="handleBatchNextMonth"
                    size="small"
                  >
                    <el-icon>
                      <ArrowRight />
                    </el-icon>
                  </el-button>
                </div>
              </div>
            </el-form-item>

            <el-form-item label="納入先" class="inline-form-item">
              <el-select
                v-model="batchForm.destination_cd"
                filterable
                placeholder="納入先を選択"
                class="destination-select"
              >
                <el-option
                  v-for="item in batchDestinationOptions"
                  :key="item.cd"
                  :label="`${item.cd} | ${item.name}`"
                  :value="item.cd"
                />
              </el-select>
            </el-form-item>

            <el-form-item class="inline-form-item button-item">
              <el-button type="primary" class="load-btn" @click="fetchProducts">
                <el-icon>
                  <Download />
                </el-icon>
                読込
              </el-button>
            </el-form-item>
          </el-form>
          <div class="table-container">
            <div v-if="filteredBatchProducts.length > 0" class="table-info">
              <span class="info-text">
                表示中: {{ filteredBatchProducts.length }}件（納入先関連製品）
              </span>
            </div>
            <el-table
              v-if="filteredBatchProducts.length > 0"
              :data="filteredBatchProducts"
              class="batch-product-table"
              :loading="batchLoading"
              border
              stripe
              highlight-current-row
              max-height="350"
            >
              <el-table-column label="製品タイプ" width="110" show-overflow-tooltip>
                <template #default="{ row }">
                  <el-tag
                    :type="getProductTypeTagType(row.product_type)"
                    effect="light"
                    size="small"
                  >
                    {{ row.product_type || '未設定' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="product_cd" label="製品CD" width="90" />
              <el-table-column
                prop="product_name"
                label="製品名"
                min-width="180"
                show-overflow-tooltip
              />
              <el-table-column label="状態" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.exists ? 'info' : 'success'" size="small" effect="plain">
                    {{ row.exists ? '登録済' : '新規' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="数量" width="120" align="center">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="row.quantity"
                    type="text"
                    class="quantity-input"
                    :class="hasQuantity(row.quantity) ? 'normal-cell' : 'warning-cell'"
                    placeholder="数量"
                    @keydown.enter.prevent="handleQuantityEnter($index)"
                    @focus="handleFocus"
                    @input="handleQuantityChange(row)"
                    :id="`quantity-input-${$index}`"
                  />
                </template>
              </el-table-column>
            </el-table>
            <div v-else-if="batchLoading" class="loading-placeholder compact-placeholder">
              <el-icon class="is-loading">
                <LoadingIcon />
              </el-icon>
              <p>データ読込中...</p>
            </div>
            <div
              v-else-if="!batchForm.destination_cd"
              class="empty-placeholder compact-placeholder"
            >
              <p>納入先を選択し、製品一覧を読み込んでください</p>
            </div>
            <div v-else class="empty-placeholder compact-placeholder">
              <p>製品データがありません</p>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="batchDialogVisible = false" class="cancel-btn">
            <el-icon>
              <Close />
            </el-icon>
            キャンセル
          </el-button>
          <el-button type="primary" @click="handleBatchRegister" class="register-btn">
            <el-icon>
              <Check />
            </el-icon>
            登録する
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Calendar, Search, ArrowLeft, ArrowRight, Upload, Download, Close, Check, Loading as LoadingIcon } from '@element-plus/icons-vue'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { getProductOptions } from '@/api/options'
import {
  getOrderProducts,
  checkCombinationExists,
  batchCreateMonthly,
} from '@/api/erp/orderBatch'
import {
  fetchOrderMonthlyList,
  createOrderMonthly,
  updateOrderMonthly,
  deleteOrderMonthly,
  type OrderMonthlyItem,
  type OrderMonthlyCreate,
  type OrderMonthlyFilters,
} from '@/api/erp/orderMonthly'

const loading = ref(false)
const list = ref<OrderMonthlyItem[]>([])
const now = new Date()
const filters = reactive<OrderMonthlyFilters>({
  year: now.getFullYear(),
  month: now.getMonth() + 1,
})
const destinationOptions = ref<{ cd: string; name: string }[]>([])
const productOptions = ref<{ cd: string; name: string }[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const yearOptions = computed(() => {
  const y = new Date().getFullYear()
  return [y + 1, y, y - 1, y - 2]
})

async function loadOptions() {
  try {
    const [d, p] = await Promise.all([getDestinationOptions(), getProductOptions()])
    destinationOptions.value = d.map((x) => ({ cd: x.cd, name: x.name }))
    productOptions.value = p.map((x) => ({ cd: x.cd, name: x.name }))
  } catch {
    destinationOptions.value = []
    productOptions.value = []
  }
}

async function loadList() {
  loading.value = true
  try {
    const allData = await fetchOrderMonthlyList(filters)
    pagination.total = allData.length
    // Client-side pagination
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

function goPrevPeriod() {
  const y = filters.year ?? new Date().getFullYear()
  const m = filters.month ?? new Date().getMonth() + 1
  if (m <= 1) {
    filters.month = 12
    filters.year = y - 1
  } else {
    filters.month = m - 1
    filters.year = y
  }
  loadList()
}

function goNextPeriod() {
  const y = filters.year ?? new Date().getFullYear()
  const m = filters.month ?? new Date().getMonth() + 1
  if (m >= 12) {
    filters.month = 1
    filters.year = y + 1
  } else {
    filters.month = m + 1
    filters.year = y
  }
  loadList()
}

function goCurrentMonth() {
  const d = new Date()
  filters.year = d.getFullYear()
  filters.month = d.getMonth() + 1
  loadList()
}

// 自動篩選：期間・納入先変更時は即時、キーワードは 300ms デバウンス
let keywordDebounceTimer: ReturnType<typeof setTimeout> | null = null
watch(
  () => ({ year: filters.year, month: filters.month, destination_cd: filters.destination_cd }),
  () => {
    pagination.page = 1
    loadList()
  },
  { deep: true }
)
watch(
  () => filters.keyword,
  () => {
    if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
    keywordDebounceTimer = setTimeout(() => {
      pagination.page = 1
      loadList()
      keywordDebounceTimer = null
    }, 300)
  }
)

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const saving = ref(false)
const editId = ref<number | null>(null)

const form = reactive<OrderMonthlyCreate & { destination_name?: string; product_name?: string }>({
  destination_cd: '',
  destination_name: '',
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  product_cd: '',
  product_name: '',
  product_alias: '',
  product_type: '量産品',
  forecast_units: 0,
  forecast_total_units: 0,
  forecast_diff: 0,
})

const rules: FormRules = {
  destination_cd: [{ required: true, message: '納入先を選択してください', trigger: 'change' }],
  destination_name: [{ required: true, message: '納入先名を入力してください', trigger: 'blur' }],
  year: [{ required: true, message: '年を選択してください', trigger: 'change' }],
  month: [{ required: true, message: '月を選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
  product_name: [{ required: true, message: '製品名を入力してください', trigger: 'blur' }],
}

function onDestinationChange(cd: string) {
  const d = destinationOptions.value.find((x) => x.cd === cd)
  if (d) form.destination_name = d.name
}

function onProductChange(cd: string) {
  const p = productOptions.value.find((x) => x.cd === cd)
  if (p) form.product_name = p.name
}

function openDialog(row?: OrderMonthlyItem) {
  editId.value = row?.id ?? null
  if (row) {
    form.destination_cd = row.destination_cd
    form.destination_name = row.destination_name
    form.year = row.year
    form.month = row.month
    form.product_cd = row.product_cd
    form.product_name = row.product_name
    form.product_alias = row.product_alias ?? ''
    form.product_type = row.product_type
    form.forecast_units = row.forecast_units
    form.forecast_total_units = row.forecast_total_units
    form.forecast_diff = row.forecast_diff
  } else {
    resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  editId.value = null
  form.destination_cd = ''
  form.destination_name = ''
  form.year = new Date().getFullYear()
  form.month = new Date().getMonth() + 1
  form.product_cd = ''
  form.product_name = ''
  form.product_alias = ''
  form.product_type = '量産品'
  form.forecast_units = 0
  form.forecast_total_units = 0
  form.forecast_diff = 0
}

async function submitForm() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const payload: OrderMonthlyCreate = {
      destination_cd: form.destination_cd,
      destination_name: form.destination_name!,
      year: form.year!,
      month: form.month!,
      product_cd: form.product_cd,
      product_name: form.product_name!,
      product_alias: form.product_alias || undefined,
      product_type: form.product_type,
      forecast_units: form.forecast_units ?? 0,
      forecast_total_units: form.forecast_total_units ?? 0,
      forecast_diff: form.forecast_diff ?? 0,
    }
    if (editId.value != null) {
      await updateOrderMonthly(editId.value, payload)
      ElMessage.success('更新しました')
    } else {
      await createOrderMonthly(payload)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: OrderMonthlyItem) {
  try {
    await ElMessageBox.confirm(`受注ID「${row.order_id}」を削除しますか？`, '確認', { type: 'warning' })
    await deleteOrderMonthly(row.id)
    ElMessage.success('削除しました')
    loadList()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.message || '削除に失敗しました')
  }
}

// Batch registration state
const batchDialogVisible = ref(false)
const batchLoading = ref(false)
const batchForm = reactive({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  destination_cd: '',
})
const batchProducts = ref<any[]>([])
const batchDestinationOptions = ref<{ cd: string; name: string }[]>([])

const filteredBatchProducts = computed(() => {
  return [...batchProducts.value].sort((a, b) => {
    const nameA = a.product_name || ''
    const nameB = b.product_name || ''
    return nameA.localeCompare(nameB, 'ja')
  })
})

const batchYearOptions = computed(() => {
  const y = new Date().getFullYear()
  return [y + 1, y, y - 1, y - 2]
})

const isBatchCurrentMonth = computed(() => {
  const now = new Date()
  return batchForm.year === now.getFullYear() && batchForm.month === now.getMonth() + 1
})

function openBatchDialog() {
  batchDialogVisible.value = true
  batchDestinationOptions.value = destinationOptions.value
  const now = new Date()
  batchForm.year = now.getFullYear()
  batchForm.month = now.getMonth() + 1
  batchForm.destination_cd = ''
  batchProducts.value = []
}

watch(
  () => batchForm.destination_cd,
  () => {
    if (batchDialogVisible.value && batchForm.destination_cd) batchProducts.value = []
  }
)

function resetBatchForm() {
  batchForm.year = new Date().getFullYear()
  batchForm.month = new Date().getMonth() + 1
  batchForm.destination_cd = ''
  batchProducts.value = []
}

function handleBatchPrevMonth() {
  if (batchForm.month <= 1) {
    batchForm.month = 12
    batchForm.year = batchForm.year - 1
  } else {
    batchForm.month = batchForm.month - 1
  }
}

function handleBatchCurrentMonth() {
  const now = new Date()
  batchForm.year = now.getFullYear()
  batchForm.month = now.getMonth() + 1
}

function handleBatchNextMonth() {
  if (batchForm.month >= 12) {
    batchForm.month = 1
    batchForm.year = batchForm.year + 1
  } else {
    batchForm.month = batchForm.month + 1
  }
}

async function fetchProducts() {
  if (!batchForm.destination_cd) {
    ElMessage.warning('納入先を選択してください')
    return
  }
  batchLoading.value = true
  try {
    const res = await getOrderProducts({
      destination_cd: batchForm.destination_cd,
      year: batchForm.year,
      month: batchForm.month,
    })
    const list = res?.data ?? []
    // 補給品・試作品を除外
    const filtered = list.filter(
      (p: { product_type?: string }) =>
        p.product_type !== '補給品' && p.product_type !== '試作品'
    )
    const destinationName =
      batchDestinationOptions.value.find((d) => d.cd === batchForm.destination_cd)?.name || ''
    batchProducts.value = filtered.map((p: { product_cd: string; product_name: string; product_type: string; forecast_units: number }) => ({
      product_cd: p.product_cd,
      product_name: p.product_name,
      product_type: p.product_type || '量産品',
      forecast_units: p.forecast_units,
      quantity: String(p.forecast_units || ''),
      exists: false as boolean,
      orderMonthlyId: null as number | null,
    }))
    // 每条调用「组合是否存在」打上 exists / orderMonthlyId（更新用）
    for (const row of batchProducts.value) {
      const r = await checkCombinationExists({
        destination_name: destinationName,
        product_name: row.product_name,
        year: batchForm.year,
        month: batchForm.month,
      })
      row.exists = r?.exists ?? false
      if (r?.exists && r.id != null) {
        row.orderMonthlyId = r.id
        if (r.forecast_units != null) row.forecast_units = r.forecast_units
      }
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '製品データの取得に失敗しました')
  } finally {
    batchLoading.value = false
  }
}

function getProductTypeTagType(type: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' {
  const typeMap: Record<string, 'success' | 'warning' | 'info' | 'primary' | 'danger'> = {
    量産品: 'success',
    試作品: 'warning',
    別注品: 'info',
    補給品: 'primary',
    サンプル品: 'info',
    代替品: 'info',
    返却品: 'danger',
    その他: 'info',
  }
  return typeMap[type] || 'info'
}

function handleQuantityEnter(index: number) {
  const nextIndex = index + 1
  if (nextIndex < batchProducts.value.length) {
    const nextInput = document.getElementById(`quantity-input-${nextIndex}`)
    if (nextInput) {
      nextInput.focus()
      ;(nextInput as HTMLInputElement).select()
    }
  }
}

function handleFocus(event: FocusEvent) {
  const input = event.target as HTMLInputElement
  input.select()
}

function handleQuantityChange(row: any) {
  // Ensure numeric value
  const value = row.quantity
  if (value && !/^\d*$/.test(value)) {
    row.quantity = value.replace(/\D/g, '')
  }
}

function hasQuantity(v: any): boolean {
  if (v === '' || v == null) return false
  const n = Number(v)
  return !Number.isNaN(n) && n > 0
}

async function handleBatchRegister() {
  // 新規：不存在且非補給品且数量有效
  const itemsToCreate = batchProducts.value.filter(
    (p) => !p.exists && p.product_type !== '補給品' && hasQuantity(p.quantity)
  )
  // 更新：已存在且数量有变更
  const itemsToUpdate = batchProducts.value.filter(
    (p) =>
      p.exists &&
      p.orderMonthlyId != null &&
      hasQuantity(p.quantity) &&
      Number(p.quantity) !== p.forecast_units
  )
  if (itemsToCreate.length === 0 && itemsToUpdate.length === 0) {
    ElMessage.warning('登録・更新対象がありません（新規は数量入力、既存は数量変更後に登録するを押してください）')
    return
  }

  try {
    const createCount = itemsToCreate.length
    const updateCount = itemsToUpdate.length
    await ElMessageBox.confirm(
      (createCount ? `新規 ${createCount}件` : '') +
        (createCount && updateCount ? '、' : '') +
        (updateCount ? `更新 ${updateCount}件` : '') +
        ' を反映しますか?',
      '確認',
      { type: 'info' }
    )

    batchLoading.value = true
    const destinationName =
      batchDestinationOptions.value.find((d) => d.cd === batchForm.destination_cd)?.name || ''

    if (itemsToCreate.length > 0) {
      const res = await batchCreateMonthly({
        year: batchForm.year,
        month: batchForm.month,
        destination_cd: batchForm.destination_cd,
        destination_name: destinationName,
        products: itemsToCreate.map((p) => ({
          product_cd: p.product_cd,
          forecast_units: Number(p.quantity) || 0,
        })),
      })
      ElMessage.success(res?.message ?? `${res?.inserted ?? 0}件登録しました`)
    }
    for (const p of itemsToUpdate) {
      await updateOrderMonthly(p.orderMonthlyId!, {
        forecast_units: Number(p.quantity) || 0,
      })
    }
    if (itemsToUpdate.length > 0) {
      ElMessage.success(`${itemsToUpdate.length}件を更新しました`)
    }
    batchDialogVisible.value = false
    loadList()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '一括登録・更新に失敗しました')
    }
  } finally {
    batchLoading.value = false
  }
}

onMounted(() => {
  loadOptions()
  loadList()
})
</script>

<style scoped>
.order-monthly-list { padding: 20px; }
.page-header { margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }
.header-content { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.main-title { font-size: 20px; font-weight: 600; margin: 0; }
.batch-register-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-weight: 500;
}
.batch-register-btn:hover { opacity: 0.9; }

.filter-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  border: 1px solid #e8e8e8;
  padding: 16px 20px;
  margin-bottom: 16px;
}
.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 20px;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.filter-label {
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 6px;
}
.filter-label .label-icon { font-size: 16px; color: #909399; }
.filter-label .label-condition { margin-right: 4px; }
.filter-period .period-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.period-select { width: 90px; }
.period-select.year-select { width: 100px; }
.period-select.month-select { width: 85px; }
.period-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}
.period-nav .nav-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  background: #fff;
}
.period-nav .nav-btn:hover { border-color: #8b5cf6; color: #8b5cf6; }
.btn-current {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border: none;
  color: #fff;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
}
.btn-current:hover { opacity: 0.9; color: #fff; }
.filter-destination .destination-select { width: 220px; min-width: 180px; }
.filter-product .product-search-input { width: 280px; min-width: 220px; }
.table-section { margin-top: 16px; }
.data-table { width: 100%; }
.text-warning { color: #e6a23c; }

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding: 12px 0;
}

/* Batch Dialog Styles */
.dialog-header.compact-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}
.dialog-icon {
  font-size: 24px;
  color: #10b981;
}
.dialog-title {
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.batch-form-container {
  padding: 0;
}
.batch-form.compact-form {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
}
.batch-form-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  margin-bottom: 16px;
}
.inline-form-item {
  margin-bottom: 0 !important;
  margin-right: 0 !important;
}
.inline-form-item .year-select {
  width: 100px;
}
.inline-form-item .month-select {
  width: 85px;
}
.inline-form-item .destination-select {
  width: 220px;
}
.month-select-with-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}
.month-nav-buttons {
  display: flex;
  gap: 4px;
}
.month-nav-btn {
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 13px;
}
.month-nav-btn.current-month-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border: none;
  color: #fff;
}
.month-nav-btn.current-month-btn.active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}
.month-nav-btn.current-month-btn:hover {
  opacity: 0.9;
  color: #fff;
}
.load-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  padding: 8px 16px;
}
.load-btn:hover {
  opacity: 0.9;
  color: #fff;
}

.table-container {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
}
.table-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: #f0f9ff;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}
.info-text {
  font-size: 13px;
  color: #1e40af;
  font-weight: 500;
}
.batch-product-table {
  width: 100%;
}
.quantity-input {
  text-align: center;
}
.quantity-input.normal-cell :deep(.el-input__inner) {
  background: #f0fdf4;
  border-color: #86efac;
  color: #166534;
  font-weight: 500;
}
.quantity-input.warning-cell :deep(.el-input__inner) {
  background: #fef3c7;
  border-color: #fde047;
  color: #854d0e;
}

.loading-placeholder.compact-placeholder,
.empty-placeholder.compact-placeholder {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
}
.loading-placeholder .is-loading {
  font-size: 32px;
  margin-bottom: 12px;
}
.empty-placeholder p {
  margin: 0;
  font-size: 14px;
}

.dialog-footer-compact {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
.cancel-btn {
  border-radius: 6px;
  padding: 8px 20px;
}
.register-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 6px;
  padding: 8px 20px;
  color: #fff;
}
.register-btn:hover {
  opacity: 0.9;
  color: #fff;
}
</style>
