<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Monitor,
  Refresh,
  VideoPlay,
  VideoPause,
  CircleCheck,
  WarningFilled,
  Timer,
  DataLine,
  User,
} from '@element-plus/icons-vue'
import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import { fetchCuttingManagementList, type CuttingManagementListRow } from '@/api/cuttingManagement'
import {
  fetchCuttingPlanningMachines,
  type CuttingPlanningMachine,
} from '@/api/cuttingPlanning'
import {
  fetchInspectionManagementList,
  type InspectionManagementListRow,
} from '@/api/inspectionManagement'
import {
  fetchWeldingManagementList,
  type WeldingManagementListRow,
} from '@/api/weldingManagement'
import { fetchWeldingMesMachines, type WeldingMesMachine } from '@/api/weldingMesEquipment'
import {
  collectWeldingPersistForMonitorDay,
  getWeldingPersistOperatorUserId,
  readPausedAccumMs,
  type PersistedPlanSession,
} from '@/views/mes/actualDataCollection/welding/weldingActualPersist'
import { formatDateTimeJST, getJSTToday, localeForIntl, parseDateAsJST } from '@/utils/dateFormat'

defineOptions({ name: 'ProductionMonitorDashboard' })

const { locale, t } = useI18n()
const intlLocale = computed(() => localeForIntl(locale.value as string))

const productionDay = ref(getJSTToday())
const loading = ref(false)
const autoRefresh = ref(true)
const tickNow = ref(Date.now())
let tickTimer: ReturnType<typeof setInterval> | null = null
let refreshTimer: ReturnType<typeof setInterval> | null = null
const AUTO_REFRESH_MS = 8000

const cuttingRows = ref<CuttingManagementListRow[]>([])
const cuttingMachines = ref<CuttingPlanningMachine[]>([])
const inspectionRows = ref<InspectionManagementListRow[]>([])
const weldingRows = ref<WeldingManagementListRow[]>([])
const weldingMachines = ref<WeldingMesMachine[]>([])
const operators = ref<UserListItem[]>([])

interface ProcessSummary {
  key: string
  label: string
  icon: string
  color: string
  gradient: string
  totalPlans: number
  completedPlans: number
  inProgressPlans: number
  pausedPlans: number
  waitingPlans: number
  totalQty: number
  actualQty: number
  defectQty: number
  machines: MachineStatus[]
  historyRows: ActualHistoryRow[]
}

interface ActualHistoryRow {
  id: number
  operatorName: string
  machineName: string
  productName: string
  actualQty: number
  defectQty: number
  startedAt: string | null
  endedAt: string | null
  elapsedSec: number
}

interface MachineStatus {
  /** 一覧 v-for 用（検査など複数カード） */
  id?: number
  name: string
  status: 'running' | 'paused' | 'idle' | 'completed'
  currentProduct: string
  currentProductCd: string
  progress: number
  totalPlans: number
  completedPlans: number
  elapsedSec: number
  actualQty: number
  plannedQty: number
  operatorName: string
  /** 一時停止累計（秒）。status=paused のとき表示 */
  pausedSec: number
}

type MesRowLike = {
  mes_production_started_at?: string | null
  mes_production_ended_at?: string | null
  mes_net_production_sec?: number | null
  mes_production_is_paused?: number | null
  production_completed_check?: number | null
}

type MesRowWithOperator = MesRowLike & {
  id?: number
  mes_operator_user_id?: number | null
  mes_inspector_user_id?: number | null
  mes_paused_accum_sec?: number | null
}

function operatorUserIdFromRow(row: MesRowWithOperator): number | null {
  const op = row.mes_operator_user_id
  if (op != null && Number.isFinite(Number(op)) && Number(op) > 0) return Number(op)
  const insp = row.mes_inspector_user_id
  if (insp != null && Number.isFinite(Number(insp)) && Number(insp) > 0) return Number(insp)
  return null
}

function operatorNameById(userId: number | null | undefined): string {
  if (userId == null) return ''
  const u = operators.value.find((x) => x.id === userId)
  return (u?.full_name || u?.username || '').trim()
}

function operatorNameForRow(row: MesRowWithOperator | null | undefined): string {
  if (!row) return ''
  return operatorNameById(operatorUserIdFromRow(row))
}

/** 溶接実績収集の isRowMesProductionActive と同じ判定 */
function isRowMesActive(row: MesRowLike): boolean {
  if (Number(row.production_completed_check ?? 0) === 1) return false
  const started = row.mes_production_started_at
  if (started == null || !String(started).trim()) return false
  const ended = row.mes_production_ended_at
  return ended == null || !String(ended).trim()
}

function classifyRow(row: MesRowLike): 'completed' | 'running' | 'paused' | 'waiting' {
  if (Number(row.production_completed_check ?? 0) === 1) return 'completed'
  if (isRowMesActive(row)) {
    return Number(row.mes_production_is_paused ?? 0) === 1 ? 'paused' : 'running'
  }
  const ended = row.mes_production_ended_at
  if (ended != null && String(ended).trim()) return 'completed'
  return 'waiting'
}

type RowClassifier = (row: MesRowLike) => 'completed' | 'running' | 'paused' | 'waiting'

