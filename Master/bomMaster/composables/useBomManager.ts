/**
 * BOM管理ページのコンポーネント間連携用
 */
import { ref, provide, inject, InjectionKey } from 'vue'
// import type { BomItem } from '@/shared/types/bom'

// 注入キー
export const BOM_MANAGER_KEY = Symbol() as InjectionKey<ReturnType<typeof useBomManager>>

// インタフェース
export interface BomTreeViewProduct {
  product_id: number
  product_name: string
}

/**
 * BOM管理機能
 */
export function useBomManager() {
  // 状態
  const showBomTree = ref(false)
  const selectedProduct = ref<BomTreeViewProduct | null>(null)
  const activeTabName = ref('list')

  // ツリー表示
  const openBomTree = (product: BomTreeViewProduct) => {
    selectedProduct.value = product
    showBomTree.value = true
  }

  // タブ切り替え
  const switchToTab = (tabName: string) => {
    activeTabName.value = tabName
  }

  // 機能を公開
  return {
    // 状態
    showBomTree,
    selectedProduct,
    activeTabName,

    // アクション
    openBomTree,
    switchToTab,
  }
}

/**
 * Provider関数 - 親コンポーネントで使用
 */
export function provideBomManager() {
  const manager = useBomManager()
  provide(BOM_MANAGER_KEY, manager)
  return manager
}

/**
 * 子コンポーネントでの利用
 */
export function injectBomManager() {
  const manager = inject(BOM_MANAGER_KEY)
  if (!manager) {
    throw new Error(
      'BomManagerが提供されていません。provideBomManagerを親コンポーネントで呼び出してください。',
    )
  }
  return manager
}
