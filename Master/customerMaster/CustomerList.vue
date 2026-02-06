<!-- 顧客マスタ -->
<template>
  <div class="customer-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <UserFilled />
            </el-icon>
            顧客マスタ管理
          </h1>
          <p class="subtitle">顧客情報の登録・編集・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ customerList.length }}</div>
            <div class="stat-label">総顧客数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeCustomersCount }}</div>
            <div class="stat-label">有効顧客</div>
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
          <el-button type="primary" @click="openForm()" :icon="Plus" class="add-customer-btn">
            顧客追加
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
          <el-input v-model="filters.searchText" placeholder="顧客CD・顧客名・電話番号で検索" clearable @input="handleFilter"
            class="filter-input">
            <template #suffix>
              <el-icon v-if="filters.searchText" class="search-active">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>

        <!-- 顾客类型筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <Management />
            </el-icon>
            顧客種別
          </label>
          <el-select v-model="filters.customerType" placeholder="全ての種別" clearable @change="handleFilter"
            class="filter-input">
            <el-option label="法人" value="corporate">
              <div class="type-option">
                <el-tag type="primary" size="small">法人</el-tag>
                <span class="type-desc">企業・団体</span>
              </div>
            </el-option>
            <el-option label="個人" value="individual">
              <div class="type-option">
                <el-tag type="success" size="small">個人</el-tag>
                <span class="type-desc">個人顧客</span>
              </div>
            </el-option>
            <el-option label="代理店" value="agency">
              <div class="type-option">
                <el-tag type="warning" size="small">代理店</el-tag>
                <span class="type-desc">販売代理店</span>
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
            顧客状態
          </label>
          <el-select v-model="filters.status" placeholder="全ての状態" clearable @change="handleFilter" class="filter-input">
            <el-option label="有効" :value="1">
              <div class="status-option">
                <el-tag type="success" size="small">有効</el-tag>
                <span class="status-desc">取引可能</span>
              </div>
            </el-option>
            <el-option label="無効" :value="0">
              <div class="status-option">
                <el-tag type="info" size="small">無効</el-tag>
                <span class="status-desc">取引停止</span>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 地域筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <Location />
            </el-icon>
            地域
          </label>
          <el-select v-model="filters.region" placeholder="全ての地域" clearable @change="handleFilter" class="filter-input">
            <el-option label="関東" value="関東" />
            <el-option label="関西" value="関西" />
            <el-option label="中部" value="中部" />
            <el-option label="九州" value="九州" />
            <el-option label="東北" value="東北" />
            <el-option label="中国" value="中国" />
            <el-option label="四国" value="四国" />
            <el-option label="北海道" value="北海道" />
            <el-option label="沖縄" value="沖縄" />
          </el-select>
        </div>
      </div>

      <!-- 筛选结果摘要 -->
      <div class="filter-summary" v-if="hasActiveFilters">
        <div class="summary-text">
          <el-icon class="summary-icon">
            <InfoFilled />
          </el-icon>
          <span>{{ filteredCustomers.length }}件 / {{ customerList.length }}件中を表示</span>
        </div>
        <div class="active-filters">
          <el-tag v-if="filters.searchText" closable @close="filters.searchText = ''; handleFilter()" type="primary"
            size="small">
            検索: {{ filters.searchText }}
          </el-tag>
          <el-tag v-if="filters.customerType" closable @close="filters.customerType = ''; handleFilter()" type="warning"
            size="small">
            種別: {{ getCustomerTypeText(filters.customerType) }}
          </el-tag>
          <el-tag v-if="filters.status !== ''" closable @close="filters.status = ''; handleFilter()" type="info"
            size="small">
            状態: {{ filters.status === 1 ? '有効' : '無効' }}
          </el-tag>
          <el-tag v-if="filters.region" closable @close="filters.region = ''; handleFilter()" type="success"
            size="small">
            地域: {{ filters.region }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 顾客卡片视图（移动端） -->
    <div class="mobile-view" v-if="isMobile">
      <div class="customers-grid">
        <div v-for="customer in filteredCustomers" :key="customer.id" class="customer-card" @click="openForm(customer)">
          <div class="customer-avatar">
            <el-icon>
              <UserFilled />
            </el-icon>
          </div>
          <div class="customer-info">
            <h3 class="customer-name">{{ customer.customer_name }}</h3>
            <p class="customer-code">{{ customer.customer_cd }}</p>
            <p class="customer-phone" v-if="customer.phone">
              <el-icon>
                <Phone />
              </el-icon>
              {{ customer.phone }}
            </p>
            <p class="customer-address" v-if="customer.address">
              <el-icon>
                <Location />
              </el-icon>
              {{ customer.address }}
            </p>
            <div class="customer-meta">
              <el-tag :type="getCustomerTypeTagType(customer.customer_type)" size="small">
                {{ getCustomerTypeText(customer.customer_type) }}
              </el-tag>
              <el-tag :type="customer.status ? 'success' : 'info'" size="small">
                {{ customer.status ? '有効' : '無効' }}
              </el-tag>
            </div>
          </div>
          <div class="customer-actions">
            <el-dropdown @command="handleCommand">
              <el-button circle size="small" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="`edit-${customer.id}`" :icon="Edit">編集</el-dropdown-item>
                  <el-dropdown-item :command="`toggle-${customer.id}`" :icon="Switch">状態切替</el-dropdown-item>
                  <el-dropdown-item :command="`delete-${customer.id}`" :icon="Delete" divided>削除</el-dropdown-item>
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
        <el-table :data="filteredCustomers" stripe highlight-current-row v-loading="loading" class="modern-table">
          <el-table-column prop="customer_cd" label="顧客CD" width="120" align="center">
            <template #default="{ row }">
              <div class="customer-code-cell">
                <el-icon class="code-icon">
                  <Tickets />
                </el-icon>
                <span>{{ row.customer_cd }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="customer_name" label="顧客名" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="customer-name-cell">
                <el-icon class="name-icon">
                  <UserFilled />
                </el-icon>
                <span>{{ row.customer_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="電話番号" width="150" show-overflow-tooltip>
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
          <el-table-column prop="address" label="住所" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <div v-if="row.address" class="address-cell">
                <el-icon class="address-icon">
                  <Location />
                </el-icon>
                <span>{{ row.address }}</span>
              </div>
              <span v-else class="no-data">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="customer_type" label="種別" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getCustomerTypeTagType(row.customer_type)" size="small">
                {{ getCustomerTypeText(row.customer_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状態" width="100" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.status" :active-value="1" :inactive-value="0" @change="toggleStatus(row)"
                :loading="row.statusLoading" inline-prompt active-text="有効" inactive-text="無効" />
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="140" align="center">
            <template #default="{ row }">
              <div class="action-buttons-table">
                <el-button size="small" type="primary" link @click="openForm(row)" :icon="Edit">
                  編集
                </el-button>
                <el-button size="small" type="danger" link @click="deleteCustomer(row.id)" :icon="Delete">
                  削除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 结果统计 -->
    <div class="result-section">
      <div class="result-info">
        表示件数: {{ filteredCustomers.length }} / {{ customerList.length }}
      </div>
    </div>

    <!-- 顾客表单弹窗 -->
    <CustomerForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useWindowSize } from '@vueuse/core'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UserFilled,
  Filter,
  Refresh,
  Plus,
  Search,
  Management,
  CircleCheck,
  Location,
  InfoFilled,
  Edit,
  Delete,
  MoreFilled,
  Switch,
  Phone,
  Tickets
} from '@element-plus/icons-vue'
import CustomerForm from './CustomerForm.vue'
import {
  getCustomerList,
  deleteCustomerById,
  updateCustomerStatus
} from '@/api/master/customerMaster'

// 定义Customer类型
interface Customer {
  id: number
  customer_cd: string
  customer_name: string
  phone: string
  address: string
  customer_type: 'corporate' | 'individual' | 'agency'
  status: number
  statusLoading?: boolean
}

// 响应式检测
const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)

// 数据状态
const customerList = ref<Customer[]>([])
const loading = ref(false)
const formVisible = ref(false)
const editData = ref<Customer | null>(null)

// 筛选状态
const filters = ref({
  searchText: '',
  customerType: '',
  status: '' as string | number,
  region: ''
})

// 计算属性
const activeCustomersCount = computed(() =>
  customerList.value.filter(customer => customer.status).length
)

const hasActiveFilters = computed(() => {
  return filters.value.searchText ||
    filters.value.customerType ||
    filters.value.status !== '' ||
    filters.value.region
})

// 筛选后的顾客列表
const filteredCustomers = computed(() => {
  let result = customerList.value

  // 文本搜索
  if (filters.value.searchText) {
    const searchText = filters.value.searchText.toLowerCase()
    result = result.filter(customer =>
      customer.customer_cd?.toLowerCase().includes(searchText) ||
      customer.customer_name?.toLowerCase().includes(searchText) ||
      customer.phone?.toLowerCase().includes(searchText)
    )
  }

  // 顾客类型筛选
  if (filters.value.customerType) {
    result = result.filter(customer => customer.customer_type === filters.value.customerType)
  }

  // 状态筛选
  if (filters.value.status !== '') {
    result = result.filter(customer => customer.status === filters.value.status)
  }

  // 地域筛选
  if (filters.value.region) {
    result = result.filter(customer =>
      customer.address?.includes(filters.value.region)
    )
  }

  return result
})

// 辅助函数
const getCustomerTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    corporate: '法人',
    individual: '個人',
    agency: '代理店'
  }
  return typeMap[type] || type
}

const getCustomerTypeTagType = (type: string) => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    corporate: 'primary',
    individual: 'success',
    agency: 'warning'
  }
  return typeMap[type] || 'info'
}

