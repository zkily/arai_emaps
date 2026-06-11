import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_MASTER } from '@/constants/operationModules'

/** マスタ管理モジュールの操作権限（新規・編集・削除・出力・承認） */
export function useMasterOperationPermission() {
  return useOperationPermission(OPERATION_MODULE_MASTER)
}
