<template>
  <el-dialog
    v-model="visible"
    :show-close="false"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    append-to-body
    align-center
    width="460px"
    class="uevent-remind-dialog"
  >
    <div v-if="current" class="uevent-remind">
      <div class="uevent-remind__glow" aria-hidden="true" />
      <div class="uevent-remind__icon" aria-hidden="true">
        <el-icon :size="30"><BellFilled /></el-icon>
      </div>
      <div class="uevent-remind__eyebrow">{{ t('common.userEventReminderLabel') }}</div>
      <h2 class="uevent-remind__title">{{ current.title }}</h2>
      <p v-if="bodyText" class="uevent-remind__body">{{ bodyText }}</p>
      <div class="uevent-remind__meta">
        <span class="uevent-remind__chip">{{ dateTimeLabel }}</span>
        <span v-if="current.location" class="uevent-remind__chip uevent-remind__chip--loc">
          <el-icon :size="12"><Location /></el-icon>
          {{ current.location }}
        </span>
        <span v-if="queueLength > 1" class="uevent-remind__chip uevent-remind__chip--muted">
          {{ t('common.userEventReminderQueue', { n: queueLength - 1 }) }}
        </span>
      </div>
      <el-button type="primary" class="uevent-remind__btn" @click="dismiss">
        {{ t('common.userEventReminderDismiss') }}
      </el-button>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { BellFilled, Location } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { useUserEvents } from '@/composables/useUserEvents'

const { t, locale } = useI18n()
const events = useUserEvents()

const current = computed(() => events.activeReminders.value[0] ?? null)
const queueLength = computed(() => events.activeReminders.value.length)

const visible = computed({
  get: () => events.activeReminders.value.length > 0,
  set: (v: boolean) => {
    if (!v) events.dismissCurrentReminder()
  },
})

const bodyText = computed(() => {
  const ev = current.value
  if (!ev) return ''
  return ev.description?.trim() || ''
})

const dateTimeLabel = computed(() => {
  const ev = current.value
  if (!ev) return ''
  const start = dayjs(ev.start_at)
  const loc = locale.value
  let datePart = start.format('YYYY-MM-DD')
  if (loc === 'ja' || loc === 'zh') datePart = start.format('M月D日')
  else if (loc === 'en') datePart = start.format('MMM D')
  else if (loc === 'vi') datePart = start.format('DD/MM')
  if (ev.all_day) return `${datePart} · ${t('common.userMemoAllDay')}`
  return `${datePart} · ${start.format('HH:mm')}`
})

function dismiss() {
  events.dismissCurrentReminder()
}
</script>

<style scoped>
.uevent-remind {
  position: relative;
  text-align: center;
  padding: 8px 4px 4px;
}

.uevent-remind__glow {
  position: absolute;
  inset: -20px -10px auto;
  height: 120px;
  background: radial-gradient(ellipse at 50% 0%, rgba(99, 102, 241, 0.25), transparent 70%);
  pointer-events: none;
}

.uevent-remind__icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #818cf8, #4f46e5);
  color: #fff;
  box-shadow: 0 10px 28px rgba(79, 70, 229, 0.35);
}

.uevent-remind__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6366f1;
  margin-bottom: 6px;
}

.uevent-remind__title {
  margin: 0 0 8px;
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
}

.uevent-remind__body {
  margin: 0 0 12px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.uevent-remind__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-bottom: 18px;
}

.uevent-remind__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  background: #eef2ff;
  color: #4338ca;
}

.uevent-remind__chip--loc {
  background: #f0fdf4;
  color: #15803d;
}

.uevent-remind__chip--muted {
  background: #f1f5f9;
  color: #64748b;
}

.uevent-remind__btn {
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
}
</style>
