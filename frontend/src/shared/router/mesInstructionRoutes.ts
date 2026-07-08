import type { RouteRecordRaw } from 'vue-router'

/** 生産指示ルート（views/mes/productionInstruction）。MainLayout children に spread する。 */
export const mesInstructionRoutes: RouteRecordRaw[] = [
  { path: 'mes/productionInstruction/cutting', name: 'MesCuttingInstruction', component: () => import('@/views/mes/productionInstruction/cutting/CuttingInstruction.vue'), meta: { title: '切断・面取指示', group: 'MES > 生産指示', requiresAuth: true } },
  { path: 'mes/productionInstruction/forming', name: 'MesFormingInstruction', component: () => import('@/views/mes/productionInstruction/forming/FormingInstruction.vue'), meta: { title: '成型指示', group: 'MES > 生産指示', requiresAuth: true } },
  { path: 'mes/productionInstruction/welding', name: 'MesWeldingInstruction', component: () => import('@/views/mes/productionInstruction/welding/WeldingInstruction.vue'), meta: { title: '溶接指示', group: 'MES > 生産指示', requiresAuth: true } },
  { path: 'mes/productionInstruction/plating', name: 'MesPlatingInstruction', component: () => import('@/views/mes/productionInstruction/plating/PlatingInstruction.vue'), meta: { title: 'メッキ指示', group: 'MES > 生産指示', requiresAuth: true } },
  { path: 'mes/productionInstruction/product-label', name: 'MesProductLabelIssuance', component: () => import('@/views/mes/productionInstruction/productLabel/ProductLabelIssuance.vue'), meta: { title: '製品ラベル発行', group: 'MES > 生産指示', requiresAuth: true } },
  // 旧パス互換
  { path: 'mes/instruction/cutting', redirect: '/mes/productionInstruction/cutting' },
  { path: 'mes/instruction/forming', redirect: '/mes/productionInstruction/forming' },
  { path: 'mes/instruction/welding', redirect: '/mes/productionInstruction/welding' },
  { path: 'mes/instruction/plating', redirect: '/mes/productionInstruction/plating' },
  { path: 'mes/instruction', redirect: '/mes/productionInstruction/cutting' },
  { path: 'erp/production/instruction/cutting', redirect: '/mes/productionInstruction/cutting' },
  { path: 'erp/production/instruction/forming', redirect: '/mes/productionInstruction/forming' },
  { path: 'erp/production/instruction/welding', redirect: '/mes/productionInstruction/welding' },
  { path: 'erp/production/instruction/plating', redirect: '/mes/productionInstruction/plating' },
  { path: 'erp/production/instruction', redirect: '/mes/productionInstruction/cutting' },
]
