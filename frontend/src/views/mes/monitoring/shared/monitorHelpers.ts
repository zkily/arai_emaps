import type { UserListItem } from '@/api/system'
import { formatDateTimeJST, parseDateAsJST } from '@/utils/dateFormat'
import { parseMesDefectMapFromRow } from '@/views/mes/actualDataCollection/shared/mesDefectByItem'
import type { MesDefectItemOption } from '@/views/mes/actualDataCollection/shared/loadProcessDefectItems'
import { readPausedAccumMs, type PersistedPlanSession } from '@/views/mes/actualDataCollection/welding/weldingActualPersist'
import type {
  ActualHistoryRow,
  HistorySourceRow,
  InspectionDefectItemRow,
  InspectionDefectListRow,
  InspectionInspectorEfficiencyRow,
  MachineStatus,
  MesRowLike,
  MesRowWithOperator,
  PersistSessionMap,
  RowClassifier,
} from './monitorTypes'

export function operatorUserIdFromRow(row: MesRowWithOperator): number | null {
  const op = row.mes_operator_user_id
  if (op != null && Number.isFinite(Number(op)) && Number(op) > 0) return Number(op)
  const insp = row.mes_inspector_user_id
  if (insp != null && Number.isFinite(Number(insp)) && Number(insp) > 0) return Number(insp)
  return null
}

export function operatorNameById(userId: number | null | undefined, operators: UserListItem[]): string {
  if (userId == null) return ''
  const u = operators.find((x) => x.id === userId)
  return (u?.full_name || u?.username || '').trim()
}

/** 行に結合済みの検査員名（API JOIN）を優先 */
export function inspectorNameFromRow(row: MesRowWithOperator | null | undefined): string {
  if (!row) return ''
  return ((row.mes_inspector_name || row.mes_inspector_username || '') as string).trim()
}

export function operatorNameForRow(
  row: MesRowWithOperator | null | undefined,
  operators: UserListItem[],
): string {
  if (!row) return ''
  const fromRow = inspectorNameFromRow(row)
  if (fromRow) return fromRow
  return operatorNameById(operatorUserIdFromRow(row), operators)
}

export function isRowMesActive(row: MesRowLike): boolean {
  if (Number(row.production_completed_check ?? 0) === 1) return false
  const started = row.mes_production_started_at
  if (started == null || !String(started).trim()) return false
  const ended = row.mes_production_ended_at
  return ended == null || !String(ended).trim()
}

export function classifyRow(row: MesRowLike): 'completed' | 'running' | 'paused' | 'waiting' {
  if (Number(row.production_completed_check ?? 0) === 1) return 'completed'
  if (isRowMesActive(row)) {
    const flag = Number(row.mes_production_is_paused ?? 0)
    if (flag === 1 || flag === 2) return 'paused'
    return 'running'
  }
  const ended = row.mes_production_ended_at
  if (ended != null && String(ended).trim()) return 'completed'
  return 'waiting'
}

/** 検査工程：mes_production_is_paused 2=休憩中 */
export function classifyInspectionRow(
  row: MesRowLike,
): 'completed' | 'running' | 'paused' | 'break' | 'waiting' {
  if (Number(row.production_completed_check ?? 0) === 1) return 'completed'
  if (isRowMesActive(row)) {
    const flag = Number(row.mes_production_is_paused ?? 0)
    if (flag === 2) return 'break'
    if (flag === 1) return 'paused'
    return 'running'
  }
  const ended = row.mes_production_ended_at
  if (ended != null && String(ended).trim()) return 'completed'
  return 'waiting'
}

export type InspectionPersistSession = {
  breakAccumMs?: number
  breakSliceStart?: number | null
}

export function breakSecondsForInspectionRow(
  row: { mes_break_sec?: number | null; mes_production_is_paused?: number | null },
  tickNow: number,
  persistSess?: InspectionPersistSession | null,
): number {
  const base = Math.max(0, Math.round(Number(row.mes_break_sec ?? 0)))
  if (Number(row.mes_production_is_paused) !== 2) return base
  if (persistSess?.breakSliceStart == null) return base
  const accum = Math.max(0, Math.round((persistSess.breakAccumMs ?? 0) / 1000))
  const live = Math.max(0, Math.round((tickNow - persistSess.breakSliceStart) / 1000))
  return accum + live
}

