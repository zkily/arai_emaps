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
      {
        path: 'capacity',
        name: 'LineCapacity',
        component: () => import('@/views/aps/LineCapacity.vue'),
        meta: { title: '設備稼働設定' },
      },
      {
        path: 'daily-report',
        name: 'DailyReport',
        component: () => import('@/views/aps/DailyReport.vue'),
        meta: { title: '日別設備計画表' },
      },
      {
        path: 'batch-plans',
        name: 'ApsBatchPlans',
        component: () => import('@/views/aps/BatchPlans.vue'),
        meta: { title: 'APSバッチ計画' },
      },
    ],
  },
]
