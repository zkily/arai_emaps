<template>
  <div class="eco-management">
    <div class="page-header">
      <h2>設計変更(ECO)管理</h2>
      <p class="subtitle">BOM版数管理・切替日設定・影響範囲分析</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="ECO番号">
          <el-input v-model="filters.eco_no" placeholder="ECO番号" clearable />
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番" clearable />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="申請中" value="pending" />
            <el-option label="承認済" value="approved" />
            <el-option label="実施中" value="in_progress" />
            <el-option label="完了" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新規ECO登録
      </el-button>
      <el-button @click="handleImpactAnalysis">
        <el-icon><DataAnalysis /></el-icon> 影響範囲分析
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="ecoList" v-loading="loading" stripe border>
        <el-table-column prop="eco_no" label="ECO番号" width="130" fixed />
        <el-table-column prop="title" label="変更件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="product_code" label="対象品番" width="120" />
        <el-table-column prop="change_type" label="変更種別" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ { design: '設計変更', material: '材料変更', process: '工程変更' }[row.change_type] || row.change_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="bom_version" label="BOM版数" width="90" align="center" />
        <el-table-column prop="effective_date" label="切替日" width="110" />
        <el-table-column prop="applicant" label="申請者" width="100" />
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleApprove(row)" v-if="row.status === 'pending'">承認</el-button>
            <el-button size="small" type="warning" link @click="handleExecute(row)" v-if="row.status === 'approved'">実施</el-button>
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
import { Search, Plus, DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const ecoList = ref<any[]>([])
const filters = reactive({ eco_no: '', product_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { ecoList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('新規ECO登録画面を開きます') }
const handleImpactAnalysis = () => { ElMessage.info('影響範囲分析を実行します') }
const handleView = (row: any) => { ElMessage.info(`ECO ${row.eco_no} の詳細`) }
const handleApprove = (row: any) => { ElMessage.success(`ECO ${row.eco_no} を承認しました`) }
const handleExecute = (row: any) => { ElMessage.info(`ECO ${row.eco_no} の実施画面を開きます`) }
const getStatusType = (s: string) => ({ pending: 'warning', approved: 'primary', in_progress: 'info', completed: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '申請中', approved: '承認済', in_progress: '実施中', completed: '完了' }[s] || s)
</script>

<style scoped>
.eco-management { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
