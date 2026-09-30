<template>
  <div class="organization-list org-modern">
    <!-- Modern Gradient Header -->
    <div class="page-header">
      <div class="page-header-fx" aria-hidden="true"><span class="fx-orb orb-a" /><span class="fx-orb orb-b" /><span class="fx-grid" /><span class="fx-sheen" /></div>
      <div class="header-content">
        <div class="header-icon">
          <el-icon :size="28"><OfficeBuilding /></el-icon>
        </div>
        <div class="header-text">
          <h1>{{ t('systemUser.org.title') }}</h1>
          <p class="subtitle">{{ t('systemUser.org.subtitle') }}</p>
        </div>
      </div>
      <div class="header-stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
        <div class="stat-item stat-item--total">
          <span class="stat-value">{{ orgCount }}</span>
          <span class="stat-label">{{ t('systemUser.org.totalOrgs') }}</span>
        </div>
        <div class="stat-item stat-item--site">
          <span class="stat-value">{{ siteCount }}</span>
          <span class="stat-label">{{ t('systemUser.org.typeSite') }}</span>
        </div>
        <div class="stat-item stat-item--dept">
          <span class="stat-value highlight">{{ deptCount }}</span>
          <span class="stat-label">{{ t('systemUser.org.depts') }}</span>
        </div>
        <div class="stat-item stat-item--line">
          <span class="stat-value">{{ sectionLineCount }}</span>
          <span class="stat-label">{{ t('systemUser.org.typeSection') }}・{{ t('systemUser.org.typeLine') }}</span>
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
            <el-button type="primary" size="small" :icon="Edit" class="org-btn-edit" @click="handleEditOrg">{{ t('systemUser.org.edit') }}</el-button>
            <el-button type="danger" size="small" :icon="Delete" class="org-btn-del" @click="handleDeleteOrg" plain>{{ t('systemUser.org.delete') }}</el-button>
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
const countOrgTypes = (types: string[]) => {
  const count = (nodes: OrganizationTreeNode[]): number =>
    nodes.reduce((sum, n) => sum + (types.includes(n.type) ? 1 : 0) + count(n.children || []), 0)
  return count(orgTree.value)
}
const siteCount = computed(() => countOrgTypes(['site']))
const sectionLineCount = computed(() => countOrgTypes(['section', 'line']))

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-item')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-item').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 14).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 14).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-item').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

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

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（組織・部門管理 / エバーグリーン：深松→翠→黄緑）
 * ============================================================ */
.org-modern {
  --hx-1: #052e16;
  --hx-2: #166534;
  --hx-3: #16a34a;
  --hx-4: #a3e635;
  --hx-deep: #166534;
  --hx-soft: #f0fdf4;
  --hx-line: rgba(22, 163, 74, 0.18);
  background:
    radial-gradient(ellipse 80% 50% at 8% -8%, rgba(22, 163, 74, 0.1), transparent 55%),
    radial-gradient(ellipse 55% 42% at 96% 2%, rgba(163, 230, 53, 0.1), transparent 50%),
    linear-gradient(165deg, #f1f5f9 0%, #f0fdf4 40%, #f8fafc 100%);
}

.org-modern .page-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 14px 20px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 36%, var(--hx-3) 70%, var(--hx-4) 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.18) inset,
    0 14px 32px -12px rgba(22, 101, 52, 0.6),
    0 2px 6px rgba(15, 23, 42, 0.08);
}

.org-modern .page-header > :not(.page-header-fx) {
  position: relative;
  z-index: 1;
}

.org-modern .page-header-fx {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.org-modern .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(22px);
  opacity: 0.55;
  animation: orgOrbFloat 11s ease-in-out infinite;
}

.org-modern .orb-a {
  width: 180px;
  height: 180px;
  top: -70px;
  right: 26%;
  background: radial-gradient(circle, #bef264 0%, transparent 70%);
}

.org-modern .orb-b {
  width: 150px;
  height: 150px;
  bottom: -70px;
  left: 30%;
  background: radial-gradient(circle, #6ee7b7 0%, transparent 70%);
  animation-delay: -5s;
}

.org-modern .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse 70% 90% at 70% 40%, #000 20%, transparent 75%);
}

.org-modern .fx-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 30%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.18), transparent);
  transform: skewX(-18deg);
  animation: orgSheen 7s ease-in-out infinite;
}

@keyframes orgOrbFloat {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(18px, 10px) scale(1.12);
  }
}

@keyframes orgSheen {
  0% {
    left: -40%;
  }
  60%,
  100% {
    left: 130%;
  }
}

