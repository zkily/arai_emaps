import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_PRODUCTION_PLAN } from '@/constants/operationModules'

/** APS（生産計画）モジュールの操作権限 */
export function useApsOperationPermission() {
  return useOperationPermission(OPERATION_MODULE_PRODUCTION_PLAN)
}
