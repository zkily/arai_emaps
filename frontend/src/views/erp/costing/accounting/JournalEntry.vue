<template>
  <div class="journal-entry">
    <div class="page-header">
      <h2>自動仕訳生成</h2>
      <p class="subtitle">売上・仕入・移動・製造振替の自動仕訳</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="対象年月">
          <el-date-picker v-model="filters.targetMonth" type="month" placeholder="対象月" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="仕訳種別">
          <el-select v-model="filters.type" placeholder="全て" clearable>
            <el-option label="売上" value="sales" />
            <el-option label="仕入" value="purchase" />
            <el-option label="在庫移動" value="transfer" />
            <el-option label="製造振替" value="manufacturing" />
            <el-option label="減価償却" value="depreciation" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="未生成" value="pending" />
            <el-option label="生成済" value="generated" />
            <el-option label="転記済" value="posted" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleGenerate"><el-icon><Cpu /></el-icon> 仕訳生成</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="success" @click="handlePost"><el-icon><Check /></el-icon> 一括転記</el-button>
      <el-button @click="handleExport"><el-icon><Download /></el-icon> エクスポート</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="journalList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="journal_no" label="仕訳番号" width="130" fixed />
        <el-table-column prop="journal_date" label="仕訳日" width="110" />
        <el-table-column prop="type" label="種別" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ { sales: '売上', purchase: '仕入', transfer: '移動', manufacturing: '製造', depreciation: '償却' }[row.type] || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="debit_account" label="借方勘定" width="130" />
        <el-table-column prop="credit_account" label="貸方勘定" width="130" />
        <el-table-column prop="amount" label="金額" width="130" align="right">
          <template #default="{ row }">¥{{ row.amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="description" label="摘要" min-width="200" show-overflow-tooltip />
        <el-table-column prop="source_no" label="元伝票番号" width="130" />
        <el-table-column prop="status" label="ステータス" width="90" align="center">
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Check, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const journalList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const filters = reactive({ targetMonth: '', type: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { journalList.value = [] } finally { loading.value = false }
}

const handleGenerate = () => { ElMessage.info('自動仕訳生成を実行します') }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handlePost = () => { ElMessage.info(`${selectedRows.value.length}件の仕訳を転記します`) }
const handleExport = () => { ElMessage.info('仕訳データをエクスポートします') }
const handleView = (row: any) => { ElMessage.info(`仕訳 ${row.journal_no} の詳細`) }
const getStatusType = (s: string) => ({ pending: 'info', generated: 'primary', posted: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '未生成', generated: '生成済', posted: '転記済' }[s] || s)
</script>

<style scoped>
.journal-entry { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
