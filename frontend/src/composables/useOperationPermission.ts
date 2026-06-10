import { computed } from 'vue'
import { useUserStore } from '@/modules/auth/stores/user'
import type { OperationModule } from '@/constants/operationModules'
import {
  canApprove as canApproveForUser,
  canCreate as canCreateForUser,
  canDelete as canDeleteForUser,
  canEdit as canEditForUser,
  canExport as canExportForUser,
  canOperate as canOperateForUser,
  getModulePermission as getModulePermissionForUser,
  type OperationAction,
  type OperationPermission,
} from '@/utils/operationPermissions'

export function useOperationPermission(module: OperationModule | string) {
  const userStore = useUserStore()
  const user = computed(() => userStore.user)

  const modulePermission = computed<OperationPermission | null>(() =>
    getModulePermissionForUser(user.value, module),
  )

  function canOperate(action: OperationAction) {
    return canOperateForUser(user.value, module, action)
  }

  return {
    user,
    modulePermission,
    canOperate,
    canCreate: computed(() => canCreateForUser(user.value, module)),
    canEdit: computed(() => canEditForUser(user.value, module)),
    canDelete: computed(() => canDeleteForUser(user.value, module)),
    canExport: computed(() => canExportForUser(user.value, module)),
    canApprove: computed(() => canApproveForUser(user.value, module)),
  }
}
