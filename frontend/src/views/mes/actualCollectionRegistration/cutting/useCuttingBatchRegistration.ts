import { computed, ref, watch, type ComputedRef, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchCuttingManagementList, type CuttingManagementListRow } from '@/api/cuttingManagement'
import {
  createCuttingProductionIndicatorManual,
  type CuttingProductionIndicatorRow,
} from '@/api/cuttingProductionIndicator'
import { guardMesOperation } from '@/utils/mesOperationGuard'
import { formatTimeInputValue } from '../inspection/useInspectionManualRegistration'
import {
  minToHours,
  parseTimeInput,
  resolveProductionEndDateTime,
  sanitizeTimeDraft,
  sumLossMin,
} from './useCuttingManualRegistration'

/** 切断指示（生産完了）から一括登録する行 */
export interface CuttingBatchRow {
  key: number
  line: string
  productCd: string
  productName: string
  plannedQty: number | null
  actualQty: number | null
  startedText: string
  endedText: string
  breakMin: number
  setupMin: number
  repairMin: number
  sawBladeMin: number
  stopMin: number
  remarks: string
  selected: boolean
  error: string
}

interface BatchOptions {
  productionDay: Ref<string>
  registeredRows: Ref<CuttingProductionIndicatorRow[]>
  canCreate: ComputedRef<boolean>
  onSaved: () => Promise<void>
}

/** MES 時刻（YYYY-MM-DDTHH:mm:ss）から HH:mm を取り出す */
function extractHm(value: string | null | undefined): string {
  const m = String(value ?? '').match(/[T\s](\d{2}):(\d{2})/)
  return m ? `${m[1]}:${m[2]}` : ''
}

function toNonNegInt(value: number | null | undefined): number {
  const n = Number(value ?? 0)
  return Number.isFinite(n) && n > 0 ? Math.round(n) : 0
}

function lineProductKey(line: string | null | undefined, productCd: string | null | undefined): string {
  return `${(line ?? '').trim()}|${(productCd ?? '').trim()}`
}

/** 計画数 = 切断指示の生産数 + 不良数 */
function resolvePlannedQty(src: CuttingManagementListRow): number | null {
  if (src.actual_production_quantity == null && src.defect_qty == null) return null
  return toNonNegInt(src.actual_production_quantity) + toNonNegInt(src.defect_qty)
}

function toBatchRow(src: CuttingManagementListRow): CuttingBatchRow {
  return {
    key: Number(src.id),
    line: (src.cutting_machine || src.production_line || '').trim(),
    productCd: (src.product_cd || '').trim(),
    productName: (src.product_name || src.product_cd || '').trim(),
    plannedQty: resolvePlannedQty(src),
    actualQty: src.actual_production_quantity ?? null,
    startedText: extractHm(src.mes_production_started_at),
    endedText: extractHm(src.mes_production_ended_at),
    breakMin: 0,
    setupMin: toNonNegInt(src.mes_setup_time_min),
    repairMin: toNonNegInt(src.mes_repair_min),
    sawBladeMin: toNonNegInt(src.mes_saw_blade_exchange_min),
    stopMin: 0,
    remarks: '',
    selected: false,
    error: '',
  }
}

