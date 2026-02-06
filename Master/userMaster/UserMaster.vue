<!-- ユーザーマスタ -->
<template>
  <div class="user-master-container">
    <!-- 页面头部 -->
    <div class="page-header section-card">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <User />
            </el-icon>
            ユーザーマスタ管理
          </h1>
          <p class="subtitle">システムユーザーの登録・編集・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ users?.length || 0 }}</div>
            <div class="stat-label">総ユーザー数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeUsersCount }}</div>
            <div class="stat-label">有効ユーザー</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区域 -->
    <div class="action-section section-card">
      <!-- 筛选标题 -->
      <div class="filter-header">
        <div class="filter-header-left">
          <div class="filter-title">
            <el-icon class="filter-icon">
              <Filter />
            </el-icon>
            <span>検索・絞り込み</span>
          </div>
          <div class="filter-inline-summary" v-if="hasActiveFilters">
            <span class="summary-count">
              {{ filteredUsers.length }}件 / {{ users?.length || 0 }}件中を表示
            </span>
            <div class="inline-tags">
              <el-tag v-if="filters.searchText" closable @close="
                () => {
                  filters.searchText = ''
                  handleFilter()
                }
              " type="primary" size="small">
                検索: {{ filters.searchText }}
              </el-tag>
              <el-tag v-if="filters.department" closable @close="
                () => {
                  filters.department = ''
                  handleFilter()
                }
              " type="warning" size="small">
                部門: {{ getDeptName(filters.department as number) }}
              </el-tag>
              <el-tag v-if="filters.role" closable @close="
                () => {
                  filters.role = ''
                  handleFilter()
                }
              " type="success" size="small">
                権限: {{ getRoleText(filters.role) }}
              </el-tag>
              <el-tag v-if="filters.status !== ''" closable @close="
                () => {
                  filters.status = ''
                  handleFilter()
                }
              " type="info" size="small">
                状態: {{ filters.status === 1 ? '有効' : '無効' }}
              </el-tag>
            </div>
          </div>
        </div>
        <div class="filter-actions">
          <el-button text size="small" @click="clearFilters" :icon="Refresh" class="clear-btn">
            クリア
          </el-button>
          <el-button type="primary" size="small" @click="handleAdd" :icon="Plus" class="add-user-btn">
            ユーザー追加
          </el-button>
        </div>
      </div>

      <!-- 筛选内容 -->
      <div class="filters-grid">
        <!-- 搜索框 -->
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon>
              <Search />
            </el-icon>
            キーワード検索
          </label>
          <el-input v-model="filters.searchText" placeholder="ユーザー名・ログインIDで検索" clearable @input="handleFilter"
            class="filter-input" size="small">
            <template #suffix>
              <el-icon v-if="filters.searchText" class="search-active">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>

        <!-- 部门筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <OfficeBuilding />
            </el-icon>
            所属部門
          </label>
          <el-select v-model="filters.department" placeholder="全ての部門" clearable @change="handleFilter"
            class="filter-input" size="small">
            <el-option v-for="dept in departments" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </div>

        <!-- 权限筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <Key />
            </el-icon>
            ユーザー権限
          </label>
          <el-select v-model="filters.role" placeholder="全ての権限" clearable @change="handleFilter" class="filter-input"
            size="small">
            <el-option label="管理者" value="admin">
              <div class="role-option">
                <el-tag type="danger" size="small">管理者</el-tag>
                <span class="role-desc">システム管理権限</span>
              </div>
            </el-option>
            <el-option label="マネージャー" value="manager">
              <div class="role-option">
                <el-tag type="warning" size="small">マネージャー</el-tag>
                <span class="role-desc">部門管理権限</span>
              </div>
            </el-option>
            <el-option label="検査" value="inspection">
              <div class="role-option">
                <el-tag type="success" size="small">検査</el-tag>
                <span class="role-desc">検査関連権限</span>
              </div>
            </el-option>
            <el-option label="一般ユーザー" value="staff">
              <div class="role-option">
                <el-tag type="primary" size="small">一般ユーザー</el-tag>
                <span class="role-desc">基本操作権限</span>
              </div>
            </el-option>
            <el-option label="ゲスト" value="guest">
              <div class="role-option">
                <el-tag type="info" size="small">ゲスト</el-tag>
                <span class="role-desc">閲覧のみ</span>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 状态筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <CircleCheck />
            </el-icon>
            アカウント状態
          </label>
          <el-select v-model="filters.status" placeholder="全ての状態" clearable @change="handleFilter" class="filter-input"
            size="small">
            <el-option label="有効" :value="1">
              <div class="status-option">
                <el-tag type="success" size="small">有効</el-tag>
                <span class="status-desc">利用可能</span>
              </div>
            </el-option>
            <el-option label="無効" :value="0">
              <div class="status-option">
                <el-tag type="info" size="small">無効</el-tag>
                <span class="status-desc">利用停止</span>
              </div>
            </el-option>
          </el-select>
        </div>
      </div>

    </div>

    <!-- 用户卡片视图（移动端） -->
    <div class="mobile-view" v-if="isMobile">
      <div class="users-grid">
        <div v-for="user in paginatedUsers" :key="user.id" class="user-card" @click="handleEdit(user)">
          <div class="user-avatar">
            <el-icon>
              <Avatar />
            </el-icon>
          </div>
          <div class="user-info">
            <h3 class="user-name">{{ user.name }}</h3>
            <p class="user-id">{{ user.username }}</p>
            <p class="user-dept">{{ getDeptName(user.department_id) }}</p>
            <div class="user-meta">
              <el-tag :type="getRoleTagType(user.role)" size="small">
                {{ getRoleText(user.role) }}
              </el-tag>
              <el-tag :type="user.status ? 'success' : 'info'" size="small">
                {{ user.status ? '有効' : '無効' }}
              </el-tag>
            </div>
          </div>
          <div class="user-actions">
            <el-dropdown @command="handleCommand">
              <el-button circle size="small" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="`edit-${user.id}`" :icon="Edit">編集</el-dropdown-item>
                  <el-dropdown-item :command="`delete-${user.id}`" :icon="Delete" divided>削除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 表格视图（桌面端） -->
    <div class="desktop-view" v-else>
      <el-card class="table-card section-card">
        <el-table :data="paginatedUsers" size="small" stripe highlight-current-row v-loading="loading"
          class="modern-table">
          <el-table-column prop="username" label="ログインID" min-width="120">
            <template #default="{ row }">
              <div class="username-cell">
                <el-icon class="user-icon">
                  <User />
                </el-icon>
                <span>{{ row.username }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="氏名" min-width="120" show-overflow-tooltip />
          <el-table-column prop="department_id" label="所属部門" min-width="120">
            <template #default="{ row }">
              <el-tag type="info" effect="plain" size="small">
                {{ getDeptName(row.department_id) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="role" label="権限" min-width="100">
            <template #default="{ row }">
              <el-tag :type="getRoleTagType(row.role)" size="small">
                {{ getRoleText(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="email" label="メール" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <div v-if="row.email" class="email-cell">
                <el-icon class="email-icon">
                  <Message />
                </el-icon>
                <span>{{ row.email }}</span>
              </div>
              <span v-else class="no-data">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="電話番号" min-width="130" show-overflow-tooltip>
            <template #default="{ row }">
              <div v-if="row.phone" class="phone-cell">
                <el-icon class="phone-icon">
                  <Phone />
                </el-icon>
                <span>{{ row.phone }}</span>
              </div>
              <span v-else class="no-data">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状態" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status ? 'success' : 'info'" effect="dark" size="small">
                {{ row.status ? '有効' : '無効' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="120" align="center">
            <template #default="{ row }">
              <div class="action-buttons-table">
                <el-button size="small" type="primary" link @click="handleEdit(row)" :icon="Edit">
                  編集
                </el-button>
                <el-popconfirm title="本当に削除しますか？" @confirm="handleDelete(row.id)" width="200">
                  <template #reference>
                    <el-button size="small" type="danger" link :icon="Delete"> 削除 </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 分页和统计信息 -->
    <div class="pagination-section section-card">
      <div class="result-info">
        表示件数: {{ paginatedUsers.length }} / {{ filteredUsers.length }}
        <span v-if="filteredUsers.length !== (users?.length || 0)">
          (総件数: {{ users?.length || 0 }})
        </span>
      </div>
      <el-pagination layout="prev, pager, next, sizes, jumper" :total="filteredUsers.length" :page-size="pageSize"
        :page-sizes="[5, 10, 20, 50]" :current-page="currentPage" small @current-change="handlePageChange"
        @size-change="handleSizeChange" class="modern-pagination" />
    </div>

    <!-- 用户编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" destroy-on-close class="user-dialog"
      :close-on-click-modal="false">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" label-position="right" size="small"
        class="user-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="ログインID" prop="username">
              <el-input v-model="form.username" size="small" placeholder="ログインIDを入力" :prefix-icon="User" />
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="!form.id">
            <el-form-item label="パスワード" prop="password">
              <el-input v-model="form.password" size="small" type="password" placeholder="パスワードを入力" show-password
                :prefix-icon="Lock" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="氏名" prop="name">
              <el-input v-model="form.name" size="small" placeholder="氏名を入力" :prefix-icon="User" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属部門" prop="department_id">
              <el-select v-model="form.department_id" size="small" placeholder="部門を選択" style="width: 100%"
                :prefix-icon="OfficeBuilding">
                <el-option v-for="dept in departments" :key="dept.id" :label="dept.name" :value="dept.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="権限" prop="role">
              <el-select v-model="form.role" size="small" placeholder="権限を選択" style="width: 100%">
                <el-option label="管理者" value="admin" />
                <el-option label="マネージャー" value="manager" />
                <el-option label="検査" value="inspection" />
                <el-option label="一般ユーザー" value="staff" />
                <el-option label="ゲスト" value="guest" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状態">
              <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="有効"
                inactive-text="無効" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="メール" prop="email">
              <el-input v-model="form.email" size="small" placeholder="メールアドレスを入力" :prefix-icon="Message" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="電話番号" prop="phone">
              <el-input v-model="form.phone" size="small" placeholder="電話番号を入力" :prefix-icon="Phone" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button size="small" @click="dialogVisible = false" :icon="Close"> キャンセル </el-button>
          <el-button type="primary" size="small" @click="submitForm" :loading="submitting" :icon="Check">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * ユーザーマスタ
 * 功能：
 * - 用户列表显示（表格视图+卡片视图）
 * - 筛选功能（姓名、部门、权限、状态）
 * - 新增用户
 * - 编辑用户
 * - 删除用户
 * - 响应式设计
 * - 分页显示
 */
import { ref, computed, onMounted, nextTick } from 'vue'
import { useWindowSize } from '@vueuse/core'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import {
  User,
  Search,
  Plus,
  Edit,
  Delete,
  Refresh,
  Avatar,
  MoreFilled,
  Message,
  Phone,
  OfficeBuilding,
  Lock,
  Close,
  Check,
  Filter,
  Key,
  CircleCheck,
  InfoFilled,
} from '@element-plus/icons-vue'
import {
  fetchUsers,
  createUser,
  updateUser,
  deleteUser,
  fetchDepartments,
} from '@/api/master/userMaster'
import type { User as UserType } from '@/types/master'

// 响应式检测
const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)

// 数据状态
const users = ref<UserType[]>([])
const departments = ref<{ id: number; name: string }[]>([])
const loading = ref(false)
const submitting = ref(false)

// 弹窗状态
const dialogVisible = ref(false)
const form = ref<Partial<UserType>>({ status: 1 })
const formRef = ref<FormInstance>()

// 分页状态
const pageSize = ref(10)
const currentPage = ref(1)

// 筛选状态
const filters = ref({
  searchText: '',
  department: '' as string | number,
  role: '',
  status: '' as string | number,
})

// 计算属性
const activeUsersCount = computed(() => users.value?.filter((user) => user.status).length || 0)

const dialogTitle = computed(() => (form.value.id ? 'ユーザー編集' : 'ユーザー追加'))

const hasActiveFilters = computed(() => {
  return (
    filters.value.searchText ||
    filters.value.department ||
    filters.value.role ||
    filters.value.status !== ''
  )
})

// 筛选后的用户列表
const filteredUsers = computed(() => {
  let result = users.value || []

  // 文本搜索
  if (filters.value.searchText) {
    const searchText = filters.value.searchText.toLowerCase()
    result = result.filter(
      (user) =>
        user.name?.toLowerCase().includes(searchText) ||
        user.username?.toLowerCase().includes(searchText),
    )
  }

  // 部门筛选
  if (filters.value.department) {
    result = result.filter((user) => user.department_id === filters.value.department)
  }

  // 权限筛选
  if (filters.value.role) {
    result = result.filter((user) => user.role === filters.value.role)
  }

  // 状态筛选
  if (filters.value.status !== '') {
    result = result.filter((user) => user.status === filters.value.status)
  }

  return result
})

// 分页后的用户列表
const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredUsers.value.slice(start, start + pageSize.value)
})

// 表单验证规则
const rules: FormRules = {
  username: [{ required: true, message: 'ログインIDは必須です', trigger: 'blur' }],
  password: [{ required: true, message: 'パスワードは必須です', trigger: 'blur' }],
  name: [{ required: true, message: '氏名は必須です', trigger: 'blur' }],
  department_id: [{ required: true, message: '部門を選択してください', trigger: 'change' }],
  role: [{ required: true, message: '権限を選択してください', trigger: 'change' }],
}

// 辅助函数
const getDeptName = (id: number) => departments.value.find((d) => d.id === id)?.name || '—'

const getRoleText = (role: string) => {
  const roleMap: Record<string, string> = {
    admin: '管理者',
    manager: 'マネージャー',
    inspection: '検査',
    staff: '一般ユーザー',
    guest: 'ゲスト',
  }
  return roleMap[role] || role
}

const getRoleTagType = (role: string) => {
  const typeMap: Record<string, 'danger' | 'warning' | 'primary' | 'info' | 'success'> = {
    admin: 'danger',
    manager: 'warning',
    inspection: 'success',
    staff: 'primary',
    guest: 'info',
  }
  return typeMap[role] || 'info'
}

// 事件处理
const handleFilter = () => {
  currentPage.value = 1
}

const clearFilters = () => {
  filters.value = {
    searchText: '',
    department: '',
    role: '',
    status: '',
  }
  currentPage.value = 1
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCommand = (command: string) => {
  const [action, userId] = command.split('-')
  const user = users.value.find((u) => u.id === parseInt(userId))

  if (!user) return

  if (action === 'edit') {
    handleEdit(user)
  } else if (action === 'delete') {
    handleDelete(user.id as number)
  }
}

// 数据操作
const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchUsers()
    console.log('API Response:', res)

    // The request interceptor should extract the data, but handle both cases
    users.value = Array.isArray(res) ? res : (res as any).data || []

    console.log('Current users.value:', users.value)
    console.log('Users length:', users.value?.length)
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

const loadDepartments = async () => {
  try {
    const res = await fetchDepartments()
    departments.value = res.data.data
  } catch (error) {
    console.error('Failed to load departments:', error)
  }
}

const handleAdd = () => {
  form.value = {
    id: undefined,
    username: '',
    password: '',
    name: '',
    department_id: undefined,
    role: '',
    email: '',
    phone: '',
    status: 1,
  }
  dialogVisible.value = true
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

const handleEdit = (row: UserType) => {
  form.value = { ...row, password: '' }
  dialogVisible.value = true
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

const handleDelete = async (id: number) => {
  try {
    await deleteUser(id)
    ElMessage.success('削除成功')
    loadData()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (form.value.id) {
      await updateUser(form.value.id, form.value as UserType)
      ElMessage.success('更新成功')
    } else {
      await createUser(form.value as UserType)
      ElMessage.success('登録成功')
    }

    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('Submit failed:', error)
  } finally {
    submitting.value = false
  }
}

// 页面初始化
onMounted(() => {
  loadData()
  loadDepartments()
})
</script>

<style scoped>
.user-master-container {
  padding: 10px;
  background: #eef2f7;
  min-height: 100vh;
}

.section-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

/* 页面头部 */
.page-header {
  padding: 10px 28px;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #ffffff 0%, #f5f7fb 100%);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 1.7rem;
  font-weight: 700;
  margin: 0 0 6px;
  color: #1f2a37;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 1.8rem;
  color: #3498db;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 0.95rem;
}

.header-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stat-card {
  background: linear-gradient(135deg, #5c6ac4 0%, #826af9 100%);
  color: white;
  padding: 10px 18px;
  border-radius: 12px;
  text-align: center;
  min-width: 110px;
  box-shadow: 0 6px 20px rgba(92, 106, 196, 0.35);
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.85rem;
  opacity: 0.9;
  margin-top: 4px;
}

/* 操作区域 */
.action-section {
  padding: 0;
  margin-bottom: 10px;
  overflow: hidden;
}

/* 筛选标题区 */
.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
  border-bottom: 1px solid #e2e8f0;
  gap: 16px;
}

.filter-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  flex-wrap: wrap;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2933;
}

.filter-icon {
  font-size: 1.3rem;
  color: #667eea;
}

.filter-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.filter-inline-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.85rem;
  color: #4a5568;
  flex-wrap: wrap;
}

.summary-count {
  font-weight: 600;
  color: #334155;
}

.inline-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.inline-tags .el-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: 1.8;
}

.inline-tags .el-tag:hover {
  transform: scale(1.03);
}

.clear-btn {
  color: #718096;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  color: #667eea;
  transform: scale(1.05);
}

.add-user-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.add-user-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

/* 筛选网格 */
.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 12px 24px;
  background: white;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.search-item {
  grid-column: span 1;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #475467;
  margin-bottom: 2px;
}

.filter-label .el-icon {
  font-size: 1rem;
  color: #667eea;
}

.filter-input {
  transition: all 0.3s ease;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.search-active {
  color: #667eea;
  animation: pulse 2s infinite;
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

/* 选项样式 */
.role-option,
.status-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.role-desc,
.status-desc {
  font-size: 0.8rem;
  color: #718096;
  margin-left: 8px;
}

/* 移动端卡片视图 */
.mobile-view {
  margin-bottom: 16px;
}

.users-grid {
  display: grid;
  gap: 16px;
}

.user-card {
  background: white;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.user-avatar {
  width: 54px;
  height: 54px;
  border-radius: 14px;
  background: linear-gradient(135deg, #5c6ac4 0%, #7f56d9 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.3rem;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 2px;
  color: #1f2933;
}

.user-id {
  font-size: 0.85rem;
  color: #6b7280;
  margin: 0 0 2px;
}

.user-dept {
  font-size: 0.85rem;
  color: #9ca3af;
  margin: 0 0 6px;
}

.user-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.user-actions {
  flex-shrink: 0;
}

/* 桌面端表格视图 */
.desktop-view {
  margin-bottom: 16px;
}

.table-card {
  border-radius: 14px;
  box-shadow: none;
  border: none;
  padding: 12px;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
  background: white;
}

.username-cell,
.email-cell,
.phone-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-icon,
.email-icon,
.phone-icon {
  color: #667eea;
  font-size: 1rem;
}

.no-data {
  color: #bdc3c7;
  font-style: italic;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 分页区域 */
.pagination-section {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-info {
  color: #4b5563;
  font-size: 0.85rem;
}

.modern-pagination {
  flex-shrink: 0;
}

/* 弹窗样式 */
.user-dialog {
  border-radius: 20px;
}

.user-form {
  padding: 20px 0;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .header-stats {
    width: 100%;
    justify-content: space-between;
  }

  .filters-grid {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
  }

  .search-item {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .user-master-container {
    padding: 12px;
  }

  .page-header {
    padding: 20px;
  }

  .main-title {
    font-size: 1.4rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 16px 20px;
  }

  .filter-actions {
    justify-content: stretch;
  }

  .filter-actions>* {
    flex: 1;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 18px 16px;
  }

  .search-item {
    grid-column: span 1;
  }

  .pagination-section {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .modern-pagination {
    align-self: center;
  }

  .stat-card {
    min-width: auto;
    flex: 1;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.25rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .user-card {
    padding: 14px;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .user-actions {
    align-self: flex-end;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .user-master-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .section-card,
  .user-card {
    background: rgba(45, 55, 72, 0.8);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .main-title {
    color: #e2e8f0;
  }

  .subtitle,
  .result-info {
    color: #a0aec0;
  }
}

/* 动画效果 */
.user-card,
.table-card,
.page-header,
.action-section,
.pagination-section {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-table th) {
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

:deep(.el-pagination) {
  color: #4a5568;
}

:deep(.el-tag) {
  border-radius: 12px;
  font-weight: 500;
}
</style>
