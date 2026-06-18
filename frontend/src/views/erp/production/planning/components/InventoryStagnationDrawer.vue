<template>

  <el-drawer

    v-model="visible"

    direction="rtl"

    size="820px"

    :close-on-click-modal="false"

    :show-close="false"

    class="inventory-stagnation-drawer"

    @open="handleOpen"

  >

    <template #header>

      <div class="isd-header">

        <div class="isd-header__brand">

          <div class="isd-header__icon" aria-hidden="true">

            <el-icon :size="22"><TrendCharts /></el-icon>

          </div>

          <div class="isd-header__text">

            <h2 class="isd-header__title">在庫停滞監視</h2>

            <p class="isd-header__sub">連続日数・閾値超過の在庫を工程別に検出</p>

          </div>

        </div>

        <el-button class="isd-header__close" circle text @click="visible = false">

          <el-icon :size="18"><Close /></el-icon>

        </el-button>

      </div>

    </template>



    <div class="isd-body">

      <!-- 検索条件 -->

      <section class="isd-card isd-filters">

        <div class="isd-card__head">

          <span class="isd-card__head-icon"><el-icon><Filter /></el-icon></span>

          <span class="isd-card__head-title">検索条件</span>

          <el-button

            class="isd-refresh-btn"

            size="small"

            :loading="loading"

            round

            @click="fetchList"

          >

            <el-icon><Refresh /></el-icon>

            再検索

          </el-button>

        </div>

        <el-form class="isd-filter-form" :inline="true" label-position="top" size="default">

          <el-form-item label="基準日">

            <el-date-picker

              v-model="asOfDate"

              type="date"

              format="YYYY-MM-DD"

              value-format="YYYY-MM-DD"

              :clearable="false"

              :locale="jaLocale"

              placeholder="基準日"

              class="isd-date-picker"

            />

          </el-form-item>

          <el-form-item label="在庫数閾値">

            <el-input-number

              v-model="minQuantity"

              :min="0"

              :step="1"

              controls-position="right"

              class="isd-number-input"

            />

            <span class="isd-field-hint">超過のみ表示</span>

          </el-form-item>

          <el-form-item label="連続暦日">

            <el-input-number

              v-model="stableDays"

              :min="2"

              :max="60"

              :step="1"

              controls-position="right"

              class="isd-number-input"

            />

            <span class="isd-field-hint">日以上同一在庫</span>

          </el-form-item>

        </el-form>

      </section>



      <!-- KPI -->

      <section class="isd-kpi">

        <div class="isd-kpi-card isd-kpi-card--primary">

          <div class="isd-kpi-card__icon"><el-icon><WarningFilled /></el-icon></div>

          <div class="isd-kpi-card__body">

            <span class="isd-kpi-card__label">検出件数</span>

            <strong class="isd-kpi-card__value">{{ list.length }}</strong>

          </div>

        </div>

        <div class="isd-kpi-card">

          <div class="isd-kpi-card__icon isd-kpi-card__icon--blue"><el-icon><Grid /></el-icon></div>

          <div class="isd-kpi-card__body">

            <span class="isd-kpi-card__label">対象工程</span>

            <strong class="isd-kpi-card__value">{{ processSummary.length }}</strong>

          </div>

        </div>

        <div class="isd-kpi-card">

          <div class="isd-kpi-card__icon isd-kpi-card__icon--violet"><el-icon><Box /></el-icon></div>

          <div class="isd-kpi-card__body">

            <span class="isd-kpi-card__label">製品数</span>

            <strong class="isd-kpi-card__value">{{ uniqueProductCount }}</strong>

          </div>

        </div>

        <div v-if="meta" class="isd-kpi-card isd-kpi-card--wide">

          <div class="isd-kpi-card__icon isd-kpi-card__icon--slate"><el-icon><Calendar /></el-icon></div>

          <div class="isd-kpi-card__body">

            <span class="isd-kpi-card__label">対象期間</span>

            <strong class="isd-kpi-card__value isd-kpi-card__value--sm">

              {{ meta.period_start }} ～ {{ meta.period_end }}

              <span class="isd-kpi-card__badge">{{ meta.stable_calendar_days }} 日</span>

            </strong>

          </div>

        </div>

      </section>



      <!-- 工程サマリー -->

      <section v-if="processSummary.length" class="isd-process-chips">

        <button

          v-for="item in processSummary"

          :key="item.column"

          type="button"

          class="isd-process-chip"

          :class="[inventoryChipClass(item.column), { 'is-active': activeProcessFilter === item.column }]"

          @click="toggleProcessFilter(item.column)"

        >

          <span class="isd-process-chip__label">{{ item.label }}</span>

          <span class="isd-process-chip__count">{{ item.count }}</span>

        </button>

        <button

          v-if="activeProcessFilter"

          type="button"

          class="isd-process-chip isd-process-chip--clear"

          @click="activeProcessFilter = null"

        >

          すべて表示

        </button>

      </section>



      <!-- ツールバー -->

      <section class="isd-toolbar">

        <span class="isd-toolbar__info">

          <template v-if="filteredList.length">

            {{ filteredList.length }} 件を表示中

            <template v-if="activeProcessFilter">（{{ inventoryLabel(activeProcessFilter) }} で絞込）</template>

          </template>

          <template v-else-if="!loading">該当データなし</template>

        </span>

        <div class="isd-toolbar__actions">

          <el-button class="isd-btn isd-btn--ghost" :disabled="!list.length" @click="handlePrint">

            <el-icon><Printer /></el-icon>

            印刷

          </el-button>

          <el-button

            class="isd-btn isd-btn--primary"

            type="primary"

            :disabled="!list.length"

            @click="handleOpenNotify"

          >

            <el-icon><Promotion /></el-icon>

            メール・LINE送信

          </el-button>

        </div>

      </section>



      <!-- テーブル -->

      <section class="isd-table-wrap isd-card" v-loading="loading">

        <el-table

          :data="filteredList"

          stripe

          size="default"

          class="isd-table"

          :default-sort="{ prop: 'inventory_column', order: 'ascending' }"

          empty-text=""

          height="100%"

        >

          <el-table-column prop="inventory_column_label" label="在庫列" width="108" sortable>

            <template #default="{ row }">

              <span class="column-label" :class="inventoryChipClass(row.inventory_column)">

                {{ inventoryLabel(row.inventory_column) }}

              </span>

            </template>

          </el-table-column>

          <el-table-column prop="product_name" label="製品名" min-width="140" show-overflow-tooltip sortable />

          <el-table-column prop="product_cd" label="製品CD" width="100" show-overflow-tooltip sortable />

          <el-table-column prop="stable_quantity" label="在庫数" width="88" align="right" sortable>

            <template #default="{ row }">

              <span class="quantity-badge">{{ Number(row.stable_quantity).toLocaleString() }}</span>

            </template>

          </el-table-column>

          <el-table-column label="停滞期間" min-width="200" align="center">

            <template #default="{ row }">

              <div class="period-cell">

                <span class="period-cell__dates">{{ row.period_start }} ～ {{ row.period_end }}</span>

                <span v-if="row.days" class="period-cell__days">{{ row.days }} 日</span>

              </div>

            </template>

          </el-table-column>

          <el-table-column label="操作" width="120" align="center" fixed="right">

            <template #default="{ row }">

              <el-button class="isd-link-btn" type="primary" link @click="$emit('filter-product', row.product_cd)">

                <el-icon><Search /></el-icon>

                主表で絞込

              </el-button>

            </template>

          </el-table-column>



          <template #empty>

            <div class="isd-empty">

              <div class="isd-empty__icon"><el-icon :size="40"><CircleCheck /></el-icon></div>

              <p class="isd-empty__title">停滞在庫は見つかりませんでした</p>

              <p class="isd-empty__sub">条件を変更して再検索してください</p>

            </div>

          </template>

        </el-table>

      </section>

    </div>



    <template #footer>

      <div class="isd-footer">

        <el-button class="isd-footer__close" @click="visible = false">閉じる</el-button>

      </div>

    </template>



    <InventoryStagnationNotifyDialog

      v-model="notifyDialogVisible"

      :as-of-date="asOfDate"

      :min-quantity="minQuantity"

      :stable-days="stableDays"

    />

  </el-drawer>

