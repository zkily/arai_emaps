/** MES 検査実績収集：ローカル復元（多端末・オフライン計測） */

import { emptyDefectCounts } from './inspectionActualConfig'

export const INSPECTION_ACTUAL_PERSIST_KEY = 'smart_emap_mes_inspection_actual_v2'

const PERSIST_TTL_MS = 48 * 60 * 60 * 1000

export interface PersistedPlanSession {
  activeAccumMs: number
  runningSliceStart: number | null
  pausedAccumMs?: number
  pauseSliceStart?: number | null
  wallStart: number | null
  wallEnd: number | null
  defects: Record<string, number>
}

export interface PlanSessionLike {
  activeAccumMs: number
  runningSliceStart: number | null
  pausedAccumMs?: number
  pauseSliceStart?: number | null
  wallStart: number | null
  wallEnd: number | null
  defects: Record<string, number>
}

interface PersistScopeData {
  savedAt: number
  sessions: Record<string, PersistedPlanSession>
}

export interface InspectionActualPersistStoreV2 {
  v: 2
  productionDay: string
  inspectorUserId: number | null
  hideCompleted: boolean
  selectedProductCode: string | null
  activePlanId: number | null
  scopes: Record<string, PersistScopeData>
}

export interface InspectionActualPagePersistSnapshot {
  productionDay: string
  inspectorUserId: number | null
  hideCompleted: boolean
  selectedProductCode: string | null
  activePlanId: number | null
  sessions: Record<string, PersistedPlanSession>
}

function getStorage(): Storage | null {
  try {
    return localStorage
  } catch {
    return null
  }
}

function emptyStoreV2(): InspectionActualPersistStoreV2 {
  return {
    v: 2,
    productionDay: '',
    inspectorUserId: null,
    hideCompleted: false,
    selectedProductCode: null,
    activePlanId: null,
    scopes: {},
  }
}

export function makePersistScopeKey(productionDay: string): string {
  return (productionDay ?? '').trim() || '—'
}

function pruneExpiredScopes(store: InspectionActualPersistStoreV2): void {
  const now = Date.now()
  for (const [key, scope] of Object.entries(store.scopes)) {
    if (now - scope.savedAt > PERSIST_TTL_MS) delete store.scopes[key]
  }
}

