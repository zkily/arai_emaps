import type { RouteRecordRaw } from 'vue-router'
import { mesRegistrationProcesses } from '@/views/mes/actualCollectionRegistration/shared/registrationProcesses'

const routeGroup = 'MES > 実績登録'

/** 実績登録ルート（views/mes/actualCollectionRegistration）。MainLayout children に spread する。 */
export const mesActualCollectionRegistrationRoutes: RouteRecordRaw[] = [
  { path: 'mes/actualCollectionRegistration', redirect: '/mes/actualCollectionRegistration/cutting' },
  ...mesRegistrationProcesses.map((process) => ({
    path: `mes/actualCollectionRegistration/${process.slug}`,
    name: `Mes${process.componentPrefix}ActualCollectionRegistration`,
    component: () =>
      import(
        `@/views/mes/actualCollectionRegistration/${process.slug}/${process.componentPrefix}ActualCollectionRegistration.vue`
      ),
    meta: {
      title: process.pageTitle,
      group: routeGroup,
      requiresAuth: true,
    },
  })),
]
