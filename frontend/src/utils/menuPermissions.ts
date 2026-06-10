import type { User } from '@/modules/auth/stores/user'
import { codesForPath } from '@/utils/menuCodes'

export function isAdminUser(user: User | null | undefined): boolean {
  return user?.permissions.includes('all') ?? false
}

/** P0: ログイン済みユーザーは常に menu_codes によるページ制御（admin は全ページ許可） */
export function usesMenuCodePermissions(user: User | null | undefined): boolean {
  return user != null
}

export function hasMenuCode(user: User | null | undefined, code: string): boolean {
  if (isAdminUser(user)) return true
  return user?.menu_codes?.includes(code) ?? false
}

export function canAccessMenuCode(user: User | null | undefined, code: string): boolean {
  if (!user) return false
  if (code === 'DASHBOARD') return true
  if (isAdminUser(user)) return true
  if (code === 'SYSTEM' || code.startsWith('SYSTEM_')) return false
  return hasMenuCode(user, code)
}

export function canAccessPath(user: User | null | undefined, path: string): boolean {
  const normalized = path.trim() || '/dashboard'
  if (!user) return false
  if (normalized === '/access-denied') return true
  if (normalized === '/dashboard') return true
  if (normalized === '/system' || normalized.startsWith('/system/')) return isAdminUser(user)

  const codes = codesForPath(normalized)
  if (codes.length === 0) {
    // menuConfig 未登録のルート（プロフィール等）は menu_codes 対象外
    return true
  }
  if (isAdminUser(user)) return true
  return codes.some((code) => hasMenuCode(user, code))
}
