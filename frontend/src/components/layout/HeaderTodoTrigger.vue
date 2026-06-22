<template>
  <el-popover
    v-model:visible="popoverVisible"
    placement="bottom-start"
    :width="popoverWidth"
    trigger="click"
    popper-class="header-todo-popper"
    @show="onPopoverShow"
  >
    <template #reference>
      <button
        type="button"
        class="header-todo-trigger"
        :class="{ 'header-todo-trigger--active': popoverVisible }"
        :title="todoTooltip"
        :aria-label="todoAriaLabel"
      >
        <span class="header-todo-trigger__divider" aria-hidden="true" />
        <span class="header-todo-trigger__core" aria-hidden="true">
          <el-icon class="header-todo-trigger__icon" :size="13"><List /></el-icon>
          <span
            v-if="pendingCount > 0"
            class="header-todo-trigger__count"
            aria-hidden="true"
          >{{ pendingBadge }}</span>
        </span>
      </button>
    </template>

    <div v-loading="loading" class="header-todo-panel">
      <div class="header-todo-panel__head">
        <div class="header-todo-panel__lead">
          <span class="header-todo-panel__icon-wrap" aria-hidden="true">
            <el-icon :size="15"><Memo /></el-icon>
          </span>
          <div>
            <div class="header-todo-panel__title">{{ t('common.headerTodoTitle') }}</div>
            <div class="header-todo-panel__subtitle">{{ t('common.headerTodoSubtitle') }}</div>
          </div>
        </div>
        <span v-if="pendingCount > 0" class="header-todo-panel__pill">
          {{ t('common.headerTodoPending', { n: pendingCount }) }}
        </span>
      </div>

      <form class="header-todo-compose" @submit.prevent="submitDraft">
        <el-input
          v-model="draft"
          :placeholder="t('common.headerTodoPlaceholder')"
          maxlength="500"
          clearable
          class="header-todo-compose__input"
          :disabled="submitting"
          @keydown.enter.prevent="submitDraft"
        />
        <el-button
          type="primary"
          class="header-todo-compose__btn"
          :disabled="!draft.trim() || submitting"
          :loading="submitting"
          @click="submitDraft"
        >
          <el-icon v-if="!submitting" :size="14"><Plus /></el-icon>
        </el-button>
      </form>

      <div v-if="!loading && sortedItems.length === 0" class="header-todo-empty">
        <span class="header-todo-empty__emoji" aria-hidden="true">✨</span>
        <p>{{ t('common.headerTodoEmpty') }}</p>
      </div>

      <el-scrollbar v-else-if="sortedItems.length > 0" max-height="320" class="header-todo-scroll">
        <ul class="header-todo-list" role="list">
          <li
            v-for="item in sortedItems"
            :key="item.id"
            class="header-todo-row"
            :class="{ 'header-todo-row--done': item.is_done === 1 }"
          >
            <el-checkbox
              :model-value="item.is_done === 1"
              class="header-todo-row__check"
              @change="toggleItem(item.id)"
            />
            <div class="header-todo-row__main">
              <el-input
                v-if="editingId === item.id"
                ref="editInputRef"
                v-model="editingText"
                size="small"
                maxlength="500"
                class="header-todo-row__edit"
                @blur="commitEdit(item.id)"
                @keydown.enter.prevent="commitEdit(item.id)"
                @keydown.esc.prevent="cancelEdit"
              />
              <span
                v-else
                class="header-todo-row__text"
                :title="t('common.headerTodoEditHint')"
                @dblclick="startEdit(item)"
              >{{ item.content }}</span>
              <div class="header-todo-row__meta">
                <span v-if="item.created_by" class="header-todo-row__author">
                  {{ t('common.headerTodoCreatedBy', { name: item.created_by }) }}
                </span>
                <span class="header-todo-row__time">
                  {{ t('common.headerTodoCreatedAt', { time: formatDateTime(item.created_at) }) }}
                </span>
                <span
                  v-if="item.is_done === 1 && item.completed_at"
                  class="header-todo-row__time header-todo-row__time--done"
                >
                  {{ t('common.headerTodoCompletedAt', { time: formatDateTime(item.completed_at) }) }}
                </span>
              </div>
            </div>
            <button
              type="button"
              class="header-todo-row__del"
              :title="t('common.headerTodoDelete')"
              :aria-label="t('common.headerTodoDelete')"
              @click="removeItem(item.id)"
            >
              <el-icon :size="13"><Delete /></el-icon>
            </button>
          </li>
        </ul>
      </el-scrollbar>

      <div v-if="doneCount > 0" class="header-todo-footer">
        <button type="button" class="header-todo-footer__clear" @click="clearDone">
          {{ t('common.headerTodoClearDone', { n: doneCount }) }}
        </button>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { List, Memo, Plus, Delete } from '@element-plus/icons-vue'
