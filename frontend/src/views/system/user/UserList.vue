<template>
  <div class="user-list">
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon-sm">
          <el-icon :size="18"><User /></el-icon>
        </div>
        <div class="header-text">
          <h1>{{ t('systemUser.user.title') }}</h1>
          <p class="subtitle">{{ t('systemUser.user.subtitle') }}</p>
        </div>
      </div>
      <div class="header-chips">
        <span class="h-chip">
          <strong>{{ pagination.total }}</strong>
          <em>{{ t('systemUser.user.totalUsers') }}</em>
        </span>
        <span class="h-chip ok">
          <strong>{{ activeUserCount }}</strong>
          <em>{{ t('systemUser.user.active') }}</em>
        </span>
        <span class="h-chip warn">
          <strong>{{ lockedUserCount }}</strong>
          <em>{{ t('systemUser.user.locked') }}</em>
        </span>
      </div>
    </div>

    <div class="toolbar-card">
      <div class="filter-row">
        <div class="filter-field filter-field--grow">
          <el-input
            v-model="searchForm.keyword"
            :placeholder="t('systemUser.user.keywordPlaceholder')"
            clearable
            :prefix-icon="Search"
            size="small"
          />
        </div>
        <div class="filter-field">
          <el-select
            v-model="searchForm.department_id"
            :placeholder="t('systemUser.user.department')"
            clearable
            size="small"
          >
            <el-option v-for="d in departmentOptions" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </div>
        <div class="filter-field">
          <el-select
            v-model="searchForm.section_id"
            :placeholder="t('systemUser.user.section')"
            clearable
            size="small"
          >
            <el-option v-for="s in filterSectionOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </div>
        <div class="filter-field filter-field--sm">
          <el-select
            v-model="searchForm.status"
            :placeholder="t('systemUser.user.status')"
            clearable
            size="small"
          >
            <el-option :label="t('systemUser.user.statusActive')" value="active" />
            <el-option :label="t('systemUser.user.statusLocked')" value="locked" />
          </el-select>
        </div>
      </div>
      <div class="toolbar-actions">
        <el-button v-if="canCreate" type="primary" size="small" :icon="Plus" class="btn-add" @click="handleAdd">
          {{ t('systemUser.user.addUser') }}
        </el-button>
        <el-button v-if="canExport" size="small" :icon="Printer" class="btn-print" @click="handlePrint">
          {{ t('systemUser.user.print') }}
        </el-button>
      </div>
    </div>

    <div class="table-card">
      <el-table
        :data="userList"
        v-loading="loading"
        :header-cell-style="tableHeaderStyle"
        :row-class-name="tableRowClassName"
        size="small"
        class="user-table"
      >
        <el-table-column prop="id" :label="t('systemUser.user.id')" width="52" align="center">
          <template #default="{ row }">
            <span class="id-badge">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('systemUser.user.username')" min-width="168">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="avatar-mini" :style="{ background: getAvatarColor(row.username) }">
                {{ row.username.charAt(0).toUpperCase() }}
              </div>
              <div class="user-cell-text">
                <span class="username-text">{{ row.username }}</span>
                <span class="user-sub" v-if="row.full_name">{{ row.full_name }}</span>
                <span class="user-sub muted">{{ row.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="t('systemUser.user.department')" width="140" align="center">
          <template #default="{ row }">
            <div class="org-cell">
              <span v-if="row.department" class="dept-badge">{{ row.department }}</span>
              <span v-if="row.section" class="dept-badge section-badge">{{ row.section }}</span>
              <span v-if="!row.department && !row.section" class="text-muted">—</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="role" :label="t('systemUser.user.role')" width="118" align="center">
          <template #default="{ row }">
            <span class="role-pill" :class="`role-pill--${row.role || 'user'}`">
              {{ displayUserRoleName(row, t) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="t('systemUser.user.statusCol')" width="88" align="center">
          <template #default="{ row }">
            <span class="status-pill" :class="row.status">
              <i class="status-dot" />
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="t('systemUser.user.twoFA')" width="48" align="center">
          <template #default="{ row }">
            <el-tooltip
              :content="row.two_factor ? t('systemUser.user.twoFAOn') : t('systemUser.user.twoFAOff')"
              placement="top"
            >
              <span class="tfa-pill" :class="{ on: row.two_factor }">
                <el-icon :size="14">
                  <component :is="row.two_factor ? CircleCheck : CircleClose" />
                </el-icon>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column
          prop="last_login"
          :label="t('systemUser.user.lastLogin')"
          min-width="128"
          align="center"
        >
          <template #default="{ row }">
            <span class="login-time">{{ row.last_login || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('systemUser.user.actions')" width="118" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-cell">
              <el-button v-if="canEdit" size="small" text type="primary" :icon="Edit" @click="handleEdit(row)" />
              <el-button
                v-if="canEdit && (row.status === 'locked' || row.id !== userStore.user?.id)"
                size="small"
                text
                :type="row.status === 'locked' ? 'success' : 'warning'"
                :icon="row.status === 'locked' ? Unlock : Lock"
                @click="handleToggleLock(row)"
              />
              <el-button v-if="canEdit" size="small" text type="info" :icon="Key" @click="handleResetPassword(row)" />
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="footer-info">
          {{ t('systemUser.user.displayCount', { shown: userList.length, total: pagination.total }) }}
        </span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          size="small"
          background
        />
      </div>
    </div>

    <!-- User form dialog -->
    <el-dialog
      v-model="dialogVisible"
      width="500px"
      destroy-on-close
      class="user-form-dialog"
      :close-on-click-modal="false"
      align-center
    >
      <template #header>
        <div class="ufd-header">
          <div class="ufd-header-glow" />
          <div class="ufd-header-body">
            <div class="ufd-header-icon">
              <el-icon :size="22"><User /></el-icon>
            </div>
            <div>
              <h3 class="ufd-title">{{ dialogTitle }}</h3>
              <p class="ufd-subtitle">
                {{
                  isEdit
                    ? t('systemUser.user.formEditSubtitle')
                    : t('systemUser.user.formAddSubtitle')
                }}
              </p>
            </div>
          </div>
        </div>
      </template>

      <div class="ufd-body">
        <el-form
          :model="userForm"
          :rules="formRules"
          ref="formRef"
          label-position="top"
          class="ufd-form"
        >
          <div class="ufd-section ufd-section--basic">
            <div class="ufd-section-head">
              <el-icon><User /></el-icon>
              <span>{{ t('systemUser.user.formSectionBasic') }}</span>
            </div>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item :label="t('systemUser.user.formUsername')" prop="username">
                  <el-input
                    v-model="userForm.username"
                    :placeholder="t('systemUser.user.formUsernamePlaceholder')"
                    :disabled="isEdit"
                    :prefix-icon="User"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="t('systemUser.user.formFullName')" prop="full_name">
                  <el-input
                    v-model="userForm.full_name"
                    :placeholder="t('systemUser.user.formFullNamePlaceholder')"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item :label="t('systemUser.user.formEmail')" prop="email">
              <el-input
                v-model="userForm.email"
                type="email"
                :placeholder="t('systemUser.user.formEmailPlaceholder')"
              />
            </el-form-item>
          </div>

          <div class="ufd-section ufd-section--access">
            <div class="ufd-section-head">
              <el-icon><Key /></el-icon>
              <span>{{ t('systemUser.user.formSectionAccess') }}</span>
            </div>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item :label="t('systemUser.user.formDept')" prop="department_id">
                  <el-select
                    v-model="userForm.department_id"
                    :placeholder="t('systemUser.user.formDeptPlaceholder')"
                    clearable
                    style="width: 100%"
                  >
                    <el-option
                      v-for="org in departmentOptions"
                      :key="org.id"
                      :label="org.name"
                      :value="org.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="t('systemUser.user.formSection')" prop="section_id">
                  <el-select
                    v-model="userForm.section_id"
                    :placeholder="t('systemUser.user.formSectionPlaceholder')"
                    clearable
                    style="width: 100%"
                  >
                    <el-option
                      v-for="org in formSectionOptions"
                      :key="org.id"
                      :label="org.name"
                      :value="org.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item :label="t('systemUser.user.formRole')" prop="role_id">
                  <el-select
                    v-model="userForm.role_id"
                    :placeholder="t('systemUser.user.formRolePlaceholder')"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="r in roleOptions"
                      :key="r.id"
                      :label="r.name"
                      :value="r.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="ufd-section ufd-section--security">
            <div class="ufd-section-head">
              <el-icon><Lock /></el-icon>
              <span>{{ t('systemUser.user.formSectionSecurity') }}</span>
            </div>
            <div class="ufd-2fa-row">
              <div class="ufd-2fa-text">
                <span class="ufd-2fa-label">{{ t('systemUser.user.form2FA') }}</span>
                <span class="ufd-2fa-hint">{{ t('systemUser.user.form2FAHint') }}</span>
              </div>
              <el-switch
                v-model="userForm.two_factor_enabled"
                :active-text="t('systemUser.user.form2FAOn')"
                :inactive-text="t('systemUser.user.form2FAOff')"
                inline-prompt
              />
            </div>
            <el-form-item
              v-if="!isEdit"
              :label="t('systemUser.user.formPassword')"
              prop="password"
              class="ufd-password-item"
            >
              <el-input
                v-model="userForm.password"
                type="password"
                show-password
                :placeholder="t('systemUser.user.formPasswordPlaceholder')"
                :prefix-icon="Lock"
              />
            </el-form-item>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="ufd-footer">
          <el-button class="ufd-btn-cancel" @click="dialogVisible = false">
            {{ t('systemUser.user.cancel') }}
          </el-button>
          <el-button
            type="primary"
            class="ufd-btn-submit"
            @click="handleSubmit"
            :loading="submitting"
          >
            <el-icon v-if="!submitting"><Check /></el-icon>
            {{ isEdit ? t('systemUser.user.update') : t('systemUser.user.formRegister') }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- パスワード再設定ダイアログ -->
    <el-dialog
      v-model="resetPwdVisible"
      :title="t('systemUser.user.resetPwdTitle')"
      width="420px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="resetPwdUserId = null"
    >
      <el-form
        ref="resetPwdFormRef"
        :model="resetPwdForm"
        :rules="resetPwdRules"
        label-width="140px"
        label-position="left"
      >
        <el-form-item :label="t('systemUser.user.newPassword')" prop="new_password">
          <el-input
            v-model="resetPwdForm.new_password"
            type="password"
            show-password
            :placeholder="t('systemUser.user.formPasswordPlaceholder')"
            autocomplete="new-password"
          />
        </el-form-item>
        <el-form-item :label="t('systemUser.user.confirmPassword')" prop="confirm_password">
          <el-input
            v-model="resetPwdForm.confirm_password"
            type="password"
            show-password
            :placeholder="t('systemUser.user.confirmPasswordPlaceholder')"
            autocomplete="new-password"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resetPwdVisible = false">{{ t('systemUser.user.cancel') }}</el-button>
          <el-button
            type="primary"
            @click="handleResetPasswordSubmit"
            :loading="resetPwdSubmitting"
          >
            {{ t('systemUser.user.update') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Plus,
  Printer,
  CircleCheck,
  CircleClose,
  User,
  Edit,
  Lock,
  Unlock,
  Key,
  Check,
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import * as systemApi from '@/api/system'
import type { UserListItem, PaginatedUserResponse } from '@/api/system'
import { useUserStore } from '@/modules/auth/stores/user'
import { useOperationPermission } from '@/composables/useOperationPermission'
import { OPERATION_MODULE_SYSTEM } from '@/constants/operationModules'
import { displayUserRoleName, resolveUserRoleId } from '@/utils/userRoleDisplay'

const { t } = useI18n()
const userStore = useUserStore()
const { canCreate, canEdit, canExport } = useOperationPermission(OPERATION_MODULE_SYSTEM)

// Computed stats for header
const activeUserCount = computed(() => userList.value.filter((u) => u.status === 'active').length)
const lockedUserCount = computed(() => userList.value.filter((u) => u.status === 'locked').length)

const avatarColors = ['#6366f1', '#8b5cf6', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444']
const getAvatarColor = (name: string) => avatarColors[(name?.charCodeAt(0) || 0) % avatarColors.length]

const tableHeaderStyle = {
  background: '#f8fafc',
  color: '#475569',
  fontWeight: '600',
  fontSize: '11px',
  padding: '6px 0',
}

const tableRowClassName = ({ row }: { row: UserListItem }) => {
  return row.status === 'locked' ? 'row-locked' : ''
}

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()

const resetPwdVisible = ref(false)
const resetPwdUserId = ref<number | null>(null)
const resetPwdForm = reactive({ new_password: '', confirm_password: '' })
const resetPwdFormRef = ref<FormInstance>()
const resetPwdSubmitting = ref(false)
const validateConfirmPassword = (_rule: unknown, value: string, callback: (e?: Error) => void) => {
  if (value !== resetPwdForm.new_password) {
    callback(new Error(t('systemUser.user.validationPasswordMismatch')))
  } else {
    callback()
  }
}
const resetPwdRules = computed<FormRules>(() => ({
  new_password: [
    { required: true, message: t('systemUser.user.validationNewPassword'), trigger: 'blur' },
    { min: 8, message: t('systemUser.user.validationNewPasswordMin'), trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: t('systemUser.user.validationConfirmPassword'), trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}))

const searchForm = reactive({
  keyword: '',
  department_id: null as number | null,
  section_id: null as number | null,
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const userForm = reactive({
  id: 0,
  username: '',
  full_name: '',
  email: '',
  department_id: null as number | null,
  section_id: null as number | null,
  role_id: null as number | null,
  two_factor_enabled: false,
  password: '',
})

type OrgOption = { id: number; name: string; type: string; parent_id: number | null }

const roleOptions = ref<{ id: number; name: string }[]>([])
const allOrgs = ref<OrgOption[]>([])

const departmentOptions = computed(() =>
  allOrgs.value.filter((o) => ['company', 'site', 'department'].includes(o.type)),
)

const filterSectionOptions = computed(() => {
  const sections = allOrgs.value.filter((o) => o.type === 'section')
  if (searchForm.department_id) {
    return sections.filter((s) => s.parent_id === searchForm.department_id)
  }
  return sections
})

const formSectionOptions = computed(() => {
  const sections = allOrgs.value.filter((o) => o.type === 'section')
  if (userForm.department_id) {
    return sections.filter((s) => s.parent_id === userForm.department_id)
  }
  return sections
})

const formRules = computed<FormRules>(() => ({
  username: [{ required: true, message: t('systemUser.user.validationUsername'), trigger: 'blur' }],
  full_name: [
    { required: true, message: t('systemUser.user.validationFullName'), trigger: 'blur' },
  ],
  email: [
    { required: true, message: t('systemUser.user.validationEmail'), trigger: 'blur' },
    { type: 'email', message: t('systemUser.user.validationEmailInvalid'), trigger: 'blur' },
  ],
  role_id: [{ required: true, message: t('systemUser.user.validationRole'), trigger: 'change' }],
  ...(isEdit.value
    ? {}
    : {
        password: [
          { required: true, message: t('systemUser.user.validationPassword'), trigger: 'blur' },
        ],
      }),
}))

const userList = ref<UserListItem[]>([])
const dialogTitle = computed(() =>
  isEdit.value ? t('systemUser.user.formEditTitle') : t('systemUser.user.formAddTitle'),
)

const getStatusLabel = (status: string) => {
  const keyMap: Record<string, string> = {
    active: 'statusActive',
    locked: 'statusLocked',
    inactive: 'statusInactive',
  }
  const key = keyMap[status]
  return key ? t(`systemUser.user.${key}`) : status
}

async function fetchUsers() {
  loading.value = true
  try {
    const res = (await systemApi.getUsers({
      keyword: searchForm.keyword?.trim() || undefined,
      department_id: searchForm.department_id ?? undefined,
      section_id: searchForm.section_id ?? undefined,
      status: (searchForm.status || undefined) as systemApi.UserStatus | undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
    })) as unknown as PaginatedUserResponse
    userList.value = res.items ?? []
    pagination.total = res.total ?? 0
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.user.msgListError'))
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [rolesRes, orgsRes] = await Promise.all([
      systemApi.getRoles(),
      systemApi.getOrganizations(),
    ])
    // request インターセプターが response.data を返すため、getRoles/getOrganizations は配列をそのまま返す
    const roles = Array.isArray(rolesRes) ? rolesRes : ((rolesRes as any)?.data ?? [])
    const orgs = Array.isArray(orgsRes) ? orgsRes : ((orgsRes as any)?.data ?? [])
    roleOptions.value = roles.map((r: { id: number; name: string }) => ({ id: r.id, name: r.name }))
    allOrgs.value = orgs.map(
      (o: { id: number; name: string; type: string; parent_id: number | null }) => ({
        id: o.id,
        name: o.name,
        type: o.type,
        parent_id: o.parent_id,
      }),
    )
  } catch (_) {
    roleOptions.value = []
    allOrgs.value = []
  }
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(userForm, {
    id: 0,
    username: '',
    full_name: '',
    email: '',
    department_id: null,
    section_id: null,
    role_id: null,
    two_factor_enabled: false,
    password: '',
  })
  loadOptions()
  dialogVisible.value = true
  nextTick(() => {
    userForm.username = ''
    userForm.password = ''
    formRef.value?.clearValidate()
  })
}

const handleEdit = async (row: UserListItem) => {
  isEdit.value = true
  await loadOptions()
  Object.assign(userForm, {
    id: row.id,
    username: row.username,
    full_name: row.full_name || '',
    email: row.email,
    department_id: null,
    section_id: null,
    role_id: resolveUserRoleId(row, roleOptions.value),
    two_factor_enabled: row.two_factor,
    password: '',
  })
  const org = departmentOptions.value.find((d) => d.name === row.department)
  if (org) userForm.department_id = org.id
  const sectionOrg = allOrgs.value.find((o) => o.type === 'section' && o.name === row.section)
  if (sectionOrg) userForm.section_id = sectionOrg.id
  dialogVisible.value = true
}

const handleToggleLock = async (row: UserListItem) => {
  if (row.status !== 'locked' && row.id === userStore.user?.id) {
    ElMessage.warning(t('systemUser.user.msgCannotLockSelf'))
    return
  }
  const actionKey = row.status === 'locked' ? 'unlock' : 'lock'
  const action = row.status === 'locked' ? t('systemUser.user.unlock') : t('systemUser.user.lock')
  try {
    const msg =
      row.status === 'locked'
        ? t('systemUser.user.msgUnlockConfirm', { name: row.full_name || row.username })
        : t('systemUser.user.msgLockConfirm', { name: row.full_name || row.username })
    await ElMessageBox.confirm(msg, t('common.confirm'), { type: 'warning' })
    if (row.status === 'locked') {
      await systemApi.unlockUser(row.id)
    } else {
      await systemApi.lockUser(row.id)
    }
    ElMessage.success(t('systemUser.user.msgLockSuccess', { action }))
    fetchUsers()
  } catch (e: unknown) {
    if (e !== 'cancel')
      ElMessage.error((e as any)?.response?.data?.detail || t('systemUser.user.msgResetError'))
  }
}

const handleResetPassword = (row: UserListItem) => {
  resetPwdUserId.value = row.id
  resetPwdForm.new_password = ''
  resetPwdForm.confirm_password = ''
  resetPwdVisible.value = true
  nextTick(() => resetPwdFormRef.value?.clearValidate())
}

const handleResetPasswordSubmit = async () => {
  if (!resetPwdFormRef.value || resetPwdUserId.value == null) return
  await resetPwdFormRef.value.validate()
  resetPwdSubmitting.value = true
  try {
    await systemApi.resetUserPassword(resetPwdUserId.value, {
      new_password: resetPwdForm.new_password,
    })
    ElMessage.success(t('systemUser.user.msgResetSuccess'))
    resetPwdVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.user.msgResetError'))
  } finally {
    resetPwdSubmitting.value = false
  }
}

const handlePrint = () => {
  const rows = userList.value
  const statusLabels: Record<string, string> = {
    active: t('systemUser.user.statusActive'),
    locked: t('systemUser.user.statusLocked'),
    inactive: t('systemUser.user.statusInactive'),
  }
  const headers = [
    t('systemUser.user.id'),
    t('systemUser.user.username'),
    t('systemUser.user.fullName'),
    t('systemUser.user.email'),
    t('systemUser.user.department'),
    t('systemUser.user.section'),
    t('systemUser.user.role'),
    t('systemUser.user.statusCol'),
    t('systemUser.user.twoFA'),
    t('systemUser.user.lastLogin'),
  ]
  const body = rows.map((r) => [
    r.id,
    r.username,
    r.full_name || '—',
    r.email,
    r.department || '—',
    r.section || '—',
    displayUserRoleName(r, t),
    statusLabels[r.status] || r.status,
    r.two_factor ? t('systemUser.user.form2FAOn') : '—',
    r.last_login || '—',
  ])
  const tableRows = body
    .map((cells) => `<tr>${cells.map((c) => `<td>${escapeHtml(String(c))}</td>`).join('')}</tr>`)
    .join('')
  const headerRow = `<tr>${headers.map((h) => `<th>${escapeHtml(h)}</th>`).join('')}</tr>`
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(t('systemUser.user.printTitle'))}</title>
  <style>
    @page { size: A4 landscape; margin: 12mm; }
    body { margin: 0; font-family: sans-serif; }
    table { border-collapse: collapse; width: 100%; font-size: 11px; }
    th, td { border: 1px solid #333; padding: 5px 8px; text-align: left; }
    th { background: #f0f0f0; font-weight: 600; }
  </style>
</head>
<body>
  <h2>${escapeHtml(t('systemUser.user.printTitle'))}</h2>
  <p>${t('systemUser.user.printDateCount', { date: new Date().toLocaleString(), n: rows.length })}</p>
  <table>
    <thead>${headerRow}</thead>
    <tbody>${tableRows}</tbody>
  </table>
</body>
</html>`
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.warning(t('systemUser.user.popupBlocked'))
    return
  }
  w.document.write(html)
  w.document.close()
  w.focus()

  const closePrintWindow = () => {
    w.close()
  }

  w.onload = () => {
    let closed = false
    const doClose = () => {
      if (closed) return
      closed = true
      w.removeEventListener('focus', onFocusBack)
      closePrintWindow()
    }
    // 印刷完了またはキャンセル時にウィンドウを閉じる（標準）
    w.onafterprint = doClose
    // ダイアログを閉じた後にフォーカスが戻った場合も閉じる（キャンセル時のフォールバック）
    const onFocusBack = () => doClose()
    w.addEventListener('focus', onFocusBack)
    w.print()
  }
}

function escapeHtml(s: string): string {
  const el = document.createElement('div')
  el.textContent = s
  return el.innerHTML
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      const roleId = userForm.role_id != null ? Number(userForm.role_id) : undefined
      await systemApi.updateUser(userForm.id, {
        email: userForm.email,
        full_name: userForm.full_name,
        department_id: userForm.department_id ?? undefined,
        section_id: userForm.section_id ?? undefined,
        role_id: roleId,
        two_factor_enabled: userForm.two_factor_enabled,
      })
      ElMessage.success(t('systemUser.user.msgSaveSuccess'))
    } else {
      await systemApi.createUser({
        username: userForm.username,
        email: userForm.email,
        full_name: userForm.full_name,
        department_id: userForm.department_id ?? undefined,
        section_id: userForm.section_id ?? undefined,
        role_id: userForm.role_id ?? undefined,
        two_factor_enabled: userForm.two_factor_enabled,
        password: userForm.password,
      })
      ElMessage.success(t('systemUser.user.msgCreateSuccess'))
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('systemUser.user.msgSaveFailed'))
  } finally {
    submitting.value = false
  }
}

const handleSizeChange = () => fetchUsers()
const handlePageChange = () => fetchUsers()

let keywordDebounceTimer: ReturnType<typeof setTimeout> | null = null
watch(
  () => searchForm.department_id,
  () => {
    if (
      searchForm.section_id &&
      !filterSectionOptions.value.some((s) => s.id === searchForm.section_id)
    ) {
      searchForm.section_id = null
    }
  },
)

watch(
  () => userForm.department_id,
  () => {
    if (userForm.section_id && !formSectionOptions.value.some((s) => s.id === userForm.section_id)) {
      userForm.section_id = null
    }
  },
)

watch(
  () => [searchForm.keyword, searchForm.department_id, searchForm.section_id, searchForm.status],
  () => {
    pagination.page = 1
    if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
    keywordDebounceTimer = setTimeout(() => {
      keywordDebounceTimer = null
      fetchUsers()
    }, 300)
  },
  { deep: true },
)

onMounted(() => {
  loadOptions()
  fetchUsers()
})
</script>

<style scoped>
.user-list {
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
  background: linear-gradient(120deg, #0ea5e9 0%, #6366f1 55%, #8b5cf6 100%);
  box-shadow: 0 4px 14px rgba(14, 165, 233, 0.25);
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
  color: rgba(255, 255, 255, 0.85);
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
  opacity: 0.88;
}

.h-chip.ok {
  background: rgba(255, 255, 255, 0.22);
}

.h-chip.warn {
  background: rgba(251, 191, 36, 0.35);
}

.toolbar-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 10px;
  margin-bottom: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.filter-field {
  width: 132px;
}

.filter-field--grow {
  flex: 1;
  min-width: 140px;
  max-width: 280px;
}

.filter-field--sm {
  width: 108px;
}

.filter-field :deep(.el-input),
.filter-field :deep(.el-select) {
  width: 100%;
}

.toolbar-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.btn-add {
  border: none;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  font-weight: 600;
}

.btn-print {
  color: #475569;
}

.table-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.user-table :deep(.el-table) {
  --el-table-border-color: #f1f5f9;
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: #f8fafc;
}

.user-table :deep(.el-table th.el-table__cell) {
  border-bottom: 1px solid #e2e8f0;
  padding: 6px 4px;
}

.user-table :deep(.el-table td.el-table__cell) {
  padding: 5px 4px;
  border-bottom: 1px solid #f8fafc;
}

.user-table :deep(.row-locked > td) {
  background: #fffbeb !important;
}

.id-badge {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: left;
}

.avatar-mini {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-cell-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.username-text {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.25;
}

.user-sub {
  font-size: 10px;
  color: #475569;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-sub.muted {
  color: #94a3b8;
}

.org-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.dept-badge {
  display: inline-block;
  max-width: 100%;
  padding: 1px 6px;
  border-radius: 4px;
  background: #e0f2fe;
  color: #0369a1;
  font-size: 10px;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.section-badge {
  background: #ecfeff;
  color: #0e7490;
}

.text-muted {
  color: #cbd5e1;
  font-size: 11px;
}

.role-pill {
  display: inline-block;
  max-width: 100%;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  line-height: 1.35;
  background: #f1f5f9;
  color: #475569;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-pill--admin {
  background: #fee2e2;
  color: #b91c1c;
}

.role-pill--manager {
  background: #dcfce7;
  color: #15803d;
}

.role-pill--worker {
  background: #fef3c7;
  color: #b45309;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #64748b;
}

.status-pill.active {
  background: #dcfce7;
  color: #15803d;
}

.status-pill.locked {
  background: #fef3c7;
  color: #b45309;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.85;
}

.tfa-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #94a3b8;
}

.tfa-pill.on {
  background: #dcfce7;
  color: #16a34a;
}

.login-time {
  font-size: 10px;
  color: #64748b;
}

.action-cell {
  display: flex;
  justify-content: center;
  gap: 0;
}

.action-cell :deep(.el-button) {
  padding: 4px;
  margin: 0;
}

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.footer-info {
  font-size: 11px;
  color: #64748b;
}

/* User form dialog */
.user-form-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 20px 50px rgba(102, 126, 234, 0.22),
    0 8px 24px rgba(15, 23, 42, 0.12);
  animation: ufd-dialog-in 0.32s cubic-bezier(0.34, 1.4, 0.64, 1);
}

@keyframes ufd-dialog-in {
  from {
    opacity: 0;
    transform: scale(0.94) translateY(12px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.user-form-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

.user-form-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  z-index: 2;
}

.user-form-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
  font-size: 16px;
}

.user-form-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.user-form-dialog :deep(.el-dialog__footer) {
  padding: 0;
}

.ufd-header {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.ufd-header-glow {
  position: absolute;
  top: -40px;
  right: -20px;
  width: 140px;
  height: 140px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.28) 0%, transparent 70%);
  pointer-events: none;
}

.ufd-header-body {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
}

.ufd-header-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.ufd-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.3px;
}

.ufd-subtitle {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.82);
}

.ufd-body {
  padding: 10px 12px 6px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  max-height: 62vh;
  overflow-y: auto;
}

.ufd-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.ufd-form :deep(.el-form-item__label) {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding-bottom: 2px;
  line-height: 1.2;
}

.ufd-form :deep(.el-input__wrapper),
.ufd-form :deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition:
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.ufd-form :deep(.el-input__wrapper:hover),
.ufd-form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.14);
}

.ufd-form :deep(.el-input__wrapper.is-focus),
.ufd-form :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 2px rgba(102, 126, 234, 0.2),
    0 4px 12px rgba(102, 126, 234, 0.15);
}

.ufd-section {
  background: #fff;
  border-radius: 10px;
  padding: 10px 12px 4px;
  margin-bottom: 8px;
  border: 1px solid #e8edf5;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
  transition:
    box-shadow 0.25s ease,
    transform 0.25s ease;
  animation: ufd-section-in 0.35s ease backwards;
}

.ufd-section--basic {
  animation-delay: 0.04s;
  border-left: 3px solid #667eea;
}

.ufd-section--access {
  animation-delay: 0.1s;
  border-left: 3px solid #0ea5e9;
}

.ufd-section--security {
  animation-delay: 0.16s;
  border-left: 3px solid #f59e0b;
  margin-bottom: 4px;
}

@keyframes ufd-section-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ufd-section:hover {
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
}

.ufd-section-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
}

.ufd-section--basic .ufd-section-head {
  color: #667eea;
}

.ufd-section--access .ufd-section-head {
  color: #0ea5e9;
}

.ufd-section--security .ufd-section-head {
  color: #d97706;
}

.ufd-2fa-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 8px;
  margin-bottom: 6px;
  background: #fffbeb;
  border-radius: 8px;
  border: 1px solid #fde68a;
}

.ufd-2fa-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.ufd-2fa-label {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}

.ufd-2fa-hint {
  font-size: 10px;
  color: #94a3b8;
}

.ufd-password-item {
  margin-bottom: 4px !important;
}

.ufd-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 14px;
  background: #fff;
  border-top: 1px solid #e8edf5;
}

.ufd-btn-cancel {
  border-radius: 8px;
  padding: 8px 16px;
  transition: all 0.2s ease;
}

.ufd-btn-cancel:hover {
  transform: translateY(-1px);
}

.ufd-btn-submit {
  border-radius: 8px;
  padding: 8px 18px;
  font-weight: 600;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
  transition: all 0.22s ease;
}

.ufd-btn-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(102, 126, 234, 0.45);
}

@media (max-width: 1100px) {
  .header-chips {
    display: none;
  }

  .filter-field {
    width: 120px;
  }
}

@media (max-width: 768px) {
  .user-list {
    padding: 8px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar-card {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-field,
  .filter-field--grow,
  .filter-field--sm {
    width: 100%;
    max-width: none;
  }

  .toolbar-actions {
    justify-content: flex-end;
  }

  .table-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
