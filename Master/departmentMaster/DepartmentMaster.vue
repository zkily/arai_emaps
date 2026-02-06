<!-- 部門マスタ -->
<template>
  <div class="department-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <OfficeBuilding />
            </el-icon>
            部門マスタ管理
          </h1>
          <p class="subtitle">組織部門の構造管理・設定を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ departments.length }}</div>
            <div class="stat-label">総部門数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeDepartmentsCount }}</div>
            <div class="stat-label">有効部門</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区域 -->
    <div class="action-section">
      <!-- 筛选标题 -->
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">
            クリア
          </el-button>
          <el-button type="primary" @click="handleAdd" :icon="Plus" class="add-dept-btn">
            部門追加
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
            部門名検索
          </label>
          <el-input v-model="filters.searchText" placeholder="部門名で検索" clearable @input="handleFilter"
            class="filter-input">
            <template #suffix>
              <el-icon v-if="filters.searchText" class="search-active">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>

        <!-- 上位部门筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <Rank />
            </el-icon>
            上位部門
          </label>
          <el-select v-model="filters.parentDepartment" placeholder="全ての上位部門" clearable @change="handleFilter"
            class="filter-input">
            <el-option v-for="dept in parentDepartments" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </div>

        <!-- 状态筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <CircleCheck />
            </el-icon>
            部門状態
          </label>
          <el-select v-model="filters.status" placeholder="全ての状態" clearable @change="handleFilter" class="filter-input">
            <el-option label="有効" :value="1">
              <div class="status-option">
                <el-tag type="success" size="small">有効</el-tag>
                <span class="status-desc">運用中</span>
              </div>
            </el-option>
            <el-option label="無効" :value="0">
              <div class="status-option">
                <el-tag type="info" size="small">無効</el-tag>
                <span class="status-desc">停止中</span>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 层级筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <Operation />
            </el-icon>
            部門レベル
          </label>
          <el-select v-model="filters.level" placeholder="全てのレベル" clearable @change="handleFilter" class="filter-input">
            <el-option label="トップレベル" value="top">
              <div class="level-option">
                <el-tag type="danger" size="small">トップ</el-tag>
                <span class="level-desc">最上位部門</span>
              </div>
            </el-option>
            <el-option label="サブレベル" value="sub">
              <div class="level-option">
                <el-tag type="warning" size="small">サブ</el-tag>
                <span class="level-desc">下位部門</span>
              </div>
            </el-option>
          </el-select>
        </div>
      </div>

      <!-- 筛选结果摘要 -->
      <div class="filter-summary" v-if="hasActiveFilters">
        <div class="summary-text">
          <el-icon class="summary-icon">
            <InfoFilled />
          </el-icon>
          <span>{{ filteredDepartments.length }}件 / {{ departments.length }}件中を表示</span>
        </div>
        <div class="active-filters">
          <el-tag v-if="filters.searchText" closable @close="filters.searchText = ''; handleFilter()" type="primary"
            size="small">
            検索: {{ filters.searchText }}
          </el-tag>
          <el-tag v-if="filters.parentDepartment" closable @close="filters.parentDepartment = ''; handleFilter()"
            type="warning" size="small">
            上位: {{ getParentDeptName(filters.parentDepartment as number) }}
          </el-tag>
          <el-tag v-if="filters.status !== ''" closable @close="filters.status = ''; handleFilter()" type="info"
            size="small">
            状態: {{ filters.status === 1 ? '有効' : '無効' }}
          </el-tag>
          <el-tag v-if="filters.level" closable @close="filters.level = ''; handleFilter()" type="success" size="small">
            レベル: {{ filters.level === 'top' ? 'トップレベル' : 'サブレベル' }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 部门卡片视图（移动端） -->
    <div class="mobile-view" v-if="isMobile">
      <div class="departments-grid">
        <div v-for="dept in filteredDepartments" :key="dept.id" class="dept-card" @click="handleEdit(dept)">
          <div class="dept-icon">
            <el-icon>
              <OfficeBuilding />
            </el-icon>
          </div>
          <div class="dept-info">
            <h3 class="dept-name">{{ dept.name }}</h3>
            <p class="dept-parent" v-if="dept.parent_name">
              上位: {{ dept.parent_name }}
            </p>
            <p class="dept-parent no-parent" v-else>
              トップレベル部門
            </p>
            <div class="dept-meta">
              <el-tag :type="dept.status ? 'success' : 'info'" size="small">
                {{ dept.status ? '有効' : '無効' }}
              </el-tag>
              <el-tag :type="!dept.parent_name ? 'danger' : 'warning'" size="small">
                {{ !dept.parent_name ? 'トップ' : 'サブ' }}
              </el-tag>
            </div>
          </div>
          <div class="dept-actions">
            <el-dropdown @command="handleCommand">
              <el-button circle size="small" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="`edit-${dept.id}`" :icon="Edit">編集</el-dropdown-item>
                  <el-dropdown-item :command="`delete-${dept.id}`" :icon="Delete" divided>削除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 表格视图（桌面端） -->
    <div class="desktop-view" v-else>
      <el-card class="table-card">
        <el-table :data="filteredDepartments" stripe highlight-current-row v-loading="loading" class="modern-table"
          :tree-props="{ children: 'children', hasChildren: 'hasChildren' }" row-key="id">
          <el-table-column prop="name" label="部門名" min-width="200">
            <template #default="{ row }">
              <div class="dept-name-cell">
                <el-icon class="dept-icon-small">
                  <OfficeBuilding />
                </el-icon>
                <span class="dept-name-text">{{ row.name }}</span>
                <el-tag v-if="!row.parent_name" type="danger" size="small" class="level-tag">
                  トップ
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="parent_name" label="上位部門" min-width="150">
            <template #default="{ row }">
              <div v-if="row.parent_name" class="parent-cell">
                <el-icon class="parent-icon">
                  <Rank />
                </el-icon>
                <span>{{ row.parent_name }}</span>
              </div>
              <span v-else class="no-parent">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状態" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status ? 'success' : 'info'" effect="dark" size="small">
                {{ row.status ? '有効' : '無効' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="140" align="center">
            <template #default="{ row }">
              <div class="action-buttons-table">
                <el-button size="small" type="primary" link @click="handleEdit(row)" :icon="Edit">
                  編集
                </el-button>
                <el-popconfirm title="削除しますか？" @confirm="handleDelete(row.id!)" width="200">
                  <template #reference>
                    <el-button size="small" type="danger" link :icon="Delete">
                      削除
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 结果统计 -->
    <div class="result-section">
      <div class="result-info">
        表示件数: {{ filteredDepartments.length }} / {{ departments.length }}
      </div>
    </div>

    <!-- 部门编辑弹窗 -->
    <el-dialog v-model="dialogVisible" width="600px" destroy-on-close class="dept-dialog" :close-on-click-modal="false">
      <div class="dialog-title">
        <el-icon class="dialog-icon">
          <OfficeBuilding />
        </el-icon>
        <span>{{ dialogTitle }}</span>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px" label-position="right" class="dept-form">
        <div class="form-grid">
          <div class="form-section">
            <h4 class="section-title">基本情報</h4>
            <el-form-item label="部門名" prop="name">
              <el-input v-model="form.name" placeholder="部門名を入力" :prefix-icon="OfficeBuilding" />
            </el-form-item>
          </div>
          <div class="form-section">
            <h4 class="section-title">上位・状態</h4>
            <el-form-item label="上位部門" prop="parent_id">
              <el-select v-model="form.parent_id" clearable placeholder="選択なし（トップレベル部門）" style="width: 100%"
                :prefix-icon="Rank">
                <el-option v-for="dept in allDepartments" :key="dept.id" :label="dept.name" :value="dept.id ?? -1"
                  :disabled="!!form.id && dept.id === form.id">
                  <div class="parent-option">
                    <el-icon>
                      <OfficeBuilding />
                    </el-icon>
                    <span>{{ dept.name }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="状態">
              <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="有効" inactive-text="無効"
                style="width: 100%" />
            </el-form-item>
          </div>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" :icon="Close">キャンセル</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting" :icon="Check">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, computed } from 'vue'
import { useWindowSize } from '@vueuse/core'
import type { FormInstance } from 'element-plus'
import { ElMessage } from 'element-plus'
import {
  OfficeBuilding,
  Filter,
  Refresh,
  Plus,
  Search,
  Rank,
  CircleCheck,
  Operation,
  InfoFilled,
  Edit,
  Delete,
  MoreFilled,
  Close,
  Check
} from '@element-plus/icons-vue'
import {
  fetchAllDepartments,
  fetchDepartmentList,
  createDepartment,
  updateDepartment,
  deleteDepartment,
} from '@/api/master/departmentMaster'
import { Department } from '@/types/master'

// 定义组件名称
defineOptions({
  name: 'DepartmentMasterView'
})

// 扩展部门类型，添加parent_name属性
interface ExtendedDepartment extends Department {
  parent_name?: string;
}

// 响应式检测
const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)

// 数据状态
const departments = ref<ExtendedDepartment[]>([])
const allDepartments = ref<ExtendedDepartment[]>([])
const loading = ref(false)
const submitting = ref(false)

// 弹窗状态
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)

// 筛选状态
const filters = ref({
  searchText: '',
  parentDepartment: '' as string | number,
  status: '' as string | number,
  level: ''
})

// 定义表单专用类型
interface DepartmentForm {
  id?: number
  name: string
  parent_id: number | undefined
  status: number
}

const form = reactive<DepartmentForm>({
  name: '',
  parent_id: 0,
  status: 1
})

const rules = {
  name: [{ required: true, message: '部門名は必須です', trigger: 'blur' }]
}

// 计算属性
const activeDepartmentsCount = computed(() =>
  departments.value.filter(dept => dept.status).length
)

const dialogTitle = computed(() => form.id ? '部門編集' : '部門追加')

const parentDepartments = computed(() =>
  allDepartments.value.filter(dept => !dept.parent_id)
)

const hasActiveFilters = computed(() => {
  return filters.value.searchText ||
    filters.value.parentDepartment ||
    filters.value.status !== '' ||
    filters.value.level
})

// 筛选后的部门列表
const filteredDepartments = computed(() => {
  let result = departments.value

  // 文本搜索
  if (filters.value.searchText) {
    const searchText = filters.value.searchText.toLowerCase()
    result = result.filter(dept =>
      dept.name?.toLowerCase().includes(searchText)
    )
  }

  // 上位部门筛选
  if (filters.value.parentDepartment) {
    result = result.filter(dept => {
      const parentName = getParentDeptName(filters.value.parentDepartment as number)
      return dept.parent_name === parentName
    })
  }

  // 状态筛选
  if (filters.value.status !== '') {
    result = result.filter(dept => dept.status === filters.value.status)
  }

  // 层级筛选
  if (filters.value.level) {
    if (filters.value.level === 'top') {
      result = result.filter(dept => !dept.parent_name)
    } else if (filters.value.level === 'sub') {
      result = result.filter(dept => dept.parent_name)
    }
  }

  return result
})

// 辅助函数
const getParentDeptName = (id: number) =>
  allDepartments.value.find(d => d.id === id)?.name || '—'

// 事件处理
const handleFilter = () => {
  // 筛选逻辑已通过computed属性实现
}

const clearFilters = () => {
  filters.value = {
    searchText: '',
    parentDepartment: '',
    status: '',
    level: ''
  }
}

const handleCommand = (command: string) => {
  const [action, deptId] = command.split('-')
  const dept = departments.value.find(d => d.id === parseInt(deptId))

  if (!dept) return

  if (action === 'edit') {
    handleEdit(dept)
  } else if (action === 'delete') {
    handleDelete(dept.id as number)
  }
}

// 数据操作
const loadDepartments = async () => {
  loading.value = true
  try {
    const res = await fetchDepartmentList()
    const depts = res.data.data as ExtendedDepartment[]

    // 处理数据，设置parent_name属性
    depts.forEach(dept => {
      if (dept.parent_id) {
        // 查找父部门并设置parent_name
        const parentDept = depts.find(d => d.id === dept.parent_id)
        dept.parent_name = parentDept?.name || '—'
      }
    })

    departments.value = depts
  } catch {
    ElMessage.error('部門データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

const loadAllDepartments = async () => {
  try {
    const res = await fetchAllDepartments()
    const depts = res.data.data as ExtendedDepartment[]

    // 处理数据，设置parent_name属性
    depts.forEach(dept => {
      if (dept.parent_id) {
        // 查找父部门并设置parent_name
        const parentDept = depts.find(d => d.id === dept.parent_id)
        dept.parent_name = parentDept?.name || '—'
      }
    })

    allDepartments.value = depts
  } catch {
    ElMessage.error('部門リストの読み込みに失敗しました')
  }
}

const handleAdd = () => {
  Object.assign(form, {
    id: undefined,
    name: '',
    parent_id: null,
    status: 1
  })
  dialogVisible.value = true
}

const handleEdit = (row: ExtendedDepartment) => {
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleDelete = async (id: number) => {
  try {
    await deleteDepartment(id)
    ElMessage.success('削除成功')
    loadDepartments()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (form.id) {
      await updateDepartment(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await createDepartment(form)
      ElMessage.success('登録成功')
    }

    dialogVisible.value = false
    loadDepartments()
    loadAllDepartments()
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadDepartments()
  loadAllDepartments()
})
</script>

<style scoped>
.department-master-container {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  background: white;
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 8px;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 1.8rem;
  color: #e67e22;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
  font-size: 1rem;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(230, 126, 34, 0.3);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 4px;
}

/* 操作区域 */
.action-section {
  background: white;
  border-radius: 20px;
  padding: 0;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

/* 筛选标题区 */
.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
}

.filter-icon {
  font-size: 1.3rem;
  color: #e67e22;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.clear-btn {
  color: #718096;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  color: #e67e22;
  transform: scale(1.05);
}

.add-dept-btn {
  background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(230, 126, 34, 0.3);
  transition: all 0.3s ease;
}

.add-dept-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(230, 126, 34, 0.4);
}

/* 筛选网格 */
.filters-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 24px;
  padding: 32px;
  background: white;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-item {
  grid-column: span 1;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 4px;
}

.filter-label .el-icon {
  font-size: 1rem;
  color: #e67e22;
}

.filter-input {
  transition: all 0.3s ease;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.search-active {
  color: #e67e22;
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
.status-option,
.level-option,
.parent-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.status-desc,
.level-desc {
  font-size: 0.8rem;
  color: #718096;
  margin-left: 8px;
}

/* 筛选摘要 */
.filter-summary {
  padding: 20px 32px;
  background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
  border-top: 1px solid #e2e8f0;
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: #4a5568;
  font-weight: 500;
}

.summary-icon {
  color: #e67e22;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.active-filters .el-tag {
  cursor: pointer;
  transition: all 0.3s ease;
}

.active-filters .el-tag:hover {
  transform: scale(1.05);
}

/* 移动端卡片视图 */
.mobile-view {
  margin-bottom: 24px;
}

.departments-grid {
  display: grid;
  gap: 16px;
}

.dept-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 16px;
}

.dept-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.dept-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.dept-info {
  flex: 1;
}

.dept-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 4px;
  color: #2c3e50;
}

.dept-parent {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin: 0 0 8px;
}

.no-parent {
  color: #e67e22;
  font-weight: 500;
}

.dept-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.dept-actions {
  flex-shrink: 0;
}

/* 桌面端表格视图 */
.desktop-view {
  margin-bottom: 24px;
}

.table-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

.dept-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dept-icon-small {
  color: #e67e22;
  font-size: 1rem;
}

.dept-name-text {
  flex: 1;
}

.level-tag {
  margin-left: 8px;
}

.parent-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.parent-icon {
  color: #e67e22;
  font-size: 1rem;
}

.no-parent {
  color: #bdc3c7;
  font-style: italic;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 结果区域 */
.result-section {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.result-info {
  color: #7f8c8d;
  font-size: 0.9rem;
}

/* 弹窗样式 */
.dept-dialog :deep(.el-dialog__body) {
  padding-top: 0;
}

.dialog-title {
  font-size: 22px;
  font-weight: bold;
  color: #2c3e50;
  padding: 20px 24px 12px;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(to right, #ffe6c7, #fff7e6);
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-icon {
  font-size: 24px;
  color: #e67e22;
}

.form-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.form-section {
  flex: 1 1 220px;
  min-width: 220px;
  background: #fafafa;
  border-radius: 12px;
  padding: 18px 16px 10px 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #e67e22;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #eaeaea;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 10px;
}

@media (max-width: 768px) {
  .form-grid {
    flex-direction: column;
    gap: 10px;
  }

  .form-section {
    min-width: 0;
    padding: 12px 8px 8px 8px;
  }

  .dialog-title {
    font-size: 18px;
    padding: 14px 10px 8px 10px;
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: space-around;
  }

  .filters-grid {
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  .search-item {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .department-master-container {
    padding: 16px;
  }

  .page-header {
    padding: 24px 20px;
  }

  .main-title {
    font-size: 1.6rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 20px 24px;
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
    padding: 24px 20px;
  }

  .search-item {
    grid-column: span 1;
  }

  .filter-summary {
    padding: 16px 20px;
  }

  .stat-card {
    min-width: auto;
    flex: 1;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.4rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .dept-card {
    padding: 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .dept-actions {
    align-self: flex-end;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .department-master-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .page-header,
  .action-section,
  .table-card,
  .result-section,
  .dept-card {
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
.dept-card,
.table-card,
.page-header,
.action-section,
.result-section {
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

:deep(.el-tag) {
  border-radius: 12px;
  font-weight: 500;
}
</style>
