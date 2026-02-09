<template>
  <div class="contract-pricing">
    <div class="page-header">
      <h2>契約単価管理</h2>
      <p class="subtitle">期間別・数量別ボリュームディスカウント単価設定</p>
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
        <el-form-item label="有効期限">
          <el-select v-model="filters.validity" placeholder="全て" clearable>
            <el-option label="有効のみ" value="active" />
            <el-option label="期限切れ含む" value="all" />
            <el-option label="期限切れのみ" value="expired" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新規契約単価登録
      </el-button>
      <el-button @click="handleBulkImport">
        <el-icon><Upload /></el-icon> 一括取込
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="pricingList" v-loading="loading" stripe border>
        <el-table-column prop="customer_name" label="顧客名" min-width="120" fixed />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="unit_price" label="契約単価" width="110" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="min_qty" label="最低数量" width="90" align="right" />
        <el-table-column prop="discount_type" label="割引種別" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ { volume: '数量割', period: '期間', special: '特別' }[row.discount_type] || row.discount_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="valid_from" label="有効開始日" width="110" />
        <el-table-column prop="valid_until" label="有効終了日" width="110" />
        <el-table-column prop="status" label="ステータス" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">{{ row.status === 'active' ? '有効' : '期限切れ' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="warning" link @click="handleEdit(row)">編集</el-button>
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
import { Search, Plus, Upload } from '@element-plus/icons-vue'

const loading = ref(false)
const pricingList = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ customer_code: '', product_code: '', validity: 'active' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { pricingList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('新規契約単価登録画面を開きます') }
const handleBulkImport = () => { ElMessage.info('一括取込画面を開きます') }
const handleView = (row: any) => { ElMessage.info(`${row.product_code} の契約単価詳細`) }
const handleEdit = (row: any) => { ElMessage.info(`${row.product_code} の契約単価を編集`) }
</script>

<style scoped>
.contract-pricing { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
