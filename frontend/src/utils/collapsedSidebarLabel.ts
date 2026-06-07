/** 折叠侧栏图标下方显示的简短名称（与 Android SidebarMenu.kt 保持一致） */
export function collapsedSidebarLabel(code: string, label: string): string {
  switch (code) {
    case 'DASHBOARD':
      return 'ホーム'
    case 'ERP':
      return 'ERP'
    case 'APS':
      return 'APS'
    case 'MES':
      return 'MES'
    case 'FIN':
      return 'ACR'
    case 'MASTER':
      return 'マスタ'
    case 'SYSTEM':
      return 'システム'
    default:
      return label
        .split(/[(（]/)[0]
        .trim()
        .slice(0, 6)
  }
}
