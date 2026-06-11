import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_COST } from '@/constants/operationModules'

/** 原価・会計モジュールの操作権限 */
export function useCostOperationPermission() {
  return useOperationPermission(OPERATION_MODULE_COST)
}
