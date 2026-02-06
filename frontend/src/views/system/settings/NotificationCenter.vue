<template>
  <div class="notification-center">
    <div class="page-header">
      <h2>通知センター</h2>
      <p class="subtitle">システム内通知、メール通知テンプレート、LINE/Slack連携設定</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- システム通知 -->
      <el-tab-pane label="システム通知" name="system">
        <el-table :data="systemNotifications" stripe border>
          <el-table-column prop="event" label="イベント" min-width="180" />
          <el-table-column prop="description" label="説明" min-width="250" />
          <el-table-column label="通知方法" width="200">
            <template #default="{ row }">
              <el-tag v-if="row.in_app" type="primary" size="small" class="notify-tag">アプリ内</el-tag>
              <el-tag v-if="row.email" type="success" size="small" class="notify-tag">メール</el-tag>
              <el-tag v-if="row.slack" type="warning" size="small" class="notify-tag">Slack</el-tag>
              <el-tag v-if="row.line" type="danger" size="small" class="notify-tag">LINE</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="有効" width="80" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.status" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditNotification(row)">編集</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- メールテンプレート -->
      <el-tab-pane label="メールテンプレート" name="email">
        <div class="tab-actions">
          <el-button type="primary" :icon="Plus" @click="handleAddTemplate">テンプレート追加</el-button>
        </div>
        <el-table :data="emailTemplates" stripe border>
          <el-table-column prop="code" label="コード" width="120" />
          <el-table-column prop="name" label="テンプレート名" min-width="150" />
          <el-table-column prop="subject" label="件名" min-width="200" />
          <el-table-column prop="event" label="イベント" width="150" />
          <el-table-column prop="lang" label="言語" width="80">
            <template #default="{ row }">
              <el-tag size="small">{{ row.lang }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditTemplate(row)">編集</el-button>
              <el-button size="small" type="info" link @click="handlePreviewTemplate(row)">プレビュー</el-button>
              <el-button size="small" type="danger" link @click="handleDeleteTemplate(row)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 外部連携 -->
      <el-tab-pane label="外部連携" name="integration">
        <el-row :gutter="16">
          <!-- Slack連携 -->
          <el-col :span="12">
            <el-card class="integration-card" shadow="hover">
              <template #header>
                <div class="integration-header">
                  <img src="https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png" alt="Slack" class="integration-logo" />
                  <span>Slack連携</span>
                  <el-tag :type="slackConfig.enabled ? 'success' : 'info'" size="small">
                    {{ slackConfig.enabled ? '接続済み' : '未接続' }}
                  </el-tag>
                </div>
              </template>
              <el-form label-width="120px" size="small">
                <el-form-item label="Webhook URL">
                  <el-input v-model="slackConfig.webhook_url" placeholder="https://hooks.slack.com/services/..." show-password />
                </el-form-item>
                <el-form-item label="チャンネル">
                  <el-input v-model="slackConfig.channel" placeholder="#notifications" />
                </el-form-item>
                <el-form-item label="有効化">
                  <el-switch v-model="slackConfig.enabled" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleSaveSlack">保存</el-button>
                  <el-button @click="handleTestSlack">テスト送信</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <!-- LINE連携 -->
          <el-col :span="12">
            <el-card class="integration-card" shadow="hover">
              <template #header>
                <div class="integration-header">
                  <img src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg" alt="LINE" class="integration-logo" />
                  <span>LINE連携</span>
                  <el-tag :type="lineConfig.enabled ? 'success' : 'info'" size="small">
                    {{ lineConfig.enabled ? '接続済み' : '未接続' }}
                  </el-tag>
                </div>
              </template>
              <el-form label-width="120px" size="small">
                <el-form-item label="Channel Token">
                  <el-input v-model="lineConfig.channel_token" placeholder="Channel Access Token" show-password />
                </el-form-item>
                <el-form-item label="Channel Secret">
                  <el-input v-model="lineConfig.channel_secret" placeholder="Channel Secret" show-password />
                </el-form-item>
                <el-form-item label="有効化">
                  <el-switch v-model="lineConfig.enabled" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleSaveLine">保存</el-button>
                  <el-button @click="handleTestLine">テスト送信</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const activeTab = ref('system')

const systemNotifications = ref([
  { id: 1, event: '承認依頼', description: '新しい承認依頼が届いた時', in_app: true, email: true, slack: true, line: false, status: true },
  { id: 2, event: '承認完了', description: '承認が完了した時', in_app: true, email: true, slack: false, line: false, status: true },
  { id: 3, event: '承認却下', description: '承認が却下された時', in_app: true, email: true, slack: true, line: false, status: true },
  { id: 4, event: '納期アラート', description: '納期が近づいている時', in_app: true, email: true, slack: true, line: true, status: true },
  { id: 5, event: '在庫アラート', description: '在庫が基準値を下回った時', in_app: true, email: true, slack: true, line: false, status: true },
  { id: 6, event: 'システムエラー', description: 'システムエラーが発生した時', in_app: true, email: true, slack: true, line: false, status: true },
])

const emailTemplates = ref([
  { id: 1, code: 'APPROVAL_REQUEST', name: '承認依頼', subject: '【要承認】{document_type} #{document_no}', event: '承認依頼', lang: 'ja' },
  { id: 2, code: 'APPROVAL_COMPLETE', name: '承認完了', subject: '【承認完了】{document_type} #{document_no}', event: '承認完了', lang: 'ja' },
  { id: 3, code: 'PASSWORD_RESET', name: 'パスワードリセット', subject: '【Smart-EMAP】パスワードリセット', event: 'パスワードリセット', lang: 'ja' },
  { id: 4, code: 'WELCOME', name: 'ようこそ', subject: '【Smart-EMAP】アカウント作成完了', event: '新規登録', lang: 'ja' },
])

const slackConfig = reactive({
  webhook_url: '',
  channel: '#notifications',
  enabled: false,
})

const lineConfig = reactive({
  channel_token: '',
  channel_secret: '',
  enabled: false,
})

const handleEditNotification = (row: any) => ElMessage.info(`通知設定「${row.event}」を編集（TODO: 実装）`)

const handleAddTemplate = () => ElMessage.info('テンプレート追加ダイアログを表示（TODO: 実装）')
const handleEditTemplate = (row: any) => ElMessage.info(`テンプレート「${row.name}」を編集（TODO: 実装）`)
const handlePreviewTemplate = (row: any) => ElMessage.info(`テンプレート「${row.name}」をプレビュー（TODO: 実装）`)
const handleDeleteTemplate = async (row: any) => {
  await ElMessageBox.confirm(`テンプレート「${row.name}」を削除しますか？`, '確認', { type: 'warning' })
  ElMessage.success('削除しました（TODO: API呼び出し）')
}

const handleSaveSlack = () => ElMessage.success('Slack設定を保存しました（TODO: API呼び出し）')
const handleTestSlack = () => ElMessage.info('Slackにテストメッセージを送信しました（TODO: API呼び出し）')
const handleSaveLine = () => ElMessage.success('LINE設定を保存しました（TODO: API呼び出し）')
const handleTestLine = () => ElMessage.info('LINEにテストメッセージを送信しました（TODO: API呼び出し）')
</script>

<style scoped>
.notification-center {
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

.tab-actions {
  margin-bottom: 16px;
}

.notify-tag {
  margin-right: 4px;
}

.integration-card {
  height: 100%;
}

.integration-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.integration-logo {
  width: 24px;
  height: 24px;
  object-fit: contain;
}
</style>