function pausedSecondsForRow(
  row: MesRowWithOperator,
  persistSess?: PersistedPlanSession | null,
): number {
  if (persistSess) {
    return Math.max(0, Math.round(readPausedAccumMs(persistSess, tickNow.value) / 1000))
  }
  const raw = row.mes_paused_accum_sec
  if (raw != null && Number.isFinite(Number(raw))) {
    return Math.max(0, Math.round(Number(raw)))
  }
  return 0
}

function buildMachineStatus(
  name: string,
  mRows: Array<{
    product_cd?: string | null
    product_name?: string | null
    actual_production_quantity?: number | null
    planned_quantity?: number | null
  } & MesRowWithOperator>,
  classify: RowClassifier = classifyRow,
  persistSessionsByPlanId?: Map<number, PersistedPlanSession>,
): MachineStatus {
  void tickNow.value
  const running = mRows.find((r) => classify(r) === 'running')
  const pausedRow = mRows.find((r) => classify(r) === 'paused')
  const active = running || pausedRow
  const completed = mRows.filter((r) => classify(r) === 'completed').length
  const operatorName =
    active && (running || pausedRow) ? operatorNameForRow(active) : ''
  const status: MachineStatus['status'] = running ? 'running' : pausedRow ? 'paused' : 'idle'
  let pausedSec = 0
  if (status === 'paused' && pausedRow) {
    const sess =
      pausedRow.id != null && persistSessionsByPlanId
        ? persistSessionsByPlanId.get(pausedRow.id)
        : undefined
    pausedSec = pausedSecondsForRow(pausedRow, sess)
  }
  return {
    name,
    status,
    currentProduct: active?.product_name || '',
    currentProductCd: active?.product_cd || '',
    progress: mRows.length > 0 ? Math.round((completed / mRows.length) * 100) : 0,
    totalPlans: mRows.length,
    completedPlans: completed,
    elapsedSec: active ? elapsedSeconds(active) : 0,
    actualQty: mRows.reduce((s, r) => s + (r.actual_production_quantity ?? 0), 0),
    plannedQty: mRows.reduce((s, r) => s + (r.planned_quantity ?? 0), 0),
    operatorName,
    pausedSec,
  }
}

function weldingMachineLabel(row: WeldingManagementListRow): string {
  return (row.welding_machine ?? '').trim()
}

/** 設備名またはコードに「外注」を含む切断機はモニターから除外（実績収集画面と同様） */
function cuttingMachineHasGaichu(m: CuttingPlanningMachine): boolean {
  const name = m.machine_name ?? ''
  const cd = m.machine_cd ?? ''
  return name.includes('外注') || cd.includes('外注')
}

function cuttingMachineNameHasGaichu(name: string): boolean {
  return String(name).includes('外注')
}

function isRowProductionCompleted(row: MesRowLike): boolean {
  return Number(row.production_completed_check ?? 0) === 1
}

type HistorySourceRow = MesRowWithOperator & {
  product_name?: string | null
  actual_production_quantity?: number | null
  defect_qty?: number | null
  cutting_machine?: string | null
  welding_machine?: string | null
}

function historyElapsedSec(row: MesRowLike): number {
  const net = row.mes_net_production_sec
  if (typeof net === 'number' && net >= 0) return net
  return elapsedSeconds(row)
}

function buildHistoryRows(
  rows: HistorySourceRow[],
  machineLabel: (row: HistorySourceRow) => string,
): ActualHistoryRow[] {
  return rows
    .filter(isRowProductionCompleted)
    .sort((a, b) => {
      const tb = parseDateAsJST(b.mes_production_ended_at)?.getTime() ?? 0
      const ta = parseDateAsJST(a.mes_production_ended_at)?.getTime() ?? 0
      if (tb !== ta) return tb - ta
      return (b.id ?? 0) - (a.id ?? 0)
    })
    .map((row) => ({
      id: row.id ?? 0,
      operatorName: operatorNameForRow(row) || '—',
      machineName: machineLabel(row) || '—',
      productName: (row.product_name ?? '').trim() || '—',
      actualQty: row.actual_production_quantity ?? 0,
      defectQty: row.defect_qty ?? 0,
      startedAt: row.mes_production_started_at ?? null,
      endedAt: row.mes_production_ended_at ?? null,
      elapsedSec: historyElapsedSec(row),
    }))
}

function processHistoryTitle(procKey: string): string {
  if (procKey === 'welding') return t('mesWeldingActual.historyTitle')
  if (procKey === 'inspection') return t('mesInspectionActual.historyTitle')
  return t('mesWeldingActual.historyTitle')
}

function historyProductionQtyTotal(rows: ActualHistoryRow[]): number {
  return rows.reduce((sum, row) => sum + (row.actualQty ?? 0), 0)
}

function historyCardTitle(procKey: string, row: ActualHistoryRow): string {
  if (procKey === 'inspection') return row.productName
  const machine = row.machineName.trim()
  if (machine && machine !== '—') return `${machine} · ${row.productName}`
  return row.productName
}

