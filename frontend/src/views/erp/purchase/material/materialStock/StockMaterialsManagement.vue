<template>
  <div class="stock-materials-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="main-title">
          <el-icon class="title-icon">
            <Box />
          </el-icon>
          材料在庫管理
        </h1>
        <p class="subtitle">材料在庫の管理・使用状況の追跡を行います</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleMigrate" :loading="migrating">
          <el-icon><Refresh /></el-icon>
          新データ追加
        </el-button>
        <el-button type="success" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          更新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-container">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon total">
                <el-icon><Box /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.total_count || 0 }}</div>
                <div class="stat-label">総記録数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon materials">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.leftover_materials || 0 }}</div>
                <div class="stat-label">半端材料数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon used">
                <el-icon><Check /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.used_quantity || 0 }}</div>
                <div class="stat-label">使用済み数量</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon unused">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.unused_quantity || 0 }}</div>
                <div class="stat-label">未使用数量</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选区域 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="キーワード">
          <el-input
            v-model="searchForm.keyword"
            placeholder="材料名または製造番号"
            clearable
            @keyup.enter="handleSearch"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="日付範囲">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="仕入先">
          <el-select
            v-model="searchForm.supplier"
            placeholder="仕入先を選択"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="supplier in supplierOptions"
              :key="supplier.value"
              :label="supplier.label"
              :value="supplier.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="使用状態">
          <el-select
            v-model="searchForm.is_used"
            placeholder="使用状態を選択"
            clearable
            style="width: 120px"
          >
            <el-option label="未使用" :value="0" />
            <el-option label="使用済み" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            検索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            リセット
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <template #header>
        <div class="table-header">
          <span class="table-title">材料在庫リスト</span>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        border
        style="width: 100%"
        @sort-change="handleSortChange"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column
          prop="log_date"
          label="入荷日"
          width="110"
          align="center"
          sortable="custom"
        />
        <el-table-column
          prop="supplier"
          label="仕入先"
          width="150"
          align="center"
          sortable="custom"
        />
        <el-table-column prop="material_name" label="材料名" width="150" sortable="custom" />
        <el-table-column
          prop="material_quality"
          label="材料品質"
          width="120"
          align="center"
          sortable="custom"
        />
        <el-table-column
          prop="manufacture_no"
          label="製造番号"
          width="150"
          align="center"
          sortable="custom"
        />
        <el-table-column
          prop="quantity"
          label="数量"
          width="100"
          align="center"
          sortable="custom"
        />
        <el-table-column prop="is_used" label="使用状態" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_used ? 'success' : 'warning'">
              {{ row.is_used ? '使用済み' : '未使用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewDetail(row)"> 詳細 </el-button>
            <el-button
              :type="row.is_used ? 'warning' : 'success'"
              size="small"
              @click="handleToggleUsage(row)"
            >
              {{ row.is_used ? '未使用マーク' : '使用済みマーク' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="材料在庫詳細" width="600px">
      <div v-if="currentRow" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ currentRow.id }}</el-descriptions-item>
          <el-descriptions-item label="材料名">{{ currentRow.material_name }}</el-descriptions-item>
          <el-descriptions-item label="製造番号">{{
            currentRow.manufacture_no
          }}</el-descriptions-item>
          <el-descriptions-item label="数量">{{ currentRow.quantity }}</el-descriptions-item>
          <el-descriptions-item label="ログ日付">{{ currentRow.log_date }}</el-descriptions-item>
          <el-descriptions-item label="仕入先">{{
            currentRow.supplier || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="材料品質">{{
            currentRow.material_quality || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="備考">{{ currentRow.note || '-' }}</el-descriptions-item>
          <el-descriptions-item label="使用状態">
            <el-tag :type="currentRow.is_used ? 'success' : 'warning'">
              {{ currentRow.is_used ? '使用済み' : '未使用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="作成日時">{{ currentRow.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新日時">{{ currentRow.updated_at }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">閉じる</el-button>
        <el-button type="primary" @click="handleToggleUsage(currentRow)">
          {{ currentRow?.is_used ? '未使用マーク' : '使用済みマーク' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Box, Refresh, Search, Check, Clock, Document } from '@element-plus/icons-vue'
import {
  getStockMaterialsList,
  getStockMaterialsSummary,
  getSupplierList,
  toggleStockMaterialUsage,
} from '@/api/material'

// 响应式数据
const loading = ref(false)
const migrating = ref(false)
const tableData = ref([])
const detailDialogVisible = ref(false)
const currentRow = ref(null)

// 统计数据
const stats = ref({
  total_count: 0,
  unique_materials: 0,
  leftover_materials: 0,
  unique_suppliers: 0,
  total_quantity: 0,
  used_quantity: 0,
  unused_quantity: 0,
})

// 搜索表单
const searchForm = reactive({
  keyword: '',
  start_date: '',
  end_date: '',
  supplier: '',
  is_used: '',
  dateRange: [],
})

// 分页数据
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// 选项数据
const supplierOptions = ref([])

// 排序数据
const sortField = ref('')
const sortOrder = ref('')

// 计算属性（如果有其他计算属性，可以在这里添加）

// 方法
const fetchData = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      pageSize: pagination.page_size,
      sortBy: sortField.value || undefined,
      sortOrder: sortField.value ? sortOrder.value : undefined,
      keyword: searchForm.keyword || undefined,
      startDate: searchForm.start_date || undefined,
      endDate: searchForm.end_date || undefined,
      supplier: searchForm.supplier || undefined,
      is_used: searchForm.is_used || undefined,
    }
    Object.keys(params).forEach((key) => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) delete params[key]
    })

    const result = await getStockMaterialsList(params)
    const data = result?.data
    tableData.value = data?.list ?? []
    pagination.total = data?.total ?? 0
  } catch (error) {
    console.error('データ取得に失敗しました:', error)
    ElMessage.error('データ取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const result = await getStockMaterialsSummary()
    const d = result?.data
    if (d) {
      stats.value.total_count = d.total ?? 0
      stats.value.used_quantity = d.used ?? 0
      stats.value.unused_quantity = d.unused ?? 0
      stats.value.total_quantity = d.total_quantity ?? 0
      stats.value.unique_materials = d.total ?? 0
      stats.value.unique_suppliers = 0
      stats.value.leftover_materials = d.unused ?? 0
    }
  } catch (error) {
    console.error('統計情報の取得に失敗しました:', error)
  }
}

const fetchSupplierOptions = async () => {
  try {
    const result = await getSupplierList()
    supplierOptions.value = result?.data ?? []
  } catch (error) {
    console.error('仕入先オプションの取得に失敗しました:', error)
    supplierOptions.value = []
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
  fetchStats() // 搜索时也更新统计数据
}

const handleReset = () => {
  Object.keys(searchForm).forEach((key) => {
    if (key === 'dateRange') {
      searchForm[key] = []
    } else {
      searchForm[key] = ''
    }
  })
  // 重置排序
  sortField.value = ''
  sortOrder.value = ''
  pagination.page = 1
  fetchData()
  fetchStats() // 重置时也更新统计数据
}

const handleDateRangeChange = (value) => {
  if (value && value.length === 2) {
    searchForm.start_date = value[0]
    searchForm.end_date = value[1]
  } else {
    searchForm.start_date = ''
    searchForm.end_date = ''
  }
  // 日期范围改变时自动更新统计数据
  fetchStats()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleViewDetail = (row) => {
  currentRow.value = row
  detailDialogVisible.value = true
}

const handleToggleUsage = async (row) => {
  try {
    await toggleStockMaterialUsage(row.id)
    ElMessage.success('使用状態の更新に成功しました')
    row.is_used = !row.is_used
    fetchStats()
    detailDialogVisible.value = false
  } catch (error) {
    console.error('使用状態の更新に失敗しました:', error)
    ElMessage.error('更新に失敗しました')
  }
}

const handleMigrate = async () => {
  try {
    await ElMessageBox.confirm(
      '新しいデータを追加しますか？material_logsテーブルから、まだstock_materialsテーブルに存在しない新しいデータのみを追加します。',
      'データ追加確認',
      { type: 'info' },
    )
    migrating.value = true
    ElMessage.info('データ移行機能は現在未実装です。')
    fetchData()
    fetchStats()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('データ追加に失敗しました')
  } finally {
    migrating.value = false
  }
}

const handleRefresh = () => {
  fetchData()
  fetchStats()
}

// 处理表格排序
const handleSortChange = ({ prop, order }) => {
  if (prop) {
    sortField.value = prop
    sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  } else {
    sortField.value = ''
    sortOrder.value = ''
  }
  pagination.page = 1
  fetchData()
}

// 生命周期
onMounted(() => {
  fetchData()
  fetchStats()
  fetchSupplierOptions()
})
</script>

<style scoped>
.stock-materials-management {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  position: relative;
  overflow: hidden;
}

.header-content {
  flex: 1;
}

.main-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 32px;
}

.subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-container {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.materials {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.used {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.unused {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.search-card {
  margin-bottom: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.search-form {
  margin: 0;
}

.table-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.detail-content {
  padding: 20px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }

  .search-form {
    flex-direction: column;
  }

  .search-form .el-form-item {
    width: 100%;
  }
}
</style>
