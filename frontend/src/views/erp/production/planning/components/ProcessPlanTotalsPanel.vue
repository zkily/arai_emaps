<template>

  <section v-if="totals.length" class="fdp-process-totals" aria-label="process plan totals">

    <div v-if="orderTotalsList.length" class="fdp-process-totals__block fdp-process-totals__block--order">

      <div class="fdp-process-totals__head">

        <span class="fdp-process-totals__mark fdp-process-totals__mark--order" />

        <div class="fdp-process-totals__titles">

          <span class="fdp-process-totals__title">{{ t('formingDailyPlan.orderProcessTotalsTitle') }}</span>

          <span class="fdp-process-totals__hint">{{ t('formingDailyPlan.orderProcessTotalsHint') }}</span>

        </div>

        <div class="fdp-process-totals__actions">

          <el-select

            v-model="printOrderProcessKey"

            size="small"

            :placeholder="t('formingDailyPlan.printProcessSelect')"

            class="fdp-process-totals__print-select"

          >

            <el-option

              v-for="p in printProcessOptions"

              :key="`order-print-${p.key}`"

              :label="p.label"

              :value="p.key"

            />

          </el-select>

          <el-button size="small" type="success" plain :icon="Printer" :loading="orderPrintLoading" @click="handlePrintOrder">

            {{ t('formingDailyPlan.printOrderProcessPlan') }}

          </el-button>

        </div>

      </div>

      <div class="fdp-process-totals__grid">

        <div

          v-for="row in orderTotalsList"

          :key="`order-${row.process_key}`"

          class="fdp-process-totals__card fdp-process-totals__card--order"

          :class="{ 'is-baseline': row.is_baseline }"

          :style="cardStyle(row.process_key)"

        >

          <span class="fdp-process-totals__dot" :style="{ background: processColor(row.process_key) }" />

          <span class="fdp-process-totals__label">{{ processLabel(row.process_key) }}</span>

          <span class="fdp-process-totals__value">{{ fmt(row.total) }}</span>

          <span v-if="!row.is_baseline && row.ratio_to_molding != null" class="fdp-process-totals__ratio">

            {{ t('formingDailyPlan.ratioToMolding') }} {{ pct(row.ratio_to_molding) }}

          </span>

          <span v-if="row.is_baseline" class="fdp-process-totals__badge fdp-process-totals__badge--order">

            {{ t('formingDailyPlan.baseline') }}

          </span>

        </div>

      </div>

    </div>



    <div class="fdp-process-totals__block fdp-process-totals__block--plan">

      <div class="fdp-process-totals__head">

        <span class="fdp-process-totals__mark" />

        <div class="fdp-process-totals__titles">

          <span class="fdp-process-totals__title">{{ t('formingDailyPlan.processTotalsTitle') }}</span>

          <span class="fdp-process-totals__hint">{{ t('formingDailyPlan.processTotalsHint') }}</span>

        </div>

        <div class="fdp-process-totals__actions">

          <el-select

            v-model="printProcessKey"

            size="small"

            :placeholder="t('formingDailyPlan.printProcessSelect')"

            class="fdp-process-totals__print-select"

          >

            <el-option v-for="p in printProcessOptions" :key="p.key" :label="p.label" :value="p.key" />

          </el-select>

          <el-button size="small" type="primary" plain :icon="Printer" :disabled="!canPrint" @click="handlePrint">

            {{ t('formingDailyPlan.printProcessPlan') }}

          </el-button>

        </div>

      </div>



      <div class="fdp-process-totals__grid">

        <div

          v-for="row in totals"

          :key="row.process_key"

          class="fdp-process-totals__card"

          :class="{ 'is-baseline': row.is_baseline }"

          :style="cardStyle(row.process_key)"

        >

          <span class="fdp-process-totals__dot" :style="{ background: processColor(row.process_key) }" />

          <span class="fdp-process-totals__label">{{ processLabel(row.process_key) }}</span>

          <span class="fdp-process-totals__value">{{ fmt(row.total) }}</span>

          <span v-if="!row.is_baseline && row.ratio_to_molding != null" class="fdp-process-totals__ratio">

            {{ t('formingDailyPlan.ratioToMolding') }} {{ pct(row.ratio_to_molding) }}

          </span>

          <span v-if="row.is_baseline" class="fdp-process-totals__badge">{{ t('formingDailyPlan.baseline') }}</span>

        </div>

      </div>



      <el-collapse v-if="showDailyTable && dailyRowsList.length" v-model="dailyTableOpen" class="fdp-process-totals__collapse">
        <el-collapse-item name="daily">
          <template #title>
            <span class="fdp-process-totals__collapse-title">{{ t('formingDailyPlan.processDailyTotals') }}</span>
            <el-button
              size="small"
              type="success"
              plain
              :icon="Download"
              class="fdp-process-totals__export-btn"
              @click.stop="exportDailyTotals"
            >
              {{ t('formingDailyPlan.exportExcel') }}
            </el-button>
          </template>
          <el-table :data="dailyRowsList" stripe border size="small" :max-height="240" class="fdp-process-totals__table">

            <el-table-column prop="process_key" :label="t('formingDailyPlan.colProcess')" width="72" fixed>

              <template #default="{ row }">

                <span class="fdp-process-totals__proc-cell">

                  <i class="fdp-process-totals__dot fdp-process-totals__dot--inline" :style="{ background: processColor(row.process_key) }" />

                  {{ processLabel(row.process_key) }}

                </span>

              </template>

            </el-table-column>

            <el-table-column prop="total" :label="t('formingDailyPlan.colPeriodTotal')" width="88" align="right" fixed>

              <template #default="{ row }">{{ fmt(row.total) }}</template>

            </el-table-column>

            <el-table-column v-for="d in datesList" :key="d" :label="d.slice(5)" width="58" align="right">

              <template #default="{ row }">{{ fmt(row.by_date?.[d]) }}</template>

            </el-table-column>

          </el-table>

        </el-collapse-item>

      </el-collapse>

    </div>

  </section>

