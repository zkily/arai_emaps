<template>
  <el-drawer
    v-model="visible"
    title="在庫停滞監視"
    direction="rtl"
    size="720px"
    :close-on-click-modal="false"
    class="inventory-stagnation-drawer"
    @open="handleOpen"
  >
    <div class="drawer-body">
      <el-form class="filter-form panel" :inline="true" label-position="right" size="small" label-width="76px">
        <el-form-item label="基準日">
          <el-date-picker
            v-model="asOfDate"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="false"
            :locale="jaLocale"
            class="filter-control control-date"
          />
        </el-form-item>
        <el-form-item label="閾値(>)">
          <el-input-number
            v-model="minQuantity"
            :min="0"
            :step="1"
            class="filter-control control-short"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="連続暦日">
          <el-input-number
            v-model="stableDays"
            :min="2"
            :max="60"
            :step="1"
            class="filter-control control-short"
            controls-position="right"
          />
        </el-form-item>
      </el-form>

      <div class="result-summary panel">
        <el-tag type="primary" effect="light">検出件数 {{ list.length }}</el-tag>
        <el-tag v-if="meta" type="info" effect="plain">
          対象期間：{{ meta.period_start }} ～ {{ meta.period_end }}（{{ meta.stable_calendar_days }}日）
        </el-tag>
        <el-button size="small" class="print-btn" @click="handlePrint">印刷</el-button>
      </div>

      <el-table
        :data="list"
        v-loading="loading"
        border
        size="small"
        class="result-table panel"
        :default-sort="{ prop: 'inventory_column_label', order: 'ascending' }"
        empty-text="該当する停滞在庫は見つかりませんでした"
      >
        <el-table-column prop="inventory_column_label" label="在庫列" width="90" sortable>
          <template #default="{ row }">
            <span class="column-label" :class="inventoryClass(row.inventory_column)">
              {{ inventoryLabel(row.inventory_column) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="製品名" width="120" show-overflow-tooltip sortable />
        <el-table-column
          prop="stable_quantity"
          label="在庫数"
          width="60"
          align="right"
        >
          <template #default="{ row }">
            <span class="quantity-badge">{{ Number(row.stable_quantity).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="期間" min-width="180" align="center">
          <template #default="{ row }">
            {{ row.period_start }} ～ {{ row.period_end }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              @click="$emit('filter-product', row.product_cd)"
            >
              主表で絞込
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <el-button @click="visible = false">閉じる</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import jaLocale from 'element-plus/es/locale/lang/ja'
import {
  getInventoryStagnation,
  type InventoryStagnationResponse,
  type InventoryStagnationRow,
} from '@/api/database'

interface Props {
  modelValue: boolean
}
const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'filter-product', productCd: string): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

const INVENTORY_COLUMN_LABELS: Record<string, string> = {
  cutting_inventory: '切断',
  chamfering_inventory: '面取',
  molding_inventory: '成型',
  plating_inventory: 'メッキ',
  welding_inventory: '溶接',
  inspection_inventory: '検査',
  warehouse_inventory: '倉庫',
  outsourced_warehouse_inventory: '外注倉庫',
  outsourced_plating_inventory: '外注メッキ',
  outsourced_welding_inventory: '外注溶接',
  pre_welding_inspection_inventory: '溶接前検査',
  pre_inspection_inventory: '外注支給前',
  pre_outsourcing_inventory: '外注検査前',
}
const inventoryLabel = (col: string) => INVENTORY_COLUMN_LABELS[col] || col
const inventoryClass = (col: string) => `inventory-chip--${String(col || '').replace(/_/g, '-')}`

const todayJst = () => {
  const now = new Date()
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000)
  const y = jst.getUTCFullYear()
  const m = String(jst.getUTCMonth() + 1).padStart(2, '0')
  const d = String(jst.getUTCDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const asOfDate = ref<string>(todayJst())
const minQuantity = ref<number>(50)
const stableDays = ref<number>(7)

const loading = ref(false)
const list = ref<InventoryStagnationRow[]>([])
const meta = ref<InventoryStagnationResponse['data'] | null>(null)

function sortByProductAndInventoryColumn(rows: InventoryStagnationRow[]) {
  return [...rows].sort((a, b) => {
    const invA = inventoryLabel(a.inventory_column)
    const invB = inventoryLabel(b.inventory_column)
    const invCmp = invA.localeCompare(invB, 'ja')
    if (invCmp !== 0) return invCmp
    return (a.product_name || '').localeCompare(b.product_name || '', 'ja')
  })
}

function handlePrint() {
  if (!list.value.length) {
    ElMessage.warning('印刷対象データがありません')
    return
  }
  const grouped = new Map<string, InventoryStagnationRow[]>()
  for (const row of list.value) {
    const key = inventoryLabel(row.inventory_column)
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(row)
  }
  const sections = Array.from(grouped.entries())
    .map(([groupName, rows]) => {
      const body = rows
        .map((r) => {
          const qty = Number(r.stable_quantity ?? 0).toLocaleString()
          return `<tr><td>${r.product_name || ''}</td><td class="num">${qty}</td><td>${r.period_start} ～ ${r.period_end}</td></tr>`
        })
        .join('')
      return `<section class="group"><h2>${groupName}</h2><table><thead><tr><th>製品名</th><th>在庫数</th><th>期間</th></tr></thead><tbody>${body}</tbody></table></section>`
    })
    .join('')

  const html = `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>在庫停滞監視 印刷</title>
  <style>
    @page { size: A4 portrait; margin: 10mm; }
    body { font-family: "Segoe UI", "Yu Gothic UI", sans-serif; color:#1f2937; font-size:12px; }
    .meta { margin-bottom: 8px; font-size: 11px; color:#4b5563; }
    .group { margin-bottom: 10px; break-inside: avoid; }
    h2 { margin: 0 0 6px; font-size: 13px; }
    table { width:100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #d1d5db; padding: 4px 6px; word-break: break-all; }
    th { background:#f3f4f6; text-align:left; }
    td.num { text-align:right; width: 90px; }
  </style>
</head>
<body onafterprint="window.close()">
  <div class="meta">基準日: ${asOfDate.value} / 閾値(>): ${minQuantity.value} / 連続暦日: ${stableDays.value} / 件数: ${list.value.length}</div>
  ${sections}
</body>
</html>`
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.error('印刷ウィンドウを開けませんでした')
    return
  }
  let hasTriggeredPrint = false
  const triggerPrint = () => {
    if (hasTriggeredPrint) return
    hasTriggeredPrint = true
    try {
      w.focus()
      w.print()
    } catch {
      ElMessage.error('印刷処理に失敗しました')
    }
  }
  w.document.open()
  w.document.write(html)
  w.document.close()
  // wait until the popup has rendered content, then print
  w.onload = () => {
    setTimeout(triggerPrint, 120)
  }
  // fallback for browsers where onload is unreliable with document.write
  setTimeout(triggerPrint, 500)
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getInventoryStagnation({
      as_of: asOfDate.value || undefined,
      min_quantity: minQuantity.value ?? 50,
      stable_calendar_days: stableDays.value ?? 7,
    })
    const data = (res as any)?.data?.data ?? (res as any)?.data
    if (data && Array.isArray(data.list)) {
      list.value = sortByProductAndInventoryColumn(data.list)
      meta.value = data
    } else {
      list.value = []
      meta.value = null
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '在庫停滞の取得に失敗しました')
    list.value = []
    meta.value = null
  } finally {
    loading.value = false
  }
}

function handleOpen() {
  if (!asOfDate.value) asOfDate.value = todayJst()
  fetchList()
}

watch([asOfDate, minQuantity, stableDays], () => {
  if (!visible.value) return
  fetchList()
})
</script>

<style scoped>
.inventory-stagnation-drawer :deep(.el-drawer__body) {
  padding: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f3f6fb 100%);
}

.inventory-stagnation-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 9px 10px 6px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: #ffffffd9;
  backdrop-filter: blur(4px);
}

.inventory-stagnation-drawer :deep(.el-drawer__title) {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 8px 0;
}

.filter-form {
  display: flex;
  flex-wrap: nowrap;
  row-gap: 2px;
  align-items: center;
  overflow-x: auto;
}

.filter-form :deep(.el-form-item) {
  margin-right: 4px;
  margin-bottom: 2px;
}

.filter-form :deep(.el-form-item__label) {
  font-size: 12px;
  padding-right: 4px;
}

.panel {
  background: #fff;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.04);
}

.filter-form.panel {
  padding: 4px 6px 0;
}

.filter-control {
  width: 104px;
}

.control-date {
  width: 90px !important;
  min-width: 90px !important;
  flex: 0 0 90px;
}

.control-date :deep(.el-input),
.control-date :deep(.el-input__wrapper) {
  width: 90px !important;
}

.control-short {
  width: 78px;
}

.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-input-number),
.filter-form :deep(.el-input-number .el-input__wrapper) {
  min-height: 24px;
  height: 24px;
}

