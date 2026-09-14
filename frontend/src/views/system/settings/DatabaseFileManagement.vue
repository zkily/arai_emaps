<template>
  <div class="dfm">
    <div class="dfm-orb dfm-orb--teal" />
    <div class="dfm-orb dfm-orb--amber" />
    <div class="dfm-orb dfm-orb--slate" />

    <header class="dfm-hero">
      <div class="dfm-hero__glow" />
      <div class="dfm-hero__left">
        <div class="dfm-hero__icon">
          <el-icon :size="22"><FolderOpened /></el-icon>
        </div>
        <div>
          <div class="dfm-hero__eyebrow">システム設定 · データ保全</div>
          <h1 class="dfm-hero__title">アーカイブ管理</h1>
          <p class="dfm-hero__sub">
            肥大化したテーブルの過去データを退避し、業務で使う現行データだけをホットテーブルに残します
          </p>
        </div>
      </div>
      <el-button
        class="dfm-hero__refresh"
        round
        :icon="Refresh"
        :loading="overviewLoading"
        @click="refreshAll"
      >
        再読込
      </el-button>
    </header>

    <el-tabs v-model="activeTab" class="dfm-tabs" @tab-change="onTabChange">
      <el-tab-pane name="shipping">
        <template #label>
          <span class="dfm-tab-label">
            <el-icon><Box /></el-icon>
            shipping_log
          </span>
        </template>

    <section class="dfm-policy">
      <div class="dfm-policy__icon">
        <el-icon :size="18"><InfoFilled /></el-icon>
      </div>
      <div>
        <div class="dfm-policy__title">運用方針</div>
        <p class="dfm-policy__text">
          <code>shipping_log</code> は直近 {{ retentionDays }} 日を保持。それより古い行は
          <code>shipping_log_archive</code> へ移動します。
          <strong>picking_log_matched</strong>（完了フラグ）は再計算しないため、過去の完了状態は維持されます。
        </p>
      </div>
    </section>

    <div class="dfm-stats">
      <article class="dfm-stat dfm-stat--hot">
        <div class="dfm-stat__icon"><el-icon :size="18"><Coin /></el-icon></div>
        <div class="dfm-stat__label">shipping_log（ホット）</div>
        <div class="dfm-stat__value">{{ formatNumber(overview.shippingLog) }}</div>
        <div class="dfm-stat__hint">業務で参照する直近データ</div>
      </article>
      <article class="dfm-stat dfm-stat--archive">
        <div class="dfm-stat__icon"><el-icon :size="18"><Box /></el-icon></div>
        <div class="dfm-stat__label">shipping_log_archive（退避）</div>
        <div class="dfm-stat__value">{{ formatNumber(overview.shippingLogArchive) }}</div>
        <div class="dfm-stat__hint">過去ログの保管先</div>
      </article>
      <article class="dfm-stat dfm-stat--days">
        <div class="dfm-stat__icon"><el-icon :size="18"><Timer /></el-icon></div>
        <div class="dfm-stat__label">保持日数</div>
        <div class="dfm-stat__value">{{ retentionDays }}<span class="dfm-stat__unit">日</span></div>
        <div class="dfm-stat__hint">これより古い行を退避</div>
      </article>
    </div>

    <section class="dfm-panel dfm-panel--archive">
      <header class="dfm-panel__head">
        <div class="dfm-panel__badge dfm-panel__badge--amber">
          <el-icon><Box /></el-icon>
        </div>
        <div class="dfm-panel__titles">
          <h2>shipping_log アーカイブ</h2>
          <p>{{ retentionDays }} 日以前のログを archive 表へ移動（削除ではなく退避）</p>
        </div>
        <el-button
          class="dfm-btn-archive"
          type="warning"
          round
          :icon="Box"
          :loading="archiveLoading"
          :disabled="archiveLoading"
          @click="runArchive"
        >
          アーカイブ実行
        </el-button>
      </header>

      <div class="dfm-panel__body">
        <div v-if="archiveLoading || archiveProgress > 0" class="dfm-progress">
          <div class="dfm-progress__meta">
            <span class="dfm-progress__msg">{{ archiveMessage || '処理中...' }}</span>
            <span class="dfm-progress__count">
              {{ formatNumber(archiveDone) }}
              <template v-if="archiveTotal > 0"> / {{ formatNumber(archiveTotal) }}</template>
            </span>
          </div>
          <el-progress
            :percentage="Math.min(archiveProgress, 100)"
            :stroke-width="12"
            :status="archiveProgressStatus"
            striped
            striped-flow
          />
        </div>

        <div class="dfm-toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="picking_no / 製品名 / 製品CD で検索"
            clearable
            class="dfm-search"
            :prefix-icon="Search"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
          <el-button round :icon="Search" @click="handleSearch">検索</el-button>
          <el-button round :icon="Refresh" :loading="logsLoading" @click="loadLogs">更新</el-button>
          <span class="dfm-toolbar__total">表示 {{ formatNumber(totalRecords) }} 件</span>
        </div>

        <el-table
          :data="logs"
          v-loading="logsLoading"
          height="420"
          stripe
          class="dfm-table"
          empty-text="ホットテーブルにデータがありません"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="picking_no" label="ピッキングNo" min-width="160" />
          <el-table-column prop="product_code" label="製品CD" width="120" />
          <el-table-column prop="product_name" label="製品名" min-width="180" show-overflow-tooltip />
          <el-table-column prop="quantity" label="数量" width="80" align="right" />
          <el-table-column prop="date" label="日付" width="120" />
          <el-table-column prop="created_at" label="作成日時" width="170">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <div class="dfm-pager">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalRecords"
            layout="total, sizes, prev, pager, next"
            background
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </section>

    <section class="dfm-panel dfm-panel--dup">
      <header class="dfm-panel__head">
        <div class="dfm-panel__badge dfm-panel__badge--rose">
          <el-icon><WarningFilled /></el-icon>
        </div>
        <div class="dfm-panel__titles">
          <h2>重複データ整理</h2>
          <p>同一 picking_no + product_code + date の重複を整理</p>
        </div>
        <div class="dfm-panel__actions">
          <el-button round :loading="dupLoading" @click="loadDuplicateStats">重複統計</el-button>
          <el-button
            type="danger"
            plain
            round
            :loading="dedupeLoading"
            @click="runDeduplicate"
          >
            重複削除
          </el-button>
        </div>
      </header>

      <div class="dfm-panel__body">
        <div v-if="duplicateStats" class="dfm-dup-grid">
          <div class="dfm-dup-card">
            <div class="dfm-dup-card__label">余剰重複</div>
            <div class="dfm-dup-card__value">{{ formatNumber(duplicateStats.total_duplicates) }}</div>
            <div class="dfm-dup-card__unit">件</div>
          </div>
          <div class="dfm-dup-card dfm-dup-card--indigo">
            <div class="dfm-dup-card__label">対象 picking_no</div>
            <div class="dfm-dup-card__value">{{ formatNumber(duplicateStats.unique_picking_nos) }}</div>
            <div class="dfm-dup-card__unit">件</div>
          </div>
        </div>
        <div v-else class="dfm-empty">
          <el-icon :size="28"><DataAnalysis /></el-icon>
          <p>「重複統計」を実行すると結果が表示されます</p>
        </div>
      </div>
    </section>
      </el-tab-pane>

      <el-tab-pane name="lotForecast" lazy>
        <template #label>
          <span class="dfm-tab-label">
            <el-icon><DataAnalysis /></el-icon>
            lot_forecast_attribution
          </span>
        </template>

        <section class="dfm-policy dfm-policy--indigo">
          <div class="dfm-policy__icon dfm-policy__icon--indigo">
            <el-icon :size="18"><InfoFilled /></el-icon>
          </div>
          <div>
            <div class="dfm-policy__title">運用方針</div>
            <p class="dfm-policy__text">
              業務照会は <code>is_current = 1</code> のみ参照します。再計算で無効になった
              <code>is_current = 0</code> の行だけを
              <code>lot_forecast_attribution_archive</code> へ移動します（削除ではなく退避）。
              現行行はホットテーブルに残るため、生産ロット進捗・APS 看板への影響はありません。
            </p>
          </div>
        </section>

        <div class="dfm-stats">
          <article class="dfm-stat dfm-stat--hot">
            <div class="dfm-stat__icon"><el-icon :size="18"><Coin /></el-icon></div>
            <div class="dfm-stat__label">現行（is_current=1）</div>
            <div class="dfm-stat__value">{{ formatNumber(lfaOverview.current) }}</div>
            <div class="dfm-stat__hint">業務で使う有効データ</div>
          </article>
          <article class="dfm-stat dfm-stat--stale">
            <div class="dfm-stat__icon"><el-icon :size="18"><WarningFilled /></el-icon></div>
            <div class="dfm-stat__label">無効版（退避対象）</div>
            <div class="dfm-stat__value">{{ formatNumber(lfaOverview.stale) }}</div>
            <div class="dfm-stat__hint">is_current=0 の履歴バージョン</div>
          </article>
          <article class="dfm-stat dfm-stat--archive">
            <div class="dfm-stat__icon"><el-icon :size="18"><Box /></el-icon></div>
            <div class="dfm-stat__label">archive（退避済）</div>
            <div class="dfm-stat__value">{{ formatNumber(lfaOverview.archive) }}</div>
            <div class="dfm-stat__hint">lot_forecast_attribution_archive</div>
          </article>
        </div>

        <section class="dfm-panel dfm-panel--lfa">
          <header class="dfm-panel__head">
            <div class="dfm-panel__badge">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="dfm-panel__titles">
              <h2>lot_forecast_attribution アーカイブ</h2>
              <p>無効版のみ移動。現行行（is_current=1）は残します</p>
            </div>
            <el-button
              class="dfm-btn-lfa"
              type="primary"
              round
              :icon="Box"
              :loading="lfaArchiveLoading"
              :disabled="lfaArchiveLoading || lfaOverview.stale <= 0"
              @click="runLfaArchive"
            >
              アーカイブ実行
            </el-button>
          </header>

          <div class="dfm-panel__body">
            <div v-if="lfaArchiveLoading || lfaArchiveProgress > 0" class="dfm-progress dfm-progress--indigo">
              <div class="dfm-progress__meta">
                <span class="dfm-progress__msg">{{ lfaArchiveMessage || '処理中...' }}</span>
                <span class="dfm-progress__count">
                  {{ formatNumber(lfaArchiveDone) }}
                  <template v-if="lfaArchiveTotal > 0"> / {{ formatNumber(lfaArchiveTotal) }}</template>
                </span>
              </div>
              <el-progress
                :percentage="Math.min(lfaArchiveProgress, 100)"
                :stroke-width="12"
                :status="lfaArchiveProgressStatus"
                striped
                striped-flow
              />
            </div>

            <div class="dfm-toolbar">
              <el-input
                v-model="lfaSearchQuery"
                placeholder="管理コード / 製品CD で検索"
                clearable
                class="dfm-search"
                :prefix-icon="Search"
                @keyup.enter="handleLfaSearch"
                @clear="handleLfaSearch"
              />
              <el-button round :icon="Search" @click="handleLfaSearch">検索</el-button>
              <el-button round :icon="Refresh" :loading="lfaLogsLoading" @click="loadLfaPreview">更新</el-button>
              <span class="dfm-toolbar__total">現行 {{ formatNumber(lfaTotalRecords) }} 件</span>
            </div>

            <el-table
              :data="lfaLogs"
              v-loading="lfaLogsLoading"
              height="420"
              stripe
              class="dfm-table"
              empty-text="現行データがありません"
            >
              <el-table-column prop="id" label="ID" width="90" />
              <el-table-column prop="management_code" label="管理コード" min-width="150" show-overflow-tooltip />
              <el-table-column prop="product_cd" label="製品CD" width="120" />
              <el-table-column prop="destination_cd" label="納入先" width="110" />
              <el-table-column prop="process_key" label="工程" width="100" />
              <el-table-column prop="source_date" label="生産日" width="120" />
              <el-table-column prop="forecast_attribution_date" label="内示帰属日" width="120" />
              <el-table-column prop="attributed_qty" label="数量" width="90" align="right" />
              <el-table-column prop="computed_at" label="計算日時" width="170">
                <template #default="{ row }">
                  {{ formatDateTime(row.computed_at) }}
                </template>
              </el-table-column>
            </el-table>

            <div class="dfm-pager">
              <el-pagination
                v-model:current-page="lfaCurrentPage"
                v-model:page-size="lfaPageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="lfaTotalRecords"
                layout="total, sizes, prev, pager, next"
                background
                @size-change="handleLfaSizeChange"
                @current-change="handleLfaCurrentChange"
              />
            </div>
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Box,
  Coin,
  DataAnalysis,
  FolderOpened,
  InfoFilled,
  Refresh,
  Search,
  Timer,
  WarningFilled,
} from '@element-plus/icons-vue'
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
import {
  getLotForecastArchiveOverview,
  getLotForecastArchivePreview,
  getLotForecastArchiveTask,
  startLotForecastArchive,
  type LotForecastArchivePreviewRow,
} from '@/api/lotForecastAttribution'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import { useSalesOperationPermission } from '@/composables/useSalesOperationPermission'
import { guardMesOperation } from '@/utils/mesOperationGuard'
import { guardSalesOperation } from '@/utils/salesOperationGuard'

