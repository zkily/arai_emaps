import type { RouteRecordRaw } from 'vue-router'

/** 原価管理ルート（views/fin/costing）。finRoutes の後に spread する。 */
export const finCostingRoutes: RouteRecordRaw[] = [
  { path: 'fin/costing', name: 'FinCostingHome', component: () => import('@/views/fin/costing/Costing.vue'), meta: { title: '原価ホーム', group: 'FIN', requiresAuth: true } },
  { path: 'fin/costing/standard', name: 'FinStandardCosting', component: () => import('@/views/fin/costing/cost/StandardCosting.vue'), meta: { title: '標準原価計算', group: 'FIN', requiresAuth: true } },
  { path: 'fin/costing/actual', name: 'FinActualCosting', component: () => import('@/views/fin/costing/cost/ActualCosting.vue'), meta: { title: '実際原価計算', group: 'FIN', requiresAuth: true } },
  { path: 'fin/costing/variance', name: 'FinVarianceAnalysis', component: () => import('@/views/fin/costing/cost/VarianceAnalysis.vue'), meta: { title: '原価差異分析', group: 'FIN', requiresAuth: true } },
  { path: 'fin/costing/allocation', name: 'FinAllocationCalc', component: () => import('@/views/fin/costing/cost/AllocationCalc.vue'), meta: { title: '配賦計算', group: 'FIN', requiresAuth: true } },
  { path: 'fin/costing/wip', name: 'FinWipEvaluation', component: () => import('@/views/fin/costing/cost/WipEvaluation.vue'), meta: { title: '仕掛品(WIP)評価', group: 'FIN', requiresAuth: true } },
  { path: 'fin/costing/equipment', name: 'FinEquipmentLedger', component: () => import('@/views/fin/costing/asset/EquipmentLedger.vue'), meta: { title: '設備台帳', group: 'FIN', requiresAuth: true } },
  { path: 'fin/costing/depreciation', name: 'FinDepreciation', component: () => import('@/views/fin/costing/asset/Depreciation.vue'), meta: { title: '減価償却計算', group: 'FIN', requiresAuth: true } },
  // 旧 ERP 原価パス → FIN
  { path: 'erp/costing', redirect: '/fin/costing' },
  { path: 'erp/costing/standard', redirect: '/fin/costing/standard' },
  { path: 'erp/costing/actual', redirect: '/fin/costing/actual' },
  { path: 'erp/costing/variance', redirect: '/fin/costing/variance' },
  { path: 'erp/costing/allocation', redirect: '/fin/costing/allocation' },
  { path: 'erp/costing/wip', redirect: '/fin/costing/wip' },
  { path: 'erp/costing/equipment', redirect: '/fin/costing/equipment' },
  { path: 'erp/costing/depreciation', redirect: '/fin/costing/depreciation' },
  { path: 'erp/costing/journal', redirect: '/fin/accounting/journals' },
  { path: 'erp/costing/accounting-export', redirect: '/fin/accounting/import' },
  { path: 'erp/costing/billing', redirect: '/fin/receivables/invoices' },
  { path: 'erp/costing/payment', redirect: '/fin/payables/payments' },
]
