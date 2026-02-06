<template>
  <div class="purchase-order-list">
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
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">発注一覧</h1>
            <div class="header-subtitle">{{ pagination.total }} 件</div>
          </div>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="createOrder">
            <el-icon><Plus /></el-icon>新規発注
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
        <el-form-item label="発注番号">
          <el-input v-model="filters.order_no" placeholder="発注番号" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="仕入先">
          <el-select v-model="filters.supplier_code" placeholder="仕入先を選択" clearable filterable>
            <el-option
              v-for="s in supplierOptions"
              :key="s.code"
              :label="s.name"
              :value="s.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="ステータス" clearable>
            <el-option label="下書き" value="draft" />
            <el-option label="承認待ち" value="pending" />
            <el-option label="承認済" value="approved" />
            <el-option label="一部入荷" value="partial_received" />
            <el-option label="完了" value="completed" />
            <el-option label="キャンセル" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="発注日">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
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
      <el-table :data="orders" v-loading="loading" stripe border class="modern-table">
        <el-table-column prop="order_no" label="発注番号" width="140">
          <template #default="{ row }">
            <span class="link-text" @click="viewOrder(row)">{{ row.order_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="仕入先" min-width="150" />
        <el-table-column prop="order_date" label="発注日" width="110" />
        <el-table-column prop="expected_delivery_date" label="入荷予定" width="110" />
        <el-table-column prop="status_name" label="ステータス" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ row.status_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="発注金額" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="payment_status_name" label="支払状況" width="100">
          <template #default="{ row }">
            <el-tag :type="getPaymentStatusType(row.payment_status)" size="small">
              {{ row.payment_status_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" label="担当者" width="100" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewOrder(row)">詳細</el-button>
            <el-button size="small" type="warning" link @click="editOrder(row)" v-if="row.status === 'draft'">編集</el-button>
            <el-button size="small" type="success" link @click="approveOrder(row)" v-if="row.status === 'pending'">承認</el-button>
            <el-button size="small" type="danger" link @click="cancelOrder(row)" v-if="['draft', 'pending'].includes(row.status)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Plus, Download, Search, Refresh } from '@element-plus/icons-vue'
import { getPurchaseOrderList, approvePurchaseOrder, cancelPurchaseOrder } from '@/api/erp/purchase'
import { getSupplierOptions } from '@/api/erp/supplier'
import type { PurchaseOrder } from '@/types/erp/purchase'

const router = useRouter()
const loading = ref(false)
const orders = ref<PurchaseOrder[]>([])
const supplierOptions = ref<Array<{ code: string; name: string }>>([])

const filters = reactive({
  order_no: '',
  supplier_code: '',
  status: '',
  dateRange: [] as string[]
})

const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0
})

// 获取状态标签类型
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    partial_received: 'primary',
    completed: '',
    cancelled: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取支付状态标签类型
const getPaymentStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    unpaid: 'danger',
    partial_paid: 'warning',
    paid: 'success'
  }
  return typeMap[status] || 'info'
}

// 创建订单
const createOrder = () => {
  router.push('/erp/purchase/orders/new')
}

// 查看订单
const viewOrder = (row: PurchaseOrder) => {
  router.push(`/erp/purchase/orders/${row.id}`)
}

// 编辑订单
const editOrder = (row: PurchaseOrder) => {
  router.push(`/erp/purchase/orders/${row.id}/edit`)
}

// 审批订单
const approveOrder = async (row: PurchaseOrder) => {
  try {
    await ElMessageBox.confirm('この発注を承認しますか？', '確認', { type: 'warning' })
    await approvePurchaseOrder(row.id, true)
    ElMessage.success('承認しました')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('承認に失敗しました')
    }
  }
}

// 取消订单
const cancelOrder = async (row: PurchaseOrder) => {
  try {
    const { value: reason } = await ElMessageBox.prompt('取消理由を入力してください', '発注取消', {
      confirmButtonText: '確認',
      cancelButtonText: 'キャンセル',
      inputPattern: /\S+/,
      inputErrorMessage: '理由を入力してください'
    })
    await cancelPurchaseOrder(row.id, reason)
    ElMessage.success('取消しました')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消に失敗しました')
    }
  }
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

// 重置
const resetFilters = () => {
  filters.order_no = ''
  filters.supplier_code = ''
  filters.status = ''
  filters.dateRange = []
  pagination.page = 1
  fetchData()
}

// 分页
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
      order_no: filters.order_no || undefined,
      supplier_code: filters.supplier_code || undefined,
      status: filters.status || undefined,
      start_date: filters.dateRange?.[0] || undefined,
      end_date: filters.dateRange?.[1] || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    }
    const res = await getPurchaseOrderList(params)
    orders.value = res.data?.items || res.items || []
    pagination.total = res.data?.total || res.total || 0
  } catch (error) {
    console.error('データ取得に失敗しました', error)
  } finally {
    loading.value = false
  }
}

// 获取供应商选项
const fetchSupplierOptions = async () => {
  try {
    const res = await getSupplierOptions()
    supplierOptions.value = res.data || res || []
  } catch (error) {
    console.error('仕入先オプション取得に失敗しました', error)
  }
}

onMounted(() => {
  fetchData()
  fetchSupplierOptions()
})
</script>

<style scoped>
.purchase-order-list {
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
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-30px); }
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

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
