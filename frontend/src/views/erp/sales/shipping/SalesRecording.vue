<template>
  <div class="recording-page">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <!-- Header -->
    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon :size="26"><Coin /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">売上計上</h1>
            <span class="header-subtitle">Sales Recording</span>
          </div>
        </div>
        <div class="header-actions">
          <el-date-picker
            v-model="selectedMonth"
            type="month"
            placeholder="対象月を選択"
            value-format="YYYY-MM"
            format="YYYY年MM月"
            class="month-picker"
            @change="handleMonthChange"
          />
          <el-button
            type="primary"
            :icon="DataAnalysis"
            @click="handleCalculate"
            :loading="calculating"
            class="calc-btn"
          >
            月次計上実行
          </el-button>
        </div>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="stats-grid animate-in" style="animation-delay:0.08s">
      <div class="stat-card glass-card">
        <div class="stat-card-inner">
          <div class="stat-icon icon-revenue">
            <el-icon :size="22"><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">今月売上額</div>
            <div class="stat-value">{{ formatCurrency(summary.total_amount) }}</div>
          </div>
        </div>
      </div>
      <div class="stat-card glass-card">
        <div class="stat-card-inner">
          <div class="stat-icon icon-shipments">
            <el-icon :size="22"><Van /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">出荷件数</div>
            <div class="stat-value">{{ summary.delivery_count?.toLocaleString() || 0 }}件</div>
          </div>
        </div>
      </div>
      <div class="stat-card glass-card">
        <div class="stat-card-inner">
          <div class="stat-icon icon-recorded">
            <el-icon :size="22"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">計上済件数</div>
            <div class="stat-value">{{ summary.recorded_count?.toLocaleString() || 0 }}件</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="glass-card table-section animate-in" style="animation-delay:0.16s">
      <div class="table-header">
        <h3 class="table-title">売上計上一覧</h3>
        <el-button @click="fetchRecordings" :icon="Refresh" circle class="refresh-btn" />
      </div>

      <el-table
        :data="tableData"
        v-loading="loading"
        class="dark-table"
        :header-cell-style="headerStyle"
        :row-class-name="tableRowClass"
        show-summary
        :summary-method="summaryMethod"
        empty-text="データがありません"
      >
        <el-table-column prop="recording_date" label="計上日" min-width="110">
          <template #default="{ row }">
            <span class="date-text">{{ row.recording_date || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="delivery_no" label="出荷番号" min-width="130">
          <template #default="{ row }">
            <span class="mono-text">{{ row.delivery_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="顧客名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="product_code" label="品番" min-width="120">
          <template #default="{ row }">
            <span class="mono-text">{{ row.product_code || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" min-width="90" align="right">
          <template #default="{ row }">
            <span class="number-text">{{ row.quantity?.toLocaleString() || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金額" min-width="120" align="right">
          <template #default="{ row }">
            <span class="number-text amount-text">¥{{ row.amount?.toLocaleString() || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="recordingStatusType(row.status)" effect="dark" round size="small">
              {{ recordingStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap" v-if="pagination.total > pagination.pageSize">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="fetchRecordings"
          @current-change="fetchRecordings"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Coin, Money, Van, CircleCheck, DataAnalysis, Refresh } from '@element-plus/icons-vue'
import { getSalesRecordings, calculateSalesRecordings, getSalesRecordingSummary } from '@/api/erp/sales'

const loading = ref(false)
const calculating = ref(false)
const tableData = ref<any[]>([])

const now = new Date()
const selectedMonth = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)

const summary = reactive({
  total_amount: 0,
  delivery_count: 0,
  recorded_count: 0,
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const headerStyle = {
  background: 'linear-gradient(135deg, rgba(20,184,166,0.15), rgba(6,182,212,0.15))',
  color: 'rgba(255,255,255,0.9)',
  borderBottom: '1px solid rgba(255,255,255,0.08)',
  fontSize: '12px',
  fontWeight: '600',
  padding: '8px 12px',
}

function tableRowClass({ rowIndex }: { rowIndex: number }) {
  return rowIndex % 2 === 0 ? 'row-even' : 'row-odd'
}

function formatCurrency(n: number): string {
  if (!n) return '¥0'
  if (n >= 1e8) return `¥${(n / 1e8).toFixed(1)}億`
  if (n >= 1e4) return `¥${(n / 1e4).toFixed(0)}万`
  return `¥${n.toLocaleString()}`
}

function recordingStatusType(status: string) {
  const map: Record<string, string> = {
    pending: 'info',
    recorded: 'success',
    cancelled: 'danger',
  }
  return map[status] || 'info'
}

function recordingStatusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '未計上',
    recorded: '計上済',
    cancelled: '取消',
  }
  return map[status] || status
}

function summaryMethod({ columns, data }: { columns: any[]; data: any[] }) {
  const sums: string[] = []
  columns.forEach((col, index) => {
    if (index === 0) {
      sums[index] = '合計'
      return
    }
    if (col.property === 'quantity') {
      const total = data.reduce((acc, row) => acc + (row.quantity || 0), 0)
      sums[index] = total.toLocaleString()
    } else if (col.property === 'amount') {
      const total = data.reduce((acc, row) => acc + (row.amount || 0), 0)
      sums[index] = `¥${total.toLocaleString()}`
    } else {
      sums[index] = ''
    }
  })
  return sums
}

async function fetchSummary() {
  try {
    const res: any = await getSalesRecordingSummary({ month: selectedMonth.value })
    const data = res?.data ?? res
    if (data) {
      summary.total_amount = data.total_amount || 0
      summary.delivery_count = data.delivery_count || 0
      summary.recorded_count = data.recorded_count || 0
    }
  } catch (e: any) {
    console.error('Failed to fetch summary', e)
  }
}

async function fetchRecordings() {
  loading.value = true
  try {
    const [year, month] = selectedMonth.value.split('-')
    const startDate = `${year}-${month}-01`
    const lastDay = new Date(Number(year), Number(month), 0).getDate()
    const endDate = `${year}-${month}-${String(lastDay).padStart(2, '0')}`

    const res: any = await getSalesRecordings({
      start_date: startDate,
      end_date: endDate,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    const data = res?.data ?? res
    tableData.value = data?.items || data?.list || data || []
    pagination.total = data?.total || tableData.value.length
  } catch (e: any) {
    console.error('Failed to fetch recordings', e)
    tableData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

function handleMonthChange() {
  pagination.page = 1
  fetchSummary()
  fetchRecordings()
}

async function handleCalculate() {
  try {
    await ElMessageBox.confirm(
      `${selectedMonth.value} の月次売上計上を実行しますか？`,
      '月次計上実行',
      { type: 'warning', confirmButtonText: '実行', cancelButtonText: 'キャンセル' }
    )
    calculating.value = true
    await calculateSalesRecordings({ month: selectedMonth.value })
    ElMessage.success('月次計上が完了しました')
    fetchSummary()
    fetchRecordings()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('月次計上に失敗しました')
    }
  } finally {
    calculating.value = false
  }
}

onMounted(() => {
  fetchSummary()
  fetchRecordings()
})
</script>

<style scoped>
.recording-page {
  position: relative;
  min-height: 100vh;
  padding: 16px;
  overflow-x: hidden;
}

.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: float 20s ease-in-out infinite;
}
.orb-1 { width: 380px; height: 380px; top: -80px; right: -60px; background: radial-gradient(circle, #14b8a6, transparent); }
.orb-2 { width: 320px; height: 320px; top: 50%; left: -80px; background: radial-gradient(circle, #8b5cf6, transparent); animation-delay: -7s; }
.orb-3 { width: 280px; height: 280px; bottom: -40px; right: 30%; background: radial-gradient(circle, #06b6d4, transparent); animation-delay: -14s; }
.noise-overlay {
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.glass-header {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 14px 20px;
  margin-bottom: 12px;
}
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #14b8a6, #0d9488);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 16px rgba(20, 184, 166, 0.4);
}
.header-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}
.header-subtitle {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.55);
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.month-picker :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  box-shadow: none;
}
.month-picker :deep(.el-input__inner) {
  color: rgba(255, 255, 255, 0.9);
}
.month-picker :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.4);
}
.calc-btn {
  border-radius: 8px;
  font-weight: 600;
  background: linear-gradient(135deg, #14b8a6, #0d9488);
  border: none;
}
.calc-btn:hover {
  background: linear-gradient(135deg, #0d9488, #0f766e);
}

.stats-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}
.stat-card {
  padding: 16px 18px;
  transition: all 0.3s ease;
}
.stat-card:hover {
  transform: translateY(-3px);
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
}
.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.icon-revenue { background: linear-gradient(135deg, #10b981, #059669); }
.icon-shipments { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.icon-recorded { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.stat-label {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 3px;
}
.stat-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: #fff;
}

.glass-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 14px 18px;
  margin-bottom: 12px;
}

.table-section {
  padding: 0;
  overflow: hidden;
}
.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.table-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}
.refresh-btn {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: rgba(255, 255, 255, 0.7) !important;
}
.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.12) !important;
  color: #fff !important;
}

.table-section :deep(.el-table) {
  background: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-text-color: rgba(255, 255, 255, 0.85);
  --el-table-header-text-color: rgba(255, 255, 255, 0.9);
  color: rgba(255, 255, 255, 0.85);
}
.table-section :deep(.el-table__body-wrapper) {
  background: transparent;
}
.table-section :deep(.el-table__row) {
  transition: background 0.2s;
}
.table-section :deep(.el-table__row.row-even td) {
  background: rgba(255, 255, 255, 0.02);
}
.table-section :deep(.el-table__row.row-odd td) {
  background: transparent;
}
.table-section :deep(.el-table__row:hover td) {
  background: rgba(20, 184, 166, 0.06) !important;
}
.table-section :deep(.el-table td),
.table-section :deep(.el-table th) {
  border-color: rgba(255, 255, 255, 0.06);
  padding: 8px 12px;
}
.table-section :deep(.el-table__footer-wrapper td) {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  border-color: rgba(255, 255, 255, 0.08);
}
.table-section :deep(.el-table__empty-text) {
  color: rgba(255, 255, 255, 0.45);
}

.mono-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.9);
}
.date-text {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.75);
}
.number-text {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  color: #60a5fa;
}
.amount-text {
  color: #34d399;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.pagination-wrap :deep(.el-pagination) {
  --el-pagination-bg-color: rgba(255, 255, 255, 0.06);
  --el-pagination-text-color: rgba(255, 255, 255, 0.7);
  --el-pagination-button-disabled-color: rgba(255, 255, 255, 0.3);
}
.pagination-wrap :deep(.el-pagination .btn-prev),
.pagination-wrap :deep(.el-pagination .btn-next),
.pagination-wrap :deep(.el-pager li) {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
}
.pagination-wrap :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #14b8a6, #06b6d4);
  color: #fff;
}

.animate-in {
  animation: slideIn 0.5s ease forwards;
  opacity: 0;
  transform: translateY(12px);
}
@keyframes slideIn {
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .recording-page { padding: 10px; }
  .header-content { flex-direction: column; align-items: flex-start; }
  .header-actions { width: 100%; }
  .stats-grid { grid-template-columns: 1fr; }
}
@media (min-width: 769px) and (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
