/** 溶接工程向け製品候補（生産性分析） */
import type { Product } from '@/types/master'

export function filterWeldingSelectableProducts(list: Product[]): Product[] {
  return list
    .filter((p) => p.status !== 'inactive')
    .sort((a, b) =>
      (a.product_name ?? '').localeCompare(b.product_name ?? '', 'ja', { sensitivity: 'base' }),
    )
}