/** 稼働中は壁時計（tickNow）で毎秒更新。終了後は DB の净稼働秒を優先 */
function elapsedSeconds(row: {
  mes_net_production_sec?: number | null
  mes_production_started_at?: string | null
  mes_production_ended_at?: string | null
}): number {
  const startedRaw = row.mes_production_started_at
  const startDate =
    startedRaw != null && String(startedRaw).trim() ? parseDateAsJST(startedRaw) : null
  if (!startDate) {
    const net = row.mes_net_production_sec
    return typeof net === 'number' && net > 0 ? net : 0
  }
  const start = startDate.getTime()
  const endedRaw = row.mes_production_ended_at
  const hasEnded = endedRaw != null && String(endedRaw).trim() !== ''
  if (!hasEnded) {
    return Math.max(0, Math.round((tickNow.value - start) / 1000))
  }
  const net = row.mes_net_production_sec
  if (typeof net === 'number' && net >= 0) return net
  const endDate = parseDateAsJST(endedRaw)
  if (!endDate) return 0
  return Math.max(0, Math.round((endDate.getTime() - start) / 1000))
}

function buildCuttingSummary(): ProcessSummary {
  void tickNow.value
  const rows = cuttingRows.value.filter(
    (r) => !cuttingMachineNameHasGaichu((r.cutting_machine ?? '').trim() || '未割当'),
  )
  const machineMap = new Map<string, CuttingManagementListRow[]>()
  for (const r of rows) {
    const m = r.cutting_machine || '未割当'
    if (!machineMap.has(m)) machineMap.set(m, [])
    machineMap.get(m)!.push(r)
  }

  const knownNames = new Set<string>()
  for (const m of cuttingMachines.value) {
    if (cuttingMachineHasGaichu(m)) continue
    const label = (m.machine_name ?? '').trim()
    if (label) knownNames.add(label)
  }

  const machines: MachineStatus[] = []
  for (const name of [...knownNames].sort((a, b) => a.localeCompare(b, 'ja'))) {
    const mRows = rows.filter((r) => (r.cutting_machine ?? '').trim() === name)
    machines.push(buildMachineStatus(name, mRows))
  }
  for (const [name, mRows] of machineMap) {
    if (knownNames.has(name) || cuttingMachineNameHasGaichu(name)) continue
    machines.push(buildMachineStatus(name, mRows))
  }

  const total = rows.length
  const completed = rows.filter((r) => classifyRow(r) === 'completed').length
  const inProgress = rows.filter((r) => classifyRow(r) === 'running').length
  const paused = rows.filter((r) => classifyRow(r) === 'paused').length

  return {
    key: 'cutting',
    label: '切断工程',
    icon: '✂',
    color: '#409eff',
    gradient: 'linear-gradient(135deg, #409eff 0%, #53a8ff 100%)',
    totalPlans: total,
    completedPlans: completed,
    inProgressPlans: inProgress,
    pausedPlans: paused,
    waitingPlans: total - completed - inProgress - paused,
    totalQty: rows.reduce((s, r) => s + (r.planned_quantity ?? 0), 0),
    actualQty: rows.reduce((s, r) => s + (r.actual_production_quantity ?? 0), 0),
    defectQty: rows.reduce((s, r) => s + (r.defect_qty ?? 0), 0),
    machines: machines.sort((a, b) => a.name.localeCompare(b.name, 'ja')),
    historyRows: buildHistoryRows(rows, (r) => (r.cutting_machine ?? '').trim() || '—'),
  }
}

function weldingElapsedFromPersist(sess: PersistedPlanSession): number {
  if (sess.wallStart == null) return 0
  const end = sess.wallEnd ?? tickNow.value
  return Math.max(0, Math.round((end - sess.wallStart) / 1000))
}

function buildWeldingSummary(): ProcessSummary {
  void tickNow.value
  const rows = weldingRows.value
  const day = (productionDay.value ?? '').trim()
  const { sessionsByPlanId, machineActivities } = collectWeldingPersistForMonitorDay(day)

  function classifyWeldingRow(row: WeldingManagementListRow): ReturnType<typeof classifyRow> {
    if (row.id != null) {
      const sess = sessionsByPlanId.get(row.id)
      if (sess?.wallStart != null && sess.wallEnd == null) {
        return sess.pauseSliceStart != null ? 'paused' : 'running'
      }
    }
    return classifyRow(row)
  }

  const knownNames = new Set<string>()
  for (const m of weldingMachines.value) {
    const label = (m.machine_name ?? '').trim()
    if (label) knownNames.add(label)
  }

  const machines: MachineStatus[] = []
  for (const name of [...knownNames].sort((a, b) => a.localeCompare(b, 'ja'))) {
    const mRows = rows.filter((r) => weldingMachineLabel(r) === name)
    machines.push(buildMachineStatus(name, mRows, classifyWeldingRow, sessionsByPlanId))
  }

  const unassigned = rows.filter((r) => !weldingMachineLabel(r))
  if (unassigned.length > 0) {
    machines.push(buildMachineStatus('未割当', unassigned, classifyWeldingRow, sessionsByPlanId))
  }

  for (const r of rows) {
    const label = weldingMachineLabel(r)
    if (!label || knownNames.has(label)) continue
    machines.push(
      buildMachineStatus(
        label,
        rows.filter((x) => weldingMachineLabel(x) === label),
        classifyWeldingRow,
        sessionsByPlanId,
      ),
    )
    knownNames.add(label)
  }

  for (const act of machineActivities) {
    const machineName = (weldingMachines.value.find((m) => m.id === act.machineId)?.machine_name ?? '').trim()
    if (!machineName) continue
    const row = rows.find((r) => r.id === act.planId)
    let card = machines.find((m) => m.name === machineName)
    if (!card) {
      card = buildMachineStatus(
        machineName,
        row ? [row] : [],
        classifyWeldingRow,
        sessionsByPlanId,
      )
      machines.push(card)
    }
    const nextStatus = act.paused ? 'paused' : 'running'
    if (card.status !== 'running' && card.status !== 'paused') {
      card.status = nextStatus
    }
    if (row) {
      card.currentProduct = row.product_name || ''
      card.currentProductCd = row.product_cd || ''
      card.operatorName = operatorNameForRow(row)
    } else {
      const uid = getWeldingPersistOperatorUserId(day, act.machineId)
      card.operatorName = operatorNameById(uid)
    }
    const sess = sessionsByPlanId.get(act.planId)
    if (sess) {
      card.elapsedSec = weldingElapsedFromPersist(sess)
      if (act.paused) {
        card.pausedSec = pausedSecondsForRow(row ?? {}, sess)
      }
    }
  }

  const total = rows.length
  const completed = rows.filter((r) => classifyWeldingRow(r) === 'completed').length
  const inProgress = rows.filter((r) => classifyWeldingRow(r) === 'running').length
  const paused = rows.filter((r) => classifyWeldingRow(r) === 'paused').length

  return {
    key: 'welding',
    label: '溶接工程',
    icon: '⚡',
    color: '#e6a23c',
    gradient: 'linear-gradient(135deg, #e6a23c 0%, #f0c060 100%)',
    totalPlans: total,
    completedPlans: completed,
    inProgressPlans: inProgress,
    pausedPlans: paused,
    waitingPlans: total - completed - inProgress - paused,
    totalQty: 0,
    actualQty: rows.reduce((s, r) => s + (r.actual_production_quantity ?? 0), 0),
    defectQty: rows.reduce((s, r) => s + (r.defect_qty ?? 0), 0),
    machines: machines.sort((a, b) => a.name.localeCompare(b.name, 'ja')),
    historyRows: buildHistoryRows(rows, (r) => weldingMachineLabel(r as WeldingManagementListRow) || '—'),
  }
}

