/** MES 検査実績収集：ローカル復元（多端末・オフライン計測） */

export const WELDING_ACTUAL_PERSIST_KEY = 'smart_emap_mes_welding_actual_v2'

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
  /** 本端末で「生産開始」した planId（他端末の在産行と区別） */
  operatedPlanIds?: number[]
}

export interface WeldingActualPersistStoreV2 {
  v: 2
  productionDay: string
  selectedWeldingMachineId: number | null
  operatorUserId: number | null
  selectedProductCode: string | null
  activePlanId: number | null
  scopes: Record<string, PersistScopeData>
}

export interface WeldingActualPagePersistSnapshot {
  productionDay: string
  selectedWeldingMachineId: number | null
  operatorUserId: number | null
  selectedProductCode: string | null
  activePlanId: number | null
  sessions: Record<string, PersistedPlanSession>
  operatedPlanIds?: number[]
}

function getStorage(): Storage | null {
  try {
    return localStorage
  } catch {
    return null
  }
}

function emptyStoreV2(): WeldingActualPersistStoreV2 {
  return {
    v: 2,
    productionDay: '',
    selectedWeldingMachineId: null,
    operatorUserId: null,
    selectedProductCode: null,
    activePlanId: null,
    scopes: {},
  }
}

export function makePersistScopeKey(productionDay: string, machineId: number | null): string {
  const day = (productionDay ?? '').trim() || '—'
  return `${day}::${machineId ?? 'none'}`
}

function pruneExpiredScopes(store: WeldingActualPersistStoreV2): void {
  const now = Date.now()
  for (const [key, scope] of Object.entries(store.scopes)) {
    if (now - scope.savedAt > PERSIST_TTL_MS) delete store.scopes[key]
  }
}

