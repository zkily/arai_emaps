import { ElMessage } from 'element-plus'
import type { Ref } from 'vue'

const DEFAULT_MESSAGE = '原価・会計の操作権限がありません'

export function guardCostOperation(
  allowed: Ref<boolean> | boolean,
  message = DEFAULT_MESSAGE,
): boolean {
  const ok = typeof allowed === 'boolean' ? allowed : allowed.value
  if (!ok) ElMessage.warning(message)
  return ok
}
