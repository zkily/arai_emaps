<template>
  <div class="payment">
    <div class="page-header">
      <h2>支払管理（AP）</h2>
      <p class="subtitle">支払予定表作成・FBデータ（全銀協フォーマット）出力</p>
    </div>

    <!-- サマリー -->
    <div class="summary-cards">
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">¥{{ summary.totalPayables?.toLocaleString() }}</div>
        <div class="summary-label">買掛金残高</div>
      </el-card>
      <el-card class="summary-card warning" shadow="never">
        <div class="summary-value">¥{{ summary.thisWeekDue?.toLocaleString() }}</div>
        <div class="summary-label">今週支払予定</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">¥{{ summary.thisMonthDue?.toLocaleString() }}</div>
        <div class="summary-label">今月支払予定</div>
      </el-card>
      <el-card class="summary-card danger" shadow="never">
        <div class="summary-value">{{ summary.overdueCount }}</div>
        <div class="summary-label">支払遅延件数</div>
      </el-card>
    </div>

    <!-- フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="支払予定日">
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
            <el-option label="支払待ち" value="pending" />
            <el-option label="承認待ち" value="approval" />
            <el-option label="支払済" value="paid" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="primary" @click="handleCreateSchedule">
        <el-icon><Calendar /></el-icon> 支払予定表作成
      </el-button>
      <el-button type="success" @click="handleExportFb" :disabled="!hasSelection">
        <el-icon><Download /></el-icon> FBデータ出力
      </el-button>
      <el-button type="warning" @click="handleApprove" :disabled="!hasPendingApproval">
        <el-icon><Check /></el-icon> 支払承認
      </el-button>
      <el-button @click="handlePrint" :disabled="!hasSelection">
        <el-icon><Printer /></el-icon> 支払一覧印刷
      </el-button>
    </div>

    <!-- 支払一覧 -->
    <el-card shadow="never">
      <el-table :data="paymentList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="payment_no" label="支払番号" width="130" fixed />
        <el-table-column prop="due_date" label="支払予定日" width="110">
          <template #default="{ row }">
            <span :class="isOverdue(row) ? 'text-danger' : ''">{{ row.due_date }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="仕入先" min-width="150" />
        <el-table-column prop="invoice_no" label="請求書番号" width="130" />
        <el-table-column prop="payment_amount" label="支払金額" width="130" align="right">
          <template #default="{ row }">
            <span class="font-bold">¥{{ row.payment_amount?.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="bank_name" label="振込先銀行" width="150" />
        <el-table-column prop="account_no" label="口座番号" width="120" />
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
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
import { Search, Calendar, Download, Check, Printer } from '@element-plus/icons-vue'

const loading = ref(false)
const paymentList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const suppliers = ref<{ cd: string; name: string }[]>([])

const summary = reactive({ totalPayables: 0, thisWeekDue: 0, thisMonthDue: 0, overdueCount: 0 })
const filters = reactive({ dateRange: null as string[] | null, supplier_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)
const hasPendingApproval = computed(() => selectedRows.value.some(r => r.status === 'approval'))

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { paymentList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleCreateSchedule = () => { ElMessage.info('支払予定表作成画面を開きます') }
const handleExportFb = () => { ElMessage.success('FBデータ（全銀協フォーマット）を出力しました') }
const handleApprove = () => { ElMessage.success('支払を承認しました') }
const handlePrint = () => { ElMessage.info('支払一覧を印刷します') }
const handleView = (row: any) => { ElMessage.info(`支払 ${row.payment_no} の詳細`) }

const isOverdue = (row: any) => row.status === 'pending' && new Date(row.due_date) < new Date()
const getStatusType = (s: string) => ({ pending: 'warning', approval: 'info', paid: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '支払待ち', approval: '承認待ち', paid: '支払済' }[s] || s)
</script>

<style scoped>
.payment { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.summary-card { text-align: center; padding: 20px; }
.summary-value { font-size: 28px; font-weight: bold; color: #409eff; }
.summary-card.warning .summary-value { color: #e6a23c; }
.summary-card.danger .summary-value { color: #f56c6c; }
.summary-label { color: #909399; margin-top: 8px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.font-bold { font-weight: bold; }
.text-danger { color: #f56c6c; }
</style>
