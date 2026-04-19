<template>
  <div class="part-master-container">
    <!-- 与 ProductList / MaterialInspection 同构的页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Grid />
            </el-icon>
            {{ t('master.part.title') }}
          </h1>
          <p class="subtitle">{{ t('master.part.subtitle') }}</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ total }}</div>
            <div class="stat-label">{{ t('master.part.listTotal') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ rows.length }}</div>
            <div class="stat-label">{{ t('master.part.pageRows') }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>{{ t('master.product.searchFilter') }}</span>
          <div class="filter-inline-summary" v-if="rows.length || hasActiveFilters">
            <div class="summary-text">
              <el-icon class="summary-icon">
                <InfoFilled />
              </el-icon>
              <span>{{ t('master.common.displayCount', { shown: rows.length, total }) }}</span>
            </div>
            <div class="active-filters" v-if="hasActiveFilters">
              <el-tag
                v-if="filters.keyword"
                closable
                @close="handleClearFilter('keyword')"
                type="primary"
                size="small"
              >
                {{ t('master.part.keyword') }}: {{ filters.keyword }}
              </el-tag>
              <el-tag
                v-if="filters.status === 0 || filters.status === 1"
                closable
                @close="handleClearFilter('status')"
                type="warning"
                size="small"
              >
                {{ t('master.common.status') }}:
                {{ filters.status === 1 ? t('master.part.statusActive') : t('master.part.statusInactive') }}
              </el-tag>
            </div>
          </div>
        </div>
        <div class="filter-actions">
          <el-button type="primary" :icon="Search" class="search-btn" @click="fetchList">
            {{ t('master.common.search') }}
          </el-button>
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">
            {{ t('master.product.reset') }}
          </el-button>
          <el-button type="primary" @click="openForm()" :icon="Plus" class="add-product-btn">
            {{ t('master.part.add') }}
          </el-button>
        </div>
      </div>

      <div class="filters-grid">
        <el-row :gutter="16">
          <el-col :lg="10" :md="12" :sm="24">
            <el-form-item :label="`🔍 ${t('master.part.keyword')}`">
              <el-input
                v-model="filters.keyword"
                clearable
                :placeholder="t('master.part.keywordPh')"
                style="width: 100%"
                @keyup.enter="fetchList"
              />
            </el-form-item>
          </el-col>
          <el-col :lg="8" :md="12" :sm="24">
            <el-form-item :label="`🔖 ${t('master.common.status')}`">
              <el-select
                v-model="filters.status"
                clearable
                :placeholder="t('master.common.select')"
                style="width: 100%"
                @change="fetchList"
              >
                <el-option :label="t('master.part.statusActive')" :value="1" />
                <el-option :label="t('master.part.statusInactive')" :value="0" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </div>

    <el-table
      v-loading="loading"
      :data="rows"
      stripe
      border
      highlight-current-row
      :style="{ width: '100%' }"
      height="600"
      class="part-table"
      :header-cell-style="{ background: '#f5f7fa', fontWeight: 'bold' }"
      :cell-style="{ padding: '4px 8px' }"
      :scrollbar-always-on="true"
      :default-sort="{ prop: 'part_name', order: 'ascending' }"
    >
        <el-table-column prop="part_cd" :label="t('master.part.partCd')" width="80" show-overflow-tooltip />
        <el-table-column prop="part_name" :label="t('master.part.partName')" min-width="150" show-overflow-tooltip />
        <el-table-column prop="category" :label="t('master.part.category')" width="100" show-overflow-tooltip />
        <el-table-column prop="kind" :label="t('master.part.kind')" width="56" align="center" />
        <el-table-column :label="t('master.part.settlementType')" width="90" show-overflow-tooltip>
          <template #default="{ row }">{{ settlementOptionLabel(row.settlement_type) }}</template>
        </el-table-column>
        <el-table-column prop="uom" :label="t('master.part.uom')" width="64" align="center" />
        <el-table-column :label="t('master.part.unitPriceOrig')" width="112" align="right">
          <template #default="{ row }">
            {{ formatNum(row.unit_price) }} {{ row.currency }}
          </template>
        </el-table-column>
        <el-table-column :label="t('master.part.materialUnitPrice')" width="160" align="right">
          <template #default="{ row }">
            {{ formatNum(row.material_unit_price) }} {{ row.currency }}
          </template>
        </el-table-column>
        <el-table-column prop="exchange_rate" :label="t('master.part.exchangeRate')" width="108" align="right">
          <template #default="{ row }">{{ formatNum(row.exchange_rate, 2) }}</template>
        </el-table-column>
        <el-table-column :label="t('master.part.totalUnitPrice')" width="128" align="right">
          <template #default="{ row }">
            <strong class="part-jpy">¥{{ formatNum(row.standard_price_jpy) }}</strong>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.part.supplier')" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.supplier_name || row.supplier_cd || '—' }}</template>
        </el-table-column>
        <el-table-column prop="status" :label="t('master.common.status')" width="88" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? t('master.part.statusActive') : t('master.part.statusInactive') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.common.actions')" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openForm(row)">{{ t('master.common.edit') }}</el-button>
            <el-popconfirm :title="t('master.part.confirmDelete')" @confirm="remove(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">{{ t('master.common.delete') }}</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      class="pagination"
      small
      @current-change="fetchList"
    />

    <el-dialog
      v-model="dlgVisible"
      width="560px"
      destroy-on-close
      align-center
      class="part-dlg"
      :close-on-click-modal="false"
      :show-close="true"
    >
      <template #header="{ titleId, titleClass }">
        <div class="part-dlg__head">
          <div class="part-dlg__head-accent" aria-hidden="true" />
          <div class="part-dlg__head-main">
            <div class="part-dlg__head-icon" aria-hidden="true">
              <el-icon :size="20"><Grid /></el-icon>
            </div>
            <div class="part-dlg__head-text">
              <h2 :id="titleId" :class="['part-dlg__head-title', titleClass]">
                {{ isEdit ? t('master.part.editTitle') : t('master.part.createTitle') }}
              </h2>
              <p class="part-dlg__head-sub">{{ t('master.part.dialogSub') }}</p>
            </div>
          </div>
        </div>
      </template>

      <el-form ref="formRef" class="part-dlg__form" :model="form" :rules="rules" label-position="top" size="small">
        <div class="part-dlg__block">
          <div class="part-dlg__block-label">{{ t('master.part.secBasic') }}</div>
          <el-row :gutter="8">
            <el-col :span="14">
              <el-form-item :label="t('master.part.partCd')" prop="part_cd" class="part-dlg__fi">
                <el-input v-model="form.part_cd" :disabled="isEdit" maxlength="50" show-word-limit />
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item :label="t('master.part.uom')" prop="uom" class="part-dlg__fi">
                <el-input v-model="form.uom" maxlength="20" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item :label="t('master.part.partName')" prop="part_name" class="part-dlg__fi">
            <el-input v-model="form.part_name" maxlength="200" show-word-limit />
          </el-form-item>
          <el-row :gutter="8">
            <el-col :span="12">
              <el-form-item :label="t('master.part.category')" class="part-dlg__fi">
                <el-input v-model="form.category" maxlength="100" show-word-limit clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.part.kind')" prop="kind" class="part-dlg__fi">
                <el-select v-model="form.kind" class="part-input-full">
                  <el-option label="T" value="T" />
                  <el-option label="N" value="N" />
                  <el-option label="F" value="F" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item :label="t('master.part.settlementType')" prop="settlement_type" class="part-dlg__fi">
            <el-select v-model="form.settlement_type" class="part-input-full">
              <el-option
                v-for="opt in PART_SETTLEMENT_TYPES"
                :key="opt"
                :value="opt"
                :label="settlementOptionLabel(opt)"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('master.part.supplierCd')" class="part-dlg__fi part-dlg__fi--mb0">
            <el-select
              v-model="form.supplier_cd"
              filterable
              clearable
              class="part-input-full"
              :loading="suppliersLoading"
              :placeholder="t('master.part.supplierCdPh')"
            >
              <el-option
                v-for="s in supplierSelectOptions"
                :key="s.supplier_cd"
                :value="s.supplier_cd"
                :label="formatSupplierOption(s)"
              />
            </el-select>
          </el-form-item>
        </div>

        <div class="part-dlg__block part-dlg__block--price">
          <div class="part-dlg__block-label">{{ t('master.part.secPrice') }}</div>
          <el-row :gutter="8">
            <el-col :span="8">
              <el-form-item :label="t('master.part.currency')" prop="currency" class="part-dlg__fi">
                <el-select v-model="form.currency" class="part-input-full" @change="onCurrencyChange">
                  <el-option label="JPY" value="JPY" />
                  <el-option label="USD" value="USD" />
                  <el-option label="EUR" value="EUR" />
                  <el-option label="CNY" value="CNY" />
                  <el-option label="VND" value="VND" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="t('master.part.unitPriceOrig')" prop="unit_price" class="part-dlg__fi">
                <el-input-number v-model="form.unit_price" :min="0" :precision="2" :step="0.01" class="part-input-full" controls-position="right" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="t('master.part.materialUnitPrice')" prop="material_unit_price" class="part-dlg__fi">
                <el-input-number v-model="form.material_unit_price" :min="0" :precision="2" :step="0.01" class="part-input-full" controls-position="right" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="8">
            <el-col :span="8">
              <el-form-item :label="t('master.part.exchangeRate')" prop="exchange_rate" class="part-dlg__fi">
                <el-input-number v-model="form.exchange_rate" :min="0.01" :precision="2" :step="0.01" class="part-input-full" controls-position="right" />
              </el-form-item>
            </el-col>
          </el-row>
          <p class="part-dlg__fx-hint">{{ t('master.part.exchangeHint') }}</p>
          <div class="part-preview-jpy">
            <span class="part-preview-jpy__lbl">{{ t('master.part.totalUnitPrice') }}</span>
            <span class="part-preview-jpy__val">¥{{ formatNum(previewTotalJpy) }}</span>
          </div>
        </div>

        <div class="part-dlg__block part-dlg__block--tail">
          <el-row :gutter="8" align="middle">
            <el-col :span="24">
              <el-form-item :label="t('master.common.status')" prop="status" class="part-dlg__fi">
                <el-radio-group v-model="form.status" class="part-dlg__status">
                  <el-radio-button :value="1">{{ t('master.part.statusActive') }}</el-radio-button>
                  <el-radio-button :value="0">{{ t('master.part.statusInactive') }}</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item :label="t('master.part.remarks')" class="part-dlg__fi part-dlg__fi--mb0">
            <el-input v-model="form.remarks" type="textarea" :rows="2" maxlength="500" show-word-limit />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="part-dlg__footer">
          <el-button size="small" @click="dlgVisible = false">{{ t('master.common.cancel') }}</el-button>
          <el-button type="primary" size="small" :loading="saving" @click="submit">{{ t('master.common.save') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Grid, Filter, Refresh, InfoFilled } from '@element-plus/icons-vue'
import {
  getPartList,
  createPart,
  updatePart,
  deletePart,
  PART_SETTLEMENT_TYPES,
  type PartMasterRow,
  type PartKind,
  type PartSettlementType,
} from '@/api/master/partMaster'
import { getSupplierList } from '@/api/master/supplierMaster'
import type { Supplier } from '@/types/master'

const { t } = useI18n()

const loading = ref(false)
const rows = ref<PartMasterRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 30

const filters = ref<{ keyword: string; status?: number }>({ keyword: '' })

const hasActiveFilters = computed(() => {
  const kw = filters.value.keyword?.trim()
  const st = filters.value.status
  return Boolean(kw) || st === 0 || st === 1
})

function handleClearFilter(key: 'keyword' | 'status') {
  if (key === 'keyword') filters.value.keyword = ''
  else filters.value.status = undefined
  page.value = 1
  fetchList()
}

const dlgVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  part_cd: '',
  part_name: '',
  category: '' as string,
  kind: 'N' as PartKind,
  settlement_type: '有償支給' as PartSettlementType,
  uom: '個',
  unit_price: 0,
  material_unit_price: 0,
  currency: 'JPY',
  exchange_rate: 1,
  supplier_cd: '' as string,
  status: 1,
  remarks: '' as string,
})

