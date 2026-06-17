<template>
  <div class="nc-page" v-loading="pageLoading">
    <!-- 顶部：标题 + 统计 + Tab 一体化 -->
    <header class="nc-top">
      <div class="nc-top__bar">
        <div class="nc-top__brand">
          <div class="nc-top__icon" aria-hidden="true">
            <el-icon :size="18"><Bell /></el-icon>
          </div>
          <div class="nc-top__titles">
            <h1 class="nc-top__title">通知センター</h1>
            <span class="nc-top__desc">イベント通知・受信者・テンプレート・外部連携</span>
          </div>
        </div>
        <div class="nc-top__stats">
          <div
            v-for="s in statCards"
            :key="s.key"
            class="nc-chip"
            :style="{ '--chip-accent': s.color }"
          >
            <el-icon :size="13"><component :is="s.icon" /></el-icon>
            <span class="nc-chip__value">{{ s.value }}</span>
            <span class="nc-chip__label">{{ s.label }}</span>
          </div>
        </div>
        <el-button :icon="Refresh" circle size="small" class="nc-top__refresh" :loading="pageLoading" @click="loadAll" />
      </div>
      <nav class="nc-top__tabs" aria-label="通知センタータブ">
        <button
          v-for="tab in tabs"
          :key="tab.name"
          type="button"
          class="nc-tab"
          :class="{ 'nc-tab--active': activeTab === tab.name }"
          @click="activeTab = tab.name"
        >
          <el-icon :size="14"><component :is="tab.icon" /></el-icon>
          {{ tab.label }}
          <span v-if="tab.badge" class="nc-tab__badge">{{ tab.badge }}</span>
        </button>
      </nav>
    </header>

    <!-- イベント通知 -->
    <section v-show="activeTab === 'events'" class="nc-panel">
      <div class="nc-panel__head">
        <h2 class="nc-panel__title">
          イベント通知設定
          <span class="nc-panel__sub">各イベントの通知チャネルと有効状態</span>
        </h2>
      </div>
      <div class="nc-event-grid">
        <article v-for="row in notifications" :key="row.id" class="nc-event-card" :class="{ 'nc-event-card--off': !row.is_active }">
          <div class="nc-event-card__top">
            <div class="nc-event-card__title-wrap">
              <span class="nc-event-card__code">{{ row.event_code }}</span>
              <h3 class="nc-event-card__name">{{ row.event_name }}</h3>
            </div>
            <el-switch
              v-model="row.is_active"
              :disabled="!isAdmin"
              size="small"
              inline-prompt
              active-text="ON"
              inactive-text="OFF"
              @change="(v) => patchNotification(row, { is_active: v })"
            />
          </div>
          <p class="nc-event-card__desc">{{ row.description || '—' }}</p>
          <div class="nc-event-card__channels">
            <label
              v-for="ch in channelDefs"
              :key="ch.key"
              class="nc-channel"
              :class="[`nc-channel--${ch.key}`, { 'nc-channel--on': row[ch.field] }]"
            >
              <el-switch
                v-model="row[ch.field]"
                :disabled="!isAdmin"
                size="small"
                @change="(v) => patchNotification(row, { [ch.field]: v })"
              />
              <span>{{ ch.label }}</span>
            </label>
          </div>
          <div class="nc-event-card__footer">
            <span class="nc-recipient-count">
              <el-icon><User /></el-icon>
              受信者 {{ recipientCountByEvent(row.event_code) }} 名
            </span>
            <el-button size="small" text type="primary" @click="goRecipients(row.event_code)">受信者を編集</el-button>
          </div>
        </article>
      </div>
      <el-empty v-if="!notifications.length && !pageLoading" description="通知設定がありません" />
    </section>

    <!-- メール受信者 -->
    <section v-show="activeTab === 'recipients'" class="nc-panel">
      <div class="nc-panel__head">
        <h2 class="nc-panel__title">
          メール受信者
          <span class="nc-panel__sub">ユーザ・ロール・メール・LINE 送信先</span>
        </h2>
        <div class="nc-panel__actions">
          <el-select v-model="recipientEventFilter" clearable placeholder="イベント絞込" style="width: 180px" size="small">
            <el-option v-for="ev in notifications" :key="ev.event_code" :label="ev.event_name" :value="ev.event_code" />
          </el-select>
          <el-button v-if="isAdmin" type="primary" size="small" :icon="Plus" @click="openRecipientDialog()">追加</el-button>
        </div>
      </div>
      <div class="nc-table-wrap">
        <el-table :data="filteredRecipients" stripe size="small" class="nc-table" empty-text="受信者が登録されていません">
          <el-table-column label="イベント" min-width="160">
            <template #default="{ row }">
              <div class="nc-cell-event">
                <span class="nc-cell-event__name">{{ eventName(row.event_code) }}</span>
                <span class="nc-cell-event__code">{{ row.event_code }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="種別" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="recipientTypeTag(row.recipient_type)">{{ recipientTypeLabel(row.recipient_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="送信先" min-width="200">
            <template #default="{ row }">{{ recipientDisplay(row) }}</template>
          </el-table-column>
          <el-table-column prop="machine_cd" label="設備" width="100">
            <template #default="{ row }">{{ row.machine_cd || '—' }}</template>
          </el-table-column>
          <el-table-column label="有効" width="80" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                :disabled="!isAdmin"
                size="small"
                @change="(v) => patchRecipient(row, { is_active: v })"
              />
            </template>
          </el-table-column>
          <el-table-column v-if="isAdmin" label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openRecipientDialog(row)">編集</el-button>
              <el-button link type="danger" size="small" @click="removeRecipient(row)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <!-- メールテンプレート -->
    <section v-show="activeTab === 'templates'" class="nc-panel">
      <div class="nc-panel__head">
        <h2 class="nc-panel__title">
          メールテンプレート
          <span class="nc-panel__sub">プレースホルダ <code>{変数名}</code> で差し込み</span>
        </h2>
        <el-button v-if="isAdmin" type="primary" size="small" :icon="Plus" @click="openTemplateDialog()">追加</el-button>
      </div>
      <div class="nc-template-grid">
        <article v-for="tpl in emailTemplates" :key="tpl.id" class="nc-template-card">
          <div class="nc-template-card__head">
            <el-tag size="small" effect="plain">{{ tpl.code }}</el-tag>
            <el-switch
              v-if="isAdmin"
              v-model="tpl.is_active"
              size="small"
              @change="(v) => patchTemplate(tpl, { is_active: v })"
            />
          </div>
          <h3 class="nc-template-card__name">{{ tpl.name }}</h3>
          <p class="nc-template-card__subject">{{ tpl.subject }}</p>
          <div class="nc-template-card__meta">
            <el-tag size="small" type="info">{{ tpl.language }}</el-tag>
            <span v-if="tpl.event_code">{{ eventName(tpl.event_code) }}</span>
          </div>
          <div class="nc-template-card__actions">
            <el-button size="small" :icon="View" @click="previewTemplate(tpl)">プレビュー</el-button>
            <el-button v-if="isAdmin" size="small" type="primary" plain @click="openTemplateDialog(tpl)">編集</el-button>
            <el-button v-if="isAdmin" size="small" type="danger" plain @click="removeTemplate(tpl)">削除</el-button>
          </div>
        </article>
      </div>
      <el-empty v-if="!emailTemplates.length && !pageLoading" description="テンプレートがありません" />
    </section>

    <!-- 外部連携 -->
    <section v-show="activeTab === 'integration'" class="nc-panel">
      <div class="nc-panel__head">
        <h2 class="nc-panel__title">
          外部連携
          <span class="nc-panel__sub">SMTP・Slack・LINE 接続とテスト送信</span>
        </h2>
      </div>
      <div class="nc-integration-grid">
        <!-- SMTP -->
        <article class="nc-int-card nc-int-card--smtp">
          <div class="nc-int-card__header">
            <div class="nc-int-card__brand">
              <div class="nc-int-card__logo nc-int-card__logo--smtp"><el-icon :size="22"><Message /></el-icon></div>
              <div>
                <h3>SMTP（メール）</h3>
                <span class="nc-int-card__status" :class="smtpConfig.is_enabled ? 'is-on' : 'is-off'">
                  {{ smtpConfig.is_enabled ? '有効' : '無効' }}
                </span>
              </div>
            </div>
            <el-switch v-model="smtpConfig.is_enabled" :disabled="!isAdmin" @change="saveSmtp" />
          </div>
          <el-form label-position="top" size="small" class="nc-int-form" :disabled="!isAdmin">
            <el-row :gutter="8">
              <el-col :span="14"><el-form-item label="ホスト"><el-input v-model="smtpForm.host" placeholder="smtp.example.com" /></el-form-item></el-col>
              <el-col :span="10"><el-form-item label="ポート"><el-input-number v-model="smtpForm.port" :min="1" :max="65535" controls-position="right" style="width:100%" /></el-form-item></el-col>
            </el-row>
            <el-form-item label="ユーザー名"><el-input v-model="smtpForm.username" autocomplete="off" /></el-form-item>
            <el-form-item label="パスワード"><el-input v-model="smtpForm.password" type="password" show-password autocomplete="new-password" /></el-form-item>
            <el-form-item label="送信元アドレス"><el-input v-model="smtpForm.from_address" placeholder="noreply@example.com" /></el-form-item>
            <el-form-item label="テスト送信先"><el-input v-model="smtpForm.test_email" placeholder="テストメールの宛先" /></el-form-item>
            <el-form-item>
              <el-checkbox v-model="smtpForm.use_tls">TLS を使用</el-checkbox>
            </el-form-item>
          </el-form>
          <div class="nc-int-card__footer">
            <span v-if="smtpConfig.last_test_at" class="nc-int-card__test">
              最終テスト: {{ formatDateTime(smtpConfig.last_test_at) }}
              <el-tag size="small" :type="smtpConfig.last_test_result === 'success' ? 'success' : 'danger'">{{ smtpConfig.last_test_result || '—' }}</el-tag>
            </span>
            <div class="nc-int-card__btns">
              <el-button v-if="isAdmin" type="primary" size="small" :loading="savingSmtp" @click="saveSmtp">保存</el-button>
              <el-button size="small" :loading="testingSmtp" :disabled="!smtpConfig.is_enabled" @click="testSmtp">テスト</el-button>
            </div>
          </div>
        </article>

        <!-- Slack -->
        <article class="nc-int-card">
          <div class="nc-int-card__header">
            <div class="nc-int-card__brand">
              <div class="nc-int-card__logo nc-int-card__logo--slack">
                <img src="https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png" alt="" />
              </div>
              <div>
                <h3>Slack</h3>
                <span class="nc-int-card__status" :class="slackConfig.is_enabled ? 'is-on' : 'is-off'">{{ slackConfig.is_enabled ? '有効' : '無効' }}</span>
              </div>
            </div>
            <el-switch v-model="slackConfig.is_enabled" :disabled="!isAdmin" @change="saveSlack" />
          </div>
          <el-form label-position="top" size="small" class="nc-int-form" :disabled="!isAdmin">
            <el-form-item label="Webhook URL"><el-input v-model="slackForm.webhook_url" placeholder="https://hooks.slack.com/..." show-password /></el-form-item>
            <el-form-item label="チャンネル"><el-input v-model="slackForm.channel" placeholder="#notifications" /></el-form-item>
          </el-form>
          <div class="nc-int-card__footer">
            <div class="nc-int-card__btns">
              <el-button v-if="isAdmin" type="primary" size="small" :loading="savingSlack" @click="saveSlack">保存</el-button>
              <el-button size="small" :loading="testingSlack" @click="testSlack">テスト</el-button>
            </div>
          </div>
        </article>

        <!-- LINE -->
        <article class="nc-int-card">
          <div class="nc-int-card__header">
            <div class="nc-int-card__brand">
              <div class="nc-int-card__logo nc-int-card__logo--line">
                <img src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg" alt="" />
              </div>
              <div>
                <h3>LINE</h3>
                <span class="nc-int-card__status" :class="lineConfig.is_enabled ? 'is-on' : 'is-off'">{{ lineConfig.is_enabled ? '有効' : '無効' }}</span>
              </div>
            </div>
            <el-switch v-model="lineConfig.is_enabled" :disabled="!isAdmin" @change="saveLine" />
          </div>
          <el-form label-position="top" size="small" class="nc-int-form" :disabled="!isAdmin">
            <el-form-item label="Channel Token"><el-input v-model="lineForm.channel_token" show-password /></el-form-item>
            <el-form-item label="Channel Secret"><el-input v-model="lineForm.channel_secret" show-password /></el-form-item>
            <el-form-item label="テスト送信先 User ID">
              <el-input v-model="lineForm.test_line_user_id" placeholder="Uxxxxxxxx（友だち追加済みユーザーの LINE User ID）" />
            </el-form-item>
            <p class="nc-line-hint">※ 入力後は必ず「保存」を押してください（DB に永続化）。再読み込み後はセキュリティのためマスク表示されますが、保存済みの値は保持されます。</p>
            <p class="nc-line-hint">Webhook URL（User ID 収集）: <code>{{ lineWebhookUrl }}</code> — LINE Developers に登録後、友だち追加・メッセージ送信でバックエンドログに userId が出力されます。</p>
          </el-form>
          <div class="nc-int-card__footer">
            <div class="nc-int-card__btns">
              <el-button v-if="isAdmin" type="primary" size="small" :loading="savingLine" @click="saveLine">保存</el-button>
              <el-button size="small" :loading="testingLine" @click="testLine">テスト</el-button>
            </div>
          </div>
        </article>
      </div>
    </section>

  <!-- 受信者ダイアログ -->
  <el-dialog v-model="recipientDialogVisible" :title="recipientEditing ? '受信者編集' : '受信者追加'" width="480px" destroy-on-close class="nc-dialog">
    <el-form ref="recipientFormRef" :model="recipientForm" :rules="recipientRules" label-width="110px">
      <el-form-item label="イベント" prop="event_code">
        <el-select v-model="recipientForm.event_code" placeholder="選択" style="width:100%" :disabled="!!recipientEditing">
          <el-option v-for="ev in notifications" :key="ev.event_code" :label="`${ev.event_name} (${ev.event_code})`" :value="ev.event_code" />
        </el-select>
      </el-form-item>
      <el-form-item label="種別" prop="recipient_type">
        <el-radio-group v-model="recipientForm.recipient_type">
          <el-radio value="user">ユーザー</el-radio>
          <el-radio value="role">ロール</el-radio>
          <el-radio value="email">メール</el-radio>
          <el-radio value="line">LINE</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item v-if="recipientForm.recipient_type === 'user'" label="ユーザー" prop="user_id">
        <el-select v-model="recipientForm.user_id" filterable placeholder="ユーザーを選択" style="width:100%">
          <el-option v-for="u in users" :key="u.id" :label="`${u.full_name || u.username} (${u.email})`" :value="u.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="recipientForm.recipient_type === 'role'" label="ロール" prop="role">
        <el-select v-model="recipientForm.role" placeholder="ロールを選択" style="width:100%">
          <el-option v-for="r in ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
        </el-select>
      </el-form-item>
      <template v-if="recipientForm.recipient_type === 'email'">
        <el-form-item label="メール" prop="email">
          <el-input v-model="recipientForm.email" placeholder="example@company.com" />
        </el-form-item>
        <el-form-item label="表示名">
          <el-input v-model="recipientForm.display_name" placeholder="任意" />
        </el-form-item>
      </template>
      <template v-if="recipientForm.recipient_type === 'line'">
        <el-form-item label="LINE User ID" prop="line_user_id">
          <el-input v-model="recipientForm.line_user_id" placeholder="U で始まる33文字（例: U1234...）" />
        </el-form-item>
        <p class="nc-line-hint">※ LINE 表示名・電話番号は不可。友だち追加後に Webhook 等で取得した User ID を登録してください。</p>
        <el-form-item label="表示名">
          <el-input v-model="recipientForm.display_name" placeholder="任意（例：生産管理部 田中）" />
        </el-form-item>
      </template>
      <el-form-item label="設備コード">
        <el-input v-model="recipientForm.machine_cd" placeholder="任意（将来拡張）" />
      </el-form-item>
      <el-form-item label="有効">
        <el-switch v-model="recipientForm.is_active" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="recipientDialogVisible = false">キャンセル</el-button>
      <el-button type="primary" :loading="recipientSubmitting" @click="submitRecipient">保存</el-button>
    </template>
  </el-dialog>

  <!-- テンプレートダイアログ -->
  <el-dialog v-model="templateDialogVisible" :title="templateEditing ? 'テンプレート編集' : 'テンプレート追加'" width="640px" destroy-on-close class="nc-dialog">
    <el-form ref="templateFormRef" :model="templateForm" :rules="templateRules" label-width="100px">
      <el-form-item label="コード" prop="code">
        <el-input v-model="templateForm.code" :disabled="!!templateEditing" placeholder="CUTTING_ACTUAL_CONFIRMED" />
      </el-form-item>
      <el-form-item label="名前" prop="name"><el-input v-model="templateForm.name" /></el-form-item>
      <el-form-item label="イベント">
        <el-select v-model="templateForm.event_code" clearable placeholder="任意" style="width:100%">
          <el-option v-for="ev in notifications" :key="ev.event_code" :label="ev.event_name" :value="ev.event_code" />
        </el-select>
      </el-form-item>
      <el-form-item label="件名" prop="subject"><el-input v-model="templateForm.subject" /></el-form-item>
      <el-form-item label="本文" prop="body">
        <el-input v-model="templateForm.body" type="textarea" :rows="8" placeholder="HTML 可。{production_day} など" />
      </el-form-item>
      <el-form-item label="言語"><el-input v-model="templateForm.language" style="width:120px" /></el-form-item>
      <el-form-item v-if="templateEditing" label="有効"><el-switch v-model="templateForm.is_active" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="templateDialogVisible = false">キャンセル</el-button>
      <el-button type="primary" :loading="templateSubmitting" @click="submitTemplate">保存</el-button>
    </template>
  </el-dialog>

  <!-- プレビュー -->
  <el-drawer v-model="previewVisible" title="テンプレートプレビュー" size="480px" class="nc-preview-drawer">
    <div v-if="previewTpl" class="nc-preview">
      <div class="nc-preview__field"><label>件名</label><p>{{ previewSubject }}</p></div>
      <div class="nc-preview__field"><label>本文</label><div class="nc-preview__body" v-html="previewBody" /></div>
      <div v-if="previewTpl.variables?.length" class="nc-preview__vars">
        <label>利用可能変数</label>
        <div class="nc-preview__var-list">
          <el-tag v-for="v in previewTpl.variables" :key="v" size="small" effect="plain">{{ formatTemplateVar(v) }}</el-tag>
        </div>
      </div>
    </div>
  </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Bell, Refresh, Plus, User, View, Message, Connection, Document, Setting,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/modules/auth/stores/user'
import {
  getNotificationSettings,
  updateNotificationSetting,
  getEmailTemplates,
  createEmailTemplate,
  updateEmailTemplate,
  deleteEmailTemplate,
  getNotificationRecipients,
  createNotificationRecipient,
  updateNotificationRecipient,
  deleteNotificationRecipient,
  getIntegrationConfig,
  updateIntegrationConfig,
  testIntegration,
  getUsers,
  type NotificationSettingItem,
  type NotificationSettingUpdateParams,
  type EmailTemplateItem,
  type NotificationRecipientItem,
  type IntegrationConfigItem,
  type UserListItem,
} from '@/api/system'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.user?.role === 'admin')

const lineWebhookUrl = computed(() => {
  if (typeof window === 'undefined') return '/api/line/webhook'
  return `${window.location.origin}/api/line/webhook`
})

const pageLoading = ref(false)
const activeTab = ref('events')

const tabs = computed(() => [
  { name: 'events', label: 'イベント通知', icon: Bell, badge: notifications.value.length || undefined },
  { name: 'recipients', label: 'メール受信者', icon: User, badge: recipients.value.length || undefined },
  { name: 'templates', label: 'テンプレート', icon: Document, badge: emailTemplates.value.length || undefined },
  { name: 'integration', label: '外部連携', icon: Connection },
])

const notifications = ref<NotificationSettingItem[]>([])
const emailTemplates = ref<EmailTemplateItem[]>([])
const recipients = ref<NotificationRecipientItem[]>([])
const users = ref<UserListItem[]>([])

const recipientEventFilter = ref('')

const smtpConfig = ref<IntegrationConfigItem>({ id: 0, service_type: 'smtp', config: {}, is_enabled: false, last_test_at: null, last_test_result: null, created_at: '', updated_at: '' })
const slackConfig = ref<IntegrationConfigItem>({ id: 0, service_type: 'slack', config: {}, is_enabled: false, last_test_at: null, last_test_result: null, created_at: '', updated_at: '' })
const lineConfig = ref<IntegrationConfigItem>({ id: 0, service_type: 'line', config: {}, is_enabled: false, last_test_at: null, last_test_result: null, created_at: '', updated_at: '' })

const smtpForm = reactive({ host: '', port: 587, username: '', password: '', from_address: '', test_email: '', use_tls: true })
const slackForm = reactive({ webhook_url: '', channel: '#notifications' })
const lineForm = reactive({ channel_token: '', channel_secret: '', test_line_user_id: '' })

const savingSmtp = ref(false)
const testingSmtp = ref(false)
const savingSlack = ref(false)
const testingSlack = ref(false)
const savingLine = ref(false)
const testingLine = ref(false)

const ROLE_OPTIONS = [
  { value: 'admin', label: '管理者' },
  { value: 'manager', label: 'マネージャー' },
  { value: 'user', label: '一般ユーザー' },
  { value: 'worker', label: '作業者' },
  { value: 'viewer', label: '閲覧者' },
  { value: 'guest', label: 'ゲスト' },
]

const PREVIEW_SAMPLE: Record<string, string> = {
  production_day: '2026-06-16',
  inserted_count: '12',
  total_quantity: '1,234',
  confirmed_by: '山田太郎',
  confirmed_at: '2026-06-16 18:30',
  machine_summary: '<p>設備別内訳（サンプル）</p>',
  document_type: '発注書',
  document_no: 'PO-2026-001',
  approver_name: '鈴木花子',
  requester_name: '田中一郎',
  amount: '¥120,000',
  user_name: '佐藤次郎',
  username: 'sato',
  initial_password: '********',
}

const statCards = computed(() => [
  { key: 'events', label: '有効イベント', value: notifications.value.filter((n) => n.is_active).length, icon: Bell, color: '#6366f1' },
  { key: 'email', label: 'メール有効', value: notifications.value.filter((n) => n.email_enabled).length, icon: Message, color: '#10b981' },
  { key: 'recipients', label: '受信者', value: recipients.value.filter((r) => r.is_active).length, icon: User, color: '#f59e0b' },
  { key: 'smtp', label: 'SMTP', value: smtpConfig.value.is_enabled ? 'ON' : 'OFF', icon: Setting, color: '#8b5cf6' },
])

type ChannelField = 'in_app_enabled' | 'email_enabled' | 'slack_enabled' | 'line_enabled'
const channelDefs: { key: string; field: ChannelField; label: string }[] = [
  { key: 'app', field: 'in_app_enabled', label: 'アプリ内' },
  { key: 'email', field: 'email_enabled', label: 'メール' },
  { key: 'slack', field: 'slack_enabled', label: 'Slack' },
  { key: 'line', field: 'line_enabled', label: 'LINE' },
]

const filteredRecipients = computed(() => {
  if (!recipientEventFilter.value) return recipients.value
  return recipients.value.filter((r) => r.event_code === recipientEventFilter.value)
})

const usersById = computed(() => Object.fromEntries(users.value.map((u) => [u.id, u])))

function eventName(code: string) {
  return notifications.value.find((n) => n.event_code === code)?.event_name || code
}

function recipientCountByEvent(code: string) {
  return recipients.value.filter((r) => r.event_code === code && r.is_active).length
}

function recipientTypeLabel(t: string) {
  return ({ user: 'ユーザー', role: 'ロール', email: 'メール', line: 'LINE' } as Record<string, string>)[t] || t
}

function recipientTypeTag(t: string) {
  return ({ user: 'primary', role: 'warning', email: 'success', line: 'danger' } as Record<string, string>)[t] || 'info'
}

function recipientDisplay(row: NotificationRecipientItem) {
  if (row.recipient_type === 'line' && row.line_user_id) {
    return row.display_name ? `${row.display_name} (${row.line_user_id})` : row.line_user_id
  }
  if (row.recipient_type === 'user' && row.user_id) {
    const u = usersById.value[row.user_id]
    return u ? `${u.full_name || u.username} <${u.email}>` : `user#${row.user_id}`
  }
  if (row.recipient_type === 'role') return `ロール: ${row.role}`
  return row.display_name ? `${row.display_name} <${row.email}>` : row.email || '—'
}

function formatDateTime(iso: string | null) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('ja-JP')
  } catch {
    return iso
  }
}

function formatTemplateVar(name: string) {
  return `{${name}}`
}

function renderPreview(text: string) {
  return text.replace(/\{(\w+)\}/g, (_, key) => PREVIEW_SAMPLE[key] ?? `{${key}}`)
}

function goRecipients(eventCode: string) {
  recipientEventFilter.value = eventCode
  activeTab.value = 'recipients'
}

async function loadAll() {
  pageLoading.value = true
  try {
    const [notif, tpls, recs, userRes, smtp, slack, line] = await Promise.all([
      getNotificationSettings(),
      getEmailTemplates(),
      getNotificationRecipients(),
      getUsers({ page: 1, page_size: 500 }),
      getIntegrationConfig('smtp'),
      getIntegrationConfig('slack'),
      getIntegrationConfig('line'),
    ])
    notifications.value = notif
    emailTemplates.value = tpls
    recipients.value = recs
    users.value = userRes.items || []
    applyIntegrationConfig(smtp, smtpForm, smtpConfig)
    applyIntegrationConfig(slack, slackForm, slackConfig)
    applyIntegrationConfig(line, lineForm, lineConfig)
    if (!smtpForm.test_email && userStore.user?.email) {
      smtpForm.test_email = userStore.user.email
    }
  } catch (e) {
    ElMessage.error('通知設定の読み込みに失敗しました')
    console.error(e)
  } finally {
    pageLoading.value = false
  }
}

function applyIntegrationConfig(
  data: IntegrationConfigItem,
  form: Record<string, unknown>,
  target: { value: IntegrationConfigItem }
) {
  target.value = data
  const cfg = data.config || {}
  Object.keys(form).forEach((k) => {
    if (k in cfg) (form as Record<string, unknown>)[k] = cfg[k]
  })
}

async function patchNotification(row: NotificationSettingItem, patch: NotificationSettingUpdateParams) {
  if (!isAdmin.value) return
  try {
    await updateNotificationSetting(row.id, patch)
    ElMessage.success('保存しました')
  } catch {
    ElMessage.error('保存に失敗しました')
    await loadAll()
  }
}

// ---- Recipients ----
const recipientDialogVisible = ref(false)
const recipientEditing = ref<NotificationRecipientItem | null>(null)
const recipientSubmitting = ref(false)
const recipientFormRef = ref<FormInstance>()
const recipientForm = reactive({
  event_code: '',
  recipient_type: 'user' as 'user' | 'email' | 'role' | 'line',
  user_id: null as number | null,
  email: '',
  line_user_id: '',
  role: '',
  machine_cd: '',
  display_name: '',
  is_active: true,
})

const recipientRules: FormRules = {
  event_code: [{ required: true, message: 'イベントを選択', trigger: 'change' }],
  recipient_type: [{ required: true, message: '種別を選択', trigger: 'change' }],
  line_user_id: [
    { required: true, message: 'LINE User ID を入力', trigger: 'blur' },
    {
      pattern: /^U[a-fA-F0-9]{32}$/,
      message: 'U で始まる33文字の LINE User ID を入力してください',
      trigger: 'blur',
    },
  ],
}

function openRecipientDialog(row?: NotificationRecipientItem) {
  recipientEditing.value = row || null
  recipientForm.event_code = row?.event_code || recipientEventFilter.value || ''
  recipientForm.recipient_type = row?.recipient_type || 'user'
  recipientForm.user_id = row?.user_id ?? null
  recipientForm.email = row?.email || ''
  recipientForm.line_user_id = row?.line_user_id || ''
  recipientForm.role = row?.role || ''
  recipientForm.machine_cd = row?.machine_cd || ''
  recipientForm.display_name = row?.display_name || ''
  recipientForm.is_active = row?.is_active ?? true
  recipientDialogVisible.value = true
}

async function submitRecipient() {
  const valid = await recipientFormRef.value?.validate().catch(() => false)
  if (!valid) return
  recipientSubmitting.value = true
  try {
    const payload = {
      event_code: recipientForm.event_code,
      recipient_type: recipientForm.recipient_type,
      user_id: recipientForm.recipient_type === 'user' ? recipientForm.user_id : null,
      email: recipientForm.recipient_type === 'email' ? recipientForm.email : null,
      line_user_id: recipientForm.recipient_type === 'line' ? recipientForm.line_user_id : null,
      role: recipientForm.recipient_type === 'role' ? recipientForm.role : null,
      machine_cd: recipientForm.machine_cd || null,
      display_name: recipientForm.display_name || null,
      is_active: recipientForm.is_active,
    }
    if (recipientEditing.value) {
      await updateNotificationRecipient(recipientEditing.value.id, payload)
    } else {
      await createNotificationRecipient(payload)
    }
    ElMessage.success('保存しました')
    recipientDialogVisible.value = false
    recipients.value = await getNotificationRecipients()
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '保存に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    recipientSubmitting.value = false
  }
}

async function patchRecipient(row: NotificationRecipientItem, patch: Partial<NotificationRecipientItem>) {
  if (!isAdmin.value) return
  try {
    await updateNotificationRecipient(row.id, patch)
  } catch {
    ElMessage.error('更新に失敗しました')
    recipients.value = await getNotificationRecipients()
  }
}

async function removeRecipient(row: NotificationRecipientItem) {
  await ElMessageBox.confirm(`この受信者を削除しますか？\n${recipientDisplay(row)}`, '確認', { type: 'warning' })
  try {
    await deleteNotificationRecipient(row.id)
    ElMessage.success('削除しました')
    recipients.value = await getNotificationRecipients()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

// ---- Templates ----
const templateDialogVisible = ref(false)
const templateEditing = ref<EmailTemplateItem | null>(null)
const templateSubmitting = ref(false)
const templateFormRef = ref<FormInstance>()
const templateForm = reactive({
  code: '',
  name: '',
  subject: '',
  body: '',
  event_code: '' as string | null,
  language: 'ja',
  is_active: true,
})

const templateRules: FormRules = {
  code: [{ required: true, message: 'コードを入力', trigger: 'blur' }],
  name: [{ required: true, message: '名前を入力', trigger: 'blur' }],
  subject: [{ required: true, message: '件名を入力', trigger: 'blur' }],
  body: [{ required: true, message: '本文を入力', trigger: 'blur' }],
}

function openTemplateDialog(tpl?: EmailTemplateItem) {
  templateEditing.value = tpl || null
  templateForm.code = tpl?.code || ''
  templateForm.name = tpl?.name || ''
  templateForm.subject = tpl?.subject || ''
  templateForm.body = tpl?.body || ''
  templateForm.event_code = tpl?.event_code || null
  templateForm.language = tpl?.language || 'ja'
  templateForm.is_active = tpl?.is_active ?? true
  templateDialogVisible.value = true
}

async function submitTemplate() {
  const valid = await templateFormRef.value?.validate().catch(() => false)
  if (!valid) return
  templateSubmitting.value = true
  try {
    if (templateEditing.value) {
      await updateEmailTemplate(templateEditing.value.id, {
        name: templateForm.name,
        subject: templateForm.subject,
        body: templateForm.body,
        event_code: templateForm.event_code || null,
        language: templateForm.language,
        is_active: templateForm.is_active,
      })
    } else {
      await createEmailTemplate({
        code: templateForm.code,
        name: templateForm.name,
        subject: templateForm.subject,
        body: templateForm.body,
        event_code: templateForm.event_code || null,
        language: templateForm.language,
      })
    }
    ElMessage.success('保存しました')
    templateDialogVisible.value = false
    emailTemplates.value = await getEmailTemplates()
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '保存に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    templateSubmitting.value = false
  }
}

async function patchTemplate(tpl: EmailTemplateItem, patch: { is_active?: boolean }) {
  if (!isAdmin.value) return
  try {
    await updateEmailTemplate(tpl.id, patch)
  } catch {
    ElMessage.error('更新に失敗しました')
    emailTemplates.value = await getEmailTemplates()
  }
}

async function removeTemplate(tpl: EmailTemplateItem) {
  await ElMessageBox.confirm(`テンプレート「${tpl.name}」を削除しますか？`, '確認', { type: 'warning' })
  try {
    await deleteEmailTemplate(tpl.id)
    ElMessage.success('削除しました')
    emailTemplates.value = await getEmailTemplates()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

const previewVisible = ref(false)
const previewTpl = ref<EmailTemplateItem | null>(null)
const previewSubject = computed(() => (previewTpl.value ? renderPreview(previewTpl.value.subject) : ''))
const previewBody = computed(() => (previewTpl.value ? renderPreview(previewTpl.value.body) : ''))

function previewTemplate(tpl: EmailTemplateItem) {
  previewTpl.value = tpl
  previewVisible.value = true
}

// ---- Integrations ----
async function saveSmtp() {
  if (!isAdmin.value) return
  savingSmtp.value = true
  try {
    smtpConfig.value = await updateIntegrationConfig('smtp', {
      is_enabled: smtpConfig.value.is_enabled,
      config: { ...smtpForm },
    })
    ElMessage.success('SMTP 設定を保存しました')
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    savingSmtp.value = false
  }
}

async function testSmtp() {
  testingSmtp.value = true
  try {
    if (isAdmin.value) {
      smtpConfig.value = await updateIntegrationConfig('smtp', {
        is_enabled: smtpConfig.value.is_enabled,
        config: { ...smtpForm },
      })
    }
    const res = await testIntegration('smtp')
    ElMessage.success(res.message)
    smtpConfig.value = await getIntegrationConfig('smtp')
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'テスト送信に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    testingSmtp.value = false
  }
}

async function saveSlack() {
  if (!isAdmin.value) return
  savingSlack.value = true
  try {
    slackConfig.value = await updateIntegrationConfig('slack', { is_enabled: slackConfig.value.is_enabled, config: { ...slackForm } })
    ElMessage.success('Slack 設定を保存しました')
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    savingSlack.value = false
  }
}

async function testSlack() {
  testingSlack.value = true
  try {
    const res = await testIntegration('slack')
    ElMessage.success(res.message)
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'テスト送信に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    testingSlack.value = false
  }
}

async function saveLine() {
  if (!isAdmin.value) return
  savingLine.value = true
  try {
    const saved = await updateIntegrationConfig('line', { is_enabled: lineConfig.value.is_enabled, config: { ...lineForm } })
    applyIntegrationConfig(saved, lineForm, lineConfig)
    ElMessage.success('LINE 設定を保存しました')
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    savingLine.value = false
  }
}

async function testLine() {
  const uid = (lineForm.test_line_user_id || '').trim()
  if (!/^U[a-fA-F0-9]{32}$/.test(uid)) {
    ElMessage.warning('テスト送信先は U で始まる33文字の LINE User ID を入力し、保存してください')
    return
  }
  if (!lineForm.channel_token?.trim()) {
    ElMessage.warning('Channel Token を入力して保存してください')
    return
  }
  testingLine.value = true
  try {
    if (isAdmin.value) {
      lineConfig.value = await updateIntegrationConfig('line', {
        is_enabled: lineConfig.value.is_enabled,
        config: { ...lineForm },
      })
    }
    const res = await testIntegration('line')
    ElMessage.success(res.message)
    applyIntegrationConfig(await getIntegrationConfig('line'), lineForm, lineConfig)
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'テスト送信に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    testingLine.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.nc-page {
  --nc-accent: #6366f1;
  --nc-accent-2: #8b5cf6;
  --nc-border: #e2e8f0;
  --nc-surface: #fff;
  --nc-muted: #64748b;
  padding: 8px 12px 16px;
  max-width: 1360px;
  margin: 0 auto;
}

/* ---- 顶部一体化 ---- */
.nc-top {
  margin-bottom: 10px;
  border-radius: 12px;
  background: var(--nc-surface);
  border: 1px solid var(--nc-border);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(99, 102, 241, 0.06);
  overflow: hidden;
}

.nc-top__bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #f8faff 0%, #faf5ff 50%, #fdf4ff 100%);
  border-bottom: 1px solid color-mix(in srgb, var(--nc-accent) 10%, transparent);
}

.nc-top__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.nc-top__icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--nc-accent), var(--nc-accent-2));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--nc-accent) 30%, transparent);
}

