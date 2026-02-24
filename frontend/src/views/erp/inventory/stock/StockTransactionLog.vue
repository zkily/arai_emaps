<template>
  <div class="stock-log-page">
    <header class="page-header glass">
      <div class="header-inner">
        <div class="header-icon-wrap glass-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">在庫取引記録</h1>
          <p class="page-subtitle">在庫受払履歴の照会・編集</p>
        </div>
      </div>
    </header>

    <div class="page-body">
      <section class="filter-section glass">
        <div class="filter-head">
          <el-icon class="filter-head-icon"><Search /></el-icon>
          <span class="filter-head-title">検索フィルタ</span>
        </div>
        <el-form :model="filters" class="filter-form" @submit.prevent label-position="top">
          <div class="filter-block">
            <el-form-item label="在庫種別" class="filter-item full">
              <el-radio-group v-model="filters.stock_type" class="stock-type-radio" size="small">
                <el-radio-button value="">全て</el-radio-button>
                <el-radio-button value="製品">製品</el-radio-button>
                <el-radio-button value="仕掛品">仕掛品</el-radio-button>
                <el-radio-button value="部品">部品</el-radio-button>
                <el-radio-button value="材料">材料</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </div>
          <div class="filter-grid">
            <el-form-item label="製品" class="filter-item">
              <el-select
                v-model="filters.target_cd"
                placeholder="製品を選択"
                clearable
                filterable
                size="small"
                class="select-glass product-select"
              >
                <el-option
                  v-for="item in productOptions"
                  :key="item.product_cd"
                  :label="`${item.product_cd} - ${item.product_name || ''}`"
                  :value="item.product_cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="キーワード" class="filter-item">
              <el-input v-model="filters.keyword" placeholder="対象CD / 備考" clearable :prefix-icon="Search" size="small" class="input-glass" />
            </el-form-item>
            <el-form-item label="保管場所" class="filter-item">
              <el-select v-model="filters.location_cd" placeholder="選択" clearable size="small" class="select-glass">
                <el-option v-for="item in locationOptions" :key="item.cd" :label="item.name" :value="item.cd" />
              </el-select>
            </el-form-item>
            <el-form-item label="操作種別" class="filter-item">
              <el-select v-model="filters.transaction_type" placeholder="選択" clearable size="small" class="select-glass">
                <el-option v-for="item in transactionTypeOptions" :key="item.cd" :label="item.name" :value="item.cd" />
              </el-select>
            </el-form-item>
            <el-form-item label="工程" class="filter-item">
              <el-select v-model="filters.process_cd" placeholder="選択" clearable size="small" class="select-glass">
                <el-option v-for="item in processOptions" :key="item.cd" :label="item.name" :value="item.cd" />
              </el-select>
            </el-form-item>
            <el-form-item label="操作日" class="filter-item date-item">
              <div class="date-row">
                <el-date-picker
                  v-model="filters.date_range"
                  type="daterange"
                  range-separator="～"
                  start-placeholder="開始"
                  end-placeholder="終了"
                  value-format="YYYY-MM-DD"
                  unlink-panels
                  size="small"
                  class="date-picker-glass"
                />
                <div class="date-quick">
                  <el-button size="small" :icon="ArrowLeft" circle title="前日" class="btn-glass btn-ghost" @click="adjustDate(-1)" />
                  <el-button size="small" type="primary" title="今日" class="btn-glass btn-primary" @click="setToday">今日</el-button>
                  <el-button size="small" :icon="ArrowRight" circle title="翌日" class="btn-glass btn-ghost" @click="adjustDate(1)" />
                </div>
              </div>
            </el-form-item>
          </div>
        </el-form>
      </section>

      <div class="stats-row">
        <div class="stat-card glass stat-total">
          <div class="stat-icon-wrap"><el-icon><TrendCharts /></el-icon></div>
          <div class="stat-info">
            <span class="stat-label">総数量</span>
            <span class="stat-value">{{ statistics.totalQuantity.toLocaleString() }}</span>
          </div>
        </div>
        <div class="stat-card glass stat-inbound">
          <div class="stat-icon-wrap"><el-icon><DataAnalysis /></el-icon></div>
          <div class="stat-info">
            <span class="stat-label">入庫系</span>
            <span class="stat-value">{{ statistics.inboundQuantity.toLocaleString() }}</span>
          </div>
        </div>
        <div class="stat-card glass stat-outbound">
          <div class="stat-icon-wrap"><el-icon><Histogram /></el-icon></div>
          <div class="stat-info">
            <span class="stat-label">出庫系</span>
            <span class="stat-value">{{ statistics.outboundQuantity.toLocaleString() }}</span>
          </div>
        </div>
        <div class="stat-card glass stat-records">
          <div class="stat-icon-wrap"><el-icon><Document /></el-icon></div>
          <div class="stat-info">
            <span class="stat-label">総件数</span>
            <span class="stat-value">{{ statistics.totalRecords.toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <section class="table-section glass">
        <div class="table-head">
          <div class="table-head-left">
            <el-icon class="table-head-icon"><Document /></el-icon>
            <span>履歴データ一覧</span>
            <span class="table-total">総件数: {{ pagination.total }}件</span>
          </div>
          <div class="table-head-right">
            <span v-if="selectedRows.length > 0" class="selected-badge">選択中: {{ selectedRows.length }}件</span>
            <el-button
              v-if="selectedRows.length > 0"
              type="danger"
              size="small"
              :icon="Delete"
              :loading="batchDeleteLoading"
              @click="handleBatchDelete"
              class="btn-glass btn-danger"
            >
              一括削除
            </el-button>
          </div>
        </div>
        <el-table
          :data="logList"
          border
          stripe
          highlight-current-row
          size="small"
          class="data-table"
          v-loading="loading"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="44" align="center" fixed="left" />
          <el-table-column label="在庫種別" prop="stock_type" width="82" align="center">
            <template #default="scope">
              <el-tag :type="getStockTypeColor(scope.row.stock_type)" effect="light" size="small" class="cell-tag">
                {{ scope.row.stock_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="対象CD" prop="target_cd" width="92" align="center" show-overflow-tooltip />
          <el-table-column label="製品名" prop="product_name" min-width="120" show-overflow-tooltip>
            <template #default="scope">{{ scope.row.product_name || '-' }}</template>
          </el-table-column>
          <el-table-column label="保管場所" prop="location_cd" width="100" align="center" show-overflow-tooltip />
          <el-table-column label="操作種別" prop="transaction_type" width="92" align="center">
            <template #default="scope">
              <el-tag :type="getTransactionTypeColor(scope.row.transaction_type)" effect="plain" size="small" class="cell-tag">
                {{ scope.row.transaction_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="数量" prop="quantity" width="80" align="center">
            <template #default="scope">
              <span class="qty-cell" :class="{ negative: Number(scope.row.quantity) < 0 }">{{ scope.row.quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column label="単位" prop="unit" width="56" align="center">
            <template #default="scope">{{ scope.row.unit || '-' }}</template>
          </el-table-column>
          <!-- <el-table-column label="ロット" prop="lot_no" width="82" align="center" show-overflow-tooltip /> -->
          <el-table-column label="操作日時" prop="transaction_time" width="158" align="center">
            <template #default="scope">{{ formatDate(scope.row.transaction_time) }}</template>
          </el-table-column>
          <el-table-column label="工程" prop="process_name" width="100" align="center" show-overflow-tooltip>
            <template #default="scope">{{ scope.row.process_name ?? scope.row.process_cd ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="設備" prop="machine_cd" width="82" align="center" show-overflow-tooltip />
          <el-table-column label="来源" prop="source_file" width="185" align="center" show-overflow-tooltip />
          <el-table-column label="操作" fixed="right" width="160" align="center">
            <template #default="scope">
              <el-button size="small" type="primary" link @click="handleEdit(scope.row)" :icon="Edit" class="btn-inline btn-edit">編集</el-button>
              <el-button size="small" type="danger" link @click="handleDelete(scope.row)" :icon="Delete" class="btn-inline btn-delete">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap">
          <el-pagination
            layout="total, sizes, prev, pager, next"
            :total="pagination.total"
            :page-size="pagination.pageSize"
            :current-page="pagination.page"
            :page-sizes="[10, 20, 50, 100]"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
            size="small"
            class="pagination-glass"
          />
        </div>
      </section>
    </div>

    <el-dialog
      v-model="editDialogVisible"
      title="履歴データ編集"
      width="560px"
      :close-on-click-modal="false"
      class="edit-dialog glass-dialog"
      @close="handleEditDialogClose"
    >
      <el-form :model="editForm" :rules="editFormRules" ref="editFormRef" label-width="110px" label-position="right" size="small">
        <el-form-item label="在庫種別" prop="stock_type">
          <el-select v-model="editForm.stock_type" placeholder="選択" class="edit-select full">
            <el-option label="製品" value="製品" /><el-option label="仕掛品" value="仕掛品" /><el-option label="部品" value="部品" /><el-option label="材料" value="材料" />
          </el-select>
        </el-form-item>
        <el-form-item label="対象CD" prop="target_cd">
          <el-input v-model="editForm.target_cd" placeholder="対象CD" />
        </el-form-item>
        <el-form-item label="保管場所" prop="location_cd">
          <el-select v-model="editForm.location_cd" placeholder="選択" class="edit-select full">
            <el-option v-for="item in locationOptions" :key="item.cd" :label="item.name" :value="item.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作種別" prop="transaction_type">
          <el-select v-model="editForm.transaction_type" placeholder="選択" class="edit-select full">
            <el-option v-for="item in transactionTypeOptions" :key="item.cd" :label="item.name" :value="item.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="editForm.quantity" :min="-999999" :max="999999" :precision="4" class="edit-input-number full" />
        </el-form-item>
        <el-form-item label="単位" prop="unit">
          <el-input v-model="editForm.unit" placeholder="kg, pcs, m など" />
        </el-form-item>
        <el-form-item label="ロット番号" prop="lot_no">
          <el-input v-model="editForm.lot_no" placeholder="ロット番号" />
        </el-form-item>
        <el-form-item label="操作日時" prop="transaction_time">
          <el-date-picker v-model="editForm.transaction_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="選択" class="edit-date full" />
        </el-form-item>
        <el-form-item label="工程" prop="process_cd">
          <el-select v-model="editForm.process_cd" placeholder="選択" clearable class="edit-select full">
            <el-option v-for="item in processOptions" :key="item.cd" :label="item.name" :value="item.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="設備CD" prop="machine_cd">
          <el-input v-model="editForm.machine_cd" placeholder="設備CD" />
        </el-form-item>
        <el-form-item label="関連伝票No" prop="order_no">
          <el-input v-model="editForm.order_no" placeholder="受注No, 発注No 等" />
        </el-form-item>
        <el-form-item label="担当者名" prop="operator_name">
          <el-input v-model="editForm.operator_name" placeholder="担当者名" />
        </el-form-item>
        <el-form-item label="来源" prop="source_file">
          <el-input v-model="editForm.source_file" placeholder="手入力 / 文件名等" />
        </el-form-item>
        <el-form-item label="備考" prop="remarks">
          <el-input v-model="editForm.remarks" type="textarea" :rows="2" placeholder="備考" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button size="small" @click="editDialogVisible = false" class="btn-glass btn-secondary">キャンセル</el-button>
          <el-button type="primary" size="small" @click="handleSaveEdit" :loading="editLoading" class="btn-glass btn-primary">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue'
import request from '@/utils/request'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, Document, Search, TrendCharts, DataAnalysis, Histogram, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import type { OptionItem } from '@/types/master'

const locationOptions = ref([
  { cd: '製品倉庫', name: '製品倉庫' },
  { cd: '仮設倉庫', name: '仮設倉庫' },
  { cd: '部品倉庫', name: '部品倉庫' },
  { cd: '仕上倉庫', name: '仕上倉庫' },
  { cd: 'メッキ倉庫', name: 'メッキ倉庫' },
  { cd: '工程中間在庫', name: '工程中間在庫' },
  { cd: '材料置場', name: '材料置場' },
  { cd: '外注倉庫', name: '外注倉庫' },
  { cd: 'その他', name: 'その他' },
])

const transactionTypeOptions = ref([
  { cd: '入庫', name: '入庫' },
  { cd: '出庫', name: '出庫' },
  { cd: '実績', name: '実績' },
  { cd: '不良', name: '不良' },
  { cd: '廃棄', name: '廃棄' },
  { cd: '保留', name: '保留' },
  { cd: '調整', name: '調整' },
  { cd: '初期', name: '初期' },
])

const processOptions = ref<OptionItem[]>([])
const productOptions = ref<Array<{ product_cd: string; product_name?: string }>>([])

const getStockTypeColor = (type: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  const map: Record<string, 'success' | 'warning' | 'info' | 'primary' | 'danger'> = {
    製品: 'primary',
    材料: 'success',
    部品: 'warning',
    仕掛品: 'info',
  }
  return map[type] || 'danger'
}

const getTransactionTypeColor = (type: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  const map: Record<string, 'success' | 'warning' | 'info' | 'primary' | 'danger'> = {
    入庫: 'success',
    出庫: 'danger',
    実績: 'primary',
    不良: 'danger',
    廃棄: 'warning',
    保留: 'info',
    調整: 'warning',
    初期: 'info',
  }
  return map[type] ?? 'info'
}

const loading = ref(false)
const batchDeleteLoading = ref(false)
const editLoading = ref(false)
const logList = ref<StockLogRow[]>([])
const selectedRows = ref<StockLogRow[]>([])
const editDialogVisible = ref(false)
const editFormRef = ref()

const filters = ref({
  stock_type: '',
  target_cd: '',
  keyword: '',
  location_cd: '',
  transaction_type: '',
  process_cd: '',
  date_range: [dayjs().format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')] as string[],
})

const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

const statistics = ref({
  totalQuantity: 0,
  inboundQuantity: 0,
  outboundQuantity: 0,
  totalRecords: 0,
})

interface StockLogRow {
  id: number
  stock_type: string
  transaction_type: string
  target_cd: string
  product_name?: string
  location_cd: string
  lot_no?: string
  process_cd?: string
  process_name?: string
  machine_cd?: string
  quantity: number
  unit?: string
  order_no?: string
  related_log_id?: number
  operator_id?: string
  operator_name?: string
  transaction_time: string
  created_at?: string
  source_file?: string
  remarks?: string
}

const formatDate = (val: string) => (val ? dayjs(val).format('YYYY-MM-DD HH:mm:ss') : '-')

const API_BASE = '/api/erp/stock-transaction-logs'

function buildParams() {
  const d = filters.value.date_range
  return {
    stock_type: filters.value.stock_type || undefined,
    target_cd: filters.value.target_cd || undefined,
    keyword: filters.value.keyword || undefined,
    location_cd: filters.value.location_cd || undefined,
    transaction_type: filters.value.transaction_type || undefined,
    process_cd: filters.value.process_cd || undefined,
    date_start: d && d[0] ? d[0] : undefined,
    date_end: d && d[1] ? d[1] : undefined,
    page: pagination.value.page,
    pageSize: pagination.value.pageSize,
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = (await request.get(API_BASE, { params: buildParams() })) as {
      list?: StockLogRow[]
      total?: number
      totalQuantity?: number
      inboundQuantity?: number
      outboundQuantity?: number
    }
    const list = res?.list ?? []
    const total = res?.total ?? 0
    logList.value = list
    pagination.value.total = total

    // 統計は筛选条件の全件合計（API で返却）
    statistics.value = {
      totalQuantity: Number(res?.totalQuantity) ?? 0,
      inboundQuantity: Number(res?.inboundQuantity) ?? 0,
      outboundQuantity: Number(res?.outboundQuantity) ?? 0,
      totalRecords: total,
    }
  } catch (err) {
    console.error('在庫取引履歴の取得に失敗しました', err)
    ElMessage.error('データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// フィルタ変更で自動検索（デバウンス 350ms）
let filterDebounceId: ReturnType<typeof setTimeout> | null = null
watch(
  filters,
  () => {
    pagination.value.page = 1
    if (filterDebounceId) clearTimeout(filterDebounceId)
    filterDebounceId = setTimeout(() => {
      filterDebounceId = null
      fetchLogs()
    }, 350)
  },
  { deep: true }
)

const adjustDate = (days: number) => {
  if (filters.value.date_range && filters.value.date_range.length === 2) {
    const start = dayjs(filters.value.date_range[0]).add(days, 'day').format('YYYY-MM-DD')
    const end = dayjs(filters.value.date_range[1]).add(days, 'day').format('YYYY-MM-DD')
    filters.value.date_range = [start, end]
  }
}

const setToday = () => {
  const today = dayjs().format('YYYY-MM-DD')
  filters.value.date_range = [today, today]
}

const handleSelectionChange = (selection: StockLogRow[]) => {
  selectedRows.value = selection
}

const handlePageChange = (newPage: number) => {
  pagination.value.page = newPage
  selectedRows.value = []
  fetchLogs()
}

const handleSizeChange = (newSize: number) => {
  pagination.value.pageSize = newSize
  pagination.value.page = 1
  selectedRows.value = []
  fetchLogs()
}

const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('削除する項目を選択してください')
    return
  }
  try {
    await ElMessageBox.confirm(
      `選択した${selectedRows.value.length}件のデータを削除しますか？\nこの操作は取り消せません。`,
      '一括削除確認',
      { type: 'warning', confirmButtonText: '削除実行', cancelButtonText: 'キャンセル' }
    )
    batchDeleteLoading.value = true
    await request.post(`${API_BASE}/batch-delete`, { ids: selectedRows.value.map((r) => r.id) })
    ElMessage.success('削除しました')
    selectedRows.value = []
    await fetchLogs()
  } catch (e: unknown) {
    if (e !== 'cancel') ElMessage.error('一括削除に失敗しました')
  } finally {
    batchDeleteLoading.value = false
  }
}

const handleDelete = async (row: StockLogRow) => {
  try {
    await ElMessageBox.confirm(`本当に削除しますか？ 対象CD: ${row.target_cd}`, '確認', { type: 'warning' })
    loading.value = true
    await request.delete(`${API_BASE}/${row.id}`)
    ElMessage.success('削除しました')
    await fetchLogs()
  } catch (e: unknown) {
    if (e !== 'cancel') ElMessage.error('削除に失敗しました')
  } finally {
    loading.value = false
  }
}

const editForm = ref<Partial<StockLogRow>>({})
const editFormRules = {
  stock_type: [{ required: true, message: '在庫種別を選択してください', trigger: 'change' }],
  target_cd: [{ required: true, message: '対象CDを入力してください', trigger: 'blur' }],
  location_cd: [{ required: true, message: '保管場所を選択してください', trigger: 'change' }],
  transaction_type: [{ required: true, message: '操作種別を選択してください', trigger: 'change' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }],
  transaction_time: [{ required: true, message: '操作日時を選択してください', trigger: 'change' }],
}

const handleEdit = (row: StockLogRow) => {
  editForm.value = {
    id: row.id,
    stock_type: row.stock_type,
    target_cd: row.target_cd,
    location_cd: row.location_cd,
    transaction_type: row.transaction_type,
    quantity: row.quantity,
    unit: row.unit ?? '',
    lot_no: row.lot_no ?? '',
    process_cd: row.process_cd ?? '',
    machine_cd: row.machine_cd ?? '',
    order_no: row.order_no ?? '',
    operator_name: row.operator_name ?? '',
    source_file: row.source_file ?? '',
    remarks: row.remarks ?? '',
    transaction_time: row.transaction_time ? dayjs(row.transaction_time).format('YYYY-MM-DD HH:mm:ss') : '',
  }
  editDialogVisible.value = true
}

const handleSaveEdit = async () => {
  if (!editFormRef.value) return
  try {
    await editFormRef.value.validate()
    editLoading.value = true
    await request.put(`${API_BASE}/${editForm.value.id}`, editForm.value)
    ElMessage.success('更新しました')
    editDialogVisible.value = false
    await fetchLogs()
  } catch (e: unknown) {
    if (e !== false) ElMessage.error('更新に失敗しました')
  } finally {
    editLoading.value = false
  }
}

const handleEditDialogClose = () => {
  editFormRef.value?.resetFields()
  editForm.value = {}
}

const loadProcessOptions = async () => {
  try {
    const res = await request.get<OptionItem[]>('/api/master/processes/options')
    processOptions.value = Array.isArray(res) ? res : (res as { data?: OptionItem[] })?.data ?? []
  } catch {
    processOptions.value = []
  }
}

const loadProductOptions = async () => {
  try {
    const res = await request.get('/api/database/production-summarys/products')
    const list = (res as { data?: Array<{ product_cd: string; product_name?: string }> })?.data ?? (Array.isArray(res) ? res : [])
    productOptions.value = [...list].sort((a, b) => (a.product_name || '').localeCompare(b.product_name || '') || (a.product_cd || '').localeCompare(b.product_cd || ''))
  } catch {
    productOptions.value = []
  }
}

onMounted(async () => {
  await Promise.all([loadProcessOptions(), loadProductOptions()])
  await fetchLogs()
})
</script>

<style scoped>
/* ----- 玻璃质感基础 ----- */
.glass {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

/* ----- 页面容器 ----- */
.stock-log-page {
  min-height: 100vh;
  padding: 8px 10px 16px;
  background: linear-gradient(160deg, #e8ecf1 0%, #dde2e8 50%, #e2e7ee 100%);
  font-size: 13px;
}

/* ----- 页头 ----- */
.page-header {
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 8px;
}
.header-inner {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-icon-wrap {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(135deg, #5b8def 0%, #7ba8f5 100%);
  box-shadow: 0 2px 10px rgba(91, 141, 239, 0.4);
}
.header-text { flex: 1; min-width: 0; }
.page-title { margin: 0; font-size: 1.05rem; font-weight: 700; color: #1e293b; letter-spacing: 0.02em; }
.page-subtitle { margin: 2px 0 0; font-size: 0.7rem; color: #64748b; }

/* ----- 主体 ----- */
.page-body { display: flex; flex-direction: column; gap: 8px; max-width: 100%; }

/* ----- 筛选区 ----- */
.filter-section {
  border-radius: 10px;
  padding: 8px 12px 10px;
}
.filter-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.filter-head-icon { color: #5b8def; font-size: 14px; }
.filter-head-title { font-weight: 600; font-size: 0.8rem; color: #334155; }
.filter-form :deep(.el-form-item) { margin-bottom: 6px; }
.filter-form :deep(.el-form-item__label) { font-size: 0.7rem; color: #64748b; padding-bottom: 2px; }
.filter-block { margin-bottom: 4px; }
.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 6px 10px;
  align-items: start;
}
.filter-item.full { grid-column: 1 / -1; }
.filter-item.date-item { grid-column: span 2; }
.input-glass,
.select-glass { width: 100%; }
.input-glass :deep(.el-input__wrapper),
.select-glass :deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
  box-shadow: none;
}
.date-row {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
}
.date-picker-glass { flex: 1; min-width: 0; }
.date-picker-glass :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
}
.date-quick { display: flex; gap: 4px; flex-shrink: 0; }
.btn-glass {
  border-radius: 6px;
  font-weight: 500;
  border: 1px solid transparent;
  backdrop-filter: blur(8px);
}
.btn-glass.btn-primary {
  background: linear-gradient(135deg, #5b8def 0%, #7ba8f5 100%);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 8px rgba(91, 141, 239, 0.35);
}
.btn-glass.btn-primary:hover { filter: brightness(1.08); }
.btn-glass.btn-secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #475569;
  border-color: rgba(0, 0, 0, 0.1);
}
.btn-glass.btn-secondary:hover { background: rgba(255, 255, 255, 0.95); color: #1e293b; }
.btn-glass.btn-danger {
  background: linear-gradient(135deg, #e85347 0%, #ef6b60 100%);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 2px 8px rgba(232, 83, 71, 0.35);
}
.btn-glass.btn-ghost {
  background: rgba(255, 255, 255, 0.6);
  color: #64748b;
  border-color: rgba(0, 0, 0, 0.08);
}
.filter-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.stock-type-radio { width: 100%; display: flex; flex-wrap: wrap; gap: 0 2px; }
.stock-type-radio :deep(.el-radio-button__inner) {
  padding: 4px 10px;
  font-size: 0.75rem;
  height: 26px;
  line-height: 18px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
}
.stock-type-radio :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #5b8def 0%, #7ba8f5 100%);
  border-color: transparent;
  color: #fff;
}

/* ----- 统计卡片 ----- */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}
.stat-card {
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.stat-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.stat-total .stat-icon-wrap { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4); }
.stat-inbound .stat-icon-wrap { background: linear-gradient(135deg, #10b981 0%, #34d399 100%); box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4); }
.stat-outbound .stat-icon-wrap { background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%); box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4); }
.stat-records .stat-icon-wrap { background: linear-gradient(135deg, #f43f5e 0%, #fb7185 100%); box-shadow: 0 2px 8px rgba(244, 63, 94, 0.4); }
.stat-info { display: flex; flex-direction: column; gap: 0; min-width: 0; }
.stat-label { font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.03em; }
.stat-value { font-size: 1rem; font-weight: 700; color: #1e293b; line-height: 1.2; }

/* ----- 表格区 ----- */
.table-section {
  border-radius: 10px;
  padding: 8px 10px 10px;
  overflow: hidden;
}
.table-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.table-head-left {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.8rem;
  color: #334155;
}
.table-head-icon { color: #5b8def; font-size: 14px; }
.table-total { font-size: 0.7rem; font-weight: 500; color: #64748b; margin-left: 8px; }
.table-head-right { display: flex; align-items: center; gap: 8px; }
.selected-badge {
  font-size: 0.7rem;
  color: #5b8def;
  font-weight: 500;
  padding: 2px 8px;
  background: rgba(91, 141, 239, 0.12);
  border-radius: 6px;
  border: 1px solid rgba(91, 141, 239, 0.25);
}
.data-table { border-radius: 8px; overflow: hidden; font-size: 0.75rem; }
.data-table :deep(.el-table__header th) {
  background: rgba(248, 250, 252, 0.95);
  color: #475569;
  font-weight: 600;
  font-size: 0.7rem;
  padding: 6px 8px;
}
.data-table :deep(.el-table__body td) { padding: 4px 8px; font-size: 0.75rem; }
.cell-tag { font-size: 0.65rem; padding: 0 5px; height: 20px; line-height: 18px; }
.qty-cell { font-weight: 600; font-size: 0.8rem; color: #10b981; }
.qty-cell.negative { color: #ef4444; }
.btn-inline { padding: 2px 6px; font-size: 0.7rem; }
.btn-inline.btn-edit { color: #5b8def; }
.btn-inline.btn-delete { color: #ef4444; }
.pagination-wrap { margin-top: 6px; display: flex; justify-content: flex-end; padding: 4px 0; }
.pagination-glass :deep(.el-pagination__total),
.pagination-glass :deep(.btn-prev),
.pagination-glass :deep(.btn-next),
.pagination-glass :deep(.el-pager li) { font-size: 0.75rem; }

/* ----- 编辑弹窗 ----- */
.glass-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}
.glass-dialog :deep(.el-dialog__header) { padding: 10px 14px; border-bottom: 1px solid rgba(0, 0, 0, 0.06); }
.glass-dialog :deep(.el-dialog__body) { padding: 12px 14px; }
.glass-dialog :deep(.el-form-item) { margin-bottom: 8px; }
.edit-select.full, .edit-input-number.full, .edit-date.full { width: 100%; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 6px; }

/* ----- 响应式 ----- */
@media (max-width: 992px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .filter-grid .filter-item.date-item { grid-column: span 1; }
}
@media (max-width: 768px) {
  .stock-log-page { padding: 6px 8px 12px; }
  .page-header { padding: 8px 10px; }
  .header-icon-wrap { width: 30px; height: 30px; }
  .page-title { font-size: 0.95rem; }
  .filter-section { padding: 6px 10px 8px; }
  .filter-grid { grid-template-columns: 1fr; }
  .filter-item.date-item { grid-column: span 1; }
  .date-row { flex-wrap: wrap; }
  .date-picker-glass { min-width: 100%; }
  .stats-row { grid-template-columns: 1fr; gap: 4px; }
  .stat-card { padding: 6px 8px; }
  .table-head { flex-direction: column; align-items: flex-start; }
  .table-head-right { width: 100%; justify-content: flex-end; }
  .data-table :deep(.el-table__header th),
  .data-table :deep(.el-table__body td) { padding: 4px 6px; font-size: 0.7rem; }
}
@media (max-width: 576px) {
  .stock-log-page { padding: 4px 6px 10px; }
  .page-title { font-size: 0.9rem; }
  .stat-value { font-size: 0.9rem; }
  .pagination-glass :deep(.el-pagination__sizes) { display: none; }
}
</style>
