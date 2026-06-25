import { onMounted, onUnmounted, ref } from 'vue'
import { getAutoNews, type AutoNewsItem } from '@/api/system/autoNews'
import { useUserStore } from '@/modules/auth/stores/user'

const REFRESH_MS = 30 * 60 * 1000

/** モバイル向けに媒体名を短縮 */
export function abbreviateSource(source: string): string {
  const map: Record<string, string> = {
    乗りものニュース: '乗リ物',
    ベストカーWeb: 'ベストカー',
    'AUTOCAR JAPAN': 'AUTOCAR',
    MotorFan: 'MF',
    レスポンス: 'Response',
    webCG: 'webCG',
    'ENGINE WEB': 'ENGINE',
  }
  return map[source] ?? source
}

export function useAutoNewsTicker() {
  const userStore = useUserStore()
  const items = ref<AutoNewsItem[]>([])
  const loading = ref(false)
  const isFallback = ref(false)
  const visible = ref(false)
  let pollTimer: number | null = null

  async function reload() {
    if (!userStore.isAuthenticated) {
      items.value = []
      visible.value = false
      return
    }
    loading.value = true
    try {
      const data = await getAutoNews(20)
      if (!data.enabled) {
        items.value = []
        visible.value = false
        return
      }
      items.value = data.items ?? []
      isFallback.value = Boolean(data.isFallback)
      visible.value = items.value.length > 0
    } catch {
      items.value = []
      visible.value = false
    } finally {
      loading.value = false
    }
  }

  function openNews(url: string) {
    if (!url) return
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  onMounted(() => {
    void reload()
    pollTimer = window.setInterval(() => {
      void reload()
    }, REFRESH_MS)
  })

  onUnmounted(() => {
    if (pollTimer) {
      clearInterval(pollTimer)
    }
  })

  return {
    items,
    loading,
    isFallback,
    visible,
    reload,
    openNews,
    abbreviateSource,
  }
}