function inspectionCardName(row: InspectionManagementListRow): string {
  const cd = (row.product_cd ?? '').trim()
  const name = (row.product_name ?? '').trim()
  if (cd && name) return `${cd} · ${name}`
  return cd || name || '検査ライン'
}

function buildInspectionSummary(): ProcessSummary {
  void tickNow.value
  const rows = inspectionRows.value
  const total = rows.length
  const completed = rows.filter((r) => classifyRow(r) === 'completed').length
  const inProgress = rows.filter((r) => classifyRow(r) === 'running').length
  const paused = rows.filter((r) => classifyRow(r) === 'paused').length

  const machines: MachineStatus[] = []
  for (const row of rows) {
    const rowStatus = classifyRow(row)
    if (rowStatus !== 'running' && rowStatus !== 'paused') continue
    const card = buildMachineStatus(inspectionCardName(row), [row] as MesRowWithOperator[])
    if (row.id != null) card.id = row.id
    machines.push(card)
  }
  machines.sort((a, b) => a.name.localeCompare(b.name, 'ja'))

  return {
    key: 'inspection',
    label: '検査工程',
    icon: '🔍',
    color: '#67c23a',
    gradient: 'linear-gradient(135deg, #67c23a 0%, #85ce61 100%)',
    totalPlans: total,
    completedPlans: completed,
    inProgressPlans: inProgress,
    pausedPlans: paused,
    waitingPlans: total - completed - inProgress - paused,
    totalQty: 0,
    actualQty: rows.reduce((s, r) => s + (r.actual_production_quantity ?? 0), 0),
    defectQty: rows.reduce((s, r) => s + (r.defect_qty ?? 0), 0),
    machines,
    historyRows: buildHistoryRows(rows as HistorySourceRow[], () => '—'),
  }
}

const processes = computed<ProcessSummary[]>(() => {
  void tickNow.value
  return [buildCuttingSummary(), buildWeldingSummary(), buildInspectionSummary()]
})

const overallStats = computed(() => {
  const all = processes.value
  const totalRunning = all.reduce((s, p) => s + p.inProgressPlans, 0)
  const totalPaused = all.reduce((s, p) => s + p.pausedPlans, 0)
  const totalCompleted = all.reduce((s, p) => s + p.completedPlans, 0)
  const totalWaiting = all.reduce((s, p) => s + p.waitingPlans, 0)
  const totalPlans = all.reduce((s, p) => s + p.totalPlans, 0)
  const totalActual = all.reduce((s, p) => s + p.actualQty, 0)
  const totalDefect = all.reduce((s, p) => s + p.defectQty, 0)
  const runningMachines = all.reduce(
    (s, p) => s + p.machines.filter((m) => m.status === 'running').length,
    0,
  )
  const totalMachines = all.reduce((s, p) => s + p.machines.length, 0)
  return {
    totalRunning,
    totalPaused,
    totalCompleted,
    totalWaiting,
    totalPlans,
    totalActual,
    totalDefect,
    runningMachines,
    totalMachines,
    completionRate: totalPlans > 0 ? Math.round((totalCompleted / totalPlans) * 100) : 0,
  }
})

function formatHistoryTime(iso: string | null | undefined): string {
  if (iso == null || !String(iso).trim()) return '—'
  const text = formatDateTimeJST(iso, intlLocale.value, { second: undefined })
  return text || '—'
}

