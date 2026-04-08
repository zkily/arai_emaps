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
        name: 'FormingPlanning',
        component: () => import('@/views/aps/productionPlanCreation/FormingPlanning.vue'),
        meta: { title: '成型計画作成' },
      },
      {
        path: 'cutting-planning',
        name: 'CuttingPlanning',
        component: () => import('@/views/aps/productionPlanCreation/CuttingPlanning.vue'),
        meta: { title: '切断計画作成' },
      },
      {
        path: 'planning-list',
        name: 'FormingPlanningList',
        component: () => import('@/views/aps/productionPlanOverview/FormingPlanningList.vue'),
        meta: { title: '成型計画一覧' },
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
        path: 'capacity-matrix',
        name: 'CapacityMatrix',
        component: () => import('@/views/aps/CapacityMatrix.vue'),
        meta: { title: '設備稼働時間表' },
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
        meta: { title: 'APSロット計画' },
      },
    ],
  },
]
