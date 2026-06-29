<template>
  <div class="fdp-cal" v-loading="loading">
    <p class="fdp-cal__hint">{{ t('formingDailyPlan.calendarHint') }}</p>
    <div v-for="proc in processOptions" :key="proc.key" class="fdp-cal__row">
      <span class="fdp-cal__label">{{ proc.label }}</span>
      <div class="fdp-cal__days">
        <label
          v-for="d in dates"
          :key="`${proc.key}-${d}`"
          class="fdp-cal__day"
          :class="{ 'is-checked': isChecked(proc.key, d) }"
          :title="d"
        >
          <input type="checkbox" :checked="isChecked(proc.key, d)" @change="toggle(proc.key, d)" />
          <span>{{ d.slice(8) }}</span>
        </label>
      </div>
    </div>
    <div class="fdp-cal__actions">
      <el-button size="small" type="primary" :loading="saving" @click="save">{{ t('formingDailyPlan.saveBtn') }}</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { ProcessRunCalendarItem } from '@/api/formingDailyPlan'
import { putProcessRunDays } from '@/api/formingDailyPlan'
import { FORMING_PLAN_PROCESS_OPTIONS } from './formingDailyPlanConstants'

const props = defineProps<{
  startDate: string
  endDate: string
  dates: string[]
  items: ProcessRunCalendarItem[]
  loading?: boolean
}>()

const emit = defineEmits<{ saved: [items: ProcessRunCalendarItem[]]; change: [items: ProcessRunCalendarItem[]] }>()

const { t } = useI18n()
const processOptions = FORMING_PLAN_PROCESS_OPTIONS.filter((p) => p.key !== 'warehouse')
const localItems = ref<ProcessRunCalendarItem[]>([])
const saving = ref(false)

watch(
  () => props.items,
  (v) => {
    localItems.value = processOptions.map((p) => {
      const found = v.find((i) => i.process_key === p.key)
      return { process_key: p.key, dates: [...(found?.dates ?? [])] }
    })
  },
  { immediate: true, deep: true }
)

function isChecked(processKey: string, date: string) {
  const item = localItems.value.find((i) => i.process_key === processKey)
  return item?.dates.includes(date) ?? false
}

function toggle(processKey: string, date: string) {
  const item = localItems.value.find((i) => i.process_key === processKey)
  if (!item) return
  const idx = item.dates.indexOf(date)
  if (idx >= 0) item.dates.splice(idx, 1)
  else item.dates.push(date)
  item.dates.sort()
  emit('change', localItems.value)
}

async function save() {
  saving.value = true
  try {
    const res = await putProcessRunDays({
      startDate: props.startDate,
      endDate: props.endDate,
      items: localItems.value,
    })
    const data = (res as { data?: { items?: ProcessRunCalendarItem[] } }).data
    ElMessage.success(t('formingDailyPlan.calendarSaved'))
    emit('saved', data?.items ?? localItems.value)
  } catch {
    ElMessage.error(t('formingDailyPlan.calendarSaveFailed'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.fdp-cal__hint {
  font-size: 12px;
  color: #909399;
  margin: 0 0 10px;
}
.fdp-cal__row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: flex-start;
}
.fdp-cal__label {
  width: 48px;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  padding-top: 4px;
}
.fdp-cal__days {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
}
.fdp-cal__day {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 4px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  font-size: 11px;
  cursor: pointer;
  user-select: none;
}
.fdp-cal__day.is-checked {
  background: #ecf5ff;
  border-color: #409eff;
}
.fdp-cal__day input {
  display: none;
}
.fdp-cal__actions {
  margin-top: 12px;
}
</style>
