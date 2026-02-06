<template>
  <div class="transactions-page">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>

    <!-- 页面头部 -->
    <div class="modern-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32"><Tickets /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">入出庫履歴</h1>
            <div class="header-subtitle">在庫移動の履歴を確認</div>
          </div>
        </div>
        <div class="header-actions">
          <el-button @click="exportData">
            <el-icon><Download /></el-icon>エクスポート
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card modern-card inbound">
        <div class="stat-icon"><el-icon><Top /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">本日入庫</div>
          <div class="stat-value">{{ todayStats.inbound?.toLocaleString() || 0 }}</div>
        </div>
      </div>
      <div class="stat-card modern-card outbound">
        <div class="stat-icon"><el-icon><Bottom /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">本日出庫</div>
          <div class="stat-value">{{ todayStats.outbound?.toLocaleString() || 0 }}</div>
        </div>
      </div>
      <div class="stat-card modern-card transfer">
        <div class="stat-icon"><el-icon><Sort /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">本日移動</div>
          <div class="stat-value">{{ todayStats.transfer?.toLocaleString() || 0 }}</div>
        </div>
      </div>
      <div class="stat-card modern-card adjustment">
        <div class="stat-icon"><el-icon><Setting /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">本日調整</div>
          <div class="stat-value">{{ todayStats.adjustment?.toLocaleString() || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section modern-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番" clearable />
        </el-form-item>
        <el-form-item label="取引種別">
          <el-select v-model="filters.transaction_type" placeholder="種別を選択" clearable>
            <el-option label="入庫" value="inbound" />
            <el-option label="出庫" value="outbound" />
            <el-option label="移動（入）" value="transfer_in" />
            <el-option label="移動（出）" value="transfer_out" />
            <el-option label="調整" value="adjustment" />
          </el-select>
        </el-form-item>
        <el-form-item label="期間">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>検索
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>リセット
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格 -->
    <div class="table-section modern-card">
      <el-table :data="transactions" v-loading="loading" stripe border class="modern-table">
        <el-table-column prop="transaction_no" label="取引番号" width="140" />
        <el-table-column prop="created_at" label="日時" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="transaction_type_name" label="種別" width="100">
          <template #default="{ row }">
            <el-tag :type="getTransactionTypeTag(row.transaction_type)" size="small">
              {{ row.transaction_type_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" />
        <el-table-column prop="warehouse_name" label="倉庫" width="120" />
        <el-table-column prop="quantity" label="数量" width="100" align="right">
          <template #default="{ row }">
            <span :class="getQuantityClass(row.transaction_type)">
              {{ row.transaction_type.includes('out') ? '-' : '+' }}{{ row.quantity?.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="balance_after" label="残高" width="100" align="right">
          <template #default="{ row }">
            {{ row.balance_after?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="reference_no" label="参照番号" width="140" />
        <el-table-column prop="created_by" label="担当者" width="100" />
        <el-table-column prop="remarks" label="備考" min-width="150" show-overflow-tooltip />
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Tickets, Download, Search, Refresh, Top, Bottom, Sort, Setting } from '@element-plus/icons-vue'
import { getInventoryTransactions } from '@/api/erp/inventory'
import type { InventoryTransaction } from '@/types/erp/inventory'

const loading = ref(false)
const transactions = ref<InventoryTransaction[]>([])

const filters = reactive({
  product_code: '',
  transaction_type: '',
  dateRange: [] as string[]
})

const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0
})

const todayStats = reactive({
  inbound: 0,
  outbound: 0,
  transfer: 0,
  adjustment: 0
})

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('ja-JP')
}

// 获取交易类型标签样式
const getTransactionTypeTag = (type: string) => {
  const typeMap: Record<string, string> = {
    inbound: 'success',
    outbound: 'warning',
    transfer_in: 'info',
    transfer_out: 'info',
    adjustment: 'danger'
  }
  return typeMap[type] || 'info'
}

// 获取数量样式
const getQuantityClass = (type: string) => {
  if (type === 'inbound' || type === 'transfer_in') return 'quantity-in'
  return 'quantity-out'
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

// 重置
const resetFilters = () => {
  filters.product_code = ''
  filters.transaction_type = ''
  filters.dateRange = []
  pagination.page = 1
  fetchData()
}

// 导出
const exportData = () => {
  ElMessage.info('エクスポート機能は開発中です')
}

// 分页
const handleSizeChange = () => {
  pagination.page = 1
  fetchData()
}

const handleCurrentChange = () => {
  fetchData()
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      product_code: filters.product_code || undefined,
      transaction_type: filters.transaction_type || undefined,
      start_date: filters.dateRange?.[0] || undefined,
      end_date: filters.dateRange?.[1] || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    }
    const res = await getInventoryTransactions(params)
    transactions.value = res.data?.items || res.items || []
    pagination.total = res.data?.total || res.total || 0
  } catch (error) {
    console.error('データ取得に失敗しました', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.transactions-page {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  animation: float 20s ease-in-out infinite;
}

.orb-1 { width: 300px; height: 300px; top: -150px; right: -150px; }
.orb-2 { width: 200px; height: 200px; bottom: -100px; left: -100px; animation-delay: -10s; }

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-30px); }
}

.modern-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #67c23a, #85ce61);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.header-title {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: #8492a6;
}

.modern-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.stat-card.inbound .stat-icon { background: linear-gradient(135deg, #67c23a, #85ce61); }
.stat-card.outbound .stat-icon { background: linear-gradient(135deg, #e6a23c, #f7ba2a); }
.stat-card.transfer .stat-icon { background: linear-gradient(135deg, #409eff, #66b1ff); }
.stat-card.adjustment .stat-icon { background: linear-gradient(135deg, #909399, #b1b3b8); }

.stat-label {
  font-size: 14px;
  color: #8492a6;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
}

.filter-section {
  padding: 20px;
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.table-section {
  padding: 20px;
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

.quantity-in {
  color: #67c23a;
  font-weight: 600;
}

.quantity-out {
  color: #f56c6c;
  font-weight: 600;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
