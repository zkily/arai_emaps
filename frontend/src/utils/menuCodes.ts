import { menuConfig } from '@/router/menuConfig'

const pathToCodes = new Map<string, string[]>()

for (const item of menuConfig) {
  if (!item.path) continue
  const list = pathToCodes.get(item.path) ?? []
  list.push(item.code)
  pathToCodes.set(item.path, list)
}

// 旧「外注メッキ受入」権限でも統合後の外注メッキ画面を開ける
const platingPath = '/erp/purchase/outsourcing/plating-order'
const platingCodes = pathToCodes.get(platingPath) ?? []
if (!platingCodes.includes('ERP_OUTSOURCING_PLATING_RECEIVING')) {
  platingCodes.push('ERP_OUTSOURCING_PLATING_RECEIVING')
  pathToCodes.set(platingPath, platingCodes)
}

/** 同一路由可能对应多个菜单 code（各模块ホーム等） */
export function codesForPath(path: string): string[] {
  return pathToCodes.get(path) ?? []
}