.filter-form :deep(.el-input-number__decrease),
.filter-form :deep(.el-input-number__increase) {
  width: 16px;
  font-size: 10px;
}

.result-summary {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  padding: 4px 6px;
  align-items: center;
}

.result-summary :deep(.el-tag) {
  height: 20px;
  line-height: 18px;
  font-size: 11px;
}

.result-table {
  flex: 1;
  overflow: hidden;
}

.result-table :deep(.el-table) {
  --el-table-header-bg-color: #f7f9fc;
  --el-table-border-color: #e9edf5;
  font-size: 12px;
}

.result-table :deep(.el-table__header th) {
  background: #f8fafc;
  color: var(--el-text-color-primary);
  font-size: 11px;
  font-weight: 700;
  padding-top: 3px;
  padding-bottom: 3px;
}

.result-table :deep(.el-table__row td) {
  padding-top: 2px;
  padding-bottom: 2px;
}

.column-label {
  display: inline-block;
  padding: 0 6px;
  border-radius: 999px;
  line-height: 16px;
  font-weight: 600;
  font-size: 11px;
  color: #374151;
  background: #eef2f7;
}

.inventory-chip--cutting-inventory { background: #e0f2fe; color: #075985; }
.inventory-chip--chamfering-inventory { background: #dcfce7; color: #166534; }
.inventory-chip--molding-inventory { background: #fef3c7; color: #92400e; }
.inventory-chip--plating-inventory { background: #ede9fe; color: #5b21b6; }
.inventory-chip--welding-inventory { background: #fee2e2; color: #991b1b; }
.inventory-chip--inspection-inventory { background: #cffafe; color: #155e75; }
.inventory-chip--warehouse-inventory { background: #e5e7eb; color: #374151; }
.inventory-chip--outsourced-warehouse-inventory { background: #fce7f3; color: #9d174d; }
.inventory-chip--outsourced-plating-inventory { background: #fae8ff; color: #86198f; }
.inventory-chip--outsourced-welding-inventory { background: #ffe4e6; color: #9f1239; }
.inventory-chip--pre-welding-inspection-inventory { background: #ecfccb; color: #365314; }
.inventory-chip--pre-inspection-inventory { background: #e0e7ff; color: #3730a3; }
.inventory-chip--pre-outsourcing-inventory { background: #f1f5f9; color: #334155; }

.quantity-badge {
  display: inline-block;
  padding: 0 6px;
  border-radius: 999px;
  font-weight: 700;
  color: #0b5ad9;
  background: #e8f1ff;
  font-size: 11px;
  line-height: 16px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  padding: 0 8px;
}

.drawer-footer :deep(.el-button) {
  min-height: 24px;
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
}

.print-btn {
  margin-left: auto;
  min-height: 22px;
  height: 22px;
  padding: 0 8px;
}
</style>
