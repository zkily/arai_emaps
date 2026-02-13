<template>
  <el-dialog
    v-model="visible"
    width="94%"
    :close-on-click-modal="false"
    class="print-history-dialog"
    @close="handleClose"
  >
    <template #header>
      <div class="dialog-header glass-header">
        <div class="header-left">
          <el-icon class="header-icon"><Document /></el-icon>
          <span class="header-title">印刷履歴管理</span>
        </div>
        <div class="header-actions">
          <el-button class="btn-glass btn-primary" @click="fetchData" :icon="Refresh">更新</el-button>
          <el-button class="btn-glass btn-default" @click="handleClose">閉じる</el-button>
        </div>
      </div>
    </template>

    <div class="print-history-content">
      <!-- フィルター：紧凑一行 -->
      <div class="filter-section glass-card">
        <el-form :inline="true" :model="queryParams" size="small" class="filter-form">
          <el-form-item label="レポート種別">
            <el-select
              v-model="queryParams.report_type"
              placeholder="種別"
              clearable
              class="filter-input"
            >
              <el-option label="出荷レポート" value="shipping_report" />
              <el-option label="出荷カレンダー" value="shipping_calendar" />
              <el-option label="その他" value="other_report" />
            </el-select>
          </el-form-item>
          <el-form-item label="ユーザー">
            <el-input v-model="queryParams.user_name" placeholder="ユーザー名" clearable class="filter-input" />
          </el-form-item>
          <el-form-item label="印刷日">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              start-placeholder="開始"
              end-placeholder="終了"
              value-format="YYYY-MM-DD"
              class="filter-date"
              @change="handleDateChange"
            />
          </el-form-item>
          <el-form-item>
            <el-button class="btn-glass btn-primary" :icon="Search" @click="fetchData" :loading="loading">検索</el-button>
            <el-button class="btn-glass btn-default" :icon="Refresh" @click="resetFilters">リセット</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 統計：玻璃卡片、颜色区分 -->
      <div v-if="stats" class="stats-section">
        <div class="stat-item glass-card stat-total">
          <div class="stat-value">{{ stats.total || 0 }}</div>
          <div class="stat-label">総印刷数</div>
        </div>
        <div class="stat-item glass-card stat-success">
          <div class="stat-value">{{ getStatusCount('成功') }}</div>
          <div class="stat-label">成功</div>
        </div>
        <div class="stat-item glass-card stat-danger">
          <div class="stat-value">{{ getStatusCount('失败') }}</div>
          <div class="stat-label">失敗</div>
        </div>
        <div class="stat-item glass-card stat-warning">
          <div class="stat-value">{{ getStatusCount('取消') }}</div>
          <div class="stat-label">キャンセル</div>
        </div>
      </div>

      <!-- テーブル -->
      <div class="table-section glass-card">
        <div class="table-header">
          <span class="table-title"><el-icon><List /></el-icon> 一覧 ({{ total }}件)</span>
          <el-button
            v-if="selectedRows.length > 0"
            class="btn-glass btn-danger"
            size="small"
            :icon="Delete"
            @click="handleBatchDelete"
          >
            一括削除 ({{ selectedRows.length }})
          </el-button>
        </div>
        <div v-loading="loading" class="table-container">
          <el-table
              :data="historyData"
              border
              stripe
              style="width: 100%"
              size="small"
              @selection-change="handleSelectionChange"
              empty-text="データがありません"
            >
              <el-table-column type="selection" width="55" />

              <el-table-column label="ID" prop="id" width="80" align="center" />

              <el-table-column label="レポート種別" prop="report_type" width="140" align="center">
                <template #default="{ row }">
                  <el-tag :type="getReportTypeTagType(row.report_type)" size="small">
                    {{ getReportTypeName(row.report_type) }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column
                label="レポートタイトル"
                prop="report_title"
                min-width="300"
                show-overflow-tooltip
              />

              <el-table-column label="ユーザー" prop="user_name" width="120" align="center" />

              <el-table-column label="印刷時間" prop="print_date" width="160" align="center">
                <template #default="{ row }">
                  <div class="time-cell">
                    <el-icon>
                      <Clock />
                    </el-icon>
                    {{ formatDateTime(row.print_date) }}
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="レコード数" prop="record_count" width="100" align="center">
                <template #default="{ row }">
                  <el-tag type="info" size="small">{{ row.record_count || 0 }}</el-tag>
                </template>
              </el-table-column>

              <el-table-column label="ステータス" prop="status" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="getStatusTagType(row.status)" size="small">
                    <el-icon>
                      <Check v-if="row.status === '成功'" />
                      <Close v-else-if="row.status === '失败'" />
                      <Warning v-else />
                    </el-icon>
                    {{ getStatusName(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column label="フィルター条件" prop="filters" min-width="200">
                <template #default="{ row }">
                  <div class="filters-cell">
                    <el-popover
                      placement="top-start"
                      :width="400"
                      trigger="hover"
                      popper-class="filters-popover"
                    >
                      <template #reference>
                        <el-text type="info" truncated class="filters-text">
                          {{ formatFiltersShort(row.filters) }}
                        </el-text>
                      </template>
                      <div class="filters-detail">
                        <pre>{{ formatFilters(row.filters) }}</pre>
                      </div>
                    </el-popover>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="120" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="handleDelete(row)"
                    title="削除"
                    circle
                  />
                </template>
              </el-table-column>
            </el-table>

            <div class="pagination-section">
              <el-pagination
                v-model:current-page="queryParams.page"
                v-model:page-size="queryParams.limit"
                :page-sizes="[10, 20, 50, 100]"
                :total="total"
                layout="total, sizes, prev, pager, next, jumper"
                small
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
              />
            </div>
          </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Search,
  Refresh,
  Delete,
  Download,
  DataAnalysis,
  Clock,
  Check,
  Close,
  Warning,
  List,
} from '@element-plus/icons-vue'
import request from '@/utils/request'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
})

// Emits
const emit = defineEmits(['update:modelValue'])

// レスポンシブデータ
const visible = ref(false)
const loading = ref(false)
const historyData = ref([])
const total = ref(0)
const selectedRows = ref([])
const stats = ref(null)
const dateRange = ref(null)
const debugInfo = ref('')

// クエリパラメータ
const queryParams = reactive({
  page: 1,
  limit: 20,
  report_type: '',
  user_name: '',
  date_from: '',
  date_to: '',
})

// 計算プロパティ
// 後端 API は { total, success_count, fail_count, cancel_count } を返す
const getStatusCount = (status) => {
  const s = stats.value
  if (!s) return 0
  if (status === '成功') return s.success_count ?? 0
  if (status === '失败' || status === '失敗') return s.fail_count ?? 0
  if (status === '取消') return s.cancel_count ?? 0
  return s.byStatus?.find((item) => item.status === status)?.count ?? 0
}

// モデル値の変更を監視
watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
    if (val) {
      fetchData()
      fetchStats()
    }
  },
  { immediate: true },
)

