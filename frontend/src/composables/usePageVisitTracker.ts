import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSidebarShortcutsStore } from '@/stores/sidebarShortcuts'
import { isTrackableMenuPath } from '@/composables/useMenuLabel'
import { useUserStore } from '@/modules/auth/stores/user'

export function usePageVisitTracker() {
  const route = useRoute()
  const shortcutsStore = useSidebarShortcutsStore()
  const userStore = useUserStore()

  watch(
    () => route.path,
    (path) => {
      if (!userStore.isAuthenticated) return
      if (!isTrackableMenuPath(path)) return
      shortcutsStore.recordVisit(path)
    },
    { immediate: true },
  )
}
