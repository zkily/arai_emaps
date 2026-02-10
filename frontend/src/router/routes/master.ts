import type { RouteRecordRaw } from 'vue-router'

/** マスタ管理モジュールルート */
export const masterRoutes: RouteRecordRaw[] = [
  {
    path: 'master',
    name: 'MasterHome',
    component: () => import('@/views/master/MasterList.vue'),
    meta: { title: 'マスタホーム', requiresAuth: true },
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
    path: 'master/process',
    name: 'ProcessList',
    component: () => import('@/views/master/process/ProcessList.vue'),
    meta: { title: '工程マスタ', requiresAuth: true },
  },
  {
    path: 'master/process-route',
    name: 'ProcessRouteList',
    component: () => import('@/views/master/processRoute/ProcessRouteList.vue'),
    meta: { title: '工程ルートマスタ', requiresAuth: true },
  },
  {
    path: 'master/customer',
    name: 'CustomerList',
    component: () => import('@/views/master/customer/CustomerList.vue'),
    meta: { title: '顧客マスタ', requiresAuth: true },
  },
  {
    path: 'master/carrier',
    name: 'CarrierList',
    component: () => import('@/views/master/carrier/CarrierList.vue'),
    meta: { title: '運送便マスタ', requiresAuth: true },
  },
  {
    path: 'master/machine',
    name: 'MachineList',
    component: () => import('@/views/master/machine/MachineList.vue'),
    meta: { title: '設備マスタ', requiresAuth: true },
  },
  {
    path: 'master/destination',
    name: 'DestinationList',
    component: () => import('@/views/master/destination/DestinationList.vue'),
    meta: { title: '納入先マスタ', requiresAuth: true },
  },
  {
    path: 'master/destination/holiday',
    name: 'DestinationHoliday',
    component: () => import('@/views/master/destination/DestinationHoliday.vue'),
    meta: { title: '納入先休日設定', requiresAuth: true },
  },
  {
    path: 'master/process-route/:route_cd/steps',
    name: 'RouteStepList',
    component: () => import('@/views/master/processRoute/ProcessRouteStepEditor.vue'),
    meta: { title: 'ルートステップ編集', requiresAuth: true },
  },
  {
    path: 'master/product-process-route',
    name: 'ProductProcessRouteManager',
    component: () => import('@/views/master/productProcessRoute/ProductRouteStepManager.vue'),
    meta: { title: '製品別工程ルートマスタ', requiresAuth: true },
  },
  {
    path: 'master/bom',
    name: 'Bom',
    component: () => import('@/views/master/Bom.vue'),
    meta: { title: 'BOM', requiresAuth: true },
  },
]
