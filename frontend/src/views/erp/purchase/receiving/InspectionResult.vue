<template>
  <div class="inspection-result">
    <div class="page-header">
      <h2>受入検査</h2>
      <p class="subtitle">良品/不良/保留判定・ロット番号付与（トレーサビリティ開始点）</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="受入番号">
          <el-input v-model="filters.receipt_no" placeholder="受入番号" clearable />
        </el-form-item>
        <el-form-item label="仕入先">
          <el-select v-model="filters.supplier_code" placeholder="仕入先選択" clearable filterable>
            <el-option v-for="s in suppliers" :key="s.cd" :label="s.name" :value="s.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="判定">
          <el-select v-model="filters.result" placeholder="全て" clearable>
            <el-option label="未検査" value="pending" />
            <el-option label="合格" value="passed" />
            <el-option label="不合格" value="failed" />
            <el-option label="保留" value="hold" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="inspectionList" v-loading="loading" stripe border>
        <el-table-column prop="receipt_no" label="受入番号" width="130" fixed />
        <el-table-column prop="supplier_name" label="仕入先" min-width="120" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="received_qty" label="受入数" width="80" align="right" />
        <el-table-column prop="lot_no" label="ロット番号" width="130" />
        <el-table-column prop="good_qty" label="良品数" width="80" align="right" />
        <el-table-column prop="defect_qty" label="不良数" width="80" align="right">
          <template #default="{ row }">
            <span :class="row.defect_qty > 0 ? 'text-danger' : ''">{{ row.defect_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="result" label="判定" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getResultType(row.result)">{{ getResultLabel(row.result) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="inspection_date" label="検査日" width="110" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleInspect(row)" v-if="row.result === 'pending'">検査実施</el-button>
            <el-button size="small" type="warning" link @click="handleAssignLot(row)" v-if="!row.lot_no">ロット付与</el-button>
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
import { Search } from '@element-plus/icons-vue'

const loading = ref(false)
const inspectionList = ref<any[]>([])
const suppliers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ receipt_no: '', supplier_code: '', result: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { inspectionList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleView = (row: any) => { ElMessage.info(`受入 ${row.receipt_no} の検査詳細`) }
const handleInspect = (row: any) => { ElMessage.info(`受入 ${row.receipt_no} の検査画面を開きます`) }
const handleAssignLot = (row: any) => { ElMessage.success(`受入 ${row.receipt_no} にロット番号を付与しました`) }
const getResultType = (s: string) => ({ pending: 'info', passed: 'success', failed: 'danger', hold: 'warning' }[s] || 'info')
const getResultLabel = (s: string) => ({ pending: '未検査', passed: '合格', failed: '不合格', hold: '保留' }[s] || s)
</script>

<style scoped>
.inspection-result { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-danger { color: #f56c6c; font-weight: bold; }
</style>
