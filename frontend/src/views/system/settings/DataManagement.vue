<template>
  <div class="data-management">
    <header class="top-bar">
      <div class="top-bar__brand">
        <div class="top-bar__icon" aria-hidden="true">
          <el-icon :size="22"><DataBoard /></el-icon>
        </div>
        <div class="top-bar__text">
          <h1 class="top-bar__title">データ管理</h1>
          <p class="top-bar__desc">マスターの CSV 入出力、データベースのバックアップ、データ初期化</p>
        </div>
      </div>
    </header>

    <el-tabs v-model="activeTab" type="border-card" class="dm-tabs">
      <!-- インポート/エクスポート -->
      <el-tab-pane label="インポート/エクスポート" name="import_export">
        <div class="dm-pane">
          <div class="dm-grid">
            <el-card class="dm-card" shadow="hover">
              <template #header>
                <div class="dm-card-head">
                  <el-icon class="dm-card-head__icon dm-card-head__icon--primary" :size="18"><Upload /></el-icon>
                  <span class="dm-card-head__title">データインポート</span>
                </div>
              </template>
              <el-form class="dm-form" label-width="96px" label-position="top" size="small">
                <el-form-item label="対象マスター">
                  <el-select v-model="importForm.master_type" placeholder="マスターを選択" class="dm-fullwidth">
                    <el-option label="品目マスター" value="items" />
                    <el-option label="取引先マスター" value="customers" />
                    <el-option label="仕入先マスター" value="suppliers" />
                    <el-option label="倉庫マスター" value="warehouses" />
                    <el-option label="ユーザーマスター" value="users" />
                  </el-select>
                </el-form-item>
                <el-form-item label="ファイル">
                  <el-upload
                    ref="uploadRef"
                    class="dm-upload"
                    :auto-upload="false"
                    :limit="1"
                    accept=".csv,.xlsx"
                    :on-change="handleImportFileChange"
                  >
                    <template #trigger>
                      <el-button type="primary" size="small">ファイル選択</el-button>
                    </template>
                    <template #tip>
                      <span class="dm-upload-tip">CSV・Excel 形式</span>
                    </template>
                  </el-upload>
                </el-form-item>
                <el-form-item label="オプション">
                  <div class="dm-checks">
                    <el-checkbox v-model="importForm.update_existing">既存データを更新</el-checkbox>
                    <el-checkbox v-model="importForm.skip_errors">エラー行をスキップ</el-checkbox>
                  </div>
                </el-form-item>
                <el-form-item class="dm-form-actions">
                  <el-button type="primary" size="small" :loading="importing" @click="handleImport">
                    インポート実行
                  </el-button>
                  <el-button size="small" @click="handleDownloadTemplate">テンプレートを取得</el-button>
                </el-form-item>
              </el-form>
            </el-card>

            <el-card class="dm-card" shadow="hover">
              <template #header>
                <div class="dm-card-head">
                  <el-icon class="dm-card-head__icon dm-card-head__icon--success" :size="18"><Download /></el-icon>
                  <span class="dm-card-head__title">データエクスポート</span>
                </div>
              </template>
              <el-form class="dm-form" label-width="96px" label-position="top" size="small">
                <el-form-item label="対象マスター">
                  <el-select v-model="exportForm.master_type" placeholder="マスターを選択" class="dm-fullwidth">
                    <el-option label="品目マスター" value="items" />
                    <el-option label="取引先マスター" value="customers" />
                    <el-option label="仕入先マスター" value="suppliers" />
                    <el-option label="倉庫マスター" value="warehouses" />
                    <el-option label="ユーザーマスター" value="users" />
                  </el-select>
                </el-form-item>
                <el-form-item label="フォーマット">
                  <el-radio-group v-model="exportForm.format" size="small">
                    <el-radio value="csv">CSV</el-radio>
                    <el-radio value="xlsx">Excel</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item v-if="exportForm.format === 'csv'" label="文字コード">
                  <el-select v-model="exportForm.encoding" class="dm-fullwidth">
                    <el-option label="UTF-8" value="utf8" />
                    <el-option label="Shift-JIS" value="sjis" />
                  </el-select>
                </el-form-item>
                <el-form-item class="dm-form-actions">
                  <el-button type="success" size="small" :loading="exporting" @click="handleExport">
                    エクスポート実行
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </div>

          <el-card class="dm-card dm-card--flat" shadow="never" v-loading="importHistoryLoading">
            <template #header>
              <span class="dm-section-title">インポート / エクスポート履歴</span>
            </template>
            <el-table :data="importExportHistory" stripe size="small" class="dm-table" max-height="260">
              <el-table-column prop="timestamp" label="日時" width="156" />
              <el-table-column prop="type" label="種類" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.type === 'import' ? 'primary' : 'success'" size="small">
                    {{ row.typeLabel }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="master" label="マスター" width="112" />
              <el-table-column prop="filename" label="ファイル名" min-width="160" show-overflow-tooltip />
              <el-table-column prop="records" label="件数" width="72" align="right" />
              <el-table-column prop="status" label="状態" width="96">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">{{ row.statusLabel }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="user" label="実行者" width="100" show-overflow-tooltip />
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- バックアップ -->
      <el-tab-pane label="バックアップ" name="backup">
        <div class="dm-pane">
          <el-alert type="info" :closable="false" show-icon class="backup-hint">
            <strong>mysqldump</strong> によりデータベース全体を <code>.sql.gz</code> 形式で保存します。一覧の
            <strong>保存パス</strong>列に実際のファイルの場所が表示されます。以前の保存先が
            <code>/backup/</code> のままの場合、Windows 環境では共有ではなく
            <code>C:\backup\</code> 付近に出力されていることがあります。
          </el-alert>
          <div class="dm-grid dm-grid--backup-37" v-loading="backupLoading">
            <el-card class="dm-card" shadow="hover">
              <template #header>
                <div class="dm-card-head">
                  <el-icon class="dm-card-head__icon dm-card-head__icon--warn" :size="18"><Folder /></el-icon>
                  <span class="dm-card-head__title">バックアップ設定</span>
                </div>
              </template>
              <el-form class="dm-form" :model="backupSettings" label-width="108px" label-position="top" size="small">
                <el-form-item label="自動バックアップ">
                  <el-switch v-model="backupSettings.auto_backup" />
                </el-form-item>
                <el-form-item v-if="backupSettings.auto_backup" label="実行タイミング">
                  <el-select v-model="backupSettings.schedule" class="dm-fullwidth">
                    <el-option label="毎日 02:00" value="daily" />
                    <el-option label="毎週日曜 02:00" value="weekly" />
                    <el-option label="毎月1日 02:00" value="monthly" />
                  </el-select>
                </el-form-item>
                <el-form-item label="保存先">
                  <el-input
                    v-model="backupSettings.storage_path"
                    type="textarea"
                    :rows="2"
                    placeholder="例：社内共有の UNC パス、またはローカルフォルダ"
                    class="dm-mono"
                  />
                </el-form-item>
                <el-form-item label="保持世代数">
                  <el-input-number v-model="backupSettings.retention_count" :min="1" :max="30" size="small" />
                </el-form-item>
                <el-form-item class="dm-form-actions">
                  <el-button type="primary" size="small" :loading="savingBackup" @click="handleSaveBackupSettings">
                    設定を保存
                  </el-button>
                  <el-button type="warning" size="small" :loading="backupRunning" @click="handleManualBackup">
                    今すぐバックアップ
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>

            <el-card class="dm-card" shadow="hover">
              <template #header>
                <div class="dm-card-head">
                  <el-icon class="dm-card-head__icon dm-card-head__icon--primary" :size="18"><Files /></el-icon>
                  <span class="dm-card-head__title">バックアップ一覧</span>
                </div>
              </template>
              <el-table :data="backupList" stripe size="small" class="dm-table" max-height="280">
                <el-table-column prop="filename" label="ファイル名" min-width="120" show-overflow-tooltip />
                <el-table-column prop="file_path" label="保存パス" min-width="160" show-overflow-tooltip />
                <el-table-column prop="created_at" label="完了日時" width="132" />
                <el-table-column prop="size" label="サイズ" width="68" />
                <el-table-column prop="status" label="状態" width="84">
                  <template #default="{ row }">
                    <el-tag size="small" :type="backupStatusTag(row.status)">{{ row.statusLabel }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" link @click="handleRestore(row)">復元</el-button>
                    <el-button size="small" type="info" link @click="handleDownloadBackup(row)">ダウンロード</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <!-- データ初期化 -->
      <el-tab-pane label="データ初期化" name="reset">
        <div class="dm-pane">
          <el-alert type="warning" :closable="false" show-icon class="reset-alert">
            <template #title>この操作は取り消せません</template>
            選択した種類のデータは完全に削除されます。実行前に必ずバックアップを取得してください。
          </el-alert>
          <el-card class="dm-card dm-card--danger-zone" shadow="hover">
            <el-form class="dm-form" label-width="108px" label-position="top" size="small">
              <el-form-item label="初期化対象">
                <el-checkbox-group v-model="resetTargets" class="dm-checks-vertical">
                  <el-checkbox label="transactions">トランザクションデータ</el-checkbox>
                  <el-checkbox label="logs">ログデータ</el-checkbox>
                  <el-checkbox label="cache">キャッシュデータ</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
              <el-form-item label="確認入力">
                <el-input v-model="resetConfirmation" placeholder="「初期化する」と入力してください" clearable />
              </el-form-item>
              <el-form-item class="dm-form-actions">
                <el-button
                  type="danger"
                  size="small"
                  :disabled="resetConfirmation !== '初期化する'"
                  @click="handleResetData"
                >
                  データ初期化を実行
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile, UploadFiles, UploadInstance } from 'element-plus'
import { Upload, Download, Folder, Files, DataBoard } from '@element-plus/icons-vue'
import type { BackupHistoryItem, ImportExportHistoryRow } from '@/api/system'
import {
  getBackupSettings,
  updateBackupSettings,
  getBackupHistory,
  runManualBackup,
  downloadBackup,
  restoreBackup,
  getDataImportExportHistory,
  postDataImport,
  postDataExport,
  getDataImportTemplate,
} from '@/api/system'

const activeTab = ref('import_export')
const importing = ref(false)
const exporting = ref(false)

const importForm = reactive({
  master_type: '',
  update_existing: false,
  skip_errors: true,
})

const exportForm = reactive({
  master_type: '',
  format: 'csv',
  encoding: 'utf8',
})

const DEFAULT_BACKUP_STORAGE = '\\\\192.168.1.200\\社内共有\\02_生産管理部\\バックアップ'

const backupSettings = reactive({
  auto_backup: true,
  schedule: 'daily',
  storage_path: DEFAULT_BACKUP_STORAGE,
  retention_count: 7,
  compression_enabled: true,
})

const backupList = ref<
  {
    id: number
    filename: string
    file_path: string
    created_at: string
    size: string
    status: string
    statusLabel: string
  }[]
>([])
const backupLoading = ref(false)
const savingBackup = ref(false)
const backupRunning = ref(false)

const resetTargets = ref<string[]>([])
const resetConfirmation = ref('')

const uploadRef = ref<UploadInstance>()
const importSelectedFile = ref<File | null>(null)
const importHistoryLoading = ref(false)

const MASTER_TYPE_LABELS: Record<string, string> = {
  items: '品目',
  customers: '取引先',
  suppliers: '仕入先',
  warehouses: '倉庫',
  users: 'ユーザー',
}

const importExportHistory = ref<
  {
    timestamp: string
    type: string
    typeLabel: string
    master: string
    filename: string
    records: number
    status: string
    statusLabel: string
    user: string
  }[]
>([])

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

function ieStatusLabel(raw: string): string {
  const u = (raw || '').toLowerCase()
  const map: Record<string, string> = {
    success: '成功',
    failed: '失敗',
    partial_success: '一部失敗',
    processing: '処理中',
  }
  return map[u] || raw || '―'
}

function mapImportExportRow(r: ImportExportHistoryRow) {
  const t = r.completed_at || r.started_at || r.created_at || ''
  return {
    timestamp: t ? t.replace('T', ' ').slice(0, 19) : '―',
    type: r.type,
    typeLabel: r.type === 'import' ? 'インポート' : 'エクスポート',
    master: MASTER_TYPE_LABELS[r.master_type] || r.master_type,
    filename: r.filename,
    records: r.total_records ?? 0,
    status: r.status,
    statusLabel: ieStatusLabel(r.status),
    user: r.user_name || '―',
  }
}

const getStatusType = (status: string): TagType => {
  const u = (status || '').toLowerCase()
  const types: Record<string, TagType> = {
    success: 'success',
    failed: 'danger',
    partial_success: 'warning',
    processing: 'info',
    成功: 'success',
    一部失敗: 'warning',
    失敗: 'danger',
  }
  return types[u] || types[status] || 'info'
}

function backupStatusTag(status: string): TagType {
  const u = (status || '').toLowerCase()
  if (u === 'completed' || status === '完了') return 'success'
  if (u === 'failed' || status === '失敗') return 'danger'
  if (u === 'running' || status === '実行中') return 'warning'
  return 'info'
}

/** API の英語ステータスを画面用の日本語に変換 */
function backupStatusLabel(raw: string): string {
  if (!raw) return '―'
  const u = raw.toLowerCase()
  const map: Record<string, string> = {
    completed: '完了',
    failed: '失敗',
    running: '実行中',
    pending: '待機',
  }
  if (map[u]) return map[u]
  return raw
}

function formatBackupRow(r: BackupHistoryItem) {
  const t = r.completed_at || r.started_at || r.created_at || ''
  const created_at = t ? t.replace('T', ' ').slice(0, 16) : '―'
  const size = r.file_size_display ?? (r.file_size != null ? String(r.file_size) : '―')
  return {
    id: r.id,
    filename: r.filename,
    file_path: r.file_path || '―',
    created_at,
    size,
    status: r.status,
    statusLabel: backupStatusLabel(r.status),
  }
}

async function loadBackupData() {
  backupLoading.value = true
  try {
    const [settings, history] = await Promise.all([
      getBackupSettings(),
      getBackupHistory({ page: 1, page_size: 50 }),
    ])
    backupSettings.auto_backup = settings.auto_backup_enabled
    backupSettings.schedule = settings.schedule || 'daily'
    backupSettings.storage_path = settings.storage_path || DEFAULT_BACKUP_STORAGE
    backupSettings.retention_count = settings.retention_count ?? 7
    backupSettings.compression_enabled = settings.compression_enabled !== false
    backupList.value = (history || []).map(formatBackupRow)
  } catch (e) {
    ElMessage.error('バックアップ情報の取得に失敗しました')
    console.error(e)
  } finally {
    backupLoading.value = false
  }
}

async function loadImportExportHistory() {
  importHistoryLoading.value = true
  try {
    const rows = await getDataImportExportHistory({ page: 1, page_size: 50 })
    importExportHistory.value = (rows || []).map(mapImportExportRow)
  } catch (e) {
    ElMessage.error('履歴の取得に失敗しました')
    console.error(e)
  } finally {
    importHistoryLoading.value = false
  }
}

watch(activeTab, (name) => {
  if (name === 'backup') void loadBackupData()
  if (name === 'import_export') void loadImportExportHistory()
})

onMounted(() => {
  if (activeTab.value === 'backup') void loadBackupData()
  if (activeTab.value === 'import_export') void loadImportExportHistory()
})

const handleImportFileChange = (_file: UploadFile, fileList: UploadFiles) => {
  if (!fileList.length) {
    importSelectedFile.value = null
    return
  }
  const raw = fileList[0]?.raw
  importSelectedFile.value = raw instanceof File ? raw : null
}

const msgBoxCancel = { cancelButtonText: 'キャンセル' }

function triggerBlobDownload(blob: Blob, filename: string) {
  if (blob.type?.includes('application/json')) {
    void blob.text().then((text) => {
      try {
        const j = JSON.parse(text) as { detail?: string }
        ElMessage.error(j.detail || 'ダウンロードに失敗しました')
      } catch {
        ElMessage.error('ダウンロードに失敗しました')
      }
    })
    return
  }
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const handleImport = async () => {
  if (!importForm.master_type) {
    ElMessage.warning('対象マスターを選択してください')
    return
  }
  if (!importSelectedFile.value) {
    ElMessage.warning('ファイルを選択してください')
    return
  }
  const fd = new FormData()
  fd.append('master_type', importForm.master_type)
  fd.append('update_existing', String(importForm.update_existing))
  fd.append('skip_errors', String(importForm.skip_errors))
  fd.append('file', importSelectedFile.value)
  importing.value = true
  try {
    const res = await postDataImport(fd)
    ElMessage.success(res.message || 'インポートが完了しました')
    importSelectedFile.value = null
    uploadRef.value?.clearFiles()
    await loadImportExportHistory()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : 'インポートに失敗しました')
    console.error(e)
  } finally {
    importing.value = false
  }
}

const handleDownloadTemplate = async () => {
  if (!importForm.master_type) {
    ElMessage.warning('対象マスターを選択してください')
    return
  }
  try {
    const blob = await getDataImportTemplate(importForm.master_type)
    triggerBlobDownload(blob, `${importForm.master_type}_template.csv`)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : 'テンプレートの取得に失敗しました')
    console.error(e)
  }
}

