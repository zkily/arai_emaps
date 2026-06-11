import { ElMessage } from 'element-plus'
import type { Ref } from 'vue'

const DEFAULT_MESSAGE = '購買管理の操作権限がありません'

export function guardPurchaseOperation(
  allowed: Ref<boolean> | boolean,
  message = DEFAULT_MESSAGE,
): boolean {
  const ok = typeof allowed === 'boolean' ? allowed : allowed.value
  if (!ok) ElMessage.warning(message)
  return ok
}
