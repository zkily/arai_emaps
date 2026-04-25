<template>
  <div class="sales-page-shell sales-order-list">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.orderList.title') }}</h1>
          <p class="sales-page-hero__subtitle">
            {{ t('salesPages.common.recordCount', { n: pagination.total }) }}
          </p>
        </div>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="createOrder">
          <el-icon><Plus /></el-icon>
          {{ t('salesPages.orderList.newOrder') }}
        </el-button>
        <el-button @click="exportData">
          <el-icon><Download /></el-icon>
          {{ t('salesPages.orderList.export') }}
        </el-button>
      </div>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item :label="t('salesPages.orderList.filterOrderNo')">
          <el-input v-model="filters.order_no" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item :label="t('salesPages.common.customer')">
          <el-select
            v-model="filters.customer_code"
            :placeholder="t('salesPages.common.selectCustomer')"
            clearable
            filterable
          >
            <el-option v-for="c in customerOptions" :key="c.code" :label="c.name" :value="c.code" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.orderList.filterStatus')">
          <el-select v-model="filters.status" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.orderList.statusDraft')" value="draft" />
            <el-option :label="t('salesPages.orderList.statusPending')" value="pending" />
            <el-option :label="t('salesPages.orderList.statusApproved')" value="approved" />
            <el-option :label="t('salesPages.orderList.statusPartial')" value="partial_delivered" />
            <el-option :label="t('salesPages.orderList.statusCompleted')" value="completed" />
            <el-option :label="t('salesPages.orderList.statusCancelled')" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.orderList.filterOrderDate')">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            :range-separator="t('salesPages.common.rangeSep')"
            :start-placeholder="t('salesPages.common.startDate')"
            :end-placeholder="t('salesPages.common.endDate')"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            {{ t('salesPages.common.search') }}
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            {{ t('salesPages.common.reset') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card" shadow="never">
      <el-table :data="orders" v-loading="loading" stripe border>
        <el-table-column prop="order_no" :label="t('salesPages.common.orderNo')" width="140">
          <template #default="{ row }">
            <span class="link-text" @click="viewOrder(row)">{{ row.order_no }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="customer_name"
          :label="t('salesPages.common.customer')"
          min-width="150"
        />
        <el-table-column
          prop="order_date"
          :label="t('salesPages.orderList.colOrderDate')"
          width="110"
        />
        <el-table-column
          prop="expected_delivery_date"
          :label="t('salesPages.orderList.colShipDue')"
          width="110"
        />
        <el-table-column
          prop="status_name"
          :label="t('salesPages.orderList.colStatus')"
          width="100"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ row.status_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="total_amount"
          :label="t('salesPages.orderList.colOrderAmount')"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            ¥{{ formatDecimal(row.total_amount ?? 0, locale as LocaleType, 0) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="payment_status_name"
          :label="t('salesPages.orderList.colPayment')"
          width="100"
        >
          <template #default="{ row }">
            <el-tag :type="getPaymentStatusType(row.payment_status)" size="small">
              {{ row.payment_status_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="sales_person"
          :label="t('salesPages.orderList.colSalesPerson')"
          width="100"
        />
        <el-table-column
          :label="t('salesPages.common.actions')"
          width="220"
          fixed="right"
          align="center"
        >
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewOrder(row)">
              {{ t('salesPages.common.detail') }}
            </el-button>
            <el-button
              size="small"
              type="warning"
              link
              @click="editOrder(row)"
              v-if="row.status === 'draft'"
            >
              {{ t('salesPages.orderList.edit') }}
            </el-button>
            <el-button
              size="small"
              type="success"
              link
              @click="deliverOrder(row)"
              v-if="row.status === 'approved'"
            >
              {{ t('salesPages.salesHome.ship') }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              link
              @click="cancelOrder(row)"
              v-if="['draft', 'pending'].includes(row.status)"
            >
              {{ t('salesPages.orderList.cancel') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
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
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Plus, Download, Search, Refresh } from '@element-plus/icons-vue'
import { getSalesOrderList, cancelSalesOrder } from '@/api/erp/sales'
import type { SalesOrder } from '@/types/erp/sales'
import type { LocaleType } from '@/i18n'
import type { ElTagType } from '@/types/elementPlus'
import { formatDecimal } from '@/utils/formatInteger'

const router = useRouter()
const { t, locale } = useI18n()
const loading = ref(false)
const orders = ref<SalesOrder[]>([])
const customerOptions = ref<Array<{ code: string; name: string }>>([])

const filters = reactive({
  order_no: '',
  customer_code: '',
  status: '',
  dateRange: [] as string[],
})

const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0,
})

const getStatusType = (status: string): ElTagType => {
  const typeMap: Record<string, ElTagType> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    partial_delivered: 'primary',
    completed: 'success',
    cancelled: 'danger',
  }
  return typeMap[status] || 'info'
}

const getPaymentStatusType = (status: string): ElTagType => {
  const typeMap: Record<string, ElTagType> = {
    unpaid: 'danger',
    partial_paid: 'warning',
    paid: 'success',
  }
  return typeMap[status] || 'info'
}

const createOrder = () => {
  router.push('/erp/sales/orders/new')
}

const viewOrder = (row: SalesOrder) => {
  router.push(`/erp/sales/orders/${row.id}`)
}

const editOrder = (row: SalesOrder) => {
  router.push(`/erp/sales/orders/${row.id}/edit`)
}

const deliverOrder = (row: SalesOrder) => {
  router.push(`/erp/sales/deliveries/new?order_id=${row.id}`)
}

const cancelOrder = async (row: SalesOrder) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      t('salesPages.salesHome.cancelPromptLabel'),
      t('salesPages.salesHome.cancelPromptTitle'),
      {
        confirmButtonText: t('salesPages.common.confirm'),
        cancelButtonText: t('salesPages.common.cancel'),
        inputPattern: /\S+/,
        inputErrorMessage: t('salesPages.salesHome.cancelReasonRequired'),
      },
    )
    await cancelSalesOrder(row.id, reason)
    ElMessage.success(t('salesPages.salesHome.cancelOk'))
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('salesPages.salesHome.cancelFail'))
    }
  }
}

const exportData = () => {
  ElMessage.info(t('salesPages.salesHome.exportWip'))
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const resetFilters = () => {
  filters.order_no = ''
  filters.customer_code = ''
  filters.status = ''
  filters.dateRange = []
  pagination.page = 1
  fetchData()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchData()
}

const handleCurrentChange = () => {
  fetchData()
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      order_no: filters.order_no || undefined,
      customer_code: filters.customer_code || undefined,
      status: filters.status || undefined,
      start_date: filters.dateRange?.[0] || undefined,
      end_date: filters.dateRange?.[1] || undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    const res = await getSalesOrderList(params)
    const body = res as { items?: SalesOrder[]; total?: number }
    orders.value = body.items ?? []
    pagination.total = body.total ?? 0
  } catch (error) {
    console.error(t('salesPages.common.loadFailed'), error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped src="@/views/erp/sales/sales-page-shell.scss"></style>

<style scoped>
.sales-order-list .sales-page-hero {
  flex-wrap: wrap;
}

.hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-card {
  margin-bottom: 12px;
}

.filter-card :deep(.el-card__body) {
  padding: 16px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.table-card :deep(.el-card__body) {
  padding: 16px;
}

.link-text {
  color: #409eff;
  cursor: pointer;
}

.link-text:hover {
  text-decoration: underline;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
