import type { RouteRecordRaw } from 'vue-router'

/** APS モジュールルート */
export const apsRoutes: RouteRecordRaw[] = [
  {
    path: '/aps',
    name: 'APS',
    meta: { title: 'APS', requiresAuth: true },
    children: [
      {
        path: 'planning',
        name: 'Planning',
        component: () => import('@/views/aps/Planning.vue'),
        meta: { title: '生産計画' },
      },
      {
        path: 'scheduling',
        name: 'Scheduling',
        component: () => import('@/views/aps/Scheduling.vue'),
        meta: { title: 'スケジューリング' },
      },
    ],
  },
]
