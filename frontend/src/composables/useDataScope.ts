/**
 * データ範囲（データスコープ）用 composable
 * ログインユーザーの部門・権限に基づき、一覧APIなどで使用する
 */
import { computed } from 'vue'
import { useUserStore } from '@/modules/auth/stores/user'

export function useDataScope() {
  const userStore = useUserStore()

  const isAdmin = computed(() => userStore.hasPermission('all'))
  const departmentId = computed(() => userStore.user?.department_id ?? null)

  /** 一覧APIの部門フィルタに渡す値（管理者は undefined＝全件、一般は自部門ID） */
  const scopeDepartmentId = computed(() => {
    if (isAdmin.value) return undefined
    return departmentId.value ?? undefined
  })

  return {
    isAdmin,
    departmentId,
    scopeDepartmentId,
  }
}