function formatDuration(sec: number): string {
  if (sec <= 0) return '--:--'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (h > 0) return `${h}h ${String(m).padStart(2, '0')}m`
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    running: '稼働中',
    paused: '一時停止',
    idle: '待機中',
    completed: '完了',
  }
  return map[status] ?? status
}

type ElTagType = 'primary' | 'success' | 'info' | 'warning' | 'danger'

function statusTagType(status: string): ElTagType {
  const map: Record<string, ElTagType> = {
    running: 'success',
    paused: 'warning',
    idle: 'info',
    completed: 'info',
  }
  return map[status] ?? 'info'
}

async function fetchWeldingRowsForDay(day: string): Promise<WeldingManagementListRow[]> {
  const base = await fetchWeldingManagementList({ production_day: day, limit: 2000 })
  const merged = new Map<number, WeldingManagementListRow>()
  for (const r of base.data ?? []) {
    if (r.id != null) merged.set(r.id, r)
  }
  const machines = weldingMachines.value
  if (machines.length === 0) return [...merged.values()]

  const perMachine = await Promise.allSettled(
    machines.map((m) =>
      fetchWeldingManagementList({
        production_day: day,
        welding_machine: m.machine_name,
        limit: 2000,
      }),
    ),
  )
  for (const res of perMachine) {
    if (res.status !== 'fulfilled') continue
    for (const r of res.value.data ?? []) {
      if (r.id != null) merged.set(r.id, r)
    }
  }
  return [...merged.values()]
}

async function fetchAll() {
  loading.value = true
  try {
    const day = productionDay.value
    if (weldingMachines.value.length === 0) {
      try {
        weldingMachines.value = await fetchWeldingMesMachines()
      } catch {
        weldingMachines.value = []
      }
    }
    if (cuttingMachines.value.length === 0) {
      try {
        const allCutting = await fetchCuttingPlanningMachines()
        cuttingMachines.value = allCutting.filter((m) => !cuttingMachineHasGaichu(m))
      } catch {
        cuttingMachines.value = []
      }
    }
    const [cutRes, insRes, weldRows, usersRes] = await Promise.all([
      fetchCuttingManagementList({ production_day: day, limit: 2000 }),
      fetchInspectionManagementList({ production_day: day, limit: 2000 }),
      fetchWeldingRowsForDay(day),
      getUsers({ page: 1, page_size: 500, status: 'active' }),
    ])
    cuttingRows.value = cutRes.data ?? []
    inspectionRows.value = insRes.data ?? []
    weldingRows.value = weldRows
    const userPayload = usersRes as unknown as PaginatedUserResponse
    operators.value = userPayload?.items ?? []
  } finally {
    loading.value = false
  }
}

function startTimers() {
  tickTimer = setInterval(() => { tickNow.value = Date.now() }, 1000)
  refreshTimer = setInterval(() => {
    if (autoRefresh.value) fetchAll()
  }, AUTO_REFRESH_MS)
}

function stopTimers() {
  if (tickTimer) { clearInterval(tickTimer); tickTimer = null }
  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
}

onMounted(() => {
  fetchAll()
  startTimers()
})

onUnmounted(() => {
  stopTimers()
})

function onDateChange() {
  fetchAll()
}

const currentTime = computed(() =>
  formatDateTimeJST(new Date(tickNow.value), intlLocale.value, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }),
)
</script>