const { canEdit, canExport } = useSalesOperationPermission()
const { canEdit: canMesEdit } = useMesOperationPermission()

const activeTab = ref('shipping')
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

const lfaLoaded = ref(false)
const lfaOverview = ref({ current: 0, stale: 0, archive: 0 })
const lfaLogs = ref<LotForecastArchivePreviewRow[]>([])
const lfaLogsLoading = ref(false)
const lfaSearchQuery = ref('')
const lfaCurrentPage = ref(1)
const lfaPageSize = ref(20)
const lfaTotalRecords = ref(0)
const lfaArchiveLoading = ref(false)
const lfaArchiveProgress = ref(0)
const lfaArchiveMessage = ref('')
const lfaArchiveDone = ref(0)
const lfaArchiveTotal = ref(0)
const lfaArchiveProgressStatus = ref<'' | 'success' | 'exception' | 'warning'>('')

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

async function loadLfaOverview() {
  overviewLoading.value = true
  try {
    const response = await getLotForecastArchiveOverview()
    const data = (response.data ?? response) as {
      current?: number
      stale?: number
      archive?: number
    }
    lfaOverview.value = {
      current: Number(data.current || 0),
      stale: Number(data.stale || 0),
      archive: Number(data.archive || 0),
    }
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, 'lot_forecast_attribution 件数の取得に失敗しました'))
  } finally {
    overviewLoading.value = false
  }
}

