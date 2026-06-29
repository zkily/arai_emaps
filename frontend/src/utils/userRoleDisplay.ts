import { builtinRoleDisplayName } from '@/utils/builtinRoleDisplayName'

export const BUILTIN_ROLE_CODE_TO_DB_NAME: Record<string, string> = {
  admin: '管理者',
  user: '一般ユーザー',
  manager: 'マネージャー',
  worker: '作業者',
  guest: 'ゲスト',
  viewer: '閲覧者',
}

export function resolveUserRoleId(
  row: { role_id?: number | null; role: string },
  roleOptions: { id: number; name: string }[],
): number | null {
  if (row.role_id != null) return row.role_id
  const dbName = BUILTIN_ROLE_CODE_TO_DB_NAME[row.role]
  if (dbName) {
    return roleOptions.find((r) => r.name === dbName)?.id ?? null
  }
  return roleOptions.find((r) => r.name === row.role)?.id ?? null
}

export function displayUserRoleName(
  row: { role_name?: string | null; role?: string | null } | null | undefined,
  t?: (key: string) => string,
): string {
  if (!row) return '—'
  const name = row.role_name?.trim()
  if (name) return name
  const code = row.role?.trim()
  if (!code) return '—'
  if (BUILTIN_ROLE_CODE_TO_DB_NAME[code]) {
    return BUILTIN_ROLE_CODE_TO_DB_NAME[code]
  }
  if (t) {
    const localized = builtinRoleDisplayName(code, t)
    if (localized !== code) return localized
  }
  return code
}
