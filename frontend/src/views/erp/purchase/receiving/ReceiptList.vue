<template>
  <div class="receipt-list">
    <div class="page-header">
      <h2>受入登録</h2>
      <p class="subtitle">現品票発行（QRコード）・受入検査依頼（良品/不良品/保留）</p>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="受入番号">
          <el-input v-model="filters.receipt_no" placeholder="受入番号" clearable />
        </el-form-item>
        <el-form-item label="入荷日">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="〜"
            start-placeholder="開始日" end-placeholder="終了日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="検査ステータス">
          <el-select v-model="filters.inspection_status" placeholder="全て" clearable>
            <el-option label="未検査" value="pending" />
            <el-option label="合格" value="passed" />
            <el-option label="不合格" value="rejected" />
            <el-option label="保留" value="hold" />
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
        <el-icon><Plus /></el-icon> 新規受入登録
      </el-button>
      <el-button @click="handlePrintLabel" :disabled="!hasSelection">
        <el-icon><Printer /></el-icon> 現品票発行
      </el-button>
      <el-button type="warning" @click="handleRequestInspection" :disabled="!hasPendingSelection">
        <el-icon><View /></el-icon> 受入検査依頼
      </el-button>
    </div>

    <!-- 受入一覧 -->
    <el-card shadow="never">
      <el-table :data="receiptList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="receipt_no" label="受入番号" width="130" fixed />
        <el-table-column prop="receipt_date" label="入荷日" width="110" />
        <el-table-column prop="order_no" label="発注番号" width="130" />
        <el-table-column prop="supplier_name" label="仕入先" min-width="150" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="lot_no" label="ロット番号" width="120" />
        <el-table-column prop="quantity" label="受入数" width="80" align="right" />
        <el-table-column prop="inspection_status" label="検査" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getInspectionType(row.inspection_status)" size="small">
              {{ getInspectionLabel(row.inspection_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quality_result" label="判定" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.quality_result === 'good'" class="result-good">良品</span>
            <span v-else-if="row.quality_result === 'defective'" class="result-bad">不良品</span>
            <span v-else-if="row.quality_result === 'hold'" class="result-hold">保留</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="good_quantity" label="良品数" width="80" align="right" />
        <el-table-column prop="defective_quantity" label="不良数" width="80" align="right">
          <template #default="{ row }">
            <span :class="row.defective_quantity > 0 ? 'text-danger' : ''">{{ row.defective_quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleInspect(row)" v-if="row.inspection_status === 'pending'">検査入力</el-button>
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
import { Search, Plus, Printer, View } from '@element-plus/icons-vue'

const loading = ref(false)
const receiptList = ref<any[]>([])
const selectedRows = ref<any[]>([])

const filters = reactive({ receipt_no: '', dateRange: null as string[] | null, inspection_status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)
const hasPendingSelection = computed(() => selectedRows.value.some(r => r.inspection_status === 'pending'))

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { receiptList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleCreate = () => { ElMessage.info('新規受入登録画面を開きます') }
const handlePrintLabel = () => { ElMessage.info(`${selectedRows.value.length}件の現品票（QRコード）を発行します`) }
const handleRequestInspection = () => { ElMessage.success('受入検査依頼を送信しました') }
const handleView = (row: any) => { ElMessage.info(`受入 ${row.receipt_no} の詳細`) }
const handleInspect = (row: any) => { ElMessage.info(`受入 ${row.receipt_no} の検査入力画面を開きます`) }

const getInspectionType = (s: string) => ({ pending: 'warning', passed: 'success', rejected: 'danger', hold: 'info' }[s] || 'info')
const getInspectionLabel = (s: string) => ({ pending: '未', passed: '済', rejected: '否', hold: '保' }[s] || s)
</script>

<style scoped>
.receipt-list { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.result-good { color: #67c23a; font-weight: bold; }
.result-bad { color: #f56c6c; font-weight: bold; }
.result-hold { color: #e6a23c; }
.text-danger { color: #f56c6c; }
</style>
