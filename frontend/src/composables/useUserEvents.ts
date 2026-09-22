import { ref, watch, onUnmounted } from 'vue'
import { useUserStore } from '@/modules/auth/stores/user'
import * as eventsApi from '@/api/auth/events'
import type { UserEventItem } from '@/api/auth/events'

const POLL_INTERVAL_MS = 45_000

let shared: ReturnType<typeof createUserEventsState> | null = null

function createUserEventsState() {
  const userStore = useUserStore()
  const activeReminders = ref<UserEventItem[]>([])
  const badgeCount = ref(0)
  const todayCount = ref(0)
  const weekCount = ref(0)
  const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)
  const processingIds = new Set<string>()

  function reminderKey(ev: UserEventItem) {
    return `${ev.id}:${ev.occurrence_date || ev.start_at.slice(0, 10)}`
  }

  async function refreshUpcoming() {
    if (!userStore.isAuthenticated) {
      badgeCount.value = 0
      todayCount.value = 0
      weekCount.value = 0
      return
    }
    try {
      const data = await eventsApi.getUserEventsUpcoming()
      badgeCount.value = data.badge_count ?? 0
      todayCount.value = data.today_count ?? 0
      weekCount.value = data.week_count ?? 0
      for (const ev of data.due_now ?? []) {
        await fireReminder(ev)
      }
    } catch {
      // background poll
    }
  }

  async function fireReminder(ev: UserEventItem) {
    const key = reminderKey(ev)
    if (processingIds.has(key)) return
    if (activeReminders.value.some((row) => reminderKey(row) === key)) return
    processingIds.add(key)
    try {
      await eventsApi.ackUserEventReminder(ev.id, ev.occurrence_date)
      activeReminders.value = [...activeReminders.value, ev]
      await refreshUpcoming()
    } catch {
      // already acked elsewhere
    } finally {
      processingIds.delete(key)
    }
  }

  function dismissCurrentReminder() {
    if (!activeReminders.value.length) return
    activeReminders.value = activeReminders.value.slice(1)
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
      if (id) startPolling()
      else {
        activeReminders.value = []
        badgeCount.value = 0
        todayCount.value = 0
        weekCount.value = 0
        stopPolling()
      }
    },
    { immediate: true },
  )

  onUnmounted(() => stopPolling())

  return {
    activeReminders,
    badgeCount,
    todayCount,
    weekCount,
    refreshUpcoming,
    dismissCurrentReminder,
    startPolling,
    stopPolling,
  }
}

export function useUserEvents() {
  if (!shared) shared = createUserEventsState()
  return shared
}