</template>



<script setup lang="ts">

import { computed, ref, watch } from 'vue'

import { ElMessage } from 'element-plus'

import {

  Box,

  Calendar,

  CircleCheck,

  Close,

  Filter,

  Grid,

  Printer,

  Promotion,

  Refresh,

  Search,

  TrendCharts,

  WarningFilled,

} from '@element-plus/icons-vue'

import jaLocale from 'element-plus/es/locale/lang/ja'

import {

  getInventoryStagnation,

  type InventoryStagnationResponse,

  type InventoryStagnationRow,

} from '@/api/database'

import { useApsOperationPermission } from '@/composables/useApsOperationPermission'

import { guardApsOperation } from '@/utils/apsOperationGuard'

import InventoryStagnationNotifyDialog from './InventoryStagnationNotifyDialog.vue'

import { inventoryChipClass, inventoryColumnLabel } from './inventoryStagnationConstants'



const { canEdit, canExport } = useApsOperationPermission()



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



const inventoryLabel = inventoryColumnLabel



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

const notifyDialogVisible = ref(false)

const activeProcessFilter = ref<string | null>(null)



const processSummary = computed(() => {

  const map = new Map<string, { column: string; label: string; count: number }>()

  for (const row of list.value) {

    const col = row.inventory_column

    if (!map.has(col)) {

      map.set(col, { column: col, label: inventoryLabel(col), count: 0 })

    }

    map.get(col)!.count += 1

  }

  return [...map.values()].sort((a, b) => a.label.localeCompare(b.label, 'ja'))

})



