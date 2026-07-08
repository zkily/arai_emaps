<template>
  <div class="pli-page fade-in">
    <div class="page-header">
      <h1 class="main-title">
        <el-icon><Printer /></el-icon>
        製品ラベル発行
      </h1>
      <p class="subtitle">現品票（A4縦 2×3）の印刷</p>
    </div>

    <el-card shadow="never" class="search-card">
      <el-form inline @submit.prevent="handleSearch">
        <el-form-item label="製品CD">
          <el-select
            v-model="selectedProductCd"
            filterable
            clearable
            placeholder="製品を選択"
            style="width: 320px"
            @change="handleProductChange"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.product_cd"
              :label="`${p.product_cd} ${p.product_name}`"
              :value="p.product_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" :loading="loading" @click="handleSearch">読込</el-button>
          <el-button :icon="Edit" :disabled="!previewData" @click="openEditDialog">編集</el-button>
          <el-button type="success" :icon="Printer" :disabled="!printData" @click="openPrintConfirm">
            印刷
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="previewData" v-loading="loading" shadow="never" class="preview-card">
      <template #header>プレビュー</template>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="製品CD">{{ previewData.product_cd }}</el-descriptions-item>
        <el-descriptions-item label="マスタ製品名">{{ previewData.master_product_name }}</el-descriptions-item>
        <el-descriptions-item label="加工用製品名">{{ displayData?.label_product_name }}</el-descriptions-item>
        <el-descriptions-item label="入数">{{ displayData?.process_unit_qty ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="用紙色">
          <span class="paper-color-badge">{{ displayData?.paper_color || '白' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="製品名色">
          <span :style="{ color: displayData?.product_name_color || '#000' }">■</span>
          {{ displayData?.product_name_color }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="label-mockup">
        <div class="mockup-title">現品票</div>
        <div class="mockup-body">
          <div class="mockup-product" :style="{ color: displayData?.product_name_color || '#000' }">
            {{ displayData?.label_product_name || '—' }}
          </div>
          <div class="mockup-qty">
            <span>入数</span>
            <strong>{{ displayData?.process_unit_qty ?? '' }}</strong>
          </div>
        </div>
        <div class="mockup-grid">
          <div class="mockup-row mockup-row-top">
            <div v-for="(cell, idx) in printGrid.topRow" :key="`t-${idx}`" class="mockup-cell">
              <div class="mockup-cell-hdr">{{ cell || '　' }}</div>
              <div class="mockup-cell-body" />
            </div>
          </div>
          <div class="mockup-row mockup-row-bottom">
            <div v-for="(cell, idx) in printGrid.bottomRow" :key="`b-${idx}`" class="mockup-cell">
              <div class="mockup-cell-hdr">{{ cell || '　' }}</div>
              <div class="mockup-cell-body" />
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="editVisible" title="印刷前編集" width="640px" destroy-on-close>
      <el-form v-if="editForm" :model="editForm" label-width="120px">
        <el-form-item label="加工用製品名">
          <el-input v-model="editForm.label_product_name" />
        </el-form-item>
        <el-form-item label="加工入数">
          <el-input-number v-model="editForm.process_unit_qty" :min="0" style="width: 160px" />
        </el-form-item>
        <el-form-item label="用紙色">
          <el-select v-model="editForm.paper_color" placeholder="用紙色を選択" style="width: 160px">
            <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="製品名色">
          <el-select v-model="editForm.product_name_color" placeholder="文字色を選択" style="width: 160px">
            <el-option
              v-for="c in PRODUCT_NAME_COLOR_OPTIONS"
              :key="c.value"
              :label="c.label"
              :value="c.value"
            />
          </el-select>
        </el-form-item>
        <el-divider content-position="left">上排（枠1-4）</el-divider>
        <el-form-item v-for="i in 4" :key="`top-${i}`" :label="i === 4 ? '枠4（手直し）' : `枠${i}（成型設備）`">
          <el-input v-model="editForm.process_slots[i - 1]" :readonly="i === 4" />
        </el-form-item>
        <el-divider content-position="left">下排（枠5-8 成型後工程）</el-divider>
        <el-form-item v-for="i in 4" :key="`bottom-${i}`" :label="`枠${i + 4}`">
          <el-input v-model="editForm.process_slots[i + 3]" />
        </el-form-item>
        <el-form-item label="印刷枚数（A4）">
          <el-input-number v-model="printPages" :min="1" :max="20" />
          <span class="hint">1枚あたり 6 ラベル（2列×3行）</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="applyEdit">適用</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="printConfirmVisible" title="印刷確認" width="420px">
      <div v-if="displayData" class="print-confirm-body">
        <p class="confirm-lead">以下の設定で印刷します。用紙をご確認ください。</p>
        <div class="confirm-paper">
          <span class="confirm-label">用紙色</span>
          <span class="confirm-paper-value">{{ displayData.paper_color || '白' }}</span>
        </div>
        <div class="confirm-row">
          <span>製品名</span>
          <strong :style="{ color: displayData.product_name_color || '#000' }">
            {{ displayData.label_product_name }}
          </strong>
        </div>
        <div class="confirm-row">
          <span>入数</span>
          <strong>{{ displayData.process_unit_qty ?? '-' }}</strong>
        </div>
        <div class="confirm-row">
          <span>枚数</span>
          <strong>{{ printPages * 6 }} 枚（A4 × {{ printPages }} 枚）</strong>
        </div>
      </div>
      <template #footer>
        <el-button @click="printConfirmVisible = false">キャンセル</el-button>
        <el-button type="primary" :icon="Printer" @click="doPrint">印刷開始</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Printer, Search } from '@element-plus/icons-vue'
import { fetchProductLabelPreview, type ProductLabelPreview } from '@/api/mes/productLabel'
import {
  PAPER_COLOR_OPTIONS,
  PRODUCT_NAME_COLOR_OPTIONS,
  fetchAvailableProductsForLabel,
  type AvailableProductForLabel,
} from '@/api/master/productLabelConfig'
import {
  buildPrintGridFromSlots,
  previewFromApiData,
  printProductLabels,
  type ProductLabelPrintInput,
} from './utils/productLabelPrint'

const loading = ref(false)
const selectedProductCd = ref('')
const productOptions = ref<AvailableProductForLabel[]>([])
const previewData = ref<ProductLabelPreview | null>(null)
const overrideData = ref<ProductLabelPrintInput | null>(null)
const editVisible = ref(false)
const printConfirmVisible = ref(false)
const printPages = ref(1)

const editForm = ref<ProductLabelPrintInput & { paper_color?: string } | null>(null)

const displayData = computed(() => {
  if (!previewData.value) return null
  const base = overrideData.value || previewFromApiData(previewData.value)
  return {
    ...base,
    paper_color: editForm.value?.paper_color ?? previewData.value.paper_color,
  }
})

const printData = computed(() => {
  if (!previewData.value || !displayData.value) return null
  const slots = displayData.value.process_slots || []
  return {
    label_product_name: displayData.value.label_product_name,
    process_unit_qty: displayData.value.process_unit_qty,
    product_name_color: displayData.value.product_name_color,
    top_row: {
      machine_1: slots[0] || '',
      machine_2: slots[1] || '',
      machine_3: slots[2] || '',
      machine_4_fixed: slots[3] || '手直し',
    },
    process_slots: slots,
  } satisfies ProductLabelPrintInput
})

const printGrid = computed(() => {
  const slots = displayData.value?.process_slots || previewData.value?.process_slots || []
  return buildPrintGridFromSlots(slots)
})

async function loadProductOptions() {
  try {
    const res = await fetchAvailableProductsForLabel()
    productOptions.value = res?.data || []
  } catch {
    productOptions.value = []
  }
}

async function loadPreview(productCd: string) {
  if (!productCd) {
    previewData.value = null
    overrideData.value = null
    return
  }
  loading.value = true
  try {
    const res = await fetchProductLabelPreview(productCd)
    previewData.value = res?.data || null
    overrideData.value = previewData.value ? previewFromApiData(previewData.value) : null
  } catch {
    previewData.value = null
    overrideData.value = null
    ElMessage.error('プレビューの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  if (!selectedProductCd.value) {
    ElMessage.warning('製品CDを選択してください')
    return
  }
  loadPreview(selectedProductCd.value)
}

function handleProductChange() {
  if (selectedProductCd.value) loadPreview(selectedProductCd.value)
}

function openEditDialog() {
  if (!previewData.value) return
  const base = overrideData.value || previewFromApiData(previewData.value)
  const slots = base.process_slots.map((s) => s ?? '')
  while (slots.length < 8) slots.push('')
  if (!String(slots[3] || '').trim()) slots[3] = '手直し'
  editForm.value = {
    ...base,
    paper_color: previewData.value.paper_color || '白',
    process_slots: slots,
  }
  editVisible.value = true
}

function applyEdit() {
  if (!editForm.value || !previewData.value) return
  const slots = [...editForm.value.process_slots]
  while (slots.length < 8) slots.push('')
  if (!String(slots[3] || '').trim()) slots[3] = '手直し'
  overrideData.value = {
    label_product_name: editForm.value.label_product_name,
    process_unit_qty: editForm.value.process_unit_qty,
    product_name_color: editForm.value.product_name_color,
    top_row: {
      machine_1: slots[0] || '',
      machine_2: slots[1] || '',
      machine_3: slots[2] || '',
      machine_4_fixed: slots[3] || '手直し',
    },
    process_slots: slots.map((s) => (String(s || '').trim() ? String(s).trim() : null)),
  }
  if (editForm.value.paper_color) {
    previewData.value.paper_color = editForm.value.paper_color
  }
  editVisible.value = false
  ElMessage.success('編集内容を反映しました')
}

function openPrintConfirm() {
  if (!printData.value) return
  if (!printData.value.label_product_name?.trim()) {
    ElMessage.warning('加工用製品名を入力してください')
    return
  }
  printConfirmVisible.value = true
}

function doPrint() {
  if (!printData.value) return
  printProductLabels(printData.value, { pages: printPages.value, copiesPerPage: 6 })
  printConfirmVisible.value = false
  ElMessage.success('印刷ダイアログを開きました')
}

onMounted(() => {
  loadProductOptions()
})
</script>

<style scoped>
.pli-page {
  padding: 16px 20px 24px;
}
.page-header {
  margin-bottom: 16px;
}
.main-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 22px;
}
.subtitle {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}
.search-card,
.preview-card {
  margin-bottom: 16px;
  border-radius: 8px;
}
.paper-color-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  background: #fef3c7;
  font-weight: 600;
}
.grid-preview {
  margin-top: 16px;
}
.label-mockup {
  margin-top: 14px;
  max-width: 360px;
  border: 1.5px solid #111;
  padding: 8px 8px 6px;
  background: #fff;
}
.mockup-title {
  text-align: center;
  font-size: 13px;
  font-weight: 700;
  text-decoration: underline;
  border: 1px solid #111;
  padding: 3px 6px;
  margin-bottom: 6px;
  letter-spacing: 0.1em;
}
.mockup-body {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  min-height: 44px;
  padding: 0 4px 4px;
}
.mockup-product {
  font-size: 22px;
  font-weight: 800;
  line-height: 1.1;
  flex: 1;
  word-break: break-word;
}
.mockup-qty {
  display: flex;
  align-items: baseline;
  gap: 4px;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 700;
}
.mockup-qty strong {
  font-size: 20px;
  font-weight: 800;
}
.mockup-grid {
  border-top: 1px solid #111;
}
.mockup-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
}
.mockup-row-top {
  border-bottom: 1px solid #111;
}
.mockup-cell {
  border-left: 1px dotted #666;
  min-height: 52px;
}
.mockup-cell:first-child {
  border-left: none;
}
.mockup-cell-hdr {
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 2px;
  min-height: 18px;
}
.mockup-row-top .mockup-cell-hdr {
  font-size: 12px;
}
.mockup-cell-body {
  min-height: 30px;
}
.grid-title {
  font-size: 12px;
  color: #64748b;
  margin: 8px 0 4px;
}
.grid-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
}
.hint {
  margin-left: 8px;
  color: #94a3b8;
  font-size: 12px;
}
.print-confirm-body {
  padding: 4px 0;
}
.confirm-lead {
  margin: 0 0 12px;
  color: #475569;
}
.confirm-paper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
  background: #fef9c3;
  border: 2px solid #eab308;
  border-radius: 8px;
}
.confirm-label {
  font-size: 13px;
  color: #713f12;
}
.confirm-paper-value {
  font-size: 24px;
  font-weight: 800;
  color: #a16207;
}
.confirm-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #f1f5f9;
}
</style>
