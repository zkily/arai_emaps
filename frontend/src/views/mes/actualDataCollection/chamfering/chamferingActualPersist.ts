/** MES 面取実績収集画面のローカル復元（リロード・タブ閉鎖・設備切替後も計測状態を保持） */

export const CHAMFERING_ACTUAL_PERSIST_KEY = 'smart_emap_mes_chamfering_actual_v2'

const LEGACY_V1_KEY = 'smart_emap_mes_chamfering_actual_v1'

const PERSIST_TTL_MS = 48 * 60 * 60 * 1000

export interface PersistedPlanSession {
  activeAccumMs: number
  runningSliceStart: number | null
  /** 一時停止〜再開の累計（ミリ秒） */
  pausedAccumMs?: number
  /** 現在の一時停止開始時刻（停止中のみ） */
  pauseSliceStart?: number | null
  wallStart: number | null
  wallEnd: number | null
  operatorUserId: number | null
  setupTimeMin: number | undefined
}

export interface PlanSessionLike {
  activeAccumMs: number
  runningSliceStart: number | null
  pausedAccumMs?: number
  pauseSliceStart?: number | null
  wallStart: number | null
  wallEnd: number | null
  operatorUserId: number | null
  setupTimeMin: number | undefined
}

interface PersistScopeData {
  savedAt: number
  sessions: Record<string, PersistedPlanSession>
}

export interface ChamferingActualPersistStoreV2 {
  v: 2
  productionDay: string
  selectedMachineId: number | null
  hideCompleted: boolean
  scopes: Record<string, PersistScopeData>
}

/** v1 互換（移行用） */
interface CuttingActualPagePersistV1 {
  v: 1
  savedAt: number
  productionDay: string
  selectedMachineId: number | null
  hideCompleted: boolean
  sessions: Record<string, PersistedPlanSession>
}

export interface CuttingActualPagePersistSnapshot {
  productionDay: string
  selectedMachineId: number | null
  hideCompleted: boolean
  sessions: Record<string, PersistedPlanSession>
}

function getStorage(): Storage | null {
  try {
    return localStorage
  } catch {
    return null
  }
}

function readRawKeys(): string[] {
  const keys = [CHAMFERING_ACTUAL_PERSIST_KEY, LEGACY_V1_KEY]
  try {
    const legacySession = sessionStorage.getItem(LEGACY_V1_KEY)
    if (legacySession) keys.push(`session:${LEGACY_V1_KEY}`)
  } catch {
    /* ignore */
  }
  return keys
}

function readAnyRaw(): { raw: string; fromKey: string } | null {
  const storage = getStorage()
  if (!storage) return null
  for (const key of [CHAMFERING_ACTUAL_PERSIST_KEY, LEGACY_V1_KEY]) {
    const raw = storage.getItem(key)
    if (raw) return { raw, fromKey: key }
  }
  try {
    const raw = sessionStorage.getItem(LEGACY_V1_KEY)
    if (raw) {
      storage.setItem(CHAMFERING_ACTUAL_PERSIST_KEY, raw)
      sessionStorage.removeItem(LEGACY_V1_KEY)
      return { raw, fromKey: LEGACY_V1_KEY }
    }
  } catch {
    /* ignore */
  }
  return null
}

function writeStore(store: ChamferingActualPersistStoreV2): void {
  const storage = getStorage()
  if (!storage) return
  storage.setItem(CHAMFERING_ACTUAL_PERSIST_KEY, JSON.stringify(store))
  try {
    sessionStorage.removeItem(LEGACY_V1_KEY)
  } catch {
    /* ignore */
  }
}

function removeStored(): void {
  const storage = getStorage()
  if (!storage) return
  for (const key of readRawKeys()) {
    if (key.startsWith('session:')) continue
    try {
      storage.removeItem(key)
    } catch {
      /* ignore */
    }
  }
  try {
    sessionStorage.removeItem(LEGACY_V1_KEY)
  } catch {
    /* ignore */
  }
}

