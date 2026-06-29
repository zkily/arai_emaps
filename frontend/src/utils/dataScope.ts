import type { User } from '@/modules/auth/stores/user'
import { isAdminUser } from '@/utils/menuPermissions'

export type DataScopeCode =
  | 'all'
  | 'self'
  | 'department'
  | 'department_below'
  | 'custom'

const I18N_KEY: Record<DataScopeCode, string> = {
  all: 'systemUser.role.scopeAll',
  self: 'systemUser.role.scopeSelf',
  department: 'systemUser.role.scopeDept',
  department_below: 'systemUser.role.scopeDeptBelow',
  custom: 'systemUser.role.scopeCustom',
}

export function userDataScopeCode(user: User | null | undefined): DataScopeCode {
  if (!user) return 'self'
  if (isAdminUser(user)) return 'all'
  const code = (user.data_scope || 'department') as DataScopeCode
  return code in I18N_KEY ? code : 'department'
}

export function displayUserDataScope(user: User | null | undefined, t: (key: string) => string): string {
  const code = userDataScopeCode(user)
  return t(I18N_KEY[code])
}

/** 全社データを見られるか（UI の注意表示用） */
export function hasUnrestrictedDataScope(user: User | null | undefined): boolean {
  return userDataScopeCode(user) === 'all'
}
