import type { RouteRecordRaw } from 'vue-router'

/** ログインユーザー向け（権限 all 不要） */
export const accountRoutes: RouteRecordRaw[] = [
  {
    path: 'account/profile',
    name: 'UserProfile',
    component: () => import('@/views/account/UserProfile.vue'),
    meta: { title: 'プロフィール', requiresAuth: true },
  },
]
