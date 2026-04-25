<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.quotation.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.quotation.subtitle') }}</p>
        </div>
      </div>
    </div>

    <el-card class="sales-page-section filter-card" shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item :label="t('salesPages.quotation.quotationNo')">
          <el-input v-model="filters.quotation_no" clearable />
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
        <el-form-item :label="t('salesPages.common.period')">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            :range-separator="t('salesPages.common.rangeSep')"
            :start-placeholder="t('salesPages.common.startDate')"
            :end-placeholder="t('salesPages.common.endDate')"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item :label="t('salesPages.common.status')">
          <el-select v-model="filters.status" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.quotation.statusDraft')" value="draft" />
            <el-option :label="t('salesPages.quotation.statusSubmitted')" value="submitted" />
            <el-option :label="t('salesPages.quotation.statusOrdered')" value="ordered" />
            <el-option :label="t('salesPages.quotation.statusLost')" value="lost" />
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
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        {{ t('salesPages.quotation.newQuotation') }}
      </el-button>
      <el-button @click="handleCostSimulation">
        <el-icon><DataAnalysis /></el-icon>
        {{ t('salesPages.quotation.costSim') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="quotationList" v-loading="loading" stripe border>
        <el-table-column
          prop="quotation_no"
          :label="t('salesPages.quotation.quotationNo')"
          width="140"
          fixed
        />
        <el-table-column
          prop="quotation_date"
          :label="t('salesPages.quotation.quotationDate')"
          width="110"
        />
        <el-table-column
          prop="customer_name"
          :label="t('salesPages.common.customer')"
          min-width="150"
        />
        <el-table-column
          prop="subject"
          :label="t('salesPages.quotation.subject')"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          prop="total_amount"
          :label="t('salesPages.quotation.amount')"
          width="130"
          align="right"
        >
          <template #default="{ row }">
            ¥{{ formatDecimal(row.total_amount ?? 0, locale as LocaleType, 0) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="gross_profit_rate"
          :label="t('salesPages.quotation.grossMargin')"
          width="90"
          align="right"
        >
          <template #default="{ row }">
            <span :class="getProfitClass(row.gross_profit_rate)">
              {{ formatDecimal(row.gross_profit_rate ?? 0, locale as LocaleType, 1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column
          prop="valid_until"
          :label="t('salesPages.quotation.validUntil')"
          width="110"
        />
        <el-table-column
          prop="status"
          :label="t('salesPages.common.status')"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('salesPages.common.actions')" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">
              {{ t('salesPages.common.detail') }}
            </el-button>
            <el-button size="small" type="success" link @click="handleCopy(row)">
              {{ t('salesPages.common.copy') }}
            </el-button>
            <el-button size="small" type="warning" link @click="handleExportPdf(row)">
              {{ t('salesPages.common.pdf') }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              link
              @click="handleDelete(row)"
              v-if="row.status === 'draft'"
            >
              {{ t('salesPages.common.delete') }}
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
          @size-change="onPageSizeChange"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, DataAnalysis, Document } from '@element-plus/icons-vue'
import type { LocaleType } from '@/i18n'
import type { ElTagType } from '@/types/elementPlus'
import { formatDecimal } from '@/utils/formatInteger'

const { t, locale } = useI18n()
const loading = ref(false)
const quotationList = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])

const filters = reactive({
  quotation_no: '',
  customer_code: '',
  dateRange: null as string[] | null,
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    quotationList.value = []
    pagination.total = 0
  } catch {
    ElMessage.error(t('salesPages.common.loadFailed'))
  } finally {
    loading.value = false
  }
}

const onPageSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(filters, { quotation_no: '', customer_code: '', dateRange: null, status: '' })
  handleSearch()
}

const handleCreate = () => {
  ElMessage.info(t('salesPages.quotation.createWip'))
}

const handleCostSimulation = () => {
  ElMessage.info(t('salesPages.quotation.simWip'))
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.quotation.viewWip', { no: String(row.quotation_no ?? '') }))
}

const handleCopy = (row: Record<string, unknown>) => {
  ElMessage.success(t('salesPages.quotation.copyOk', { no: String(row.quotation_no ?? '') }))
}

const handleExportPdf = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.quotation.pdfWip', { no: String(row.quotation_no ?? '') }))
}

const handleDelete = async (row: Record<string, unknown>) => {
  await ElMessageBox.confirm(
    t('salesPages.quotation.deleteConfirm'),
    t('salesPages.common.confirm'),
  )
  ElMessage.success(t('salesPages.quotation.deleteOk'))
}

const getStatusType = (status: string): ElTagType => {
  const map: Record<string, ElTagType> = {
    draft: 'info',
    submitted: 'primary',
    ordered: 'success',
    lost: 'danger',
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const keys: Record<string, string> = {
    draft: 'salesPages.quotation.statusDraft',
    submitted: 'salesPages.quotation.statusSubmitted',
    ordered: 'salesPages.quotation.statusOrdered',
    lost: 'salesPages.quotation.statusLost',
  }
  return keys[status] ? t(keys[status]) : status
}

const getProfitClass = (rate: number) => {
  if (rate >= 30) return 'text-profit-high'
  if (rate >= 15) return 'text-profit-mid'
  return 'text-profit-low'
}
</script>

<style scoped src="@/views/erp/sales/sales-page-shell.scss"></style>

<style scoped>
.filter-card :deep(.el-card__body) {
  padding: 16px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}
</style>
