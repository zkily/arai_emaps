import type { PatchChamferingManagementBody } from '@/api/chamferingManagement'

export const OFFLINE_PATCH_QUEUE_KEY = 'smart_emap_mes_chamfering_offline_patch_v1'

interface OfflinePatchQueueItem {
  scopeKey: string
  planId: number
  body: PatchChamferingManagementBody
  updatedAt: number
}

interface OfflinePatchQueueStore {
  v: 1
  items: OfflinePatchQueueItem[]
}

function readQueue(): OfflinePatchQueueStore {
  try {
    const raw = localStorage.getItem(OFFLINE_PATCH_QUEUE_KEY)
    if (!raw) return { v: 1, items: [] }
    const parsed = JSON.parse(raw) as unknown
    if (!parsed || typeof parsed !== 'object') return { v: 1, items: [] }
    const p = parsed as Partial<OfflinePatchQueueStore>
    if (p.v !== 1 || !Array.isArray(p.items)) return { v: 1, items: [] }
    return { v: 1, items: p.items.filter((x) => x && typeof x.planId === 'number') }
  } catch {
    return { v: 1, items: [] }
  }
}

function writeQueue(store: OfflinePatchQueueStore): void {
  try {
    localStorage.setItem(OFFLINE_PATCH_QUEUE_KEY, JSON.stringify(store))
  } catch (e) {
    console.warn('[chamferingActual] offline queue save failed', e)
  }
}

/** ネットワーク不通・タイムアウト・5xx */
export function isNetworkOrServerDownError(e: unknown): boolean {
  if (!e || typeof e !== 'object') return true
  const err = e as { response?: { status?: number } | null; code?: string }
  if (err.response == null) return true
  const status = err.response.status
  if (status != null && status >= 500) return true
  if (err.code === 'ECONNABORTED' || err.code === 'ERR_NETWORK') return true
  return false
}

export function enqueueOfflinePatch(
  scopeKey: string,
  planId: number,
  body: PatchChamferingManagementBody,
): void {
  const store = readQueue()
  const idx = store.items.findIndex((x) => x.scopeKey === scopeKey && x.planId === planId)
  if (idx >= 0) {
    store.items[idx] = {
      scopeKey,
      planId,
      body: { ...store.items[idx].body, ...body },
      updatedAt: Date.now(),
    }
  } else {
    store.items.push({ scopeKey, planId, body: { ...body }, updatedAt: Date.now() })
  }
  writeQueue(store)
}

export function getOfflineQueueCount(scopeKey?: string | null): number {
  const store = readQueue()
  if (!scopeKey) return store.items.length
  return store.items.filter((x) => x.scopeKey === scopeKey).length
}

export function clearOfflinePatchForPlan(scopeKey: string, planId: number): void {
  const store = readQueue()
  const next = store.items.filter((x) => !(x.scopeKey === scopeKey && x.planId === planId))
  if (next.length === store.items.length) return
  writeQueue({ v: 1, items: next })
}

export async function flushOfflinePatchQueue(
  patchFn: (
    planId: number,
    body: PatchChamferingManagementBody,
  ) => Promise<{ success?: boolean; message?: string }>,
  options?: { scopeKey?: string | null },
): Promise<{ ok: number; fail: number }> {
  const store = readQueue()
  const scopeKey = options?.scopeKey
  const targets =
    scopeKey != null ? store.items.filter((x) => x.scopeKey === scopeKey) : [...store.items]
  if (targets.length === 0) return { ok: 0, fail: 0 }

  let ok = 0
  let fail = 0
  const remaining: OfflinePatchQueueItem[] = store.items.filter(
    (x) => scopeKey != null && x.scopeKey !== scopeKey,
  )

  for (const item of targets) {
    try {
      const res = await patchFn(item.planId, item.body)
      if (res && res.success === false) {
        fail += 1
        remaining.push(item)
      } else {
        ok += 1
      }
    } catch (e) {
      if (isNetworkOrServerDownError(e)) {
        fail += 1
        remaining.push(item)
        break
      }
      fail += 1
      remaining.push(item)
    }
  }

  writeQueue({ v: 1, items: remaining })
  return { ok, fail }
}
