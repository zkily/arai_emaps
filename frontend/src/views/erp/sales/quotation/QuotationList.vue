<template>
  <div class="quotation-list">
    <div class="page-header">
      <h2>見積管理</h2>
      <p class="subtitle">見積作成・過去見積参照・原価積算シミュレーション</p>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="見積番号">
          <el-input v-model="filters.quotation_no" placeholder="見積番号" clearable />
        </el-form-item>
        <el-form-item label="顧客">
          <el-select v-model="filters.customer_code" placeholder="顧客選択" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="期間">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="〜"
            start-placeholder="開始日" end-placeholder="終了日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="作成中" value="draft" />
            <el-option label="提出済" value="submitted" />
            <el-option label="受注済" value="ordered" />
            <el-option label="失注" value="lost" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 検索
          </el-button>
          <el-button @click="handleReset">リセット</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新規見積作成
      </el-button>
      <el-button @click="handleCostSimulation">
        <el-icon><DataAnalysis /></el-icon> 原価積算シミュレーション
      </el-button>
    </div>

    <!-- 見積一覧テーブル -->
    <el-card shadow="never">
      <el-table :data="quotationList" v-loading="loading" stripe border>
        <el-table-column prop="quotation_no" label="見積番号" width="140" fixed />
        <el-table-column prop="quotation_date" label="見積日" width="110" />
        <el-table-column prop="customer_name" label="顧客名" min-width="150" />
        <el-table-column prop="subject" label="件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="total_amount" label="見積金額" width="130" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="gross_profit_rate" label="粗利率" width="90" align="right">
          <template #default="{ row }">
            <span :class="getProfitClass(row.gross_profit_rate)">
              {{ row.gross_profit_rate?.toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="valid_until" label="有効期限" width="110" />
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleCopy(row)">複製</el-button>
            <el-button size="small" type="warning" link @click="handleExportPdf(row)">PDF</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)" v-if="row.status === 'draft'">削除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper" background />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const quotationList = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])

const filters = reactive({
  quotation_no: '',
  customer_code: '',
  dateRange: null as string[] | null,
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    // TODO: API呼び出し
    quotationList.value = []
    pagination.total = 0
  } catch (e) {
    ElMessage.error('データ取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(filters, { quotation_no: '', customer_code: '', dateRange: null, status: '' })
  handleSearch()
}

const handleCreate = () => {
  ElMessage.info('見積作成画面を開きます')
}

const handleCostSimulation = () => {
  ElMessage.info('原価積算シミュレーション画面を開きます')
}

const handleView = (row: any) => {
  ElMessage.info(`見積 ${row.quotation_no} の詳細を表示`)
}

const handleCopy = (row: any) => {
  ElMessage.success(`見積 ${row.quotation_no} を複製しました`)
}

const handleExportPdf = (row: any) => {
  ElMessage.info(`見積 ${row.quotation_no} のPDFを出力します`)
}

const handleDelete = async (row: any) => {
  await ElMessageBox.confirm('この見積を削除しますか？', '確認')
  ElMessage.success('削除しました')
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = { draft: 'info', submitted: 'primary', ordered: 'success', lost: 'danger' }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = { draft: '作成中', submitted: '提出済', ordered: '受注済', lost: '失注' }
  return map[status] || status
}

const getProfitClass = (rate: number) => {
  if (rate >= 30) return 'profit-high'
  if (rate >= 15) return 'profit-mid'
  return 'profit-low'
}
</script>

<style scoped>
.quotation-list { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.profit-high { color: #67c23a; font-weight: bold; }
.profit-mid { color: #e6a23c; }
.profit-low { color: #f56c6c; }
</style>
