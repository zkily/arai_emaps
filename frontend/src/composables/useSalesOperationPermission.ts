import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_SALES } from '@/constants/operationModules'

/** 販売管理モジュールの操作権限 */
export function useSalesOperationPermission() {
  return useOperationPermission(OPERATION_MODULE_SALES)
}
