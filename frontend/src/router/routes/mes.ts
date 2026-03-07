import type { RouteRecordRaw } from 'vue-router'

/** MES モジュールルート */
export const mesRoutes: RouteRecordRaw[] = [
  {
    path: '/mes',
    name: 'MES',
    meta: { title: 'MES', requiresAuth: true },
    children: [
      {
        path: 'execution',
        name: 'Execution',
        component: () => import('@/views/mes/Execution.vue'),
        meta: { title: '製造実行' },
      },
      {
        path: 'quality',
        name: 'Quality',
        component: () => import('@/views/mes/Quality.vue'),
        meta: { title: '品質管理' },
      },
    ],
  },
]
