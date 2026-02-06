<template>
  <div class="system-log">
    <!-- Modern Gradient Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon :size="28"><Tickets /></el-icon>
        </div>
        <div class="header-text">
          <h1>システムログ</h1>
          <p class="subtitle">操作・エラー・API連携ログ</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ operationPagination.total }}</span>
          <span class="stat-label">操作ログ</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value error">{{ errorPagination.total }}</span>
          <span class="stat-label">エラー</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value api">{{ apiPagination.total }}</span>
          <span class="stat-label">API</span>
        </div>
      </div>
    </div>

    <!-- Modern Tabs Container -->
    <div class="tabs-container">
      <el-tabs v-model="activeTab" @tab-change="onTabChange" class="modern-tabs">
        <!-- Operation Log Tab -->
        <el-tab-pane name="operation">
          <template #label>
            <div class="tab-label">
              <el-icon><User /></el-icon>
              <span>操作ログ</span>
            </div>
          </template>

          <!-- Filter Section -->
          <div class="filter-section">
            <div class="filter-grid">
              <div class="filter-item">
                <label>ユーザー</label>
                <el-input v-model="operationSearch.user" placeholder="検索..." clearable :prefix-icon="Search" size="default" />
              </div>
              <div class="filter-item">
                <label>操作</label>
                <el-select v-model="operationSearch.action" placeholder="すべて" clearable size="default">
                  <el-option label="ログイン" value="login" />
                  <el-option label="ログアウト" value="logout" />
                  <el-option label="作成" value="create" />
                  <el-option label="更新" value="update" />
                  <el-option label="削除" value="delete" />
                </el-select>
              </div>
              <div class="filter-item date-range">
                <label>期間</label>
                <el-date-picker
                  v-model="operationSearch.dateRange"
                  type="daterange"
                  range-separator="〜"
                  start-placeholder="開始"
                  end-placeholder="終了"
                  value-format="YYYY-MM-DD"
                  size="default"
                />
              </div>
              <div class="filter-actions">
                <el-button type="primary" :icon="Search" @click="fetchOperationLogs">検索</el-button>
                <el-button :icon="Download" @click="handleExportOperation" plain>CSV</el-button>
              </div>
            </div>
          </div>

          <!-- Table -->
          <div class="table-container">
            <el-table 
              :data="operationLogs" 
              v-loading="loadingOperation"
              :header-cell-style="tableHeaderStyle"
              size="default"
              border
            >
              <el-table-column prop="timestamp" label="日時" width="160" align="center">
                <template #default="{ row }">
                  <span class="datetime">{{ formatDateTime(row.timestamp) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="username" label="ユーザー" width="120">
                <template #default="{ row }">
                  <div class="user-cell" v-if="row.username">
                    <div class="avatar-mini">{{ row.username.charAt(0).toUpperCase() }}</div>
                    <span>{{ row.username }}</span>
                  </div>
                  <span class="text-muted" v-else>—</span>
                </template>
              </el-table-column>
              <el-table-column prop="action" label="操作" width="120" align="center">
                <template #default="{ row }">
                  <span class="action-badge" :class="row.action">{{ actionLabel(row.action) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="module" label="モジュール" width="110">
                <template #default="{ row }">
                  <span class="module-tag" v-if="row.module">{{ row.module }}</span>
                  <span class="text-muted" v-else>—</span>
                </template>
              </el-table-column>
              <el-table-column prop="target" label="対象" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">{{ row.target || '—' }}</template>
              </el-table-column>
              <el-table-column prop="ip_address" label="IP" width="120">
                <template #default="{ row }">
                  <code class="ip-code" v-if="row.ip_address">{{ row.ip_address }}</code>
                  <span class="text-muted" v-else>—</span>
                </template>
              </el-table-column>
            </el-table>

            <div class="table-footer">
              <div class="footer-info">{{ operationLogs.length }} / {{ operationPagination.total }} 件</div>
              <el-pagination
                v-model:current-page="operationPagination.page"
                v-model:page-size="operationPagination.pageSize"
                :page-sizes="[20, 50, 100]"
                :total="operationPagination.total"
                layout="sizes, prev, pager, next"
                @current-change="fetchOperationLogs"
                @size-change="() => { operationPagination.page = 1; fetchOperationLogs() }"
                small
                background
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- Error Log Tab -->
        <el-tab-pane name="error">
          <template #label>
            <div class="tab-label">
              <el-icon><WarningFilled /></el-icon>
              <span>エラーログ</span>
            </div>
          </template>

          <div class="filter-section">
            <div class="filter-grid">
              <div class="filter-item">
                <label>レベル</label>
                <el-select v-model="errorSearch.level" placeholder="すべて" clearable size="default">
                  <el-option label="ERROR" value="ERROR">
                    <span class="level-option error">ERROR</span>
                  </el-option>
                  <el-option label="WARN" value="WARN">
                    <span class="level-option warn">WARN</span>
                  </el-option>
                  <el-option label="INFO" value="INFO">
                    <span class="level-option info">INFO</span>
                  </el-option>
                </el-select>
              </div>
              <div class="filter-item date-range">
                <label>期間</label>
                <el-date-picker
                  v-model="errorSearch.dateRange"
                  type="daterange"
                  range-separator="〜"
                  start-placeholder="開始"
                  end-placeholder="終了"
                  value-format="YYYY-MM-DD"
                  size="default"
                />
              </div>
              <div class="filter-actions">
                <el-button type="primary" :icon="Search" @click="fetchErrorLogs">検索</el-button>
              </div>
            </div>
          </div>

          <div class="table-container">
            <el-table 
              :data="errorLogs" 
              v-loading="loadingError"
              :header-cell-style="tableHeaderStyle"
              size="default"
              border
            >
              <el-table-column prop="timestamp" label="日時" width="160" align="center">
                <template #default="{ row }">
                  <span class="datetime">{{ formatDateTime(row.timestamp) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="level" label="レベル" width="90" align="center">
                <template #default="{ row }">
                  <span class="level-badge" :class="row.level?.toLowerCase()">{{ row.level }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="source" label="ソース" width="140">
                <template #default="{ row }">
                  <code class="source-code" v-if="row.source">{{ row.source }}</code>
                  <span class="text-muted" v-else>—</span>
                </template>
              </el-table-column>
              <el-table-column prop="message" label="メッセージ" min-width="300" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="error-message">{{ row.message }}</span>
                </template>
              </el-table-column>
            </el-table>

            <div class="table-footer">
              <div class="footer-info">{{ errorLogs.length }} / {{ errorPagination.total }} 件</div>
              <el-pagination
                v-model:current-page="errorPagination.page"
                v-model:page-size="errorPagination.pageSize"
                :page-sizes="[20, 50, 100]"
                :total="errorPagination.total"
                layout="sizes, prev, pager, next"
                @current-change="fetchErrorLogs"
                @size-change="() => { errorPagination.page = 1; fetchErrorLogs() }"
                small
                background
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- API Log Tab -->
        <el-tab-pane name="api">
          <template #label>
            <div class="tab-label">
              <el-icon><Connection /></el-icon>
              <span>API連携ログ</span>
            </div>
          </template>

          <div class="filter-section">
            <div class="filter-grid">
              <div class="filter-item">
                <label>エンドポイント</label>
                <el-input v-model="apiSearch.endpoint" placeholder="/api/..." clearable size="default" />
              </div>
              <div class="filter-item">
                <label>ステータス</label>
                <el-select v-model="apiSearch.status" placeholder="すべて" clearable size="default">
                  <el-option label="成功 (2xx)" value="success" />
                  <el-option label="クライアントエラー (4xx)" value="client_error" />
                  <el-option label="サーバーエラー (5xx)" value="server_error" />
                </el-select>
              </div>
              <div class="filter-actions">
                <el-button type="primary" :icon="Search" @click="fetchApiLogs">検索</el-button>
              </div>
            </div>
          </div>

          <div class="table-container">
            <el-table 
              :data="apiLogs" 
              v-loading="loadingApi"
              :header-cell-style="tableHeaderStyle"
              size="default"
              border
            >
              <el-table-column prop="timestamp" label="日時" width="160" align="center">
                <template #default="{ row }">
                  <span class="datetime">{{ formatDateTime(row.timestamp) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="method" label="メソッド" width="100" align="center">
                <template #default="{ row }">
                  <span class="method-badge" :class="row.method?.toLowerCase()">{{ row.method }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="endpoint" label="エンドポイント" width="250" show-overflow-tooltip>
                <template #default="{ row }">
                  <code class="endpoint-code">{{ row.endpoint }}</code>
                </template>
              </el-table-column>
              <el-table-column prop="status_code" label="ステータス" width="110" align="center">
                <template #default="{ row }">
                  <span class="status-badge" :class="getStatusClass(row.status_code)">{{ row.status_code }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="応答時間" width="90" align="right">
                <template #default="{ row }">
                  <span class="duration" :class="getDurationClass(row.duration)" v-if="row.duration != null">
                    {{ row.duration }}ms
                  </span>
                  <span class="text-muted" v-else>—</span>
                </template>
              </el-table-column>
              <el-table-column prop="client" label="クライアント" min-width="300">
                <template #default="{ row }">{{ row.client || '—' }}</template>
              </el-table-column>
            </el-table>

            <div class="table-footer">
              <div class="footer-info">{{ apiLogs.length }} / {{ apiPagination.total }} 件</div>
              <el-pagination
                v-model:current-page="apiPagination.page"
                v-model:page-size="apiPagination.pageSize"
                :page-sizes="[20, 50, 100]"
                :total="apiPagination.total"
                layout="sizes, prev, pager, next"
                @current-change="fetchApiLogs"
                @size-change="() => { apiPagination.page = 1; fetchApiLogs() }"
                small
                background
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download, Tickets, User, WarningFilled, Connection } from '@element-plus/icons-vue'
import * as systemApi from '@/api/system'
import type {
  OperationLogItem,
  ErrorLogItem,
  ApiLogItem,
} from '@/api/system'

const tableHeaderStyle = { background: '#f8fafc', color: '#475569', fontWeight: '600', fontSize: '12px', padding: '10px 8px' }

const activeTab = ref('operation')
const loadingOperation = ref(false)
const loadingError = ref(false)
const loadingApi = ref(false)

const operationSearch = reactive<{ user: string; action: string; dateRange: [string, string] | null }>({
  user: '',
  action: '',
  dateRange: null,
})
const errorSearch = reactive<{ level: string; dateRange: [string, string] | null }>({
  level: '',
  dateRange: null,
})
const apiSearch = reactive({ endpoint: '', status: '' })

const operationLogs = ref<OperationLogItem[]>([])
const errorLogs = ref<ErrorLogItem[]>([])
const apiLogs = ref<ApiLogItem[]>([])

const operationPagination = reactive({ page: 1, pageSize: 20, total: 0 })
const errorPagination = reactive({ page: 1, pageSize: 20, total: 0 })
const apiPagination = reactive({ page: 1, pageSize: 20, total: 0 })

function formatDateTime(val: string | undefined): string {
  if (!val) return '—'
  try {
    const d = new Date(val)
    return Number.isNaN(d.getTime()) ? val : d.toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return String(val)
  }
}

function actionLabel(action: string): string {
  const map: Record<string, string> = {
    login: 'ログイン',
    logout: 'ログアウト',
    create: '作成',
    update: '更新',
    delete: '削除',
  }
  return map[action] || action
}

const getStatusClass = (code: number) => {
  if (code >= 200 && code < 300) return 'success'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'error'
  return 'info'
}

const getDurationClass = (duration: number) => {
  if (duration < 100) return 'fast'
  if (duration < 500) return 'normal'
  return 'slow'
}

async function fetchOperationLogs() {
  loadingOperation.value = true
  try {
    const [start_date, end_date] = operationSearch.dateRange || [undefined, undefined]
    const res = await systemApi.getOperationLogs({
      user: operationSearch.user || undefined,
      action: operationSearch.action || undefined,
      start_date,
      end_date,
      page: operationPagination.page,
      page_size: operationPagination.pageSize,
    })
    operationLogs.value = (res as { items?: OperationLogItem[] }).items ?? []
    operationPagination.total = (res as { total?: number }).total ?? 0
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e, '操作ログの取得に失敗しました'))
  } finally {
    loadingOperation.value = false
  }
}

async function fetchErrorLogs() {
  loadingError.value = true
  try {
    const [start_date, end_date] = errorSearch.dateRange || [undefined, undefined]
    const res = await systemApi.getErrorLogs({
      level: errorSearch.level || undefined,
      start_date,
      end_date,
      page: errorPagination.page,
      page_size: errorPagination.pageSize,
    })
    errorLogs.value = (res as { items?: ErrorLogItem[] }).items ?? []
    errorPagination.total = (res as { total?: number }).total ?? 0
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e, 'エラーログの取得に失敗しました'))
  } finally {
    loadingError.value = false
  }
}

async function fetchApiLogs() {
  loadingApi.value = true
  try {
    const res = await systemApi.getApiLogs({
      endpoint: apiSearch.endpoint || undefined,
      status: apiSearch.status || undefined,
      page: apiPagination.page,
      page_size: apiPagination.pageSize,
    })
    apiLogs.value = (res as { items?: ApiLogItem[] }).items ?? []
    apiPagination.total = (res as { total?: number }).total ?? 0
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e, 'APIログの取得に失敗しました'))
  } finally {
    loadingApi.value = false
  }
}

function getErrorMessage(e: unknown, defaultMsg: string): string {
  const err = e as { response?: { data?: { detail?: string | string[] }; status?: number } }
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) return String(detail[0])
  return defaultMsg
}

function onTabChange(name: string | number) {
  const tab = String(name)
  if (tab === 'operation') fetchOperationLogs()
  else if (tab === 'error') fetchErrorLogs()
  else if (tab === 'api') fetchApiLogs()
}

async function handleExportOperation() {
  try {
    const [start_date, end_date] = operationSearch.dateRange || [undefined, undefined]
    const blob = (await systemApi.exportOperationLogs({
      user: operationSearch.user || undefined,
      action: operationSearch.action || undefined,
      start_date,
      end_date,
    })) as unknown as Blob
    if (!(blob instanceof Blob)) {
      ElMessage.error('エクスポートに失敗しました')
      return
    }
    if (blob.type?.startsWith('application/json')) {
      const text = await blob.text()
      let msg = 'エクスポートに失敗しました'
      try {
        const json = JSON.parse(text) as { detail?: string }
        if (json.detail) msg = typeof json.detail === 'string' ? json.detail : String(json.detail)
      } catch {
        /* ignore */
      }
      ElMessage.error(msg)
      return
    }
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `operation_logs_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('エクスポートしました')
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e, 'エクスポートに失敗しました'))
  }
}

onMounted(() => {
  fetchOperationLogs()
})
</script>

<style scoped>
/* Base Layout */
.system-log {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

/* Modern Gradient Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  backdrop-filter: blur(10px);
}

.header-text h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.5px;
}

.header-text .subtitle {
  margin: 2px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  padding: 10px 20px;
  border-radius: 10px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: white;
}

.stat-value.error { color: #fca5a5; }
.stat-value.api { color: #a5f3fc; }

.stat-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 2px;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: rgba(255, 255, 255, 0.2);
}

/* Tabs Container */
.tabs-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.modern-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.modern-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.modern-tabs :deep(.el-tabs__item) {
  height: 48px;
  padding: 0 20px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Filter Section */
.filter-section {
  padding: 14px 16px;
  background: rgba(248, 250, 252, 0.5);
  border-bottom: 1px solid #e2e8f0;
}

.filter-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 140px;
}

.filter-item.date-range {
  min-width: 280px;
}

.filter-item label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

/* Table Container */
.table-container {
  padding: 0;
}

.table-container :deep(.el-table) {
  --el-table-border-color: #e2e8f0;
}

.table-container :deep(.el-table--border::after),
.table-container :deep(.el-table--border::before) {
  display: none;
}

.table-container :deep(.el-table td.el-table__cell) {
  padding: 8px;
  border-bottom: 1px solid #f1f5f9;
}

/* Cell Styles */
.datetime {
  font-size: 12px;
  color: #64748b;
  font-family: 'SF Mono', monospace;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-mini {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.text-muted {
  color: #cbd5e1;
}

/* Action Badge */
.action-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.action-badge.login { background: #dcfce7; color: #16a34a; }
.action-badge.logout { background: #f1f5f9; color: #64748b; }
.action-badge.create { background: #dbeafe; color: #2563eb; }
.action-badge.update { background: #fef3c7; color: #d97706; }
.action-badge.delete { background: #fee2e2; color: #dc2626; }

.module-tag {
  display: inline-block;
  padding: 2px 8px;
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 4px;
  font-size: 11px;
}

.ip-code, .source-code, .endpoint-code {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 11px;
  padding: 2px 6px;
  background: #f1f5f9;
  border-radius: 4px;
  color: #475569;
}

/* Level Badge */
.level-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.level-badge.error { background: #fee2e2; color: #dc2626; }
.level-badge.warn { background: #fef3c7; color: #d97706; }
.level-badge.info { background: #dbeafe; color: #2563eb; }

.level-option.error { color: #dc2626; font-weight: 600; }
.level-option.warn { color: #d97706; font-weight: 600; }
.level-option.info { color: #2563eb; font-weight: 600; }

.error-message {
  font-size: 12px;
  color: #475569;
}

/* Method Badge */
.method-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  font-family: 'SF Mono', monospace;
}

.method-badge.get { background: #dcfce7; color: #16a34a; }
.method-badge.post { background: #dbeafe; color: #2563eb; }
.method-badge.put { background: #fef3c7; color: #d97706; }
.method-badge.delete { background: #fee2e2; color: #dc2626; }
.method-badge.patch { background: #ede9fe; color: #7c3aed; }

/* Status Badge */
.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  font-family: 'SF Mono', monospace;
}

.status-badge.success { background: #dcfce7; color: #16a34a; }
.status-badge.warning { background: #fef3c7; color: #d97706; }
.status-badge.error { background: #fee2e2; color: #dc2626; }
.status-badge.info { background: #f1f5f9; color: #64748b; }

/* Duration */
.duration {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
}

.duration.fast { color: #16a34a; }
.duration.normal { color: #64748b; }
.duration.slow { color: #dc2626; }

/* Table Footer */
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.footer-info {
  font-size: 12px;
  color: #64748b;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .header-stats {
    display: none;
  }
  
  .filter-item.date-range {
    min-width: 100%;
  }
}

@media (max-width: 768px) {
  .system-log {
    padding: 12px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .header-content {
    flex-direction: column;
  }
  
  .filter-grid {
    flex-direction: column;
  }
  
  .filter-item {
    width: 100%;
  }
  
  .filter-actions {
    width: 100%;
    margin-left: 0;
    justify-content: flex-start;
  }
  
  .table-footer {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