const handleExport = async () => {
  if (!exportForm.master_type) {
    ElMessage.warning('対象マスターを選択してください')
    return
  }
  exporting.value = true
  try {
    const blob = await postDataExport({
      master_type: exportForm.master_type,
      format: exportForm.format,
      encoding: exportForm.format === 'csv' ? exportForm.encoding : undefined,
    })
    const ext = exportForm.format === 'xlsx' ? 'xlsx' : 'csv'
    const day = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    triggerBlobDownload(blob, `${exportForm.master_type}_${day}.${ext}`)
    await loadImportExportHistory()
    ElMessage.success('エクスポートファイルをダウンロードしました')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : 'エクスポートに失敗しました')
    console.error(e)
  } finally {
    exporting.value = false
  }
}
const handleSaveBackupSettings = async () => {
  savingBackup.value = true
  try {
    await updateBackupSettings({
      auto_backup_enabled: backupSettings.auto_backup,
      schedule: backupSettings.schedule,
      storage_path: backupSettings.storage_path,
      retention_count: backupSettings.retention_count,
      include_files: false,
      compression_enabled: backupSettings.compression_enabled,
      encryption_enabled: false,
      notify_on_complete: false,
      notify_on_error: true,
    })
    ElMessage.success('バックアップ設定を保存しました')
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof msg === 'string' ? msg : '保存に失敗しました')
    console.error(e)
  } finally {
    savingBackup.value = false
  }
}

