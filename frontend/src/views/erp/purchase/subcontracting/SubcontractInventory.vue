<template>
  <div class="subcontract-inventory">
    <div class="page-header">
      <h2>外注先在庫管理</h2>
      <p class="subtitle">外注先にある自社資産の把握・棚卸・過不足管理</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="外注先">
          <el-select v-model="filters.supplier_code" placeholder="外注先選択" clearable filterable>
            <el-option v-for="s in suppliers" :key="s.cd" :label="s.name" :value="s.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="材料CD">
          <el-input v-model="filters.material_code" placeholder="材料CD" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button @click="handleStocktaking">
        <el-icon><Document /></el-icon> 外注先棚卸
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon> エクスポート
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="inventoryList" v-loading="loading" stripe border>
        <el-table-column prop="supplier_name" label="外注先" min-width="130" fixed />
        <el-table-column prop="material_code" label="材料CD" width="120" />
        <el-table-column prop="material_name" label="材料名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="supplied_qty" label="支給累計" width="100" align="right" />
        <el-table-column prop="used_qty" label="使用累計" width="100" align="right" />
        <el-table-column prop="returned_qty" label="返却累計" width="100" align="right" />
        <el-table-column prop="current_stock" label="預り在庫" width="100" align="right">
          <template #default="{ row }">
            <strong>{{ row.current_stock }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="valuation" label="評価額" width="120" align="right">
          <template #default="{ row }">¥{{ row.valuation?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="last_updated" label="最終更新" width="110" />
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
import { Search, Document, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const inventoryList = ref<any[]>([])
const suppliers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ supplier_code: '', material_code: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { inventoryList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleStocktaking = () => { ElMessage.info('外注先棚卸処理を開始します') }
const handleExport = () => { ElMessage.info('外注先在庫をエクスポートします') }
const handleView = (row: any) => { ElMessage.info(`${row.supplier_name} - ${row.material_code} の詳細`) }
</script>

<style scoped>
.subcontract-inventory { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
