<template>
  <div class="plc-page">
    <header class="plc-header">
      <div class="plc-header-main">
        <div class="plc-title-row">
          <span class="plc-title-icon"><el-icon :size="18"><PriceTag /></el-icon></span>
          <div>
            <h1 class="plc-title">成型用ラベル設定</h1>
            <p class="plc-subtitle">現品票（A4縦・2列×3行）の加工用製品名・入数・8枠・印刷色を管理（製品CD末尾「1」のみ）</p>
          </div>
        </div>
        <div class="plc-stat">
          <span class="plc-stat-num">{{ pagination.total }}</span>
          <span class="plc-stat-lbl">登録件数</span>
        </div>
      </div>

      <div class="plc-toolbar">
        <el-input
          v-model="filters.keyword"
          placeholder="製品CD・製品名・加工用製品名で検索"
          clearable
          size="small"
          class="plc-search"
          @input="onKeywordInput"
          @clear="onKeywordClear"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <div class="plc-toolbar-actions">
          <el-button size="small" :icon="Refresh" @click="loadList">再読込</el-button>
          <el-button
            v-if="canEdit"
            size="small"
            type="success"
            plain
            :icon="Download"
            :loading="syncing"
            @click="handleSyncFromMaster"
          >
            マスタ取込
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            type="warning"
            plain
            :icon="RefreshRight"
            :loading="derivingAll"
            @click="handleDeriveAll"
          >
            一括枠導出
          </el-button>
          <el-button v-if="canCreate" size="small" type="primary" :icon="Plus" @click="openDialog()">
            新規登録
          </el-button>
        </div>
      </div>
    </header>

    <section class="plc-table-wrap">
      <div class="plc-result-bar">
        <span>{{ pagination.total }} 件中 {{ list.length }} 件を表示</span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="sizes, prev, pager, next"
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
        class="plc-table"
        :header-cell-style="headerCellStyle"
        height="calc(100vh - 210px)"
      >
        <el-table-column prop="product_cd" label="製品CD" :width="TABLE_COL.productCd" fixed="left" show-overflow-tooltip />
        <el-table-column prop="master_product_name" label="製品名（マスタ）" :min-width="TABLE_COL.masterName" show-overflow-tooltip />
        <el-table-column prop="label_product_name" label="加工用製品名" :min-width="TABLE_COL.labelName" show-overflow-tooltip />
        <el-table-column prop="process_unit_qty" label="入数" :width="TABLE_COL.qty" align="center">
          <template #default="{ row }">{{ row.process_unit_qty ?? '—' }}</template>
        </el-table-column>
        <el-table-column label="用紙色" :width="TABLE_COL.paperColor" align="center">
          <template #default="{ row }">
            <el-select
              v-if="canEdit"
              :model-value="row.paper_color || '白'"
              size="small"
              class="plc-inline-select"
              @change="(val: string) => saveInlineField(row, { paper_color: val })"
            >
              <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c">
                <span class="plc-opt-paper" :style="paperChipStyle(c)">{{ c }}</span>
              </el-option>
            </el-select>
            <span v-else class="plc-paper-chip" :style="paperChipStyle(row.paper_color)">
              {{ row.paper_color || '白' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="製品名色" :width="TABLE_COL.nameColor" align="center">
          <template #default="{ row }">
            <el-select
              v-if="canEdit"
              :model-value="normalizeNameColor(row.product_name_color)"
              size="small"
              class="plc-inline-select"
              @change="(val: string) => saveInlineField(row, { product_name_color: val })"
            >
              <el-option
                v-for="c in PRODUCT_NAME_COLOR_OPTIONS"
                :key="c.value"
                :label="c.label"
                :value="c.value"
              >
                <span class="plc-opt-color">
                  <span class="plc-color-dot" :style="{ background: c.value }" />
                  {{ c.label }}
                </span>
              </el-option>
            </el-select>
            <span v-else class="plc-color-dot" :style="{ background: normalizeNameColor(row.product_name_color) }" />
          </template>
        </el-table-column>

        <el-table-column label="上段固定" :width="TABLE_COL.upperLock" align="center" fixed="left">
          <template #default="{ row }">
            <el-switch
              v-if="canEdit"
              :model-value="!!row.upper_slots_locked"
              size="small"
              inline-prompt
              active-text="ON"
              inactive-text="OFF"
              @change="(val: boolean) => handleUpperLockChange(row, val)"
            />
            <el-tag v-else :type="row.upper_slots_locked ? 'warning' : 'info'" size="small" effect="plain">
              {{ row.upper_slots_locked ? 'ON' : 'OFF' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="上段（枠1〜4）" align="center" class-name="plc-slot-group">
          <el-table-column
            v-for="i in 4"
            :key="`top-${i}`"
            :label="topSlotHeader(i)"
            :width="TABLE_COL.slot"
            align="center"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span :class="['plc-slot-cell', 'plc-slot-top', { 'is-empty': slotValue(row, i - 1) === '—' }]">
                {{ slotValue(row, i - 1) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column label="下段（枠5〜8）" align="center" class-name="plc-slot-group">
          <el-table-column
            v-for="i in 4"
            :key="`bottom-${i}`"
            :label="String(i + 4)"
            :width="TABLE_COL.slot"
            align="center"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span :class="['plc-slot-cell', 'plc-slot-bottom', { 'is-empty': slotValue(row, i + 3) === '—' }]">
                {{ slotValue(row, i + 3) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column label="操作" :width="TABLE_COL.action" fixed="right" align="center">
          <template #default="{ row }">
            <div class="plc-row-actions">
              <el-button
                v-if="canEdit"
                link
                type="primary"
                size="small"
                @click="openDialog(row)"
              >
                編集
              </el-button>
              <el-button
                link
                type="success"
                size="small"
                :loading="printingCd === row.product_cd"
                @click="openPrintDialog(row)"
              >
                印刷
              </el-button>
              <el-dropdown v-if="canEdit || canDelete" trigger="click" @command="(cmd: string) => onRowCommand(cmd, row)">
                <el-button link type="info" size="small">
                  その他<el-icon class="plc-more-icon"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item v-if="canEdit" command="import">マスタ取込</el-dropdown-item>
                    <el-dropdown-item v-if="canEdit" command="derive">枠導出</el-dropdown-item>
                    <el-dropdown-item v-if="canDelete" command="delete" divided>削除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 編集ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '成型用ラベル設定の編集' : '成型用ラベル設定の新規登録'"
      width="720px"
      destroy-on-close
      class="plc-dialog"
    >
      <el-form ref="formRef" :model="form" label-position="top" class="plc-form" size="small">
        <el-form-item label="製品CD" required>
          <el-select
            v-model="form.product_cd"
            filterable
            :disabled="isEdit"
            placeholder="製品を選択してください"
            style="width: 100%"
            @change="onProductCdChange"
          >
            <el-option
              v-for="p in availableProducts"
              :key="p.product_cd"
              :label="`${p.product_cd}　${p.product_name}`"
              :value="p.product_cd"
              :disabled="!isEdit && p.configured"
            />
          </el-select>
        </el-form-item>

        <div class="plc-form-section">
          <div class="plc-section-title">製品マスタ情報（参照）</div>
          <div class="plc-form-grid">
            <el-form-item label="製品名（マスタ）">
              <el-input :model-value="masterInfo.product_name || '—'" readonly />
            </el-form-item>
            <el-form-item label="別名">
              <el-input :model-value="masterInfo.product_alias || '—'" readonly />
            </el-form-item>
            <el-form-item label="工程ルート">
              <el-input :model-value="masterInfo.route_cd || '—'" readonly />
            </el-form-item>
            <el-form-item label="ロットサイズ">
              <el-input :model-value="formatMasterNumber(masterInfo.lot_size)" readonly />
            </el-form-item>
            <el-form-item label="箱入数" class="plc-span-full">
              <el-input :model-value="formatMasterNumber(masterInfo.unit_per_box)" readonly />
            </el-form-item>
          </div>
        </div>

        <div class="plc-form-section">
          <div class="plc-section-title">ラベル印刷設定</div>
          <div class="plc-form-grid">
            <el-form-item label="加工用製品名" class="plc-span-full">
              <el-input v-model="form.label_product_name" placeholder="現場表示用の製品名" />
            </el-form-item>
            <el-form-item label="加工入数">
              <el-input-number
                v-model="form.process_unit_qty"
                :min="0"
                :controls="true"
                placeholder="手動入力"
                style="width: 100%"
              />
              <div class="plc-field-hint">ロットサイズとは別に、現品票の入数を入力してください</div>
            </el-form-item>
            <el-form-item label="用紙色">
              <el-select v-model="form.paper_color" placeholder="用紙色を選択" style="width: 100%">
                <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c">
                  <span class="plc-opt-paper" :style="paperChipStyle(c)">{{ c }}</span>
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
                  <span class="plc-opt-color">
                    <span class="plc-color-dot" :style="{ background: c.value }" />
                    {{ c.label }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </div>
        </div>

        <div class="plc-form-section">
          <div class="plc-section-title plc-section-title-row">
            <span>上段（枠1〜4：成型設備・手直し）</span>
            <el-switch
              v-model="form.upper_slots_locked"
              inline-prompt
              active-text="上段固定ON"
              inactive-text="上段固定OFF"
              size="small"
            />
          </div>
          <p class="plc-field-hint plc-section-hint">
            上段固定ONのとき、枠導出・一括枠導出・マスタ取込では枠1〜4を上書きしません
          </p>
          <div class="plc-form-grid">
            <el-form-item v-for="i in 4" :key="`top-${i}`" :label="slotLabel(i)">
              <el-input
                v-model="form.process_slots[i - 1]"
                :placeholder="slotPlaceholder(i)"
                :readonly="i === 4"
              />
            </el-form-item>
          </div>
        </div>

        <div class="plc-form-section">
          <div class="plc-section-title">下段（枠5〜8：成型後工程）</div>
          <div class="plc-form-grid">
            <el-form-item v-for="i in 4" :key="`bottom-${i}`" :label="`枠${i + 4}`">
              <el-input v-model="form.process_slots[i + 3]" placeholder="工程名" />
            </el-form-item>
          </div>
        </div>

        <div class="plc-form-actions">
          <el-button
            v-if="form.product_cd"
            size="small"
            type="success"
            plain
            :loading="prefilling"
            @click="handleLoadFromMasterInDialog"
          >
            マスタから読込
          </el-button>
          <el-button
            v-if="form.product_cd"
            size="small"
            type="warning"
            plain
            :loading="deriving"
            @click="handleDeriveInDialog"
          >
            枠を再導出
          </el-button>
        </div>
      </el-form>
      <template #footer>
        <div class="plc-dialog-footer">
          <el-button size="small" class="plc-btn-cancel" @click="dialogVisible = false">キャンセル</el-button>
          <el-button size="small" type="primary" class="plc-btn-save" :loading="submitting" @click="handleSubmit">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 印刷ダイアログ -->
    <el-dialog v-model="printDialogVisible" title="現品票の印刷" width="400px" destroy-on-close class="plc-dialog">
      <div v-if="printTarget" class="plc-print-body">
        <div class="plc-print-product">
          <span class="plc-print-cd">{{ printTarget.product_cd }}</span>
          <strong>{{ printTarget.label_product_name || printTarget.master_product_name }}</strong>
        </div>
        <div class="plc-print-paper">
          <span>用紙色</span>
          <span class="plc-print-paper-val" :style="paperChipStyle(printTarget.paper_color)">
            {{ printTarget.paper_color || '白' }}
          </span>
        </div>
        <el-form label-position="top" size="small">
          <el-form-item label="印刷枚数（A4用紙）">
            <el-input-number v-model="printPages" :min="1" :max="20" style="width: 140px" />
            <span class="plc-print-hint">1枚あたり 6 ラベル（2列×3行）</span>
          </el-form-item>
        </el-form>
        <p class="plc-print-note">用紙色をご確認のうえ、印刷を開始してください。</p>
      </div>
      <template #footer>
        <div class="plc-dialog-footer">
          <el-button size="small" class="plc-btn-cancel" @click="printDialogVisible = false">キャンセル</el-button>
          <el-button size="small" type="success" class="plc-btn-print" :icon="Printer" :loading="printing" @click="doPrint">
            印刷開始
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  Download,
  Plus,
  PriceTag,
  Printer,
  Refresh,
  RefreshRight,
  Search,
} from '@element-plus/icons-vue'
import {
  PAPER_COLOR_OPTIONS,
  PRODUCT_NAME_COLOR_OPTIONS,
  createProductLabelConfig,
  deleteProductLabelConfig,
  deriveAllProductLabelProcesses,
  deriveProductLabelProcesses,
  fetchAvailableProductsForLabel,
  fetchProductLabelConfigList,
  fetchProductLabelPrefill,
  importProductLabelFromMaster,
  syncProductLabelFromMaster,
  updateProductLabelConfig,
  type AvailableProductForLabel,
  type ProductLabelConfig,
  type ProductLabelPrefill,
} from '@/api/master/productLabelConfig'
import {
  printProductLabels,
  type ProductLabelPrintInput,
} from '@/views/mes/productionInstruction/productLabel/utils/productLabelPrint'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

const headerCellStyle = {
  background: 'linear-gradient(180deg, #f0fdfa 0%, #ecfeff 100%)',
  color: '#0f766e',
  fontWeight: '700',
  fontSize: '12px',
  padding: '6px 0',
}

/** 表格列宽（px）。固定列用 width，可伸缩列用 minWidth */
const TABLE_COL = {
  productCd: 70,
  masterName: 130,
  labelName: 150,
  qty: 56,
  paperColor: 92,
  nameColor: 100,
  slot: 85,
  upperLock: 88,
  action: 150,
} as const

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
const deriving = ref(false)
const derivingAll = ref(false)
const prefilling = ref(false)
const syncing = ref(false)
const printing = ref(false)
const printingCd = ref('')
const dialogVisible = ref(false)
const printDialogVisible = ref(false)
const isEdit = ref(false)
const list = ref<ProductLabelConfig[]>([])
const availableProducts = ref<AvailableProductForLabel[]>([])
const printTarget = ref<ProductLabelConfig | null>(null)
const printPages = ref(1)

const filters = reactive({ keyword: '' })
const pagination = reactive({ page: 1, pageSize: 50, total: 0 })

let keywordTimer: ReturnType<typeof setTimeout> | null = null

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

const emptySlots = (): (string | null)[] => Array.from({ length: 8 }, () => null)

const masterInfo = reactive({
  product_name: '',
  product_alias: '',
  route_cd: '',
  lot_size: null as number | null,
  unit_per_box: null as number | null,
})

const form = reactive({
  id: undefined as number | undefined,
  product_cd: '',
  label_product_name: '',
  process_unit_qty: null as number | null,
  paper_color: '白' as string | null,
  product_name_color: '#000000',
  upper_slots_locked: false,
  process_slots: emptySlots() as (string | null)[],
})

function paperChipStyle(color?: string | null) {
  const key = color || '白'
  const s = PAPER_CHIP_STYLES[key] || PAPER_CHIP_STYLES['白']
  return {
    background: s.background,
    border: `1px solid ${s.border}`,
    color: s.color,
  }
}

function normalizeNameColor(hex?: string | null): string {
  const v = (hex || '#000000').toLowerCase()
  const found = PRODUCT_NAME_COLOR_OPTIONS.find((o) => o.value.toLowerCase() === v)
  return found?.value ?? '#000000'
}

async function saveInlineField(row: ProductLabelConfig, patch: Partial<ProductLabelConfig>) {
  if (!guardMasterOperation(canEdit) || !row.id) return
  try {
    await updateProductLabelConfig(row.id, patch)
    Object.assign(row, patch)
  } catch {
    ElMessage.error('更新に失敗しました')
    await loadList()
  }
}

function topSlotHeader(i: number): string {
  if (i === 4) return '4（手直し）'
  return String(i)
}

function formatMasterNumber(v: number | null | undefined): string {
  if (v == null || v === ('' as unknown as number)) return '—'
  return String(v)
}

function normalizeSlots(row: ProductLabelConfig): (string | null)[] {
  const slots: (string | null)[] = []
  for (let i = 0; i < 8; i++) {
    const fromArr = row.process_slots?.[i]
    if (fromArr != null && String(fromArr).trim()) {
      slots.push(String(fromArr).trim())
      continue
    }
    const field = `process_slot_${i + 1}` as keyof ProductLabelConfig
    const val = row[field]
    slots.push(val != null && String(val).trim() ? String(val).trim() : null)
  }
  return slots
}

function slotValue(row: ProductLabelConfig, index: number): string {
  const val = normalizeSlots(row)[index]
  return val || '—'
}

function slotLabel(i: number): string {
  if (i <= 3) return `枠${i}（成型設備）`
  if (i === 4) return '枠4（手直し）'
  return `枠${i}（成型後工程）`
}

function slotPlaceholder(i: number): string {
  if (i <= 3) return '設備名'
  if (i === 4) return '手直し'
  return '工程名'
}

function configToPrintInput(row: ProductLabelConfig): ProductLabelPrintInput {
  const slots = normalizeSlots(row)
  if (!String(slots[3] || '').trim()) slots[3] = '手直し'
  return {
    label_product_name: row.label_product_name || row.master_product_name || '',
    process_unit_qty: row.process_unit_qty ?? null,
    product_name_color: row.product_name_color || '#000000',
    top_row: {
      machine_1: slots[0] || '',
      machine_2: slots[1] || '',
      machine_3: slots[2] || '',
      machine_4_fixed: slots[3] || '手直し',
    },
    process_slots: slots,
  }
}

function applyMasterInfoOnly(data: ProductLabelPrefill) {
  masterInfo.product_name = data.master_product_name || ''
  masterInfo.product_alias = data.product_alias || ''
  masterInfo.route_cd = data.route_cd || ''
  masterInfo.lot_size = data.lot_size ?? null
  masterInfo.unit_per_box = data.unit_per_box ?? null
}

function applyPrefill(data: ProductLabelPrefill, includeEditable = true) {
  applyMasterInfoOnly(data)
  if (!includeEditable) return
  form.label_product_name = data.label_product_name || ''
  // 入数は手動入力（ロットサイズとは連動しない）
  form.paper_color = data.paper_color || '白'
  form.product_name_color = data.product_name_color || '#000000'
  form.process_slots = [...(data.process_slots || emptySlots())]
  while (form.process_slots.length < 8) form.process_slots.push(null)
}

function resetMasterInfo() {
  masterInfo.product_name = ''
  masterInfo.product_alias = ''
  masterInfo.route_cd = ''
  masterInfo.lot_size = null
  masterInfo.unit_per_box = null
}

async function loadList() {
  loading.value = true
  try {
    const res = await fetchProductLabelConfigList({
      keyword: filters.keyword || undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    const data = (res as { list?: ProductLabelConfig[]; total?: number }) || res
    list.value = data.list || []
    pagination.total = data.total || 0
  } catch {
    ElMessage.error('一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

async function loadAvailableProducts() {
  try {
    const res = await fetchAvailableProductsForLabel()
    availableProducts.value = res?.data || []
  } catch {
    availableProducts.value = []
  }
}

function resetForm() {
  form.id = undefined
  form.product_cd = ''
  form.label_product_name = ''
  form.process_unit_qty = null
  form.paper_color = '白'
  form.product_name_color = '#000000'
  form.upper_slots_locked = false
  form.process_slots = emptySlots()
  resetMasterInfo()
}

async function loadPrefillFromMaster(showMessage = true, overwriteEditable = true) {
  if (!form.product_cd) {
    ElMessage.warning('製品CDを選択してください')
    return
  }
  prefilling.value = true
  try {
    const res = await fetchProductLabelPrefill(form.product_cd)
    const data = res?.data
    if (!data) {
      ElMessage.error('製品マスタの読込に失敗しました')
      return
    }
    applyPrefill(data, overwriteEditable)
    if (showMessage) {
      ElMessage.success(overwriteEditable ? 'マスタから読込みました' : 'マスタ情報を表示しました')
    }
  } catch {
    ElMessage.error('製品マスタの読込に失敗しました')
  } finally {
    prefilling.value = false
  }
}

async function onProductCdChange() {
  if (!form.product_cd || isEdit.value) return
  await loadPrefillFromMaster(false, true)
}

function openDialog(row?: ProductLabelConfig) {
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  resetForm()
  isEdit.value = !!row
  if (row) {
    form.id = row.id
    form.product_cd = row.product_cd
    form.label_product_name = row.label_product_name || ''
    form.process_unit_qty = row.process_unit_qty ?? null
    form.paper_color = row.paper_color || '白'
    form.product_name_color = row.product_name_color || '#000000'
    form.upper_slots_locked = !!row.upper_slots_locked
    form.process_slots = [...normalizeSlots(row)]
    masterInfo.product_name = row.master_product_name || ''
    void loadPrefillFromMaster(false, false)
  }
  dialogVisible.value = true
}

function openPrintDialog(row: ProductLabelConfig) {
  const name = row.label_product_name || row.master_product_name
  if (!name?.trim()) {
    ElMessage.warning('加工用製品名が未設定のため印刷できません')
    return
  }
  printTarget.value = row
  printPages.value = 1
  printDialogVisible.value = true
}

async function doPrint() {
  if (!printTarget.value) return
  const input = configToPrintInput(printTarget.value)
  if (!input.label_product_name?.trim()) {
    ElMessage.warning('加工用製品名が未設定です')
    return
  }
  printing.value = true
  printingCd.value = printTarget.value.product_cd
  try {
    printProductLabels(input, { pages: printPages.value, copiesPerPage: 6 })
    printDialogVisible.value = false
    ElMessage.success('印刷ダイアログを開きました')
  } catch {
    ElMessage.error('印刷の開始に失敗しました')
  } finally {
    printing.value = false
    printingCd.value = ''
  }
}

async function handleLoadFromMasterInDialog() {
  if (isEdit.value) {
    try {
      await ElMessageBox.confirm(
        '製品マスタの値でラベル設定を上書きします。よろしいですか？',
        '確認',
        { type: 'warning' }
      )
    } catch {
      return
    }
  }
  await loadPrefillFromMaster(true, true)
}

async function handleSubmit() {
  if (isEdit.value ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  if (!form.product_cd) {
    ElMessage.warning('製品CDを選択してください')
    return
  }
  submitting.value = true
  try {
    const payload = {
      product_cd: form.product_cd,
      label_product_name: form.label_product_name || null,
      process_unit_qty: form.process_unit_qty,
      paper_color: form.paper_color,
      product_name_color: form.product_name_color,
      upper_slots_locked: form.upper_slots_locked,
      process_slots: form.process_slots.map((s) => (String(s || '').trim() ? String(s).trim() : null)),
    }
    if (isEdit.value && form.id) {
      await updateProductLabelConfig(form.id, payload)
      ElMessage.success('更新しました')
    } else {
      await createProductLabelConfig(payload)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    await loadList()
    await loadAvailableProducts()
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    submitting.value = false
  }
}

async function handleSyncFromMaster() {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      '製品マスタの未登録製品（製品CD末尾「1」）を一括取込します。枠1〜3：設備、枠4：手直し、枠5〜8：工程を自動設定します。よろしいですか？',
      'マスタ取込',
      { type: 'info' }
    )
    syncing.value = true
    const res = await syncProductLabelFromMaster()
    const added = res?.data?.added ?? 0
    ElMessage.success(`取込完了：${added} 件を追加しました`)
    await loadList()
    await loadAvailableProducts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('マスタ取込に失敗しました')
  } finally {
    syncing.value = false
  }
}

async function handleUpperLockChange(row: ProductLabelConfig, val: boolean) {
  if (!guardMasterOperation(canEdit) || !row.id) return
  const prev = !!row.upper_slots_locked
  try {
    await updateProductLabelConfig(row.id, { upper_slots_locked: val })
    row.upper_slots_locked = val
    ElMessage.success(val ? '上段固定をONにしました' : '上段固定をOFFにしました')
  } catch {
    row.upper_slots_locked = prev
    ElMessage.error('上段固定の更新に失敗しました')
  }
}

async function handleImportFromMaster(row: ProductLabelConfig) {
  if (!guardMasterOperation(canEdit)) return
  try {
    const lockNote = row.upper_slots_locked
      ? '上段固定ONのため、枠1〜4は維持され下段のみ更新されます。'
      : ''
    await ElMessageBox.confirm(
      `製品 ${row.product_cd} の設定を製品マスタと工程ルートで上書き取込します。${lockNote}よろしいですか？`,
      'マスタ取込',
      { type: 'warning' }
    )
    await importProductLabelFromMaster(row.product_cd)
    ElMessage.success('マスタから取込みました')
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('マスタ取込に失敗しました')
  }
}

async function applyDerivedSlots(productCd: string) {
  deriving.value = true
  try {
    const res = await deriveProductLabelProcesses(productCd)
    const data = res as ProductLabelConfig & { upper_preserved?: boolean }
    const slots = data.process_slots
    if (Array.isArray(slots)) {
      form.process_slots = [...slots]
      while (form.process_slots.length < 8) form.process_slots.push(null)
      ElMessage.success(
        data.upper_preserved ? '下段のみ導出しました（上段固定ON）' : '枠を導出しました'
      )
    }
  } catch {
    ElMessage.error('枠導出に失敗しました')
  } finally {
    deriving.value = false
  }
}

async function handleDeriveAll() {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      '登録済みの全製品について枠を再導出します。上段固定ONの製品は枠1〜4を維持し、下段（枠5〜8）のみ更新します。よろしいですか？',
      '一括枠導出',
      { type: 'warning' }
    )
    derivingAll.value = true
    const res = await deriveAllProductLabelProcesses()
    const updated = res?.data?.updated ?? 0
    const skipped = res?.data?.skipped ?? 0
    const upperPreserved = res?.data?.upper_preserved ?? 0
    const lockNote = upperPreserved > 0 ? `、上段固定 ${upperPreserved} 件` : ''
    const suffix = skipped > 0 ? `（スキップ ${skipped} 件）` : ''
    ElMessage.success(`一括導出完了：${updated} 件を更新しました${lockNote}${suffix}`)
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('一括枠導出に失敗しました')
  } finally {
    derivingAll.value = false
  }
}

async function handleDerive(row: ProductLabelConfig) {
  if (!guardMasterOperation(canEdit)) return
  try {
    const lockNote = row.upper_slots_locked
      ? '上段固定ONのため、枠1〜4は維持され下段のみ更新されます。'
      : ''
    await ElMessageBox.confirm(
      `設備能率・工程ルートから8枠を再導出します。${lockNote}よろしいですか？`,
      '枠導出',
      { type: 'warning' }
    )
    deriving.value = true
    const res = await deriveProductLabelProcesses(row.product_cd)
    const preserved = (res as ProductLabelConfig & { upper_preserved?: boolean }).upper_preserved
    ElMessage.success(preserved ? '下段のみ導出しました（上段固定ON）' : '枠を導出しました')
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('枠導出に失敗しました')
  } finally {
    deriving.value = false
  }
}

async function handleDeriveInDialog() {
  if (!form.product_cd) {
    ElMessage.warning('製品CDを選択してください')
    return
  }
  await applyDerivedSlots(form.product_cd)
}

async function handleDelete(row: ProductLabelConfig) {
  if (!guardMasterOperation(canDelete) || !row.id) return
  try {
    await ElMessageBox.confirm(`製品 ${row.product_cd} の設定を削除しますか？`, '削除確認', { type: 'warning' })
    await deleteProductLabelConfig(row.id)
    ElMessage.success('削除しました')
    await loadList()
    await loadAvailableProducts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('削除に失敗しました')
  }
}

function onRowCommand(command: string, row: ProductLabelConfig) {
  if (command === 'import') void handleImportFromMaster(row)
  else if (command === 'derive') void handleDerive(row)
  else if (command === 'delete') void handleDelete(row)
}

onMounted(async () => {
  await Promise.all([loadList(), loadAvailableProducts()])
})

onUnmounted(() => {
  if (keywordTimer) clearTimeout(keywordTimer)
})
</script>

<style scoped>
.plc-page {
  padding: 10px 14px 14px;
  min-height: 100%;
  background: linear-gradient(160deg, #f8fafc 0%, #f0fdfa 40%, #f8fafc 100%);
}

.plc-header {
  margin-bottom: 8px;
}

.plc-header-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.plc-title-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.plc-title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0d9488, #0891b2);
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.3);
}

.plc-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.02em;
}

.plc-subtitle {
  margin: 2px 0 0;
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}

.plc-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 14px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid rgba(13, 148, 136, 0.15);
  box-shadow: 0 1px 6px rgba(13, 148, 136, 0.08);
  flex-shrink: 0;
}

.plc-stat-num {
  font-size: 20px;
  font-weight: 800;
  color: #0d9488;
  line-height: 1.1;
}

.plc-stat-lbl {
  font-size: 10px;
  color: #94a3b8;
}

.plc-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px 10px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid rgba(13, 148, 136, 0.12);
  box-shadow: 0 1px 6px rgba(15, 118, 110, 0.05);
}

.plc-search {
  width: 280px;
}

.plc-toolbar-actions {
  margin-left: auto;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.plc-table-wrap {
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(13, 148, 136, 0.1);
  box-shadow: 0 2px 12px rgba(15, 118, 110, 0.06);
  overflow: hidden;
}

.plc-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 10px;
  font-size: 11px;
  color: #64748b;
  border-bottom: 1px solid #f1f5f9;
}

.plc-table :deep(.el-table__cell) {
  padding: 4px 0;
  font-size: 12px;
}

.plc-paper-chip {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.6;
}

.plc-color-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.12);
  vertical-align: middle;
}

.plc-inline-select {
  width: 100%;
}

.plc-inline-select :deep(.el-select__wrapper) {
  padding: 0 6px;
  min-height: 26px;
}

.plc-opt-paper {
  display: inline-block;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.8;
}

.plc-opt-color {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.plc-slot-cell {
  font-size: 11px;
  font-weight: 600;
  color: #334155;
}

.plc-slot-cell.is-empty {
  color: #cbd5e1;
  font-weight: 400;
}

.plc-slot-top {
  color: #0f766e;
}

.plc-slot-bottom {
  color: #475569;
}

.plc-row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  flex-wrap: nowrap;
}

.plc-more-icon {
  margin-left: 2px;
  font-size: 10px;
}

/* ダイアログ */
.plc-dialog :deep(.el-dialog__header) {
  padding: 12px 16px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, #0d9488 0%, #0891b2 55%, #0284c7 100%);
  border-radius: 12px 12px 0 0;
  margin-right: 0;
}

.plc-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.plc-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.85);
}

.plc-dialog :deep(.el-dialog__body) {
  padding: 10px 14px 6px;
}

.plc-form :deep(.el-form-item__label) {
  color: #0f766e;
  font-weight: 700;
  font-size: 11px;
  padding-bottom: 2px;
  line-height: 1.3;
}

.plc-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.plc-form-section {
  margin-bottom: 10px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.plc-section-title {
  font-size: 11px;
  font-weight: 700;
  color: #0f766e;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px dashed #cbd5e1;
}

.plc-section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border-bottom: none;
  padding-bottom: 0;
  margin-bottom: 4px;
}

.plc-section-hint {
  margin: 0 0 6px;
}

.plc-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 10px;
}

.plc-span-full {
  grid-column: 1 / -1;
}

.plc-form-actions {
  display: flex;
  gap: 8px;
  padding-top: 4px;
}

.plc-field-hint {
  margin-top: 4px;
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.3;
}

.plc-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.plc-btn-cancel {
  border-radius: 8px;
}

.plc-btn-save {
  border-radius: 8px;
  background: linear-gradient(135deg, #0d9488, #0891b2);
  border: none;
}

.plc-btn-print {
  border-radius: 8px;
  background: linear-gradient(135deg, #16a34a, #059669);
  border: none;
}

/* 印刷ダイアログ */
.plc-print-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plc-print-product {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  background: #f0fdfa;
  border-radius: 8px;
  border: 1px solid #99f6e4;
}

.plc-print-cd {
  font-size: 11px;
  color: #64748b;
  font-family: monospace;
}

.plc-print-paper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #fffbeb;
  border: 2px solid #fbbf24;
  border-radius: 8px;
  font-size: 12px;
  color: #92400e;
}

.plc-print-paper-val {
  padding: 2px 12px;
  border-radius: 999px;
  font-size: 16px;
  font-weight: 800;
}

.plc-print-hint {
  margin-left: 8px;
  font-size: 11px;
  color: #94a3b8;
}

.plc-print-note {
  margin: 0;
  font-size: 11px;
  color: #64748b;
}
</style>
