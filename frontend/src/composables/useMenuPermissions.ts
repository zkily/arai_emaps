import { computed } from 'vue'
import { useUserStore } from '@/modules/auth/stores/user'
import type { MenuTreeNode } from '@/composables/useMenuTree'
import {
  canAccessMenuCode as canAccessMenuCodeForUser,
  canAccessPath as canAccessPathForUser,
  hasMenuCode as hasMenuCodeForUser,
  isAdminUser,
  usesMenuCodePermissions as usesMenuCodePermissionsForUser,
} from '@/utils/menuPermissions'

export function filterMenuTreeForUser(
  node: MenuTreeNode,
  canAccess: (code: string) => boolean,
): MenuTreeNode | null {
  if (node.path) {
    return canAccess(node.code) ? node : null
  }

  const children = node.children
    .map((child) => filterMenuTreeForUser(child, canAccess))
    .filter((child): child is MenuTreeNode => child != null)

  if (children.length === 0) return null
  return { ...node, children }
}

export function useMenuPermissions() {
  const userStore = useUserStore()
  const user = computed(() => userStore.user)

  const usesMenuCodePermissions = computed(() => usesMenuCodePermissionsForUser(user.value))

  function hasMenuCode(code: string) {
    return hasMenuCodeForUser(user.value, code)
  }

  function canAccessMenuCode(code: string) {
    return canAccessMenuCodeForUser(user.value, code)
  }

  function canAccessPath(path: string) {
    return canAccessPathForUser(user.value, path)
  }

  function filterMenuTree(node: MenuTreeNode | null): MenuTreeNode | null {
    if (!node) return null
    return filterMenuTreeForUser(node, canAccessMenuCode)
  }

  return {
    user,
    isAdmin: computed(() => isAdminUser(user.value)),
    usesMenuCodePermissions,
    hasMenuCode,
    canAccessMenuCode,
    canAccessPath,
    filterMenuTree,
  }
}
