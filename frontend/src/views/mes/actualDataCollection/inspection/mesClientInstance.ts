/** 検査 MES：端末ごとの永続 ID（サーバー mes_client_instance_id と対応） */
const STORAGE_KEY = 'smart_emap_mes_inspection_client_instance_v1'

export function getMesClientInstanceId(): string {
  if (typeof window === 'undefined') return 'ssr-anon'
  try {
    let id = localStorage.getItem(STORAGE_KEY)?.trim()
    if (!id) {
      id =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : `mes-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
      localStorage.setItem(STORAGE_KEY, id)
    }
    return id
  } catch {
    return `mes-fallback-${Date.now()}`
  }
}