<template>
  <div class="monitor-page" v-loading="loading && cuttingRows.length === 0">
    <!-- Header -->
    <div class="monitor-header">
      <div class="monitor-header__left">
        <el-icon :size="26" color="#409eff"><Monitor /></el-icon>
        <h1 class="monitor-header__title">生産モニター</h1>
        <span class="monitor-header__clock">{{ currentTime }}</span>
      </div>
      <div class="monitor-header__right">
        <el-date-picker
          v-model="productionDay"
          type="date"
          value-format="YYYY-MM-DD"
          size="small"
          style="width: 150px"
          @change="onDateChange"
        />
        <el-switch
          v-model="autoRefresh"
          active-text="自動更新"
          size="small"
          style="margin-left: 10px"
        />
        <el-button size="small" :icon="Refresh" circle @click="fetchAll" style="margin-left: 6px" />
      </div>
    </div>

    <!-- Overall KPI Cards -->
    <div class="kpi-row">
      <div class="kpi-card kpi-card--running">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--running">
          <el-icon :size="22"><VideoPlay /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.totalRunning }}</div>
          <div class="kpi-card__label">稼働中</div>
        </div>
      </div>
      <div class="kpi-card kpi-card--paused">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--paused">
          <el-icon :size="22"><VideoPause /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.totalPaused }}</div>
          <div class="kpi-card__label">一時停止</div>
        </div>
      </div>
      <div class="kpi-card kpi-card--completed">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--completed">
          <el-icon :size="22"><CircleCheck /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.totalCompleted }}</div>
          <div class="kpi-card__label">完了</div>
        </div>
      </div>
      <div class="kpi-card kpi-card--waiting">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--waiting">
          <el-icon :size="22"><Timer /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.totalWaiting }}</div>
          <div class="kpi-card__label">待機中</div>
        </div>
      </div>
      <div class="kpi-card kpi-card--machines">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--machines">
          <el-icon :size="22"><DataLine /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">
            {{ overallStats.runningMachines }}<span class="kpi-card__sub">/{{ overallStats.totalMachines }}</span>
          </div>
          <div class="kpi-card__label">設備稼働</div>
        </div>
      </div>
      <div class="kpi-card kpi-card--rate">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--rate">
          <el-icon :size="22"><DataLine /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.completionRate }}<span class="kpi-card__sub">%</span></div>
          <div class="kpi-card__label">完了率</div>
        </div>
      </div>
      <div class="kpi-card kpi-card--defect" v-if="overallStats.totalDefect > 0">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--defect">
          <el-icon :size="22"><WarningFilled /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.totalDefect }}</div>
          <div class="kpi-card__label">不良数</div>
        </div>
      </div>
    </div>

    <!-- Process Sections（上段：稼働 / 下段：確定実績・上端揃え） -->
    <div class="process-layout">
      <div class="process-runtime-row">
        <div
          v-for="proc in processes"
          :key="`${proc.key}-runtime`"
          class="process-section process-section--runtime"
        >
        <div class="process-section__header" :style="{ background: proc.gradient }">
          <span class="process-section__icon">{{ proc.icon }}</span>
          <span class="process-section__name">{{ proc.label }}</span>
          <div class="process-section__badges">
            <el-tag size="small" type="success" effect="dark" v-if="proc.inProgressPlans > 0" round>
              稼働 {{ proc.inProgressPlans }}
            </el-tag>
            <el-tag size="small" type="warning" effect="dark" v-if="proc.pausedPlans > 0" round>
              停止 {{ proc.pausedPlans }}
            </el-tag>
          </div>
        </div>

        <div class="machine-list" v-if="proc.machines.length > 0">
          <div
            v-for="machine in proc.machines"
            :key="machine.id != null ? `${proc.key}-${machine.id}` : machine.name"
            class="machine-card"
            :class="'machine-card--' + machine.status"
          >
            <div class="machine-card__top">
              <div class="machine-card__top-left">
                <span class="machine-card__name">{{ machine.name }}</span>
                <span
                  v-if="
                    (proc.key === 'welding' || proc.key === 'cutting') && machine.currentProduct
                  "
                  class="machine-card__product-inline"
                  :title="machine.currentProduct"
                >{{ machine.currentProduct }}</span>
                <span
                  v-if="
                    (proc.key === 'inspection' ||
                      proc.key === 'welding' ||
                      proc.key === 'cutting') &&
                    (machine.elapsedSec > 0 || machine.status === 'paused')
                  "
                  class="machine-card__title-metrics"
                >
                  <span v-if="machine.elapsedSec > 0" class="machine-card__title-metric">
                    <span class="machine-card__title-metric-label">経過</span>
                    <span class="machine-card__title-metric-value machine-card__stat-value--time">{{
                      formatDuration(machine.elapsedSec)
                    }}</span>
                  </span>
                  <span v-if="machine.status === 'paused'" class="machine-card__title-metric">
                    <span class="machine-card__title-metric-label">一時停止</span>
                    <span class="machine-card__title-metric-value machine-card__stat-value--pause">
                      <template v-if="machine.pausedSec > 0">{{
                        formatDuration(machine.pausedSec)
                      }}</template>
                      <template v-else>—</template>
                    </span>
                  </span>
                </span>
              </div>
              <div class="machine-card__top-right">
                <span
                  v-if="machine.operatorName && (machine.status === 'running' || machine.status === 'paused')"
                  class="machine-card__operator-inline"
                  :title="machine.operatorName"
                >
                  <el-icon :size="13"><User /></el-icon>
                  <span class="machine-card__operator-inline-name">{{ machine.operatorName }}</span>
                </span>
                <el-tag
                  size="small"
                  :type="statusTagType(machine.status)"
                  effect="plain"
                  round
                >
                  <span
                    v-if="machine.status === 'running'"
                    class="machine-card__pulse"
                  ></span>
                  {{ statusLabel(machine.status) }}
                </el-tag>
              </div>
            </div>

          </div>
        </div>
        <div v-else class="process-section__empty">
          <el-empty
            :description="
              proc.key === 'inspection' && proc.totalPlans > 0
                ? '稼働中の検査はありません'
                : '本日の計画はありません'
            "
            :image-size="48"
          />
        </div>
        </div>
      </div>

      <div class="process-history-row">
        <div
          v-for="proc in processes"
          :key="`${proc.key}-history`"
          class="process-history-cell"
        >
        <section
          v-if="proc.historyRows.length > 0"
          class="process-history-panel"
        >
          <header class="process-history-panel__head">
            <span class="process-history-panel__icon" aria-hidden="true">
              <el-icon :size="16"><CircleCheck /></el-icon>
            </span>
            <h3 class="process-history-panel__title">{{ processHistoryTitle(proc.key) }}</h3>
            <span class="process-history-panel__qty-total">
              <span class="process-history-panel__qty-total-label">{{
                t('mesWeldingActual.historyProductionQtyTotal')
              }}</span>
              <span class="process-history-panel__qty-total-value">{{
                historyProductionQtyTotal(proc.historyRows).toLocaleString()
              }}</span>
            </span>
            <span class="process-history-panel__count">{{ proc.historyRows.length }}</span>
          </header>
          <div class="history-card-list">
            <div
              v-for="row in proc.historyRows"
              :key="`${proc.key}-hist-${row.id}`"
              class="history-card"
            >
              <div class="history-card__top">
                <div class="history-card__top-left">
                  <span class="history-card__name" :title="historyCardTitle(proc.key, row)">{{
                    historyCardTitle(proc.key, row)
                  }}</span>
                  <span v-if="row.elapsedSec > 0" class="history-card__title-metrics">
                    <span class="history-card__title-metric">
                      <span class="history-card__title-metric-label">経過</span>
                      <span class="history-card__title-metric-value history-card__title-metric-value--time">{{
                        formatDuration(row.elapsedSec)
                      }}</span>
                    </span>
                  </span>
                </div>
                <div class="history-card__top-right">
                  <span
                    v-if="row.operatorName && row.operatorName !== '—'"
                    class="history-card__operator-inline"
                    :title="row.operatorName"
                  >
                    <el-icon :size="13"><User /></el-icon>
                    <span class="history-card__operator-inline-name">{{ row.operatorName }}</span>
                  </span>
                  <el-tag size="small" type="success" effect="plain" round>
                    {{ statusLabel('completed') }}
                  </el-tag>
                </div>
              </div>
              <div class="history-card__stats">
                <span class="history-card__stat">
                  <span class="history-card__stat-label">{{ t('mesWeldingActual.productionQty') }}</span>
                  <span class="history-card__stat-value">{{ row.actualQty.toLocaleString() }}</span>
                </span>
                <span class="history-card__stat">
                  <span class="history-card__stat-label">{{ t('mesWeldingActual.defectQty') }}</span>
                  <span
                    class="history-card__stat-value"
                    :class="{ 'history-card__stat-value--defect': row.defectQty > 0 }"
                  >{{ row.defectQty > 0 ? row.defectQty.toLocaleString() : '—' }}</span>
                </span>
                <span class="history-card__stat">
                  <span class="history-card__stat-label">{{ t('mesWeldingActual.productionStart') }}</span>
                  <span class="history-card__stat-value history-card__stat-value--time">{{
                    formatHistoryTime(row.startedAt)
                  }}</span>
                </span>
                <span class="history-card__stat">
                  <span class="history-card__stat-label">{{ t('mesWeldingActual.productionEnd') }}</span>
                  <span class="history-card__stat-value history-card__stat-value--time">{{
                    formatHistoryTime(row.endedAt)
                  }}</span>
                </span>
              </div>
            </div>
          </div>
        </section>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.monitor-page {
  padding: 12px 16px 24px;
  min-height: 100vh;
  background: #f0f2f5;
}

