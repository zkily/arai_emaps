import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_INVENTORY } from '@/constants/operationModules'

/** 在庫管理モジュールの操作権限 */
export function useInventoryOperationPermission() {
  return useOperationPermission(OPERATION_MODULE_INVENTORY)
}
