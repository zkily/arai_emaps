import { builtinRoleDisplayName } from '@/utils/builtinRoleDisplayName'

/** 組み込みロールコード → roles テーブルの日本語名（backend ROLE_NAME_TO_CODE と対応） */
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
  row: { role_name?: string | null; role: string },
  t: (key: string) => string,
): string {
  if (row.role_name) return row.role_name
  return builtinRoleDisplayName(row.role, t)
}
