<template>
  <div class="forecast-management">
    <div class="page-header">
      <h2>内示・フォーキャスト管理</h2>
      <p class="subtitle">確定前の需要予測をAPSへ連携・フォーキャスト精度分析</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="顧客">
          <el-select v-model="filters.customer_code" placeholder="顧客選択" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番" clearable />
        </el-form-item>
        <el-form-item label="対象月">
          <el-date-picker v-model="filters.targetMonth" type="month" placeholder="対象月" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="内示" value="forecast" />
            <el-option label="確定" value="confirmed" />
            <el-option label="差異あり" value="diff" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
          <el-button @click="handleReset">リセット</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleImport">
        <el-icon><Upload /></el-icon> 内示データ取込
      </el-button>
      <el-button @click="handleSyncAps">
        <el-icon><Connection /></el-icon> APS連携
      </el-button>
      <el-button @click="handleAccuracyReport">
        <el-icon><DataAnalysis /></el-icon> 精度分析レポート
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="forecastList" v-loading="loading" stripe border>
        <el-table-column prop="customer_name" label="顧客名" min-width="120" fixed />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="target_month" label="対象月" width="100" />
        <el-table-column prop="forecast_qty" label="内示数量" width="100" align="right" />
        <el-table-column prop="confirmed_qty" label="確定数量" width="100" align="right" />
        <el-table-column prop="diff_qty" label="差異" width="90" align="right">
          <template #default="{ row }">
            <span :class="row.diff_qty > 0 ? 'text-success' : row.diff_qty < 0 ? 'text-danger' : ''">
              {{ row.diff_qty > 0 ? '+' : '' }}{{ row.diff_qty }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="accuracy_rate" label="精度" width="80" align="right">
          <template #default="{ row }">{{ row.accuracy_rate?.toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'confirmed' ? 'success' : row.status === 'diff' ? 'warning' : 'info'">
              {{ { forecast: '内示', confirmed: '確定', diff: '差異あり' }[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleConfirm(row)" v-if="row.status === 'forecast'">確定</el-button>
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
import { Search, Upload, Connection, DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const forecastList = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ customer_code: '', product_code: '', targetMonth: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { forecastList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleReset = () => { Object.assign(filters, { customer_code: '', product_code: '', targetMonth: '', status: '' }); handleSearch() }
const handleImport = () => { ElMessage.info('内示データ取込画面を開きます') }
const handleSyncAps = () => { ElMessage.info('APS連携を実行します') }
const handleAccuracyReport = () => { ElMessage.info('精度分析レポートを生成します') }
const handleView = (row: any) => { ElMessage.info(`${row.product_code} のフォーキャスト詳細`) }
const handleConfirm = (row: any) => { ElMessage.success(`${row.product_code} を確定しました`) }
</script>

<style scoped>
.forecast-management { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-success { color: #67c23a; font-weight: bold; }
.text-danger { color: #f56c6c; font-weight: bold; }
</style>