export function pausedSecondsForRow(
  row: MesRowWithOperator,
  tickNow: number,
  persistSess?: PersistedPlanSession | null,
): number {
  if (persistSess) {
    return Math.max(0, Math.round(readPausedAccumMs(persistSess, tickNow) / 1000))
  }
  const raw = row.mes_paused_accum_sec
  if (raw != null && Number.isFinite(Number(raw))) {
    return Math.max(0, Math.round(Number(raw)))
  }
  return 0
}

export function elapsedSeconds(
  row: {
    mes_net_production_sec?: number | null
    mes_production_started_at?: string | null
    mes_production_ended_at?: string | null
  },
  tickNow: number,
): number {
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
    return Math.max(0, Math.round((tickNow - start) / 1000))
  }
  const net = row.mes_net_production_sec
  if (typeof net === 'number' && net >= 0) return net
  const endDate = parseDateAsJST(endedRaw)
  if (!endDate) return 0
  return Math.max(0, Math.round((endDate.getTime() - start) / 1000))
}

export function buildMachineStatus(
  name: string,
  mRows: Array<{
    product_cd?: string | null
    product_name?: string | null
    actual_production_quantity?: number | null
    planned_quantity?: number | null
    mes_break_sec?: number | null
    mes_production_is_paused?: number | null
  } & MesRowWithOperator>,
  operators: UserListItem[],
  tickNow: number,
  classify: RowClassifier = classifyRow,
  persistSessionsByPlanId?: PersistSessionMap,
  inspectionPersistByPlanId?: Map<number, InspectionPersistSession>,
): MachineStatus {
  const running = mRows.find((r) => classify(r) === 'running')
  const pausedRow = mRows.find((r) => classify(r) === 'paused')
  const breakRow = mRows.find((r) => classify(r) === 'break')
  const active = running || pausedRow || breakRow
  const completed = mRows.filter((r) => classify(r) === 'completed').length
  const operatorName = active ? operatorNameForRow(active, operators) : ''
  const status: MachineStatus['status'] = running
    ? 'running'
    : breakRow
      ? 'break'
      : pausedRow
        ? 'paused'
        : 'idle'
  let pausedSec = 0
  let breakSec = 0
  if (status === 'paused' && pausedRow) {
    const sess =
      pausedRow.id != null && persistSessionsByPlanId
        ? persistSessionsByPlanId.get(pausedRow.id)
        : undefined
    pausedSec = pausedSecondsForRow(pausedRow, tickNow, sess)
  }
  if (status === 'break' && breakRow) {
    const inspSess =
      breakRow.id != null && inspectionPersistByPlanId
        ? inspectionPersistByPlanId.get(breakRow.id)
        : undefined
    breakSec = breakSecondsForInspectionRow(breakRow, tickNow, inspSess)
  }
  return {
    name,
    status,
    currentProduct: active?.product_name || '',
    currentProductCd: active?.product_cd || '',
    progress: mRows.length > 0 ? Math.round((completed / mRows.length) * 100) : 0,
    totalPlans: mRows.length,
    completedPlans: completed,
    elapsedSec: active ? elapsedSeconds(active, tickNow) : 0,
    actualQty: mRows.reduce((s, r) => s + (r.actual_production_quantity ?? 0), 0),
    plannedQty: mRows.reduce((s, r) => s + (r.planned_quantity ?? 0), 0),
    operatorName,
    pausedSec,
    breakSec,
  }
}

function isRowProductionCompleted(row: MesRowLike): boolean {
  return Number(row.production_completed_check ?? 0) === 1
}

function historyElapsedSec(row: MesRowLike, tickNow: number): number {
  const net = row.mes_net_production_sec
  if (typeof net === 'number' && net >= 0) return net
  return elapsedSeconds(row, tickNow)
}

