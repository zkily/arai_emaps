<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><Van /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.shippingList.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.shippingList.subtitle') }}</p>
        </div>
      </div>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item :label="t('salesPages.shippingList.shipDate')">
          <el-date-picker v-model="filters.shipping_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="t('salesPages.common.customer')">
          <el-select
            v-model="filters.customer_code"
            :placeholder="t('salesPages.common.selectCustomer')"
            clearable
            filterable
          >
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.common.status')">
          <el-select v-model="filters.status" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.shippingList.statusPending')" value="pending" />
            <el-option :label="t('salesPages.shippingList.statusPicking')" value="picking" />
            <el-option :label="t('salesPages.shippingList.statusShipped')" value="shipped" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            {{ t('salesPages.common.search') }}
          </el-button>
          <el-button @click="handleReset">{{ t('salesPages.common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="sales-page-toolbar">
      <el-button type="primary" @click="handlePrintPickingList" :disabled="!hasSelection">
        <el-icon><Document /></el-icon>
        {{ t('salesPages.shippingList.pickingList') }}
      </el-button>
      <el-button type="success" @click="handlePrintShippingOrder" :disabled="!hasSelection">
        <el-icon><Tickets /></el-icon>
        {{ t('salesPages.shippingList.shipOrder') }}
      </el-button>
      <el-button @click="handleExportInvoiceData" :disabled="!hasSelection">
        <el-icon><Download /></el-icon>
        {{ t('salesPages.shippingList.waybillExport') }}
      </el-button>
      <el-divider direction="vertical" />
      <el-button type="warning" @click="handleBatchShip" :disabled="!hasSelection">
        <el-icon><Van /></el-icon>
        {{ t('salesPages.shippingList.batchShip') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table
        :data="shippingList"
        v-loading="loading"
        stripe
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" fixed />
        <el-table-column
          prop="order_no"
          :label="t('salesPages.common.orderNo')"
          width="130"
          fixed
        />
        <el-table-column
          prop="shipping_date"
          :label="t('salesPages.shippingList.shipDate')"
          width="110"
        />
        <el-table-column
          prop="customer_name"
          :label="t('salesPages.credit.colCustomerName')"
          min-width="150"
        />
        <el-table-column
          prop="destination_name"
          :label="t('salesPages.shippingList.colDest')"
          min-width="150"
        />
        <el-table-column
          prop="product_code"
          :label="t('salesPages.common.productCode')"
          width="120"
        />
        <el-table-column
          prop="product_name"
          :label="t('salesPages.contractPricing.productName')"
          min-width="150"
          show-overflow-tooltip
        />
        <el-table-column
          prop="quantity"
          :label="t('salesPages.shippingList.colQty')"
          width="90"
          align="right"
        />
        <el-table-column prop="location" :label="t('salesPages.shippingList.colLoc')" width="120" />
        <el-table-column
          prop="carrier"
          :label="t('salesPages.shippingList.colCarrier')"
          width="100"
        />
        <el-table-column
          prop="status"
          :label="t('salesPages.common.status')"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusType(String(row.status))">
              {{ getStatusLabel(String(row.status)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('salesPages.common.actions')" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">
              {{ t('salesPages.common.detail') }}
            </el-button>
            <el-button
              size="small"
              type="success"
              link
              @click="handleShip(row)"
              v-if="row.status !== 'shipped'"
            >
              {{ t('salesPages.shippingList.ship') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="sales-page-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="onPageSize"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Document, Tickets, Download, Van } from '@element-plus/icons-vue'
import type { ElTagType } from '@/types/elementPlus'

const { t } = useI18n()
const loading = ref(false)
const shippingList = ref<Record<string, unknown>[]>([])
const selectedRows = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])

const filters = reactive({
  shipping_date: '',
  customer_code: '',
  status: '',
})

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)

const statusTypeMap: Record<string, ElTagType> = {
  pending: 'warning',
  picking: 'info',
  shipped: 'success',
}
const statusLabelKeys: Record<string, string> = {
  pending: 'salesPages.shippingList.statusPending',
  picking: 'salesPages.shippingList.statusPicking',
  shipped: 'salesPages.shippingList.statusShipped',
}

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    shippingList.value = []
  } finally {
    loading.value = false
  }
}

const onPageSize = () => {
  pagination.page = 1
  loadData()
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(filters, { shipping_date: '', customer_code: '', status: '' })
  handleSearch()
}

const handleSelectionChange = (rows: Record<string, unknown>[]) => {
  selectedRows.value = rows
}

const handlePrintPickingList = () => {
  ElMessage.info(t('salesPages.shippingList.pickingWip', { n: selectedRows.value.length }))
}

const handlePrintShippingOrder = () => {
  ElMessage.info(t('salesPages.shippingList.orderWip', { n: selectedRows.value.length }))
}

const handleExportInvoiceData = () => {
  ElMessage.success(t('salesPages.shippingList.waybillOk'))
}

const handleBatchShip = async () => {
  await ElMessageBox.confirm(
    t('salesPages.shippingList.batchShipConfirm', { n: selectedRows.value.length }),
    t('salesPages.common.confirmTitle'),
  )
  ElMessage.success(t('salesPages.shippingList.batchShipOk'))
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.shippingList.detailWip', { no: String(row.order_no ?? '') }))
}

const handleShip = (row: Record<string, unknown>) => {
  ElMessage.success(t('salesPages.shippingList.shipOk', { no: String(row.order_no ?? '') }))
}

const getStatusType = (s: string): ElTagType => statusTypeMap[s] || 'info'
const getStatusLabel = (s: string) => (statusLabelKeys[s] ? t(statusLabelKeys[s]) : s)
</script>

<style scoped src="@/views/erp/sales/sales-page-shell.scss"></style>

<style scoped>
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
</style>
