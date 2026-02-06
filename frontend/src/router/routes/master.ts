import type { RouteRecordRaw } from 'vue-router'

/** マスタ管理モジュールルート */
export const masterRoutes: RouteRecordRaw[] = [
  {
    path: 'master',
    redirect: { name: 'ProductList' },
  },
  {
    path: 'master/product',
    name: 'ProductList',
    component: () => import('@/views/master/product/ProductList.vue'),
    meta: { title: '製品マスタ', requiresAuth: true },
  },
  {
    path: 'master/material',
    name: 'MaterialList',
    component: () => import('@/views/master/material/MaterialList.vue'),
    meta: { title: '材料マスタ', requiresAuth: true },
  },
  {
    path: 'master/supplier',
    name: 'SupplierList',
    component: () => import('@/views/master/supplier/SupplierList.vue'),
    meta: { title: '仕入先マスタ', requiresAuth: true },
  },
  {
    path: 'master/process-route',
    name: 'ProcessRouteList',
    component: () => import('@/views/master/processRoute/ProcessRouteList.vue'),
    meta: { title: '工程ルートマスタ', requiresAuth: true },
  },
  {
    path: 'master/process-route/:route_cd/steps',
    name: 'RouteStepList',
    component: () => import('@/views/master/processRoute/ProcessRouteStepEditor.vue'),
    meta: { title: 'ルートステップ編集', requiresAuth: true },
  },
  {
    path: 'master/bom',
    name: 'Bom',
    component: () => import('@/views/master/Bom.vue'),
    meta: { title: 'BOM', requiresAuth: true },
  },
]