export function buildHistoryRows(
  rows: HistorySourceRow[],
  operators: UserListItem[],
  tickNow: number,
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
      operatorName: operatorNameForRow(row, operators) || '—',
      machineName: machineLabel(row) || '—',
      productName: (row.product_name ?? '').trim() || '—',
      actualQty: row.actual_production_quantity ?? 0,
      defectQty: row.defect_qty ?? 0,
      startedAt: row.mes_production_started_at ?? null,
      endedAt: row.mes_production_ended_at ?? null,
      elapsedSec: historyElapsedSec(row, tickNow),
    }))
}

export function formatDuration(sec: number): string {
  if (sec <= 0) return '--:--'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (h > 0) return `${h}h ${String(m).padStart(2, '0')}m`
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    running: '稼働中',
    paused: '一時停止',
    break: '休憩中',
    idle: '待機中',
    waiting: '待機',
    completed: '完了',
  }
  return map[status] ?? status
}

export type ElTagType = 'primary' | 'success' | 'info' | 'warning' | 'danger'

export function statusTagType(status: string): ElTagType {
  const map: Record<string, ElTagType> = {
    running: 'success',
    paused: 'warning',
    break: 'primary',
    idle: 'info',
    completed: 'info',
  }
  return map[status] ?? 'info'
}

export function formatHistoryTime(
  iso: string | null | undefined,
  intlLocale: string,
): string {
  if (iso == null || !String(iso).trim()) return '—'
  const text = formatDateTimeJST(iso, intlLocale, { second: undefined })
  return text || '—'
}

/** 不良発生時刻など：時刻のみ（日付なし） */
export function formatHistoryTimeOnly(
  iso: string | null | undefined,
  intlLocale: string,
): string {
  if (iso == null || !String(iso).trim()) return '—'
  const date = parseDateAsJST(iso)
  if (!date) return '—'
  const text = date.toLocaleString(intlLocale, {
    timeZone: 'Asia/Tokyo',
    hour: '2-digit',
    minute: '2-digit',
  })
  return text || '—'
}

export function historyProductionQtyTotal(rows: ActualHistoryRow[]): number {
  return rows.reduce((sum, row) => sum + (row.actualQty ?? 0), 0)
}

export function historyCardTitle(
  processKey: 'inspection' | 'welding',
  row: ActualHistoryRow,
): string {
  if (processKey === 'inspection') return row.productName
  const machine = row.machineName.trim()
  if (machine && machine !== '—') return `${machine} · ${row.productName}`
  return row.productName
}

export function processHistoryTitle(
  processKey: 'inspection' | 'welding',
  t: (key: string) => string,
): string {
  if (processKey === 'inspection') return t('mesInspectionActual.historyTitle')
  return t('mesWeldingActual.historyTitle')
}

export function weldingElapsedFromPersist(sess: PersistedPlanSession, tickNow: number): number {
  if (sess.wallStart == null) return 0
  const end = sess.wallEnd ?? tickNow
  return Math.max(0, Math.round((end - sess.wallStart) / 1000))
}

export function buildDefectDetailRows(
  rawDefects: unknown,
  defectItems: MesDefectItemOption[],
  labelOf: (cd: string, fallback?: string) => string,
  fallbackAt?: string | null,
): InspectionDefectItemRow[] {
  const defects = parseMesDefectMapFromRow(rawDefects)
  const rows: InspectionDefectItemRow[] = []
  const seen = new Set<string>()
  for (const item of defectItems) {
    const entry = defects[item.id]
    if (!entry || entry.qty <= 0) continue
    rows.push({
      cd: item.id,
      label: labelOf(item.id, item.label),
      qty: entry.qty,
      occurredAt: entry.at ?? fallbackAt ?? null,
    })
    seen.add(item.id)
  }
  for (const [cd, entry] of Object.entries(defects)) {
    if (seen.has(cd) || entry.qty <= 0) continue
    rows.push({
      cd,
      label: labelOf(cd),
      qty: entry.qty,
      occurredAt: entry.at ?? fallbackAt ?? null,
    })
  }
  return rows
}

