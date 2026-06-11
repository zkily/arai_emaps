import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_PURCHASE } from '@/constants/operationModules'

/** 購買管理モジュールの操作権限 */
export function usePurchaseOperationPermission() {
  return useOperationPermission(OPERATION_MODULE_PURCHASE)
}