const rules: FormRules = {
  part_cd: [{ required: true, message: () => t('master.part.ruleCd'), trigger: 'blur' }],
  part_name: [{ required: true, message: () => t('master.part.ruleName'), trigger: 'blur' }],
  kind: [{ required: true, message: () => t('master.part.ruleKind'), trigger: 'change' }],
  settlement_type: [{ required: true, message: () => t('master.part.ruleSettlement'), trigger: 'change' }],
  unit_price: [{ required: true, message: () => t('master.part.rulePrice'), trigger: 'change' }],
  material_unit_price: [{ required: true, message: () => t('master.part.ruleMaterialPrice'), trigger: 'change' }],
  exchange_rate: [{ required: true, message: () => t('master.part.ruleFx'), trigger: 'change' }],
}

const suppliersLoading = ref(false)
const supplierRows = ref<Pick<Supplier, 'supplier_cd' | 'supplier_name'>[]>([])
const supplierExtra = ref<Pick<Supplier, 'supplier_cd' | 'supplier_name'> | null>(null)

const supplierSelectOptions = computed(() => {
  const extra = supplierExtra.value
  if (!extra) return supplierRows.value
  return [extra, ...supplierRows.value.filter((s) => s.supplier_cd !== extra.supplier_cd)]
})

const previewTotalJpy = computed(() => {
  const u = Number(form.unit_price) || 0
  const m = Number(form.material_unit_price) || 0
  const ex = Number(form.exchange_rate) || 0
  if (ex > 0) return u * ex + m
  return u + m
})

