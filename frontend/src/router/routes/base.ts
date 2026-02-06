import type { RouteRecordRaw } from 'vue-router'
import { layoutPageRoutes } from './layouts'

/** ベースルート（layouts/pages で管理） */
export const baseRoutes: RouteRecordRaw[] = [...layoutPageRoutes]
