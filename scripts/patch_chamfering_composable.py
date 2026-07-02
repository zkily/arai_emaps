# -*- coding: utf-8
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "frontend/src/views/mes/actualCollectionRegistration/chamfering/useChamferingManualRegistration.ts"
t = p.read_text(encoding="utf-8")

repls = [
    ("Cutting", "Chamfering"),
    ("cutting", "chamfering"),
    ("Cutting", "Chamfering"),
]
for old, new in repls:
    t = t.replace(old, new)

t = t.replace(
    """export interface ManualRegistrationForm {
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
}""",
    """export interface ManualRegistrationForm {
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
)

t = t.replace(
    """    plannedQty: null,
    actualQty: null,
    quantityVariance: null,
    varianceManual: false,""",
    """    chamferPlannedQty: null,
    chamferActualQty: null,
    swPlannedQty: null,
    swActualQty: null,
    chamferDefectQty: null,
    swDefectQty: null,""",
)

t = t.replace(
    "getQty: (row) => Math.max(0, Number(row.actual_quantity ?? 0)),",
    "getQty: (row) => Math.max(0, Number(row.total_production_qty ?? 0)),",
)

t = t.replace(
    """  const computedVariance = computed(() => {
    if (form.value.varianceManual) return form.value.quantityVariance
    return resolveVariance(form.value.plannedQty, form.value.actualQty, null)
  })""",
    """  const computedTotalQty = computed(() => {
    const chamfer = Math.max(0, Math.round(Number(form.value.chamferActualQty) || 0))
    const sw = Math.max(0, Math.round(Number(form.value.swActualQty) || 0))
    return chamfer + sw
  })""",
)

t = t.replace(
    """  function onPlannedQtyInput(raw: string | undefined | null): void {
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
  }""",
    """  function onChamferPlannedQtyInput(raw: string | undefined | null): void {
    form.value.chamferPlannedQty = parseQtyInput(raw)
  }

  function onChamferActualQtyInput(raw: string | undefined | null): void {
    form.value.chamferActualQty = parseQtyInput(raw)
  }

  function onSwPlannedQtyInput(raw: string | undefined | null): void {
    form.value.swPlannedQty = parseQtyInput(raw)
  }

  function onSwActualQtyInput(raw: string | undefined | null): void {
    form.value.swActualQty = parseQtyInput(raw)
  }

  function onChamferDefectQtyInput(raw: string | undefined | null): void {
    form.value.chamferDefectQty = parseQtyInput(raw)
  }

  function onSwDefectQtyInput(raw: string | undefined | null): void {
    form.value.swDefectQty = parseQtyInput(raw)
  }""",
)

t = t.replace(
    """      plannedQty: row.planned_quantity ?? null,
      actualQty: row.actual_quantity ?? null,
      quantityVariance: row.quantity_variance ?? null,
      varianceManual: row.quantity_variance != null,""",
    """      chamferPlannedQty: row.chamfer_planned_quantity ?? null,
      chamferActualQty: row.chamfer_actual_quantity ?? null,
      swPlannedQty: row.sw_planned_quantity ?? null,
      swActualQty: row.sw_actual_quantity ?? null,
      chamferDefectQty: row.chamfer_defect_quantity ?? null,
      swDefectQty: row.sw_defect_quantity ?? null,""",
)

t = t.replace(
    """    if (draft.actualQty == null || !Number.isFinite(draft.actualQty) || draft.actualQty < 0) {
      ElMessage.warning('④ 生産数を入力してください')
      return
    }""",
    """    if (computedTotalQty.value <= 0) {
      ElMessage.warning('④ 面取またはSWの生産数を入力してください')
      return
    }""",
)

t = t.replace(
    """    const body = {
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
    }""",
    """    const body = {
      production_day: day,
      production_line: draft.productionLine.trim(),
      product_cd: draft.productCd.trim(),
      product_name: draft.productName.trim() || draft.productCd.trim(),
      chamfer_planned_quantity: draft.chamferPlannedQty,
      chamfer_actual_quantity: draft.chamferActualQty,
      chamfer_defect_quantity: draft.chamferDefectQty,
      sw_planned_quantity: draft.swPlannedQty,
      sw_actual_quantity: draft.swActualQty,
      sw_defect_quantity: draft.swDefectQty,
      shift_hours: minToHours(shiftMin),
      break_hours: minToHours(breakMin),
      setup_hours: minToHours(stopMin),
      remarks: draft.registrationNote.trim() || null,
    }""",
)

t = t.replace("computedVariance,", "computedTotalQty,")
t = t.replace("onPlannedQtyInput,", "onChamferPlannedQtyInput,")
t = t.replace("onActualQtyInput,", "onChamferActualQtyInput,")
t = t.replace("onVarianceQtyInput,", "onSwPlannedQtyInput,")

# fix return exports - need all handlers
t = t.replace(
    """    onChamferPlannedQtyInput,
    onChamferActualQtyInput,
    onSwPlannedQtyInput,""",
    """    onChamferPlannedQtyInput,
    onChamferActualQtyInput,
    onSwPlannedQtyInput,
    onSwActualQtyInput,
    onChamferDefectQtyInput,
    onSwDefectQtyInput,""",
)

# remove unused resolveVariance if still referenced - grep
t = t.replace(
    """function resolveVariance(planned: number | null, actual: number | null, manual: number | null): number | null {
  if (manual != null && Number.isFinite(manual)) return Math.round(manual)
  if (planned == null || actual == null) return null
  return Math.round(planned - actual)
}

""",
    "",
)

p.write_text(t, encoding="utf-8")
print("patched composable")
