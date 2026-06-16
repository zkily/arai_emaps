import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createWeldingManagement,
  fetchWeldingManagementList,
  patchWeldingManagement,
  type WeldingManagementListRow,
  type PatchWeldingManagementBody,
} from '@/api/weldingManagement'
import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import {
  fetchWeldingMesMachines,
  fetchWeldingMesProducts,
  type WeldingMesMachine,
  type WeldingMesProductOption,
} from '@/api/weldingMesEquipment'
import { formatDateTimeJST, getJSTToday, shiftDateYmdJST } from '@/utils/dateFormat'
import { WELDING_DEFECT_DETECTION_PROCESS_CD } from './weldingActualConfig'
import {
  alignSessionElapsedFromWallClock,
  applyPersistedSessionsForScope,
  correctNetProductionFromWallClock,
  emptySession,
  flushPauseSlice,
  flushRunningSlice,
  formatDurationMs,
  freezePausedAccumMs,
  readPausedAccumMs,
  hydratePlanSessionFromRow,
  loadWeldingActualPersist,
  makePersistScopeKey,
  reconcileInProgressTimer,
  saveWeldingActualPersist,
  serializePlanSessions,
  type PlanSessionLike,
} from './weldingActualPersist'
import {
  emptyDefectCountsFromItems,
  loadMesDefectItemsForProcess,
  resolveMesDefectItemLabel,
  totalDefectCountFromItems,
  type MesDefectItemOption,
} from '../shared/loadProcessDefectItems'
import {
  enqueueOfflinePatch,
  flushOfflinePatchQueue,
  getOfflineQueueCount,
  isNetworkOrServerDownError,
} from './weldingActualOfflineSync'
import { getMesClientInstanceId } from './mesClientInstance'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import { guardMesOperation } from '@/utils/mesOperationGuard'

type MesLockOwner = 'mine' | 'other' | 'unclaimed'

export type WeldingMgmtRow = WeldingManagementListRow & { id: number }

interface PlanSession extends PlanSessionLike {}