.nc-top__titles {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nc-top__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #1e1b4b;
  line-height: 1.2;
}

.nc-top__desc {
  font-size: 0.7rem;
  color: var(--nc-muted);
  line-height: 1.3;
}

.nc-top__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
  min-width: 0;
  justify-content: center;
}

.nc-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid color-mix(in srgb, var(--chip-accent) 18%, transparent);
  color: var(--chip-accent);
  font-size: 0.7rem;
  white-space: nowrap;
  backdrop-filter: blur(4px);
}

.nc-chip__value {
  font-weight: 700;
  font-size: 0.8rem;
  color: #0f172a;
}

.nc-chip__label {
  color: var(--nc-muted);
}

.nc-top__refresh {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.9);
}

.nc-top__tabs {
  display: flex;
  gap: 2px;
  padding: 4px 8px;
  background: #f8fafc;
  overflow-x: auto;
}

.nc-tab {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--nc-muted);
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.nc-tab:hover {
  color: #334155;
  background: rgba(255, 255, 255, 0.7);
}

.nc-tab--active {
  background: #fff;
  color: var(--nc-accent);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
  font-weight: 600;
}

.nc-tab__badge {
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--nc-accent) 14%, transparent);
  color: var(--nc-accent);
  font-size: 0.65rem;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
}

