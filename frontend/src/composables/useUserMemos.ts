import { ref, computed, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { useUserStore } from '@/modules/auth/stores/user'
import * as memosApi from '@/api/auth/memos'
import type { UserMemoItem, UserMemoCreatePayload, UserMemoUpdatePayload } from '@/api/auth/memos'

export type { UserMemoItem }

const POLL_INTERVAL_MS = 45_000

let shared: ReturnType<typeof createUserMemosState> | null = null

function monthRange(ym: string): { from: string; to: string } {
  const base = dayjs(`${ym}-01`)
  return {
    from: base.startOf('month').format('YYYY-MM-DD'),
    to: base.endOf('month').format('YYYY-MM-DD'),
  }
}

function createUserMemosState() {
  const { t } = useI18n()
  const userStore = useUserStore()

  const items = ref<UserMemoItem[]>([])
  const loading = ref(false)
  const submitting = ref(false)
  const monthValue = ref(dayjs().format('YYYY-MM'))
  const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
  const drawerVisible = ref(false)
  const badgeCount = ref(0)
  const activeReminders = ref<UserMemoItem[]>([])
  const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)
  const processingReminderIds = new Set<number>()

  const datesWithMemos = computed(() => {
    const map = new Map<string, UserMemoItem[]>()
    for (const item of items.value) {
      if (item.status === 1) continue
      const list = map.get(item.memo_date) ?? []
      list.push(item)
      map.set(item.memo_date, list)
    }
    return map
  })

  const selectedDayItems = computed(() =>
    items.value
      .filter((item) => item.memo_date === selectedDate.value)
      .sort((a, b) => {
        if (a.status !== b.status) return a.status - b.status
        const ta = a.memo_time ?? '99:99'
        const tb = b.memo_time ?? '99:99'
        return ta.localeCompare(tb)
      }),
  )

  async function loadMonth(ym?: string) {
    if (!userStore.isAuthenticated) {
      items.value = []
      return
    }
    const target = ym ?? monthValue.value
    const { from, to } = monthRange(target)
    loading.value = true
    try {
      const data = await memosApi.getUserMemos(from, to)
      items.value = data.list ?? []
    } catch {
      ElMessage.error(t('common.userMemoLoadFailed'))
    } finally {
      loading.value = false
    }
  }

  async function refreshUpcoming() {
    if (!userStore.isAuthenticated) {
      badgeCount.value = 0
      return
    }
    try {
      const data = await memosApi.getUserMemosUpcoming()
      badgeCount.value = data.badge_count ?? 0
      const due = data.due_now ?? []
      for (const memo of due) {
        await fireReminder(memo)
      }
    } catch {
      // サイレント（バックグラウンドポーリング）
    }
  }

  async function fireReminder(memo: UserMemoItem) {
    if (processingReminderIds.has(memo.id)) return
    if (activeReminders.value.some((row) => row.id === memo.id)) return
    processingReminderIds.add(memo.id)
    try {
      // 先に ack してポーリング再発火を防ぎ、ダイアログは手動閉じるまで表示し続ける
      await memosApi.ackUserMemoReminder(memo.id)
      const local = items.value.find((row) => row.id === memo.id)
      if (local) {
        local.reminded_at = dayjs().format('YYYY-MM-DDTHH:mm:ss')
      }
      activeReminders.value = [...activeReminders.value, memo]
      await refreshUpcoming()
    } catch {
      // 他タブ等で既に ack 済みの場合は無視
    } finally {
      processingReminderIds.delete(memo.id)
    }
  }

  function dismissCurrentReminder() {
    if (activeReminders.value.length === 0) return
    activeReminders.value = activeReminders.value.slice(1)
  }

  function dismissAllReminders() {
    activeReminders.value = []
  }

  function startPolling() {
    stopPolling()
    void refreshUpcoming()
    pollTimer.value = setInterval(() => {
      void refreshUpcoming()
    }, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    if (pollTimer.value) {
      clearInterval(pollTimer.value)
      pollTimer.value = null
    }
  }

  watch(
    () => userStore.user?.id,
    (id) => {
      if (id) {
        void loadMonth()
        startPolling()
      } else {
        items.value = []
        badgeCount.value = 0
        activeReminders.value = []
        stopPolling()
      }
    },
    { immediate: true },
  )

  function openDrawer(date?: string) {
    drawerVisible.value = true
    if (date) selectedDate.value = date
    void loadMonth()
  }

  function closeDrawer() {
    drawerVisible.value = false
  }

  function selectDate(date: string) {
    selectedDate.value = date
    const ym = date.slice(0, 7)
    if (ym !== monthValue.value) {
      monthValue.value = ym
      void loadMonth(ym)
    }
  }

  function shiftMonth(delta: number) {
    monthValue.value = dayjs(`${monthValue.value}-01`).add(delta, 'month').format('YYYY-MM')
    void loadMonth()
  }

  async function createMemo(payload: UserMemoCreatePayload) {
    submitting.value = true
    try {
      const created = await memosApi.createUserMemo(payload)
      const createdYm = created.memo_date.slice(0, 7)
      if (createdYm === monthValue.value) {
        items.value.push(created)
      } else {
        await loadMonth()
      }
      await refreshUpcoming()
      return created
    } catch {
      ElMessage.error(t('common.userMemoSaveFailed'))
      return null
    } finally {
      submitting.value = false
    }
  }

  async function updateMemo(id: number, payload: UserMemoUpdatePayload) {
    submitting.value = true
    try {
      const updated = await memosApi.updateUserMemo(id, payload)
      const idx = items.value.findIndex((row) => row.id === id)
      if (idx >= 0) {
        if (updated.memo_date.slice(0, 7) === monthValue.value) {
          items.value[idx] = updated
        } else {
          items.value.splice(idx, 1)
        }
      } else if (updated.memo_date.slice(0, 7) === monthValue.value) {
        items.value.push(updated)
      }
      await refreshUpcoming()
      return updated
    } catch {
      ElMessage.error(t('common.userMemoSaveFailed'))
      return null
    } finally {
      submitting.value = false
    }
  }

  async function completeMemo(id: number) {
    try {
      const updated = await memosApi.completeUserMemo(id)
      const item = items.value.find((row) => row.id === id)
      if (item) Object.assign(item, updated)
      await refreshUpcoming()
    } catch {
      ElMessage.error(t('common.userMemoUpdateFailed'))
    }
  }

  async function removeMemo(id: number) {
    try {
      await memosApi.deleteUserMemo(id)
      items.value = items.value.filter((row) => row.id !== id)
      await refreshUpcoming()
    } catch {
      ElMessage.error(t('common.userMemoDeleteFailed'))
    }
  }

  return {
    items,
    loading,
    submitting,
    monthValue,
    selectedDate,
    drawerVisible,
    badgeCount,
    activeReminders,
    datesWithMemos,
    selectedDayItems,
    loadMonth,
    refreshUpcoming,
    openDrawer,
    closeDrawer,
    selectDate,
    shiftMonth,
    createMemo,
    updateMemo,
    completeMemo,
    removeMemo,
    dismissCurrentReminder,
    dismissAllReminders,
    startPolling,
    stopPolling,
  }
}

export function useUserMemos() {
  if (!shared) {
    shared = createUserMemosState()
  }
  return shared
}

export function useUserMemosLifecycle() {
  const memos = useUserMemos()
  onUnmounted(() => {
    // シングルトンは破棄しない（HeaderBar と Drawer で共有）
  })
  return memos
}
