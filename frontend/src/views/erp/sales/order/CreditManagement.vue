<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><User /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.credit.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.credit.subtitle') }}</p>
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
        <el-form-item :label="t('salesPages.common.status')">
          <el-select v-model="filters.status" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.credit.statusNormal')" value="normal" />
            <el-option :label="t('salesPages.credit.statusWarning')" value="warning" />
            <el-option :label="t('salesPages.credit.statusExceeded')" value="exceeded" />
            <el-option :label="t('salesPages.credit.statusSuspended')" value="suspended" />
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
      <el-button type="primary" @click="handleSetLimit">
        <el-icon><Setting /></el-icon>
        {{ t('salesPages.credit.setLimit') }}
      </el-button>
      <el-button type="warning" @click="handleAlertList">
        <el-icon><Warning /></el-icon>
        {{ t('salesPages.credit.alerts') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="creditList" v-loading="loading" stripe border>
        <el-table-column prop="customer_code" :label="t('salesPages.credit.colCustomerCd')" width="100" fixed />
        <el-table-column prop="customer_name" :label="t('salesPages.credit.colCustomerName')" min-width="150" />
        <el-table-column prop="credit_limit" :label="t('salesPages.credit.colLimit')" width="130" align="right">
          <template #default="{ row }">¥{{ formatDecimal(row.credit_limit ?? 0, locale as LocaleType, 0) }}</template>
        </el-table-column>
        <el-table-column prop="current_balance" :label="t('salesPages.credit.colBalance')" width="130" align="right">
          <template #default="{ row }">¥{{ formatDecimal(row.current_balance ?? 0, locale as LocaleType, 0) }}</template>
        </el-table-column>
        <el-table-column prop="pending_orders" :label="t('salesPages.credit.colPendingOrders')" width="120" align="right">
          <template #default="{ row }">¥{{ formatDecimal(row.pending_orders ?? 0, locale as LocaleType, 0) }}</template>
        </el-table-column>
        <el-table-column prop="usage_rate" :label="t('salesPages.credit.colUsage')" width="120" align="right">
          <template #default="{ row }">
            <el-progress :percentage="row.usage_rate" :color="getUsageColor(row.usage_rate)" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('salesPages.common.status')" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
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
import { Search, Setting, Warning, User } from '@element-plus/icons-vue'
import type { LocaleType } from '@/i18n'
import { formatDecimal } from '@/utils/formatInteger'

const { t, locale } = useI18n()
const loading = ref(false)
const creditList = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ customer_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    creditList.value = []
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

const handleSetLimit = () => {
  ElMessage.info(t('salesPages.credit.setLimitWip'))
}

const handleAlertList = () => {
  ElMessage.info(t('salesPages.credit.alertsWip'))
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.credit.detailWip', { name: String(row.customer_name ?? '') }))
}

const handleEdit = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.credit.editWip', { name: String(row.customer_name ?? '') }))
}

const getUsageColor = (rate: number) => (rate >= 90 ? '#f56c6c' : rate >= 70 ? '#e6a23c' : '#67c23a')

const statusLabelKeys: Record<string, string> = {
  normal: 'salesPages.credit.statusNormal',
  warning: 'salesPages.credit.statusWarning',
  exceeded: 'salesPages.credit.statusExceeded',
  suspended: 'salesPages.credit.statusSuspended',
}

const getStatusType = (s: string) =>
  ({ normal: 'success', warning: 'warning', exceeded: 'danger', suspended: 'info' }[s] || 'info')

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
