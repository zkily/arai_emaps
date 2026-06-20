/** MES 溶接実績収集：ローカル復元（多端末・オフライン計測） */

import {
  buildMesDefectByItemPayload,
  parseDefectAtFromRow,
  parseDefectsFromRow,
} from '../shared/mesDefectByItem'

export { parseDefectsFromRow, parseDefectAtFromRow, buildMesDefectByItemPayload }

export const WELDING_ACTUAL_PERSIST_KEY = 'smart_emap_mes_welding_actual_v2'

const PERSIST_TTL_MS = 48 * 60 * 60 * 1000

export interface PersistedPlanSession {
  activeAccumMs: number
  runningSliceStart: number | null
  pausedAccumMs?: number
  pauseSliceStart?: number | null
  breakAccumMs?: number
  breakSliceStart?: number | null
  wallStart: number | null
  wallEnd: number | null
  defects: Record<string, number>
  defectAtByItem?: Record<string, string>
}

export interface PlanSessionLike {
  activeAccumMs: number
  runningSliceStart: number | null
  pausedAccumMs?: number
  pauseSliceStart?: number | null
  breakAccumMs?: number
  breakSliceStart?: number | null
  wallStart: number | null
  wallEnd: number | null
  defects: Record<string, number>
  defectAtByItem?: Record<string, string>
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
        machineActivities.push({
          machineId,
          planId,
          paused: sess.pauseSliceStart != null || sess.breakSliceStart != null,
        })
      }
    }
  }
  return { sessionsByPlanId, machineActivities }
}

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
    mes_break_sec?: number | null
    mes_stop_sec?: number | null
    mes_production_is_paused?: number | null
    mes_defect_by_item?: unknown
  },
): void {
  sess.defects = parseDefectsFromRow(row.mes_defect_by_item)
  sess.defectAtByItem = parseDefectAtFromRow(row.mes_defect_by_item)

  const ws = row.mes_production_started_at ? Date.parse(String(row.mes_production_started_at)) : NaN
  const we = row.mes_production_ended_at ? Date.parse(String(row.mes_production_ended_at)) : NaN

  if (Number.isNaN(ws) && Number.isNaN(we)) {
    sess.wallStart = null
    sess.wallEnd = null
    sess.activeAccumMs = 0
    sess.runningSliceStart = null
    sess.pausedAccumMs = 0
    sess.pauseSliceStart = null
    sess.breakAccumMs = 0
    sess.breakSliceStart = null
    return
  }

  const netSec = row.mes_net_production_sec
  const pausedSec = row.mes_paused_accum_sec
  const breakSec = row.mes_break_sec
  const stopSec = row.mes_stop_sec

  if (!Number.isNaN(ws)) sess.wallStart = ws

  if (!Number.isNaN(we)) {
    sess.wallEnd = we
    sess.runningSliceStart = null
    sess.pauseSliceStart = null
    sess.breakSliceStart = null
    if (netSec != null && Number.isFinite(Number(netSec))) {
      sess.activeAccumMs = Math.max(0, Math.round(Number(netSec))) * 1000
    } else if (!Number.isNaN(ws)) {
      sess.activeAccumMs = Math.max(0, we - ws)
    }
    if (breakSec != null && Number.isFinite(Number(breakSec))) {
      sess.breakAccumMs = Math.max(0, Math.round(Number(breakSec))) * 1000
    } else {
      sess.breakAccumMs = 0
    }
    if (stopSec != null && Number.isFinite(Number(stopSec))) {
      sess.pausedAccumMs = Math.max(0, Math.round(Number(stopSec))) * 1000
    } else if (pausedSec != null && Number.isFinite(Number(pausedSec))) {
      sess.pausedAccumMs = Math.max(0, Math.round(Number(pausedSec))) * 1000
    } else if (!Number.isNaN(ws)) {
      const wallSpan = Math.max(0, we - ws)
      const breakMs = sess.breakAccumMs ?? 0
      sess.pausedAccumMs = Math.max(0, wallSpan - (sess.activeAccumMs ?? 0) - breakMs)
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

  const bsec =
    breakSec != null && Number.isFinite(Number(breakSec))
      ? Math.max(0, Math.round(Number(breakSec)))
      : 0
  const stopFromRow =
    stopSec != null && Number.isFinite(Number(stopSec))
      ? Math.max(0, Math.round(Number(stopSec)))
      : null

  sess.activeAccumMs = (nsec ?? 0) * 1000
  sess.breakAccumMs = bsec * 1000
  sess.breakSliceStart = null
  sess.pausedAccumMs = (stopFromRow ?? psec) * 1000
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

export function flushBreakSlice(sess: PlanSessionLike, now = Date.now()): void {
  if (sess.breakSliceStart != null) {
    sess.breakAccumMs = (sess.breakAccumMs ?? 0) + Math.max(0, now - sess.breakSliceStart)
    sess.breakSliceStart = null
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

/** 明示的一時停止のみ（ボタン操作分。セッションを変更しない） */
export function readExplicitPausedAccumMs(sess: PlanSessionLike, at = Date.now()): number {
  if (sess.wallStart == null) return 0
  let ms = sess.pausedAccumMs ?? 0
  if (sess.pauseSliceStart != null) {
    ms += Math.max(0, at - sess.pauseSliceStart)
  }
  return Math.max(0, ms)
}

/** 明示的休憩のみ（ボタン操作分。セッションを変更しない） */
export function readExplicitBreakAccumMs(sess: PlanSessionLike, at = Date.now()): number {
  if (sess.wallStart == null) return 0
  let ms = sess.breakAccumMs ?? 0
  if (sess.breakSliceStart != null) {
    ms += Math.max(0, at - sess.breakSliceStart)
  }
  return Math.max(0, ms)
}

/**
 * 再開時：稼働時間表示を「生産開始〜現在の壁時計 − 一時停止 − 休憩」で補正し、净稼働と running スライスを整合。
 */
export function correctNetProductionFromWallClock(
  sess: PlanSessionLike,
  wallStartMs: number,
  now = Date.now(),
): void {
  const wallMs = Math.max(0, now - wallStartMs)
  const pauseMs = readExplicitPausedAccumMs(sess, now)
  const breakMs = readExplicitBreakAccumMs(sess, now)
  sess.activeAccumMs = Math.max(0, wallMs - pauseMs - breakMs)
  sess.runningSliceStart = now
  sess.pauseSliceStart = null
  sess.breakSliceStart = null
}

/** 作業再開・サーバー同期後：稼働時間を生産開始時刻基準で補正 */
export function alignSessionElapsedFromWallClock(
  sess: PlanSessionLike,
  row?: {
    mes_production_started_at?: string | null
    mes_net_production_sec?: number | null
  } | null,
  now = Date.now(),
): void {
  if (sess.wallEnd != null || sess.wallStart == null) return
  const ws =
    sess.wallStart ??
    (row?.mes_production_started_at
      ? Date.parse(String(row.mes_production_started_at))
      : Number.NaN)
  if (!Number.isFinite(ws)) return

  const isPaused = sess.pauseSliceStart != null
  const isOnBreak = sess.breakSliceStart != null
  const serverNet = row?.mes_net_production_sec

  if (isPaused || isOnBreak) {
    if ((serverNet ?? 0) === 0 && (sess.activeAccumMs ?? 0) === 0) {
      const pauseMs = readExplicitPausedAccumMs(sess, now)
      const breakMs = readExplicitBreakAccumMs(sess, now)
      sess.activeAccumMs = Math.max(0, now - ws - pauseMs - breakMs)
    }
    return
  }
  correctNetProductionFromWallClock(sess, ws, now)
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
export function freezeBreakAccumMs(sess: PlanSessionLike, at = Date.now()): number {
  if (sess.wallStart == null) {
    sess.breakAccumMs = 0
    sess.breakSliceStart = null
    return 0
  }

  let ms = sess.breakAccumMs ?? 0
  if (sess.breakSliceStart != null) {
    ms += Math.max(0, at - sess.breakSliceStart)
    sess.breakSliceStart = null
  }
  sess.breakAccumMs = ms
  return ms
}

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
  const breakMs = sess.breakAccumMs ?? 0
  const derived = Math.max(0, wallSpan - Math.min(Math.max(0, netMs), wallSpan) - breakMs)
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

  if (sess.breakSliceStart != null) {
    if (sess.breakSliceStart < sess.wallStart) sess.breakSliceStart = sess.wallStart
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
    breakAccumMs: 0,
    breakSliceStart: null,
    wallStart: null,
    wallEnd: null,
    defects: { ...defects },
    defectAtByItem: {},
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
      breakAccumMs: s.breakAccumMs ?? 0,
      breakSliceStart: s.breakSliceStart ?? null,
      wallStart: s.wallStart,
      wallEnd: s.wallEnd,
      defects: { ...s.defects },
      defectAtByItem: { ...(s.defectAtByItem ?? {}) },
    }
  }
  return out
}

export function applyPersistedSessionsForScope(
  scopeDay: string,
  machineId: number | null,
  rowIds: number[],
  ensureSession: (planId: number) => PlanSessionLike,
  operatedPlanIds?: ReadonlySet<number> | readonly number[],
  /** サーバー行がまだ MES 生産中のときのみ端末キャッシュを復元する */
  shouldRestorePersistedSession?: (planId: number) => boolean,
): boolean {
  const scopeSessions = getScopeSessions(scopeDay, machineId)
  if (!scopeSessions) return false
  const operated =
    operatedPlanIds instanceof Set
      ? operatedPlanIds
      : operatedPlanIds
        ? new Set(operatedPlanIds)
        : null
  let any = false
  for (const id of rowIds) {
    if (operated && !operated.has(id)) continue
    if (shouldRestorePersistedSession && !shouldRestorePersistedSession(id)) continue
    const sess = ensureSession(id)
    const p = scopeSessions[String(id)]
    if (!p || p.wallStart == null || p.wallEnd != null) continue
    // 本端末で操作開始済み（operatedPlanIds）の未終了タイマーのみ復元
    sess.wallStart = p.wallStart
    sess.wallEnd = null
    sess.activeAccumMs = p.activeAccumMs ?? 0
    sess.runningSliceStart = p.runningSliceStart ?? p.wallStart
    sess.pausedAccumMs = p.pausedAccumMs ?? 0
    sess.pauseSliceStart = p.pauseSliceStart ?? null
    sess.breakAccumMs = p.breakAccumMs ?? 0
    sess.breakSliceStart = p.breakSliceStart ?? null
    sess.defects = { ...p.defects }
    sess.defectAtByItem = { ...(p.defectAtByItem ?? {}) }
    reconcileInProgressTimer(sess)
    any = true
  }
  return any
}