// 事件处理
const handleFilter = () => {
  // 筛选逻辑已通过computed属性实现
}

const clearFilters = () => {
  filters.value = {
    searchText: '',
    customerType: '',
    status: '',
    region: ''
  }
}

const handleCommand = (command: string) => {
  const [action, customerId] = command.split('-')
  const customer = customerList.value.find(c => c.id === parseInt(customerId))

  if (!customer) return

  if (action === 'edit') {
    openForm(customer)
  } else if (action === 'toggle') {
    toggleStatus(customer)
  } else if (action === 'delete') {
    deleteCustomer(customer.id)
  }
}

// 数据操作
const fetchList = async () => {
  loading.value = true
  try {
    const res = await getCustomerList({ keyword: filters.value.searchText })
    customerList.value = res.data.map((customer: Customer) => ({
      ...customer,
      statusLoading: false
    }))
  } catch {
    ElMessage.error('顧客データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

const openForm = (row: Customer | null = null) => {
  editData.value = row
  formVisible.value = true
}

const deleteCustomer = async (id: number) => {
  try {
    await ElMessageBox.confirm('この顧客を削除しますか？', '確認', {
      type: 'warning',
      confirmButtonText: 'はい',
      cancelButtonText: 'キャンセル'
    })

    await deleteCustomerById(id)
    ElMessage.success('削除しました')
    fetchList()
  } catch {
    // ユーザーがキャンセルした場合は何もしない
  }
}

const toggleStatus = async (row: Customer) => {
  row.statusLoading = true
  try {
    await updateCustomerStatus(row.id, row.status)
    ElMessage.success('状態を更新しました')
  } catch {
    // エラー時は元の状態に戻す
    row.status = row.status === 1 ? 0 : 1
    ElMessage.error('状態の更新に失敗しました')
  } finally {
    row.statusLoading = false
  }
}

// 页面初始化
onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.customer-master-container {
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
  color: #27ae60;
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
  background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
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
  color: #27ae60;
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
  color: #27ae60;
  transform: scale(1.05);
}

.add-customer-btn {
  background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
  transition: all 0.3s ease;
}

.add-customer-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
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
  color: #27ae60;
}

.filter-input {
  transition: all 0.3s ease;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.search-active {
  color: #27ae60;
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
.type-option,
.status-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.type-desc,
.status-desc {
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
  color: #27ae60;
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

.customers-grid {
  display: grid;
  gap: 16px;
}

.customer-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.customer-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.customer-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.customer-info {
  flex: 1;
}

.customer-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 4px;
  color: #2c3e50;
}

.customer-code {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin: 0 0 8px;
  font-family: monospace;
}

.customer-phone,
.customer-address {
  font-size: 0.9rem;
  color: #95a5a6;
  margin: 0 0 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.customer-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.customer-actions {
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

.customer-code-cell,
.customer-name-cell,
.phone-cell,
.address-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code-icon,
.name-icon,
.phone-icon,
.address-icon {
  color: #27ae60;
  font-size: 1rem;
  flex-shrink: 0;
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
  .customer-master-container {
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

  .customer-card {
    padding: 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .customer-actions {
    align-self: flex-end;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .customer-master-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .page-header,
  .action-section,
  .table-card,
  .result-section,
  .customer-card {
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
.customer-card,
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

:deep(.el-switch) {
  --el-switch-on-color: #27ae60;
}
</style>
