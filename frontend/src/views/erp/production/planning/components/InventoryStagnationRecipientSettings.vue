<template>
  <div class="recipient-settings" v-loading="loading">
    <div class="recipient-settings__intro">
      <el-icon class="recipient-settings__intro-icon"><InfoFilled /></el-icon>
      <p class="recipient-settings__hint">
        工程ごとにメール・LINE の送信先を設定します。空欄（全工程）の受信者は全工程のアラートにも含まれます。
      </p>
    </div>

    <el-table :data="tableRows" stripe size="small" class="recipient-table" max-height="360">
      <el-table-column label="工程" width="120" fixed>
        <template #default="{ row }">
          <span class="process-label" :class="{ 'process-label--global': !row.inventory_column }">
            {{ row.process_label }}
          </span>
          <el-tag
            v-if="row.detected"
            size="small"
            type="primary"
            effect="plain"
            round
            class="detected-tag"
          >
            検出中
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="メール受信者" min-width="160">
        <template #default="{ row }">
          <span class="recipient-text">{{ formatEmailList(row.emailItems) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="LINE受信者" min-width="140">
        <template #default="{ row }">
          <span class="recipient-text recipient-text--line">{{ formatLineList(row.lineItems) }}</span>
        </template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="操作" width="100" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openAdd(row.inventory_column)">追加</el-button>
        </template>
      </el-table-column>
    </el-table>

    <p v-if="!isAdmin" class="recipient-settings__readonly">
      受信者の変更は管理者のみ可能です。通知センターでも設定できます。
    </p>

    <el-dialog
      v-model="formVisible"
      title="受信者追加"
      width="480px"
      append-to-body
      destroy-on-close
      align-center
      class="recipient-form-dialog"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="108px" size="default">
        <el-form-item label="対象工程">
          <el-select
            v-model="form.inventory_column"
            clearable
            placeholder="全工程（空欄）"
            style="width: 100%"
          >
            <el-option
              v-for="opt in INVENTORY_COLUMN_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="種別" prop="recipient_type">
          <el-radio-group v-model="form.recipient_type">
            <el-radio value="user">ユーザー</el-radio>
            <el-radio value="role">ロール</el-radio>
            <el-radio value="email">メール</el-radio>
            <el-radio value="line">LINE</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.recipient_type === 'user'" label="ユーザー" prop="user_id">
          <el-select v-model="form.user_id" filterable placeholder="選択" style="width: 100%">
            <el-option
              v-for="u in users"
              :key="u.id"
              :label="`${u.full_name || u.username} (${u.email})`"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.recipient_type === 'role'" label="ロール" prop="role">
          <el-select v-model="form.role" placeholder="選択" style="width: 100%">
            <el-option v-for="r in ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <template v-if="form.recipient_type === 'email'">
          <el-form-item label="メール" prop="email">
            <el-select
              v-model="form.email"
              filterable
              clearable
              placeholder="メールアドレスを選択"
              style="width: 100%"
              @change="handleEmailSelect"
            >
              <el-option
                v-for="opt in emailOptions"
                :key="opt.email"
                :label="opt.label"
                :value="opt.email"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="表示名">
            <el-input v-model="form.display_name" placeholder="任意（未入力時はユーザー名）" />
          </el-form-item>
        </template>
        <template v-if="form.recipient_type === 'line'">
          <el-form-item label="LINE User ID" prop="line_user_id">
            <el-input v-model="form.line_user_id" placeholder="U で始まる33文字" />
          </el-form-item>
          <el-form-item label="表示名">
            <el-input v-model="form.display_name" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/modules/auth/stores/user'
import {
  createNotificationRecipient,
  getNotificationRecipients,
  getUsers,
  type NotificationRecipientItem,
  type UserListItem,
} from '@/api/system'
import {
  INVENTORY_COLUMN_OPTIONS,
  INVENTORY_STAGNATION_EVENT,
  inventoryColumnLabel,
} from './inventoryStagnationConstants'

const props = defineProps<{
  active: boolean
  detectedColumns?: string[]
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

const userStore = useUserStore()
const isAdmin = computed(() => userStore.user?.role === 'admin')

const loading = ref(false)
const submitting = ref(false)
const recipients = ref<NotificationRecipientItem[]>([])
const users = ref<UserListItem[]>([])

const ROLE_OPTIONS = [
  { value: 'admin', label: '管理者' },
  { value: 'manager', label: 'マネージャー' },
  { value: 'user', label: '一般ユーザー' },
  { value: 'worker', label: '作業者' },
  { value: 'viewer', label: '閲覧者' },
  { value: 'guest', label: 'ゲスト' },
]

const emailOptions = computed(() => {
  const seen = new Set<string>()
  const opts: Array<{ email: string; label: string }> = []
  for (const u of users.value) {
    const email = (u.email || '').trim()
    if (!email || seen.has(email)) continue
    seen.add(email)
    opts.push({
      email,
      label: `${u.full_name || u.username} (${email})`,
    })
  }
  return opts.sort((a, b) => a.label.localeCompare(b.label, 'ja'))
})

const detectedSet = computed(() => new Set(props.detectedColumns || []))

interface RowView {
  inventory_column: string | null
  process_label: string
  detected: boolean
  emailItems: NotificationRecipientItem[]
  lineItems: NotificationRecipientItem[]
}

const tableRows = computed<RowView[]>(() => {
  const active = recipients.value.filter((r) => r.is_active)
  const rows: RowView[] = [
    {
      inventory_column: null,
      process_label: '全工程',
      detected: false,
      emailItems: scoped(active, null, 'email'),
      lineItems: scoped(active, null, 'line'),
    },
  ]
  for (const opt of INVENTORY_COLUMN_OPTIONS) {
    rows.push({
      inventory_column: opt.value,
      process_label: opt.label,
      detected: detectedSet.value.has(opt.value),
      emailItems: scoped(active, opt.value, 'email'),
      lineItems: scoped(active, opt.value, 'line'),
    })
  }
  return rows
})

function scoped(
  list: NotificationRecipientItem[],
  col: string | null,
  channel: 'email' | 'line',
) {
  return list.filter((r) => {
    const colMatch = col ? r.inventory_column === col : !r.inventory_column
    if (!colMatch) return false
    if (channel === 'line') return r.recipient_type === 'line'
    return r.recipient_type !== 'line'
  })
}

function formatEmailList(items: NotificationRecipientItem[]) {
  if (!items.length) return '—'
  return items.map((r) => recipientLabel(r)).join('、')
}

function formatLineList(items: NotificationRecipientItem[]) {
  if (!items.length) return '—'
  return items.map((r) => recipientLabel(r)).join('、')
}

function recipientLabel(r: NotificationRecipientItem) {
  if (r.recipient_type === 'user' && r.user_id) {
    const u = users.value.find((x) => x.id === r.user_id)
    return u ? (u.full_name || u.username || u.email) : `user#${r.user_id}`
  }
  if (r.recipient_type === 'role') return `ロール:${r.role}`
  if (r.recipient_type === 'line') return r.display_name || r.line_user_id || 'LINE'
  return r.display_name || r.email || '—'
}

async function loadData() {
  loading.value = true
  try {
    const [recs, userRes] = await Promise.all([
      getNotificationRecipients(INVENTORY_STAGNATION_EVENT),
      isAdmin.value ? getUsers({ page: 1, page_size: 500 }) : Promise.resolve({ items: [] as UserListItem[] }),
    ])
    recipients.value = recs
    users.value = userRes.items || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '受信者の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const formVisible = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  inventory_column: '' as string,
  recipient_type: 'user' as 'user' | 'email' | 'role' | 'line',
  user_id: null as number | null,
  email: '',
  line_user_id: '',
  role: '',
  display_name: '',
})

const formRules: FormRules = {
  recipient_type: [{ required: true, message: '種別を選択', trigger: 'change' }],
  email: [{ required: true, message: 'メールを選択', trigger: 'change' }],
  line_user_id: [
    { required: true, message: 'LINE User ID を入力', trigger: 'blur' },
    { pattern: /^U[a-fA-F0-9]{32}$/, message: 'U で始まる33文字', trigger: 'blur' },
  ],
}

function handleEmailSelect(email: string) {
  if (!email) return
  const u = users.value.find((x) => x.email === email)
  if (u) {
    form.display_name = u.full_name || u.username || ''
  }
}

function openAdd(inventoryColumn: string | null) {
  form.inventory_column = inventoryColumn || ''
  form.recipient_type = 'user'
  form.user_id = null
  form.email = ''
  form.line_user_id = ''
  form.role = ''
  form.display_name = ''
  formVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await createNotificationRecipient({
      event_code: INVENTORY_STAGNATION_EVENT,
      recipient_type: form.recipient_type,
      user_id: form.recipient_type === 'user' ? form.user_id : null,
      email: form.recipient_type === 'email' ? form.email : null,
      line_user_id: form.recipient_type === 'line' ? form.line_user_id : null,
      role: form.recipient_type === 'role' ? form.role : null,
      inventory_column: form.inventory_column || null,
      display_name: form.display_name || null,
      is_active: true,
    })
    ElMessage.success(
      `${inventoryColumnLabel(form.inventory_column || null)} の受信者を追加しました`,
    )
    formVisible.value = false
    await loadData()
    emit('updated')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存に失敗しました')
  } finally {
    submitting.value = false
  }
}

watch(
  () => props.active,
  (v) => {
    if (v) loadData()
  },
  { immediate: true },
)

defineExpose({ reload: loadData, openAdd })
</script>

<style scoped>
.recipient-settings__intro {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e8edf3;
}

.recipient-settings__intro-icon {
  margin-top: 2px;
  color: #3b82f6;
  flex-shrink: 0;
}

.recipient-settings__hint {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.55;
}

.recipient-settings__readonly {
  margin: 10px 0 0;
  font-size: 11px;
  color: #94a3b8;
}

.recipient-table {
  border-radius: 12px;
  overflow: hidden;
}

.recipient-table :deep(.el-table__cell) {
  font-size: 12px;
  padding: 6px 0;
}

.recipient-table :deep(.el-table__header th) {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}

.process-label {
  font-weight: 600;
  color: #0f172a;
}

.process-label--global {
  color: #475569;
}

.detected-tag {
  margin-left: 4px;
  vertical-align: middle;
}

.recipient-text {
  word-break: break-all;
  line-height: 1.45;
  color: #334155;
}

.recipient-text--line {
  color: #15803d;
}

.recipient-form-dialog :deep(.el-dialog) {
  border-radius: 14px;
}
</style>
