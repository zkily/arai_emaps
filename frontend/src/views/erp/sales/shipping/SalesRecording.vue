<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><DataAnalysis /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.salesRecording.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.salesRecording.subtitle') }}</p>
        </div>
      </div>
    </div>

    <el-card class="basis-card" shadow="never">
      <div class="basis-toggle">
        <span class="basis-label">{{ t('salesPages.salesRecording.basis') }}</span>
        <el-radio-group v-model="recordingBasis">
          <el-radio-button value="shipment">
            {{ t('salesPages.salesRecording.basisShip') }}
          </el-radio-button>
          <el-radio-button value="acceptance">
            {{ t('salesPages.salesRecording.basisAccept') }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </el-card>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
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
        <el-form-item :label="t('salesPages.common.customer')">
          <el-select
            v-model="filters.customer_code"
            :placeholder="t('salesPages.common.all')"
            clearable
            filterable
          >
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.common.status')">
          <el-select v-model="filters.status" :placeholder="t('salesPages.common.all')" clearable>
            <el-option :label="t('salesPages.salesRecording.statusPending')" value="pending" />
            <el-option :label="t('salesPages.salesRecording.statusRecorded')" value="recorded" />
            <el-option :label="t('salesPages.salesRecording.statusCorrected')" value="corrected" />
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
      <el-button type="primary" @click="handleBatchRecord" :disabled="!hasSelection">
        <el-icon><Check /></el-icon>
        {{ t('salesPages.salesRecording.batchRecord') }}
      </el-button>
      <el-button type="warning" @click="handleCorrection" :disabled="!hasSingleSelection">
        <el-icon><EditPen /></el-icon>
        {{ t('salesPages.salesRecording.redBlack') }}
      </el-button>
      <el-button @click="handleExportSlip" :disabled="!hasSelection">
        <el-icon><Document /></el-icon>
        {{ t('salesPages.salesRecording.exportSlip') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table
        :data="salesList"
        v-loading="loading"
        stripe
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" fixed />
        <el-table-column
          prop="slip_no"
          :label="t('salesPages.salesRecording.colSlipNo')"
          width="130"
          fixed
        />
        <el-table-column prop="order_no" :label="t('salesPages.common.orderNo')" width="130" />
        <el-table-column
          prop="shipment_date"
          :label="t('salesPages.salesRecording.colShipDate')"
          width="110"
        />
        <el-table-column
          prop="acceptance_date"
          :label="t('salesPages.salesRecording.colAcceptDate')"
          width="110"
        />
        <el-table-column
          prop="customer_name"
          :label="t('salesPages.credit.colCustomerName')"
          min-width="150"
        />
        <el-table-column
          prop="product_code"
          :label="t('salesPages.common.productCode')"
          width="120"
        />
        <el-table-column
          prop="quantity"
          :label="t('salesPages.salesRecording.colQty')"
          width="80"
          align="right"
        />
        <el-table-column
          prop="unit_price"
          :label="t('salesPages.salesRecording.colUnitPrice')"
          width="100"
          align="right"
        >
          <template #default="{ row }">
            ¥{{ formatDecimal(row.unit_price ?? 0, locale as LocaleType, 0) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="total_amount"
          :label="t('salesPages.salesRecording.colTotal')"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            ¥{{ formatDecimal(row.total_amount ?? 0, locale as LocaleType, 0) }}
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
        <el-table-column
          prop="correction_type"
          :label="t('salesPages.salesRecording.correction')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <el-tag v-if="row.correction_type === 'red'" type="danger" size="small">
              {{ t('salesPages.salesRecording.tagRed') }}
            </el-tag>
            <el-tag v-else-if="row.correction_type === 'black'" type="info" size="small">
              {{ t('salesPages.salesRecording.tagBlack') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('salesPages.common.actions')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">
              {{ t('salesPages.common.detail') }}
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Check, EditPen, Document, DataAnalysis } from '@element-plus/icons-vue'
import type { LocaleType } from '@/i18n'
import type { ElTagType } from '@/types/elementPlus'
import { formatDecimal } from '@/utils/formatInteger'

const { t, locale } = useI18n()
const loading = ref(false)
const salesList = ref<Record<string, unknown>[]>([])
const selectedRows = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const recordingBasis = ref('shipment')

const filters = reactive({ dateRange: null as string[] | null, customer_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)
const hasSingleSelection = computed(() => selectedRows.value.length === 1)

const statusLabelKeys: Record<string, string> = {
  pending: 'salesPages.salesRecording.statusPending',
  recorded: 'salesPages.salesRecording.statusRecorded',
  corrected: 'salesPages.salesRecording.statusCorrected',
}

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    salesList.value = []
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

const handleBatchRecord = async () => {
  await ElMessageBox.confirm(
    t('salesPages.salesRecording.batchConfirm', { n: selectedRows.value.length }),
    t('salesPages.common.confirmTitle'),
  )
  ElMessage.success(t('salesPages.salesRecording.batchOk'))
}

const handleCorrection = async () => {
  await ElMessageBox.confirm(
    t('salesPages.salesRecording.redBlackConfirm'),
    t('salesPages.salesRecording.redBlack'),
  )
  ElMessage.success(t('salesPages.salesRecording.redBlackOk'))
}

const handleExportSlip = () => {
  ElMessage.info(t('salesPages.salesRecording.slipWip'))
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.salesRecording.detailWip', { no: String(row.slip_no ?? '') }))
}

const getStatusType = (s: string): ElTagType =>
  (({ pending: 'warning', recorded: 'success', corrected: 'info' }) as Record<string, ElTagType>)[s] ||
  'info'
const getStatusLabel = (s: string) => (statusLabelKeys[s] ? t(statusLabelKeys[s]) : s)
</script>

<style scoped src="@/views/erp/sales/sales-page-shell.scss"></style>

<style scoped>
.basis-card {
  margin-bottom: 12px;
}
.basis-card :deep(.el-card__body) {
  padding: 16px;
}
.basis-toggle {
  display: flex;
  align-items: center;
  gap: 16px;
}
.basis-label {
  font-weight: 500;
  color: #606266;
}
.filter-card {
  margin-bottom: 12px;
}
.filter-card :deep(.el-card__body) {
  padding: 16px;
}
</style>
