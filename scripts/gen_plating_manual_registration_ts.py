# -*- coding: utf-8
"""从面取 composable 生成メッキ日次実績登録 composable。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend/src/views/mes/actualCollectionRegistration/chamfering/useChamferingManualRegistration.ts"
DST = ROOT / "frontend/src/views/mes/actualCollectionRegistration/plating/usePlatingManualRegistration.ts"

t = SRC.read_text(encoding="utf-8")

repls = [
    ("Chamfering", "Plating"),
    ("chamferingProductionIndicator", "platingProductionIndicator"),
    ("filterChamferingSelectableProducts", "filterPlatingSelectableProducts"),
    ("chamferingProductFilter", "platingProductFilter"),
    ("面取またはSWの生産数", "実績数"),
    ("面取", "メッキ"),
]

for old, new in repls:
    t = t.replace(old, new)

# imports cleanup
t = re.sub(
    r"import \{ getProductList \} from '@/api/master/productMaster'\n",
    "",
    t,
)
t = re.sub(
    r"import \{ filterPlatingSelectableProducts \} from '@/views/mes/shared/platingProductFilter'\n",
    "",
    t,
)

# types
t = t.replace(
    """export interface PlatingRegistrationProduct {
  product_code: string
  product_name: string
}

export interface ManualRegistrationForm {
  productionDay: string
  productionLine: string
  productCd: string
  productName: string
  chamferPlannedQty: number | null
  chamferActualQty: number | null
  swPlannedQty: number | null
  swActualQty: number | null
  chamferDefectQty: number | null
  swDefectQty: number | null
  registrationNote: string
  startedAt: string | null
  endedAt: string | null
  breakMin: number
  stopMin: number
}""",
    """export interface ManualRegistrationForm {
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
}""",
)

t = t.replace(
    """function emptyForm(day: string, line: string): ManualRegistrationForm {
  return {
    productionDay: day,
    productionLine: line,
    productCd: '',
    productName: '',
    chamferPlannedQty: null,
    chamferActualQty: null,
    swPlannedQty: null,
    swActualQty: null,
    chamferDefectQty: null,
    swDefectQty: null,
    registrationNote: '',
    startedAt: null,
    endedAt: null,
    breakMin: 0,
    stopMin: 0,
  }
}""",
    """function emptyForm(day: string): ManualRegistrationForm {
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
}""",
)

# remove product/line state
t = re.sub(r"  const lineFilterName = ref\(''\)\n", "", t)
t = re.sub(r"  const products = ref<PlatingRegistrationProduct\[\]>\(\[\]\)\n", "", t)
t = re.sub(r"  const loadingProducts = ref\(false\)\n", "", t)
t = re.sub(r"  const lineOptions = ref<\{ line_name: string \}\[\]>\(\[\]\)\n", "", t)
t = re.sub(r"  const loadingLines = ref\(false\)\n", "", t)

t = t.replace(
    "const form = ref<ManualRegistrationForm>(emptyForm(getJSTToday(), ''))",
    "const form = ref<ManualRegistrationForm>(emptyForm(getJSTToday()))",
)

t = re.sub(
    r"  const filteredRows = computed\(\(\) => \{.*?\}\)\n",
    "  const filteredRows = computed(() => rows.value)\n",
    t,
    count=1,
    flags=re.S,
)

t = t.replace(
    "getQty: (row) => Math.max(0, Number(row.total_production_qty ?? 0)),",
    "getQty: (row) => Math.max(0, Number(row.actual_quantity ?? 0)),",
)

t = re.sub(
    r"  const computedTotalQty = computed\(\(\) => \{.*?\}\)\n",
    "  const computedTotalQty = computed(() => Math.max(0, Math.round(Number(form.value.actualQty) || 0)))\n",
    t,
    count=1,
    flags=re.S,
)

t = t.replace(
    "breakMin: form.value.breakMin, stopMin: form.value.stopMin, endsNextDay: false }",
    "maintenanceMin: form.value.maintenanceMin, troubleMin: form.value.troubleMin, chocoMin: form.value.chocoMin, plannedStopMin: form.value.plannedStopMin, endsNextDay: false }",
)
t = t.replace(
    "const pauseMin = Math.max(0, form.value.breakMin) + Math.max(0, form.value.stopMin)",
    "const pauseMin = Math.max(0, form.value.maintenanceMin) + Math.max(0, form.value.troubleMin) + Math.max(0, form.value.chocoMin) + Math.max(0, form.value.plannedStopMin)",
)
t = t.replace(
    "breakMin: form.value.breakMin,\n      stopMin: form.value.stopMin,",
    "maintenanceMin: form.value.maintenanceMin,\n      troubleMin: form.value.troubleMin,\n      chocoMin: form.value.chocoMin,\n      plannedStopMin: form.value.plannedStopMin,",
)

# remove loadLines/loadProducts and related functions
t = re.sub(r"  async function loadLines\(\): Promise<void> \{.*?\n  \}\n\n", "", t, count=1, flags=re.S)
t = re.sub(r"  async function loadProducts\(\): Promise<void> \{.*?\n  \}\n\n", "", t, count=1, flags=re.S)
t = re.sub(r"      await loadLines\(\)\n", "", t)

t = re.sub(r"  function onProductChange\(code: string\): void \{.*?\n  \}\n\n", "", t, count=1, flags=re.S)

# qty handlers
for old, new in [
    ("onChamferPlannedQtyInput", "onPlannedQtyInput"),
    ("onChamferActualQtyInput", "onActualQtyInput"),
    ("onSwPlannedQtyInput", "onDefectQtyInput"),
    ("onSwActualQtyInput", "onDefectPlatingScratchInput"),
    ("onChamferDefectQtyInput", "onDefectMoyaKaburiInput"),
    ("onSwDefectQtyInput", "onDefectNickelInput"),
]:
    t = t.replace(old, new)

t = t.replace("form.value.chamferPlannedQty", "form.value.plannedQty")
t = t.replace("form.value.chamferActualQty", "form.value.actualQty")
t = t.replace("form.value.swPlannedQty", "form.value.defectQty")
t = t.replace("form.value.swActualQty", "form.value.defectPlatingScratch")
t = t.replace("form.value.chamferDefectQty", "form.value.defectMoyaKaburi")
t = t.replace("form.value.swDefectQty", "form.value.defectNickel")

# add missing handlers before onProductionDayChange
extra_handlers = """
  function onDefectContactInput(raw: string | undefined | null): void {
    form.value.defectContact = parseQtyInput(raw)
  }

  function onDefectOtherInput(raw: string | undefined | null): void {
    form.value.defectOther = parseQtyInput(raw)
  }

