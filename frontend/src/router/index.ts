import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/modules/auth/stores/user'
import { routes } from './routes'

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ナビゲーションガード
router.beforeEach(async (to, _from, next) => {
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - Smart-EMAP`
  }

  const userStore = useUserStore()

  // 認証チェック
  if (to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      next({
        path: '/login',
        query: { redirect: to.fullPath },
      })
      return
    }
    // ページ権限チェック（meta.permission: 例 'all' は管理者のみ）
    const requiredPermission = to.meta.permission as string | undefined
    if (requiredPermission && !userStore.hasPermission(requiredPermission)) {
      next({ path: '/dashboard' })
      const { ElMessage } = await import('element-plus')
      ElMessage.warning('このページへのアクセス権限がありません')
      return
    }
    try {
      const { getUserInfo } = await import('@/api/auth')
      const userData = await getUserInfo() as unknown
      if (userData && typeof userData === 'object' && userData !== null && 'id' in userData) {
        userStore.setUser(userData as import('@/modules/auth/stores/user').User, false)
      }
      next()
    } catch (error: any) {
      if (error?.response?.status === 401) {
        const errorDetail = error?.response?.data?.detail || ''
        const isForceLogout = error?.response?.headers?.['x-force-logout'] === 'true'
        const isOtherDeviceLogin =
          errorDetail.includes('他のデバイス') ||
          errorDetail.includes('他のデバイスでログイン') ||
          isForceLogout

        if (isOtherDeviceLogin) {
          const { ElMessage } = await import('element-plus')
          ElMessage.error({
            message:
              'このアカウントは他のデバイスでログインされています。再度ログインしてください。',
            duration: 5000,
            showClose: true,
          })
        }
        userStore.clearLocalSession()
        next('/login')
        return
      }
      next()
    }
  } else {
    if ((to.path === '/login' || to.path === '/') && userStore.isAuthenticated) {
      const redirect = to.query.redirect as string
      next(redirect || '/dashboard')
    } else {
      next()
    }
  }
})

export default router