const uniqueProductCount = computed(() => new Set(list.value.map((r) => r.product_cd).filter(Boolean)).size)



const filteredList = computed(() => {

  if (!activeProcessFilter.value) return list.value

  return list.value.filter((r) => r.inventory_column === activeProcessFilter.value)

})



function toggleProcessFilter(column: string) {

  activeProcessFilter.value = activeProcessFilter.value === column ? null : column

}



function handleOpenNotify() {

  if (!guardApsOperation(canExport)) return

  if (!list.value.length) {

    ElMessage.warning('送信対象データがありません')

    return

  }

  notifyDialogVisible.value = true

}



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

  if (!guardApsOperation(canExport)) return



  const printRows = filteredList.value.length ? filteredList.value : list.value

  if (!printRows.length) {

    ElMessage.warning('印刷対象データがありません')

    return

  }

  const grouped = new Map<string, InventoryStagnationRow[]>()

  for (const row of printRows) {

    const key = inventoryLabel(row.inventory_column)

    if (!grouped.has(key)) grouped.set(key, [])

    grouped.get(key)!.push(row)

  }

  const sections = Array.from(grouped.entries())

    .map(([groupName, rows]) => {

      const body = rows

        .map((r) => {

          const qty = Number(r.stable_quantity ?? 0).toLocaleString()

          return `<tr><td>${r.product_name || ''}</td><td>${r.product_cd || ''}</td><td class="num">${qty}</td><td>${r.period_start} ～ ${r.period_end}</td></tr>`

        })

        .join('')

      return `<section class="group"><h2>${groupName}</h2><table><thead><tr><th>製品名</th><th>製品CD</th><th>在庫数</th><th>期間</th></tr></thead><tbody>${body}</tbody></table></section>`

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

    h2 { margin: 0 0 6px; font-size: 13px; color:#1e40af; }

    table { width:100%; border-collapse: collapse; table-layout: fixed; }

    th, td { border: 1px solid #d1d5db; padding: 4px 6px; word-break: break-all; }

    th { background:#f3f4f6; text-align:left; }

    td.num { text-align:right; width: 90px; }

  </style>

</head>

<body onafterprint="window.close()">

  <div class="meta">基準日: ${asOfDate.value} / 閾値(>): ${minQuantity.value} / 連続暦日: ${stableDays.value} / 件数: ${printRows.length}</div>

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

  w.onload = () => {

    setTimeout(triggerPrint, 120)

  }

  setTimeout(triggerPrint, 500)

}



async function fetchList() {

  loading.value = true

  activeProcessFilter.value = null

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

  if (!guardApsOperation(canEdit)) return



  if (!asOfDate.value) asOfDate.value = todayJst()

  fetchList()

}



watch([asOfDate, minQuantity, stableDays], () => {

  if (!visible.value) return

  fetchList()

})

</script>



<style scoped>

.inventory-stagnation-drawer :deep(.el-drawer) {

  border-radius: 16px 0 0 16px;

  overflow: hidden;

}



.inventory-stagnation-drawer :deep(.el-drawer__header) {

  margin: 0;

  padding: 0;

  border-bottom: none;

}



.inventory-stagnation-drawer :deep(.el-drawer__body) {

  padding: 0;

  display: flex;

  flex-direction: column;

  background: linear-gradient(180deg, #f0f4fa 0%, #eef2f7 48%, #f8fafc 100%);

}



.inventory-stagnation-drawer :deep(.el-drawer__footer) {

  padding: 12px 20px 16px;

  border-top: 1px solid #e8edf3;

  background: rgba(255, 255, 255, 0.92);

  backdrop-filter: blur(8px);

}



/* Header */

.isd-header {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 12px;

  padding: 18px 20px 14px;

  background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);

  border-bottom: 1px solid #e8edf3;

}



.isd-header__brand {

  display: flex;

  align-items: center;

  gap: 14px;

  min-width: 0;

}



.isd-header__icon {

  display: flex;

  align-items: center;

  justify-content: center;

  width: 48px;

  height: 48px;

  border-radius: 14px;

  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);

  color: #fff;

  box-shadow: 0 10px 24px rgba(239, 68, 68, 0.28);

  flex-shrink: 0;

}



.isd-header__title {

  margin: 0;

  font-size: 18px;

  font-weight: 700;

  color: #0f172a;

  letter-spacing: 0.01em;

  line-height: 1.3;

}



.isd-header__sub {

  margin: 4px 0 0;

  font-size: 12px;

  color: #64748b;

  line-height: 1.4;

}



.isd-header__close {

  flex-shrink: 0;

  color: #64748b;

}



.isd-header__close:hover {

  color: #0f172a;

  background: #f1f5f9;

}



/* Body */

.isd-body {

  flex: 1;

  display: flex;

  flex-direction: column;

  gap: 12px;

  padding: 14px 16px 8px;

  min-height: 0;

  overflow: hidden;

}



.isd-card {

  background: #fff;

  border: 1px solid #e8edf3;

  border-radius: 14px;

  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);

}



.isd-card__head {

  display: flex;

  align-items: center;

  gap: 8px;

  padding: 12px 14px 0;

}



.isd-card__head-icon {

  display: inline-flex;

  align-items: center;

  justify-content: center;

  width: 28px;

  height: 28px;

  border-radius: 8px;

  background: #eff6ff;

  color: #2563eb;

  font-size: 14px;

}



.isd-card__head-title {

  font-size: 13px;

  font-weight: 700;

  color: #334155;

  flex: 1;

}



.isd-refresh-btn {

  font-weight: 600;

}



/* Filters */

.isd-filters {

  padding-bottom: 4px;

}



.isd-filter-form {

  display: flex;

  flex-wrap: wrap;

  gap: 4px 16px;

  padding: 8px 14px 12px;

}



.isd-filter-form :deep(.el-form-item) {

  margin-bottom: 0;

  margin-right: 0;

}



.isd-filter-form :deep(.el-form-item__label) {

  font-size: 11px;

  font-weight: 600;

  color: #64748b;

  padding-bottom: 4px;

  line-height: 1.2;

}



.isd-date-picker {

  width: 148px !important;

}



.isd-number-input {

  width: 120px;

}



.isd-field-hint {

  display: block;

  margin-top: 4px;

  font-size: 10px;

  color: #94a3b8;

  line-height: 1.2;

}



/* KPI */

.isd-kpi {

  display: grid;

  grid-template-columns: repeat(4, minmax(0, 1fr));

  gap: 10px;

}



.isd-kpi-card {

  display: flex;

  align-items: center;

  gap: 10px;

  padding: 12px 14px;

  border-radius: 14px;

  background: #fff;

  border: 1px solid #e8edf3;

  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);

  min-width: 0;

}



.isd-kpi-card--primary {

  background: linear-gradient(135deg, #fff7ed 0%, #fff1f2 100%);

  border-color: #fed7aa;

}



.isd-kpi-card--wide {

  grid-column: span 1;

}



.isd-kpi-card__icon {

  display: flex;

  align-items: center;

  justify-content: center;

  width: 36px;

  height: 36px;

  border-radius: 10px;

  background: #fee2e2;

  color: #dc2626;

  font-size: 18px;

  flex-shrink: 0;

}



.isd-kpi-card__icon--blue {

  background: #dbeafe;

  color: #2563eb;

}



.isd-kpi-card__icon--violet {

  background: #ede9fe;

  color: #7c3aed;

}



.isd-kpi-card__icon--slate {

  background: #f1f5f9;

  color: #475569;

}



.isd-kpi-card__body {

  min-width: 0;

}



.isd-kpi-card__label {

  display: block;

  font-size: 10px;

  font-weight: 600;

  color: #64748b;

  text-transform: uppercase;

  letter-spacing: 0.04em;

  margin-bottom: 2px;

}



.isd-kpi-card__value {

  font-size: 20px;

  font-weight: 800;

  color: #0f172a;

  line-height: 1.2;

}



.isd-kpi-card__value--sm {

  font-size: 12px;

  font-weight: 700;

  display: flex;

  flex-wrap: wrap;

  align-items: center;

  gap: 6px;

}



.isd-kpi-card__badge {

  display: inline-block;

  padding: 2px 8px;

  border-radius: 999px;

  font-size: 10px;

  font-weight: 700;

  color: #4338ca;

  background: #eef2ff;

}



/* Process chips */

.isd-process-chips {

  display: flex;

  flex-wrap: wrap;

  gap: 8px;

}



.isd-process-chip {

  display: inline-flex;

  align-items: center;

  gap: 6px;

  padding: 6px 12px;

  border-radius: 999px;

  border: 1px solid #e2e8f0;

  background: #fff;

  cursor: pointer;

  font-size: 12px;

  font-weight: 600;

  color: #475569;

  transition: all 0.18s ease;

  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);

}



.isd-process-chip:hover {

  border-color: #93c5fd;

  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);

  transform: translateY(-1px);

}



