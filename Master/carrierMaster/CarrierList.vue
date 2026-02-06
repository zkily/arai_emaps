<!-- 運送便マスタ -->
<template>
  <div class="carrier-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Van />
            </el-icon>
            運送便マスタ管理
          </h1>
          <p class="subtitle">運送便情報の登録・編集・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ carrierList.length }}</div>
            <div class="stat-label">総運送便数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeCount }}</div>
            <div class="stat-label">有効運送便</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区 -->
    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Search />
          </el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">クリア</el-button>
          <el-button type="primary" @click="openForm()" :icon="Plus" class="add-btn">運送便追加</el-button>
        </div>
      </div>
      <div class="filters-grid">
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon>
              <Search />
            </el-icon>
            キーワード検索
          </label>
          <el-input v-model="filters.keyword" placeholder="運送便CD・名称・連絡人 検索" clearable @input="handleFilter"
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
      </div>
      <div class="filter-summary" v-if="hasActiveFilters">
        <div class="summary-text">
          <el-icon class="summary-icon">
            <InfoFilled />
          </el-icon>
          <span>{{ filteredList.length }}件 / {{ carrierList.length }}件中を表示</span>
        </div>
        <div class="active-filters">
          <el-tag v-if="filters.keyword" closable @close="filters.keyword = ''; handleFilter()" type="primary"
            size="small">検索: {{ filters.keyword }}</el-tag>
          <el-tag v-if="filters.status !== ''" closable @close="filters.status = ''; handleFilter()" type="info"
            size="small">状態: {{ filters.status == 1 ? '有効' : '無効' }}</el-tag>
        </div>
      </div>
    </div>

    <!-- 主表格卡片 -->
    <el-card class="table-card">
      <el-table :data="filteredList" stripe highlight-current-row v-loading="loading" class="modern-table">
        <el-table-column prop="carrier_cd" label="運送便CD" width="110" align="center" />
        <el-table-column prop="carrier_name" label="運送便名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="contact_person" label="連絡人" width="100" align="center" />
        <el-table-column prop="phone" label="電話番号" width="130" align="center" />
        <el-table-column prop="shipping_time" label="出荷時間" width="100" align="center" />
        <el-table-column prop="report_no" label="報告No" width="80" align="center" />
        <el-table-column prop="note" label="備考" min-width="120" show-overflow-tooltip />
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
              <el-button size="small" type="danger" link @click="deleteCarrier(row.id)">削除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="result-section">
      <div class="result-info">
        表示件数: {{ filteredList.length }} / {{ carrierList.length }}
      </div>
    </div>

    <!-- 弹窗 -->
    <CarrierForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Van, Search, Plus, Refresh, CircleCheck, InfoFilled } from '@element-plus/icons-vue'
import CarrierForm from './CarrierForm.vue'
import {
  getCarrierList,
  deleteCarrierById,
  updateCarrierStatus
} from '@/api/master/carrierMaster'

interface Carrier {
  id: number
  carrier_cd: string
  carrier_name: string
  contact_person: string
  phone: string
  shipping_time: string
  report_no: string
  note: string
  status: number
  statusLoading?: boolean
}

const loading = ref(false)
const carrierList = ref<Carrier[]>([])
const formVisible = ref(false)
const editData = ref<Carrier | null>(null)
const filters = ref({
  keyword: '',
  status: '' as string | number
})

const activeCount = computed(() => carrierList.value.filter(row => row.status == 1).length)
const hasActiveFilters = computed(() => filters.value.keyword || filters.value.status !== '')

const filteredList = computed(() => {
  let result = carrierList.value
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(row =>
      row.carrier_cd?.toLowerCase().includes(keyword) ||
      row.carrier_name?.toLowerCase().includes(keyword) ||
      row.contact_person?.toLowerCase().includes(keyword)
    )
  }
  if (filters.value.status !== '') {
    result = result.filter(row => row.status == filters.value.status)
  }
  return result
})

function handleFilter() {
  // computed 已自动筛选
}
function clearFilters() {
  filters.value = { keyword: '', status: '' }
}

function openForm(row: Carrier | null = null) {
  editData.value = row
  formVisible.value = true
}

async function deleteCarrier(id: number) {
  try {
    await ElMessageBox.confirm('この運送便を削除しますか？', '確認', {
      type: 'warning',
      confirmButtonText: 'はい',
      cancelButtonText: 'キャンセル'
    })
    await deleteCarrierById(id)
    ElMessage.success('削除しました')
    fetchList()
  } catch { }
}

async function toggleStatus(row: Carrier) {
  row.statusLoading = true
  try {
    await updateCarrierStatus(row.id, row.status)
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
  try {
    const res = await getCarrierList({ keyword: filters.value.keyword })
    carrierList.value = (res.data || []).map((row: Carrier) => ({ ...row, statusLoading: false }))
  } finally {
    loading.value = false
  }
}
onMounted(fetchList)
</script>

<style scoped>
/* 参考 CustomerList.vue 的样式，略作调整 */
.carrier-master-container {
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
  grid-template-columns: 2fr 1fr;
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

.status-desc {
  font-size: 0.8rem;
  color: #718096;
  margin-left: 8px;
}

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
  .carrier-master-container {
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

@media (prefers-color-scheme: dark) {
  .carrier-master-container {
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
