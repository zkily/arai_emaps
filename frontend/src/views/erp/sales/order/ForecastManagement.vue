<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><DataAnalysis /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.forecast.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.forecast.subtitle') }}</p>
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
        <el-form-item :label="t('salesPages.forecast.targetMonth')">
          <el-date-picker v-model="filters.targetMonth" type="month" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item :label="t('salesPages.common.status')">
          <el-select v-model="filters.status" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.forecast.statusForecast')" value="forecast" />
            <el-option :label="t('salesPages.forecast.statusConfirmed')" value="confirmed" />
            <el-option :label="t('salesPages.forecast.statusDiff')" value="diff" />
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
      <el-button type="primary" @click="handleImport">
        <el-icon><Upload /></el-icon>
        {{ t('salesPages.forecast.import') }}
      </el-button>
      <el-button @click="handleSyncAps">
        <el-icon><Connection /></el-icon>
        {{ t('salesPages.forecast.syncAps') }}
      </el-button>
      <el-button @click="handleAccuracyReport">
        <el-icon><DataAnalysis /></el-icon>
        {{ t('salesPages.forecast.report') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="forecastList" v-loading="loading" stripe border>
        <el-table-column prop="customer_name" :label="t('salesPages.credit.colCustomerName')" min-width="120" fixed />
        <el-table-column prop="product_code" :label="t('salesPages.common.productCode')" width="120" />
        <el-table-column prop="product_name" :label="t('salesPages.contractPricing.productName')" min-width="150" show-overflow-tooltip />
        <el-table-column prop="target_month" :label="t('salesPages.forecast.targetMonth')" width="100" />
        <el-table-column prop="forecast_qty" :label="t('salesPages.forecast.colForecastQty')" width="100" align="right" />
        <el-table-column prop="confirmed_qty" :label="t('salesPages.forecast.colConfirmedQty')" width="100" align="right" />
        <el-table-column prop="diff_qty" :label="t('salesPages.forecast.colDiff')" width="90" align="right">
          <template #default="{ row }">
            <span
              :class="
                row.diff_qty > 0 ? 'text-diff-pos' : row.diff_qty < 0 ? 'text-diff-neg' : ''
              "
            >
              {{ row.diff_qty > 0 ? '+' : '' }}{{ row.diff_qty }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="accuracy_rate" :label="t('salesPages.forecast.colAccuracy')" width="80" align="right">
          <template #default="{ row }">{{ formatDecimal(row.accuracy_rate ?? 0, locale as LocaleType, 1) }}%</template>
        </el-table-column>
        <el-table-column prop="status" :label="t('salesPages.common.status')" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'confirmed' ? 'success' : row.status === 'diff' ? 'warning' : 'info'">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('salesPages.common.actions')" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">{{ t('salesPages.common.detail') }}</el-button>
            <el-button size="small" type="success" link @click="handleConfirm(row)" v-if="row.status === 'forecast'">
              {{ t('salesPages.forecast.actionConfirm') }}
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
import { Search, Upload, Connection, DataAnalysis } from '@element-plus/icons-vue'
import type { LocaleType } from '@/i18n'
import { formatDecimal } from '@/utils/formatInteger'

const { t, locale } = useI18n()
const loading = ref(false)
const forecastList = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ customer_code: '', product_code: '', targetMonth: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const statusKeys: Record<string, string> = {
  forecast: 'salesPages.forecast.statusForecast',
  confirmed: 'salesPages.forecast.statusConfirmed',
  diff: 'salesPages.forecast.statusDiff',
}

const statusLabel = (s: string) => (statusKeys[s] ? t(statusKeys[s]) : s)

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    forecastList.value = []
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
  Object.assign(filters, { customer_code: '', product_code: '', targetMonth: '', status: '' })
  handleSearch()
}

const handleImport = () => {
  ElMessage.info(t('salesPages.forecast.importWip'))
}

const handleSyncAps = () => {
  ElMessage.info(t('salesPages.forecast.syncWip'))
}

const handleAccuracyReport = () => {
  ElMessage.info(t('salesPages.forecast.reportWip'))
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.forecast.detailWip', { code: String(row.product_code ?? '') }))
}

const handleConfirm = (row: Record<string, unknown>) => {
  ElMessage.success(t('salesPages.forecast.confirmOk', { code: String(row.product_code ?? '') }))
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
