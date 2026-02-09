<template>
  <div class="organization-list">
    <!-- Modern Gradient Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon :size="28"><OfficeBuilding /></el-icon>
        </div>
        <div class="header-text">
          <h1>{{ t('systemUser.org.title') }}</h1>
          <p class="subtitle">{{ t('systemUser.org.subtitle') }}</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ orgCount }}</span>
          <span class="stat-label">{{ t('systemUser.org.totalOrgs') }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value highlight">{{ deptCount }}</span>
          <span class="stat-label">{{ t('systemUser.org.depts') }}</span>
        </div>
      </div>
    </div>

    <!-- Two Column Layout -->
    <div class="layout-grid">
      <!-- Organization Tree Panel -->
      <div class="tree-panel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><Share /></el-icon>
            <span>{{ t('systemUser.org.treeTitle') }}</span>
          </div>
          <el-button type="primary" size="small" :icon="Plus" @click="handleAddOrg" class="btn-add-sm">
            {{ t('systemUser.org.add') }}
          </el-button>
        </div>
        <div class="tree-hint">
          <el-icon><InfoFilled /></el-icon>
          {{ t('systemUser.org.treeHint') }}
        </div>
        <div class="panel-body">
          <el-tree
            :key="treeKey"
            v-loading="treeLoading"
            :data="orgTree"
            :props="treeProps"
            node-key="id"
            default-expand-all
            highlight-current
            @node-click="handleNodeClick"
            class="org-tree"
          >
            <template #default="{ data }">
              <div class="tree-node" @dblclick.stop="handleNodeDblclick(data)">
                <div class="node-icon-wrapper" :style="{ background: getNodeBgColor(data.type) }">
                  <el-icon :size="14" color="white">
                    <component :is="getNodeIcon(data.type)" />
                  </el-icon>
                </div>
                <span class="node-label">{{ data.name }}</span>
                <span class="node-type-badge" :class="data.type">{{ typeLabel(data.type) }}</span>
              </div>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- Detail Panel -->
      <div class="detail-panel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><Document /></el-icon>
            <span v-if="selectedOrg">{{ selectedOrg.name }}</span>
            <span v-else class="text-muted">{{ t('systemUser.org.selectOrg') }}</span>
            <span class="panel-subtitle" v-if="selectedOrg">{{ t('systemUser.org.detailInfo') }}</span>
          </div>
          <div class="header-actions" v-if="selectedOrg">
            <el-button type="primary" size="small" :icon="Edit" @click="handleEditOrg">{{ t('systemUser.org.edit') }}</el-button>
            <el-button type="danger" size="small" :icon="Delete" @click="handleDeleteOrg" plain>{{ t('systemUser.org.delete') }}</el-button>
          </div>
        </div>

        <div class="panel-body" v-if="selectedOrg">
          <!-- Organization Info Cards -->
          <div class="info-section">
            <div class="info-grid">
              <div class="info-card">
                <div class="info-icon code">
                  <el-icon><Ticket /></el-icon>
                </div>
                <div class="info-content">
                  <label>{{ t('systemUser.org.orgCode') }}</label>
                  <span>{{ selectedOrg.code }}</span>
                </div>
              </div>
              <div class="info-card">
                <div class="info-icon type">
                  <el-icon><component :is="getNodeIcon(selectedOrg.type)" /></el-icon>
                </div>
                <div class="info-content">
                  <label>{{ t('systemUser.org.type') }}</label>
                  <span class="type-badge" :class="selectedOrg.type">{{ typeLabel(selectedOrg.type) }}</span>
                </div>
              </div>
              <div class="info-card">
                <div class="info-icon parent">
                  <el-icon><Connection /></el-icon>
                </div>
                <div class="info-content">
                  <label>{{ t('systemUser.org.parentOrg') }}</label>
                  <span>{{ parentName || '—' }}</span>
                </div>
              </div>
              <div class="info-card">
                <div class="info-icon manager">
                  <el-icon><User /></el-icon>
                </div>
                <div class="info-content">
                  <label>{{ t('systemUser.org.manager') }}</label>
                  <span>{{ selectedOrg.manager_name || '—' }}</span>
                </div>
              </div>
            </div>

            <div class="detail-list">
              <div class="detail-item">
                <el-icon><Location /></el-icon>
                <label>{{ t('systemUser.org.location') }}</label>
                <span>{{ selectedOrg.location || '—' }}</span>
              </div>
              <div class="detail-item">
                <el-icon><Phone /></el-icon>
                <label>{{ t('systemUser.org.phone') }}</label>
                <span>{{ selectedOrg.phone || '—' }}</span>
              </div>
              <div class="detail-item">
                <el-icon><Message /></el-icon>
                <label>{{ t('systemUser.org.email') }}</label>
                <span>{{ selectedOrg.email || '—' }}</span>
              </div>
              <div class="detail-item" v-if="selectedOrg.description">
                <el-icon><Document /></el-icon>
                <label>{{ t('systemUser.org.description') }}</label>
                <span>{{ selectedOrg.description }}</span>
              </div>
            </div>
          </div>

          <!-- Member Section -->
          <div class="member-section">
            <div class="section-header">
              <el-icon><UserFilled /></el-icon>
              <span>{{ t('systemUser.org.members') }}</span>
              <el-tag size="small" type="info">{{ t('systemUser.org.usersCount', { n: orgUsers.length }) }}</el-tag>
            </div>
            <el-table 
              v-if="orgUsers.length > 0" 
              :data="orgUsers" 
              size="small"
              :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: '600', fontSize: '12px', padding: '8px' }"
            >
              <el-table-column prop="username" :label="t('systemUser.org.username')" width="120">
                <template #default="{ row }">
                  <div class="user-cell">
                    <div class="avatar-mini">{{ row.username.charAt(0).toUpperCase() }}</div>
                    <span>{{ row.username }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="full_name" :label="t('systemUser.org.fullName')" min-width="100" />
              <el-table-column prop="role" :label="t('systemUser.org.role')" width="100">
                <template #default="{ row }">
                  <el-tag size="small" type="primary">{{ row.role }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="email" :label="t('systemUser.org.email')" min-width="160" />
            </el-table>
            <div class="empty-users" v-else>
              <el-icon :size="32"><UserFilled /></el-icon>
              <p>{{ t('systemUser.org.emptyUsersHint') }}</p>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div class="empty-state" v-else>
          <div class="empty-icon">
            <el-icon :size="48"><Select /></el-icon>
          </div>
          <p class="empty-title">{{ t('systemUser.org.emptyTitle') }}</p>
          <p class="empty-desc">{{ t('systemUser.org.emptyDesc') }}</p>
        </div>
      </div>
    </div>

    <!-- Modern Dialog -->
    <el-dialog 
      v-model="orgDialogVisible" 
      :title="orgDialogTitle" 
      width="500px" 
      destroy-on-close 
      @closed="resetOrgForm"
      class="modern-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="orgForm" :rules="orgFormRules" ref="orgFormRef" label-width="90px" label-position="left">
        <el-form-item :label="t('systemUser.org.orgCode')" prop="code">
          <el-input v-model="orgForm.code" :placeholder="t('systemUser.org.codePlaceholder')" :disabled="isEditOrg" />
        </el-form-item>
        <el-form-item :label="t('systemUser.org.nameLabel')" prop="name">
          <el-input v-model="orgForm.name" :placeholder="t('systemUser.org.namePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.org.type')" prop="type">
          <el-select v-model="orgForm.type" :placeholder="t('systemUser.org.typePlaceholder')" style="width: 100%">
            <el-option :label="t('systemUser.org.typeCompany')" value="company">
              <div class="type-option">
                <el-icon><OfficeBuilding /></el-icon>
                <span>{{ t('systemUser.org.typeCompany') }}</span>
              </div>
            </el-option>
            <el-option :label="t('systemUser.org.typeSite')" value="site">
              <div class="type-option">
                <el-icon><House /></el-icon>
                <span>{{ t('systemUser.org.typeSite') }}</span>
              </div>
            </el-option>
            <el-option :label="t('systemUser.org.typeDept')" value="department">
              <div class="type-option">
                <el-icon><Grid /></el-icon>
                <span>{{ t('systemUser.org.typeDept') }}</span>
              </div>
            </el-option>
            <el-option :label="t('systemUser.org.typeSection')" value="section">
              <div class="type-option">
                <el-icon><Folder /></el-icon>
                <span>{{ t('systemUser.org.typeSection') }}</span>
              </div>
            </el-option>
            <el-option :label="t('systemUser.org.typeLine')" value="line">
              <div class="type-option">
                <el-icon><Setting /></el-icon>
                <span>{{ t('systemUser.org.typeLine') }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('systemUser.org.parentOrg')" prop="parent_id">
          <el-tree-select
            v-model="orgForm.parent_id"
            :data="orgTreeForSelect"
            :props="{ label: 'name', children: 'children' }"
            value-key="id"
            :placeholder="t('systemUser.org.parentPlaceholder')"
            clearable
            check-strictly
            style="width: 100%"
            :render-after-expand="false"
          />
        </el-form-item>
        <el-form-item :label="t('systemUser.org.manager')">
          <el-input v-model="orgForm.manager_name" :placeholder="t('systemUser.org.managerPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.org.location')">
          <el-input v-model="orgForm.location" :placeholder="t('systemUser.org.locationPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.org.phone')">
          <el-input v-model="orgForm.phone" :placeholder="t('systemUser.org.phonePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.org.email')">
          <el-input v-model="orgForm.email" type="email" :placeholder="t('systemUser.org.emailPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.org.description')">
          <el-input v-model="orgForm.description" type="textarea" :rows="2" :placeholder="t('systemUser.org.descPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="orgDialogVisible = false">{{ t('systemUser.org.cancel') }}</el-button>
          <el-button type="primary" @click="handleOrgSubmit" :loading="orgSubmitting">
            <el-icon v-if="!orgSubmitting"><Check /></el-icon>
            {{ t('systemUser.org.save') }}
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
import { Plus, OfficeBuilding, House, Grid, Setting, Share, InfoFilled, Document, Edit, Delete, Ticket, Connection, User, Location, Phone, Message, UserFilled, Select, Check, Folder } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import * as systemApi from '@/api/system'
import type { Organization, OrganizationTreeNode } from '@/api/system'

const { t } = useI18n()
const treeProps = { children: 'children', label: 'name' }
const treeLoading = ref(false)
const treeKey = ref(0)
const orgTree = ref<OrganizationTreeNode[]>([])
const selectedOrg = ref<Organization | null>(null)
const orgUsers = ref<{ username: string; full_name: string; role: string; email: string }[]>([])

// Stats computed
const orgCount = computed(() => {
  const count = (nodes: OrganizationTreeNode[]): number => {
    return nodes.reduce((sum, n) => sum + 1 + count(n.children || []), 0)
  }
  return count(orgTree.value)
})
const deptCount = computed(() => {
  const count = (nodes: OrganizationTreeNode[]): number => {
    return nodes.reduce((sum, n) => {
      return sum + (n.type === 'department' ? 1 : 0) + count(n.children || [])
    }, 0)
  }
  return count(orgTree.value)
})

const orgDialogVisible = ref(false)
const orgDialogTitle = ref('')
const isEditOrg = ref(false)
const orgSubmitting = ref(false)
const orgFormRef = ref<FormInstance>()

const orgForm = ref<{
  id: number
  code: string
  name: string
  type: 'company' | 'site' | 'department' | 'section' | 'line'
  parent_id: number | null
  manager_name: string
  location: string
  phone: string
  email: string
  description: string
}>({
  id: 0,
  code: '',
  name: '',
  type: 'department',
  parent_id: 0,
  manager_name: '',
  location: '',
  phone: '',
  email: '',
  description: '',
})

const orgFormRules = computed<FormRules>(() => ({
  code: [{ required: true, message: t('systemUser.org.validationCode'), trigger: 'blur' }],
  name: [{ required: true, message: t('systemUser.org.validationName'), trigger: 'blur' }],
  type: [{ required: true, message: t('systemUser.org.validationType'), trigger: 'change' }],
}))

const typeLabelKey: Record<string, string> = {
  company: 'typeCompany',
  site: 'typeSite',
  department: 'typeDept',
  section: 'typeSection',
  line: 'typeLine',
}
const typeLabel = (type: string) => t(`systemUser.org.${typeLabelKey[type] || 'typeDept'}`)

const parentName = computed(() => {
  if (!selectedOrg.value?.parent_id) return null
  const find = (nodes: OrganizationTreeNode[], id: number): string | null => {
    for (const n of nodes) {
      if (n.id === id) return n.name
      const inChild = find(n.children || [], id)
      if (inChild) return inChild
    }
    return null
  }
  return find(orgTree.value, selectedOrg.value.parent_id)
})

const orgTreeForSelect = computed(() => [
  { id: 0, name: t('systemUser.org.rootOption'), children: orgTree.value },
])

const getNodeIcon = (type: string) => {
  const icons = { company: OfficeBuilding, site: House, department: Grid, section: Folder, line: Setting } as const
  return icons[type as keyof typeof icons] ?? Grid
}

const getNodeBgColor = (type: string) => {
  const colors: Record<string, string> = { 
    company: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', 
    site: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', 
    department: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
    section: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)', 
    line: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' 
  }
  return colors[type] || colors.department
}

async function fetchTree() {
  treeLoading.value = true
  try {
    const res = (await systemApi.getOrganizationTree({ _t: Date.now() })) as unknown as OrganizationTreeNode[]
    orgTree.value = Array.isArray(res) ? res : []
    treeKey.value += 1
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.org.msgTreeError'))
  } finally {
    treeLoading.value = false
  }
}

async function handleNodeClick(nodeData: OrganizationTreeNode) {
  try {
    const org = (await systemApi.getOrganization(nodeData.id)) as unknown as Organization
    selectedOrg.value = org
    orgUsers.value = []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.org.msgDetailError'))
  }
}

async function handleNodeDblclick(nodeData: OrganizationTreeNode) {
  try {
    const org = (await systemApi.getOrganization(nodeData.id)) as unknown as Organization
    selectedOrg.value = org
    orgUsers.value = []
    handleEditOrg()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.org.msgDetailError'))
  }
}

function resetOrgForm() {
  orgForm.value = {
    id: 0,
    code: '',
    name: '',
    type: 'department',
    parent_id: 0,
    manager_name: '',
    location: '',
    phone: '',
    email: '',
    description: '',
  }
}

const handleAddOrg = () => {
  isEditOrg.value = false
  orgDialogTitle.value = t('systemUser.org.formAddTitle')
  resetOrgForm()
  orgDialogVisible.value = true
}

const handleEditOrg = () => {
  if (!selectedOrg.value) return
  isEditOrg.value = true
  orgDialogTitle.value = t('systemUser.org.formEditTitle')
  orgForm.value = {
    id: selectedOrg.value.id,
    code: selectedOrg.value.code,
    name: selectedOrg.value.name,
    type: selectedOrg.value.type,
    parent_id: selectedOrg.value.parent_id ?? 0,
    manager_name: selectedOrg.value.manager_name || '',
    location: selectedOrg.value.location || '',
    phone: selectedOrg.value.phone || '',
    email: selectedOrg.value.email || '',
    description: selectedOrg.value.description || '',
  }
  orgDialogVisible.value = true
}

const handleOrgSubmit = async () => {
  if (!orgFormRef.value) return
  await orgFormRef.value.validate()
  orgSubmitting.value = true
  try {
    const parentId = orgForm.value.parent_id === 0 ? undefined : (orgForm.value.parent_id ?? undefined)
    if (isEditOrg.value) {
      await systemApi.updateOrganization(orgForm.value.id, {
        name: orgForm.value.name,
        type: orgForm.value.type,
        parent_id: parentId,
        manager_name: orgForm.value.manager_name || undefined,
        location: orgForm.value.location || undefined,
        phone: orgForm.value.phone || undefined,
        email: orgForm.value.email || undefined,
        description: orgForm.value.description || undefined,
      })
      ElMessage.success(t('systemUser.org.msgSaveSuccess'))
    } else {
      await systemApi.createOrganization({
        code: orgForm.value.code,
        name: orgForm.value.name,
        type: orgForm.value.type,
        parent_id: parentId,
        manager_name: orgForm.value.manager_name || undefined,
        location: orgForm.value.location || undefined,
        phone: orgForm.value.phone || undefined,
        email: orgForm.value.email || undefined,
        description: orgForm.value.description || undefined,
      })
      ElMessage.success(t('systemUser.org.msgCreateSuccess'))
    }
    orgDialogVisible.value = false
    await fetchTree()
    if (selectedOrg.value && selectedOrg.value.id === orgForm.value.id) {
      const org = (await systemApi.getOrganization(orgForm.value.id)) as unknown as Organization
      selectedOrg.value = org
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.org.msgSaveFailed'))
  } finally {
    orgSubmitting.value = false
  }
}

const handleDeleteOrg = async () => {
  if (!selectedOrg.value) return
  try {
    await ElMessageBox.confirm(t('systemUser.org.msgDeleteConfirm'), t('common.confirm'), { type: 'warning' })
    await systemApi.deleteOrganization(selectedOrg.value.id)
    ElMessage.success(t('systemUser.org.msgDeleteSuccess'))
    selectedOrg.value = null
    await fetchTree()
  } catch (e: unknown) {
    if (e !== 'cancel') ElMessage.error((e as any)?.response?.data?.detail || t('systemUser.org.msgDeleteError'))
  }
}

onMounted(() => fetchTree())
</script>

<style scoped>
/* Base Layout */
.organization-list {
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
  grid-template-columns: 340px 1fr;
  gap: 12px;
  height: calc(100vh - 140px);
}

/* Panel Styles */
.tree-panel,
.detail-panel {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.tree-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f0f9ff;
  font-size: 11px;
  color: #0369a1;
  border-bottom: 1px solid #e0f2fe;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.btn-add-sm {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-size: 12px;
  padding: 6px 12px;
}

/* Tree Styles */
.org-tree {
  --el-tree-node-hover-bg-color: #f1f5f9;
}

.org-tree :deep(.el-tree-node__content) {
  height: 40px;
  border-radius: 8px;
  margin: 2px 0;
  padding-right: 8px;
}

.org-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: #ede9fe;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  cursor: pointer;
  padding: 4px 0;
}

.node-icon-wrapper {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  font-weight: 500;
  color: #1e293b;
  font-size: 13px;
}

.node-type-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.node-type-badge.company { background: #fee2e2; color: #dc2626; }
.node-type-badge.site { background: #fef3c7; color: #d97706; }
.node-type-badge.department { background: #ede9fe; color: #7c3aed; }
.node-type-badge.section { background: #cffafe; color: #0891b2; }
.node-type-badge.line { background: #d1fae5; color: #059669; }

/* Info Section */
.info-section {
  margin-bottom: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 10px;
  transition: all 0.2s;
}

.info-card:hover {
  background: #f1f5f9;
}

.info-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.info-icon.code { background: #ede9fe; color: #7c3aed; }
.info-icon.type { background: #dbeafe; color: #2563eb; }
.info-icon.parent { background: #fef3c7; color: #d97706; }
.info-icon.manager { background: #dcfce7; color: #16a34a; }

.info-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-content label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.info-content span {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.type-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  width: fit-content;
}

.type-badge.company { background: #fee2e2; color: #dc2626; }
.type-badge.site { background: #fef3c7; color: #d97706; }
.type-badge.department { background: #ede9fe; color: #7c3aed; }
.type-badge.section { background: #cffafe; color: #0891b2; }
.type-badge.line { background: #d1fae5; color: #059669; }

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.detail-item .el-icon {
  color: #64748b;
  flex-shrink: 0;
}

.detail-item label {
  font-size: 12px;
  color: #64748b;
  min-width: 70px;
}

.detail-item span {
  font-size: 13px;
  color: #1e293b;
}

/* Member Section */
.member-section {
  border-top: 1px solid #e2e8f0;
  padding-top: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
}

.section-header .el-icon {
  color: #667eea;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-mini {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.empty-users {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  color: #94a3b8;
  text-align: center;
}

.empty-users p {
  margin: 8px 0 0;
  font-size: 13px;
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

/* Type Option in Select */
.type-option {
  display: flex;
  align-items: center;
  gap: 8px;
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

.modern-dialog :deep(.el-form-item) {
  margin-bottom: 16px;
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

/* Responsive Design */
@media (max-width: 1024px) {
  .layout-grid {
    grid-template-columns: 280px 1fr;
  }
  
  .header-stats {
    display: none;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .organization-list {
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
  
  .tree-panel {
    max-height: 350px;
  }
  
  .detail-panel {
    min-height: 400px;
  }
}
</style>