// 対話框可見性を監視
watch(visible, (val) => {
  emit('update:modelValue', val)
})

// メソッド
const fetchData = async () => {
  loading.value = true
  debugInfo.value = ''

  try {
    console.log('🔍 印刷履歴データを取得中...', queryParams)

    // APIリクエスト（后端使用 offset/limit）
    const params = {
      report_type: queryParams.report_type,
      user_name: queryParams.user_name,
      date_from: queryParams.date_from,
      date_to: queryParams.date_to,
      limit: queryParams.limit,
      offset: (queryParams.page - 1) * queryParams.limit,
    }
    const response = await request.get('/api/shipping/print/history', { params })

    console.log('📋 API応答 (原始):', response)
    debugInfo.value = `API応答:\n${JSON.stringify(response, null, 2)}`

    // レスポンスデータの処理
    let responseData = response

    // response.data が存在する場合
    if (response && response.data) {
      responseData = response.data
    }

    console.log('📊 処理後のデータ:', responseData)

    // 成功チェック
    if (responseData.success === false) {
      throw new Error(responseData.message || 'データ取得に失敗しました')
    }

    // データ抽出
    if (responseData.data && responseData.data.list) {
      // 標準形式: { success: true, data: { list: [], total: 0 } }
      historyData.value = responseData.data.list || []
      total.value = responseData.data.total || 0
      console.log('✅ 標準形式でデータを取得:', historyData.value.length, '件')
    } else if (responseData.data && Array.isArray(responseData.data)) {
      // 配列形式: { success: true, data: [] }
      historyData.value = responseData.data
      total.value = responseData.data.length
      console.log('✅ 配列形式でデータを取得:', historyData.value.length, '件')
    } else if (Array.isArray(responseData)) {
      // 直接配列: []
      historyData.value = responseData
      total.value = responseData.length
      console.log('✅ 直接配列でデータを取得:', historyData.value.length, '件')
    } else if (responseData.list) {
      // list プロパティ: { list: [], total: 0 }
      historyData.value = responseData.list || []
      total.value = responseData.total || 0
      console.log('✅ listプロパティでデータを取得:', historyData.value.length, '件')
    } else {
      // データなし
      historyData.value = []
      total.value = 0
      console.log('⚠️ データが見つかりません')
    }

    console.log('📈 最結果:', {
      count: historyData.value.length,
      total: total.value,
      sample: historyData.value.slice(0, 2),
    })

    // デバッグ情報更新
    debugInfo.value = `取得成功:\n件数: ${historyData.value.length}\n総数: ${total.value}\n\nサンプルデータ:\n${JSON.stringify(historyData.value.slice(0, 2), null, 2)}`
  } catch (error) {
    console.error('❌ 印刷履歴の取得に失敗:', error)
    ElMessage.error('印刷履歴の取得に失敗しました: ' + error.message)
    historyData.value = []
    total.value = 0
    debugInfo.value = `エラー:\n${error.message}\n\nスタック:\n${error.stack}`
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const response = await request.get('/api/shipping/print/history/stats', {
      params: {
        date_from: queryParams.date_from,
        date_to: queryParams.date_to,
      },
    })

    let data = response
    if (response.data) {
      data = response.data
    }

    if (data.success !== false) {
      stats.value = data.data || data
    }

    console.log('📈 統計データ:', stats.value)
  } catch (error) {
    console.error('❌ 統計情報の取得に失敗:', error)
  }
}

