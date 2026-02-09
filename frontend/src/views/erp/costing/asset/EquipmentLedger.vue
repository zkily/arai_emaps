<template>
  <div class="equipment-ledger">
    <div class="page-header">
      <h2>設備台帳</h2>
      <p class="subtitle">固定資産管理・設備情報・メンテナンス履歴</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="資産番号">
          <el-input v-model="filters.asset_no" placeholder="資産番号" clearable />
        </el-form-item>
        <el-form-item label="設備種別">
          <el-select v-model="filters.type" placeholder="全て" clearable>
            <el-option label="製造設備" value="manufacturing" />
            <el-option label="検査設備" value="inspection" />
            <el-option label="搬送設備" value="transport" />
            <el-option label="ユーティリティ" value="utility" />
          </el-select>
        </el-form-item>
        <el-form-item label="設置場所">
          <el-input v-model="filters.location" placeholder="設置場所" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新規登録</el-button>
      <el-button @click="handleExport"><el-icon><Download /></el-icon> 台帳エクスポート</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="assetList" v-loading="loading" stripe border>
        <el-table-column prop="asset_no" label="資産番号" width="120" fixed />
        <el-table-column prop="name" label="設備名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="type" label="種別" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ { manufacturing: '製造', inspection: '検査', transport: '搬送', utility: 'ユーティリティ' }[row.type] || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="acquisition_date" label="取得日" width="110" />
        <el-table-column prop="acquisition_cost" label="取得価額" width="130" align="right">
          <template #default="{ row }">¥{{ row.acquisition_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="book_value" label="帳簿価額" width="130" align="right">
          <template #default="{ row }">¥{{ row.book_value?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="depreciation_method" label="償却方法" width="100" align="center" />
        <el-table-column prop="useful_life" label="耐用年数" width="90" align="right" />
        <el-table-column prop="location" label="設置場所" width="120" />
        <el-table-column prop="status" label="ステータス" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : row.status === 'maintenance' ? 'warning' : 'info'">
              {{ { active: '稼働中', maintenance: '保全中', retired: '除却済' }[row.status] || row.status }}
            </el-tag>
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
import { Search, Plus, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const assetList = ref<any[]>([])
const filters = reactive({ asset_no: '', type: '', location: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { assetList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('新規設備登録画面を開きます') }
const handleExport = () => { ElMessage.info('設備台帳をエクスポートします') }
const handleView = (row: any) => { ElMessage.info(`設備 ${row.asset_no} の詳細`) }
</script>

<style scoped>
.equipment-ledger { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
