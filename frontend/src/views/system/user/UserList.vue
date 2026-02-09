<template>
  <div class="user-list">
    <!-- Modern Gradient Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon :size="28"><User /></el-icon>
        </div>
        <div class="header-text">
          <h1>{{ t('systemUser.user.title') }}</h1>
          <p class="subtitle">{{ t('systemUser.user.subtitle') }}</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ pagination.total }}</span>
          <span class="stat-label">{{ t('systemUser.user.totalUsers') }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value active">{{ activeUserCount }}</span>
          <span class="stat-label">{{ t('systemUser.user.active') }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value locked">{{ lockedUserCount }}</span>
          <span class="stat-label">{{ t('systemUser.user.locked') }}</span>
        </div>
      </div>
    </div>

    <!-- Compact Filter & Actions Card -->
    <div class="filter-card">
      <div class="filter-grid">
        <div class="filter-item">
          <label>{{ t('systemUser.user.keyword') }}</label>
          <el-input 
            v-model="searchForm.keyword" 
            :placeholder="t('systemUser.user.keywordPlaceholder')" 
            clearable 
            :prefix-icon="Search"
            size="default"
          />
        </div>
        <div class="filter-item">
          <label>{{ t('systemUser.user.department') }}</label>
          <el-select v-model="searchForm.department_id" :placeholder="t('systemUser.user.all')" clearable size="default" style="width: 100%">
            <el-option v-for="d in departmentOptions" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </div>
        <div class="filter-item">
          <label>{{ t('systemUser.user.status') }}</label>
          <el-select v-model="searchForm.status" :placeholder="t('systemUser.user.all')" clearable size="default">
            <el-option :label="t('systemUser.user.statusActive')" value="active" />
            <el-option :label="t('systemUser.user.statusLocked')" value="locked" />
          </el-select>
        </div>
      </div>
      <div class="toolbar-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd" class="btn-add">
          <span>{{ t('systemUser.user.addUser') }}</span>
        </el-button>
        <el-button :icon="Printer" @click="handlePrint" class="btn-print">{{ t('systemUser.user.print') }}</el-button>
      </div>
    </div>

    <!-- Enhanced Table Card -->
    <div class="table-card">
      <el-table 
        :data="userList" 
        v-loading="loading" 
        :header-cell-style="{ background: '#f8fafc', color: '#334155', fontWeight: '600', fontSize: '13px' }"
        :row-class-name="tableRowClassName"
        border
        size="default"
      >
        <el-table-column prop="id" :label="t('systemUser.user.id')" width="80" align="center">
          <template #default="{ row }">
            <span class="id-badge">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="username" :label="t('systemUser.user.username')" width="130" align="center">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="avatar-mini">{{ row.username.charAt(0).toUpperCase() }}</div>
              <span class="username-text">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="full_name" :label="t('systemUser.user.fullName')" width="100" align="center"/>
        <el-table-column prop="email" :label="t('systemUser.user.email')" width="220">
          <template #default="{ row }">
            <span class="email-text">{{ row.email }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="department" :label="t('systemUser.user.department')" width="250" align="center">
          <template #default="{ row }">
            <span class="dept-badge" v-if="row.department">{{ row.department }}</span>
            <span class="text-muted" v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="role" :label="t('systemUser.user.role')" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small" effect="dark" class="role-tag">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('systemUser.user.statusCol')" width="110" align="center">
          <template #default="{ row }">
            <div class="status-indicator" :class="row.status">
              <span class="status-dot"></span>
              <span>{{ getStatusLabel(row.status) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="two_factor" :label="t('systemUser.user.twoFA')" width="70" align="center">
          <template #default="{ row }">
            <el-tooltip :content="row.two_factor ? t('systemUser.user.twoFAOn') : t('systemUser.user.twoFAOff')" placement="top">
              <div class="tfa-indicator" :class="{ enabled: row.two_factor }">
                <el-icon :size="16">
                  <component :is="row.two_factor ? CircleCheck : CircleClose" />
                </el-icon>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" :label="t('systemUser.user.lastLogin')" min-width="180" align="center">
          <template #default="{ row }">
            <span class="login-time">{{ row.last_login || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('systemUser.user.actions')" width="170" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-cell">
              <el-tooltip :content="t('systemUser.user.edit')" placement="top">
                <el-button size="small" type="primary" circle :icon="Edit" @click="handleEdit(row)" />
              </el-tooltip>
              <el-tooltip :content="row.status === 'locked' ? t('systemUser.user.unlock') : t('systemUser.user.lock')" placement="top">
                <el-button 
                  v-if="row.status === 'locked' || row.id !== userStore.user?.id"
                  size="small" 
                  :type="row.status === 'locked' ? 'success' : 'warning'" 
                  circle 
                  :icon="row.status === 'locked' ? Unlock : Lock"
                  @click="handleToggleLock(row)"
                />
                <el-button v-else size="small" circle :icon="Lock" disabled class="btn-disabled" />
              </el-tooltip>
              <el-tooltip :content="t('systemUser.user.resetPwd')" placement="top">
                <el-button size="small" type="info" circle :icon="Key" @click="handleResetPassword(row)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <div class="footer-info">
          {{ t('systemUser.user.displayCount', { shown: userList.length, total: pagination.total }) }}
        </div>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          small
          background
        />
      </div>
    </div>

    <!-- Modern Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="520px" 
      destroy-on-close
      class="modern-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="userForm" :rules="formRules" ref="formRef" label-width="100px" label-position="left">
        <el-form-item :label="t('systemUser.user.formUsername')" prop="username">
          <el-input v-model="userForm.username" :placeholder="t('systemUser.user.formUsernamePlaceholder')" :disabled="isEdit" />
        </el-form-item>
        <el-form-item :label="t('systemUser.user.formFullName')" prop="full_name">
          <el-input v-model="userForm.full_name" :placeholder="t('systemUser.user.formFullNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.user.formEmail')" prop="email">
          <el-input v-model="userForm.email" type="email" :placeholder="t('systemUser.user.formEmailPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.user.formDept')" prop="department_id">
          <el-select v-model="userForm.department_id" :placeholder="t('systemUser.user.formDeptPlaceholder')" clearable style="width: 100%">
            <el-option v-for="org in departmentOptions" :key="org.id" :label="org.name" :value="org.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('systemUser.user.formRole')" prop="role_id">
          <el-select v-model="userForm.role_id" :placeholder="t('systemUser.user.formRolePlaceholder')" style="width: 100%">
            <el-option v-for="r in roleOptions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('systemUser.user.form2FA')">
          <el-switch v-model="userForm.two_factor_enabled" :active-text="t('systemUser.user.form2FAOn')" :inactive-text="t('systemUser.user.form2FAOff')" />
        </el-form-item>
        <el-form-item :label="t('systemUser.user.formPassword')" prop="password" v-if="!isEdit">
          <el-input v-model="userForm.password" type="password" show-password :placeholder="t('systemUser.user.formPasswordPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">{{ t('systemUser.user.cancel') }}</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            <el-icon v-if="!submitting"><Check /></el-icon>
            {{ t('systemUser.user.save') }}
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
          <el-button type="primary" @click="handleResetPasswordSubmit" :loading="resetPwdSubmitting">
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
import { Search, Plus, Printer, CircleCheck, CircleClose, User, Edit, Lock, Unlock, Key, Check } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import * as systemApi from '@/api/system'
import type { UserListItem, PaginatedUserResponse } from '@/api/system'
import { useUserStore } from '@/modules/auth/stores/user'

const { t } = useI18n()
const userStore = useUserStore()

// Computed stats for header
const activeUserCount = computed(() => userList.value.filter(u => u.status === 'active').length)
const lockedUserCount = computed(() => userList.value.filter(u => u.status === 'locked').length)

// Table row class for hover effects
const tableRowClassName = ({ row }: { row: UserListItem }) => {
  return row.status === 'locked' ? 'row-locked' : ''
}

// Role label mapping（i18n）
const getRoleLabel = (role: string) => {
  const keyMap: Record<string, string> = {
    admin: 'roleAdmin',
    user: 'roleUser',
    manager: 'roleManager',
    worker: 'roleWorker',
    guest: 'roleGuest',
    viewer: 'roleViewer',
  }
  const key = keyMap[role]
  return key ? t(`systemUser.user.${key}`) : role
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
  role_id: null as number | null,
  two_factor_enabled: false,
  password: '',
})

const roleOptions = ref<{ id: number; name: string }[]>([])
const departmentOptions = ref<{ id: number; name: string }[]>([])

const formRules = computed<FormRules>(() => ({
  username: [{ required: true, message: t('systemUser.user.validationUsername'), trigger: 'blur' }],
  full_name: [{ required: true, message: t('systemUser.user.validationFullName'), trigger: 'blur' }],
  email: [
    { required: true, message: t('systemUser.user.validationEmail'), trigger: 'blur' },
    { type: 'email', message: t('systemUser.user.validationEmailInvalid'), trigger: 'blur' },
  ],
  role_id: [{ required: true, message: t('systemUser.user.validationRole'), trigger: 'change' }],
  ...(isEdit.value ? {} : { password: [{ required: true, message: t('systemUser.user.validationPassword'), trigger: 'blur' }] }),
}))

const userList = ref<UserListItem[]>([])
const dialogTitle = computed(() => (isEdit.value ? t('systemUser.user.formEditTitle') : t('systemUser.user.formAddTitle')))

type TagType = 'primary' | 'success' | 'warning' | 'danger' | 'info'
const getRoleType = (role: string): TagType => {
  const types: Record<string, TagType> = {
    admin: 'danger',
    user: 'primary',
    manager: 'success',
    worker: 'warning',
    guest: 'info',
    viewer: 'info',
  }
  return types[role] || 'info'
}
const getStatusLabel = (status: string) => {
  const keyMap: Record<string, string> = { active: 'statusActive', locked: 'statusLocked', inactive: 'statusInactive' }
  const key = keyMap[status]
  return key ? t(`systemUser.user.${key}`) : status
}

async function fetchUsers() {
  loading.value = true
  try {
    const res = (await systemApi.getUsers({
      keyword: searchForm.keyword?.trim() || undefined,
      department_id: searchForm.department_id ?? undefined,
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
    const roles = Array.isArray(rolesRes) ? rolesRes : (rolesRes as any)?.data ?? []
    const orgs = Array.isArray(orgsRes) ? orgsRes : (orgsRes as any)?.data ?? []
    roleOptions.value = roles.map((r: { id: number; name: string }) => ({ id: r.id, name: r.name }))
    departmentOptions.value = orgs
      .filter((o: { type: string }) => o.type === 'department' || o.type === 'site' || o.type === 'company')
      .map((o: { id: number; name: string }) => ({ id: o.id, name: o.name }))
  } catch (_) {
    roleOptions.value = []
    departmentOptions.value = []
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

const roleCodeToName = computed(() => ({
  admin: t('systemUser.user.roleAdmin'),
  user: t('systemUser.user.roleUser'),
  manager: t('systemUser.user.roleManager'),
  worker: t('systemUser.user.roleWorker'),
  guest: t('systemUser.user.roleGuest'),
  viewer: t('systemUser.user.roleViewer'),
}))

const handleEdit = async (row: UserListItem) => {
  isEdit.value = true
  await loadOptions()
  const roleName = roleCodeToName.value[row.role] || row.role
  const matchedRole = roleOptions.value.find((r) => r.name === roleName)
  Object.assign(userForm, {
    id: row.id,
    username: row.username,
    full_name: row.full_name || '',
    email: row.email,
    department_id: null,
    role_id: matchedRole?.id ?? null,
    two_factor_enabled: row.two_factor,
    password: '',
  })
  const org = departmentOptions.value.find((d) => d.name === row.department)
  if (org) userForm.department_id = org.id
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
    const msg = row.status === 'locked'
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
    if (e !== 'cancel') ElMessage.error((e as any)?.response?.data?.detail || t('systemUser.user.msgResetError'))
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
    await systemApi.resetUserPassword(resetPwdUserId.value, { new_password: resetPwdForm.new_password })
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
  const roleLabels: Record<string, string> = {
    admin: t('systemUser.user.roleAdmin'),
    user: t('systemUser.user.roleUser'),
    manager: t('systemUser.user.roleManager'),
    worker: t('systemUser.user.roleWorker'),
    guest: t('systemUser.user.roleGuest'),
    viewer: t('systemUser.user.roleViewer'),
  }
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
    roleLabels[r.role] || r.role,
    statusLabels[r.status] || r.status,
    r.two_factor ? t('systemUser.user.form2FAOn') : '—',
    r.last_login || '—',
  ])
  const tableRows = body.map((cells) => `<tr>${cells.map((c) => `<td>${escapeHtml(String(c))}</td>`).join('')}</tr>`).join('')
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
      const roleId =
        userForm.role_id != null ? Number(userForm.role_id) : undefined
      await systemApi.updateUser(userForm.id, {
        email: userForm.email,
        full_name: userForm.full_name,
        department_id: userForm.department_id ?? undefined,
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
  () => [searchForm.keyword, searchForm.department_id, searchForm.status],
  () => {
    pagination.page = 1
    if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
    keywordDebounceTimer = setTimeout(() => {
      keywordDebounceTimer = null
      fetchUsers()
    }, 300)
  },
  { deep: true }
)

onMounted(() => {
  loadOptions()
  fetchUsers()
})
</script>

<style scoped>
/* Base Layout */
.user-list {
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

.stat-value.active { color: #a5f3fc; }
.stat-value.locked { color: #fcd34d; }

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

/* Glassmorphism Filter Card */
.filter-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(3, 160px) auto;
  gap: 12px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-item label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-item :deep(.el-input),
.filter-item :deep(.el-select) {
  width: 100%;
}

.filter-item :deep(.el-input__wrapper),
.filter-item :deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.btn-add {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.btn-add:hover {
  background: linear-gradient(135deg, #5a6fd6 0%, #6a4393 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-print {
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  border: none;
  color: #fff;
  border-radius: 8px;
  transition: all 0.25s ease;
}

.btn-print:hover {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(71, 85, 105, 0.35);
}

.btn-print .el-icon {
  margin-right: 4px;
}

/* Enhanced Table Card */
.table-card {
  background: white;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.table-card :deep(.el-table) {
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: #f1f5f9;
  border: none;
}

.table-card :deep(.el-table th.el-table__cell) {
  border-bottom: 2px solid #e2e8f0;
  padding: 10px 8px;
}

.table-card :deep(.el-table td.el-table__cell) {
  padding: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.table-card :deep(.el-table--border::after),
.table-card :deep(.el-table--border::before) {
  display: none;
}

.table-card :deep(.el-table__border-left-patch) {
  display: none;
}

/* Row styling */
.table-card :deep(.row-locked) {
  background-color: #fffbeb !important;
}

.table-card :deep(.el-table__row:hover > td) {
  background-color: #f1f5f9 !important;
}

/* Cell Styles */
.id-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  padding: 2px 8px;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-mini {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.username-text {
  font-weight: 500;
  color: #1e293b;
}

.email-text {
  font-size: 13px;
  color: #64748b;
}

.dept-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 4px;
  font-size: 12px;
}

.text-muted {
  color: #cbd5e1;
}

.role-tag {
  font-size: 11px;
  border-radius: 6px;
}

/* Status Indicator with Dot */
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-indicator.active { color: #16a34a; }
.status-indicator.locked { color: #d97706; }
.status-indicator.inactive { color: #64748b; }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-indicator.active .status-dot {
  background: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.2);
}

.status-indicator.locked .status-dot {
  background: #f59e0b;
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
  animation: none;
}

.status-indicator.inactive .status-dot {
  background: #94a3b8;
  animation: none;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* 2FA Indicator */
.tfa-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #f1f5f9;
  color: #94a3b8;
  transition: all 0.2s;
}

.tfa-indicator.enabled {
  background: #dcfce7;
  color: #16a34a;
}

.login-time {
  font-size: 12px;
  color: #64748b;
}

/* Action Buttons */
.action-cell {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.action-cell :deep(.el-button.is-circle) {
  width: 30px;
  height: 30px;
  transition: all 0.2s;
}

.action-cell :deep(.el-button.is-circle:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.btn-disabled {
  opacity: 0.4;
  cursor: not-allowed !important;
}

/* Table Footer */
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.footer-info {
  font-size: 13px;
  color: #64748b;
}

.footer-info strong {
  color: #1e293b;
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

.modern-dialog :deep(.el-form-item__label) {
  font-weight: 500;
  color: #334155;
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
@media (max-width: 1200px) {
  .filter-grid {
    grid-template-columns: repeat(2, 1fr) auto;
  }
  
  .header-stats {
    display: none;
  }
}

@media (max-width: 768px) {
  .user-list {
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
  
  .filter-card {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-grid {
    grid-template-columns: 1fr;
  }
  
  .toolbar-actions {
    justify-content: center;
  }
  
  .table-footer {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
