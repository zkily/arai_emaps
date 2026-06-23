import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createWeldingManagement,
  deleteWeldingManagement,
  fetchWeldingManagementList,
  patchWeldingManagement,
  type PatchWeldingManagementBody,
  type WeldingManagementListRow,
} from '@/api/weldingManagement'
import { fetchWeldingMesMachines, fetchWeldingMesProducts, type WeldingMesMachine } from '@/api/weldingMesEquipment'
import { getProductList } from '@/api/master/productMaster'
import { useUserStore } from '@/modules/auth/stores/user'
import { formatDateTimeJST, getJSTToday, shiftDateYmdJST } from '@/utils/dateFormat'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import { guardMesOperation } from '@/utils/mesOperationGuard'
import { fetchWeldingSectionOperators } from '@/views/mes/shared/weldingOperatorFilter'
import { WELDING_DEFECT_DETECTION_PROCESS_CD } from '@/views/mes/actualDataCollection/welding/weldingActualConfig'
import { parseDefectsFromRow } from '@/views/mes/actualDataCollection/welding/weldingActualPersist'
import {
  groupMesDefectItemsByAttributableProcess,
  loadMesDefectItemsForProcess,
  resolveMesDefectItemLabel,
  type MesDefectItemGroup,
  type MesDefectItemOption,
} from '@/views/mes/actualDataCollection/shared/loadProcessDefectItems'
import {
  resolveWeldingDataSource,
  weldingDataSourceTagType,
} from '@/views/mes/actualDataCollection/welding/weldingDataSource'
import { useI18n } from 'vue-i18n'
import {
  formatQtyInputValue,
  formatTimeInputValue,
} from '../inspection/useInspectionManualRegistration'
import { confirmWeldingPieceQty } from './confirmPieceQtyDialog'

export type WeldingMgmtRow = WeldingManagementListRow & { id: number }

export interface WeldingRegistrationProduct {
  product_code: string
  product_name: string
  unit_per_box: number
}

export type QtyInputSource = 'box' | 'piece' | null

export interface ManualRegistrationForm {
  productionDay: string
  productionSequence: number | null
  weldingMachineId: number | null
  weldingMachineName: string
  productCd: string
  productName: string
  operatorUserId: number | null
  boxQty: number | null
  pieceQty: number | null
  qtyInputSource: QtyInputSource
  defects: Record<string, number>
  registrationNote: string
  startedAt: string | null
  endedAt: string | null
  breakMin: number
  stopMin: number
}

function emptyForm(day: string, operatorId: number | null): ManualRegistrationForm {
  return {
    productionDay: day,
    productionSequence: null,
    weldingMachineId: null,
    weldingMachineName: '',
    productCd: '',
    productName: '',
    operatorUserId: operatorId,
    boxQty: null,
    pieceQty: null,
    qtyInputSource: null,
    defects: {},
    registrationNote: '',
    startedAt: null,
    endedAt: null,
    breakMin: 0,
    stopMin: 0,
  }
}

function pieceQtyFromBoxes(boxes: number, unitPerBox: number): number {
  return Math.round(boxes * unitPerBox)
}

function boxQtyFromPieces(pieces: number, unitPerBox: number): number {
  if (unitPerBox <= 0) return 0
  return Math.round(pieces / unitPerBox)
}

