<template>
  <div class="data-management">
    <div class="page-header">
      <h2>データ管理</h2>
      <p class="subtitle">マスターデータのCSVインポート/エクスポート、バックアップ設定</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- インポート/エクスポート -->
      <el-tab-pane label="インポート/エクスポート" name="import_export">
        <el-row :gutter="16">
          <!-- インポート -->
          <el-col :span="12">
            <el-card class="function-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon :size="20" color="#409eff"><Upload /></el-icon>
                  <span>データインポート</span>
                </div>
              </template>
              <el-form label-width="100px">
                <el-form-item label="対象マスター">
                  <el-select v-model="importForm.master_type" placeholder="マスターを選択" style="width: 100%">
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
                    :auto-upload="false"
                    :limit="1"
                    accept=".csv,.xlsx"
                    :on-change="handleFileChange"
                  >
                    <template #trigger>
                      <el-button type="primary">ファイル選択</el-button>
                    </template>
                    <template #tip>
                      <div class="el-upload__tip">CSV/Excelファイルをアップロード</div>
                    </template>
                  </el-upload>
                </el-form-item>
                <el-form-item label="オプション">
                  <el-checkbox v-model="importForm.update_existing">既存データを更新</el-checkbox>
                  <el-checkbox v-model="importForm.skip_errors">エラー行をスキップ</el-checkbox>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleImport" :loading="importing">インポート実行</el-button>
                  <el-button @click="handleDownloadTemplate">テンプレートDL</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <!-- エクスポート -->
          <el-col :span="12">
            <el-card class="function-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon :size="20" color="#67c23a"><Download /></el-icon>
                  <span>データエクスポート</span>
                </div>
              </template>
              <el-form label-width="100px">
                <el-form-item label="対象マスター">
                  <el-select v-model="exportForm.master_type" placeholder="マスターを選択" style="width: 100%">
                    <el-option label="品目マスター" value="items" />
                    <el-option label="取引先マスター" value="customers" />
                    <el-option label="仕入先マスター" value="suppliers" />
                    <el-option label="倉庫マスター" value="warehouses" />
                    <el-option label="ユーザーマスター" value="users" />
                  </el-select>
                </el-form-item>
                <el-form-item label="フォーマット">
                  <el-radio-group v-model="exportForm.format">
                    <el-radio label="csv">CSV</el-radio>
                    <el-radio label="xlsx">Excel</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="文字コード" v-if="exportForm.format === 'csv'">
                  <el-select v-model="exportForm.encoding" style="width: 100%">
                    <el-option label="UTF-8" value="utf8" />
                    <el-option label="Shift-JIS" value="sjis" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="success" @click="handleExport" :loading="exporting">エクスポート実行</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
        </el-row>

        <!-- インポート履歴 -->
        <el-card class="history-card" shadow="never" style="margin-top: 16px;">
          <template #header>インポート/エクスポート履歴</template>
          <el-table :data="importExportHistory" stripe size="small">
            <el-table-column prop="timestamp" label="日時" width="160" />
            <el-table-column prop="type" label="種類" width="100">
              <template #default="{ row }">
                <el-tag :type="row.type === 'import' ? 'primary' : 'success'" size="small">
                  {{ row.type === 'import' ? 'インポート' : 'エクスポート' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="master" label="マスター" width="120" />
            <el-table-column prop="filename" label="ファイル名" min-width="200" />
            <el-table-column prop="records" label="件数" width="80" align="right" />
            <el-table-column prop="status" label="ステータス" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="user" label="実行者" width="100" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- バックアップ -->
      <el-tab-pane label="バックアップ" name="backup">
        <el-row :gutter="16">
          <!-- バックアップ設定 -->
          <el-col :span="12">
            <el-card class="function-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon :size="20" color="#e6a23c"><Folder /></el-icon>
                  <span>バックアップ設定</span>
                </div>
              </template>
              <el-form :model="backupSettings" label-width="120px">
                <el-form-item label="自動バックアップ">
                  <el-switch v-model="backupSettings.auto_backup" />
                </el-form-item>
                <el-form-item label="実行タイミング" v-if="backupSettings.auto_backup">
                  <el-select v-model="backupSettings.schedule" style="width: 100%">
                    <el-option label="毎日 02:00" value="daily" />
                    <el-option label="毎週日曜 02:00" value="weekly" />
                    <el-option label="毎月1日 02:00" value="monthly" />
                  </el-select>
                </el-form-item>
                <el-form-item label="保存先">
                  <el-input v-model="backupSettings.storage_path" placeholder="/backup/" />
                </el-form-item>
                <el-form-item label="保持世代数">
                  <el-input-number v-model="backupSettings.retention_count" :min="1" :max="30" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleSaveBackupSettings">設定を保存</el-button>
                  <el-button type="warning" @click="handleManualBackup">今すぐバックアップ</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <!-- バックアップ一覧 -->
          <el-col :span="12">
            <el-card class="function-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon :size="20" color="#409eff"><Files /></el-icon>
                  <span>バックアップ一覧</span>
                </div>
              </template>
              <el-table :data="backupList" stripe size="small" max-height="300">
                <el-table-column prop="filename" label="ファイル名" min-width="180" />
                <el-table-column prop="created_at" label="作成日時" width="140" />
                <el-table-column prop="size" label="サイズ" width="80" />
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" link @click="handleRestore(row)">復元</el-button>
                    <el-button size="small" type="info" link @click="handleDownloadBackup(row)">DL</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- データ初期化 -->
      <el-tab-pane label="データ初期化" name="reset">
        <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 16px;">
          <template #title>警告: データ初期化は取り消せません</template>
          <p>データ初期化を行うと、選択したデータが完全に削除されます。実行前に必ずバックアップを取得してください。</p>
        </el-alert>

        <el-card shadow="never">
          <el-form label-width="120px">
            <el-form-item label="初期化対象">
              <el-checkbox-group v-model="resetTargets">
                <el-checkbox label="transactions">トランザクションデータ</el-checkbox>
                <el-checkbox label="logs">ログデータ</el-checkbox>
                <el-checkbox label="cache">キャッシュデータ</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="確認入力">
              <el-input v-model="resetConfirmation" placeholder="「初期化する」と入力してください" />
            </el-form-item>
            <el-form-item>
              <el-button type="danger" :disabled="resetConfirmation !== '初期化する'" @click="handleResetData">
                データ初期化を実行
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download, Folder, Files } from '@element-plus/icons-vue'

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

const backupSettings = reactive({
  auto_backup: true,
  schedule: 'daily',
  storage_path: '/backup/',
  retention_count: 7,
})

const resetTargets = ref<string[]>([])
const resetConfirmation = ref('')

const importExportHistory = ref([
  { timestamp: '2026-02-05 14:30:00', type: 'import', master: '品目マスター', filename: 'items_20260205.csv', records: 1500, status: '成功', user: 'admin' },
  { timestamp: '2026-02-05 10:00:00', type: 'export', master: '取引先マスター', filename: 'customers_20260205.xlsx', records: 320, status: '成功', user: 'yamada' },
  { timestamp: '2026-02-04 16:45:00', type: 'import', master: '仕入先マスター', filename: 'suppliers_20260204.csv', records: 85, status: '一部失敗', user: 'admin' },
])

const backupList = ref([
  { filename: 'backup_20260205_020000.sql.gz', created_at: '2026-02-05 02:00', size: '125MB' },
  { filename: 'backup_20260204_020000.sql.gz', created_at: '2026-02-04 02:00', size: '124MB' },
  { filename: 'backup_20260203_020000.sql.gz', created_at: '2026-02-03 02:00', size: '123MB' },
  { filename: 'backup_20260202_020000.sql.gz', created_at: '2026-02-02 02:00', size: '122MB' },
])

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'
const getStatusType = (status: string): TagType => {
  const types: Record<string, TagType> = { '成功': 'success', '一部失敗': 'warning', '失敗': 'danger' }
  return types[status] || 'info'
}

const handleFileChange = () => { /* ファイル変更処理 */ }
const handleImport = () => {
  importing.value = true
  setTimeout(() => {
    importing.value = false
    ElMessage.success('インポートが完了しました（TODO: API呼び出し）')
  }, 2000)
}
const handleDownloadTemplate = () => ElMessage.info('テンプレートをダウンロード（TODO: 実装）')
const handleExport = () => {
  exporting.value = true
  setTimeout(() => {
    exporting.value = false
    ElMessage.success('エクスポートが完了しました（TODO: API呼び出し）')
  }, 2000)
}
const handleSaveBackupSettings = () => ElMessage.success('バックアップ設定を保存しました（TODO: API呼び出し）')
const handleManualBackup = () => ElMessage.success('バックアップを開始しました（TODO: API呼び出し）')
const handleRestore = async (row: any) => {
  await ElMessageBox.confirm(`${row.filename} からデータを復元しますか？`, '確認', { type: 'warning' })
  ElMessage.success('復元を開始しました（TODO: API呼び出し）')
}
const handleDownloadBackup = (row: any) => ElMessage.info(`${row.filename} をダウンロード（TODO: 実装）`)
const handleResetData = async () => {
  await ElMessageBox.confirm('本当にデータを初期化しますか？この操作は取り消せません。', '最終確認', { type: 'error' })
  ElMessage.success('データ初期化が完了しました（TODO: API呼び出し）')
}
</script>

<style scoped>
.data-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.function-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-card {
  margin-top: 16px;
}
</style>
