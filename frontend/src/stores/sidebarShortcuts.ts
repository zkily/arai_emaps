import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as shortcutsApi from '@/api/auth/shortcuts'
import type { ShortcutItem } from '@/api/auth/shortcuts'
import { i18n } from '@/i18n'

const MAX_PINNED = 12
const VISIT_DEBOUNCE_MS = 5 * 60 * 1000

export const useSidebarShortcutsStore = defineStore('sidebarShortcuts', () => {
  const pinned = ref<ShortcutItem[]>([])
  const frequent = ref<ShortcutItem[]>([])
  const loaded = ref(false)
  const loading = ref(false)
  const lastVisitSent = new Map<string, number>()

  const pinnedPaths = computed(() => pinned.value.map((item) => item.path))
  const hasShortcuts = computed(() => pinned.value.length > 0 || frequent.value.length > 0)

  function isPinned(path: string) {
    return pinnedPaths.value.includes(path)
  }

  async function load() {
    loading.value = true
    try {
      const data = await shortcutsApi.getShortcuts()
      pinned.value = data.pinned ?? []
      frequent.value = data.frequent ?? []
      loaded.value = true
    } catch {
      pinned.value = []
      frequent.value = []
      loaded.value = false
    } finally {
      loading.value = false
    }
  }

  function reset() {
    pinned.value = []
    frequent.value = []
    loaded.value = false
    lastVisitSent.clear()
  }

  async function savePins(paths: string[]) {
    const data = await shortcutsApi.updatePins(paths)
    pinned.value = data.pinned ?? []
    frequent.value = data.frequent ?? []
    loaded.value = true
  }

  async function togglePin(path: string) {
    const current = [...pinnedPaths.value]
    const idx = current.indexOf(path)

    if (idx >= 0) {
      current.splice(idx, 1)
      await savePins(current)
      return
    }

    if (current.length >= MAX_PINNED) {
      ElMessage.warning(
        String(i18n.global.t('sidebar.PIN_LIMIT', { max: MAX_PINNED })),
      )
      return
    }

    current.push(path)
    await savePins(current)
  }

  async function recordVisit(path: string) {
    const normalized = (path || '').trim()
    if (!normalized) return

    const now = Date.now()
    const last = lastVisitSent.get(normalized) ?? 0
    if (now - last < VISIT_DEBOUNCE_MS) return

    lastVisitSent.set(normalized, now)
    try {
      await shortcutsApi.recordPageVisit(normalized)
      if (loaded.value) {
        const data = await shortcutsApi.getShortcuts()
        pinned.value = data.pinned ?? []
        frequent.value = data.frequent ?? []
      }
    } catch {
      lastVisitSent.delete(normalized)
    }
  }

  return {
    pinned,
    frequent,
    loaded,
    loading,
    pinnedPaths,
    hasShortcuts,
    isPinned,
    load,
    reset,
    togglePin,
    recordVisit,
    savePins,
  }
})
