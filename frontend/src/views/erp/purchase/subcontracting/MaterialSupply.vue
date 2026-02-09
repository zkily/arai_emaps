<template>
  <div class="material-supply">
    <div class="page-header">
      <h2>有償/無償支給管理</h2>
      <p class="subtitle">自社材料の外注先への支給処理・支給在庫管理</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="外注先">
          <el-select v-model="filters.supplier_code" placeholder="外注先選択" clearable filterable>
            <el-option v-for="s in suppliers" :key="s.cd" :label="s.name" :value="s.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="支給区分">
          <el-select v-model="filters.supply_type" placeholder="全て" clearable>
            <el-option label="有償支給" value="paid" />
            <el-option label="無償支給" value="free" />
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
      <el-button type="primary" @click="handleCreateSupply">
        <el-icon><Plus /></el-icon> 新規支給指示
      </el-button>
      <el-button @click="handleSupplierStock">
        <el-icon><Box /></el-icon> 外注先在庫照会
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="supplyList" v-loading="loading" stripe border>
        <el-table-column prop="supply_no" label="支給番号" width="130" fixed />
        <el-table-column prop="supplier_name" label="外注先" min-width="130" />
        <el-table-column prop="material_code" label="材料CD" width="120" />
        <el-table-column prop="material_name" label="材料名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="supply_type" label="支給区分" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.supply_type === 'paid' ? 'warning' : 'success'" size="small">
              {{ row.supply_type === 'paid' ? '有償' : '無償' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="支給数量" width="90" align="right" />
        <el-table-column prop="unit_price" label="支給単価" width="100" align="right">
          <template #default="{ row }">
            {{ row.supply_type === 'paid' ? `¥${row.unit_price?.toLocaleString()}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="supply_date" label="支給日" width="110" />
        <el-table-column prop="status" label="ステータス" width="100" align="center">
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
import { Search, Plus, Box } from '@element-plus/icons-vue'

const loading = ref(false)
const supplyList = ref<any[]>([])
const suppliers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ supplier_code: '', supply_type: '', dateRange: null as string[] | null })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { supplyList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreateSupply = () => { ElMessage.info('新規支給指示画面を開きます') }
const handleSupplierStock = () => { ElMessage.info('外注先在庫照会画面を開きます') }
const handleView = (row: any) => { ElMessage.info(`支給 ${row.supply_no} の詳細`) }
const getStatusType = (s: string) => ({ pending: 'info', shipped: 'warning', received: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '準備中', shipped: '出荷済', received: '受領済' }[s] || s)
</script>

<style scoped>
.material-supply { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
