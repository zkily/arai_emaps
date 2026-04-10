<template>
  <div class="ppup-page">
    <header class="ppup-hero">
      <div class="ppup-hero__glow" aria-hidden="true" />
      <div class="ppup-hero__inner">
        <div class="ppup-hero__brand">
          <div class="ppup-hero__icon">
            <el-icon :size="18"><Money /></el-icon>
          </div>
          <div class="ppup-hero__text">
            <h1 class="ppup-hero__title">{{ t('bomHome.productUnitPriceTitle') }}</h1>
            <p class="ppup-hero__sub">{{ t('bomHome.productUnitPriceDesc') }}</p>
          </div>
        </div>
      </div>
      <div class="ppup-hero__accent" aria-hidden="true" />
    </header>

    <el-card class="ppup-toolbar-card" shadow="never">
      <div class="ppup-toolbar">
        <el-form :inline="true" class="ppup-filter-form" @submit.prevent>
          <el-form-item label="製品" class="ppup-form-item--product">
            <el-select
              v-model="selectedProductCd"
              filterable
              clearable
              placeholder="製品を選択してください"
              class="ppup-filt-product"
              size="small"
              :loading="productsLoading"
              @change="onProductChange"
            >
              <el-option
                v-for="p in productOptions"
                :key="p.product_cd"
                :label="`${p.product_cd} — ${p.product_name || ''}`"
                :value="p.product_cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item v-if="routeCd" label="ルート" class="ppup-form-item--chip">
            <el-tag class="ppup-chip ppup-chip--route" size="small" effect="dark">{{ routeCd }}</el-tag>
          </el-form-item>
          <el-form-item v-if="bomRevisionLabel" label="BOM" class="ppup-form-item--chip">
            <el-tag class="ppup-chip ppup-chip--bom" size="small">{{ bomRevisionLabel }}</el-tag>
          </el-form-item>
          <el-form-item v-if="selectedProductCd" label="取数" class="ppup-form-item--chip">
            <span class="ppup-take-badge">{{ selectedProductTakeCount }}</span>
            <span v-if="!hasExplicitProductTakeCount" class="ppup-take-fallback">（未設定時 1）</span>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <div v-if="!selectedProductCd" class="ppup-placeholder">
      <el-empty class="ppup-empty" description="製品を選択すると、工程・部品材料・累計単価が表示されます" :image-size="56" />
    </div>

    <div v-else class="ppup-grid">
      <!-- 工程 + 標準加工費 -->
      <el-card class="ppup-data-card ppup-data-card--process" shadow="never">
        <template #header>
          <div class="ppup-data-cap">
            <span class="ppup-data-cap__dot" />
            <span class="ppup-data-cap__title">工程順・標準加工費</span>
            <span class="ppup-data-cap__meta ppup-data-cap__pill">{{ routeSteps.length }} 工程</span>
          </div>
        </template>
        <div v-loading="loadingProcessPanel" class="ppup-card-body">
          <el-empty
            v-if="!loadingProcessPanel && !routeSteps.length"
            class="ppup-empty ppup-empty--sm"
            description="工程ルート未設定"
            :image-size="48"
          />
          <el-table
            v-else
            class="ppup-table ppup-table--process"
            :data="routeSteps"
            stripe
            size="small"
            max-height="calc(100vh - 280px)"
          >
            <el-table-column prop="step_no" label="順" width="44" align="center" />
            <el-table-column prop="process_cd" label="工程CD" min-width="88" show-overflow-tooltip />
            <el-table-column label="工程名" min-width="100" show-overflow-tooltip>
              <template #default="{ row }">{{ row.process_name || '—' }}</template>
            </el-table-column>
            <el-table-column label="標準加工費" width="160" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="stepFees[row.step_no]"
                  :min="0"
                  :precision="2"
                  :step="1"
                  size="small"
                  controls-position="right"
                  class="ppup-fee-input"
                  :disabled="!routeCd || savingStep === row.step_no"
                  @change="scheduleSaveProcessFee(row.step_no)"
                />
              </template>
            </el-table-column>
          </el-table>
          <p v-if="routeSteps.length && routeCd" class="ppup-hint ppup-hint--process">
            標準加工費は入力・変更後に自動で保存され、製品×ルート×工程の標準原価行（加工費）が更新されます。
          </p>
        </div>
      </el-card>

      <!-- 部品・材料 -->
      <el-card class="ppup-data-card ppup-data-card--bom" shadow="never">
        <template #header>
          <div class="ppup-data-cap">
            <span class="ppup-data-cap__dot ppup-data-cap__dot--amber" />
            <span class="ppup-data-cap__title">部品・材料</span>
            <span class="ppup-data-cap__meta ppup-data-cap__pill ppup-data-cap__pill--amber">
              {{ bomComponentRows.length }} 行 · 小計 {{ formatPriceYen(materialPartSubtotal) }}
            </span>
          </div>
        </template>
        <div v-loading="loadingBom" class="ppup-card-body">
          <el-empty
            v-if="!loadingBom && !selectedBomHeaderId"
            class="ppup-empty ppup-empty--sm"
            description="BOMが未登録です（製品BOM表で登録してください）"
            :image-size="48"
          />
          <el-table
            v-else-if="selectedBomHeaderId"
            class="ppup-table ppup-table--bom"
            :data="bomComponentRows"
            stripe
            size="small"
            max-height="calc(100vh - 280px)"
          >
            <el-table-column label="区分" width="68" align="center">
              <template #default="{ row }">
                <el-tag :type="row.kind === 'material' ? 'warning' : 'primary'" size="small">
                  {{ row.kind === 'material' ? '材料' : '部品' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="code" label="CD" min-width="96" show-overflow-tooltip />
            <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip />
            <el-table-column label="所要量" width="100" align="right">
              <template #default="{ row }">
                <el-tooltip :content="row.calcLabel" placement="top" :show-after="400">
                  <span class="ppup-qty-cell">
                    {{ row.qtyEff.toLocaleString('ja-JP', { maximumFractionDigits: 6 }) }}
                    <span v-if="row.scrapRate" class="ppup-qty-sub">（{{ row.qtyPer }}×{{ 100 + row.scrapRate }}%）</span>
                  </span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="uom" label="単位" width="56" align="center" />
            <el-table-column label="使用重量(kg)" width="112" align="right">
              <template #default="{ row }">
                <span v-if="row.kind === 'material'">{{ formatWeightKg(row.weightKg) }}</span>
                <span v-else class="ppup-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="単価" min-width="112" align="right">
              <template #default="{ row }">
                <template v-if="row.kind === 'material'">
                  <div>{{ formatPriceYen(row.pricePerKg) }}<span class="ppup-unit-suffix">/kg</span></div>
                </template>
                <template v-else>
                  <div>
                    {{ formatPriceYen(row.partUnitPrice) }}<span class="ppup-unit-suffix">/{{ row.uom || '個' }}</span>
                  </div>
                </template>
              </template>
            </el-table-column>
            <el-table-column label="行金額" width="112" align="right">
              <template #default="{ row }">
                <el-tooltip :content="row.calcLabel" placement="left" :show-after="300">
                  <strong class="ppup-line-amt">{{ formatPriceYen(row.lineAmount) }}</strong>
                </el-tooltip>
              </template>
            </el-table-column>
          </el-table>
          <p v-if="selectedBomHeaderId && bomComponentRows.length" class="ppup-hint ppup-hint--bom">
            <strong>計算ルール：</strong>材料の行金額は<strong>(使用重量 kg ÷ 選択製品の取数) × 単重単価(¥/kg)</strong>（本・個は
            <code>所要量×長尺単重</code>で kg 化）。取数は製品マスタの「取り数」、未設定は 1。
            一本単価のみの行は <strong>(所要量×一本単価)÷取数</strong>。部品は<strong>所要量×標準単価（円）</strong>—
            <router-link class="ppup-link" to="/master/part">部品マスタ</router-link>
            の登録があれば <strong>単価×為替の円換算</strong>を優先、なければ
            <router-link class="ppup-link" to="/master/product">製品マスタ</router-link>
            の単価。材料単価・長尺単重は
            <router-link class="ppup-link" to="/master/material">材料マスタ</router-link>
            。構成数量は
            <router-link class="ppup-link" to="/master/bom/product-bom">製品BOM表</router-link>
            の明細です。
          </p>
        </div>
      </el-card>

      <!-- 累計（材料 + 工程完了時点） -->
      <el-card class="ppup-data-card ppup-data-card--cumulative ppup-card--wide" shadow="never">
        <template #header>
          <div class="ppup-data-cap">
            <span class="ppup-data-cap__dot ppup-data-cap__dot--cyan" />
            <span class="ppup-data-cap__title">単価累計（工程完了時点）</span>
            <span class="ppup-data-cap__meta ppup-data-cap__pill ppup-data-cap__pill--cyan">材料 + 加工を積み上げ</span>
          </div>
        </template>
        <div class="ppup-card-body">
          <el-table class="ppup-table ppup-table--cumulative" :data="cumulativeStageRows" stripe size="small">
            <el-table-column prop="stage" label="時点" min-width="220" show-overflow-tooltip />
            <el-table-column prop="materialIncrement" label="材料単価" width="110" align="right">
              <template #default="{ row }">
                {{ formatPriceYen(row.materialIncrement) }}
              </template>
            </el-table-column>
            <el-table-column prop="partIncrement" label="部品単価" width="110" align="right">
              <template #default="{ row }">
                {{ formatPriceYen(row.partIncrement) }}
              </template>
            </el-table-column>
            <el-table-column prop="processIncrement" label="工程単価" width="110" align="right">
              <template #default="{ row }">
                {{ formatPriceYen(row.processIncrement) }}
              </template>
            </el-table-column>
            <el-table-column prop="stageIncrement" label="当段増分" width="120" align="right">
              <template #default="{ row }">
                {{ formatPriceYen(row.stageIncrement) }}
              </template>
            </el-table-column>
            <el-table-column prop="cumulative" label="累計単価" width="140" align="right">
              <template #default="{ row }">
                <strong class="ppup-cum-strong">{{ formatPriceYen(row.cumulative) }}</strong>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Money } from '@element-plus/icons-vue'
import request from '@/shared/api/request'
import {
  getUnitPrices,
  createUnitPrice,
  updateUnitPrice,
  deleteUnitPrice,
  type UnitPriceRow,
  type UnitPricePayload,
} from '@/api/master/productProcessUnitPrice'
import { getBomHeaders, getBomTree, type BomLine } from '@/api/master/productBom'
import { getProductList } from '@/api/master/productMaster'
import { getMaterialList } from '@/api/master/materialMaster'
import { getPartList, type PartMasterRow } from '@/api/master/partMaster'
import type { Product, Material } from '@/types/master'

const { t } = useI18n()

interface ProductRouteStepLite {
  step_no: number
  process_cd: string
  process_name?: string
}

interface MaterialCalcFields {
  unit_price?: number
  long_weight?: number
  single_price?: number
}

interface BomDisplayRow {
  kind: 'material' | 'part'
  code: string
  name: string
  consumeStepNo: number | null
  consumeProcessCd: string
  qtyPer: number
  qtyEff: number
  scrapRate: number
  uom: string
  /** 材料：使用重量(kg)。部品：null */
  weightKg: number | null
  /** 材料：単重単価 ¥/kg（表示用）。部品：null */
  pricePerKg: number | null
  /** 部品：1個あたり標準単価。材料：null */
  partUnitPrice: number | null
  /** 試算根拠（ツールチップ用） */
  calcLabel: string
  lineAmount: number
}

interface CumulativeStageRow {
  stage: string
  materialIncrement: number
  partIncrement: number
  processIncrement: number
  stageIncrement: number
  cumulative: number
}

const selectedProductCd = ref('')
const productOptions = ref<Product[]>([])
const productsLoading = ref(false)

const routeSteps = ref<ProductRouteStepLite[]>([])
const routeCd = ref('')
const loadingRouteSteps = ref(false)

const priceRows = ref<UnitPriceRow[]>([])
const loadingPrices = ref(false)
const loadingProcessPanel = computed(() => loadingRouteSteps.value || loadingPrices.value)

/** 各工程の標準加工費（入力バインド） */
const stepFees = reactive<Record<number, number>>({})
const savingStep = ref<number | null>(null)
const feeSaveTimers = new Map<number, ReturnType<typeof setTimeout>>()
const FEE_SAVE_DEBOUNCE_MS = 400

function clearFeeSaveTimers() {
  for (const t of feeSaveTimers.values()) clearTimeout(t)
  feeSaveTimers.clear()
}

function scheduleSaveProcessFee(stepNo: number) {
  const existing = feeSaveTimers.get(stepNo)
  if (existing) clearTimeout(existing)
  feeSaveTimers.set(
    stepNo,
    setTimeout(() => {
      feeSaveTimers.delete(stepNo)
      void saveProcessFee(stepNo, { quiet: true })
    }, FEE_SAVE_DEBOUNCE_MS)
  )
}

const selectedBomHeaderId = ref<number | undefined>(undefined)
const bomRevisionLabel = ref('')
const bomTree = ref<BomLine[]>([])
const loadingBom = ref(false)

const materialNameByCd = ref<Record<string, string>>({})
/** 材料の試算用（単重単価・長尺単重・一本単価） */
const materialCalcByCd = ref<Record<string, MaterialCalcFields>>({})
const productUnitPriceByCd = ref<Record<string, number>>({})
const productNameByCd = ref<Record<string, string>>({})
/** BOM 子品目CD と一致する部品マスタ（円換算標準単価）— 優先して原価試算に使用 */
const partStandardJpyByCd = ref<Record<string, number>>({})
const partNameByCd = ref<Record<string, string>>({})

/** 製品マスタの取り数（材料行の「÷取数」に使用）。未設定・0以下は試算上 1 */
const rawProductTakeCount = computed(() => {
  const p = productOptions.value.find((x) => x.product_cd === selectedProductCd.value)
  return Number(p?.take_count)
})

const hasExplicitProductTakeCount = computed(() => {
  const t = rawProductTakeCount.value
  return t > 0 && Number.isFinite(t)
})

const selectedProductTakeCount = computed(() => (hasExplicitProductTakeCount.value ? rawProductTakeCount.value : 1))

function formatPriceYen(v: number | undefined | null) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Number(v)
  if (Math.abs(n) < 0.0000001) return '-'
  return `¥${n.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function uomIsMassKg(uom: string): boolean {
  const u = (uom || '').trim().toLowerCase().replace(/\s|　/g, '')
  return u === 'kg' || u === 'キロ' || u === 'ｋｇ' || u === 'kgs' || u === 'kilogram'
}

function uomIsMassG(uom: string): boolean {
  const u = (uom || '').trim().toLowerCase().replace(/\s|　/g, '')
  return u === 'g' || u === 'gr' || u === 'グラム' || u === 'ｇ'
}

/**
 * 材料行金額：使用重量(kg) ÷ 親製品の取数 × 単重単価（¥/kg）
 * 取数は製品マスタ take_count。≤0 または未設定は 1。
 * 一本単価のみの行：(所要量×一本単価)÷取数
 */
function materialCostFromLine(
  line: BomLine,
  mat: MaterialCalcFields | undefined,
  takeCount: number
): {
  weightKg: number | null
  pricePerKg: number
  lineAmount: number
  calcLabel: string
} {
  const tc = takeCount > 0 && Number.isFinite(takeCount) ? takeCount : 1
  const qtyPer = Number(line.qty_per) || 0
  const scrap = Number(line.scrap_rate) || 0
  const qtyEff = qtyPer * (1 + scrap / 100)
  const uom = line.uom || ''
  const unitPrice = Number(mat?.unit_price) || 0
  const longW = Number(mat?.long_weight) || 0
  const singleP = Number(mat?.single_price) || 0
  const tcLabel = `÷取数${tc}`

  if (uomIsMassKg(uom)) {
    const w = qtyEff
    return {
      weightKg: w,
      pricePerKg: unitPrice,
      lineAmount: (w / tc) * unitPrice,
      calcLabel: `材料: ${w.toFixed(4)} kg ${tcLabel} × 単重単価（スクラップ${scrap}%込）`,
    }
  }
  if (uomIsMassG(uom)) {
    const kg = qtyEff / 1000
    return {
      weightKg: kg,
      pricePerKg: unitPrice,
      lineAmount: (kg / tc) * unitPrice,
      calcLabel: `材料: ${qtyEff.toFixed(2)} g→${kg.toFixed(6)} kg ${tcLabel} × 単重単価`,
    }
  }
  if (longW > 0 && unitPrice > 0) {
    const w = qtyEff * longW
    return {
      weightKg: w,
      pricePerKg: unitPrice,
      lineAmount: (w / tc) * unitPrice,
      calcLabel: `材料: 所要量${qtyEff.toFixed(4)}${uom || '本'}×長尺単重${longW}kg/本=${w.toFixed(6)}kg ${tcLabel}×単重単価`,
    }
  }
  if (singleP > 0) {
    return {
      weightKg: longW > 0 ? qtyEff * longW : null,
      pricePerKg: unitPrice,
      lineAmount: (qtyEff * singleP) / tc,
      calcLabel: `材料: 所要量×一本単価 ${tcLabel}（一本単価優先）`,
    }
  }
  const wFb = longW > 0 ? qtyEff * longW : null
  const amt =
    wFb != null && unitPrice > 0 ? (wFb / tc) * unitPrice : (qtyEff * unitPrice) / tc
  return {
    weightKg: wFb,
    pricePerKg: unitPrice,
    lineAmount: amt,
    calcLabel: `材料: フォールバック ${tcLabel}×単重単価（長尺単重・一本単価を確認）`,
  }
}

function formatWeightKg(v: number | null | undefined) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Number(v)
  return `${n.toLocaleString('ja-JP', { minimumFractionDigits: 0, maximumFractionDigits: 6 })}`
}

function flattenBomComponents(nodes: BomLine[]): BomLine[] {
  const out: BomLine[] = []
  function walk(items: BomLine[]) {
    for (const it of items) {
      const m = it.component_material_cd && String(it.component_material_cd).trim()
      const p = it.component_product_cd && String(it.component_product_cd).trim()
      if (m || p) out.push(it)
      if (it.children?.length) walk(it.children)
    }
  }
  walk(nodes)
  return out
}

function processRowsForStep(stepNo: number): UnitPriceRow[] {
  return priceRows.value
    .filter((r) => r.step_no === stepNo && String(r.line_type || '').toLowerCase() === 'process')
    .sort((a, b) => (a.line_seq ?? 0) - (b.line_seq ?? 0))
}

function syncStepFeesFromPrices() {
  for (const key of Object.keys(stepFees)) {
    delete stepFees[Number(key)]
  }
  for (const s of routeSteps.value) {
    const rows = processRowsForStep(s.step_no)
    const sum = rows.reduce((acc, r) => acc + (Number(r.increment_unit_price) || 0), 0)
    stepFees[s.step_no] = sum
  }
}

const bomComponentRows = computed((): BomDisplayRow[] => {
  const lines = flattenBomComponents(bomTree.value)
  const rows: BomDisplayRow[] = []
  for (const line of lines) {
    const matCd = line.component_material_cd && String(line.component_material_cd).trim()
    if (matCd) {
      const mc = materialCalcByCd.value[matCd]
      const { weightKg, pricePerKg, lineAmount, calcLabel } = materialCostFromLine(
        line,
        mc,
        selectedProductTakeCount.value
      )
      const qtyPer = Number(line.qty_per) || 0
      const scrap = Number(line.scrap_rate) || 0
      const qtyEff = qtyPer * (1 + scrap / 100)
      rows.push({
        kind: 'material',
        code: matCd,
        name: materialNameByCd.value[matCd] ?? matCd,
        consumeStepNo: Number(line.consume_step_no) > 0 ? Number(line.consume_step_no) : null,
        consumeProcessCd: String(line.consume_process_cd || '').trim(),
        qtyPer,
        qtyEff,
        scrapRate: scrap,
        uom: line.uom || '',
        weightKg,
        pricePerKg,
        partUnitPrice: null,
        calcLabel,
        lineAmount,
      })
      continue
    }
    const pc = line.component_product_cd && String(line.component_product_cd).trim()
    if (pc) {
      const qtyPer = Number(line.qty_per) || 0
      const scrap = Number(line.scrap_rate) || 0
      const qtyEff = qtyPer * (1 + scrap / 100)
      const fromPart = partStandardJpyByCd.value[pc]
      const fromProd = Number(productUnitPriceByCd.value[pc]) || 0
      const partUp = fromPart != null && fromPart > 0 ? fromPart : fromProd
      const nm = partNameByCd.value[pc] ?? productNameByCd.value[pc] ?? pc
      const src =
        fromPart != null && fromPart > 0 ? '部品マスタ（円換算）' : '製品マスタ標準単価'
      rows.push({
        kind: 'part',
        code: pc,
        name: nm,
        consumeStepNo: Number(line.consume_step_no) > 0 ? Number(line.consume_step_no) : null,
        consumeProcessCd: String(line.consume_process_cd || '').trim(),
        qtyPer,
        qtyEff,
        scrapRate: scrap,
        uom: line.uom || '',
        weightKg: null,
        pricePerKg: null,
        partUnitPrice: partUp,
        calcLabel: `部品: 所要量 ${qtyEff.toFixed(4)}（スクラップ${scrap}%込）× ${src}`,
        lineAmount: qtyEff * partUp,
      })
    }
  }
  return rows
})

const materialPartSubtotal = computed(() =>
  bomComponentRows.value.reduce((acc, r) => acc + r.lineAmount, 0)
)

const cumulativeStageRows = computed((): CumulativeStageRow[] => {
  const rows: CumulativeStageRow[] = []
  let cum = 0
  const steps = [...routeSteps.value].sort((a, b) => a.step_no - b.step_no)
  const stepNoByProcessCd = new Map<string, number>()
  for (const s of steps) {
    const cd = String(s.process_cd || '').trim()
    if (cd) stepNoByProcessCd.set(cd, s.step_no)
  }

  const materialCostByStepNo = new Map<number, number>()
  const partCostByStepNo = new Map<number, number>()
  let unassignedMaterialCost = 0
  let unassignedPartCost = 0
  for (const r of bomComponentRows.value) {
    let targetStepNo: number | undefined
    if (r.consumeStepNo != null) {
      targetStepNo = r.consumeStepNo
    } else if (r.consumeProcessCd) {
      targetStepNo = stepNoByProcessCd.get(r.consumeProcessCd)
    }
    if (targetStepNo == null || !Number.isFinite(targetStepNo)) {
      if (r.kind === 'material') unassignedMaterialCost += Number(r.lineAmount) || 0
      else unassignedPartCost += Number(r.lineAmount) || 0
      continue
    }
    if (r.kind === 'material') {
      materialCostByStepNo.set(
        targetStepNo,
        (materialCostByStepNo.get(targetStepNo) || 0) + (Number(r.lineAmount) || 0)
      )
    } else {
      partCostByStepNo.set(targetStepNo, (partCostByStepNo.get(targetStepNo) || 0) + (Number(r.lineAmount) || 0))
    }
  }

  for (const s of steps) {
    const materialInc = materialCostByStepNo.get(s.step_no) || 0
    const partInc = partCostByStepNo.get(s.step_no) || 0
    const processInc = Number(stepFees[s.step_no]) || 0
    const stageInc = materialInc + partInc + processInc
    cum += stageInc
    const name = (s.process_name || s.process_cd || '').trim() || `ステップ${s.step_no}`
    rows.push({
      stage: `〜 ${name} 工程完了時点`,
      materialIncrement: materialInc,
      partIncrement: partInc,
      processIncrement: processInc,
      stageIncrement: stageInc,
      cumulative: cum,
    })
  }
  const unassignedStageInc = unassignedMaterialCost + unassignedPartCost
  if (unassignedStageInc > 0) {
    cum += unassignedStageInc
    rows.push({
      stage: '〜 工程未割当の部品・材料投入',
      materialIncrement: unassignedMaterialCost,
      partIncrement: unassignedPartCost,
      processIncrement: 0,
      stageIncrement: unassignedStageInc,
      cumulative: cum,
    })
  }
  return rows
})

async function loadProductOptions() {
  productsLoading.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 10000, status: 'active' })
    const list = res?.data?.list ?? res?.list ?? []
    productOptions.value = (list as Product[])
      .filter((p) => p.product_cd)
      .sort((a, b) => {
        const nameCmp = String(a.product_name || a.product_cd).localeCompare(
          String(b.product_name || b.product_cd),
          'ja'
        )
        if (nameCmp !== 0) return nameCmp
        return String(a.product_cd).localeCompare(String(b.product_cd), 'ja')
      })
    const up: Record<string, number> = {}
    const nm: Record<string, string> = {}
    for (const p of list as Product[]) {
      if (!p.product_cd) continue
      up[p.product_cd] = Number(p.unit_price) || 0
      nm[p.product_cd] = p.product_name || p.product_cd
    }
    productUnitPriceByCd.value = up
    productNameByCd.value = nm
  } catch {
    productOptions.value = []
    ElMessage.error('製品一覧の取得に失敗しました')
  } finally {
    productsLoading.value = false
  }
}

async function loadPartMasters() {
  const pageSize = 10000
  try {
    const all: PartMasterRow[] = []
    let page = 1
    for (;;) {
      const res = await getPartList({ page, pageSize, status: 1 })
      const list = res?.data?.list ?? []
      const total = res?.data?.total ?? list.length
      all.push(...list)
      if (all.length >= total || list.length < pageSize) break
      page += 1
    }
    const jpy: Record<string, number> = {}
    const nm: Record<string, string> = {}
    for (const p of all) {
      if (!p.part_cd) continue
      jpy[p.part_cd] = Number(p.standard_price_jpy) || 0
      nm[p.part_cd] = p.part_name || p.part_cd
    }
    partStandardJpyByCd.value = jpy
    partNameByCd.value = nm
  } catch {
    partStandardJpyByCd.value = {}
    partNameByCd.value = {}
  }
}

async function loadMaterialPrices() {
  /** 后端 materials 列表 pageSize 上限为 10000，超过会 422 */
  const pageSize = 10000
  try {
    const all: Material[] = []
    let page = 1
    for (;;) {
      const res = await getMaterialList({ page, pageSize })
      const list = (res?.data?.list ?? res?.list ?? []) as Material[]
      const total = res?.data?.total ?? res?.total ?? list.length
      all.push(...list)
      if (all.length >= total || list.length < pageSize) break
      page += 1
    }
    const nm: Record<string, string> = {}
    const calc: Record<string, MaterialCalcFields> = {}
    for (const it of all) {
      if (!it.material_cd) continue
      nm[it.material_cd] = it.material_name || it.material_cd
      calc[it.material_cd] = {
        unit_price: Number(it.unit_price) || 0,
        long_weight: Number(it.long_weight) || 0,
        single_price: Number(it.single_price) || 0,
      }
    }
    materialNameByCd.value = nm
    materialCalcByCd.value = calc
  } catch {
    materialNameByCd.value = {}
    materialCalcByCd.value = {}
  }
}

async function loadRouteForProduct(productCd: string) {
  routeSteps.value = []
  routeCd.value = ''
  if (!productCd?.trim()) return
  loadingRouteSteps.value = true
  try {
    const productRes = await request.get(`/api/master/product/process/routes/${encodeURIComponent(productCd)}`)
    const product = (productRes as { data?: { route_cd?: string } })?.data ?? productRes
    const rc = (product as { route_cd?: string })?.route_cd || ''
    routeCd.value = rc
    if (!rc) return
    const stepsRes = await request.get(
      `/api/master/product/process/routes/${encodeURIComponent(productCd)}/${encodeURIComponent(rc)}`
    )
    const raw = (stepsRes as { data?: unknown })?.data ?? stepsRes
    const steps = Array.isArray(raw) ? (raw as ProductRouteStepLite[]) : []
    routeSteps.value = [...steps].sort((a, b) => (a.step_no ?? 0) - (b.step_no ?? 0))
  } catch {
    routeSteps.value = []
    routeCd.value = ''
  } finally {
    loadingRouteSteps.value = false
  }
}

async function loadPricesForProduct(productCd: string, rc: string) {
  priceRows.value = []
  if (!productCd || !rc) return
  loadingPrices.value = true
  try {
    const res = await getUnitPrices({ product_cd: productCd, route_cd: rc, page: 1, limit: 500 })
    const d = (res as { data?: { list: UnitPriceRow[] } })?.data ?? res
    priceRows.value = (d as { list?: UnitPriceRow[] })?.list ?? []
    syncStepFeesFromPrices()
  } catch {
    priceRows.value = []
    ElMessage.error('標準原価行の取得に失敗しました')
  } finally {
    loadingPrices.value = false
  }
}

async function loadBomForProduct(productCd: string) {
  bomTree.value = []
  selectedBomHeaderId.value = undefined
  bomRevisionLabel.value = ''
  if (!productCd?.trim()) return
  loadingBom.value = true
  try {
    const res = await getBomHeaders({ parent_product_cd: productCd, page: 1, limit: 200 })
    const d = (res as { data?: { list: { id: number; revision?: string; status?: string }[] } })?.data ?? res
    const list = (d as { list?: { id: number; revision?: string; status?: string }[] })?.list ?? []
    const active = list.find((h) => h.status === 'active')
    const header = active ?? list[0]
    if (!header) return
    selectedBomHeaderId.value = header.id
    bomRevisionLabel.value = `Rev.${header.revision ?? '—'} · ${header.status === 'active' ? '有効' : header.status || ''}`
    const treeRes = await getBomTree(header.id)
    const td = (treeRes as { data?: { tree?: BomLine[] } })?.data ?? treeRes
    bomTree.value = (td as { tree?: BomLine[] })?.tree ?? []
  } catch {
    bomTree.value = []
    ElMessage.error('BOMの取得に失敗しました')
  } finally {
    loadingBom.value = false
  }
}

async function onProductChange() {
  clearFeeSaveTimers()
  const cd = selectedProductCd.value
  for (const key of Object.keys(stepFees)) delete stepFees[Number(key)]
  priceRows.value = []
  if (!cd) {
    routeSteps.value = []
    routeCd.value = ''
    bomTree.value = []
    selectedBomHeaderId.value = undefined
    bomRevisionLabel.value = ''
    return
  }
  await loadRouteForProduct(cd)
  const rc = routeCd.value
  await Promise.all([loadPricesForProduct(cd, rc), loadBomForProduct(cd)])
  if (rc) syncStepFeesFromPrices()
}

function persistedProcessFeeSum(stepNo: number): number {
  const rows = processRowsForStep(stepNo)
  return rows.reduce((acc, r) => acc + (Number(r.increment_unit_price) || 0), 0)
}

async function saveProcessFee(stepNo: number, options?: { quiet?: boolean }) {
  const cd = selectedProductCd.value
  const rc = routeCd.value
  if (!cd || !rc) {
    if (!options?.quiet) ElMessage.warning('製品・ルートが未設定です')
    return
  }
  const step = routeSteps.value.find((s) => s.step_no === stepNo)
  const fee = Number(stepFees[stepNo]) || 0
  const persisted = persistedProcessFeeSum(stepNo)
  if (Math.abs(fee - persisted) < 0.000001) return

  savingStep.value = stepNo
  try {
    const rows = processRowsForStep(stepNo)
    const primary = rows[0]
    const payload: UnitPricePayload = {
      product_cd: cd,
      route_cd: rc,
      step_no: stepNo,
      line_seq: 1,
      line_type: 'process',
      description: step?.process_name || step?.process_cd || `Step ${stepNo}`,
      increment_unit_price: fee,
      currency: 'JPY',
      effective_from: null,
      effective_to: null,
      status: 'active',
      bom_line_id: null,
      remarks: '',
    }
    if (primary) {
      await updateUnitPrice(primary.id, payload)
      for (let i = 1; i < rows.length; i++) {
        await deleteUnitPrice(rows[i].id)
      }
      if (!options?.quiet) ElMessage.success('保存しました')
    } else {
      await createUnitPrice(payload)
      if (!options?.quiet) ElMessage.success('登録しました')
    }
    await loadPricesForProduct(cd, rc)
    syncStepFeesFromPrices()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err?.response?.data?.detail || '保存に失敗しました')
  } finally {
    savingStep.value = null
  }
}

onMounted(async () => {
  await Promise.all([loadProductOptions(), loadMaterialPrices(), loadPartMasters()])
})

onBeforeUnmount(() => {
  clearFeeSaveTimers()
})
</script>

<style scoped>
.ppup-page {
  --ppup-violet: #6366f1;
  --ppup-violet-d: #4f46e5;
  --ppup-amber: #f59e0b;
  --ppup-amber-d: #d97706;
  --ppup-cyan: #06b6d4;
  --ppup-cyan-d: #0891b2;
  --ppup-slate-50: #f8fafc;
  --ppup-slate-100: #f1f5f9;
  --ppup-slate-500: #64748b;
  --ppup-slate-600: #475569;
  --ppup-slate-700: #334155;
  --ppup-slate-900: #0f172a;

  font-family:
    'Segoe UI Variable',
    'Segoe UI',
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    'PingFang SC',
    'Microsoft YaHei UI',
    'Microsoft YaHei',
    'Hiragino Sans',
    'Yu Gothic UI',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;

  min-height: 100vh;
  padding: 6px 8px 8px;
  background:
    radial-gradient(ellipse 100% 80% at 100% 0%, rgba(99, 102, 241, 0.12), transparent 50%),
    radial-gradient(ellipse 80% 50% at 0% 100%, rgba(6, 182, 212, 0.08), transparent 45%),
    linear-gradient(165deg, #f1f5f9 0%, #e8eef5 48%, #f0f4f8 100%);
}

.ppup-hero {
  position: relative;
  border-radius: 10px;
  margin-bottom: 6px;
  overflow: hidden;
  box-shadow:
    0 4px 6px -1px rgba(15, 23, 42, 0.08),
    0 12px 28px -8px rgba(79, 70, 229, 0.35);
}

.ppup-hero__glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 120% 100% at 20% -40%, rgba(167, 139, 250, 0.45), transparent 55%);
  pointer-events: none;
}

.ppup-hero__inner {
  position: relative;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(125deg, #312e81 0%, #4338ca 42%, #5b21b6 88%);
}

.ppup-hero__accent {
  height: 2px;
  background: linear-gradient(90deg, #a78bfa, #6366f1 35%, #22d3ee 70%, #fbbf24);
}

.ppup-hero__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.ppup-hero__icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #eef2ff;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.06));
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.ppup-hero__title {
  margin: 0 0 1px;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #fff;
  line-height: 1.25;
}

.ppup-hero__sub {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: rgba(237, 242, 255, 0.92);
}

.ppup-toolbar-card {
  margin-bottom: 6px;
  border-radius: 10px;
  border: 1px solid rgba(99, 102, 241, 0.14);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.98));
  backdrop-filter: blur(8px);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.ppup-toolbar-card :deep(.el-card__body) {
  padding: 6px 10px;
}

.ppup-filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 10px;
}

.ppup-filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.ppup-filter-form :deep(.el-form-item__label) {
  padding-right: 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--ppup-slate-700);
}

.ppup-form-item--product :deep(.el-form-item__label) {
  color: var(--ppup-violet-d);
}

.ppup-filt-product {
  width: min(340px, 90vw);
}

.ppup-toolbar-card :deep(.el-input__inner),
.ppup-toolbar-card :deep(.el-select__wrapper),
.ppup-toolbar-card :deep(.el-select .el-input__inner) {
  font-size: 12px;
}

.ppup-chip {
  border: none;
  font-weight: 700;
  font-size: 12px;
  border-radius: 6px;
}

.ppup-chip--route {
  background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
  color: #fff !important;
}

.ppup-chip--bom {
  background: linear-gradient(180deg, #fff7ed, #ffedd5) !important;
  color: #9a3412 !important;
  border: 1px solid rgba(251, 146, 60, 0.45) !important;
}

.ppup-placeholder {
  padding: 20px 10px;
}

.ppup-empty :deep(.el-empty__description p) {
  font-size: 13px;
  line-height: 1.5;
  color: var(--ppup-slate-700);
}

.ppup-empty--sm :deep(.el-empty__image) {
  margin-bottom: 8px;
}

.ppup-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  align-items: start;
}

.ppup-card--wide {
  grid-column: 1 / -1;
}

.ppup-data-card {
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
  overflow: hidden;
  background: #fff;
}

.ppup-data-card--process {
  border-color: rgba(99, 102, 241, 0.22);
  box-shadow:
    0 2px 10px rgba(15, 23, 42, 0.04),
    inset 3px 0 0 0 var(--ppup-violet);
}

.ppup-data-card--bom {
  border-color: rgba(245, 158, 11, 0.28);
  box-shadow:
    0 2px 10px rgba(15, 23, 42, 0.04),
    inset 3px 0 0 0 var(--ppup-amber);
}

.ppup-data-card--cumulative {
  border-color: rgba(6, 182, 212, 0.25);
  box-shadow:
    0 2px 10px rgba(15, 23, 42, 0.04),
    inset 3px 0 0 0 var(--ppup-cyan);
}

.ppup-data-card--process :deep(.el-card__header) {
  background: linear-gradient(90deg, rgba(238, 242, 255, 0.95), rgba(248, 250, 252, 0.5));
}

.ppup-data-card--bom :deep(.el-card__header) {
  background: linear-gradient(90deg, rgba(255, 251, 235, 0.95), rgba(248, 250, 252, 0.45));
}

.ppup-data-card--cumulative :deep(.el-card__header) {
  background: linear-gradient(90deg, rgba(236, 254, 255, 0.9), rgba(248, 250, 252, 0.45));
}

.ppup-data-card :deep(.el-card__header) {
  padding: 6px 10px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.85);
}

.ppup-data-cap {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  min-height: 22px;
}

.ppup-data-cap__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--ppup-violet), #818cf8);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.ppup-data-cap__dot--amber {
  background: linear-gradient(135deg, #fbbf24, var(--ppup-amber-d));
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.22);
}

.ppup-data-cap__dot--cyan {
  background: linear-gradient(135deg, #22d3ee, var(--ppup-cyan-d));
  box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.22);
}

.ppup-data-cap__title {
  font-size: 13px;
  font-weight: 800;
  color: var(--ppup-slate-900);
  letter-spacing: -0.015em;
}

.ppup-data-cap__meta {
  font-size: 11px;
  font-weight: 600;
  color: var(--ppup-slate-700);
}

.ppup-data-cap__pill {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: var(--ppup-violet-d);
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.ppup-data-cap__pill--amber {
  color: #b45309;
  background: rgba(251, 191, 36, 0.15);
  border-color: rgba(245, 158, 11, 0.28);
}

.ppup-data-cap__pill--cyan {
  color: var(--ppup-cyan-d);
  background: rgba(6, 182, 212, 0.1);
  border-color: rgba(6, 182, 212, 0.22);
}

.ppup-card-body {
  padding: 0;
}

.ppup-table {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.ppup-table :deep(.el-table th.el-table__cell) {
  font-size: 11px;
  font-weight: 800;
  text-transform: none;
  letter-spacing: 0.01em;
  color: var(--ppup-slate-700);
  padding: 5px 6px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9) !important;
}

.ppup-table :deep(.el-table td.el-table__cell) {
  padding: 4px 6px;
}

.ppup-table :deep(.el-table .cell) {
  line-height: 1.45;
  word-break: break-word;
}

.ppup-table--process :deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, #eef2ff, #e0e7ff) !important;
  color: #3730a3;
}

.ppup-table--bom :deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, #fffbeb, #fef3c7) !important;
  color: #92400e;
}

.ppup-table--cumulative :deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, #ecfeff, #cffafe) !important;
  color: #0e7490;
}

.ppup-table :deep(.el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: rgba(248, 250, 252, 0.65) !important;
}

.ppup-table--process :deep(.el-table__row:hover > td.el-table__cell) {
  background-color: rgba(99, 102, 241, 0.07) !important;
}

.ppup-table--bom :deep(.el-table__row:hover > td.el-table__cell) {
  background-color: rgba(245, 158, 11, 0.08) !important;
}

.ppup-table--cumulative :deep(.el-table__row:hover > td.el-table__cell) {
  background-color: rgba(6, 182, 212, 0.07) !important;
}

.ppup-fee-input {
  width: 118px !important;
}

.ppup-fee-input :deep(.el-input-number) {
  width: 100%;
}

.ppup-fee-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2) inset;
}

.ppup-fee-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.45) inset;
}

.ppup-fee-input :deep(.el-input__inner) {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.ppup-muted {
  color: #64748b;
  font-size: 11px;
}

.ppup-qty-cell {
  cursor: default;
}

.ppup-qty-sub {
  display: block;
  font-size: 10px;
  color: var(--ppup-slate-500);
  font-weight: 500;
  line-height: 1.35;
}

.ppup-unit-suffix {
  margin-left: 2px;
  font-size: 10px;
  font-weight: 700;
  color: var(--ppup-slate-600);
}

.ppup-line-amt {
  cursor: help;
  color: var(--ppup-amber-d);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.ppup-link {
  color: var(--ppup-violet-d);
  font-weight: 700;
  text-decoration: none;
}

.ppup-link:hover {
  color: #4338ca;
  text-decoration: underline;
}

.ppup-take-badge {
  display: inline-block;
  min-width: 24px;
  padding: 1px 7px;
  font-size: 12px;
  font-weight: 800;
  color: var(--ppup-violet-d);
  background: linear-gradient(180deg, #eef2ff, #e0e7ff);
  border-radius: 6px;
  text-align: center;
  border: 1px solid rgba(99, 102, 241, 0.22);
}

.ppup-take-fallback {
  margin-left: 4px;
  font-size: 11px;
  color: var(--ppup-slate-700);
}

.ppup-hint {
  margin: 0;
  padding: 6px 10px 7px;
  font-size: 12px;
  line-height: 1.55;
  color: var(--ppup-slate-900);
  border-top: 1px solid rgba(226, 232, 240, 0.85);
}

.ppup-hint--process {
  background: linear-gradient(90deg, rgba(238, 242, 255, 0.55), rgba(248, 250, 252, 0.9));
  border-left: 3px solid var(--ppup-violet);
}

.ppup-hint--bom {
  background: linear-gradient(90deg, rgba(255, 251, 235, 0.55), rgba(248, 250, 252, 0.92));
  border-left: 3px solid var(--ppup-amber);
}

.ppup-hint code {
  font-size: 11px;
  font-family: ui-monospace, 'Cascadia Code', 'Segoe UI Mono', 'Consolas', monospace;
  padding: 1px 5px;
  background: rgba(241, 245, 249, 0.9);
  border-radius: 3px;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.ppup-cum-strong {
  color: var(--ppup-cyan-d);
  font-size: 13px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1100px) {
  .ppup-grid {
    grid-template-columns: 1fr;
  }
}
</style>