function loadStore(): InspectionActualPersistStoreV2 | null {
  const storage = getStorage()
  if (!storage) return null
  try {
    const raw = storage.getItem(INSPECTION_ACTUAL_PERSIST_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<InspectionActualPersistStoreV2>
    if (parsed.v !== 2) return null
    const store: InspectionActualPersistStoreV2 = {
      v: 2,
      productionDay: typeof parsed.productionDay === 'string' ? parsed.productionDay : '',
      inspectorUserId:
        parsed.inspectorUserId != null && Number.isFinite(Number(parsed.inspectorUserId))
          ? Number(parsed.inspectorUserId)
          : null,
      hideCompleted: parsed.hideCompleted === true,
      selectedProductCode:
        typeof parsed.selectedProductCode === 'string' ? parsed.selectedProductCode : null,
      activePlanId:
        parsed.activePlanId != null && Number.isFinite(Number(parsed.activePlanId))
          ? Number(parsed.activePlanId)
          : null,
      scopes: parsed.scopes && typeof parsed.scopes === 'object' ? { ...parsed.scopes } : {},
    }
    pruneExpiredScopes(store)
    return store
  } catch {
    return null
  }
}

function writeStore(store: InspectionActualPersistStoreV2): void {
  const storage = getStorage()
  if (!storage) return
  pruneExpiredScopes(store)
  storage.setItem(INSPECTION_ACTUAL_PERSIST_KEY, JSON.stringify(store))
}

export function getScopeSessions(productionDay: string): Record<string, PersistedPlanSession> | null {
  const store = loadStore()
  if (!store) return null
  const key = makePersistScopeKey(productionDay)
  const scope = store.scopes[key]
  if (!scope) return null
  if (Date.now() - scope.savedAt > PERSIST_TTL_MS) {
    delete store.scopes[key]
    writeStore(store)
    return null
  }
  return scope.sessions
}

export function loadInspectionActualPersist(): InspectionActualPagePersistSnapshot | null {
  const store = loadStore()
  if (!store) return null
  const key = makePersistScopeKey(store.productionDay)
  const scope = store.scopes[key]
  return {
    productionDay: store.productionDay,
    inspectorUserId: store.inspectorUserId,
    hideCompleted: store.hideCompleted,
    selectedProductCode: store.selectedProductCode,
    activePlanId: store.activePlanId,
    sessions: scope?.sessions ?? {},
  }
}

export function saveInspectionActualPersist(payload: InspectionActualPagePersistSnapshot): void {
  try {
    const store = loadStore() ?? emptyStoreV2()
    const key = makePersistScopeKey(payload.productionDay)
    store.productionDay = payload.productionDay
    store.inspectorUserId = payload.inspectorUserId
    store.hideCompleted = payload.hideCompleted
    store.selectedProductCode = payload.selectedProductCode
    store.activePlanId = payload.activePlanId
    if (/^\d{4}-\d{2}-\d{2}$/.test(payload.productionDay)) {
      store.scopes[key] = {
        savedAt: Date.now(),
        sessions: payload.sessions ?? {},
      }
    }
    writeStore(store)
  } catch (e) {
    console.warn('[inspectionActual] persist save failed', e)
  }
}

export function parseDefectsFromRow(raw: unknown): Record<string, number> {
  const base = emptyDefectCounts()
  if (!raw || typeof raw !== 'object') return base
  const obj = raw as Record<string, unknown>
  for (const [k, v] of Object.entries(obj)) {
    const n = Math.round(Number(v))
    if (Number.isFinite(n) && n > 0) base[k] = n
  }
  return base
}

export function hydratePlanSessionFromRow(
  sess: PlanSessionLike,
  row: {
    mes_production_started_at?: string | null
    mes_production_ended_at?: string | null
    mes_net_production_sec?: number | null
    mes_paused_accum_sec?: number | null
    mes_production_is_paused?: number | null
    mes_defect_by_item?: Record<string, number> | null
  },
): void {
  sess.defects = parseDefectsFromRow(row.mes_defect_by_item)

  const ws = row.mes_production_started_at ? Date.parse(String(row.mes_production_started_at)) : NaN
  const we = row.mes_production_ended_at ? Date.parse(String(row.mes_production_ended_at)) : NaN
  const netSec = row.mes_net_production_sec
  const pausedSec = row.mes_paused_accum_sec

  if (!Number.isNaN(ws)) sess.wallStart = ws

  if (!Number.isNaN(we)) {
    sess.wallEnd = we
    sess.runningSliceStart = null
    sess.pauseSliceStart = null
    if (netSec != null && Number.isFinite(Number(netSec))) {
      sess.activeAccumMs = Math.max(0, Math.round(Number(netSec))) * 1000
    } else if (!Number.isNaN(ws)) {
      sess.activeAccumMs = Math.max(0, we - ws)
    }
    if (pausedSec != null && Number.isFinite(Number(pausedSec))) {
      sess.pausedAccumMs = Math.max(0, Math.round(Number(pausedSec))) * 1000
    }
    return
  }

  if (Number.isNaN(ws)) return

  const now = Date.now()
  const nsec =
    netSec != null && Number.isFinite(Number(netSec)) ? Math.max(0, Math.round(Number(netSec))) : null
  const psec =
    pausedSec != null && Number.isFinite(Number(pausedSec))
      ? Math.max(0, Math.round(Number(pausedSec)))
      : 0
  const pausedFlag =
    row.mes_production_is_paused != null && Number.isFinite(Number(row.mes_production_is_paused))
      ? Number(row.mes_production_is_paused) === 1
      : null

  sess.activeAccumMs = (nsec ?? 0) * 1000
  sess.pausedAccumMs = psec * 1000
  sess.pauseSliceStart = null

  const isPaused = pausedFlag === true || (pausedFlag === null && nsec != null)

  if (isPaused) {
    sess.runningSliceStart = null
    sess.pauseSliceStart = now
    return
  }

  sess.runningSliceStart = now
  if (nsec == null) {
    sess.activeAccumMs = 0
    sess.runningSliceStart = ws
  }
}

export function flushPauseSlice(sess: PlanSessionLike, now = Date.now()): void {
  if (sess.pauseSliceStart != null) {
    sess.pausedAccumMs = (sess.pausedAccumMs ?? 0) + Math.max(0, now - sess.pauseSliceStart)
    sess.pauseSliceStart = null
  }
}

export function flushRunningSlice(sess: PlanSessionLike, now = Date.now()): void {
  if (sess.runningSliceStart != null) {
    sess.activeAccumMs += Math.max(0, now - sess.runningSliceStart)
    sess.runningSliceStart = null
  }
}

export function freezePausedAccumMs(sess: PlanSessionLike, at = Date.now()): number {
  if (sess.wallStart == null) return 0
  let ms = sess.pausedAccumMs ?? 0
  if (sess.pauseSliceStart != null) {
    ms += Math.max(0, at - sess.pauseSliceStart)
  }
  return ms
}

export function reconcileInProgressTimer(sess: PlanSessionLike, now = Date.now()): void {
  if (sess.wallEnd != null || sess.wallStart == null) return
  if (sess.runningSliceStart != null) {
    if (sess.runningSliceStart < sess.wallStart) sess.runningSliceStart = sess.wallStart
    return
  }
  const maxNet = Math.max(0, now - sess.wallStart)
  if (sess.activeAccumMs > maxNet) sess.activeAccumMs = maxNet
}

export function formatDurationMs(ms: number): string {
  const totalSec = Math.max(0, Math.floor(ms / 1000))
  const h = Math.floor(totalSec / 3600)
  const m = Math.floor((totalSec % 3600) / 60)
  const s = totalSec % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

export function emptySession(): PlanSessionLike {
  return {
    activeAccumMs: 0,
    runningSliceStart: null,
    pausedAccumMs: 0,
    pauseSliceStart: null,
    wallStart: null,
    wallEnd: null,
    defects: emptyDefectCounts(),
  }
}

export function serializePlanSessions(
  sessions: Record<number, PlanSessionLike>,
): Record<string, PersistedPlanSession> {
  const out: Record<string, PersistedPlanSession> = {}
  for (const [id, s] of Object.entries(sessions)) {
    out[id] = {
      activeAccumMs: s.activeAccumMs,
      runningSliceStart: s.runningSliceStart,
      pausedAccumMs: s.pausedAccumMs ?? 0,
      pauseSliceStart: s.pauseSliceStart ?? null,
      wallStart: s.wallStart,
      wallEnd: s.wallEnd,
      defects: { ...s.defects },
    }
  }
  return out
}

export function applyPersistedSessionsForScope(
  scopeDay: string,
  rowIds: number[],
  ensureSession: (planId: number) => PlanSessionLike,
): boolean {
  const scopeSessions = getScopeSessions(scopeDay)
  if (!scopeSessions) return false
  let any = false
  for (const id of rowIds) {
    const sess = ensureSession(id)
    const p = scopeSessions[String(id)]
    if (!p) continue
    if (sess.wallEnd != null || sess.wallStart != null) continue
    if (p.wallStart != null) {
      sess.wallStart = p.wallStart
      sess.activeAccumMs = p.activeAccumMs ?? 0
      sess.runningSliceStart = p.runningSliceStart ?? p.wallStart
      sess.pausedAccumMs = p.pausedAccumMs ?? 0
      sess.pauseSliceStart = p.pauseSliceStart ?? null
      sess.defects = { ...p.defects }
      any = true
    }
    if (sess.wallStart != null && sess.wallEnd == null) reconcileInProgressTimer(sess)
  }
  return any
}
