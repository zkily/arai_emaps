<!-- DestinationList.vue -->
<template>
  <div class="destination-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Van />
            </el-icon>
            納入先マスタ管理
          </h1>
          <p class="subtitle">納入先情報の登録・編集・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ destinationList.length }}</div>
            <div class="stat-label">総納入先数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeCount }}</div>
            <div class="stat-label">有効納入先</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区 -->
    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">クリア</el-button>
          <el-button type="primary" @click="openForm()" :icon="Plus" class="add-btn">納入先追加</el-button>
        </div>
      </div>

      <!-- 筛选区 -->
      <div class="filters-grid">
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon>
              <Search />
            </el-icon>
            キーワード検索
          </label>
          <el-input v-model="filters.keyword" placeholder="納入先CD・納入先名・顧客CD 検索" clearable @input="handleFilter"
            class="filter-input">
            <template #suffix>
              <el-icon v-if="filters.keyword" class="search-active">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <label class="filter-label"><el-icon>
              <CircleCheck />
            </el-icon>状態</label>
          <el-select v-model="filters.status" placeholder="全て" clearable @change="handleFilter" class="filter-input">
            <el-option label="有効" :value="1">
              <el-tag type="success" size="small">有効</el-tag>
              <span class="status-desc">利用可能</span>
            </el-option>
            <el-option label="無効" :value="0">
              <el-tag type="info" size="small">無効</el-tag>
              <span class="status-desc">利用停止</span>
            </el-option>
          </el-select>
        </div>
        <div class="filter-item">
          <label class="filter-label"><el-icon>
              <Tickets />
            </el-icon>発行区分</label>
          <el-select v-model="filters.issue_type" placeholder="全て" clearable @change="handleFilter"
            class="filter-input">
            <el-option label="1" value="1" />
            <el-option label="2" value="2" />
            <el-option label="3" value="3" />
            <el-option label="4" value="4" />
          </el-select>
        </div>
        <div class="filter-item">
          <label class="filter-label"><el-icon>
              <Box />
            </el-icon>運送会社CD</label>
          <el-input v-model="filters.carrier_cd" placeholder="運送会社CD" clearable @input="handleFilter"
            class="filter-input" />
        </div>
      </div>

      <!-- 筛选结果摘要 -->
      <div class="filter-summary" v-if="hasActiveFilters">
        <div class="summary-text">
          <el-icon class="summary-icon">
            <InfoFilled />
          </el-icon>
          <span>{{ filteredList.length }}件 / {{ destinationList.length }}件中を表示</span>
        </div>
        <div class="active-filters">
          <el-tag v-if="filters.keyword" closable @close="filters.keyword = ''; handleFilter()" type="primary"
            size="small">検索:
            {{ filters.keyword }}</el-tag>
          <el-tag v-if="filters.status !== ''" closable @close="filters.status = ''; handleFilter()" type="info"
            size="small">状態:
            {{ filters.status == 1 ? '有効' : '無効' }}</el-tag>
          <el-tag v-if="filters.issue_type" closable @close="filters.issue_type = ''; handleFilter()" type="warning"
            size="small">発行区分: {{ filters.issue_type }}</el-tag>
          <el-tag v-if="filters.carrier_cd" closable @close="filters.carrier_cd = ''; handleFilter()" type="success"
            size="small">運送会社: {{ filters.carrier_cd }}</el-tag>
        </div>
      </div>
    </div>

    <!-- 主表格卡片 -->
    <el-card class="table-card">
      <el-table :data="filteredList" stripe highlight-current-row v-loading="loading" class="modern-table">
        <el-table-column prop="destination_cd" label="納入先CD" width="110" align="center" />
        <el-table-column prop="destination_name" label="納入先名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="customer_cd" label="顧客CD" width="80" align="center" />
        <el-table-column prop="carrier_cd" label="運送会社CD" width="110" align="center" />
        <el-table-column prop="delivery_lead_time" label="リードタイム(日)" width="120" align="center" />
        <el-table-column prop="issue_type" label="発行区分" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.issue_type === '通常' ? 'info' : 'warning'" size="small">{{ row.issue_type }}</el-tag>
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
              <el-button size="small" type="primary" link @click="openForm(row)">編集</el-button>
              <el-button size="small" type="danger" link @click="deleteDestination(row.id)">削除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="result-section">
      <div class="result-info">
        表示件数: {{ filteredList.length }} / {{ destinationList.length }}
      </div>
    </div>

    <!-- 弹窗 -->
    <DestinationForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Van, Filter, Refresh, Plus, Search, CircleCheck, InfoFilled, Tickets, Box
} from '@element-plus/icons-vue'
import DestinationForm from './DestinationForm.vue'
import { getDestinationList, deleteDestinationById, updateDestinationStatus } from '@/api/master/destinationMaster'

