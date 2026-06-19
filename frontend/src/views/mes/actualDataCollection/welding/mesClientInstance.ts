/** 溶接 MES：端末ごとの永続 ID（サーバー mes_client_instance_id と対応） */
const STORAGE_KEY = 'smart_emap_mes_welding_client_instance_v1'

function userBackupKey(userId: number): string {
  return `smart_emap_mes_welding_client_instance_u${userId}`
}

function readStorageItem(key: string): string | null {
  try {
    return localStorage.getItem(key)?.trim() || null
  } catch {
    return null
  }
}

function writeStorageItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* ignore quota / private mode */
  }
}

/** ログインユーザー別バックアップから primary を復元（キャッシュ削除対策） */
export function restoreMesClientInstanceFromUserBackup(userId: number | null | undefined): void {
  if (typeof window === 'undefined' || userId == null) return
  if (readStorageItem(STORAGE_KEY)) return
  const backup = readStorageItem(userBackupKey(userId))
  if (backup) writeStorageItem(STORAGE_KEY, backup)
}

export function getMesClientInstanceId(userId?: number | null): string {
  if (typeof window === 'undefined') return 'ssr-anon'
  try {
    restoreMesClientInstanceFromUserBackup(userId ?? null)
    let id = readStorageItem(STORAGE_KEY)
    if (!id) {
      id =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : `mes-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
      writeStorageItem(STORAGE_KEY, id)
    }
    if (userId != null && Number.isFinite(Number(userId))) {
      writeStorageItem(userBackupKey(Number(userId)), id)
    }
    return id
  } catch {
    return `mes-fallback-${Date.now()}`
  }
}
