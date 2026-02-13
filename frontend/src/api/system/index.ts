/**
 * システム管理 API
 * ユーザー管理、組織管理、権限・ロール管理
 */
import request from '@/shared/api/request'

const BASE = '/api/system'

// ========== 型定義 ==========

export type UserStatus = 'active' | 'locked' | 'inactive'

export interface UserListItem {
  id: number
  username: string
  full_name: string | null
  email: string
  department: string | null
  role: string
  status: UserStatus
  two_factor: boolean
  last_login: string | null
}

export interface UserSearchParams {
  keyword?: string
  department_id?: number
  status?: UserStatus
  page?: number
  page_size?: number
}

export interface PaginatedUserResponse {
  items: UserListItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface UserCreateParams {
  username: string
  email: string
  full_name?: string
  department_id?: number
  role_id?: number
  two_factor_enabled?: boolean
  password: string
}

export interface UserUpdateParams {
  email?: string
  full_name?: string
  department_id?: number
  role_id?: number
  two_factor_enabled?: boolean
  status?: UserStatus
}

export interface OrganizationTreeNode {
  id: number
  code: string
  name: string
  type: string
  parent_id: number | null
  children: OrganizationTreeNode[]
}

export interface Organization {
  id: number
  code: string
  name: string
  type: 'company' | 'site' | 'department' | 'section' | 'line'
  parent_id: number | null
  manager_name: string | null
  location: string | null
  phone: string | null
  email: string | null
  description: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface OrganizationCreateParams {
  code: string
  name: string
  type: 'company' | 'site' | 'department' | 'section' | 'line'
  parent_id?: number
  manager_name?: string
  location?: string
  phone?: string
  email?: string
  description?: string
  sort_order?: number
}

export interface OrganizationUpdateParams {
  name?: string
  type?: 'company' | 'site' | 'department' | 'section' | 'line'
  parent_id?: number
  manager_name?: string
  location?: string
  phone?: string
  email?: string
  description?: string
  sort_order?: number
  is_active?: boolean
}

export interface RoleListItem {
  id: number
  name: string
  is_system: boolean
  user_count: number
}

export interface OperationPermission {
  module: string
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
  can_export: boolean
  can_approve: boolean
}

export interface Role {
  id: number
  name: string
  description: string | null
  is_system: boolean
  data_scope: 'self' | 'department' | 'department_below' | 'all' | 'custom'
  custom_departments: string[] | null
  is_active: boolean
  user_count: number
  menu_permissions: number[]
  operation_permissions: OperationPermission[]
  created_at: string
  updated_at: string
}

export interface RoleCreateParams {
  name: string
  description?: string
  data_scope?: 'self' | 'department' | 'department_below' | 'all' | 'custom'
  custom_departments?: string[]
  menu_permissions?: number[]
  operation_permissions?: OperationPermission[]
}

export interface RoleUpdateParams {
  name?: string
  description?: string
  data_scope?: 'self' | 'department' | 'department_below' | 'all' | 'custom'
  custom_departments?: string[]
  menu_permissions?: number[]
  operation_permissions?: OperationPermission[]
  is_active?: boolean
}

export interface MenuTreeNode {
  id: number
  code: string
  label: string
  children: MenuTreeNode[]
}

export interface MenuItem {
  id: number
  code: string
  name: string
  parent_id: number | null
  path: string | null
  icon: string | null
  sort_order: number
  is_active: boolean
}

export interface MenuCreateParams {
  code: string
  name: string
  parent_id?: number | null
  path?: string | null
  icon?: string | null
  sort_order?: number
  is_active?: boolean
}

export interface MenuUpdateParams {
  name?: string
  parent_id?: number | null
  path?: string | null
  icon?: string | null
  sort_order?: number
  is_active?: boolean
}

export interface MenuSyncItemParams {
  code: string
  name: string
  path?: string | null
  icon?: string | null
  parent_code?: string | null
  sort_order?: number
}

// ========== ユーザー管理 API ==========

/** ユーザー一覧取得 */
export function getUsers(params?: UserSearchParams) {
  return request.get<PaginatedUserResponse>(`${BASE}/users`, { params })
}

/** ユーザー作成 */
export function createUser(data: UserCreateParams) {
  return request.post<UserListItem>(`${BASE}/users`, data)
}

/** ユーザー更新 */
export function updateUser(userId: number, data: UserUpdateParams) {
  return request.put<UserListItem>(`${BASE}/users/${userId}`, data)
}

/** ユーザーロック */
export function lockUser(userId: number) {
  return request.post(`${BASE}/users/${userId}/lock`)
}

/** ユーザーロック解除 */
export function unlockUser(userId: number) {
  return request.post(`${BASE}/users/${userId}/unlock`)
}

/** パスワード再設定（新しいパスワードで直接更新） */
export function resetUserPassword(userId: number, data: { new_password: string }) {
  return request.post(`${BASE}/users/${userId}/reset-password`, data)
}

// ========== 組織管理 API ==========

/** 組織一覧取得 */
export function getOrganizations() {
  return request.get<Organization[]>(`${BASE}/organizations`)
}

/** 組織ツリー取得（キャッシュ回避のため params で _t を渡すとクエリに付与） */
export function getOrganizationTree(params?: { _t?: number }) {
  return request.get<OrganizationTreeNode[]>(`${BASE}/organizations/tree`, { params })
}

/** 組織詳細取得 */
export function getOrganization(orgId: number) {
  return request.get<Organization>(`${BASE}/organizations/${orgId}`)
}

/** 組織作成 */
export function createOrganization(data: OrganizationCreateParams) {
  return request.post<Organization>(`${BASE}/organizations`, data)
}

/** 組織更新 */
export function updateOrganization(orgId: number, data: OrganizationUpdateParams) {
  return request.put<Organization>(`${BASE}/organizations/${orgId}`, data)
}

/** 組織削除 */
export function deleteOrganization(orgId: number) {
  return request.delete(`${BASE}/organizations/${orgId}`)
}

// ========== ロール・権限管理 API ==========

/** ロール一覧取得 */
export function getRoles() {
  return request.get<RoleListItem[]>(`${BASE}/roles`)
}

/** 現在の利用者数（WebSocket接続中のユニークユーザー数） */
export function getOnlineCount() {
  return request.get<{ online_count: number }>(`${BASE}/stats/online`)
}

/** ロール詳細取得 */
export function getRole(roleId: number) {
  return request.get<Role>(`${BASE}/roles/${roleId}`)
}

/** ロール作成 */
export function createRole(data: RoleCreateParams) {
  return request.post<Role>(`${BASE}/roles`, data)
}

/** ロール更新 */
export function updateRole(roleId: number, data: RoleUpdateParams) {
  return request.put<Role>(`${BASE}/roles/${roleId}`, data)
}

/** ロール削除 */
export function deleteRole(roleId: number) {
  return request.delete(`${BASE}/roles/${roleId}`)
}

// ========== メニュー API ==========

/** メニュー一覧取得（管理用: includeInactive=true で無効含む） */
export function getMenus(includeInactive = false) {
  return request.get<MenuItem[]>(`${BASE}/menus`, { params: { include_inactive: includeInactive } })
}

/** メニューツリー取得 */
export function getMenuTree() {
  return request.get<MenuTreeNode[]>(`${BASE}/menus/tree`)
}

/** メニュー新規登録 */
export function createMenu(data: MenuCreateParams) {
  return request.post<MenuItem>(`${BASE}/menus`, data)
}

/** メニュー更新 */
export function updateMenu(menuId: number, data: MenuUpdateParams) {
  return request.put<MenuItem>(`${BASE}/menus/${menuId}`, data)
}

/** メニュー削除 */
export function deleteMenu(menuId: number) {
  return request.delete(`${BASE}/menus/${menuId}`)
}

/** ルート定義からメニュー同期（既存は更新、新規は追加） */
export function syncMenus(items: MenuSyncItemParams[]) {
  return request.post<MenuItem[]>(`${BASE}/menus/sync`, { items })
}

// ========== システムログ API ==========

const SETTINGS_BASE = `${BASE}/settings`

export interface OperationLogItem {
  id: number
  timestamp: string
  user_id: number | null
  username: string | null
  action: string
  module: string | null
  target: string | null
  target_id: number | null
  ip_address: string | null
  user_agent: string | null
  details: Record<string, unknown> | null
  created_at: string
}

export interface ErrorLogItem {
  id: number
  timestamp: string
  level: string
  source: string | null
  message: string
  stack_trace: string | null
  user_id: number | null
  request_id: string | null
  extra_data: Record<string, unknown> | null
  created_at: string
}

export interface ApiLogItem {
  id: number
  timestamp: string
  method: string
  endpoint: string
  status_code: number
  duration: number | null
  client: string | null
  user_id: number | null
  ip_address: string | null
  created_at: string
}

export interface PaginatedLogs<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface OperationLogParams {
  user?: string
  action?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface ErrorLogParams {
  level?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface ApiLogParams {
  endpoint?: string
  status?: string
  page?: number
  page_size?: number
}

/** 操作ログ一覧取得 */
export function getOperationLogs(params?: OperationLogParams) {
  return request.get<PaginatedLogs<OperationLogItem>>(`${SETTINGS_BASE}/logs/operations`, { params })
}

/** 操作ログCSVエクスポート（Blobで返す） */
export function exportOperationLogs(params?: { user?: string; action?: string; start_date?: string; end_date?: string }) {
  return request.get<Blob>(`${SETTINGS_BASE}/logs/operations/export`, {
    params,
    responseType: 'blob',
  })
}

/** エラーログ一覧取得 */
export function getErrorLogs(params?: ErrorLogParams) {
  return request.get<PaginatedLogs<ErrorLogItem>>(`${SETTINGS_BASE}/logs/errors`, { params })
}

/** APIログ一覧取得 */
export function getApiLogs(params?: ApiLogParams) {
  return request.get<PaginatedLogs<ApiLogItem>>(`${SETTINGS_BASE}/logs/api`, { params })
}

// ========== ファイル監視設定 ==========

export interface FileWatcherSettings {
  stockFiles: string[]
  materialFiles: string[]
  pickingFiles: string[]
  enabled: Record<string, boolean>
  excelWatcherEnabled: boolean
}

/** ファイル監視の有効/無効一覧取得 */
export function getFileWatcherSettings() {
  return request.get<FileWatcherSettings>(`${SETTINGS_BASE}/file-watcher`)
}

/** ファイル監視の有効/無効を保存 */
export function updateFileWatcherSettings(payload: {
  enabled: Record<string, boolean>
  excelWatcherEnabled?: boolean
}) {
  return request.put<{ message: string; enabled: Record<string, boolean>; excelWatcherEnabled: boolean }>(
    `${SETTINGS_BASE}/file-watcher`,
    payload
  )
}
