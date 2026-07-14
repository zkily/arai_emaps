<template>
  <el-drawer
    v-model="visible"
    direction="rtl"
    size="540px"
    append-to-body
    destroy-on-close
    class="user-memo-drawer"
    :show-close="false"
    @close="onClose"
  >
    <template #header>
      <div class="umemo-hero">
        <div class="umemo-hero__lead">
          <span class="umemo-hero__icon" aria-hidden="true">
            <el-icon :size="18"><Calendar /></el-icon>
          </span>
          <div class="umemo-hero__text">
            <div class="umemo-hero__title">{{ t('common.userMemoTitle') }}</div>
            <div class="umemo-hero__sub">{{ t('common.userMemoSubtitle') }}</div>
          </div>
        </div>
        <div class="umemo-hero__right">
          <span v-if="badgeCount > 0" class="umemo-hero__badge">{{ badgeCount }}</span>
          <button type="button" class="umemo-hero__close" :aria-label="t('common.cancel')" @click="visible = false">
            <el-icon :size="16"><Close /></el-icon>
          </button>
        </div>
      </div>
    </template>

    <div v-loading="loading" class="umemo-drawer">
      <section class="umemo-panel umemo-panel--cal">
        <UserMemoCalendar
          :month-value="monthValue"
          :selected-date="selectedDate"
          :dates-with-memos="datesWithMemos"
          @select-date="onSelectDate"
          @shift-month="shiftMonth"
        />
      </section>

      <section class="umemo-panel umemo-panel--day">
        <UserMemoDayList
          v-if="!formMode"
          :selected-date="selectedDate"
          :items="selectedDayItems"
          @create="openCreateForm"
          @edit="openEditForm"
          @complete="completeMemo"
          @delete="confirmDelete"
        />

        <div v-else class="umemo-drawer__form-wrap">
          <div class="umemo-drawer__form-head">
            <div class="umemo-drawer__form-title">
              <el-icon :size="15"><EditPen /></el-icon>
              <span>{{ editingItem ? t('common.userMemoEdit') : t('common.userMemoNew') }}</span>
            </div>
            <el-button text size="small" class="umemo-drawer__back" @click="closeForm">
              <el-icon :size="14"><ArrowLeft /></el-icon>
              {{ t('common.userMemoBackToList') }}
            </el-button>
          </div>
          <UserMemoForm
            :initial-date="selectedDate"
            :editing="editingItem"
            :submitting="submitting"
            @submit="onFormSubmit"
            @cancel="closeForm"
          />
        </div>
      </section>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Calendar, Close, EditPen, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useUserMemos } from '@/composables/useUserMemos'
import UserMemoCalendar from '@/components/account/UserMemoCalendar.vue'
import UserMemoDayList from '@/components/account/UserMemoDayList.vue'
import UserMemoForm from '@/components/account/UserMemoForm.vue'
import type { UserMemoItem } from '@/api/auth/memos'

const { t } = useI18n()
const memos = useUserMemos()

const formMode = ref(false)
const editingItem = ref<UserMemoItem | null>(null)

const visible = computed({
  get: () => memos.drawerVisible.value,
  set: (v: boolean) => {
    if (v) memos.openDrawer()
    else memos.closeDrawer()
  },
})

const monthValue = computed(() => memos.monthValue.value)
const selectedDate = computed(() => memos.selectedDate.value)
const datesWithMemos = computed(() => memos.datesWithMemos.value)
const selectedDayItems = computed(() => memos.selectedDayItems.value)
const loading = computed(() => memos.loading.value)
const submitting = computed(() => memos.submitting.value)
const badgeCount = computed(() => memos.badgeCount.value)

watch(
  () => memos.drawerVisible.value,
  (open) => {
    if (open) {
      formMode.value = false
      editingItem.value = null
      void memos.loadMonth()
    }
  },
)

function onClose() {
  formMode.value = false
  editingItem.value = null
}

function onSelectDate(date: string) {
  memos.selectDate(date)
  if (formMode.value && !editingItem.value) {
    // keep create form; date sync handled by form watch
  }
}

function shiftMonth(delta: number) {
  memos.shiftMonth(delta)
}

function openCreateForm() {
  editingItem.value = null
  formMode.value = true
}

function openEditForm(item: UserMemoItem) {
  editingItem.value = item
  formMode.value = true
}

function closeForm() {
  formMode.value = false
  editingItem.value = null
}

async function onFormSubmit(payload: Parameters<typeof memos.createMemo>[0]) {
  if (editingItem.value) {
    const updated = await memos.updateMemo(editingItem.value.id, payload)
    if (updated) closeForm()
  } else {
    const created = await memos.createMemo(payload)
    if (created) closeForm()
  }
}

async function confirmDelete(id: number) {
  try {
    await ElMessageBox.confirm(t('common.userMemoDeleteConfirm'), t('common.confirm'), {
      confirmButtonText: t('common.userMemoDelete'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })
    await memos.removeMemo(id)
  } catch {
    // cancelled
  }
}

function completeMemo(id: number) {
  void memos.completeMemo(id)
}
</script>

<style scoped>
.umemo-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding-right: 4px;
}

.umemo-hero__lead {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.umemo-hero__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: #fff;
  background: linear-gradient(145deg, #0f766e 0%, #0d9488 55%, #14b8a6 100%);
  box-shadow: 0 6px 14px -6px rgba(13, 148, 136, 0.55);
  flex-shrink: 0;
}

.umemo-hero__text {
  min-width: 0;
}

.umemo-hero__title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #0f172a;
  line-height: 1.2;
}

.umemo-hero__sub {
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.3;
}

.umemo-hero__right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.umemo-hero__badge {
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: 999px;
  background: linear-gradient(135deg, #0d9488, #14b8a6);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 22px;
  text-align: center;
  box-shadow: 0 4px 10px -4px rgba(13, 148, 136, 0.5);
}

.umemo-hero__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: #f1f5f9;
  color: #64748b;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, transform 0.15s;
}

.umemo-hero__close:hover {
  background: #e2e8f0;
  color: #0f172a;
  transform: translateY(-1px);
}

.umemo-drawer {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100%;
  padding-bottom: 8px;
}

.umemo-panel {
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.umemo-panel--cal {
  padding: 14px 14px 12px;
}

.umemo-panel--day {
  padding: 14px;
  flex: 1;
  min-height: 0;
}

.umemo-drawer__form-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: umemo-fade-in 0.22s ease;
}

.umemo-drawer__form-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.umemo-drawer__form-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 14px;
  color: #0f172a;
}

.umemo-drawer__form-title .el-icon {
  color: #0d9488;
}

.umemo-drawer__back {
  color: #64748b !important;
}

@keyframes umemo-fade-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

<style>
/* drawer shell (teleported) */
.user-memo-drawer.el-drawer {
  border-radius: 16px 0 0 16px;
  overflow: hidden;
  box-shadow:
    -12px 0 40px -16px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(148, 163, 184, 0.18);
}

.user-memo-drawer .el-drawer__header {
  margin-bottom: 0;
  padding: 16px 18px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(180deg, #f8fffd 0%, #ffffff 100%);
}

.user-memo-drawer .el-drawer__body {
  padding: 14px 16px 20px;
  background:
    radial-gradient(1200px 280px at 100% 0%, rgba(20, 184, 166, 0.08), transparent 55%),
    linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}
</style>
