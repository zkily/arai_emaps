<template>
  <div class="material-consumption">
    <div class="page-header">
      <h2>材料消費実績</h2>
      <p class="subtitle">バックフラッシュ/実消費選択・標準消費量との差異管理</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="生産オーダー">
          <el-input v-model="filters.order_no" placeholder="オーダー番号" clearable />
        </el-form-item>
        <el-form-item label="消費方式">
          <el-select v-model="filters.method" placeholder="全て" clearable>
            <el-option label="バックフラッシュ" value="backflush" />
            <el-option label="実消費" value="actual" />
          </el-select>
        </el-form-item>
        <el-form-item label="期間">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="〜"
            start-placeholder="開始日" end-placeholder="終了日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleBackflush"><el-icon><Cpu /></el-icon> バックフラッシュ実行</el-button>
      <el-button @click="handleManualEntry"><el-icon><Edit /></el-icon> 手動消費登録</el-button>
      <el-button @click="handleVarianceReport"><el-icon><DataAnalysis /></el-icon> 差異レポート</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="consumptionList" v-loading="loading" stripe border>
        <el-table-column prop="order_no" label="生産オーダー" width="130" fixed />
        <el-table-column prop="material_code" label="材料CD" width="120" />
        <el-table-column prop="material_name" label="材料名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="method" label="消費方式" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.method === 'backflush' ? 'primary' : 'success'" size="small">
              {{ row.method === 'backflush' ? 'BF' : '実消費' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="standard_qty" label="標準消費量" width="100" align="right" />
        <el-table-column prop="actual_qty" label="実績消費量" width="100" align="right" />
        <el-table-column prop="variance_qty" label="差異" width="80" align="right">
          <template #default="{ row }">
            <span :class="row.variance_qty > 0 ? 'text-danger' : row.variance_qty < 0 ? 'text-success' : ''">
              {{ row.variance_qty > 0 ? '+' : '' }}{{ row.variance_qty }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="lot_no" label="ロット番号" width="130" />
        <el-table-column prop="consumption_date" label="消費日" width="110" />
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
import { Search, Cpu, Edit, DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const consumptionList = ref<any[]>([])
const filters = reactive({ order_no: '', method: '', dateRange: null as string[] | null })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { consumptionList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleBackflush = () => { ElMessage.info('バックフラッシュ処理を実行します') }
const handleManualEntry = () => { ElMessage.info('手動消費登録画面を開きます') }
const handleVarianceReport = () => { ElMessage.info('消費差異レポートを生成します') }
const handleView = (row: any) => { ElMessage.info(`${row.order_no} の消費実績詳細`) }
</script>

<style scoped>
.material-consumption { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-danger { color: #f56c6c; font-weight: bold; }
.text-success { color: #67c23a; }
</style>