async function loadLfaPreview() {
  lfaLogsLoading.value = true
  try {
    const params: { page: number; pageSize: number; search?: string } = {
      page: lfaCurrentPage.value,
      pageSize: lfaPageSize.value,
    }
    if (lfaSearchQuery.value.trim()) params.search = lfaSearchQuery.value.trim()
    const response = await getLotForecastArchivePreview(params)
    const data = (response.data ?? response) as {
      items?: LotForecastArchivePreviewRow[]
      total?: number
    }
    lfaLogs.value = data.items || []
    lfaTotalRecords.value = Number(data.total || 0)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '現行データの取得に失敗しました'))
  } finally {
    lfaLogsLoading.value = false
  }
}

function handleLfaSearch() {
  lfaCurrentPage.value = 1
  loadLfaPreview()
}

function handleLfaSizeChange(size: number) {
  lfaPageSize.value = size
  lfaCurrentPage.value = 1
  loadLfaPreview()
}

function handleLfaCurrentChange(page: number) {
  lfaCurrentPage.value = page
  loadLfaPreview()
}

async function refreshLfa() {
  lfaLoaded.value = true
  await Promise.all([loadLfaOverview(), loadLfaPreview()])
}

async function refreshAll() {
  if (activeTab.value === 'lotForecast') {
    await refreshLfa()
    return
  }
  await Promise.all([loadOverview(), loadLogs()])
}

