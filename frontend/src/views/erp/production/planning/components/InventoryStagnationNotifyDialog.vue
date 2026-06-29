<template>
  <el-dialog
    v-model="visible"
    width="780px"
    :close-on-click-modal="false"
    class="stagnation-notify-dialog"
    destroy-on-close
    align-center
    @open="handleOpen"
  >
    <template #header>
      <div class="snd-header">
        <div class="snd-header__icon" aria-hidden="true">
          <el-icon :size="20"><Bell /></el-icon>
        </div>
        <div class="snd-header__text">
          <h3 class="snd-header__title">在庫停滞アラート送信</h3>
          <p class="snd-header__sub">工程別にメール・LINE で停滞在庫を通知します</p>
        </div>
      </div>
    </template>

    <el-tabs v-model="activeTab" class="snd-tabs">
      <el-tab-pane name="preview">
        <template #label>
          <span class="snd-tab-label">
            <el-icon><View /></el-icon>
            送信プレビュー
          </span>
        </template>

        <div v-loading="loading" class="snd-body">
          <template v-if="preview">
            <div class="snd-stats">
              <div class="snd-stat">
                <span class="snd-stat__label">基準日</span>
                <strong class="snd-stat__value">{{ preview.as_of }}</strong>
              </div>
              <div class="snd-stat">
                <span class="snd-stat__label">閾値 (&gt;)</span>
                <strong class="snd-stat__value">{{ preview.min_quantity }}</strong>
              </div>
              <div class="snd-stat">
                <span class="snd-stat__label">連続日数</span>
                <strong class="snd-stat__value">{{ preview.stable_calendar_days }} 日</strong>
              </div>
              <div class="snd-stat snd-stat--accent">
                <span class="snd-stat__label">検出件数</span>
                <strong class="snd-stat__value">{{ preview.total_count }} 件</strong>
              </div>
            </div>

            <el-empty
              v-if="!preview.groups.length"
              description="送信対象の停滞在庫がありません"
              class="snd-empty"
            />

            <template v-else>
              <div class="snd-toolbar">
                <span class="snd-toolbar__hint">
                  送信する工程を選択してください（{{ selectedSendableCount }} / {{ sendableCount }} 件選択中）
                </span>
                <div class="snd-toolbar__actions">
                  <el-button size="small" text type="primary" :disabled="!sendableCount" @click="selectAllSendable">
                    送信可能を全選択
                  </el-button>
                  <el-button size="small" text :disabled="!selectedSendableCount" @click="clearSelection">
                    選択解除
                  </el-button>
                </div>
              </div>

              <div class="snd-groups">
                <article
                  v-for="group in preview.groups"
                  :key="group.inventory_column"
                  class="snd-group"
                  :class="{
                    'snd-group--selected': selectedColumns[group.inventory_column],
                    'snd-group--sendable': group.can_send,
                    'snd-group--warn': group.no_recipients,
                    'snd-group--sent': group.already_sent,
                  }"
                  @click="toggleGroup(group)"
                >
                  <div class="snd-group__main">
                    <el-checkbox
                      v-model="selectedColumns[group.inventory_column]"
                      :disabled="!group.can_send"
                      class="snd-group__check"
                      @click.stop
                    />
                    <div class="snd-group__content">
                      <div class="snd-group__head">
                        <div class="snd-group__title-row">
                          <span class="snd-group__title">{{ group.process_label }}</span>
                          <span class="snd-group__count">{{ group.item_count }} 件</span>
                        </div>
                        <div class="snd-group__badges">
                          <span v-if="group.already_sent" class="snd-badge snd-badge--muted">
                            <el-icon><CircleCheck /></el-icon>
                            送信済み
                          </span>
                          <span v-else-if="group.no_recipients" class="snd-badge snd-badge--warn">
                            <el-icon><Warning /></el-icon>
                            受信者未設定
                          </span>
                          <span v-else-if="group.can_send" class="snd-badge snd-badge--ok">
                            <el-icon><Select /></el-icon>
                            送信可能
                          </span>
                        </div>
                      </div>

                      <div v-if="group.recipient_count || group.line_recipient_count" class="snd-recipients">
                        <div v-if="group.recipient_count" class="snd-recipient-row">
                          <span class="snd-recipient-row__icon snd-recipient-row__icon--mail">
                            <el-icon><Message /></el-icon>
                          </span>
                          <span class="snd-recipient-row__text">{{ formatRecipientNames(group.recipients) }}</span>
                        </div>
                        <div v-if="group.line_recipient_count" class="snd-recipient-row">
                          <span class="snd-recipient-row__icon snd-recipient-row__icon--line">
                            <el-icon><ChatDotRound /></el-icon>
                          </span>
                          <span class="snd-recipient-row__text">{{ formatLineRecipientNames(group.line_recipients) }}</span>
                        </div>
                      </div>

                      <p v-if="group.no_recipients" class="snd-group__hint">
                        この工程専用の受信者が未設定です（全工程共通の受信者も対象になります）
                      </p>
                    </div>
                  </div>

                  <el-button
                    v-if="group.no_recipients && isAdmin"
                    class="snd-group__setup"
                    size="small"
                    round
                    @click.stop="goRecipientSetup(group.inventory_column)"
                  >
                    受信者を設定
                  </el-button>
                </article>
              </div>

              <el-alert
                v-if="!preview.can_send"
                type="warning"
                :closable="false"
                show-icon
                class="snd-alert"
                title="送信可能な工程がありません。「工程別受信者」タブで受信者を登録してください。"
              />
            </template>
          </template>
        </div>
      </el-tab-pane>

      <el-tab-pane name="recipients">
        <template #label>
          <span class="snd-tab-label">
            <el-icon><User /></el-icon>
            工程別受信者
          </span>
        </template>

        <InventoryStagnationRecipientSettings
          ref="recipientSettingsRef"
          :active="activeTab === 'recipients'"
          :detected-columns="detectedColumns"
          @updated="handleRecipientsUpdated"
        />
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <div class="snd-footer">
        <el-button class="snd-footer__cancel" @click="visible = false">キャンセル</el-button>
        <el-button
          type="primary"
          class="snd-footer__send"
          :loading="sending"
          :disabled="!hasSelectedSendable"
          @click="handleSend"
        >
          <el-icon v-if="!sending" class="snd-footer__send-icon"><Promotion /></el-icon>
          メール・LINE送信
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell,
  ChatDotRound,
  CircleCheck,
  Message,
  Promotion,
  Select,
  User,
  View,
  Warning,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/modules/auth/stores/user'