</template>



<script setup lang="ts">

import { computed, ref } from 'vue'

import { useI18n } from 'vue-i18n'

import { ElMessage } from 'element-plus'

import { Download, Printer } from '@element-plus/icons-vue'

import type { DailyMatrixRow, OrderMatrixRow, ProcessPlanTotalItem, ProcessPlanDailyTotalRow } from '@/api/formingDailyPlan'

import { getFormingOrderMatrix } from '@/api/formingDailyPlan'

import {

  FORMING_PLAN_PROCESS_OPTIONS,

  fmtFormingNumber,

  processBgTint,

  processColor,

  processLabel,

} from './formingDailyPlanConstants'

import { printOrderProcessDetail, printProcessPlanDetail } from '../utils/formingDailyPlanPrint'
import { downloadExcelFromJson } from '@/utils/excelExport'



const props = defineProps<{

  totals?: ProcessPlanTotalItem[]

  orderTotals?: ProcessPlanTotalItem[]

  dailyRows?: ProcessPlanDailyTotalRow[]

  dates?: string[]

  showDailyTable?: boolean

  matrixRows?: DailyMatrixRow[]

  orderMatrixRows?: OrderMatrixRow[]

  products?: {

    product_cd: string

    product_name?: string | null

    machines?: Record<string, string>

    molding_order?: number | null

  }[]

  periodStart?: string

  periodEnd?: string

}>()



const { t } = useI18n()

const printProcessKey = ref('molding')

const printOrderProcessKey = ref('molding')

const orderPrintLoading = ref(false)

const dailyTableOpen = ref<string[]>([])

const cachedOrderMatrixRows = ref<OrderMatrixRow[] | null>(null)



const totals = computed(() => props.totals ?? [])

const orderTotalsList = computed(() => props.orderTotals ?? [])

const dailyRowsList = computed(() => props.dailyRows ?? [])

const datesList = computed(() => props.dates ?? [])



const printProcessOptions = computed(() => FORMING_PLAN_PROCESS_OPTIONS.filter((p) => p.key !== 'warehouse'))



const canPrint = computed(

  () => Boolean(printProcessKey.value && props.matrixRows?.length && props.periodStart && props.periodEnd),

)



function cardStyle(processKey: string) {

  return {

    background: processBgTint(processKey),

    borderLeftColor: processColor(processKey),

  }

}



function orderPrintLabels() {

  return {

    titleSuffix: t('formingDailyPlan.printOrderTitleSuffix'),

    period: t('formingDailyPlan.printPeriod'),

    printedAt: t('formingDailyPlan.printPrintedAt'),

    processTotal: t('formingDailyPlan.printOrderProcessTotal'),

    productCount: t('formingDailyPlan.printProductCount'),

    machineGroupCount: t('formingDailyPlan.printMachineGroupCount'),

    colProductName: t('formingDailyPlan.printColProductName'),

    colPeriodTotal: t('formingDailyPlan.printColPeriodTotal'),

    grandTotal: t('formingDailyPlan.printGrandTotal'),

    subtotal: t('formingDailyPlan.printSubtotal'),

    noData: t('formingDailyPlan.printContentNoData'),

    machineLabel: t('formingDailyPlan.printMachineLabel'),

    productUnit: t('formingDailyPlan.printProductUnit'),

    docTitle: t('formingDailyPlan.printOrderDocTitle'),

  }

}



