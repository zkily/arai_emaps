<template>
  <div class="umemo-day">
    <div class="umemo-day__head">
      <div class="umemo-day__head-text">
        <div class="umemo-day__title">{{ dayLabel }}</div>
        <div class="umemo-day__count">
          <template v-if="items.length">
            {{ t('common.userMemoDayCount', { n: items.length }) }}
          </template>
          <template v-else>
            {{ t('common.userMemoDayEmptyShort') }}
          </template>
        </div>
      </div>
      <button type="button" class="umemo-day__add" @click="emit('create')">
        <el-icon :size="14"><Plus /></el-icon>
        {{ t('common.userMemoNew') }}
      </button>
    </div>

    <div v-if="items.length === 0" class="umemo-day__empty">
      <div class="umemo-day__empty-icon" aria-hidden="true">
        <el-icon :size="22"><Notebook /></el-icon>
      </div>
      <p class="umemo-day__empty-title">{{ t('common.userMemoDayEmpty') }}</p>
    </div>

    <ul v-else class="umemo-day__list" role="list">
      <li
        v-for="item in items"
        :key="item.id"
        class="umemo-day__row"
        :class="[`umemo-day__row--${item.color || 'blue'}`, { 'is-done': item.status === 1 }]"
      >
        <button type="button" class="umemo-day__body" @click="emit('edit', item)">
          <div class="umemo-day__meta">
            <span class="umemo-day__time">{{ timeLabel(item) }}</span>
            <span
              v-if="item.remind_offset_minutes != null && item.status === 0"
              class="umemo-day__remind"
            >
              <el-icon :size="11"><Bell /></el-icon>
              {{ remindLabel(item) }}
            </span>
          </div>
          <div class="umemo-day__name">{{ item.title }}</div>
          <div v-if="item.content" class="umemo-day__content">{{ item.content }}</div>
        </button>
        <div class="umemo-day__actions">
          <button
            v-if="item.status === 0"
            type="button"
            class="umemo-day__action umemo-day__action--ok"
            :title="t('common.userMemoComplete')"
            @click.stop="emit('complete', item.id)"
          >
            <el-icon :size="14"><Check /></el-icon>
          </button>
          <button
            type="button"
            class="umemo-day__action umemo-day__action--del"
            :title="t('common.userMemoDelete')"
            @click.stop="emit('delete', item.id)"
          >
            <el-icon :size="14"><Delete /></el-icon>
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Plus, Check, Delete, Bell, Notebook } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import type { UserMemoItem } from '@/api/auth/memos'

const props = defineProps<{
  selectedDate: string
  items: UserMemoItem[]
}>()

const emit = defineEmits<{
  create: []
  edit: [item: UserMemoItem]
  complete: [id: number]
  delete: [id: number]
}>()

const { t, locale } = useI18n()

const dayLabel = computed(() => {
  const d = dayjs(props.selectedDate)
  const loc = locale.value
  if (loc === 'en') return d.format('dddd, MMM D')
  if (loc === 'ja') return d.format('M月D日（ddd）')
  if (loc === 'vi') return d.format('DD/MM/YYYY')
  return d.format('M月D日 dddd')
})

function timeLabel(item: UserMemoItem) {
  if (!item.memo_time) return t('common.userMemoAllDay')
  return item.memo_time.slice(0, 5)
}

function remindLabel(item: UserMemoItem) {
  const n = item.remind_offset_minutes ?? 0
  if (n === 0) return t('common.userMemoRemindAtTime')
  return t('common.userMemoRemindBefore', { n })
}
</script>

<style scoped>
.umemo-day {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.umemo-day__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.umemo-day__head-text {
  min-width: 0;
}

.umemo-day__title {
  font-weight: 700;
  font-size: 15px;
  letter-spacing: -0.01em;
  color: #0f172a;
}

.umemo-day__count {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.umemo-day__add {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 12px;
  border: none;
  border-radius: 9px;
  background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px -4px rgba(13, 148, 136, 0.55);
  transition: transform 0.15s, filter 0.15s, box-shadow 0.15s;
}

.umemo-day__add:hover {
  transform: translateY(-1px);
  filter: brightness(1.05);
  box-shadow: 0 6px 14px -4px rgba(13, 148, 136, 0.6);
}

.umemo-day__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 36px 16px;
  border-radius: 12px;
  border: 1px dashed rgba(148, 163, 184, 0.45);
  background: rgba(248, 250, 252, 0.7);
}

.umemo-day__empty-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  color: #0d9488;
  background: rgba(20, 184, 166, 0.12);
}

.umemo-day__empty-title {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  text-align: center;
  line-height: 1.5;
  max-width: 260px;
}

.umemo-day__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.umemo-day__row {
  display: flex;
  align-items: stretch;
  gap: 0;
  border-radius: 12px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  overflow: hidden;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}

.umemo-day__row:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px -10px rgba(15, 23, 42, 0.18);
  border-color: rgba(13, 148, 136, 0.28);
}

.umemo-day__row::before {
  content: '';
  width: 4px;
  flex-shrink: 0;
  background: #3b82f6;
}

.umemo-day__row--blue::before { background: linear-gradient(180deg, #3b82f6, #60a5fa); }
.umemo-day__row--green::before { background: linear-gradient(180deg, #16a34a, #4ade80); }
.umemo-day__row--amber::before { background: linear-gradient(180deg, #d97706, #fbbf24); }
.umemo-day__row--rose::before { background: linear-gradient(180deg, #e11d48, #fb7185); }
.umemo-day__row--slate::before { background: linear-gradient(180deg, #475569, #94a3b8); }

.umemo-day__row.is-done {
  opacity: 0.58;
}

.umemo-day__row.is-done .umemo-day__name {
  text-decoration: line-through;
  color: #94a3b8;
}

.umemo-day__body {
  flex: 1;
  min-width: 0;
  text-align: left;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 11px 10px 11px 12px;
}

.umemo-day__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  margin-bottom: 4px;
}

.umemo-day__time {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #0f766e;
  font-variant-numeric: tabular-nums;
  background: rgba(20, 184, 166, 0.1);
  padding: 2px 7px;
  border-radius: 999px;
}

.umemo-day__remind {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: #b45309;
  background: rgba(245, 158, 11, 0.12);
  padding: 2px 7px;
  border-radius: 999px;
}

.umemo-day__name {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.35;
}

.umemo-day__content {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.umemo-day__actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  padding: 8px 8px 8px 0;
}

.umemo-day__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: #f8fafc;
  color: #64748b;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, transform 0.15s;
}

.umemo-day__action:hover {
  transform: translateY(-1px);
}

.umemo-day__action--ok:hover {
  background: rgba(34, 197, 94, 0.14);
  color: #16a34a;
}

.umemo-day__action--del:hover {
  background: rgba(244, 63, 94, 0.12);
  color: #e11d48;
}
</style>
