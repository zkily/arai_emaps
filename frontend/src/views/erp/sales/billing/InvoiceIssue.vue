<template>
  <div class="invoice-issue">
    <div class="page-header">
      <h2>請求書発行</h2>
      <p class="subtitle">インボイス制度対応・締め請求書発行・電子請求書送信</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="顧客">
          <el-select v-model="filters.customer_code" placeholder="顧客選択" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="締め日">
          <el-date-picker v-model="filters.closingDate" type="date" placeholder="締め日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="未発行" value="pending" />
            <el-option label="発行済" value="issued" />
            <el-option label="送信済" value="sent" />
            <el-option label="入金済" value="paid" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleBatchIssue">
        <el-icon><Document /></el-icon> 一括請求書発行
      </el-button>
      <el-button @click="handleBatchSend">
        <el-icon><Promotion /></el-icon> 一括送信
      </el-button>
      <el-button @click="handleExportPdf">
        <el-icon><Download /></el-icon> PDF一括出力
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="invoiceList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="invoice_no" label="請求書番号" width="140" fixed />
        <el-table-column prop="customer_name" label="顧客名" min-width="150" />
        <el-table-column prop="closing_date" label="締め日" width="110" />
        <el-table-column prop="invoice_date" label="請求日" width="110" />
        <el-table-column prop="due_date" label="支払期限" width="110" />
        <el-table-column prop="subtotal" label="税抜金額" width="120" align="right">
          <template #default="{ row }">¥{{ row.subtotal?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="tax_amount" label="消費税" width="100" align="right">
          <template #default="{ row }">¥{{ row.tax_amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="total_amount" label="請求金額" width="130" align="right">
          <template #default="{ row }"><strong>¥{{ row.total_amount?.toLocaleString() }}</strong></template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleExportSingle(row)">PDF</el-button>
            <el-button size="small" type="warning" link @click="handleSend(row)" v-if="row.status === 'issued'">送信</el-button>
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
import { Search, Document, Promotion, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const invoiceList = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const selectedRows = ref<any[]>([])
const filters = reactive({ customer_code: '', closingDate: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { invoiceList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleBatchIssue = () => { ElMessage.info('一括請求書発行処理を実行します') }
const handleBatchSend = () => { ElMessage.info(`${selectedRows.value.length}件の請求書を送信します`) }
const handleExportPdf = () => { ElMessage.info('PDF一括出力します') }
const handleView = (row: any) => { ElMessage.info(`請求書 ${row.invoice_no} の詳細`) }
const handleExportSingle = (row: any) => { ElMessage.info(`請求書 ${row.invoice_no} のPDF出力`) }
const handleSend = (row: any) => { ElMessage.success(`請求書 ${row.invoice_no} を送信しました`) }
const getStatusType = (s: string) => ({ pending: 'info', issued: 'primary', sent: 'warning', paid: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '未発行', issued: '発行済', sent: '送信済', paid: '入金済' }[s] || s)
</script>

<style scoped>
.invoice-issue { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
