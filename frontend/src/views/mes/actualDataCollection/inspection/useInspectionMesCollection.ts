import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  createInspectionManagement,
  fetchInspectionManagementList,
  patchInspectionManagement,
  type InspectionManagementListRow,
  type PatchInspectionManagementBody,
} from '@/api/inspectionManagement'
import { getProducts, type ProductItem } from '@/api/erp/optionsData'
import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import { formatDateTimeJST, getJSTToday } from '@/utils/dateFormat'
import { INSPECTION_DEFECT_ITEMS, totalDefectCount } from './inspectionActualConfig'
import {
  applyPersistedSessionsForScope,
  emptySession,
  flushPauseSlice,
  flushRunningSlice,
  formatDurationMs,
  freezePausedAccumMs,
  hydratePlanSessionFromRow,
  loadInspectionActualPersist,
  makePersistScopeKey,
  reconcileInProgressTimer,
  saveInspectionActualPersist,
  serializePlanSessions,
  type PlanSessionLike,
} from './inspectionActualPersist'
import {
  enqueueOfflinePatch,
  flushOfflinePatchQueue,
  getOfflineQueueCount,
  isNetworkOrServerDownError,
} from './inspectionActualOfflineSync'

export type InspectionMgmtRow = InspectionManagementListRow & { id: number }

interface PlanSession extends PlanSessionLike {}

function shiftDateYmd(ymd: string, delta: number): string {
  const d = new Date(ymd + 'T12:00:00+09:00')
  d.setDate(d.getDate() + delta)
  return d.toISOString().slice(0, 10)
}

const INSPECTION_PRODUCT_NAME_EXCLUDES = ['加工', 'アーチ'] as const

/** 検査 MES：製品 CD 末尾が 1、製品名に除外語なし、製品名昇順 */
function filterInspectionProductOptions(list: ProductItem[]): ProductItem[] {
  return list
    .filter((p) => {
      if (p.is_active === false) return false
      const code = (p.product_code ?? '').trim()
      if (code.length === 0 || !code.endsWith('1')) return false
      const name = p.product_name ?? ''
      if (INSPECTION_PRODUCT_NAME_EXCLUDES.some((kw) => name.includes(kw))) return false
      return true
    })
    .sort((a, b) =>
      (a.product_name ?? '').localeCompare(b.product_name ?? '', 'ja', { sensitivity: 'base' }),
    )
}