import { useHeaderTodo } from '@/composables/useHeaderTodo'
import type { UserTodoItem } from '@/composables/useHeaderTodo'

const { t } = useI18n()
const popoverVisible = ref(false)
const editingId = ref<number | null>(null)
const editingText = ref('')
const editInputRef = ref<{ focus?: () => void } | null>(null)

const popoverWidth = computed(() =>
  typeof window !== 'undefined' ? Math.min(380, Math.round(window.innerWidth * 0.92)) : 380,
)

const {
  draft,
  loading,
  submitting,
  pendingCount,
  doneCount,
  sortedItems,
  addItem,
  toggleItem,
  updateContent,
  removeItem,
  clearDone,
  reload,
} = useHeaderTodo()

const pendingBadge = computed(() => (pendingCount.value > 99 ? '99+' : String(pendingCount.value)))

const todoTooltip = computed(() => {
  if (pendingCount.value > 0) {
    return t('common.headerTodoOpenWithCount', { n: pendingCount.value })
  }
  return t('common.headerTodoOpen')
})

const todoAriaLabel = computed(() => todoTooltip.value)

function formatDateTime(value: string | null | undefined) {
  if (!value) return '--'
  return dayjs(value).tz('Asia/Tokyo').format('MM/DD HH:mm')
}

function onPopoverShow() {
  void reload()
}

async function submitDraft() {
  await addItem()
}

function startEdit(item: UserTodoItem) {
  if (item.is_done === 1) return
  editingId.value = item.id
  editingText.value = item.content
  void nextTick(() => {
    editInputRef.value?.focus?.()
  })
}

function cancelEdit() {
  editingId.value = null
  editingText.value = ''
}

async function commitEdit(id: number) {
  if (editingId.value !== id) return
  const ok = await updateContent(id, editingText.value)
  if (ok) cancelEdit()
}

</script>

<style scoped>
.header-todo-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 2px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
  color: inherit;
}

.header-todo-trigger__divider {
  width: 1px;
  height: 15px;
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(255, 255, 255, 0.32) 50%,
    transparent 100%
  );
}

.header-todo-trigger__core {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.18) 0%,
    rgba(52, 211, 153, 0.22) 55%,
    rgba(16, 185, 129, 0.18) 100%
  );
  border: 1px solid rgba(167, 243, 208, 0.35);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 8px rgba(6, 95, 70, 0.18);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.header-todo-trigger__icon {
  color: #a7f3d0;
  filter: drop-shadow(0 1px 1px rgba(6, 78, 59, 0.35));
}

.header-todo-trigger:hover .header-todo-trigger__core,
.header-todo-trigger--active .header-todo-trigger__core {
  transform: translateY(-1px) scale(1.04);
  border-color: rgba(167, 243, 208, 0.65);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.45),
    0 4px 12px rgba(16, 185, 129, 0.28);
}

.header-todo-trigger:hover .header-todo-trigger__icon,
.header-todo-trigger--active .header-todo-trigger__icon {
  color: #ecfdf5;
}

.header-todo-trigger__count {
  position: absolute;
  top: -7px;
  right: -9px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #6ee7b7 0%, #10b981 52%, #059669 100%);
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.02em;
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow:
    0 3px 10px rgba(16, 185, 129, 0.4),
    0 0 0 2px rgba(15, 23, 42, 0.35);
  pointer-events: none;
}

