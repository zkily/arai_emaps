<template>
  <div class="stock-panel">
    <div class="kpi-strip">
      <div class="kpi kpi--items">
        <span class="kpi__label">品目数</span>
        <span class="kpi__value">{{ formatNum(rows.length) }}</span>
      </div>
      <div class="kpi kpi--stock">
        <span class="kpi__label">現在庫合計</span>
        <span class="kpi__value">{{ formatNum(totals.stock) }}</span>
      </div>
      <div class="kpi kpi--order">
        <span class="kpi__label">当月注文</span>
        <span class="kpi__value">{{ formatNum(totals.order) }}</span>
      </div>
      <div class="kpi kpi--recv">
        <span class="kpi__label">当月受入</span>
        <span class="kpi__value">{{ formatNum(totals.receiving) }}</span>
      </div>
      <div class="kpi kpi--defect">
        <span class="kpi__label">当月不良</span>
        <span class="kpi__value">{{ formatNum(totals.defect) }}</span>
      </div>
      <div class="kpi kpi--neg" :class="{ 'is-alert': totals.negative > 0 }">
        <span class="kpi__label">マイナス在庫</span>
        <span class="kpi__value">{{ formatNum(totals.negative) }}<small>件</small></span>
      </div>
    </div>

    <el-table
      v-loading="loading"
      :data="rows"
      border
      stripe
      show-summary
      :summary-method="summary"
      :max-height="520"
      size="small"
    >
      <el-table-column prop="supplier_name" label="外注先" width="160" fixed="left" show-overflow-tooltip />
      <el-table-column prop="product_cd" label="製品CD" width="86" align="center" class-name="col-code" />
      <el-table-column prop="product_name" label="製品名" min-width="170" show-overflow-tooltip />
      <el-table-column prop="month_initial" label="当月初期在庫" width="108" align="right" class-name="col-initial">
        <template #default="{ row }">
          <span :class="row.month_initial ? 'qty qty--initial' : 'num-empty'">{{ blankIfZero(row.month_initial) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="month_order_qty" label="当月注文" width="96" align="right" class-name="col-order">
        <template #default="{ row }">
          <span class="qty qty--order">{{ blankIfZero(row.month_order_qty) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="month_receiving_qty" label="当月受入" width="96" align="right" class-name="col-recv">
        <template #default="{ row }">
          <span class="qty qty--recv">{{ blankIfZero(row.month_receiving_qty) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="month_defect_qty" label="当月不良" width="96" align="right" class-name="col-defect">
        <template #default="{ row }">
          <span class="qty qty--defect">{{ blankIfZero(row.month_defect_qty) }}</span>
        </template>
      </el-table-column>
      <el-table-column
        prop="current_stock"
        label="現在庫"
        width="112"
        align="right"
        sortable
        class-name="col-stock"
      >
        <template #default="{ row }">
          <span class="stock-badge" :class="stockClass(row.current_stock)">{{ formatNum(row.current_stock) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="last_order_date" label="最終注文日" width="112" align="center" sortable>
        <template #default="{ row }">
          <span class="date-text">{{ row.last_order_date || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="last_receiving_date" label="最終受入日" width="112" align="center" sortable>
        <template #default="{ row }">
          <span class="date-text">{{ row.last_receiving_date || '—' }}</span>
        </template>
      </el-table-column>
      <template #empty>
        <span>基準日までの台帳データがありません</span>
      </template>
    </el-table>

    <PlatingStockAnalysis v-loading="loading" :rows="rows" :trend="trend" :as-of="asOf" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TableColumnCtx } from 'element-plus'
import { type PlatingStockItem, type PlatingStockTrendItem } from '@/api/outsourcing'
import { useLedger } from './ledgerContext'
import { notifyLedgerError } from './ledgerError'
import PlatingStockAnalysis from './PlatingStockAnalysis.vue'

const ledger = useLedger()

const props = defineProps<{
  asOf: string
  supplierCd?: string
  productCd?: string
}>()

const rows = ref<PlatingStockItem[]>([])
const trend = ref<PlatingStockTrendItem[]>([])
const loading = ref(false)
let loadSeq = 0

const totals = computed(() => {
  let stock = 0
  let order = 0
  let receiving = 0
  let defect = 0
  let negative = 0
  for (const r of rows.value) {
    stock += r.current_stock || 0
    order += r.month_order_qty || 0
    receiving += r.month_receiving_qty || 0
    defect += r.month_defect_qty || 0
    if ((r.current_stock || 0) < 0) negative += 1
  }
  return { stock, order, receiving, defect, negative }
})

function formatNum(value: number | null | undefined): string {
  return Number(value || 0).toLocaleString()
}

function blankIfZero(value: number | null | undefined): string {
  return value ? formatNum(value) : ''
}

function stockClass(value: number | null | undefined): string {
  const n = Number(value || 0)
  if (n < 0) return 'is-neg'
  if (n === 0) return 'is-zero'
  return 'is-pos'
}

function summary({ columns }: { columns: TableColumnCtx<PlatingStockItem>[] }): string[] {
  const sumKeys = [
    'month_initial',
    'month_order_qty',
    'month_receiving_qty',
    'month_defect_qty',
    'current_stock',
  ]
  return columns.map((col, i) => {
    if (i === 0) return '合計'
    if (!sumKeys.includes(col.property)) return ''
    const key = col.property as keyof PlatingStockItem
    return formatNum(rows.value.reduce((s, r) => s + (Number(r[key]) || 0), 0))
  })
}

async function load() {
  if (!props.asOf) return
  const seq = ++loadSeq
  loading.value = true
  const params = {
    asOf: props.asOf,
    supplierCd: props.supplierCd || undefined,
    productCd: props.productCd || undefined,
  }
  try {
    const [res, trendRes] = await Promise.all([
      ledger.getStock(params),
      ledger.getStockTrend(params),
    ])
    if (seq !== loadSeq) return
    rows.value = res?.data || []
    trend.value = trendRes?.data || []
  } catch (error: any) {
    if (seq !== loadSeq) return
    rows.value = []
    trend.value = []
    notifyLedgerError(error, '現在庫の取得に失敗しました')
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

watch(() => [props.asOf, props.supplierCd, props.productCd], load, { immediate: true })

defineExpose({ reload: load })
</script>

<style scoped>
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

.kpi {
  --k: #64748b;
  --k-soft: #f1f5f9;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 7px 12px 7px 14px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #fff 0%, var(--k-soft) 100%);
}

.kpi::before {
  content: '';
  position: absolute;
  top: 8px;
  bottom: 8px;
  left: 0;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--k);
}

.kpi__label {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  color: #64748b;
}

.kpi__value {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
  white-space: nowrap;
  color: var(--k);
  font-variant-numeric: tabular-nums;
}

.kpi__value small {
  margin-left: 2px;
  font-size: 11px;
  font-weight: 600;
}

.kpi--items {
  --k: #0f766e;
  --k-soft: #e6f7f5;
}

.kpi--stock {
  --k: #6d28d9;
  --k-soft: #f5f3ff;
}

.kpi--order {
  --k: #4338ca;
  --k-soft: #eef2ff;
}

.kpi--recv {
  --k: #047857;
  --k-soft: #ecfdf5;
}

.kpi--defect {
  --k: #be123c;
  --k-soft: #fff1f2;
}

.kpi--neg {
  --k: #94a3b8;
  --k-soft: #f8fafc;
}

.kpi--neg.is-alert {
  --k: #dc2626;
  --k-soft: #fee2e2;
  border-color: #fecaca;
}

.qty {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.qty--initial {
  color: #b45309;
}

.qty--order {
  color: #3730a3;
}

.qty--recv {
  color: #047857;
}

.qty--defect {
  color: #be123c;
}

.num-empty {
  color: #cbd5e1;
}

.stock-badge {
  display: inline-block;
  min-width: 48px;
  padding: 1px 8px;
  border-radius: 999px;
  text-align: right;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.stock-badge.is-pos {
  color: #5b21b6;
  background: #ede9fe;
}

.stock-badge.is-zero {
  color: #94a3b8;
  background: #f1f5f9;
}

.stock-badge.is-neg {
  color: #be123c;
  background: #ffe4e6;
}

.date-text {
  font-variant-numeric: tabular-nums;
  color: #475569;
}
</style>