function onTabChange(name: string | number) {
  if (name === 'lotForecast' && !lfaLoaded.value) {
    refreshLfa()
  }
}

async function runArchive() {
  if (!guardSalesOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      `${retentionDays}日以前の shipping_log を shipping_log_archive へ退避します。直近データとピッキング完了フラグは保持されます。`,
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

async function runLfaArchive() {
  if (!guardMesOperation(canMesEdit)) return
  try {
    await ElMessageBox.confirm(
      `無効版（is_current=0）を lot_forecast_attribution_archive へ退避します。現行行（${formatNumber(lfaOverview.value.current)} 件）はホットテーブルに残ります。対象は約 ${formatNumber(lfaOverview.value.stale)} 件です。`,
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

  lfaArchiveLoading.value = true
  lfaArchiveProgress.value = 1
  lfaArchiveProgressStatus.value = ''
  lfaArchiveMessage.value = 'アーカイブを開始しています...'
  lfaArchiveDone.value = 0
  lfaArchiveTotal.value = 0

  try {
    const startResult = await startLotForecastArchive()
    const taskId = String(startResult.data?.task_id || startResult.task_id || '')
    if (!taskId) {
      throw new Error('task_id が取得できませんでした')
    }

    const maxPoll = 3600
    for (let i = 0; i < maxPoll; i += 1) {
      await new Promise((r) => setTimeout(r, 1000))
      const statusResult = await getLotForecastArchiveTask(taskId)
      const task = (statusResult.data ?? statusResult) as Record<string, any>
      lfaArchiveProgress.value = Math.min(100, Number(task.progress_percent || 0))
      lfaArchiveMessage.value = String(task.message || '')
      lfaArchiveDone.value = Number(task.archived || 0)
      lfaArchiveTotal.value = Number(task.total_candidates || 0)

      if (task.status === 'completed') {
        lfaArchiveProgress.value = 100
        lfaArchiveProgressStatus.value = 'success'
        ElMessage.success(String(task.message || 'アーカイブが完了しました'))
        break
      }
      if (task.status === 'failed') {
        lfaArchiveProgressStatus.value = 'exception'
        throw new Error(String(task.error || task.message || 'アーカイブに失敗しました'))
      }
      if (i === maxPoll - 1) {
        lfaArchiveProgressStatus.value = 'warning'
        ElMessage.warning('処理は継続中です。しばらくしてから件数を再読込してください。')
      }
    }

    await refreshLfa()
  } catch (error: unknown) {
    lfaArchiveProgressStatus.value = 'exception'
    ElMessage.error(getErrorMessage(error, 'アーカイブに失敗しました'))
  } finally {
    lfaArchiveLoading.value = false
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
.dfm {
  --ink: #0f172a;
  --muted: #64748b;
  --line: rgba(148, 163, 184, 0.28);
  --hot: #0d9488;
  --archive: #d97706;
  --dup: #e11d48;
  position: relative;
  isolation: isolate;
  min-height: calc(100vh - 88px);
  padding: 18px 20px 36px;
  overflow: hidden;
  color: var(--ink);
  background:
    radial-gradient(1100px 460px at 6% -12%, rgba(13, 148, 136, 0.14), transparent 55%),
    radial-gradient(900px 420px at 98% 4%, rgba(245, 158, 11, 0.12), transparent 50%),
    linear-gradient(180deg, #f8fafc 0%, #f0fdfa 46%, #f8fafc 100%);
}

.dfm-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  filter: blur(2px);
  animation: dfm-float 10s ease-in-out infinite;
}
.dfm-orb--teal {
  width: 240px;
  height: 240px;
  top: 30px;
  right: 10%;
  background: radial-gradient(circle, rgba(45, 212, 191, 0.28), transparent 70%);
}
.dfm-orb--amber {
  width: 190px;
  height: 190px;
  bottom: 14%;
  left: 3%;
  background: radial-gradient(circle, rgba(251, 191, 36, 0.24), transparent 70%);
  animation-delay: -3.2s;
}
.dfm-orb--slate {
  width: 150px;
  height: 150px;
  top: 42%;
  right: -30px;
  background: radial-gradient(circle, rgba(100, 116, 139, 0.18), transparent 70%);
  animation-delay: -6s;
}

@keyframes dfm-float {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(10px, -16px, 0) scale(1.06);
  }
}

.dfm-hero,
.dfm-policy,
.dfm-stats,
.dfm-panel,
.dfm-tabs {
  position: relative;
  z-index: 1;
}

.dfm-tabs {
  margin-top: 2px;
}
.dfm-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 800;
}
:deep(.dfm-tabs .el-tabs__header) {
  margin: 0 0 14px;
}
:deep(.dfm-tabs .el-tabs__nav-wrap::after) {
  display: none;
}
:deep(.dfm-tabs .el-tabs__item) {
  height: 42px;
  font-weight: 700;
  color: #64748b;
}
:deep(.dfm-tabs .el-tabs__item.is-active) {
  color: #0f766e;
}
:deep(.dfm-tabs .el-tabs__active-bar) {
  height: 3px;
  border-radius: 99px;
  background: linear-gradient(90deg, #0d9488, #d97706);
}
:deep(.dfm-tabs .el-tabs__nav) {
  padding: 4px 6px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
}

.dfm-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding: 18px 20px;
  border-radius: 22px;
  overflow: hidden;
  color: #fff;
  background: linear-gradient(135deg, #134e4a 0%, #0f766e 48%, #d97706 100%);
  box-shadow:
    0 18px 40px rgba(15, 118, 110, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
  transform: perspective(900px) rotateX(2deg);
  animation: dfm-in 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}

.dfm-hero__glow {
  position: absolute;
  inset: -35% auto auto 18%;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.18), transparent 65%);
  pointer-events: none;
}

.dfm-hero__left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}
.dfm-hero__icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(160deg, #5eead4, #0d9488);
  box-shadow: 0 10px 20px rgba(13, 148, 136, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.dfm-hero__eyebrow {
  font-size: 11px;
  letter-spacing: 0.12em;
  opacity: 0.78;
  font-weight: 700;
}
.dfm-hero__title {
  margin: 2px 0 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.dfm-hero__sub {
  margin: 4px 0 0;
  font-size: 12px;
  opacity: 0.86;
  line-height: 1.45;
  max-width: 640px;
}
.dfm-hero__refresh {
  color: #134e4a !important;
  background: rgba(255, 255, 255, 0.92) !important;
  border: none !important;
  font-weight: 700 !important;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

@keyframes dfm-in {
  from {
    opacity: 0;
    transform: perspective(900px) rotateX(8deg) translateY(14px);
  }
  to {
    opacity: 1;
    transform: perspective(900px) rotateX(2deg) translateY(0);
  }
}

.dfm-policy {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.75);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(14px);
  animation: dfm-rise 0.5s ease both;
  animation-delay: 0.05s;
}
.dfm-policy__icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #0f766e;
  background: #ccfbf1;
}
.dfm-policy__icon--indigo {
  color: #4338ca;
  background: #e0e7ff;
}
.dfm-policy--indigo .dfm-policy__title {
  color: #3730a3;
}
.dfm-policy__title {
  font-size: 13px;
  font-weight: 800;
  color: #115e59;
}
.dfm-policy__text {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.55;
  color: var(--muted);
}
.dfm-policy__text code {
  padding: 1px 6px;
  border-radius: 6px;
  font-size: 11px;
  color: #0f766e;
  background: #f0fdfa;
}

.dfm-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.dfm-stat {
  position: relative;
  overflow: hidden;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
  backdrop-filter: blur(12px);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  animation: dfm-rise 0.55s ease both;
}
.dfm-stat:nth-child(1) {
  animation-delay: 0.08s;
}
.dfm-stat:nth-child(2) {
  animation-delay: 0.14s;
}
.dfm-stat:nth-child(3) {
  animation-delay: 0.2s;
}
.dfm-stat:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.12);
}
.dfm-stat--hot {
  border-top: 3px solid #14b8a6;
}
.dfm-stat--archive {
  border-top: 3px solid #f59e0b;
}
.dfm-stat--days {
  border-top: 3px solid #6366f1;
}
.dfm-stat--stale {
  border-top: 3px solid #e11d48;
}
.dfm-stat__icon {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  margin-bottom: 10px;
}
.dfm-stat--hot .dfm-stat__icon {
  color: #0f766e;
  background: #ccfbf1;
}
.dfm-stat--archive .dfm-stat__icon {
  color: #b45309;
  background: #ffedd5;
}
.dfm-stat--days .dfm-stat__icon {
  color: #4338ca;
  background: #e0e7ff;
}
.dfm-stat--stale .dfm-stat__icon {
  color: #be123c;
  background: #ffe4e6;
}
.dfm-stat__label {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}
.dfm-stat__value {
  margin-top: 6px;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}
.dfm-stat--hot .dfm-stat__value {
  color: #0f766e;
}
.dfm-stat--archive .dfm-stat__value {
  color: #b45309;
}
.dfm-stat--days .dfm-stat__value {
  color: #4338ca;
}
.dfm-stat--stale .dfm-stat__value {
  color: #be123c;
}
.dfm-stat__unit {
  margin-left: 4px;
  font-size: 14px;
  font-weight: 700;
}
.dfm-stat__hint {
  margin-top: 4px;
  font-size: 11px;
  color: #94a3b8;
}

@keyframes dfm-rise {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dfm-panel {
  margin-bottom: 16px;
  border-radius: 22px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
  animation: dfm-rise 0.55s ease both;
}
.dfm-panel--archive {
  animation-delay: 0.16s;
}
.dfm-panel--dup {
  animation-delay: 0.22s;
}
.dfm-panel--lfa .dfm-panel__head {
  background: linear-gradient(135deg, #818cf8 0%, #6366f1 48%, #4338ca 100%);
}
.dfm-btn-lfa {
  font-weight: 800 !important;
  background: #fff !important;
  color: #3730a3 !important;
  border: none !important;
  box-shadow: 0 8px 16px rgba(67, 56, 202, 0.28) !important;
}

.dfm-panel__head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  color: #fff;
}
.dfm-panel--archive .dfm-panel__head {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 48%, #d97706 100%);
}
.dfm-panel--dup .dfm-panel__head {
  background: linear-gradient(135deg, #fb7185 0%, #e11d48 55%, #9f1239 100%);
}
.dfm-panel__badge {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.2);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.dfm-panel__titles {
  min-width: 0;
  flex: 1;
}
.dfm-panel__titles h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
}
.dfm-panel__titles p {
  margin: 2px 0 0;
  font-size: 11px;
  opacity: 0.9;
}
.dfm-panel__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.dfm-btn-archive {
  font-weight: 800 !important;
  box-shadow: 0 8px 16px rgba(180, 83, 9, 0.28) !important;
}
.dfm-panel__body {
  padding: 14px 16px 16px;
}

.dfm-progress {
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fde68a;
}
.dfm-progress__meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 13px;
}
.dfm-progress__msg {
  color: #92400e;
  font-weight: 700;
}
.dfm-progress__count {
  color: #b45309;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.dfm-progress--indigo {
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  border-color: #c7d2fe;
}
.dfm-progress--indigo .dfm-progress__msg {
  color: #3730a3;
}
.dfm-progress--indigo .dfm-progress__count {
  color: #4338ca;
}

.dfm-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.dfm-search {
  width: min(360px, 100%);
}
.dfm-toolbar__total {
  margin-left: auto;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 999px;
}

.dfm-table {
  border-radius: 14px;
  overflow: hidden;
}
.dfm-pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.dfm-dup-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.dfm-dup-card {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  gap: 2px 8px;
  padding: 16px 18px;
  border-radius: 16px;
  background: linear-gradient(160deg, #fff1f2 0%, #ffe4e6 100%);
  border: 1px solid #fecdd3;
}
.dfm-dup-card--indigo {
  background: linear-gradient(160deg, #eef2ff 0%, #e0e7ff 100%);
  border-color: #c7d2fe;
}
.dfm-dup-card__label {
  grid-column: 1 / -1;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}
.dfm-dup-card__value {
  font-size: 28px;
  font-weight: 800;
  color: #be123c;
  font-variant-numeric: tabular-nums;
}
.dfm-dup-card--indigo .dfm-dup-card__value {
  color: #4338ca;
}
.dfm-dup-card__unit {
  align-self: end;
  padding-bottom: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.dfm-empty {
  display: grid;
  place-items: center;
  gap: 8px;
  padding: 28px 12px;
  color: #94a3b8;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px dashed #e2e8f0;
}
.dfm-empty p {
  margin: 0;
  font-size: 13px;
}

:deep(.el-button) {
  font-weight: 700;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}
:deep(.el-button:not(.is-disabled):hover) {
  transform: translateY(-1px);
}
:deep(.el-button:not(.is-disabled):active) {
  transform: translateY(1px);
}

@media (max-width: 980px) {
  .dfm-stats,
  .dfm-dup-grid {
    grid-template-columns: 1fr;
  }
  .dfm-hero {
    display: block;
    transform: none;
  }
  .dfm-hero__refresh {
    margin-top: 12px;
  }
  .dfm-panel__head {
    flex-wrap: wrap;
  }
  .dfm-toolbar__total {
    margin-left: 0;
  }
}
</style>
