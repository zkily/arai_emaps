<template>
  <div class="rfq-list">
    <div class="page-header">
      <h2>見積依頼 (RFQ)</h2>
      <p class="subtitle">サプライヤーへの相見積もり依頼・比較表作成</p>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="RFQ番号">
          <el-input v-model="filters.rfq_no" placeholder="RFQ番号" clearable />
        </el-form-item>
        <el-form-item label="期間">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="〜"
            start-placeholder="開始日" end-placeholder="終了日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="依頼中" value="pending" />
            <el-option label="回答受領" value="received" />
            <el-option label="確定済" value="confirmed" />
            <el-option label="キャンセル" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新規見積依頼
      </el-button>
      <el-button @click="handleComparisonTable" :disabled="!hasSelection">
        <el-icon><DataAnalysis /></el-icon> 比較表作成
      </el-button>
    </div>

    <!-- RFQ一覧 -->
    <el-card shadow="never">
      <el-table :data="rfqList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="rfq_no" label="RFQ番号" width="130" fixed />
        <el-table-column prop="request_date" label="依頼日" width="110" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="90" align="right" />
        <el-table-column prop="suppliers_count" label="依頼先数" width="90" align="center" />
        <el-table-column prop="responses_count" label="回答数" width="80" align="center" />
        <el-table-column prop="deadline" label="回答期限" width="110" />
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleViewResponses(row)">回答一覧</el-button>
            <el-button size="small" type="warning" link @click="handleSend(row)" v-if="row.status === 'draft'">送信</el-button>
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
import { Search, Plus, DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const rfqList = ref<any[]>([])
const selectedRows = ref<any[]>([])

const filters = reactive({ rfq_no: '', dateRange: null as string[] | null, status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { rfqList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleCreate = () => { ElMessage.info('新規見積依頼画面を開きます') }
const handleComparisonTable = () => { ElMessage.info(`${selectedRows.value.length}件の比較表を作成します`) }
const handleView = (row: any) => { ElMessage.info(`RFQ ${row.rfq_no} の詳細`) }
const handleViewResponses = (row: any) => { ElMessage.info(`RFQ ${row.rfq_no} の回答一覧`) }
const handleSend = (row: any) => { ElMessage.success(`RFQ ${row.rfq_no} を送信しました`) }

const getStatusType = (s: string) => ({ pending: 'warning', received: 'success', confirmed: 'primary', cancelled: 'info' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '依頼中', received: '回答受領', confirmed: '確定済', cancelled: 'キャンセル' }[s] || s)
</script>

<style scoped>
.rfq-list { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