const handleManualBackup = async () => {
  try {
    await ElMessageBox.confirm(
      'mysqldump によりデータベース全体をバックアップします。データ量によっては数分かかる場合があります。',
      'ご確認',
      { type: 'warning', confirmButtonText: 'バックアップを開始', ...msgBoxCancel },
    )
  } catch {
    return
  }
  backupRunning.value = true
  try {
    const res = await runManualBackup({})
    ElMessage.success(res.message || 'バックアップが正常に完了しました')
    await loadBackupData()
  } catch (e: unknown) {
    const ax = e as { response?: { data?: { detail?: string | { msg?: string }[] } } }
    const d = ax?.response?.data?.detail
    const text = typeof d === 'string' ? d : 'バックアップに失敗しました'
    ElMessage.error(text)
    console.error(e)
  } finally {
    backupRunning.value = false
  }
}

const handleRestore = async (row: { id: number; filename: string }) => {
  try {
    await ElMessageBox.confirm(
      `「${row.filename}」の内容でデータベースを復元しますか？`,
      'ご確認',
      { type: 'warning', confirmButtonText: '復元する', ...msgBoxCancel },
    )
  } catch {
    return
  }
  try {
    await restoreBackup(row.id)
    ElMessage.success('復元処理を開始しました')
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    if (status === 501) {
      ElMessage.warning(
        typeof detail === 'string'
          ? detail
          : '復元機能は未実装です。ダンプファイルを MySQL クライアント等で手動インポートしてください。',
      )
      return
    }
    ElMessage.error(typeof detail === 'string' ? detail : '復元に失敗しました')
    console.error(e)
  }
}

