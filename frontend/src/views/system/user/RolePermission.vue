<template>
  <div class="role-permission">
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon-sm">
          <el-icon :size="18"><Key /></el-icon>
        </div>
        <div class="header-text">
          <h1>{{ t('systemUser.role.title') }}</h1>
          <p class="subtitle">{{ t('systemUser.role.subtitle') }}</p>
        </div>
      </div>
      <div class="header-chips">
        <span class="h-chip">
          <strong>{{ roleList.length }}</strong>
          <em>{{ t('systemUser.role.roleCount') }}</em>
        </span>
        <span class="h-chip accent">
          <strong>{{ totalUserCount }}</strong>
          <em>{{ t('systemUser.role.totalUsers') }}</em>
        </span>
      </div>
    </div>

    <div class="layout-grid">
      <aside class="role-panel">
        <div class="panel-header">
          <span class="panel-title">
            <el-icon><List /></el-icon>
            {{ t('systemUser.role.roleList') }}
          </span>
          <el-button type="primary" size="small" :icon="Plus" class="btn-add-sm" @click="handleAddRole">
            {{ t('systemUser.role.add') }}
          </el-button>
        </div>
        <div class="panel-body role-list-wrap" v-loading="rolesLoading">
          <div
            v-for="row in roleList"
            :key="row.id"
            class="role-card"
            :class="{ active: selectedRole?.id === row.id }"
            @click="handleRoleSelect(row)"
          >
            <div class="role-card-main">
              <div class="role-avatar" :style="{ background: getRoleColor(row.name) }">
                {{ row.name.charAt(0) }}
              </div>
              <div class="role-info">
                <div class="role-name-row">
                  <span class="role-name">{{ row.name }}</span>
                  <span class="user-count-badge">{{ row.user_count }}</span>
                </div>
                <div class="role-meta">
                  <span v-if="row.code" class="role-code">{{ row.code }}</span>
                  <span v-if="row.is_super_admin" class="role-badge admin">{{ t('systemUser.role.superAdminBadge') }}</span>
                  <span v-else-if="row.is_system" class="role-badge">{{ t('systemUser.role.systemRole') }}</span>
                </div>
              </div>
            </div>
            <div class="role-card-actions" @click.stop>
              <el-button size="small" text type="primary" :icon="Edit" @click="handleEditRole(row)" />
              <el-button
                size="small"
                text
                type="danger"
                :icon="Delete"
                :disabled="row.is_system"
                @click="handleDeleteRole(row)"
              />
            </div>
          </div>
          <div v-if="!rolesLoading && roleList.length === 0" class="role-list-empty">
            {{ t('systemUser.role.emptyTitle') }}
          </div>
        </div>
      </aside>

      <section class="permission-panel">
        <div class="panel-header" :class="{ 'has-role': selectedRole }">
          <div class="panel-title-group" v-if="selectedRole">
            <div class="selected-role-avatar" :style="{ background: getRoleColor(selectedRole.name) }">
              {{ selectedRole.name.charAt(0) }}
            </div>
            <div class="selected-role-text">
              <span class="selected-role-name">{{ selectedRole.name }}</span>
              <span class="selected-role-sub">{{ t('systemUser.role.permissionSettings') }}</span>
            </div>
          </div>
          <span v-else class="panel-title muted">
            <el-icon><Setting /></el-icon>
            {{ t('systemUser.role.selectRole') }}
          </span>
          <el-button
            v-if="selectedRole"
            type="primary"
            size="small"
            :loading="saveLoading"
            :icon="Check"
            class="btn-save"
            @click="handleSavePermission"
          >
            {{ t('systemUser.role.save') }}
          </el-button>
        </div>

        <div class="panel-body perm-body" v-if="selectedRole">
          <el-tabs v-model="activeTab" class="compact-tabs">
            <!-- Menu Permissions Tab -->
            <el-tab-pane name="menu">
              <template #label>
                <div class="tab-label">
                  <el-icon><Menu /></el-icon>
                  <span>{{ t('systemUser.role.menuPermission') }}</span>
                </div>
              </template>
              <div class="tab-content menu-permission-content">
                <div class="menu-toolbar">
                  <span class="menu-hint">
                    <el-icon><InfoFilled /></el-icon>
                    {{ t('systemUser.role.menuPermissionHint') }}
                  </span>
                  <div class="menu-toolbar-btns">
                    <el-button size="small" link type="primary" @click="expandAllMenuNodes">
                      {{ t('systemUser.role.menuExpandAll') }}
                    </el-button>
                    <el-button size="small" link type="primary" @click="collapseAllMenuNodes">
                      {{ t('systemUser.role.menuCollapseAll') }}
                    </el-button>
                  </div>
                </div>
                <div class="menu-tree-wrap" v-loading="menuTreeLoading">
                  <el-tree
                    :key="`menu-tree-${selectedRole.id}-${menuTreeRenderKey}`"
                    :data="menuTree"
                    show-checkbox
                    node-key="code"
                    :default-checked-keys="menuTreeCheckedKeys"
                    :default-expanded-keys="menuTreeExpandedKeys"
                    :props="{ children: 'children', label: 'label', disabled: 'disabled' }"
                    ref="menuTreeRef"
                    class="permission-tree"
                  >
                    <template #default="{ node, data }">
                      <div
                        class="permission-tree-node"
                        :class="{
                          'is-root': node.level === 1,
                          'is-missing': data.syncMissing,
                        }"
                      >
                        <el-icon class="node-icon">
                          <component :is="data.icon || 'Menu'" />
                        </el-icon>
                        <span class="node-label" :title="resolveMenuNodeLabel(data)">
                          {{ resolveMenuNodeLabel(data) }}
                        </span>
                        <el-tag
                          v-if="data.syncMissing"
                          size="small"
                          type="warning"
                          effect="plain"
                          class="sync-tag"
                        >
                          {{ t('systemUser.role.menuSyncMissing') }}
                        </el-tag>
                      </div>
                    </template>
                  </el-tree>
                </div>
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
                <p class="inline-hint">
                  <el-icon><InfoFilled /></el-icon>
                  {{ t('systemUser.role.operationHint') }}
                </p>
                <div class="op-matrix">
                  <div class="op-row op-head">
                    <span class="op-module">{{ t('systemUser.role.module') }}</span>
                    <span>{{ t('systemUser.role.create') }}</span>
                    <span>{{ t('systemUser.role.edit') }}</span>
                    <span>{{ t('systemUser.role.delete') }}</span>
                    <span>{{ t('systemUser.role.export') }}</span>
                    <span>{{ t('systemUser.role.approve') }}</span>
                  </div>
                  <div v-for="row in operationPermissions" :key="row.module" class="op-row">
                    <span class="op-module">{{ row.module }}</span>
                    <span><el-checkbox v-model="row.can_create" /></span>
                    <span><el-checkbox v-model="row.can_edit" /></span>
                    <span><el-checkbox v-model="row.can_delete" /></span>
                    <span><el-checkbox v-model="row.can_export" /></span>
                    <span><el-checkbox v-model="row.can_approve" /></span>
                  </div>
                </div>
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
              <div class="tab-content data-tab">
                <p class="section-label">{{ t('systemUser.role.dataScopeLabel') }}</p>
                <div class="scope-chips">
                  <button
                    v-for="option in scopeOptions"
                    :key="option.value"
                    type="button"
                    class="scope-chip"
                    :class="{ active: dataScope === option.value }"
                    @click="dataScope = option.value"
                  >
                    <el-icon><component :is="option.icon" /></el-icon>
                    <span class="scope-chip-label">{{ option.label }}</span>
                    <span class="scope-chip-desc">{{ option.desc }}</span>
                  </button>
                </div>
                <transition name="fade">
                  <div class="custom-dept-section" v-if="dataScope === 'custom'">
                    <label class="section-label">{{ t('systemUser.role.customDept') }}</label>
                    <el-select
                      v-model="customDepartments"
                      multiple
                      collapse-tags
                      collapse-tags-tooltip
                      :placeholder="t('systemUser.role.selectDept')"
                      class="custom-dept-select"
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

        <div class="empty-state" v-else>
          <el-icon :size="32" class="empty-icon"><Select /></el-icon>
          <p class="empty-title">{{ t('systemUser.role.emptyTitle') }}</p>
          <p class="empty-desc">{{ t('systemUser.role.emptyDesc') }}</p>
        </div>
      </section>
    </div>

    <!-- Role Edit Dialog -->
    <el-dialog
      v-model="roleDialogVisible"
      width="460px"
      destroy-on-close
      align-center
      class="role-edit-dialog"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <template #header>
        <div class="role-dialog-hero">
          <button type="button" class="role-dialog-close" :aria-label="t('systemUser.role.cancel')" @click="roleDialogVisible = false">
            <el-icon><Close /></el-icon>
          </button>
          <div class="role-dialog-hero-row">
            <div class="role-dialog-avatar" :style="{ background: roleDialogAvatarColor }">
              {{ roleDialogInitial }}
            </div>
            <div class="role-dialog-titles">
              <h3 class="role-dialog-title">{{ roleDialogTitle }}</h3>
              <p class="role-dialog-subtitle">{{ roleDialogSubtitle }}</p>
            </div>
            <div class="role-dialog-badges">
              <span v-if="roleForm.is_system" class="dlg-badge system">{{ t('systemUser.role.systemRole') }}</span>
              <span v-if="roleForm.is_super_admin" class="dlg-badge admin">{{ t('systemUser.role.superAdminBadge') }}</span>
            </div>
          </div>
        </div>
      </template>

      <div class="role-dialog-body">
        <el-form
          :model="roleForm"
          :rules="roleFormRules"
          ref="roleFormRef"
          label-position="top"
          class="role-dialog-form"
          @submit.prevent="handleRoleSubmit"
        >
          <el-form-item :label="t('systemUser.role.formRoleName')" prop="name">
            <el-input
              v-model="roleForm.name"
              :placeholder="t('systemUser.role.formRoleNamePlaceholder')"
              clearable
              class="field-input"
            />
          </el-form-item>
          <el-form-item :label="t('systemUser.role.formRoleCode')" prop="code">
            <el-input
              v-model="roleForm.code"
              :placeholder="t('systemUser.role.formRoleCodePlaceholder')"
              clearable
              class="field-input code-input"
            />
            <p class="field-hint">{{ t('systemUser.role.formRoleCodeHint') }}</p>
          </el-form-item>
          <el-form-item :label="t('systemUser.role.formDesc')">
            <el-input
              v-model="roleForm.description"
              type="textarea"
              :rows="2"
              :placeholder="t('systemUser.role.formDescPlaceholder')"
              resize="none"
              class="field-textarea"
            />
          </el-form-item>

          <div class="privilege-row" :class="{ 'is-active': roleForm.is_super_admin }">
            <div class="privilege-row-main">
              <el-icon class="privilege-icon"><StarFilled /></el-icon>
              <div class="privilege-row-text">
                <span class="privilege-label">{{ t('systemUser.role.formSuperAdmin') }}</span>
                <span class="privilege-hint">{{ t('systemUser.role.formSuperAdminHint') }}</span>
              </div>
              <el-switch v-model="roleForm.is_super_admin" class="privilege-switch" />
            </div>
            <div v-if="roleForm.is_super_admin" class="privilege-alert">
              <el-icon><WarningFilled /></el-icon>
              <span>{{ t('systemUser.role.formSuperAdminWarn') }}</span>
            </div>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="role-dialog-footer">
          <el-button class="btn-cancel" @click="roleDialogVisible = false">
            {{ t('systemUser.role.cancel') }}
          </el-button>
          <el-button type="primary" class="btn-submit" :loading="roleSubmitting" @click="handleRoleSubmit">
            <el-icon v-if="!roleSubmitting"><Check /></el-icon>
            {{ roleForm.id ? t('systemUser.role.save') : t('systemUser.role.formCreateBtn') }}
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
import { Plus, Key, List, Edit, Delete, Setting, Check, Menu, Operation, DataAnalysis, InfoFilled, Select, User, OfficeBuilding, HomeFilled, Grid, Close, StarFilled, WarningFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import * as systemApi from '@/api/system'
import type { Role, RoleListItem, OperationPermission } from '@/api/system'
import {
  buildPermissionMenuTree,
  collectPermissionTreeCodeToId,
  expandCheckedCodesWithDescendants,
  menuIdsToTreeCheckedKeys,
  type PermissionMenuTreeNode,
} from '@/composables/usePermissionMenuTree'
import { resolveMenuLabel } from '@/utils/menuLabel'
import type ElTree from 'element-plus/es/components/tree/src/tree.vue'

const { t } = useI18n()

import { OPERATION_MODULES } from '@/constants/operationModules'

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

const activeTab = ref('menu')
const dataScope = ref<'self' | 'department' | 'department_below' | 'all' | 'custom'>('department')
const customDepartments = ref<string[]>([])
const menuTreeRef = ref<InstanceType<typeof ElTree> | null>(null)

const rolesLoading = ref(false)
const menuTreeLoading = ref(false)
const saveLoading = ref(false)
const roleDialogVisible = ref(false)
const roleSubmitting = ref(false)
const roleFormRef = ref<FormInstance>()

const roleDialogTitle = computed(() =>
  roleForm.value.id ? t('systemUser.role.formEditTitle') : t('systemUser.role.formAddTitle'),
)
const roleDialogSubtitle = computed(() =>
  roleForm.value.id ? t('systemUser.role.formDialogEditDesc') : t('systemUser.role.formDialogAddDesc'),
)
const roleDialogInitial = computed(() => {
  const n = roleForm.value.name.trim()
  return n ? n.charAt(0).toUpperCase() : '?'
})
const roleDialogAvatarColor = computed(() => getRoleColor(roleForm.value.name || '?'))

const roleList = ref<RoleListItem[]>([])
const selectedRole = ref<Role | null>(null)
const menuTree = ref<PermissionMenuTreeNode[]>([])
const menuTreeRenderKey = ref(0)

const menuTreeCheckedKeys = computed(() => {
  if (!selectedRole.value || menuTree.value.length === 0) return []
  return menuIdsToTreeCheckedKeys(selectedRole.value.menu_permissions, menuTree.value)
})

const menuTreeExpandedKeys = computed(() => menuTree.value.map((node) => node.code))

function resolveMenuNodeLabel(data: PermissionMenuTreeNode) {
  return resolveMenuLabel(data.code, data.label, t)
}

function expandAllMenuNodes() {
  const store = menuTreeRef.value?.store
  if (!store) return
  Object.values(store.nodesMap).forEach((node) => node.expand())
}

function collapseAllMenuNodes() {
  const store = menuTreeRef.value?.store
  if (!store) return
  Object.values(store.nodesMap).forEach((node) => node.collapse())
}
const departmentOptions = ref<{ id: number; name: string }[]>([])
const operationPermissions = ref<OperationPermission[]>([])

const roleForm = ref({ id: 0, name: '', code: '', description: '', is_super_admin: false, is_system: false })
const roleFormRules = computed<FormRules>(() => ({
  name: [{ required: true, message: t('systemUser.role.validationRoleName'), trigger: 'blur' }],
  code: [
    {
      validator: (_rule, value, callback) => {
        const v = (value ?? '').trim()
        if (!v) {
          callback()
          return
        }
        if (!/^[a-z][a-z0-9_]{0,49}$/.test(v)) {
          callback(new Error(t('systemUser.role.validationRoleCode')))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
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
    const res = (await systemApi.getMenus()) as unknown as { id: number; code: string }[]
    const list = Array.isArray(res) ? res : []
    const codeToId = new Map(list.map((m) => [m.code, m.id]))
    menuTree.value = buildPermissionMenuTree(codeToId)
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
    menuTreeRenderKey.value += 1
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.role.msgRoleDetailError'))
    selectedRole.value = null
    operationPermissions.value = []
  }
}

const handleAddRole = () => {
  roleForm.value = { id: 0, name: '', code: '', description: '', is_super_admin: false, is_system: false }
  roleDialogVisible.value = true
}

const handleEditRole = async (row: RoleListItem) => {
  try {
    const role = (await systemApi.getRole(row.id)) as unknown as Role
    roleForm.value = {
      id: role.id,
      name: role.name,
      code: role.code ?? '',
      description: role.description ?? '',
      is_super_admin: Boolean(role.is_super_admin),
      is_system: role.is_system,
    }
    roleDialogVisible.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.role.msgRoleDetailError'))
  }
}

const handleRoleSubmit = async () => {
  if (!roleFormRef.value) return
  await roleFormRef.value.validate()
  roleSubmitting.value = true
  try {
    if (roleForm.value.id) {
      await systemApi.updateRole(roleForm.value.id, {
        name: roleForm.value.name,
        code: roleForm.value.code.trim() || undefined,
        description: roleForm.value.description || undefined,
        is_super_admin: roleForm.value.is_super_admin,
      })
      ElMessage.success(t('systemUser.role.msgSaveSuccess'))
    } else {
      await systemApi.createRole({
        name: roleForm.value.name,
        code: roleForm.value.code.trim() || undefined,
        description: roleForm.value.description || undefined,
        is_super_admin: roleForm.value.is_super_admin,
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
  const checkedCodes = expandCheckedCodesWithDescendants(
    menuTree.value,
    (menuTreeRef.value?.getCheckedKeys(false) ?? []) as string[],
  )
  const codeToId = collectPermissionTreeCodeToId(menuTree.value)
  const menu_permissions = checkedCodes
    .map((code) => codeToId.get(code))
    .filter((id): id is number => id != null && id > 0)
  if (checkedCodes.length > 0 && menu_permissions.length === 0) {
    ElMessage.warning(t('systemUser.role.msgMenuPermEmptyWarn'))
    return
  }
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
    menuTreeRenderKey.value += 1
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
.role-permission {
  padding: 10px 12px;
  background: #eef2f7;
  min-height: calc(100vh - 48px);
  box-sizing: border-box;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  margin-bottom: 8px;
  border-radius: 10px;
  background: linear-gradient(120deg, #5b6fd6 0%, #7c3aed 100%);
  box-shadow: 0 4px 14px rgba(91, 111, 214, 0.28);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.header-icon-sm {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-text h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  line-height: 1.25;
}

.header-text .subtitle {
  margin: 1px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.3;
}

.header-chips {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.h-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 11px;
}

.h-chip strong {
  font-size: 14px;
  font-weight: 800;
}

.h-chip em {
  font-style: normal;
  opacity: 0.85;
}

.h-chip.accent {
  background: rgba(255, 255, 255, 0.24);
}

.layout-grid {
  display: grid;
  grid-template-columns: 272px minmax(0, 1fr);
  gap: 8px;
  height: calc(100vh - 108px);
  min-height: 420px;
}

.role-panel,
.permission-panel {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
  min-height: 40px;
}

.panel-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.panel-title .el-icon,
.panel-title.muted .el-icon {
  color: #6366f1;
  font-size: 15px;
}

.panel-title.muted {
  color: #64748b;
  font-weight: 500;
}

.panel-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.selected-role-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.selected-role-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.selected-role-name {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-role-sub {
  font-size: 10px;
  color: #64748b;
  line-height: 1.2;
}

.btn-save,
.btn-add-sm {
  border: none;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  font-weight: 600;
}

.panel-body {
  flex: 1;
  overflow: hidden;
}

.role-list-wrap {
  overflow-y: auto;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.role-card {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 6px 6px 8px;
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.role-card:hover {
  background: #f1f5f9;
}

.role-card.active {
  background: linear-gradient(90deg, #eef2ff, #f5f3ff);
  border-color: #c7d2fe;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.12);
}

.role-card-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.role-avatar {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.role-info {
  min-width: 0;
  flex: 1;
}

.role-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.role-name {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  margin-top: 1px;
}

.role-code {
  font-size: 9px;
  color: #64748b;
  font-family: ui-monospace, monospace;
}

.role-badge {
  font-size: 9px;
  padding: 0 5px;
  border-radius: 4px;
  background: #e0f2fe;
  color: #0369a1;
  line-height: 16px;
}

.role-badge.admin {
  background: #fef3c7;
  color: #b45309;
}

.user-count-badge {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  background: #f1f5f9;
  padding: 0 5px;
  border-radius: 4px;
  line-height: 16px;
  flex-shrink: 0;
}

.role-card-actions {
  display: flex;
  flex-shrink: 0;
  opacity: 0.55;
  transition: opacity 0.15s;
}

.role-card:hover .role-card-actions,
.role-card.active .role-card-actions {
  opacity: 1;
}

.role-list-empty {
  padding: 20px 8px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
}

.perm-body {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.compact-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.compact-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 6px 8px 0;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.compact-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.compact-tabs :deep(.el-tabs__item) {
  height: 34px;
  padding: 0 10px;
  font-size: 12px;
}

.compact-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.compact-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tab-content {
  padding: 8px 10px 10px;
}

.menu-permission-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: 100%;
}

.menu-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 8px;
  border-radius: 7px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.menu-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #64748b;
  line-height: 1.3;
  min-width: 0;
}

.menu-hint .el-icon {
  color: #6366f1;
  flex-shrink: 0;
}

.menu-toolbar-btns {
  display: flex;
  flex-shrink: 0;
}

.menu-tree-wrap {
  flex: 1;
  min-height: 200px;
  padding: 6px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: auto;
  background: #fafbfc;
}

.permission-tree {
  --el-tree-node-hover-bg-color: #f1f5f9;
  background: transparent;
}

.permission-tree :deep(.el-tree-node__content) {
  height: 30px;
  border-radius: 6px;
  margin: 1px 0;
}

.permission-tree :deep(.el-tree > .el-tree-node > .el-tree-node__content) {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  font-weight: 600;
  margin-bottom: 4px;
}

.permission-tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.permission-tree-node .node-icon {
  color: #6366f1;
  font-size: 14px;
  flex-shrink: 0;
}

.permission-tree-node .node-label {
  font-size: 12px;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.permission-tree-node.is-root .node-label {
  font-weight: 600;
}

.permission-tree-node.is-missing {
  opacity: 0.7;
}

.permission-tree-node .sync-tag {
  margin-left: auto;
  flex-shrink: 0;
}

.inline-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0 0 6px;
  padding: 5px 8px;
  border-radius: 6px;
  background: #f0f9ff;
  font-size: 11px;
  color: #0369a1;
  line-height: 1.35;
}

.inline-hint .el-icon {
  flex-shrink: 0;
}

.op-matrix {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  font-size: 11px;
}

.op-row {
  display: grid;
  grid-template-columns: minmax(100px, 1.4fr) repeat(5, minmax(44px, 1fr));
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-bottom: 1px solid #f1f5f9;
}

.op-row:last-child {
  border-bottom: none;
}

.op-row.op-head {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 10px;
  padding: 6px 8px;
}

.op-row:not(.op-head):hover {
  background: #fafbfc;
}

.op-module {
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.op-row > span:not(.op-module) {
  text-align: center;
}

.op-row :deep(.el-checkbox) {
  height: auto;
}

.data-tab .section-label {
  margin: 0 0 6px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}

.scope-chips {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
  gap: 6px;
}

.scope-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 8px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.scope-chip:hover {
  border-color: #cbd5e1;
  background: #f1f5f9;
}

.scope-chip.active {
  border-color: #8b5cf6;
  background: #f5f3ff;
  box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.2);
}

.scope-chip .el-icon {
  font-size: 14px;
  color: #64748b;
}

.scope-chip.active .el-icon {
  color: #7c3aed;
}

.scope-chip-label {
  font-size: 11px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.scope-chip-desc {
  font-size: 9px;
  color: #64748b;
  line-height: 1.25;
}

.custom-dept-section {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e2e8f0;
}

.custom-dept-select {
  width: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 24px 16px;
  text-align: center;
}

.empty-icon {
  color: #94a3b8;
  margin-bottom: 8px;
}

.empty-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.empty-desc {
  margin: 0;
  font-size: 11px;
  color: #94a3b8;
  max-width: 280px;
  line-height: 1.45;
}

/* Role Edit Dialog */
.role-edit-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.15);
  padding: 0;
}

.role-edit-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

.role-edit-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.role-edit-dialog :deep(.el-dialog__footer) {
  padding: 10px 16px 14px;
  margin: 0;
  border-top: 1px solid #e2e8f0;
}

.role-dialog-hero {
  position: relative;
  padding: 14px 16px;
  background: linear-gradient(135deg, #5b6fd6 0%, #7c3aed 100%);
  color: #fff;
}

.role-dialog-close {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 2;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.role-dialog-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.role-dialog-hero-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-right: 28px;
}

.role-dialog-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.role-dialog-titles {
  flex: 1;
  min-width: 0;
}

.role-dialog-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
}

.role-dialog-subtitle {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-dialog-badges {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}

.dlg-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
}

.dlg-badge.system {
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.dlg-badge.admin {
  background: #fbbf24;
  color: #78350f;
}

.role-dialog-body {
  padding: 12px 16px 4px;
}

.role-dialog-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.role-dialog-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  padding-bottom: 4px;
  line-height: 1.2;
}

.field-hint {
  margin: 4px 0 0;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.35;
}

.role-dialog-form :deep(.field-input .el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.role-dialog-form :deep(.field-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
}

.role-dialog-form :deep(.code-input .el-input__inner) {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}

.role-dialog-form :deep(.field-textarea .el-textarea__inner) {
  border-radius: 8px;
  padding: 8px 10px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  font-size: 13px;
  line-height: 1.45;
}

.privilege-row {
  margin-top: 2px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  transition: border-color 0.2s, background 0.2s;
}

.privilege-row.is-active {
  background: #fffbeb;
  border-color: #fcd34d;
}

.privilege-row-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.privilege-icon {
  color: #d97706;
  font-size: 18px;
  flex-shrink: 0;
}

.privilege-row-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.privilege-label {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
}

.privilege-hint {
  font-size: 11px;
  color: #64748b;
  line-height: 1.35;
}

.privilege-switch {
  flex-shrink: 0;
}

.privilege-alert {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(245, 158, 11, 0.12);
  font-size: 11px;
  color: #92400e;
  line-height: 1.4;
}

.privilege-alert .el-icon {
  margin-top: 1px;
  flex-shrink: 0;
  color: #d97706;
}

.role-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.role-dialog-footer .btn-cancel {
  border-radius: 8px;
  padding: 8px 16px;
}

.role-dialog-footer .btn-submit {
  border-radius: 8px;
  padding: 8px 18px;
  font-weight: 600;
  border: none;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

@media (max-width: 520px) {
  .role-edit-dialog :deep(.el-dialog) {
    width: calc(100vw - 20px) !important;
  }

  .role-dialog-subtitle {
    white-space: normal;
  }
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

@media (max-width: 1024px) {
  .layout-grid {
    grid-template-columns: 240px minmax(0, 1fr);
  }

  .header-chips {
    display: none;
  }
}

@media (max-width: 768px) {
  .role-permission {
    padding: 8px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .layout-grid {
    grid-template-columns: 1fr;
    height: auto;
  }

  .role-panel {
    max-height: 220px;
  }

  .permission-panel {
    min-height: 360px;
  }

  .scope-chips {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .op-row {
    grid-template-columns: minmax(80px, 1.2fr) repeat(5, minmax(36px, 1fr));
    font-size: 10px;
  }
}
</style>
