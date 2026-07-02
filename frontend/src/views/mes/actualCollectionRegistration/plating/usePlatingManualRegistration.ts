import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPlatingProductionIndicatorManual,
  deletePlatingProductionIndicator,
  fetchPlatingProductionIndicatorList,
  patchPlatingProductionIndicator,
  type PlatingProductionIndicatorRow,
} from '@/api/platingProductionIndicator'
import { formatDateTimeJST, getJSTToday, shiftDateYmdJST } from '@/utils/dateFormat'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import { guardMesOperation } from '@/utils/mesOperationGuard'
import {
  buildRegistrationListSummary,
  formatRegistrationListEfficiency,
  formatRegistrationListQty,
} from '@/views/mes/actualCollectionRegistration/shared/registrationListSummary'
import {
  formatQtyInputValue,
  formatTimeInputValue,
} from '../inspection/useInspectionManualRegistration'

export type PlatingIndicatorRow = PlatingProductionIndicatorRow

export interface ManualRegistrationForm {
  productionDay: string
  plannedQty: number | null
  actualQty: number | null
  defectQty: number | null
  defectPlatingScratch: number | null
  defectMoyaKaburi: number | null
  defectNickel: number | null
  defectContact: number | null
  defectOther: number | null
  registrationNote: string
  startedAt: string | null
  endedAt: string | null
  maintenanceMin: number
  troubleMin: number
  chocoMin: number
  plannedStopMin: number
}

function emptyForm(day: string): ManualRegistrationForm {
  return {
    productionDay: day,
    plannedQty: null,
    actualQty: null,
    defectQty: null,
    defectPlatingScratch: null,
    defectMoyaKaburi: null,
    defectNickel: null,
    defectContact: null,
    defectOther: null,
    registrationNote: '',
    startedAt: null,
    endedAt: null,
    maintenanceMin: 0,
    troubleMin: 0,
    chocoMin: 0,
    plannedStopMin: 0,
  }
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

function combineProductionDayAndTime(day: string, time: string | null | undefined): Date | null {
  const dayStr = day.trim().slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dayStr) || !time) return null
  const match = time.trim().match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/)
  if (!match) return null
  const [y, mo, d] = dayStr.split('-').map(Number)
  const hours = Number(match[1])
  const minutes = Number(match[2])
  const seconds = Number(match[3] ?? 0)
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

function hoursToMin(hours: number | null | undefined): number {
  const h = Number(hours ?? 0)
  if (!Number.isFinite(h) || h <= 0) return 0
  return Math.round(h * 60)
}

function minToHours(min: number): number {
  return Math.round((Math.max(0, min) / 60) * 1000) / 1000
}

function formatMinutesLabel(totalMin: number): string {
  const m = Math.max(0, Math.round(totalMin))
  const h = Math.floor(m / 60)
  const min = m % 60
  if (h <= 0) return `${min}分`
  return `${h}時間${min}分`
}

function resolveDataSource(row: PlatingIndicatorRow): 'manual' | 'excel' | 'csv' {
  const src = (row.data_source || '').trim().toLowerCase()
  if (src === 'manual') return 'manual'
  if (src === 'csv') return 'csv'
  return 'excel'
}

function workHoursToSec(hours: number | null | undefined): number {
  const h = Number(hours ?? 0)
  if (!Number.isFinite(h) || h <= 0) return 0
  return Math.round(h * 3600)
}

