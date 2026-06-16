/** 検査 MES 製品一覧フィルタ（実績収集・モニタ次製品指定で共用） */

export const INSPECTION_PRODUCT_NAME_EXCLUDES = ['加工', 'アーチ'] as const

export interface InspectionProductOptionLike {
  product_code?: string | null
  product_name?: string | null
  is_active?: boolean
}

/** 製品 CD 末尾が 1、製品名に除外語なし、製品名昇順 */
export function filterInspectionProductOptions<T extends InspectionProductOptionLike>(
  list: T[],
): T[] {
  return list
    .filter((p) => {
      if (p.is_active === false) return false
      const code = (p.product_code ?? '').trim()
      if (code.length === 0 || !code.endsWith('1')) return false
      const name = p.product_name ?? ''
      if (INSPECTION_PRODUCT_NAME_EXCLUDES.some((kw) => name.includes(kw))) return false
      return true
    })
    .sort((a, b) =>
      (a.product_name ?? '').localeCompare(b.product_name ?? '', 'ja', { sensitivity: 'base' }),
    )
}