"""
t = t.replace("  function onProductionDayChange(day: string): void {", extra_handlers + "  function onProductionDayChange(day: string): void {")

t = t.replace(
    "function resetForm(options?: { preserveLine?: boolean }): void {\n    editingRowId.value = null\n    const line = options?.preserveLine ? form.value.productionLine : ''\n    form.value = emptyForm(productionDay.value, line)",
    "function resetForm(): void {\n    editingRowId.value = null\n    form.value = emptyForm(productionDay.value)",
)
t = t.replace("resetForm({ preserveLine: true })", "resetForm()")

# loadRowIntoForm
load_row = """  function loadRowIntoForm(row: PlatingIndicatorRow): void {
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
  }"""

t = re.sub(r"  function loadRowIntoForm\(row: PlatingIndicatorRow\): void \{.*?\n  \}", load_row, t, count=1, flags=re.S)

# submitForm body
submit_old = re.search(r"  async function submitForm\(\): Promise<void> \{.*?\n  \}\n\n  async function deleteRow", t, re.S)
if not submit_old:
    raise SystemExit("submitForm not found")

submit_new = """  async function submitForm(): Promise<void> {
    if (!guardMesOperation(canSave)) return

    const draft = form.value
    const day = draft.productionDay.trim().slice(0, 10)
    if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(day)) {
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

  async function deleteRow"""

t = t[: submit_old.start()] + submit_new + t[submit_old.end() - len("  async function deleteRow") :]

# deleteRow message
t = t.replace(
    """    const productLabel = (row.product_name ?? row.product_cd ?? '').trim() || '—'
    const line = lineLabel(row.production_line)
    try {
      await ElMessageBox.confirm(
        `ライン「${line}」・製品「${productLabel}」の登録を削除しますか？`,""",
    """    const dayLabel = String(row.production_day ?? productionDay.value).slice(0, 10)
    try {
      await ElMessageBox.confirm(
        `生産日「${dayLabel}」の手動登録を削除しますか？`,""",
)

# format helpers
t = t.replace(
    """  function formatBreakMin(row: PlatingIndicatorRow): string {
    const m = hoursToMin(row.break_hours)
    return m > 0 ? `${m}分` : '—'
  }

  function formatStopMin(row: PlatingIndicatorRow): string {
    const m = hoursToMin(row.setup_hours)
    return m > 0 ? `${m}分` : '—'
  }""",
    """  function formatMaintenanceMin(row: PlatingIndicatorRow): string {
    const m = hoursToMin(row.maintenance_hours)
    return m > 0 ? `${m}分` : '—'
  }

  function formatTroubleMin(row: PlatingIndicatorRow): string {
    const m = hoursToMin(row.trouble_hours)
    return m > 0 ? `${m}分` : '—'
  }""",
)

# init
t = t.replace(
    """  async function init(): Promise<void> {
    form.value = emptyForm(productionDay.value, '')
    syncTimeTextsFromForm()
    await loadProducts()
    await loadRows()
  }""",
    """  async function init(): Promise<void> {
    form.value = emptyForm(productionDay.value)
    syncTimeTextsFromForm()
    await loadRows()
  }""",
)

# return block cleanup
for name in [
    "lineFilterName",
    "products",
    "loadingProducts",
    "lineOptions",
    "loadingLines",
    "lineLabel",
    "onProductChange",
    "onChamferPlannedQtyInput",
    "onChamferActualQtyInput",
    "onSwPlannedQtyInput",
    "onSwActualQtyInput",
    "onChamferDefectQtyInput",
    "onSwDefectQtyInput",
    "formatBreakMin",
    "formatStopMin",
]:
    t = re.sub(rf"    {name},\n", "", t)

return_add = """    onPlannedQtyInput,
    onActualQtyInput,
    onDefectQtyInput,
    onDefectPlatingScratchInput,
    onDefectMoyaKaburiInput,
    onDefectNickelInput,
    onDefectContactInput,
    onDefectOtherInput,
    formatMaintenanceMin,
    formatTroubleMin,
"""
t = t.replace("    formatQtyInputValue,\n", "    formatQtyInputValue,\n" + return_add)

# remove unused import fetch lines
t = re.sub(r",\n  fetchPlatingProductionIndicatorLines,", ",", t)

DST.write_text(t, encoding="utf-8")
print(f"Wrote {DST}")