.isd-process-chip.is-active {

  border-color: #3b82f6;

  background: linear-gradient(135deg, #eff6ff 0%, #eef2ff 100%);

  color: #1d4ed8;

  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.15);

}



.isd-process-chip__count {

  display: inline-flex;

  align-items: center;

  justify-content: center;

  min-width: 20px;

  height: 20px;

  padding: 0 6px;

  border-radius: 999px;

  background: rgba(15, 23, 42, 0.08);

  font-size: 11px;

  font-weight: 800;

}



.isd-process-chip.is-active .isd-process-chip__count {

  background: #2563eb;

  color: #fff;

}



.isd-process-chip--clear {

  border-style: dashed;

  color: #64748b;

  background: transparent;

}



/* Toolbar */

.isd-toolbar {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 12px;

  padding: 8px 4px 0;

}



.isd-toolbar__info {

  font-size: 12px;

  color: #64748b;

  font-weight: 500;

}



.isd-toolbar__actions {

  display: flex;

  gap: 8px;

  flex-shrink: 0;

}



.isd-btn {

  font-weight: 600;

  border-radius: 10px;

}



.isd-btn--ghost {

  border: 1px solid #e2e8f0;

  background: #fff;

  color: #475569;

}



.isd-btn--ghost:hover {

  border-color: #cbd5e1;

  background: #f8fafc;

  color: #0f172a;

}



