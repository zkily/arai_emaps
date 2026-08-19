<template>
  <div class="supply-item-master">
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon"><Box /></el-icon>
            備品マスタ
          </h1>
          <p class="subtitle">仕入先別の備品カタログを登録・管理します</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ pagination.total }}</div>
            <div class="stat-label">総件数</div>
          </div>
        </div>
      </div>
    </div>

    <div class="toolbar-section">
      <div class="toolbar-filters">
        <el-select
          v-model="filters.supplierCd"
          filterable
          clearable
          placeholder="仕入先"
          size="small"
          class="filter-supplier"
          :loading="suppliersLoading"
          @change="handleSearch"
        >
          <el-option
            v-for="s in suppliers"
            :key="s.supplier_cd"
            :label="`${s.supplier_cd} ${s.supplier_name}`"
            :value="s.supplier_cd"
          />
        </el-select>
        <el-input
          v-model="filters.keyword"
          size="small"
          clearable
          placeholder="備品CD・名称・規格"
          class="filter-keyword"
          @keyup.enter="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select
          v-model="filters.discontinued"
          size="small"
          class="filter-status"
          @change="handleSearch"
        >
          <el-option label="すべて" value="all" />
          <el-option label="有効" value="0" />
          <el-option label="終息" value="1" />
        </el-select>
        <el-button size="small" :icon="Search" @click="handleSearch">検索</el-button>
        <el-button size="small" :icon="Refresh" @click="clearFilter">クリア</el-button>
      </div>
      <el-button v-if="canCreate" type="primary" size="small" :icon="Plus" class="add-btn" @click="openDialog()">
        新規追加
      </el-button>
    </div>

    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        highlight-current-row
        class="modern-table"
        :header-cell-style="{ background: '#f8fafc', fontWeight: '600', color: '#334155' }"
      >
        <el-table-column label="仕入先CD" prop="supplier_cd" width="110" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="code-cell">{{ row.supplier_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column label="仕入先名" prop="supplier_name" min-width="140" show-overflow-tooltip />
        <el-table-column label="備品CD" prop="item_cd" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="code-cell">{{ row.item_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column label="品名" prop="item_name" min-width="150" show-overflow-tooltip />
        <el-table-column label="規格" prop="specification" min-width="120" show-overflow-tooltip />
        <el-table-column label="単位" prop="unit" width="64" align="center" />
        <el-table-column label="個数" prop="pack_qty" width="70" align="right" />
        <el-table-column label="注文ロット" prop="order_lot" width="100" align="right" />
        <el-table-column label="単価" width="100" align="right">
          <template #default="{ row }">{{ formatMoney(row.unit_price) }}</template>
        </el-table-column>
        <el-table-column label="終息" width="72" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_discontinued" size="small" type="info">終息</el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="canEdit || canDelete"
          label="操作"
          width="140"
          fixed="right"
          align="center"
        >
          <template #default="{ row }">
            <el-button v-if="canEdit" size="small" type="primary" link :icon="Edit" @click="openDialog(row)">
              編集
            </el-button>
            <el-button v-if="canDelete" size="small" type="danger" link :icon="Delete" @click="handleDelete(row)">
              削除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="pagination-section">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="fetchList"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      width="600px"
      class="item-form-dialog"
      align-center
      destroy-on-close
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="item-dialog-header">
          <div class="item-dialog-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div>
            <h3>{{ form.id ? '備品を編集' : '備品を登録' }}</h3>
            <p>{{ form.id ? 'カタログ情報を更新します' : '自動採番のCDで新しい備品を登録します' }}</p>
          </div>
        </div>
      </template>
      <div class="item-dialog-body">
        <div class="item-cd-banner">
          <div class="item-cd-banner__mark">CD</div>
          <div class="item-cd-banner__meta">
            <span class="item-cd-banner__label">備品コード</span>
            <strong class="item-cd-banner__value">{{ form.item_cd || '採番中…' }}</strong>
          </div>
          <el-tag size="small" effect="dark" round type="primary">自動採番</el-tag>
        </div>
        <el-form ref="formRef" :model="form" :rules="formRules" label-position="top" class="item-form">
          <section class="form-section">
            <header class="form-section__title">
              <span class="form-section__dot" />
              基本情報
            </header>
            <el-form-item label="仕入先" prop="supplier_cd">
              <el-select v-model="form.supplier_cd" filterable placeholder="仕入先を選択" style="width: 100%">
                <el-option
                  v-for="s in suppliers"
                  :key="s.supplier_cd"
                  :label="`${s.supplier_cd} ${s.supplier_name}`"
                  :value="s.supplier_cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="品名" prop="item_name">
              <el-input v-model="form.item_name" placeholder="品名を入力" maxlength="200" />
            </el-form-item>
            <el-form-item label="規格">
              <el-input v-model="form.specification" placeholder="規格・型番" maxlength="200" />
            </el-form-item>
          </section>
          <section class="form-section form-section--amber">
            <header class="form-section__title">
              <span class="form-section__dot" />
              発注条件
            </header>
            <div class="form-grid">
              <el-form-item label="単位">
                <el-input v-model="form.unit" maxlength="20" placeholder="個" />
              </el-form-item>
              <el-form-item label="個数">
                <el-input-number v-model="form.pack_qty" :min="1" controls-position="right" style="width: 100%" />
              </el-form-item>
              <el-form-item label="注文ロット">
                <el-input-number v-model="form.order_lot" :min="1" controls-position="right" style="width: 100%" />
              </el-form-item>
              <el-form-item label="単価">
                <el-input-number
                  v-model="form.unit_price"
                  :min="0"
                  :precision="2"
                  :step="0.01"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
            </div>
          </section>
          <section class="form-section form-section--slate">
            <header class="form-section__title">
              <span class="form-section__dot" />
              その他
            </header>
            <div class="status-row">
              <div>
                <div class="status-row__title">終息フラグ</div>
                <p class="status-row__hint">終息すると購買カタログから除外されます</p>
              </div>
              <el-switch v-model="form.is_discontinued" inline-prompt active-text="終息" inactive-text="有効" />
            </div>
            <el-form-item label="備考">
              <el-input v-model="form.remarks" type="textarea" :rows="2" placeholder="備考があれば入力" />
            </el-form-item>
          </section>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="dialog-cancel" @click="dialogVisible = false">キャンセル</el-button>
          <el-button type="primary" class="dialog-save" :loading="saving" @click="handleSubmit">
            <el-icon><Check /></el-icon>
            保存する
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Box, Check, Delete, Edit, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { getSupplierList } from '@/api/master/supplierMaster'
import {
  createSupplyItem,
  deleteSupplyItem,
  fetchNextSupplyItemCd,
  fetchSupplyItems,
  updateSupplyItem,
  type SupplyItem,
} from '@/api/supplyPurchase'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

const loading = ref(false)
const saving = ref(false)
const suppliersLoading = ref(false)
const dialogVisible = ref(false)
const tableData = ref<SupplyItem[]>([])
const suppliers = ref<{ supplier_cd: string; supplier_name: string }[]>([])
const formRef = ref<FormInstance>()

const filters = reactive({
  supplierCd: '',
  keyword: '',
  discontinued: 'all' as 'all' | '0' | '1',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  id: 0,
  supplier_cd: '',
  item_cd: '',
  item_name: '',
  specification: '',
  unit: '個',
  pack_qty: 1,
  order_lot: 1,
  unit_price: 0,
  is_discontinued: false,
  remarks: '',
})

const formRules: FormRules = {
  supplier_cd: [{ required: true, message: '仕入先を選択してください', trigger: 'change' }],
  item_name: [{ required: true, message: '品名を入力してください', trigger: 'blur' }],
}

function formatMoney(v: number) {
  return Number(v || 0).toLocaleString('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

async function loadSuppliers() {
  suppliersLoading.value = true
  try {
    const res = await getSupplierList({ page: 1, pageSize: 5000 })
    suppliers.value = (res.data?.list ?? res.list ?? []).map((s) => ({
      supplier_cd: s.supplier_cd,
      supplier_name: s.supplier_name,
    }))
  } catch {
    ElMessage.error('仕入先一覧の取得に失敗しました')
  } finally {
    suppliersLoading.value = false
  }
}

async function fetchList() {
  loading.value = true
  try {
    const res = await fetchSupplyItems({
      supplierCd: filters.supplierCd || undefined,
      keyword: filters.keyword || undefined,
      includeDiscontinued: filters.discontinued === 'all',
      discontinuedStatus: filters.discontinued === 'all' ? undefined : filters.discontinued,
      page: pagination.page,
      pageSize: pagination.pageSize,
    })
    tableData.value = res.list
    pagination.total = res.total
  } catch {
    ElMessage.error('備品一覧の取得に失敗しました')
    tableData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  void fetchList()
}

function clearFilter() {
  filters.supplierCd = ''
  filters.keyword = ''
  filters.discontinued = 'all'
  handleSearch()
}

async function openDialog(row?: SupplyItem) {
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  form.id = row?.id ?? 0
  form.supplier_cd = row?.supplier_cd ?? filters.supplierCd ?? ''
  form.item_cd = row?.item_cd ?? ''
  form.item_name = row?.item_name ?? ''
  form.specification = row?.specification ?? ''
  form.unit = row?.unit || '個'
  form.pack_qty = row?.pack_qty ?? 1
  form.order_lot = row?.order_lot ?? 1
  form.unit_price = row?.unit_price ?? 0
  form.is_discontinued = row?.is_discontinued ?? false
  form.remarks = row?.remarks ?? ''
  dialogVisible.value = true
  if (!row) {
    try {
      form.item_cd = await fetchNextSupplyItemCd()
    } catch {
      form.item_cd = 'B0001'
    }
  }
}

async function handleSubmit() {
  if (form.id ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const payload = {
      item_cd: form.item_cd.trim(),
      item_name: form.item_name.trim(),
      specification: form.specification,
      unit: form.unit,
      pack_qty: form.pack_qty,
      order_lot: form.order_lot,
      unit_price: form.unit_price,
      supplier_cd: form.supplier_cd,
      is_discontinued: form.is_discontinued,
      remarks: form.remarks,
    }
    if (form.id) {
      await updateSupplyItem(form.id, payload)
    } else {
      await createSupplyItem(payload)
    }
    ElMessage.success('保存しました')
    dialogVisible.value = false
    await fetchList()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: SupplyItem) {
  if (!guardMasterOperation(canDelete)) return
  try {
    await ElMessageBox.confirm(`「${row.item_cd} ${row.item_name}」を削除しますか？`, '確認', {
      type: 'warning',
    })
    await deleteSupplyItem(row.id)
    ElMessage.success('削除しました')
    await fetchList()
  } catch {
    /* cancel */
  }
}

onMounted(async () => {
  await loadSuppliers()
  await fetchList()
})
</script>

<style scoped>
.supply-item-master {
  padding: 6px;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  min-height: 100vh;
}
.page-header {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  border-radius: 14px;
  padding: 12px 18px;
  margin-bottom: 8px;
  box-shadow: 0 6px 24px rgba(71, 85, 105, 0.28);
}
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.main-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0 0 3px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-icon {
  font-size: 1.35rem;
}
.subtitle {
  color: rgba(255, 255, 255, 0.78);
  margin: 0;
  font-size: 0.82rem;
}
.header-stats {
  display: flex;
  gap: 8px;
}
.stat-card {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  padding: 7px 14px;
  border-radius: 12px;
  text-align: center;
  min-width: 76px;
  border: 1px solid rgba(255, 255, 255, 0.18);
}
.stat-number {
  font-size: 1.45rem;
  font-weight: 700;
  line-height: 1;
}
.stat-label {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 3px;
}
.toolbar-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: #fff;
  border-radius: 12px;
  padding: 10px 16px;
  margin-bottom: 8px;
  border: 1px solid #e2e8f0;
}
.toolbar-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.filter-supplier {
  width: 240px;
}
.filter-keyword {
  width: 220px;
}
.filter-status {
  width: 110px;
}
.add-btn {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
  border: none !important;
}
.table-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  margin-bottom: 8px;
  overflow: hidden;
}
.table-card :deep(.el-card__body) {
  padding: 0;
}
.code-cell {
  font-family: Consolas, Monaco, monospace;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 6px;
}
.muted {
  color: #94a3b8;
}
.pagination-section {
  display: flex;
  justify-content: flex-end;
  padding: 4px 2px 12px;
}

.item-form-dialog :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 32px 80px rgba(15, 23, 42, 0.28);
}
.item-form-dialog :deep(.el-dialog__header) {
  padding: 18px 20px 16px;
  margin: 0;
  background:
    radial-gradient(circle at 88% -20%, rgba(255, 255, 255, 0.28), transparent 42%),
    linear-gradient(135deg, #1d4ed8 0%, #2563eb 48%, #0ea5e9 100%);
}
.item-form-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
  font-size: 18px;
}
.item-form-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #f8fbff, #f1f5f9);
}
.item-form-dialog :deep(.el-dialog__footer) {
  padding: 12px 18px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
.item-dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #fff;
  padding-right: 24px;
}
.item-dialog-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4), 0 8px 16px rgba(15, 23, 42, 0.16);
}
.item-dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.item-dialog-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.84);
}
.item-dialog-body {
  padding: 16px 16px 10px;
}
.item-cd-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #fff 70%);
  border: 1px solid #bfdbfe;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.1);
}
.item-cd-banner__mark {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #0ea5e9);
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.28);
  flex-shrink: 0;
}
.item-cd-banner__meta {
  flex: 1;
  min-width: 0;
}
.item-cd-banner__label {
  display: block;
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
}
.item-cd-banner__value {
  display: block;
  margin-top: 2px;
  font-size: 22px;
  letter-spacing: 0.08em;
  color: #1d4ed8;
  font-family: Consolas, Monaco, monospace;
  line-height: 1.1;
}
.form-section {
  margin-bottom: 10px;
  padding: 12px 14px 6px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
}
.form-section--amber {
  background: linear-gradient(180deg, #fffbeb, #fff);
  border-color: #fde68a;
}
.form-section--slate {
  background: linear-gradient(180deg, #f8fafc, #fff);
}
.form-section__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  color: #334155;
  margin-bottom: 10px;
  letter-spacing: 0.06em;
}
.form-section__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2563eb;
  box-shadow: 0 0 0 4px #dbeafe;
}
.form-section--amber .form-section__dot {
  background: #f59e0b;
  box-shadow: 0 0 0 4px #fef3c7;
}
.form-section--slate .form-section__dot {
  background: #64748b;
  box-shadow: 0 0 0 4px #e2e8f0;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}
.item-form :deep(.el-form-item) {
  margin-bottom: 12px;
}
.item-form :deep(.el-form-item__label) {
  font-weight: 700;
  color: #475569;
  margin-bottom: 4px !important;
}
.item-form :deep(.el-input__wrapper),
.item-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.item-form :deep(.el-textarea__inner) {
  border-radius: 10px;
}
.item-form :deep(.el-input-number) {
  width: 100%;
}
.item-form :deep(.el-input-number .el-input__wrapper) {
  border-radius: 10px;
}
.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 10px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.status-row__title {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}
.status-row__hint {
  margin: 2px 0 0;
  font-size: 11px;
  color: #94a3b8;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.dialog-save {
  min-width: 118px;
  height: 36px;
  border-radius: 10px !important;
  font-weight: 700;
  background: linear-gradient(135deg, #2563eb, #0ea5e9) !important;
  border: none !important;
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.28);
}
.dialog-cancel {
  height: 36px;
  border-radius: 10px;
}
</style>