/* ── Header ── */
.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.monitor-header__left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.monitor-header__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  letter-spacing: 0.04em;
}
.monitor-header__clock {
  font-size: 14px;
  font-weight: 600;
  color: #909399;
  font-variant-numeric: tabular-nums;
  background: rgba(64, 158, 255, 0.08);
  border-radius: 6px;
  padding: 2px 10px;
}
.monitor-header__right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

/* ── KPI Row ── */
.kpi-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}
.kpi-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border-radius: 10px;
  padding: 12px 16px;
  min-width: 140px;
  flex: 1;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.kpi-card__icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.kpi-card__icon-wrap--running { background: linear-gradient(135deg, #67c23a, #85ce61); }
.kpi-card__icon-wrap--paused  { background: linear-gradient(135deg, #e6a23c, #f0c060); }
.kpi-card__icon-wrap--completed { background: linear-gradient(135deg, #409eff, #66b1ff); }
.kpi-card__icon-wrap--waiting { background: linear-gradient(135deg, #909399, #b1b3b8); }
.kpi-card__icon-wrap--machines { background: linear-gradient(135deg, #7c3aed, #a78bfa); }
.kpi-card__icon-wrap--rate { background: linear-gradient(135deg, #0ea5e9, #38bdf8); }
.kpi-card__icon-wrap--defect { background: linear-gradient(135deg, #f56c6c, #f89898); }
.kpi-card__body { min-width: 0; }
.kpi-card__value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
.kpi-card__sub {
  font-size: 13px;
  font-weight: 500;
  color: #909399;
}
.kpi-card__label {
  font-size: 12px;
  color: #909399;
  margin-top: 1px;
}

/* ── Process Grid ── */
.process-layout {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.process-runtime-row,
.process-history-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 14px;
  align-items: stretch;
}
.process-history-row {
  align-items: start;
}
.process-history-cell {
  min-width: 0;
}
.process-section {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.07);
  transition: box-shadow 0.2s;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.process-section--runtime {
  min-height: 0;
}
.process-section--runtime:hover,
.process-history-panel:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}
.process-section__header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  color: #fff;
}
.process-section__icon {
  font-size: 20px;
}
.process-section__name {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.process-section__badges {
  margin-left: auto;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.process-section__progress {
  padding: 8px 16px 4px;
}
.process-section__empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  min-height: 80px;
}

/* ── Machine Cards ── */
.machine-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 12px 12px;
  min-height: 80px;
}
.machine-card {
  flex-shrink: 0;
  min-height: 52px;
  box-sizing: border-box;
  border-radius: 8px;
  padding: 10px 12px 8px;
  border: 1px solid #ebeef5;
  transition: border-color 0.2s, background 0.2s;
}
.machine-card--running {
  border-color: #b3e19d;
  background: linear-gradient(135deg, rgba(103,194,58,0.04) 0%, rgba(103,194,58,0.01) 100%);
}
.machine-card--paused {
  border-color: #f3d19e;
  background: linear-gradient(135deg, rgba(230,162,60,0.04) 0%, rgba(230,162,60,0.01) 100%);
}
.machine-card--completed {
  border-color: #d9ecff;
  background: rgba(64,158,255,0.02);
}
.machine-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}
.machine-card__top-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  min-width: 0;
  flex: 1;
}
.machine-card__name {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
  flex-shrink: 0;
}
.machine-card__title-metrics {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.machine-card__title-metric {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  font-size: 12px;
  white-space: nowrap;
}
.machine-card__title-metric-label {
  color: #909399;
  font-weight: 500;
}
.machine-card__title-metric-value {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.machine-card__product-inline {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  max-width: min(220px, 40vw);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.machine-card__top-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  min-width: 0;
  flex: 1;
}
.machine-card__operator-inline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 140px;
  font-size: 12px;
  color: #606266;
}
.machine-card__operator-inline-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  color: #303133;
}
.machine-card__stat-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}
.machine-card__stat-value--pause {
  color: #e6a23c;
}
.machine-card__pulse {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #67c23a;
  margin-right: 4px;
  animation: pulse-blink 1.4s infinite;
  vertical-align: middle;
}
@keyframes pulse-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.machine-card__product {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.machine-card__product--empty {
  color: #c0c4cc;
}
.machine-card__product-cd {
  font-weight: 600;
  margin-right: 6px;
  color: #409eff;
}
.machine-card__product-name {
  color: #606266;
}
.machine-card__stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.machine-card__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
}
.machine-card__stat-label {
  font-size: 10px;
  color: #909399;
}
.machine-card__stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
  font-variant-numeric: tabular-nums;
}
.machine-card__stat-value--time {
  color: #e6a23c;
}
.machine-card__bar {
  margin-top: 2px;
}

/* ── Process history panel（下段グリッド・上端揃え） ── */
.process-history-panel {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.07);
  padding: 10px 12px 12px;
  transition: box-shadow 0.2s;
}
.process-history-panel__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.process-history-panel__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: #67c23a;
  background: rgba(103, 194, 58, 0.12);
}
.process-history-panel__title {
  margin: 0;
  flex: 1;
  font-size: 13px;
  font-weight: 700;
  color: #303133;
}
.process-history-panel__qty-total {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  flex-shrink: 0;
  font-size: 12px;
  white-space: nowrap;
}
.process-history-panel__qty-total-label {
  color: #909399;
  font-weight: 500;
}
.process-history-panel__qty-total-value {
  font-weight: 700;
  color: #303133;
  font-variant-numeric: tabular-nums;
}
.process-history-panel__count {
  font-size: 12px;
  font-weight: 700;
  color: #606266;
  font-variant-numeric: tabular-nums;
  padding: 2px 10px;
  border-radius: 999px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
}
.history-card-list {
  --history-card-row-height: 76px;
  --history-card-row-gap: 8px;
  --history-card-visible-rows: 5;
  display: flex;
  flex-direction: column;
  gap: var(--history-card-row-gap);
  height: calc(
    var(--history-card-visible-rows) * var(--history-card-row-height) +
      (var(--history-card-visible-rows) - 1) * var(--history-card-row-gap)
  );
  max-height: calc(
    var(--history-card-visible-rows) * var(--history-card-row-height) +
      (var(--history-card-visible-rows) - 1) * var(--history-card-row-gap)
  );
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-right: 2px;
}
.history-card-list::-webkit-scrollbar {
  width: 6px;
}
.history-card-list::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: #c0c4cc;
}
.history-card-list::-webkit-scrollbar-track {
  background: transparent;
}
.history-card {
  flex-shrink: 0;
  height: var(--history-card-row-height);
  min-height: var(--history-card-row-height);
  box-sizing: border-box;
  border-radius: 8px;
  padding: 10px 12px 8px;
  border: 1px solid #d9ecff;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.03) 0%, rgba(103, 194, 58, 0.04) 100%);
  overflow: hidden;
}
.history-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.history-card__top-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  min-width: 0;
  flex: 1;
}
.history-card__name {
  font-size: 13px;
  font-weight: 700;
  color: #303133;
}
.history-card__title-metrics {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.history-card__title-metric {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  font-size: 12px;
  white-space: nowrap;
}
.history-card__title-metric-label {
  color: #909399;
  font-weight: 500;
}
.history-card__title-metric-value {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.history-card__title-metric-value--time {
  color: #e6a23c;
}
.history-card__top-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  min-width: 0;
  flex-shrink: 0;
}
.history-card__operator-inline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 120px;
  font-size: 12px;
  color: #606266;
}
.history-card__operator-inline-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  color: #303133;
}
.history-card__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
}
.history-card__stat {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  font-size: 12px;
}
.history-card__stat-label {
  color: #909399;
  font-size: 11px;
}
.history-card__stat-value {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #303133;
}
.history-card__stat-value--defect {
  color: #f56c6c;
}
.history-card__stat-value--time {
  color: #606266;
  font-weight: 500;
}

/* ── Responsive ── */
@media (min-width: 1200px) {
  .process-runtime-row,
  .process-history-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 600px) {
  .monitor-page { padding: 8px; }
  .kpi-card { min-width: 120px; padding: 8px 10px; }
  .kpi-card__value { font-size: 18px; }
  .process-runtime-row,
  .process-history-row {
    grid-template-columns: 1fr;
  }
}
</style>
