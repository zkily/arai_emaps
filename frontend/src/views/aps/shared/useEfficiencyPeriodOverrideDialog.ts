import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { fetchEquipmentEfficiencyProducts, type EquipmentEfficiencyProduct, type ProductionLine } from '@/api/aps'

export function eeProductOptionLabel(row: EquipmentEfficiencyProduct): string {
  const name = row.product_name?.trim() || ''
  const cd = row.product_cd?.trim() || ''
  if (name && cd) return `${name}（${cd}）`
  return name || cd || `ID:${row.id}`
}

/** 成型/溶接計画作成：能率期間指定ダイアログ用の共通状態 */
export function useEfficiencyPeriodOverrideDialog(options: {
  selectedLineId: Ref<number | null>
  lines: Ref<ProductionLine[]>
  eeProducts: Ref<EquipmentEfficiencyProduct[]>
  loadingEeProducts: Ref<boolean>
  defaultProductCd: Ref<string> | ComputedRef<string>
  replanAll: () => Promise<void>
}) {
  const { selectedLineId, lines, eeProducts, loadingEeProducts, defaultProductCd, replanAll } = options

  const efficiencyOverrideDialogVisible = ref(false)

  const selectedLineMachineCd = computed(() => {
    const ln = lines.value.find((l) => l.id === selectedLineId.value)
    return (ln?.line_code || '').trim()
  })

  const selectedLineMachineName = computed(() => {
    const ln = lines.value.find((l) => l.id === selectedLineId.value)
    return (ln?.line_name || '').trim()
  })

  const efficiencyOverrideProductOptions = computed(() => {
    const seen = new Set<string>()
    const out: { product_cd: string; product_name?: string | null; label: string }[] = []
    for (const row of eeProducts.value) {
      const product_cd = (row.product_cd || '').trim()
      if (!product_cd || seen.has(product_cd)) continue
      seen.add(product_cd)
      out.push({
        product_cd,
        product_name: row.product_name,
        label: eeProductOptionLabel(row),
        efficiency_rate: Number(row.efficiency_rate) > 0 ? Number(row.efficiency_rate) : null,
      })
    }
    return out
  })

  function ensureEeProductsLoaded() {
    if (!selectedLineId.value || eeProducts.value.length > 0) return
    loadingEeProducts.value = true
    fetchEquipmentEfficiencyProducts(selectedLineId.value)
      .then((list) => {
        eeProducts.value = list
      })
      .catch(() => {
        eeProducts.value = []
      })
      .finally(() => {
        loadingEeProducts.value = false
      })
  }

  function openEfficiencyOverrideDialog() {
    if (!selectedLineId.value) return false
    ensureEeProductsLoaded()
    efficiencyOverrideDialogVisible.value = true
    return true
  }

  async function replanAfterEfficiencyOverride() {
    efficiencyOverrideDialogVisible.value = false
    await replanAll()
  }

  return {
    efficiencyOverrideDialogVisible,
    selectedLineMachineCd,
    selectedLineMachineName,
    efficiencyOverrideProductOptions,
    openEfficiencyOverrideDialog,
    replanAfterEfficiencyOverride,
    defaultProductCd,
  }
}
