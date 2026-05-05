<template>
  <div class="shipping-page">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <!-- Header -->
    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon :size="26"><Van /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">出荷指示</h1>
            <span class="header-subtitle">Shipping Instructions</span>
          </div>
        </div>
        <div class="header-badges">
          <el-badge :value="totalCount" type="primary" class="header-badge">
            <el-tag effect="dark" round size="small">全件</el-tag>
          </el-badge>
          <el-badge :value="pendingCount" type="warning" class="header-badge">
            <el-tag effect="dark" round size="small">未確定</el-tag>
          </el-badge>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="glass-card filter-section animate-in" style="animation-delay:0.08s">
      <el-form :inline="true" class="filter-form" @submit.prevent="fetchData">
        <el-form-item>
          <el-input
            v-model="filters.delivery_no"
            placeholder="出荷番号で検索"
            clearable
            prefix-icon="Search"
            class="glass-input"
            @clear="fetchData"
            @keyup.enter="fetchData"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="filters.customer"
            placeholder="顧客名"
            clearable
            class="glass-input"
            @clear="fetchData"
          />
        </el-form-item>
        <el-form-item>
          <el-select
            v-model="filters.status"
            placeholder="ステータス"
            clearable
            class="glass-select"
            @change="fetchData"
          >
            <el-option label="下書き" value="draft" />
            <el-option label="確定済" value="confirmed" />
            <el-option label="出荷済" value="shipped" />
            <el-option label="完了" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="~"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            class="glass-date"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData" :icon="Search" class="action-btn">検索</el-button>
          <el-button @click="resetFilters" :icon="RefreshLeft" class="action-btn-outline">リセット</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Toolbar -->
    <div class="glass-card toolbar-section animate-in" style="animation-delay:0.12s">
      <el-button type="primary" @click="showCreateDialog = true" :icon="Plus" class="create-btn">
        新規出荷指示
      </el-button>
      <el-button @click="fetchData" :icon="Refresh" circle class="refresh-btn" />
    </div>

    <!-- Table -->
    <div class="glass-card table-section animate-in" style="animation-delay:0.16s">
      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        class="dark-table"
        :header-cell-style="headerStyle"
        :row-class-name="tableRowClass"
        empty-text="データがありません"
      >
        <el-table-column prop="delivery_no" label="出荷番号" min-width="130">
          <template #default="{ row }">
            <span class="mono-text">{{ row.delivery_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="order_no" label="受注番号" min-width="120">
          <template #default="{ row }">
            <span class="mono-text">{{ row.order_no || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="顧客名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="delivery_date" label="出荷日" min-width="110" />
        <el-table-column prop="warehouse" label="倉庫" min-width="90" />
        <el-table-column prop="quantity" label="数量" min-width="80" align="right">
          <template #default="{ row }">
            <span class="number-text">{{ row.quantity?.toLocaleString() || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" effect="dark" round size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="アクション" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'draft'"
              type="warning"
              size="small"
              text
              @click="handleConfirm(row)"
              :loading="row._confirming"
            >確定</el-button>
            <el-button type="primary" size="small" text @click="handleDetail(row)">詳細</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- Create Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="新規出荷指示"
      width="680px"
      class="glass-dialog"
      destroy-on-close
    >
      <el-form :model="createForm" label-width="100px" class="create-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="受注番号">
              <el-input v-model="createForm.order_no" placeholder="受注番号を入力" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="顧客">
              <el-input v-model="createForm.customer_name" placeholder="顧客名" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="倉庫">
              <el-input v-model="createForm.warehouse" placeholder="倉庫を指定" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出荷日">
              <el-date-picker
                v-model="createForm.delivery_date"
                type="date"
                placeholder="日付を選択"
                value-format="YYYY-MM-DD"
                style="width:100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">出荷明細</el-divider>

        <div class="items-table">
          <el-table :data="createForm.items" size="small" class="dark-table inner-table">
            <el-table-column label="品番" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.product_code" size="small" placeholder="品番" />
              </template>
            </el-table-column>
            <el-table-column label="品名" min-width="140">
              <template #default="{ row }">
                <el-input v-model="row.product_name" size="small" placeholder="品名" />
              </template>
            </el-table-column>
            <el-table-column label="数量" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" size="small" :min="1" controls-position="right" />
              </template>
            </el-table-column>
            <el-table-column width="60" align="center">
              <template #default="{ $index }">
                <el-button type="danger" size="small" text :icon="Delete" @click="removeItem($index)" />
              </template>
            </el-table-column>
          </el-table>
          <el-button type="primary" text size="small" :icon="Plus" @click="addItem" class="add-item-btn">
            明細追加
          </el-button>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">キャンセル</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">作成</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="showDetailDialog"
      title="出荷指示 詳細"
      width="600px"
      class="glass-dialog"
      destroy-on-close
    >
      <el-descriptions :column="2" border size="small" v-if="detailData">
        <el-descriptions-item label="出荷番号">{{ detailData.delivery_no }}</el-descriptions-item>
        <el-descriptions-item label="受注番号">{{ detailData.order_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="顧客名">{{ detailData.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="出荷日">{{ detailData.delivery_date }}</el-descriptions-item>
        <el-descriptions-item label="倉庫">{{ detailData.warehouse || '-' }}</el-descriptions-item>
        <el-descriptions-item label="数量">{{ detailData.quantity }}</el-descriptions-item>
        <el-descriptions-item label="ステータス">
          <el-tag :type="statusType(detailData.status)" effect="dark" size="small">
            {{ statusLabel(detailData.status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showDetailDialog = false">閉じる</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Van, Search, RefreshLeft, Plus, Refresh, Delete } from '@element-plus/icons-vue'
import { getDeliveries, createDelivery, confirmDelivery } from '@/api/erp/sales'

const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const detailData = ref<any>(null)
const tableData = ref<any[]>([])

const filters = reactive({
  delivery_no: '',
  customer: '',
  status: '',
  dateRange: null as [string, string] | null,
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const createForm = reactive({
  order_no: '',
  customer_name: '',
  warehouse: '',
  delivery_date: '',
  items: [{ product_code: '', product_name: '', quantity: 1 }] as Array<{
    product_code: string
    product_name: string
    quantity: number
  }>,
})

const totalCount = computed(() => pagination.total)
const pendingCount = computed(() => tableData.value.filter(r => r.status === 'draft').length)

const headerStyle = {
  background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))',
  color: 'rgba(255,255,255,0.9)',
  borderBottom: '1px solid rgba(255,255,255,0.08)',
  fontSize: '12px',
  fontWeight: '600',
  padding: '8px 12px',
}

function tableRowClass({ rowIndex }: { rowIndex: number }) {
  return rowIndex % 2 === 0 ? 'row-even' : 'row-odd'
}

function statusType(status: string) {
  const map: Record<string, string> = {
    draft: 'info',
    confirmed: 'warning',
    shipped: '',
    completed: 'success',
  }
  return map[status] || 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    draft: '下書き',
    confirmed: '確定済',
    shipped: '出荷済',
    completed: '完了',
  }
  return map[status] || status
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.delivery_no) params.delivery_no = filters.delivery_no
    if (filters.customer) params.customer = filters.customer
    if (filters.status) params.status = filters.status
    if (filters.dateRange) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    const res: any = await getDeliveries(params)
    const data = res?.data ?? res
    tableData.value = data?.items || data?.list || data || []
    pagination.total = data?.total || tableData.value.length
  } catch (e: any) {
    console.error('Failed to fetch deliveries', e)
    tableData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.delivery_no = ''
  filters.customer = ''
  filters.status = ''
  filters.dateRange = null
  pagination.page = 1
  fetchData()
}

async function handleConfirm(row: any) {
  try {
    await ElMessageBox.confirm('この出荷指示を確定しますか？', '確認', { type: 'warning' })
    row._confirming = true
    await confirmDelivery(row.id)
    ElMessage.success('確定しました')
    fetchData()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('確定に失敗しました')
    }
  } finally {
    row._confirming = false
  }
}

function handleDetail(row: any) {
  detailData.value = row
  showDetailDialog.value = true
}

function addItem() {
  createForm.items.push({ product_code: '', product_name: '', quantity: 1 })
}

function removeItem(index: number) {
  if (createForm.items.length > 1) {
    createForm.items.splice(index, 1)
  }
}

async function handleCreate() {
  if (!createForm.delivery_date) {
    ElMessage.warning('出荷日を選択してください')
    return
  }
  creating.value = true
  try {
    await createDelivery({
      order_no: createForm.order_no,
      customer_name: createForm.customer_name,
      warehouse: createForm.warehouse,
      delivery_date: createForm.delivery_date,
      items: createForm.items.filter(i => i.product_code),
    })
    ElMessage.success('出荷指示を作成しました')
    showCreateDialog.value = false
    createForm.order_no = ''
    createForm.customer_name = ''
    createForm.warehouse = ''
    createForm.delivery_date = ''
    createForm.items = [{ product_code: '', product_name: '', quantity: 1 }]
    fetchData()
  } catch (e: any) {
    ElMessage.error('作成に失敗しました')
  } finally {
    creating.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.shipping-page {
  position: relative;
  min-height: 100vh;
  padding: 16px;
  overflow-x: hidden;
}

.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: float 20s ease-in-out infinite;
}
.orb-1 { width: 380px; height: 380px; top: -80px; left: -80px; background: radial-gradient(circle, #3b82f6, transparent); }
.orb-2 { width: 320px; height: 320px; top: 50%; right: -60px; background: radial-gradient(circle, #8b5cf6, transparent); animation-delay: -7s; }
.orb-3 { width: 280px; height: 280px; bottom: -40px; left: 40%; background: radial-gradient(circle, #ec4899, transparent); animation-delay: -14s; }
.noise-overlay {
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.glass-header {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 14px 20px;
  margin-bottom: 12px;
}
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #ec4899, #db2777);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 16px rgba(236, 72, 153, 0.4);
}
.header-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}
.header-subtitle {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.55);
}
.header-badges {
  display: flex;
  gap: 12px;
}
.header-badge :deep(.el-tag) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.glass-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 14px 18px;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.filter-section .filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.filter-section :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}
.filter-section :deep(.el-input__wrapper),
.filter-section :deep(.el-select .el-input__wrapper),
.filter-section :deep(.el-date-editor .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  box-shadow: none;
  color: #fff;
}
.filter-section :deep(.el-input__inner) {
  color: rgba(255, 255, 255, 0.9);
}
.filter-section :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.4);
}
.filter-section :deep(.el-range-input) {
  color: rgba(255, 255, 255, 0.9);
  background: transparent;
}
.filter-section :deep(.el-range-separator) {
  color: rgba(255, 255, 255, 0.5);
}

.action-btn {
  border-radius: 8px;
  font-weight: 500;
}
.action-btn-outline {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
}
.action-btn-outline:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
}

.toolbar-section {
  display: flex;
  align-items: center;
  gap: 8px;
}
.create-btn {
  border-radius: 8px;
  font-weight: 600;
}
.refresh-btn {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: rgba(255, 255, 255, 0.7) !important;
}
.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.12) !important;
  color: #fff !important;
}

.table-section {
  padding: 0;
  overflow: hidden;
}
.table-section :deep(.el-table) {
  background: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-text-color: rgba(255, 255, 255, 0.85);
  --el-table-header-text-color: rgba(255, 255, 255, 0.9);
  color: rgba(255, 255, 255, 0.85);
}
.table-section :deep(.el-table__body-wrapper) {
  background: transparent;
}
.table-section :deep(.el-table__row) {
  transition: background 0.2s;
}
.table-section :deep(.el-table__row.row-even td) {
  background: rgba(255, 255, 255, 0.02);
}
.table-section :deep(.el-table__row.row-odd td) {
  background: transparent;
}
.table-section :deep(.el-table__row:hover td) {
  background: rgba(59, 130, 246, 0.06) !important;
}
.table-section :deep(.el-table td),
.table-section :deep(.el-table th) {
  border-color: rgba(255, 255, 255, 0.06);
  padding: 8px 12px;
}
.table-section :deep(.el-table__empty-text) {
  color: rgba(255, 255, 255, 0.45);
}

.mono-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.9);
}
.number-text {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  color: #60a5fa;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.pagination-wrap :deep(.el-pagination) {
  --el-pagination-bg-color: rgba(255, 255, 255, 0.06);
  --el-pagination-text-color: rgba(255, 255, 255, 0.7);
  --el-pagination-button-disabled-color: rgba(255, 255, 255, 0.3);
}
.pagination-wrap :deep(.el-pagination .btn-prev),
.pagination-wrap :deep(.el-pagination .btn-next),
.pagination-wrap :deep(.el-pager li) {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
}
.pagination-wrap :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #fff;
}

.glass-dialog :deep(.el-dialog) {
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}
.glass-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 16px 20px;
}
.glass-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 600;
}
.glass-dialog :deep(.el-dialog__body) {
  padding: 20px;
  color: rgba(255, 255, 255, 0.85);
}
.glass-dialog :deep(.el-dialog__footer) {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 12px 20px;
}
.glass-dialog :deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.7);
}
.glass-dialog :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  box-shadow: none;
}
.glass-dialog :deep(.el-input__inner) {
  color: rgba(255, 255, 255, 0.9);
}
.glass-dialog :deep(.el-divider__text) {
  background: rgba(15, 23, 42, 0.95);
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
}
.glass-dialog :deep(.el-divider) {
  border-color: rgba(255, 255, 255, 0.08);
}
.glass-dialog :deep(.el-descriptions__label) {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.6);
}
.glass-dialog :deep(.el-descriptions__content) {
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
}
.glass-dialog :deep(.el-descriptions__cell) {
  border-color: rgba(255, 255, 255, 0.08);
}

.inner-table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
}

.add-item-btn {
  margin-top: 8px;
}

.animate-in {
  animation: slideIn 0.5s ease forwards;
  opacity: 0;
  transform: translateY(12px);
}
@keyframes slideIn {
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .shipping-page { padding: 10px; }
  .header-badges { display: none; }
  .filter-section .filter-form { flex-direction: column; align-items: stretch; }
  .filter-section :deep(.el-form-item) { width: 100%; }
}
</style>
