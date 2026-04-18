/**
 * 認証ユーザーに付与される組み込みロールコード（users.role）の表示名。
 * 文言は systemUser.user.* と共通（ユーザー管理画面と揃える）。
 */
const I18N_KEY_BY_CODE: Record<string, string> = {
  admin: 'systemUser.user.roleAdmin',
  user: 'systemUser.user.roleUser',
  manager: 'systemUser.user.roleManager',
  worker: 'systemUser.user.roleWorker',
  guest: 'systemUser.user.roleGuest',
  viewer: 'systemUser.user.roleViewer',
}

export function builtinRoleDisplayName(
  role: string | undefined | null,
  t: (key: string) => string
): string {
  if (role == null || role === '') return '—'
  const key = I18N_KEY_BY_CODE[role]
  return key ? t(key) : role
}