export function makePersistScopeKey(productionDay: string, machineId: number | null): string {
  const day = (productionDay ?? '').trim() || '—'
  return `${day}::${machineId ?? 'none'}`
}

function emptyStoreV2(): ChamferingActualPersistStoreV2 {
  return {
    v: 2,
    productionDay: '',
    selectedMachineId: null,
    hideCompleted: true,
    scopes: {},
  }
}

function migrateV1ToV2(p: CuttingActualPagePersistV1): ChamferingActualPersistStoreV2 {
  const store = emptyStoreV2()
  store.productionDay = p.productionDay
  store.selectedMachineId = p.selectedMachineId
  store.hideCompleted = p.hideCompleted
  const key = makePersistScopeKey(p.productionDay, p.selectedMachineId)
  store.scopes[key] = { savedAt: p.savedAt, sessions: p.sessions ?? {} }
  return store
}

function pruneExpiredScopes(store: ChamferingActualPersistStoreV2): void {
  const now = Date.now()
  for (const [key, scope] of Object.entries(store.scopes)) {
    if (now - scope.savedAt > PERSIST_TTL_MS) delete store.scopes[key]
  }
}

function parseStore(raw: string): ChamferingActualPersistStoreV2 | null {
  const parsed = JSON.parse(raw) as unknown
  if (!parsed || typeof parsed !== 'object') return null
  const p = parsed as { v?: number }

  if (p.v === 2) {
    const s = parsed as Partial<ChamferingActualPersistStoreV2>
    const store: ChamferingActualPersistStoreV2 = {
      v: 2,
      productionDay: typeof s.productionDay === 'string' ? s.productionDay : '',
      selectedMachineId:
        s.selectedMachineId != null && Number.isFinite(Number(s.selectedMachineId))
          ? Number(s.selectedMachineId)
          : null,
      hideCompleted: s.hideCompleted !== false,
      scopes: s.scopes && typeof s.scopes === 'object' ? { ...s.scopes } : {},
    }
    pruneExpiredScopes(store)
    return store
  }

  if (p.v === 1 && typeof (parsed as CuttingActualPagePersistV1).savedAt === 'number') {
    const v1 = parsed as CuttingActualPagePersistV1
    if (Date.now() - v1.savedAt > PERSIST_TTL_MS) return null
    return migrateV1ToV2(v1)
  }

  return null
}

function loadStore(): ChamferingActualPersistStoreV2 | null {
  try {
    const found = readAnyRaw()
    if (!found) return null
    const store = parseStore(found.raw)
    if (!store) {
      removeStored()
      return null
    }
    if (Object.keys(store.scopes).length === 0 && !store.productionDay) return null
    writeStore(store)
    return store
  } catch {
    return null
  }
}

export function getScopeSessions(
  productionDay: string,
  machineId: number | null,
): Record<string, PersistedPlanSession> | null {
  const store = loadStore()
  if (!store) return null
  const key = makePersistScopeKey(productionDay, machineId)
  const scope = store.scopes[key]
  if (!scope) return null
  if (Date.now() - scope.savedAt > PERSIST_TTL_MS) {
    delete store.scopes[key]
    writeStore(store)
    return null
  }
  return scope.sessions
}

/** 画面フィルタ（生産日・最後に選んだ設備・確定済除外） */
export function loadChamferingActualPersist(): CuttingActualPagePersistSnapshot | null {
  const store = loadStore()
  if (!store) return null
  const key = makePersistScopeKey(store.productionDay, store.selectedMachineId)
  const scope = store.scopes[key]
  return {
    productionDay: store.productionDay,
    selectedMachineId: store.selectedMachineId,
    hideCompleted: store.hideCompleted,
    sessions: scope?.sessions ?? {},
  }
}