export function useInspectionMesCollection() {
  const { t } = useI18n()

  const productionDay = ref(getJSTToday())
  const inspectorUserId = ref<number | null>(null)
  const selectedProductCode = ref<string | null>(null)
  const activePlanId = ref<number | null>(null)
  const hideCompleted = ref(false)

  const products = ref<ProductItem[]>([])
  const inspectors = ref<UserListItem[]>([])
  const managementRows = ref<InspectionMgmtRow[]>([])
  const sessions = reactive<Record<number, PlanSession>>({})

  const loadingProducts = ref(false)
  const loadingInspectors = ref(false)
  const loadingPlans = ref(false)

  const tickNow = ref(Date.now())
  let tickTimer: ReturnType<typeof setInterval> | null = null
  let persistTimer: ReturnType<typeof setTimeout> | null = null
  let defectPatchTimer: ReturnType<typeof setTimeout> | null = null
  let mesSyncTimer: ReturnType<typeof setInterval> | null = null
  let mesSyncInFlight = false
  let runningPersistTimer: ReturnType<typeof setInterval> | null = null

  const localMesEchoUntil = new Map<number, number>()
  const MES_SYNC_INTERVAL_MS = 4000

  const endDialogVisible = ref(false)
  const endDialogQty = ref('')
  const endDialogSubmitting = ref(false)

  const isBrowserOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
  const offlineQueueCount = ref(0)
  let flushingOfflineQueue = false

  const activeRow = computed(() => {
    const id = activePlanId.value
    if (id == null) return null
    return managementRows.value.find((r) => r.id === id) ?? null
  })

  const session = computed(() => {
    const id = activePlanId.value
    if (id == null) return null
    return sessions[id] ?? null
  })

  function currentScopeKey(): string {
    return makePersistScopeKey((productionDay.value ?? '').trim())
  }

  function refreshOfflineQueueCount(): void {
    offlineQueueCount.value = getOfflineQueueCount()
  }

  async function patchWithOfflineSync(
    planId: number,
    body: PatchInspectionManagementBody,
    options?: { silentQueue?: boolean },
  ): Promise<boolean> {
    if (!navigator.onLine) {
      enqueueOfflinePatch(currentScopeKey(), planId, body)
      refreshOfflineQueueCount()
      if (!options?.silentQueue) ElMessage.warning(t('mesInspectionActual.offlineQueued'))
      return false
    }
    try {
      const res = await patchInspectionManagement(planId, body)
      if (res && res.success === false) {
        if (!options?.silentQueue) ElMessage.warning(res.message || t('mesInspectionActual.saveFailed'))
        return false
      }
      return true
    } catch (e: unknown) {
      if (isNetworkOrServerDownError(e)) {
        enqueueOfflinePatch(currentScopeKey(), planId, body)
        refreshOfflineQueueCount()
        if (!options?.silentQueue) ElMessage.warning(t('mesInspectionActual.offlineQueued'))
        return false
      }
      throw e
    }
  }

  async function tryFlushOfflineQueue(options?: { reloadAfter?: boolean }): Promise<void> {
    if (flushingOfflineQueue || !navigator.onLine) return
    if (getOfflineQueueCount() === 0) return
    flushingOfflineQueue = true
    try {
      const { ok, fail } = await flushOfflinePatchQueue(patchInspectionManagement)
      refreshOfflineQueueCount()
      if (ok > 0) {
        ElMessage.success(t('mesInspectionActual.offlineSyncOk', { n: ok }))
        if (options?.reloadAfter) await loadPlans()
      }
      if (fail > 0) ElMessage.warning(t('mesInspectionActual.offlineSyncPartial'))
    } finally {
      flushingOfflineQueue = false
    }
  }

  function ensureSession(planId: number): PlanSession {
    if (!sessions[planId]) sessions[planId] = emptySession()
    return sessions[planId]
  }

  function flushPersistToStorage(): void {
    const day = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return
    saveInspectionActualPersist({
      productionDay: day,
      inspectorUserId: inspectorUserId.value,
      hideCompleted: hideCompleted.value,
      selectedProductCode: selectedProductCode.value,
      activePlanId: activePlanId.value,
      sessions: serializePlanSessions(sessions),
    })
  }

  function schedulePersist(): void {
    if (persistTimer) clearTimeout(persistTimer)
    persistTimer = setTimeout(flushPersistToStorage, 350)
  }

  function isTimerRunning(sess: PlanSession): boolean {
    return sess.runningSliceStart != null
  }

  function isTimerPaused(sess: PlanSession): boolean {
    return sess.wallStart != null && sess.wallEnd == null && sess.runningSliceStart == null
  }

  function isProductionInProgress(sess: PlanSession): boolean {
    return sess.wallStart != null && sess.wallEnd == null
  }

  function netProductionSeconds(sess: PlanSession): number {
    const now = Date.now()
    let ms = sess.activeAccumMs
    if (sess.runningSliceStart != null) ms += Math.max(0, now - sess.runningSliceStart)
    return Math.max(0, Math.round(ms / 1000))
  }

  function pausedAccumSeconds(sess: PlanSession): number {
    return Math.max(0, Math.round(freezePausedAccumMs(sess) / 1000))
  }

  function markLocalMesEcho(planId: number): void {
    localMesEchoUntil.set(planId, Date.now() + 2800)
  }

  function isLocalMesEchoGuarded(planId: number): boolean {
    const until = localMesEchoUntil.get(planId) ?? 0
    if (Date.now() < until) return true
    if (until > 0) localMesEchoUntil.delete(planId)
    return false
  }

  function mesTimerCheckpointBody(planId: number): Pick<
    PatchInspectionManagementBody,
    'mes_net_production_sec' | 'mes_paused_accum_sec' | 'mes_production_is_paused'
  > {
    const s = ensureSession(planId)
    return {
      mes_net_production_sec: netProductionSeconds(s),
      mes_paused_accum_sec: pausedAccumSeconds(s),
      mes_production_is_paused: isTimerPaused(s) ? 1 : 0,
    }
  }

  async function persistMesTimerCheckpoints(planId: number): Promise<void> {
    const s = ensureSession(planId)
    const now = Date.now()
    if (s.runningSliceStart != null) {
      flushRunningSlice(s, now)
      if (s.wallEnd == null && s.pauseSliceStart == null) s.runningSliceStart = now
    } else if (s.pauseSliceStart != null) {
      flushPauseSlice(s, now)
      if (s.wallEnd == null) s.pauseSliceStart = now
    }
    try {
      await patchWithOfflineSync(planId, mesTimerCheckpointBody(planId), { silentQueue: true })
    } catch (e) {
      console.error(e)
    }
  }

  function scheduleDefectPatch(planId: number): void {
    if (defectPatchTimer) clearTimeout(defectPatchTimer)
    defectPatchTimer = setTimeout(() => {
      const s = sessions[planId]
      if (!s) return
      void patchWithOfflineSync(
        planId,
        { mes_defect_by_item: { ...s.defects } },
        { silentQueue: true },
      )
    }, 400)
  }

  function isRowMesProductionActive(row: InspectionMgmtRow): boolean {
    if (row.id != null && sessions[row.id]) {
      const sess = sessions[row.id]
      if (sess.wallStart != null && sess.wallEnd == null) return true
    }
    const started = row.mes_production_started_at
    if (started == null || !String(started).trim()) return false
    const ended = row.mes_production_ended_at
    return ended == null || !String(ended).trim()
  }

  function findOtherActiveRow(excludeId: number): InspectionMgmtRow | null {
    for (const row of managementRows.value) {
      if (row.id === excludeId) continue
      if (isRowMesProductionActive(row)) return row
    }
    return null
  }

  function rowShortLabel(row: InspectionMgmtRow): string {
    const name = (row.product_name || row.product_cd || '').trim()
    return name || `#${row.id}`
  }

  function findOpenRowForProduct(code: string): InspectionMgmtRow | null {
    for (const row of managementRows.value) {
      if (row.product_cd !== code) continue
      if (Number(row.production_completed_check ?? 0) === 1) continue
      return row
    }
    return null
  }

  async function ensurePlanForProduct(code: string, name: string): Promise<number | null> {
    const existing = findOpenRowForProduct(code)
    if (existing) return existing.id
    const day = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return null
    try {
      const res = await createInspectionManagement({
        production_day: day,
        product_cd: code,
        product_name: name,
        mes_inspector_user_id: inspectorUserId.value ?? undefined,
      })
      const newId = res?.data?.id
      if (newId == null) {
        ElMessage.error(res?.message || t('mesInspectionActual.saveFailed'))
        return null
      }
      await loadPlans()
      return Number(newId)
    } catch (e) {
      console.error(e)
      ElMessage.error(t('mesInspectionActual.saveFailed'))
      return null
    }
  }

  async function syncMesStateFromServer(): Promise<void> {
    if (mesSyncInFlight || !navigator.onLine) return
    const day = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return
    mesSyncInFlight = true
    try {
      const res = await fetchInspectionManagementList({ production_day: day, limit: 2000 })
      if (!res.success || !res.data) return
      const byId = new Map(res.data.filter((r) => r.id != null).map((r) => [Number(r.id), r]))
      for (const row of managementRows.value) {
        const fresh = byId.get(row.id)
        if (!fresh) continue
        row.mes_production_started_at = fresh.mes_production_started_at
        row.mes_production_ended_at = fresh.mes_production_ended_at
        row.mes_net_production_sec = fresh.mes_net_production_sec
        row.mes_paused_accum_sec = fresh.mes_paused_accum_sec
        row.mes_production_is_paused = fresh.mes_production_is_paused
        row.mes_inspector_user_id = fresh.mes_inspector_user_id
        row.mes_defect_by_item = fresh.mes_defect_by_item
        row.actual_production_quantity = fresh.actual_production_quantity
        row.defect_qty = fresh.defect_qty
        row.production_completed_check = fresh.production_completed_check
        if (isLocalMesEchoGuarded(row.id)) continue
        const sess = ensureSession(row.id)
        hydratePlanSessionFromRow(sess, fresh)
        if (sess.wallStart != null && sess.wallEnd == null) reconcileInProgressTimer(sess)
      }
    } finally {
      mesSyncInFlight = false
    }
  }

  async function loadPlans(): Promise<void> {
    const dayStr = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dayStr)) {
      ElMessage.warning(t('mesInspectionActual.invalidProductionDay'))
      return
    }
    loadingPlans.value = true
    try {
      const res = await fetchInspectionManagementList({
        production_day: dayStr,
        limit: 2000,
      })
      if (!res.success) {
        ElMessage.error(res.message || t('mesInspectionActual.loadPlansFailed'))
        return
      }
      const rows = (res.data ?? []).filter((r): r is InspectionMgmtRow => r.id != null)
      managementRows.value = rows
      for (const r of rows) {
        const sess = ensureSession(r.id)
        hydratePlanSessionFromRow(sess, r)
        if (sess.wallStart != null && sess.wallEnd == null) reconcileInProgressTimer(sess)
      }
      const restored = applyPersistedSessionsForScope(
        dayStr,
        rows.map((r) => r.id),
        ensureSession,
      )
      if (restored) ElMessage.info(t('mesInspectionActual.stateRestored'))
      flushPersistToStorage()
      void tryFlushOfflineQueue()
      bindActivePlanFromSelection()
    } catch (e) {
      console.error(e)
      ElMessage.error(t('mesInspectionActual.loadPlansFailed'))
    } finally {
      loadingPlans.value = false
    }
  }

  function bindActivePlanFromSelection(): void {
    const code = selectedProductCode.value
    if (!code) {
      activePlanId.value = null
      return
    }
    const row = findOpenRowForProduct(code)
    activePlanId.value = row?.id ?? null
  }

  const completedRows = computed(() =>
    managementRows.value.filter((r) => Number(r.production_completed_check ?? 0) === 1),
  )

  const elapsedDisplay = computed(() => {
    const sess = session.value
    if (!sess) return '0:00'
    const now = tickNow.value
    let active = sess.activeAccumMs
    if (sess.runningSliceStart != null) active += Math.max(0, now - sess.runningSliceStart)
    return formatDurationMs(active)
  })

  const pausedDisplay = computed(() => {
    const sess = session.value
    if (!sess) return '0:00'
    return formatDurationMs(freezePausedAccumMs(sess, tickNow.value))
  })

  const defectTotal = computed(() => {
    const sess = session.value
    if (!sess) return 0
    return totalDefectCount(sess.defects)
  })

  const canStart = computed(() => {
    if (inspectorUserId.value == null || !selectedProductCode.value) return false
    const sess = session.value
    if (!sess) return true
    return sess.wallStart == null
  })

  const canPause = computed(() => session.value != null && isTimerRunning(session.value))
  const canResume = computed(() => session.value != null && isTimerPaused(session.value))
  const canEnd = computed(() => session.value != null && isProductionInProgress(session.value))

  const timerStatusKey = computed(() => {
    const sess = session.value
    if (!sess) return 'idle'
    if (sess.wallEnd != null) return 'ended'
    if (isTimerPaused(sess)) return 'paused'
    if (isTimerRunning(sess)) return 'running'
    if (sess.wallStart != null) return 'paused'
    return 'idle'
  })

  const timerStatusLabel = computed(() => {
    const map = { idle: 'timerIdle', running: 'timerRunning', paused: 'timerPaused', ended: 'timerEnded' } as const
    return t(`mesInspectionActual.${map[timerStatusKey.value]}`)
  })

  const canEditDefects = computed(() => {
    const sess = session.value
    return sess != null && isProductionInProgress(sess)
  })

  function formatElapsed(ms: number): string {
    const s = Math.max(0, Math.floor(ms / 1000))
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const sec = s % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  }

  function netProductionMs(sess: PlanSession, now = tickNow.value): number {
    let net = sess.activeAccumMs
    if (sess.runningSliceStart != null) net += now - sess.runningSliceStart
    return Math.max(0, net)
  }

  function pausedAccumMs(sess: PlanSession): number {
    if (sess.wallStart == null) return 0
    const now = tickNow.value
    let ms = sess.pausedAccumMs ?? 0
    if (sess.pauseSliceStart != null) ms += Math.max(0, now - sess.pauseSliceStart)
    if (ms > 0 || sess.pauseSliceStart != null) return ms
    const wallSpan =
      sess.wallEnd != null
        ? Math.max(0, sess.wallEnd - sess.wallStart)
        : Math.max(0, now - sess.wallStart)
    return Math.max(0, wallSpan - Math.min(netProductionMs(sess, now), wallSpan))
  }

  function operationDisplayMs(sess: PlanSession, now = tickNow.value): number {
    if (sess.wallStart == null) return 0
    if (sess.wallEnd != null) {
      if (sess.activeAccumMs > 0) return sess.activeAccumMs
      return Math.max(0, sess.wallEnd - sess.wallStart)
    }
    return netProductionMs(sess, now)
  }

  function timerPhase(sess: PlanSession): 'idle' | 'running' | 'paused' | 'ended' {
    if (sess.wallEnd != null) return 'ended'
    if (sess.wallStart == null) return 'idle'
    if (sess.pauseSliceStart != null) return 'paused'
    if (sess.runningSliceStart != null) return 'running'
    return 'paused'
  }

  function timerPhaseLabel(sess: PlanSession): string {
    const ph = timerPhase(sess)
    const map = { idle: 'timerIdle', running: 'timerRunning', paused: 'timerPaused', ended: 'timerEnded' } as const
    return t(`mesInspectionActual.${map[ph]}`)
  }

  function formatWall(ts: number | null | undefined): string {
    if (ts == null) return '—'
    return formatDateTimeJST(new Date(ts), 'ja-JP', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  function workSession(): PlanSession | null {
    const id = activePlanId.value
    if (id == null) return null
    return sessions[id] ?? null
  }

  const showOfflineAlert = computed(() => isBrowserOffline.value || offlineQueueCount.value > 0)
  const offlineAlertText = computed(() => {
    if (isBrowserOffline.value) return t('mesInspectionActual.offlineBanner')
    return t('mesInspectionActual.offlinePendingSync', { n: offlineQueueCount.value })
  })

  function defectCount(itemId: string): number {
    return Math.max(0, Math.round(session.value?.defects[itemId] ?? 0))
  }

  function bumpDefect(itemId: string, delta: number): void {
    const id = activePlanId.value
    const sess = session.value
    if (id == null || !sess) return
    sess.defects[itemId] = Math.max(0, defectCount(itemId) + delta)
    schedulePersist()
    scheduleDefectPatch(id)
  }

  async function onStartProduction(): Promise<void> {
    if (inspectorUserId.value == null) {
      ElMessage.warning(t('mesInspectionActual.inspectorRequired'))
      return
    }
    const code = selectedProductCode.value
    const p = products.value.find((x) => x.product_code === code)
    if (!code || !p) return
    const name = (p.product_name || '').trim() || code
    let planId = activePlanId.value
    if (planId == null) {
      planId = await ensurePlanForProduct(code, name)
      if (planId == null) return
      activePlanId.value = planId
    }
    const other = findOtherActiveRow(planId)
    if (other) {
      ElMessage.warning(
        t('mesInspectionActual.singleDayProductionOnly', { label: rowShortLabel(other) }),
      )
      return
    }
    const s = ensureSession(planId)
    if (s.wallStart != null) return
    const now = Date.now()
    markLocalMesEcho(planId)
    const ok = await patchWithOfflineSync(planId, {
      mes_production_started_at: new Date(now).toISOString(),
      mes_production_is_paused: 0,
      mes_inspector_user_id: inspectorUserId.value,
    })
    if (!ok && navigator.onLine) return
    s.wallStart = now
    s.activeAccumMs = 0
    s.pausedAccumMs = 0
    s.pauseSliceStart = null
    s.runningSliceStart = now
    schedulePersist()
    ElMessage.success(t('mesInspectionActual.started'))
  }

  function onPauseProduction(): void {
    const id = activePlanId.value
    const s = session.value
    if (id == null || !s || !isTimerRunning(s)) return
    const now = Date.now()
    flushRunningSlice(s, now)
    s.pauseSliceStart = now
    markLocalMesEcho(id)
    void persistMesTimerCheckpoints(id)
    schedulePersist()
  }

  function onResumeProduction(): void {
    const id = activePlanId.value
    const s = session.value
    if (id == null || !s || !isTimerPaused(s)) return
    const now = Date.now()
    flushPauseSlice(s, now)
    s.runningSliceStart = now
    markLocalMesEcho(id)
    void persistMesTimerCheckpoints(id)
    schedulePersist()
  }

  function openEndDialog(): void {
    const s = session.value
    if (!s || !canEnd.value) return
    const now = Date.now()
    if (isTimerRunning(s)) flushRunningSlice(s, now)
    if (isTimerPaused(s)) flushPauseSlice(s, now)
    endDialogQty.value = ''
    endDialogVisible.value = true
  }

  function closeEndDialog(): void {
    endDialogVisible.value = false
  }

  const endDialogPreview = computed(() => {
    const row = activeRow.value
    const s = session.value
    if (!row || !s) return null
    const now = tickNow.value
    let activeMs = s.activeAccumMs
    if (s.runningSliceStart != null) activeMs += Math.max(0, now - s.runningSliceStart)
    return {
      productName: row.product_name,
      inspectorName: inspectorLabel.value || t('mesInspectionActual.inspectorMissing'),
      wallStart: s.wallStart,
      wallEnd: now,
      activeMs,
      pausedMs: freezePausedAccumMs(s, now),
      defects: { ...s.defects },
      defectTotal: totalDefectCount(s.defects),
    }
  })

  const inspectorLabel = computed(() => {
    const id = inspectorUserId.value
    if (id == null) return ''
    const u = inspectors.value.find((x) => x.id === id)
    return (u?.full_name || u?.username || '').trim()
  })

  async function submitProductionEnd(): Promise<void> {
    const id = activePlanId.value
    const s = session.value
    const preview = endDialogPreview.value
    if (id == null || !s || !preview) return
    const qty = Math.round(Number(String(endDialogQty.value).trim()))
    if (!Number.isFinite(qty) || qty < 0) {
      ElMessage.warning(t('mesInspectionActual.qtyInvalid'))
      return
    }
    if (!navigator.onLine) {
      ElMessage.warning(t('mesInspectionActual.needOnlineForEnd'))
      return
    }
    const now = Date.now()
    if (isTimerRunning(s)) flushRunningSlice(s, now)
    if (isTimerPaused(s)) flushPauseSlice(s, now)
    s.wallEnd = now
    endDialogSubmitting.value = true
    try {
      const ok = await patchWithOfflineSync(id, {
        mes_production_ended_at: new Date(now).toISOString(),
        mes_net_production_sec: netProductionSeconds(s),
        mes_paused_accum_sec: pausedAccumSeconds(s),
        mes_production_is_paused: 0,
        mes_inspector_user_id: inspectorUserId.value ?? undefined,
        mes_defect_by_item: { ...s.defects },
        actual_production_quantity: qty,
        production_completed_check: true,
        defect_qty: preview.defectTotal,
      })
      if (!ok) return
      endDialogVisible.value = false
      selectedProductCode.value = null
      activePlanId.value = null
      ElMessage.success(t('mesInspectionActual.completeSaved'))
      await loadPlans()
    } finally {
      endDialogSubmitting.value = false
    }
  }

  function defectRowsForRecord(defects: Record<string, number>) {
    return INSPECTION_DEFECT_ITEMS.filter((d) => (defects[d.id] ?? 0) > 0).map((d) => ({
      id: d.id,
      label: t(`mesInspectionActual.${d.labelKey}`),
      qty: defects[d.id] ?? 0,
    }))
  }

  function restorePageFilters(): void {
    const blob = loadInspectionActualPersist()
    if (!blob) return
    if (blob.productionDay && /^\d{4}-\d{2}-\d{2}$/.test(blob.productionDay)) {
      productionDay.value = blob.productionDay
    }
    hideCompleted.value = blob.hideCompleted
    if (blob.inspectorUserId != null) inspectorUserId.value = blob.inspectorUserId
    if (blob.selectedProductCode) selectedProductCode.value = blob.selectedProductCode
    if (blob.activePlanId != null) activePlanId.value = blob.activePlanId
  }

  watch([productionDay, inspectorUserId, hideCompleted], () => {
    schedulePersist()
    void loadPlans()
  })

  watch(selectedProductCode, (code) => {
    if (!code) {
      activePlanId.value = null
      return
    }
    const inProgress = activePlanId.value != null && session.value && isProductionInProgress(session.value)
    if (inProgress && activeRow.value?.product_cd !== code) {
      ElMessage.warning(t('mesInspectionActual.switchProductBlocked'))
      selectedProductCode.value = activeRow.value?.product_cd ?? null
      return
    }
    bindActivePlanFromSelection()
    schedulePersist()
  })

  watch(inspectorUserId, (id) => {
    const planId = activePlanId.value
    if (planId != null && id != null) {
      void patchWithOfflineSync(planId, { mes_inspector_user_id: id }, { silentQueue: true })
    }
    schedulePersist()
  })

  function shiftProductionDay(delta: number): void {
    const base = (productionDay.value ?? '').trim().slice(0, 10)
    const anchor = /^\d{4}-\d{2}-\d{2}$/.test(base) ? base : getJSTToday()
    productionDay.value = shiftDateYmd(anchor, delta)
  }

  function setProductionDayToday(): void {
    productionDay.value = getJSTToday()
  }

  async function loadProducts(): Promise<void> {
    loadingProducts.value = true
    try {
      products.value = filterInspectionProductOptions((await getProducts()) ?? [])
      const code = selectedProductCode.value
      if (code && !products.value.some((p) => p.product_code === code)) {
        const inProgress =
          activePlanId.value != null && session.value != null && isProductionInProgress(session.value)
        if (!inProgress) selectedProductCode.value = null
      }
    } catch {
      ElMessage.error(t('mesInspectionActual.loadProductsFailed'))
    } finally {
      loadingProducts.value = false
    }
  }

  async function loadInspectors(): Promise<void> {
    loadingInspectors.value = true
    try {
      const res = (await getUsers({ page: 1, page_size: 500, status: 'active' })) as unknown as PaginatedUserResponse
      inspectors.value = res?.items ?? []
    } catch {
      ElMessage.error(t('mesInspectionActual.loadInspectorsFailed'))
    } finally {
      loadingInspectors.value = false
    }
  }

  function setupLifecycle(): void {
    restorePageFilters()
    tickTimer = setInterval(() => {
      tickNow.value = Date.now()
    }, 1000)
    window.addEventListener('online', () => {
      isBrowserOffline.value = false
      void tryFlushOfflineQueue({ reloadAfter: true })
    })
    window.addEventListener('offline', () => {
      isBrowserOffline.value = true
    })
    window.addEventListener('beforeunload', flushPersistToStorage)
    runningPersistTimer = setInterval(() => {
      const inProgress = Object.values(sessions).some((s) => s.wallEnd == null && s.wallStart != null)
      if (inProgress) flushPersistToStorage()
      for (const [planId, s] of Object.entries(sessions)) {
        if (s.wallEnd == null && s.wallStart != null) {
          void persistMesTimerCheckpoints(Number(planId))
        }
      }
    }, 5000)
    mesSyncTimer = setInterval(() => void syncMesStateFromServer(), MES_SYNC_INTERVAL_MS)
  }

  function teardownLifecycle(): void {
    if (tickTimer) clearInterval(tickTimer)
    if (persistTimer) clearTimeout(persistTimer)
    if (runningPersistTimer) clearInterval(runningPersistTimer)
    if (mesSyncTimer) clearInterval(mesSyncTimer)
    flushPersistToStorage()
    window.removeEventListener('beforeunload', flushPersistToStorage)
  }

  async function init(): Promise<void> {
    setupLifecycle()
    refreshOfflineQueueCount()
    await Promise.all([loadProducts(), loadInspectors()])
    await loadPlans()
    void tryFlushOfflineQueue({ reloadAfter: true })
  }

  return {
    INSPECTION_DEFECT_ITEMS,
    productionDay,
    inspectorUserId,
    selectedProductCode,
    activePlanId,
    activeRow,
    hideCompleted,
    products,
    inspectors,
    managementRows,
    completedRows,
    loadingProducts,
    loadingInspectors,
    loadingPlans,
    endDialogVisible,
    endDialogQty,
    endDialogSubmitting,
    elapsedDisplay,
    pausedDisplay,
    defectTotal,
    canStart,
    canPause,
    canResume,
    canEnd,
    canEditDefects,
    timerStatusLabel,
    showOfflineAlert,
    offlineAlertText,
    endDialogPreview,
    inspectorLabel,
    shiftProductionDay,
    setProductionDayToday,
    loadPlans,
    onStartProduction,
    onPauseProduction,
    onResumeProduction,
    openEndDialog,
    closeEndDialog,
    submitProductionEnd,
    defectCount,
    bumpDefect,
    defectRowsForRecord,
    workSession,
    formatElapsed,
    operationDisplayMs,
    pausedAccumMs,
    timerPhase,
    timerPhaseLabel,
    formatWall,
    isProductionInProgress,
    init,
    teardownLifecycle,
  }
}