.header-todo-panel {
  padding: 14px 14px 12px;
  min-height: 120px;
}

.header-todo-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.22);
}

.header-todo-panel__lead {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.header-todo-panel__icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(145deg, #ecfdf5 0%, #d1fae5 100%);
  color: #059669;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.header-todo-panel__title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.01em;
}

.header-todo-panel__subtitle {
  margin-top: 2px;
  font-size: 11px;
  color: #64748b;
}

.header-todo-panel__pill {
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #047857;
  background: rgba(209, 250, 229, 0.85);
  border: 1px solid rgba(110, 231, 183, 0.45);
}

.header-todo-compose {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.header-todo-compose__input {
  flex: 1;
}

.header-todo-compose__input :deep(.el-input__wrapper) {
  border-radius: 11px;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.28) inset;
  transition: box-shadow 0.2s ease;
}

.header-todo-compose__input :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px rgba(16, 185, 129, 0.55) inset,
    0 0 0 3px rgba(16, 185, 129, 0.12);
}

.header-todo-compose__btn {
  width: 38px;
  min-width: 38px;
  padding: 0;
  border: none;
  border-radius: 11px;
  background: linear-gradient(145deg, #34d399 0%, #10b981 55%, #059669 100%);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.28);
}

.header-todo-compose__btn:hover:not(:disabled) {
  background: linear-gradient(145deg, #6ee7b7 0%, #10b981 55%, #047857 100%);
}

.header-todo-empty {
  padding: 28px 12px 22px;
  text-align: center;
  color: #64748b;
}

.header-todo-empty__emoji {
  display: block;
  font-size: 22px;
  margin-bottom: 8px;
}

.header-todo-empty p {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
}

.header-todo-scroll :deep(.el-scrollbar__wrap) {
  overscroll-behavior: contain;
}

.header-todo-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.header-todo-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 10px 10px 8px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
  border: 1px solid rgba(148, 163, 184, 0.24);
  transition:
    border-color 0.18s ease,
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.header-todo-row:hover {
  border-color: rgba(16, 185, 129, 0.35);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.08);
}

.header-todo-row--done {
  opacity: 0.78;
  background: rgba(248, 250, 252, 0.92);
}

.header-todo-row__check {
  margin-top: 2px;
  flex-shrink: 0;
}

.header-todo-row__check :deep(.el-checkbox__inner) {
  border-radius: 6px;
}

.header-todo-row__check :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #10b981;
  border-color: #10b981;
}

.header-todo-row__main {
  flex: 1;
  min-width: 0;
}

.header-todo-row__text {
  display: block;
  font-size: 12px;
  line-height: 1.5;
  color: #0f172a;
  word-break: break-word;
  cursor: text;
}

.header-todo-row--done .header-todo-row__text {
  color: #64748b;
  text-decoration: line-through;
}

.header-todo-row__edit :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.45) inset;
}

.header-todo-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-top: 5px;
}

.header-todo-row__author {
  font-size: 10px;
  line-height: 1.4;
  color: #64748b;
  font-weight: 600;
}

.header-todo-row__time {
  font-size: 10px;
  line-height: 1.4;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.header-todo-row__time--done {
  color: #10b981;
}

.header-todo-row__del {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease;
}

.header-todo-row__del:hover {
  background: rgba(254, 226, 226, 0.85);
  color: #ef4444;
}

.header-todo-footer {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(148, 163, 184, 0.28);
  display: flex;
  justify-content: flex-end;
}

.header-todo-footer__clear {
  border: none;
  background: transparent;
  padding: 4px 2px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: color 0.18s ease;
}

.header-todo-footer__clear:hover {
  color: #059669;
}
</style>

<style>
.header-todo-popper.el-popover.el-popper {
  padding: 0;
  border-radius: 14px;
  border: 1px solid rgba(167, 243, 208, 0.55);
  box-shadow:
    0 20px 44px -14px rgba(6, 95, 70, 0.28),
    0 0 0 1px rgba(255, 255, 255, 0.75) inset;
  overflow: hidden;
  background: linear-gradient(168deg, #ffffff 0%, #f8fafc 45%, #ecfdf5 100%);
}
</style>
