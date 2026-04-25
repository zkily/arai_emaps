<template>
  <div class="sales-page-shell">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><RefreshLeft /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.returns.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.returns.subtitle') }}</p>
        </div>
      </div>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="t('salesPages.returns.rmaNo')">
          <el-input v-model="filters.rma_no" clearable />
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
            <el-option :label="t('salesPages.returns.stPending')" value="pending" />
            <el-option :label="t('salesPages.returns.stInspecting')" value="inspecting" />
            <el-option :label="t('salesPages.returns.stProcessing')" value="processing" />
            <el-option :label="t('salesPages.returns.stCompleted')" value="completed" />
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
        {{ t('salesPages.returns.newRma') }}
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="returnsList" v-loading="loading" stripe border>
        <el-table-column prop="rma_no" :label="t('salesPages.returns.rmaNo')" width="130" fixed />
        <el-table-column
          prop="request_date"
          :label="t('salesPages.returns.colRequestDate')"
          width="110"
        />
        <el-table-column
          prop="order_no"
          :label="t('salesPages.returns.colOrigOrder')"
          width="130"
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
          prop="product_name"
          :label="t('salesPages.contractPricing.productName')"
          min-width="150"
          show-overflow-tooltip
        />
        <el-table-column
          prop="quantity"
          :label="t('salesPages.returns.qty')"
          width="80"
          align="right"
        />
        <el-table-column prop="reason" :label="t('salesPages.returns.colReason')" width="120" />
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
        <el-table-column
          prop="resolution"
          :label="t('salesPages.returns.colResolution')"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.resolution === 'replacement'">
              {{ t('salesPages.returns.resolutionReplacement') }}
            </span>
            <span v-else-if="row.resolution === 'refund'">
              {{ t('salesPages.returns.resolutionRefund') }}
            </span>
            <span v-else>{{ t('salesPages.returns.resolutionNone') }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('salesPages.common.actions')" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">
              {{ t('salesPages.common.detail') }}
            </el-button>
            <el-button
              size="small"
              type="warning"
              link
              @click="handleInspection(row)"
              v-if="row.status === 'pending'"
            >
              {{ t('salesPages.returns.inspection') }}
            </el-button>
            <el-button
              size="small"
              type="success"
              link
              @click="handleProcess(row)"
              v-if="row.status === 'processing'"
            >
              {{ t('salesPages.returns.process') }}
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

    <el-dialog
      v-model="createDialogVisible"
      :title="t('salesPages.returns.dialogTitle')"
      width="600px"
    >
      <el-form :model="createForm" label-width="120px">
        <el-form-item :label="t('salesPages.returns.origOrder')" required>
          <el-input v-model="createForm.order_no" />
        </el-form-item>
        <el-form-item :label="t('salesPages.credit.colCustomerName')">
          <el-input v-model="createForm.customer_name" disabled />
        </el-form-item>
        <el-form-item :label="t('salesPages.common.productCode')">
          <el-select
            v-model="createForm.product_code"
            :placeholder="t('salesPages.returns.productSelect')"
            filterable
          >
            <el-option
              v-for="p in products"
              :key="p.cd"
              :label="`${p.cd} - ${p.name}`"
              :value="p.cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.returns.qty')" required>
          <el-input-number v-model="createForm.quantity" :min="1" />
        </el-form-item>
        <el-form-item :label="t('salesPages.returns.reason')" required>
          <el-select
            v-model="createForm.reason"
            :placeholder="t('salesPages.returns.reasonPlaceholder')"
          >
            <el-option :label="t('salesPages.returns.reasonDefect')" value="defective" />
            <el-option :label="t('salesPages.returns.reasonWrong')" value="wrong_delivery" />
            <el-option :label="t('salesPages.returns.reasonQty')" value="quantity_mismatch" />
            <el-option :label="t('salesPages.returns.reasonOther')" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('salesPages.returns.remarks')">
          <el-input v-model="createForm.remarks" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">
          {{ t('salesPages.common.cancel') }}
        </el-button>
        <el-button type="primary" @click="submitCreate">
          {{ t('salesPages.returns.register') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Search, Plus, RefreshLeft } from '@element-plus/icons-vue'
import type { ElTagType } from '@/types/elementPlus'

const { t } = useI18n()
const loading = ref(false)
const returnsList = ref<Record<string, unknown>[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const products = ref<{ cd: string; name: string }[]>([])
const createDialogVisible = ref(false)

const filters = reactive({ rma_no: '', customer_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const createForm = reactive({
  order_no: '',
  customer_name: '',
  product_code: '',
  quantity: 1,
  reason: '',
  remarks: '',
})

const statusLabelKeys: Record<string, string> = {
  pending: 'salesPages.returns.stPending',
  inspecting: 'salesPages.returns.stInspecting',
  processing: 'salesPages.returns.stProcessing',
  completed: 'salesPages.returns.stCompleted',
}

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    returnsList.value = []
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
  Object.assign(createForm, {
    order_no: '',
    customer_name: '',
    product_code: '',
    quantity: 1,
    reason: '',
    remarks: '',
  })
  createDialogVisible.value = true
}

const submitCreate = () => {
  ElMessage.success(t('salesPages.returns.registerOk'))
  createDialogVisible.value = false
  loadData()
}

const handleView = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.returns.detailWip', { no: String(row.rma_no ?? '') }))
}

const handleInspection = (row: Record<string, unknown>) => {
  ElMessage.success(t('salesPages.returns.inspectionOk', { no: String(row.rma_no ?? '') }))
}

const handleProcess = (row: Record<string, unknown>) => {
  ElMessage.info(t('salesPages.returns.processWip', { no: String(row.rma_no ?? '') }))
}

const getStatusType = (s: string): ElTagType =>
  (({
    pending: 'warning',
    inspecting: 'info',
    processing: 'primary',
    completed: 'success',
  }) as Record<string, ElTagType>)[s] || 'info'

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
