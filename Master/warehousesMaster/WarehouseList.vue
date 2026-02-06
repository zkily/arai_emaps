<!-- 倉庫マスタ -->
<template>
  <div class="warehouse-master-container">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Warehouse />
            </el-icon>
            倉庫マスタ管理
          </h1>
          <p class="subtitle">倉庫情報の登録・編集・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ warehouseList.length }}</div>
            <div class="stat-label">総倉庫数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeCount }}</div>
            <div class="stat-label">有効倉庫</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 機能操作区 -->
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
          <el-button type="primary" @click="openForm()" :icon="Plus" class="add-btn">倉庫追加</el-button>
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
          <el-input v-model="filters.keyword" placeholder="倉庫コード・名称・管理者 検索" clearable @input="handleFilter"
            class="filter-input">
            <template #suffix>
              <el-icon v-if="filters.keyword" class="search-active">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <CircleCheck />
            </el-icon>
            状態
          </label>
          <el-select v-model="filters.status" placeholder="全て" clearable @change="handleFilter" class="filter-input">
            <el-option label="有効" value="active">
              <el-tag type="success" size="small">有効</el-tag>
              <span class="status-desc">利用可能</span>
            </el-option>
            <el-option label="無効" value="inactive">
              <el-tag type="info" size="small">無効</el-tag>
              <span class="status-desc">利用停止</span>
            </el-option>
            <el-option label="メンテナンス" value="maintenance">
              <el-tag type="warning" size="small">メンテナンス</el-tag>
              <span class="status-desc">保守中</span>
            </el-option>
          </el-select>
        </div>
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <OfficeBuilding />
            </el-icon>
            倉庫タイプ
          </label>
          <el-select v-model="filters.warehouse_type" placeholder="全て" clearable @change="handleFilter" class="filter-input">
            <el-option label="内部倉庫" value="internal">
              <el-tag type="primary" size="small">内部</el-tag>
            </el-option>
            <el-option label="外注倉庫" value="outsourcing">
              <el-tag type="warning" size="small">外注</el-tag>
            </el-option>
            <el-option label="一時倉庫" value="temporary">
              <el-tag type="info" size="small">一時</el-tag>
            </el-option>
            <el-option label="特殊倉庫" value="special">
              <el-tag type="danger" size="small">特殊</el-tag>
            </el-option>
          </el-select>
        </div>
      </div>
      <div class="filter-summary" v-if="hasActiveFilters">
        <div class="summary-text">
          <el-icon class="summary-icon">
            <InfoFilled />
          </el-icon>
          <span>{{ filteredList.length }}件 / {{ warehouseList.length }}件中を表示</span>
        </div>
        <div class="active-filters">
          <el-tag v-if="filters.keyword" closable @close="filters.keyword = ''; handleFilter()" type="primary"
            size="small">検索: {{ filters.keyword }}</el-tag>
          <el-tag v-if="filters.status" closable @close="filters.status = ''; handleFilter()" type="info"
            size="small">状態: {{ getStatusLabel(filters.status) }}</el-tag>
          <el-tag v-if="filters.warehouse_type" closable @close="filters.warehouse_type = ''; handleFilter()" type="warning"
            size="small">タイプ: {{ getTypeLabel(filters.warehouse_type) }}</el-tag>
        </div>
      </div>
    </div>

    <!-- 主表格カード -->
    <el-card class="table-card">
      <el-table :data="filteredList" stripe highlight-current-row v-loading="loading" class="modern-table">
        <el-table-column prop="warehouse_code" label="倉庫コード" width="120" align="center" />
        <el-table-column prop="warehouse_name" label="倉庫名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="warehouse_type" label="タイプ" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.warehouse_type) as 'primary' | 'success' | 'warning' | 'danger' | 'info'" size="small">
              {{ getTypeLabel(row.warehouse_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="所在地" min-width="140" show-overflow-tooltip />
        <el-table-column prop="capacity" label="容量" width="100" align="center">
          <template #default="{ row }">
            {{ formatNumber(row.capacity) }}
          </template>
        </el-table-column>
        <el-table-column prop="current_usage" label="使用量" width="100" align="center">
          <template #default="{ row }">
            {{ formatNumber(row.current_usage) }}
          </template>
        </el-table-column>
        <el-table-column label="使用率" width="120" align="center">
          <template #default="{ row }">
            <div class="usage-progress">
              <el-progress
                :percentage="getUsagePercentage(row)"
                :color="getUsageColor(row)"
                :stroke-width="8"
                text-inside
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="manager_name" label="管理者" width="100" align="center" />
        <el-table-column prop="manager_contact" label="連絡先" width="130" align="center" />
        <el-table-column prop="status" label="状態" width="120" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.status"
              active-value="active"
              inactive-value="inactive"
              @change="toggleStatus(row)"
              :loading="row.statusLoading"
              inline-prompt
              active-text="有効"
              inactive-text="無効" />
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="140" align="center">
          <template #default="{ row }">
            <div class="action-buttons-table">
              <el-button size="small" type="primary" link @click="openForm(row)">編集</el-button>
              <el-button size="small" type="danger" link @click="deleteWarehouse(row.id)">削除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="result-section">
      <div class="result-info">
        表示件数: {{ filteredList.length }} / {{ warehouseList.length }}
      </div>
    </div>

    <!-- 弹窗 -->
    <WarehouseForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { House as Warehouse, Search, Plus, Refresh, CircleCheck, InfoFilled, OfficeBuilding } from '@element-plus/icons-vue'
import WarehouseForm from './WarehouseForm.vue'
import {
  getWarehouseList,
  deleteWarehouseById,
  updateWarehouseStatus
} from '../../../api/master/warehouseMaster'

interface WarehouseItem {
  id: number
  warehouse_code: string
  warehouse_name: string
  warehouse_type: 'internal' | 'outsourcing' | 'temporary' | 'special'
  status: 'active' | 'inactive' | 'maintenance'
  location: string
  capacity: number
  current_usage: number
  manager_name: string
  manager_contact: string
  company_name?: string
  contract_start?: string
  contract_end?: string
  monthly_cost?: number
  notes?: string
  statusLoading?: boolean
}

const loading = ref(false)
const warehouseList = ref<WarehouseItem[]>([])
const formVisible = ref(false)
const editData = ref<WarehouseItem | null>(null)
const filters = ref({
  keyword: '',
  status: '' as string,
  warehouse_type: '' as string
})

const activeCount = computed(() => warehouseList.value.filter(row => row.status === 'active').length)
const hasActiveFilters = computed(() => filters.value.keyword || filters.value.status || filters.value.warehouse_type)

const filteredList = computed(() => {
  let result = warehouseList.value
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(row =>
      row.warehouse_code?.toLowerCase().includes(keyword) ||
      row.warehouse_name?.toLowerCase().includes(keyword) ||
      row.manager_name?.toLowerCase().includes(keyword)
    )
  }
  if (filters.value.status) {
    result = result.filter(row => row.status === filters.value.status)
  }
  if (filters.value.warehouse_type) {
    result = result.filter(row => row.warehouse_type === filters.value.warehouse_type)
  }
  return result
})

function handleFilter() {
  // computed 已自动筛选
}

function clearFilters() {
  filters.value = { keyword: '', status: '', warehouse_type: '' }
}

function openForm(row: WarehouseItem | null = null) {
  editData.value = row
  formVisible.value = true
}

async function deleteWarehouse(id: number) {
  try {
    await ElMessageBox.confirm('この倉庫を削除しますか？', '確認', {
      type: 'warning',
      confirmButtonText: 'はい',
      cancelButtonText: 'キャンセル'
    })
    await deleteWarehouseById(id)
    ElMessage.success('削除しました')
    fetchList()
  } catch { }
}

async function toggleStatus(row: WarehouseItem) {
  row.statusLoading = true
  try {
    await updateWarehouseStatus(row.id, row.status)
    ElMessage.success('状態を更新しました')
  } catch {
    row.status = row.status === 'active' ? 'inactive' : 'active'
    ElMessage.error('状態の更新に失敗しました')
  } finally {
    row.statusLoading = false
  }
}

function getStatusLabel(status: string) {
  const labels = {
    'active': '有効',
    'inactive': '無効',
    'maintenance': 'メンテナンス'
  }
  return labels[status as keyof typeof labels] || status
}

function getTypeLabel(type: string) {
  const labels = {
    'internal': '内部倉庫',
    'outsourcing': '外注倉庫',
    'temporary': '一時倉庫',
    'special': '特殊倉庫'
  }
  return labels[type as keyof typeof labels] || type
}

function getTypeTagType(type: string) {
  const types = {
    'internal': 'primary',
    'outsourcing': 'warning',
    'temporary': 'info',
    'special': 'danger'
  }
  return types[type as keyof typeof types] || 'info'
}

function formatNumber(num: number) {
  return Math.floor(num || 0).toLocaleString()
}

function getUsagePercentage(row: WarehouseItem) {
  if (!row.capacity || row.capacity === 0) return 0
  return Math.round((row.current_usage / row.capacity) * 100)
}

function getUsageColor(row: WarehouseItem) {
  const percentage = getUsagePercentage(row)
  if (percentage >= 90) return '#f56c6c'
  if (percentage >= 70) return '#e6a23c'
  return '#67c23a'
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getWarehouseList({ keyword: filters.value.keyword })
    warehouseList.value = (res.data || []).map((row: WarehouseItem) => ({ ...row, statusLoading: false }))
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
/* 参考 CarrierList.vue の様式 */
.warehouse-master-container {
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
  justify-content: space-between;
  align-items: center;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 36px;
  color: #3498db;
}

.subtitle {
  font-size: 16px;
  color: #7f8c8d;
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 24px;
}

.stat-card {
  text-align: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  min-width: 120px;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.action-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.filter-icon {
  color: #3498db;
}

.filter-actions {
  display: flex;
  gap: 12px;
}

.filters-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 20px;
  margin-bottom: 16px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.filter-input {
  width: 100%;
}

.search-active {
  color: #3498db;
}

.filter-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #3498db;
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #555;
}

.summary-icon {
  color: #3498db;
}

.active-filters {
  display: flex;
  gap: 8px;
}

.table-card {
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: none;
  margin-bottom: 24px;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

.usage-progress {
  padding: 0 8px;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.result-section {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.result-info {
  font-size: 14px;
  color: #666;
  background: white;
  padding: 8px 16px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-desc {
  margin-left: 8px;
  font-size: 12px;
  color: #999;
}

.clear-btn {
  color: #666;
}

.add-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.add-btn:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
}
</style>
