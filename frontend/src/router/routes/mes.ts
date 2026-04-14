import type { RouteRecordRaw } from 'vue-router'

/** MES モジュールルート */
export const mesRoutes: RouteRecordRaw[] = [
  {
    path: '/mes',
    name: 'MES',
    meta: { title: 'MES', requiresAuth: true },
    children: [
      {
        path: 'instruction/forming',
        name: 'MesFormingInstruction',
        component: () => import('@/views/mes/instruction/forming/MesFormingInstruction.vue'),
        meta: {
          title: '成型指示',
          useApsSchedulePlanData: true,
        },
      },
    ],
  },
]
