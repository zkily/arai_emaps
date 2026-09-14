<template>
  <div class="db-file-mgmt">
    <header class="page-header">
      <div class="title-block">
        <el-icon class="title-icon" :size="28"><FolderOpened /></el-icon>
        <div>
          <h1>データベースファイル管理</h1>
          <p class="subtitle">
            肥大化したテーブルの過去データを退避し、業務で使う直近データだけをホットテーブルに残します
          </p>
        </div>
      </div>
      <el-button type="primary" :icon="Refresh" :loading="overviewLoading" @click="refreshAll">
        再読込
      </el-button>
    </header>

    <el-alert
      class="info-alert"
      type="info"
      show-icon
      :closable="false"
      title="運用方針"
      description="shipping_log は直近30日を保持します。それより古い行は shipping_log_archive へ移動します。picking_log_matched（完了フラグ）は再計算しないため、過去の完了状態は維持されます。"
    />

    <div class="overview-grid">
      <el-card shadow="never" class="stat-card">
        <div class="stat-label">shipping_log（ホット）</div>
        <div class="stat-value">{{ formatNumber(overview.shippingLog) }}</div>
      </el-card>
      <el-card shadow="never" class="stat-card archive">
        <div class="stat-label">shipping_log_archive（退避）</div>
        <div class="stat-value">{{ formatNumber(overview.shippingLogArchive) }}</div>
      </el-card>
      <el-card shadow="never" class="stat-card">
        <div class="stat-label">保持日数</div>
        <div class="stat-value">{{ retentionDays }} 日</div>
      </el-card>
    </div>

    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <div>
            <div class="section-title">shipping_log アーカイブ</div>
            <div class="section-desc">30日以前のログを archive 表へ移動（削除ではなく退避）</div>
          </div>
          <el-button
            type="warning"
            :icon="Box"
            :loading="archiveLoading"
            :disabled="archiveLoading"
            @click="runArchive"
          >
            アーカイブ実行
          </el-button>
        </div>
      </template>

      <div v-if="archiveLoading || archiveProgress > 0" class="progress-panel">
        <div class="progress-meta">
          <span>{{ archiveMessage || '処理中...' }}</span>
          <span>
            {{ formatNumber(archiveDone) }}
            <template v-if="archiveTotal > 0"> / {{ formatNumber(archiveTotal) }}</template>
          </span>
        </div>
        <el-progress
          :percentage="Math.min(archiveProgress, 100)"
          :stroke-width="14"
          :status="archiveProgressStatus"
        />
      </div>

      <div class="toolbar">
        <el-input
          v-model="searchQuery"
          placeholder="picking_no / 製品名 / 製品CD で検索"
          clearable
          class="search-input"
          :prefix-icon="Search"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-button :icon="Search" @click="handleSearch">検索</el-button>
        <el-button :icon="Refresh" :loading="logsLoading" @click="loadLogs">更新</el-button>
      </div>

      <el-table :data="logs" v-loading="logsLoading" height="420" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="picking_no" label="ピッキングNo" min-width="160" />
        <el-table-column prop="product_code" label="製品CD" width="120" />
        <el-table-column prop="product_name" label="製品名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="date" label="日付" width="120" />
        <el-table-column prop="created_at" label="作成日時" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalRecords"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <div>
            <div class="section-title">重複データ整理</div>
            <div class="section-desc">同一 picking_no + product_code + date の重複を整理</div>
          </div>
          <div class="header-actions">
            <el-button :loading="dupLoading" @click="loadDuplicateStats">重複統計</el-button>
            <el-button type="danger" plain :loading="dedupeLoading" @click="runDeduplicate">
              重複削除
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="duplicateStats" class="dup-summary">
        余剰重複: {{ formatNumber(duplicateStats.total_duplicates) }} 件 /
        対象 picking_no: {{ formatNumber(duplicateStats.unique_picking_nos) }}
      </div>
      <el-empty v-else description="「重複統計」で確認できます" :image-size="64" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Box, FolderOpened, Refresh, Search } from '@element-plus/icons-vue'
import {
  getArchiveShippingLogsTask,
  getDuplicateStats,
  getShippingLogs,
  getSyncDebugInfo,
  performDeduplicate,
  startArchiveShippingLogs,
  type DuplicateStats,
  type ShippingLogRecord,
} from '@/api/shipping/databaseFiles'
import { useSalesOperationPermission } from '@/composables/useSalesOperationPermission'
import { guardSalesOperation } from '@/utils/salesOperationGuard'

const { canEdit, canExport } = useSalesOperationPermission()

const retentionDays = 30
const overviewLoading = ref(false)
const overview = ref({
  shippingLog: 0,
  shippingLogArchive: 0,
})

const logs = ref<ShippingLogRecord[]>([])
const logsLoading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalRecords = ref(0)

const archiveLoading = ref(false)
const archiveProgress = ref(0)
const archiveMessage = ref('')
const archiveDone = ref(0)
const archiveTotal = ref(0)
const archiveProgressStatus = ref<'' | 'success' | 'exception' | 'warning'>('')

const duplicateStats = ref<DuplicateStats | null>(null)
const dupLoading = ref(false)
const dedupeLoading = ref(false)

function formatNumber(num: number) {
  return Number(num || 0).toLocaleString('ja-JP')
}