export function buildMonitorDefectListRows(
  rows: Array<
    {
      id?: number
      product_cd?: string | null
      product_name?: string | null
      mes_defect_by_item?: Record<string, number> | null
      mes_production_ended_at?: string | null
      updated_at?: string | null
      welding_machine?: string | null
    } & MesRowWithOperator
  >,
  operators: UserListItem[],
  defectItems: MesDefectItemOption[],
  labelOf: (cd: string, fallback?: string) => string,
  classify: RowClassifier = classifyInspectionRow,
  machineLabel?: (row: MesRowWithOperator & { welding_machine?: string | null }) => string,
): InspectionDefectListRow[] {
  const list: InspectionDefectListRow[] = []
  for (const row of rows) {
    const status = classify(row)
    const planId = row.id ?? 0
    const inspectorName = operatorNameForRow(row, operators) || '—'
    const productName = (row.product_name ?? '').trim() || '—'
    const fallbackAt =
      status === 'completed'
        ? row.mes_production_ended_at ?? row.updated_at ?? null
        : row.updated_at ?? null
    const defectItemsRows = buildDefectDetailRows(
      row.mes_defect_by_item,
      defectItems,
      labelOf,
      fallbackAt,
    )
    if (defectItemsRows.length === 0) continue
    const machineName = machineLabel ? machineLabel(row) || '—' : undefined
    for (const item of defectItemsRows) {
      list.push({
        rowKey: `${planId}-${item.cd}`,
        planId,
        inspectorName,
        machineName,
        status,
        productName,
        defectItemLabel: item.label,
        defectQty: item.qty,
        defectOccurredAt: item.occurredAt,
      })
    }
  }
  return list.sort((a, b) => {
    const tb = parseDateAsJST(b.defectOccurredAt)?.getTime() ?? 0
    const ta = parseDateAsJST(a.defectOccurredAt)?.getTime() ?? 0
    if (tb !== ta) return tb - ta
    const machineCmp = (a.machineName ?? '').localeCompare(b.machineName ?? '', 'ja')
    if (machineCmp !== 0) return machineCmp
    const productCmp = a.productName.localeCompare(b.productName, 'ja')
    if (productCmp !== 0) return productCmp
    const defectCmp = a.defectItemLabel.localeCompare(b.defectItemLabel, 'ja')
    if (defectCmp !== 0) return defectCmp
    return a.planId - b.planId
  })
}

export function buildInspectionDefectListRows(
  rows: Array<
    {
      id?: number
      product_cd?: string | null
      product_name?: string | null
      mes_defect_by_item?: Record<string, number> | null
      mes_production_ended_at?: string | null
      updated_at?: string | null
    } & MesRowWithOperator
  >,
  operators: UserListItem[],
  defectItems: MesDefectItemOption[],
  labelOf: (cd: string, fallback?: string) => string,
): InspectionDefectListRow[] {
  return buildMonitorDefectListRows(rows, operators, defectItems, labelOf, classifyInspectionRow)
}

/** 検査実績収集端の checkpoint 間隔（5s）+ モニタ刷新（15s）を考慮した通信断判定 */
export const INSPECTION_MONITOR_COMM_STALE_MS = 60_000

/**
 * 進行中セッションで updated_at が閾値を超えたら通信断とみなす（経過時間の算出には使わない）。
 * mes_client_instance_id がある行のみ（MES 端末がロックしたセッション）。
 */
export function isInspectionClientCommStale(
  row: {
    updated_at?: string | null
    mes_production_started_at?: string | null
    mes_client_instance_id?: string | null
  },
  tickNow: number,
  status: 'running' | 'paused' | 'break',
): boolean {
  if (status !== 'running' && status !== 'paused' && status !== 'break') return false
  const clientId = (row.mes_client_instance_id ?? '').trim()
  if (!clientId) return false
  const started = row.mes_production_started_at
  if (started == null || !String(started).trim()) return false
  const updatedMs = parseDateAsJST(row.updated_at)?.getTime()
  if (updatedMs == null || !Number.isFinite(updatedMs)) return false
  return tickNow - updatedMs > INSPECTION_MONITOR_COMM_STALE_MS
}

export function fmtMonitorEfficiency(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return Math.round(value).toLocaleString()
}

