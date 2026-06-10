import { menuConfig } from '@/router/menuConfig'

const pathToCodes = new Map<string, string[]>()

for (const item of menuConfig) {
  if (!item.path) continue
  const list = pathToCodes.get(item.path) ?? []
  list.push(item.code)
  pathToCodes.set(item.path, list)
}

/** 同一路由可能对应多个菜单 code（各模块ホーム等） */
export function codesForPath(path: string): string[] {
  return pathToCodes.get(path) ?? []
}