.isd-btn--primary {

  border: none;

  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);

  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28);

}



.isd-btn--primary:hover {

  background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%);

}



/* Table */

.isd-table-wrap {

  flex: 1;

  min-height: 200px;

  overflow: hidden;

  padding: 0;

  display: flex;

  flex-direction: column;

}



.isd-table {

  flex: 1;

  --el-table-header-bg-color: #f8fafc;

  --el-table-border-color: #eef2f7;

  --el-table-row-hover-bg-color: #f0f7ff;

}



.isd-table :deep(.el-table__header th) {

  background: #f8fafc !important;

  color: #475569;

  font-size: 12px;

  font-weight: 700;

  padding: 10px 0;

}



.isd-table :deep(.el-table__row td) {

  padding: 8px 0;

  font-size: 13px;

}



.isd-table :deep(.el-table__row--striped td) {

  background: #fafbfd;

}



.column-label {

  display: inline-block;

  padding: 3px 10px;

  border-radius: 999px;

  line-height: 18px;

  font-weight: 700;

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

  padding: 3px 10px;

  border-radius: 8px;

  font-weight: 800;

  font-variant-numeric: tabular-nums;

  color: #1d4ed8;

  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);

  font-size: 13px;

  line-height: 1.4;

  border: 1px solid #bfdbfe;

}



.period-cell {

  display: flex;

  flex-direction: column;

  align-items: center;

  gap: 4px;

}



.period-cell__dates {

  font-size: 12px;

  color: #334155;

  font-weight: 500;

}



.period-cell__days {

  display: inline-block;

  padding: 1px 8px;

  border-radius: 999px;

  font-size: 10px;

  font-weight: 700;

  color: #b45309;

  background: #fef3c7;

}



.isd-link-btn {

  font-weight: 600;

}



/* Empty */

.isd-empty {

  padding: 40px 16px;

  text-align: center;

}



.isd-empty__icon {

  display: inline-flex;

  align-items: center;

  justify-content: center;

  width: 72px;

  height: 72px;

  border-radius: 50%;

  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);

  color: #059669;

  margin-bottom: 12px;

}



.isd-empty__title {

  margin: 0 0 6px;

  font-size: 15px;

  font-weight: 700;

  color: #334155;

}



.isd-empty__sub {

  margin: 0;

  font-size: 12px;

  color: #94a3b8;

}



/* Footer */

.isd-footer {

  display: flex;

  justify-content: flex-end;

}



.isd-footer__close {

  min-width: 100px;

  font-weight: 600;

  border-radius: 10px;

}



@media (max-width: 860px) {

  .isd-kpi {

    grid-template-columns: repeat(2, minmax(0, 1fr));

  }



  .isd-toolbar {

    flex-direction: column;

    align-items: flex-start;

  }



  .isd-toolbar__actions {

    width: 100%;

    justify-content: flex-end;

  }

}

</style>


