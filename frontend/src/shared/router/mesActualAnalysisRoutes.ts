import type { RouteRecordRaw } from 'vue-router'
import { mesAnalysisProcesses } from '@/views/mes/actualAnalysis/shared/analysisProcesses'

const productivityGroup = 'MES > 実績分析項目 > 生産性分析'

interface ProcessRouteCategory {
  slug: string
  title: string
  group: string
  routePrefix: string
  typeSuffix: string
  importDir: string
}

const processRouteCategories: ProcessRouteCategory[] = [
  {
    slug: 'utilization',
    title: '稼働率分析',
    group: 'MES > 実績分析項目 > 稼働率分析',
    routePrefix: 'utilization',
    typeSuffix: 'Utilization',
    importDir: 'utilization',
  },
  {
    slug: 'progress',
    title: '進捗分析',
    group: 'MES > 実績分析項目 > 進捗分析',
    routePrefix: 'progress',
    typeSuffix: 'Progress',
    importDir: 'progress',
  },
  {
    slug: 'quality',
    title: '品質分析',
    group: 'MES > 実績分析項目 > 品質分析',
    routePrefix: 'quality',
    typeSuffix: 'Quality',
    importDir: 'quality',
  },
  {
    slug: 'cost',
    title: 'コスト分析',
    group: 'MES > 実績分析項目 > コスト分析',
    routePrefix: 'cost',
    typeSuffix: 'Cost',
    importDir: 'cost',
  },
]

function buildProcessAnalysisRoutes(category: ProcessRouteCategory): RouteRecordRaw[] {
  const basePath = `mes/actualAnalysis/${category.routePrefix}`
  return [
    { path: basePath, redirect: `/${basePath}/cutting` },
    ...mesAnalysisProcesses.map((process) => ({
      path: `${basePath}/${process.slug}`,
      name: `Mes${process.componentPrefix}${category.typeSuffix}Analysis`,
      component: () =>
        import(
          `@/views/mes/actualAnalysis/${category.importDir}/${process.componentPrefix}${category.typeSuffix}Analysis.vue`
        ),
      meta: {
        title: `${process.name} — ${category.title}`,
        group: category.group,
        requiresAuth: true,
      },
    })),
  ]
}

/** 実績分析ルート（views/mes/actualAnalysis）。MainLayout children に spread する。 */
export const mesActualAnalysisRoutes: RouteRecordRaw[] = [
  { path: 'mes/actualAnalysis/productivity', redirect: '/mes/actualAnalysis/productivity/cutting' },
  {
    path: 'mes/actualAnalysis/productivity/cutting',
    name: 'MesCuttingProductivityAnalysis',
    component: () => import('@/views/mes/actualAnalysis/productivity/CuttingProductivityAnalysis.vue'),
    meta: { title: '切断工程 — 生産性分析', group: productivityGroup, requiresAuth: true },
  },
  {
    path: 'mes/actualAnalysis/productivity/chamfering',
    name: 'MesChamferingProductivityAnalysis',
    component: () => import('@/views/mes/actualAnalysis/productivity/ChamferingProductivityAnalysis.vue'),
    meta: { title: '面取工程 — 生産性分析', group: productivityGroup, requiresAuth: true },
  },
  {
    path: 'mes/actualAnalysis/productivity/forming',
    name: 'MesFormingProductivityAnalysis',
    component: () => import('@/views/mes/actualAnalysis/productivity/FormingProductivityAnalysis.vue'),
    meta: { title: '成型工程 — 生産性分析', group: productivityGroup, requiresAuth: true },
  },
  {
    path: 'mes/actualAnalysis/productivity/plating',
    name: 'MesPlatingProductivityAnalysis',
    component: () => import('@/views/mes/actualAnalysis/productivity/PlatingProductivityAnalysis.vue'),
    meta: { title: 'メッキ工程 — 生産性分析', group: productivityGroup, requiresAuth: true },
  },
  {
    path: 'mes/actualAnalysis/productivity/welding',
    name: 'MesWeldingProductivityAnalysis',
    component: () => import('@/views/mes/actualAnalysis/productivity/WeldingProductivityAnalysis.vue'),
    meta: { title: '溶接生産性', group: productivityGroup, requiresAuth: true },
  },
  {
    path: 'mes/actualAnalysis/productivity/inspection',
    name: 'MesInspectionProductivityAnalysis',
    component: () => import('@/views/mes/actualAnalysis/productivity/InspectionProductivityAnalysis.vue'),
    meta: { title: '検査工程 — 生産性分析', group: productivityGroup, requiresAuth: true },
  },
  ...processRouteCategories.flatMap(buildProcessAnalysisRoutes),
]
