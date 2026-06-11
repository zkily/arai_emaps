import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_QUALITY } from '@/constants/operationModules'

/** 品質管理モジュールの操作権限 */
export function useQualityOperationPermission() {
  return useOperationPermission(OPERATION_MODULE_QUALITY)
}