export function saveChamferingActualPersist(payload: CuttingActualPagePersistSnapshot): void {
  try {
    const store = loadStore() ?? emptyStoreV2()
    const key = makePersistScopeKey(payload.productionDay, payload.selectedMachineId)
    store.productionDay = payload.productionDay
    store.selectedMachineId = payload.selectedMachineId
    store.hideCompleted = payload.hideCompleted
    if (payload.selectedMachineId != null && /^\d{4}-\d{2}-\d{2}$/.test(payload.productionDay)) {
      store.scopes[key] = {
        savedAt: Date.now(),
        sessions: payload.sessions ?? {},
      }
    }
    pruneExpiredScopes(store)
    writeStore(store)
  } catch (e) {
    console.warn('[chamferingActual] persist save failed', e)
  }
}

export function clearChamferingActualPersist(): void {
  removeStored()
}

/** 一覧行の MES 列からセッションを復元（表示時間は開始〜現在の壁時計差で算出） */
function mesProductionIsPausedFromRow(row: {
  mes_production_is_paused?: number | null
}): boolean | null {
  const raw = row.mes_production_is_paused
  if (raw === null || raw === undefined) return null
  const n = Number(raw)
  if (!Number.isFinite(n)) return null
  return n === 1
}

export function hydratePlanSessionFromRow(
  sess: PlanSessionLike,
  row: {
    mes_production_started_at?: string | null
    mes_production_ended_at?: string | null
    mes_net_production_sec?: number | null
    mes_paused_accum_sec?: number | null
    mes_production_is_paused?: number | null
  },
): void {
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
    } else if (!Number.isNaN(ws)) {
      const wallSpan = Math.max(0, we - ws)
      sess.pausedAccumMs = Math.max(0, wallSpan - (sess.activeAccumMs ?? 0))
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
  const pausedFlag = mesProductionIsPausedFromRow(row)

  sess.activeAccumMs = (nsec ?? 0) * 1000
  sess.pausedAccumMs = psec * 1000
  sess.pauseSliceStart = null

  const isPaused =
    pausedFlag === true || (pausedFlag === null && nsec != null)

  if (isPaused) {
    sess.runningSliceStart = null
    sess.pauseSliceStart = now
    if (nsec == null) {
      const wallSpan = Math.max(0, now - ws)
      sess.pausedAccumMs = Math.max(0, wallSpan)
    }
    return
  }

  sess.runningSliceStart = now
  if (nsec == null) {
    sess.activeAccumMs = 0
    sess.runningSliceStart = ws
  }
}

/** 停止中の区間を pausedAccumMs に合算 */
export function flushPauseSlice(sess: PlanSessionLike, now = Date.now()): void {
  if (sess.pauseSliceStart != null) {
    sess.pausedAccumMs = (sess.pausedAccumMs ?? 0) + Math.max(0, now - sess.pauseSliceStart)
    sess.pauseSliceStart = null
  }
}

/**
 * 生産終了時に一時停止累計を確定（明示累計と壁時計−净稼働の大きい方）。
 * 戻り値はミリ秒。
 */
export function freezePausedAccumMs(sess: PlanSessionLike, at = Date.now()): number {
  if (sess.wallStart == null) {
    sess.pausedAccumMs = 0
    sess.pauseSliceStart = null
    return 0
  }

  let ms = sess.pausedAccumMs ?? 0
  if (sess.pauseSliceStart != null) {
    ms += Math.max(0, at - sess.pauseSliceStart)
    sess.pauseSliceStart = null
  }

  const wallEnd = sess.wallEnd ?? at
  const wallSpan = Math.max(0, wallEnd - sess.wallStart)
  let netMs = sess.activeAccumMs
  if (sess.runningSliceStart != null && sess.wallEnd == null) {
    netMs += Math.max(0, at - sess.runningSliceStart)
  }
  const derived = Math.max(0, wallSpan - Math.min(Math.max(0, netMs), wallSpan))
  const total = Math.max(ms, derived)
  sess.pausedAccumMs = total
  return total
}

