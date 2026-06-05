/** MES 検査実績収集：ローカル復元（多端末・オフライン計測） */

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
  /** 本端末で「生産開始」した planId（他端末の在産行と区別） */
  operatedPlanIds?: number[]
}

export interface InspectionActualPersistStoreV2 {
  v: 2
  productionDay: string
  inspectorUserId: number | null
  selectedProductCode: string | null
  activePlanId: number | null
  scopes: Record<string, PersistScopeData>
}

export interface InspectionActualPagePersistSnapshot {
  productionDay: string
  inspectorUserId: number | null
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

function emptyStoreV2(): InspectionActualPersistStoreV2 {
  return {
    v: 2,
    productionDay: '',
    inspectorUserId: null,
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
  const operatedPlanIds = Array.isArray(scope?.operatedPlanIds)
    ? scope.operatedPlanIds.filter((id) => Number.isFinite(Number(id))).map((id) => Number(id))
    : []
  return {
    productionDay: store.productionDay,
    inspectorUserId: store.inspectorUserId,
    selectedProductCode: store.selectedProductCode,
    activePlanId: store.activePlanId,
    sessions: scope?.sessions ?? {},
    operatedPlanIds,
  }
}

export function saveInspectionActualPersist(payload: InspectionActualPagePersistSnapshot): void {
  try {
    const store = loadStore() ?? emptyStoreV2()
    const key = makePersistScopeKey(payload.productionDay)
    store.productionDay = payload.productionDay
    store.inspectorUserId = payload.inspectorUserId
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
    console.warn('[inspectionActual] persist save failed', e)
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

  if (pausedFlag === true) {
    sess.runningSliceStart = null
    sess.pauseSliceStart = now
    if (nsec == null) {
      sess.pausedAccumMs = Math.max(0, now - ws)
    }
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

/** 净稼働時間（表示用・セッションを変更しない）。一時停止中は activeAccumMs のみで表示が止まる */
export function readNetProductionMs(sess: PlanSessionLike, at = Date.now()): number {
  if (sess.wallStart == null) return 0
  let ms = sess.activeAccumMs ?? 0
  if (sess.runningSliceStart != null && sess.wallEnd == null) {
    ms += Math.max(0, at - sess.runningSliceStart)
  }
  return Math.max(0, ms)
}

/**
 * 再開時：稼働時間表示を「生産開始〜現在の壁時計 − 一時停止累計」で補正し、净稼働と running スライスを整合。
 */
export function correctNetProductionFromWallClock(
  sess: PlanSessionLike,
  wallStartMs: number,
  now = Date.now(),
): void {
  const wallMs = Math.max(0, now - wallStartMs)
  const pauseMs = sess.pausedAccumMs ?? 0
  sess.activeAccumMs = Math.max(0, wallMs - pauseMs)
  sess.runningSliceStart = now
  sess.pauseSliceStart = null
}

/** 明示的一時停止のみ（ボタン操作分。セッションを変更しない） */
export function readExplicitPausedAccumMs(sess: PlanSessionLike, at = Date.now()): number {
  if (sess.wallStart == null) return 0
  let ms = sess.pausedAccumMs ?? 0
  if (sess.pauseSliceStart != null) {
    ms += Math.max(0, at - sess.pauseSliceStart)
  }
  return Math.max(0, ms)
}

/**
 * 一時停止累計の表示用（セッションを変更しない）。
 * 稼働中は明示停止分のみ。生産終了後（wallEnd あり）は壁時計−净稼働の補正も参照。
 */
export function readPausedAccumMs(sess: PlanSessionLike, at = Date.now()): number {
  const explicit = readExplicitPausedAccumMs(sess, at)
  if (sess.wallStart == null || sess.wallEnd == null) {
    return explicit
  }

  const wallSpan = Math.max(0, sess.wallEnd - sess.wallStart)
  let netMs = sess.activeAccumMs ?? 0
  const derived = Math.max(0, wallSpan - Math.min(Math.max(0, netMs), wallSpan))
  return Math.max(explicit, derived)
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
  let netMs = sess.activeAccumMs ?? 0
  if (sess.runningSliceStart != null && sess.wallEnd == null) {
    netMs += Math.max(0, at - sess.runningSliceStart)
  }
  const derived = Math.max(0, wallSpan - Math.min(Math.max(0, netMs), wallSpan))
  const total = Math.max(ms, derived)
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

  // 在産中だが running/pause スライスが無い → 稼働中とみなし復帰（暗黙の一時停止累計を防ぐ）
  sess.runningSliceStart = now
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
  rowIds: number[],
  ensureSession: (planId: number) => PlanSessionLike,
): boolean {
  const scopeSessions = getScopeSessions(scopeDay)
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