function loadStore(): WeldingActualPersistStoreV2 | null {
  const storage = getStorage()
  if (!storage) return null
  try {
    const raw = storage.getItem(WELDING_ACTUAL_PERSIST_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<WeldingActualPersistStoreV2>
    if (parsed.v !== 2) return null
    const store: WeldingActualPersistStoreV2 = {
      v: 2,
      productionDay: typeof parsed.productionDay === 'string' ? parsed.productionDay : '',
      selectedWeldingMachineId:
        parsed.selectedWeldingMachineId != null &&
        Number.isFinite(Number(parsed.selectedWeldingMachineId))
          ? Number(parsed.selectedWeldingMachineId)
          : null,
      operatorUserId:
        parsed.operatorUserId != null && Number.isFinite(Number(parsed.operatorUserId))
          ? Number(parsed.operatorUserId)
          : null,
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

function writeStore(store: WeldingActualPersistStoreV2): void {
  const storage = getStorage()
  if (!storage) return
  pruneExpiredScopes(store)
  storage.setItem(WELDING_ACTUAL_PERSIST_KEY, JSON.stringify(store))
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

export interface WeldingPersistMachineActivity {
  machineId: number
  planId: number
  paused: boolean
}

/** 生産モニター：指定生産日の全設備スコープから在産セッションを収集 */
export function collectWeldingPersistForMonitorDay(productionDay: string): {
  sessionsByPlanId: Map<number, PersistedPlanSession>
  machineActivities: WeldingPersistMachineActivity[]
} {
  const sessionsByPlanId = new Map<number, PersistedPlanSession>()
  const machineActivities: WeldingPersistMachineActivity[] = []
  const store = loadStore()
  if (!store) return { sessionsByPlanId, machineActivities }

  const day = (productionDay ?? '').trim()
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return { sessionsByPlanId, machineActivities }

  const prefix = `${day}::`
  const now = Date.now()
  for (const [scopeKey, scope] of Object.entries(store.scopes)) {
    if (!scopeKey.startsWith(prefix)) continue
    if (now - scope.savedAt > PERSIST_TTL_MS) continue
    const machinePart = scopeKey.slice(prefix.length)
    if (machinePart === 'none') continue
    const machineId = Number(machinePart)
    if (!Number.isFinite(machineId)) continue

    for (const [planIdStr, sess] of Object.entries(scope.sessions ?? {})) {
      const planId = Number(planIdStr)
      if (!Number.isFinite(planId)) continue
      sessionsByPlanId.set(planId, sess)
      if (sess.wallStart != null && sess.wallEnd == null) {
        const paused = sess.pauseSliceStart != null
        machineActivities.push({ machineId, planId, paused })
      }
    }
  }
  return { sessionsByPlanId, machineActivities }
}

/** 生産モニター：当該設備スコープの溶接作業者（localStorage、同一端末のみ） */
export function getWeldingPersistOperatorUserId(
  productionDay: string,
  machineId: number,
): number | null {
  const store = loadStore()
  if (!store) return null
  const day = (productionDay ?? '').trim()
  if (store.productionDay !== day || store.selectedWeldingMachineId !== machineId) return null
  const id = store.operatorUserId
  if (id == null || !Number.isFinite(Number(id)) || Number(id) <= 0) return null
  return Number(id)
}

export function loadWeldingActualPersist(): WeldingActualPagePersistSnapshot | null {
  const store = loadStore()
  if (!store) return null
  const key = makePersistScopeKey(store.productionDay, store.selectedWeldingMachineId)
  const scope = store.scopes[key]
  const operatedPlanIds = Array.isArray(scope?.operatedPlanIds)
    ? scope.operatedPlanIds.filter((id) => Number.isFinite(Number(id))).map((id) => Number(id))
    : []
  return {
    productionDay: store.productionDay,
    selectedWeldingMachineId: store.selectedWeldingMachineId,
    operatorUserId: store.operatorUserId,
    selectedProductCode: store.selectedProductCode,
    activePlanId: store.activePlanId,
    sessions: scope?.sessions ?? {},
    operatedPlanIds,
  }
}

export function saveWeldingActualPersist(payload: WeldingActualPagePersistSnapshot): void {
  try {
    const store = loadStore() ?? emptyStoreV2()
    const key = makePersistScopeKey(payload.productionDay, payload.selectedWeldingMachineId)
    store.productionDay = payload.productionDay
    store.selectedWeldingMachineId = payload.selectedWeldingMachineId
    store.operatorUserId = payload.operatorUserId
    store.selectedProductCode = payload.selectedProductCode
    store.activePlanId = payload.activePlanId
    if (/^\d{4}-\d{2}-\d{2}$/.test(payload.productionDay)) {
      const prev = store.scopes[key]
      store.scopes[key] = {
        savedAt: Date.now(),
        sessions: payload.sessions ?? {},
        operatedPlanIds: payload.operatedPlanIds ?? prev?.operatedPlanIds ?? [],
      }
    }
    writeStore(store)
  } catch (e) {
    console.warn('[weldingActual] persist save failed', e)
  }
}

export function parseDefectsFromRow(raw: unknown): Record<string, number> {
  const out: Record<string, number> = {}
  if (!raw || typeof raw !== 'object') return out
  const obj = raw as Record<string, unknown>
  for (const [k, v] of Object.entries(obj)) {
    const n = Math.round(Number(v))
    if (Number.isFinite(n) && n > 0) out[k] = n
  }
  return out
}

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
    } else {
      sess.pausedAccumMs = 0
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

  if (pausedFlag === true) {
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

/** 一時停止累計の表示用（一時停止ボタン操作分のみ。セッションを変更しない） */
export function readPausedAccumMs(sess: PlanSessionLike, at = Date.now()): number {
  if (sess.wallStart == null) return 0

  let ms = sess.pausedAccumMs ?? 0
  if (sess.pauseSliceStart != null) {
    ms += Math.max(0, at - sess.pauseSliceStart)
  }
  return Math.max(0, ms)
}

/** 生産終了時に一時停止累計を確定（一時停止ボタンで積み上げた分のみ）。戻り値はミリ秒。 */
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

  const total = Math.max(0, ms)
  sess.pausedAccumMs = total
  return total
}

export function reconcileInProgressTimer(sess: PlanSessionLike, now = Date.now()): void {
  if (sess.wallEnd != null || sess.wallStart == null) return

  if (sess.pauseSliceStart != null) {
    if (sess.pauseSliceStart < sess.wallStart) sess.pauseSliceStart = sess.wallStart
    return
  }

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

export function emptySession(defects: Record<string, number> = {}): PlanSessionLike {
  return {
    activeAccumMs: 0,
    runningSliceStart: null,
    pausedAccumMs: 0,
    pauseSliceStart: null,
    wallStart: null,
    wallEnd: null,
    defects: { ...defects },
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
  machineId: number | null,
  rowIds: number[],
  ensureSession: (planId: number) => PlanSessionLike,
): boolean {
  const scopeSessions = getScopeSessions(scopeDay, machineId)
  if (!scopeSessions) return false
  let any = false
  for (const id of rowIds) {
    const sess = ensureSession(id)
    const p = scopeSessions[String(id)]
    if (!p || p.wallStart == null || p.wallEnd != null) continue
    // サーバー同期済みの在産でも、本端末の未終了タイマーを優先復元
    sess.wallStart = p.wallStart
    sess.wallEnd = null
    sess.activeAccumMs = p.activeAccumMs ?? 0
    sess.runningSliceStart = p.runningSliceStart ?? p.wallStart
    sess.pausedAccumMs = p.pausedAccumMs ?? 0
    sess.pauseSliceStart = p.pauseSliceStart ?? null
    sess.defects = { ...p.defects }
    reconcileInProgressTimer(sess)
    any = true
  }
  return any
}
