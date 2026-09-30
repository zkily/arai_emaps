<template>
  <div class="part-master-container">
    <!-- 与 ProductList / MaterialInspection 同构的页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon><Grid /></el-icon>
          </div>
          <div class="title-text">
            <h1 class="main-title">{{ t('master.part.title') }}</h1>
            <p class="subtitle">{{ t('master.part.subtitle') }}</p>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat-card stat-card--total">
            <div class="stat-icon"><el-icon><Collection /></el-icon></div>
            <div class="stat-body">
              <div class="stat-number">{{ total.toLocaleString('ja-JP') }}</div>
              <div class="stat-label">{{ t('master.part.listTotal') }}</div>
            </div>
          </div>
          <div class="stat-card stat-card--page">
            <div class="stat-icon"><el-icon><Document /></el-icon></div>
            <div class="stat-body">
              <div class="stat-number">{{ rows.length.toLocaleString('ja-JP') }}</div>
              <div class="stat-label">{{ t('master.part.pageRows') }}</div>
            </div>
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
          <el-button
            v-if="canExport"
            type="success"
            @click="exportToCSV"
            :icon="Download"
            :disabled="total === 0"
            class="export-csv-btn"
          >
            CSV出力
          </el-button>
          <el-button
            v-if="canExport"
            type="warning"
            @click="generateAndPrintQRCodes"
            :icon="Printer"
            :loading="qrPrinting"
            class="qr-code-btn"
          >
            QRコード印刷
          </el-button>
          <el-button v-if="canCreate" type="primary" @click="openForm()" :icon="Plus" class="add-product-btn">
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

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="rows"
        border
        highlight-current-row
        :style="{ width: '100%' }"
        height="calc(100vh - 290px)"
        class="part-table"
        :scrollbar-always-on="true"
        :default-sort="{ prop: 'part_name', order: 'ascending' }"
      >
        <el-table-column prop="part_cd" :label="t('master.part.partCd')" width="96" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="code-chip">{{ row.part_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="part_name" :label="t('master.part.partName')" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="part-name">{{ row.part_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" :label="t('master.part.category')" width="110" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.category" class="category-chip">{{ row.category }}</span>
            <span v-else class="muted-dash">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="part_material" :label="t('master.part.partMaterial')" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.part_material">{{ row.part_material }}</span>
            <span v-else class="muted-dash">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="kind" :label="t('master.part.kind')" width="64" align="center">
          <template #default="{ row }">
            <span v-if="row.kind" :class="['kind-badge', `kind-badge--${row.kind}`]">{{ row.kind }}</span>
            <span v-else class="muted-dash">—</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.part.settlementType')" width="100" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <span :class="['st-chip', settlementClass(row.settlement_type)]">
              {{ settlementOptionLabel(row.settlement_type) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="uom" :label="t('master.part.uom')" width="64" align="center" />
        <el-table-column prop="capacity_qty" :label="t('master.part.capacityQty')" width="84" align="right">
          <template #default="{ row }">
            <span v-if="row.capacity_qty != null" class="num">{{ formatNum(row.capacity_qty, 0) }}</span>
            <span v-else class="muted-dash">—</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.part.unitPriceOrig')" width="128" align="right">
          <template #default="{ row }">
            <span class="num">{{ formatNum(row.unit_price) }}</span>
            <span class="ccy-chip">{{ row.currency }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.part.materialUnitPrice')" width="160" align="right">
          <template #default="{ row }">
            <span class="num">{{ formatNum(row.material_unit_price) }}</span>
            <span class="ccy-chip">{{ row.currency }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="exchange_rate" :label="t('master.part.exchangeRate')" width="108" align="right">
          <template #default="{ row }">
            <span :class="['num', { 'num--muted': Number(row.exchange_rate) === 1 }]">
              {{ formatNum(row.exchange_rate, 2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.part.totalUnitPrice')" width="132" align="right" class-name="jpy-col">
          <template #default="{ row }">
            <strong class="part-jpy">¥{{ formatNum(row.standard_price_jpy) }}</strong>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.part.supplier')" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.supplier_name || row.supplier_cd" class="supplier-text">
              {{ row.supplier_name || row.supplier_cd }}
            </span>
            <span v-else class="muted-dash">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('master.common.status')" width="92" align="center">
          <template #default="{ row }">
            <span :class="['status-pill', row.status === 1 ? 'is-active' : 'is-inactive']">
              <i class="status-dot" />
              {{ row.status === 1 ? t('master.part.statusActive') : t('master.part.statusInactive') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column v-if="canEdit || canDelete" :label="t('master.common.actions')" width="130" fixed="right" align="center">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button v-if="canEdit" class="row-btn row-btn--edit" size="small" :icon="Edit" @click="openForm(row)">
                {{ t('master.common.edit') }}
              </el-button>
              <el-popconfirm v-if="canDelete" :title="t('master.part.confirmDelete')" @confirm="remove(row.id)">
                <template #reference>
                  <el-button class="row-btn row-btn--delete" size="small" :icon="Delete" />
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          class="pagination"
          size="small"
          @current-change="fetchList"
        />
      </div>
    </div>

    <el-dialog
      v-model="dlgVisible"
      width="784px"
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
              <el-icon :size="22"><Grid /></el-icon>
            </div>
            <div class="part-dlg__head-text">
              <h2 :id="titleId" :class="['part-dlg__head-title', titleClass]">
                {{ isEdit ? t('master.part.editTitle') : t('master.part.createTitle') }}
              </h2>
              <p class="part-dlg__head-sub">{{ t('master.part.dialogSub') }}</p>
            </div>
            <div v-if="isEdit && form.part_cd" class="part-dlg__head-chips">
              <span class="part-dlg__head-chip part-dlg__head-chip--code">{{ form.part_cd }}</span>
              <span :class="['part-dlg__head-chip', form.status === 1 ? 'is-active' : 'is-inactive']">
                <i class="part-dlg__head-dot" />
                {{ form.status === 1 ? t('master.part.statusActive') : t('master.part.statusInactive') }}
              </span>
            </div>
          </div>
        </div>
      </template>

      <el-form ref="formRef" class="part-dlg__form" :model="form" :rules="rules" label-position="top">
        <div class="part-dlg__grid">
          <div class="part-dlg__col">
            <section class="part-dlg__block part-dlg__block--basic">
              <header class="part-dlg__block-head">
                <span class="part-dlg__block-icon"><el-icon><Document /></el-icon></span>
                <span class="part-dlg__block-title">{{ t('master.part.secBasic') }}</span>
              </header>
              <el-row :gutter="10">
                <el-col :span="9">
                  <el-form-item :label="t('master.part.partCd')" prop="part_cd" class="part-dlg__fi">
                    <el-input v-model="form.part_cd" :disabled="isEdit" maxlength="50" />
                  </el-form-item>
                </el-col>
                <el-col :span="15">
                  <el-form-item :label="t('master.part.partName')" prop="part_name" class="part-dlg__fi">
                    <el-input v-model="form.part_name" maxlength="200" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="10">
                <el-col :span="9">
                  <el-form-item :label="t('master.part.category')" class="part-dlg__fi">
                    <el-input v-model="form.category" maxlength="100" clearable />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item :label="t('master.part.kind')" prop="kind" class="part-dlg__fi">
                    <el-radio-group v-model="form.kind" class="part-dlg__seg part-dlg__seg--kind">
                      <el-radio-button
                        v-for="k in PART_KINDS"
                        :key="k"
                        :value="k"
                        :class="`part-dlg__kind--${k}`"
                      >
                        {{ k }}
                      </el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
                <el-col :span="7">
                  <el-form-item :label="t('master.part.uom')" prop="uom" class="part-dlg__fi">
                    <el-input v-model="form.uom" maxlength="20" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="10">
                <el-col :span="15">
                  <el-form-item :label="t('master.part.partMaterial')" class="part-dlg__fi part-dlg__fi--mb0">
                    <el-input
                      v-model="form.part_material"
                      maxlength="100"
                      clearable
                      :placeholder="t('master.part.partMaterialPh')"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="9">
                  <el-form-item :label="t('master.part.capacityQty')" class="part-dlg__fi part-dlg__fi--mb0">
                    <el-input-number
                      v-model="form.capacity_qty"
                      :min="0"
                      :precision="0"
                      :step="1"
                      class="part-input-full"
                      controls-position="right"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </section>

            <section class="part-dlg__block part-dlg__block--trade">
              <header class="part-dlg__block-head">
                <span class="part-dlg__block-icon"><el-icon><Shop /></el-icon></span>
                <span class="part-dlg__block-title">{{ t('master.part.secTrade') }}</span>
              </header>
              <el-form-item :label="t('master.part.settlementType')" prop="settlement_type" class="part-dlg__fi">
                <el-radio-group v-model="form.settlement_type" class="part-dlg__seg part-dlg__seg--st">
                  <el-radio-button
                    v-for="opt in PART_SETTLEMENT_TYPES"
                    :key="opt"
                    :value="opt"
                    :class="settlementClass(opt).replace('st-chip--', 'part-dlg__st--')"
                  >
                    {{ settlementOptionLabel(opt) }}
                  </el-radio-button>
                </el-radio-group>
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
            </section>
          </div>

          <div class="part-dlg__col">
            <section class="part-dlg__block part-dlg__block--price">
              <header class="part-dlg__block-head">
                <span class="part-dlg__block-icon"><el-icon><Money /></el-icon></span>
                <span class="part-dlg__block-title">{{ t('master.part.secPrice') }}</span>
              </header>
              <el-row :gutter="10">
                <el-col :span="12">
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
                <el-col :span="12">
                  <el-form-item :label="t('master.part.exchangeRate')" prop="exchange_rate" class="part-dlg__fi">
                    <el-input-number
                      v-model="form.exchange_rate"
                      :min="0.01"
                      :precision="2"
                      :step="0.01"
                      class="part-input-full"
                      controls-position="right"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item :label="t('master.part.unitPriceOrig')" prop="unit_price" class="part-dlg__fi">
                    <el-input-number
                      v-model="form.unit_price"
                      :min="0"
                      :precision="2"
                      :step="0.01"
                      class="part-input-full"
                      controls-position="right"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item :label="t('master.part.materialUnitPrice')" prop="material_unit_price" class="part-dlg__fi">
                    <el-input-number
                      v-model="form.material_unit_price"
                      :min="0"
                      :precision="2"
                      :step="0.01"
                      class="part-input-full"
                      controls-position="right"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <div class="part-preview-jpy">
                <div class="part-preview-jpy__main">
                  <span class="part-preview-jpy__lbl">{{ t('master.part.totalUnitPrice') }}</span>
                  <span class="part-preview-jpy__val">¥{{ formatNum(previewTotalJpy) }}</span>
                </div>
                <div class="part-preview-jpy__formula">{{ t('master.part.priceFormula') }}</div>
              </div>
              <p class="part-dlg__fx-hint">
                <el-icon class="part-dlg__fx-hint-icon"><InfoFilled /></el-icon>
                <span>{{ t('master.part.exchangeHint') }}</span>
              </p>
            </section>

            <section class="part-dlg__block part-dlg__block--status">
              <header class="part-dlg__block-head">
                <span class="part-dlg__block-icon"><el-icon><CircleCheck /></el-icon></span>
                <span class="part-dlg__block-title">{{ t('master.common.status') }}</span>
              </header>
              <el-form-item prop="status" class="part-dlg__fi part-dlg__fi--mb0">
                <el-radio-group v-model="form.status" class="part-dlg__seg part-dlg__seg--status">
                  <el-radio-button :value="1" class="part-dlg__status--on">
                    {{ t('master.part.statusActive') }}
                  </el-radio-button>
                  <el-radio-button :value="0" class="part-dlg__status--off">
                    {{ t('master.part.statusInactive') }}
                  </el-radio-button>
                </el-radio-group>
              </el-form-item>
            </section>
          </div>

          <section class="part-dlg__block part-dlg__block--remarks part-dlg__span-all">
            <header class="part-dlg__block-head">
              <span class="part-dlg__block-icon"><el-icon><Memo /></el-icon></span>
              <span class="part-dlg__block-title">{{ t('master.part.remarks') }}</span>
            </header>
            <el-form-item class="part-dlg__fi part-dlg__fi--mb0">
              <el-input v-model="form.remarks" type="textarea" :rows="2" maxlength="500" show-word-limit />
            </el-form-item>
          </section>
        </div>
      </el-form>

      <template #footer>
        <div class="part-dlg__footer">
          <el-button class="part-dlg__btn part-dlg__btn--cancel" @click="dlgVisible = false">
            {{ t('master.common.cancel') }}
          </el-button>
          <el-button class="part-dlg__btn part-dlg__btn--save" :loading="saving" @click="submit">
            {{ t('master.common.save') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Search,
  Grid,
  Filter,
  Refresh,
  InfoFilled,
  Printer,
  Download,
  Collection,
  Document,
  Edit,
  Delete,
  Shop,
  Money,
  Memo,
  CircleCheck,
} from '@element-plus/icons-vue'
import {
  getPartList,
  createPart,
  updatePart,
  deletePart,
  exportPartToCSV,
  PART_SETTLEMENT_TYPES,
  type PartMasterRow,
  type PartKind,
  type PartSettlementType,
} from '@/api/master/partMaster'
import { getSupplierList } from '@/api/master/supplierMaster'
import type { Supplier } from '@/types/master'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { t } = useI18n()
const { canCreate, canEdit, canDelete, canExport } = useMasterOperationPermission()

const PART_KINDS: PartKind[] = ['T', 'N', 'F']

const loading = ref(false)
const qrPrinting = ref(false)
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
  part_material: '' as string,
  kind: 'N' as PartKind,
  settlement_type: '有償支給' as PartSettlementType,
  uom: '個',
  capacity_qty: undefined as number | undefined,
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

function settlementClass(v: string | undefined | null) {
  const map: Record<string, string> = {
    有償支給: 'st-chip--paid',
    無償支給: 'st-chip--free',
    自給: 'st-chip--self',
  }
  return (v && map[v]) || 'st-chip--other'
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
    part_material: '',
    kind: 'N' as PartKind,
    settlement_type: '有償支給' as PartSettlementType,
    uom: '個',
    capacity_qty: undefined,
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
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
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
      part_material: row.part_material || '',
      kind: (row.kind === 'T' || row.kind === 'N' || row.kind === 'F' ? row.kind : 'N') as PartKind,
      settlement_type: normalizeSettlementType(row.settlement_type),
      uom: row.uom || '個',
      capacity_qty: row.capacity_qty ?? undefined,
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
  if (isEdit.value ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
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
        part_material: form.part_material.trim() || null,
        kind: form.kind,
        settlement_type: form.settlement_type,
        uom: form.uom,
        capacity_qty: form.capacity_qty ?? null,
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
        part_material: form.part_material.trim() || null,
        kind: form.kind,
        settlement_type: form.settlement_type,
        uom: form.uom,
        capacity_qty: form.capacity_qty ?? null,
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
  if (!guardMasterOperation(canDelete)) return
  try {
    await deletePart(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {
    ElMessage.error(t('master.part.deleteFailed'))
  }
}

const exportToCSV = async () => {
  if (!guardMasterOperation(canExport)) return
  try {
    loading.value = true

    const st = filters.value.status
    const allDataResponse = await getPartList({
      keyword: filters.value.keyword || undefined,
      status: st === 0 || st === 1 ? st : undefined,
      page: 1,
      pageSize: 10000,
    })

    const allPartsData = allDataResponse?.data?.list ?? []

    if (allPartsData.length === 0) {
      ElMessage.warning('出力する部品がありません')
      return
    }

    const exportData = allPartsData.map((part) => ({
      part_cd: part.part_cd || '',
      part_name: part.part_name || '',
    }))

    const result = await exportPartToCSV(exportData)
    if (result?.success) {
      ElMessage.success(
        `${exportData.length}件を${result.fileName || 'PartsMaster.csv'}として共有フォルダに保存しました`,
      )
    } else {
      ElMessage.error(result?.message || 'CSVファイルの保存に失敗しました')
    }
  } catch (error) {
    console.error('CSV出力エラー:', error)
    ElMessage.error('CSVファイルの出力に失敗しました')
  } finally {
    loading.value = false
  }
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

async function fetchAllPartsForPrint(): Promise<PartMasterRow[]> {
  const all: PartMasterRow[] = []
  let currentPage = 1
  const batchSize = 1000
  let totalCount = 0
  let first = true

  while (first || all.length < totalCount) {
    first = false
    const res = await getPartList({ page: currentPage, pageSize: batchSize })
    const list = res?.data?.list ?? []
    totalCount = res?.data?.total ?? list.length
    all.push(...list)
    if (list.length < batchSize) break
    currentPage += 1
  }

  return all
}

const generateAndPrintQRCodes = async () => {
  if (!guardMasterOperation(canExport)) return
  qrPrinting.value = true
  try {
    const partsToUse = await fetchAllPartsForPrint()

    if (partsToUse.length === 0) {
      ElMessage.warning('印刷する部品がありません')
      return
    }

    let QRCode: typeof import('qrcode')
    try {
      QRCode = await import('qrcode')
    } catch {
      ElMessage.error(
        'QRコードライブラリが見つかりません。以下のコマンドでインストールしてください: npm install qrcode',
      )
      return
    }

    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください')
      return
    }

    const sortedParts = [...partsToUse].sort((a, b) => {
      const nameA = a.part_name || ''
      const nameB = b.part_name || ''
      return nameA.localeCompare(nameB, 'ja')
    })

    const qrCodes: Array<{ dataUrl: string; part_cd: string; part_name: string }> = []
    for (const part of sortedParts) {
      if (!part.part_cd) continue
      try {
        const qrDataUrl = await QRCode.toDataURL(part.part_cd, {
          width: 95,
          margin: 2,
          color: {
            dark: '#000000',
            light: '#FFFFFF',
          },
        })
        qrCodes.push({
          dataUrl: qrDataUrl,
          part_cd: part.part_cd,
          part_name: part.part_name || '',
        })
      } catch (error) {
        console.error(`QRコード生成エラー (${part.part_cd}):`, error)
      }
    }

    if (qrCodes.length === 0) {
      printWindow.close()
      ElMessage.error('QRコードの生成に失敗しました')
      return
    }

    const qrCodesPerRow = 5
    const qrCodesPerPage = 40
    const totalPages = qrCodes.length > 0 ? Math.ceil(qrCodes.length / qrCodesPerPage) : 0

    let html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>部品QRコード印刷</title>
        <style>
          @page {
            size: A4 portrait;
            margin: 0;
          }
          body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
          }
          .page {
            width: 210mm;
            height: 297mm;
            padding: 12mm;
            margin: 0;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
          }
          .page:not(:last-child) {
            page-break-after: always;
          }
          .page:last-child {
            page-break-after: avoid;
          }
          .page-title {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8mm;
            color: #333;
            flex-shrink: 0;
          }
          .qr-grid {
            display: grid;
            grid-template-columns: repeat(${qrCodesPerRow}, 1fr);
            grid-template-rows: repeat(8, 1fr);
            gap: 1.2mm;
            width: 100%;
            height: 100%;
            align-content: start;
          }
          .qr-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1mm;
            border: 1px solid #ddd;
            border-radius: 2px;
            page-break-inside: avoid;
            box-sizing: border-box;
          }
          .qr-code {
            width: 70px;
            height: 70px;
            margin-bottom: 2px;
            flex-shrink: 0;
          }
          .qr-part-name {
            font-size: 12px;
            font-weight: bold;
            text-align: center;
            color: #000;
            word-break: break-all;
            line-height: 1.3;
            margin-top: 2px;
            padding: 0 2px;
          }
          @media print {
            body {
              margin: 0;
              padding: 0;
            }
            .page {
              margin: 0;
              padding: 12mm;
            }
          }
        </style>
      </head>
      <body>
    `

    for (let pageIndex = 0; pageIndex < totalPages; pageIndex++) {
      const startIndex = pageIndex * qrCodesPerPage
      const endIndex = Math.min(startIndex + qrCodesPerPage, qrCodes.length)

      if (startIndex >= qrCodes.length || endIndex <= startIndex) break

      const pageQRCodes = qrCodes.slice(startIndex, endIndex)
      if (pageQRCodes.length === 0) break

      html += `<div class="page">`
      html += `<div class="page-title">部品マスタQR</div>`
      html += `<div class="qr-grid">`

      for (let i = 0; i < pageQRCodes.length; i++) {
        const { dataUrl, part_name } = pageQRCodes[i]
        const col = i % qrCodesPerRow
        const row = Math.floor(i / qrCodesPerRow)
        const gridColumn = col + 1
        const gridRow = row + 1

        html += `
          <div class="qr-item" style="grid-column: ${gridColumn}; grid-row: ${gridRow};">
            <img src="${dataUrl}" alt="QRコード" class="qr-code" />
            ${part_name ? `<div class="qr-part-name">${escapeHtml(part_name)}</div>` : ''}
          </div>
        `
      }

      html += `</div></div>`
    }

    html += `
      </body>
      </html>
    `

    printWindow.document.write(html)
    printWindow.document.close()

    printWindow.onload = () => {
      setTimeout(() => {
        let isClosed = false
        let fallbackTimeout: ReturnType<typeof setTimeout> | null = null

        const closeWindow = () => {
          if (!isClosed) {
            isClosed = true
            if (fallbackTimeout) {
              clearTimeout(fallbackTimeout)
              fallbackTimeout = null
            }
            setTimeout(() => {
              try {
                printWindow.close()
              } catch (error) {
                console.error('窗口关闭エラー:', error)
              }
            }, 100)
          }
        }

        printWindow.addEventListener('afterprint', closeWindow)

        let focusTimeout: ReturnType<typeof setTimeout> | null = null
        printWindow.addEventListener('focus', () => {
          if (focusTimeout) clearTimeout(focusTimeout)
          focusTimeout = setTimeout(() => {
            closeWindow()
          }, 300)
        })

        fallbackTimeout = setTimeout(() => {
          if (!isClosed) closeWindow()
        }, 5000)

        printWindow.print()
      }, 250)
    }

    ElMessage.success(`${qrCodes.length}件のQRコードを生成しました`)
  } catch (error) {
    console.error('QRコード生成エラー:', error)
    ElMessage.error('QRコードの生成に失敗しました')
  } finally {
    qrPrinting.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
/* 部品在庫管理ページと同系統のパレット（indigo / violet 基調） */
.part-master-container {
  --pm-indigo: #4f46e5;
  --pm-violet: #7c3aed;
  --pm-sky: #0284c7;
  --pm-emerald: #059669;
  --pm-amber: #d97706;
  --pm-rose: #e11d48;
  --pm-ink: #0f172a;
  --pm-muted: #64748b;
  --pm-line: #e2e8f0;
  padding: 10px 12px;
  background:
    radial-gradient(1200px 380px at 0% 0%, rgba(99, 102, 241, 0.1), transparent 60%),
    radial-gradient(900px 320px at 100% 0%, rgba(139, 92, 246, 0.09), transparent 60%),
    linear-gradient(180deg, #f5f7fc 0%, #eef1f8 100%);
  min-height: 100vh;
  animation: pmFadeIn 0.45s ease-out;
}

@keyframes pmFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes pmSlideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pmRise {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pmShine {
  0% { transform: translateX(-120%) skewX(-18deg); }
  60%, 100% { transform: translateX(320%) skewX(-18deg); }
}

/* ページヘッダー */
.page-header {
  position: relative;
  overflow: hidden;
  padding: 10px 18px;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 58%, #8b5cf6 100%);
  border-radius: 14px;
  color: #fff;
  box-shadow:
    0 10px 28px rgba(79, 70, 229, 0.28),
    0 0 0 1px rgba(255, 255, 255, 0.18) inset;
  animation: pmSlideDown 0.45s ease-out;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.page-header:hover {
  transform: translateY(-1px);
  box-shadow:
    0 14px 34px rgba(124, 58, 237, 0.32),
    0 0 0 1px rgba(255, 255, 255, 0.22) inset;
}

.page-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 88% -30%, rgba(255, 255, 255, 0.28) 0, transparent 38%),
    radial-gradient(circle at 62% 140%, rgba(255, 255, 255, 0.16) 0, transparent 34%),
    radial-gradient(circle at 8% 120%, rgba(56, 189, 248, 0.28) 0, transparent 30%);
  pointer-events: none;
}

.page-header::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 30%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.14), transparent);
  animation: pmShine 7s ease-in-out infinite;
  pointer-events: none;
}

.header-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.title-icon {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  border-radius: 11px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(10px);
  box-shadow:
    0 6px 14px rgba(30, 27, 75, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  transition: transform 0.3s ease;
}

.page-header:hover .title-icon {
  transform: rotate(-6deg) scale(1.06);
}

.title-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.04em;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.subtitle {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.88);
}

.header-stats {
  display: flex;
  gap: 10px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 128px;
  padding: 7px 14px 7px 8px;
  border-radius: 12px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition: transform 0.2s ease, background 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.12));
}

.stat-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  border-radius: 9px;
  color: #fff;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.18);
}

.stat-card--total .stat-icon {
  background: linear-gradient(135deg, #38bdf8, #0284c7);
}

.stat-card--page .stat-icon {
  background: linear-gradient(135deg, #34d399, #059669);
}

.stat-number {
  font-size: 1.3rem;
  font-weight: 800;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  margin-top: 1px;
  font-size: 0.7rem;
  opacity: 0.9;
  white-space: nowrap;
}

/* 検索・フィルター */
.action-section {
  margin-bottom: 10px;
  overflow: hidden;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow:
    0 4px 16px rgba(15, 23, 42, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  animation: pmRise 0.45s ease-out 0.05s both;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 14px;
  border-bottom: 1px solid #eef2f7;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.9), rgba(255, 255, 255, 0.6));
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 0.92rem;
  font-weight: 700;
  color: #334155;
}

.filter-icon {
  width: 26px;
  height: 26px;
  padding: 5px;
  font-size: 14px;
  border-radius: 8px;
  color: var(--pm-indigo);
  background: rgba(79, 70, 229, 0.1);
}

.filter-inline-summary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid var(--pm-line);
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--pm-muted);
}

.summary-icon {
  font-size: 14px;
  color: var(--pm-indigo);
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.active-filters :deep(.el-tag) {
  height: 22px;
  padding: 0 8px;
  font-size: 11px;
  border-radius: 999px;
}

.filter-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.filter-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

/* グラデーションボタン共通 */
.search-btn,
.export-csv-btn,
.qr-code-btn,
.add-product-btn {
  border: none !important;
  border-radius: 9px;
  padding: 7px 13px !important;
  font-size: 12px !important;
  font-weight: 600;
  color: #fff !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

.search-btn:hover,
.export-csv-btn:hover:not(:disabled),
.qr-code-btn:hover:not(:disabled),
.add-product-btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.06);
}

.search-btn:active,
.export-csv-btn:active:not(:disabled),
.qr-code-btn:active:not(:disabled),
.add-product-btn:active {
  transform: translateY(0);
}

.search-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.28);
}

.search-btn:hover {
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.38);
}

.export-csv-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.26);
}

.export-csv-btn:hover:not(:disabled) {
  box-shadow: 0 6px 16px rgba(5, 150, 105, 0.36);
}

.qr-code-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
  box-shadow: 0 4px 12px rgba(217, 119, 6, 0.26);
}

.qr-code-btn:hover:not(:disabled) {
  box-shadow: 0 6px 16px rgba(217, 119, 6, 0.36);
}

.add-product-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.28);
}

.add-product-btn:hover {
  box-shadow: 0 6px 16px rgba(124, 58, 237, 0.38);
}

.export-csv-btn:disabled,
.qr-code-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.clear-btn {
  padding: 6px 10px !important;
  font-size: 12px !important;
  color: var(--pm-muted);
  border-radius: 8px;
  transition: color 0.2s ease, background 0.2s ease;
}

.clear-btn:hover {
  color: var(--pm-indigo);
  background: rgba(79, 70, 229, 0.08) !important;
}

.filters-grid {
  padding: 10px 14px 2px;
}

.filters-grid :deep(.el-form-item) {
  margin-bottom: 8px;
}

.filters-grid :deep(.el-form-item__label) {
  padding-bottom: 2px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.filters-grid :deep(.el-input__wrapper),
.filters-grid :deep(.el-select__wrapper) {
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 0 0 1px var(--pm-line) inset;
  transition: box-shadow 0.15s ease;
}

.filters-grid :deep(.el-input__wrapper:hover),
.filters-grid :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #c7d2fe inset;
}

.filters-grid :deep(.el-input__wrapper.is-focus),
.filters-grid :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px var(--pm-indigo) inset,
    0 0 0 3px rgba(79, 70, 229, 0.14);
}

/* テーブル（シンプル・行高め） */
.table-card {
  overflow: hidden;
  border-radius: 14px;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.05);
  animation: pmRise 0.45s ease-out 0.1s both;
}

.part-table {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: #f8fafc;
  --el-table-current-row-bg-color: #eef2ff;
  font-size: 12.5px;
}

.part-table :deep(.el-table__inner-wrapper::before),
.part-table :deep(.el-table__border-left-patch) {
  display: none;
}

.part-table :deep(th.el-table__cell) {
  padding: 10px 0;
  background: #f8fafc !important;
  border-bottom: 1px solid var(--pm-line) !important;
  font-size: 12px;
  font-weight: 600;
  color: var(--pm-muted);
  letter-spacing: 0.02em;
}

.part-table :deep(td.el-table__cell) {
  padding: 9px 0;
  border-bottom: 1px solid #f1f5f9 !important;
  color: #334155;
}

.part-table :deep(.cell) {
  padding: 0 12px;
  line-height: 22px;
}

.part-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #f8fafc !important;
}

.part-table :deep(.el-table__body tr.current-row > td.el-table__cell) {
  background: #eef2ff !important;
}

.part-table :deep(td.jpy-col) {
  background: rgba(238, 242, 255, 0.45);
}

.code-chip {
  display: inline-block;
  padding: 1px 7px;
  font-family: 'JetBrains Mono', Consolas, 'Courier New', monospace;
  font-size: 11.5px;
  font-weight: 600;
  color: #4338ca;
  background: #eef2ff;
  border-radius: 6px;
}

.part-name {
  font-weight: 600;
  color: var(--pm-ink);
}

.category-chip {
  display: inline-block;
  max-width: 100%;
  padding: 0 8px;
  font-size: 11.5px;
  line-height: 20px;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid var(--pm-line);
  border-radius: 999px;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
}

.muted-dash {
  color: #cbd5e1;
}

.kind-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 22px;
  font-size: 11.5px;
  font-weight: 800;
  border-radius: 7px;
}

.kind-badge--T {
  color: #0369a1;
  background: #e0f2fe;
  box-shadow: inset 0 0 0 1px #bae6fd;
}

.kind-badge--N {
  color: #6d28d9;
  background: #ede9fe;
  box-shadow: inset 0 0 0 1px #ddd6fe;
}

.kind-badge--F {
  color: #b45309;
  background: #fef3c7;
  box-shadow: inset 0 0 0 1px #fde68a;
}

.st-chip {
  display: inline-block;
  padding: 0 9px;
  font-size: 11.5px;
  font-weight: 600;
  line-height: 20px;
  border-radius: 999px;
  white-space: nowrap;
}

.st-chip--paid {
  color: #b45309;
  background: #fffbeb;
  box-shadow: inset 0 0 0 1px #fde68a;
}

.st-chip--free {
  color: #0369a1;
  background: #f0f9ff;
  box-shadow: inset 0 0 0 1px #bae6fd;
}

.st-chip--self {
  color: #047857;
  background: #ecfdf5;
  box-shadow: inset 0 0 0 1px #a7f3d0;
}

.st-chip--other {
  color: #475569;
  background: #f8fafc;
  box-shadow: inset 0 0 0 1px var(--pm-line);
}

.num {
  font-variant-numeric: tabular-nums;
  color: #334155;
}

.num--muted {
  color: #94a3b8;
}

.ccy-chip {
  display: inline-block;
  margin-left: 5px;
  padding: 0 5px;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  color: var(--pm-muted);
  background: #f1f5f9;
  border-radius: 4px;
  letter-spacing: 0.03em;
  vertical-align: 1px;
}

.part-jpy {
  font-size: 13px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--pm-indigo);
}

.supplier-text {
  color: #475569;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0 9px;
  font-size: 11.5px;
  font-weight: 600;
  line-height: 20px;
  border-radius: 999px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-pill.is-active {
  color: #047857;
  background: #ecfdf5;
}

.status-pill.is-active .status-dot {
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
}

.status-pill.is-inactive {
  color: #94a3b8;
  background: #f1f5f9;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.row-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.row-btn {
  height: 26px;
  padding: 0 9px !important;
  font-size: 12px;
  font-weight: 600;
  border-radius: 7px;
  border: none !important;
  transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}

.row-btn:hover {
  transform: translateY(-1px);
}

.row-btn--edit {
  color: var(--pm-indigo) !important;
  background: #eef2ff !important;
}

.row-btn--edit:hover {
  color: #fff !important;
  background: var(--pm-indigo) !important;
}

.row-btn--delete {
  width: 26px;
  padding: 0 !important;
  color: var(--pm-rose) !important;
  background: #fff1f2 !important;
}

.row-btn--delete:hover {
  color: #fff !important;
  background: var(--pm-rose) !important;
}

.table-footer {
  display: flex;
  justify-content: center;
  padding: 8px 12px;
  border-top: 1px solid #f1f5f9;
  background: linear-gradient(180deg, #fff, #fafbff);
}

.pagination :deep(.el-pager li),
.pagination :deep(.btn-prev),
.pagination :deep(.btn-next) {
  min-width: 28px;
  height: 28px;
  line-height: 28px;
  font-size: 12px;
  border-radius: 8px;
  background: transparent;
  transition: background 0.15s ease, color 0.15s ease;
}

.pagination :deep(.el-pager li:hover) {
  color: var(--pm-indigo);
  background: #eef2ff;
}

.pagination :deep(.el-pager li.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #7c3aed);
  box-shadow: 0 3px 8px rgba(99, 102, 241, 0.3);
}

.part-input-full {
  width: 100%;
}

@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .header-stats {
    align-self: stretch;
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .part-master-container {
    padding: 6px;
  }

  .page-header {
    padding: 8px 12px;
    border-radius: 12px;
  }

  .main-title {
    font-size: 16px;
  }

  .filter-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding: 10px 12px;
  }

  .filter-inline-summary {
    padding-left: 0;
    border-left: none;
  }

  .stat-card {
    min-width: 0;
    flex: 1;
  }

  .stat-number {
    font-size: 1.1rem;
  }
}
</style>

<!-- 弹窗 teleport 至 body，单独块保证样式命中 -->
<style>
/* ===== 部品編集ダイアログ（784px・2カラム・セクション色分け） ===== */
.part-dlg.el-dialog {
  --pd-ink: #0f172a;
  --pd-text: #334155;
  --pd-muted: #64748b;
  --pd-line: #e2e8f0;
  padding: 0;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.06) inset,
    0 28px 56px -14px rgba(15, 23, 42, 0.32),
    0 12px 24px -8px rgba(15, 23, 42, 0.12);
}

.part-dlg .el-dialog__header {
  padding: 0;
  margin: 0;
}

.part-dlg .el-dialog__headerbtn {
  top: 14px;
  right: 14px;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  transition: background 0.15s ease, transform 0.2s ease;
}

.part-dlg .el-dialog__headerbtn:hover {
  background: rgba(255, 255, 255, 0.18);
  transform: rotate(90deg);
}

.part-dlg .el-dialog__headerbtn .el-dialog__close {
  color: rgba(255, 255, 255, 0.88);
}

.part-dlg .el-dialog__headerbtn:hover .el-dialog__close {
  color: #fff;
}

.part-dlg .el-dialog__body {
  padding: 14px 18px 14px;
  background:
    radial-gradient(600px 200px at 0% 0%, rgba(99, 102, 241, 0.06), transparent 60%),
    radial-gradient(500px 200px at 100% 100%, rgba(139, 92, 246, 0.05), transparent 60%),
    #f5f7fb;
}

.part-dlg .el-dialog__footer {
  padding: 0;
  margin: 0;
}

/* ヘッダー */
.part-dlg__head {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 92% -40%, rgba(255, 255, 255, 0.28) 0, transparent 42%),
    radial-gradient(circle at 6% 140%, rgba(56, 189, 248, 0.3) 0, transparent 34%),
    linear-gradient(135deg, #4f46e5 0%, #7c3aed 58%, #8b5cf6 100%);
  color: #f8fafc;
}

.part-dlg__head-accent {
  height: 3px;
  background: linear-gradient(90deg, #38bdf8, #a5b4fc, #f0abfc);
}

.part-dlg__head-main {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 60px 14px 20px;
}

.part-dlg__head-icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.32);
  box-shadow:
    0 6px 14px rgba(30, 27, 75, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  color: #fff;
}

.part-dlg__head-text {
  min-width: 0;
}

.part-dlg__head-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  line-height: 1.25;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.part-dlg__head-sub {
  margin: 3px 0 0;
  font-size: 11px;
  line-height: 1.35;
  font-weight: 500;
  color: rgba(238, 242, 255, 0.82);
}

.part-dlg__head-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  flex-shrink: 0;
}

.part-dlg__head-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 24px;
  padding: 0 10px;
  font-size: 11.5px;
  font-weight: 700;
  border-radius: 999px;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(8px);
}

.part-dlg__head-chip--code {
  font-family: 'JetBrains Mono', Consolas, 'Courier New', monospace;
  letter-spacing: 0.02em;
}

.part-dlg__head-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.part-dlg__head-chip.is-active {
  color: #d1fae5;
}

.part-dlg__head-chip.is-active .part-dlg__head-dot {
  background: #34d399;
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.3);
}

.part-dlg__head-chip.is-inactive {
  color: #e2e8f0;
}

.part-dlg__head-chip.is-inactive .part-dlg__head-dot {
  background: #94a3b8;
}

/* レイアウト */
.part-dlg__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(0, 1fr);
  gap: 12px;
}

.part-dlg__col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.part-dlg__col > .part-dlg__block:last-child {
  flex: 1;
}

.part-dlg__span-all {
  grid-column: 1 / -1;
}

/* セクションカード（--blk-* で色分け） */
.part-dlg__block {
  --blk-c: #4f46e5;
  --blk-c2: #818cf8;
  --blk-soft: #eef2ff;
  --blk-ring: rgba(79, 70, 229, 0.16);
  position: relative;
  padding: 14px 14px 12px;
  background: #fff;
  border: 1px solid #e8ecf3;
  border-radius: 12px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 4px 14px rgba(15, 23, 42, 0.04);
  overflow: hidden;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.part-dlg__block::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--blk-c), var(--blk-c2));
}

.part-dlg__block:focus-within {
  border-color: color-mix(in srgb, var(--blk-c) 30%, #e8ecf3);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 22px -6px var(--blk-ring);
}

.part-dlg__block--basic {
  --blk-c: #4f46e5;
  --blk-c2: #818cf8;
  --blk-soft: #eef2ff;
  --blk-ring: rgba(79, 70, 229, 0.16);
}

.part-dlg__block--trade {
  --blk-c: #0284c7;
  --blk-c2: #38bdf8;
  --blk-soft: #e0f2fe;
  --blk-ring: rgba(2, 132, 199, 0.16);
}

.part-dlg__block--price {
  --blk-c: #7c3aed;
  --blk-c2: #c084fc;
  --blk-soft: #f3e8ff;
  --blk-ring: rgba(124, 58, 237, 0.16);
}

.part-dlg__block--status {
  --blk-c: #059669;
  --blk-c2: #34d399;
  --blk-soft: #d1fae5;
  --blk-ring: rgba(5, 150, 105, 0.16);
}

.part-dlg__block--remarks {
  --blk-c: #d97706;
  --blk-c2: #fbbf24;
  --blk-soft: #fef3c7;
  --blk-ring: rgba(217, 119, 6, 0.16);
}

.part-dlg__block-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.part-dlg__block-icon {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  border-radius: 7px;
  color: var(--blk-c);
  background: var(--blk-soft);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--blk-c) 18%, transparent);
}

.part-dlg__block-title {
  font-size: 12.5px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #1e293b;
}

/* フォーム項目 */
.part-dlg__form .el-form-item {
  margin-bottom: 12px;
}

.part-dlg__form .el-form-item__label {
  height: auto;
  padding-bottom: 4px;
  margin-bottom: 0 !important;
  font-size: 11.5px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--pd-muted);
}

.part-dlg__form .el-form-item.is-required:not(.is-no-asterisk) > .el-form-item__label::before {
  color: #e11d48;
}

.part-dlg__form .el-form-item__error {
  padding-top: 2px;
  font-size: 11px;
}

.part-dlg__form .part-dlg__fi--mb0.el-form-item {
  margin-bottom: 0;
}

.part-dlg .el-input__wrapper,
.part-dlg .el-select__wrapper {
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 0 0 1px var(--pd-line) inset;
  transition: box-shadow 0.15s ease, background 0.15s ease;
}

.part-dlg .el-input__wrapper:hover,
.part-dlg .el-select__wrapper:hover {
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}

.part-dlg .el-input__wrapper.is-focus,
.part-dlg .el-select__wrapper.is-focused {
  box-shadow:
    0 0 0 1px var(--blk-c, #6366f1) inset,
    0 0 0 3px var(--blk-ring, rgba(99, 102, 241, 0.18));
}

.part-dlg .el-input.is-disabled .el-input__wrapper {
  background: var(--blk-soft, #f1f5f9);
  box-shadow: 0 0 0 1px transparent inset;
}

.part-dlg .el-input.is-disabled .el-input__inner {
  -webkit-text-fill-color: var(--blk-c, #4338ca);
  color: var(--blk-c, #4338ca);
  font-family: 'JetBrains Mono', Consolas, 'Courier New', monospace;
  font-weight: 700;
  cursor: not-allowed;
}

.part-dlg .el-input-number {
  width: 100%;
}

.part-dlg .el-input-number .el-input__inner {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.part-dlg .el-input-number.is-controls-right .el-input-number__increase,
.part-dlg .el-input-number.is-controls-right .el-input-number__decrease {
  background: #f8fafc;
}

.part-dlg .el-input-number.is-controls-right .el-input-number__increase:hover,
.part-dlg .el-input-number.is-controls-right .el-input-number__decrease:hover {
  color: var(--blk-c, #4f46e5);
}

.part-dlg .el-textarea__inner {
  min-height: 56px !important;
  padding: 8px 10px;
  font-size: 12.5px;
  border-radius: 8px;
  box-shadow: 0 0 0 1px var(--pd-line) inset;
  transition: box-shadow 0.15s ease;
}

.part-dlg .el-textarea__inner:hover {
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}

.part-dlg .el-textarea__inner:focus {
  box-shadow:
    0 0 0 1px var(--blk-c, #6366f1) inset,
    0 0 0 3px var(--blk-ring, rgba(99, 102, 241, 0.18));
}

/* セグメントボタン（種別・決済種類・状態） */
.part-dlg__seg.el-radio-group {
  display: flex;
  flex-wrap: nowrap;
  gap: 3px;
  width: 100%;
  padding: 3px;
  background: #f1f5f9;
  border-radius: 9px;
  box-shadow: inset 0 0 0 1px #e8ecf3;
}

.part-dlg__seg .el-radio-button {
  --seg-c: #4f46e5;
  --seg-bg: #eef2ff;
  --seg-line: #c7d2fe;
  flex: 1;
  min-width: 0;
}

.part-dlg__seg .el-radio-button__inner,
.part-dlg__seg .el-radio-button:first-child .el-radio-button__inner,
.part-dlg__seg .el-radio-button:last-child .el-radio-button__inner {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 26px;
  padding: 0 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--pd-muted);
  background: transparent;
  border: none !important;
  border-radius: 7px !important;
  box-shadow: none !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}

.part-dlg__seg .el-radio-button__inner:hover {
  color: var(--pd-text);
  background: rgba(255, 255, 255, 0.7);
}

.part-dlg__seg .el-radio-button.is-active .el-radio-button__inner,
.part-dlg__seg .el-radio-button__original-radio:checked + .el-radio-button__inner {
  color: var(--seg-c);
  background: var(--seg-bg);
  box-shadow:
    inset 0 0 0 1px var(--seg-line),
    0 1px 3px rgba(15, 23, 42, 0.1) !important;
}

.part-dlg__seg--kind .el-radio-button__inner {
  font-weight: 800;
  letter-spacing: 0.04em;
}

.part-dlg__kind--T {
  --seg-c: #0369a1;
  --seg-bg: #e0f2fe;
  --seg-line: #bae6fd;
}

.part-dlg__kind--N {
  --seg-c: #6d28d9;
  --seg-bg: #ede9fe;
  --seg-line: #ddd6fe;
}

.part-dlg__kind--F {
  --seg-c: #b45309;
  --seg-bg: #fef3c7;
  --seg-line: #fde68a;
}

.part-dlg__seg .part-dlg__st--paid {
  --seg-c: #b45309;
  --seg-bg: #fffbeb;
  --seg-line: #fde68a;
}

.part-dlg__seg .part-dlg__st--free {
  --seg-c: #0369a1;
  --seg-bg: #f0f9ff;
  --seg-line: #bae6fd;
}

.part-dlg__seg .part-dlg__st--self {
  --seg-c: #047857;
  --seg-bg: #ecfdf5;
  --seg-line: #a7f3d0;
}

.part-dlg__seg .part-dlg__st--other {
  --seg-c: #475569;
  --seg-bg: #f8fafc;
  --seg-line: #cbd5e1;
}

.part-dlg__seg--status .el-radio-button__inner,
.part-dlg__seg--status .el-radio-button:first-child .el-radio-button__inner,
.part-dlg__seg--status .el-radio-button:last-child .el-radio-button__inner {
  height: 30px;
  font-size: 12.5px;
}

.part-dlg__status--on {
  --seg-c: #047857;
  --seg-bg: #ecfdf5;
  --seg-line: #a7f3d0;
}

.part-dlg__status--off {
  --seg-c: #475569;
  --seg-bg: #f1f5f9;
  --seg-line: #cbd5e1;
}

/* 総単価プレビュー */
.part-preview-jpy {
  position: relative;
  overflow: hidden;
  padding: 10px 14px;
  margin: 2px 0 8px;
  color: #fff;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 60%, #a855f7 100%);
  box-shadow:
    0 8px 18px -6px rgba(124, 58, 237, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.part-preview-jpy::after {
  content: '';
  position: absolute;
  top: -40%;
  right: -10%;
  width: 55%;
  height: 180%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.22) 0, transparent 60%);
  pointer-events: none;
}

.part-preview-jpy__main {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.part-preview-jpy__lbl {
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: rgba(255, 255, 255, 0.9);
}

.part-preview-jpy__val {
  font-size: 1.35rem;
  font-weight: 800;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
}

.part-preview-jpy__formula {
  position: relative;
  z-index: 1;
  margin-top: 2px;
  font-size: 10.5px;
  color: rgba(255, 255, 255, 0.78);
}

.part-dlg__fx-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 0;
  padding: 7px 9px;
  font-size: 10.5px;
  line-height: 1.5;
  color: var(--pd-muted);
  background: #faf5ff;
  border: 1px dashed #d8b4fe;
  border-radius: 8px;
}

.part-dlg__fx-hint-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: #7c3aed;
}

/* フッター */
.part-dlg__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 18px;
  background: #fff;
  border-top: 1px solid var(--pd-line);
}

.part-dlg__footer .el-button + .el-button {
  margin-left: 0;
}

.part-dlg__btn.el-button {
  min-width: 96px;
  height: 34px;
  padding: 0 18px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: 9px;
  transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease, background 0.2s ease;
}

.part-dlg__btn--cancel.el-button {
  color: #475569;
  background: #f1f5f9;
}

.part-dlg__btn--cancel.el-button:hover,
.part-dlg__btn--cancel.el-button:focus-visible {
  color: #334155;
  background: #e2e8f0;
}

.part-dlg__btn--save.el-button {
  color: #fff;
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.32);
}

.part-dlg__btn--save.el-button:hover,
.part-dlg__btn--save.el-button:focus-visible {
  color: #fff;
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
  box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4);
  filter: brightness(1.06);
  transform: translateY(-1px);
}

.part-dlg__btn--save.el-button:active {
  transform: translateY(0);
}

@media (max-width: 820px) {
  .part-dlg.el-dialog {
    width: 94vw !important;
  }

  .part-dlg__grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .part-dlg__head-chips {
    display: none;
  }
}
</style>