async function resolveOrderMatrixRows(): Promise<OrderMatrixRow[]> {

  if (props.orderMatrixRows?.length) return props.orderMatrixRows

  if (cachedOrderMatrixRows.value?.length) return cachedOrderMatrixRows.value

  if (!props.periodStart || !props.periodEnd) return []

  const res = await getFormingOrderMatrix({ startDate: props.periodStart, endDate: props.periodEnd })

  const rows = (res as { data?: { rows?: OrderMatrixRow[] } }).data?.rows ?? []

  cachedOrderMatrixRows.value = rows

  return rows

}



async function handlePrintOrder() {

  if (!printOrderProcessKey.value || !props.periodStart || !props.periodEnd) {

    ElMessage.warning(t('formingDailyPlan.printNoData'))

    return

  }

  orderPrintLoading.value = true

  try {

    const matrixRows = await resolveOrderMatrixRows()

    if (!matrixRows.length) {

      ElMessage.warning(t('formingDailyPlan.printNoData'))

      return

    }

    const pk = printOrderProcessKey.value

    printOrderProcessDetail({

      processKey: pk,

      processLabel: processLabel(pk),

      periodStart: props.periodStart,

      periodEnd: props.periodEnd,

      dates: datesList.value,

      matrixRows,

      products: props.products ?? [],

      labels: orderPrintLabels(),

    })

  } catch (e) {

    if (e instanceof Error && e.message === 'POPUP_BLOCKED') {

      ElMessage.error(t('formingDailyPlan.printPopupBlocked'))

    } else {

      ElMessage.error(t('formingDailyPlan.printFailed'))

    }

  } finally {

    orderPrintLoading.value = false

  }

}



function handlePrint() {

  if (!printProcessKey.value || !props.matrixRows?.length) {

    ElMessage.warning(t('formingDailyPlan.printNoData'))

    return

  }

  const pk = printProcessKey.value

  try {

    printProcessPlanDetail({

      processKey: pk,

      processLabel: processLabel(pk),

      periodStart: props.periodStart!,

      periodEnd: props.periodEnd!,

      dates: datesList.value,

      matrixRows: props.matrixRows,

      products: props.products ?? [],

      labels: {

        titleSuffix: t('formingDailyPlan.printTitleSuffix'),

        period: t('formingDailyPlan.printPeriod'),

        printedAt: t('formingDailyPlan.printPrintedAt'),

        processTotal: t('formingDailyPlan.printProcessTotal'),

        productCount: t('formingDailyPlan.printProductCount'),

        machineGroupCount: t('formingDailyPlan.printMachineGroupCount'),

        colProductName: t('formingDailyPlan.printColProductName'),

        colPeriodTotal: t('formingDailyPlan.printColPeriodTotal'),

        grandTotal: t('formingDailyPlan.printGrandTotal'),

        subtotal: t('formingDailyPlan.printSubtotal'),

        noData: t('formingDailyPlan.printContentNoData'),

        machineLabel: t('formingDailyPlan.printMachineLabel'),

        productUnit: t('formingDailyPlan.printProductUnit'),

        docTitle: t('formingDailyPlan.printDocTitle'),

      },

    })

  } catch (e) {

    if (e instanceof Error && e.message === 'POPUP_BLOCKED') {

      ElMessage.error(t('formingDailyPlan.printPopupBlocked'))

    } else {

      ElMessage.error(t('formingDailyPlan.printFailed'))

    }

  }

}



function fmt(v?: number | null) {

  const n = Number(v ?? 0)

  if (!Number.isFinite(n) || n === 0) return '—'

  return fmtFormingNumber(n, false)

}



function pct(ratio: number | null | undefined) {
  const n = Number(ratio ?? 0)
  if (!Number.isFinite(n)) return '—'
  return `${(n * 100).toFixed(1)}%`
}

async function exportDailyTotals() {
  if (!dailyRowsList.value.length) {
    ElMessage.warning(t('formingDailyPlan.exportNoData'))
    return
  }
  const colProcess = t('formingDailyPlan.colProcess')
  const colTotal = t('formingDailyPlan.colPeriodTotal')
  const rows: Record<string, string | number>[] = dailyRowsList.value.map((row) => {
    const record: Record<string, string | number> = {
      [colProcess]: processLabel(row.process_key),
      [colTotal]: row.total ?? 0,
    }
    for (const d of datesList.value) {
      record[d] = row.by_date?.[d] ?? 0
    }
    return record
  })
  const start = props.periodStart ?? datesList.value[0] ?? 'period'
  await downloadExcelFromJson(
    rows,
    t('formingDailyPlan.exportSheetProcessDaily'),
    `process-daily-totals-${start}.xlsx`,
  )
}
</script>



