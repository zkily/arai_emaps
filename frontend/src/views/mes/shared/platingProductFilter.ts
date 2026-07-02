export function filterPlatingSelectableProducts<T extends { product_cd?: string | null }>(
  products: T[],
): T[] {
  return products
}