function settlementOptionLabel(v: string | undefined | null) {
  if (!v) return '—'
  const map: Record<string, string> = {
    有償支給: t('master.part.stPaid'),
    無償支給: t('master.part.stFree'),
    自給: t('master.part.stSelf'),
    その他: t('master.part.stOther'),
  }
  return map[v] || v
}

function normalizeSettlementType(v: string | undefined | null): PartSettlementType {
  if (v && (PART_SETTLEMENT_TYPES as readonly string[]).includes(v)) return v as PartSettlementType
  return '有償支給'
}

function formatSupplierOption(s: Pick<Supplier, 'supplier_cd' | 'supplier_name'>) {
  const name = (s.supplier_name || '').trim()
  return name ? `${s.supplier_cd} — ${name}` : s.supplier_cd
}

async function loadSuppliers() {
  suppliersLoading.value = true
  try {
    const pageSize = 10000
    let page = 1
    const all: Pick<Supplier, 'supplier_cd' | 'supplier_name'>[] = []
    let total = 0
    let first = true
    while (first || all.length < total) {
      first = false
      const res = await getSupplierList({ page, pageSize })
      const list = (res?.data?.list ?? res?.list ?? []) as Supplier[]
      total = res?.data?.total ?? res?.total ?? 0
      for (const s of list) {
        all.push({ supplier_cd: s.supplier_cd, supplier_name: s.supplier_name || '' })
      }
      if (list.length < pageSize) break
      page += 1
    }
    supplierRows.value = all
  } catch {
    supplierRows.value = []
    ElMessage.error(t('master.part.suppliersLoadFailed'))
  } finally {
    suppliersLoading.value = false
  }
}