<style scoped>

.fdp-process-totals {

  margin-bottom: 8px;

  display: flex;

  flex-direction: column;

  gap: 6px;

}

.fdp-process-totals__block {

  padding: 8px 10px;

  border-radius: 10px;

  border: 1px solid #e2e8f0;

}

.fdp-process-totals__block--order {

  background: linear-gradient(180deg, #f0fdf4 0%, #f8fffb 55%, #fff 100%);

  border-color: #bbf7d0;

}

.fdp-process-totals__block--plan {

  background: linear-gradient(180deg, #eff6ff 0%, #f8fbff 55%, #fff 100%);

  border-color: #bfdbfe;

}

.fdp-process-totals__head {

  display: flex;

  align-items: flex-start;

  gap: 8px;

  margin-bottom: 6px;

  flex-wrap: wrap;

}

.fdp-process-totals__mark {

  width: 4px;

  height: 28px;

  border-radius: 4px;

  background: linear-gradient(180deg, #3b82f6, #6366f1);

  flex-shrink: 0;

  margin-top: 2px;

}

.fdp-process-totals__mark--order {

  background: linear-gradient(180deg, #22c55e, #10b981);

}

.fdp-process-totals__titles {

  flex: 1;

  min-width: 160px;

}

.fdp-process-totals__title {

  display: block;

  font-size: 13px;

  font-weight: 700;

  color: #0f172a;

  line-height: 1.3;

}

.fdp-process-totals__hint {

  display: block;

  font-size: 10px;

  color: #64748b;

  margin-top: 1px;

  line-height: 1.35;

}

.fdp-process-totals__actions {

  display: flex;

  align-items: center;

  gap: 6px;

  flex-wrap: wrap;

}

.fdp-process-totals__print-select {

  width: 128px;

}

.fdp-process-totals__grid {

  display: grid;

  grid-template-columns: repeat(auto-fill, minmax(102px, 1fr));

  gap: 5px;

}

.fdp-process-totals__card {

  position: relative;

  padding: 5px 8px 6px 10px;

  border: 1px solid rgba(148, 163, 184, 0.35);

  border-left-width: 3px;

  border-radius: 8px;

  min-height: 58px;

}

.fdp-process-totals__card.is-baseline {

  border-color: rgba(245, 158, 11, 0.45);

  box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.12);

}

.fdp-process-totals__dot {

  display: block;

  width: 6px;

  height: 6px;

  border-radius: 50%;

  margin-bottom: 3px;

}

.fdp-process-totals__dot--inline {

  display: inline-block;

  margin: 0 4px 0 0;

  vertical-align: middle;

}

.fdp-process-totals__proc-cell {

  display: inline-flex;

  align-items: center;

  white-space: nowrap;

}

.fdp-process-totals__label {

  display: block;

  font-size: 10px;

  font-weight: 600;

  color: #475569;

  line-height: 1.2;

}

.fdp-process-totals__value {

  display: block;

  font-size: 15px;

  font-weight: 700;

  font-variant-numeric: tabular-nums;

  color: #0f172a;

  margin-top: 1px;

  line-height: 1.2;

}

.fdp-process-totals__ratio {

  display: block;

  font-size: 9px;

  font-weight: 600;

  color: #64748b;

  margin-top: 1px;

}

.fdp-process-totals__badge {

  display: inline-block;

  margin-top: 2px;

  font-size: 9px;

  font-weight: 700;

  padding: 0 5px;

  border-radius: 4px;

  background: linear-gradient(90deg, #f59e0b, #f97316);

  color: #fff;

}

.fdp-process-totals__badge--order {

  background: linear-gradient(90deg, #22c55e, #16a34a);

}

.fdp-process-totals__collapse {

  margin-top: 6px;

  border: none;

  background: transparent;

}

.fdp-process-totals__collapse :deep(.el-collapse-item__header) {
  height: 32px;
  line-height: 32px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  background: rgba(255, 255, 255, 0.65);
  border-radius: 6px;
  padding: 0 8px;
  border: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.fdp-process-totals__collapse-title {
  flex: 1;
  min-width: 0;
}
.fdp-process-totals__export-btn {
  flex-shrink: 0;
  margin-right: 4px;
}

.fdp-process-totals__collapse :deep(.el-collapse-item__wrap) {

  border: none;

}

.fdp-process-totals__collapse :deep(.el-collapse-item__content) {

  padding: 6px 0 0;

}

.fdp-process-totals__table :deep(.el-table__cell) {

  padding: 2px 0;

}

</style>