export function useCuttingBatchRegistration(options: BatchOptions) {
  const { productionDay, registeredRows, canCreate, onSaved } = options

  const batchRows = ref<CuttingBatchRow[]>([])
  const batchLoading = ref(false)
  const batchSaving = ref(false)
  const batchLoadedDay = ref('')
  const batchLineFilter = ref('')

  /** 同一ライン・製品の登録件数ぶん、指示行を先頭から「登録済」とみなす */
  const registeredKeys = computed(() => {
    const remain = new Map<string, number>()
    for (const r of registeredRows.value) {
      const k = lineProductKey(r.production_line, r.product_cd)
      remain.set(k, (remain.get(k) ?? 0) + 1)
    }
    const out = new Set<number>()
    for (const row of batchRows.value) {
      const k = lineProductKey(row.line, row.productCd)
      const n = remain.get(k) ?? 0
      if (n > 0) {
        out.add(row.key)
        remain.set(k, n - 1)
      }
    }
    return out
  })

  watch(registeredKeys, (keys, prev) => {
    for (const r of batchRows.value) {
      if (keys.has(r.key) && !prev?.has(r.key)) r.selected = false
    }
  })

  const batchLineOptions = computed(() =>
    [...new Set(batchRows.value.map((r) => r.line).filter(Boolean))].sort(),
  )

  const visibleBatchRows = computed(() => {
    const line = (batchLineFilter.value ?? '').trim()
    if (!line) return batchRows.value
    return batchRows.value.filter((r) => r.line === line)
  })

  const selectedBatchRows = computed(() => visibleBatchRows.value.filter((r) => r.selected))

  const batchRegisteredCount = computed(
    () => visibleBatchRows.value.filter((r) => registeredKeys.value.has(r.key)).length,
  )

  const allVisibleSelected = computed(
    () => visibleBatchRows.value.length > 0 && visibleBatchRows.value.every((r) => r.selected),
  )

  const someVisibleSelected = computed(
    () => selectedBatchRows.value.length > 0 && !allVisibleSelected.value,
  )

  function isBatchRowRegistered(row: CuttingBatchRow): boolean {
    return registeredKeys.value.has(row.key)
  }

  function toggleAllVisible(checked: boolean | string | number): void {
    const on = Boolean(checked)
    for (const r of visibleBatchRows.value) r.selected = on
  }

  async function loadBatch(): Promise<void> {
    const day = productionDay.value.trim().slice(0, 10)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) {
      ElMessage.warning('生産日を選択してください')
      return
    }
    batchLoading.value = true
    try {
      const res = await fetchCuttingManagementList({ production_day: day, limit: 2000 })
      const list = (res.data ?? []).filter(
        (r) => r.id != null && Number(r.production_completed_check) === 1 && (r.product_cd || '').trim(),
      )
      batchRows.value = list.map(toBatchRow)
      batchLoadedDay.value = day
      for (const r of batchRows.value) r.selected = !registeredKeys.value.has(r.key)
      if (batchLineFilter.value && !batchLineOptions.value.includes(batchLineFilter.value)) {
        batchLineFilter.value = ''
      }
    } catch (e: unknown) {
      console.error(e)
      batchRows.value = []
      const err = e as { response?: { data?: { detail?: string; message?: string } }; message?: string }
      ElMessage.error(
        err?.response?.data?.detail ?? err?.response?.data?.message ?? err?.message ?? '切断指示の取得に失敗しました',
      )
    } finally {
      batchLoading.value = false
    }
  }

  function onBatchTimeInput(row: CuttingBatchRow, field: 'startedText' | 'endedText', raw: string): void {
    row[field] = sanitizeTimeDraft(raw)
    row.error = ''
  }

  function onBatchTimeBlur(row: CuttingBatchRow, field: 'startedText' | 'endedText'): void {
    row[field] = formatTimeInputValue(parseTimeInput(row[field]))
  }

  function onBatchQtyInput(row: CuttingBatchRow, raw: string): void {
    const digits = String(raw ?? '').replace(/\D/g, '')
    row.actualQty = digits ? Number.parseInt(digits, 10) : null
    row.error = ''
  }

  function batchVariance(row: CuttingBatchRow): number | null {
    if (row.plannedQty == null || row.actualQty == null) return null
    return Math.round(row.plannedQty - row.actualQty)
  }

  function batchWorkMin(row: CuttingBatchRow): number | null {
    const day = productionDay.value.trim().slice(0, 10)
    const { started, ended } = resolveProductionEndDateTime(
      day,
      parseTimeInput(row.startedText),
      parseTimeInput(row.endedText),
    )
    if (!started || !ended) return null
    const shiftMin = Math.round((ended.getTime() - started.getTime()) / 60000)
    return shiftMin - Math.max(0, row.breakMin || 0) - sumLossMin(row)
  }

  function validateBatchRow(row: CuttingBatchRow, day: string): string {
    if (!row.line) return 'ラインなし'
    if (row.actualQty == null || row.actualQty < 0) return '生産数未入力'
    const { started, ended } = resolveProductionEndDateTime(
      day,
      parseTimeInput(row.startedText),
      parseTimeInput(row.endedText),
    )
    if (!started || !ended) return '開始・終了未入力'
    const shiftMin = Math.round((ended.getTime() - started.getTime()) / 60000)
    if (Math.max(0, row.breakMin || 0) + sumLossMin(row) > shiftMin) {
      return '休憩・ロス時間が生産時間超過'
    }
    return ''
  }

  async function submitBatch(): Promise<void> {
    if (!guardMesOperation(canCreate)) return
    const day = batchLoadedDay.value || productionDay.value.trim().slice(0, 10)
    const targets = selectedBatchRows.value
    if (!targets.length) {
      ElMessage.warning('登録する行を選択してください')
      return
    }

    let invalid = 0
    for (const r of targets) {
      r.error = validateBatchRow(r, day)
      if (r.error) invalid += 1
    }
    if (invalid > 0) {
      ElMessage.warning(`入力不備が ${invalid} 件あります（赤字の行を確認してください）`)
      return
    }

    const dupCount = targets.filter((r) => registeredKeys.value.has(r.key)).length
    if (dupCount > 0) {
      try {
        await ElMessageBox.confirm(
          `登録済の行が ${dupCount} 件含まれています。重複して登録しますか？`,
          '重複確認',
          { type: 'warning', confirmButtonText: '登録する', cancelButtonText: 'キャンセル' },
        )
      } catch {
        return
      }
    }

    batchSaving.value = true
    let ok = 0
    let ng = 0
    try {
      for (const r of targets) {
        const { started, ended } = resolveProductionEndDateTime(
          day,
          parseTimeInput(r.startedText),
          parseTimeInput(r.endedText),
        )
        const shiftMin = Math.round(((ended?.getTime() ?? 0) - (started?.getTime() ?? 0)) / 60000)
        try {
          const res = await createCuttingProductionIndicatorManual({
            production_day: day,
            production_line: r.line,
            product_cd: r.productCd,
            product_name: r.productName || r.productCd,
            planned_quantity: r.plannedQty,
            actual_quantity: Math.max(0, Math.round(r.actualQty ?? 0)),
            quantity_variance: batchVariance(r),
            shift_hours: minToHours(shiftMin),
            break_hours: minToHours(Math.max(0, Math.round(r.breakMin || 0))),
            setup_hours: minToHours(Math.max(0, Math.round(r.setupMin || 0))),
            repair_hours: minToHours(Math.max(0, Math.round(r.repairMin || 0))),
            saw_blade_exchange_hours: minToHours(Math.max(0, Math.round(r.sawBladeMin || 0))),
            planned_stop_hours: minToHours(Math.max(0, Math.round(r.stopMin || 0))),
            remarks: r.remarks.trim() || null,
          })
          if (res.success === false || !res.data?.id) {
            r.error = res.message ?? '登録失敗'
            ng += 1
          } else {
            r.selected = false
            r.error = ''
            ok += 1
          }
        } catch (e: unknown) {
          console.error(e)
          const err = e as { response?: { data?: { detail?: string; message?: string } }; message?: string }
          r.error = err?.response?.data?.detail ?? err?.response?.data?.message ?? err?.message ?? '登録失敗'
          ng += 1
        }
      }
    } finally {
      batchSaving.value = false
    }

    if (ok > 0) await onSaved()
    if (ng === 0) ElMessage.success(`${ok}件を登録しました`)
    else ElMessage.warning(`${ok}件登録 / ${ng}件失敗（赤字の行を確認してください）`)
  }

  return {
    batchRows,
    batchLoading,
    batchSaving,
    batchLoadedDay,
    batchLineFilter,
    batchLineOptions,
    visibleBatchRows,
    selectedBatchRows,
    batchRegisteredCount,
    allVisibleSelected,
    someVisibleSelected,
    isBatchRowRegistered,
    toggleAllVisible,
    loadBatch,
    onBatchTimeInput,
    onBatchTimeBlur,
    onBatchQtyInput,
    batchVariance,
    batchWorkMin,
    submitBatch,
  }
}