/** 未終了セッションのタイマー整合（表示上限・切片起点） */
export function reconcileInProgressTimer(sess: PlanSessionLike, now = Date.now()): void {
  if (sess.wallEnd != null || sess.wallStart == null) return

  if (sess.runningSliceStart != null) {
    if (sess.runningSliceStart < sess.wallStart) {
      sess.runningSliceStart = sess.wallStart
    }
    return
  }

  const maxNet = Math.max(0, now - sess.wallStart)
  if (sess.activeAccumMs > maxNet) {
    sess.activeAccumMs = maxNet
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
      operatorUserId: s.operatorUserId,
      setupTimeMin: s.setupTimeMin,
    }
  }
  return out
}

/** サーバー同期済みセッションにローカル状態をマージ（作業者・段取・停止累計タイマー） */
export function mergePlanSessionFromPersist(
  base: PlanSessionLike,
  persisted: PersistedPlanSession | undefined,
): boolean {
  if (!persisted) return false
  let changed = false

  if (base.wallEnd == null) {
    if (persisted.operatorUserId != null && persisted.operatorUserId !== base.operatorUserId) {
      base.operatorUserId = persisted.operatorUserId
      changed = true
    }
    if (persisted.setupTimeMin !== undefined && persisted.setupTimeMin !== base.setupTimeMin) {
      base.setupTimeMin = persisted.setupTimeMin
      changed = true
    }
  }

  if (base.wallEnd != null || persisted.wallEnd != null) {
    return changed
  }

  // サーバー復元済み（他端末と共有）の計測はローカルで上書きしない
  if (base.wallStart != null) {
    return changed
  }

  if (base.wallStart == null && persisted.wallStart != null) {
    base.wallStart = persisted.wallStart
    base.activeAccumMs = persisted.activeAccumMs ?? 0
    base.runningSliceStart = persisted.runningSliceStart ?? persisted.wallStart
    base.pausedAccumMs = persisted.pausedAccumMs ?? 0
    base.pauseSliceStart = persisted.pauseSliceStart ?? null
    return true
  }

  const sameWallStart =
    base.wallStart != null &&
    persisted.wallStart != null &&
    Math.abs(persisted.wallStart - base.wallStart) < 5000

  if (!sameWallStart) return changed

  const paused = Math.max(base.pausedAccumMs ?? 0, persisted.pausedAccumMs ?? 0)
  if (paused !== (base.pausedAccumMs ?? 0)) {
    base.pausedAccumMs = paused
    changed = true
  }

  const accum = Math.max(base.activeAccumMs, persisted.activeAccumMs ?? 0)
  if (accum !== base.activeAccumMs) {
    base.activeAccumMs = accum
    changed = true
  }

  if (persisted.pauseSliceStart != null) {
    if (base.runningSliceStart != null) {
      return changed
    }
    if (base.pauseSliceStart !== persisted.pauseSliceStart || base.runningSliceStart != null) {
      base.pauseSliceStart = persisted.pauseSliceStart
      base.runningSliceStart = null
      changed = true
    }
  } else if (persisted.runningSliceStart != null) {
    if (base.runningSliceStart !== persisted.runningSliceStart || base.pauseSliceStart != null) {
      base.runningSliceStart = persisted.runningSliceStart
      base.pauseSliceStart = null
      changed = true
    }
  }

  return changed
}

export function applyPersistedSessionsForScope(
  scopeDay: string,
  scopeMachineId: number | null,
  rowIds: number[],
  ensureSession: (planId: number) => PlanSessionLike,
): boolean {
  const scopeSessions = getScopeSessions(scopeDay, scopeMachineId)
  if (!scopeSessions) return false

  let any = false
  for (const id of rowIds) {
    const sess = ensureSession(id)
    const p = scopeSessions[String(id)]
    if (p && mergePlanSessionFromPersist(sess, p)) any = true
    if (sess.wallStart != null && sess.wallEnd == null) {
      reconcileInProgressTimer(sess)
    }
  }
  return any
}