/* ---- 面板 ---- */
.nc-panel {
  background: var(--nc-surface);
  border-radius: 12px;
  border: 1px solid var(--nc-border);
  padding: 12px 14px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

.nc-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.nc-panel__title {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.nc-panel__sub {
  font-size: 0.7rem;
  font-weight: 400;
  color: var(--nc-muted);
}

.nc-panel__sub code {
  padding: 0 4px;
  border-radius: 3px;
  background: #f1f5f9;
  font-size: 0.68rem;
}

.nc-panel__actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

/* ---- イベント卡片 ---- */
.nc-event-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 8px;
}

.nc-event-card {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--nc-border);
  background: #fff;
  border-left: 3px solid var(--nc-accent);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.nc-event-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.nc-event-card--off {
  opacity: 0.6;
  border-left-color: #cbd5e1;
}

.nc-event-card__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 4px;
}

.nc-event-card__code {
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: #94a3b8;
  text-transform: uppercase;
}

.nc-event-card__name {
  margin: 1px 0 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.25;
}

.nc-event-card__desc {
  margin: 0 0 8px;
  font-size: 0.72rem;
  color: var(--nc-muted);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.nc-event-card__channels {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.nc-channel {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px 2px 4px;
  border-radius: 6px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  font-size: 0.68rem;
  color: #94a3b8;
  cursor: default;
  transition: all 0.15s;
}

.nc-channel--on {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}

.nc-channel--email.nc-channel--on { background: #ecfdf5; border-color: #a7f3d0; color: #047857; }
.nc-channel--slack.nc-channel--on { background: #fff7ed; border-color: #fed7aa; color: #c2410c; }
.nc-channel--line.nc-channel--on { background: #fef2f2; border-color: #fecaca; color: #b91c1c; }

.nc-channel :deep(.el-switch) {
  transform: scale(0.85);
  transform-origin: left center;
}

.nc-event-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 6px;
  border-top: 1px dashed #e2e8f0;
}

.nc-recipient-count {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.68rem;
  color: var(--nc-muted);
}

/* ---- 表格 ---- */
.nc-table-wrap {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--nc-border);
}

.nc-table :deep(.el-table__header th) {
  background: #f8fafc !important;
  font-weight: 600;
  font-size: 0.75rem;
  color: #475569;
  padding: 6px 0;
}

.nc-table :deep(.el-table__body td) {
  font-size: 0.78rem;
  padding: 4px 0;
}

.nc-cell-event__name {
  display: block;
  font-weight: 500;
  color: #1e293b;
  font-size: 0.78rem;
}

.nc-cell-event__code {
  font-size: 0.65rem;
  color: #94a3b8;
}

/* ---- テンプレート ---- */
.nc-template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 8px;
}

.nc-template-card {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--nc-border);
  display: flex;
  flex-direction: column;
  gap: 5px;
  transition: box-shadow 0.15s, border-color 0.15s;
}

.nc-template-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.nc-template-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nc-template-card__name {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
}

.nc-template-card__subject {
  margin: 0;
  font-size: 0.72rem;
  color: var(--nc-muted);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.nc-template-card__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.68rem;
  color: #94a3b8;
}

.nc-template-card__actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 4px;
}

