import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_MES } from '@/constants/operationModules'

/** MES（製造実行）モジュールの操作権限 */
export function useMesOperationPermission() {
  return useOperationPermission(OPERATION_MODULE_MES)
}
