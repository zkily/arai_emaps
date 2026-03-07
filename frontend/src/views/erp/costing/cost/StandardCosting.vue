<template>
  <div class="standard-costing">
    <div class="page-header">
      <h2>標準原価計算</h2>
      <p class="subtitle">積み上げ計算（材料費＋加工費＋経費）</p>
    </div>

    <!-- フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="品番">
          <el-select v-model="filters.product_code" placeholder="品番選択" clearable filterable>
            <el-option v-for="p in products" :key="p.cd" :label="`${p.cd} - ${p.name}`" :value="p.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="原価バージョン">
          <el-select v-model="filters.version" placeholder="バージョン">
            <el-option label="2026年度" value="2026" />
            <el-option label="2025年度" value="2025" />
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
        <el-icon><Plus /></el-icon> 新規原価登録
      </el-button>
      <el-button @click="handleImport">
        <el-icon><Upload /></el-icon> インポート
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon> エクスポート
      </el-button>
    </div>

    <!-- 標準原価一覧 -->
    <el-card shadow="never">
      <el-table :data="costList" v-loading="loading" stripe border>
        <el-table-column prop="product_code" label="品番" width="120" fixed />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="version" label="バージョン" width="100" />
        <el-table-column label="材料費" width="120" align="right">
          <template #default="{ row }">¥{{ row.material_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="加工費" width="120" align="right">
          <template #default="{ row }">¥{{ row.processing_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="経費" width="100" align="right">
          <template #default="{ row }">¥{{ row.overhead_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="標準原価" width="130" align="right">
          <template #default="{ row }">
            <span class="total-cost">¥{{ row.total_cost?.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="effective_date" label="適用開始日" width="110" />
        <el-table-column prop="status" label="ステータス" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '有効' : '無効' }}
            </el-tag>
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

    <!-- 原価構成詳細ダイアログ -->
    <el-dialog v-model="detailDialogVisible" :title="`原価構成詳細: ${selectedProduct?.product_code}`" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="品番">{{ selectedProduct?.product_code }}</el-descriptions-item>
        <el-descriptions-item label="品名">{{ selectedProduct?.product_name }}</el-descriptions-item>
        <el-descriptions-item label="バージョン">{{ selectedProduct?.version }}</el-descriptions-item>
        <el-descriptions-item label="適用開始日">{{ selectedProduct?.effective_date }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>材料費内訳</el-divider>
      <el-table :data="materialBreakdown" size="small" border>
        <el-table-column prop="material_code" label="材料コード" width="120" />
        <el-table-column prop="material_name" label="材料名" min-width="150" />
        <el-table-column prop="quantity" label="使用量" width="80" align="right" />
        <el-table-column prop="unit_price" label="単価" width="100" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金額" width="100" align="right">
          <template #default="{ row }">¥{{ row.amount?.toLocaleString() }}</template>
        </el-table-column>
      </el-table>

      <el-divider>加工費内訳</el-divider>
      <el-table :data="processingBreakdown" size="small" border>
        <el-table-column prop="process_code" label="工程コード" width="120" />
        <el-table-column prop="process_name" label="工程名" min-width="150" />
        <el-table-column prop="hours" label="工数(H)" width="80" align="right" />
        <el-table-column prop="rate" label="レート" width="100" align="right">
          <template #default="{ row }">¥{{ row.rate?.toLocaleString() }}/H</template>
        </el-table-column>
        <el-table-column prop="amount" label="金額" width="100" align="right">
          <template #default="{ row }">¥{{ row.amount?.toLocaleString() }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, Upload, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const costList = ref<any[]>([])
const products = ref<{ cd: string; name: string }[]>([])
const detailDialogVisible = ref(false)
const selectedProduct = ref<any>(null)
const materialBreakdown = ref<any[]>([])
const processingBreakdown = ref<any[]>([])

const filters = reactive({ product_code: '', version: '2026' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { costList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('新規原価登録画面を開きます') }
const handleImport = () => { ElMessage.info('インポート画面を開きます') }
const handleExport = () => { ElMessage.info('エクスポートしました') }
const handleView = (row: any) => {
  selectedProduct.value = row
  materialBreakdown.value = []
  processingBreakdown.value = []
  detailDialogVisible.value = true
}
const handleEdit = (row: any) => { ElMessage.info(`品番 ${row.product_code} の編集画面を開きます`) }
</script>

<style scoped>
.standard-costing { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.total-cost { font-weight: bold; color: #409eff; }
</style>