import { isAdminUser } from '@/utils/menuPermissions'
import {
  previewInventoryStagnationNotification,
  sendInventoryStagnationNotification,
  type InventoryStagnationNotifyPreview,
  type InventoryStagnationNotifyGroup,
} from '@/api/database'
import InventoryStagnationRecipientSettings from './InventoryStagnationRecipientSettings.vue'

interface Props {
  modelValue: boolean
  asOfDate: string
  minQuantity: number
  stableDays: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'sent'): void
}>()

const userStore = useUserStore()
const isAdmin = computed(() => isAdminUser(userStore.user))

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

const activeTab = ref<'preview' | 'recipients'>('preview')
const loading = ref(false)
const sending = ref(false)
const preview = ref<InventoryStagnationNotifyPreview | null>(null)
const selectedColumns = reactive<Record<string, boolean>>({})
const recipientSettingsRef = ref<InstanceType<typeof InventoryStagnationRecipientSettings> | null>(null)

const detectedColumns = computed(() => preview.value?.groups.map((g) => g.inventory_column) || [])

const sendableCount = computed(() => preview.value?.groups.filter((g) => g.can_send).length ?? 0)

const selectedSendableCount = computed(() => {
  if (!preview.value) return 0
  return preview.value.groups.filter((g) => g.can_send && selectedColumns[g.inventory_column]).length
})