/* ---- 外部連携 ---- */
.nc-integration-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

@media (max-width: 1100px) {
  .nc-integration-grid { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 720px) {
  .nc-integration-grid { grid-template-columns: 1fr; }
  .nc-top__bar { flex-wrap: wrap; }
  .nc-top__stats { justify-content: flex-start; }
}

.nc-int-card {
  border-radius: 10px;
  border: 1px solid var(--nc-border);
  padding: 10px 12px;
  background: #fff;
}

.nc-int-card--smtp {
  border-color: #c7d2fe;
  background: linear-gradient(180deg, #fafaff 0%, #fff 100%);
}

.nc-int-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.nc-int-card__brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nc-int-card__brand h3 {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 600;
}

.nc-int-card__logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  flex-shrink: 0;
}

.nc-int-card__logo img {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.nc-int-card__logo--smtp {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}

.nc-int-card__status {
  font-size: 0.65rem;
  font-weight: 600;
}

.nc-int-card__status.is-on { color: #059669; }
.nc-int-card__status.is-off { color: #94a3b8; }

.nc-int-form :deep(.el-form-item) {
  margin-bottom: 6px;
}

.nc-int-form :deep(.el-form-item__label) {
  font-size: 0.68rem;
  color: var(--nc-muted);
  padding-bottom: 0;
  line-height: 1.4;
}

.nc-int-card__footer {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.nc-int-card__test {
  font-size: 0.68rem;
  color: var(--nc-muted);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.nc-int-card__btns {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

/* ---- 预览 / 提示 ---- */
.nc-preview__field {
  margin-bottom: 14px;
}

.nc-preview__field label {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--nc-muted);
  margin-bottom: 4px;
}

.nc-preview__field p {
  margin: 0;
  font-size: 0.875rem;
  color: #1e293b;
}

.nc-preview__body {
  padding: 10px;
  border-radius: 6px;
  background: #f8fafc;
  border: 1px solid var(--nc-border);
  font-size: 0.8125rem;
  line-height: 1.5;
}

.nc-preview__var-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.nc-line-hint {
  margin: 0 0 6px;
  font-size: 0.68rem;
  color: var(--nc-muted);
  line-height: 1.4;
}
</style>
