<template>
  <div class="plan-summary-page">
    <header class="toolbar">
      <div class="toolbar-lead">
        <h1 class="toolbar-title">工程別計画試算</h1>
        <span class="toolbar-period">{{ periodLabel }}</span>
      </div>
      <div class="toolbar-actions">
        <el-date-picker
          v-model="yearMonth"
          type="month"
          value-format="YYYY-MM"
          format="YYYY年MM月"
          size="default"
          class="month-picker"
          :clearable="false"
          @change="loadData"
        />
        <el-button type="primary" :loading="loading" :icon="Refresh" @click="loadData">更新</el-button>
        <el-button
          type="success"
          plain
          :disabled="loading || matrixRows.length === 0"
          :icon="Download"
          @click="exportExcel"
        >
          Excel出力
        </el-button>
      </div>
    </header>

    <div class="table-shell" v-loading="loading">
      <div class="table-scroll">
        <el-table
          :data="matrixRows"
          border
          stripe
          size="small"
          class="matrix-table"
          empty-text="データがありません"
          :header-cell-style="headerCellStyle"
          :cell-style="cellStyle"
        >
          <el-table-column prop="item" label="項目" width="110" fixed="left" />
          <el-table-column
            v-for="date in dateColumns"
            :key="date"
            :prop="date"
            :label="formatDateLabel(date)"
            min-width="70"
            align="right"
          >
            <template #default="{ row }">
              {{ formatNumber(Number(row[date] ?? 0)) }}
            </template>
          </el-table-column>
          <el-table-column prop="rowTotal" label="合計" width="80" align="right" fixed="right" class-name="col-total">
            <template #default="{ row }">
              <span class="total-cell">{{ formatNumber(Number(row.rowTotal ?? 0)) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { getProductionSummarysList } from '@/api/database'
import { fetchProductProcessBOMList } from '@/api/master/productProcessBomMaster'

type MatrixRow = Record<string, string | number>
type DailyPlanValue = {
  forming: number
  forecastQuantity: number
  outsourcedWarehouseForecastQuantity: number
  chamferingPlan: number
  swPlan: number
  platingPlan: number
  outsourcedPlatingPlan: number
  weldingPlan: number
  outsourcedWeldingPlan: number
  outsourcedWarehousePlan: number
}

const today = new Date()
const yearMonth = ref(`${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`)
const loading = ref(false)
const dayPlanMap = ref<Record<string, DailyPlanValue>>({})

const periodLabel = computed(() => {
  const ym = yearMonth.value
  if (!ym || !/^\d{4}-\d{2}$/.test(ym)) return ''
  const [, m] = ym.split('-')
  return `${ym.slice(0, 4)}年${Number(m)}月`
})

function monthStartEnd(ym: string): { startDate: string; endDate: string } {
  const [yearStr, monthStr] = ym.split('-')
  const year = Number(yearStr)
  const month = Number(monthStr)
  const first = new Date(year, month - 1, 1)
  const last = new Date(year, month, 0)
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return { startDate: fmt(first), endDate: fmt(last) }
}

function formatNumber(value: number): string {
  return value.toLocaleString('ja-JP')
}

/** 列ヘッダーを「M/D」で短く表示 */
function formatDateLabel(isoDate: string): string {
  const parts = isoDate.split('-')
  if (parts.length !== 3) return isoDate
  return `${Number(parts[1])}/${Number(parts[2])}`
}

const headerCellStyle = () => ({
  background: 'var(--ps-header-bg)',
  color: 'var(--ps-header-text)',
  fontWeight: '600',
  fontSize: '12px',
  padding: '8px 6px',
})

const cellStyle = ({ column }: { column: { property?: string } }) => {
  if (column.property === 'rowTotal') {
    return { background: 'var(--ps-total-bg)' }
  }
  return { padding: '6px 8px' }
}

/** product_process_bom.outsourced_warehouse_process が有効な製品のみ true */
function hasOutsourcedWarehouseProcessFlag(v: unknown): boolean {
  if (v === true) return true
  if (typeof v === 'number') return v !== 0
  if (typeof v === 'string') return v === '1' || v.toLowerCase() === 'true'
  return false
}

async function loadOutsourcedWarehouseProductCdSet(): Promise<Set<string>> {
  const set = new Set<string>()
  let page = 1
  const limit = 500
  while (true) {
    const res = (await fetchProductProcessBOMList({ page, limit })) as {
      data?: { list?: unknown[] }
      list?: unknown[]
    }
    const list = res?.data?.list ?? res?.list ?? []
    for (const r of list as Array<{ product_cd?: unknown; outsourced_warehouse_process?: unknown }>) {
      if (!hasOutsourcedWarehouseProcessFlag(r?.outsourced_warehouse_process)) continue
      const cd = String(r?.product_cd ?? '').trim()
      if (cd) set.add(cd)
    }
    if (!list.length || list.length < limit) break
    page += 1
  }
  return set
}

const dateColumns = computed(() => Object.keys(dayPlanMap.value).sort((a, b) => a.localeCompare(b)))

const matrixRows = computed<MatrixRow[]>(() => {
  if (dateColumns.value.length === 0) return []
  const forecastRow: MatrixRow = { item: '内示数' }
  const outsourcedForecastRow: MatrixRow = { item: '外注内示数' }
  const formingRow: MatrixRow = { item: '成型計画数' }
  const chamferingRow: MatrixRow = { item: '面取数' }
  const swRow: MatrixRow = { item: 'SW数' }
  const kt05Row: MatrixRow = { item: 'メッキ数' }
  const kt06Row: MatrixRow = { item: '外注メッキ数' }
  const weldingRow: MatrixRow = { item: '溶接数' }
  const outsourcedWeldingRow: MatrixRow = { item: '外注溶接数' }
  const outsourcedWarehouseRow: MatrixRow = { item: '外注検査数' }
  let formingTotal = 0
  let forecastTotal = 0
  let outsourcedForecastTotal = 0
  let chamferingTotal = 0
  let swTotal = 0
  let kt05Total = 0
  let kt06Total = 0
  let weldingTotal = 0
  let outsourcedWeldingTotal = 0
  let outsourcedWarehouseTotal = 0

  for (const d of dateColumns.value) {
    const formingValue = Number(dayPlanMap.value[d]?.forming ?? 0)
    const forecastValue = Number(dayPlanMap.value[d]?.forecastQuantity ?? 0)
    const outsourcedForecastValue = Number(dayPlanMap.value[d]?.outsourcedWarehouseForecastQuantity ?? 0)
    const chamferingValue = Number(dayPlanMap.value[d]?.chamferingPlan ?? 0)
    const swValue = Number(dayPlanMap.value[d]?.swPlan ?? 0)
    const kt05Value = Number(dayPlanMap.value[d]?.platingPlan ?? 0)
    const kt06Value = Number(dayPlanMap.value[d]?.outsourcedPlatingPlan ?? 0)
    const weldingValue = Number(dayPlanMap.value[d]?.weldingPlan ?? 0)
    const outsourcedWeldingValue = Number(dayPlanMap.value[d]?.outsourcedWeldingPlan ?? 0)
    const outsourcedWarehouseValue = Number(dayPlanMap.value[d]?.outsourcedWarehousePlan ?? 0)
    formingRow[d] = formingValue
    forecastRow[d] = forecastValue
    outsourcedForecastRow[d] = outsourcedForecastValue
    chamferingRow[d] = chamferingValue
    swRow[d] = swValue
    kt05Row[d] = kt05Value
    kt06Row[d] = kt06Value
    weldingRow[d] = weldingValue
    outsourcedWeldingRow[d] = outsourcedWeldingValue
    outsourcedWarehouseRow[d] = outsourcedWarehouseValue
    formingTotal += formingValue
    forecastTotal += forecastValue
    outsourcedForecastTotal += outsourcedForecastValue
    chamferingTotal += chamferingValue
    swTotal += swValue
    kt05Total += kt05Value
    kt06Total += kt06Value
    weldingTotal += weldingValue
    outsourcedWeldingTotal += outsourcedWeldingValue
    outsourcedWarehouseTotal += outsourcedWarehouseValue
  }

  formingRow.rowTotal = formingTotal
  forecastRow.rowTotal = forecastTotal
  outsourcedForecastRow.rowTotal = outsourcedForecastTotal
  chamferingRow.rowTotal = chamferingTotal
  swRow.rowTotal = swTotal
  kt05Row.rowTotal = kt05Total
  kt06Row.rowTotal = kt06Total
  weldingRow.rowTotal = weldingTotal
  outsourcedWeldingRow.rowTotal = outsourcedWeldingTotal
  outsourcedWarehouseRow.rowTotal = outsourcedWarehouseTotal
  return [
    forecastRow,
    outsourcedForecastRow,
    formingRow,
    chamferingRow,
    swRow,
    kt05Row,
    kt06Row,
    weldingRow,
    outsourcedWeldingRow,
    outsourcedWarehouseRow,
  ]
})

function exportExcel() {
  const dates = dateColumns.value
  const rows = matrixRows.value
  if (rows.length === 0 || dates.length === 0) {
    ElMessage.warning('出力するデータがありません')
    return
  }
  const headerRow = ['項目', ...dates, '合計']
  const aoa: (string | number)[][] = [headerRow]
  for (const row of rows) {
    const line: (string | number)[] = [String(row.item)]
    for (const d of dates) {
      line.push(Number(row[d] ?? 0))
    }
    line.push(Number(row.rowTotal ?? 0))
    aoa.push(line)
  }
  const worksheet = XLSX.utils.aoa_to_sheet(aoa)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '工程別計画試算')
  const safeYm = (yearMonth.value || 'export').replace(/[^\d-]/g, '')
  XLSX.writeFile(workbook, `工程別計画試算_${safeYm}.xlsx`)
}

async function loadData() {
  if (!yearMonth.value) return
  loading.value = true
  try {
    const { startDate, endDate } = monthStartEnd(yearMonth.value)
    const [res, outsourcedWarehouseProducts] = await Promise.all([
      getProductionSummarysList({
        page: 1,
        limit: 50000,
        startDate,
        endDate,
      }),
      loadOutsourcedWarehouseProductCdSet(),
    ])
    const raw = (res as any)?.data?.list ?? (res as any)?.list ?? []
    const byDate = new Map<string, DailyPlanValue>()

    for (const item of raw) {
      const date = String(item?.date ?? '').slice(0, 10)
      if (!date) continue
      const productCd = String(item?.product_cd ?? '').trim()
      const molding = Number(item?.molding_plan ?? 0)
      const forecast = Number(item?.forecast_quantity ?? 0)
      const chamfering = Number(item?.chamfering_plan ?? 0)
      const sw = Number(item?.sw_plan ?? 0)
      const plating = Number(item?.plating_plan ?? 0)
      const outsourcedPlating = Number(item?.outsourced_plating_plan ?? 0)
      const welding = Number(item?.welding_plan ?? 0)
      const outsourcedWelding = Number(item?.outsourced_welding_plan ?? 0)
      const outsourcedWarehouse = Number(item?.outsourced_warehouse_plan ?? 0)
      const current = byDate.get(date) ?? {
        forming: 0,
        forecastQuantity: 0,
        outsourcedWarehouseForecastQuantity: 0,
        chamferingPlan: 0,
        swPlan: 0,
        platingPlan: 0,
        outsourcedPlatingPlan: 0,
        weldingPlan: 0,
        outsourcedWeldingPlan: 0,
        outsourcedWarehousePlan: 0,
      }
      current.forming += Number.isFinite(molding) ? molding : 0
      current.forecastQuantity += Number.isFinite(forecast) ? forecast : 0
      if (productCd && outsourcedWarehouseProducts.has(productCd)) {
        current.outsourcedWarehouseForecastQuantity += Number.isFinite(forecast) ? forecast : 0
      }
      current.chamferingPlan += Number.isFinite(chamfering) ? chamfering : 0
      current.swPlan += Number.isFinite(sw) ? sw : 0
      current.platingPlan += Number.isFinite(plating) ? plating : 0
      current.outsourcedPlatingPlan += Number.isFinite(outsourcedPlating) ? outsourcedPlating : 0
      current.weldingPlan += Number.isFinite(welding) ? welding : 0
      current.outsourcedWeldingPlan += Number.isFinite(outsourcedWelding) ? outsourcedWelding : 0
      current.outsourcedWarehousePlan += Number.isFinite(outsourcedWarehouse) ? outsourcedWarehouse : 0
      byDate.set(date, current)
    }

    dayPlanMap.value = Object.fromEntries(
      Array.from(byDate.entries()).sort(([a], [b]) => a.localeCompare(b)),
    )
  } catch (error) {
    console.error('工程別計画試算の読み込みに失敗しました', error)
    ElMessage.error('読み込みに失敗しました')
    dayPlanMap.value = {}
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadData()
})
</script>

<style scoped>
.plan-summary-page {
  --ps-header-bg: #f1f5f9;
  --ps-header-text: #334155;
  --ps-total-bg: #f8fafc;
  --ps-border: #e2e8f0;
  --ps-toolbar-bg: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  padding: 12px 14px 14px;
  max-width: 100%;
  box-sizing: border-box;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
  margin-bottom: 10px;
  padding: 10px 14px;
  background: var(--ps-toolbar-bg);
  border: 1px solid var(--ps-border);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.toolbar-lead {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  min-width: 0;
}

.toolbar-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.2;
}

.toolbar-period {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  padding: 2px 10px;
  background: #fff;
  border: 1px solid var(--ps-border);
  border-radius: 999px;
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.month-picker {
  width: 140px;
}

.table-shell {
  border: 1px solid var(--ps-border);
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.table-scroll {
  overflow-x: auto;
  vertical-align: middle;
}

.matrix-table {
  width: max-content;
  min-width: 100%;
}

.matrix-table :deep(.el-table__header-wrapper th) {
  border-color: var(--ps-border) !important;
}

.matrix-table :deep(.el-table__body-wrapper td) {
  border-color: #eef2f7 !important;
}

.matrix-table :deep(.el-table__row--striped td) {
  background: #fafbfc !important;
}

.matrix-table :deep(.col-total) {
  font-variant-numeric: tabular-nums;
}

.total-cell {
  font-weight: 600;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
</style>
