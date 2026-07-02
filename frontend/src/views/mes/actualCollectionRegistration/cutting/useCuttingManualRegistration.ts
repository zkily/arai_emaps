import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createCuttingProductionIndicatorManual,
  deleteCuttingProductionIndicator,
  fetchCuttingProductionIndicatorList,
  fetchCuttingProductionIndicatorLines,
  patchCuttingProductionIndicator,
  type CuttingProductionIndicatorRow,
} from '@/api/cuttingProductionIndicator'
import { getProductList } from '@/api/master/productMaster'
import { formatDateTimeJST, getJSTToday, shiftDateYmdJST } from '@/utils/dateFormat'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import { guardMesOperation } from '@/utils/mesOperationGuard'
import { filterCuttingSelectableProducts } from '@/views/mes/shared/cuttingProductFilter'
import {
  buildRegistrationListSummary,
  formatRegistrationListEfficiency,
  formatRegistrationListQty,
} from '@/views/mes/actualCollectionRegistration/shared/registrationListSummary'
import {
  formatQtyInputValue,
  formatTimeInputValue,
} from '../inspection/useInspectionManualRegistration'

export type CuttingIndicatorRow = CuttingProductionIndicatorRow

export interface CuttingRegistrationProduct {
  product_code: string
  product_name: string
}

export interface ManualRegistrationForm {
  productionDay: string
  productionLine: string
  productCd: string
  productName: string
  plannedQty: number | null
  actualQty: number | null
  quantityVariance: number | null
  varianceManual: boolean
  registrationNote: string
  startedAt: string | null
  endedAt: string | null
  breakMin: number
  stopMin: number
}