export function usePlatingManualRegistration() {
  const { canCreate, canEdit, canDelete } = useMesOperationPermission()

  const productionDay = ref(getJSTToday())
  const loading = ref(false)
  const saving = ref(false)
  const deletingRowId = ref<number | null>(null)
  const rows = ref<PlatingIndicatorRow[]>([])

  const editingRowId = ref<number | null>(null)
  const form = ref<ManualRegistrationForm>(emptyForm(getJSTToday()))
  const startedAtText = ref('')
  const endedAtText = ref('')

  const isEdit = computed(() => editingRowId.value != null)
  const canSave = computed(() => (isEdit.value ? canEdit.value : canCreate.value))

  const filteredRows = computed(() => rows.value)

  const listSummary = computed(() =>
    buildRegistrationListSummary(filteredRows.value, {
      getQty: (row) => Math.max(0, Number(row.actual_quantity ?? 0)),
      isInProgress: () => false,
      getNetSec: (row) => workHoursToSec(row.work_hours),
    }),
  )

  const listSummaryQtyLabel = computed(() =>
    formatRegistrationListQty(listSummary.value.totalProductionQty),
  )

  const listSummaryEfficiencyLabel = computed(() =>
    formatRegistrationListEfficiency(listSummary.value.avgEfficiencyPerHour, '本/時'),
  )

  const computedTotalQty = computed(() => Math.max(0, Math.round(Number(form.value.actualQty) || 0)))

  const timeSummary = computed(() => {
    const day = form.value.productionDay.trim().slice(0, 10)
    const { started, ended, endsNextDay } = resolveProductionEndDateTime(
      day,
      form.value.startedAt,
      form.value.endedAt,
    )
    if (!started || !ended) {
      return { shiftMin: null, workMin: null, maintenanceMin: form.value.maintenanceMin, troubleMin: form.value.troubleMin, chocoMin: form.value.chocoMin, plannedStopMin: form.value.plannedStopMin, endsNextDay: false }
    }
    const shiftMin = Math.round((ended.getTime() - started.getTime()) / 60000)
    const pauseMin = Math.max(0, form.value.maintenanceMin) + Math.max(0, form.value.troubleMin) + Math.max(0, form.value.chocoMin) + Math.max(0, form.value.plannedStopMin)
    const workMin = Math.max(0, shiftMin - pauseMin)
    return {
      shiftMin,
      workMin,
      maintenanceMin: form.value.maintenanceMin,
      troubleMin: form.value.troubleMin,
      chocoMin: form.value.chocoMin,
      plannedStopMin: form.value.plannedStopMin,
      endsNextDay,
    }
  })

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

  function lineLabel(name: string | null | undefined): string {
    return (name || '').trim() || '—'
  }

  function dataSourceLabel(row: PlatingIndicatorRow): string {
    const src = resolveDataSource(row)
    if (src === 'manual') return '手動'
    if (src === 'csv') return 'CSV'
    return 'Excel'
  }

  function dataSourceTagType(row: PlatingIndicatorRow): 'success' | 'info' | 'warning' {
    const src = resolveDataSource(row)
    if (src === 'manual') return 'success'
    if (src === 'csv') return 'warning'
    return 'info'
  }

  function canEditRow(row: PlatingIndicatorRow): boolean {
    return canEdit.value && resolveDataSource(row) === 'manual'
  }

  function canDeleteRow(row: PlatingIndicatorRow): boolean {
    return canDelete.value && resolveDataSource(row) === 'manual'
  }

  function isRowMesInProgress(_row: PlatingIndicatorRow): boolean {
    return false
  }

  function formatEfficiencyRate(row: PlatingIndicatorRow): string {
    const rate = row.efficiency_rate
    if (rate == null || !Number.isFinite(Number(rate))) return '—'
    return String(Math.round(Number(rate)))
  }

  function isEfficiencyRateOutOfRange(row: PlatingIndicatorRow): boolean {
    const rate = Number(row.efficiency_rate ?? 0)
    if (!Number.isFinite(rate) || rate <= 0) return false
    return rate < 80 || rate > 300
  }

  function formatMaintenanceMin(row: PlatingIndicatorRow): string {
    const m = hoursToMin(row.maintenance_hours)
    return m > 0 ? `${m}分` : '—'
  }

  function formatTroubleMin(row: PlatingIndicatorRow): string {
    const m = hoursToMin(row.trouble_hours)
    return m > 0 ? `${m}分` : '—'
  }

  function formatWorkHours(row: PlatingIndicatorRow): string {
    const h = Number(row.work_hours ?? 0)
    if (!Number.isFinite(h) || h <= 0) return '—'
    return `${Math.round(h * 10) / 10}h`
  }

  async function loadRows(): Promise<void> {
    const day = productionDay.value.trim().slice(0, 10)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      ElMessage.warning('生産日を選択してください')
      return
    }
    loading.value = true
    try {
      const res = await fetchPlatingProductionIndicatorList({ production_day: day, limit: 2000 })
      rows.value = (res.data ?? []).filter((r): r is PlatingIndicatorRow => r.id != null)
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

  function onPlannedQtyInput(raw: string | undefined | null): void {
    form.value.plannedQty = parseQtyInput(raw)
  }

  function onActualQtyInput(raw: string | undefined | null): void {
    form.value.actualQty = parseQtyInput(raw)
  }

  function onDefectQtyInput(raw: string | undefined | null): void {
    form.value.defectQty = parseQtyInput(raw)
  }

  function onDefectPlatingScratchInput(raw: string | undefined | null): void {
    form.value.defectPlatingScratch = parseQtyInput(raw)
  }

  function onDefectMoyaKaburiInput(raw: string | undefined | null): void {
    form.value.defectMoyaKaburi = parseQtyInput(raw)
  }

  function onDefectNickelInput(raw: string | undefined | null): void {
    form.value.defectNickel = parseQtyInput(raw)
  }


  function onDefectContactInput(raw: string | undefined | null): void {
    form.value.defectContact = parseQtyInput(raw)
  }

  function onDefectOtherInput(raw: string | undefined | null): void {
    form.value.defectOther = parseQtyInput(raw)
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

  function resetForm(): void {
    editingRowId.value = null
    form.value = emptyForm(productionDay.value)
    syncTimeTextsFromForm()
  }

  function loadRowIntoForm(row: PlatingIndicatorRow): void {
    if (!guardMesOperation(canEdit)) return
    if (!canEditRow(row)) {
      ElMessage.warning('Excel/CSV 取込データは手動編集できません')
      return
    }
    editingRowId.value = row.id
    const day = String(row.production_day ?? productionDay.value).slice(0, 10)
    productionDay.value = day
    form.value = {
      productionDay: day,
      plannedQty: row.planned_quantity ?? null,
      actualQty: row.actual_quantity ?? null,
      defectQty: row.defect_quantity ?? null,
      defectPlatingScratch: row.defect_plating_scratch ?? null,
      defectMoyaKaburi: row.defect_moya_kaburi ?? null,
      defectNickel: row.defect_nickel ?? null,
      defectContact: row.defect_contact ?? null,
      defectOther: row.defect_other ?? null,
      registrationNote: (row.remarks || '').trim(),
      startedAt: null,
      endedAt: null,
      maintenanceMin: hoursToMin(row.maintenance_hours),
      troubleMin: hoursToMin(row.trouble_hours),
      chocoMin: hoursToMin(row.choco_stop_hours),
      plannedStopMin: hoursToMin(row.planned_stop_hours),
    }
    const shiftMin = hoursToMin(row.shift_hours)
    if (shiftMin > 0) {
      form.value.startedAt = '08:00:00'
      const lossMin =
        hoursToMin(row.maintenance_hours) +
        hoursToMin(row.trouble_hours) +
        hoursToMin(row.choco_stop_hours) +
        hoursToMin(row.planned_stop_hours)
      const endMin = Math.max(0, shiftMin + lossMin)
      const endH = Math.floor(endMin / 60) % 24
      const endM = endMin % 60
      form.value.endedAt = `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}:00`
    }
    syncTimeTextsFromForm()
  }

  async function submitForm(): Promise<void> {
    if (!guardMesOperation(canSave)) return

    const draft = form.value
    const day = draft.productionDay.trim().slice(0, 10)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      ElMessage.warning('① 生産日を選択してください')
      return
    }
    if (computedTotalQty.value <= 0) {
      ElMessage.warning('② 実績数を入力してください')
      return
    }

    const { started, ended } = resolveProductionEndDateTime(day, draft.startedAt, draft.endedAt)
    const ws = started?.getTime()
    const we = ended?.getTime()
    if (ws == null || !Number.isFinite(ws) || we == null || !Number.isFinite(we)) {
      ElMessage.warning('③ 生産開始・終了時刻を入力してください')
      return
    }

    const maintenanceMin = Math.max(0, Math.round(draft.maintenanceMin))
    const troubleMin = Math.max(0, Math.round(draft.troubleMin))
    const chocoMin = Math.max(0, Math.round(draft.chocoMin))
    const plannedStopMin = Math.max(0, Math.round(draft.plannedStopMin))
    const shiftMin = Math.round((we - ws) / 60000)
    const pauseMin = maintenanceMin + troubleMin + chocoMin + plannedStopMin
    if (pauseMin > shiftMin) {
      ElMessage.warning('停止時間合計が生産時間を超えています')
      return
    }

    const body = {
      production_day: day,
      planned_quantity: draft.plannedQty,
      actual_quantity: draft.actualQty,
      defect_quantity: draft.defectQty,
      defect_plating_scratch: draft.defectPlatingScratch,
      defect_moya_kaburi: draft.defectMoyaKaburi,
      defect_nickel: draft.defectNickel,
      defect_contact: draft.defectContact,
      defect_other: draft.defectOther,
      shift_hours: minToHours(shiftMin),
      maintenance_hours: minToHours(maintenanceMin),
      trouble_hours: minToHours(troubleMin),
      choco_stop_hours: minToHours(chocoMin),
      planned_stop_hours: minToHours(plannedStopMin),
      remarks: draft.registrationNote.trim() || null,
    }

    saving.value = true
    try {
      if (editingRowId.value != null) {
        const res = await patchPlatingProductionIndicator(editingRowId.value, body)
        if (res.success === false) {
          ElMessage.error(res.message ?? '更新に失敗しました')
          return
        }
      } else {
        const res = await createPlatingProductionIndicatorManual(body)
        if (res.success === false || !res.data?.id) {
          ElMessage.error(res.message ?? '登録に失敗しました')
          return
        }
      }
      productionDay.value = day
      ElMessage.success(isEdit.value ? '更新しました' : '登録しました')
      resetForm()
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

  async function deleteRow(row: PlatingIndicatorRow): Promise<void> {
    if (!guardMesOperation(canDelete)) return
    if (!canDeleteRow(row)) {
      ElMessage.warning('Excel/CSV 取込データは削除できません')
      return
    }
    const dayLabel = String(row.production_day ?? productionDay.value).slice(0, 10)
    try {
      await ElMessageBox.confirm(
        `生産日「${dayLabel}」の手動登録を削除しますか？`,
        '削除確認',
        { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' },
      )
    } catch {
      return
    }
    deletingRowId.value = row.id
    try {
      const res = await deletePlatingProductionIndicator(row.id)
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
    form.value = emptyForm(productionDay.value)
    syncTimeTextsFromForm()
    await loadRows()
  }

  return {
    productionDay,
    loading,
    saving,
    deletingRowId,
    filteredRows,
    listSummaryQtyLabel,
    listSummaryEfficiencyLabel,
    editingRowId,
    form,
    isEdit,
    canSave,
    canEdit,
    canDelete,
    timeSummary,
    formatMinutesLabel,
    computedTotalQty,
    loadRows,
    formatQtyInputValue,
    onPlannedQtyInput,
    onActualQtyInput,
    onDefectQtyInput,
    onDefectPlatingScratchInput,
    onDefectMoyaKaburiInput,
    onDefectNickelInput,
    onDefectContactInput,
    onDefectOtherInput,
    formatMaintenanceMin,
    formatTroubleMin,
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
    formatWorkHours,
    formatEfficiencyRate,
    isEfficiencyRateOutOfRange,
    dataSourceLabel,
    dataSourceTagType,
    canEditRow,
    canDeleteRow,
    isRowMesInProgress,
    init,
  }
}