const testConnection = async () => {
  try {
    ElMessage.info('接続テスト中...')
    const response = await request.get('/api/shipping/print/history?limit=1')
    console.log('接続テスト結果:', response)
    ElMessage.success('接続テストに成功しました')
    debugInfo.value = `接続テスト成功:\n${JSON.stringify(response, null, 2)}`
  } catch (error) {
    console.error('接続テストに失敗:', error)
    ElMessage.error('接続テストに失敗しました: ' + error.message)
    debugInfo.value = `接続テストエラー:\n${error.message}`
  }
}

const handleDateChange = () => {
  if (dateRange.value) {
    queryParams.date_from = dateRange.value[0]
    queryParams.date_to = dateRange.value[1]
  } else {
    queryParams.date_from = ''
    queryParams.date_to = ''
  }
}

const resetFilters = () => {
  queryParams.report_type = ''
  queryParams.user_name = ''
  queryParams.date_from = ''
  queryParams.date_to = ''
  queryParams.page = 1
  dateRange.value = null
  fetchData()
  fetchStats()
}

const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('この印刷履歴を削除しますか？', '削除確認', {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })

    await request.delete(`/api/shipping/print/history/${row.id}`)
    ElMessage.success('削除しました')
    fetchData()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('❌ 削除に失敗:', error)
      ElMessage.error('削除に失敗しました: ' + error.message)
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('削除するレコードを選択してください')
    return
  }

  try {
    await ElMessageBox.confirm(
      `選択中の ${selectedRows.value.length} 件の印刷履歴を削除しますか？`,
      '一括削除確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    const ids = selectedRows.value.map((row) => row.id)
    await request.delete(`/api/shipping/print/history/batch/${ids.join(',')}`)
    ElMessage.success(`${selectedRows.value.length} 件を削除しました`)
    selectedRows.value = []
    fetchData()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('❌ 一括削除に失敗:', error)
      ElMessage.error('一括削除に失敗しました: ' + error.message)
    }
  }
}

