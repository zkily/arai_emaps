import { ElMessage } from 'element-plus'
import type { Ref } from 'vue'

const DEFAULT_MESSAGE = '生産計画の操作権限がありません'

/** 操作権限が無い場合は警告を出して false を返す */
export function guardApsOperation(
  allowed: Ref<boolean> | boolean,
  message = DEFAULT_MESSAGE,
): boolean {
  const ok = typeof allowed === 'boolean' ? allowed : allowed.value
  if (!ok) ElMessage.warning(message)
  return ok
}
