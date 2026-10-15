<template>
  <div class="customer-master-container cst-modern pb-std">
    <div class="page-shell">
      <!-- 紧凑页头：标题 + 统计 + 新增 -->
      <header class="page-header page-toolbar pb-hero pb-hero--page">
        <div class="page-toolbar-glow" aria-hidden="true" />
        <div class="page-header-fx pb-bubbles" aria-hidden="true" />
        <div class="header-left">
          <div class="title-icon-wrap">
            <el-icon><User /></el-icon>
          </div>
          <div class="title-block">
            <h1 class="main-title pb-hero-title">{{ t('master.customer.title') }}</h1>
            <p class="subtitle pb-hero-desc">顧客情報の登録・編集・管理</p>
          </div>
          <div class="stat-pills">
            <span class="stat-pill stat-pill--total">
              <strong>{{ customerList.length }}</strong>
              <em>{{ t('master.common.items') }}</em>
            </span>
            <span class="stat-pill stat-pill--active">
              <strong>{{ activeCount }}</strong>
              <em>{{ t('master.common.active') }}</em>
            </span>
            <span class="stat-pill stat-pill--inactive">
              <strong>{{ customerList.length - activeCount }}</strong>
              <em>{{ t('master.common.inactive') }}</em>
            </span>
          </div>
        </div>
        <el-button v-if="canCreate" class="tb-btn tb-btn-green add-btn" @click="openForm()">
          <el-icon><Plus /></el-icon>
          <span class="tb-label">{{ t('master.customer.addCustomer') }}</span>
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

      <section class="table-section">
        <el-table
          :data="filteredList"
          stripe
          border
          size="small"
          highlight-current-row
          v-loading="loading"
          class="modern-table"
          height="100%"
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
                :disabled="!canEdit"
                :loading="row.statusLoading"
                size="small"
                inline-prompt
                :active-text="t('master.common.active')"
                :inactive-text="t('master.common.inactive')"
              />
            </template>
          </el-table-column>
          <el-table-column
            v-if="canEdit || canDelete"
            :label="t('master.common.actions')"
            fixed="right"
            width="88"
            align="center"
          >
            <template #default="{ row }">
              <div class="action-buttons">
                <el-tooltip v-if="canEdit" :content="t('master.supplier.edit')" placement="top">
                  <el-button
                    size="small"
                    plain
                    circle
                    :icon="Edit"
                    class="action-btn action-btn--edit"
                    @click="openForm(row)"
                  />
                </el-tooltip>
                <el-tooltip v-if="canDelete" :content="t('master.supplier.delete')" placement="top">
                  <el-button
                    size="small"
                    plain
                    circle
                    :icon="Delete"
                    class="action-btn action-btn--del"
                    @click="deleteCustomer(row.id)"
                  />
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <footer class="footer-bar">
          <div class="footer-pills">
            <span class="footer-pill footer-pill--count">
              {{
                t('master.common.displayCount', {
                  shown: filteredList.length,
                  total: customerList.length,
                })
              }}
            </span>
            <span class="footer-pill footer-pill--active">
              {{ t('master.common.active') }} {{ activeCount.toLocaleString() }}
            </span>
            <span class="footer-pill footer-pill--inactive">
              {{ t('master.common.inactive') }}
              {{ (customerList.length - activeCount).toLocaleString() }}
            </span>
          </div>
        </footer>
      </section>
    </div>

    <CustomerForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import CustomerForm from './CustomerForm.vue'
import {
  getCustomerList,
  deleteCustomerById,
  updateCustomerStatus,
} from '@/api/master/customerMaster'
import type { CustomerItem } from '@/types/master'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { t } = useI18n()
const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

type RowEx = CustomerItem & { statusLoading?: boolean }

const loading = ref(false)
const customerList = ref<RowEx[]>([])
const filters = ref({ keyword: '', status: '' as '' | number, customer_type: '' })

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
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  editData.value = row
  formVisible.value = true
}

async function deleteCustomer(id: number | undefined) {
  if (!guardMasterOperation(canDelete)) return
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
  if (!guardMasterOperation(canEdit)) return
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
  --cst-app-chrome: 84px;
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  min-height: 0;
  height: calc(100vh - var(--cst-app-chrome));
  height: calc(100dvh - var(--cst-app-chrome));
  max-height: calc(100vh - var(--cst-app-chrome));
  max-height: calc(100dvh - var(--cst-app-chrome));
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.page-shell {
  width: 100%;
  box-sizing: border-box;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ── 页头 ── */
.page-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  border-radius: 16px;
  padding: 14px 18px;
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
}

/* ── 筛选工具栏 ── */
.toolbar-card {
  flex-shrink: 0;
  position: relative;
  background: #fff;
  border-radius: 12px;
  padding: 10px 14px 10px 18px;
  border: 1px solid #fbcfe8;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.06);
}
.toolbar-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 4px;
  border-radius: 99px;
  background: linear-gradient(180deg, #f9a8d4, #db2777, #9d174d);
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
  color: #be185d;
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
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border-radius: 14px;
  border: 1px solid #fbcfe8;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.06);
  padding: 10px 12px;
}

.table-section :deep(.el-table) {
  flex: 1 1 auto;
  height: 100% !important;
}
.table-section :deep(.el-table__inner-wrapper) {
  height: 100%;
}
.table-section :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
}

.code-cell {
  display: inline-block;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
  font-weight: 600;
  color: #9d174d;
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
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
  flex-shrink: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #fce7f3;
}

