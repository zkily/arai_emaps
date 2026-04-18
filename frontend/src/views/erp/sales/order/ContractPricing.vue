<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><Tickets /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.contractPricing.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.contractPricing.subtitle') }}</p>
        </div>
      </div>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="t('salesPages.common.customer')">
          <el-select v-model="filters.customer_code" :placeholder="t('salesPages.common.selectCustomer')" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.common.productCode')">
          <el-input v-model="filters.product_code" clearable />
        </el-form-item>
        <el-form-item :label="t('salesPages.contractPricing.validity')">
          <el-select v-model="filters.validity" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.contractPricing.validityActive')" value="active" />
            <el-option :label="t('salesPages.contractPricing.validityAll')" value="all" />
            <el-option :label="t('salesPages.contractPricing.validityExpired')" value="expired" />
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
        {{ t('salesPages.contractPricing.toolbarNew') }}
      </el-button>
      <el-button @click="handleBulkImport">
        <el-icon><Upload /></el-icon>
        {{ t('salesPages.contractPricing.toolbarImport') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="pricingList" v-loading="loading" stripe border>
        <el-table-column prop="customer_name" :label="t('salesPages.credit.colCustomerName')" min-width="120" fixed />
        <el-table-column prop="product_code" :label="t('salesPages.common.productCode')" width="120" />
        <el-table-column prop="product_name" :label="t('salesPages.contractPricing.productName')" min-width="150" show-overflow-tooltip />
        <el-table-column prop="unit_price" :label="t('salesPages.contractPricing.unitPrice')" width="110" align="right">
          <template #default="{ row }">¥{{ formatDecimal(row.unit_price ?? 0, locale as LocaleType, 0) }}</template>
        </el-table-column>
        <el-table-column prop="min_qty" :label="t('salesPages.contractPricing.minQty')" width="90" align="right" />
        <el-table-column prop="discount_type" :label="t('salesPages.contractPricing.discountType')" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ discountLabel(String(row.discount_type)) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="valid_from" :label="t('salesPages.contractPricing.validFrom')" width="110" />
        <el-table-column prop="valid_until" :label="t('salesPages.contractPricing.validUntil')" width="110" />
        <el-table-column prop="status" :label="t('salesPages.common.status')" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? t('salesPages.contractPricing.active') : t('salesPages.contractPricing.expired') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('salesPages.common.actions')" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">{{ t('salesPages.common.detail') }}</el-button>
            <el-button size="small" type="warning" link @click="handleEdit(row)">{{ t('salesPages.common.edit') }}</el-button>
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
import { Search, Plus, Upload, Tickets } from '@element-plus/icons-vue'
import type { LocaleType } from '@/i18n'
import { formatDecimal } from '@/utils/formatInteger'

const { t, locale } = useI18n()
const loading = ref(false)
const pricingList = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ customer_code: '', product_code: '', validity: 'active' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    pricingList.value = []
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
  ElMessage.info(t('salesPages.contractPricing.createWip'))
}

const handleBulkImport = () => {
  ElMessage.info(t('salesPages.contractPricing.importWip'))
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.contractPricing.detailWip', { code: String(row.product_code ?? '') }))
}

const handleEdit = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.contractPricing.editWip', { code: String(row.product_code ?? '') }))
}

const discountLabel = (type: string) => {
  const map: Record<string, string> = {
    volume: t('salesPages.contractPricing.discountVolume'),
    period: t('salesPages.contractPricing.discountPeriod'),
    special: t('salesPages.contractPricing.discountSpecial'),
  }
  return map[type] || type
}
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
