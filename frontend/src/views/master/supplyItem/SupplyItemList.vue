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
        <el-table-column label="備品名" prop="item_name" min-width="150" show-overflow-tooltip />
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
      :title="form.id ? '備品マスタ編集' : '備品マスタ新規追加'"
      width="520px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px" size="small">
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
        <el-form-item label="備品CD" prop="item_cd">
          <el-input v-model="form.item_cd" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="備品名" prop="item_name">
          <el-input v-model="form.item_name" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="規格">
          <el-input v-model="form.specification" maxlength="200" />
        </el-form-item>
        <el-form-item label="単位">
          <el-input v-model="form.unit" maxlength="20" />
        </el-form-item>
        <el-form-item label="個数">
          <el-input-number v-model="form.pack_qty" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="注文ロット">
          <el-input-number v-model="form.order_lot" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="単価">
          <el-input-number
            v-model="form.unit_price"
            :min="0"
            :precision="2"
            :step="0.01"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="終息">
          <el-switch v-model="form.is_discontinued" />
        </el-form-item>
        <el-form-item label="備考">
          <el-input v-model="form.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Box, Delete, Edit, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { getSupplierList } from '@/api/master/supplierMaster'
import {
  createSupplyItem,
  deleteSupplyItem,
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
  item_cd: [{ required: true, message: '備品CDを入力してください', trigger: 'blur' }],
  item_name: [{ required: true, message: '備品名を入力してください', trigger: 'blur' }],
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

function openDialog(row?: SupplyItem) {
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
</style>
