import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import {
  fetchInspectionMonitorSummary,
  fetchInspectionNextAssignments,
  upsertInspectionNextAssignment,
  deleteInspectionNextAssignment,
  patchInspectionManagement,
  type InspectionManagementListRow,
  type InspectionNextAssignment,
} from '@/api/inspectionManagement'
import { getProductList } from '@/api/master/productMaster'
import {
  fetchWeldingMonitorSummary,
  patchWeldingManagement,
  type WeldingManagementListRow,
} from '@/api/weldingManagement'
import { fetchWeldingMesMachines, type WeldingMesMachine } from '@/api/weldingMesEquipment'
import { INSPECTION_DEFECT_DETECTION_PROCESS_CD } from '@/views/mes/actualDataCollection/inspection/inspectionActualConfig'
import { WELDING_DEFECT_DETECTION_PROCESS_CD } from '@/views/mes/actualDataCollection/welding/weldingActualConfig'
import {
  loadMesDefectItemsForProcess,
  resolveMesDefectItemLabel,
  type MesDefectItemOption,
} from '@/views/mes/actualDataCollection/shared/loadProcessDefectItems'
import {
  collectWeldingPersistForMonitorDay,
  getWeldingPersistOperatorUserId,
} from '@/views/mes/actualDataCollection/welding/weldingActualPersist'
import { fetchInspectionShiageSectionInspectors, type InspectionInspectorOption } from '@/views/mes/shared/inspectionInspectorFilter'
import { formatDateTimeJST, getJSTToday, localeForIntl } from '@/utils/dateFormat'
import {
  buildHistoryRows,
  buildInspectionDefectListRows,
  buildMonitorDefectListRows,
  buildInspectionInspectorEfficiencyRows,
  isInspectionClientCommStale,
  computeCompletedInspectorAvgEfficiency,
  breakSecondsForInspectionRow,
  buildMachineStatus,
  classifyInspectionRow,
  operatorNameById,
  operatorNameForRow,
  pausedSecondsForRow,
  type InspectionPersistSession,
  weldingElapsedFromPersist,
} from './monitorHelpers'
import {
  loadInspectionActualPersist,
  makePersistScopeKey,
} from '@/views/mes/actualDataCollection/inspection/inspectionActualPersist'
import { monitorProcessByKey } from './monitorProcesses'
import { filterInspectionProductOptions } from '@/views/mes/actualDataCollection/inspection/inspectionProductFilter'
import type { MonitorProcessKey, MachineStatus, NextAssignPanelRow, ProcessSummary } from './monitorTypes'

interface MonitorProductOption {
  product_code: string
  product_name: string
}

const MODERN_MONITOR_AUTO_REFRESH_MS = 15000
const TICK_MS = 1000
const FETCH_ERROR_TOAST_COOLDOWN_MS = 30000

function weldingMachineLabel(row: WeldingManagementListRow): string {
  return (row.welding_machine ?? '').trim()
}

function inspectionCardName(row: InspectionManagementListRow): string {
  const cd = (row.product_cd ?? '').trim()
  const name = (row.product_name ?? '').trim()
  if (cd && name) return `${cd} · ${name}`
  return cd || name || '検査ライン'
}

function mergeOperatorsFromInspectionRows(rows: InspectionManagementListRow[]): UserListItem[] {
  const map = new Map<number, UserListItem>()
  for (const row of rows) {
    const id = row.mes_inspector_user_id
    if (id == null || !Number.isFinite(Number(id)) || Number(id) <= 0) continue
    const uid = Number(id)
    const fullName = (row.mes_inspector_name ?? '').trim()
    const username = (row.mes_inspector_username ?? '').trim()
    if (!fullName && !username) continue
    map.set(uid, {
      id: uid,
      full_name: fullName || undefined,
      username: username || fullName || String(uid),
    } as UserListItem)
  }
  return [...map.values()]
}

function mergeOperatorLists(base: UserListItem[], extra: UserListItem[]): UserListItem[] {
  const map = new Map<number, UserListItem>()
  for (const u of base) {
    if (u.id != null) map.set(Number(u.id), u)
  }
  for (const u of extra) {
    if (u.id == null) continue
    const id = Number(u.id)
    const prev = map.get(id)
    if (!prev) {
      map.set(id, u)
      continue
    }
    map.set(id, {
      ...prev,
      full_name: prev.full_name || u.full_name,
      username: prev.username || u.username,
    })
  }
  return [...map.values()]
}

function isModernMonitorProcess(key: MonitorProcessKey): boolean {
  return key === 'inspection' || key === 'welding'
}

function extractFetchErrorMessage(e: unknown, pageTitle: string): string {
  const err = e as {
    response?: { data?: { detail?: string; message?: string }; status?: number }
    message?: string
  }
  if (err?.response?.status === 403) {
    return err.response.data?.detail ?? `${pageTitle}へのアクセス権がありません`
  }
  return (
    err?.response?.data?.detail ??
    err?.response?.data?.message ??
    err?.message ??
    'データの取得に失敗しました'
  )
}

