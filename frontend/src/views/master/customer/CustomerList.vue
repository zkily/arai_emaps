<template>
  <div class="customer-master-container">
    <div class="page-shell">
      <!-- 紧凑页头：标题 + 统计 + 新增 -->
      <header class="page-header">
        <div class="header-left">
          <div class="title-icon-wrap">
            <el-icon><User /></el-icon>
          </div>
          <div class="title-block">
            <h1 class="main-title">{{ t('master.customer.title') }}</h1>
            <p class="subtitle">顧客情報の登録・編集・管理</p>
          </div>
          <div class="stat-pills">
            <span class="stat-pill">
              <strong>{{ customerList.length }}</strong>
              <em>{{ t('master.common.items') }}</em>
            </span>
            <span class="stat-pill stat-pill--active">
              <strong>{{ activeCount }}</strong>
              <em>{{ t('master.common.active') }}</em>
            </span>
          </div>
        </div>
        <el-button type="primary" :icon="Plus" class="add-btn" @click="openForm()">
          {{ t('master.customer.addCustomer') }}
        </el-button>
      </header>

      <!-- 单行筛选工具栏 -->
      <section class="toolbar-card">
        <div class="toolbar-row">
          <el-input
            v-model="filters.keyword"
            :placeholder="t('master.customer.searchPlaceholder')"
            clearable
            size="small"
            class="filter-keyword"
            @input="handleFilter"
          >
            <template #prefix>
              <el-icon class="input-prefix-icon"><Search /></el-icon>
            </template>
          </el-input>
          <el-select
            v-model="filters.status"
            :placeholder="t('master.common.status')"
            clearable
            size="small"
            class="filter-select"
            @change="handleFilter"
          >
            <el-option :label="t('master.common.active')" :value="1" />
            <el-option :label="t('master.common.inactive')" :value="0" />
          </el-select>
          <el-select
            v-model="filters.customer_type"
            :placeholder="t('master.customer.type')"
            clearable
            size="small"
            class="filter-select"
            @change="handleFilter"
          >
            <el-option :label="t('master.customer.typeCorp')" value="法人" />
            <el-option :label="t('master.customer.typePerson')" value="個人" />
            <el-option :label="t('master.customer.typeAgency')" value="代理店" />
          </el-select>
          <el-button text size="small" :icon="Refresh" class="clear-btn" @click="clearFilters">
            {{ t('master.common.clear') }}
          </el-button>
        </div>
        <div v-if="hasActiveFilters" class="active-filters">
          <el-tag
            v-if="filters.keyword"
            closable
            size="small"
            type="primary"
            @close="clearFilterField('keyword')"
          >
            {{ filters.keyword }}
          </el-tag>
          <el-tag
            v-if="filters.status !== ''"
            closable
            size="small"
            type="warning"
            @close="clearFilterField('status')"
          >
            {{ filters.status === 1 ? t('master.common.active') : t('master.common.inactive') }}
          </el-tag>
          <el-tag
            v-if="filters.customer_type"
            closable
            size="small"
            type="info"
            @close="clearFilterField('customer_type')"
          >
            {{ filters.customer_type }}
          </el-tag>
        </div>
      </section>

      <!-- 数据表格 -->
      <section class="table-section">
        <el-table
          :data="filteredList"
          stripe
          highlight-current-row
          v-loading="loading"
          class="modern-table"
          :height="tableHeight"
          :header-cell-style="tableHeaderStyle"
          :cell-style="tableCellStyle"
        >
          <el-table-column
            prop="customer_cd"
            :label="t('master.customer.customerCD')"
            width="100"
            align="center"
            fixed
          >
            <template #default="{ row }">
              <span class="code-cell">{{ row.customer_cd }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="customer_name"
            :label="t('master.customer.customerName')"
            min-width="130"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span class="name-cell">{{ row.customer_name }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="phone"
            :label="t('master.customer.phone')"
            width="120"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span class="muted-cell">{{ row.phone || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="address"
            :label="t('master.customer.address')"
            min-width="150"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span class="muted-cell">{{ row.address || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="customer_type"
            :label="t('master.customer.type')"
            width="76"
            align="center"
          >
            <template #default="{ row }">
              <el-tag
                :type="getCustomerTypeTagType(row.customer_type)"
                size="small"
                effect="light"
                round
              >
                {{ row.customer_type || '—' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="status"
            :label="t('master.common.status')"
            width="84"
            align="center"
          >
            <template #default="{ row }">
              <el-switch
                :model-value="row.status === 1"
                @update:model-value="(v: string | number | boolean) => toggleStatus(row, v === true)"
                :loading="row.statusLoading"
                size="small"
                inline-prompt
                :active-text="t('master.common.active')"
                :inactive-text="t('master.common.inactive')"
              />
            </template>
          </el-table-column>
          <el-table-column
            :label="t('master.common.actions')"
            fixed="right"
            width="88"
            align="center"
          >
            <template #default="{ row }">
              <div class="action-buttons">
                <el-tooltip :content="t('master.supplier.edit')" placement="top">
                  <el-button
                    size="small"
                    type="primary"
                    plain
                    circle
                    :icon="Edit"
                    class="action-btn"
                    @click="openForm(row)"
                  />
                </el-tooltip>
                <el-tooltip :content="t('master.supplier.delete')" placement="top">
                  <el-button
                    size="small"
                    type="danger"
                    plain
                    circle
                    :icon="Delete"
                    class="action-btn"
                    @click="deleteCustomer(row.id)"
                  />
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <!-- 底部统计 -->
      <footer class="footer-bar">
        <el-icon class="footer-icon"><DataAnalysis /></el-icon>
        <span>
          {{
            t('master.common.displayCount', {
              shown: filteredList.length,
              total: customerList.length,
            })
          }}
        </span>
      </footer>
    </div>

    <CustomerForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Search, Refresh, Plus, Edit, Delete, DataAnalysis } from '@element-plus/icons-vue'
import CustomerForm from './CustomerForm.vue'
import {
  getCustomerList,
  deleteCustomerById,
  updateCustomerStatus,
} from '@/api/master/customerMaster'
import type { CustomerItem } from '@/types/master'

const { t } = useI18n()

type RowEx = CustomerItem & { statusLoading?: boolean }

const loading = ref(false)
const customerList = ref<RowEx[]>([])
const filters = ref({ keyword: '', status: '' as '' | number, customer_type: '' })

const tableHeight = 'calc(100vh - 196px)'
const tableHeaderStyle = {
  background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
  color: '#fff',
  fontWeight: '600',
  fontSize: '12px',
  padding: '6px 4px',
}
const tableCellStyle = { padding: '4px 6px', fontSize: '12px' }

const handleFilter = () => {}

const hasActiveFilters = computed(
  () => !!filters.value.keyword || filters.value.status !== '' || !!filters.value.customer_type,
)

function clearFilterField(field: 'keyword' | 'status' | 'customer_type') {
  if (field === 'keyword') filters.value.keyword = ''
  else if (field === 'status') filters.value.status = ''
  else filters.value.customer_type = ''
}

const clearFilters = () => {
  filters.value = { keyword: '', status: '', customer_type: '' }
  fetchList()
}

const activeCount = computed(() => customerList.value.filter((row) => row.status === 1).length)

function getCustomerTypeTagType(
  type: string | undefined,
): 'primary' | 'success' | 'warning' | 'info' {
  if (!type) return 'info'
  if (type === '法人') return 'primary'
  if (type === '個人') return 'success'
  if (type === '代理店') return 'warning'
  return 'info'
}

const filteredList = computed(() => {
  let result = customerList.value
  if (filters.value.keyword) {
    const k = filters.value.keyword.toLowerCase()
    result = result.filter(
      (row) =>
        row.customer_cd?.toLowerCase().includes(k) ||
        row.customer_name?.toLowerCase().includes(k) ||
        row.phone?.toLowerCase().includes(k),
    )
  }
  if (filters.value.status !== '')
    result = result.filter((row) => row.status === filters.value.status)
  if (filters.value.customer_type)
    result = result.filter((row) => row.customer_type === filters.value.customer_type)
  return result
})

const formVisible = ref(false)
const editData = ref<RowEx | null>(null)
function openForm(row: RowEx | null = null) {
  editData.value = row
  formVisible.value = true
}

async function deleteCustomer(id: number | undefined) {
  if (id == null) return
  try {
    await ElMessageBox.confirm(t('master.customer.confirmDelete'), t('common.confirm'), {
      type: 'warning',
    })
    await deleteCustomerById(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {
    void 0
  }
}

async function toggleStatus(row: RowEx, on: boolean) {
  const next = on ? 1 : 0
  row.statusLoading = true
  try {
    await updateCustomerStatus(row.id!, next)
    row.status = next
    ElMessage.success(t('master.common.updateSuccess'))
  } catch {
    ElMessage.error(t('master.common.saveFailed'))
  } finally {
    row.statusLoading = false
  }
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getCustomerList({
      keyword: filters.value.keyword || undefined,
      status: filters.value.status !== '' ? filters.value.status : undefined,
      customer_type: filters.value.customer_type || undefined,
      page: 1,
      pageSize: 5000,
    })
    customerList.value = (res.list ?? res.data?.list ?? []).map((row) => ({
      ...row,
      statusLoading: false,
    }))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.customer-master-container {
  padding: 8px 10px;
  background: linear-gradient(160deg, #f0f9ff 0%, #e8f4fc 50%, #f1f5f9 100%);
  min-height: 100%;
}

.page-shell {
  max-width: 1320px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ── 页头 ── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%);
  border-radius: 10px;
  padding: 8px 14px;
  box-shadow: 0 3px 14px rgba(14, 165, 233, 0.28);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.title-icon-wrap {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 17px;
  flex-shrink: 0;
}

.title-block {
  min-width: 0;
}

.main-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.subtitle {
  margin: 1px 0 0;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.2;
}

.stat-pills {
  display: flex;
  gap: 6px;
  margin-left: 6px;
  flex-shrink: 0;
}

.stat-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 2px 10px;
  color: #fff;
}

.stat-pill--active {
  background: rgba(16, 185, 129, 0.28);
  border-color: rgba(16, 185, 129, 0.4);
}

.stat-pill strong {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1;
}

.stat-pill em {
  font-size: 0.65rem;
  font-style: normal;
  opacity: 0.88;
}

.add-btn {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.18) !important;
  border: 1px solid rgba(255, 255, 255, 0.35) !important;
  color: #fff !important;
  border-radius: 8px !important;
  font-weight: 600;
  font-size: 12px !important;
  padding: 6px 14px !important;
  height: 32px;
  transition: background 0.15s;
}

.add-btn:hover {
  background: rgba(255, 255, 255, 0.28) !important;
}

/* ── 筛选工具栏 ── */
.toolbar-card {
  background: #fff;
  border-radius: 8px;
  padding: 7px 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-keyword {
  flex: 1;
  min-width: 160px;
  max-width: 360px;
}

.filter-select {
  width: 108px;
}

.input-prefix-icon {
  color: #94a3b8;
}

.clear-btn {
  color: #64748b;
  font-size: 12px;
  padding: 4px 6px !important;
}

.clear-btn:hover {
  color: #0ea5e9;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed #e2e8f0;
}

/* ── 表格 ── */
.table-section {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.code-cell {
  display: inline-block;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
  font-weight: 600;
  color: #0284c7;
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
  padding: 1px 6px;
  border-radius: 4px;
}

.name-cell {
  font-weight: 500;
  color: #1e293b;
  font-size: 12px;
}

.muted-cell {
  color: #64748b;
  font-size: 11px;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.action-btn {
  width: 26px !important;
  height: 26px !important;
  padding: 0 !important;
}

:deep(.modern-table) {
  --el-table-border-color: #e8edf2;
  --el-table-row-hover-bg-color: #f0f9ff;
  font-size: 12px;
}

:deep(.modern-table .el-table__header-wrapper th) {
  border-bottom: none !important;
}

:deep(.modern-table .el-table__header .cell) {
  line-height: 1.3;
  padding: 0 4px;
}

:deep(.modern-table .el-table__body .cell) {
  line-height: 1.35;
  padding: 0 4px;
}

:deep(.modern-table.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafbfc;
}

:deep(.modern-table .el-tag) {
  border-radius: 10px;
  font-size: 10px;
  padding: 0 6px;
  height: 20px;
  line-height: 18px;
}

:deep(.modern-table .el-switch) {
  --el-switch-on-color: #10b981;
}

/* ── 底部 ── */
.footer-bar {
  display: flex;
  align-items: center;
  gap: 5px;
  background: #fff;
  border-radius: 8px;
  padding: 5px 12px;
  border: 1px solid #e2e8f0;
  color: #64748b;
  font-size: 0.78rem;
}

.footer-icon {
  color: #0ea5e9;
  font-size: 14px;
}

/* ── 响应式 ── */
@media (max-width: 900px) {
  .page-header {
    flex-wrap: wrap;
    padding: 8px 10px;
  }

  .header-left {
    flex-wrap: wrap;
  }

  .stat-pills {
    margin-left: 0;
  }

  .add-btn {
    width: 100%;
  }

  .filter-keyword {
    max-width: none;
    width: 100%;
  }

  .filter-select {
    flex: 1;
    min-width: 90px;
  }
}

@media (max-width: 600px) {
  .customer-master-container {
    padding: 4px 6px;
  }

  .subtitle {
    display: none;
  }

  .stat-pill em {
    display: none;
  }
}

.page-header,
.toolbar-card,
.table-section,
.footer-bar {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
