<template>
  <div class="umemo-form">
    <el-form label-position="top" size="small" class="umemo-form__el" @submit.prevent="submit">
      <el-form-item :label="t('common.userMemoTitleLabel')" required>
        <el-input
          v-model="form.title"
          maxlength="200"
          :placeholder="t('common.userMemoTitlePlaceholder')"
          clearable
          class="umemo-form__title-input"
        />
      </el-form-item>

      <div class="umemo-form__row">
        <el-form-item :label="t('common.userMemoDateLabel')" class="umemo-form__date">
          <el-date-picker
            v-model="form.memo_date"
            type="date"
            value-format="YYYY-MM-DD"
            :clearable="false"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('common.userMemoTimeLabel')" class="umemo-form__time">
          <el-time-picker
            v-model="form.memo_time"
            format="HH:mm"
            value-format="HH:mm"
            :disabled="form.all_day"
            :placeholder="t('common.userMemoTimePlaceholder')"
            style="width: 100%"
          />
        </el-form-item>
      </div>

      <div class="umemo-form__chips">
        <button
          type="button"
          class="umemo-form__chip"
          :class="{ 'is-on': form.all_day }"
          @click="form.all_day = !form.all_day"
        >
          {{ t('common.userMemoAllDay') }}
        </button>
        <button
          type="button"
          class="umemo-form__chip"
          :class="{ 'is-on': form.remind_enabled }"
          @click="form.remind_enabled = !form.remind_enabled"
        >
          <el-icon :size="12"><Bell /></el-icon>
          {{ t('common.userMemoRemindEnable') }}
        </button>
      </div>

      <el-form-item :label="t('common.userMemoColorLabel')" class="umemo-form__color-item">
        <div class="umemo-form__colors">
          <button
            v-for="c in MEMO_COLORS"
            :key="c"
            type="button"
            class="umemo-form__color"
            :class="[`umemo-form__color--${c}`, { 'is-active': form.color === c }]"
            :aria-label="t(`common.userMemoColor_${c}`)"
            @click="form.color = c"
          />
        </div>
      </el-form-item>

      <el-form-item
        v-if="form.remind_enabled"
        :label="t('common.userMemoRemindOffsetLabel')"
        class="umemo-form__remind"
      >
        <div class="umemo-form__offset">
          <button
            v-for="opt in REMIND_OFFSET_OPTIONS"
            :key="opt"
            type="button"
            class="umemo-form__offset-btn"
            :class="{ 'is-on': form.remind_offset_minutes === opt }"
            @click="form.remind_offset_minutes = opt"
          >
            {{ remindLabel(opt) }}
          </button>
        </div>
      </el-form-item>

      <el-form-item :label="t('common.userMemoContentLabel')">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="3"
          maxlength="2000"
          :placeholder="t('common.userMemoContentPlaceholder')"
          show-word-limit
        />
      </el-form-item>

      <div class="umemo-form__actions">
        <el-button size="small" class="umemo-form__cancel" @click="emit('cancel')">
          {{ t('common.cancel') }}
        </el-button>
        <el-button
          type="primary"
          size="small"
          class="umemo-form__submit"
          :loading="submitting"
          @click="submit"
        >
          {{ editing ? t('common.userMemoSave') : t('common.userMemoCreate') }}
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import {
  MEMO_COLORS,
  REMIND_OFFSET_OPTIONS,
  type UserMemoItem,
  type UserMemoColor,
} from '@/api/auth/memos'

const props = defineProps<{
  initialDate: string
  editing?: UserMemoItem | null
  submitting?: boolean
}>()

const emit = defineEmits<{
  submit: [payload: {
    title: string
    memo_date: string
    content?: string | null
    memo_time?: string | null
    all_day: boolean
    remind_offset_minutes?: number | null
    color?: UserMemoColor | null
  }]
  cancel: []
}>()

const { t } = useI18n()

const form = reactive({
  title: '',
  memo_date: props.initialDate,
  memo_time: '09:00' as string | null,
  all_day: true,
  color: 'blue' as UserMemoColor,
  remind_enabled: false,
  remind_offset_minutes: 15,
  content: '',
})

function remindLabel(minutes: number) {
  if (minutes === 0) return t('common.userMemoRemindAtTime')
  return t('common.userMemoRemindBefore', { n: minutes })
}

