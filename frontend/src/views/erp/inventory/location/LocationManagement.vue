<template>
  <div class="location-management">
    <div class="page-header">
      <h2>ロケーション管理</h2>
      <p class="subtitle">マルチ倉庫・ロケーション管理・有効在庫照会</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="倉庫">
          <el-select v-model="filters.warehouse_code" placeholder="倉庫選択" clearable>
            <el-option v-for="w in warehouses" :key="w.cd" :label="w.name" :value="w.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="ロケーション">
          <el-input v-model="filters.location_code" placeholder="ロケーションCD" clearable />
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleAddLocation">
        <el-icon><Plus /></el-icon> ロケーション追加
      </el-button>
      <el-button @click="handleEffectiveStock">
        <el-icon><DataAnalysis /></el-icon> 有効在庫照会
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="locationList" v-loading="loading" stripe border>
        <el-table-column prop="warehouse_name" label="倉庫" width="120" fixed />
        <el-table-column prop="location_code" label="ロケーションCD" width="130" />
        <el-table-column prop="location_name" label="ロケーション名" min-width="150" />
        <el-table-column prop="zone" label="ゾーン" width="80" align="center" />
        <el-table-column prop="row" label="列" width="60" align="center" />
        <el-table-column prop="level" label="段" width="60" align="center" />
        <el-table-column prop="items_count" label="品目数" width="80" align="right" />
        <el-table-column prop="capacity_rate" label="使用率" width="100" align="right">
          <template #default="{ row }">
            <el-progress :percentage="row.capacity_rate" :color="row.capacity_rate > 90 ? '#f56c6c' : '#67c23a'" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">{{ row.status === 'active' ? '使用中' : '停止' }}</el-tag>
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
import { Search, Plus, DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const locationList = ref<any[]>([])
const warehouses = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ warehouse_code: '', location_code: '', product_code: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { locationList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleAddLocation = () => { ElMessage.info('ロケーション追加画面を開きます') }
const handleEffectiveStock = () => { ElMessage.info('有効在庫照会画面を開きます') }
const handleView = (row: any) => { ElMessage.info(`ロケーション ${row.location_code} の詳細`) }
const handleEdit = (row: any) => { ElMessage.info(`ロケーション ${row.location_code} を編集`) }
</script>

<style scoped>
.location-management { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