.org-modern .header-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 4px 0 rgba(5, 46, 22, 0.5),
    0 10px 18px -6px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  animation: orgBuildingRise 3.6s ease-in-out infinite;
}

@keyframes orgBuildingRise {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

.org-modern .header-text h1 {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 8px rgba(5, 46, 22, 0.4);
}

.org-modern .header-text .subtitle {
  color: rgba(240, 253, 244, 0.88);
}

/* 統計カード */
.org-modern .header-stats {
  gap: 10px;
  padding: 0;
  background: transparent;
  backdrop-filter: none;
  perspective: 650px;
}

.org-modern .stat-item {
  position: relative;
  overflow: hidden;
  min-width: 74px;
  padding: 8px 12px 7px;
  border-radius: 12px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow:
    0 4px 0 rgba(5, 46, 22, 0.45),
    0 12px 22px -10px rgba(0, 0, 0, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transform-style: preserve-3d;
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transition:
    transform 0.18s ease,
    background 0.2s ease;
}

.org-modern .stat-item:hover {
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.12));
}

.org-modern .stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--sc);
  box-shadow: 0 0 10px var(--sc);
}

.org-modern .stat-item::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 0%), rgba(255, 255, 255, 0.28), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.org-modern .stat-item:hover::after {
  opacity: 1;
}

.org-modern .stat-value {
  display: block;
  line-height: 1.1;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  transform: translateZ(14px);
  text-shadow: 0 2px 6px rgba(5, 46, 22, 0.45);
}

.org-modern .stat-value.highlight {
  color: #fff;
}

.org-modern .stat-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: rgba(240, 253, 244, 0.85);
  white-space: nowrap;
}

.org-modern .stat-item--total {
  --sc: #bef264;
}

.org-modern .stat-item--site {
  --sc: #fcd34d;
}

.org-modern .stat-item--dept {
  --sc: #c4b5fd;
}

.org-modern .stat-item--line {
  --sc: #67e8f9;
}

/* パネル（ツリー：緑 / 詳細：スカイ） */
.org-modern .tree-panel,
.org-modern .detail-panel {
  --pc: #16a34a;
  --pc-deep: #166534;
  position: relative;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--pc) 20%, transparent);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 10px 26px -14px color-mix(in srgb, var(--pc) 55%, transparent),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.org-modern .detail-panel {
  --pc: #0284c7;
  --pc-deep: #075985;
}

.org-modern .tree-panel::before,
.org-modern .detail-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, var(--pc-deep), var(--pc));
}

.org-modern .panel-header {
  padding-top: 14px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--pc) 7%, #fff) 0%, #fff 100%);
  border-bottom-color: color-mix(in srgb, var(--pc) 16%, transparent);
}

.org-modern .panel-title .el-icon,
.org-modern .section-header .el-icon {
  color: var(--pc);
}