function resetFromProps() {
  const item = props.editing
  if (item) {
    form.title = item.title
    form.memo_date = item.memo_date
    form.memo_time = item.memo_time ? item.memo_time.slice(0, 5) : '09:00'
    form.all_day = !item.memo_time
    form.color = (item.color as UserMemoColor) || 'blue'
    form.remind_enabled = item.remind_offset_minutes != null
    form.remind_offset_minutes = item.remind_offset_minutes ?? 15
    form.content = item.content ?? ''
  } else {
    form.title = ''
    form.memo_date = props.initialDate
    form.memo_time = '09:00'
    form.all_day = true
    form.color = 'blue'
    form.remind_enabled = false
    form.remind_offset_minutes = 15
    form.content = ''
  }
}

watch(
  () => [props.initialDate, props.editing?.id] as const,
  () => resetFromProps(),
  { immediate: true },
)

function submit() {
  const title = form.title.trim()
  if (!title) return
  const memoTime = form.all_day ? null : (form.memo_time || '09:00')
  emit('submit', {
    title,
    memo_date: form.memo_date,
    content: form.content.trim() || null,
    memo_time: memoTime,
    all_day: form.all_day,
    remind_offset_minutes: form.remind_enabled ? form.remind_offset_minutes : null,
    color: form.color,
  })
}
</script>

<style scoped>
.umemo-form {
  animation: umemo-form-in 0.2s ease;
}

@keyframes umemo-form-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.umemo-form__el :deep(.el-form-item) {
  margin-bottom: 12px;
}

.umemo-form__el :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 4px !important;
}

.umemo-form__el :deep(.el-input__wrapper),
.umemo-form__el :deep(.el-textarea__inner) {
  border-radius: 9px;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.28) inset;
}

.umemo-form__el :deep(.el-input__wrapper:hover),
.umemo-form__el :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px rgba(13, 148, 136, 0.35) inset;
}

.umemo-form__el :deep(.el-input__wrapper.is-focus),
.umemo-form__el :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #0d9488 inset, 0 0 0 3px rgba(20, 184, 166, 0.15) !important;
}

.umemo-form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.umemo-form__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.umemo-form__chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #fff;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s, box-shadow 0.15s;
}

.umemo-form__chip:hover {
  border-color: rgba(13, 148, 136, 0.4);
  color: #0f766e;
}

.umemo-form__chip.is-on {
  border-color: transparent;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(20, 184, 166, 0.18));
  color: #0f766e;
  box-shadow: inset 0 0 0 1px rgba(13, 148, 136, 0.28);
}

.umemo-form__color-item {
  margin-bottom: 10px !important;
}

.umemo-form__colors {
  display: flex;
  gap: 10px;
  align-items: center;
  padding-top: 2px;
}

.umemo-form__color {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;
  transition: transform 0.15s, box-shadow 0.15s;
}

.umemo-form__color:hover {
  transform: scale(1.08);
}

.umemo-form__color.is-active {
  box-shadow:
    0 0 0 2px #fff,
    0 0 0 4px rgba(15, 23, 42, 0.35);
  transform: scale(1.08);
}

.umemo-form__color--blue { background: linear-gradient(145deg, #3b82f6, #60a5fa); }
.umemo-form__color--green { background: linear-gradient(145deg, #16a34a, #4ade80); }
.umemo-form__color--amber { background: linear-gradient(145deg, #d97706, #fbbf24); }
.umemo-form__color--rose { background: linear-gradient(145deg, #e11d48, #fb7185); }
.umemo-form__color--slate { background: linear-gradient(145deg, #475569, #94a3b8); }

.umemo-form__offset {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  width: 100%;
}

.umemo-form__offset-btn {
  height: 28px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: #fff;
  color: #475569;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.umemo-form__offset-btn.is-on {
  border-color: transparent;
  background: #0f766e;
  color: #fff;
}

.umemo-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
  padding-top: 4px;
}

.umemo-form__submit {
  --el-button-bg-color: #0f766e;
  --el-button-border-color: #0f766e;
  --el-button-hover-bg-color: #0d9488;
  --el-button-hover-border-color: #0d9488;
  --el-button-active-bg-color: #0f766e;
  --el-button-active-border-color: #0f766e;
  border-radius: 9px !important;
  font-weight: 600;
  box-shadow: 0 4px 12px -4px rgba(13, 148, 136, 0.55);
}
</style>