const handleDownloadBackup = async (row: { id: number; filename: string }) => {
  try {
    const blob = await downloadBackup(row.id)
    if (blob.type?.includes('application/json')) {
      const text = await blob.text()
      try {
        const j = JSON.parse(text) as { detail?: string }
        ElMessage.error(j.detail || 'ダウンロードに失敗しました')
      } catch {
        ElMessage.error('ダウンロードに失敗しました')
      }
      return
    }
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.filename
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : 'ダウンロードに失敗しました')
    console.error(e)
  }
}
const handleResetData = async () => {
  await ElMessageBox.confirm(
    '本当にデータを初期化しますか？この操作は取り消せません。',
    '最終確認',
    { type: 'error', confirmButtonText: '初期化する', cancelButtonText: 'キャンセル' },
  )
  ElMessage.success('データ初期化が完了しました（※API 連携は今後対応予定です）')
}
</script>

<style scoped>
.data-management {
  --dm-accent: #0d9488;
  --dm-accent-soft: color-mix(in srgb, var(--dm-accent) 12%, transparent);
  max-width: 1180px;
  margin: 0 auto;
  padding: 8px 12px 14px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  padding: 4px 2px 2px;
}

.top-bar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.top-bar__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0d9488 0%, #0e7490 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--dm-accent) 32%, transparent);
}