export function useWeldingMesCollection() {
  const { t, te } = useI18n()
  const { canCreate, canEdit, canDelete, canExport } = useMesOperationPermission()

  const productionDay = ref(getJSTToday())
  const selectedWeldingMachineId = ref<number | null>(null)
  const machines = ref<WeldingMesMachine[]>([])
  const operatorUserId = ref<number | null>(null)
  const selectedProductCode = ref<string | null>(null)
  const activePlanId = ref<number | null>(null)
  const products = ref<WeldingMesProductOption[]>([])
  const operators = ref<UserListItem[]>([])
  const managementRows = ref<WeldingMgmtRow[]>([])
  const sessions = reactive<Record<number, PlanSession>>({})

  const loadingProducts = ref(false)
  const loadingMachines = ref(false)
  const loadingOperators = ref(false)
  const loadingPlans = ref(false)
  const loadingDefectItems = ref(false)
  const defectItems = ref<MesDefectItemOption[]>([])
  const productScanDialogVisible = ref(false)

  const tickNow = ref(Date.now())
  let tickTimer: ReturnType<typeof setInterval> | null = null
  let persistTimer: ReturnType<typeof setTimeout> | null = null
  let defectPatchTimer: ReturnType<typeof setTimeout> | null = null
  let mesSyncTimer: ReturnType<typeof setInterval> | null = null
  let mesSyncInFlight = false
  let mesSyncVisibilityHandler: (() => void) | null = null
  let runningPersistTimer: ReturnType<typeof setInterval> | null = null

  const localMesEchoUntil = new Map<number, number>()
  /** 本端末で生産開始した plan（他端末 hydrate の在産と区別） */
  const locallyOperatedPlanIds = ref<Set<number>>(new Set())
  /** resumeInProgressSession 等で operatorUserId watch の誤判定を抑止 */
  let suppressOperatorUserWatch = false
  let suppressMachineWatch = false
  /** 検査生産中ストリップ・他端末在産の同期（一覧 GET、セッション hydrate は本端末のみ） */
  const MES_SYNC_INTERVAL_MS = 5000
  const MES_SYNC_INTERVAL_HIDDEN_MS = 15000

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

  const selectedWeldingMachineName = computed(() => {
    const id = selectedWeldingMachineId.value
    if (id == null) return ''
    const m = machines.value.find((x) => x.id === id)
    return (m?.machine_name || m?.machine_cd || '').trim()
  })

  function currentScopeKey(): string {
    return makePersistScopeKey(
      (productionDay.value ?? '').trim(),
      selectedWeldingMachineId.value,
    )
  }

  function refreshOfflineQueueCount(): void {
    offlineQueueCount.value = getOfflineQueueCount()
  }

  function mesPatchBody(body: PatchWeldingManagementBody): PatchWeldingManagementBody {
    return {
      ...body,
      mes_client_instance_id: getMesClientInstanceId(),
    }
  }

  function rowMesLockOwner(row: WeldingMgmtRow | null | undefined): MesLockOwner {
    if (!row) return 'unclaimed'
    const lock = (row.mes_client_instance_id ?? '').trim()
    if (!lock) return 'unclaimed'
    return lock === getMesClientInstanceId() ? 'mine' : 'other'
  }

  /** サーバー在産行への PATCH（計測同期・不良等）可否 */
  function canServerPatchPlan(planId: number): boolean {
    const row = managementRows.value.find((r) => r.id === planId)
    if (!row || !isRowMesProductionActive(row)) return false
    const owner = rowMesLockOwner(row)
    if (owner === 'other') return false
    if (owner === 'mine') return true
    return isPlanLocallyOperated(planId)
  }

  function httpErrorFromUnknown(e: unknown): { status?: number; detail?: string } {
    if (!e || typeof e !== 'object' || !('response' in e)) return {}
    const res = (e as { response?: { status?: number; data?: { detail?: string } } }).response
    const detail = res?.data?.detail
    return {
      status: res?.status,
      detail: typeof detail === 'string' ? detail.trim() : undefined,
    }
  }

  function canResumeSession(row: WeldingMgmtRow): boolean {
    if (row.id == null || !isRowMesProductionActive(row)) return false
    return rowMesLockOwner(row) !== 'other'
  }

  async function patchWithOfflineSync(
    planId: number,
    body: PatchWeldingManagementBody,
    options?: { silentQueue?: boolean },
  ): Promise<boolean> {
    const payload = mesPatchBody(body)
    if (!navigator.onLine) {
      enqueueOfflinePatch(currentScopeKey(), planId, payload)
      refreshOfflineQueueCount()
      if (!options?.silentQueue) ElMessage.warning(t('mesWeldingActual.offlineQueued'))
      return false
    }
    try {
      const res = await patchWeldingManagement(planId, payload)
      if (res && res.success === false) {
        if (!options?.silentQueue) ElMessage.warning(res.message || t('mesWeldingActual.saveFailed'))
        return false
      }
      return true
    } catch (e: unknown) {
      if (isNetworkOrServerDownError(e)) {
        enqueueOfflinePatch(currentScopeKey(), planId, payload)
        refreshOfflineQueueCount()
        if (!options?.silentQueue) ElMessage.warning(t('mesWeldingActual.offlineQueued'))
        return false
      }
      const { status, detail } = httpErrorFromUnknown(e)
      if (status === 409) {
        if (!options?.silentQueue && detail) ElMessage.warning(detail)
        void syncMesStateFromServer()
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
      const { ok, fail } = await flushOfflinePatchQueue(patchWeldingManagement)
      refreshOfflineQueueCount()
      if (ok > 0) {
        ElMessage.success(t('mesWeldingActual.offlineSyncOk', { n: ok }))
        if (options?.reloadAfter) await loadPlans()
      }
      if (fail > 0) ElMessage.warning(t('mesWeldingActual.offlineSyncPartial'))
    } finally {
      flushingOfflineQueue = false
    }
  }

  function makeEmptyDefectCounts(): Record<string, number> {
    return emptyDefectCountsFromItems(defectItems.value)
  }

  function mergeSessionDefects(parsed: Record<string, number>): Record<string, number> {
    const merged = makeEmptyDefectCounts()
    for (const [k, v] of Object.entries(parsed)) {
      const n = Math.max(0, Math.round(v))
      if (n > 0) merged[k] = n
    }
    return merged
  }

  function normalizeSessionDefects(sess: PlanSession): void {
    sess.defects = mergeSessionDefects(sess.defects)
  }

  function ensureSession(planId: number): PlanSession {
    if (!sessions[planId]) sessions[planId] = emptySession(makeEmptyDefectCounts())
    return sessions[planId]
  }

  function flushPersistToStorage(): void {
    const day = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return
    saveWeldingActualPersist({
      productionDay: day,
      selectedWeldingMachineId: selectedWeldingMachineId.value,
      operatorUserId: operatorUserId.value,
      selectedProductCode: selectedProductCode.value,
      activePlanId: activePlanId.value,
      sessions: serializePlanSessions(sessions),
      operatedPlanIds: Array.from(locallyOperatedPlanIds.value),
    })
  }

  function loadLocallyOperatedPlanIds(day: string, machineId: number | null): void {
    const blob = loadWeldingActualPersist()
    const ids =
      blob &&
      makePersistScopeKey(blob.productionDay, blob.selectedWeldingMachineId) ===
        makePersistScopeKey(day, machineId)
        ? blob.operatedPlanIds ?? []
        : []
    locallyOperatedPlanIds.value = new Set(ids)
  }

  function rowWeldingMachine(row: WeldingMgmtRow): string {
    return (row.welding_machine ?? '').trim()
  }

  function rowMatchesSelectedMachine(row: WeldingMgmtRow): boolean {
    const name = selectedWeldingMachineName.value
    if (!name) return true
    const rm = rowWeldingMachine(row)
    return !rm || rm === name
  }

  function markPlanLocallyOperated(planId: number): void {
    const next = new Set(locallyOperatedPlanIds.value)
    next.add(planId)
    locallyOperatedPlanIds.value = next
    schedulePersist()
  }

  function unmarkPlanLocallyOperated(planId: number): void {
    if (!locallyOperatedPlanIds.value.has(planId)) return
    const next = new Set(locallyOperatedPlanIds.value)
    next.delete(planId)
    locallyOperatedPlanIds.value = next
    schedulePersist()
  }

  function isPlanLocallyOperated(planId: number | null | undefined): boolean {
    if (planId == null) return false
    return locallyOperatedPlanIds.value.has(planId)
  }

  function syncActivePlanSessionFromRow(planId?: number | null): void {
    const id = planId ?? activePlanId.value
    if (id == null) return
    const row = managementRows.value.find((r) => r.id === id)
    if (!row) return
    const sess = ensureSession(id)
    hydratePlanSessionFromRow(sess, row)
    normalizeSessionDefects(sess)
    if (sess.wallStart != null && sess.wallEnd == null) reconcileInProgressTimer(sess)
  }

  function activePlanSessionInProgress(): boolean {
    const planId = activePlanId.value
    if (planId == null) return false
    const sess = sessions[planId]
    if (sess && isProductionInProgress(sess)) return true
    const row = managementRows.value.find((r) => r.id === planId)
    return row != null && isRowMesProductionActive(row)
  }

  function schedulePersist(): void {
    if (persistTimer) clearTimeout(persistTimer)
    persistTimer = setTimeout(flushPersistToStorage, 350)
  }

  function isTimerRunning(sess: PlanSession): boolean {
    return sess.runningSliceStart != null
  }

  function isTimerPaused(sess: PlanSession): boolean {
    return sess.wallStart != null && sess.wallEnd == null && sess.pauseSliceStart != null
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

  function pausedAccumSeconds(sess: PlanSession, at = Date.now()): number {
    return Math.max(0, Math.round(readPausedAccumMs(sess, at) / 1000))
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
    PatchWeldingManagementBody,
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
    if (!canServerPatchPlan(planId)) return
    const s = ensureSession(planId)
    const now = Date.now()
    if (s.runningSliceStart != null) {
      flushRunningSlice(s, now)
      if (s.wallEnd == null && s.pauseSliceStart == null) s.runningSliceStart = now
    } else if (s.pauseSliceStart != null) {
      flushPauseSlice(s, now)
      if (s.wallEnd == null) s.pauseSliceStart = now
    }
    await patchWithOfflineSync(planId, mesTimerCheckpointBody(planId), { silentQueue: true })
  }

  function scheduleDefectPatch(planId: number): void {
    if (defectPatchTimer) clearTimeout(defectPatchTimer)
    defectPatchTimer = setTimeout(() => {
      const s = sessions[planId]
      if (!s || !canServerPatchPlan(planId)) return
      void patchWithOfflineSync(
        planId,
        { mes_defect_by_item: { ...s.defects } },
        { silentQueue: true },
      )
    }, 400)
  }

  function isRowMesProductionActive(row: WeldingMgmtRow): boolean {
    if (row.id != null && sessions[row.id]) {
      const sess = sessions[row.id]
      if (sess.wallStart != null && sess.wallEnd == null) return true
    }
    const started = row.mes_production_started_at
    if (started == null || !String(started).trim()) return false
    const ended = row.mes_production_ended_at
    return ended == null || !String(ended).trim()
  }

  function rowOperatorId(row: WeldingMgmtRow): number | null {
    const v = row.mes_operator_user_id
    if (v == null || !Number.isFinite(Number(v))) return null
    return Number(v)
  }

  function operatorNameById(userId: number | null | undefined): string {
    if (userId == null) return ''
    const u = operators.value.find((x) => x.id === userId)
    return (u?.full_name || u?.username || '').trim()
  }

  /** 同一溶接設備で別製品を同時に生産中か */
  function findOtherActiveRowForMachine(excludeId: number): WeldingMgmtRow | null {
    const machine = selectedWeldingMachineName.value
    if (!machine) return null
    for (const row of managementRows.value) {
      if (row.id === excludeId) continue
      if (!isRowMesProductionActive(row)) continue
      if (rowWeldingMachine(row) !== machine) continue
      return row
    }
    return null
  }

  function findInProgressRowForOperator(inspectorId: number): WeldingMgmtRow | null {
    for (const row of managementRows.value) {
      if (rowOperatorId(row) !== inspectorId) continue
      if (!rowMatchesSelectedMachine(row)) continue
      if (isRowMesProductionActive(row)) return row
    }
    return null
  }

  function findInProgressRowForMachine(): WeldingMgmtRow | null {
    const machine = selectedWeldingMachineName.value
    if (!machine) return null
    for (const row of managementRows.value) {
      if (rowWeldingMachine(row) !== machine) continue
      if (isRowMesProductionActive(row)) return row
    }
    return null
  }

  function rowShortLabel(row: WeldingMgmtRow): string {
    const name = (row.product_name || row.product_cd || '').trim()
    return name || `#${row.id}`
  }

  function isRowProductionCompleted(row: WeldingMgmtRow): boolean {
    return Number(row.production_completed_check ?? 0) === 1
  }

  /** 当該設備・溶接作業者の未確定オープン行 */
  function findOpenRowForScope(code: string, inspectorId: number): WeldingMgmtRow | null {
    const machine = selectedWeldingMachineName.value
    for (const row of managementRows.value) {
      if (row.product_cd !== code) continue
      if (isRowProductionCompleted(row)) continue
      if (rowOperatorId(row) !== inspectorId) continue
      if (machine && rowWeldingMachine(row) && rowWeldingMachine(row) !== machine) continue
      return row
    }
    return null
  }

  async function ensurePlanForProduct(code: string, name: string): Promise<number | null> {
    if (!guardMesOperation(canCreate)) return null
    const inspId = operatorUserId.value
    if (inspId == null) return null
    const machine = selectedWeldingMachineName.value
    if (!machine) {
      ElMessage.warning(t('mesWeldingActual.machineRequired'))
      return null
    }
    const existing = findOpenRowForScope(code, inspId)
    if (existing?.id != null) return existing.id
    const day = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return null
    try {
      const res = await createWeldingManagement({
        production_day: day,
        product_cd: code,
        product_name: name,
        welding_machine: machine,
        mes_operator_user_id: inspId,
      })
      const newId = res?.data?.id
      if (newId == null) {
        ElMessage.error(res?.message || t('mesWeldingActual.saveFailed'))
        return null
      }
      await loadPlans()
      return Number(newId)
    } catch (e) {
      console.error(e)
      ElMessage.error(t('mesWeldingActual.saveFailed'))
      return null
    }
  }

  function compareWeldingMgmtRows(a: WeldingMgmtRow, b: WeldingMgmtRow): number {
    const seqA = a.production_sequence ?? 0
    const seqB = b.production_sequence ?? 0
    if (seqA !== seqB) return seqA - seqB
    return a.id - b.id
  }

  function copyWeldingRowFromServer(target: WeldingMgmtRow, fresh: WeldingMgmtRow): void {
    target.production_sequence = fresh.production_sequence
    target.product_cd = fresh.product_cd
    target.product_name = fresh.product_name
    target.actual_production_quantity = fresh.actual_production_quantity
    target.defect_qty = fresh.defect_qty
    target.mes_defect_by_item = fresh.mes_defect_by_item
    target.production_completed_check = fresh.production_completed_check
    target.mes_production_started_at = fresh.mes_production_started_at
    target.mes_production_ended_at = fresh.mes_production_ended_at
    target.mes_net_production_sec = fresh.mes_net_production_sec
    target.mes_paused_accum_sec = fresh.mes_paused_accum_sec
    target.mes_production_is_paused = fresh.mes_production_is_paused
    target.mes_operator_user_id = fresh.mes_operator_user_id
    target.mes_client_instance_id = fresh.mes_client_instance_id
    target.welding_machine = fresh.welding_machine
  }

  function listQueryParams(dayStr: string): {
    production_day: string
    welding_machine?: string
    limit: number
  } {
    const params: { production_day: string; welding_machine?: string; limit: number } = {
      production_day: dayStr,
      limit: 2000,
    }
    const machine = selectedWeldingMachineName.value
    if (machine) params.welding_machine = machine
    return params
  }

  /** 他端末行は一覧のみ更新；本端末操作行だけタイマー session をサーバーと同期 */
  function shouldHydrateSessionFromServer(planId: number): boolean {
    if (isPlanLocallyOperated(planId)) return true
    if (activePlanId.value === planId) return true
    const row = managementRows.value.find((r) => r.id === planId)
    return row != null && rowMesLockOwner(row) === 'mine'
  }

  function mergeManagementRowsFromServer(freshRows: WeldingMgmtRow[]): Map<number, WeldingMgmtRow> {
    const byId = new Map(freshRows.map((r) => [r.id, r]))
    const known = new Set(managementRows.value.map((r) => r.id))
    for (const row of managementRows.value) {
      const fresh = byId.get(row.id)
      if (fresh) copyWeldingRowFromServer(row, fresh)
    }
    const additions: WeldingMgmtRow[] = []
    for (const fresh of freshRows) {
      if (known.has(fresh.id)) continue
      additions.push({ ...fresh })
    }
    if (additions.length > 0) {
      managementRows.value.push(...additions)
      managementRows.value.sort(compareWeldingMgmtRows)
    }
    return byId
  }

  async function syncMesStateFromServer(): Promise<void> {
    if (mesSyncInFlight || !navigator.onLine) return
    if (selectedWeldingMachineId.value == null) return
    const day = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return
    mesSyncInFlight = true
    try {
      const res = await fetchWeldingManagementList(listQueryParams(day))
      if (!res.success || !res.data) return
      const freshRows = (res.data ?? []).filter((r): r is WeldingMgmtRow => r.id != null)
      const byId = mergeManagementRowsFromServer(freshRows)
      for (const row of managementRows.value) {
        const fresh = byId.get(row.id)
        if (!fresh || !shouldHydrateSessionFromServer(row.id)) continue
        if (isLocalMesEchoGuarded(row.id)) continue
        const sess = ensureSession(row.id)
        hydratePlanSessionFromRow(sess, fresh)
        normalizeSessionDefects(sess)
        if (sess.wallStart != null && sess.wallEnd == null) reconcileInProgressTimer(sess)
      }
      detachFromRemoteInProgressContext()
    } finally {
      mesSyncInFlight = false
    }
  }

  function getMesSyncIntervalMs(): number {
    if (typeof document === 'undefined') return MES_SYNC_INTERVAL_MS
    return document.visibilityState === 'hidden' ? MES_SYNC_INTERVAL_HIDDEN_MS : MES_SYNC_INTERVAL_MS
  }

  function restartMesSyncTimer(): void {
    if (mesSyncTimer) clearInterval(mesSyncTimer)
    mesSyncTimer = setInterval(() => void syncMesStateFromServer(), getMesSyncIntervalMs())
  }

  async function loadPlans(): Promise<void> {
    const dayStr = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dayStr)) {
      ElMessage.warning(t('mesWeldingActual.invalidProductionDay'))
      return
    }
    if (selectedWeldingMachineId.value == null) {
      managementRows.value = []
      activePlanId.value = null
      return
    }
    loadingPlans.value = true
    try {
      loadLocallyOperatedPlanIds(dayStr, selectedWeldingMachineId.value)
      const res = await fetchWeldingManagementList(listQueryParams(dayStr))
      if (!res.success) {
        ElMessage.error(res.message || t('mesWeldingActual.loadPlansFailed'))
        return
      }
      const rows = (res.data ?? []).filter((r): r is WeldingMgmtRow => r.id != null)
      managementRows.value = rows
      for (const r of rows) {
        const sess = ensureSession(r.id)
        hydratePlanSessionFromRow(sess, r)
        normalizeSessionDefects(sess)
        if (sess.wallStart != null && sess.wallEnd == null) reconcileInProgressTimer(sess)
      }
      const restored = applyPersistedSessionsForScope(
        dayStr,
        selectedWeldingMachineId.value,
        rows.map((r) => r.id),
        ensureSession,
      )
      for (const r of rows) normalizeSessionDefects(ensureSession(r.id))
      if (restored) ElMessage.info(t('mesWeldingActual.stateRestored'))
      flushPersistToStorage()
      void tryFlushOfflineQueue()
      tryReclaimOperatedPlansOnLoad()
      detachFromRemoteInProgressContext()
      bindContextFromSelection()
    } catch (e) {
      console.error(e)
      ElMessage.error(t('mesWeldingActual.loadPlansFailed'))
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
    const inspId = operatorUserId.value
    if (inspId == null) {
      activePlanId.value = null
      return
    }
    const row = findOpenRowForScope(code, inspId)
    activePlanId.value = row?.id ?? null
  }

  /** 設備・作業者・製品の選択に応じてアクティブ行を紐付け */
  function bindContextFromSelection(): void {
    const inProgMachine = findInProgressRowForMachine()
    if (
      inProgMachine?.product_cd &&
      inProgMachine.id != null &&
      isPlanLocallyOperated(inProgMachine.id)
    ) {
      selectedProductCode.value = inProgMachine.product_cd
      activePlanId.value = inProgMachine.id
      const ri = rowOperatorId(inProgMachine)
      if (ri != null) operatorUserId.value = ri
      return
    }
    const inspId = operatorUserId.value
    if (inspId != null) {
      const inProg = findInProgressRowForOperator(inspId)
      if (inProg?.product_cd && inProg.id != null && isPlanLocallyOperated(inProg.id)) {
        selectedProductCode.value = inProg.product_cd
        activePlanId.value = inProg.id
        return
      }
    }
    bindActivePlanFromSelection()
  }

  /** 他端末ロックの在産はフォーカス解除；本端末ロックは維持 */
  function detachFromRemoteInProgressContext(): void {
    const planId = activePlanId.value
    if (planId == null) return
    const row = managementRows.value.find((r) => r.id === planId)
    if (!row || !isRowMesProductionActive(row)) return
    const owner = rowMesLockOwner(row)
    if (owner === 'mine') {
      if (!isPlanLocallyOperated(planId)) markPlanLocallyOperated(planId)
      return
    }
    if (owner === 'other') {
      selectedProductCode.value = null
      activePlanId.value = null
      const ri = rowOperatorId(row)
      if (ri != null && operatorUserId.value === ri) operatorUserId.value = null
    }
  }

  /** ページ復帰時：選択中検査員のサーバー在産行を本端末操作対象に復帰 */
  function tryReclaimOperatedPlansOnLoad(): void {
    const inspId = operatorUserId.value
    if (inspId == null) return
    const row = findInProgressRowForOperator(inspId)
    if (row?.id != null && isRowMesProductionActive(row) && rowMesLockOwner(row) === 'mine') {
      markPlanLocallyOperated(row.id)
      syncActivePlanSessionFromRow(row.id)
    }
  }

  async function resumeInProgressSession(row: WeldingMgmtRow): Promise<void> {
    if (!guardMesOperation(canEdit)) return
    const ri = rowOperatorId(row)
    if (ri == null) {
      ElMessage.warning(t('mesWeldingActual.inspectorRequired'))
      return
    }
    if (row.id == null || !isRowMesProductionActive(row)) return
    if (rowMesLockOwner(row) === 'other') {
      ElMessage.warning(t('mesWeldingActual.sessionLockedByOtherTerminal'))
      return
    }
    suppressOperatorUserWatch = true
    try {
      if (rowMesLockOwner(row) !== 'mine') {
        const ok = await patchWithOfflineSync(row.id, {
          mes_claim_client_lock: true,
          mes_operator_user_id: ri,
        })
        if (!ok && navigator.onLine) return
        await loadPlans()
        const fresh = managementRows.value.find((r) => r.id === row.id)
        if (!fresh || rowMesLockOwner(fresh) === 'other') {
          ElMessage.warning(t('mesWeldingActual.sessionLockedByOtherTerminal'))
          return
        }
      }
      markPlanLocallyOperated(row.id)
      if (row.product_cd) selectedProductCode.value = row.product_cd
      activePlanId.value = row.id
      syncActivePlanSessionFromRow(row.id)
      const resumedSess = sessions[row.id]
      const freshRow = managementRows.value.find((r) => r.id === row.id) ?? row
      if (resumedSess) alignSessionElapsedFromWallClock(resumedSess, freshRow)
      operatorUserId.value = ri
      schedulePersist()
      ElMessage.success(t('mesWeldingActual.sessionResumed'))
    } finally {
      void nextTick(() => {
        suppressOperatorUserWatch = false
      })
    }
  }

  function focusInProgressRow(row: WeldingMgmtRow): void {
    if (row.product_cd) selectedProductCode.value = row.product_cd
    activePlanId.value = row.id
    const ri = rowOperatorId(row)
    if (ri != null) {
      if (!isRowMesProductionActive(row) || isPlanLocallyOperated(row.id)) {
        operatorUserId.value = ri
      }
    } else if (operatorUserId.value == null) {
      ElMessage.warning(t('mesWeldingActual.inspectorRequired'))
      return
    }
  }

  const inProgressRows = computed(() =>
    managementRows.value.filter(
      (r) =>
        rowMatchesSelectedMachine(r) &&
        isRowMesProductionActive(r) &&
        !isRowProductionCompleted(r),
    ),
  )

  /** 他端末でロック中の検査員は選択不可 */
  function isOperatorOptionDisabled(inspectorId: number): boolean {
    const busyRow = findInProgressRowForOperator(inspectorId)
    if (!busyRow?.id) return false
    if (rowMesLockOwner(busyRow) === 'other') return true
    if (rowMesLockOwner(busyRow) === 'mine') return false
    return true
  }

  function operatorOptionLabel(u: UserListItem): string {
    const base = (u.full_name || u.username || '').trim() || String(u.id)
    if (!isOperatorOptionDisabled(u.id)) return base
    return `${base} (${t('mesWeldingActual.inspectorInProgress')})`
  }

  const completedRows = computed(() =>
    managementRows.value.filter((r) => rowMatchesSelectedMachine(r) && isRowProductionCompleted(r)),
  )

  /** 溶接設備・製品が選ばれていれば生産カードを表示（作業者はカード内で選択） */
  const showPlanProductionCard = computed(() => {
    const code = selectedProductCode.value
    return Boolean(selectedWeldingMachineId.value != null && code)
  })

  const elapsedDisplay = computed(() => {
    const sess = session.value
    if (!sess) return '0:00:00'
    return formatElapsed(operationDisplayMs(sess, tickNow.value))
  })

  const pausedDisplay = computed(() => {
    const sess = session.value
    if (!sess) return '0:00:00'
    return formatElapsed(readPausedAccumMs(sess, tickNow.value))
  })

  const defectTotal = computed(() => {
    const sess = session.value
    if (!sess) return 0
    return totalDefectCountFromItems(defectItems.value, sess.defects)
  })

  const canOperateActivePlan = computed(() => {
    if (!canEdit.value) return false
    const planId = activePlanId.value
    if (planId == null) return false
    const row = managementRows.value.find((r) => r.id === planId)
    if (!row || !isRowMesProductionActive(row)) return isPlanLocallyOperated(planId)
    return rowMesLockOwner(row) === 'mine'
  })

  const canStart = computed(() => {
    if (!canEdit.value) return false
    if (
      selectedWeldingMachineId.value == null ||
      operatorUserId.value == null ||
      !selectedProductCode.value
    ) {
      return false
    }
    const planId = activePlanId.value
    const row = activeRow.value
    if (planId != null && row && isRowMesProductionActive(row) && !canOperateActivePlan.value) {
      return false
    }
    const sess = session.value
    if (!sess) return true
    return sess.wallStart == null
  })

  const canPause = computed(() => {
    const sess = session.value
    return canOperateActivePlan.value && sess != null && isTimerRunning(sess)
  })
  const canResume = computed(() => {
    const sess = session.value
    return canOperateActivePlan.value && sess != null && isTimerPaused(sess)
  })
  const canEnd = computed(
    () => canOperateActivePlan.value && activePlanSessionInProgress(),
  )

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
    return t(`mesWeldingActual.${map[timerStatusKey.value]}`)
  })

  const canEditDefects = computed(
    () => canOperateActivePlan.value && activePlanSessionInProgress(),
  )

  const canScanProduct = computed(
    () => selectedWeldingMachineId.value != null && !canEnd.value,
  )

  const showSessionRecoveryAlert = computed(() => {
    const id = activePlanId.value
    const row = activeRow.value
    if (id == null || !row || !isRowMesProductionActive(row)) return false
    const owner = rowMesLockOwner(row)
    if (owner === 'other') return false
    return owner === 'unclaimed' || !isPlanLocallyOperated(id)
  })

  /** 読取は5桁数字のみ。製品CDは末尾が「{5桁}1」または「{5桁}」の検査製品と照合 */
  function resolveProductCodeFromScan(scanned: string): string | null {
    const key = scanned.trim()
    if (!/^\d{5}$/.test(key)) return null
    const matches = products.value.filter((p) => {
      const cd = (p.product_code ?? '').trim()
      if (!cd) return false
      return cd.endsWith(`${key}1`) || cd.endsWith(key)
    })
    if (matches.length === 0) return null
    const strict = matches.filter((p) => (p.product_code ?? '').trim().endsWith(`${key}1`))
    if (strict.length === 1) return strict[0].product_code ?? null
    if (strict.length > 1) {
      strict.sort((a, b) => (a.product_code?.length ?? 0) - (b.product_code?.length ?? 0))
      return strict[0].product_code ?? null
    }
    if (matches.length === 1) return matches[0].product_code ?? null
    return null
  }

  function openProductScanDialog(): void {
    if (!canScanProduct.value) {
      ElMessage.warning(t('mesWeldingActual.switchProductBlocked'))
      return
    }
    productScanDialogVisible.value = true
  }

  function onProductBarcodeScanned(code: string): void {
    const trimmed = code.trim()
    if (!trimmed) return
    if (!canScanProduct.value) {
      ElMessage.warning(t('mesWeldingActual.switchProductBlocked'))
      return
    }
    if (!/^\d{5}$/.test(trimmed)) {
      ElMessage.warning(t('mesWeldingActual.scanProductInvalidDigits'))
      return
    }
    const productCd = resolveProductCodeFromScan(trimmed)
    if (!productCd) {
      ElMessage.warning(t('mesWeldingActual.scanProductNotFound', { code: trimmed }))
      return
    }
    selectedProductCode.value = productCd
    const p = products.value.find((x) => x.product_code === productCd)
    const label = p?.product_name
      ? `${productCd} · ${p.product_name}`
      : productCd
    ElMessage.success(t('mesWeldingActual.scanProductSelected', { label }))
  }

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

  /** 生産開始日時（wallStart またはサーバー mes_production_started_at） */
  function resolveSessionWallStartMs(
    sess: PlanSession,
    row?: WeldingMgmtRow | null,
  ): number | null {
    if (sess.wallStart != null) return sess.wallStart
    const started = row?.mes_production_started_at
    if (!started || !String(started).trim()) return null
    const ws = Date.parse(String(started))
    return Number.isNaN(ws) ? null : ws
  }

  /** 稼働時間表示：現在時刻 − 開始時刻（壁時計。一時停止中も経過は進む） */
  function operationDisplayMs(sess: PlanSession, now = tickNow.value): number {
    const planId = activePlanId.value
    const row =
      planId != null ? managementRows.value.find((r) => r.id === planId) ?? activeRow.value : activeRow.value
    const ws = resolveSessionWallStartMs(sess, row)
    if (ws == null) return 0
    if (sess.wallEnd != null) return Math.max(0, sess.wallEnd - ws)
    return Math.max(0, now - ws)
  }

  /** 確定実績表：一時停止累計（DB またはボタン操作セッション） */
  function rowPausedAccumSec(row: WeldingMgmtRow, now = tickNow.value): number {
    const stored = row.mes_paused_accum_sec
    if (stored != null && Number.isFinite(Number(stored))) {
      return Math.max(0, Math.round(Number(stored)))
    }
    if (row.id != null && sessions[row.id]) {
      return Math.max(0, Math.round(readPausedAccumMs(sessions[row.id], now) / 1000))
    }
    return 0
  }

  /** 確定実績表：開始〜終了（未終了は現在）の壁時計秒 */
  function rowWallElapsedSec(row: WeldingMgmtRow, now = tickNow.value): number {
    const started = row.mes_production_started_at
    if (!started || !String(started).trim()) return Math.max(0, row.mes_net_production_sec ?? 0)
    const ws = Date.parse(String(started))
    if (Number.isNaN(ws)) return Math.max(0, row.mes_net_production_sec ?? 0)
    const ended = row.mes_production_ended_at
    const we =
      ended != null && String(ended).trim() ? Date.parse(String(ended)) : now
    if (Number.isNaN(we)) return Math.max(0, row.mes_net_production_sec ?? 0)
    return Math.max(0, Math.floor((we - ws) / 1000))
  }

  function timerPhase(sess: PlanSession): 'idle' | 'running' | 'paused' | 'ended' {
    if (sess.wallEnd != null) return 'ended'
    if (sess.wallStart == null) return 'idle'
    if (sess.pauseSliceStart != null) return 'paused'
    if (sess.runningSliceStart != null) return 'running'
    return 'idle'
  }

  function timerPhaseLabel(sess: PlanSession): string {
    const ph = timerPhase(sess)
    const map = { idle: 'timerIdle', running: 'timerRunning', paused: 'timerPaused', ended: 'timerEnded' } as const
    return t(`mesWeldingActual.${map[ph]}`)
  }

  function formatWall(ts: number | null | undefined): string {
    if (ts == null) return '—'
    return formatDateTimeJST(new Date(ts), 'ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  }

  function sessionWallStartTs(sess: PlanSession | null): number | null {
    if (!sess) return null
    return resolveSessionWallStartMs(sess, activeRow.value)
  }

  function workSession(): PlanSession | null {
    const id = activePlanId.value
    if (id == null) return null
    return sessions[id] ?? null
  }

  const showOfflineAlert = computed(() => isBrowserOffline.value || offlineQueueCount.value > 0)
  const offlineAlertText = computed(() => {
    if (isBrowserOffline.value) return t('mesWeldingActual.offlineBanner')
    return t('mesWeldingActual.offlinePendingSync', { n: offlineQueueCount.value })
  })

  function defectCount(itemId: string): number {
    return Math.max(0, Math.round(session.value?.defects[itemId] ?? 0))
  }

  function bumpDefect(itemId: string, delta: number): void {
    if (!guardMesOperation(canEdit)) return
    const id = activePlanId.value
    const sess = session.value
    if (id == null || !sess || !isPlanLocallyOperated(id)) return
    sess.defects[itemId] = Math.max(0, defectCount(itemId) + delta)
    schedulePersist()
    scheduleDefectPatch(id)
  }

  async function onStartProduction(): Promise<void> {
    if (!guardMesOperation(canEdit)) return
    if (selectedWeldingMachineId.value == null) {
      ElMessage.warning(t('mesWeldingActual.machineRequired'))
      return
    }
    if (operatorUserId.value == null) {
      ElMessage.warning(t('mesWeldingActual.inspectorRequired'))
      return
    }
    const code = selectedProductCode.value
    const p = products.value.find((x) => x.product_code === code)
    if (!code || !p) return
    const name = (p.product_name || '').trim() || code
    const inspId = operatorUserId.value
    let planId = findOpenRowForScope(code, inspId)?.id ?? null
    if (planId == null) {
      planId = await ensurePlanForProduct(code, name)
      if (planId == null) return
    }
    activePlanId.value = planId
    const other = findOtherActiveRowForMachine(planId)
    if (other) {
      ElMessage.warning(
        t('mesWeldingActual.machineAlreadyProducing', { label: rowShortLabel(other) }),
      )
      return
    }
    const s = ensureSession(planId)
    if (s.wallStart != null) return
    const now = Date.now()
    markLocalMesEcho(planId)
    try {
      const ok = await patchWithOfflineSync(planId, {
        mes_production_started_at: new Date(now).toISOString(),
        mes_production_is_paused: 0,
        mes_operator_user_id: operatorUserId.value,
      })
      if (!ok && navigator.onLine) return
    } catch (e: unknown) {
      const { status, detail } = httpErrorFromUnknown(e)
      if (status === 409 && detail) {
        ElMessage.warning(detail)
      } else {
        ElMessage.error(detail || t('mesWeldingActual.saveFailed'))
      }
      void loadPlans()
      return
    }
    markPlanLocallyOperated(planId)
    s.wallStart = now
    s.activeAccumMs = 0
    s.pausedAccumMs = 0
    s.pauseSliceStart = null
    s.runningSliceStart = now
    schedulePersist()
    ElMessage.success(t('mesWeldingActual.started'))
  }

  function onPauseProduction(): void {
    if (!guardMesOperation(canEdit)) return
    const id = activePlanId.value
    if (id == null || !isPlanLocallyOperated(id)) return
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
    if (!guardMesOperation(canEdit)) return
    const id = activePlanId.value
    if (id == null || !isPlanLocallyOperated(id)) return
    const s = session.value
    if (id == null || !s || !isTimerPaused(s)) return
    const now = Date.now()
    flushPauseSlice(s, now)
    const ws = resolveSessionWallStartMs(s, activeRow.value)
    if (ws != null) {
      correctNetProductionFromWallClock(s, ws, now)
    } else {
      s.runningSliceStart = now
      s.pauseSliceStart = null
    }
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
    const ws = resolveSessionWallStartMs(s, row)
    const activeMs = ws != null ? Math.max(0, now - ws) : 0
    return {
      productName: row.product_name,
      operatorName: operatorLabel.value || t('mesWeldingActual.inspectorMissing'),
      wallStart: ws,
      wallEnd: now,
      activeMs,
      pausedMs: readPausedAccumMs(s, now),
      defects: { ...s.defects },
      defectTotal: totalDefectCountFromItems(defectItems.value, s.defects),
    }
  })

  const operatorLabel = computed(() => {
    const id = operatorUserId.value
    if (id == null) return ''
    const u = operators.value.find((x) => x.id === id)
    return (u?.full_name || u?.username || '').trim()
  })

  async function submitProductionEnd(): Promise<void> {
    if (!guardMesOperation(canEdit)) return
    const id = activePlanId.value
    const s = session.value
    const preview = endDialogPreview.value
    if (id == null || !s || !preview) return
    const qty = Math.round(Number(String(endDialogQty.value).trim()))
    if (!Number.isFinite(qty) || qty < 0) {
      ElMessage.warning(t('mesWeldingActual.qtyInvalid'))
      return
    }
    if (!navigator.onLine) {
      ElMessage.warning(t('mesWeldingActual.needOnlineForEnd'))
      return
    }
    const now = Date.now()
    if (isTimerRunning(s)) flushRunningSlice(s, now)
    if (isTimerPaused(s)) flushPauseSlice(s, now)
    s.wallEnd = now
    freezePausedAccumMs(s, now)
    endDialogSubmitting.value = true
    try {
      const ok = await patchWithOfflineSync(id, {
        mes_production_ended_at: new Date(now).toISOString(),
        mes_net_production_sec: netProductionSeconds(s),
        mes_paused_accum_sec: Math.max(0, Math.round((s.pausedAccumMs ?? 0) / 1000)),
        mes_production_is_paused: 0,
        mes_operator_user_id: operatorUserId.value ?? undefined,
        mes_defect_by_item: { ...s.defects },
        actual_production_quantity: qty,
        production_completed_check: true,
        defect_qty: preview.defectTotal,
      })
      if (!ok) return
      unmarkPlanLocallyOperated(id)
      endDialogVisible.value = false
      activePlanId.value = null
      Object.assign(sessions[id], emptySession(makeEmptyDefectCounts()))
      ElMessage.success(t('mesWeldingActual.completeSaved'))
      await loadPlans()
    } finally {
      endDialogSubmitting.value = false
    }
  }

  function defectItemLabel(item: Pick<MesDefectItemOption, 'id' | 'label'>): string {
    return resolveMesDefectItemLabel(item.id, item.label, t, te)
  }

  function defectItemLabelById(defectCd: string, fallbackName?: string): string {
    const master = defectItems.value.find((d) => d.id === defectCd)
    return resolveMesDefectItemLabel(defectCd, fallbackName ?? master?.label ?? defectCd, t, te)
  }

  function defectRowsForRecord(defects: Record<string, number>) {
    const rows: { id: string; label: string; qty: number }[] = []
    const seen = new Set<string>()
    for (const item of defectItems.value) {
      const qty = Math.max(0, Math.round(defects[item.id] ?? 0))
      if (qty <= 0) continue
      rows.push({ id: item.id, label: defectItemLabel(item), qty })
      seen.add(item.id)
    }
    for (const [id, rawQty] of Object.entries(defects)) {
      if (seen.has(id)) continue
      const qty = Math.max(0, Math.round(rawQty))
      if (qty <= 0) continue
      rows.push({ id, label: defectItemLabelById(id), qty })
    }
    return rows
  }

  function restorePageFilters(): void {
    const blob = loadWeldingActualPersist()
    if (!blob) return
    if (blob.productionDay && /^\d{4}-\d{2}-\d{2}$/.test(blob.productionDay)) {
      productionDay.value = blob.productionDay
    }
    if (blob.selectedWeldingMachineId != null) {
      selectedWeldingMachineId.value = blob.selectedWeldingMachineId
    }
    if (blob.operatorUserId != null) operatorUserId.value = blob.operatorUserId
    if (blob.selectedProductCode) selectedProductCode.value = blob.selectedProductCode
    if (blob.activePlanId != null) activePlanId.value = blob.activePlanId
  }

  watch(productionDay, () => {
    schedulePersist()
    void loadPlans()
  })

  watch(selectedWeldingMachineId, (newId, oldId) => {
    if (suppressMachineWatch) {
      schedulePersist()
      return
    }
    selectedProductCode.value = null
    activePlanId.value = null
    if (newId == null) {
      products.value = []
      managementRows.value = []
      schedulePersist()
      return
    }
    if (oldId != null && newId !== oldId) {
      operatorUserId.value = null
    }
    schedulePersist()
    void loadProducts()
    void loadPlans()
  })

  watch(selectedProductCode, (code) => {
    if (!code) {
      activePlanId.value = null
      return
    }
    const inProgress = activePlanId.value != null && session.value && isProductionInProgress(session.value)
    if (inProgress && activeRow.value?.product_cd !== code) {
      ElMessage.warning(t('mesWeldingActual.switchProductBlocked'))
      selectedProductCode.value = activeRow.value?.product_cd ?? null
      return
    }
    bindActivePlanFromSelection()
    schedulePersist()
  })

  watch(operatorUserId, (newId, oldId) => {
    if (newId == null) {
      schedulePersist()
      return
    }
    if (suppressOperatorUserWatch) {
      schedulePersist()
      return
    }
    if (isOperatorOptionDisabled(newId)) {
      const busyRow = findInProgressRowForOperator(newId)
      operatorUserId.value = oldId ?? null
      ElMessage.warning(
        t('mesWeldingActual.inspectorBusyElsewhere', {
          inspector: operatorNameById(newId) || String(newId),
          label: busyRow ? rowShortLabel(busyRow) : '—',
        }),
      )
      return
    }
    const planId = activePlanId.value
    const sess = planId != null ? sessions[planId] : null
    if (sess && isProductionInProgress(sess)) {
      const rowInsp = activeRow.value ? rowOperatorId(activeRow.value) : null
      if (rowInsp != null && rowInsp !== newId) {
        operatorUserId.value = oldId ?? rowInsp
        ElMessage.warning(t('mesWeldingActual.switchInspectorBlocked'))
        return
      }
    }
    detachFromRemoteInProgressContext()
    bindContextFromSelection()
    const planIdAfter = activePlanId.value
    const sessAfter = planIdAfter != null ? sessions[planIdAfter] : null
    if (
      planIdAfter != null &&
      newId != null &&
      (!sessAfter || !isProductionInProgress(sessAfter))
    ) {
      if (canServerPatchPlan(planIdAfter)) {
        void patchWithOfflineSync(planIdAfter, { mes_operator_user_id: newId }, { silentQueue: true })
      }
    }
    schedulePersist()
  })

  function shiftProductionDay(delta: number): void {
    const base = (productionDay.value ?? '').trim().slice(0, 10)
    const anchor = /^\d{4}-\d{2}-\d{2}$/.test(base) ? base : getJSTToday()
    productionDay.value = shiftDateYmdJST(anchor, delta)
  }

  function setProductionDayToday(): void {
    productionDay.value = getJSTToday()
  }

  async function loadMachines(): Promise<void> {
    loadingMachines.value = true
    try {
      machines.value = await fetchWeldingMesMachines()
    } catch (e) {
      console.error(e)
      ElMessage.error(t('mesWeldingActual.loadMachinesFailed'))
    } finally {
      loadingMachines.value = false
    }
  }

  async function loadProducts(): Promise<void> {
    const machineId = selectedWeldingMachineId.value
    if (machineId == null) {
      products.value = []
      return
    }
    loadingProducts.value = true
    try {
      products.value = await fetchWeldingMesProducts(machineId)
      const code = selectedProductCode.value
      if (code && !products.value.some((p) => p.product_code === code)) {
        const inProgress =
          activePlanId.value != null && session.value != null && isProductionInProgress(session.value)
        if (!inProgress) selectedProductCode.value = null
      }
    } catch (e) {
      console.error(e)
      products.value = []
      ElMessage.error(t('mesWeldingActual.loadProductsFailed'))
    } finally {
      loadingProducts.value = false
    }
  }

  async function loadDefectItems(): Promise<void> {
    loadingDefectItems.value = true
    try {
      defectItems.value = await loadMesDefectItemsForProcess(WELDING_DEFECT_DETECTION_PROCESS_CD)
      for (const sess of Object.values(sessions)) {
        normalizeSessionDefects(sess)
      }
    } catch {
      defectItems.value = []
      ElMessage.error(t('mesWeldingActual.loadDefectItemsFailed'))
    } finally {
      loadingDefectItems.value = false
    }
  }

  async function loadOperators(): Promise<void> {
    loadingOperators.value = true
    try {
      const res = (await getUsers({ page: 1, page_size: 500, status: 'active' })) as unknown as PaginatedUserResponse
      operators.value = res?.items ?? []
    } catch {
      ElMessage.error(t('mesWeldingActual.loadOperatorsFailed'))
    } finally {
      loadingOperators.value = false
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
    restartMesSyncTimer()
    mesSyncVisibilityHandler = () => {
      restartMesSyncTimer()
      if (document.visibilityState === 'visible') void syncMesStateFromServer()
    }
    document.addEventListener('visibilitychange', mesSyncVisibilityHandler)
    void syncMesStateFromServer()
  }

  interface ConfirmedHistoryEditDraft {
    operatorUserId: number | null
    actualQty: number | null
    defects: Record<string, number>
    wallStart: Date | null
    wallEnd: Date | null
    pausedAccumSec: number
    savedWallStart: number | null
    savedWallEnd: number | null
    savedPausedAccumMs: number
    savedActiveAccumMs: number
    savedDefects: Record<string, number>
  }

  const confirmedEditDialogVisible = ref(false)
  const confirmedEditRow = ref<WeldingMgmtRow | null>(null)
  const confirmedEditPlanId = ref<number | null>(null)
  const confirmedEditForm = ref<ConfirmedHistoryEditDraft | null>(null)
  const confirmedEditSaving = ref(false)
  const confirmedEditClearing = ref(false)

  function buildClearInspectionMesPatchBody(): PatchWeldingManagementBody {
    return {
      production_completed_check: false,
      mes_production_started_at: '',
      mes_production_ended_at: '',
      mes_net_production_sec: -1,
      mes_paused_accum_sec: -1,
      mes_production_is_paused: -1,
      mes_operator_user_id: 0,
      mes_defect_by_item: {},
    }
  }

  function resetLocalSessionAfterMesClear(planId: number): void {
    const sess = sessions[planId]
    if (!sess) return
    Object.assign(sess, emptySession(makeEmptyDefectCounts()))
  }

  const confirmedEditElapsedPreview = computed(() => {
    const draft = confirmedEditForm.value
    if (!draft) return '00:00:00'
    const ws = draft.wallStart?.getTime()
    const we = draft.wallEnd?.getTime()
    if (ws == null || we == null || !Number.isFinite(ws) || !Number.isFinite(we)) return '00:00:00'
    const pauseMs = Math.max(0, Math.round(draft.pausedAccumSec)) * 1000
    return formatElapsed(Math.max(0, we - ws - pauseMs))
  })

  function applyConfirmedEditToSession(planId: number, draft: ConfirmedHistoryEditDraft): void {
    const sess = ensureSession(planId)
    const ws = draft.wallStart?.getTime()
    const we = draft.wallEnd?.getTime()
    if (ws == null || !Number.isFinite(ws) || we == null || !Number.isFinite(we)) return
    const pauseMs = Math.max(0, Math.round(draft.pausedAccumSec)) * 1000
    sess.wallStart = ws
    sess.wallEnd = we
    sess.runningSliceStart = null
    sess.pauseSliceStart = null
    sess.pausedAccumMs = pauseMs
    sess.activeAccumMs = Math.max(0, we - ws - pauseMs)
    sess.defects = mergeSessionDefects(draft.defects)
  }

  function restoreConfirmedEditSessionFromDraft(planId: number, draft: ConfirmedHistoryEditDraft): void {
    const sess = ensureSession(planId)
    sess.wallStart = draft.savedWallStart
    sess.wallEnd = draft.savedWallEnd
    sess.pausedAccumMs = draft.savedPausedAccumMs
    sess.activeAccumMs = draft.savedActiveAccumMs
    sess.defects = { ...draft.savedDefects }
    sess.runningSliceStart = null
    sess.pauseSliceStart = null
  }

  function clearConfirmedEditState(): void {
    confirmedEditDialogVisible.value = false
    confirmedEditRow.value = null
    confirmedEditPlanId.value = null
    confirmedEditForm.value = null
    confirmedEditSaving.value = false
    confirmedEditClearing.value = false
  }

  function openConfirmedHistoryEdit(row: WeldingMgmtRow): void {
    if (!guardMesOperation(canEdit)) return
    const id = row.id
    if (id == null || !isRowProductionCompleted(row)) return
    const sess = ensureSession(id)
    hydratePlanSessionFromRow(sess, row)
    normalizeSessionDefects(sess)
    confirmedEditRow.value = row
    confirmedEditPlanId.value = id
    confirmedEditForm.value = {
      operatorUserId: rowOperatorId(row),
      actualQty:
        row.actual_production_quantity != null && Number.isFinite(Number(row.actual_production_quantity))
          ? Math.round(Number(row.actual_production_quantity))
          : null,
      defects: { ...sess.defects },
      wallStart: sess.wallStart != null ? new Date(sess.wallStart) : null,
      wallEnd: sess.wallEnd != null ? new Date(sess.wallEnd) : null,
      pausedAccumSec: Math.round((sess.pausedAccumMs ?? 0) / 1000),
      savedWallStart: sess.wallStart,
      savedWallEnd: sess.wallEnd,
      savedPausedAccumMs: sess.pausedAccumMs ?? 0,
      savedActiveAccumMs: sess.activeAccumMs,
      savedDefects: { ...sess.defects },
    }
    confirmedEditDialogVisible.value = true
  }

  function closeConfirmedHistoryEdit(): void {
    const planId = confirmedEditPlanId.value
    const draft = confirmedEditForm.value
    if (planId != null && draft) {
      restoreConfirmedEditSessionFromDraft(planId, draft)
    }
    clearConfirmedEditState()
  }

  function confirmedEditDefectCount(defectCd: string): number {
    return Math.max(0, Math.round(confirmedEditForm.value?.defects[defectCd] ?? 0))
  }

  function bumpConfirmedEditDefect(defectCd: string, delta: number): void {
    const form = confirmedEditForm.value
    if (!form) return
    const next = Math.max(0, (form.defects[defectCd] ?? 0) + delta)
    if (next === 0) delete form.defects[defectCd]
    else form.defects[defectCd] = next
  }

  async function submitConfirmedHistoryEdit(): Promise<void> {
    if (!guardMesOperation(canEdit)) return
    const row = confirmedEditRow.value
    const planId = confirmedEditPlanId.value
    const draft = confirmedEditForm.value
    if (!row || planId == null || !draft) return
    if (!navigator.onLine) {
      ElMessage.warning(t('mesWeldingActual.needOnlineForEdit'))
      return
    }
    if (draft.operatorUserId == null || draft.operatorUserId <= 0) {
      ElMessage.warning(t('mesWeldingActual.inspectorRequired'))
      return
    }
    if (draft.actualQty != null && (!Number.isFinite(draft.actualQty) || draft.actualQty < 0)) {
      ElMessage.warning(t('mesWeldingActual.qtyInvalid'))
      return
    }
    const ws = draft.wallStart?.getTime()
    const we = draft.wallEnd?.getTime()
    if (ws == null || !Number.isFinite(ws) || we == null || !Number.isFinite(we)) {
      ElMessage.warning(t('mesWeldingActual.editTimeRequired'))
      return
    }
    if (we < ws) {
      ElMessage.warning(t('mesWeldingActual.editTimeOrder'))
      return
    }
    const wallSec = (we - ws) / 1000
    const pauseSec = Math.max(0, Math.round(draft.pausedAccumSec))
    if (!Number.isFinite(pauseSec) || pauseSec > wallSec) {
      ElMessage.warning(t('mesWeldingActual.editPauseTooLong'))
      return
    }

    applyConfirmedEditToSession(planId, draft)
    const defects = mergeSessionDefects(draft.defects)
    const body: PatchWeldingManagementBody = {
      mes_production_started_at: new Date(ws).toISOString(),
      mes_production_ended_at: new Date(we).toISOString(),
      mes_paused_accum_sec: pauseSec,
      mes_net_production_sec: Math.max(0, Math.round(wallSec - pauseSec)),
      mes_production_is_paused: 0,
      mes_operator_user_id: draft.operatorUserId,
      mes_defect_by_item: defects,
      production_completed_check: true,
    }
    if (draft.actualQty != null && Number.isFinite(draft.actualQty)) {
      body.actual_production_quantity = Math.max(0, Math.round(draft.actualQty))
    }

    confirmedEditSaving.value = true
    try {
      const ok = await patchWithOfflineSync(planId, body)
      if (!ok) return
      ElMessage.success(t('mesWeldingActual.confirmedEditSaved'))
      clearConfirmedEditState()
      flushPersistToStorage()
      await loadPlans()
    } catch (e: unknown) {
      console.error(e)
      ElMessage.error(t('mesWeldingActual.saveFailed'))
    } finally {
      confirmedEditSaving.value = false
    }
  }

  async function clearConfirmedHistoryMesAndSave(): Promise<void> {
    if (!guardMesOperation(canDelete)) return
    const row = confirmedEditRow.value
    const planId = confirmedEditPlanId.value
    if (!row || planId == null) return
    if (!navigator.onLine) {
      ElMessage.warning(t('mesWeldingActual.needOnlineForEdit'))
      return
    }
    try {
      await ElMessageBox.confirm(
        t('mesWeldingActual.clearMesConfirmMessage'),
        t('mesWeldingActual.clearMesConfirmTitle'),
        {
          type: 'warning',
          confirmButtonText: t('mesWeldingActual.btnClearMesActual'),
          cancelButtonText: t('common.cancel'),
        },
      )
    } catch {
      return
    }

    resetLocalSessionAfterMesClear(planId)
    confirmedEditClearing.value = true
    try {
      const ok = await patchWithOfflineSync(planId, buildClearInspectionMesPatchBody())
      if (!ok) return
      ElMessage.success(t('mesWeldingActual.clearMesSaved'))
      clearConfirmedEditState()
      flushPersistToStorage()
      await loadPlans()
    } catch (e: unknown) {
      console.error(e)
      ElMessage.error(t('mesWeldingActual.saveFailed'))
    } finally {
      confirmedEditClearing.value = false
    }
  }

  function teardownLifecycle(): void {
    if (tickTimer) clearInterval(tickTimer)
    if (persistTimer) clearTimeout(persistTimer)
    if (runningPersistTimer) clearInterval(runningPersistTimer)
    if (mesSyncTimer) clearInterval(mesSyncTimer)
    if (mesSyncVisibilityHandler) {
      document.removeEventListener('visibilitychange', mesSyncVisibilityHandler)
      mesSyncVisibilityHandler = null
    }
    flushPersistToStorage()
    window.removeEventListener('beforeunload', flushPersistToStorage)
  }

  async function init(): Promise<void> {
    setupLifecycle()
    refreshOfflineQueueCount()
    await Promise.all([loadMachines(), loadOperators(), loadDefectItems()])
    if (selectedWeldingMachineId.value != null) {
      await loadProducts()
    }
    await loadPlans()
    void tryFlushOfflineQueue({ reloadAfter: true })
  }

  return {
    defectItems,
    loadingDefectItems,
    productScanDialogVisible,
    canScanProduct,
    openProductScanDialog,
    onProductBarcodeScanned,
    productionDay,
    selectedWeldingMachineId,
    machines,
    loadingMachines,
    operatorUserId,
    selectedProductCode,
    activePlanId,
    activeRow,
    inProgressRows,
    focusInProgressRow,
    resumeInProgressSession,
    canResumeSession,
    rowMesLockOwner,
    isPlanLocallyOperated,
    showSessionRecoveryAlert,
    operatorNameById,
    isOperatorOptionDisabled,
    operatorOptionLabel,
    products,
    operators,
    managementRows,
    completedRows,
    showPlanProductionCard,
    loadingProducts,
    loadingOperators,
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
    operatorLabel,
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
    defectItemLabel,
    defectRowsForRecord,
    workSession,
    formatElapsed,
    operationDisplayMs,
    rowWallElapsedSec,
    rowPausedAccumSec,
    readPausedAccumMs,
    timerPhase,
    timerPhaseLabel,
    formatWall,
    sessionWallStartTs,
    isProductionInProgress,
    confirmedEditDialogVisible,
    confirmedEditRow,
    confirmedEditForm,
    confirmedEditSaving,
    confirmedEditClearing,
    confirmedEditElapsedPreview,
    openConfirmedHistoryEdit,
    closeConfirmedHistoryEdit,
    submitConfirmedHistoryEdit,
    clearConfirmedHistoryMesAndSave,
    confirmedEditDefectCount,
    bumpConfirmedEditDefect,
    init,
    teardownLifecycle,
    canCreate,
    canEdit,
    canDelete,
    canExport,
  }
}
