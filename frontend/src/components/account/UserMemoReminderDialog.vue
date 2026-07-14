<template>
  <el-dialog
    v-model="visible"
    :show-close="false"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :append-to-body="true"
    align-center
    width="440px"
    class="user-memo-reminder-dialog"
  >
    <div v-if="current" class="umemo-remind">
      <div class="umemo-remind__icon" aria-hidden="true">
        <el-icon :size="28"><BellFilled /></el-icon>
      </div>
      <div class="umemo-remind__eyebrow">{{ t('common.userMemoReminderLabel') }}</div>
      <h2 class="umemo-remind__title">{{ current.title }}</h2>
      <p class="umemo-remind__body">{{ bodyText }}</p>
      <div class="umemo-remind__meta">
        <span class="umemo-remind__chip">{{ dateTimeLabel }}</span>
        <span v-if="queueLength > 1" class="umemo-remind__chip umemo-remind__chip--muted">
          {{ t('common.userMemoReminderQueue', { n: queueLength }) }}
        </span>
      </div>
      <div class="umemo-remind__actions">
        <el-button type="primary" class="umemo-remind__btn" @click="dismiss">
          {{ t('common.userMemoReminderDismiss') }}
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { BellFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { useUserMemos } from '@/composables/useUserMemos'

const { t, locale } = useI18n()
const memos = useUserMemos()

const current = computed(() => memos.activeReminders.value[0] ?? null)
const queueLength = computed(() => memos.activeReminders.value.length)

const visible = computed({
  get: () => memos.activeReminders.value.length > 0,
  set: (v: boolean) => {
    if (!v) memos.dismissCurrentReminder()
  },
})

const bodyText = computed(() => {
  const memo = current.value
  if (!memo) return ''
  return memo.content?.trim() || t('common.userMemoReminderBodyFallback')
})

const dateTimeLabel = computed(() => {
  const memo = current.value
  if (!memo) return ''
  const d = dayjs(memo.memo_date)
  const loc = locale.value
  let datePart = d.format('YYYY-MM-DD')
  if (loc === 'ja') datePart = d.format('M月D日')
  else if (loc === 'zh') datePart = d.format('M月D日')
  else if (loc === 'en') datePart = d.format('MMM D')
  else if (loc === 'vi') datePart = d.format('DD/MM')

  if (!memo.memo_time) return `${datePart} · ${t('common.userMemoAllDay')}`
  return `${datePart} · ${memo.memo_time.slice(0, 5)}`
})

function dismiss() {
  memos.dismissCurrentReminder()
}
</script>

<style scoped>
.umemo-remind {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 4px 4px;
}

.umemo-remind__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(145deg, #0f766e 0%, #14b8a6 100%);
  box-shadow: 0 10px 24px -8px rgba(13, 148, 136, 0.55);
  margin-bottom: 14px;
}

.umemo-remind__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0d9488;
  margin-bottom: 8px;
}

.umemo-remind__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.35;
  word-break: break-word;
}

.umemo-remind__body {
  margin: 10px 0 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
  max-width: 100%;
}

.umemo-remind__meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}

.umemo-remind__chip {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #0f766e;
  background: rgba(20, 184, 166, 0.12);
}

.umemo-remind__chip--muted {
  color: #64748b;
  background: #f1f5f9;
}

.umemo-remind__actions {
  margin-top: 22px;
  width: 100%;
}

.umemo-remind__btn {
  width: 100%;
  height: 40px;
  border-radius: 10px !important;
  font-weight: 700;
  --el-button-bg-color: #0f766e;
  --el-button-border-color: #0f766e;
  --el-button-hover-bg-color: #0d9488;
  --el-button-hover-border-color: #0d9488;
  --el-button-active-bg-color: #0f766e;
  --el-button-active-border-color: #0f766e;
  box-shadow: 0 6px 16px -6px rgba(13, 148, 136, 0.55);
}
</style>

<style>
.user-memo-reminder-dialog.el-dialog {
  border-radius: 18px;
  overflow: hidden;
  box-shadow:
    0 24px 48px -16px rgba(15, 23, 42, 0.35),
    0 0 0 1px rgba(148, 163, 184, 0.2);
}

.user-memo-reminder-dialog .el-dialog__header {
  display: none;
}

.user-memo-reminder-dialog .el-dialog__body {
  padding: 28px 28px 24px;
  background: linear-gradient(180deg, #f8fffd 0%, #ffffff 48%, #f8fafc 100%);
}
</style>
