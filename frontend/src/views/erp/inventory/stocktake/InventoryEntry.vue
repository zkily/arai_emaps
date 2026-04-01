<template>
  <div class="inventory-entry-page">
    <div class="page-ambient" aria-hidden="true" />
    <header class="page-toolbar">
      <div class="toolbar-main">
        <div class="toolbar-brand">
          <div class="brand-icon">
            <el-icon><DocumentAdd /></el-icon>
          </div>
          <div class="brand-text">
            <h1 class="toolbar-title">棚卸登録</h1>
            <p class="toolbar-sub">材料・部品・ステーの棚卸を入力</p>
          </div>
        </div>
        <div class="toolbar-actions">
          <el-button
            type="primary"
            size="default"
            @click="handleNewInput"
            v-if="!showForm"
          >
            <el-icon><Plus /></el-icon>
            新規入力
          </el-button>
          <el-button type="success" size="default" @click="handleBatchInput" v-if="!showForm">
            <el-icon><DocumentAdd /></el-icon>
            一括入力
          </el-button>
          <el-button @click="goBack" v-if="showForm" plain>
            <el-icon><ArrowLeft /></el-icon>
            一覧に戻る
          </el-button>
        </div>
      </div>
    </header>

    <div v-if="showForm" class="form-panel">
      <InventoryEntryForm
        :submitting="submitting"
        :initial-data="lastFormData"
        @submit="handleFormSubmit"
        @cancel="handleFormCancel"
      />
    </div>

    <div v-else class="history-panel">
      <el-card class="history-card" shadow="never">
        <template #header>
          <div class="history-toolbar">
            <div class="history-toolbar-left">
              <h2 class="history-title">手入力記録</h2>
              <el-tag type="info" effect="light" size="small" class="history-badge">
                手入力のみ
              </el-tag>
            </div>
            <div class="history-toolbar-right">
              <el-select
                v-model="selectedProcessCd"
                placeholder="工程"
                clearable
                filterable
                size="small"
                class="process-filter-select"
                @change="applyDisplayFilters"
              >
                <el-option
                  :label="processFilterNoneLabel"
                  :value="PROCESS_FILTER_NONE"
                />
                <el-option
                  v-for="p in processFilterOptions"
                  :key="p.process_cd"
                  :label="`${p.process_name} (${p.process_cd})`"
                  :value="p.process_cd"
                />
              </el-select>
              <el-date-picker
                v-model="selectedMonth"
                type="month"
                placeholder="月"
                format="YYYY-MM"
                value-format="YYYY-MM"
                size="small"
                @change="handleMonthChange"
                class="month-picker-compact"
              />
              <el-button text size="small" @click="clearFilter">
                <el-icon><Close /></el-icon>
                クリア
              </el-button>
              <el-button text size="small" @click="refreshHistory">
                <el-icon><Refresh /></el-icon>
                更新
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          :data="pagedRecentEntries"
          border
          stripe
          size="small"
          v-loading="historyLoading"
          class="history-table"
          @sort-change="handleSortChange"
          :default-sort="{ prop: 'log_date', order: 'descending' }"
          table-layout="fixed"
        >
          <el-table-column
            label="項目"
            prop="item"
            width="100"
            align="center"
            header-align="center"
          >
            <template #default="scope">
              <el-tag :type="getItemTypeColor(scope.row.item)" effect="light">
                {{ scope.row.item }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            label="製品CD"
            prop="product_cd"
            width="140"
            align="center"
            header-align="center"
          />
          <el-table-column
            label="製品名"
            prop="product_name"
            min-width="140"
            align="left"
            header-align="center"
            sortable
          />
          <el-table-column
            label="工程名"
            prop="process_name"
            width="120"
            align="center"
            header-align="center"
          />
          <el-table-column
            label="数量"
            prop="quantity"
            width="100"
            align="center"
            header-align="center"
          >
            <template #default="scope">
              <span :class="getQuantityClass(scope.row.quantity)">{{ scope.row.quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="作業者"
            prop="worker_name"
            width="100"
            align="center"
            header-align="center"
          >
            <template #default="scope">
              <span>{{ scope.row.worker_name || scope.row.remarks || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="棚卸日"
            prop="log_date"
            width="108"
            align="center"
            header-align="center"
          >
            <template #default="scope">
              {{ formatLogDate(scope.row.log_date) }}
            </template>
          </el-table-column>
          <el-table-column
            label="入力日時"
            prop="updated_at"
            width="160"
            align="center"
            header-align="center"
          >
            <template #default="scope">
              {{ formatDateTime(scope.row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="88"
            align="center"
            header-align="center"
            fixed="right"
          >
            <template #default="scope">
              <el-button
                type="danger"
                size="small"
                link
                @click="handleDelete(scope.row)"
                :loading="scope.row.deleting"
              >
                <el-icon><Delete /></el-icon>
                削除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div
          v-if="recentEntries.length > 0"
          class="history-pagination-wrap"
        >
          <div class="history-qty-summary" aria-live="polite">
            <span class="history-qty-summary-label">数量合計</span>
            <span
              class="history-qty-summary-value"
              :class="getQuantityClass(filteredQuantityTotal)"
            >
              {{ filteredQuantityTotal }}
            </span>
            <span class="history-qty-summary-meta">
              （フィルター対象 {{ recentEntries.length }} 件・全ページ集計）
            </span>
          </div>
          <el-pagination
            v-model:current-page="historyCurrentPage"
            :page-size="HISTORY_PAGE_SIZE"
            :total="recentEntries.length"
            layout="total, prev, pager, next"
            size="small"
            background
          />
        </div>

        <div class="empty-state" v-if="recentEntries.length === 0 && !historyLoading">
          <el-empty description="手入力記録がありません" :image-size="72">
            <el-button type="primary" size="small" @click="handleNewInput">
              <el-icon><Plus /></el-icon>
              入力開始
            </el-button>
          </el-empty>
        </div>
      </el-card>
    </div>

    <!-- 成功提示 -->
    <el-dialog
      v-model="successDialogVisible"
      title="入力完了"
      width="400px"
      center
      :show-close="false"
      class="success-dialog"
    >
      <div class="success-content">
        <div class="success-animation">
          <div class="success-circle">
            <div class="success-checkmark">
              <div class="checkmark-stem"></div>
              <div class="checkmark-kick"></div>
            </div>
          </div>
        </div>
        <h3 class="success-title">入力完了</h3>
        <p class="success-message">棚卸情報の入力が完了しました！</p>
        <div class="success-details">
          <div class="detail-item">
            <span class="detail-label">製品CD:</span>
            <span class="detail-value">{{ lastEntry?.product_cd }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">製品名:</span>
            <span class="detail-value">{{ lastEntry?.product_name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">数量:</span>
            <span class="detail-value quantity-highlight">{{ lastEntry?.quantity }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleContinueInput" class="continue-btn">
            <el-icon><Plus /></el-icon>
            続けて入力
          </el-button>
          <el-button type="primary" @click="handleSuccessConfirm" class="confirm-btn">
            <el-icon><CircleCheckFilled /></el-icon>
            完了
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量录入弹窗 -->
    <BatchInventoryEntryDialog v-model:visible="batchDialogVisible" @success="handleBatchSuccess" />

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="削除確認"
      width="400px"
      center
      :show-close="false"
      class="delete-dialog"
    >
      <div class="delete-content">
        <div class="delete-animation">
          <div class="warning-circle">
            <div class="warning-icon">
              <div class="warning-line"></div>
              <div class="warning-dot"></div>
            </div>
          </div>
        </div>
        <h3 class="delete-title">削除確認</h3>
        <p class="delete-message">この記録を削除しますか？</p>
        <div class="delete-details">
          <div class="detail-item">
            <span class="detail-label">項目:</span>
            <span class="detail-value">{{ deleteTarget?.item }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">製品CD:</span>
            <span class="detail-value">{{ deleteTarget?.product_cd }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">製品名:</span>
            <span class="detail-value">{{ deleteTarget?.product_name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">数量:</span>
            <span class="detail-value">{{ deleteTarget?.quantity }}</span>
          </div>
        </div>
        <div class="delete-warning">
          <el-icon><WarningFilled /></el-icon>
          この操作は取り消すことができません。
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="deleteDialogVisible = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button type="danger" @click="confirmDelete" :loading="deleting" class="delete-btn">
            <el-icon><Delete /></el-icon>
            削除
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus,
  ArrowLeft,
  Refresh,
  CircleCheckFilled,
  Delete,
  WarningFilled,
  DocumentAdd,
  Close,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import InventoryEntryForm from './components/InventoryEntryForm.vue'
import BatchInventoryEntryDialog from './components/BatchInventoryEntryDialog.vue'
import {
  createInventoryEntry,
  getRecentEntries,
  deleteInventoryLog,
  type InventoryLog,
} from '@/api/inventory'
import { getProcesses } from '@/api/stocktake/common'
import type { ProcessItem } from '@/types/master'

/** 工程フィルター：工程コード未設定の行のみ（材料・部品など） */
const PROCESS_FILTER_NONE = '__filter_no_process__' as const
const processFilterNoneLabel = '工程なし（材料・部品など）'

// 响应式数据
const showForm = ref(false)
const submitting = ref(false)
const historyLoading = ref(false)
const successDialogVisible = ref(false)
const lastEntry = ref<any>(null)
const lastFormData = ref<any>({})

// 最近录入记录（月・工程フィルター適用後）
const recentEntries = ref<InventoryLog[]>([])

/** API から取得した直近一覧（クライアント側で月・工程を絞り込み） */
const historyRawEntries = ref<InventoryLog[]>([])

const processFilterOptions = ref<ProcessItem[]>([])
const selectedProcessCd = ref<string>('')

/** 手入力記録：1ページあたり件数 */
const HISTORY_PAGE_SIZE = 25
const historyCurrentPage = ref(1)

const pagedRecentEntries = computed(() => {
  const list = recentEntries.value
  const start = (historyCurrentPage.value - 1) * HISTORY_PAGE_SIZE
  return list.slice(start, start + HISTORY_PAGE_SIZE)
})

/** 現在のフィルターに一致する全行の数量合計（ページ分割前の一覧で集計） */
const filteredQuantityTotal = computed(() =>
  recentEntries.value.reduce((sum, r) => sum + (Number(r.quantity) || 0), 0),
)

// 排序相关状态
const sortBy = ref('log_date')
const sortOrder = ref<'ascending' | 'descending'>('descending')

// 筛选相关状态
const selectedMonth = ref<string>('')

// 删除相关状态
const deleteDialogVisible = ref(false)
const deleteTarget = ref<InventoryLog | null>(null)
const deleting = ref(false)

// 批量录入相关状态
const batchDialogVisible = ref(false)
const getItemTypeColor = (type: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  switch (type) {
    case '材料棚卸':
      return 'success'
    case '部品棚卸':
      return 'warning'
    case '製品棚卸':
      return 'primary'
    default:
      return 'info'
  }
}

// 获取数量样式类
const getQuantityClass = (quantity: number): string => {
  if (quantity <= 0) return 'out-of-stock'
  if (quantity <= 10) return 'low-stock'
  return 'normal-stock'
}

// 格式化日期时间
const formatDateTime = (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm:ss')

/** 棚卸日（log_date）表示 */
function formatLogDate(val: string | undefined) {
  if (val == null || String(val).trim() === '') return '-'
  const d = dayjs(val)
  return d.isValid() ? d.format('YYYY-MM-DD') : '-'
}

function applyDisplayFilters() {
  let rows = [...historyRawEntries.value]

  if (selectedMonth.value) {
    const selectedYm = dayjs(selectedMonth.value + '-01').format('YYYY-MM')
    rows = rows.filter((entry: InventoryLog) => {
      const raw = entry.log_date
      if (raw == null || String(raw).trim() === '') return false
      const d = dayjs(raw)
      if (!d.isValid()) return false
      return d.format('YYYY-MM') === selectedYm
    })
  }

  if (selectedProcessCd.value === PROCESS_FILTER_NONE) {
    rows = rows.filter(
      (e) => !e.process_cd || String(e.process_cd).trim() === '',
    )
  } else if (selectedProcessCd.value) {
    rows = rows.filter((e) => (e.process_cd || '') === selectedProcessCd.value)
  }

  recentEntries.value = rows
  historyCurrentPage.value = 1
}

async function loadProcessFilterOptions() {
  try {
    processFilterOptions.value = await getProcesses()
  } catch (error: unknown) {
    console.error('工程マスタ取得失敗:', error)
    processFilterOptions.value = []
  }
}

// 处理表单提交
const handleFormSubmit = async (data: any) => {
  submitting.value = true

  try {
    // 调用API创建库存记录
    const response = await createInventoryEntry(data)
    console.log('创建库存记录响应:', response)

    // 响应拦截器已经处理了数据结构
    lastEntry.value = response.data || response

    // 保存表单数据用于继续输入
    lastFormData.value = {
      item:
        data.item === '材料棚卸'
          ? '材料'
          : data.item === '部品棚卸'
            ? '部品'
            : data.item === '製品棚卸'
              ? 'ステー'
              : data.item,
      product_cd: data.product_cd,
      product_name: data.product_name,
      process_cd: data.process_cd,
      process_name: data.process_name,
      remarks: data.remarks,
      // 重置数量和时间相关字段
      quantity: 0,
      log_date: dayjs().format('YYYY-MM-DD'),
      log_time: dayjs().format('HH:mm:ss'),
      hd_no: '手入力',
      pack_qty: null,
      case_qty: null,
    }

    successDialogVisible.value = true
    showForm.value = false

    ElMessage.success('棚卸情報の入力が完了しました！')
  } catch (error: any) {
    console.error('创建库存记录失败:', error)
    ElMessage.error('入力に失敗しました。再試行してください: ' + (error.message || error))
  } finally {
    submitting.value = false
  }
}

// 处理表单取消
const handleFormCancel = () => {
  showForm.value = false
}

// 处理成功确认
const handleSuccessConfirm = () => {
  successDialogVisible.value = false
  refreshHistory()
}

// 处理继续输入
const handleContinueInput = () => {
  successDialogVisible.value = false
  showForm.value = true
  // 表单组件会自动使用 lastFormData 作为初始数据
}

// 处理新規入力
const handleNewInput = () => {
  // 清空上次的表单数据
  lastFormData.value = {
    item: '',
    product_cd: '',
    product_name: '',
    process_cd: '',
    process_name: '',
    remarks: '',
    quantity: 0,
    log_date: dayjs().format('YYYY-MM-DD'),
    log_time: dayjs().format('HH:mm:ss'),
    hd_no: '手入力',
    pack_qty: null,
    case_qty: null,
  }
  showForm.value = true
}

// 处理批量录入
const handleBatchInput = () => {
  batchDialogVisible.value = true
}

// 处理批量录入成功
const handleBatchSuccess = () => {
  refreshHistory()
  ElMessage.success('一括棚卸登録が完了しました！')
}

// 处理排序变化
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  sortBy.value = prop
  sortOrder.value = order as 'ascending' | 'descending'

  // 对数据进行排序
  recentEntries.value.sort((a: any, b: any) => {
    let aValue = a[prop]
    let bValue = b[prop]

    // 如果是字符串，进行字符串比较
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    }

    if (order === 'ascending') {
      return aValue > bValue ? 1 : aValue < bValue ? -1 : 0
    } else {
      return aValue < bValue ? 1 : aValue > bValue ? -1 : 0
    }
  })
}

// 处理月份筛选变化
const handleMonthChange = async (month: string) => {
  selectedMonth.value = month
  await filterEntriesByMonth()
}

// 清除筛选
const clearFilter = () => {
  selectedMonth.value = ''
  selectedProcessCd.value = ''
  refreshHistory()
}

// 根据月份筛选记录
const filterEntriesByMonth = async () => {
  if (!selectedMonth.value) {
    refreshHistory()
    return
  }

  historyLoading.value = true
  try {
    const response = await getRecentEntries(500, '手入力')
    const allEntries = Array.isArray(response) ? response : response.data || []

    historyRawEntries.value = allEntries
    applyDisplayFilters()
    console.log(`筛选出 ${recentEntries.value.length} 条 ${selectedMonth.value} 的记录`)
  } catch (error: any) {
    console.error('月份筛选失败:', error)
    ElMessage.error('月別フィルターに失敗しました')
  } finally {
    historyLoading.value = false
  }
}

// 刷新历史记录
const refreshHistory = async () => {
  historyLoading.value = true

  try {
    console.log('开始获取最近录入记录...')
    const response = await getRecentEntries(500, '手入力')
    console.log('API 响应:', response)
    // 响应拦截器已经处理了数据结构，直接使用 response
    const allEntries = Array.isArray(response) ? response : response.data || []

    historyRawEntries.value = allEntries
    applyDisplayFilters()
    console.log('设置到 recentEntries:', recentEntries.value)
  } catch (error: any) {
    console.error('获取历史记录失败:', error)
    ElMessage.error('履歴記録の取得に失敗しました: ' + (error.message || error))
  } finally {
    historyLoading.value = false
  }
}

// 返回列表
const goBack = () => {
  showForm.value = false
  refreshHistory()
}

// 处理删除
const handleDelete = (row: InventoryLog) => {
  deleteTarget.value = row
  deleteDialogVisible.value = true
}

// 确认删除
const confirmDelete = async () => {
  if (!deleteTarget.value) return

  deleting.value = true
  try {
    await deleteInventoryLog(deleteTarget.value.id)
    ElMessage.success('記録を削除しました')
    deleteDialogVisible.value = false
    deleteTarget.value = null
    refreshHistory() // 刷新列表
  } catch (error: any) {
    console.error('删除失败:', error)
    ElMessage.error('削除に失敗しました: ' + (error.message || error))
  } finally {
    deleting.value = false
  }
}

// 组件挂载时加载工程选项与历史记录
onMounted(() => {
  void loadProcessFilterOptions()
  void refreshHistory()
})
</script>

<style scoped>
@keyframes glow {
  0%,
  100% {
    box-shadow: 0 0 16px rgba(14, 165, 233, 0.25);
  }
  50% {
    box-shadow: 0 0 28px rgba(14, 165, 233, 0.45);
  }
}

@keyframes successCheckmark {
  0% {
    stroke-dashoffset: 100;
  }
  100% {
    stroke-dashoffset: 0;
  }
}

@keyframes successCircle {
  0% {
    transform: scale(0) rotate(0deg);
    opacity: 0;
  }
  50% {
    transform: scale(1.1) rotate(180deg);
    opacity: 1;
  }
  100% {
    transform: scale(1) rotate(360deg);
    opacity: 1;
  }
}

@keyframes warningPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.inventory-entry-page {
  --ie-surface: rgba(255, 255, 255, 0.88);
  --ie-border: rgba(15, 23, 42, 0.08);
  --ie-accent: #0ea5e9;
  --ie-muted: #64748b;
  position: relative;
  padding: 12px 14px 16px;
  background:
    linear-gradient(165deg, #f8fafc 0%, #f1f5f9 45%, #e2e8f0 100%);
  min-height: 100vh;
  box-sizing: border-box;
}

.page-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 70% 50% at 12% -10%, rgba(14, 165, 233, 0.14), transparent 55%),
    radial-gradient(ellipse 50% 40% at 92% 20%, rgba(99, 102, 241, 0.1), transparent 50%);
}

.page-toolbar,
.form-panel,
.history-panel {
  position: relative;
  z-index: 1;
}

.page-toolbar {
  margin-bottom: 12px;
}

.toolbar-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 14px;
  background: var(--ie-surface);
  border: 1px solid var(--ie-border);
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(12px);
}

.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.brand-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: linear-gradient(145deg, #0ea5e9, #0284c7);
  color: #fff;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.35);
}

.brand-icon :deep(.el-icon) {
  font-size: 20px;
}

.brand-text {
  min-width: 0;
}

.toolbar-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.25;
}

.toolbar-sub {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--ie-muted);
  line-height: 1.3;
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.form-panel {
  padding: 14px 16px;
  background: var(--ie-surface);
  border: 1px solid var(--ie-border);
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 10px 28px rgba(15, 23, 42, 0.07);
  backdrop-filter: blur(12px);
}

.form-panel::before {
  content: '';
  display: block;
  height: 3px;
  margin: -14px -16px 14px;
  border-radius: 12px 12px 0 0;
  background: linear-gradient(90deg, #0ea5e9, #38bdf8, #22d3ee);
}

.history-panel {
  background: var(--ie-surface);
  border: 1px solid var(--ie-border);
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 10px 28px rgba(15, 23, 42, 0.07);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.history-card {
  --el-card-border-color: transparent;
  border: none;
  border-radius: 0;
  background: transparent;
}

.history-card :deep(.el-card__header) {
  padding: 10px 12px;
  border-bottom: 1px solid var(--ie-border);
  background: linear-gradient(180deg, rgba(14, 165, 233, 0.04), transparent);
}

.history-card :deep(.el-card__body) {
  padding: 10px 12px 12px;
}

.history-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.history-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.history-title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.history-badge {
  flex-shrink: 0;
}

.history-toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.process-filter-select {
  width: min(200px, 42vw);
  min-width: 140px;
}

.month-picker-compact {
  width: 120px;
}

.month-picker-compact :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.history-pagination-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
  gap: 10px 16px;
}

.history-qty-summary {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 6px 10px;
  font-size: 13px;
  color: #334155;
}

.history-qty-summary-label {
  font-weight: 600;
  color: #0f172a;
}

.history-qty-summary-value {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  font-size: 1.05rem;
}

.history-qty-summary-meta {
  font-size: 12px;
  color: #64748b;
}

.history-table {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--ie-border);
  --el-table-border-color: var(--ie-border);
  --el-table-header-bg-color: #f8fafc;
  table-layout: fixed;
  width: 100%;
}

.history-table :deep(.el-table__header th) {
  background: #f1f5f9 !important;
  color: #334155;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 10px !important;
  letter-spacing: 0.02em;
  cursor: pointer;
  box-sizing: border-box;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-table :deep(.el-table__header th:hover) {
  background: #e2e8f0 !important;
  color: #0f172a;
}

.history-table :deep(.el-table__sort-caret) {
  border-color: #94a3b8;
}

.history-table :deep(.el-table__sort-caret.ascending) {
  border-bottom-color: #0ea5e9;
}

.history-table :deep(.el-table__sort-caret.descending) {
  border-top-color: #0ea5e9;
}

.history-table :deep(.el-table__column-sort) {
  color: #0ea5e9;
}

.history-table :deep(.el-table__row) {
  background: #fff;
}

.history-table :deep(.el-table__row:hover > td) {
  background: rgba(14, 165, 233, 0.06) !important;
}

/* 确保表格列宽度对齐 */
.history-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.history-table :deep(.el-table__header-wrapper) {
  overflow-x: hidden;
}

.history-table :deep(.el-table__body) {
  width: 100%;
}

.history-table :deep(.el-table__header) {
  width: 100%;
}

.history-table :deep(.el-table td) {
  padding: 6px 10px !important;
  font-size: 13px;
  font-weight: 500;
  color: #334155;
  box-sizing: border-box;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-table :deep(.el-tag) {
  border-radius: 6px;
  font-weight: 600;
  padding: 0 8px;
  height: 22px;
  line-height: 22px;
}

/* 数量样式 */
.out-of-stock {
  color: #dc2626;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(254, 226, 226, 0.85);
}

.low-stock {
  color: #d97706;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(254, 243, 199, 0.85);
}

.normal-stock {
  color: #059669;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(209, 250, 229, 0.85);
}

.empty-state {
  padding: 24px 0 12px;
  text-align: center;
}

.empty-state :deep(.el-empty) {
  padding: 12px;
}

.empty-state :deep(.el-empty__description) {
  color: var(--ie-muted);
  font-size: 13px;
  margin-top: 8px;
}

/* 成功对话框样式 */
.success-content {
  text-align: center;
  padding: 20px 18px 16px;
  background: #fff;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.success-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #10b981, #059669, #047857, #059669, #10b981);
}

.success-animation {
  position: relative;
  margin-bottom: 14px;
}

.success-circle {
  width: 72px;
  height: 72px;
  margin: 0 auto;
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 12px 40px rgba(16, 185, 129, 0.4),
    0 6px 20px rgba(5, 150, 105, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.3);
  animation: successCircle 0.8s ease-out;
  position: relative;
  overflow: hidden;
}

.success-circle::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: glow 2s ease-in-out infinite;
}

.success-checkmark {
  position: relative;
  width: 50px;
  height: 50px;
}

.checkmark-stem {
  position: absolute;
  width: 3px;
  height: 16px;
  background-color: white;
  left: 13px;
  top: 11px;
  transform: rotate(45deg);
  border-radius: 2px;
  animation: successCheckmark 0.6s ease-out 0.3s both;
}

.checkmark-kick {
  position: absolute;
  width: 3px;
  height: 9px;
  background-color: white;
  left: 8px;
  top: 16px;
  transform: rotate(-45deg);
  border-radius: 2px;
  animation: successCheckmark 0.6s ease-out 0.5s both;
}

.success-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #047857;
  margin-bottom: 6px;
  animation: slideUp 0.6s ease-out 0.5s both;
}

.success-message {
  font-size: 13px;
  color: #64748b;
  margin: 8px 0 0;
  font-weight: 500;
  animation: slideUp 0.6s ease-out 0.7s both;
}

.success-details {
  background: #f0fdf4;
  border: 1px solid rgba(16, 185, 129, 0.22);
  border-radius: 10px;
  padding: 12px 14px;
  margin-top: 16px;
  text-align: left;
  backdrop-filter: blur(10px);
  box-shadow:
    0 8px 32px rgba(16, 185, 129, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  animation: slideUp 0.6s ease-out 0.9s both;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0;
  padding: 8px 0;
  border-bottom: 1px solid rgba(16, 185, 129, 0.12);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}

.detail-value {
  color: #047857;
  font-weight: 600;
  font-size: 13px;
}

.quantity-highlight {
  background: linear-gradient(135deg, #10b981, #059669);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 18px;
  font-weight: 800;
}

.dialog-footer {
  text-align: center;
  padding-top: 12px;
  animation: slideUp 0.6s ease-out 1.1s both;
}

.continue-btn {
  border-radius: 8px !important;
  padding: 8px 16px !important;
  font-weight: 600 !important;
  margin: 0 6px !important;
}

.confirm-btn {
  border-radius: 8px !important;
  padding: 8px 18px !important;
  font-weight: 600 !important;
  margin: 0 6px !important;
}

/* 删除对话框样式 */
.delete-content {
  text-align: center;
  padding: 20px 18px 16px;
  background: #fff;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.delete-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #ef4444, #dc2626, #b91c1c, #dc2626, #ef4444);
}

.delete-animation {
  position: relative;
  margin-bottom: 14px;
}

.warning-circle {
  width: 72px;
  height: 72px;
  margin: 0 auto;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 12px 40px rgba(239, 68, 68, 0.4),
    0 6px 20px rgba(220, 38, 38, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.3);
  animation: warningPulse 2s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.warning-circle::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: glow 2s ease-in-out infinite;
}

.warning-icon {
  position: relative;
  width: 50px;
  height: 50px;
}

.warning-line {
  position: absolute;
  width: 3px;
  height: 22px;
  background-color: white;
  left: 17px;
  top: 8px;
  border-radius: 2px;
  animation: warningPulse 1.5s ease-in-out infinite;
}

.warning-dot {
  position: absolute;
  width: 5px;
  height: 5px;
  background-color: white;
  left: 16px;
  top: 33px;
  border-radius: 50%;
  animation: warningPulse 1.5s ease-in-out infinite 0.3s;
}

.delete-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #b91c1c;
  margin-bottom: 6px;
  animation: slideUp 0.6s ease-out 0.5s both;
}

.delete-message {
  font-size: 13px;
  color: #64748b;
  margin: 8px 0 0;
  font-weight: 500;
  animation: slideUp 0.6s ease-out 0.7s both;
}

.delete-details {
  background: #fef2f2;
  border: 1px solid rgba(239, 68, 68, 0.22);
  border-radius: 10px;
  padding: 12px 14px;
  margin-top: 16px;
  text-align: left;
  backdrop-filter: blur(10px);
  box-shadow:
    0 8px 32px rgba(239, 68, 68, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  animation: slideUp 0.6s ease-out 0.9s both;
}

.delete-details .detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0;
  padding: 8px 0;
  border-bottom: 1px solid rgba(239, 68, 68, 0.12);
}

.delete-details .detail-item:last-child {
  border-bottom: none;
}

.delete-details .detail-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}

.delete-details .detail-value {
  color: #b91c1c;
  font-weight: 600;
  font-size: 13px;
}

.delete-warning {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #b91c1c;
  font-size: 12px;
  margin-top: 12px;
  font-weight: 600;
  background: rgba(254, 226, 226, 0.6);
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(239, 68, 68, 0.25);
  animation: slideUp 0.6s ease-out 1.1s both;
}

.cancel-btn {
  border-radius: 8px !important;
  padding: 8px 16px !important;
  font-weight: 600 !important;
  margin: 0 6px !important;
}

.delete-btn {
  border-radius: 8px !important;
  padding: 8px 18px !important;
  font-weight: 600 !important;
  margin: 0 6px !important;
}

@media (max-width: 768px) {
  .inventory-entry-page {
    padding: 10px 10px 14px;
  }

  .toolbar-main {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-actions {
    justify-content: flex-start;
  }

  .toolbar-title {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .history-title {
    font-size: 0.875rem;
  }

  .history-table :deep(.el-table td) {
    font-size: 12px;
    padding: 5px 6px !important;
  }
}

.success-dialog :deep(.el-dialog__header),
.delete-dialog :deep(.el-dialog__header) {
  padding: 12px 16px 8px;
  margin: 0;
}

.success-dialog :deep(.el-dialog__body),
.delete-dialog :deep(.el-dialog__body) {
  padding: 0 16px 12px;
}

.success-dialog :deep(.el-dialog__footer),
.delete-dialog :deep(.el-dialog__footer) {
  padding: 0 16px 14px;
}
</style>