.top-bar__text {
  min-width: 0;
}

.top-bar__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: var(--el-text-color-primary);
}

.top-bar__desc {
  margin: 2px 0 0;
  font-size: 0.75rem;
  line-height: 1.35;
  color: var(--el-text-color-secondary);
}

.dm-tabs {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.dm-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: var(--el-fill-color-light);
}

.dm-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}

.dm-tabs :deep(.el-tabs__item) {
  font-size: 0.8125rem;
  padding: 0 14px;
  height: 38px;
  line-height: 38px;
}

.dm-tabs :deep(.el-tabs__content) {
  padding: 10px 12px 12px;
}

.dm-pane {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dm-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-items: stretch;
}

/* バックアップ：左（設定）:右（一覧）= 3:7 */
.dm-grid--backup-37 {
  grid-template-columns: 3fr 7fr;
}

@media (max-width: 900px) {
  .dm-grid,
  .dm-grid--backup-37 {
    grid-template-columns: 1fr;
  }
}

.dm-card {
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
}

.dm-card :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}

.dm-card :deep(.el-card__body) {
  padding: 10px 12px 12px;
}

.dm-card--flat {
  background: var(--el-fill-color-blank);
}

.dm-card--danger-zone {
  border-color: color-mix(in srgb, var(--el-color-danger) 22%, var(--el-border-color-lighter));
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--el-color-danger) 4%, var(--el-bg-color)) 0%,
    var(--el-bg-color) 100%
  );
}

