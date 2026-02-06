import type { RouteRecordRaw } from 'vue-router'
import { baseRoutes } from './base'
import { erpRoutes } from './erp'
import { apsRoutes } from './aps'
import { mesRoutes } from './mes'
import { masterRoutes } from './master'
import { systemRoutes } from './system'
import { dashboardRoute } from './layouts'

/** レイアウト内に表示するルート（認証必須） */
const layoutRoutes: RouteRecordRaw = {
  path: '/',
  component: () => import('@/layouts/MainLayout.vue'),
  meta: { requiresAuth: true },
  children: [
    // ダッシュボード（layouts/pages で管理）
    dashboardRoute,
    // ERP モジュール（子ルートを展開）
    ...erpRoutes[0].children || [],
    // APS モジュール（子ルートを展開）
    ...(apsRoutes[0].children || []).map(route => ({
      ...route,
      path: `aps/${route.path}`,
      meta: { ...route.meta, requiresAuth: true },
    })),
    // MES モジュール（子ルートを展開）
    ...(mesRoutes[0].children || []).map(route => ({
      ...route,
      path: `mes/${route.path}`,
      meta: { ...route.meta, requiresAuth: true },
    })),
    // マスタ管理モジュール
    ...masterRoutes,
    // システム管理モジュール
    ...systemRoutes,
  ],
}

/** 全ルートを集約 */
export const routes: RouteRecordRaw[] = [
  ...baseRoutes,
  layoutRoutes,
]

// 各モジュールを個別 export（必要に応じて利用）
export { baseRoutes } from './base'
export { erpRoutes } from './erp'
export { apsRoutes } from './aps'
export { mesRoutes } from './mes'
export { masterRoutes } from './master'
export { systemRoutes } from './system'