const handleExport = () => {
  ElMessage.info('データ出力機能は開発中です...')
}

const handleSizeChange = (size) => {
  queryParams.limit = size
  queryParams.page = 1
  fetchData()
}

const handleCurrentChange = (page) => {
  queryParams.page = page
  fetchData()
}

const handleClose = () => {
  visible.value = false
}

// フォーマット関数
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
}

const getReportTypeName = (type) => {
  const typeMap = {
    shipping_report: '出荷レポート',
    shipping_calendar: '出荷カレンダー',
    other_report: 'その他レポート',
  }
  return typeMap[type] || type
}

const getReportTypeTagType = (type) => {
  const typeMap = {
    shipping_report: 'success',
    shipping_calendar: 'primary',
    other_report: 'info',
  }
  return typeMap[type] || 'default'
}

const getStatusName = (status) => {
  const statusMap = {
    成功: '成功',
    失败: '失敗',
    取消: 'キャンセル',
  }
  return statusMap[status] || status
}

const getStatusTagType = (status) => {
  const statusMap = {
    成功: 'success',
    失败: 'danger',
    取消: 'warning',
  }
  return statusMap[status] || 'default'
}

const formatFilters = (filters) => {
  if (!filters) return 'フィルターなし'

  try {
    const parsed = typeof filters === 'string' ? JSON.parse(filters) : filters
    return JSON.stringify(parsed, null, 2)
  } catch (error) {
    return filters || 'フォーマットエラー'
  }
}

const formatFiltersShort = (filters) => {
  if (!filters) return 'フィルターなし'

  try {
    const parsed = typeof filters === 'string' ? JSON.parse(filters) : filters
    const parts = []

    if (parsed.dateRange && parsed.dateRange.length === 2) {
      parts.push(`${parsed.dateRange[0]}~${parsed.dateRange[1]}`)
    }

    if (parsed.destinationCds && parsed.destinationCds.length > 0) {
      parts.push(`${parsed.destinationCds.length}件の納入先`)
    }

    if (parsed.selectedGroup !== undefined && parsed.selectedGroup >= 0) {
      const groupNames = ['オワリ便', '鈴鹿便', '社内便']
      parts.push(groupNames[parsed.selectedGroup] || `グループ${parsed.selectedGroup + 1}`)
    }

    return parts.length > 0 ? parts.join(', ') : 'フィルターなし'
  } catch (error) {
    return 'フォーマットエラー'
  }
}

// コンポーネントマウント
onMounted(() => {
  console.log('🚀 PrintHistoryDialog 初期化')
})
</script>

<style scoped>
.print-history-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(160deg, #f1f5f9 0%, #e2e8f0 100%);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
}

.print-history-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border: none;
}

.print-history-dialog :deep(.el-dialog__body) {
  padding: 10px 14px 14px;
  max-height: 85vh;
  overflow-y: auto;
}

.glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 10px 16px;
  background: rgba(30, 58, 138, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.95);
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.02em;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-glass {
  border-radius: 8px;
  font-weight: 600;
  font-size: 12px;
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(8px);
  transition: all 0.2s ease;
}

.btn-glass.btn-primary {
  background: rgba(59, 130, 246, 0.85);
  color: #fff;
}