.dm-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dm-card-head__title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.dm-card-head__icon {
  flex-shrink: 0;
}

.dm-card-head__icon--primary {
  color: var(--el-color-primary);
}

.dm-card-head__icon--success {
  color: var(--el-color-success);
}

.dm-card-head__icon--warn {
  color: var(--el-color-warning);
}

.dm-section-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.dm-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.dm-form :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.dm-form :deep(.el-form-item__label) {
  font-size: 0.75rem;
  line-height: 1.3;
  padding-bottom: 2px;
}

.dm-form-actions {
  margin-top: 4px;
}

.dm-form-actions :deep(.el-form-item__content) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dm-fullwidth {
  width: 100%;
}

.dm-mono :deep(.el-textarea__inner) {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 0.75rem;
  line-height: 1.35;
}

.dm-checks {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
}

.dm-checks-vertical {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.dm-upload-tip {
  font-size: 0.6875rem;
  color: var(--el-text-color-secondary);
  margin-left: 8px;
}

.dm-table {
  font-size: 0.75rem;
}

.backup-hint {
  margin: 0;
}

.backup-hint :deep(.el-alert__content) {
  font-size: 0.75rem;
  line-height: 1.45;
}

.backup-hint :deep(code) {
  font-size: 0.7rem;
  padding: 1px 4px;
  border-radius: 4px;
  background: var(--el-fill-color-dark);
}

.reset-alert {
  margin: 0;
}

.reset-alert :deep(.el-alert__title) {
  font-size: 0.8125rem;
}

.reset-alert :deep(.el-alert__content) {
  font-size: 0.75rem;
  line-height: 1.45;
}
</style>
