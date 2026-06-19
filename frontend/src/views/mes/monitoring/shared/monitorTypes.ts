import type { PersistedPlanSession } from '@/views/mes/actualDataCollection/welding/weldingActualPersist'

export type MonitorProcessKey = 'inspection' | 'welding'

export interface ProcessSummary {
  key: MonitorProcessKey
  label: string
  icon: string
  color: string
  gradient: string
  totalPlans: number
  completedPlans: number
  inProgressPlans: number
  pausedPlans: number
  breakPlans: number
  waitingPlans: number
  totalQty: number
  actualQty: number
  defectQty: number
  machines: MachineStatus[]
  historyRows: ActualHistoryRow[]
  /** 検査モニタ専用：当日不良（項目別）リスト */
  defectListRows?: InspectionDefectListRow[]
  /** 検査モニタ専用：検査員能率ランキング */
  inspectorEfficiencyRows?: InspectionInspectorEfficiencyRow[]
  inspectorAvgEfficiency?: number | null
  /** 検査モニタ：通信断の稼働カード数 */
  commStalePlans?: number
}

export interface ActualHistoryRow {
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

export interface InspectionDefectItemRow {
  cd: string
  label: string
  qty: number
  occurredAt: string | null
}

/** 検査モニタ：不良（項目別）リスト行 */
export interface InspectionDefectListRow {
  rowKey: string
  planId: number
  inspectorName: string
  /** 溶接モニタ：設備名 */
  machineName?: string
  status: 'running' | 'paused' | 'break' | 'completed' | 'waiting'
  productName: string
  defectItemLabel: string
  defectQty: number
  defectOccurredAt: string | null
}

/** 検査モニタ：検査員能率行 */
export interface InspectionInspectorEfficiencyRow {
  rowKey: string
  inspectorUserId: number | null
  inspectorName: string
  sessionCount: number
  sumActualQty: number
  sumNetSec: number
  efficiencyPerHour: number | null
  rank: number
}

export interface MachineStatus {
  id?: number
  name: string
  status: 'running' | 'paused' | 'break' | 'idle' | 'completed'
  currentProduct: string
  currentProductCd: string
  progress: number
  totalPlans: number
  completedPlans: number
  elapsedSec: number
  actualQty: number
  plannedQty: number
  operatorName: string
  pausedSec: number
  breakSec: number
  /** 検査モニタ：検査員 users.id */
  inspectorUserId?: number | null
  /** 検査モニタ：次製品指定 */
  nextProductCd?: string | null
  nextProductName?: string | null
  nextAssignedAt?: string | null
  /** 検査モニタ：端末通信断（updated_at 超過） */
  commStale?: boolean
  /** 通信断時のみ：最終サーバー更新時刻（ISO） */
  lastCommAt?: string | null
}

/** 検査モニタ：次製品指定パネル行（稼働中 + 未稼働の初回指定） */
export interface NextAssignPanelRow {
  key: string
  inspectorUserId: number
  inspectorName: string
  currentProductLabel: string
  status: 'running' | 'paused' | 'break' | 'idle'
  nextProductCd?: string | null
  nextProductName?: string | null
  elapsedSec?: number
  pausedSec?: number
  breakSec?: number
  commStale?: boolean
  /** 未稼働の初回製品指定 */
  isFirstProduct: boolean
}

export type MesRowLike = {
  mes_production_started_at?: string | null
  mes_production_ended_at?: string | null
  mes_net_production_sec?: number | null
  mes_production_is_paused?: number | null
  production_completed_check?: number | null
}

export type MesRowWithOperator = MesRowLike & {
  id?: number
  mes_operator_user_id?: number | null
  mes_inspector_user_id?: number | null
  mes_inspector_name?: string | null
  mes_inspector_username?: string | null
  mes_paused_accum_sec?: number | null
}

export type RowClassifier = (
  row: MesRowLike,
) => 'completed' | 'running' | 'paused' | 'break' | 'waiting'

export type HistorySourceRow = MesRowWithOperator & {
  product_name?: string | null
  actual_production_quantity?: number | null
  defect_qty?: number | null
  welding_machine?: string | null
  updated_at?: string | null
}

export type PersistSessionMap = Map<number, PersistedPlanSession>
