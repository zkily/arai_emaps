<template>
  <div class="role-permission">
    <!-- Modern Gradient Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon :size="28"><Key /></el-icon>
        </div>
        <div class="header-text">
          <h1>{{ t('systemUser.role.title') }}</h1>
          <p class="subtitle">{{ t('systemUser.role.subtitle') }}</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ roleList.length }}</span>
          <span class="stat-label">{{ t('systemUser.role.roleCount') }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value highlight">{{ totalUserCount }}</span>
          <span class="stat-label">{{ t('systemUser.role.totalUsers') }}</span>
        </div>
      </div>
    </div>

    <!-- Two Column Layout -->
    <div class="layout-grid">
      <!-- Role List Panel -->
      <div class="role-panel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><List /></el-icon>
            <span>{{ t('systemUser.role.roleList') }}</span>
          </div>
          <el-button type="primary" size="small" :icon="Plus" @click="handleAddRole" class="btn-add-sm">
            {{ t('systemUser.role.add') }}
          </el-button>
        </div>
        <div class="panel-body">
          <el-table
            :data="roleList"
            v-loading="rolesLoading"
            highlight-current-row
            @current-change="handleRoleSelect"
            size="small"
            :row-class-name="roleRowClassName"
            :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: '600', fontSize: '12px', padding: '8px 6px' }"
          >
            <el-table-column prop="name" :label="t('systemUser.role.roleName')" min-width="90">
              <template #default="{ row }">
                <div class="role-name-cell">
                  <div class="role-avatar" :style="{ background: getRoleColor(row.name) }">
                    {{ row.name.charAt(0) }}
                  </div>
                  <div class="role-info">
                    <span class="role-name">{{ row.name }}</span>
                    <span class="role-badge" v-if="row.is_system">{{ t('systemUser.role.systemRole') }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="user_count" :label="t('systemUser.role.users')" width="80" align="center">
              <template #default="{ row }">
                <span class="user-count-badge">{{ row.user_count }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="t('systemUser.role.actions')" width="85" align="center">
              <template #default="{ row }">
                <div class="action-cell">
                  <el-tooltip :content="t('systemUser.role.edit')" placement="top">
                    <el-button size="small" type="primary" circle :icon="Edit" @click.stop="handleEditRole(row)" />
                  </el-tooltip>
                  <el-tooltip :content="row.is_system ? t('systemUser.role.systemRoleNoDelete') : t('systemUser.role.delete')" placement="top">
                    <el-button 
                      size="small" 
                      type="danger" 
                      circle 
                      :icon="Delete" 
                      @click.stop="handleDeleteRole(row)" 
                      :disabled="row.is_system"
                      :class="{ 'btn-disabled': row.is_system }"
                    />
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- Permission Panel -->
      <div class="permission-panel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><Setting /></el-icon>
            <span v-if="selectedRole">{{ selectedRole.name }}</span>
            <span v-else class="text-muted">{{ t('systemUser.role.selectRole') }}</span>
            <span class="panel-subtitle" v-if="selectedRole">{{ t('systemUser.role.permissionSettings') }}</span>
          </div>
          <el-button 
            v-if="selectedRole" 
            type="primary" 
            @click="handleSavePermission" 
            :loading="saveLoading"
            :icon="Check"
          >
            {{ t('systemUser.role.save') }}
          </el-button>
        </div>

        <div class="panel-body" v-if="selectedRole">
          <el-tabs v-model="activeTab" class="modern-tabs">
            <!-- Menu Permissions Tab -->
            <el-tab-pane name="menu">
              <template #label>
                <div class="tab-label">
                  <el-icon><Menu /></el-icon>
                  <span>{{ t('systemUser.role.menuPermission') }}</span>
                </div>
              </template>
              <div class="tab-content">
                <el-tree
                  :key="selectedRole.id"
                  v-loading="menuTreeLoading"
                  :data="menuTree"
                  show-checkbox
                  node-key="id"
                  :default-checked-keys="selectedRole.menu_permissions"
                  :props="{ children: 'children', label: 'label' }"
                  ref="menuTreeRef"
                  class="permission-tree"
                />
              </div>
            </el-tab-pane>

            <!-- Operation Permissions Tab -->
            <el-tab-pane name="operation">
              <template #label>
                <div class="tab-label">
                  <el-icon><Operation /></el-icon>
                  <span>{{ t('systemUser.role.operationPermission') }}</span>
                </div>
              </template>
              <div class="tab-content">
                <div class="operation-hint">
                  <el-icon><InfoFilled /></el-icon>
                  {{ t('systemUser.role.operationHint') }}
                </div>
                <el-table 
                  :data="operationPermissions" 
                  size="small" 
                  border
                  :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: '600', fontSize: '12px', padding: '8px' }"
                >
                  <el-table-column prop="module" :label="t('systemUser.role.module')" width="130">
                    <template #default="{ row }">
                      <span class="module-name">{{ row.module }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="t('systemUser.role.create')" width="65" align="center">
                    <template #default="{ row }">
                      <el-checkbox v-model="row.can_create" class="check-primary" />
                    </template>
                  </el-table-column>
                  <el-table-column :label="t('systemUser.role.edit')" width="65" align="center">
                    <template #default="{ row }">
                      <el-checkbox v-model="row.can_edit" class="check-info" />
                    </template>
                  </el-table-column>
                  <el-table-column :label="t('systemUser.role.delete')" width="65" align="center">
                    <template #default="{ row }">
                      <el-checkbox v-model="row.can_delete" class="check-danger" />
                    </template>
                  </el-table-column>
                  <el-table-column :label="t('systemUser.role.export')" width="65" align="center">
                    <template #default="{ row }">
                      <el-checkbox v-model="row.can_export" class="check-success" />
                    </template>
                  </el-table-column>
                  <el-table-column :label="t('systemUser.role.approve')" width="65" align="center">
                    <template #default="{ row }">
                      <el-checkbox v-model="row.can_approve" class="check-warning" />
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>

            <!-- Data Scope Tab -->
            <el-tab-pane name="data">
              <template #label>
                <div class="tab-label">
                  <el-icon><DataAnalysis /></el-icon>
                  <span>{{ t('systemUser.role.dataScope') }}</span>
                </div>
              </template>
              <div class="tab-content">
                <div class="data-scope-section">
                  <label class="section-label">{{ t('systemUser.role.dataScopeLabel') }}</label>
                  <div class="scope-options">
                    <div 
                      v-for="option in scopeOptions" 
                      :key="option.value"
                      class="scope-option"
                      :class="{ active: dataScope === option.value }"
                      @click="dataScope = option.value"
                    >
                      <el-icon :size="20">
                        <component :is="option.icon" />
                      </el-icon>
                      <span class="scope-label">{{ option.label }}</span>
                      <span class="scope-desc">{{ option.desc }}</span>
                    </div>
                  </div>
                </div>
                
                <transition name="fade">
                  <div class="custom-dept-section" v-if="dataScope === 'custom'">
                    <label class="section-label">{{ t('systemUser.role.customDept') }}</label>
                    <el-select 
                      v-model="customDepartments" 
                      multiple 
                      :placeholder="t('systemUser.role.selectDept')" 
                      style="width: 100%"
                      filterable
                    >
                      <el-option 
                        v-for="org in departmentOptions" 
                        :key="org.id" 
                        :label="org.name" 
                        :value="org.name" 
                      />
                    </el-select>
                  </div>
                </transition>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- Empty State -->
        <div class="empty-state" v-else>
          <div class="empty-icon">
            <el-icon :size="48"><Select /></el-icon>
          </div>
          <p class="empty-title">{{ t('systemUser.role.emptyTitle') }}</p>
          <p class="empty-desc">{{ t('systemUser.role.emptyDesc') }}</p>
        </div>
      </div>
    </div>

    <!-- Modern Dialog -->
    <el-dialog 
      v-model="roleDialogVisible" 
      :title="roleDialogTitle" 
      width="420px" 
      destroy-on-close
      class="modern-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="roleForm" :rules="roleFormRules" ref="roleFormRef" label-width="90px" label-position="left">
        <el-form-item :label="t('systemUser.role.formRoleName')" prop="name">
          <el-input v-model="roleForm.name" :placeholder="t('systemUser.role.formRoleNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.role.formDesc')">
          <el-input v-model="roleForm.description" type="textarea" :rows="2" :placeholder="t('systemUser.role.formDescPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="roleDialogVisible = false">{{ t('systemUser.role.cancel') }}</el-button>
          <el-button type="primary" @click="handleRoleSubmit" :loading="roleSubmitting">
            <el-icon v-if="!roleSubmitting"><Check /></el-icon>
            {{ t('systemUser.role.save') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Key, List, Edit, Delete, Setting, Check, Menu, Operation, DataAnalysis, InfoFilled, Select, User, OfficeBuilding, HomeFilled, Grid } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import * as systemApi from '@/api/system'
import type { Role, RoleListItem, MenuTreeNode, OperationPermission } from '@/api/system'

const { t } = useI18n()

/** 操作権限で設定可能なモジュール一覧（API 互換のためキーは固定） */
const OPERATION_MODULES = [
  '販売管理',
  '購買管理',
  '在庫管理',
  '原価・会計',
  '生産計画',
  '製造実行',
  '品質管理',
  'システム管理',
] as const

/** データ範囲オプション（ラベルは i18n） */
const scopeOptions = computed(() => [
  { value: 'self' as const, label: t('systemUser.role.scopeSelf'), desc: t('systemUser.role.scopeSelfDesc'), icon: User },
  { value: 'department' as const, label: t('systemUser.role.scopeDept'), desc: t('systemUser.role.scopeDeptDesc'), icon: OfficeBuilding },
  { value: 'department_below' as const, label: t('systemUser.role.scopeDeptBelow'), desc: t('systemUser.role.scopeDeptBelowDesc'), icon: HomeFilled },
  { value: 'all' as const, label: t('systemUser.role.scopeAll'), desc: t('systemUser.role.scopeAllDesc'), icon: Grid },
  { value: 'custom' as const, label: t('systemUser.role.scopeCustom'), desc: t('systemUser.role.scopeCustomDesc'), icon: Setting },
])

// Computed
const totalUserCount = computed(() => roleList.value.reduce((sum, r) => sum + (r.user_count || 0), 0))

// Role colors
const roleColors = ['#667eea', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']
const getRoleColor = (name: string) => {
  const idx = name.charCodeAt(0) % roleColors.length
  return roleColors[idx]
}

// Row class for selected role
const roleRowClassName = ({ row }: { row: RoleListItem }) => {
  return selectedRole.value?.id === row.id ? 'row-selected' : ''
}

const activeTab = ref('menu')
const dataScope = ref<'self' | 'department' | 'department_below' | 'all' | 'custom'>('department')
const customDepartments = ref<string[]>([])
const menuTreeRef = ref<{ getCheckedKeys: () => number[]; getHalfCheckedKeys: () => number[] } | null>(null)

const rolesLoading = ref(false)
const menuTreeLoading = ref(false)
const saveLoading = ref(false)
const roleDialogVisible = ref(false)
const roleDialogTitle = ref('')
const roleSubmitting = ref(false)
const roleFormRef = ref<FormInstance>()

const roleList = ref<RoleListItem[]>([])
const selectedRole = ref<Role | null>(null)
const menuTree = ref<MenuTreeNode[]>([])
const departmentOptions = ref<{ id: number; name: string }[]>([])
const operationPermissions = ref<OperationPermission[]>([])

const roleForm = ref({ id: 0, name: '', description: '' })
const roleFormRules = computed<FormRules>(() => ({
  name: [{ required: true, message: t('systemUser.role.validationRoleName'), trigger: 'blur' }],
}))

async function fetchRoles() {
  rolesLoading.value = true
  try {
    const res = (await systemApi.getRoles()) as unknown as RoleListItem[]
    roleList.value = Array.isArray(res) ? res : []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.role.msgRolesError'))
  } finally {
    rolesLoading.value = false
  }
}

async function fetchMenuTree() {
  menuTreeLoading.value = true
  try {
    const res = (await systemApi.getMenuTree()) as unknown as MenuTreeNode[]
    menuTree.value = Array.isArray(res) ? res : []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.role.msgMenuError'))
  } finally {
    menuTreeLoading.value = false
  }
}

async function fetchDepartments() {
  try {
    const res = (await systemApi.getOrganizations()) as unknown as { id: number; name: string; type: string }[]
    const list = Array.isArray(res) ? res : []
    departmentOptions.value = list
      .filter((o) => o.type === 'department' || o.type === 'site')
      .map((o) => ({ id: o.id, name: o.name }))
  } catch (_) {
    departmentOptions.value = []
  }
}

function buildOperationPermissionsFromRole(role: Role | null): OperationPermission[] {
  const list = role?.operation_permissions ?? []
  const byModule = new Map(list.map((op) => [op.module, { ...op }]))
  return OPERATION_MODULES.map((module) => {
    const existing = byModule.get(module)
    return existing ?? { module, can_create: false, can_edit: false, can_delete: false, can_export: false, can_approve: false }
  })
}

async function handleRoleSelect(row: RoleListItem | null) {
  if (!row) {
    selectedRole.value = null
    operationPermissions.value = []
    return
  }
  try {
    const role = (await systemApi.getRole(row.id)) as unknown as Role
    selectedRole.value = role
    dataScope.value = role.data_scope
    customDepartments.value = role.custom_departments || []
    operationPermissions.value = buildOperationPermissionsFromRole(role)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.role.msgRoleDetailError'))
    selectedRole.value = null
    operationPermissions.value = []
  }
}

const handleAddRole = () => {
  roleDialogTitle.value = t('systemUser.role.formAddTitle')
  roleForm.value = { id: 0, name: '', description: '' }
  roleDialogVisible.value = true
}

const handleEditRole = (row: RoleListItem) => {
  roleDialogTitle.value = t('systemUser.role.formEditTitle')
  roleForm.value = { id: row.id, name: row.name, description: '' }
  roleDialogVisible.value = true
}

const handleRoleSubmit = async () => {
  if (!roleFormRef.value) return
  await roleFormRef.value.validate()
  roleSubmitting.value = true
  try {
    if (roleForm.value.id) {
      await systemApi.updateRole(roleForm.value.id, {
        name: roleForm.value.name,
        description: roleForm.value.description || undefined,
      })
      ElMessage.success(t('systemUser.role.msgSaveSuccess'))
    } else {
      await systemApi.createRole({
        name: roleForm.value.name,
        description: roleForm.value.description || undefined,
      })
      ElMessage.success(t('systemUser.role.msgCreateSuccess'))
    }
    roleDialogVisible.value = false
    fetchRoles()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.role.msgSaveFailed'))
  } finally {
    roleSubmitting.value = false
  }
}

const handleDeleteRole = async (row: RoleListItem) => {
  try {
    await ElMessageBox.confirm(t('systemUser.role.msgDeleteConfirm', { name: row.name }), t('common.confirm'), { type: 'warning' })
    await systemApi.deleteRole(row.id)
    ElMessage.success(t('systemUser.role.msgDeleteSuccess'))
    if (selectedRole.value?.id === row.id) selectedRole.value = null
    await fetchRoles()
  } catch (e: unknown) {
    if (e !== 'cancel') ElMessage.error((e as any)?.response?.data?.detail || t('systemUser.role.msgDeleteError'))
  }
}

const handleSavePermission = async () => {
  if (!selectedRole.value) return
  const checkedKeys = menuTreeRef.value?.getCheckedKeys() ?? []
  const halfCheckedKeys = menuTreeRef.value?.getHalfCheckedKeys() ?? []
  const menu_permissions = [...checkedKeys, ...halfCheckedKeys]
  saveLoading.value = true
  try {
    await systemApi.updateRole(selectedRole.value.id, {
      menu_permissions,
      operation_permissions: operationPermissions.value,
      data_scope: dataScope.value,
      custom_departments: dataScope.value === 'custom' ? customDepartments.value : undefined,
    })
    ElMessage.success(t('systemUser.role.msgPermSaveSuccess'))
    const role = (await systemApi.getRole(selectedRole.value.id)) as unknown as Role
    selectedRole.value = role
    operationPermissions.value = buildOperationPermissionsFromRole(role)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.role.msgSaveFailed'))
  } finally {
    saveLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchRoles(), fetchMenuTree(), fetchDepartments()])
})
</script>

<style scoped>
/* Base Layout */
.role-permission {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

/* Modern Gradient Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  backdrop-filter: blur(10px);
}

.header-text h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.5px;
}

.header-text .subtitle {
  margin: 2px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  padding: 10px 20px;
  border-radius: 10px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: white;
}

.stat-value.highlight { color: #a5f3fc; }

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 2px;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
}

/* Two Column Grid Layout */
.layout-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 12px;
  height: calc(100vh - 140px);
}

/* Panel Styles */
.role-panel,
.permission-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
}

.panel-title .el-icon {
  color: #667eea;
}

.panel-subtitle {
  font-size: 12px;
  color: #64748b;
  font-weight: 400;
  margin-left: 4px;
}

.panel-subtitle::before {
  content: '—';
  margin-right: 6px;
}

.text-muted {
  color: #94a3b8;
  font-weight: 400;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

/* Role List Styles */
.role-panel .panel-body :deep(.el-table) {
  --el-table-border-color: transparent;
}

.role-panel .panel-body :deep(.el-table td.el-table__cell) {
  padding: 8px 6px;
  border-bottom: 1px solid #f1f5f9;
}

.role-panel .panel-body :deep(.el-table__row:hover > td) {
  background-color: #f1f5f9 !important;
}

.role-panel .panel-body :deep(.row-selected > td) {
  background-color: #ede9fe !important;
}

.role-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.role-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.role-name {
  font-weight: 500;
  color: #1e293b;
  font-size: 13px;
}

.role-badge {
  font-size: 10px;
  padding: 1px 6px;
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 4px;
  width: fit-content;
}

.user-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  padding: 2px 6px;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.btn-add-sm {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-size: 12px;
  padding: 6px 12px;
}

/* Action Buttons */
.action-cell {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.action-cell :deep(.el-button.is-circle) {
  width: 26px;
  height: 26px;
  transition: all 0.2s;
}

.action-cell :deep(.el-button.is-circle:hover) {
  transform: translateY(-1px);
}

.btn-disabled {
  opacity: 0.4;
  cursor: not-allowed !important;
}

/* Modern Tabs */
.modern-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.modern-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.modern-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.modern-tabs :deep(.el-tabs__item) {
  height: 44px;
  padding: 0 16px;
}

.modern-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.modern-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-content {
  padding: 16px;
}

/* Permission Tree */
.permission-tree {
  --el-tree-node-hover-bg-color: #f1f5f9;
}

.permission-tree :deep(.el-tree-node__content) {
  height: 32px;
  border-radius: 6px;
  margin: 2px 0;
}

/* Operation Permissions */
.operation-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 8px;
  font-size: 12px;
  color: #0369a1;
  margin-bottom: 12px;
}

.module-name {
  font-weight: 500;
  color: #334155;
}

/* Data Scope Section */
.data-scope-section {
  margin-bottom: 20px;
}

.section-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 12px;
}

.scope-options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}

.scope-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 10px;
  background: #f8fafc;
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.scope-option:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.scope-option.active {
  background: #ede9fe;
  border-color: #8b5cf6;
}

.scope-option .el-icon {
  color: #64748b;
}

.scope-option.active .el-icon {
  color: #7c3aed;
}

.scope-label {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
}

.scope-desc {
  font-size: 11px;
  color: #64748b;
}

.custom-dept-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-icon .el-icon {
  color: #94a3b8;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 8px;
}

.empty-desc {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

/* Dialog Styles */
.modern-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

.modern-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  margin: 0;
}

.modern-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

.modern-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

.modern-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.dialog-footer :deep(.el-button) {
  border-radius: 8px;
  padding: 10px 20px;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .layout-grid {
    grid-template-columns: 280px 1fr;
  }
  
  .header-stats {
    display: none;
  }
}

@media (max-width: 768px) {
  .role-permission {
    padding: 12px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .header-content {
    flex-direction: column;
  }
  
  .layout-grid {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .role-panel {
    max-height: 300px;
  }
  
  .permission-panel {
    min-height: 400px;
  }
  
  .scope-options {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
