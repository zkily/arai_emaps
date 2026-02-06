<template>
  <div class="inventory-list-page">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>

    <!-- 页面头部 -->
    <div class="modern-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32"><List /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">在庫一覧</h1>
            <div class="header-subtitle">{{ pagination.total }} 件</div>
          </div>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="showInboundDialog">
            <el-icon><Plus /></el-icon>入庫
          </el-button>
          <el-button type="warning" @click="showOutboundDialog">
            <el-icon><Minus /></el-icon>出庫
          </el-button>
          <el-button @click="exportData">
            <el-icon><Download /></el-icon>エクスポート
          </el-button>
        </div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section modern-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番を入力" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="品名">
          <el-input v-model="filters.product_name" placeholder="品名を入力" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="倉庫">
          <el-select v-model="filters.warehouse_code" placeholder="倉庫を選択" clearable>
            <el-option
              v-for="wh in warehouseOptions"
              :key="wh.code"
              :label="wh.name"
              :value="wh.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="在庫状態">
          <el-select v-model="filters.stock_status" placeholder="状態を選択" clearable>
            <el-option label="全て" value="" />
            <el-option label="在庫あり" value="has_stock" />
            <el-option label="在庫不足" value="low_stock" />
            <el-option label="在庫切れ" value="no_stock" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>検索
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>リセット
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格 -->
    <div class="table-section modern-card">
      <el-table
        :data="inventoryList"
        v-loading="loading"
        stripe
        border
        class="modern-table"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="product_code" label="品番" width="120" sortable="custom" fixed>
          <template #default="{ row }">
            <span class="link-text" @click="showDetail(row)">{{ row.product_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="品名" min-width="180" />
        <el-table-column prop="warehouse_name" label="倉庫" width="120" />
        <el-table-column prop="location" label="ロケーション" width="100" />
        <el-table-column prop="quantity" label="在庫数" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getStockClass(row)">{{ row.quantity?.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="available_quantity" label="利用可能数" width="100" align="right">
          <template #default="{ row }">
            {{ row.available_quantity?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="reserved_quantity" label="予約数" width="80" align="right">
          <template #default="{ row }">
            {{ row.reserved_quantity?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="単位" width="60" align="center" />
        <el-table-column prop="unit_cost" label="単価" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.unit_cost?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="total_cost" label="在庫金額" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.total_cost?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="min_stock_level" label="安全在庫" width="90" align="right" />
        <el-table-column label="状態" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStockStatusType(row)" size="small">
              {{ getStockStatusText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="showInboundDialog(row)">入庫</el-button>
            <el-button size="small" type="warning" @click="showOutboundDialog(row)">出庫</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 入库弹窗 -->
    <el-dialog v-model="inboundDialogVisible" title="入庫登録" width="500px">
      <el-form :model="inboundForm" :rules="inboundRules" ref="inboundFormRef" label-width="100px">
        <el-form-item label="品番" prop="product_code">
          <el-input v-model="inboundForm.product_code" placeholder="品番を入力" />
        </el-form-item>
        <el-form-item label="倉庫" prop="warehouse_code">
          <el-select v-model="inboundForm.warehouse_code" placeholder="倉庫を選択" style="width: 100%">
            <el-option v-for="wh in warehouseOptions" :key="wh.code" :label="wh.name" :value="wh.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="inboundForm.quantity" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="単価">
          <el-input-number v-model="inboundForm.unit_cost" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="参照番号">
          <el-input v-model="inboundForm.reference_no" placeholder="発注番号など" />
        </el-form-item>
        <el-form-item label="備考">
          <el-input v-model="inboundForm.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inboundDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="handleInbound" :loading="submitting">登録</el-button>
      </template>
    </el-dialog>

    <!-- 出库弹窗 -->
    <el-dialog v-model="outboundDialogVisible" title="出庫登録" width="500px">
      <el-form :model="outboundForm" :rules="outboundRules" ref="outboundFormRef" label-width="100px">
        <el-form-item label="品番" prop="product_code">
          <el-input v-model="outboundForm.product_code" placeholder="品番を入力" />
        </el-form-item>
        <el-form-item label="倉庫" prop="warehouse_code">
          <el-select v-model="outboundForm.warehouse_code" placeholder="倉庫を選択" style="width: 100%">
            <el-option v-for="wh in warehouseOptions" :key="wh.code" :label="wh.name" :value="wh.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="outboundForm.quantity" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="参照番号">
          <el-input v-model="outboundForm.reference_no" placeholder="受注番号など" />
        </el-form-item>
        <el-form-item label="備考">
          <el-input v-model="outboundForm.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="outboundDialogVisible = false">キャンセル</el-button>
        <el-button type="warning" @click="handleOutbound" :loading="submitting">登録</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { List, Plus, Minus, Download, Search, Refresh } from '@element-plus/icons-vue'
import { getInventoryList, createInboundTransaction, createOutboundTransaction } from '@/api/erp/inventory'
import { getWarehouseOptions } from '@/api/erp/master'
import type { Inventory } from '@/types/erp/inventory'
import type { FormInstance, FormRules } from 'element-plus'

// 状态
const loading = ref(false)
const submitting = ref(false)
const inventoryList = ref<Inventory[]>([])
const warehouseOptions = ref<Array<{ code: string; name: string }>>([])

// 筛选
const filters = reactive({
  product_code: '',
  product_name: '',
  warehouse_code: '',
  stock_status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0
})

// 入库表单
const inboundDialogVisible = ref(false)
const inboundFormRef = ref<FormInstance>()
const inboundForm = reactive({
  product_code: '',
  warehouse_code: '',
  quantity: 1,
  unit_cost: 0,
  reference_no: '',
  remarks: ''
})
const inboundRules: FormRules = {
  product_code: [{ required: true, message: '品番を入力してください', trigger: 'blur' }],
  warehouse_code: [{ required: true, message: '倉庫を選択してください', trigger: 'change' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }]
}

// 出库表单
const outboundDialogVisible = ref(false)
const outboundFormRef = ref<FormInstance>()
const outboundForm = reactive({
  product_code: '',
  warehouse_code: '',
  quantity: 1,
  reference_no: '',
  remarks: ''
})
const outboundRules: FormRules = {
  product_code: [{ required: true, message: '品番を入力してください', trigger: 'blur' }],
  warehouse_code: [{ required: true, message: '倉庫を選択してください', trigger: 'change' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }]
}

// 获取在庫状态样式
const getStockClass = (row: Inventory) => {
  if (row.quantity <= 0) return 'stock-empty'
  if (row.quantity < row.min_stock_level) return 'stock-low'
  return 'stock-normal'
}

const getStockStatusType = (row: Inventory) => {
  if (row.quantity <= 0) return 'danger'
  if (row.quantity < row.min_stock_level) return 'warning'
  return 'success'
}

const getStockStatusText = (row: Inventory) => {
  if (row.quantity <= 0) return '在庫切れ'
  if (row.quantity < row.min_stock_level) return '在庫不足'
  return '正常'
}

// 显示入库弹窗
const showInboundDialog = (row?: Inventory) => {
  if (row) {
    inboundForm.product_code = row.product_code
    inboundForm.warehouse_code = row.warehouse_code
  } else {
    inboundForm.product_code = ''
    inboundForm.warehouse_code = ''
  }
  inboundForm.quantity = 1
  inboundForm.unit_cost = 0
  inboundForm.reference_no = ''
  inboundForm.remarks = ''
  inboundDialogVisible.value = true
}

// 显示出库弹窗
const showOutboundDialog = (row?: Inventory) => {
  if (row) {
    outboundForm.product_code = row.product_code
    outboundForm.warehouse_code = row.warehouse_code
  } else {
    outboundForm.product_code = ''
    outboundForm.warehouse_code = ''
  }
  outboundForm.quantity = 1
  outboundForm.reference_no = ''
  outboundForm.remarks = ''
  outboundDialogVisible.value = true
}

// 处理入库
const handleInbound = async () => {
  if (!inboundFormRef.value) return
  await inboundFormRef.value.validate()
  
  submitting.value = true
  try {
    await createInboundTransaction(inboundForm)
    ElMessage.success('入庫登録が完了しました')
    inboundDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('入庫登録に失敗しました')
  } finally {
    submitting.value = false
  }
}

// 处理出库
const handleOutbound = async () => {
  if (!outboundFormRef.value) return
  await outboundFormRef.value.validate()
  
  submitting.value = true
  try {
    await createOutboundTransaction(outboundForm)
    ElMessage.success('出庫登録が完了しました')
    outboundDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('出庫登録に失敗しました')
  } finally {
    submitting.value = false
  }
}

// 显示详情
const showDetail = (row: Inventory) => {
  ElMessage.info(`在庫詳細: ${row.product_code}`)
}

// 导出
const exportData = () => {
  ElMessage.info('エクスポート機能は開発中です')
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

// 重置筛选
const resetFilters = () => {
  filters.product_code = ''
  filters.product_name = ''
  filters.warehouse_code = ''
  filters.stock_status = ''
  pagination.page = 1
  fetchData()
}

// 排序变化
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  console.log('Sort:', prop, order)
  fetchData()
}

// 分页变化
const handleSizeChange = () => {
  pagination.page = 1
  fetchData()
}

const handleCurrentChange = () => {
  fetchData()
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      ...filters,
      page: pagination.page,
      page_size: pagination.pageSize
    }
    const res = await getInventoryList(params)
    inventoryList.value = res.data?.items || res.items || []
    pagination.total = res.data?.total || res.total || 0
  } catch (error) {
    console.error('データ取得に失敗しました', error)
  } finally {
    loading.value = false
  }
}

// 获取仓库选项
const fetchWarehouseOptions = async () => {
  try {
    const res = await getWarehouseOptions()
    warehouseOptions.value = res.data || res || []
  } catch (error) {
    console.error('倉庫オプション取得に失敗しました', error)
  }
}

onMounted(() => {
  fetchData()
  fetchWarehouseOptions()
})
</script>

<style scoped>
.inventory-list-page {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  animation: float 20s ease-in-out infinite;
}

.orb-1 { width: 300px; height: 300px; top: -150px; right: -150px; }
.orb-2 { width: 200px; height: 200px; bottom: -100px; left: -100px; animation-delay: -10s; }

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-30px) rotate(180deg); }
}

.modern-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.header-title {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: #8492a6;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.modern-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.filter-section {
  padding: 20px;
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.table-section {
  padding: 20px;
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

.link-text {
  color: #409eff;
  cursor: pointer;
}

.link-text:hover {
  text-decoration: underline;
}

.stock-normal { color: #67c23a; font-weight: 600; }
.stock-low { color: #e6a23c; font-weight: 600; }
.stock-empty { color: #f56c6c; font-weight: 600; }

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