export function fmtMonitorDefectRate(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value}%`
}

export function inspectorEfficiencyRankClass(rank: number): string {
  if (rank === 1) return 'inspection-efficiency-rank--gold'
  if (rank === 2) return 'inspection-efficiency-rank--silver'
  if (rank === 3) return 'inspection-efficiency-rank--bronze'
  return ''
}

function rowNetSecForEfficiency(row: HistorySourceRow, tickNow: number): number {
  const net = row.mes_net_production_sec
  if (typeof net === 'number' && net >= 0 && Number(row.production_completed_check ?? 0) === 1) {
    return net
  }
  if (typeof net === 'number' && net > 0) return net
  return elapsedSeconds(row, tickNow)
}

function efficiencyPerHourFromTotals(sumActualQty: number, sumNetSec: number): number | null {
  if (sumActualQty <= 0 || sumNetSec <= 0) return null
  return Math.round(sumActualQty / (sumNetSec / 3600))
}

export function buildInspectionInspectorEfficiencyRows(
  rows: HistorySourceRow[],
  operators: UserListItem[],
  tickNow: number,
): InspectionInspectorEfficiencyRow[] {
  const map = new Map<
    string,
    {
      inspectorUserId: number | null
      inspectorName: string
      sessionCount: number
      sumActualQty: number
      sumNetSec: number
    }
  >()

  for (const row of rows) {
    const actual = Number(row.actual_production_quantity ?? 0)
    const netSec = rowNetSecForEfficiency(row, tickNow)
    if (actual <= 0 && netSec <= 0) continue

    const inspId = operatorUserIdFromRow(row)
    const inspectorName = operatorNameForRow(row, operators) || '—'
    const key = inspId != null ? String(inspId) : `name:${inspectorName}`

    if (!map.has(key)) {
      map.set(key, {
        inspectorUserId: inspId,
        inspectorName,
        sessionCount: 0,
        sumActualQty: 0,
        sumNetSec: 0,
      })
    }
    const bucket = map.get(key)!
    bucket.sessionCount += 1
    bucket.sumActualQty += actual
    bucket.sumNetSec += netSec
  }

  const list: InspectionInspectorEfficiencyRow[] = []
  for (const [key, bucket] of map) {
    const efficiencyPerHour = efficiencyPerHourFromTotals(bucket.sumActualQty, bucket.sumNetSec)
    if (efficiencyPerHour == null) continue
    list.push({
      rowKey: key,
      inspectorUserId: bucket.inspectorUserId,
      inspectorName: bucket.inspectorName,
      sessionCount: bucket.sessionCount,
      sumActualQty: bucket.sumActualQty,
      sumNetSec: bucket.sumNetSec,
      efficiencyPerHour,
      rank: 0,
    })
  }

  list.sort((a, b) => (b.efficiencyPerHour ?? -1) - (a.efficiencyPerHour ?? -1))
  list.forEach((row, index) => {
    row.rank = index + 1
  })
  return list
}

export function computeInspectorAvgEfficiency(
  rows: InspectionInspectorEfficiencyRow[],
): number | null {
  const sumActualQty = rows.reduce((sum, row) => sum + row.sumActualQty, 0)
  const sumNetSec = rows.reduce((sum, row) => sum + row.sumNetSec, 0)
  return efficiencyPerHourFromTotals(sumActualQty, sumNetSec)
}

/** 検査モニタ KPI：確定済（完了）行のみで加重平均能率 */
export function computeCompletedInspectorAvgEfficiency(
  rows: HistorySourceRow[],
  operators: UserListItem[],
): number | null {
  const completed = rows.filter((row) => Number(row.production_completed_check ?? 0) === 1)
  const effRows = buildInspectionInspectorEfficiencyRows(completed, operators, Date.now())
  return computeInspectorAvgEfficiency(effRows)
}

/** 検査モニタ：能率異常（200未満 / 800超） */
export function isMonitorEfficiencyOutOfRange(value: number | null | undefined): boolean {
  if (value == null || !Number.isFinite(value)) return false
  const rate = Math.round(value)
  return rate < 200 || rate > 800
}
