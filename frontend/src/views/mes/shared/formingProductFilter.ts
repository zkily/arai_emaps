import type { Product } from '@/types/master'

/** 成形生産性分析の製品プルダウン用（全製品を表示） */
export function filterFormingSelectableProducts(products: Product[]): Product[] {
  return products.filter((p) => (p.product_cd || '').trim())
}