.org-modern .tree-hint {
  background: linear-gradient(90deg, #f0fdf4, #f7fee7);
  color: #166534;
  border-bottom-color: rgba(22, 163, 74, 0.14);
}

/* ツリーノード */
.org-modern .org-tree {
  --el-tree-node-hover-bg-color: #f0fdf4;
}

.org-modern .org-tree :deep(.el-tree-node__content) {
  transition:
    background 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.org-modern .org-tree :deep(.el-tree-node__content:hover) {
  transform: translateX(2px);
}

.org-modern .org-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: linear-gradient(90deg, #dcfce7, #f7fee7);
  box-shadow:
    inset 3px 0 0 var(--hx-3),
    0 4px 10px -6px rgba(22, 163, 74, 0.45);
}

.org-modern .node-icon-wrapper {
  box-shadow:
    0 3px 0 rgba(15, 23, 42, 0.22),
    0 6px 12px -4px rgba(15, 23, 42, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition: transform 0.2s ease;
}

.org-modern .org-tree :deep(.el-tree-node__content:hover) .node-icon-wrapper {
  transform: translateY(-2px) rotate(-6deg);
}

.org-modern .node-type-badge,
.org-modern .type-badge {
  font-weight: 700;
  border-radius: 999px;
  box-shadow:
    inset 0 0 0 1px color-mix(in srgb, currentColor 25%, transparent),
    0 2px 0 color-mix(in srgb, currentColor 18%, transparent);
}

/* 詳細カード */
.org-modern .info-grid {
  perspective: 800px;
}

.org-modern .info-card {
  --ic: #7c3aed;
  position: relative;
  overflow: hidden;
  background: linear-gradient(160deg, #fff 0%, color-mix(in srgb, var(--ic) 6%, #fff) 100%);
  border: 1px solid color-mix(in srgb, var(--ic) 18%, transparent);
  box-shadow:
    0 3px 0 color-mix(in srgb, var(--ic) 16%, transparent),
    0 10px 20px -12px color-mix(in srgb, var(--ic) 50%, transparent);
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.org-modern .info-card:hover {
  background: linear-gradient(160deg, #fff 0%, color-mix(in srgb, var(--ic) 10%, #fff) 100%);
  transform: translateY(-3px) rotateX(4deg);
  box-shadow:
    0 5px 0 color-mix(in srgb, var(--ic) 20%, transparent),
    0 16px 26px -12px color-mix(in srgb, var(--ic) 55%, transparent);
}

.org-modern .info-card:has(.info-icon.type) {
  --ic: #2563eb;
}

.org-modern .info-card:has(.info-icon.parent) {
  --ic: #d97706;
}

.org-modern .info-card:has(.info-icon.manager) {
  --ic: #16a34a;
}

.org-modern .info-icon {
  box-shadow:
    0 3px 0 color-mix(in srgb, currentColor 30%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.org-modern .detail-item {
  border: 1px solid #eef2f7;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.org-modern .detail-item:hover {
  border-color: rgba(2, 132, 199, 0.25);
  box-shadow: inset 3px 0 0 #0284c7;
  transform: translateX(2px);
}

.org-modern .detail-item .el-icon {
  color: #0284c7;
}

.org-modern .avatar-mini {
  background: linear-gradient(135deg, #22c55e 0%, #15803d 100%);
  box-shadow: 0 2px 0 rgba(21, 128, 61, 0.4);
}

.org-modern .empty-icon {
  background: linear-gradient(145deg, #f0fdf4, #dcfce7);
  box-shadow:
    0 6px 0 rgba(22, 163, 74, 0.15),
    0 16px 28px -12px rgba(22, 163, 74, 0.45);
  animation: orgBuildingRise 3.6s ease-in-out infinite;
}

.org-modern .empty-icon .el-icon {
  color: #16a34a;
}

/* 立体ボタン（キーキャップ） */
.org-modern .btn-add-sm,
.org-modern .org-btn-edit,
.org-modern .org-btn-del,
.org-modern .dialog-footer .el-button--primary {
  --k-edge: #166534;
  --k-glow: rgba(22, 163, 74, 0.5);
  border: none;
  border-radius: 8px;
  font-weight: 700;
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    filter 0.12s ease;
}

.org-modern .btn-add-sm,
.org-modern .btn-add-sm:hover,
.org-modern .dialog-footer .el-button--primary,
.org-modern .dialog-footer .el-button--primary:hover {
  color: #fff;
  background: linear-gradient(180deg, #4ade80 0%, #22c55e 45%, #16a34a 100%);
}

.org-modern .org-btn-edit,
.org-modern .org-btn-edit:hover {
  --k-edge: #075985;
  --k-glow: rgba(2, 132, 199, 0.5);
  color: #fff;
  background: linear-gradient(180deg, #38bdf8 0%, #0ea5e9 45%, #0284c7 100%);
}

.org-modern .org-btn-del {
  --k-edge: #fecaca;
  --k-glow: rgba(220, 38, 38, 0.3);
  border: 1px solid #fecaca;
}

.org-modern .org-btn-del:hover {
  --k-edge: #991b1b;
  color: #fff;
  background: linear-gradient(180deg, #f87171 0%, #ef4444 45%, #dc2626 100%);
}

.org-modern .btn-add-sm:hover,
.org-modern .org-btn-edit:hover,
.org-modern .org-btn-del:hover,
.org-modern .dialog-footer .el-button--primary:hover {
  transform: translateY(-2px);
  filter: brightness(1.06);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.org-modern .btn-add-sm:active,
.org-modern .org-btn-edit:active,
.org-modern .org-btn-del:active,
.org-modern .dialog-footer .el-button--primary:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

/* ダイアログ */
.org-modern .modern-dialog :deep(.el-dialog__header) {
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 45%, var(--hx-3) 100%);
}

@media (prefers-reduced-motion: reduce) {
  .org-modern .fx-orb,
  .org-modern .fx-sheen,
  .org-modern .header-icon,
  .org-modern .empty-icon {
    animation: none;
  }

  .org-modern .stat-item,
  .org-modern .info-card:hover {
    transform: none;
  }
}
</style>