function emptyForm(day: string, line: string): ManualRegistrationForm {
  return {
    productionDay: day,
    productionLine: line,
    productCd: '',
    productName: '',
    plannedQty: null,
    actualQty: null,
    quantityVariance: null,
    varianceManual: false,
    registrationNote: '',
    startedAt: null,
    endedAt: null,
    breakMin: 0,
    stopMin: 0,
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

function resolveVariance(planned: number | null, actual: number | null, manual: number | null): number | null {
  if (manual != null && Number.isFinite(manual)) return Math.round(manual)
  if (planned == null || actual == null) return null
  return Math.round(planned - actual)
}

function resolveDataSource(row: CuttingIndicatorRow): 'manual' | 'excel' | 'csv' {
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

export function useCuttingManualRegistration() {
  const { canCreate, canEdit, canDelete } = useMesOperationPermission()

  const productionDay = ref(getJSTToday())
  const lineFilterName = ref('')
  const loading = ref(false)
  const saving = ref(false)
  const deletingRowId = ref<number | null>(null)
  const rows = ref<CuttingIndicatorRow[]>([])
  const products = ref<CuttingRegistrationProduct[]>([])
  const loadingProducts = ref(false)
  const lineOptions = ref<{ line_name: string }[]>([])
  const loadingLines = ref(false)

  const editingRowId = ref<number | null>(null)
  const form = ref<ManualRegistrationForm>(emptyForm(getJSTToday(), ''))
  const startedAtText = ref('')
  const endedAtText = ref('')

  const isEdit = computed(() => editingRowId.value != null)
  const canSave = computed(() => (isEdit.value ? canEdit.value : canCreate.value))

  const filteredRows = computed(() => {
    const line = lineFilterName.value.trim()
    if (!line) return rows.value
    return rows.value.filter((r) => (r.production_line || '').trim() === line)
  })

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

  const computedVariance = computed(() => {
    if (form.value.varianceManual) return form.value.quantityVariance
    return resolveVariance(form.value.plannedQty, form.value.actualQty, null)
  })

  const timeSummary = computed(() => {
    const day = form.value.productionDay.trim().slice(0, 10)
    const { started, ended, endsNextDay } = resolveProductionEndDateTime(
      day,
      form.value.startedAt,
      form.value.endedAt,
    )
    if (!started || !ended) {
      return { shiftMin: null, workMin: null, breakMin: form.value.breakMin, stopMin: form.value.stopMin, endsNextDay: false }
    }
    const shiftMin = Math.round((ended.getTime() - started.getTime()) / 60000)
    const pauseMin = Math.max(0, form.value.breakMin) + Math.max(0, form.value.stopMin)
    const workMin = Math.max(0, shiftMin - pauseMin)
    return {
      shiftMin,
      workMin,
      breakMin: form.value.breakMin,
      stopMin: form.value.stopMin,
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

  function dataSourceLabel(row: CuttingIndicatorRow): string {
    const src = resolveDataSource(row)
    if (src === 'manual') return '手動'
    if (src === 'csv') return 'CSV'
    return 'Excel'
  }

  function dataSourceTagType(row: CuttingIndicatorRow): 'success' | 'info' | 'warning' {
    const src = resolveDataSource(row)
    if (src === 'manual') return 'success'
    if (src === 'csv') return 'warning'
    return 'info'
  }

  function canEditRow(row: CuttingIndicatorRow): boolean {
    return canEdit.value && resolveDataSource(row) === 'manual'
  }

  function canDeleteRow(row: CuttingIndicatorRow): boolean {
    return canDelete.value && resolveDataSource(row) === 'manual'
  }

  function isRowMesInProgress(_row: CuttingIndicatorRow): boolean {
    return false
  }

  function formatEfficiencyRate(row: CuttingIndicatorRow): string {
    const rate = row.efficiency_rate
    if (rate == null || !Number.isFinite(Number(rate))) return '—'
    return String(Math.round(Number(rate)))
  }

  function isEfficiencyRateOutOfRange(row: CuttingIndicatorRow): boolean {
    const rate = Number(row.efficiency_rate ?? 0)
    if (!Number.isFinite(rate) || rate <= 0) return false
    return rate < 80 || rate > 300
  }

  function formatBreakMin(row: CuttingIndicatorRow): string {
    const m = hoursToMin(row.break_hours)
    return m > 0 ? `${m}分` : '—'
  }

  function formatStopMin(row: CuttingIndicatorRow): string {
    const m = hoursToMin(row.setup_hours)
    return m > 0 ? `${m}分` : '—'
  }

  function formatWorkHours(row: CuttingIndicatorRow): string {
    const h = Number(row.work_hours ?? 0)
    if (!Number.isFinite(h) || h <= 0) return '—'
    return `${Math.round(h * 10) / 10}h`
  }

  async function loadLines(): Promise<void> {
    const day = productionDay.value.trim().slice(0, 10)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      lineOptions.value = []
      return
    }
    loadingLines.value = true
    try {
      const res = await fetchCuttingProductionIndicatorLines({ start_date: day, end_date: day })
      const fromApi = res.data ?? []
      const fromRows = rows.value.map((r) => (r.production_line || '').trim()).filter(Boolean)
      const set = new Set<string>([...fromApi.map((l) => l.line_name), ...fromRows])
      lineOptions.value = [...set].sort().map((line_name) => ({ line_name }))
    } catch {
      lineOptions.value = []
    } finally {
      loadingLines.value = false
    }
  }

  async function loadProducts(): Promise<void> {
    loadingProducts.value = true
    try {
      const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
      const list = res?.data?.list ?? res?.list ?? []
      products.value = filterCuttingSelectableProducts(list).map((p) => ({
        product_code: p.product_cd,
        product_name: p.product_name || p.product_cd,
      }))
    } catch {
      products.value = []
    } finally {
      loadingProducts.value = false
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
      const res = await fetchCuttingProductionIndicatorList({ production_day: day, limit: 2000 })
      rows.value = (res.data ?? []).filter((r): r is CuttingIndicatorRow => r.id != null)
      await loadLines()
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
  }

  function onPlannedQtyInput(raw: string | undefined | null): void {
    form.value.plannedQty = parseQtyInput(raw)
    if (!form.value.varianceManual) {
      form.value.quantityVariance = resolveVariance(form.value.plannedQty, form.value.actualQty, null)
    }
  }

  function onActualQtyInput(raw: string | undefined | null): void {
    form.value.actualQty = parseQtyInput(raw)
    if (!form.value.varianceManual) {
      form.value.quantityVariance = resolveVariance(form.value.plannedQty, form.value.actualQty, null)
    }
  }

  function onVarianceQtyInput(raw: string | undefined | null): void {
    form.value.varianceManual = true
    form.value.quantityVariance = parseQtyInput(raw)
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

  function resetForm(options?: { preserveLine?: boolean }): void {
    editingRowId.value = null
    const line = options?.preserveLine ? form.value.productionLine : ''
    form.value = emptyForm(productionDay.value, line)
    syncTimeTextsFromForm()
  }

  function loadRowIntoForm(row: CuttingIndicatorRow): void {
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
      productionLine: (row.production_line || '').trim(),
      productCd: (row.product_cd || '').trim(),
      productName: (row.product_name || '').trim(),
      plannedQty: row.planned_quantity ?? null,
      actualQty: row.actual_quantity ?? null,
      quantityVariance: row.quantity_variance ?? null,
      varianceManual: row.quantity_variance != null,
      registrationNote: (row.remarks || '').trim(),
      startedAt: null,
      endedAt: null,
      breakMin: hoursToMin(row.break_hours),
      stopMin: hoursToMin(row.setup_hours),
    }
    const shiftMin = hoursToMin(row.shift_hours)
    if (shiftMin > 0) {
      form.value.startedAt = '08:00:00'
      const endMin = Math.max(0, shiftMin + hoursToMin(row.break_hours) + hoursToMin(row.setup_hours))
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
    if (!draft.productionLine.trim()) {
      ElMessage.warning('② ラインを選択してください')
      return
    }
    if (!isEdit.value && !draft.productCd.trim()) {
      ElMessage.warning('③ 製品名を選択してください')
      return
    }
    if (draft.actualQty == null || !Number.isFinite(draft.actualQty) || draft.actualQty < 0) {
      ElMessage.warning('④ 生産数を入力してください')
      return
    }

    const { started, ended } = resolveProductionEndDateTime(day, draft.startedAt, draft.endedAt)
    const ws = started?.getTime()
    const we = ended?.getTime()
    if (ws == null || !Number.isFinite(ws) || we == null || !Number.isFinite(we)) {
      ElMessage.warning('⑤ 生産開始・終了時刻を入力してください')
      return
    }

    const breakMin = Math.max(0, Math.round(draft.breakMin))
    const stopMin = Math.max(0, Math.round(draft.stopMin))
    const shiftMin = Math.round((we - ws) / 60000)
    if (breakMin + stopMin > shiftMin) {
      ElMessage.warning('休憩＋停止時間が生産時間を超えています')
      return
    }

    const body = {
      production_day: day,
      production_line: draft.productionLine.trim(),
      product_cd: draft.productCd.trim(),
      product_name: draft.productName.trim() || draft.productCd.trim(),
      planned_quantity: draft.plannedQty,
      actual_quantity: Math.max(0, Math.round(draft.actualQty)),
      quantity_variance: computedVariance.value,
      shift_hours: minToHours(shiftMin),
      break_hours: minToHours(breakMin),
      setup_hours: minToHours(stopMin),
      remarks: draft.registrationNote.trim() || null,
    }

    saving.value = true
    try {
      if (editingRowId.value != null) {
        const res = await patchCuttingProductionIndicator(editingRowId.value, body)
        if (res.success === false) {
          ElMessage.error(res.message ?? '更新に失敗しました')
          return
        }
      } else {
        const res = await createCuttingProductionIndicatorManual(body)
        if (res.success === false || !res.data?.id) {
          ElMessage.error(res.message ?? '登録に失敗しました')
          return
        }
      }
      productionDay.value = day
      ElMessage.success(isEdit.value ? '更新しました' : '登録しました')
      resetForm({ preserveLine: true })
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

  async function deleteRow(row: CuttingIndicatorRow): Promise<void> {
    if (!guardMesOperation(canDelete)) return
    if (!canDeleteRow(row)) {
      ElMessage.warning('Excel/CSV 取込データは削除できません')
      return
    }
    const productLabel = (row.product_name ?? row.product_cd ?? '').trim() || '—'
    const line = lineLabel(row.production_line)
    try {
      await ElMessageBox.confirm(
        `ライン「${line}」・製品「${productLabel}」の登録を削除しますか？`,
        '削除確認',
        { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' },
      )
    } catch {
      return
    }
    deletingRowId.value = row.id
    try {
      const res = await deleteCuttingProductionIndicator(row.id)
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
    form.value = emptyForm(productionDay.value, '')
    syncTimeTextsFromForm()
    await loadProducts()
    await loadRows()
  }

  return {
    productionDay,
    lineFilterName,
    loading,
    saving,
    deletingRowId,
    filteredRows,
    listSummaryQtyLabel,
    listSummaryEfficiencyLabel,
    products,
    loadingProducts,
    lineOptions,
    loadingLines,
    editingRowId,
    form,
    isEdit,
    canSave,
    canEdit,
    canDelete,
    timeSummary,
    formatMinutesLabel,
    lineLabel,
    computedVariance,
    loadRows,
    onProductChange,
    formatQtyInputValue,
    onPlannedQtyInput,
    onActualQtyInput,
    onVarianceQtyInput,
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
    formatBreakMin,
    formatStopMin,
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