const hasSelectedSendable = computed(() => selectedSendableCount.value > 0)

function formatRecipientNames(recipients: Array<{ name: string; email: string }>) {
  return recipients.map((r) => r.name || r.email).join('、')
}

function formatLineRecipientNames(recipients: Array<{ name: string; line_user_id: string }>) {
  return recipients.map((r) => r.name || r.line_user_id).join('、')
}

function syncSelection(data: InventoryStagnationNotifyPreview) {
  Object.keys(selectedColumns).forEach((k) => delete selectedColumns[k])
  for (const g of data.groups) {
    selectedColumns[g.inventory_column] = false
  }
}

function selectAllSendable() {
  if (!preview.value) return
  for (const g of preview.value.groups) {
    if (g.can_send) selectedColumns[g.inventory_column] = true
  }
}

function clearSelection() {
  if (!preview.value) return
  for (const g of preview.value.groups) {
    selectedColumns[g.inventory_column] = false
  }
}

function toggleGroup(group: InventoryStagnationNotifyGroup) {
  if (!group.can_send) return
  selectedColumns[group.inventory_column] = !selectedColumns[group.inventory_column]
}

async function loadPreview() {
  loading.value = true
  try {
    const res = await previewInventoryStagnationNotification({
      as_of: props.asOfDate || undefined,
      min_quantity: props.minQuantity,
      stable_calendar_days: props.stableDays,
    })
    const data = (res as any)?.data ?? res
    preview.value = data
    if (data) {
      syncSelection(data)
      if (data.groups.some((g: { no_recipients: boolean }) => g.no_recipients)) {
        activeTab.value = 'recipients'
      }
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '送信プレビューの取得に失敗しました')
    visible.value = false
  } finally {
    loading.value = false
  }
}

function handleOpen() {
  activeTab.value = 'preview'
  loadPreview()
}

function goRecipientSetup(inventoryColumn: string) {
  activeTab.value = 'recipients'
  recipientSettingsRef.value?.openAdd(inventoryColumn)
}

async function handleRecipientsUpdated() {
  await loadPreview()
}

async function handleSend() {
  if (!preview.value || !hasSelectedSendable.value) return
  const columns = preview.value.groups
    .filter((g) => g.can_send && selectedColumns[g.inventory_column])
    .map((g) => g.inventory_column)
  if (!columns.length) return

  const labels = preview.value.groups
    .filter((g) => columns.includes(g.inventory_column))
    .map((g) => g.process_label)
    .join('、')

  try {
    await ElMessageBox.confirm(
      `以下の工程へ在庫停滞アラートを送信します。\n${labels}`,
      '送信確認',
      { type: 'warning', confirmButtonText: '送信', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }

  sending.value = true
  try {
    const res = await sendInventoryStagnationNotification({
      as_of: props.asOfDate || undefined,
      min_quantity: props.minQuantity,
      stable_calendar_days: props.stableDays,
      inventory_columns: columns,
    })
    const data = (res as any)?.data ?? res
    const emailCount = data?.email_sent_count ?? 0
    const lineCount = data?.line_sent_count ?? 0
    const msg = data?.message as string | undefined
    const emailFailed = (data?.email_failed as Array<{ email: string; error: string }>) || []
    const lineFailed = (data?.line_failed as Array<{ line_user_id: string; error: string }>) || []
    if (data?.status === 'partial' || emailFailed.length || lineFailed.length) {
      ElMessage.warning(msg || `一部送信失敗（メール ${emailCount} 件 / LINE ${lineCount} 件）`)
    } else {
      ElMessage.success(msg || `送信完了（メール ${emailCount} 件 / LINE ${lineCount} 件）`)
    }
    emit('sent')
    if (!emailFailed.length && !lineFailed.length) {
      visible.value = false
    } else {
      await loadPreview()
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '送信に失敗しました')
    await loadPreview()
  } finally {
    sending.value = false
  }
}

watch(
  () => [props.asOfDate, props.minQuantity, props.stableDays] as const,
  () => {
    if (visible.value) loadPreview()
  },
)
</script>

<style scoped>
.stagnation-notify-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.14);
}