.btn-glass.btn-primary:hover {
  background: rgba(37, 99, 235, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.btn-glass.btn-default {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.btn-glass.btn-default:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.btn-glass.btn-danger {
  background: rgba(239, 68, 68, 0.85);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.2);
}

.btn-glass.btn-danger:hover {
  background: rgba(220, 38, 38, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35);
}

.print-history-content {
  padding: 0;
  min-height: 60vh;
}

.filter-section {
  margin-bottom: 10px;
}

.filter-section.glass-card {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.filter-form {
  margin-bottom: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 16px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.filter-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 500;
  color: #475569;
}

.filter-input {
  width: 140px;
}

.filter-date {
  width: 220px;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 10px;
}

.stat-item.glass-card {
  padding: 10px 12px;
  text-align: center;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.2s ease;
}

.stat-item.glass-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.stat-total {
  background: rgba(59, 130, 246, 0.25);
  border-color: rgba(37, 99, 235, 0.35);
}

.stat-total .stat-value { color: #1d4ed8; }
.stat-total .stat-label { color: #1e40af; }

.stat-success {
  background: rgba(16, 185, 129, 0.2);
  border-color: rgba(16, 185, 129, 0.35);
}

.stat-success .stat-value { color: #047857; }
.stat-success .stat-label { color: #065f46; }

.stat-danger {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.35);
}

.stat-danger .stat-value { color: #b91c1c; }
.stat-danger .stat-label { color: #991b1b; }

.stat-warning {
  background: rgba(245, 158, 11, 0.2);
  border-color: rgba(245, 158, 11, 0.35);
}

.stat-warning .stat-value { color: #b45309; }
.stat-warning .stat-label { color: #92400e; }

.stat-value {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 11px;
  font-weight: 500;
  opacity: 0.9;
}

.table-section.glass-card {
  padding: 0;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(248, 250, 252, 0.8);
  border-bottom: 1px solid #e2e8f0;
}

.table-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 6px;
}

.table-container {
  min-height: 260px;
}

.table-section :deep(.el-table) {
  --el-table-border-color: #e2e8f0;
  --el-table-header-bg-color: #f8fafc;
}

.table-section :deep(.el-table__header th) {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  padding: 8px 0;
}

.table-section :deep(.el-table__body td) {
  font-size: 12px;
  padding: 8px 0;
}

.table-section :deep(.el-table__body tr:hover) {
  background-color: #f8fafc !important;
}

.time-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.filters-cell {
  max-width: 200px;
}

.filters-text {
  cursor: pointer;
}

.filters-detail {
  max-height: 200px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.4;
}

.filters-popover {
  max-width: 400px;
}

.pagination-section {
  padding: 8px 12px;
  display: flex;
  justify-content: center;
  background: rgba(248, 250, 252, 0.9);
  border-top: 1px solid #e2e8f0;
}

.pagination-section :deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  font-size: 12px;
}

.pagination-section :deep(.el-pager li) {
  border-radius: 6px;
  min-width: 26px;
  height: 26px;
  line-height: 26px;
}

.table-section :deep(.el-button--danger) {
  border-radius: 6px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #b91c1c;
}

.table-section :deep(.el-button--danger:hover) {
  background: rgba(239, 68, 68, 0.3);
  color: #991b1b;
}

@media (max-width: 1024px) {
  .stats-section { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .print-history-dialog :deep(.el-dialog) { width: 98% !important; margin: 8px auto; }
  .print-history-content { padding: 0; }
  .glass-header { flex-direction: column; gap: 8px; padding: 8px 12px; }
  .header-actions { width: 100%; justify-content: flex-end; }
  .filter-section.glass-card { padding: 8px 10px; }
  .filter-form { flex-direction: column; align-items: stretch; }
  .filter-form :deep(.el-form-item) { display: flex; flex-direction: column; align-items: stretch; }
  .filter-input, .filter-date { width: 100% !important; }
  .stats-section { grid-template-columns: 1fr; gap: 6px; }
  .stat-item.glass-card { padding: 8px 10px; }
  .stat-value { font-size: 16px; }
  .table-header { flex-direction: column; align-items: flex-start; gap: 6px; }
  .table-section :deep(.el-table) { font-size: 11px; }
}

@media (max-width: 480px) {
  .print-history-dialog :deep(.el-dialog) { width: 100% !important; margin: 4px; }
  .print-history-dialog :deep(.el-dialog__body) { padding: 6px 8px 10px; }
  .stat-value { font-size: 15px; }
  .stat-label { font-size: 10px; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.filter-section.glass-card,
.stats-section .stat-item,
.table-section.glass-card {
  animation: fadeIn 0.35s ease-out;
}

.stats-section .stat-item:nth-child(1) { animation-delay: 0.05s; }
.stats-section .stat-item:nth-child(2) { animation-delay: 0.1s; }
.stats-section .stat-item:nth-child(3) { animation-delay: 0.15s; }
.stats-section .stat-item:nth-child(4) { animation-delay: 0.2s; }
</style>