function formatNum(n: number | undefined | null, digits = 2) {
  if (n == null || Number.isNaN(Number(n))) return '0'
  return Number(n).toLocaleString('ja-JP', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

function onCurrencyChange(c: string) {
  if (c === 'JPY') form.exchange_rate = 1
}

function clearFilters() {
  filters.value = { keyword: '', status: undefined }
  page.value = 1
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const st = filters.value.status
    const res = await getPartList({
      keyword: filters.value.keyword || undefined,
      status: st === 0 || st === 1 ? st : undefined,
      page: page.value,
      pageSize: pageSize,
    })
    rows.value = res?.data?.list ?? []
    total.value = res?.data?.total ?? 0
  } catch {
    rows.value = []
    ElMessage.error(t('master.part.loadFailed'))
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, {
    part_cd: '',
    part_name: '',
    category: '',
    kind: 'N' as PartKind,
    settlement_type: '有償支給' as PartSettlementType,
    uom: '個',
    unit_price: 0,
    material_unit_price: 0,
    currency: 'JPY',
    exchange_rate: 1,
    supplier_cd: '',
    status: 1,
    remarks: '',
  })
}

async function openForm(row?: PartMasterRow) {
  supplierExtra.value = null
  await loadSuppliers()
  if (row) {
    isEdit.value = true
    editId.value = row.id
    const sc = (row.supplier_cd || '').trim()
    if (sc && !supplierRows.value.some((s) => s.supplier_cd === sc)) {
      supplierExtra.value = { supplier_cd: sc, supplier_name: row.supplier_name || '' }
    }
    Object.assign(form, {
      part_cd: row.part_cd,
      part_name: row.part_name,
      category: row.category || '',
      kind: (row.kind === 'T' || row.kind === 'N' || row.kind === 'F' ? row.kind : 'N') as PartKind,
      settlement_type: normalizeSettlementType(row.settlement_type),
      uom: row.uom || '個',
      unit_price: row.unit_price,
      material_unit_price: row.material_unit_price ?? 0,
      currency: row.currency || 'JPY',
      exchange_rate: row.exchange_rate ?? 1,
      supplier_cd: sc,
      status: row.status === 0 ? 0 : 1,
      remarks: row.remarks || '',
    })
  } else {
    isEdit.value = false
    editId.value = null
    resetForm()
  }
  dlgVisible.value = true
}

async function submit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    if (isEdit.value && editId.value != null) {
      await updatePart(editId.value, {
        part_name: form.part_name,
        category: form.category.trim() || null,
        kind: form.kind,
        settlement_type: form.settlement_type,
        uom: form.uom,
        unit_price: form.unit_price,
        material_unit_price: form.material_unit_price,
        currency: form.currency,
        exchange_rate: form.exchange_rate,
        supplier_cd: form.supplier_cd || null,
        status: form.status,
        remarks: form.remarks || null,
      })
      ElMessage.success(t('master.common.saveSuccess'))
    } else {
      await createPart({
        part_cd: form.part_cd.trim(),
        part_name: form.part_name.trim(),
        category: form.category.trim() || null,
        kind: form.kind,
        settlement_type: form.settlement_type,
        uom: form.uom,
        unit_price: form.unit_price,
        material_unit_price: form.material_unit_price,
        currency: form.currency,
        exchange_rate: form.exchange_rate,
        supplier_cd: form.supplier_cd || null,
        status: form.status,
        remarks: form.remarks || null,
      })
      ElMessage.success(t('master.common.saveSuccess'))
    }
    dlgVisible.value = false
    fetchList()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err?.response?.data?.detail || t('master.part.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function remove(id: number) {
  try {
    await deletePart(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {
    ElMessage.error(t('master.part.deleteFailed'))
  }
}

onMounted(fetchList)
</script>

<style scoped>
/* 与 ProductList / MaterialInspectionMaster 对齐的列表页骨架 */
.part-master-container {
  padding: 6px;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 10px 16px;
  margin-bottom: 6px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0 0 2px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.9);
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  font-size: 0.8rem;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  color: white;
  padding: 6px 12px;
  border-radius: 10px;
  text-align: center;
  min-width: 70px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.stat-number {
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 2px;
  white-space: nowrap;
}

.action-section {
  background: white;
  border-radius: 10px;
  padding: 0;
  margin-bottom: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
  flex-wrap: wrap;
}

.filter-icon {
  font-size: 1rem;
  color: #667eea;
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.clear-btn {
  color: #64748b;
  transition: all 0.2s ease;
  padding: 6px 10px !important;
  font-size: 12px !important;
}

.clear-btn:hover {
  color: #667eea;
}

.search-btn {
  border: none !important;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  color: #fff !important;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
}

.add-product-btn {
  border: none !important;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  color: #fff !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.add-product-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
  background: linear-gradient(135deg, #7c8ff0 0%, #8558b5 100%) !important;
}

.filters-grid {
  padding: 10px 14px;
  background: white;
}

.filters-grid :deep(.el-form-item) {
  margin-bottom: 8px;
}

.filters-grid :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  padding-bottom: 2px;
}

.filters-grid :deep(.el-input__wrapper),
.filters-grid :deep(.el-select .el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0;
}

.filters-grid :deep(.el-input__wrapper:hover),
.filters-grid :deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea;
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 0;
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.summary-icon {
  color: #667eea;
  font-size: 14px;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.active-filters :deep(.el-tag) {
  border-radius: 4px;
  font-size: 11px;
  padding: 0 6px;
  height: 22px;
}

.filter-inline-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid #e2e8f0;
  flex-wrap: wrap;
}

.filter-inline-summary .summary-text {
  margin-bottom: 0;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

:deep(.el-table .el-table__header th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
  font-weight: 600;
  color: #334155;
  font-size: 12px;
  padding: 6px 8px !important;
}

:deep(.el-table .el-table__cell) {
  padding: 4px 6px !important;
}

:deep(.el-table .cell) {
  line-height: 1.5;
}

:deep(.el-table .el-button--small) {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 5px;
}

.part-table {
  font-size: 12px;
}

.part-jpy {
  color: #4f46e5;
}

.pagination {
  margin-top: 8px;
  text-align: center;
}

.pagination :deep(.el-pager li) {
  border-radius: 6px;
  font-size: 12px;
  min-width: 28px;
  height: 28px;
  line-height: 28px;
}

.pagination :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.part-input-full {
  width: 100%;
}

.part-preview-jpy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  margin-top: 6px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-radius: 8px;
  border: 1px solid rgba(99, 102, 241, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.part-preview-jpy__lbl {
  font-size: 11px;
  font-weight: 700;
  color: #4338ca;
  letter-spacing: 0.02em;
}

.part-preview-jpy__val {
  font-size: 0.95rem;
  font-weight: 800;
  color: #312e81;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .part-master-container {
    padding: 4px;
  }

  .page-header {
    padding: 8px 12px;
    border-radius: 10px;
  }

  .main-title {
    font-size: 1.15rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
    padding: 10px 12px;
  }

  .filter-actions {
    justify-content: flex-start;
  }

  .stat-card {
    min-width: 60px;
    padding: 5px 8px;
  }

  .stat-number {
    font-size: 1.1rem;
  }
}

.page-header,
.action-section {
  animation: partListFadeIn 0.4s ease-out;
}

@keyframes partListFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

<!-- 弹窗 teleport 至 body，单独块保证样式命中 -->
<style>
.part-dlg.el-dialog {
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.06) inset,
    0 24px 48px -12px rgba(15, 23, 42, 0.28),
    0 12px 24px -8px rgba(15, 23, 42, 0.12);
}

.part-dlg .el-dialog__header {
  padding: 0;
  margin: 0;
}

.part-dlg .el-dialog__headerbtn {
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.part-dlg .el-dialog__headerbtn:hover {
  background: rgba(15, 23, 42, 0.06);
}

.part-dlg .el-dialog__body {
  padding: 0 16px 12px;
}

.part-dlg .el-dialog__footer {
  padding: 0;
  margin: 0;
}

.part-dlg__head {
  position: relative;
  background: linear-gradient(145deg, #0f172a 0%, #1e293b 52%, #0f172a 100%);
  color: #f8fafc;
}

.part-dlg__head-accent {
  height: 3px;
  background: linear-gradient(90deg, #22d3ee, #6366f1, #a78bfa);
  opacity: 0.95;
}

.part-dlg__head-main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 40px 12px 16px;
}

.part-dlg__head-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: #e0e7ff;
}

.part-dlg__head-text {
  min-width: 0;
  padding-top: 2px;
}

.part-dlg__head-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: #f8fafc;
}

.part-dlg__head-sub {
  margin: 4px 0 0;
  font-size: 11px;
  line-height: 1.35;
  color: rgba(226, 232, 240, 0.72);
  font-weight: 500;
}

.part-dlg__form .el-form-item {
  margin-bottom: 8px;
}

.part-dlg__form .el-form-item__label {
  padding-bottom: 2px;
  margin-bottom: 0 !important;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  line-height: 1.2;
}

.part-dlg__form .el-form-item__content {
  line-height: 1.2;
}

.part-dlg__form .el-form-item__error {
  padding-top: 2px;
  font-size: 11px;
}

.part-dlg__fi--mb0.el-form-item,
.part-dlg__form .part-dlg__fi--mb0 {
  margin-bottom: 0;
}

.part-dlg__block {
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.part-dlg__block--price {
  background: linear-gradient(180deg, #fafbff 0%, #f1f5f9 100%);
  border-color: #e2e8f0;
}

.part-dlg__block--tail {
  padding-top: 8px;
  padding-bottom: 8px;
  margin-bottom: 0;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.part-dlg__block-label {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #94a3b8;
  margin: 0 0 6px;
}

.part-dlg__fx-hint {
  margin: 2px 0 0;
  padding: 6px 8px;
  font-size: 10px;
  line-height: 1.45;
  color: #64748b;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 6px;
  border: 1px dashed #cbd5e1;
}

.part-dlg__status.el-radio-group {
  display: inline-flex;
  width: 100%;
}

.part-dlg__status .el-radio-button {
  flex: 1;
}

.part-dlg__status .el-radio-button__inner {
  width: 100%;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
}

.part-dlg__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 16px 12px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid #e2e8f0;
}

.part-dlg .el-input__wrapper,
.part-dlg .el-select__wrapper {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.15s ease;
}

.part-dlg .el-input__wrapper:hover,
.part-dlg .el-select__wrapper:hover {
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}

.part-dlg .el-input__wrapper.is-focus,
.part-dlg .el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px #6366f1 inset, 0 0 0 3px rgba(99, 102, 241, 0.18);
}

.part-dlg .el-textarea__inner {
  border-radius: 8px;
  min-height: 52px !important;
  padding: 6px 10px;
  font-size: 12px;
}
</style>
