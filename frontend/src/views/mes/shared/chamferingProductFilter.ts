import type { Product } from '@/types/master'

/** 面取実績登録の製品プルダウン用（全製品を表示） */
export function filterChamferingSelectableProducts(products: Product[]): Product[] {
  return products.filter((p) => (p.product_cd || '').trim())
}