function parseTimeInput(raw: string | undefined | null): string | null {
  const s = String(raw ?? '').trim()
  if (!s) return null

  const colon = s.match(/^(\d{1,2}):(\d{1,2})$/)
  if (colon) {
    const h = Number(colon[1])
    const m = Number(colon[2])
    if (h >= 0 && h <= 23 && m >= 0 && m <= 59) {
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:00`
    }
    return null
  }

  const digits = s.replace(/\D/g, '')
  if (digits.length === 1 || digits.length === 2) {
    const h = Number(digits)
    if (h >= 0 && h <= 23) return `${String(h).padStart(2, '0')}:00:00`
  }
  if (digits.length === 3) {
    const h = Number(digits.slice(0, 1))
    const m = Number(digits.slice(1, 3))
    if (h <= 23 && m <= 59) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:00`
  }
  if (digits.length >= 4) {
    const h = Number(digits.slice(0, 2))
    const m = Number(digits.slice(2, 4))
    if (h <= 23 && m <= 59) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:00`
  }
  return null
}

function sanitizeTimeDraft(raw: string | undefined | null): string {
  const s = String(raw ?? '').replace(/[^\d:]/g, '')
  if (s.includes(':')) {
    const [h, m = ''] = s.split(':')
    return `${h.slice(0, 2)}:${m.slice(0, 2)}`
  }
  return s.slice(0, 4)
}

function parseQtyInput(raw: string | undefined | null): number | null {
  const digits = String(raw ?? '').replace(/\D/g, '')
  if (!digits) return null
  const n = Number.parseInt(digits, 10)
  return Number.isFinite(n) ? Math.max(0, n) : null
}

function resolveUnitPerBox(productCd: string, list: WeldingRegistrationProduct[]): number {
  const code = productCd.trim()
  if (!code) return 0
  const hit = list.find((p) => p.product_code.trim() === code)
  return Math.max(0, Number(hit?.unit_per_box) || 0)
}

function isRowMesInProgress(row: WeldingManagementListRow): boolean {
  return Boolean(row.mes_production_started_at && !row.mes_production_ended_at)
}

function rowWallElapsedSec(row: WeldingManagementListRow): number {
  const started = row.mes_production_started_at
  if (!started || !String(started).trim()) return Math.max(0, row.mes_net_production_sec ?? 0)
  const ws = Date.parse(String(started))
  if (Number.isNaN(ws)) return Math.max(0, row.mes_net_production_sec ?? 0)
  const ended = row.mes_production_ended_at
  const we = ended != null && String(ended).trim() ? Date.parse(String(ended)) : Date.now()
  if (Number.isNaN(we)) return Math.max(0, row.mes_net_production_sec ?? 0)
  return Math.max(0, Math.floor((we - ws) / 1000))
}

function rowPausedAccumSec(row: WeldingManagementListRow): number {
  const stored = row.mes_paused_accum_sec
  if (stored != null && Number.isFinite(Number(stored))) {
    return Math.max(0, Math.round(Number(stored)))
  }
  const started = row.mes_production_started_at
  if (!started || !String(started).trim()) return 0
  const ws = Date.parse(String(started))
  if (Number.isNaN(ws)) return 0
  const ended = row.mes_production_ended_at
  const we = ended != null && String(ended).trim() ? Date.parse(String(ended)) : Date.now()
  if (Number.isNaN(we)) return 0
  const wallSec = Math.max(0, Math.floor((we - ws) / 1000))
  const netSec = Math.max(0, row.mes_net_production_sec ?? 0)
  return Math.max(0, wallSec - netSec)
}

function resolveEfficiencyRate(row: WeldingManagementListRow): number | null {
  const prod = Number(row.actual_production_quantity ?? 0)
  if (!Number.isFinite(prod) || prod <= 0) return null
  const netSec = Math.max(0, rowWallElapsedSec(row) - rowPausedAccumSec(row))
  if (netSec <= 0) return null
  const hours = netSec / 3600
  const rate = prod / hours
  if (!Number.isFinite(rate)) return null
  return Math.round(rate)
}

function formatEfficiencyRate(row: WeldingManagementListRow): string {
  const rate = resolveEfficiencyRate(row)
  return rate == null ? '—' : String(rate)
}

function isEfficiencyRateOutOfRange(row: WeldingManagementListRow): boolean {
  const rate = resolveEfficiencyRate(row)
  if (rate == null) return false
  return rate < 200 || rate > 800
}

function rowOperatorId(row: WeldingManagementListRow): number | null {
  const id = row.mes_operator_user_id
  if (id == null || !Number.isFinite(Number(id))) return null
  const n = Number(id)
  return n > 0 ? n : null
}

function mergeDefects(defects: Record<string, number>): Record<string, number> {
  const out: Record<string, number> = {}
  for (const [k, v] of Object.entries(defects)) {
    const qty = Math.max(0, Math.round(Number(v)))
    if (qty > 0) out[k] = qty
  }
  return out
}

function timeOnlyFromDateTime(val: string | Date | null | undefined): string | null {
  if (val == null) return null
  const d = val instanceof Date ? val : new Date(val)
  if (!Number.isFinite(d.getTime())) return null
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${h}:${m}:${s}`
}

function combineProductionDayAndTime(day: string, time: string | null | undefined): Date | null {
  const dayStr = day.trim().slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dayStr) || !time) return null
  const match = time.trim().match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/)
  if (!match) return null
  const [y, mo, d] = dayStr.split('-').map(Number)
  const hours = Number(match[1])
  const minutes = Number(match[2])
  const seconds = Number(match[3] ?? 0)
  if (![hours, minutes, seconds].every((n) => Number.isFinite(n))) return null
  const out = new Date(y, mo - 1, d, hours, minutes, seconds, 0)
  return Number.isFinite(out.getTime()) ? out : null
}

