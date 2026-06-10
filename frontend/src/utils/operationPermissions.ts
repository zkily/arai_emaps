import type { User } from '@/modules/auth/stores/user'
import type { OperationAction, OperationModule } from '@/constants/operationModules'
import { isAdminUser } from '@/utils/menuPermissions'

export interface OperationPermission {
  module: string
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
  can_export: boolean
  can_approve: boolean
}

function actionField(action: OperationAction): keyof OperationPermission {
  switch (action) {
    case 'create':
      return 'can_create'
    case 'edit':
      return 'can_edit'
    case 'delete':
      return 'can_delete'
    case 'export':
      return 'can_export'
    case 'approve':
      return 'can_approve'
  }
}

function fallbackCanOperate(user: User | null | undefined, action: OperationAction): boolean {
  if (!user) return false
  if (isAdminUser(user)) return true
  const perms = user.permissions ?? []
  if (action === 'export') {
    return perms.includes('all') || perms.includes('read') || perms.includes('write')
  }
  return perms.includes('all') || perms.includes('write')
}

export function getModulePermission(
  user: User | null | undefined,
  module: OperationModule | string,
): OperationPermission | null {
  const list = user?.operation_permissions
  if (!list?.length) return null
  return list.find((item) => item.module === module) ?? null
}

/** モジュール単位の操作可否（admin は常に true） */
export function canOperate(
  user: User | null | undefined,
  module: OperationModule | string,
  action: OperationAction,
): boolean {
  if (!user) return false
  if (isAdminUser(user)) return true

  const modPerm = getModulePermission(user, module)
  if (!modPerm) {
    return fallbackCanOperate(user, action)
  }
  return Boolean(modPerm[actionField(action)])
}

export function canCreate(user: User | null | undefined, module: OperationModule | string): boolean {
  return canOperate(user, module, 'create')
}

export function canEdit(user: User | null | undefined, module: OperationModule | string): boolean {
  return canOperate(user, module, 'edit')
}

export function canDelete(user: User | null | undefined, module: OperationModule | string): boolean {
  return canOperate(user, module, 'delete')
}

export function canExport(user: User | null | undefined, module: OperationModule | string): boolean {
  return canOperate(user, module, 'export')
}

export function canApprove(user: User | null | undefined, module: OperationModule | string): boolean {
  return canOperate(user, module, 'approve')
}