function formatDateTime(dateTime: string | null | undefined) {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'string') return error
  const e = error as { response?: { data?: { detail?: string; message?: string } }; message?: string }
  const detail = e?.response?.data?.detail || e?.response?.data?.message || e?.message
  return typeof detail === 'string' ? detail : fallback
}

async function loadOverview() {
  overviewLoading.value = true
  try {
    const response = (await getSyncDebugInfo()) as Record<string, any>
    const data = (response.data ?? response) as Record<string, { count?: number }>
    overview.value = {
      shippingLog: Number(data.shipping_log?.count ?? 0),
      shippingLogArchive: Number(data.shipping_log_archive?.count ?? 0),
    }
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '件数の取得に失敗しました'))
  } finally {
    overviewLoading.value = false
  }
}

async function loadLogs() {
  logsLoading.value = true
  try {
    const params: { page: number; pageSize: number; search?: string } = {
      page: currentPage.value,
      pageSize: pageSize.value,
    }
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
    const response = (await getShippingLogs(params)) as {
      items?: ShippingLogRecord[]
      total?: number
    }
    logs.value = response.items || []
    totalRecords.value = Number(response.total || 0)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, 'shipping_log の取得に失敗しました'))
  } finally {
    logsLoading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadLogs()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadLogs()
}

function handleCurrentChange(page: number) {
  currentPage.value = page
  loadLogs()
}

async function refreshAll() {
  await Promise.all([loadOverview(), loadLogs()])
}

async function runArchive() {
  if (!guardSalesOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      '30日以前の shipping_log を shipping_log_archive へ退避します。直近データとピッキング完了フラグは保持されます。',
      'アーカイブ確認',
      {
        confirmButtonText: 'アーカイブ実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )
  } catch {
    return
  }

  archiveLoading.value = true
  archiveProgress.value = 1
  archiveProgressStatus.value = ''
  archiveMessage.value = 'アーカイブを開始しています...'
  archiveDone.value = 0
  archiveTotal.value = 0

  try {
    const startResult = (await startArchiveShippingLogs()) as {
      data?: { task_id?: string }
      task_id?: string
      message?: string
    }
    const taskId = String(startResult.data?.task_id || startResult.task_id || '')
    if (!taskId) {
      throw new Error(startResult.message || 'task_id が取得できませんでした')
    }

    const maxPoll = 1200
    for (let i = 0; i < maxPoll; i += 1) {
      await new Promise((r) => setTimeout(r, 1000))
      const statusResult = (await getArchiveShippingLogsTask(taskId)) as {
        data?: Record<string, any>
      }
      const task = (statusResult.data ?? statusResult) as Record<string, any>
      archiveProgress.value = Math.min(100, Number(task.progress_percent || 0))
      archiveMessage.value = String(task.message || '')
      archiveDone.value = Number(task.archived || 0)
      archiveTotal.value = Number(task.total_candidates || 0)

      if (task.status === 'completed') {
        archiveProgress.value = 100
        archiveProgressStatus.value = 'success'
        ElMessage.success(String(task.message || 'アーカイブが完了しました'))
        break
      }
      if (task.status === 'failed') {
        archiveProgressStatus.value = 'exception'
        throw new Error(String(task.error || task.message || 'アーカイブに失敗しました'))
      }
      if (i === maxPoll - 1) {
        archiveProgressStatus.value = 'warning'
        ElMessage.warning('処理は継続中です。しばらくしてから件数を再読込してください。')
      }
    }

    await refreshAll()
  } catch (error: unknown) {
    archiveProgressStatus.value = 'exception'
    ElMessage.error(getErrorMessage(error, 'アーカイブに失敗しました'))
  } finally {
    archiveLoading.value = false
  }
}

async function loadDuplicateStats() {
  if (!guardSalesOperation(canEdit)) return
  dupLoading.value = true
  try {
    duplicateStats.value = await getDuplicateStats()
    ElMessage.success('重複統計を取得しました')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '重複統計の取得に失敗しました'))
  } finally {
    dupLoading.value = false
  }
}

async function runDeduplicate() {
  if (!guardSalesOperation(canExport)) return
  try {
    await ElMessageBox.confirm(
      '同一 picking_no / product_code / date の重複を削除します（最新IDのみ残す）。',
      '重複削除の確認',
      { type: 'warning', confirmButtonText: '削除実行', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }

  dedupeLoading.value = true
  try {
    const result = (await performDeduplicate()) as { message?: string }
    ElMessage.success(result.message || '重複削除が完了しました')
    await refreshAll()
    await loadDuplicateStats()
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '重複削除に失敗しました'))
  } finally {
    dedupeLoading.value = false
  }
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.db-file-mgmt {
  padding: 20px 24px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.title-block {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.title-icon {
  color: #409eff;
  margin-top: 4px;
}

h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.subtitle {
  margin: 6px 0 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.info-alert {
  margin-bottom: 16px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  border: 1px solid #ebeef5;
}

.stat-card.archive {
  border-color: #f5dab1;
  background: #fdf6ec;
}

.stat-label {
  color: #909399;
  font-size: 12px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.section-card {
  margin-bottom: 16px;
  border: 1px solid #ebeef5;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.section-title {
  font-weight: 700;
  color: #303133;
}

.section-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.progress-panel {
  margin-bottom: 16px;
  padding: 12px 14px;
  background: #f5f7fa;
  border-radius: 8px;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.search-input {
  width: min(360px, 100%);
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.dup-summary {
  color: #606266;
  font-size: 14px;
}

@media (max-width: 900px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