export function useProcessMonitor(processKey: MonitorProcessKey) {
  const config = monitorProcessByKey(processKey)
  const router = useRouter()
  const { locale, t, te } = useI18n()
  const intlLocale = computed(() => localeForIntl(locale.value as string))

  const productionDay = ref(getJSTToday())
  const loading = ref(false)
  const autoRefresh = ref(true)
  const tickNow = ref(Date.now())
  const lastUpdatedAt = ref<number | null>(null)
  const lastFetchError = ref<string | null>(null)
  const cachedKpiAvgEfficiency = ref<number | null>(null)
  const fullscreen = ref(false)
  const pageVisible = ref(typeof document !== 'undefined' ? !document.hidden : true)

  let tickTimer: ReturnType<typeof setInterval> | null = null
  let refreshTimer: ReturnType<typeof setInterval> | null = null
  let fetchSeq = 0
  let lastErrorToastAt = 0
  let operatorsLoaded = false

  const inspectionRows = ref<InspectionManagementListRow[]>([])
  const nextAssignments = ref<InspectionNextAssignment[]>([])
  const monitorProducts = ref<MonitorProductOption[]>([])
  const loadingMonitorProducts = ref(false)
  const nextAssignDialogVisible = ref(false)
  const nextAssignSubmitting = ref(false)
  const nextAssignTarget = ref<{
    inspectorUserId: number
    inspectorName: string
    currentProductLabel: string
    isFirstProduct: boolean
  } | null>(null)
  const nextAssignProductCd = ref('')
  const nextAssignPickInspector = ref(false)
  const nextAssignInspectorUserId = ref<number | null>(null)
  const inspectionInspectorOptions = ref<InspectionInspectorOption[]>([])
  const loadingInspectionInspectors = ref(false)
  const weldingRows = ref<WeldingManagementListRow[]>([])
  const weldingMachines = ref<WeldingMesMachine[]>([])
  const operators = ref<UserListItem[]>([])
  const defectItems = ref<MesDefectItemOption[]>([])

  const refreshIntervalMs = MODERN_MONITOR_AUTO_REFRESH_MS

  function defectItemLabel(cd: string, fallback?: string): string {
    const master = defectItems.value.find((d) => d.id === cd)
    return resolveMesDefectItemLabel(cd, fallback ?? master?.label ?? cd, t, te)
  }

  function inspectionPersistByPlanId(day: string): Map<number, InspectionPersistSession> {
    const map = new Map<number, InspectionPersistSession>()
    const store = loadInspectionActualPersist()
    const scope = store?.scopes?.[makePersistScopeKey(day)]
    if (!scope?.sessions) return map
    for (const [id, sess] of Object.entries(scope.sessions)) {
      map.set(Number(id), {
        breakAccumMs: sess.breakAccumMs,
        breakSliceStart: sess.breakSliceStart ?? null,
      })
    }
    return map
  }

  function weldingPersistBreakByPlanId(day: string): Map<number, InspectionPersistSession> {
    const { sessionsByPlanId } = collectWeldingPersistForMonitorDay(day)
    const map = new Map<number, InspectionPersistSession>()
    for (const [id, sess] of sessionsByPlanId) {
      map.set(id, {
        breakAccumMs: sess.breakAccumMs,
        breakSliceStart: sess.breakSliceStart ?? null,
      })
    }
    return map
  }

  function notifyFetchError(message: string): void {
    lastFetchError.value = message
    const now = Date.now()
    if (now - lastErrorToastAt >= FETCH_ERROR_TOAST_COOLDOWN_MS) {
      lastErrorToastAt = now
      ElMessage.error(message)
    }
  }

  function refreshKpiEfficiencyCache(): void {
    if (!isModernMonitorProcess(processKey)) return
    const rows =
      processKey === 'inspection' ? inspectionRows.value : weldingRows.value
    cachedKpiAvgEfficiency.value = computeCompletedInspectorAvgEfficiency(
      rows,
      operators.value,
    )
  }

  function nextAssignmentByInspectorId(inspectorUserId: number | null | undefined): InspectionNextAssignment | undefined {
    if (inspectorUserId == null || !Number.isFinite(Number(inspectorUserId))) return undefined
    return nextAssignments.value.find((a) => a.inspector_user_id === Number(inspectorUserId))
  }

  function buildInspectionSummary(): ProcessSummary {
    const rows = inspectionRows.value
    const day = (productionDay.value ?? '').trim()
    const inspPersist = inspectionPersistByPlanId(day)
    const total = rows.length
    const completed = rows.filter((r) => classifyInspectionRow(r) === 'completed').length
    const inProgress = rows.filter((r) => classifyInspectionRow(r) === 'running').length
    const paused = rows.filter((r) => classifyInspectionRow(r) === 'paused').length
    const onBreak = rows.filter((r) => classifyInspectionRow(r) === 'break').length

    const machines = []
    for (const row of rows) {
      const rowStatus = classifyInspectionRow(row)
      if (rowStatus !== 'running' && rowStatus !== 'paused' && rowStatus !== 'break') continue
      const card = buildMachineStatus(
        inspectionCardName(row),
        [row],
        operators.value,
        tickNow.value,
        classifyInspectionRow,
        undefined,
        inspPersist,
      )
      if (row.id != null) card.id = row.id
      const inspectorId = row.mes_inspector_user_id
      if (inspectorId != null) card.inspectorUserId = Number(inspectorId)
      const na = nextAssignmentByInspectorId(inspectorId)
      if (na) {
        card.nextProductCd = na.next_product_cd ?? null
        card.nextProductName = na.next_product_name ?? null
        card.nextAssignedAt = na.assigned_at ?? null
      }
      const stale = isInspectionClientCommStale(row, tickNow.value, rowStatus)
      card.commStale = stale
      card.lastCommAt = stale ? (row.updated_at ?? null) : null
      machines.push(card)
    }
    machines.sort((a, b) => a.name.localeCompare(b.name, 'ja'))

    const inspectorEfficiencyRows = buildInspectionInspectorEfficiencyRows(
      rows,
      operators.value,
      tickNow.value,
    )

    return {
      key: 'inspection',
      label: config.label,
      icon: config.icon,
      color: config.color,
      gradient: config.gradient,
      totalPlans: total,
      completedPlans: completed,
      inProgressPlans: inProgress,
      pausedPlans: paused,
      breakPlans: onBreak,
      waitingPlans: rows.filter((r) => classifyInspectionRow(r) === 'waiting').length,
      totalQty: 0,
      actualQty: rows.reduce((s, r) => s + (r.actual_production_quantity ?? 0), 0),
      defectQty: rows.reduce((s, r) => s + (r.defect_qty ?? 0), 0),
      machines,
      historyRows: buildHistoryRows(rows, operators.value, tickNow.value, () => '—'),
      defectListRows: buildInspectionDefectListRows(
        rows,
        operators.value,
        defectItems.value,
        defectItemLabel,
      ),
      inspectorEfficiencyRows,
      inspectorAvgEfficiency: cachedKpiAvgEfficiency.value,
      commStalePlans: machines.filter((m) => m.commStale).length,
    }
  }

  function applyWeldingMachineCommStale(
    card: MachineStatus,
    mRows: WeldingManagementListRow[],
    classifyWeldingRow: (row: WeldingManagementListRow) => ReturnType<typeof classifyInspectionRow>,
  ): void {
    const active = mRows.find((r) => {
      const s = classifyWeldingRow(r)
      return s === 'running' || s === 'paused' || s === 'break'
    })
    if (!active) return
    const st = classifyWeldingRow(active)
    if (st !== 'running' && st !== 'paused' && st !== 'break') return
    const stale = isInspectionClientCommStale(active, tickNow.value, st)
    card.commStale = stale
    card.lastCommAt = stale ? (active.updated_at ?? null) : null
  }

  function buildWeldingSummary(): ProcessSummary {
    const rows = weldingRows.value
    const day = (productionDay.value ?? '').trim()
    const { sessionsByPlanId, machineActivities } = collectWeldingPersistForMonitorDay(day)
    const weldBreakPersist = weldingPersistBreakByPlanId(day)

    function classifyWeldingRow(row: WeldingManagementListRow) {
      if (row.id != null) {
        const sess = sessionsByPlanId.get(row.id)
        if (sess?.wallStart != null && sess.wallEnd == null) {
          if (sess.breakSliceStart != null) return 'break' as const
          if (sess.pauseSliceStart != null) return 'paused' as const
          return 'running' as const
        }
      }
      return classifyInspectionRow(row)
    }

    const knownNames = new Set<string>()
    for (const m of weldingMachines.value) {
      const label = (m.machine_name ?? '').trim()
      if (label) knownNames.add(label)
    }

    const machines = []
    for (const name of [...knownNames].sort((a, b) => a.localeCompare(b, 'ja'))) {
      const mRows = rows.filter((r) => weldingMachineLabel(r) === name)
      const card = buildMachineStatus(
        name,
        mRows,
        operators.value,
        tickNow.value,
        classifyWeldingRow,
        sessionsByPlanId,
        weldBreakPersist,
      )
      applyWeldingMachineCommStale(card, mRows, classifyWeldingRow)
      machines.push(card)
    }

    const unassigned = rows.filter((r) => !weldingMachineLabel(r))
    if (unassigned.length > 0) {
      const card = buildMachineStatus(
        '未割当',
        unassigned,
        operators.value,
        tickNow.value,
        classifyWeldingRow,
        sessionsByPlanId,
        weldBreakPersist,
      )
      applyWeldingMachineCommStale(card, unassigned, classifyWeldingRow)
      machines.push(card)
    }

    for (const r of rows) {
      const label = weldingMachineLabel(r)
      if (!label || knownNames.has(label)) continue
      const mRows = rows.filter((x) => weldingMachineLabel(x) === label)
      const card = buildMachineStatus(
        label,
        mRows,
        operators.value,
        tickNow.value,
        classifyWeldingRow,
        sessionsByPlanId,
        weldBreakPersist,
      )
      applyWeldingMachineCommStale(card, mRows, classifyWeldingRow)
      machines.push(card)
      knownNames.add(label)
    }

    for (const act of machineActivities) {
      const machineName = (
        weldingMachines.value.find((m) => m.id === act.machineId)?.machine_name ?? ''
      ).trim()
      if (!machineName) continue
      const row = rows.find((r) => r.id === act.planId)
      let card: MachineStatus | undefined = machines.find((m) => m.name === machineName)
      if (!card) {
        card = buildMachineStatus(
          machineName,
          row ? [row] : [],
          operators.value,
          tickNow.value,
          classifyWeldingRow,
          sessionsByPlanId,
          weldBreakPersist,
        )
        machines.push(card)
      }
      const sess = sessionsByPlanId.get(act.planId)
      const nextStatus: MachineStatus['status'] = sess?.breakSliceStart != null
        ? 'break'
        : act.paused || sess?.pauseSliceStart != null
          ? 'paused'
          : 'running'
      if (card.status !== 'running' && card.status !== 'paused' && card.status !== 'break') {
        card.status = nextStatus
      }
      if (row) {
        card.currentProduct = row.product_name || ''
        card.currentProductCd = row.product_cd || ''
        card.operatorName = operatorNameForRow(row, operators.value)
        applyWeldingMachineCommStale(card, [row], classifyWeldingRow)
      } else {
        const uid = getWeldingPersistOperatorUserId(day, act.machineId)
        card.operatorName = operatorNameById(uid, operators.value)
      }
      if (sess) {
        card.elapsedSec = weldingElapsedFromPersist(sess, tickNow.value)
        if (nextStatus === 'paused' && row) {
          card.pausedSec = pausedSecondsForRow(row, tickNow.value, sess)
        }
        if (nextStatus === 'break' && row) {
          card.breakSec = breakSecondsForInspectionRow(row, tickNow.value, weldBreakPersist.get(act.planId))
        }
      }
    }

    const total = rows.length
    const completed = rows.filter((r) => classifyWeldingRow(r) === 'completed').length
    const inProgress = rows.filter((r) => classifyWeldingRow(r) === 'running').length
    const paused = rows.filter((r) => classifyWeldingRow(r) === 'paused').length
    const onBreak = rows.filter((r) => classifyWeldingRow(r) === 'break').length
    const waiting = rows.filter((r) => classifyWeldingRow(r) === 'waiting').length

    const inspectorEfficiencyRows = buildInspectionInspectorEfficiencyRows(
      rows,
      operators.value,
      tickNow.value,
    )

    const sortedMachines = machines.sort((a, b) => a.name.localeCompare(b.name, 'ja'))

    return {
      key: 'welding',
      label: config.label,
      icon: config.icon,
      color: config.color,
      gradient: config.gradient,
      totalPlans: total,
      completedPlans: completed,
      inProgressPlans: inProgress,
      pausedPlans: paused,
      breakPlans: onBreak,
      waitingPlans: waiting,
      totalQty: 0,
      actualQty: rows.reduce((s, r) => s + (r.actual_production_quantity ?? 0), 0),
      defectQty: rows.reduce((s, r) => s + (r.defect_qty ?? 0), 0),
      machines: sortedMachines,
      historyRows: buildHistoryRows(
        rows,
        operators.value,
        tickNow.value,
        (r) => weldingMachineLabel(r as WeldingManagementListRow) || '—',
      ),
      defectListRows: buildMonitorDefectListRows(
        rows,
        operators.value,
        defectItems.value,
        defectItemLabel,
        classifyWeldingRow,
        (r) => weldingMachineLabel(r as WeldingManagementListRow) || '—',
      ),
      inspectorEfficiencyRows,
      inspectorAvgEfficiency: cachedKpiAvgEfficiency.value,
      commStalePlans: sortedMachines.filter((m) => m.commStale).length,
    }
  }

  const processSummary = computed<ProcessSummary>(() => {
    void tickNow.value
    return processKey === 'inspection' ? buildInspectionSummary() : buildWeldingSummary()
  })

  const overallStats = computed(() => {
    const proc = processSummary.value
    const runningMachines = proc.machines.filter((m) => m.status === 'running').length
    const avgEfficiency =
      isModernMonitorProcess(processKey) ? cachedKpiAvgEfficiency.value : null
    return {
      totalRunning: proc.inProgressPlans,
      totalPaused: proc.pausedPlans,
      totalBreak: proc.breakPlans,
      totalCompleted: proc.completedPlans,
      totalWaiting: proc.waitingPlans,
      totalPlans: proc.totalPlans,
      totalActual: proc.actualQty,
      totalDefect: proc.defectQty,
      avgEfficiency,
      runningMachines,
      totalMachines: proc.machines.length,
      defectRatePercent:
        proc.actualQty > 0 ? Math.round((proc.defectQty / proc.actualQty) * 1000) / 10 : null,
      totalCommStale: isModernMonitorProcess(processKey)
        ? proc.machines.filter((m) => m.commStale).length
        : 0,
      completionRate:
        proc.totalPlans > 0 ? Math.round((proc.completedPlans / proc.totalPlans) * 100) : 0,
    }
  })

  const currentTime = computed(() =>
    formatDateTimeJST(new Date(tickNow.value), intlLocale.value, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
  )

  const lastUpdatedLabel = computed(() => {
    if (lastUpdatedAt.value == null) return ''
    return formatDateTimeJST(new Date(lastUpdatedAt.value), intlLocale.value, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  })

  async function loadOperators(force = false): Promise<void> {
    if (operatorsLoaded && !force) return
    try {
      const usersRes = await getUsers({ page: 1, page_size: 500, status: 'active' })
      const userPayload = usersRes as unknown as PaginatedUserResponse
      operators.value = userPayload?.items ?? []
      operatorsLoaded = true
    } catch (e) {
      console.error(e)
      if (!operatorsLoaded) {
        try {
          const list = await fetchInspectionShiageSectionInspectors()
          operators.value = list.map((u) => ({
            id: u.id,
            username: u.username,
            full_name: u.full_name,
          })) as UserListItem[]
          operatorsLoaded = operators.value.length > 0
        } catch {
          operators.value = []
        }
      }
    }
  }

  function syncOperatorsFromInspectionRows(rows: InspectionManagementListRow[]): void {
    const fromRows = mergeOperatorsFromInspectionRows(rows)
    if (fromRows.length === 0) return
    operators.value = mergeOperatorLists(operators.value, fromRows)
  }

  async function fetchAll() {
    if (isModernMonitorProcess(processKey) && !pageVisible.value) return

    const seq = ++fetchSeq
    loading.value = true
    try {
      const day = productionDay.value
      await loadOperators()

      if (seq !== fetchSeq) return

      if (processKey === 'inspection') {
        if (defectItems.value.length === 0) {
          try {
            defectItems.value = await loadMesDefectItemsForProcess(
              INSPECTION_DEFECT_DETECTION_PROCESS_CD,
            )
          } catch {
            defectItems.value = []
          }
        }
        if (seq !== fetchSeq) return

        const insRes = await fetchInspectionMonitorSummary({ production_day: day, limit: 2000 })
        if (seq !== fetchSeq) return

        const nextRes = await fetchInspectionNextAssignments({ production_day: day }).catch(() => ({
          success: false,
          data: [] as InspectionNextAssignment[],
        }))
        if (seq !== fetchSeq) return

        inspectionRows.value = insRes.data ?? []
        nextAssignments.value = nextRes.data ?? []
        syncOperatorsFromInspectionRows(inspectionRows.value)
        lastFetchError.value = null
        const fetchedAt = insRes.fetched_at ? Date.parse(insRes.fetched_at) : NaN
        lastUpdatedAt.value = Number.isFinite(fetchedAt) ? fetchedAt : Date.now()
        refreshKpiEfficiencyCache()
        return
      }

      if (weldingMachines.value.length === 0) {
        try {
          weldingMachines.value = await fetchWeldingMesMachines()
        } catch {
          weldingMachines.value = []
        }
      }
      if (seq !== fetchSeq) return

      if (defectItems.value.length === 0) {
        try {
          defectItems.value = await loadMesDefectItemsForProcess(WELDING_DEFECT_DETECTION_PROCESS_CD)
        } catch {
          defectItems.value = []
        }
      }
      if (seq !== fetchSeq) return

      const weldRes = await fetchWeldingMonitorSummary({ production_day: day, limit: 2000 })
      if (seq !== fetchSeq) return

      weldingRows.value = weldRes.data ?? []
      lastFetchError.value = null
      const fetchedAt = weldRes.fetched_at ? Date.parse(weldRes.fetched_at) : NaN
      lastUpdatedAt.value = Number.isFinite(fetchedAt) ? fetchedAt : Date.now()
      refreshKpiEfficiencyCache()
    } catch (e: unknown) {
      if (seq !== fetchSeq) return
      console.error(e)
      notifyFetchError(extractFetchErrorMessage(e, config.pageTitle))
    } finally {
      if (seq === fetchSeq) loading.value = false
    }
  }

  function scheduleRefreshTick() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
    if (!autoRefresh.value || (isModernMonitorProcess(processKey) && !pageVisible.value)) return
    refreshTimer = setInterval(() => {
      if (autoRefresh.value && (!isModernMonitorProcess(processKey) || pageVisible.value)) {
        void fetchAll()
      }
    }, refreshIntervalMs)
  }

  function onFullscreenChange() {
    if (typeof document === 'undefined') return
    if (!document.fullscreenElement && fullscreen.value) {
      fullscreen.value = false
      document.body.classList.remove('monitor-body--fullscreen')
    }
  }

  function onVisibilityChange() {
    pageVisible.value = !document.hidden
    if (!isModernMonitorProcess(processKey)) return
    if (pageVisible.value) {
      void fetchAll()
      scheduleRefreshTick()
    } else if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  function startTimers() {
    tickTimer = setInterval(() => {
      tickNow.value = Date.now()
    }, TICK_MS)
    scheduleRefreshTick()
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', onVisibilityChange)
      document.addEventListener('fullscreenchange', onFullscreenChange)
    }
  }

  function stopTimers() {
    if (tickTimer) {
      clearInterval(tickTimer)
      tickTimer = null
    }
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', onVisibilityChange)
      document.removeEventListener('fullscreenchange', onFullscreenChange)
    }
  }

  onMounted(() => {
    void fetchAll()
    startTimers()
  })

  onUnmounted(() => {
    stopTimers()
    if (fullscreen.value && typeof document !== 'undefined') {
      document.body.classList.remove('monitor-body--fullscreen')
    }
  })

  function onDateChange() {
    if (isModernMonitorProcess(processKey)) {
      cachedKpiAvgEfficiency.value = null
    }
    void fetchAll()
  }

  function onAutoRefreshChange() {
    scheduleRefreshTick()
  }

  async function toggleFullscreen() {
    fullscreen.value = !fullscreen.value
    if (typeof document === 'undefined') return
    document.body.classList.toggle('monitor-body--fullscreen', fullscreen.value)
    if (fullscreen.value) {
      try {
        await document.documentElement.requestFullscreen()
      } catch {
        /* ユーザージェスチャなし等 */
      }
    } else if (document.fullscreenElement) {
      try {
        await document.exitFullscreen()
      } catch {
        /* ignore */
      }
    }
  }

  function goToInspectionRegistration() {
    void router.push({
      name: 'MesInspectionActualCollectionRegistration',
      query: { production_day: productionDay.value },
    })
  }

  function goToWeldingRegistration() {
    void router.push({
      name: 'MesWeldingActualCollectionRegistration',
      query: { production_day: productionDay.value },
    })
  }

  function goToActualRegistration() {
    if (processKey === 'inspection') {
      goToInspectionRegistration()
      return
    }
    goToWeldingRegistration()
  }

  async function loadMonitorProducts(): Promise<void> {
    if (monitorProducts.value.length > 0 || loadingMonitorProducts.value) return
    loadingMonitorProducts.value = true
    try {
      const res = await getProductList({ pageSize: 9999, status: 'active' })
      const list = res?.data?.list ?? res?.list ?? []
      monitorProducts.value = filterInspectionProductOptions(
        list.map((p) => ({
          product_code: (p.product_cd ?? '').trim(),
          product_name: (p.product_name ?? '').trim(),
          is_active: (p.status || '').toLowerCase() === 'active',
        })),
      )
    } catch {
      monitorProducts.value = []
    } finally {
      loadingMonitorProducts.value = false
    }
  }

  function canAssignNextProduct(machine: MachineStatus): boolean {
    return (
      processKey === 'inspection' &&
      machine.inspectorUserId != null &&
      (machine.status === 'running' || machine.status === 'paused' || machine.status === 'break')
    )
  }

  const nextAssignPanelVisible = ref(false)

  const nextAssignPanelRows = computed<NextAssignPanelRow[]>(() => {
    if (processKey !== 'inspection') return []
    const activeInspectorIds = new Set<number>()
    const rows: NextAssignPanelRow[] = []

    for (const machine of processSummary.value.machines) {
      if (
        machine.status !== 'running' &&
        machine.status !== 'paused' &&
        machine.status !== 'break'
      ) {
        continue
      }
      const inspectorUserId = machine.inspectorUserId
      if (inspectorUserId == null) continue
      activeInspectorIds.add(inspectorUserId)
      rows.push({
        key: `active-${inspectorUserId}`,
        inspectorUserId,
        inspectorName: machine.operatorName || String(inspectorUserId),
        currentProductLabel: machine.name,
        status: machine.status,
        nextProductCd: machine.nextProductCd,
        nextProductName: machine.nextProductName,
        elapsedSec: machine.elapsedSec,
        pausedSec: machine.pausedSec,
        breakSec: machine.breakSec,
        commStale: machine.commStale,
        isFirstProduct: false,
      })
    }

    for (const na of nextAssignments.value) {
      const uid = na.inspector_user_id
      if (uid == null || activeInspectorIds.has(Number(uid))) continue
      const fromList = inspectionInspectorOptions.value.find((o) => o.id === Number(uid))
      const inspectorName =
        (na.inspector_name ?? '').trim() ||
        (fromList?.full_name ?? '').trim() ||
        (fromList?.username ?? '').trim() ||
        String(uid)
      rows.push({
        key: `idle-${uid}`,
        inspectorUserId: Number(uid),
        inspectorName,
        currentProductLabel: '—',
        status: 'idle',
        nextProductCd: na.next_product_cd,
        nextProductName: na.next_product_name,
        isFirstProduct: true,
      })
    }

    rows.sort((a, b) => {
      if (a.isFirstProduct !== b.isFirstProduct) return a.isFirstProduct ? 1 : -1
      return a.inspectorName.localeCompare(b.inspectorName, 'ja')
    })
    return rows
  })

  const nextAssignPanelActiveRows = computed(() =>
    nextAssignPanelRows.value.filter((r) => !r.isFirstProduct),
  )

  const nextAssignPanelIdleRows = computed(() =>
    nextAssignPanelRows.value.filter((r) => r.isFirstProduct),
  )

  const nextAssignPanelBadgeCount = computed(() => nextAssignments.value.length)

  async function loadInspectionInspectorOptions(): Promise<void> {
    if (processKey !== 'inspection') return
    loadingInspectionInspectors.value = true
    try {
      inspectionInspectorOptions.value = await fetchInspectionShiageSectionInspectors()
    } catch {
      inspectionInspectorOptions.value = []
    } finally {
      loadingInspectionInspectors.value = false
    }
  }

  function openNextAssignPanel(): void {
    if (processKey !== 'inspection') return
    void loadInspectionInspectorOptions()
    nextAssignPanelVisible.value = true
  }

  function closeNextAssignPanel(): void {
    nextAssignPanelVisible.value = false
  }

  function resolveNextAssignInspectorUserId(): number | null {
    if (nextAssignPickInspector.value) {
      const uid = nextAssignInspectorUserId.value
      return uid != null && uid > 0 ? uid : null
    }
    return nextAssignTarget.value?.inspectorUserId ?? null
  }

  async function openNextAssignDialogForRow(row: NextAssignPanelRow): Promise<void> {
    await loadMonitorProducts()
    nextAssignPickInspector.value = false
    nextAssignInspectorUserId.value = row.inspectorUserId
    nextAssignTarget.value = {
      inspectorUserId: row.inspectorUserId,
      inspectorName: row.inspectorName,
      currentProductLabel: row.currentProductLabel,
      isFirstProduct: row.isFirstProduct,
    }
    const existing = nextAssignmentByInspectorId(row.inspectorUserId)
    nextAssignProductCd.value = (existing?.next_product_cd ?? '').trim()
    nextAssignDialogVisible.value = true
  }

  async function openNextAssignCreateDialog(): Promise<void> {
    await Promise.all([loadMonitorProducts(), loadInspectionInspectorOptions()])
    nextAssignPickInspector.value = true
    nextAssignInspectorUserId.value = null
    nextAssignTarget.value = {
      inspectorUserId: 0,
      inspectorName: '',
      currentProductLabel: '—',
      isFirstProduct: true,
    }
    nextAssignProductCd.value = ''
    nextAssignDialogVisible.value = true
  }

  async function openNextAssignDialog(machine: MachineStatus): Promise<void> {
    if (!canAssignNextProduct(machine)) return
    const inspectorUserId = machine.inspectorUserId
    if (inspectorUserId == null) return
    await openNextAssignDialogForRow({
      key: `active-${inspectorUserId}`,
      inspectorUserId,
      inspectorName: machine.operatorName || String(inspectorUserId),
      currentProductLabel: machine.name,
      status: machine.status as 'running' | 'paused' | 'break',
      nextProductCd: machine.nextProductCd,
      nextProductName: machine.nextProductName,
      elapsedSec: machine.elapsedSec,
      pausedSec: machine.pausedSec,
      breakSec: machine.breakSec,
      commStale: machine.commStale,
      isFirstProduct: false,
    })
  }

  function closeNextAssignDialog(): void {
    nextAssignDialogVisible.value = false
    nextAssignTarget.value = null
    nextAssignProductCd.value = ''
    nextAssignPickInspector.value = false
    nextAssignInspectorUserId.value = null
  }

  async function saveNextAssignment(): Promise<void> {
    const inspectorUserId = resolveNextAssignInspectorUserId()
    const cd = nextAssignProductCd.value.trim()
    if (inspectorUserId == null) {
      ElMessage.warning(
        nextAssignPickInspector.value ? '検査員を選択してください' : '検査員が不正です',
      )
      return
    }
    if (!cd) {
      ElMessage.warning('次製品を選択してください')
      return
    }
    const product = monitorProducts.value.find((p) => p.product_code === cd)
    if (!product) {
      ElMessage.warning('検査対象外の製品です')
      return
    }
    nextAssignSubmitting.value = true
    try {
      const res = await upsertInspectionNextAssignment({
        production_day: productionDay.value,
        inspector_user_id: inspectorUserId,
        product_cd: cd,
        product_name: product.product_name,
        note: null,
      })
      if (!res.success) {
        ElMessage.error(res.message || '次製品の指定に失敗しました')
        return
      }
      ElMessage.success(res.message || '次製品を指定しました')
      closeNextAssignDialog()
      await fetchAll()
    } catch (e: unknown) {
      ElMessage.error(extractFetchErrorMessage(e, config.pageTitle))
    } finally {
      nextAssignSubmitting.value = false
    }
  }

  async function clearNextAssignment(): Promise<void> {
    const inspectorUserId = resolveNextAssignInspectorUserId()
    if (inspectorUserId == null) return
    nextAssignSubmitting.value = true
    try {
      const res = await deleteInspectionNextAssignment({
        production_day: productionDay.value,
        inspector_user_id: inspectorUserId,
      })
      if (!res.success) {
        ElMessage.error(res.message || '解除に失敗しました')
        return
      }
      ElMessage.success(res.message || '次製品指定を解除しました')
      closeNextAssignDialog()
      await fetchAll()
    } catch (e: unknown) {
      ElMessage.error(extractFetchErrorMessage(e, config.pageTitle))
    } finally {
      nextAssignSubmitting.value = false
    }
  }

  const abandoningPlanId = ref<number | null>(null)

  function canAbandonInProgressSession(machine: MachineStatus): boolean {
    if (machine.id == null) return false
    return machine.status === 'running' || machine.status === 'paused' || machine.status === 'break'
  }

  /** 稼働中／一時停止／休憩／通信断の未完了セッションを無効化（確定実績には残さない） */
  async function abandonInProgressSession(machine: MachineStatus): Promise<void> {
    if (!canAbandonInProgressSession(machine) || machine.id == null) return
    const statusText = machine.commStale
      ? '通信断'
      : machine.status === 'paused'
        ? '一時停止'
        : machine.status === 'break'
          ? '休憩中'
          : '稼働中'
    try {
      await ElMessageBox.confirm(
        `「${machine.name}」の${statusText}セッションを無効化しますか？\n未完了のままクリアされ、確定実績には残りません。`,
        'セッションの無効化',
        {
          type: 'warning',
          confirmButtonText: '無効化',
          cancelButtonText: 'キャンセル',
        },
      )
    } catch {
      return
    }
    abandoningPlanId.value = machine.id
    try {
      const body = {
        mes_force_release: true,
        mes_abandon_in_progress: true,
      }
      const res =
        processKey === 'welding'
          ? await patchWeldingManagement(machine.id, body)
          : await patchInspectionManagement(machine.id, body)
      if (!res.success) {
        ElMessage.error(res.message || '無効化に失敗しました')
        return
      }
      ElMessage.success(res.message || 'セッションを無効化しました')
      await fetchAll()
    } catch (e: unknown) {
      ElMessage.error(extractFetchErrorMessage(e, config.pageTitle))
    } finally {
      abandoningPlanId.value = null
    }
  }

  function hasNextAssignmentForInspector(inspectorUserId: number | null | undefined): boolean {
    return nextAssignmentByInspectorId(inspectorUserId) != null
  }

  watch(nextAssignInspectorUserId, (uid) => {
    if (!nextAssignPickInspector.value || uid == null || uid <= 0) return
    const existing = nextAssignmentByInspectorId(uid)
    nextAssignProductCd.value = (existing?.next_product_cd ?? '').trim()
  })

  const hasInitialData = computed(() =>
    processKey === 'inspection' ? inspectionRows.value.length > 0 : weldingRows.value.length > 0,
  )

  return {
    config,
    intlLocale,
    productionDay,
    loading,
    autoRefresh,
    processSummary,
    overallStats,
    currentTime,
    lastUpdatedAt,
    lastUpdatedLabel,
    lastFetchError,
    cachedKpiAvgEfficiency,
    fullscreen,
    fetchAll,
    onDateChange,
    onAutoRefreshChange,
    toggleFullscreen,
    goToInspectionRegistration,
    goToWeldingRegistration,
    goToActualRegistration,
    hasInitialData,
    nextAssignDialogVisible,
    nextAssignSubmitting,
    nextAssignTarget,
    nextAssignProductCd,
    monitorProducts,
    loadingMonitorProducts,
    canAssignNextProduct,
    nextAssignPanelVisible,
    nextAssignPanelRows,
    nextAssignPanelActiveRows,
    nextAssignPanelIdleRows,
    nextAssignPanelBadgeCount,
    inspectionInspectorOptions,
    loadingInspectionInspectors,
    nextAssignPickInspector,
    nextAssignInspectorUserId,
    openNextAssignPanel,
    closeNextAssignPanel,
    openNextAssignDialogForRow,
    openNextAssignCreateDialog,
    openNextAssignDialog,
    closeNextAssignDialog,
    saveNextAssignment,
    clearNextAssignment,
    abandonInProgressSession,
    canAbandonInProgressSession,
    abandoningPlanId,
    hasNextAssignmentForInspector,
  }
}
