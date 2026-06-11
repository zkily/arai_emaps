/** SidebarMenu / 権限・ロール管理で共通利用するルートメニューコード（表示順） */
export const SIDEBAR_ROOT_MENU_CODES = ['ERP', 'APS', 'MES', 'FIN', 'MASTER', 'SYSTEM'] as const

export type SidebarRootMenuCode = (typeof SIDEBAR_ROOT_MENU_CODES)[number]
