<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.invoice.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.invoice.subtitle') }}</p>
        </div>
      </div>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
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
        <el-form-item :label="t('salesPages.invoice.closingDate')">
          <el-date-picker v-model="filters.closingDate" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="t('salesPages.common.status')">
          <el-select v-model="filters.status" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.invoice.statusPending')" value="pending" />
            <el-option :label="t('salesPages.invoice.statusIssued')" value="issued" />
            <el-option :label="t('salesPages.invoice.statusSent')" value="sent" />
            <el-option :label="t('salesPages.invoice.statusPaid')" value="paid" />
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
      <el-button type="primary" @click="handleBatchIssue">
        <el-icon><Document /></el-icon>
        {{ t('salesPages.invoice.batchIssue') }}
      </el-button>
      <el-button @click="handleBatchSend">
        <el-icon><Promotion /></el-icon>
        {{ t('salesPages.invoice.batchSend') }}
      </el-button>
      <el-button @click="handleExportPdf">
        <el-icon><Download /></el-icon>
        {{ t('salesPages.invoice.exportPdf') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table
        :data="invoiceList"
        v-loading="loading"
        stripe
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" fixed />
        <el-table-column
          prop="invoice_no"
          :label="t('salesPages.invoice.invoiceNo')"
          width="140"
          fixed
        />
        <el-table-column
          prop="customer_name"
          :label="t('salesPages.credit.colCustomerName')"
          min-width="150"
        />
        <el-table-column
          prop="closing_date"
          :label="t('salesPages.invoice.closingDate')"
          width="110"
        />
        <el-table-column
          prop="invoice_date"
          :label="t('salesPages.invoice.invoiceDate')"
          width="110"
        />
        <el-table-column prop="due_date" :label="t('salesPages.invoice.dueDate')" width="110" />
        <el-table-column
          prop="subtotal"
          :label="t('salesPages.invoice.subtotal')"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            ¥{{ formatDecimal(row.subtotal ?? 0, locale as LocaleType, 0) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="tax_amount"
          :label="t('salesPages.invoice.tax')"
          width="100"
          align="right"
        >
          <template #default="{ row }">
            ¥{{ formatDecimal(row.tax_amount ?? 0, locale as LocaleType, 0) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="total_amount"
          :label="t('salesPages.invoice.total')"
          width="130"
          align="right"
        >
          <template #default="{ row }">
            <strong>¥{{ formatDecimal(row.total_amount ?? 0, locale as LocaleType, 0) }}</strong>
          </template>
        </el-table-column>
        <el-table-column
          prop="status"
          :label="t('salesPages.common.status')"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusType(String(row.status))">
              {{ getStatusLabel(String(row.status)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('salesPages.common.actions')" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">
              {{ t('salesPages.common.detail') }}
            </el-button>
            <el-button size="small" type="success" link @click="handleExportSingle(row)">
              {{ t('salesPages.common.pdf') }}
            </el-button>
            <el-button
              size="small"
              type="warning"
              link
              @click="handleSend(row)"
              v-if="row.status === 'issued'"
            >
              {{ t('salesPages.invoice.send') }}
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
import { Search, Document, Promotion, Download } from '@element-plus/icons-vue'
import type { LocaleType } from '@/i18n'
import type { ElTagType } from '@/types/elementPlus'
import { formatDecimal } from '@/utils/formatInteger'

const { t, locale } = useI18n()
const loading = ref(false)
const invoiceList = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const selectedRows = ref<Record<string, unknown>[]>([])
const filters = reactive({ customer_code: '', closingDate: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const statusLabelKeys: Record<string, string> = {
  pending: 'salesPages.invoice.statusPending',
  issued: 'salesPages.invoice.statusIssued',
  sent: 'salesPages.invoice.statusSent',
  paid: 'salesPages.invoice.statusPaid',
}

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    invoiceList.value = []
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

const handleSelectionChange = (rows: Record<string, unknown>[]) => {
  selectedRows.value = rows
}

const handleBatchIssue = () => {
  ElMessage.info(t('salesPages.invoice.batchIssueWip'))
}

const handleBatchSend = () => {
  ElMessage.info(t('salesPages.invoice.batchSendWip', { n: selectedRows.value.length }))
}

const handleExportPdf = () => {
  ElMessage.info(t('salesPages.invoice.pdfWip'))
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.invoice.detailWip', { no: String(row.invoice_no ?? '') }))
}

const handleExportSingle = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.invoice.singlePdfWip', { no: String(row.invoice_no ?? '') }))
}

const handleSend = (row: Record<string, unknown>) => {
  ElMessage.success(t('salesPages.invoice.sendOk', { no: String(row.invoice_no ?? '') }))
}

const getStatusType = (s: string): ElTagType =>
  (({ pending: 'info', issued: 'primary', sent: 'warning', paid: 'success' }) as Record<
    string,
    ElTagType
  >)[s] || 'info'
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
