/** 検査工程向け製品候補の共通フィルタ（MES 実績収集・生産性分析で共用） */

export const INSPECTION_PRODUCT_NAME_EXCLUDES = ['加工', 'アーチ'] as const

export interface InspectionProductLike {
  product_cd?: string | null
  product_code?: string | null
  product_name?: string | null
  status?: string | null
  is_active?: boolean
}

export function getInspectionProductCode(product: InspectionProductLike): string {
  return (product.product_cd ?? product.product_code ?? '').trim()
}

/** 製品 CD 末尾が 1、品名に除外語なし、有効製品 */
export function isInspectionSelectableProduct(product: InspectionProductLike): boolean {
  if (product.is_active === false) return false
  if (product.status != null && product.status !== 'active') return false
  const code = getInspectionProductCode(product)
  if (!code || !code.endsWith('1')) return false
  const name = product.product_name ?? ''
  if (INSPECTION_PRODUCT_NAME_EXCLUDES.some((kw) => name.includes(kw))) return false
  return true
}

export function filterInspectionSelectableProducts<T extends InspectionProductLike>(list: T[]): T[] {
  return list
    .filter(isInspectionSelectableProduct)
    .sort((a, b) =>
      (a.product_name ?? '').localeCompare(b.product_name ?? '', 'ja', { sensitivity: 'base' }),
    )
}
