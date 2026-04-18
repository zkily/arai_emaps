<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><EditPen /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.returnCorrection.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.returnCorrection.subtitle') }}</p>
        </div>
      </div>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="t('salesPages.common.slipNo')">
          <el-input v-model="filters.slip_no" clearable />
        </el-form-item>
        <el-form-item :label="t('salesPages.common.customer')">
          <el-select v-model="filters.customer_code" :placeholder="t('salesPages.common.selectCustomer')" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.returnCorrection.kind')">
          <el-select v-model="filters.type" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.returnCorrection.typeReturn')" value="return" />
            <el-option :label="t('salesPages.returnCorrection.typeDiscount')" value="discount" />
            <el-option :label="t('salesPages.returnCorrection.typeQty')" value="qty_correction" />
            <el-option :label="t('salesPages.returnCorrection.typePrice')" value="price_correction" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.common.status')">
          <el-select v-model="filters.status" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.returnCorrection.statusPending')" value="pending" />
            <el-option :label="t('salesPages.returnCorrection.statusApproved')" value="approved" />
            <el-option :label="t('salesPages.returnCorrection.statusProcessed')" value="processed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            {{ t('salesPages.common.search') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="sales-page-toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        {{ t('salesPages.returnCorrection.newSlip') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="correctionList" v-loading="loading" stripe border>
        <el-table-column prop="correction_no" :label="t('salesPages.returnCorrection.colCorrectionNo')" width="130" fixed />
        <el-table-column prop="original_slip_no" :label="t('salesPages.returnCorrection.colOriginalSlip')" width="130" />
        <el-table-column prop="correction_type" :label="t('salesPages.returnCorrection.colCorrectionType')" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.correction_type === 'return' ? 'danger' : 'warning'" size="small">
              {{ correctionTypeLabel(String(row.correction_type)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" :label="t('salesPages.credit.colCustomerName')" min-width="130" />
        <el-table-column prop="product_code" :label="t('salesPages.common.productCode')" width="120" />
        <el-table-column prop="original_amount" :label="t('salesPages.returnCorrection.colOriginalAmt')" width="110" align="right">
          <template #default="{ row }">¥{{ formatDecimal(row.original_amount ?? 0, locale as LocaleType, 0) }}</template>
        </el-table-column>
        <el-table-column prop="correction_amount" :label="t('salesPages.returnCorrection.colCorrectionAmt')" width="110" align="right">
          <template #default="{ row }">
            <span class="text-amount-danger">¥{{ formatDecimal(row.correction_amount ?? 0, locale as LocaleType, 0) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('salesPages.common.status')" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(String(row.status))">{{ getStatusLabel(String(row.status)) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="t('salesPages.returnCorrection.colCreated')" width="110" />
        <el-table-column :label="t('salesPages.common.actions')" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">{{ t('salesPages.common.detail') }}</el-button>
            <el-button size="small" type="success" link @click="handleApprove(row)" v-if="row.status === 'pending'">
              {{ t('salesPages.returnCorrection.approve') }}
            </el-button>
            <el-button size="small" type="warning" link @click="handleProcess(row)" v-if="row.status === 'approved'">
              {{ t('salesPages.returnCorrection.process') }}
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
          layout="total, sizes, prev, pager, next"
          background
          @size-change="onPageSize"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Search, Plus, EditPen } from '@element-plus/icons-vue'
import type { LocaleType } from '@/i18n'
import { formatDecimal } from '@/utils/formatInteger'

const { t, locale } = useI18n()
const loading = ref(false)
const correctionList = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ slip_no: '', customer_code: '', type: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const typeKeys: Record<string, string> = {
  return: 'salesPages.returnCorrection.typeReturn',
  discount: 'salesPages.returnCorrection.typeDiscount',
  qty_correction: 'salesPages.returnCorrection.typeQty',
  price_correction: 'salesPages.returnCorrection.typePrice',
}

const statusLabelKeys: Record<string, string> = {
  pending: 'salesPages.returnCorrection.statusPending',
  approved: 'salesPages.returnCorrection.statusApproved',
  processed: 'salesPages.returnCorrection.statusProcessed',
}

const correctionTypeLabel = (type: string) => (typeKeys[type] ? t(typeKeys[type]) : type)

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    correctionList.value = []
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

const handleCreate = () => {
  ElMessage.info(t('salesPages.returnCorrection.createWip'))
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.returnCorrection.detailWip', { no: String(row.correction_no ?? '') }))
}

const handleApprove = (row: Record<string, unknown>) => {
  ElMessage.success(t('salesPages.returnCorrection.approveOk', { no: String(row.correction_no ?? '') }))
}

const handleProcess = (row: Record<string, unknown>) => {
  ElMessage.success(t('salesPages.returnCorrection.processOk', { no: String(row.correction_no ?? '') }))
}

const getStatusType = (s: string) => ({ pending: 'warning', approved: 'primary', processed: 'success' }[s] || 'info')
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
</style>
