/** 操作権限モジュール（RolePermission.vue / バックエンド operation_modules.py と同期） */
export const OPERATION_MODULES = [
  '販売管理',
  '購買管理',
  '在庫管理',
  '原価・会計',
  '経理・原価・人事',
  '生産計画',
  '製造実行',
  '品質管理',
  'マスタ管理',
  'システム管理',
] as const

export type OperationModule = (typeof OPERATION_MODULES)[number]

export const OPERATION_MODULE_SALES = '販売管理' as const
export const OPERATION_MODULE_PURCHASE = '購買管理' as const
export const OPERATION_MODULE_INVENTORY = '在庫管理' as const
export const OPERATION_MODULE_COST = '原価・会計' as const
export const OPERATION_MODULE_FINANCE = '経理・原価・人事' as const
export const OPERATION_MODULE_PRODUCTION_PLAN = '生産計画' as const
export const OPERATION_MODULE_MES = '製造実行' as const
export const OPERATION_MODULE_QUALITY = '品質管理' as const
export const OPERATION_MODULE_MASTER = 'マスタ管理' as const
export const OPERATION_MODULE_SYSTEM = 'システム管理' as const

export type OperationAction = 'create' | 'edit' | 'delete' | 'export' | 'approve'
