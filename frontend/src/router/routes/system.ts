import type { RouteRecordRaw } from 'vue-router'

/** システム管理ルート（管理者権限 permission 'all' が必要） */
export const systemRoutes: RouteRecordRaw[] = [
  {
    path: 'system',
    name: 'System',
    component: () => import('@/views/system/SystemHome.vue'),
    meta: { title: 'システム管理', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/users',
    name: 'UserList',
    component: () => import('@/views/system/user/UserList.vue'),
    meta: { title: 'ユーザー管理', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/organization',
    name: 'OrganizationList',
    component: () => import('@/views/system/user/OrganizationList.vue'),
    meta: { title: '組織・部門管理', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/roles',
    name: 'RolePermission',
    component: () => import('@/views/system/user/RolePermission.vue'),
    meta: { title: '権限・ロール管理', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/numbering',
    name: 'NumberingRule',
    component: () => import('@/views/system/settings/NumberingRule.vue'),
    meta: { title: '採番ルール管理', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/workflow',
    name: 'WorkflowSetting',
    component: () => import('@/views/system/settings/WorkflowSetting.vue'),
    meta: { title: 'ワークフロー設定', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/notification',
    name: 'NotificationCenter',
    component: () => import('@/views/system/settings/NotificationCenter.vue'),
    meta: { title: '通知センター', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/logs',
    name: 'SystemLog',
    component: () => import('@/views/system/settings/SystemLog.vue'),
    meta: { title: 'システムログ', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/data',
    name: 'DataManagement',
    component: () => import('@/views/system/settings/DataManagement.vue'),
    meta: { title: 'データ管理', requiresAuth: true, permission: 'all' },
  },
  {
    path: 'system/menus',
    name: 'MenuManagement',
    component: () => import('@/views/system/settings/MenuManagement.vue'),
    meta: { title: 'メニュー管理', requiresAuth: true, permission: 'all' },
  },
]