function resolveProductionEndDateTime(
  day: string,
  startTime: string | null | undefined,
  endTime: string | null | undefined,
): { started: Date | null; ended: Date | null; endsNextDay: boolean } {
  const started = combineProductionDayAndTime(day, startTime)
  const endedSameDay = combineProductionDayAndTime(day, endTime)
  if (!started || !endedSameDay) {
    return { started, ended: endedSameDay, endsNextDay: false }
  }
  if (endedSameDay.getTime() <= started.getTime()) {
    const ended = new Date(endedSameDay)
    ended.setDate(ended.getDate() + 1)
    return { started, ended, endsNextDay: true }
  }
  return { started, ended: endedSameDay, endsNextDay: false }
}

function secToMin(sec: number | null | undefined): number {
  if (sec == null || !Number.isFinite(Number(sec))) return 0
  return Math.max(0, Math.round(Number(sec) / 60))
}

function formatMinutesLabel(totalMin: number): string {
  const m = Math.max(0, Math.round(totalMin))
  const h = Math.floor(m / 60)
  const min = m % 60
  if (h <= 0) return `${min}分`
  return `${h}時間${min}分`
}

export function useWeldingManualRegistration() {
  const { t, te } = useI18n()
  const userStore = useUserStore()
  const { canCreate, canEdit, canDelete } = useMesOperationPermission()

  const productionDay = ref(getJSTToday())
  const operatorFilterId = ref<number | null>(null)
  const machineFilterName = ref<string | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const deletingRowId = ref<number | null>(null)
  const rows = ref<WeldingMgmtRow[]>([])
  const machines = ref<WeldingMesMachine[]>([])
  const loadingMachines = ref(false)
  const products = ref<WeldingRegistrationProduct[]>([])
  let syncingQty = false
  const loadingProducts = ref(false)
  const defectItems = ref<MesDefectItemOption[]>([])
  const loadingDefectItems = ref(false)
  const operators = ref<{ id: number; username: string; full_name?: string }[]>([])
  const loadingOperators = ref(false)

  const editingRowId = ref<number | null>(null)
  const form = ref<ManualRegistrationForm>(emptyForm(getJSTToday(), null))
  const startedAtText = ref('')
  const endedAtText = ref('')

  function syncTimeTextsFromForm(): void {
    startedAtText.value = formatTimeInputValue(form.value.startedAt)
    endedAtText.value = formatTimeInputValue(form.value.endedAt)
  }

  function onStartedAtInput(raw: string | undefined | null): void {
    startedAtText.value = sanitizeTimeDraft(raw)
    const parsed = parseTimeInput(startedAtText.value)
    if (parsed) form.value.startedAt = parsed
  }

  function onEndedAtInput(raw: string | undefined | null): void {
    endedAtText.value = sanitizeTimeDraft(raw)
    const parsed = parseTimeInput(endedAtText.value)
    if (parsed) form.value.endedAt = parsed
  }

  function onStartedAtBlur(): void {
    const parsed = parseTimeInput(startedAtText.value)
    form.value.startedAt = parsed
    startedAtText.value = formatTimeInputValue(parsed)
  }

  function onEndedAtBlur(): void {
    const parsed = parseTimeInput(endedAtText.value)
    form.value.endedAt = parsed
    endedAtText.value = formatTimeInputValue(parsed)
  }

  const loggedInUserId = computed(() => {
    const id = userStore.user?.id
    return id != null && Number.isFinite(Number(id)) ? Number(id) : null
  })

  const isEdit = computed(() => editingRowId.value != null)
  const canSave = computed(() => (isEdit.value ? canEdit.value : canCreate.value))

  const defectItemGroups = computed<MesDefectItemGroup[]>(() =>
    groupMesDefectItemsByAttributableProcess(defectItems.value),
  )

  const filteredRows = computed(() => {
    let list = rows.value
    const fid = operatorFilterId.value
    if (fid != null) list = list.filter((r) => rowOperatorId(r) === fid)
    const machine = machineFilterName.value?.trim()
    if (machine) list = list.filter((r) => (r.welding_machine ?? '').trim() === machine)
    return list
  })

  const unitPerBox = computed(() => resolveUnitPerBox(form.value.productCd, products.value))

  const timeSummary = computed(() => {
    const { started, ended, endsNextDay } = resolveProductionEndDateTime(
      form.value.productionDay,
      form.value.startedAt,
      form.value.endedAt,
    )
    const ws = started?.getTime()
    const we = ended?.getTime()
    const breakMin = Math.max(0, Math.round(form.value.breakMin))
    const stopMin = Math.max(0, Math.round(form.value.stopMin))
    const pauseMin = breakMin + stopMin
    if (ws == null || we == null || !Number.isFinite(ws) || !Number.isFinite(we)) {
      return {
        shiftMin: null as number | null,
        workMin: null as number | null,
        pauseMin,
        breakMin,
        stopMin,
        endsNextDay: false,
      }
    }
    const shiftMin = Math.round((we - ws) / 60000)
    const workMin = Math.max(0, shiftMin - pauseMin)
    return { shiftMin, workMin, pauseMin, breakMin, stopMin, endsNextDay }
  })

  watch(productionDay, (day) => {
    form.value.productionDay = day
  })

  watch(
    () => form.value.weldingMachineId,
    (id, oldId) => {
      if (editingRowId.value != null) return
      if (id === oldId) return
      const hit = machines.value.find((m) => m.id === id)
      form.value.weldingMachineName = hit?.machine_name ?? ''
      form.value.productCd = ''
      form.value.productName = ''
      form.value.boxQty = null
      form.value.pieceQty = null
      form.value.qtyInputSource = null
      void loadProducts()
    },
  )

  watch(
    () => form.value.operatorUserId,
    (id) => {
      if (editingRowId.value != null) return
      if (id != null && id > 0) return
      if (!form.value.productCd.trim()) return
      form.value.productCd = ''
      form.value.productName = ''
      form.value.boxQty = null
      form.value.pieceQty = null
      form.value.qtyInputSource = null
    },
  )

  function operatorLabel(userId: number | null | undefined): string {
    if (userId == null) return '—'
    const hit = operators.value.find((u) => u.id === userId)
    if (!hit) return String(userId)
    return (hit.full_name || hit.username || '').trim() || String(userId)
  }

  function defectItemLabel(defectCd: string, fallback: string): string {
    return resolveMesDefectItemLabel(defectCd, fallback, t, te)
  }

  function dataSourceLabel(row: WeldingManagementListRow): string {
    const src = resolveWeldingDataSource(row)
    if (src === 'excel') return 'Excel'
    if (src === 'csv') return 'CSV'
    return 'MES'
  }

  function dataSourceTagType(row: WeldingManagementListRow) {
    return weldingDataSourceTagType(resolveWeldingDataSource(row))
  }

  function canEditRow(row: WeldingMgmtRow): boolean {
    if (!canEdit.value) return false
    if (isRowMesInProgress(row)) return false
    return true
  }

  function canDeleteRow(_row: WeldingMgmtRow): boolean {
    return canDelete.value
  }

  function defectCount(defectCd: string): number {
    return Math.max(0, Math.round(form.value.defects[defectCd] ?? 0))
  }

  function bumpDefect(defectCd: string, delta: number): void {
    const next = Math.max(0, (form.value.defects[defectCd] ?? 0) + delta)
    if (next === 0) delete form.value.defects[defectCd]
    else form.value.defects[defectCd] = next
  }

  function onDefectQtyInput(defectCd: string, raw: string | undefined | null): void {
    const qty = parseQtyInput(raw)
    if (qty == null || qty <= 0) {
      delete form.value.defects[defectCd]
      return
    }
    form.value.defects[defectCd] = qty
  }

  const firstDefectId = computed(() => defectItemGroups.value[0]?.items[0]?.id ?? null)

  async function loadMachines(): Promise<void> {
    loadingMachines.value = true
    try {
      machines.value = await fetchWeldingMesMachines()
      if (form.value.weldingMachineId != null && !machines.value.some((m) => m.id === form.value.weldingMachineId)) {
        form.value.weldingMachineId = null
        form.value.weldingMachineName = ''
      }
    } catch (e) {
      console.error(e)
      machines.value = []
      ElMessage.error('溶接設備一覧の取得に失敗しました')
    } finally {
      loadingMachines.value = false
    }
  }

  async function loadProducts(): Promise<void> {
    const machineId = form.value.weldingMachineId
    if (machineId == null) {
      products.value = []
      return
    }
    loadingProducts.value = true
    try {
      const mesProducts = await fetchWeldingMesProducts(machineId)
      const masterRes = await getProductList({ pageSize: 9999, status: 'active' })
      const masterList = masterRes?.data?.list ?? masterRes?.list ?? []
      const upbMap = new Map<string, number>()
      for (const p of masterList) {
        const cd = (p.product_cd ?? '').trim()
        if (cd) upbMap.set(cd, Math.max(0, Number(p.unit_per_box) || 0))
      }
      products.value = mesProducts.map((p) => ({
        product_code: p.product_code,
        product_name: p.product_name,
        unit_per_box: upbMap.get(p.product_code) ?? 0,
      }))
    } catch (e) {
      console.error(e)
      products.value = []
      ElMessage.error('製品一覧の取得に失敗しました')
    } finally {
      loadingProducts.value = false
    }
  }

  async function loadOperators(): Promise<void> {
    loadingOperators.value = true
    try {
      operators.value = await fetchWeldingSectionOperators()
      const allowed = new Set(operators.value.map((u) => u.id))
      if (form.value.operatorUserId != null && !allowed.has(form.value.operatorUserId)) {
        form.value.operatorUserId = null
      }
      if (operatorFilterId.value != null && !allowed.has(operatorFilterId.value)) {
        operatorFilterId.value = null
      }
    } catch (e) {
      console.error(e)
      operators.value = []
      ElMessage.error('溶接作業者一覧の取得に失敗しました')
    } finally {
      loadingOperators.value = false
    }
  }

  async function loadDefectItems(): Promise<void> {
    loadingDefectItems.value = true
    try {
      defectItems.value = await loadMesDefectItemsForProcess(WELDING_DEFECT_DETECTION_PROCESS_CD)
    } catch (e) {
      console.error(e)
      ElMessage.error('不良項目の取得に失敗しました')
    } finally {
      loadingDefectItems.value = false
    }
  }

  async function loadRows(): Promise<void> {
    const day = productionDay.value.trim().slice(0, 10)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      ElMessage.warning('生産日を選択してください')
      return
    }
    loading.value = true
    try {
      const res = await fetchWeldingManagementList({ production_day: day, limit: 2000 })
      rows.value = (res.data ?? []).filter((r): r is WeldingMgmtRow => r.id != null)
    } catch (e: unknown) {
      console.error(e)
      const err = e as { response?: { data?: { detail?: string; message?: string } }; message?: string }
      ElMessage.error(
        err?.response?.data?.detail ?? err?.response?.data?.message ?? err?.message ?? '一覧の取得に失敗しました',
      )
    } finally {
      loading.value = false
    }
  }

  function onProductChange(code: string): void {
    const hit = products.value.find((p) => p.product_code.trim() === code.trim())
    form.value.productName = hit?.product_name?.trim() || code.trim()
    form.value.boxQty = null
    form.value.pieceQty = null
    form.value.qtyInputSource = null
  }

  function onMachineChange(id: number | null): void {
    const hit = machines.value.find((m) => m.id === id)
    form.value.weldingMachineId = id
    form.value.weldingMachineName = hit?.machine_name ?? ''
  }

  function onBoxQtyChange(val: number | undefined | null): void {
    if (syncingQty) return
    syncingQty = true
    form.value.qtyInputSource = 'box'
    const box = val == null || !Number.isFinite(val) ? null : Math.max(0, Math.round(val))
    form.value.boxQty = box
    const upb = unitPerBox.value
    if (box != null && upb > 0) {
      form.value.pieceQty = pieceQtyFromBoxes(box, upb)
    } else if (box == null) {
      form.value.pieceQty = null
    }
    syncingQty = false
  }

  function onPieceQtyChange(val: number | undefined | null): void {
    if (syncingQty) return
    syncingQty = true
    form.value.qtyInputSource = 'piece'
    const piece = val == null || !Number.isFinite(val) ? null : Math.max(0, Math.round(val))
    form.value.pieceQty = piece
    const upb = unitPerBox.value
    if (piece != null && upb > 0) {
      form.value.boxQty = boxQtyFromPieces(piece, upb)
    } else if (piece == null) {
      form.value.boxQty = null
    }
    syncingQty = false
  }

  function onBoxQtyInput(raw: string | undefined | null): void {
    onBoxQtyChange(parseQtyInput(raw))
  }

  function onPieceQtyInput(raw: string | undefined | null): void {
    onPieceQtyChange(parseQtyInput(raw))
  }

  function onProductionDayChange(day: string): void {
    productionDay.value = day
    form.value.productionDay = day
    void loadRows()
  }

  function shiftProductionDay(delta: number): void {
    const current = form.value.productionDay.trim().slice(0, 10)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(current)) {
      onProductionDayChange(getJSTToday())
      return
    }
    onProductionDayChange(shiftDateYmdJST(current, delta))
  }

  function goProductionDayToday(): void {
    onProductionDayChange(getJSTToday())
  }

  function resetForm(options?: { preserveOperator?: boolean; preserveMachine?: boolean }): void {
    editingRowId.value = null
    const operatorId = options?.preserveOperator ? form.value.operatorUserId : null
    const machineId = options?.preserveMachine ? form.value.weldingMachineId : null
    const machineName = options?.preserveMachine ? form.value.weldingMachineName : ''
    form.value = emptyForm(productionDay.value, operatorId)
    form.value.weldingMachineId = machineId
    form.value.weldingMachineName = machineName
    syncTimeTextsFromForm()
    if (machineId != null) void loadProducts()
  }

  function loadRowIntoForm(row: WeldingMgmtRow): void {
    if (!guardMesOperation(canEdit)) return
    if (!canEditRow(row)) {
      ElMessage.warning('MES 生産中の行は手動編集できません')
      return
    }
    editingRowId.value = row.id
    const day = String(row.production_day ?? productionDay.value).slice(0, 10)
    productionDay.value = day

    const machineName = (row.welding_machine ?? '').trim()
    const machineHit = machines.value.find((m) => m.machine_name === machineName)

    const breakMin =
      row.mes_break_sec != null && Number.isFinite(Number(row.mes_break_sec))
        ? secToMin(row.mes_break_sec)
        : 0
    const stopMin =
      row.mes_stop_sec != null && Number.isFinite(Number(row.mes_stop_sec))
        ? secToMin(row.mes_stop_sec)
        : secToMin(row.mes_paused_accum_sec) - breakMin

    const productCd = (row.product_cd ?? '').trim()
    const pieceQty =
      row.actual_production_quantity != null && Number.isFinite(Number(row.actual_production_quantity))
        ? Math.round(Number(row.actual_production_quantity))
        : null
    const upb = resolveUnitPerBox(productCd, products.value)
    const boxQty =
      pieceQty != null && upb > 0 ? boxQtyFromPieces(pieceQty, upb) : pieceQty != null ? null : null

    form.value = {
      productionDay: day,
      productionSequence:
        row.production_sequence != null && Number.isFinite(Number(row.production_sequence))
          ? Math.round(Number(row.production_sequence))
          : null,
      weldingMachineId: machineHit?.id ?? null,
      weldingMachineName: machineName,
      productCd,
      productName: (row.product_name ?? '').trim(),
      operatorUserId: rowOperatorId(row),
      boxQty,
      pieceQty,
      qtyInputSource: pieceQty != null ? 'piece' : null,
      defects: parseDefectsFromRow(row.mes_defect_by_item),
      registrationNote: (row.manual_registration_note ?? '').trim(),
      startedAt: timeOnlyFromDateTime(row.mes_production_started_at),
      endedAt: timeOnlyFromDateTime(row.mes_production_ended_at),
      breakMin: Math.max(0, breakMin),
      stopMin: Math.max(0, stopMin),
    }
    syncTimeTextsFromForm()
    void loadProducts()
  }

  async function submitForm(): Promise<void> {
    if (!guardMesOperation(canSave)) return
    const uid = loggedInUserId.value
    if (uid == null) {
      ElMessage.warning('ログイン後に登録してください')
      return
    }

    const draft = form.value
    const day = draft.productionDay.trim().slice(0, 10)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      ElMessage.warning('① 生産日を選択してください')
      return
    }
    if (!draft.weldingMachineName.trim()) {
      ElMessage.warning('② 溶接設備を選択してください')
      return
    }
    if (!draft.operatorUserId || draft.operatorUserId <= 0) {
      ElMessage.warning('③ 溶接作業者を選択してください')
      return
    }
    if (!isEdit.value && !draft.productCd.trim()) {
      ElMessage.warning('④ 製品名を選択してください')
      return
    }
    if (draft.pieceQty == null || !Number.isFinite(draft.pieceQty) || draft.pieceQty < 0) {
      ElMessage.warning('⑤ 生産数（本数）を入力してください')
      return
    }

    const { started, ended } = resolveProductionEndDateTime(day, draft.startedAt, draft.endedAt)
    const ws = started?.getTime()
    const we = ended?.getTime()
    if (ws == null || !Number.isFinite(ws) || we == null || !Number.isFinite(we)) {
      ElMessage.warning('⑥ 生産開始・終了時刻を入力してください')
      return
    }

    const breakMin = Math.max(0, Math.round(draft.breakMin))
    const stopMin = Math.max(0, Math.round(draft.stopMin))
    const pauseMin = breakMin + stopMin
    const shiftMin = Math.round((we - ws) / 60000)
    if (pauseMin > shiftMin) {
      ElMessage.warning('休憩＋停止時間が生産時間を超えています')
      return
    }

    const breakSec = breakMin * 60
    const stopSec = stopMin * 60
    const pauseSec = breakSec + stopSec
    const netSec = Math.max(0, Math.round((we - ws) / 1000 - pauseSec))

    const pieceQty = Math.max(0, Math.round(draft.pieceQty))
    try {
      await confirmWeldingPieceQty({
        pieceQty,
        productName: draft.productName.trim(),
        productCd: draft.productCd.trim(),
        isEdit: isEdit.value,
      })
    } catch {
      return
    }

    saving.value = true
    try {
      let rowId = editingRowId.value
      if (rowId == null) {
        const code = draft.productCd.trim()
        const createRes = await createWeldingManagement({
          production_day: day,
          product_cd: code,
          product_name: draft.productName.trim() || code,
          welding_machine: draft.weldingMachineName.trim(),
          mes_operator_user_id: draft.operatorUserId,
          manual_registration_note: draft.registrationNote.trim() || null,
          manual_registration: true,
        })
        rowId = createRes.data?.id ?? null
        if (rowId == null) {
          ElMessage.error(createRes.message ?? '登録に失敗しました')
          return
        }
      }

      const defects = mergeDefects(draft.defects)
      const body: PatchWeldingManagementBody = {
        production_day: day,
        welding_machine: draft.weldingMachineName.trim(),
        mes_operator_user_id: draft.operatorUserId,
        production_completed_check: true,
        manual_registration: true,
        manual_registration_note: draft.registrationNote.trim() || null,
        mes_defect_by_item: defects,
        actual_production_quantity: pieceQty,
        mes_production_started_at: new Date(ws).toISOString(),
        mes_production_ended_at: new Date(we).toISOString(),
        mes_break_sec: breakSec,
        mes_stop_sec: stopSec,
        mes_paused_accum_sec: pauseSec,
        mes_net_production_sec: netSec,
        mes_production_is_paused: 0,
      }
      if (draft.productionSequence != null && Number.isFinite(draft.productionSequence)) {
        body.production_sequence = Math.max(0, Math.round(draft.productionSequence))
      }

      const patchRes = await patchWeldingManagement(rowId, body)
      if (patchRes.success === false) {
        ElMessage.error(patchRes.message ?? '保存に失敗しました')
        return
      }

      productionDay.value = day
      ElMessage.success(isEdit.value ? '更新しました' : '登録しました')
      resetForm({ preserveOperator: true, preserveMachine: true })
      await loadRows()
    } catch (e: unknown) {
      console.error(e)
      const err = e as { response?: { data?: { detail?: string; message?: string } }; message?: string }
      ElMessage.error(
        err?.response?.data?.detail ?? err?.response?.data?.message ?? err?.message ?? '保存に失敗しました',
      )
    } finally {
      saving.value = false
    }
  }

  function formatDateTime(val: string | null | undefined): string {
    if (!val) return '—'
    return formatDateTimeJST(val, 'ja', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  function formatBreakMin(row: WeldingManagementListRow): string {
    const br = secToMin(row.mes_break_sec)
    return br > 0 ? `${br}分` : '—'
  }

  function formatStopMin(row: WeldingManagementListRow): string {
    const st = secToMin(row.mes_stop_sec)
    return st > 0 ? `${st}分` : '—'
  }

  async function deleteRow(row: WeldingMgmtRow): Promise<void> {
    if (!guardMesOperation(canDelete)) return
    const productLabel = (row.product_name ?? row.product_cd ?? '').trim() || '—'
    const operator = operatorLabel(row.mes_operator_user_id)
    const machine = (row.welding_machine ?? '').trim() || '—'
    const warnings: string[] = []
    if (isRowMesInProgress(row)) warnings.push('MES生産中のデータです')
    const src = resolveWeldingDataSource(row)
    if (src === 'excel') warnings.push('Excel 取込データです')
    else if (src === 'csv') warnings.push('CSV 取込データです')
    const warningBlock = warnings.length > 0 ? `\n\n※ ${warnings.join(' / ')}` : ''
    try {
      await ElMessageBox.confirm(
        `溶接設備「${machine}」・作業者「${operator}」・製品「${productLabel}」の登録を削除しますか？${warningBlock}`,
        '削除確認',
        {
          type: 'warning',
          confirmButtonText: '削除',
          cancelButtonText: 'キャンセル',
        },
      )
    } catch {
      return
    }

    deletingRowId.value = row.id
    try {
      const res = await deleteWeldingManagement(row.id)
      if (res.success === false) {
        ElMessage.error(res.message ?? '削除に失敗しました')
        return
      }
      if (editingRowId.value === row.id) resetForm()
      ElMessage.success('削除しました')
      await loadRows()
    } catch (e: unknown) {
      console.error(e)
      const err = e as { response?: { data?: { detail?: string; message?: string } }; message?: string }
      ElMessage.error(
        err?.response?.data?.detail ?? err?.response?.data?.message ?? err?.message ?? '削除に失敗しました',
      )
    } finally {
      deletingRowId.value = null
    }
  }

  async function init(): Promise<void> {
    form.value = emptyForm(productionDay.value, null)
    syncTimeTextsFromForm()
    await Promise.all([loadMachines(), loadOperators(), loadDefectItems()])
    await loadRows()
  }

  return {
    productionDay,
    operatorFilterId,
    machineFilterName,
    loading,
    saving,
    deletingRowId,
    rows,
    filteredRows,
    machines,
    loadingMachines,
    products,
    loadingProducts,
    defectItemGroups,
    loadingDefectItems,
    operators,
    loadingOperators,
    editingRowId,
    form,
    isEdit,
    canSave,
    canEdit,
    canDelete,
    timeSummary,
    formatMinutesLabel,
    operatorLabel,
    defectItemLabel,
    dataSourceLabel,
    dataSourceTagType,
    canEditRow,
    canDeleteRow,
    isRowMesInProgress,
    defectCount,
    bumpDefect,
    onDefectQtyInput,
    firstDefectId,
    loadRows,
    loadMachines,
    onProductChange,
    onMachineChange,
    formatQtyInputValue,
    onPieceQtyInput,
    startedAtText,
    endedAtText,
    onStartedAtInput,
    onEndedAtInput,
    onStartedAtBlur,
    onEndedAtBlur,
    onProductionDayChange,
    shiftProductionDay,
    goProductionDayToday,
    resetForm,
    loadRowIntoForm,
    deleteRow,
    submitForm,
    formatDateTime,
    formatBreakMin,
    formatStopMin,
    formatEfficiencyRate,
    isEfficiencyRateOutOfRange,
    init,
  }
}

export { formatQtyInputValue, formatTimeInputValue }
