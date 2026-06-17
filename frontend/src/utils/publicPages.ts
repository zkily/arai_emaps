/** ログイン不要で開ける画面（操作説明・マニュアル等） */
const PUBLIC_PATH_PREFIXES = [
  '/login',
  '/manuals',
  '/erp/production/plan-baseline/help',
] as const

export function isPublicPagePath(path: string = window.location.pathname): boolean {
  if (path === '/') return true
  return PUBLIC_PATH_PREFIXES.some(
    (prefix) => path === prefix || path.startsWith(`${prefix}/`),
  )
}