.stagnation-notify-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 20px 24px 12px;
  border-bottom: 1px solid #eef2f7;
}

.stagnation-notify-dialog :deep(.el-dialog__body) {
  padding: 0 24px 8px;
}

.stagnation-notify-dialog :deep(.el-dialog__footer) {
  padding: 12px 24px 20px;
  border-top: 1px solid #eef2f7;
  background: #fafbfd;
}

.snd-header {
  display: flex;
  align-items: center;
  gap: 14px;
}

.snd-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  color: #fff;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.28);
}

.snd-header__title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.01em;
}

.snd-header__sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}

.snd-tabs :deep(.el-tabs__header) {
  margin-bottom: 14px;
}

.snd-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: #e8edf3;
}

.snd-tabs :deep(.el-tabs__item) {
  font-weight: 600;
  color: #64748b;
}

.snd-tabs :deep(.el-tabs__item.is-active) {
  color: #2563eb;
}

.snd-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.snd-body {
  min-height: 140px;
}

.snd-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.snd-stat {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e8edf3;
}

.snd-stat--accent {
  background: linear-gradient(135deg, #eff6ff 0%, #eef2ff 100%);
  border-color: #c7d2fe;
}

.snd-stat__label {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 4px;
}

.snd-stat__value {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.snd-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  padding: 8px 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px dashed #dbe3ee;
}

.snd-toolbar__hint {
  font-size: 12px;
  color: #64748b;
}

.snd-toolbar__actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.snd-groups {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 380px;
  overflow-y: auto;
  padding-right: 2px;
}

.snd-group {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #e8edf3;
  background: #fff;
  cursor: default;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
}

.snd-group--sendable {
  cursor: pointer;
}

.snd-group--sendable:hover {
  border-color: #bfdbfe;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.08);
}

.snd-group--selected {
  border-color: #60a5fa;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.1);
}

.snd-group--warn {
  border-color: #fde68a;
  background: #fffbeb;
}

.snd-group--sent {
  opacity: 0.88;
}

.snd-group__main {
  display: flex;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.snd-group__check {
  margin-top: 2px;
}

.snd-group__content {
  flex: 1;
  min-width: 0;
}

.snd-group__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.snd-group__title-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.snd-group__title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.snd-group__count {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  padding: 2px 8px;
  border-radius: 999px;
  background: #f1f5f9;
}

.snd-group__badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.snd-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 999px;
}

.snd-badge--ok {
  color: #15803d;
  background: #dcfce7;
}

.snd-badge--warn {
  color: #b45309;
  background: #fef3c7;
}

.snd-badge--muted {
  color: #64748b;
  background: #f1f5f9;
}

.snd-recipients {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.snd-recipient-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  color: #475569;
  line-height: 1.5;
}

.snd-recipient-row__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  flex-shrink: 0;
}

.snd-recipient-row__icon--mail {
  color: #2563eb;
  background: #dbeafe;
}

.snd-recipient-row__icon--line {
  color: #15803d;
  background: #dcfce7;
}

.snd-recipient-row__text {
  word-break: break-all;
}

.snd-group__hint {
  margin: 8px 0 0;
  font-size: 11px;
  color: #b45309;
  line-height: 1.5;
}

.snd-group__setup {
  flex-shrink: 0;
  margin-top: 2px;
}

.snd-alert {
  margin-top: 12px;
  border-radius: 10px;
}

.snd-empty {
  padding: 24px 0;
}

.snd-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.snd-footer__send {
  min-width: 168px;
  font-weight: 600;
  border: none;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
}

.snd-footer__send:hover,
.snd-footer__send:focus {
  background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%);
}

.snd-footer__send-icon {
  margin-right: 4px;
}

@media (max-width: 720px) {
  .snd-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .snd-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