.footer-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.footer-pill {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
}
.footer-pill--count {
  background: #fce7f3;
  color: #9d174d;
  border-color: #fbcfe8;
}
.footer-pill--active {
  background: #d1fae5;
  color: #047857;
  border-color: #a7f3d0;
}
.footer-pill--inactive {
  background: #f1f5f9;
  color: #64748b;
  border-color: #e2e8f0;
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

/* ============================================================
 * 页面美化：顧客マスタ（玫紅→粉・他頁と分色）
 * ============================================================ */
.customer-master-container.cst-modern {
  background:
    radial-gradient(1100px 380px at 0% 0%, rgba(190, 24, 93, 0.1), transparent 60%),
    radial-gradient(900px 380px at 100% 0%, rgba(244, 114, 182, 0.08), transparent 60%),
    linear-gradient(160deg, #fdf2f8 0%, #f8fafc 45%, #fff1f2 100%);
}

.cst-modern .page-header {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(125deg, #831843 0%, #9d174d 34%, #db2777 66%, #f472b6 100%);
  box-shadow:
    0 18px 36px -18px rgba(157, 23, 77, 0.55),
    0 4px 12px -6px rgba(219, 39, 119, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.cst-modern .page-toolbar-glow {
  position: absolute;
  inset: -40% -20% auto -10%;
  height: 120%;
  z-index: 0;
  background: radial-gradient(ellipse 80% 55% at 18% 0%, rgba(255, 255, 255, 0.22), transparent 55%);
  pointer-events: none;
}

.cst-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.cst-modern .header-left,
.cst-modern .page-header > .add-btn {
  position: relative;
  z-index: 1;
}

.cst-modern .title-icon-wrap {
  width: 40px;
  height: 40px;
  font-size: 20px;
  border-radius: 12px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(131, 24, 67, 0.3);
}

.cst-modern .main-title {
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.02em;
}

.cst-modern .subtitle {
  color: rgba(255, 255, 255, 0.88);
}

.cst-modern .stat-pill {
  padding: 4px 12px;
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.16);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22);
}
.cst-modern .stat-pill--total {
  background: rgba(255, 255, 255, 0.18);
}
.cst-modern .stat-pill--active {
  background: rgba(16, 185, 129, 0.35);
  border-color: rgba(167, 243, 208, 0.55);
}
.cst-modern .stat-pill--inactive {
  background: rgba(131, 24, 67, 0.35);
  border-color: rgba(251, 207, 232, 0.4);
}
.cst-modern .stat-pill strong {
  font-size: 1.05rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.cst-modern .tb-btn {
  --k-rgb: 5 150 105;
  --k-fg: #047857;
  --k-bd: #6ee7b7;
  --k-tint: #d1fae5;
  --k-tint-h: #a7f3d0;
  --k-ico: #10b981;
  height: 32px !important;
  padding: 0 15px 0 12px !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  letter-spacing: 0.03em;
  color: var(--k-fg) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%) !important;
  border: 1px solid var(--k-bd) !important;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.12),
    0 2px 6px -1px rgba(131, 24, 67, 0.35) !important;
}
.cst-modern .tb-btn :deep(.el-icon) {
  color: var(--k-ico);
}
.cst-modern .tb-btn:hover {
  color: rgb(var(--k-rgb)) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 30%, var(--k-tint-h) 100%) !important;
  transform: translateY(-1px);
}

.cst-modern .toolbar-card {
  background: linear-gradient(110deg, #fdf2f8 0%, #ffffff 60%);
}

.cst-modern .toolbar-row :deep(.el-input__wrapper),
.cst-modern .toolbar-row :deep(.el-select__wrapper) {
  border-radius: 9px;
  background: #f8fafc;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.cst-modern .toolbar-row :deep(.el-input__wrapper:hover),
.cst-modern .toolbar-row :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #f9a8d4 inset;
}
.cst-modern .toolbar-row :deep(.el-input__wrapper.is-focus),
.cst-modern .toolbar-row :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #db2777 inset,
    0 0 0 3px rgba(219, 39, 119, 0.15);
}

.cst-modern .clear-btn {
  font-weight: 600;
  border-radius: 999px;
  background: #fdf2f8;
  box-shadow: inset 0 0 0 1px #fbcfe8;
}

.cst-modern .clear-btn:hover {
  color: #be185d;
  background: #fce7f3;
}

.cst-modern .table-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 5;
  pointer-events: none;
  background: linear-gradient(90deg, #9d174d 0%, #db2777 55%, #f472b6 100%);
}
.cst-modern .table-section {
  position: relative;
}

.cst-modern .modern-table :deep(.el-table__header-wrapper th.el-table__cell) {
  color: #9d174d !important;
  font-weight: 700 !important;
  background: linear-gradient(180deg, #fdf2f8 0%, #fce7f3 100%) !important;
  border-bottom: 2px solid #f9a8d4 !important;
}

.cst-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child),
.cst-modern .modern-table :deep(.el-table__body tr.current-row > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #db2777;
}

.cst-modern .code-cell {
  padding: 1px 8px;
  font-weight: 700;
  color: #9d174d;
  border-radius: 6px;
  background: linear-gradient(180deg, #ffffff 0%, #fce7f3 100%);
  box-shadow: inset 0 0 0 1px #fbcfe8;
}

.cst-modern .action-btn--edit {
  color: #2563eb !important;
  border-color: #bfdbfe !important;
}
.cst-modern .action-btn--edit:hover {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  color: #fff !important;
  border-color: transparent !important;
}
.cst-modern .action-btn--del {
  color: #e11d48 !important;
  border-color: #fecdd3 !important;
}
.cst-modern .action-btn--del:hover {
  background: linear-gradient(135deg, #f43f5e, #e11d48) !important;
  color: #fff !important;
  border-color: transparent !important;
}

@media (max-width: 768px) {
  .customer-master-container {
    padding: 8px;
  }
  .add-btn {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cst-modern .tb-btn:hover {
    transform: none;
  }
}
</style>
