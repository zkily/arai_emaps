<template>
  <div class="pul-page">
    <header class="pul-hero">
      <div class="pul-hero-inner">
        <div class="pul-title-row">
          <span class="pul-title-icon"><el-icon :size="20"><Tickets /></el-icon></span>
          <div>
            <h1 class="pul-title">製品用ラベル設定</h1>
            <p class="pul-subtitle">
              B4横向・通常4×5枚／東北INOAC向け4×4枚。製品マスタから取込後、背番号・バーコード等を編集して印刷します。
            </p>
          </div>
        </div>
        <div class="pul-stat">
          <span class="pul-stat-num">{{ pagination.total }}</span>
          <span class="pul-stat-lbl">登録件数</span>
        </div>
      </div>
    </header>

    <section class="pul-toolbar-card">
      <div class="pul-toolbar">
        <div class="pul-search-wrap">
          <span class="pul-search-label"><el-icon :size="14"><Search /></el-icon> 検索</span>
          <el-input
            v-model="filters.keyword"
            placeholder="製品CD・製品名・品番・納入先で検索"
            clearable
            size="small"
            class="pul-search"
            @input="onKeywordInput"
            @clear="onKeywordClear"
          />
        </div>
        <div class="pul-toolbar-actions">
          <el-button size="small" class="pul-btn pul-btn--refresh" :icon="Refresh" @click="loadList">
            再読込
          </el-button>
          <el-button
            size="small"
            class="pul-btn pul-btn--print"
            :icon="Printer"
            :loading="printingAll"
            :disabled="pagination.total === 0"
            @click="openPrintAllDialog"
          >
            一括印刷
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="pul-btn pul-btn--sync"
            :icon="Download"
            :loading="syncing"
            @click="handleSyncFromMaster"
          >
            マスタ取込
          </el-button>
          <el-button
            v-if="canCreate"
            size="small"
            class="pul-btn pul-btn--create"
            :icon="Plus"
            @click="openDialog()"
          >
            新規登録
          </el-button>
        </div>
      </div>
    </section>

    <section ref="tableWrapRef" class="pul-table-wrap">
      <div class="pul-result-bar">
        <span class="pul-result-text">{{ pagination.total }} 件中 {{ list.length }} 件を表示</span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          :layout="paginationLayout"
          size="small"
          background
          @current-change="loadList"
          @size-change="loadList"
        />
      </div>

      <el-table
        v-loading="loading"
        :data="list"
        stripe
        border
        size="small"
        class="pul-table"
        :header-cell-style="headerCellStyle"
        :default-sort="{ prop: 'master_product_name', order: 'ascending' }"
        :height="tableHeight"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="product_cd" label="製品CD" width="72" :fixed="tableFixed" show-overflow-tooltip />
        <el-table-column
          prop="master_product_name"
          label="製品名（マスタ）"
          min-width="120"
          sortable="custom"
          show-overflow-tooltip
        />
        <el-table-column label="終息" width="56" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_discontinued" type="info" size="small" effect="plain">終</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="製品用製品名" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <el-input
              v-if="canEdit"
              :model-value="row.use_label_product_name || ''"
              size="small"
              @change="(v: string) => saveInlineField(row, { use_label_product_name: v })"
            />
            <span v-else>{{ row.use_label_product_name || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="入数" width="56" align="center">
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.unit_qty ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="品番" min-width="110" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.part_no || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="納入先名" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="pul-dest-cell">
              <span class="pul-readonly-val">{{ row.destination_name || '—' }}</span>
              <el-tag v-if="row.is_inoac_layout" size="small" type="warning" effect="plain" class="pul-inoac-tag">
                4×4
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="用紙色" width="118" align="center">
          <template #default="{ row }">
            <div class="pul-table-color-cell">
              <span class="pul-paper-chip" :style="paperChipStyle(row.paper_color)">
                {{ row.paper_color || '白' }}
              </span>
              <el-select
                v-if="canEdit"
                :model-value="row.paper_color || '白'"
                size="small"
                class="pul-table-color-select"
                @change="(val: string) => saveInlineField(row, { paper_color: val })"
              >
                <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c">
                  <span class="pul-opt-paper" :style="paperChipStyle(c)">{{ c }}</span>
                </el-option>
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="製品名色" width="128" align="center">
          <template #default="{ row }">
            <div class="pul-table-color-cell">
              <span class="pul-name-color-preview">
                <span class="pul-color-dot" :style="{ background: normalizeNameColor(row.product_name_color) }" />
                <span>{{ productNameColorLabel(row.product_name_color) }}</span>
              </span>
              <el-select
                v-if="canEdit"
                :model-value="normalizeNameColor(row.product_name_color)"
                size="small"
                class="pul-table-color-select"
                @change="(val: string) => saveInlineField(row, { product_name_color: val })"
              >
                <el-option
                  v-for="c in PRODUCT_NAME_COLOR_OPTIONS"
                  :key="c.value"
                  :label="c.label"
                  :value="c.value"
                >
                  <span class="pul-opt-color">
                    <span class="pul-color-dot" :style="{ background: c.value }" />
                    {{ c.label }}
                  </span>
                </el-option>
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="背番1" width="72" show-overflow-tooltip>
          <template #default="{ row }">
            <el-input
              v-if="canEdit"
              :model-value="row.back_no_1 || ''"
              size="small"
              @change="(v: string) => saveInlineField(row, { back_no_1: v })"
            />
            <span v-else>{{ row.back_no_1 || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="背番2" width="72" show-overflow-tooltip>
          <template #default="{ row }">
            <el-input
              v-if="canEdit"
              :model-value="row.back_no_2 || ''"
              size="small"
              @change="(v: string) => saveInlineField(row, { back_no_2: v })"
            />
            <span v-else>{{ row.back_no_2 || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="背番3" width="72" show-overflow-tooltip>
          <template #default="{ row }">
            <el-input
              v-if="canEdit"
              :model-value="row.back_no_3 || ''"
              size="small"
              @change="(v: string) => saveInlineField(row, { back_no_3: v })"
            />
            <span v-else>{{ row.back_no_3 || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="バーコード" width="88" show-overflow-tooltip>
          <template #default="{ row }">
            <el-input
              v-if="canEdit"
              :model-value="row.barcode_no || ''"
              size="small"
              @change="(v: string) => saveInlineField(row, { barcode_no: v })"
            />
            <span v-else>{{ row.barcode_no || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="148" :fixed="tableFixedRight" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog(row)">編集</el-button>
            <el-button
              link
              type="success"
              size="small"
              :loading="printing && printingCd === row.product_cd"
              @click="openPrintDialog(row)"
            >
              印刷
            </el-button>
            <el-button
              v-if="canDelete"
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              削除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '製品用ラベル編集' : '製品用ラベル新規登録'"
      :width="editDialogWidth"
      destroy-on-close
      class="pul-dialog"
    >
      <el-form label-width="120px" size="small">
        <el-form-item label="製品CD" required>
          <el-select
            v-model="form.product_cd"
            filterable
            :disabled="isEdit"
            placeholder="製品を選択"
            style="width: 100%"
            :loading="loadingProducts"
            @change="onProductCdChange"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.product_cd"
              :label="`${p.product_cd} — ${p.product_name}`"
              :value="p.product_cd"
              :disabled="!isEdit && p.configured"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="製品名（マスタ）">
          <span>{{ masterInfo.product_name || '—' }}</span>
        </el-form-item>
        <el-form-item label="製品用製品名">
          <el-input v-model="form.use_label_product_name" />
        </el-form-item>
        <el-form-item label="入数">
          <span class="pul-readonly-val">{{ form.unit_qty ?? '—' }}</span>
          <p class="pul-form-hint pul-form-hint--muted">製品マスタから自動取得（マスタ取込で更新）</p>
        </el-form-item>
        <el-form-item label="品番">
          <span class="pul-readonly-val">{{ form.part_no || '—' }}</span>
          <p class="pul-form-hint pul-form-hint--muted">製品マスタから自動取得（マスタ取込で更新）</p>
        </el-form-item>
        <el-form-item label="納入先名">
          <span class="pul-readonly-val">{{ form.destination_name || '—' }}</span>
          <p v-if="formInoacLayout" class="pul-form-hint">この納入先は B4 横向 4×4 レイアウトで印刷されます。</p>
          <p v-else class="pul-form-hint pul-form-hint--muted">製品マスタから自動取得（マスタ取込で更新）</p>
        </el-form-item>
        <el-form-item label="用紙色">
          <el-select v-model="form.paper_color" placeholder="用紙色を選択" style="width: 100%">
            <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c">
              <span class="pul-opt-paper" :style="paperChipStyle(c)">{{ c }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="製品名色">
          <el-select v-model="form.product_name_color" placeholder="文字色を選択" style="width: 100%">
            <el-option
              v-for="c in PRODUCT_NAME_COLOR_OPTIONS"
              :key="c.value"
              :label="c.label"
              :value="c.value"
            >
              <span class="pul-opt-color">
                <span class="pul-color-dot" :style="{ background: c.value }" />
                {{ c.label }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="背番号1">
          <el-input v-model="form.back_no_1" />
        </el-form-item>
        <el-form-item label="背番号2">
          <el-input v-model="form.back_no_2" />
        </el-form-item>
        <el-form-item label="背番号3">
          <el-input v-model="form.back_no_3" />
        </el-form-item>
        <el-form-item label="バーコード番号">
          <el-input v-model="form.barcode_no" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button v-if="isEdit && canEdit" :loading="prefilling" @click="handleImportFromMaster">
          マスタ再取込
        </el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '更新' : '登録' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="printDialogVisible" title="製品用ラベル印刷" :width="printDialogWidth" destroy-on-close>
      <div v-if="printTarget" class="pul-print-body">
        <div class="pul-print-product">
          <span class="pul-print-cd">{{ printTarget.product_cd }}</span>
          <strong>{{ printTarget.use_label_product_name || printTarget.master_product_name }}</strong>
          <span class="pul-print-layout">
            {{ printTarget.is_inoac_layout ? 'B4 横向 4×4（東北INOAC）' : 'B4 横向 4×5（標準）' }}
          </span>
        </div>
        <el-form label-width="100px" size="small">
          <el-form-item label="印刷枚数">
            <el-input-number v-model="printPages" :min="1" :max="50" />
            <span class="pul-print-hint">B4用紙 1枚あたり {{ printPerPage }} 枚（満版）</span>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="printDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="printing" @click="handlePrint">印刷開始</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="printAllDialogVisible" title="一括ラベル印刷" width="420px" destroy-on-close>
      <p class="pul-print-all-lead">
        一覧の全 <strong>{{ printAllCount }}</strong> 件を、納入先ごとのレイアウト（4×5／4×4）で印刷します。
      </p>
      <el-form label-width="100px" size="small">
        <el-form-item label="印刷枚数">
          <el-input-number v-model="printAllPages" :min="1" :max="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="printAllDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="printingAll" @click="handlePrintAll">印刷開始</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Plus, Printer, Refresh, Search, Tickets } from '@element-plus/icons-vue'
import {
  PAPER_COLOR_OPTIONS,
  PRODUCT_NAME_COLOR_OPTIONS,
  createProductUseLabelConfig,
  deleteProductUseLabelConfig,
  fetchAvailableProductsForUseLabel,
  fetchProductUseLabelConfigList,
  fetchProductUseLabelPrefill,
  importProductUseLabelFromMaster,
  productNameColorLabel,
  syncProductUseLabelFromMaster,
  updateProductUseLabelConfig,
  type AvailableProductForUseLabel,
  type ProductUseLabelConfig,
} from '@/api/master/productUseLabelConfig'
import {
  configToPrintInput,
  isInoacDestination,
  printProductUseLabels,
} from '@/views/master/productUseLabel/utils/productUseLabelPrint'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

const headerCellStyle = {
  background: 'linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%)',
  color: '#3730a3',
  fontWeight: '700',
  fontSize: '12px',
  padding: '6px 0',
}

const PAPER_CHIP_STYLES: Record<string, { background: string; border: string; color: string }> = {
  白: { background: '#fff', border: '#cbd5e1', color: '#334155' },
  黄: { background: '#fef9c3', border: '#eab308', color: '#854d0e' },
  ピンク: { background: '#fce7f3', border: '#ec4899', color: '#9d174d' },
  緑: { background: '#dcfce7', border: '#22c55e', color: '#166534' },
  青: { background: '#dbeafe', border: '#3b82f6', color: '#1e40af' },
  オレンジ: { background: '#ffedd5', border: '#f97316', color: '#9a3412' },
}

const loading = ref(false)
const submitting = ref(false)
const syncing = ref(false)
const prefilling = ref(false)
const loadingProducts = ref(false)
const printing = ref(false)
const printingCd = ref('')
const printingAll = ref(false)
const dialogVisible = ref(false)
const printDialogVisible = ref(false)
const printAllDialogVisible = ref(false)
const isEdit = ref(false)
const list = ref<ProductUseLabelConfig[]>([])
const availableProducts = ref<AvailableProductForUseLabel[]>([])
const printTarget = ref<ProductUseLabelConfig | null>(null)
const printPages = ref(1)
const printAllPages = ref(1)
const printAllRows = ref<ProductUseLabelConfig[]>([])
const printAllCount = computed(() => printAllRows.value.length)

const tableWrapRef = ref<HTMLElement | null>(null)
const tableHeight = ref(480)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)

const tableFixed = computed<'left' | false>(() => (viewportWidth.value >= 900 ? 'left' : false))
const tableFixedRight = computed<'right' | false>(() => (viewportWidth.value >= 900 ? 'right' : false))
const paginationLayout = computed(() =>
  viewportWidth.value < 768 ? 'prev, pager, next' : 'sizes, prev, pager, next'
)
const editDialogWidth = computed(() => (viewportWidth.value < 768 ? 'min(640px, 96vw)' : '640px'))
const printDialogWidth = computed(() => (viewportWidth.value < 480 ? 'min(400px, 96vw)' : '420px'))

const printPerPage = computed(() => (printTarget.value?.is_inoac_layout ? 16 : 20))

const filters = reactive({ keyword: '' })
const pagination = reactive({ page: 1, pageSize: 50, total: 0 })
const sortConfig = reactive({ prop: 'master_product_name', order: 'asc' as 'asc' | 'desc' })

const masterInfo = reactive({ product_name: '' })

const form = reactive({
  id: undefined as number | undefined,
  product_cd: '',
  use_label_product_name: '',
  unit_qty: null as number | null,
  part_no: '',
  destination_name: '',
  paper_color: '白',
  product_name_color: '#000000',
  back_no_1: '',
  back_no_2: '',
  back_no_3: '',
  barcode_no: '',
})

const formInoacLayout = computed(() => isInoacDestination(form.destination_name))

const productOptions = computed(() => {
  if (isEdit.value) {
    return availableProducts.value.length
      ? availableProducts.value
      : [{ product_cd: form.product_cd, product_name: masterInfo.product_name, configured: true }]
  }
  return availableProducts.value.filter((p) => !p.configured)
})

let keywordTimer: ReturnType<typeof setTimeout> | null = null

function paperChipStyle(color?: string | null) {
  const s = PAPER_CHIP_STYLES[color || '白'] || PAPER_CHIP_STYLES['白']
  return { background: s.background, border: `1px solid ${s.border}`, color: s.color }
}

function normalizeNameColor(hex?: string | null): string {
  const v = (hex || '#000000').toLowerCase()
  const found = PRODUCT_NAME_COLOR_OPTIONS.find((o) => o.value.toLowerCase() === v)
  return found?.value ?? '#000000'
}

function onKeywordInput() {
  if (keywordTimer) clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => {
    pagination.page = 1
    void loadList()
  }, 350)
}

function onKeywordClear() {
  if (keywordTimer) clearTimeout(keywordTimer)
  pagination.page = 1
  void loadList()
}

function handleSortChange(payload: { prop: string; order: 'ascending' | 'descending' | null }) {
  if (!payload.order) {
    sortConfig.prop = 'master_product_name'
    sortConfig.order = 'asc'
  } else {
    sortConfig.prop = payload.prop || 'master_product_name'
    sortConfig.order = payload.order === 'descending' ? 'desc' : 'asc'
  }
  pagination.page = 1
  void loadList()
}

function resetForm() {
  form.id = undefined
  form.product_cd = ''
  form.use_label_product_name = ''
  form.unit_qty = null
  form.part_no = ''
  form.destination_name = ''
  form.paper_color = '白'
  form.product_name_color = '#000000'
  form.back_no_1 = ''
  form.back_no_2 = ''
  form.back_no_3 = ''
  form.barcode_no = ''
  masterInfo.product_name = ''
}

function fillFormFromRow(row: ProductUseLabelConfig) {
  form.id = row.id
  form.product_cd = row.product_cd
  form.use_label_product_name = row.use_label_product_name || ''
  form.unit_qty = row.unit_qty ?? null
  form.part_no = row.part_no || ''
  form.destination_name = row.destination_name || ''
  form.paper_color = row.paper_color || '白'
  form.product_name_color = row.product_name_color || '#000000'
  form.back_no_1 = row.back_no_1 || ''
  form.back_no_2 = row.back_no_2 || ''
  form.back_no_3 = row.back_no_3 || ''
  form.barcode_no = row.barcode_no || ''
  masterInfo.product_name = row.master_product_name || ''
}

async function loadAvailableProducts() {
  loadingProducts.value = true
  try {
    const res = await fetchAvailableProductsForUseLabel()
    availableProducts.value = res?.data || []
  } finally {
    loadingProducts.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await fetchProductUseLabelConfigList({
      keyword: filters.keyword || undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
      sort_by: sortConfig.prop,
      sort_order: sortConfig.order,
    })
    const data = (res as { list?: ProductUseLabelConfig[]; total?: number }) || res
    list.value = data.list || []
    pagination.total = data.total || 0
  } catch {
    ElMessage.error('一覧の取得に失敗しました')
  } finally {
    loading.value = false
    requestAnimationFrame(updateLayoutMetrics)
  }
}

async function fetchAllListForPrint(): Promise<ProductUseLabelConfig[]> {
  const res = await fetchProductUseLabelConfigList({
    keyword: filters.keyword || undefined,
    page: 1,
    page_size: 200,
    sort_by: sortConfig.prop,
    sort_order: sortConfig.order,
  })
  const first = (res as { list?: ProductUseLabelConfig[]; total?: number }) || res
  const total = first.total || 0
  const rows = [...(first.list || [])]
  if (total > rows.length) {
    const pages = Math.ceil(total / 200)
    for (let p = 2; p <= pages; p++) {
      const more = await fetchProductUseLabelConfigList({
        keyword: filters.keyword || undefined,
        page: p,
        page_size: 200,
        sort_by: sortConfig.prop,
        sort_order: sortConfig.order,
      })
      const chunk = (more as { list?: ProductUseLabelConfig[] }) || more
      rows.push(...(chunk.list || []))
    }
  }
  return rows
}

function updateLayoutMetrics() {
  const wrap = tableWrapRef.value
  if (!wrap) return
  const top = wrap.getBoundingClientRect().top
  const h = window.innerHeight - top - 24
  tableHeight.value = Math.max(320, Math.min(h, 720))
  viewportWidth.value = window.innerWidth
}

async function openDialog(row?: ProductUseLabelConfig) {
  if (row) {
    if (!guardMasterOperation(canEdit)) return
    isEdit.value = true
    fillFormFromRow(row)
  } else {
    if (!guardMasterOperation(canCreate)) return
    isEdit.value = false
    resetForm()
  }
  await loadAvailableProducts()
  dialogVisible.value = true
}

async function onProductCdChange(cd: string) {
  const found = availableProducts.value.find((p) => p.product_cd === cd)
  masterInfo.product_name = found?.product_name || ''
  try {
    const res = await fetchProductUseLabelPrefill(cd)
    const data = res?.data
    if (data) {
      form.use_label_product_name = data.use_label_product_name || masterInfo.product_name
      form.unit_qty = data.unit_qty ?? null
      form.part_no = data.part_no || ''
      form.destination_name = data.destination_name || ''
    }
  } catch {
    /* ignore */
  }
}

async function handleSubmit() {
  if (!form.product_cd?.trim()) {
    ElMessage.warning('製品CDを選択してください')
    return
  }
  submitting.value = true
  try {
    const payload = {
      product_cd: form.product_cd,
      use_label_product_name: form.use_label_product_name,
      paper_color: form.paper_color,
      product_name_color: form.product_name_color,
      back_no_1: form.back_no_1,
      back_no_2: form.back_no_2,
      back_no_3: form.back_no_3,
      barcode_no: form.barcode_no,
    }
    if (isEdit.value && form.id) {
      await updateProductUseLabelConfig(form.id, payload)
      ElMessage.success('更新しました')
    } else {
      await createProductUseLabelConfig(payload)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    await loadList()
    await loadAvailableProducts()
  } catch {
    ElMessage.error(isEdit.value ? '更新に失敗しました' : '登録に失敗しました')
  } finally {
    submitting.value = false
  }
}

async function saveInlineField(row: ProductUseLabelConfig, patch: Partial<ProductUseLabelConfig>) {
  if (!row.id || !guardMasterOperation(canEdit)) return
  try {
    await updateProductUseLabelConfig(row.id, patch)
    Object.assign(row, patch)
  } catch {
    ElMessage.error('保存に失敗しました')
    void loadList()
  }
}

async function handleImportFromMaster() {
  if (!form.product_cd || !guardMasterOperation(canEdit)) return
  prefilling.value = true
  try {
    const res = await importProductUseLabelFromMaster(form.product_cd)
    const data = (res as ProductUseLabelConfig) || res
    fillFormFromRow(data)
    ElMessage.success('マスタから再取込しました')
  } catch {
    ElMessage.error('マスタ取込に失敗しました')
  } finally {
    prefilling.value = false
  }
}

async function handleSyncFromMaster() {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      '製品マスタから取込みます。未登録製品は新規追加、登録済み製品は品番・納入先名・入数をマスタの内容で更新します。よろしいですか？',
      'マスタ取込',
      { type: 'info' }
    )
  } catch {
    return
  }
  syncing.value = true
  try {
    const res = await syncProductUseLabelFromMaster()
    const data = (res as { data?: { added?: number; updated?: number } })?.data
    const added = data?.added ?? 0
    const updated = data?.updated ?? 0
    ElMessage.success(`新規 ${added} 件、マスタ項目更新 ${updated} 件`)
    await loadList()
    await loadAvailableProducts()
  } catch {
    ElMessage.error('マスタ取込に失敗しました')
  } finally {
    syncing.value = false
  }
}

async function handleDelete(row: ProductUseLabelConfig) {
  if (!row.id || !guardMasterOperation(canDelete)) return
  try {
    await ElMessageBox.confirm(`製品 ${row.product_cd} の設定を削除しますか？`, '削除確認', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteProductUseLabelConfig(row.id)
    ElMessage.success('削除しました')
    await loadList()
    await loadAvailableProducts()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

function openPrintDialog(row: ProductUseLabelConfig) {
  printTarget.value = row
  printPages.value = 1
  printDialogVisible.value = true
}

async function handlePrint() {
  if (!printTarget.value) return
  printing.value = true
  printingCd.value = printTarget.value.product_cd
  try {
    await printProductUseLabels(configToPrintInput(printTarget.value), {
      pages: printPages.value,
      copiesPerPage: printPerPage.value,
    })
    printDialogVisible.value = false
  } catch {
    ElMessage.error('印刷の準備に失敗しました')
  } finally {
    printing.value = false
    printingCd.value = ''
  }
}

async function openPrintAllDialog() {
  printingAll.value = true
  try {
    printAllRows.value = await fetchAllListForPrint()
    if (!printAllRows.value.length) {
      ElMessage.info('印刷対象がありません')
      return
    }
    printAllPages.value = 1
    printAllDialogVisible.value = true
  } catch {
    ElMessage.error('印刷データの取得に失敗しました')
  } finally {
    printingAll.value = false
  }
}

async function handlePrintAll() {
  if (!printAllRows.value.length) return
  printingAll.value = true
  try {
    await printProductUseLabels(
      printAllRows.value.map((r) => configToPrintInput(r)),
      { pages: printAllPages.value, copiesPerPage: 1 }
    )
    printAllDialogVisible.value = false
  } catch {
    ElMessage.error('一括印刷に失敗しました')
  } finally {
    printingAll.value = false
  }
}

onMounted(() => {
  void loadList()
  updateLayoutMetrics()
  window.addEventListener('resize', updateLayoutMetrics)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateLayoutMetrics)
  if (keywordTimer) clearTimeout(keywordTimer)
})
</script>

<style scoped>
.pul-page {
  padding: 12px 16px 20px;
  min-height: 100%;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.pul-hero {
  margin-bottom: 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, #312e81 0%, #4338ca 45%, #6366f1 100%);
  color: #fff;
  box-shadow: 0 8px 24px rgba(67, 56, 202, 0.25);
}

.pul-hero-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  flex-wrap: wrap;
}

.pul-title-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.pul-title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
}

.pul-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
}

.pul-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  opacity: 0.9;
  max-width: 640px;
  line-height: 1.45;
}

.pul-stat {
  text-align: center;
  padding: 8px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.12);
}

.pul-stat-num {
  display: block;
  font-size: 22px;
  font-weight: 800;
}

.pul-stat-lbl {
  font-size: 11px;
  opacity: 0.85;
}

.pul-toolbar-card {
  margin-bottom: 10px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.pul-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
}

.pul-search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 200px;
}

.pul-search-label {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.pul-search {
  max-width: 360px;
}

.pul-toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pul-btn {
  font-weight: 600;
}

.pul-btn--refresh {
  color: #475569;
}

.pul-btn--print {
  color: #fff;
  background: linear-gradient(180deg, #4f46e5 0%, #4338ca 100%);
  border: none;
}

.pul-btn--sync {
  color: #1d4ed8;
  border-color: #93c5fd;
}

.pul-btn--create {
  color: #fff;
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
  border: none;
}

.pul-table-wrap {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 8px 10px 10px;
}

.pul-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.pul-result-text {
  font-size: 12px;
  color: #64748b;
}

.pul-paper-chip {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.6;
}

.pul-color-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.12);
  vertical-align: middle;
}

.pul-table-color-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-wrap: nowrap;
  max-width: 100%;
}

.pul-name-color-preview {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
}

.pul-table-color-select {
  width: 28px;
  flex-shrink: 0;
}

.pul-table-color-select :deep(.el-select__wrapper) {
  padding: 0 4px;
  min-height: 24px;
}

.pul-table-color-select :deep(.el-select__selected-item),
.pul-table-color-select :deep(.el-select__placeholder) {
  display: none;
}

.pul-opt-paper {
  display: inline-block;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.8;
}

.pul-opt-color {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.pul-readonly-val {
  color: #475569;
  font-size: 13px;
  word-break: break-all;
}

.pul-dest-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.pul-inoac-tag {
  flex-shrink: 0;
}

.pul-form-hint--muted {
  color: #94a3b8;
}

.pul-form-hint {
  margin: 4px 0 0;
  font-size: 11px;
  color: #b45309;
}

.pul-print-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pul-print-product {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  background: #eef2ff;
  border-radius: 8px;
  border: 1px solid #c7d2fe;
}

.pul-print-cd {
  font-size: 11px;
  color: #64748b;
  font-family: monospace;
}

.pul-print-layout {
  font-size: 11px;
  color: #4338ca;
}

.pul-print-hint {
  margin-left: 8px;
  font-size: 11px;
  color: #94a3b8;
}

.pul-print-all-lead {
  margin: 0 0 12px;
  font-size: 13px;
  color: #334155;
  line-height: 1.5;
}
</style>
