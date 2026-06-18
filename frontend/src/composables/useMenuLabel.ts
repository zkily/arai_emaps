import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { menuConfig } from '@/router/menuConfig'

const pathToMenuItem = new Map<string, { code: string; name: string; icon?: string }>()

for (const item of menuConfig) {
  if (!item.path) continue
  if (!pathToMenuItem.has(item.path)) {
    pathToMenuItem.set(item.path, {
      code: item.code,
      name: item.name,
      icon: item.icon,
    })
  }
}

export function getMenuMetaByPath(path: string) {
  return pathToMenuItem.get(path) ?? null
}

export function useMenuLabel() {
  const { t } = useI18n()

  const labelForPath = (path: string, menuCode?: string | null) => {
    const code = menuCode || pathToMenuItem.get(path)?.code
    if (code) {
      const key = `menu.${code}`
      const translated = t(key)
      if (translated !== key) return translated
    }
    const meta = pathToMenuItem.get(path)
    return meta?.name ?? path
  }

  const iconForPath = (path: string, menuCode?: string | null) => {
    if (menuCode) {
      const fromConfig = menuConfig.find((m) => m.code === menuCode)
      if (fromConfig?.icon) return fromConfig.icon
    }
    return pathToMenuItem.get(path)?.icon ?? 'Document'
  }

  const pathToMenuCode = computed(() => {
    const map: Record<string, string> = { '/dashboard': 'DASHBOARD' }
    menuConfig.forEach((m) => {
      if (m.path) map[m.path] = m.code
    })
    return map
  })

  return {
    labelForPath,
    iconForPath,
    pathToMenuCode,
    getMenuMetaByPath,
  }
}

/** menuConfig に登録された path のみ訪問追跡対象 */
export function isTrackableMenuPath(path: string): boolean {
  const normalized = (path || '').trim()
  if (!normalized || normalized === '/login' || normalized === '/dashboard') {
    return false
  }
  return pathToMenuItem.has(normalized)
}
