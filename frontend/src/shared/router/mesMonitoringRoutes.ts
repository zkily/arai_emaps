import type { RouteRecordRaw } from 'vue-router'
import { mesMonitoringProcesses } from '@/views/mes/monitoring/shared/monitorProcesses'

const routeGroup = 'MES > モニタリング'

/** モニタリングルート（views/mes/monitoring） */
export const mesMonitoringRoutes: RouteRecordRaw[] = [
  { path: 'mes/monitoring', redirect: '/mes/monitoring/inspection' },
  ...mesMonitoringProcesses.map((process) => ({
    path: `mes/monitoring/${process.slug}`,
    name: `Mes${process.componentName}`,
    component: () =>
      import(
        `@/views/mes/monitoring/${process.slug}/${process.componentName}.vue`
      ),
    meta: {
      title: process.pageTitle,
      group: routeGroup,
      requiresAuth: true,
      menuCode: process.menuCode,
    },
  })),
  {
    path: 'mes/monitoring/factory-layout',
    name: 'MesFactoryLayout',
    component: () => import('@/views/mes/factoryLayout/FactoryLayoutPage.vue'),
    meta: {
      title: '工場レイアウト',
      group: routeGroup,
      requiresAuth: true,
      menuCode: 'MES_MONITOR_FACTORY_LAYOUT',
    },
  },
]
