<template>
  <div class="arrival-schedule">
    <div class="page-header">
      <h2>入荷予定管理</h2>
      <p class="subtitle">納期遅延アラート・督促メール送信</p>
    </div>

    <!-- サマリーカード -->
    <div class="summary-cards">
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">{{ summary.today }}</div>
        <div class="summary-label">本日入荷予定</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">{{ summary.thisWeek }}</div>
        <div class="summary-label">今週入荷予定</div>
      </el-card>
      <el-card class="summary-card warning" shadow="never">
        <div class="summary-value">{{ summary.delayed }}</div>
        <div class="summary-label">遅延中</div>
      </el-card>
      <el-card class="summary-card danger" shadow="never">
        <div class="summary-value">{{ summary.overdue }}</div>
        <div class="summary-label">納期超過</div>
      </el-card>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="入荷予定日">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="〜"
            start-placeholder="開始日" end-placeholder="終了日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="仕入先">
          <el-select v-model="filters.supplier_code" placeholder="全て" clearable filterable>
            <el-option v-for="s in suppliers" :key="s.cd" :label="s.name" :value="s.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="入荷待ち" value="pending" />
            <el-option label="遅延中" value="delayed" />
            <el-option label="入荷済" value="received" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="warning" @click="handleSendReminder" :disabled="!hasDelayedSelection">
        <el-icon><Message /></el-icon> 督促メール送信
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon> エクスポート
      </el-button>
    </div>

    <!-- 入荷予定一覧 -->
    <el-card shadow="never">
      <el-table :data="arrivalList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="order_no" label="発注番号" width="130" fixed />
        <el-table-column prop="expected_date" label="入荷予定日" width="110">
          <template #default="{ row }">
            <span :class="getDateClass(row)">{{ row.expected_date }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="仕入先" min-width="150" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="order_quantity" label="発注数" width="90" align="right" />
        <el-table-column prop="received_quantity" label="入荷済" width="80" align="right" />
        <el-table-column prop="remaining_quantity" label="残数" width="80" align="right">
          <template #default="{ row }">
            <span :class="row.remaining_quantity > 0 ? 'text-warning' : ''">{{ row.remaining_quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="delay_days" label="遅延日数" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.delay_days > 0" type="danger">{{ row.delay_days }}日</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleReceive(row)" v-if="row.status !== 'received'">入荷登録</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next" background />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Message, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const arrivalList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const suppliers = ref<{ cd: string; name: string }[]>([])

const summary = reactive({ today: 0, thisWeek: 0, delayed: 0, overdue: 0 })
const filters = reactive({ dateRange: null as string[] | null, supplier_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasDelayedSelection = computed(() => selectedRows.value.some(r => r.status === 'delayed'))

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { arrivalList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleSendReminder = () => { ElMessage.success('督促メールを送信しました') }
const handleExport = () => { ElMessage.info('エクスポートしました') }
const handleView = (row: any) => { ElMessage.info(`発注 ${row.order_no} の詳細`) }
const handleReceive = (row: any) => { ElMessage.info(`発注 ${row.order_no} の入荷登録画面を開きます`) }

const getStatusType = (s: string) => ({ pending: 'info', delayed: 'danger', received: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '入荷待ち', delayed: '遅延中', received: '入荷済' }[s] || s)
const getDateClass = (row: any) => row.delay_days > 0 ? 'text-danger' : ''
</script>

<style scoped>
.arrival-schedule { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.summary-card { text-align: center; padding: 20px; }
.summary-value { font-size: 32px; font-weight: bold; color: #409eff; }
.summary-card.warning .summary-value { color: #e6a23c; }
.summary-card.danger .summary-value { color: #f56c6c; }
.summary-label { color: #909399; margin-top: 8px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; font-weight: bold; }
</style>