interface Destination {
  id: number;
  destination_cd: string;
  destination_name: string;
  customer_cd: string;
  carrier_cd: string;
  delivery_lead_time: number;
  issue_type: string;
  status: number;
}
type DestinationEx = Destination & { statusLoading: boolean }

const loading = ref(false)
const destinationList = ref<DestinationEx[]>([])
const filters = ref({
  keyword: '',
  status: '' as string | number,
  issue_type: '',
  carrier_cd: ''
})

const handleFilter = () => { }
const clearFilters = () => {
  filters.value = {
    keyword: '',
    status: '',
    issue_type: '',
    carrier_cd: ''
  }
}

const activeCount = computed(() => destinationList.value.filter(row => row.status == 1).length)
const hasActiveFilters = computed(() =>
  filters.value.keyword ||
  filters.value.status !== '' ||
  filters.value.issue_type ||
  filters.value.carrier_cd
)

const filteredList = computed(() => {
  let result = destinationList.value
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(row =>
      row.destination_cd?.toLowerCase().includes(keyword) ||
      row.destination_name?.toLowerCase().includes(keyword) ||
      row.customer_cd?.toLowerCase().includes(keyword)
    )
  }
  if (filters.value.status !== '') {
    result = result.filter(row => row.status === filters.value.status)
  }
  if (filters.value.issue_type) {
    result = result.filter(row => row.issue_type === filters.value.issue_type)
  }
  if (filters.value.carrier_cd) {
    result = result.filter(row => row.carrier_cd?.toLowerCase().includes(filters.value.carrier_cd.toLowerCase()))
  }
  return result
})

const formVisible = ref(false)
const editData = ref<DestinationEx | null>(null)
function openForm(row: DestinationEx | null = null) {
  editData.value = row
  formVisible.value = true
}

async function deleteDestination(id: number) {
  try {
    await ElMessageBox.confirm('この納入先を削除しますか？', '確認', { type: 'warning' })
    await deleteDestinationById(id)
    ElMessage.success('削除しました')
    fetchList()
  } catch { }
}

async function toggleStatus(row: DestinationEx) {
  row.statusLoading = true
  try {
    await updateDestinationStatus(row.id, row.status)
    ElMessage.success('状態を更新しました')
  } catch {
    row.status = row.status === 1 ? 0 : 1
    ElMessage.error('状態の更新に失敗しました')
  } finally {
    row.statusLoading = false
  }
}

async function fetchList() {
  loading.value = true
  const res = await getDestinationList({ keyword: filters.value.keyword })
  destinationList.value = (res.data || []).map((row: Destination) => ({ ...row, statusLoading: false }))
  loading.value = false
}
onMounted(fetchList)
</script>

<style scoped>
.destination-master-container {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.page-header {
  background: white;
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
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
  color: #2980b9;
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
  background: linear-gradient(135deg, #2980b9 0%, #27ae60 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(41, 128, 185, 0.2);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 4px;
}

/* 操作区块 */
.action-section {
  background: white;
  border-radius: 20px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

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
  color: #2980b9;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.clear-btn {
  color: #718096;
  transition: all 0.3s;
}

.clear-btn:hover {
  color: #2980b9;
  transform: scale(1.05);
}

.add-btn {
  background: linear-gradient(135deg, #27ae60 0%, #2980b9 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(41, 128, 185, 0.18);
  transition: all 0.3s;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(41, 128, 185, 0.23);
}

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
  color: #2980b9;
}

.filter-input {
  transition: all 0.3s;
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
  color: #2980b9;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.active-filters .el-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.active-filters .el-tag:hover {
  transform: scale(1.05);
}

/* 表格 */
.table-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
  margin-bottom: 16px;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
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

/* 响应式 */
@media (max-width:1200px) {
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

@media (max-width:768px) {
  .destination-master-container {
    padding: 12px;
  }

  .page-header {
    padding: 18px 10px;
  }

  .main-title {
    font-size: 1.5rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 16px 10px;
  }

  .filter-actions>* {
    flex: 1;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 14px;
    padding: 14px 8px;
  }

  .search-item {
    grid-column: span 1;
  }

  .filter-summary {
    padding: 10px 10px;
  }

  .stat-card {
    min-width: auto;
    flex: 1;
  }
}

@media (max-width:480px) {
  .main-title {
    font-size: 1.2rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

/* 深色模式 */
@media (prefers-color-scheme: dark) {
  .destination-master-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .page-header,
  .action-section,
  .table-card,
  .result-section {
    background: rgba(45, 55, 72, 0.88);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.12);
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
.table-card,
.page-header,
.action-section,
.result-section {
  animation: fadeInUp 0.6s;
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

/* ElementPlus覆盖 */
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
  --el-switch-on-color: #2980b9;
}
</style>
