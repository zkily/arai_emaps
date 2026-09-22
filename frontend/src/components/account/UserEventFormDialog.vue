<template>
  <el-dialog
    v-model="visible"
    width="500px"
    append-to-body
    destroy-on-close
    align-center
    class="uevent-form-dialog"
    :show-close="false"
    @closed="onClosed"
  >
    <template #header>
      <div class="uevent-form-head">
        <div class="uevent-form-head__icon" :class="`is-${form.color}`" aria-hidden="true">
          <el-icon :size="18"><Calendar /></el-icon>
        </div>
        <div class="uevent-form-head__text">
          <div class="uevent-form-head__title">
            {{
              readonly
                ? t('common.userEventView')
                : editing
                  ? t('common.userEventEdit')
                  : t('common.userEventNew')
            }}
          </div>
          <div class="uevent-form-head__sub">
            {{
              readonly
                ? visibilityLabel(editing?.visibility)
                : t('common.userEventFormSub')
            }}
          </div>
        </div>
        <button type="button" class="uevent-form-head__close" @click="visible = false">
          <el-icon :size="14"><Close /></el-icon>
        </button>
      </div>
    </template>

    <el-form
      label-position="top"
      size="small"
      class="uevent-form"
      :class="{ 'is-readonly': readonly }"
      :disabled="readonly"
      @submit.prevent="submit"
    >
      <el-form-item :label="t('common.userEventTitleLabel')" required class="uevent-form__title-item">
        <el-input
          v-model="form.title"
          maxlength="200"
          :placeholder="t('common.userEventTitlePlaceholder')"
          clearable
          class="uevent-form__title"
        />
      </el-form-item>

      <div class="uevent-form__section">
        <div class="uevent-form__section-label">{{ t('common.userEventStartDate') }} / {{ t('common.userEventEndDate') }}</div>
        <div class="uevent-form__row">
          <el-form-item class="uevent-form__col" :label="t('common.userEventStartDate')">
            <el-date-picker
              v-model="form.start_date"
              type="date"
              value-format="YYYY-MM-DD"
              :clearable="false"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item
            v-if="!form.all_day"
            class="uevent-form__col"
            :label="t('common.userEventStartTime')"
          >
            <el-time-picker
              v-model="form.start_time"
              format="HH:mm"
              value-format="HH:mm"
              :placeholder="t('common.userMemoTimePlaceholder')"
              style="width: 100%"
            />
          </el-form-item>
        </div>
        <div class="uevent-form__row">
          <el-form-item class="uevent-form__col" :label="t('common.userEventEndDate')">
            <el-date-picker
              v-model="form.end_date"
              type="date"
              value-format="YYYY-MM-DD"
              :clearable="false"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item
            v-if="!form.all_day"
            class="uevent-form__col"
            :label="t('common.userEventEndTime')"
          >
            <el-time-picker
              v-model="form.end_time"
              format="HH:mm"
              value-format="HH:mm"
              :placeholder="t('common.userMemoTimePlaceholder')"
              style="width: 100%"
            />
          </el-form-item>
        </div>

        <div class="uevent-form__chips">
          <button
            type="button"
            class="uevent-form__chip"
            :class="{ 'is-on': form.all_day }"
            @click="form.all_day = !form.all_day"
          >
            {{ t('common.userMemoAllDay') }}
          </button>
          <button
            type="button"
            class="uevent-form__chip uevent-form__chip--remind"
            :class="{ 'is-on': form.remind_enabled }"
            @click="form.remind_enabled = !form.remind_enabled"
          >
            <el-icon :size="12"><Bell /></el-icon>
            {{ t('common.userEventRemindEnable') }}
          </button>
        </div>
      </div>

      <el-form-item :label="t('common.userEventVisibilityLabel')" class="uevent-form__vis-item">
        <div class="uevent-form__visibility">
          <button
            v-for="opt in VISIBILITY_OPTIONS"
            :key="opt"
            type="button"
            class="uevent-form__vis-btn"
            :class="[`is-${opt}`, { 'is-on': form.visibility === opt }]"
            @click="form.visibility = opt"
          >
            <el-icon :size="13">
              <Lock v-if="opt === 'self'" />
              <UserFilled v-else-if="opt === 'department'" />
              <OfficeBuilding v-else />
            </el-icon>
            {{ t(`common.userEventVisibility_${opt}`) }}
          </button>
        </div>
        <p class="uevent-form__visibility-hint">
          {{ t(`common.userEventVisibilityHint_${form.visibility}`) }}
        </p>
      </el-form-item>

      <div class="uevent-form__row">
        <el-form-item :label="t('common.userEventRecurrenceLabel')" class="uevent-form__col">
          <el-select v-model="form.recurrence_rule" style="width: 100%">
            <el-option
              v-for="r in RECURRENCE_OPTIONS"
              :key="r"
              :label="t(`common.userEventRecurrence_${r}`)"
              :value="r"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          v-if="form.recurrence_rule !== 'none'"
          :label="t('common.userEventRecurrenceUntil')"
          class="uevent-form__col"
        >
          <el-date-picker
            v-model="form.recurrence_until"
            type="date"
            value-format="YYYY-MM-DD"
            :placeholder="t('common.userEventRecurrenceUntilPlaceholder')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item
          v-else
          :label="t('common.userEventLocationLabel')"
          class="uevent-form__col"
        >
          <el-input
            v-model="form.location"
            maxlength="255"
            :placeholder="t('common.userEventLocationPlaceholder')"
            clearable
          />
        </el-form-item>
      </div>

      <el-form-item
        v-if="form.recurrence_rule !== 'none'"
        :label="t('common.userEventLocationLabel')"
      >
        <el-input
          v-model="form.location"
          maxlength="255"
          :placeholder="t('common.userEventLocationPlaceholder')"
          clearable
        />
      </el-form-item>

      <el-form-item v-if="form.remind_enabled" :label="t('common.userMemoRemindOffsetLabel')">
        <div class="uevent-form__offset">
          <button
            v-for="opt in REMIND_OFFSET_OPTIONS"
            :key="opt"
            type="button"
            class="uevent-form__offset-btn"
            :class="{ 'is-on': form.remind_offset_minutes === opt }"
            @click="form.remind_offset_minutes = opt"
          >
            {{ remindLabel(opt) }}
          </button>
        </div>
      </el-form-item>

      <el-form-item :label="t('common.userMemoColorLabel')" class="uevent-form__color-item">
        <div class="uevent-form__colors">
          <button
            v-for="c in EVENT_COLORS"
            :key="c"
            type="button"
            class="uevent-form__color"
            :class="[`uevent-form__color--${c}`, { 'is-active': form.color === c }]"
            :aria-label="colorLabel(c)"
            @click="form.color = c"
          />
        </div>
      </el-form-item>

      <el-form-item :label="t('common.userEventDescriptionLabel')" class="uevent-form__desc-item">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          maxlength="2000"
          :placeholder="t('common.userEventDescriptionPlaceholder')"
          show-word-limit
          resize="none"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="uevent-form__footer">
        <el-button
          v-if="editing && !readonly"
          class="uevent-form__btn-danger"
          plain
          size="small"
          :loading="deleting"
          @click="emit('delete')"
        >
          {{ t('common.userMemoDelete') }}
        </el-button>
        <span class="uevent-form__footer-spacer" />
        <el-button class="uevent-form__btn-ghost" size="small" @click="visible = false">
          {{ t('common.cancel') }}
        </el-button>
        <el-button
          v-if="!readonly"
          class="uevent-form__btn-primary"
          type="primary"
          size="small"
          :loading="submitting"
          @click="submit"
        >
          {{ editing ? t('common.userMemoSave') : t('common.userMemoCreate') }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { Bell, Calendar, Close, Lock, OfficeBuilding, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import {
  EVENT_COLORS,
  RECURRENCE_OPTIONS,
  REMIND_OFFSET_OPTIONS,
  VISIBILITY_OPTIONS,
  type UserEventColor,
  type UserEventCreatePayload,
  type UserEventItem,
  type UserEventRecurrence,
  type UserEventVisibility,
} from '@/api/auth/events'

const props = defineProps<{
  modelValue: boolean
  editing: UserEventItem | null
  initialDate?: string
  initialHour?: number
  submitting?: boolean
  deleting?: boolean
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submit: [payload: UserEventCreatePayload]
  delete: []
}>()

const { t } = useI18n()

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

type FormState = {
  title: string
  start_date: string
  start_time: string
  end_date: string
  end_time: string
  all_day: boolean
  location: string
  description: string
  color: UserEventColor
  visibility: UserEventVisibility
  recurrence_rule: UserEventRecurrence
  recurrence_until: string
  remind_enabled: boolean
  remind_offset_minutes: number
}

function defaultForm(date?: string, hour?: number): FormState {
  const base = date || dayjs().format('YYYY-MM-DD')
  const h = hour ?? dayjs().hour()
  const startTime = `${String(h).padStart(2, '0')}:00`
  const endTime = `${String(Math.min(h + 1, 23)).padStart(2, '0')}:00`
  return {
    title: '',
    start_date: base,
    start_time: startTime,
    end_date: base,
    end_time: endTime,
    all_day: false,
    location: '',
    description: '',
    color: 'blue',
    visibility: 'department',
    recurrence_rule: 'none',
    recurrence_until: dayjs(base).add(3, 'month').format('YYYY-MM-DD'),
    remind_enabled: false,
    remind_offset_minutes: 15,
  }
}

const form = reactive<FormState>(defaultForm())

function colorLabel(c: UserEventColor) {
  const key = `common.userMemoColor_${c}`
  const translated = t(key)
  return translated === key ? c : translated
}

function visibilityLabel(v?: UserEventVisibility | null) {
  if (v === 'self' || v === 'all' || v === 'department') {
    return t(`common.userEventVisibility_${v}`)
  }
  return t('common.userEventSharedBadge')
}

function remindLabel(opt: number) {
  if (opt === 0) return t('common.userMemoRemindAtTime')
  if (opt >= 1440) return t('common.userEventRemindDayBefore')
  return t('common.userMemoRemindBefore', { n: opt })
}

function fillFromEvent(ev: UserEventItem) {
  const start = dayjs(ev.start_at)
  const end = dayjs(ev.end_at)
  form.title = ev.title
  form.start_date = start.format('YYYY-MM-DD')
  form.end_date = end.format('YYYY-MM-DD')
  form.all_day = ev.all_day
  form.start_time = ev.all_day ? '09:00' : start.format('HH:mm')
  form.end_time = ev.all_day ? '10:00' : end.format('HH:mm')
  form.location = ev.location || ''
  form.description = ev.description || ''
  form.color = ev.color || 'blue'
  form.visibility =
    ev.visibility === 'self' || ev.visibility === 'all' ? ev.visibility : 'department'
  form.recurrence_rule = ev.recurrence_rule || 'none'
  form.recurrence_until = ev.recurrence_until || dayjs().add(3, 'month').format('YYYY-MM-DD')
  form.remind_enabled = ev.remind_offset_minutes != null
  form.remind_offset_minutes = ev.remind_offset_minutes ?? 15
}

watch(
  () => [props.modelValue, props.editing, props.initialDate, props.initialHour] as const,
  ([open, editing]) => {
    if (!open) return
    if (editing) fillFromEvent(editing)
    else Object.assign(form, defaultForm(props.initialDate, props.initialHour))
  },
  { immediate: true },
)

function buildPayload(): UserEventCreatePayload | null {
  const title = form.title.trim()
  if (!title) return null

  const recurrenceRule = form.recurrence_rule === 'none' ? null : form.recurrence_rule
  const recurrenceUntil =
    recurrenceRule && form.recurrence_until ? form.recurrence_until : null
  const remindOffset = form.remind_enabled ? form.remind_offset_minutes : null

  if (form.all_day) {
    return {
      title,
      start_at: form.start_date,
      end_at: form.end_date,
      all_day: true,
      location: form.location.trim() || null,
      description: form.description.trim() || null,
      color: form.color,
      visibility: form.visibility,
      recurrence_rule: recurrenceRule,
      recurrence_until: recurrenceUntil,
      remind_offset_minutes: remindOffset,
    }
  }

  return {
    title,
    start_at: `${form.start_date} ${form.start_time || '09:00'}`,
    end_at: `${form.end_date} ${form.end_time || '10:00'}`,
    all_day: false,
    location: form.location.trim() || null,
    description: form.description.trim() || null,
    color: form.color,
    visibility: form.visibility,
    recurrence_rule: recurrenceRule,
    recurrence_until: recurrenceUntil,
    remind_offset_minutes: remindOffset,
  }
}

function submit() {
  const payload = buildPayload()
  if (!payload) {
    ElMessage.warning(t('common.userEventTitlePlaceholder'))
    return
  }
  emit('submit', payload)
}

function onClosed() {
  Object.assign(form, defaultForm())
}
</script>

<style scoped>
.uevent-form-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.uevent-form-head__icon {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 6px 14px rgba(13, 148, 136, 0.28);
  background: linear-gradient(145deg, #2dd4bf, #0d9488 55%, #0369a1);
  transition: background 0.2s ease;
}

.uevent-form-head__icon.is-blue { background: linear-gradient(145deg, #60a5fa, #2563eb); box-shadow: 0 6px 14px rgba(37, 99, 235, 0.28); }
.uevent-form-head__icon.is-green { background: linear-gradient(145deg, #4ade80, #16a34a); box-shadow: 0 6px 14px rgba(22, 163, 74, 0.28); }
.uevent-form-head__icon.is-amber { background: linear-gradient(145deg, #fbbf24, #d97706); box-shadow: 0 6px 14px rgba(217, 119, 6, 0.28); }
.uevent-form-head__icon.is-rose { background: linear-gradient(145deg, #fb7185, #e11d48); box-shadow: 0 6px 14px rgba(225, 29, 72, 0.28); }
.uevent-form-head__icon.is-slate { background: linear-gradient(145deg, #94a3b8, #475569); box-shadow: 0 6px 14px rgba(71, 85, 105, 0.28); }
.uevent-form-head__icon.is-violet { background: linear-gradient(145deg, #a78bfa, #7c3aed); box-shadow: 0 6px 14px rgba(124, 58, 237, 0.28); }
.uevent-form-head__icon.is-cyan { background: linear-gradient(145deg, #22d3ee, #0891b2); box-shadow: 0 6px 14px rgba(8, 145, 178, 0.28); }

.uevent-form-head__text {
  min-width: 0;
  flex: 1;
}

.uevent-form-head__title {
  font-size: 0.98rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.uevent-form-head__sub {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
  line-height: 1.3;
}

.uevent-form-head__close {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: rgba(241, 245, 249, 0.95);
  color: #64748b;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.12s ease, color 0.12s ease;
}

.uevent-form-head__close:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.uevent-form {
  --ue-form-gap: 6px;
}

.uevent-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.uevent-form :deep(.el-form-item__label) {
  margin-bottom: 3px !important;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  line-height: 1.2;
  height: auto;
}

.uevent-form :deep(.el-input__wrapper),
.uevent-form :deep(.el-textarea__inner) {
  border-radius: 9px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  background: #fff;
}

.uevent-form :deep(.el-input__wrapper:hover),
.uevent-form :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px #99f6e4 inset;
}

.uevent-form :deep(.el-input__wrapper.is-focus),
.uevent-form :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #14b8a6 inset, 0 0 0 3px rgba(20, 184, 166, 0.12) !important;
}

.uevent-form__title :deep(.el-input__inner) {
  font-weight: 650;
  font-size: 14px;
}

.uevent-form__title-item {
  margin-bottom: 12px !important;
}

.uevent-form__section {
  margin-bottom: 10px;
  padding: 8px 10px 6px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(240, 253, 250, 0.75) 0%, rgba(255, 255, 255, 0.9) 100%);
  border: 1px solid rgba(153, 246, 228, 0.55);
}

.uevent-form__section-label {
  display: none;
}

.uevent-form__section :deep(.el-form-item) {
  margin-bottom: 8px;
}

.uevent-form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.uevent-form__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 2px 0 4px;
}

.uevent-form__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid #d1fae5;
  background: #fff;
  border-radius: 999px;
  padding: 4px 11px;
  font-size: 11px;
  font-weight: 650;
  color: #475569;
  cursor: pointer;
  transition: all 0.12s ease;
}

.uevent-form__chip:hover {
  border-color: #99f6e4;
  color: #0f766e;
}

.uevent-form__chip.is-on {
  background: linear-gradient(135deg, #ccfbf1, #99f6e4);
  border-color: #5eead4;
  color: #115e59;
}

.uevent-form__chip--remind.is-on {
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  border-color: #a5b4fc;
  color: #3730a3;
}

.uevent-form__vis-item {
  margin-bottom: 10px !important;
}

.uevent-form__visibility {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  width: 100%;
}

.uevent-form__vis-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 10px;
  padding: 7px 4px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  transition: all 0.12s ease;
}

.uevent-form__vis-btn.is-self.is-on {
  background: linear-gradient(145deg, #f8fafc, #e2e8f0);
  border-color: #94a3b8;
  color: #334155;
  box-shadow: 0 4px 10px rgba(100, 116, 139, 0.18);
}

.uevent-form__vis-btn.is-department.is-on {
  background: linear-gradient(145deg, #5eead4, #0d9488);
  border-color: #0d9488;
  color: #fff;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.28);
}

.uevent-form__vis-btn.is-all.is-on {
  background: linear-gradient(145deg, #7dd3fc, #0284c7);
  border-color: #0284c7;
  color: #fff;
  box-shadow: 0 4px 12px rgba(2, 132, 199, 0.28);
}

.uevent-form__visibility-hint {
  margin: 5px 0 0;
  font-size: 10.5px;
  color: #94a3b8;
  line-height: 1.35;
}

.uevent-form__offset {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.uevent-form__offset-btn {
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 8px;
  padding: 3px 9px;
  font-size: 11px;
  color: #475569;
  cursor: pointer;
  transition: all 0.12s ease;
}

.uevent-form__offset-btn.is-on {
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  border-color: #818cf8;
  color: #3730a3;
  font-weight: 700;
}

.uevent-form__color-item :deep(.el-form-item__content) {
  line-height: 1;
}

.uevent-form__colors {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  padding-top: 2px;
}

.uevent-form__color {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.18);
}

.uevent-form__color:hover {
  transform: scale(1.08);
}

.uevent-form__color.is-active {
  transform: scale(1.14);
  box-shadow: 0 0 0 2px #fff, 0 0 0 3.5px currentColor;
}

.uevent-form__color--blue { background: #3b82f6; color: #3b82f6; }
.uevent-form__color--green { background: #22c55e; color: #22c55e; }
.uevent-form__color--amber { background: #f59e0b; color: #f59e0b; }
.uevent-form__color--rose { background: #f43f5e; color: #f43f5e; }
.uevent-form__color--slate { background: #64748b; color: #64748b; }
.uevent-form__color--violet { background: #8b5cf6; color: #8b5cf6; }
.uevent-form__color--cyan { background: #06b6d4; color: #06b6d4; }

.uevent-form__desc-item {
  margin-bottom: 0 !important;
}

.uevent-form__desc-item :deep(.el-textarea__inner) {
  min-height: 56px !important;
}

.uevent-form.is-readonly .uevent-form__chip,
.uevent-form.is-readonly .uevent-form__color,
.uevent-form.is-readonly .uevent-form__offset-btn,
.uevent-form.is-readonly .uevent-form__vis-btn {
  pointer-events: none;
  opacity: 0.88;
}

.uevent-form__footer {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.uevent-form__footer-spacer {
  flex: 1;
}

.uevent-form__btn-primary {
  border: none !important;
  border-radius: 9px !important;
  font-weight: 700 !important;
  background: linear-gradient(135deg, #14b8a6, #0d9488) !important;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.28);
}

.uevent-form__btn-ghost {
  border-radius: 9px !important;
}

.uevent-form__btn-danger {
  border-radius: 9px !important;
  color: #e11d48 !important;
  border-color: #fecdd3 !important;
}
</style>

<style>
.uevent-form-dialog.el-dialog {
  border-radius: 16px !important;
  overflow: hidden;
  border: 1px solid rgba(153, 246, 228, 0.45);
  box-shadow:
    0 24px 48px -16px rgba(15, 118, 110, 0.22),
    0 0 0 1px rgba(255, 255, 255, 0.7) inset !important;
  background:
    radial-gradient(520px 160px at 8% -20%, rgba(45, 212, 191, 0.16), transparent 55%),
    radial-gradient(420px 140px at 100% 0%, rgba(14, 165, 233, 0.1), transparent 50%),
    #fff !important;
}

.uevent-form-dialog .el-dialog__header {
  padding: 12px 14px 6px !important;
  margin-right: 0 !important;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
}

.uevent-form-dialog .el-dialog__body {
  padding: 10px 14px 6px !important;
}

.uevent-form-dialog .el-dialog__footer {
  padding: 8px 14px 12px !important;
  border-top: 1px solid rgba(226, 232, 240, 0.7);
  background: rgba(248, 250, 252, 0.65);
}
</style>
