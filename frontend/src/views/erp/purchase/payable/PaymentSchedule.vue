<template>
  <div class="payment-schedule">
    <div class="page-header">
      <h2>支払予定表</h2>
      <p class="subtitle">支払予定管理・資金繰り計画連携</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="仕入先">
          <el-select v-model="filters.supplier_code" placeholder="仕入先選択" clearable filterable>
            <el-option v-for="s in suppliers" :key="s.cd" :label="s.name" :value="s.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="支払予定月">
          <el-date-picker v-model="filters.paymentMonth" type="month" placeholder="対象月" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="未払い" value="unpaid" />
            <el-option label="支払済" value="paid" />
            <el-option label="遅延" value="overdue" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreateFb">
        <el-icon><CreditCard /></el-icon> FBデータ作成
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon> 支払予定表出力
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="scheduleList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="supplier_name" label="仕入先" min-width="130" fixed />
        <el-table-column prop="invoice_no" label="請求書番号" width="130" />
        <el-table-column prop="invoice_date" label="請求日" width="110" />
        <el-table-column prop="due_date" label="支払期日" width="110" />
        <el-table-column prop="amount" label="支払金額" width="130" align="right">
          <template #default="{ row }">¥{{ row.amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支払方法" width="100" align="center">
          <template #default="{ row }">
            {{ { transfer: '振込', bill: '手形', offset: '相殺' }[row.payment_method] || row.payment_method }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handlePay(row)" v-if="row.status === 'unpaid'">支払</el-button>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, CreditCard, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const scheduleList = ref<any[]>([])
const suppliers = ref<{ cd: string; name: string }[]>([])
const selectedRows = ref<any[]>([])
const filters = reactive({ supplier_code: '', paymentMonth: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { scheduleList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleCreateFb = () => { ElMessage.info(`${selectedRows.value.length}件のFBデータを作成します`) }
const handleExport = () => { ElMessage.info('支払予定表をエクスポートします') }
const handleView = (row: any) => { ElMessage.info(`支払 ${row.invoice_no} の詳細`) }
const handlePay = (row: any) => { ElMessage.success(`${row.invoice_no} の支払処理を実行しました`) }
const getStatusType = (s: string) => ({ unpaid: 'warning', paid: 'success', overdue: 'danger' }[s] || 'info')
const getStatusLabel = (s: string) => ({ unpaid: '未払い', paid: '支払済', overdue: '遅延' }[s] || s)
</script>

<style scoped>
.payment-schedule { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
