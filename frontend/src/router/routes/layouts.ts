import type { RouteRecordRaw } from 'vue-router'

/**
 * レイアウト配下のベースルート（Home / Login / Redirect / Dashboard）
 * layouts/pages と対応
 */
export const layoutPageRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/layouts/pages/Home.vue'),
    meta: { title: 'ホーム' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/layouts/pages/Login.vue'),
    meta: { title: 'ログイン' },
  },
  {
    path: '/redirect/:path(.*)',
    name: 'Redirect',
    component: () => import('@/layouts/pages/Redirect.vue'),
    meta: { title: 'リダイレクト' },
  },
]

/** メインレイアウト内のダッシュボードページ */
export const dashboardRoute: RouteRecordRaw = {
  path: 'dashboard',
  name: 'Dashboard',
  component: () => import('@/layouts/pages/DashboardHome.vue'),
  meta: { title: 'ダッシュボード', requiresAuth: true },
}
